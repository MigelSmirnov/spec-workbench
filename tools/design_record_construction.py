#!/usr/bin/env python3
"""State 6 closure gate of ``record_construction_backend/v1`` (SPEC_STANDARD §6.13).

The IR is authored in ``70_record_construction_closure.json``
(``spec_workbench_record_construction_backend_closure.v1``): ``backend_ir`` names,
for every field of every target, one source from the closed ref set, and for
every field of every model-typed input whether a ref reads it or why it is
dropped. This gate runs the closure checks RC001–RC015 on the IR against the
case's projected specification (models, contracts, ownership, determinism,
imports, module paths, data provider) at the State 6 handoff, so a construction
defect (an unknown field, a field without a source) stops the layer that made
it instead of the Factory's ``model_constructor_unknown_field`` after
generation.

The checks are a port of the Factory emitter's closed-data check
(``tools/generate_record_construction_draft.py``): the Workbench runs no
Factory code. Both sides run one fixture set
(``tests/fixtures/record_construction``, byte-identical to the Factory's
``verification/fixtures/record_construction``) and must give the same codes.

There is no clock source: a builder never reads a clock; an instant is a
parameter and the one wall reading of an operation stays with its caller.

Usage::

    python tools/design_record_construction.py <case> --coverage [--json]
    python tools/design_record_construction.py --spec <spec.json> [--json]
"""
from __future__ import annotations

import argparse
import ast
import json
import keyword
import re
import sys
from pathlib import Path
from typing import Any

CLOSURE_FILE = "70_record_construction_closure.json"
CLOSURE_SCHEMA = "spec_workbench_record_construction_backend_closure.v1"
IMPORTS_FILE = "65_imports.json"
RULE_KEY = "record_construction_backend"
EMITTER = "python_record_builders_v1"
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
DOTTED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*")

ROOT_KEYS = frozenset({"kind", "schema_version", "backend", "wiring", "constructions"})
WIRING_KEYS = frozenset({"module", "models_module"})
CONSTRUCTION_KEYS = frozenset({"form", "target", "consumers", "over", "element", "base", "parts", "fields", "dropped"})
PART_KEYS = frozenset({"target", "over", "element", "fields"})
FORMS = ("construct", "replace")
# ref -> its cells besides "ref" (and the optional "convert").
REF_CELLS: dict[str, frozenset[str]] = {
    "name": frozenset({"name"}),
    "field": frozenset({"of", "field"}),
    "part": frozenset({"name"}),
    "part_field": frozenset({"part", "field"}),
    "call": frozenset({"function", "args"}),
    "fresh_id": frozenset({"kind"}),
    "constant": frozenset({"symbol"}),
    "enum": frozenset({"type", "member"}),
    "literal": frozenset({"value"}),
    "none": frozenset(),
    "empty": frozenset(),
}
CONVERTIBLE_REFS = frozenset({"name", "field", "part_field"})
OVER_REFS = frozenset({"name", "field", "part_field"})
CONVERSIONS = ("uuid_canonical_string", "is_present", "enum_by_value", "naive_utc")
FRESH_ID_KINDS = ("uuid4",)
DROP_REASONS = (
    "not_in_target", "authorization_fact", "checked_only", "confidential", "stored_elsewhere",
    "superseded_by_persisted", "filter_only", "ordering_only", "binary_boundary",
)
DROP_KEYS = frozenset({"reason", "decision"})
NON_RECORD_KINDS = frozenset({"enum", "interface", "discriminated_union"})
# §6.10: the type a consumer sees for a data-provider constant.
DATA_PROVIDER_ACCESS_TYPES = {
    "string": "str",
    "positive_integer": "int",
    "boolean": "bool",
    "string_tuple": "tuple[str, ...]",
    "string_mapping": "Mapping[str, str]",
}
# Names an annotation may use besides declared models, and where they come from.
BUILTIN_TYPE_NAMES = frozenset({"bool", "bytes", "dict", "float", "int", "list", "None", "str", "tuple"})
STDLIB_TYPE_SOURCES = {
    "date": "datetime",
    "datetime": "datetime",
    "time": "datetime",
    "timedelta": "datetime",
    "Decimal": "decimal",
    "UUID": "uuid",
    "Any": "typing",
    "Mapping": "typing",
}

CODES = {
    "RC001": "construction_form",
    "RC002": "target_field_unsourced",
    "RC003": "target_field_multiple_sources",
    "RC004": "target_field_unknown",
    "RC005": "input_field_undisposed",
    "RC006": "input_field_read_and_dropped",
    "RC007": "name_unused",
    "RC008": "source_type_incompatible",
    "RC009": "reference_unresolved",
    "RC010": "call_contract_mismatch",
    "RC011": "builder_contract_mismatch",
    "RC012": "owner_not_unique",
    "RC013": "determinism_mismatch",
    "RC014": "import_edges",
    "RC015": "part_graph",
}


class ClosureDefect(ValueError):
    pass


# --- what the Factory models emitter writes (mirrored, never imported) ---------------------------


def split_annotation_and_default(raw_type: object) -> tuple[str, str | None]:
    """A model field type with its default split off (``int = 0``), as the Factory reads it."""
    text = str(raw_type).strip()
    if " = " not in text:
        return text, None
    annotation, default = text.split(" = ", 1)
    return annotation.strip(), default.strip()


def _python_identifier(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name.strip()) or "value"
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    if keyword.iskeyword(cleaned):
        cleaned = f"{cleaned}_"
    return cleaned


