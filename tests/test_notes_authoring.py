"""The deterministic half of the State 7 notes-writing environment
(tools/DATA_CLOSURE_WORKBENCH.md §4, §6, §10): M2, M3, M4, M6 and lint L2–L5."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from notes_authoring import binding
from notes_authoring.index import SpecIndex
from notes_authoring.lint import lint
from notes_authoring.signals import detect
from notes_workbench import language

FIXTURE = Path(__file__).parent / "fixtures" / "notes_authoring" / "cabinet_kernel_b3bee2e"


@pytest.fixture(scope="module")
def kernel() -> dict:
    notes = language.authored_notes(FIXTURE)
    surface = json.loads((FIXTURE / "surface.json").read_text(encoding="utf-8"))
    return lint(notes, surface)


def at(report: dict, line: int) -> list[dict]:
    return [f for f in report["findings"] if f["line"] == line]


def codes(report: dict, line: int) -> set[str]:
    return {f"{f['rule']}:{f['signal'] if f['rule'] == 'L3' else f['code']}" for f in at(report, line)}


# ── §10 regressions on Cabinet Kernel @ b3bee2e ──────────────────────────

def test_every_note_binds_to_a_module(kernel):
    assert kernel["summary"]["notes"] == 507
    assert not [f for f in kernel["findings"] if f["code"] == "note_unbound"]


def test_10_2_store_page_records_enumerates_record_types(kernel):
    # :145 lists RecordType members without = models.RecordType; :595 is the pair table
    record_types = set(json.loads((FIXTURE / "surface.json").read_text(encoding="utf-8"))["models"]["RecordType"]["values"])
    listed = [f for f in at(kernel, 145) if f["rule"] == "L3" and f["signal"] in ("list", "enum_members")]
    assert any(len(set(f["items"]) & record_types) >= 3 for f in listed)
    # §10.2: L3 must fire on the enumeration of list_*_rows methods
    methods = [f for f in at(kernel, 145) if f["rule"] == "L3" and f["signal"] == "mapping"]
    assert any({"list_slot_rows", "list_run_rows"} <= set(f["items"]) for f in methods)
    assert {"L3:list", "L3:enum_members"} <= codes(kernel, 595)


def test_10_3_runner_message_kinds_block_and_report_fields_do_not(kernel):
    kinds = [f for f in at(kernel, 212) if f["rule"] == "L3" and f["signal"] == "list"]
    assert any({"trap", "resource", "crashed", "returned"} <= set(f["items"]) for f in kinds)
    assert not [f for f in at(kernel, 213) if f["rule"] == "L2"]


def test_10_4_surface_actor_table_handler_registry_design_order_and_codes(kernel):
    assert "L3:list" in codes(kernel, 481)
    handlers = [f for f in at(kernel, 484) if f["rule"] == "L3" and f["signal"] == "list"]
    assert any(len(f["items"]) >= 30 for f in handlers)
    assert any(f["signal"] == "design_reference" and f["value"] == "State 5" for f in at(kernel, 487))
    assert {f["value"] for f in at(kernel, 490) if f["signal"] == "number"} >= {"-32600", "-32700", "-32601"}


def test_10_4_imported_constants_are_never_signals(kernel):
    # :482 names five RELEASE_CEILING_* constants: none of them is a finding.
    # (The note also cites "A16 rules 4 and 6" and "below 1"; the contract
    # §10.4 calls the line clean, these numbers are flagged — see the PR.)
    values = {f.get("value") for f in at(kernel, 482)}
    assert not any("RELEASE_CEILING" in str(v) for v in values)
    assert values <= {"1", "4", "6"}
    assert {f["rule"] for f in at(kernel, 482)} <= {"L2", "L3"}


def test_10_5_sort_keys_are_field_names_and_their_copies_agree(kernel):
    for line in (114, 135):
        assert not [f for f in at(kernel, line) if f["rule"] == "L3"]
    shared = [f for f in kernel["findings"] if f["code"] == "shared_prose" and {f["line"], int(f["other"].split(":")[1].split()[0])} == {114, 135}]
    assert shared and all(f["severity"] == "report" for f in shared)
    assert not [f for f in kernel["findings"] if f["code"] == "diverged_copies"]


def test_10_6_negative_examples(kernel):
    assert at(kernel, 109) == []
    assert [f["code"] for f in at(kernel, 125)] == ["addressed_enumeration_restated"]


def test_l4_blocks_the_restated_list_f3_and_not_the_algorithm_f4(kernel):
    # research Q9 §2.2: :125 is F3 (members with nothing between them);
    # :226 and :159 are F4 (a condition behind every member) — prose
    assert [f["line"] for f in kernel["findings"] if f["rule"] == "L4"] == [125]


def test_a_grouped_number_is_one_literal_with_its_home(kernel):
    found = [f for f in at(kernel, 220) if f.get("value") == "1048576"]
    assert found and found[0]["rule"] == "L2"
    assert any("RELEASE_CEILING" in home for home in found[0]["homes"])
    assert not [f for f in at(kernel, 220) if f.get("value") in ("048", "576")]


def test_a_list_in_parentheses_is_one_signal(kernel):
    for line in (113, 169):
        lists = [tuple(f["items"]) for f in at(kernel, line) if f.get("signal") == "list"]
        assert len(lists) == len(set(lists))


def test_deterministic_modules_are_bound_but_unfound(kernel):
    # models (StoreRepository), store_persistence, clock, data_provider: present, 0 blocks
    for module in ("models", "store_persistence", "clock", "data_provider"):
        assert kernel["modules"][module]["blocks"] == 0


# ── M3 ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "MUST hash with sha256 under the UTF-8 encoding and SHA-256 digest",
    "MUST read = rules.x.limit_30 and the imported LIMIT_30 constant",
    "it reads no file, no clock, no environment and no store",
    "MUST read and/or write the value",
])
def test_m3_finds_no_signal_in_names_encodings_addresses_and_prose(text):
    assert detect(text) == []


@pytest.mark.parametrize("text, kind, value", [
    ("MUST wait 30 seconds", "number", "30"),
    ("answers -32600 on a bad body", "number", "-32600"),
    ('MUST write "application/json"', "quoted", "application/json"),
    ("MUST read /proc/self/status", "path", "/proc/self/status"),
    ("keeps it under ~/.codex/auth.json", "path", "~/.codex/auth.json"),
    ("in State 5 catalogue order", "design_reference", "State 5"),
    ("as 50_public_apis.md says", "design_reference", "50_public_apis.md"),
    ("open → closed", "arrow", "→"),
])
def test_m3_signals(text, kind, value):
    assert (kind, value) in {(s.kind, s.text) for s in detect(text)}


def test_m3_a_list_needs_identifier_like_items():
    assert [s.items for s in detect("one of slot_id, run_id or flow_id") if s.kind == "list"] == [
        ("slot_id", "run_id", "flow_id")
    ]
    assert not [s for s in detect("a trap, a resource or a crash") if s.kind == "list"]


def test_m_e1_field_names_do_not_count_and_m_e5_shared_members_need_their_enum():
    enums = {"Part": ("nodes", "edges", "constants"), "Outcome": ("ok", "lost", "late"), "Other": ("ok", "lost", "late")}
    assert not [s for s in detect("flow nodes, edges and constants", enums, field_names=frozenset({"nodes"})) if s.kind == "enum_members"]
    assert [s.enum for s in detect("flow nodes, edges and constants", enums) if s.kind == "enum_members"] == ["Part"]
    # members of two enums count only for the one the note names
    assert not [s for s in detect("ok, lost or late", enums) if s.kind == "enum_members"]
    assert [s.enum for s in detect("an Outcome: ok, lost or late", enums) if s.kind == "enum_members"] == ["Outcome"]


# ── M2, M4 ────────────────────────────────────────────────────────────────

SPEC = {
    "models": {"Status": {"kind": "enum", "values": ["open", "closed"]}, "Row": {"fields": {"row_id": "str"}}},
    "rules": {
        "data_provider_backend": {"kind": "data_provider_backend", "constants": {"PAGE_MAX": {"value": 200}}},
        "time_source_policy": {"kind": "time_source_policy", "samples_per_read": 1},
    },
    "config": {"persistence": {"row_table_name": "rows"}},
    "contracts": {"Store.load": "(self) -> Row"},
    "module_functions": {"store": ["Store", "load_rows"], "models": ["Row"]},
}


def test_m2_homes_and_the_homes_that_reach_code():
    index = SpecIndex.build(SPEC)
    assert index.homes("200") == ["the imported PAGE_MAX constant"]
    assert index.homes("open") == ["= models.Status"]
    assert index.homes("1") == ["rules.time_source_policy.samples_per_read"]
    assert index.homes("1", reaching_code=True) == []
    assert index.homes("rows") == ["config.persistence.row_table_name"]


def test_m4_absence_names_matches_and_namespace_digests():
    index = SpecIndex.build(SPEC)
    report = index.absence(["timeout", "page"])
    assert report["terms"]["timeout"] == []
    assert "rules.data_provider_backend.constants.PAGE_MAX" in report["terms"]["page"]
    digest = hashlib.sha256(json.dumps(SPEC["models"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert report["namespaces"]["models"] == digest


# ── M6 ────────────────────────────────────────────────────────────────────

def test_m6_binds_functions_methods_by_their_class_and_modules():
    notes = [{"scope": s, "line": i} for i, s in enumerate(["load_rows", "Store.load", "store", "nowhere"])]
    by_module, unbound = binding.bind(notes, SPEC)
    assert [n["scope"] for n in by_module["store"]] == ["load_rows", "Store.load", "store"]
    assert by_module["models"] == [] and [n["scope"] for n in unbound] == ["nowhere"]


# ── L2, L4, L5 on small inputs ────────────────────────────────────────────

def _note(scope: str, text: str, line: int = 1) -> dict:
    return {"path": "80_notes.md", "line": line, "scope": scope, "class": "BEHAVIOR", "text": text}


def test_l2_names_the_home_of_a_literal_that_reaches_code():
    report = lint([_note("load_rows", "MUST return at most 200 rows")], SPEC)
    assert [(f["rule"], f["homes"]) for f in report["findings"]] == [("L2", ["the imported PAGE_MAX constant"])]


def test_l4_claimed_order_must_be_the_declared_one():
    spec = {**SPEC, "models": {**SPEC["models"], "Phase": {"kind": "enum", "values": ["first", "second", "third"]}}}
    good = lint([_note("load_rows", "checks in this order of = models.Phase: first when a, second when b")], spec)
    bad = lint([_note("load_rows", "checks in this order of = models.Phase: second when b, first when a")], spec)
    assert not [f for f in good["findings"] if f["rule"] == "L4"]
    assert [f["code"] for f in bad["findings"] if f["rule"] == "L4"] == ["claimed_order_differs"]


def test_l5_diverged_copies_block_and_equal_copies_only_report():
    span = "MUST sort the rows by the declared keys before hashing them so that equal content"
    same = [_note("load_rows", f"{span}: by (row_id, row_name, row_kind)"),
            _note("Row", f"{span}: by (row_id, row_name, row_kind)", 2)]
    diverged = [_note("load_rows", f"{span}: by (row_id, row_name, row_kind)"),
                _note("Row", f"{span}: by (row_id, row_kind, row_name)", 2)]
    l5 = lambda notes: {f["code"] for f in lint(notes, SPEC)["findings"] if f["rule"] == "L5"}
    assert l5(same) == {"shared_prose"}
    assert l5(diverged) == {"shared_prose", "diverged_copies"}


def test_l5_finds_both_sides_of_a_pair_whatever_the_module_order():
    span = "MUST sort the rows by the declared keys before hashing them so that equal content"
    notes = [_note("load_rows", f"{span}: by (row_id, row_name, row_kind)"),
             _note("Row", f"{span}: by (row_id, row_kind, row_name)", 2)]
    for ordered in (notes, notes[::-1]):
        found = {(f["scope"], f["code"]) for f in lint(ordered, SPEC)["findings"] if f["rule"] == "L5"}
        assert found == {(scope, code) for scope in ("load_rows", "Row") for code in ("shared_prose", "diverged_copies")}


def test_l5_identical_copies_with_two_lists_only_report():
    span = "MUST sort the rows by the declared keys before hashing them so that equal content"
    text = f"{span}: first by (key_a, key_b, key_c), then by (key_a, key_b, key_d)."
    codes = {f["code"] for f in lint([_note("load_rows", text), _note("Row", text, 2)], SPEC)["findings"] if f["rule"] == "L5"}
    assert codes == {"shared_prose"}


def test_l5_divergence_in_a_later_shared_sentence_blocks():
    s1 = "MUST sort the rows by the declared keys before hashing them so that equal content hashes alike."
    s2 = "MUST then write the columns in the stored order of the table so that readers see"
    a = f"{s1} {s2} (col_a, col_b, col_c)."
    b = f"{s1} {s2} (col_a, col_c, col_b)."
    codes = {f["code"] for f in lint([_note("load_rows", a), _note("Row", b, 2)], SPEC)["findings"] if f["rule"] == "L5"}
    assert "diverged_copies" in codes


def test_a_v2_table_s_enum_column_is_no_second_home_of_the_members():
    spec = {
        "models": {"OrderStatus": {"kind": "enum", "values": ["draft", "shipped"]},
                   "OrderStatusClass": {"fields": {"status": "OrderStatus", "terminal": "bool", "label": "str"}}},
        "rules": {"data_provider_backend": {"kind": "data_provider_backend", "schema_version": 2, "constants": {
            "ORDER_STATUS_CLASSES": {"value_type": "record_tuple", "row_model": "OrderStatusClass",
                                     "key": ["status"], "total": True,
                                     "value": [{"status": "draft", "terminal": False, "label": "Draft"},
                                               {"status": "shipped", "terminal": True, "label": "Sent"}]}}}},
    }
    from notes_authoring.index import SpecIndex

    index = SpecIndex.build(spec)
    assert index.homes("shipped") == ["= models.OrderStatus"]
    assert index.homes("Sent") == ["the imported ORDER_STATUS_CLASSES constant"]
