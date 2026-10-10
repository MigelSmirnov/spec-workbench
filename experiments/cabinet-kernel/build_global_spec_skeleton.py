"""Mechanical skeleton of examples/cabinet-kernel/global_spec.json.

Writes only the sections the projector does not own. Every value is read from
a closed design state; nothing is decided here.

    python -I experiments/cabinet-kernel/build_global_spec_skeleton.py \
        examples/cabinet-kernel ../code_factory/tools

Sources: module_order / module_paths from the dependency list of 30_modules.md
(package root from the data provider's models_module); notes are the canonical
`scope: [CLASS] text` lines of 80_notes.md in file order; module_functions
holds only non-contract symbols (exceptions of 60_exception_taxonomy.json,
data-provider constants); imports.internal is every public State 6 function,
every class with contracts and every exception of its module, all constants of
data_provider; imports.module_internal is what the Factory's own
spec_import_hygiene finds in each consumer's contracts and positive note
clauses; rules.data_provider_backend is 70_data_provider_closure.json backend_ir
verbatim (no projector owns it). models stays {} so the projector, which lists
every key of models as a model, does not export role/schema_version.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CASE = Path(sys.argv[1]).resolve()
FACTORY_TOOLS = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(FACTORY_TOOLS))
import spec_import_hygiene as hygiene  # noqa: E402  the Factory's own judge of module_internal

NOTE_RE = re.compile(r"^([A-Za-z_][\w.]*): \[([A-Z_]+)\] ")


def load(name):
    return json.loads((CASE / name).read_text(encoding="utf-8"))


# --- module order and paths: the dependency list at the top of 30_modules.md
text = (CASE / "30_modules.md").read_text(encoding="utf-8")
block = text.split("```text", 1)[1].split("```", 1)[0]
layers = [[m.strip() for m in line.split(",")] for line in block.strip().splitlines()]
module_order = [m for layer in layers for m in layer]
layer_of = {m: i for i, layer in enumerate(layers) for m in layer}
provider_ir = load("70_data_provider_closure.json")["backend_ir"]
package = provider_ir["wiring"]["models_module"].rsplit(".", 1)[0]  # cabinet_kernel
module_paths = {m: f"{package}/{m}" for m in module_order}

# --- contracts and ownership: State 6 (projector writes them; read here only to derive imports)
contracts = load("60_contracts.json")["contracts"]
plan = load("60_contract_plan.json")["functions"]
owner = {row["function"]: row["module"].removeprefix("module:") for row in plan}
public = [row for row in plan if row["visibility"] == "public"]

# --- non-contract symbols each module owns
exceptions = load("60_exception_taxonomy.json")["exceptions"]
constants = sorted(provider_ir["constants"])
models = {**load("60_model_closure_domain.json")["models"], **load("60_model_closure_operations.json")["models"]}

module_functions = {m: [] for m in module_order}
module_functions["data_provider"] = list(constants)
for row in exceptions:
    module_functions[row["module"].removeprefix("module:")].append(row["symbol"])

# --- public export surface (imports.internal): public operations, owned
# classes with contracts reachable from a public signature, exceptions, constants
internal = {m: [] for m in module_order if m != "models"}
internal["data_provider"] = list(constants)
classes = {name.split(".", 1)[0] for name in contracts if "." in name}
for row in public:
    internal[owner[row["function"]]].append(row["function"])
for cls in sorted(classes):
    internal[owner[f"{cls}.__init__"] if f"{cls}.__init__" in owner else None].append(cls)
for row in exceptions:
    internal[row["module"].removeprefix("module:")].append(row["symbol"])
internal = {m: s for m, s in internal.items() if s}

# --- notes: canonical lines of 80_notes.md in file order
notes = [line for line in (CASE / "80_notes.md").read_text(encoding="utf-8").splitlines() if NOTE_RE.match(line)]

# --- module_internal: the direct runtime surface the Factory's own hygiene
# judge finds in each consumer's contracts and positive note clauses
full_mf = {m: list(s) for m, s in module_functions.items()}
for name, module in owner.items():
    sym = name.split(".", 1)[0]
    if sym not in full_mf[module]:
        full_mf[module].append(sym)
full_mf["models"] = list(models)
exports = dict(internal)
exports["models"] = list(models)
probe = {"contracts": contracts, "notes": notes, "module_functions": full_mf}
module_internal = {}
upward = []
for consumer in module_order:
    semantic = hygiene.consumer_semantic_text(probe, consumer)
    edges = {}
    for provider in module_order:
        if provider == consumer:
            continue
        used = [s for s in exports.get(provider, []) if hygiene._identifier_pattern(s).search(semantic)]
        if not used:
            continue
        if layer_of[provider] >= layer_of[consumer]:
            upward.append((consumer, provider, used))
        edges[provider] = sorted(used)
    if edges:
        module_internal[consumer] = edges

skeleton = {
    "standard_version": 2,
    "default_module": "surface",
    "contracts": {},
    "notes": notes,
    "config": {"role": "data", "schema_version": 1},
    "models": {},
    "rules": {"role": "data", "schema_version": 1, "data_provider_backend": provider_ir},
    "implementation_obligations": {},
    "imports": {"stdlib": [], "third_party": [], "internal": internal, "module_internal": module_internal},
    "module_functions": module_functions,
    "module_order": module_order,
    "module_paths": module_paths,
}
(CASE / "global_spec.json").write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "modules": len(module_order), "notes": len(notes),
    "internal": {m: len(s) for m, s in internal.items()},
    "module_internal_edges": sum(len(v) for v in module_internal.values()),
    "upward_edges": upward,
    "interfaces": [n for n, d in models.items() if d.get("kind") == "interface"],
}, indent=1))
