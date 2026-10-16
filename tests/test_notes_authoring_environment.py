"""The writing environment: structure requests, the agent's task, and the
acceptance that writes notes only after lint (Data Closure §3, §5, Q15)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from notes_authoring import accept, prompt, request
from notes_authoring.index import SpecIndex

SPEC = {
    "standard_version": 3,
    "models": {"Status": {"kind": "enum", "values": ["open", "closed"]}, "Row": {"fields": {"row_id": "str"}}},
    "rules": {"data_provider_backend": {"kind": "data_provider_backend",
                                        "constants": {"PAGE_MAX": {"value_type": "positive_integer", "value": 200}}}},
    "config": {},
    "contracts": {"load_rows": "(limit: int) -> list[Row]", "save_row": "(row: Row) -> Status", "parse": "(raw: str) -> str"},
    "module_functions": {"store": ["load_rows", "save_row"], "parser": ["parse"], "models": ["Row", "Status"]},
}
NOTES = """# State 7 — demo notes

## parser

parse: [BEHAVIOR] MUST return the text unchanged.

## store

load_rows: [BEHAVIOR] MUST return rows in store order.
save_row: [BEHAVIOR] MUST store the row.
"""
FAKE_RESOLVER = r'''
import json, re, sys
spec = json.load(sys.stdin)
items = []
for index, note in enumerate(spec["notes"]):
    for m in re.finditer(r"=\s*((?:models|rules|config)\.[A-Za-z_.]*[A-Za-z_])", note):
        legal = m.group(1).startswith("models.")
        items.append({"note_index": index, "address": m.group(1), "status": "legal" if legal else "illegal",
                      "code": "legal" if legal else "address_form_closed", "message": "v3"})
json.dump({"addresses": items}, sys.stdout)
'''


@pytest.fixture
def case(tmp_path: Path) -> Path:
    root = tmp_path / "case"
    root.mkdir()
    (root / "80_notes.md").write_text(NOTES, encoding="utf-8")
    return root


@pytest.fixture
def factory(tmp_path: Path) -> Path:
    root = tmp_path / "factory"
    (root / "tools").mkdir(parents=True)
    (root / "tools/spec_address.py").write_text(FAKE_RESOLVER, encoding="utf-8")
    return root


def result(notes=None, requests=None, module="store") -> dict:
    payload = {"schema_version": prompt.RESULT_SCHEMA, "module": module}
    if notes is not None:
        payload["notes"] = notes
    if requests is not None:
        payload["structure_requests"] = requests
    return payload


def a_request(**overrides) -> dict:
    digests = SpecIndex.build(SPEC).absence([])["namespaces"]
    base = {
        "schema_version": request.SCHEMA, "module": "store",
        "need": "how many rows a page holds when none is asked",
        "value_kind": "threshold", "candidate_values": ["25 (02_rules.md:41)"],
        "sources": [{"path": "02_rules.md", "line": 41, "quote": "a page holds 25 rows"}],
        "absence": {"terms": ["page", "default"], "namespaces": digests},
        "homes_considered": [{"home": "the imported PAGE_MAX constant", "why_not": "the ceiling, not the default"}],
        "route": "state6", "blocked_notes": ["load_rows: BEHAVIOR"],
    }
    return {**base, **overrides}


def run(case, factory, payload, write=True):
    return accept.accept(case, "store", payload, spec=json.loads(json.dumps(SPEC)), factory_root=factory, write=write)


# ── notes ────────────────────────────────────────────────────────────────

def test_clean_notes_replace_the_module_section_and_nothing_else(case, factory):
    notes = ["load_rows: [BEHAVIOR] MUST return at most the imported PAGE_MAX constant rows, in store order.",
             "save_row: [RETURN_SHAPE] MUST return the = models.Status of the stored row."]
    report = run(case, factory, result(notes))
    assert (report["status"], report["notes"], report["replaced"]) == ("written", 2, 2)
    text = (case / "80_notes.md").read_text(encoding="utf-8")
    assert "parse: [BEHAVIOR] MUST return the text unchanged." in text
    assert "MUST return rows in store order" not in text
    assert text.index("## store") < text.index("PAGE_MAX constant rows")


def test_check_mode_writes_nothing(case, factory):
    before = (case / "80_notes.md").read_text(encoding="utf-8")
    notes = ["load_rows: [BEHAVIOR] MUST return rows.", "save_row: [BEHAVIOR] MUST store the row."]
    assert run(case, factory, result(notes), write=False)["status"] == "written"
    assert (case / "80_notes.md").read_text(encoding="utf-8") == before


@pytest.mark.parametrize("notes, reason", [
    (["load_rows: [BEHAVIOR] MUST return at most 200 rows.", "save_row: [BEHAVIOR] MUST store it."], "lint"),
    (["load_rows: [BEHAVIOR] MUST read = rules.data_provider_backend.constants.PAGE_MAX.",
      "save_row: [BEHAVIOR] MUST store it."], "lint"),
    (["load_rows: [BEHAVIOR] MUST return rows."], "callables without a note"),
    (["load_rows: [BEHAVIOR] MUST return rows.", "save_row: [BEHAVIOR] MUST store it.",
      "parse: [BEHAVIOR] MUST parse."], "do not parse or bind"),
    (["load_rows: MUST return rows.", "save_row: [BEHAVIOR] MUST store it."], "do not parse or bind"),
])
def test_refused_notes_never_reach_the_file(case, factory, notes, reason):
    before = (case / "80_notes.md").read_text(encoding="utf-8")
    report = run(case, factory, result(notes))
    assert report["status"] == "refused"
    assert (reason in report["reason"]) if reason != "lint" else report["findings"]
    assert (case / "80_notes.md").read_text(encoding="utf-8") == before


def test_a_result_for_another_module_or_schema_is_refused(case, factory):
    assert run(case, factory, result(["parse: [BEHAVIOR] MUST parse."], module="parser"))["status"] == "refused"
    assert run(case, factory, {"notes": []})["status"] == "refused"


# ── structure requests ───────────────────────────────────────────────────

def test_a_request_is_written_and_the_notes_stay(case, factory):
    before = (case / "80_notes.md").read_text(encoding="utf-8")
    report = run(case, factory, result(requests=[a_request()]))
    assert report["status"] == "requested"
    assert request.load(case, "store")[0]["need"].startswith("how many rows")
    assert (case / "80_notes.md").read_text(encoding="utf-8") == before


@pytest.mark.parametrize("overrides, error", [
    ({"absence": {"terms": [], "namespaces": {}}}, "absence.terms"),
    ({"absence": {"terms": ["page"], "namespaces": {"models": "x"}}}, "absence.namespaces"),
    ({"route": "somewhere"}, "route"),
    ({"value_kind": "number"}, "value_kind"),
    ({"sources": []}, "sources"),
    ({"module": "parser"}, "module"),
])
def test_an_invalid_request_is_refused(case, factory, overrides, error):
    report = run(case, factory, result(requests=[a_request(**overrides)]))
    assert report["status"] == "refused" and any(error in e for e in report["errors"])


def test_a_request_proven_over_other_namespaces_is_refused(case, factory):
    stale = a_request(absence={"terms": ["page"], "namespaces": {"models": "0" * 64, "rules": "0" * 64, "config": "0" * 64}})
    assert "digests" in run(case, factory, result(requests=[stale]))["reason"]


def test_an_open_request_holds_the_notes_back_until_its_source_changes(case, factory):
    run(case, factory, result(requests=[a_request()]))
    notes = ["load_rows: [BEHAVIOR] MUST return rows.", "save_row: [BEHAVIOR] MUST store the row."]
    assert "open" in run(case, factory, result(notes))["reason"]
    # State 6 gave the value a home: the namespaces changed, the request is stale
    spec = json.loads(json.dumps(SPEC))
    spec["rules"]["data_provider_backend"]["constants"]["PAGE_DEFAULT"] = {"value_type": "positive_integer", "value": 25}
    status = request.status(case, SpecIndex.build(spec))["modules"]["store"]
    assert (status["open"], status["stale"]) == (0, 1)
    written = accept.accept(case, "store", result(notes), spec=spec, factory_root=factory)
    assert written["status"] == "written" and request.load(case, "store") == []


def test_notes_and_requests_together_are_refused(case, factory):
    payload = result(["load_rows: [BEHAVIOR] MUST return rows."], [a_request()])
    assert run(case, factory, payload)["status"] == "refused"


# ── the agent's task ─────────────────────────────────────────────────────

def test_the_task_carries_the_input_and_the_standard_not_the_values(case):
    slice_payload = {"responsibility": "keeps rows", "capabilities": [], "flows": [], "public_operations": [], "obligations": []}
    from notes_workbench import language

    text = prompt.build(case, "store", SPEC, slice_payload, language.authored_notes(case))
    assert '"load_rows": "(limit: int) -> list[Row]"' in text
    assert '"Row": {' in text and '"Status": {' in text
    assert "load_rows: [BEHAVIOR] MUST return rows in store order." in text
    assert "### 15.11 " in text and "## 2. notes" in text
    assert "200" not in text  # the value reaches the agent only through find_value_homes
    assert prompt.RESULT_SCHEMA in text and request.SCHEMA in text


def test_the_same_notes_handed_in_again_leave_the_file_byte_for_byte(case, factory):
    before = (case / "80_notes.md").read_text(encoding="utf-8")
    notes = ["load_rows: [BEHAVIOR] MUST return rows in store order.", "save_row: [BEHAVIOR] MUST store the row."]
    assert run(case, factory, result(notes))["status"] == "written"
    assert (case / "80_notes.md").read_text(encoding="utf-8") == before
