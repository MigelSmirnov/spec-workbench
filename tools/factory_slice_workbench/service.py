"""Ask the Factory what each module's generator will actually receive.

Every gate before this one reads the assembled specification. The Factory does
not generate from that document: it normalizes it, cuts one local specification
per module, builds a prompt from the cut, and resolves the changed data of the
whole uncarried scope. Four stops of Route B runs were decided there and nowhere
earlier:

- an operation sharing its name with a model field made the deterministic
  ``models`` module import a domain operation;
- an operation sharing its name with a contract parameter of the importing
  module was imported and then shadowed inside the body that must call it;
- a note's ``= rules.x`` put a value into the local specification, and the
  data/code seam (SPEC_STANDARD 15.9) refused to build the prompt;
- a changed data address that reaches no module stopped Route B at preflight
  (``affected_data_graph_incomplete``): the export asked the Factory about the
  delta of two specifications, the route asks about the whole scope no passing
  run has carried yet.

The probe runs the Factory's own normalizer, slicer and seam over every module
in a temporary directory, asks the Factory's own reachability resolver about
exactly the addresses Route B will ask about, and reports everything at once,
before export. Authority stays with the Factory tools; nothing here
re-implements their rules.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPORT_SCHEMA = "spec_workbench_factory_slice_probe.v1"
NORMALIZER = "tools/normalize_spec.py"
SLICER = "tools/build_local_spec.py"
SEAM = "tools/data_code_seam.py"
REACHABILITY = "tools/spec_data_reachability.py"
# The Factory names the deterministic model module literally (tools/data_code_seam.py).
MODELS_MODULE = "models"

_PARAMETER_RE = re.compile(r"[(,]\s*\*{0,2}([A-Za-z_][A-Za-z0-9_]*)\s*:")

_REACHABILITY_SCRIPT = """
import json, sys
sys.path.insert(0, 'tools')
import spec_data_reachability as reach
spec = json.load(open(sys.argv[1], encoding='utf-8'))
addresses = json.load(open(sys.argv[2], encoding='utf-8'))
print(json.dumps(reach.resolve_data_addresses(spec, addresses)['unresolved_addresses']))
"""

_SEAM_SCRIPT = """
import json, sys
sys.path.insert(0, 'tools')
import data_code_seam as seam
out = {}
for path in sys.argv[1:]:
    local_spec = json.load(open(path, encoding='utf-8'))
    out[local_spec.get('module_name') or path] = seam.data_in_model_context_defects(local_spec)