def emitted_enum_member_names(name: str, model: dict[str, Any]) -> list[str]:
    """Every member name the Factory models emitter writes for enum ``name``.

    Declared names (``members`` keys, a ``member_names`` list) are taken as
    they are; otherwise each value gets itself (when it is a non-keyword
    identifier not yet used) and its UPPER spelling: upper-case, every
    non-alphanumeric character ``_``, runs of ``_`` collapsed and stripped,
    ``VALUE_`` before a leading digit, ``_2``… on a clash. Mirrors
    ``generate_models_draft.emit_enum`` (Factory PR #194).
    """
    members = model.get("members")
    if isinstance(members, dict) and members:
        return [str(member) for member in members]
    values = model.get("values") or []
    member_names = model.get("member_names")
    if isinstance(member_names, list) and len(member_names) == len(values):
        return [str(member) for member in member_names]
    used: set[str] = set()
    names: list[str] = []
    for value in values:
        raw = str(value).strip()
        if raw.isidentifier() and not keyword.iskeyword(raw) and raw not in used:
            used.add(raw)
            names.append(raw)
        upper = _python_identifier(str(value).upper())
        while "__" in upper:
            upper = upper.replace("__", "_")
        upper = upper.strip("_") or "VALUE"
        if upper[0].isdigit():
            upper = f"VALUE_{upper}"
        base, counter = upper, 2
        while upper in used:
            upper = f"{base}_{counter}"
            counter += 1
        used.add(upper)
        if upper not in names:
            names.append(upper)
    return names


class DuplicateKey(ValueError):
    pass


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(key)
        result[key] = value
    return result


def loads_closed(text: str) -> dict[str, Any]:
    """Parse JSON refusing a repeated key: a second key is a second source (RC003)."""
    try:
        value = json.loads(text, object_pairs_hook=_no_duplicates)
    except DuplicateKey as exc:
        raise ClosureDefect(f"RC003 {CODES['RC003']}: JSON object repeats key {exc}") from None
    if not isinstance(value, dict):
        raise ClosureDefect("expected a JSON object")
    return value


def load_json(path: Path) -> dict[str, Any]:
    return loads_closed(path.read_text(encoding="utf-8"))



# --- types (§12, as far as this IR needs them) --------------------------------------------------


def canonical_type(text: str) -> str:
    annotation, _default = split_annotation_and_default(text)
    try:
        return ast.unparse(ast.parse(annotation, mode="eval").body)
    except SyntaxError:
        return annotation.strip()


def _union_members(annotation: str) -> list[str]:
    try:
        node = ast.parse(annotation, mode="eval").body
    except SyntaxError:
        return [annotation]
    members: list[str] = []

    def walk(item: ast.expr) -> None:
        if isinstance(item, ast.BinOp) and isinstance(item.op, ast.BitOr):
            walk(item.left)
            walk(item.right)
        else:
            members.append(ast.unparse(item))

    walk(node)
    return members


def is_nullable(annotation: str) -> bool:
    return "None" in _union_members(annotation)


def non_null(annotation: str) -> str:
    members = [member for member in _union_members(annotation) if member != "None"]
    return " | ".join(members)


def nullable_of(annotation: str) -> str:
    return annotation if is_nullable(annotation) else f"{annotation} | None"


def collection_element(annotation: str) -> str | None:
    """``T`` of ``list[T]`` or ``tuple[T, ...]``; None for anything else."""
    try:
        node = ast.parse(annotation, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name):
        return None
    if node.value.id == "list" and not isinstance(node.slice, ast.Tuple):
        return ast.unparse(node.slice)
    if (
        node.value.id == "tuple"
        and isinstance(node.slice, ast.Tuple)
        and len(node.slice.elts) == 2
        and isinstance(node.slice.elts[1], ast.Constant)
        and node.slice.elts[1].value is Ellipsis
    ):
        return ast.unparse(node.slice.elts[0])
    return None


def collection_kind(annotation: str) -> str | None:
    element = collection_element(annotation)
    if element is None:
        return None
    return "list" if annotation.startswith("list[") else "tuple"


def assignable(source: str, target: str) -> bool:
    """§12 without implicit conversions: equal, or ``T`` into ``T | None``."""
    if source == target:
        return True
    if is_nullable(target) and not is_nullable(source):
        return source == non_null(target)
    if is_nullable(target) and is_nullable(source):
        return non_null(source) == non_null(target)
    return False


def type_names(annotation: str) -> set[str]:
    try:
        node = ast.parse(annotation, mode="eval")
    except SyntaxError:
        return set()
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def parse_contract(signature: object) -> tuple[list[tuple[str, str]], str] | None:
    """``([(parameter, type)], return type)`` of a plain function contract."""
    if not isinstance(signature, str):
        return None
    try:
        node = ast.parse(f"def _contract{signature}:\n    pass\n").body[0]
    except SyntaxError:
        return None
    if not isinstance(node, ast.FunctionDef) or node.returns is None:
        return None
    arguments = node.args
    if arguments.vararg or arguments.kwarg or arguments.kwonlyargs or arguments.posonlyargs or arguments.defaults:
        return None
    parameters = []
    for item in arguments.args:
        if item.annotation is None:
            return None
        parameters.append((item.arg, ast.unparse(item.annotation)))
    return parameters, ast.unparse(node.returns)


# --- the spec view -------------------------------------------------------------------------------


