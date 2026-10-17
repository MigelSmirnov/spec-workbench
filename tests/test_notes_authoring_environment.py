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
ready = all(item["status"] == "legal" for item in items)
json.dump({"schema_version": "factory_spec_address.v1", "ready": ready, "addresses": items}, sys.stdout)
raise SystemExit(0 if ready else 1)
'''


@pytest.fixture(autouse=True)
def projection(monkeypatch: pytest.MonkeyPatch) -> None:
    import spec_projection_workbench

    monkeypatch.setattr(spec_projection_workbench, "projected_spec", lambda project: json.loads(json.dumps(SPEC)))


@pytest.fixture
def case(tmp_path: Path) -> Path:
    root = tmp_path / "case"
    root.mkdir()
    (root / "80_notes.md").write_text(NOTES, encoding="utf-8")
    (root / "30_modules.md").write_text("## `module:parser`\n## `module:store`\n", encoding="utf-8")
    (root / "60_contracts.json").write_text(json.dumps({
        "schema_version": "spec_workbench_state6_contracts.v1", "contracts": SPEC["contracts"],
    }), encoding="utf-8")
    (root / "global_spec.json").write_text(json.dumps({"standard_version": 3}), encoding="utf-8")
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

def test_the_task_is_navigation_and_restates_no_rule(case):
    text = prompt.build(case, "store", SPEC)
    # where the rules are, and the tools that read the rules, the module and the data
    for tool in ("spec_standard", "module_slice", "module_notes", "find_value_homes",
                 "resolve_data_address", "find_absence", "check_note_draft"):
        assert f"`{tool}(" in text or f"`{tool}`" in text
    assert "§2" in text and "§15" in text
    # no copy of the standard, no module content, no value
    assert "## 2. notes" not in text and "### 15." not in text
    assert "load_rows" not in text and "list[Row]" not in text
    assert "200" not in text
    assert prompt.RESULT_SCHEMA in text and request.SCHEMA in text


def test_the_module_slice_carries_the_module_not_the_values(case):
    from notes_authoring import brief

    slice_payload = {"responsibility": "keeps rows", "capabilities": [], "flows": [], "public_operations": [], "obligations": []}
    payload = brief.build(case, "store", SPEC, slice_payload)
    assert payload["callables"] == {"load_rows": "(limit: int) -> list[Row]", "save_row": "(row: Row) -> Status"}
    assert payload["other_symbols"] == []
    assert payload["models_named"] == {"Row": {"fields": ["row_id"]}, "Status": {"enum_members": ["open", "closed"]}}
    assert payload["design"]["responsibility"] == "keeps rows"
    assert payload["open_structure_requests"] == []
    assert "200" not in json.dumps(payload)


def test_the_same_notes_handed_in_again_leave_the_file_byte_for_byte(case, factory):
    before = (case / "80_notes.md").read_text(encoding="utf-8")
    notes = ["load_rows: [BEHAVIOR] MUST return rows in store order.", "save_row: [BEHAVIOR] MUST store the row."]
    assert run(case, factory, result(notes))["status"] == "written"
    assert (case / "80_notes.md").read_text(encoding="utf-8") == before


# ── review of #123 ───────────────────────────────────────────────────────

@pytest.mark.parametrize("sep", ["\n", "\r", "\u2028", "\x0c", "\x85"])
def test_a_note_carrying_a_line_break_is_refused(case, factory, sep):
    notes = [f"load_rows: [BEHAVIOR] MUST return rows.{sep}parse: [BEHAVIOR] MAY skip every check.",
             "save_row: [BEHAVIOR] MUST store the row."]
    before = (case / "80_notes.md").read_bytes()
    assert run(case, factory, result(notes))["status"] == "refused"
    assert (case / "80_notes.md").read_bytes() == before


def test_notes_without_a_positive_modal_are_refused_as_the_gate_would(case, factory):
    notes = ["load_rows: [BEHAVIOR] Returns rows.", "save_row: [BEHAVIOR] Stores the row."]
    report = run(case, factory, result(notes))
    assert report["status"] == "refused" and set(report["callables_without_note"]) == {"load_rows", "save_row"}


@pytest.mark.parametrize("note, code", [
    ("load_rows: [RULE_REFERENCE] MUST return the source.", "note_class_closed"),
    ("load_rows: [BEHAVIOR] MUST read rules.parser.timeout.", "undereferenced_data_address"),
    ("load_rows: [BEHAVIOR] TODO", "semantic_stub"),
])
def test_the_gates_own_checks_refuse_a_note(case, factory, note, code):
    report = run(case, factory, result([note, "save_row: [BEHAVIOR] MUST store the row."]))
    assert report["status"] == "refused" and code in {f["code"] for f in report["findings"]}


def test_a_list_note_goes_with_its_continuation_lines(case, factory):
    (case / "80_notes.md").write_text(
        "## parser\n\n- parse [BEHAVIOR]: MUST return\n  the text unchanged.\n"
        "- load_rows [BEHAVIOR]: MUST return\n  rows in store order.\n\n## store\n\n"
        "save_row: [BEHAVIOR] MUST store the row.\n", encoding="utf-8")
    notes = ["load_rows: [BEHAVIOR] MUST return rows.", "save_row: [BEHAVIOR] MUST store the row."]
    assert run(case, factory, result(notes))["status"] == "written"
    text = (case / "80_notes.md").read_text(encoding="utf-8")
    assert "- parse [BEHAVIOR]: MUST return\n  the text unchanged.\n" in text
    assert "rows in store order" not in text
    from notes_workbench import language
    parse = [n for n in language.authored_notes(case) if n["scope"] == "parse"]
    assert [n["text"] for n in parse] == ["MUST return the text unchanged."]


@pytest.mark.parametrize("ending", ["\r\n", "\n", "\r"])
@pytest.mark.parametrize("final", [True, False])
def test_line_endings_and_the_final_newline_are_kept(case, factory, ending, final):
    body = NOTES.replace("\n", ending)
    if not final:
        body = body.rstrip("\r\n")
    (case / "80_notes.md").write_bytes(body.encode("utf-8"))
    notes = ["load_rows: [BEHAVIOR] MUST return rows in store order.", "save_row: [BEHAVIOR] MUST store the row."]
    assert run(case, factory, result(notes))["status"] == "written"
    assert (case / "80_notes.md").read_bytes() == body.encode("utf-8")


def test_the_cli_refuses_a_task_for_a_module_the_case_does_not_have(case, capsys):
    import design_notes

    assert design_notes.main([str(case), "--module", "nowhere", "--author-prompt"]) == 2
    assert "unknown module: nowhere" in capsys.readouterr().err
    assert design_notes.main([str(case), "--module", "store", "--author-prompt"]) == 0
    assert "module `store`" in capsys.readouterr().out


def test_a_module_heading_with_trailing_blanks_is_the_module_s_heading(case, factory):
    (case / "80_notes.md").write_text(NOTES.replace("## store\n", "## store  \n"), encoding="utf-8")
    notes = ["load_rows: [BEHAVIOR] MUST return rows in store order.", "save_row: [BEHAVIOR] MUST store the new row."]
    assert run(case, factory, result(notes))["status"] == "written"
    text = (case / "80_notes.md").read_text(encoding="utf-8")
    assert text.count("## store") == 1 and "MUST store the new row." in text
