"""Ask the Factory what each module's generator will actually receive.

Every gate before this one reads the assembled specification. The Factory does
not generate from that document: it normalizes it, cuts one local specification
per module, and builds a prompt from the cut. Three stops of paid Route B runs
were decided in that cut and nowhere earlier:

- an operation sharing its name with a model field made the deterministic
  ``models`` module import a domain operation;
- an operation sharing its name with a contract parameter of the importing
  module was imported and then shadowed inside the body that must call it;
- a note's ``= rules.x`` put a value into the local specification, and the
  data/code seam (SPEC_STANDARD 15.9) refused to build the prompt.

The probe runs the Factory's own normalizer, slicer and seam over every module
in a temporary directory and reports all of them at once, before export. It
also holds a declared data-provider lowering to its sources. Authority stays
with the Factory tools; nothing here re-implements their rules.
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
DATA_PROVIDER_CLOSURE = "70_data_provider_closure.json"
NORMALIZER = "tools/normalize_spec.py"
SLICER = "tools/build_local_spec.py"
SEAM = "tools/data_code_seam.py"
# The Factory names the deterministic model module literally (tools/data_code_seam.py).
MODELS_MODULE = "models"

_PARAMETER_RE = re.compile(r"[(,]\s*\*{0,2}([A-Za-z_][A-Za-z0-9_]*)\s*:")
_ADDRESS_SEGMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\[\d+\]")

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


def _resolve(spec: dict[str, Any], address: str) -> Any:
    current: Any = spec
    for segment in _ADDRESS_SEGMENT_RE.findall(address):
        current = current[int(segment[1:-1])] if segment.startswith("[") else current[segment]
    return current


def _comparable(row: dict[str, Any], source: Any) -> Any:
    """The lowered value in the shape of its source.

    A record table lowered from a plain list carries the list position as its
    single other integer field; everything else is compared as written.
    """
    value = row.get("value")
    if row.get("value_type") != "record_tuple" or not isinstance(source, list):
        return value
    if not (isinstance(value, list) and all(isinstance(item, dict) and len(item) == 2 for item in value)):
        return value
    if any(isinstance(item, dict) for item in source):
        return value
    keys = sorted(value[0]) if value else []
    for position_key in keys:
        value_key = next(key for key in keys if key != position_key)
        ordered = sorted(value, key=lambda item: item[position_key])
        if [item[position_key] for item in ordered] == list(range(1, len(ordered) + 1)):
            return [item[value_key] for item in ordered]
    return value


def lowering_findings(spec: dict[str, Any], case_root: Path | None) -> tuple[list[dict[str, Any]], int]:
    """Hold a declared data-provider lowering to the values it was lowered from."""
    if case_root is None:
        return [], 0
    path = case_root / DATA_PROVIDER_CLOSURE
    if not path.is_file():
        return [], 0
    closure = json.loads(path.read_text(encoding="utf-8"))
    lowered_from = closure.get("lowered_from")
    backend = closure.get("backend_ir") if isinstance(closure.get("backend_ir"), dict) else {}
    constants = backend.get("constants") if isinstance(backend.get("constants"), dict) else {}
    module = str((backend.get("wiring") or {}).get("module") or "data_provider")
    findings: list[dict[str, Any]] = []
    assembled = (spec.get("rules") or {}).get("data_provider_backend")
    if assembled != backend:
        findings.append(_finding(
            "data_provider_not_assembled",
            module,
            f"rules.data_provider_backend of the assembled specification is not the backend_ir of {DATA_PROVIDER_CLOSURE}.",
        ))
    if not isinstance(lowered_from, dict):
        return findings, 0
    compared = 0
    for symbol, row in constants.items():
        address = lowered_from.get(symbol)
        if not isinstance(address, str):
            findings.append(_finding(
                "data_provider_constant_without_source",
                module,
                f"Constant {symbol} names no lowered_from address: its value has no design home.",
                symbol=symbol,
            ))
            continue
        try:
            source = _resolve(spec, address)
        except (KeyError, IndexError, TypeError):
            findings.append(_finding(
                "data_provider_source_unresolved",
                module,
                f"Constant {symbol} is lowered from {address}, which the assembled specification does not hold.",
                symbol=symbol,
                address=address,
            ))
            continue
        compared += 1
        if _comparable(row, source) != source:
            findings.append(_finding(
                "data_provider_lowering_drift",
                module,
                f"Constant {symbol} no longer equals {address}: change the value at its rules address and lower it again.",
                symbol=symbol,
                address=address,
            ))
    return findings, compared


def probe(source: Path, factory_root: Path, case_root: Path | None = None) -> dict[str, Any]:
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
            "constants_compared": 0,
        },
        "findings": [],
    }
    findings: list[dict[str, Any]] = report["findings"]
    lowering, compared = lowering_findings(spec, case_root)
    findings.extend(lowering)
    report["summary"]["constants_compared"] = compared
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