class _View:
    """The parts of the spec the closure reads: models, contracts, ownership, determinism, imports."""

    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.models = spec.get("models") if isinstance(spec.get("models"), dict) else {}
        self.contracts = spec.get("contracts") if isinstance(spec.get("contracts"), dict) else {}
        functions = spec.get("module_functions") if isinstance(spec.get("module_functions"), dict) else {}
        self.module_functions = {
            str(module): [str(item) for item in names] for module, names in functions.items() if isinstance(names, list)
        }
        self.owner: dict[str, list[str]] = {}
        for module, names in sorted(self.module_functions.items()):
            for name in names:
                self.owner.setdefault(name, []).append(module)
        self.determinism = spec.get("determinism") if isinstance(spec.get("determinism"), dict) else {}
        imports = spec.get("imports") if isinstance(spec.get("imports"), dict) else {}
        internal = imports.get("module_internal") if isinstance(imports.get("module_internal"), dict) else {}
        self.module_internal = internal
        self.module_paths = spec.get("module_paths") if isinstance(spec.get("module_paths"), dict) else {}
        rules = spec.get("rules") if isinstance(spec.get("rules"), dict) else {}
        provider = rules.get("data_provider_backend")
        self.provider = provider if isinstance(provider, dict) else None

    def model(self, name: str) -> dict[str, Any] | None:
        value = self.models.get(name)
        return value if isinstance(value, dict) else None

    def record_fields(self, name: str) -> dict[str, str] | None:
        """Ordered ``field -> canonical type`` of a record model; None for anything else."""
        model = self.model(name)
        if model is None or model.get("kind") in NON_RECORD_KINDS or not isinstance(model.get("fields"), dict):
            return None
        return {str(field): canonical_type(str(kind)) for field, kind in model["fields"].items()}

    def is_enum(self, name: str) -> bool:
        model = self.model(name)
        return model is not None and model.get("kind") == "enum"

    def is_interface(self, name: str) -> bool:
        model = self.model(name)
        return model is not None and model.get("kind") == "interface"

    def enum_members(self, name: str) -> set[str]:
        model = self.model(name)
        if model is None:
            return set()
        try:
            return set(emitted_enum_member_names(name, model))
        except (ValueError, SyntaxError):
            return set()

    def edge(self, consumer: str, provider: str) -> set[str]:
        providers = self.module_internal.get(consumer)
        symbols = providers.get(provider) if isinstance(providers, dict) else None
        return {str(item) for item in symbols} if isinstance(symbols, list) else set()

    def provider_module(self) -> str | None:
        wiring = self.provider.get("wiring") if self.provider else None
        module = wiring.get("module") if isinstance(wiring, dict) else None
        return module if isinstance(module, str) else None

    def provider_constant_type(self, symbol: str) -> str | None:
        constants = self.provider.get("constants") if self.provider else None
        row = constants.get(symbol) if isinstance(constants, dict) else None
        if not isinstance(row, dict):
            return None
        if row.get("value_type") == "record_tuple" and isinstance(row.get("row_model"), str):
            return f"tuple[{row['row_model']}, ...]"
        return DATA_PROVIDER_ACCESS_TYPES.get(str(row.get("value_type")))


# --- the closure (RC001–RC015) -------------------------------------------------------------------


def _is_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(IDENTIFIER.fullmatch(value)) and not keyword.iskeyword(value)


def _form_findings(backend: Any, view: _View) -> list[tuple[str, str]]:
    """RC001: the closed form of §6.13. Nothing else is checked while the form is open."""
    findings: list[tuple[str, str]] = []

    def bad(path: str, message: str) -> None:
        findings.append(("RC001", f"{path}: {message}"))

    if not isinstance(backend, dict):
        bad(RULE_KEY, "expected object")
        return findings
    if set(backend) != ROOT_KEYS:
        bad(RULE_KEY, f"keys must be exactly {sorted(ROOT_KEYS)}")
        return findings
    if backend["kind"] != RULE_KEY or backend["schema_version"] != 1:
        bad(RULE_KEY, f"{RULE_KEY}/v1 is required")
    if backend["backend"] != {"emitter": EMITTER}:
        bad(f"{RULE_KEY}.backend", f"must be {{'emitter': {EMITTER!r}}}")
    wiring = backend["wiring"]
    if not isinstance(wiring, dict) or set(wiring) != WIRING_KEYS:
        bad(f"{RULE_KEY}.wiring", f"keys must be exactly {sorted(WIRING_KEYS)}")
    else:
        if not _is_identifier(wiring["module"]):
            bad(f"{RULE_KEY}.wiring.module", "expected an identifier")
        models_path = view.module_paths.get("models")
        expected = str(models_path).replace("/", ".") if isinstance(models_path, str) else None
        if not isinstance(wiring["models_module"], str) or not DOTTED.fullmatch(wiring["models_module"]):
            bad(f"{RULE_KEY}.wiring.models_module", "expected a dotted module path")
        elif wiring["models_module"] != expected:
            bad(f"{RULE_KEY}.wiring.models_module", f"must be module_paths.models as a dotted path ({expected!r})")
    constructions = backend["constructions"]
    if not isinstance(constructions, dict) or not constructions:
        bad(f"{RULE_KEY}.constructions", "expected a non-empty object")
        return findings
    for builder, row in constructions.items():
        path = f"constructions.{builder}"
        if not _is_identifier(builder) or str(builder).startswith("_"):
            bad(path, "a builder name is a public identifier")
        if not isinstance(row, dict) or set(row) != CONSTRUCTION_KEYS:
            bad(path, f"keys must be exactly {sorted(CONSTRUCTION_KEYS)}")
            continue
        if row["form"] not in FORMS:
            bad(f"{path}.form", f"must be one of {list(FORMS)}")
        if not _is_identifier(row["target"]):
            bad(f"{path}.target", "expected a model name")
        consumers = row["consumers"]
        if (
            not isinstance(consumers, list) or not consumers
            or not all(_is_identifier(item) for item in consumers) or len(set(consumers)) != len(consumers)
        ):
            bad(f"{path}.consumers", "expected a non-empty list of distinct module names")
        _over_form(row, path, bad)
        if row["form"] == "replace":
            if not _is_identifier(row["base"]):
                bad(f"{path}.base", "form replace names its base parameter")
        elif row["base"] is not None:
            bad(f"{path}.base", "only form replace has a base")
        parts = row["parts"]
        if not isinstance(parts, dict):
            bad(f"{path}.parts", "expected object")
            parts = {}
        if parts and (row["form"] != "construct" or row["over"] is not None):
            bad(f"{path}.parts", "only a single construct row has parts")
        for part, part_row in parts.items():
            part_path = f"{path}.parts.{part}"
            if not _is_identifier(part):
                bad(part_path, "a part name is an identifier")
            if not isinstance(part_row, dict) or set(part_row) != PART_KEYS:
                bad(part_path, f"keys must be exactly {sorted(PART_KEYS)}")
                continue
            if not _is_identifier(part_row["target"]):
                bad(f"{part_path}.target", "expected a model name")
            _over_form(part_row, part_path, bad)
            _fields_form(part_row["fields"], f"{part_path}.fields", bad)
        _fields_form(row["fields"], f"{path}.fields", bad)
        dropped = row["dropped"]
        if not isinstance(dropped, dict):
            bad(f"{path}.dropped", "expected object")
        else:
            for name, fields in dropped.items():
                if not isinstance(fields, dict) or not fields:
                    bad(f"{path}.dropped.{name}", "expected a non-empty object of fields")
                    continue
                for field, reason in fields.items():
                    where = f"{path}.dropped.{name}.{field}"
                    if not isinstance(reason, dict) or set(reason) != DROP_KEYS:
                        bad(where, f"keys must be exactly {sorted(DROP_KEYS)}")
                    elif reason["reason"] not in DROP_REASONS:
                        bad(f"{where}.reason", f"must be one of {list(DROP_REASONS)}")
                    elif reason["decision"] is not None and not (
                        isinstance(reason["decision"], str) and reason["decision"].strip()
                    ):
                        bad(f"{where}.decision", "a decision id or null")
        if not findings:
            findings.extend(_collision_findings(builder, row, view))
    return findings


