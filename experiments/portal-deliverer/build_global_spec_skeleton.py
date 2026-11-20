"""Mechanical skeleton of examples/portal-deliverer/global_spec.json.

Writes only the sections the projector does not own. Every value is read from
a closed design state; nothing is decided here. Adapted from
experiments/cabinet-kernel/build_global_spec_skeleton.py.

    python -I experiments/portal-deliverer/build_global_spec_skeleton.py examples/portal-deliverer

Differences from the kernel script:

- State 3 declares its dependencies as a table "consumer | provider | symbols"
  (30_modules.md, "Dependencies"), not as layers; module_order is the
  topological order of that table, ties broken by the order of the module
  headings of 30_modules.md.
- State 3 names the model module `domain_models`; the assembled specification
  names it `models`, as cabinet-backend does (design_stage3 treats both names
  as the model substrate). Only the name changes.
- State 7 notes do not exist yet, so module_internal is the State 3 table as it
  stands, plus every model named by the signature of a callable a consumer
  imports. After the notes it is rebuilt from the Factory's import hygiene, as
  the kernel does.
- stdlib and third_party, and the module-scoped stdlib_by_module and
  third_party_by_module, are the author's full import lines (SPEC_STANDARD
  §7) and no design state holds them: the script keeps the lines the current
  global_spec.json carries. Once 60_contracts.json exists their signatures
  name stdlib and third-party types, so empty lists are refused rather than
  written: on 2026-11-20 they stayed empty and the Factory's validator found
  94 types without an origin, seen only by design_diagnose.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

CASE = Path(sys.argv[1]).resolve()
MODEL_MODULE = {"domain_models": "models"}
NOTE_RE = re.compile(r"^([A-Za-z_][\w.]*): \[([A-Z_]+)\] ")


def load(name):
    return json.loads((CASE / name).read_text(encoding="utf-8"))


def module_name(name: str) -> str:
    name = name.removeprefix("module:")
    return MODEL_MODULE.get(name, name)


# --- modules and their direct dependencies: 30_modules.md
text = (CASE / "30_modules.md").read_text(encoding="utf-8")
headings = [module_name(m) for m in re.findall(r"^## `([a-z_]+)`$", text, re.M)]
edges: dict[str, dict[str, list[str]]] = {}
table = text.split("## Dependencies", 1)[1].split("\n## ", 1)[0]
for row in re.findall(r"^\| `([a-z_]+)` \| `([a-z_]+)` \| (.+) \|$", table, re.M):
    consumer, provider, symbols = module_name(row[0]), module_name(row[1]), re.findall(r"`([A-Za-z_]\w*)`", row[2])
    edges.setdefault(consumer, {})[provider] = sorted(symbols)
unknown = {m for c, ps in edges.items() for m in (c, *ps)} - set(headings)
if unknown:
    raise SystemExit(f"modules in the dependency table without a section: {sorted(unknown)}")

module_order: list[str] = []
pending = list(headings)
while pending:
    ready = [m for m in pending if all(p in module_order for p in edges.get(m, {}))]
    if not ready:
        raise SystemExit(f"dependency cycle among {pending}")
    module_order.append(ready[0])
    pending.remove(ready[0])

provider_ir = load("70_data_provider_closure.json")["backend_ir"]
package = provider_ir["wiring"]["models_module"].rsplit(".", 1)[0]
module_paths = {m: f"{package}/{m}" for m in module_order}

# --- State 6
contracts = load("60_contracts.json")["contracts"]
plan = load("60_contract_plan.json")["functions"]
owner = {row["function"]: module_name(row["module"]) for row in plan}
public = [row for row in plan if row["visibility"] == "public"]
exceptions = load("60_exception_taxonomy.json")["exceptions"]
constants = sorted(provider_ir["constants"])
models = {name: declaration
          for path in sorted(CASE.glob("60_model_closure_*.json"))
          for name, declaration in load(path.name)["models"].items()}

# --- non-contract symbols each module owns
module_functions = {m: [] for m in module_order}
module_functions["data_provider"] = list(constants)
for row in exceptions:
    module_functions[module_name(row["module"])].append(row["symbol"])

# --- export surface: public operations, exceptions, constants, and every
# symbol another module imports by the State 3 table
internal = {m: [] for m in module_order if m != "models"}
internal["data_provider"] = list(constants)
for row in public:
    internal[owner[row["function"]]].append(row["function"])
for row in exceptions:
    module = module_name(row["module"])
    if module != "models":
        internal[module].append(row["symbol"])
for consumer, providers in edges.items():
    for provider, symbols in providers.items():
        if provider == "models":
            continue
        for symbol in symbols:
            if symbol not in internal[provider]:
                internal[provider].append(symbol)
internal = {m: s for m, s in internal.items() if s}


def models_named(text_: str) -> set[str]:
    return {name for name in models if re.search(rf"\b{re.escape(name)}\b", text_)}


# --- module_internal: the State 3 table, plus the models named by the
# signature of each callable a consumer imports
module_internal = {c: {p: list(s) for p, s in ps.items()} for c, ps in edges.items()}
for consumer, providers in module_internal.items():
    named = set()
    for provider, symbols in providers.items():
        if provider == "models":
            continue
        for symbol in symbols:
            if symbol in contracts:
                named |= models_named(contracts[symbol])
    if named:
        providers["models"] = sorted(set(providers.get("models", [])) | named)

upward = [(c, p) for c, ps in module_internal.items() for p in ps
          if module_order.index(p) >= module_order.index(c)]
if upward:
    raise SystemExit(f"upward import edges against module_order: {upward}")

notes_path = CASE / "80_notes.md"
notes = ([line for line in notes_path.read_text(encoding="utf-8").splitlines() if NOTE_RE.match(line)]
         if notes_path.is_file() else [])

# --- deterministic backends: every closed 70_*_closure.json backend_ir and the
# Router IR verbatim. Once global_spec.json exists, the Workbench compares each
# closed backend with its assembled rule and treats a missing one as open, so
# the first skeleton must already carry them; the projector then keeps them.
rules = {"role": "data", "schema_version": 1}
for path in sorted(CASE.glob("70_*_closure.json")):
    closure = load(path.name)
    backend = closure.get("backend_ir")
    if closure.get("status") == "closed" and isinstance(backend, dict) and backend.get("kind"):
        rules[backend["kind"]] = backend
router = subprocess.run([sys.executable, "tools/design_router_ir.py", str(CASE), "--handoff", "--json"],
                        capture_output=True, text=True, check=False)
router_ir = json.loads(router.stdout) if router.stdout.strip() else {}
if router_ir.get("ready"):
    rules.update(router_ir["rules"])
else:
    raise SystemExit(f"router IR is not ready: {router.stderr or router.stdout}")

# --- the author's import lines: kept, never reset
current_path = CASE / "global_spec.json"
current_imports = (json.loads(current_path.read_text(encoding="utf-8")).get("imports") or {}) if current_path.is_file() else {}
stdlib = list(current_imports.get("stdlib") or [])
third_party = list(current_imports.get("third_party") or [])
if (CASE / "60_contracts.json").is_file() and not stdlib and not third_party:
    raise SystemExit(
        "build_global_spec_skeleton: refused: imports.stdlib and imports.third_party of global_spec.json are "
        "empty while 60_contracts.json names types. Write the full import lines that bind them (SPEC_STANDARD §7, "
        "e.g. 'from uuid import UUID') into global_spec.json; the skeleton keeps them. To see which types lack "
        f"an origin: python tools/design_diagnose.py --case {CASE}")

default_module = owner["run_service"]
skeleton = {
    "standard_version": 2,
    "default_module": default_module,
    "contracts": {},
    "notes": notes,
    "config": {"role": "data", "schema_version": 1},
    "models": {},
    "rules": rules,
    "implementation_obligations": {},
    "imports": {"stdlib": stdlib, "third_party": third_party, "internal": internal, "module_internal": module_internal,
                **{key: current_imports[key] for key in ("stdlib_by_module", "third_party_by_module") if key in current_imports}},
    "module_functions": module_functions,
    "module_order": module_order,
    "module_paths": module_paths,
}
(CASE / "global_spec.json").write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "module_order": module_order,
    "default_module": default_module,
    "notes": len(notes),
    "internal": {m: len(s) for m, s in internal.items()},
    "module_internal_edges": sum(len(v) for v in module_internal.values()),
    "rules": sorted(k for k in rules if k not in ("role", "schema_version")),
}, indent=1))
