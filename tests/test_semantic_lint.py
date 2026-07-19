"""Unit tests for semantic_lint.py (S1–S10, global notes, internal imports).

Run:  python3 -m pytest test_semantic_lint.py -q
"""
from __future__ import annotations

import copy

from semantic_lint import lint, resolve_ref, imported_symbols

# ---------------------------------------------------------------- fixtures

BASE = {
    "contracts": {},
    "notes": [],
    "adapters": {},
    "config": {},
    "models": {},
    "rules": {},
    "imports": {"stdlib": [], "third_party": [], "internal": {}},
    "module_functions": {},
    "module_order": [],
    "function_order": [],
    "module_hints": {},
    "module_paths": {},
    "default_module": "core",
}


def spec(**over):
    s = copy.deepcopy(BASE)
    s.update(over)
    return s


def msgs(result, prefix):
    return [m for m in result["errors"] + result["warnings"]
            if m.startswith(prefix)]


# ---------------------------------------------------------------- S1

def test_s1_flags_undefined_type():
    r = lint(spec(contracts={"f": "(x: MysteryType) -> None"}))
    assert any("MysteryType" in m for m in msgs(r, "S1"))


def test_s1_accepts_model_type():
    r = lint(spec(contracts={"f": "(x: Foo) -> None"},
                  models={"Foo": {"fields": {}}}))
    assert not msgs(r, "S1")


def test_s1_accepts_internal_import():
    """Reviewer's point: imports.internal must count as an owner."""
    s = spec(contracts={"f": "(x: Bar) -> None"})
    s["imports"]["internal"] = {"models": ["Bar"]}
    assert not msgs(lint(s), "S1")


def test_s1_accepts_third_party_import():
    s = spec(contracts={"f": "(e: Engine) -> None"})
    s["imports"]["third_party"] = ["from sqlalchemy import Engine"]
    assert not msgs(lint(s), "S1")


# ---------------------------------------------------------------- S2

def test_s2_flags_undeclared_exception():
    r = lint(spec(contracts={"f": "() -> None"},
                  notes=["f: [VALIDATION_ERROR] MUST raise GhostError on bad input"]))
    assert any("GhostError" in m for m in msgs(r, "S2"))


def test_s2_accepts_declared_exception():
    s = spec(contracts={"f": "() -> None"},
             notes=["f: [VALIDATION_ERROR] MUST raise KnownError on bad input"])
    s["imports"]["internal"] = {"domain_errors": ["KnownError"]}
    assert not msgs(lint(s), "S2")


def test_s2_checks_global_notes():
    """Reviewer's point: global notes must be parsed too."""
    r = lint(spec(notes=["[VALIDATION_ERROR] all handlers MUST raise PhantomError"]))
    assert any("PhantomError" in m and "global" in m for m in msgs(r, "S2"))


# ---------------------------------------------------------------- S3

def test_s3_flags_dangling_reference():
    r = lint(spec(contracts={"f": "() -> None"},
                  notes=["f: [RULE_REFERENCE] MUST enforce = rules.nonexistent_rule"]))
    assert msgs(r, "S3")


def test_s3_accepts_valid_reference():
    r = lint(spec(contracts={"f": "() -> None"},
                  rules={"limits": {"max": 5}},
                  notes=["f: [RULE_REFERENCE] MUST enforce = rules.limits.max"]))
    assert not msgs(r, "S3")


def test_s3_grammar_wildcard_and_key():
    """Reviewer's point: support a.rows[*].tokens and a['key']."""
    root = {"rows": [{"tokens": [1, 2]}], "map": {"k": {"v": 1}}}
    assert resolve_ref(root, "rows[*].tokens")
    assert resolve_ref(root, 'map["k"].v')
    assert not resolve_ref(root, "rows[*].missing")


def test_s3_checks_global_notes():
    r = lint(spec(notes=["[CONFIG_REFERENCE] timeouts come from = config.ghost.timeout"]))
    assert any("global" in m for m in msgs(r, "S3"))


# ---------------------------------------------------------------- S4 / S5

def test_s4_vague_language():
    r = lint(spec(contracts={"f": "() -> None"},
                  notes=["f: [BEHAVIOR] MUST handle errors properly"]))
    assert msgs(r, "S4")


def test_s5_name_restating_note():
    r = lint(spec(contracts={"save_result": "() -> None"},
                  notes=["save_result: [BEHAVIOR] MUST save the result"]))
    assert msgs(r, "S5")


# ---------------------------------------------------------------- S6

def test_s6_generic_contract_type():
    r = lint(spec(contracts={"f": "() -> dict[str, object]"}))
    assert msgs(r, "S6")


def test_s6_generic_model_field():
    r = lint(spec(models={"M": {"fields": {"payload": "Any"}}}))
    assert msgs(r, "S6")


# ---------------------------------------------------------------- S7

def test_s7_no_notes_at_all():
    r = lint(spec(contracts={"f": "() -> None"}))
    assert any("return None" in m for m in msgs(r, "S7"))


def test_s7_producer_without_shape():
    r = lint(spec(contracts={"build_report": "() -> Report"},
                  models={"Report": {"fields": {}}},
                  notes=["build_report: [SECURITY_BOUNDARY] MUST authorize report.read"]))
    assert any("build_report" in m for m in msgs(r, "S7"))


# ---------------------------------------------------------------- S8