def _over_form(row: dict[str, Any], path: str, bad) -> None:
    over, element = row["over"], row["element"]
    if (over is None) != (element is None):
        bad(path, "over and element come together or not at all")
    if element is not None and not _is_identifier(element):
        bad(f"{path}.element", "expected an identifier")
    if over is not None:
        if not _ref_form(over, f"{path}.over", bad):
            return
        if over["ref"] not in OVER_REFS or "convert" in over:
            bad(f"{path}.over", f"over is a {sorted(OVER_REFS)} ref without convert")


def _fields_form(fields: Any, path: str, bad) -> None:
    if not isinstance(fields, dict):
        bad(path, "expected object")
        return
    for field, ref in fields.items():
        if not _is_identifier(field):
            bad(f"{path}.{field}", "a field name is an identifier")
        _ref_form(ref, f"{path}.{field}", bad)


def _scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _ref_form(ref: Any, path: str, bad) -> bool:
    if not isinstance(ref, dict) or ref.get("ref") not in REF_CELLS:
        bad(path, f"a ref is an object whose ref is one of {sorted(REF_CELLS)}")
        return False
    for cell, value in ref.items():
        # §6.0: a ref is a leaf — scalars or arrays of scalars only.
        if not (_scalar(value) or (isinstance(value, list) and all(_scalar(item) for item in value))):
            bad(path, f"cell {cell} is not a scalar or an array of scalars")
            return False
    kind = ref["ref"]
    cells = set(ref) - {"ref"}
    allowed = REF_CELLS[kind] | ({"convert"} if kind in CONVERTIBLE_REFS else set())
    if not REF_CELLS[kind] <= cells or not cells <= allowed:
        bad(path, f"ref {kind} has exactly the cells {sorted(REF_CELLS[kind])}"
                  + (" and optionally convert" if kind in CONVERTIBLE_REFS else ""))
        return False
    if "convert" in ref and ref["convert"] not in CONVERSIONS:
        bad(f"{path}.convert", f"must be one of {list(CONVERSIONS)}")
        return False
    for cell in ("name", "of", "field", "part", "function", "symbol", "type", "member"):
        if cell in ref and not isinstance(ref[cell], str):
            bad(f"{path}.{cell}", "expected a string")
            return False
    for cell in ("name", "of", "field", "part", "function", "symbol", "type"):
        if cell in ref and "." not in ref[cell] and not _is_identifier(ref[cell]):
            bad(f"{path}.{cell}", "expected an identifier")
            return False
    if kind == "call" and (
        not isinstance(ref["args"], list) or not all(isinstance(item, str) for item in ref["args"])
    ):
        bad(f"{path}.args", "expected an array of names")
        return False
    if kind == "fresh_id" and ref["kind"] not in FRESH_ID_KINDS:
        bad(f"{path}.kind", f"must be one of {list(FRESH_ID_KINDS)}")
        return False
    if kind == "literal" and not isinstance(ref["value"], bool):
        bad(f"{path}.value", "a literal is true or false")
        return False
    return True


def _collision_findings(builder: str, row: dict[str, Any], view: _View) -> list[tuple[str, str]]:
    """Local names of one builder are distinct: parameters, elements and parts never shadow each other."""
    contract = parse_contract(view.contracts.get(builder))
    parameters = {name for name, _type in contract[0]} if contract else set()
    seen: dict[str, str] = {name: "parameter" for name in parameters}
    findings = []
    locals_ = []
    if row["element"] is not None:
        locals_.append((row["element"], "element"))
    for part, part_row in row["parts"].items():
        locals_.append((part, "part"))
        if part_row["element"] is not None:
            locals_.append((part_row["element"], "element"))
    for name, kind in locals_:
        if name in seen:
            findings.append(("RC001", f"constructions.{builder}: {kind} {name} shadows the {seen[name]} of that name"))
        seen[name] = kind
    return findings


