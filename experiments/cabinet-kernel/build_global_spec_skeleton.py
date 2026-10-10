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

When 70_persistence_closure.json is present: each repository module exports its
class and schema function, imports every model its codecs name and the port it
implements (SPEC_STANDARD 6.3, 5.1); a module that imports the class imports
every model of the class's operations, and every consumer imports the models
named by the signature of each callable it imports; implementation_obligations names the
repository class as the local implementation of each interface whose every
operation it carries. Models are read from every 60_model_closure_*.json.
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

# --- deterministic persistence (70_persistence_closure.json, when present)
persistence_path = CASE / "70_persistence_closure.json"
persistence_ir = load(persistence_path.name)["backend_ir"] if persistence_path.is_file() else None
repositories = persistence_ir["repositories"] if persistence_ir else []

# --- contracts and ownership: State 6 (projector writes them; read here only to derive imports)
contracts = load("60_contracts.json")["contracts"]
plan = load("60_contract_plan.json")["functions"]
owner = {row["function"]: row["module"].removeprefix("module:") for row in plan}
public = [row for row in plan if row["visibility"] == "public"]

# --- non-contract symbols each module owns
exceptions = load("60_exception_taxonomy.json")["exceptions"]
constants = sorted(provider_ir["constants"])
models = {name: declaration
          for path in sorted(CASE.glob("60_model_closure_*.json"))
          for name, declaration in load(path.name)["models"].items()}

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
    cls_owner = owner[f"{cls}.__init__"] if f"{cls}.__init__" in owner else owner[
        next(name for name in contracts if name.startswith(cls + "."))]
    if cls_owner != "models":  # an interface's contracts belong to models, which exports it already
        internal[cls_owner].append(cls)
# a deterministic repository module exports its class and its schema function to its owner
for repository in repositories:
    if repository["schema_function"] not in internal.setdefault(repository["module"], []):
        internal[repository["module"]].append(repository["schema_function"])
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


def models_named(text):
    return {name for name in models if re.search(rf"\b{re.escape(name)}\b", text)}


# --- implementation_obligations: an interface whose every operation a
# deterministic repository class carries is implemented locally by that class
implementation_obligations = {}
for name, declaration in models.items():
    if declaration.get("kind") != "interface":
        continue
    operations = {key.split(".", 1)[1] for key in contracts if key.startswith(name + ".")}
    for repository in repositories:
        carried = {key.split(".", 1)[1] for key in contracts if key.startswith(repository["repository"] + ".")}
        if operations and operations <= carried:
            implementation_obligations[name] = {"disposition": "local", "implementations": [repository["repository"]]}


# a repository module imports every model its codecs name (SPEC_STANDARD 6.3);
# the module that builds its class imports every model of the class's operations
for repository in repositories:
    module = repository["module"]
    tables = {table["table"]: table for table in persistence_ir["tables"]}
    codec = {table["model"] for table in tables.values()} | {
        column["element_model"] for table in tables.values() for column in table["columns"]
        if column["element_model"]}
    operations = " ".join(signature for name, signature in contracts.items()
                          if name.startswith(repository["repository"] + "."))
    own = module_internal.setdefault(module, {})
    implemented = {name for name, row in implementation_obligations.items()
                   if repository["repository"] in row["implementations"]}
    own["models"] = sorted(set(own.get("models", [])) | codec | models_named(operations) | implemented)
    for consumer, edges in module_internal.items():
        if consumer != module and repository["repository"] in edges.get(module, []):
            edges["models"] = sorted(set(edges.get("models", [])) | models_named(operations))


# a consumer imports every model named by the signature of a callable it
# imports (Factory Spec Inspector, module_type_surface_incomplete)
for consumer, edges in module_internal.items():
    named = set()
    for provider, symbols in edges.items():
        if provider == "models":
            continue
        for symbol in symbols:
            named |= models_named(" ".join(signature for name, signature in contracts.items()
                                           if name == symbol or name.startswith(symbol + ".")))
    if named:
        edges["models"] = sorted(set(edges.get("models", [])) | named)


skeleton = {
    "standard_version": 2,
    "default_module": "surface",
    "contracts": {},
    "notes": notes,
    "config": {"role": "data", "schema_version": 1},
    "models": {},
    "rules": {"role": "data", "schema_version": 1, "data_provider_backend": provider_ir},
    "implementation_obligations": implementation_obligations,
    "imports": {"stdlib": [], "third_party": [], "internal": internal, "module_internal": module_internal,
                # 60_contracts.md decision 27: the surface alone names pydantic
                "third_party_by_module": {"surface": ["from pydantic import BaseModel"]}},
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
