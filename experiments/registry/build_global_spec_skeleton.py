"""Mechanical skeleton of examples/registry/global_spec.json.

Writes only the sections the projector (tools/design_spec_projection.py) does
not own. Every value is read from a closed design state; nothing is decided
here.

    python -I experiments/registry/build_global_spec_skeleton.py examples/registry

Sources:
- module_order / module_paths: the dependency list of 30_modules.md, in its
  order; the package root is the data provider's models_module (`app`).
- default_module: `instance_lifecycle`, the module that owns the start and the
  running instance (30_modules.md); every callable has an owner in
  60_contract_plan.json, so no function falls to it.
- notes: the canonical `scope: [CLASS] text` lines of 80_notes.md in file
  order, or none while State 7 is unwritten; tools/design_notes.py
  --propagate carries them afterwards.
- imports.stdlib: one line per standard-library type the contracts and models
  name (§12, source 3): date, datetime, Decimal. The request streams are
  ports (`ByteStream`, `UploadBody`), so no `BinaryIO`.
- imports.internal: every public State 6 function of its module, every class
  with contracts owned outside models, the repository module's schema
  function. data_provider's constants are the projector's.
- imports.module_internal: left to the projector, which derives it from
  65_imports.json (imports_closure, after State 7).
- implementation_obligations: the rows 60_contracts.md records ("Steps are
  ports", "StoreTransaction is a class", "The upload body is a port"); the
  script checks each implementation carries every method of its port with the
  port's signature.
- module_functions: each module present and empty; the projector writes the
  callables and the data provider's constants.
Sections the projector owns (contracts, function_order, models, config, the
data rules, persistence, properties, determinism, rules.persistence_backend,
rules.system_clock_backend, rules.data_provider_backend) are written empty.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CASE = Path(sys.argv[1]).resolve()
NOTE_RE = re.compile(r"^([A-Za-z_][\w.]*): \[([A-Z_]+)\] ")


def load(name):
    return json.loads((CASE / name).read_text(encoding="utf-8"))


# --- module order and paths: the dependency list of 30_modules.md
text = (CASE / "30_modules.md").read_text(encoding="utf-8")
block = text.split("```text", 1)[1].split("```", 1)[0]
layers = [[m.strip() for m in line.split(",")] for line in block.strip().splitlines()]
module_order = [m for layer in layers for m in layer]
provider_ir = load("70_data_provider_closure.json")["backend_ir"]
package = provider_ir["wiring"]["models_module"].rsplit(".", 1)[0]
module_paths = {m: f"{package}/{m}" for m in module_order}
DEFAULT_MODULE = "instance_lifecycle"
assert DEFAULT_MODULE in module_order

# --- State 6
contracts = load("60_contracts.json")["contracts"]
plan = load("60_contract_plan.json")["functions"]
owner = {row["function"]: row["module"].removeprefix("module:") for row in plan}
assert set(owner) == set(contracts), "plan and contracts differ"
assert set(owner.values()) <= set(module_order), set(owner.values()) - set(module_order)
models = {name: declaration
          for path in sorted(CASE.glob("60_model_closure_*.json"))
          for name, declaration in load(path.name)["models"].items()}
persistence_ir = load("70_persistence_closure.json")["backend_ir"]

# --- imports.internal
internal = {m: [] for m in module_order if m not in ("models", provider_ir["wiring"]["module"])}
for row in plan:
    if row["visibility"] == "public" and "." not in row["function"]:
        internal[owner[row["function"]]].append(row["function"])
class_owner = {}
for name in contracts:
    if "." in name:
        class_owner.setdefault(name.split(".", 1)[0], set()).add(owner[name])
for cls, owners in sorted(class_owner.items()):
    assert len(owners) == 1, (cls, owners)
    (module,) = owners
    if module != "models":
        internal[module].append(cls)
for repository in persistence_ir["repositories"]:
    internal[repository["module"]].append(repository["schema_function"])
internal = {m: s for m, s in internal.items() if s}

# --- implementation_obligations (60_contracts.md)
implementation_obligations = {
    "OwnerStep": {"disposition": "policy", "implementations": ["OwnerRequestStep"]},
    "StoreRepository": {"disposition": "local", "implementations": ["SqliteStoreRepository"]},
    "TransactionStep": {"disposition": "policy", "implementations": ["OwnerActionStep", "ServiceCallStep"]},
    "UploadBody": {"disposition": "policy", "implementations": ["MultipartFileBody"]},
    "ByteStream": {"disposition": "external"},
}
interfaces = sorted(n for n, d in models.items() if d.get("kind") == "interface")
assert sorted(implementation_obligations) == interfaces, interfaces
for port, row in implementation_obligations.items():
    methods = {k.split(".", 1)[1]: v for k, v in contracts.items() if k.startswith(port + ".")}
    assert methods, port
    for implementation in row.get("implementations", []):
        for method, signature in methods.items():
            assert contracts.get(f"{implementation}.{method}") == signature, (implementation, method)

# --- notes
notes_path = CASE / "80_notes.md"
notes = [line for line in notes_path.read_text(encoding="utf-8").splitlines()
         if NOTE_RE.match(line)] if notes_path.is_file() else []

skeleton = {
    "standard_version": 2,
    "default_module": DEFAULT_MODULE,
    "contracts": {},
    "notes": notes,
    "config": {},
    "models": {},
    "rules": {},
    "implementation_obligations": implementation_obligations,
    "imports": {
        "stdlib": [
            "from datetime import date, datetime",
            "from decimal import Decimal",
        ],
        "third_party": [],
        "internal": internal,
        "module_internal": {},
    },
    "module_functions": {m: [] for m in module_order},
    "module_order": module_order,
    "module_paths": module_paths,
}
(CASE / "global_spec.json").write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "modules": len(module_order),
    "notes": len(notes),
    "internal": {m: len(s) for m, s in internal.items()},
    "interfaces": interfaces,
}, indent=1))