def closure_findings(spec: dict[str, Any]) -> list[tuple[str, str]]:
    """Every RC finding of ``rules.record_construction_backend`` against the spec, in check order.

    Deterministic and local to the IR, ``models``, ``contracts``,
    ``module_functions``, ``determinism``, ``imports.module_internal``,
    ``module_paths`` and ``rules.data_provider_backend``. Notes are not read.
    """
    view = _View(spec)
    backend = (spec.get("rules") or {}).get(RULE_KEY) if isinstance(spec.get("rules"), dict) else None
    findings = _form_findings(backend, view)
    if findings:
        return findings
    checker = _Closure(backend, view)
    checker.run()
    return checker.findings


class _Closure:
    def __init__(self, backend: dict[str, Any], view: _View) -> None:
        self.backend = backend
        self.view = view
        self.module = backend["wiring"]["module"]
        self.constructions: dict[str, dict[str, Any]] = backend["constructions"]
        self.findings: list[tuple[str, str]] = []
        self.contracts: dict[str, tuple[list[tuple[str, str]], str]] = {}

    def add(self, code: str, message: str) -> None:
        self.findings.append((code, message))

    def run(self) -> None:
        for builder in self.constructions:
            contract = parse_contract(self.view.contracts.get(builder))
            if contract is None:
                self.add("RC011", f"{builder}: contracts.{builder} is missing or not a plain function contract")
            else:
                self.contracts[builder] = contract
        self._ownership()
        for builder in sorted(self.constructions):
            if builder in self.contracts:
                _Builder(self, builder).run()
        self._builder_call_cycles()
        self._determinism()
        self._import_edges()

    # RC012
    def _ownership(self) -> None:
        owned = self.view.module_functions.get(self.module)
        if owned is None or set(owned) != set(self.constructions) or len(owned) != len(set(owned)):
            self.add("RC012", f"module_functions.{self.module} must be exactly the builders "
                              f"{sorted(self.constructions)}; is {owned!r}")
        for builder in sorted(self.constructions):
            others = [module for module in self.view.owner.get(builder, []) if module != self.module]
            if others:
                self.add("RC012", f"{builder} is also owned by {others}")

    def called_builders(self, builder: str) -> set[str]:
        called = set()
        for ref in _all_refs(self.constructions[builder]):
            if ref["ref"] == "call" and ref["function"] in self.constructions:
                called.add(ref["function"])
        return called

    def _builder_call_cycles(self) -> None:
        state: dict[str, int] = {}

        def visit(builder: str, trail: list[str]) -> None:
            state[builder] = 1
            for callee in sorted(self.called_builders(builder)):
                if state.get(callee) == 1:
                    self.add("RC010", f"builders call each other in a cycle: {' -> '.join([*trail, callee])}")
                elif callee not in state:
                    visit(callee, [*trail, callee])
            state[builder] = 2

        for builder in sorted(self.constructions):
            if builder not in state:
                visit(builder, [builder])

    def derived_determinism(self, builder: str, seen: frozenset[str] = frozenset()) -> bool:
        if builder in seen:
            return True
        if any(ref["ref"] == "fresh_id" for ref in _all_refs(self.constructions[builder])):
            return False
        return all(self.derived_determinism(callee, seen | {builder}) for callee in self.called_builders(builder))

    # RC013
    def _determinism(self) -> None:
        for builder in sorted(self.constructions):
            expected = self.derived_determinism(builder)
            if self.view.determinism.get(builder) is not expected:
                self.add("RC013", f"determinism.{builder} must be {str(expected).lower()} "
                                  f"({'a fresh_id' if not expected else 'no fresh_id'} in the construction)")

    # RC014
    def _import_edges(self) -> None:
        provider = self.view.provider_module()
        for builder in sorted(self.constructions):
            row = self.constructions[builder]
            for consumer in row["consumers"]:
                if consumer == self.module:
                    self.add("RC014", f"{builder}: the builder module does not consume itself")
                elif builder not in self.view.edge(consumer, self.module):
                    self.add("RC014", f"{builder}: imports.module_internal.{consumer}.{self.module} lacks {builder}")
            for ref in _all_refs(row):
                if ref["ref"] == "constant" and provider is not None:
                    if ref["symbol"] not in self.view.edge(self.module, provider):
                        self.add("RC014", f"{builder}: imports.module_internal.{self.module}.{provider} "
                                          f"lacks {ref['symbol']}")
                if ref["ref"] == "call" and ref["function"] not in self.constructions:
                    for owner in self.view.owner.get(ref["function"], []):
                        if owner in row["consumers"]:
                            self.add("RC014", f"{builder}: {ref['function']} belongs to consumer {owner}; "
                                              f"the import graph would cycle")
                        elif owner != self.module and ref["function"] not in self.view.edge(self.module, owner):
                            self.add("RC014", f"{builder}: imports.module_internal.{self.module}.{owner} "
                                              f"lacks {ref['function']}")


def _all_refs(row: dict[str, Any]):
    """Every ref of a construction row: over, fields, parts (over and fields)."""
    if row.get("over") is not None:
        yield row["over"]
    yield from row["fields"].values()
    for part_row in row.get("parts", {}).values():
        if part_row["over"] is not None:
            yield part_row["over"]
        yield from part_row["fields"].values()