def _layout_spec(note_bodies):
    return spec(
        contracts={"normalize_layout": "(layout: Layout) -> Layout"},
        models={"Layout": {"fields": {}}},
        notes=[f"normalize_layout: {b}" for b in note_bodies])


def test_s8_catches_underspecified_normalize():
    """The reviewer's key case: 'MUST normalize rotation' passes S4/S5/S7
    but an identity implementation satisfies it."""
    r = lint(_layout_spec(
        ["[BEHAVIOR] MUST normalize rotation and presentation values "
         "without changing engineering structure"]))
    assert msgs(r, "S8")


def test_s8_passes_concrete_normalize():
    r = lint(_layout_spec([
        "[FIELD_ASSIGNMENT] MUST replace every rotation_degrees value with "
        "its equivalent in {0, 90, 180, 270} using modulo 360",
        "[FORBIDDEN_ACTION] MUST NOT create or remove layout entries and "
        "MUST preserve element ids and route_points"]))
    assert not msgs(r, "S8")


def test_s8_validate_needs_failure_semantics():
    r = lint(spec(contracts={"validate_input": "(x: Foo) -> Foo"},
                  models={"Foo": {"fields": {}}},
                  notes=["validate_input: [BEHAVIOR] MUST check the input "
                         "against catalog"]))
    assert msgs(r, "S8")


def test_s8_resolve_needs_precedence_or_failure():
    r = lint(spec(contracts={"resolve_thing": "(x: Foo) -> Foo"},
                  models={"Foo": {"fields": {}}},
                  notes=["resolve_thing: [BEHAVIOR] MUST combine catalog and "
                         "overrides into one snapshot"]))
    assert msgs(r, "S8")


# ---------------------------------------------------------------- S9

def test_s9_flags_non_profile_models_path():
    s = spec(models={"Item": {"fields": {"code": "str"}}})
    s["module_functions"] = {"models": ["Item"]}
    s["module_paths"] = {"models": "domain/models/__init__"}
    assert msgs(lint(s), "S9")


def test_s9_accepts_current_factory_models_path():
    s = spec(models={"Item": {"fields": {"code": "str"}}})
    s["module_functions"] = {"models": ["Item"]}
    s["module_paths"] = {"models": "core/models"}
    assert not msgs(lint(s), "S9")


# ---------------------------------------------------------------- S10

def _ledger(*invariants):
    return {"schema_version": 1, "invariants": list(invariants)}


def test_s10_flags_invariant_without_landing():
    s = spec(contracts={"validate_input": "(x: int) -> list[str]"})
    ledger = _ledger({
        "id": "INV-001",
        "statement": "invalid input produces at least one issue",
        "owner_function": "validate_input",
    })
    r = lint(s, ledger)
    assert any("no landing" in m for m in msgs(r, "S10"))
    assert r["invariant_coverage"]["INV-001"]["status"] == "uncovered"


def test_s10_rejects_unknown_ledger_schema_version():
    r = lint(spec(), {"schema_version": 2, "invariants": []})
    assert any("schema_version" in m for m in msgs(r, "S10"))


def test_s10_accepts_rules_landing():
    s = spec(
        contracts={"transition": "(state: str) -> str"},
        rules={"state_transitions": {"draft": ["active"]}},
    )
    ledger = _ledger({
        "id": "INV-001",
        "statement": "only declared state transitions are valid",
        "owner_function": "transition",
        "landing": {"kind": "rules", "path": "state_transitions"},
    })
    assert not msgs(lint(s, ledger), "S10")


def test_s10_accepts_exact_note_landing():
    note = "validate_input: [VALIDATION_ERROR] MUST report every negative value"
    s = spec(
        contracts={"validate_input": "(x: int) -> list[str]"},
        notes=[note],
    )
    ledger = _ledger({
        "id": "INV-001",
        "statement": "negative values are invalid",
        "owner_function": "validate_input",
        "landing": {"kind": "note", "text": note},
    })
    assert not msgs(lint(s, ledger), "S10")


def test_s10_accepts_exact_property_landing():
    expression = "x < 0 implies len(result) >= 1"
    s = spec(
        contracts={"validate_input": "(x: int) -> list[str]"},
        properties={"validate_input": [expression]},
    )
    ledger = _ledger({
        "id": "INV-001",
        "statement": "negative values produce at least one issue",
        "owner_function": "validate_input",
        "landing": {"kind": "property", "expression": expression},
    })
    assert not msgs(lint(s, ledger), "S10")


def test_s10_flags_property_on_the_wrong_owner():
    expression = "result >= x"
    s = spec(
        contracts={"normalize": "(x: int) -> int", "other": "(x: int) -> int"},
        properties={"other": [expression]},
    )
    ledger = _ledger({
        "id": "INV-001",
        "statement": "normalization never decreases the value",
        "owner_function": "normalize",
        "landing": {"kind": "property", "expression": expression},
    })
    assert msgs(lint(s, ledger), "S10")


# ---------------------------------------------------------------- imports

def test_imported_symbols_reads_all_sections():
    s = spec()
    s["imports"] = {
        "stdlib": ["from datetime import datetime", "import json"],
        "third_party": ["from pydantic import BaseModel, Field"],
        "internal": {"models": ["Diagram"], "catalog": ["resolve_catalog"]},
    }
    syms = imported_symbols(s)
    assert {"datetime", "json", "BaseModel", "Field",
            "Diagram", "resolve_catalog"} <= syms