print(json.dumps(out))
"""


def _finding(code: str, module: str, message: str, **evidence: Any) -> dict[str, Any]:
    return {"severity": "block", "code": code, "module": module, "message": message, **evidence}


def _run(factory_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], cwd=factory_root, text=True, capture_output=True, check=False
    )


def _tail(result: subprocess.CompletedProcess[str]) -> str:
    lines = (result.stdout + result.stderr).strip().splitlines()
    return lines[-1] if lines else ""


def _own_parameters(spec: dict[str, Any]) -> dict[str, set[str]]:
    """Parameter names of the contracts each module owns."""
    owner = {
        str(function): str(module)
        for module, functions in (spec.get("module_functions") or {}).items()
        if isinstance(functions, list)
        for function in functions
    }
    parameters: dict[str, set[str]] = {}
    for function, contract in (spec.get("contracts") or {}).items():
        if isinstance(contract, str) and function in owner:
            parameters.setdefault(owner[function], set()).update(_PARAMETER_RE.findall(contract))
    return parameters


def _import_findings(
    module: str, local_spec: dict[str, Any], models_module: str, own_parameters: set[str]
) -> tuple[list[dict[str, Any]], int]:
    findings: list[dict[str, Any]] = []
    examined = 0
    internal = (local_spec.get("imports") or {}).get("internal") or {}
    for package, names in internal.items():
        if str(package).rsplit(".", 1)[-1] == models_module:
            continue
        names = [str(name) for name in names or []]
        examined += len(names)
        if module == models_module and names:
            findings.append(_finding(
                "models_imports_operation",
                module,
                f"The Factory slice of `{module}` imports {', '.join(names)} from {package}: a callable "
                "shares its name with a model field or a word of a model-scoped note. Rename the "
                "callable; the field is owned by the model.",
                package=str(package),
                symbols=names,
            ))
        for name in names:
            if name in own_parameters:
                findings.append(_finding(
                    "import_shadows_own_parameter",
                    module,
                    f"The Factory slice of `{module}` imports `{name}` from {package}, and `{name}` is "
                    "also a parameter of a contract this module owns: the import is either induced by "
                    "the parameter name alone or shadowed inside the body that must call it. Rename "
                    "the callable.",
                    package=str(package),
                    symbol=name,
                ))
    return findings, examined


def reachability_findings(
    source: Path, factory_root: Path, project: str | None
) -> tuple[list[dict[str, Any]], int]:
    """Ask the Factory about the data addresses Route B will ask about.

    Route B resolves the lineage manifest's cumulative ``changed_addresses`` against
    the current specification and blocks (``affected_data_graph_incomplete``) when
    one reaches no module. The export's own delta is pairwise, so an address that
    lost its last consumer in this handoff but changed in an earlier, never-carried
    one passes the export and stops the route. The scope is built by the export's
    own functions and judged by the Factory's own resolver
    (SPEC_STANDARD 15.3: a leaf no reference reaches is dead data).
    """
    if not project or not (factory_root / REACHABILITY).is_file():
        return [], 0
    # export_to_factory imports the admission workbench, which imports this module.
    import export_to_factory as export

    try:
        required = export.require_factory(factory_root)
        structure = json.loads(required["structure"].read_text(encoding="utf-8"))
        paths = export.project_paths(factory_root, structure, project)
    except (SystemExit, OSError, ValueError, KeyError):
        return [], 0
    canonical = paths["canonical"]
    if not canonical.is_file():
        return [], 0
    try:
        scope = export.project_change_scope(
            delta_tool=required["delta"], project=project, previous=canonical, source=source
        )
    except SystemExit as exc:
        return [_finding(
            "factory_change_scope_refused", "",
            f"The Factory's change-scope projector refuses this handoff: {exc}",
        )], 0
    scope = export.carry_pending_scope(scope, paths["working"], export.sha256_file(canonical))
    addresses = sorted({str(item) for item in scope.get("changed_addresses") or []})
    if not addresses:
        return [], 0
    with tempfile.TemporaryDirectory(prefix="spec-workbench-reach-") as temp:
        asked = Path(temp) / "addresses.json"
        asked.write_text(json.dumps(addresses), encoding="utf-8")
        result = _run(factory_root, ["-c", _REACHABILITY_SCRIPT, str(source), str(asked)])
    try:
        unresolved = json.loads(result.stdout)
    except json.JSONDecodeError:
        return [_finding(
            "factory_reachability_failed", "", "The Factory reachability resolver could not be asked.",
            detail=_tail(result),
        )], len(addresses)
    # A missing address is a deletion the accepting delta classifies; only an address
    # that exists and reaches no module stops the route.
    orphans = sorted(
        item["address"] for item in unresolved
        if isinstance(item, dict) and item.get("reason") == "no_module_consumer"
    )
    by_namespace: dict[str, list[str]] = {}
    for address in orphans:
        by_namespace.setdefault(".".join(address.split(".")[:2]), []).append(address)
    findings = [
        _finding(
            "changed_data_without_consumer",
            "",
            f"{namespace}: {len(items)} changed address(es) reach no module, and Route B preflight will block with "
            "affected_data_graph_incomplete. SPEC_STANDARD 15.3: a leaf no reference reaches is dead data; 15.3.1 "
            "names the three paths a value has to generated code. Give the value its path or take it out of the "
            "specification.",
            namespace=namespace,
            addresses=items,
        )
        for namespace, items in sorted(by_namespace.items())
    ]
    return findings, len(addresses)

def probe(
    source: Path,
    factory_root: Path,
    case_root: Path | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    source = source.resolve()
    factory_root = factory_root.resolve()
    spec = json.loads(source.read_text(encoding="utf-8"))
    declared = [str(name) for name in (spec.get("module_functions") or {})]
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "source": str(source),
        "factory_root": str(factory_root),
        "applicable": bool(declared),
        "ready": True,
        "summary": {
            "modules_declared": len(declared),
            "modules_sliced": 0,
            "imports_examined": 0,
            "seam_checked": 0,
            "changed_addresses_asked": 0,
        },
        "findings": [],
    }
    findings: list[dict[str, Any]] = report["findings"]
    unreachable, asked = reachability_findings(source, factory_root, project)
    findings.extend(unreachable)
    report["summary"]["changed_addresses_asked"] = asked
    if not declared:
        report["ready"] = not findings
        return report

    missing = [tool for tool in (NORMALIZER, SLICER) if not (factory_root / tool).is_file()]
    if missing:
        findings.append(_finding(
            "factory_slicer_missing", "", f"Factory tools are missing: {', '.join(missing)}.", tools=missing
        ))
        report["ready"] = False
        return report

    models_module = MODELS_MODULE
    own_parameters = _own_parameters(spec)
    with tempfile.TemporaryDirectory(prefix="spec-workbench-slices-") as temp:
        work = Path(temp)
        # The normalizer writes a report beside its input: give it a copy.
        shutil.copy(source, work / "global_spec.json")
        normalized = work / "normalized.json"
        result = _run(factory_root, [NORMALIZER, str(work / "global_spec.json"), str(normalized)])
        if result.returncode or not normalized.is_file():
            findings.append(_finding(
                "factory_normalization_failed", "", "The Factory normalizer rejects the specification.",
                detail=_tail(result),
            ))
            report["ready"] = False
            return report
        modules = list((json.loads(normalized.read_text(encoding="utf-8")).get("modules") or {}))
        slices = work / "slices"
        slices.mkdir()
        sliced: list[Path] = []
        for module in modules:
            result = _run(
                factory_root,
                [SLICER, module, str(normalized), str(work / "call_graph.json"), str(slices)],
            )
            path = slices / f"{module}.json"
            if result.returncode or not path.is_file():
                findings.append(_finding(
                    "factory_slice_failed", module,
                    f"The Factory slicer cannot cut a local specification for `{module}`.",
                    detail=_tail(result),
                ))
                continue
            sliced.append(path)
            local_spec = json.loads(path.read_text(encoding="utf-8"))
            found, examined = _import_findings(
                module, local_spec, models_module, own_parameters.get(module, set())
            )
            findings.extend(found)
            report["summary"]["imports_examined"] += examined
        report["summary"]["modules_sliced"] = len(sliced)
        if not modules:
            findings.append(_finding(
                "factory_slices_empty", "",
                f"The specification declares {len(declared)} modules and the Factory normalizer yields none.",
            ))
        if sliced and (factory_root / SEAM).is_file():
            result = _run(factory_root, ["-c", _SEAM_SCRIPT, *[str(path) for path in sliced]])
            try:
                defects = json.loads(result.stdout)
            except json.JSONDecodeError:
                findings.append(_finding(
                    "factory_seam_failed", "", "The Factory data/code seam could not be asked.",
                    detail=_tail(result),
                ))
            else:
                report["summary"]["seam_checked"] = len(defects)
                for module, addresses in defects.items():
                    if addresses:
                        findings.append(_finding(
                            "data_in_model_context",
                            str(module),
                            f"The Factory will refuse to build the prompt of `{module}`: its notes address "
                            f"{', '.join(addresses)} with `= …`, which puts the value into the local "
                            "specification (SPEC_STANDARD 15.9). Lower the values into the data provider "
                            "and name the imported constants.",
                            addresses=list(addresses),
                        ))
    report["ready"] = not findings
    return report