class _Builder:
    """The per-builder checks: sources, disposal, types, references, parts."""

    def __init__(self, closure: _Closure, builder: str) -> None:
        self.closure = closure
        self.view = closure.view
        self.builder = builder
        self.row = closure.constructions[builder]
        parameters, self.returns = closure.contracts[builder]
        self.parameters = dict(parameters)
        self.used_names: set[str] = set()
        # model-typed names (parameters and elements) -> fields read
        self.read: dict[str, set[str]] = {}
        self.model_names: dict[str, str] = {}
        for name, annotation in parameters:
            if self.view.record_fields(annotation) is not None:
                self.model_names[name] = annotation
        self.part_types: dict[str, str] = {}
        self.part_edges: dict[str, set[str]] = {part: set() for part in self.row["parts"]}
        self.used_parts: set[str] = set()

    def add(self, code: str, message: str) -> None:
        self.closure.add(code, f"{self.builder}: {message}")

    def run(self) -> None:
        row = self.row
        target_fields = self.view.record_fields(row["target"])
        if target_fields is None:
            self.add("RC009", f"target {row['target']} is not a declared record model")
            return
        self._contract(target_fields)
        scope = dict(self.parameters)
        if row["over"] is not None:
            element_type = self._over(row["over"], scope, "over", owner=None)
            if element_type is not None:
                scope[row["element"]] = element_type
                if self.view.record_fields(element_type) is not None:
                    self.model_names[row["element"]] = element_type
        if row["form"] == "replace" and isinstance(row["base"], str):
            self.used_names.add(row["base"])
            if row["base"] in self.model_names:
                self.read.setdefault(row["base"], set()).update(self.view.record_fields(self.model_names[row["base"]]))
        for part, part_row in row["parts"].items():
            part_target = self.view.record_fields(part_row["target"])
            if part_target is None:
                self.add("RC009", f"part {part}: target {part_row['target']} is not a declared record model")
                continue
            self.part_types[part] = (
                f"list[{part_row['target']}]" if part_row["over"] is not None else part_row["target"]
            )
        for part, part_row in row["parts"].items():
            if part not in self.part_types:
                continue
            part_scope = dict(scope)
            if part_row["over"] is not None:
                element_type = self._over(part_row["over"], scope, f"parts.{part}.over", owner=part)
                if element_type is not None:
                    part_scope[part_row["element"]] = element_type
                    if self.view.record_fields(element_type) is not None:
                        self.model_names[part_row["element"]] = element_type
            self._fields(part_row["fields"], self.view.record_fields(part_row["target"]), part_scope,
                         f"parts.{part}", "construct", part_row["target"], owner=part)
        self._fields(row["fields"], target_fields, scope, "fields", row["form"], row["target"], owner=None)
        self._names_used()
        self._disposal()
        self._parts()

    # RC011
    def _contract(self, target_fields: dict[str, str]) -> None:
        row = self.row
        expected = f"list[{row['target']}]" if row["over"] is not None else row["target"]
        if canonical_type(self.returns) != expected:
            self.add("RC011", f"contracts.{self.builder} returns {self.returns}; the construction returns {expected}")
        if row["form"] == "replace" and isinstance(row["base"], str):
            if canonical_type(self.parameters.get(row["base"], "")) != row["target"]:
                self.add("RC011", f"base {row['base']} must be a parameter of type {row['target']}")
        unknown = set()
        for annotation in [*self.parameters.values(), self.returns]:
            for name in type_names(annotation):
                if name not in BUILTIN_TYPE_NAMES and name not in STDLIB_TYPE_SOURCES and self.view.model(name) is None:
                    unknown.add(name)
        if unknown:
            self.add("RC011", f"contracts.{self.builder} names undeclared types {sorted(unknown)}")
        if row["form"] == "replace" and row["base"] is not None:
            for field, ref in row["fields"].items():
                if ref == {"ref": "field", "of": row["base"], "field": field}:
                    self.add("RC003", f"fields.{field} repeats base.{field}: the base is its one source")

    def _over(self, ref: dict[str, Any], scope: dict[str, str], where: str, owner: str | None) -> str | None:
        source = self._source_type(ref, scope, where, owner)
        if source is None:
            return None
        element = collection_element(source)
        if element is None:
            self.add("RC008", f"{where}: {source} is not a list or tuple collection")
        return element

    def _fields(self, fields: dict[str, Any], target_fields: dict[str, str], scope: dict[str, str], where: str,
                form: str, target: str, owner: str | None) -> None:
        for field in fields:
            if field not in target_fields:
                self.add("RC004", f"{where}.{field}: {target} declares no field {field}")
        if form == "construct":
            missing = [field for field in target_fields if field not in fields]
            if missing:
                self.add("RC002", f"{where}: {target} fields without a source: {missing}")
        for field, ref in fields.items():
            if field not in target_fields:
                continue
            source = self._source_type(ref, scope, f"{where}.{field}", owner)
            if source is not None and not self._assignable(ref, source, target_fields[field]):
                self.add("RC008", f"{where}.{field}: {self._describe(ref)} of type {source} "
                                  f"does not fit {target}.{field}: {target_fields[field]}")

    def _assignable(self, ref: dict[str, Any], source: str, target: str) -> bool:
        kind = ref["ref"]
        if kind == "none":
            return is_nullable(target)
        if kind == "empty":
            return collection_element(target) is not None
        if ref.get("convert") == "enum_by_value":
            enum = non_null(target)
            model = self.view.model(enum) or {}
            return (
                self.view.is_enum(enum) and model.get("base", "str") == "str"
                and (is_nullable(target) or not is_nullable(source))
            )
        if kind == "part" and source.startswith("list["):
            element = collection_element(source)
            return collection_element(non_null(target)) == element and collection_kind(non_null(target)) is not None
        return assignable(source, target)

    @staticmethod
    def _describe(ref: dict[str, Any]) -> str:
        return json.dumps(ref, sort_keys=True)

    def _source_type(self, ref: dict[str, Any], scope: dict[str, str], where: str, owner: str | None) -> str | None:
        """The type a ref yields, or None after a finding (or for none/empty, whose fit is checked apart)."""
        kind = ref["ref"]
        if kind == "name":
            if ref["name"] not in scope:
                self.add("RC009", f"{where}: no name {ref['name']} here")
                return None
            self._use_name(ref["name"], whole=True)
            return self._convert(ref, scope[ref["name"]], where)
        if kind == "field":
            if "." in ref["field"] or "." in ref["of"]:
                self.add("RC009", f"{where}: a field ref reads exactly one level")
                return None
            if ref["of"] not in scope:
                self.add("RC009", f"{where}: no name {ref['of']} here")
                return None
            fields = self.view.record_fields(scope[ref["of"]])
            self.used_names.add(ref["of"])
            if fields is None or ref["field"] not in fields:
                self.add("RC009", f"{where}: {scope[ref['of']]} has no field {ref['field']}")
                return None
            self.read.setdefault(ref["of"], set()).add(ref["field"])
            return self._convert(ref, fields[ref["field"]], where)
        if kind in ("part", "part_field"):
            part = ref["name"] if kind == "part" else ref["part"]
            if part not in self.row["parts"]:
                self.add("RC009", f"{where}: no part {part}")
                return None
            self.used_parts.add(part)
            if owner is not None:
                self.part_edges[owner].add(part)
            if part not in self.part_types:
                return None
            if kind == "part":
                return self.part_types[part]
            if self.row["parts"][part]["over"] is not None:
                self.add("RC015", f"{where}: part {part} is a collection; its fields are not visible outside it")
                return None
            fields = self.view.record_fields(self.row["parts"][part]["target"]) or {}
            if "." in ref["field"] or ref["field"] not in fields:
                self.add("RC009", f"{where}: part {part} has no field {ref['field']}")
                return None
            return self._convert(ref, fields[ref["field"]], where)
        if kind == "call":
            return self._call(ref, scope, where)
        if kind == "fresh_id":
            return "UUID"
        if kind == "constant":
            if self.view.provider is None:
                self.add("RC009", f"{where}: constant {ref['symbol']} without rules.data_provider_backend")
                return None
            access = self.view.provider_constant_type(ref["symbol"])
            if access is None:
                self.add("RC009", f"{where}: rules.data_provider_backend declares no constant {ref['symbol']}")
                return None
            return access
        if kind == "enum":
            if not self.view.is_enum(ref["type"]):
                self.add("RC009", f"{where}: {ref['type']} is not a declared enum")
                return None
            if ref["member"] not in self.view.enum_members(ref["type"]):
                self.add("RC009", f"{where}: {ref['type']} has no member {ref['member']}")
                return None
            return ref["type"]
        if kind == "literal":
            return "bool"
        return "None" if kind == "none" else "list[None]"  # none / empty: fit checked in _assignable

    def _use_name(self, name: str, whole: bool) -> None:
        self.used_names.add(name)
        if whole and name in self.model_names:
            self.read.setdefault(name, set()).update(self.view.record_fields(self.model_names[name]) or {})

    def _convert(self, ref: dict[str, Any], source: str, where: str) -> str | None:
        conversion = ref.get("convert")
        if conversion is None:
            return source
        nullable, base = is_nullable(source), non_null(source)
        if conversion == "is_present":
            if not nullable:
                self.add("RC008", f"{where}: is_present reads a nullable source; {source} is not")
                return None
            return "bool"
        if conversion == "uuid_canonical_string":
            if base != "UUID":
                self.add("RC008", f"{where}: uuid_canonical_string reads a UUID; got {source}")
                return None
            result = "str"
        elif conversion == "naive_utc":
            if base != "datetime":
                self.add("RC008", f"{where}: naive_utc reads a datetime; got {source}")
                return None
            result = "datetime"
        else:  # enum_by_value: the enum is the one the target field names
            if base != "str":
                self.add("RC008", f"{where}: enum_by_value reads a str; got {source}")
                return None
            result = "str"  # the enum is the target field's; _assignable checks it
        return nullable_of(result) if nullable else result

    def _call(self, ref: dict[str, Any], scope: dict[str, str], where: str) -> str | None:
        function = ref["function"]
        contract = parse_contract(self.view.contracts.get(function))
        if function not in self.view.contracts:
            self.add("RC009", f"{where}: no contract {function}")
            return None
        for name in ref["args"]:
            if name not in scope:
                self.add("RC009", f"{where}: no name {name} here")
                return None
            self._use_name(name, whole=True)
        if contract is None:
            self.add("RC010", f"{where}: contracts.{function} is not a plain function contract")
            return None
        parameters, returns = contract
        problems = []
        if function.startswith("_"):
            problems.append("is private")
        builder_callee = function in self.closure.constructions
        if not builder_callee:
            if self.view.determinism.get(function) is not True:
                problems.append("is not determinism: true")
            owners = self.view.owner.get(function, [])
            if not owners:
                problems.append("has no owning module")
            if self.closure.module in owners:
                problems.append("belongs to the builder module but is not a builder")
            if set(owners) & set(self.row["consumers"]):
                problems.append("belongs to a consumer of this builder")
        if any(self.view.is_interface(non_null(annotation)) for _name, annotation in parameters):
            problems.append("takes a port")
        if len(parameters) != len(ref["args"]):
            problems.append(f"takes {len(parameters)} arguments, not {len(ref['args'])}")
        else:
            for name, (parameter, annotation) in zip(ref["args"], parameters):
                if not assignable(canonical_type(scope[name]), canonical_type(annotation)):
                    problems.append(f"parameter {parameter}: {annotation} does not take {name}: {scope[name]}")
        if problems:
            self.add("RC010", f"{where}: call {function} " + "; ".join(problems))
            return None
        return canonical_type(returns)

    # RC007
    def _names_used(self) -> None:
        for name in self.parameters:
            if name not in self.used_names:
                self.add("RC007", f"parameter {name} is used by no ref")

    # RC005, RC006
    def _disposal(self) -> None:
        dropped = self.row["dropped"]
        for name in sorted(dropped):
            if name not in self.model_names:
                self.add("RC006", f"dropped.{name}: {name} is not a model-typed name of this builder")
                continue
            fields = self.view.record_fields(self.model_names[name]) or {}
            for field in sorted(dropped[name]):
                if field not in fields:
                    self.add("RC006", f"dropped.{name}.{field}: {self.model_names[name]} has no field {field}")
                elif field in self.read.get(name, set()):
                    self.add("RC006", f"dropped.{name}.{field}: the field is read and dropped")
        for name, model in sorted(self.model_names.items()):
            fields = self.view.record_fields(model) or {}
            disposed = self.read.get(name, set()) | set(dropped.get(name, {}))
            missing = [field for field in fields if field not in disposed]
            if missing:
                self.add("RC005", f"{name}: {model} fields neither read nor dropped: {missing}")

    # RC015
    def _parts(self) -> None:
        for part in self.row["parts"]:
            if part not in self.used_parts:
                self.add("RC015", f"part {part} is used by no ref")
        state: dict[str, int] = {}

        def visit(part: str, trail: list[str]) -> None:
            state[part] = 1
            for other in sorted(self.part_edges.get(part, ())):
                if state.get(other) == 1:
                    self.add("RC015", f"parts form a cycle: {' -> '.join([*trail, other])}")
                elif other not in state:
                    visit(other, [*trail, other])
            state[part] = 2

        for part in sorted(self.row["parts"]):
            if part not in state:
                visit(part, [part])



