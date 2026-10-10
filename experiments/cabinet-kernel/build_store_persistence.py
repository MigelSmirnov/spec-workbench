"""Mechanical expansion of the store's row table into its State 6 / 70 files.

The one table below (ROWS) is the design: per record type of
`store.read_records`, the row's key, the fields a lookup filters on, whether the
row is paged by `list_records`, which equality lists `store` reads, and whether
the row's lifecycle fields change. Everything else is expanded from it by fixed
rules, so the row models, the repository port, its contracts and the
persistence IR cannot disagree:

    python -I experiments/cabinet-kernel/build_store_persistence.py examples/cabinet-kernel

Writes (each wholly regenerated, nothing else touched):
- 60_model_closure_store.json   row models, the counter, StoreRepository
- 70_persistence_closure.json   persistence_backend/v3, sqlite_sync_v2
and rewrites only its own entries of
- 60_contract_plan.json / 60_contracts.json  (StoreRepository.*,
  SqliteStoreRepository.*, create_store_schema, next_store_position)
- 60_data_closure.json  (config.persistence.* and their placements)

Fixed rules:
- A row is (store_position, record_type, key fields, lookup fields, record).
  Activation and FlowActivation are identified by store position, so their
  key is store_position itself. The counter row is not a record.
- Every list is ordered by store_position ascending (store order); `store`
  reverses for a page.
- A paged row gets `list_<x>_rows` (constant filter on its own record_type:
  the whole table, sqlite_sync_v2 has no list_all) and
  `find_<x>_row_at_position` (continuation token check).
- A changing row gets `update_<x>_row`, which rewrites status and record.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CASE = Path(sys.argv[1]).resolve()

STR, INT = "str", "int"
ELEMENT, ATTEMPT, FILE = "ElementKey", "AttemptKey", "SpooledFileKey"
OPTIONAL_STR = "str | None"

# model, record_type member, key fields, lookup fields, paged, lists (field tuples), changes
ROWS = [
    ("Slot", "slot", [("slot_id", STR)], [], True, [], False),
    ("ContractVersion", "contract_version", [("contract_version_id", STR)],
     [("slot_id", STR)], True, [("slot_id",)], False),
    ("Implementation", "implementation", [("implementation_id", STR)],
     [("contract_version_id", STR)], True, [("contract_version_id",)], False),
    ("TrialCase", "trial_case", [("trial_case_id", STR)],
     [("contract_version_id", STR)], True, [("contract_version_id",)], False),
    ("TrialExecution", "trial_execution", [("trial_execution_id", STR)],
     [("implementation_id", STR), ("trial_case_id", STR)], True,
     [("implementation_id",), ("trial_case_id",)], False),
    ("AdmissionVerdict", "admission_verdict", [("implementation_id", STR), ("corpus_digest", STR)],
     [], True, [("implementation_id",)], False),
    ("Activation", "activation", [("store_position", INT)],
     [("contract_version_id", STR)], False, [("contract_version_id",)], False),
    ("OperationBinding", "binding", [("binding_id", STR)],
     [("service_id", STR), ("status", "BindingStatus")], True, [("status",), ("service_id",)], True),
    ("Flow", "flow", [("flow_id", STR)], [], True, [], False),
    ("FlowVersion", "flow_version", [("flow_version_id", STR)],
     [("flow_id", STR)], True, [("flow_id",)], False),
    ("FlowActivation", "flow_activation", [("store_position", INT)],
     [("flow_id", STR), ("flow_version_id", STR)], False, [("flow_id",), ("flow_version_id",)], False),
    ("Run", "run", [("run_id", STR)],
     [("flow_version_id", STR), ("status", "RunStatus")], True, [("status",), ("flow_version_id",)], True),
    ("NodeExecution", "node_execution", [("attempt", ATTEMPT)],
     [("element", ELEMENT), ("run_id", STR), ("executed_implementation_id", OPTIONAL_STR),
      ("executed_binding_id", OPTIONAL_STR)], True,
     [("run_id",), ("element",), ("executed_implementation_id",), ("executed_binding_id",)], False),
    ("StoredValue", "stored_value", [("value_id", STR)],
     [("value_digest", STR)], False, [("value_digest",)], False),
    ("SpooledFile", "spooled_file", [("file", FILE)],
     [("attempt", ATTEMPT), ("run_id", STR)], False, [("attempt",), ("run_id",)], False),
    ("EffectApproval", "approval", [("approval_id", STR)],
     [("element", ELEMENT), ("run_id", STR), ("status", "ApprovalStatus")], True,
     [("run_id",), ("status",), ("element",)], True),
    ("StandingGrant", "grant", [("grant_id", STR)],
     [("flow_version_id", STR), ("node_id", STR), ("status", "GrantStatus")], True,
     [("flow_version_id",), ("status",)], True),
    ("EffectAttempt", "effect_attempt", [("attempt", ATTEMPT)],
     [("element", ELEMENT), ("run_id", STR), ("status", "AttemptStatus")], True,
     [("run_id",), ("status",), ("element",)], True),
]
# The one extra read no equality list covers: the active grant of a flow
# version's node (status is the constant `active`).
ACTIVE_GRANT_METHOD = "list_active_standing_grant_rows_of_node"

REPOSITORY = "SqliteStoreRepository"
INTERFACE = "StoreRepository"
MODULE = "store_persistence"
SCHEMA_FUNCTION = "create_store_schema"
COUNTER_MODEL = "StorePositionCounter"
COUNTER_ENUM = "StoreCounterName"
NEXT_POSITION = "next_store_position"
ENUMS = {"BindingStatus", "RunStatus", "ApprovalStatus", "GrantStatus", "AttemptStatus", "RecordType", COUNTER_ENUM}
JSON_MODELS = {ELEMENT, ATTEMPT, FILE}

OWNED = {
    f"{INTERFACE}.", f"{REPOSITORY}.", SCHEMA_FUNCTION, NEXT_POSITION,
}


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def load(name: str) -> dict:
    return json.loads((CASE / name).read_text(encoding="utf-8"))


def dump(name: str, payload: dict) -> None:
    (CASE / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def column(field: str, annotation: str, *, record_model: str | None = None) -> dict:
    nullable = annotation.endswith(" | None")
    base = annotation.removesuffix(" | None")
    if record_model is not None:
        storage, element = "json_model", record_model
    elif base == STR:
        storage, element = "text", None
    elif base == INT:
        storage, element = "integer", None
    elif base in ENUMS:
        storage, element = "enum", base
    elif base in JSON_MODELS:
        storage, element = "json_model", base
    else:
        raise SystemExit(f"no storage for {field}: {annotation}")
    return {"column": field, "field": field, "storage": storage, "nullable": nullable,
            "check": None, "element_model": element}


def main() -> None:
    domain = {}
    for path in sorted(CASE.glob("60_model_closure_*.json")):
        if path.name != "60_model_closure_store.json":
            domain.update(load(path.name)["models"])

    models: dict = {}
    tables: list = []
    methods: list = []
    contracts: dict = {}           # method -> (arguments, return)
    purposes: dict = {}
    config: dict = {}

    def add(method: dict, arguments: str, returns: str, purpose: str) -> None:
        methods.append(method)
        contracts[method["method"]] = (arguments, returns)
        purposes[method["method"]] = purpose

    for model, member, keys, lookups, paged, lists, changes in ROWS:
        assert model in domain, model
        row = f"{model}Row"
        name = snake(model)
        table = f"{name}_rows"
        fields =[("store_position", INT), ("record_type", "RecordType"),
                  *[k for k in keys if k[0] != "store_position"], *lookups]
        models[row] = {"identity": "value", "fields": {**{f: a for f, a in fields}, "record": model}}
        columns = [column(f, a) for f, a in fields] + [column("record", model, record_model=model)]
        all_columns = [c["column"] for c in columns]
        primary = [k for k, _ in keys]
        config[f"{name}_table_name"] = table
        tables.append({
            "table": table, "table_name_ref": f"{name}_table_name", "model": row, "read_by": None,
            "columns": columns, "primary_key": primary,
            "unique": [] if primary == ["store_position"] else [["store_position"]],
        })
        annotations = dict(fields)
        order = [{"column": "store_position", "direction": "asc"}]

        def by(cols, *, constant=None):
            terms = [{"column": c, "bind": "argument", "argument": c} for c in cols]
            if constant is not None:
                terms.append(constant)
            return terms

        add({"method": f"insert_{name}_row", "query": "insert", "table": table, "columns": all_columns},
            f"row: {row}", "None", f"Insert one {model} row with its store position.")
        key_args = ", ".join(f"{k}: {a}" for k, a in keys)
        add({"method": f"load_{name}_row", "query": "get_by_key", "table": table,
             "filter": by(primary), "select": all_columns},
            key_args, f"{row} | None", f"Load the {model} row with this complete key, or none.")
        if paged:
            add({"method": f"find_{name}_row_at_position", "query": "get_unique", "table": table,
                 "filter": by(["store_position"]), "select": all_columns, "on_multiple": "error"},
                "store_position: int", f"{row} | None",
                f"Find the {model} row at this store position, or none.")
            add({"method": f"list_{name}_rows", "query": "list_by", "table": table,
                 "filter": [{"column": "record_type", "bind": "constant", "enum": "RecordType",
                             "member": member.upper()}],
                 "select": all_columns, "order_by": order},
                "", f"tuple[{row}, ...]", f"List every {model} row in store order.")
        for cols in lists:
            add({"method": f"list_{name}_rows_by_{'_and_'.join(cols)}", "query": "list_by", "table": table,
                 "filter": by(cols), "select": all_columns, "order_by": order},
                ", ".join(f"{c}: {annotations[c].removesuffix(' | None')}" for c in cols),
                f"tuple[{row}, ...]",
                f"List the {model} rows with this {' and '.join(cols)} in store order.")
        if model == "StandingGrant":
            add({"method": ACTIVE_GRANT_METHOD, "query": "list_by", "table": table,
                 "filter": by(["flow_version_id", "node_id"], constant={
                     "column": "status", "bind": "constant", "enum": "GrantStatus", "member": "ACTIVE"}),
                 "select": all_columns, "order_by": order},
                "flow_version_id: str, node_id: str", f"tuple[{row}, ...]",
                "List the active StandingGrant rows of this flow version's node in store order.")
        if changes:
            add({"method": f"update_{name}_row", "query": "update_fields", "table": table,
                 "filter": [{"column": k, "bind": "argument", "argument": k} for k in primary],
                 "updates": ["status", "record"], "require_existing": True},
                f"row: {row}", "None",
                f"Rewrite the status and record of the existing {model} row in place, keeping its store position.")

    # the store-position counter
    models[COUNTER_ENUM] = {"kind": "enum", "values": ["store_position"]}
    models[COUNTER_MODEL] = {"identity": "value", "fields": {"counter": COUNTER_ENUM, "last_position": "int"}}
    counter_table = "store_position_counter_rows"
    config["store_position_counter_table_name"] = counter_table
    tables.append({
        "table": counter_table, "table_name_ref": "store_position_counter_table_name", "model": COUNTER_MODEL,
        "read_by": None,
        "columns": [column("counter", COUNTER_ENUM), column("last_position", INT)],
        "primary_key": ["counter"], "unique": [],
    })
    add({"method": "load_store_position_counter", "query": "get_by_key", "table": counter_table,
         "filter": [{"column": "counter", "bind": "argument", "argument": "counter"}],
         "select": ["counter", "last_position"]},
        f"counter: {COUNTER_ENUM}", f"{COUNTER_MODEL} | None", "Load the store-position counter, or none before the first record.")
    add({"method": "upsert_store_position_counter", "query": "upsert", "table": counter_table,
         "columns": ["counter", "last_position"], "conflict": ["counter"], "updates": ["last_position"]},
        f"row: {COUNTER_MODEL}", "None", "Write the store-position counter's last position.")

    models[INTERFACE] = {"kind": "interface"}

    def signature(arguments: str, returns: str) -> str:
        return f"(self{', ' + arguments if arguments else ''}) -> {returns}"

    new_contracts = {f"{REPOSITORY}.__init__": "(self, connection: object) -> None",
                     SCHEMA_FUNCTION: "(connection: object) -> None"}
    for method, (arguments, returns) in contracts.items():
        new_contracts[f"{INTERFACE}.{method}"] = signature(arguments, returns)
    for method, (arguments, returns) in contracts.items():
        new_contracts[f"{REPOSITORY}.{method}"] = signature(arguments, returns)
    new_contracts[NEXT_POSITION] = f"(repository: {INTERFACE}) -> int"

    plan_rows = [
        {"function": f"{REPOSITORY}.__init__", "module": f"module:{MODULE}", "visibility": "internal",
         "purpose": "Construct the SQLite store repository over the connection whose transaction store opened."},
        {"function": SCHEMA_FUNCTION, "module": f"module:{MODULE}", "visibility": "internal",
         "purpose": "Create the store's closed SQLite tables idempotently."},
    ]
    for method in contracts:
        plan_rows.append({"function": f"{INTERFACE}.{method}", "module": "module:models", "visibility": "internal",
                          "purpose": f"Declare the record-port operation: {purposes[method][0].lower()}{purposes[method][1:]}"})
    for method in contracts:
        plan_rows.append({"function": f"{REPOSITORY}.{method}", "module": f"module:{MODULE}",
                          "visibility": "internal", "purpose": purposes[method]})
    plan_rows.append({"function": NEXT_POSITION, "module": "module:store", "visibility": "internal",
                      "purpose": "Advance the one store-position counter inside the open transaction and return the next position."})

    def ours(name: str) -> bool:
        return name in OWNED or any(name.startswith(prefix) for prefix in OWNED if prefix.endswith("."))

    plan = load("60_contract_plan.json")
    plan["functions"] = [row for row in plan["functions"] if not ours(row["function"])] + plan_rows
    dump("60_contract_plan.json", plan)
    catalog = load("60_contracts.json")
    catalog["contracts"] = {k: v for k, v in catalog["contracts"].items() if not ours(k)} | new_contracts
    dump("60_contracts.json", catalog)

    dump("60_model_closure_store.json", {
        "schema_version": "spec_workbench_model_closure.v1", "status": "closed",
        "identity_scope": "contract_only", "models": models,
    })

    data = load("60_data_closure.json")
    data["sections"]["config"]["persistence"] = config
    data["placements"] = [p for p in data["placements"] if not p["address"].startswith("config.persistence.")] + [
        {"address": f"config.persistence.{key}", "source_refs": ["decision:A18", "module:store_persistence"],
         "reason": "SQLite table identifier of the store's one database (A18 rule 2), owned by store_persistence "
                   "and referenced only by persistence_backend/v3."}
        for key in config
    ]
    dump("60_data_closure.json", data)

    dump("70_persistence_closure.json", {
        "schema_version": "spec_workbench_persistence_closure.v1",
        "status": "closed",
        "backend_ir": {
            "kind": "persistence_backend",
            "schema_version": 3,
            "backend": {"engine": "sqlite", "emitter": "sqlite_sync_v2"},
            "conventions": {"assert_open": "inside_try", "guard_reraise": "unchanged",
                            "codec_naming": "row_to_snake_model", "primary_key_not_null": "always"},
            "tables": tables,
            "aggregates": [],
            "repositories": [{
                "repository": REPOSITORY, "module": MODULE, "schema_function": SCHEMA_FUNCTION,
                "emission": "table", "transaction": "external", "methods": methods,
            }],
        },
    })
    write_interface_notes(methods)
    print(json.dumps({"rows": len(ROWS), "tables": len(tables), "methods": len(methods),
                      "contracts": len(new_contracts)}, indent=1))


def interface_note(method: dict) -> str:
    """The port's promise for one operation, from its kind alone."""
    query, name = method["query"], method["method"]
    terms = [term["column"] for term in method.get("filter", []) if term["bind"] == "argument"]
    constants = [f"{term['column']} {term['member'].lower()}" for term in method.get("filter", [])
                 if term["bind"] == "constant" and term["column"] != "record_type"]
    where = " and ".join(terms + constants)
    scope = f"{INTERFACE}.{name}"
    inside = "inside the transaction its connection holds"
    if query == "insert":
        return (f"{scope}: [DEPENDENCY_BOUNDARY] MUST add the given row as one new row {inside}; a row whose "
                "key or store position is already present is an integrity error, and no row is replaced.")
    if query == "get_by_key":
        return (f"{scope}: [DEPENDENCY_BOUNDARY] MUST return the stored row whose {where} equals the given "
                f"value exactly, {inside}, or None; it changes nothing.")
    if query == "get_unique":
        return (f"{scope}: [DEPENDENCY_BOUNDARY] MUST return the stored row whose store_position equals the "
                f"given one, {inside}, or None; two such rows are an integrity error; it changes nothing.")
    if query == "list_by" and not where:
        return (f"{scope}: [DETERMINISM_OR_ORDERING] MUST return every row of its record type in ascending "
                f"store_position, {inside}; it changes nothing.")
    if query == "list_by":
        argued = " and ".join(terms)
        matched = (f"whose {argued} equals the given value" if len(terms) == 1
                   else f"whose {argued} equal the given values")
        if constants:
            matched += " and whose " + " and ".join(c.replace(" ", " is ", 1) for c in constants)
        compared = ", the key model compared whole" if any(
            term in {"element", "attempt", "file"} for term in terms) else ""
        return (f"{scope}: [DETERMINISM_OR_ORDERING] MUST return exactly the rows {matched}{compared}, in "
                f"ascending store_position, {inside}; it changes nothing.")
    if query == "update_fields":
        return (f"{scope}: [DEPENDENCY_BOUNDARY] MUST rewrite only status and record of the existing row with "
                f"the given row's key {inside}, keeping its store_position, record_type and every other column, "
                "and fail when that row is absent.")
    if query == "upsert":
        return (f"{scope}: [DEPENDENCY_BOUNDARY] MUST write the given counter row {inside}, replacing only "
                "last_position of a counter row already present.")
    raise SystemExit(f"no note for {name}")


def write_interface_notes(methods: list) -> None:
    path = CASE / "80_notes.md"
    text = path.read_text(encoding="utf-8")
    block = "## models\n\n" + "\n".join(interface_note(method) for method in methods) + "\n\n"
    start = text.find("## models\n")
    if start >= 0:
        end = text.find("\n## ", start + 1) + 1
        text = text[:start] + block + text[end:]
    else:
        anchor = text.index("## canonical_values\n")
        text = text[:anchor] + block + text[anchor:]
    path.write_text(text, encoding="utf-8")


main()