def finding_codes(spec: dict[str, Any]) -> list[str]:
    """The distinct RC codes the closure finds, sorted (the fixture parity surface)."""
    return sorted({code for code, _message in closure_findings(spec)})



# --- the case ------------------------------------------------------------------------------------

# RC014 reads imports.module_internal, which the imports closure (65_imports.json,
# after State 7) authors. Before that table exists the State 6 gate reports the
# edge findings as carried, not blocking; once it exists they block like any other.
CARRIED_UNTIL_IMPORTS = frozenset({"RC014"})


def load_closure(project: Path) -> dict[str, Any]:
    """The closure file, parsed refusing a repeated key (RC003)."""
    path = project / CLOSURE_FILE
    closure = load_json(path)
    if closure.get("schema_version") != CLOSURE_SCHEMA:
        raise ClosureDefect(f"{CLOSURE_FILE}: schema_version must be {CLOSURE_SCHEMA}")
    for key in ("status", "source_refs", "rationale", "backend_ir"):
        if key not in closure:
            raise ClosureDefect(f"{CLOSURE_FILE}: {key} is required")
    if closure["status"] not in ("open", "closed"):
        raise ClosureDefect(f"{CLOSURE_FILE}: status must be open or closed")
    if not isinstance(closure["backend_ir"], dict):
        raise ClosureDefect(f"{CLOSURE_FILE}: backend_ir must be an object")
    return closure


def case_view(project: Path, backend_ir: dict[str, Any]) -> dict[str, Any]:
    """The projected specification of the case with the authored IR in its rules."""
    from spec_projection_workbench.service import projected_spec

    spec = projected_spec(project)
    rules = dict(spec.get("rules") or {}) if isinstance(spec.get("rules"), dict) else {}
    rules[RULE_KEY] = backend_ir
    return {**spec, "rules": rules}


def _report(findings: list[tuple[str, str]], carried: frozenset[str], closure_status: str | None) -> dict[str, Any]:
    rows = [
        {"code": code, "name": CODES[code], "message": message,
         "severity": "carried" if code in carried else "block"}
        for code, message in findings
    ]
    blocks = sum(row["severity"] == "block" for row in rows)
    return {
        "schema_version": "spec_workbench_record_construction_coverage.v1",
        "summary": {
            "findings": len(rows),
            "blocks": blocks,
            "carried": len(rows) - blocks,
            "closure_status": closure_status,
            "handoff_ready": blocks == 0 and closure_status in (None, "closed"),
        },
        "findings": rows,
    }


def coverage(project: Path) -> dict[str, Any]:
    """The State 6 phase gate; a case without the closure file does not use the backend."""
    project = Path(project)
    if not (project / CLOSURE_FILE).is_file():
        report = _report([], frozenset(), None)
        report["summary"]["enabled"] = False
        return report
    try:
        closure = load_closure(project)
    except ClosureDefect as exc:
        text = str(exc)
        code = "RC003" if text.startswith("RC003") else "RC001"
        report = _report([(code, text)], frozenset(), "invalid")
        report["summary"]["enabled"] = True
        return report
    findings = closure_findings(case_view(project, closure["backend_ir"]))
    carried = frozenset() if (project / IMPORTS_FILE).is_file() else CARRIED_UNTIL_IMPORTS
    report = _report(findings, carried, closure["status"])
    report["summary"]["enabled"] = True
    return report


def spec_report(path: Path) -> dict[str, Any]:
    """Every finding of one spec-shaped JSON (a fixture, an assembled global_spec.json)."""
    try:
        spec = load_json(path)
    except ClosureDefect as exc:
        text = str(exc)
        return _report([("RC003" if text.startswith("RC003") else "RC001", text)], frozenset(), None)
    return _report(closure_findings(spec), frozenset(), None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", type=Path, nargs="?")
    parser.add_argument("--coverage", action="store_true", help="the State 6 phase gate on the case")
    parser.add_argument("--spec", type=Path, help="check one spec-shaped JSON instead of a case")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if (args.spec is None) == (args.project is None):
        parser.error("give a case directory with --coverage, or --spec <file>")
    if args.spec is not None:
        report = spec_report(args.spec)
    else:
        report = coverage(args.project)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        summary = report["summary"]
        print(f"record construction: findings={summary['findings']} blocks={summary['blocks']} "
              f"carried={summary['carried']} handoff_ready={summary['handoff_ready']}")
        for row in report["findings"]:
            print(f"  {row['severity']}: {row['code']} {row['name']}: {row['message']}")
    return 0 if report["summary"]["blocks"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
