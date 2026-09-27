"""Value-flow closure: sources of required instants, sinks of arguments, reachable collaborators."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from value_flow_workbench import CLOSURE_FILE, CLOSURE_SCHEMA, ValueFlowError, coverage

MODULES = """# Modules

## `ledger`

### Owns

Entries.

### Knows

M01, the clock through `host_clock` and stored entries through `entry_store`.

### Hides

Nothing else.

## `entry_store`

### Knows

M01.

## `host_clock`

### Knows

Nothing.
"""

STATE1 = """# Models

## Model M01 — Entry

### Meaning

One ledger entry.

Candidate fields:

- `entry_id`: stable identity;
- `title`: bounded text;
- `opened_by`: Actor; `opened_at`;
- `closed_at`: absent while the entry is `open`.

### Identity

entity

## Model M02 — EntryDraft

Candidate facts for release v1:

- `title`: 64;
- `opened_at`.

## Model M03 — Actor

Candidate fields:

- `actor_id`.

## Model M04 — Instant

Candidate fields:

- `epoch_us`: microseconds.
"""

PUBLIC = """# Public operations

## `public_op:ledger.open_entry`

### State impact

Appends one entry.

## `public_op:ledger.entry`

### State impact

Read-only.

## `public_op:entry_store.load_entry`

### State impact

Read-only.
"""


def write_case(root: Path, *, notes: dict[str, str] | None = None, contracts: dict[str, str] | None = None,
               models: dict | None = None, closure: dict | None = None, policy: bool = True) -> Path:
    case = root / "case"
    case.mkdir()
    declared = {
        "open_entry": "(actor: Actor, title: str, memo: str) -> Entry",
        "entry": "(entry_id: str) -> Entry",
        "load_entry": "(entry_id: str) -> Entry | None",
        "now": "() -> Instant",
        **(contracts or {}),
    }
    owners = {"open_entry": "ledger", "entry": "ledger", "replace_entry": "ledger", "import_entry": "ledger",
              "amend_entry": "ledger", "load_entry": "entry_store", "now": "host_clock"}
    (case / "60_contracts.json").write_text(json.dumps({"schema_version": "x", "contracts": declared}), encoding="utf-8")
    (case / "60_contract_plan.json").write_text(json.dumps({"schema_version": "x", "status": "closed", "functions": [
        {"function": name, "module": f"module:{owners[name]}", "visibility": "public"} for name in declared
    ]}), encoding="utf-8")
    (case / "60_model_closure_core.json").write_text(json.dumps({"models": {
        "Instant": {"identity": "value", "fields": {"epoch_us": "int"}},
        "Actor": {"identity": "value", "fields": {"actor_id": "str"}},
        "EntryDraft": {"identity": "value", "fields": {"title": "str", "opened_at": "Instant"}},
        "Entry": {"identity": "entity", "fields": {
            "entry_id": "str", "title": "str", "opened_by": "Actor", "opened_at": "Instant", "closed_at": "Instant | None"}},
        **(models or {}),
    }}), encoding="utf-8")
    if policy:
        (case / "60_data_closure.json").write_text(json.dumps({"sections": {"rules": {"time_source_policy": {
            "representation": {"type": "Instant", "field": "epoch_us", "unit": "epoch_us", "conversion": "floor_ns_to_us"}}}}}),
            encoding="utf-8")
        (case / "70_system_clock_closure.json").write_text(json.dumps({"backend_ir": {"wiring": {
            "module": "host_clock", "wall_clock_function": "now", "elapsed_clock_function": "ticks", "models_module": "m"}}}),
            encoding="utf-8")
    lines = {
        "open_entry": "MUST append one Entry, sample `module:host_clock.now` and fold `memo` into nothing.",
        "entry": "MUST return the entry read through `entry_store.load_entry`.",
        **(notes or {}),
    }
    (case / "80_notes.md").write_text("# Notes\n\n" + "\n".join(
        f"{scope}: [BEHAVIOR] {text}" for scope, text in lines.items() if text) + "\n", encoding="utf-8")
    (case / "30_modules.md").write_text(MODULES, encoding="utf-8")
    (case / "01_models.md").write_text(STATE1, encoding="utf-8")
    (case / "50_public_apis.md").write_text(PUBLIC, encoding="utf-8")
    if closure is not None:
        (case / CLOSURE_FILE).write_text(json.dumps({"schema_version": CLOSURE_SCHEMA, "status": "closed",
                                                     "outputs": {}, "inputs": {}, **closure}), encoding="utf-8")
    return case


def codes(report: dict) -> list[tuple[str, str]]:
    return sorted((item["code"], item.get("function") or item.get("module") or "") for item in report["findings"])


def test_a_closed_case_reports_its_denominators(tmp_path):
    report = coverage(write_case(tmp_path, closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}}))
    summary = report["summary"]
    assert report["findings"] == [] and summary["handoff_ready"] is True
    assert summary["instant_type"] == "Instant" and summary["wall_clock"] == "host_clock.now"
    # open_entry stamps opened_at from the clock; entry reads it back; the optional closed_at is not required
    assert summary["outputs"] == {"enabled": True, "pairs": 3, "by_source": {"clock": 1, "stored": 2}, "unresolved": 0}
    # actor is a record and is judged through its own model; title is a field; memo is declared
    assert summary["inputs"] == {"constructing_functions": 1, "pairs": 2, "resolved": 2, "unresolved": 0}
    assert summary["collaborators"] == {"edges": 2, "reachable": 2, "unreachable": 0}
    # a name leads a clause of a bullet (`opened_by`: Actor; `opened_at`); `open` later in a clause is a value
    assert summary["carriers"] == {"state1_models": 4, "facts": 9, "references": 0, "without_carrier": 0}


def test_a_required_instant_without_a_source_stops_the_case(tmp_path):
    report = coverage(write_case(tmp_path, notes={"open_entry": "MUST append one Entry."}))
    assert ("instant_without_source", "open_entry") in codes(report)
    finding = next(item for item in report["findings"] if item["code"] == "instant_without_source")
    assert finding["address"] == "Entry.opened_at" and "host_clock.now" in finding["message"]
    assert finding["hint"].startswith("not decided")
    # the open instant still makes the public mutating operation a constructor: its arguments are judged at once
    assert ("argument_without_sink", "open_entry") in codes(report)


def test_a_single_record_argument_carries_the_instant_and_a_collection_does_not(tmp_path):
    contracts = {"import_entry": "(draft: EntryDraft) -> Entry", "replace_entry": "(prior: tuple[Entry, ...]) -> Entry"}
    report = coverage(write_case(tmp_path, contracts=contracts, notes={
        "import_entry": "MUST append the entry.", "replace_entry": "MUST append the entry."}))
    unresolved = {item["function"] for item in report["findings"] if item["code"] == "instant_without_source"}
    assert unresolved == {"replace_entry"}
    assert report["summary"]["outputs"]["by_source"]["argument"] == 1


def test_an_argument_with_no_field_and_no_declaration_has_no_sink(tmp_path):
    report = coverage(write_case(tmp_path))
    assert codes(report) == [("argument_without_sink", "open_entry")]
    assert "Entry has no field 'memo'" in report["findings"][0]["message"]


@pytest.mark.parametrize("declaration, code", [
    ({"sink": "field", "to": "Entry.memo"}, "declared_sink_unknown"),        # the model has no such field: add it
    ({"sink": "field", "to": "EntryDraft.title"}, "declared_sink_unknown"),  # a field of a model that is not constructed
    ({"sink": "derived", "to": "Entry.entry_id"}, None),
    ({"sink": "key", "to": "Actor.actor_id"}, None),
    ({"sink": "forwarded", "to": "load_entry"}, "declared_callee_not_named"),
    ({"sink": "forwarded", "to": "nowhere"}, "declared_sink_unknown"),
    ({"sink": "dropped"}, "value_flow_declaration_invalid"),
    ({"sink": "guard", "because": "reviewed"}, "value_flow_declaration_invalid"),
])
def test_a_declared_sink_is_checked_against_the_design(tmp_path, declaration, code):
    # reachability is the module's: imports are per module, so any note of the module may name the callee.
    # Here no note of ledger names load_entry, which also leaves the State 3 collaborator unreachable.
    report = coverage(write_case(tmp_path, notes={"entry": "MUST return the stored entry."},
                                 closure={"inputs": {"open_entry": {"memo": declaration}}}))
    found = [item["code"] for item in report["findings"] if item["code"] != "known_collaborator_unreachable"]
    assert found == ([code] if code else [])


def test_a_forwarded_argument_is_accepted_once_a_note_of_the_module_names_the_callee(tmp_path):
    report = coverage(write_case(tmp_path, closure={"inputs": {"open_entry": {"memo": {"sink": "forwarded", "to": "load_entry"}}}}))
    assert report["findings"] == []


@pytest.mark.parametrize("declaration, note, code", [
    ({"source": "clock"}, "MUST append the entry.", "declared_clock_not_named"),
    ({"source": "clock"}, "MUST append the entry and sample `module:host_clock.now`.", None),
    ({"source": "stored"}, "MUST append the entry.", None),
    ({"source": "argument", "via": "entry_id"}, "MUST append the entry.", "value_flow_declaration_invalid"),
    ({"source": "callee", "via": "load_entry"}, "MUST return what `load_entry` reads.", None),
    ({"source": "callee", "via": "load_entry"}, "MUST append the entry.", "declared_callee_not_named"),
    ({"source": "guess"}, "MUST append the entry.", "value_flow_declaration_invalid"),
])
def test_a_declared_source_is_checked_against_the_design(tmp_path, declaration, note, code):
    case = write_case(tmp_path, contracts={"amend_entry": "(entry_id: str) -> Entry"},
                      notes={"amend_entry": note, "entry": "MUST return the entry kept by `entry_store`."},
                      closure={"outputs": {"amend_entry": {"Entry.opened_at": declaration}},
                               "inputs": {"open_entry": {"memo": {"sink": "guard"}},
                                          "amend_entry": {"entry_id": {"sink": "key", "to": "Entry.entry_id"}}}})
    found = [item["code"] for item in coverage(case)["findings"]]
    # a declaration that fails validation leaves amend_entry outside the constructing set: its input row goes stale
    assert [item for item in found if item != "value_flow_declaration_stale"] == ([code] if code else [])


def test_a_declaration_nothing_asks_for_is_stale(tmp_path):
    report = coverage(write_case(tmp_path, closure={
        "inputs": {"open_entry": {"memo": {"sink": "guard"}, "title": {"sink": "guard"}, "ghost": {"sink": "guard"}}},
        "outputs": {"entry": {"Entry.closed_at": {"source": "stored"}}}}))
    stale = sorted(item["message"].split(":")[0] for item in report["findings"])
    assert [item["code"] for item in report["findings"]] == ["value_flow_declaration_stale"] * 2
    # title is a real scalar argument and may be declared; an optional instant and an unknown parameter may not
    assert stale == ["inputs.open_entry.ghost", "outputs.entry.Entry.closed_at"]


def test_a_known_collaborator_nobody_names_is_unreachable(tmp_path):
    report = coverage(write_case(tmp_path, notes={"entry": "MUST return the stored entry."},
                                 closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}}))
    assert codes(report) == [("known_collaborator_unreachable", "ledger")]
    finding = report["findings"][0]
    assert finding["collaborator"] == "entry_store" and "load_entry" in finding["message"]
    assert report["summary"]["collaborators"] == {"edges": 2, "reachable": 1, "unreachable": 1}


def test_without_a_declared_instant_type_the_output_lens_says_it_did_not_judge(tmp_path):
    report = coverage(write_case(tmp_path, policy=False))
    outputs = report["summary"]["outputs"]
    assert outputs["enabled"] is False and outputs["pairs"] == 0 and "time_source_policy" in outputs["reason"]
    # not judged is not passed: the case stops until the lens has something to judge
    assert [(item["code"], item["lens"]) for item in report["findings"]] == [("value_flow_lens_judged_nothing", "outputs")]
    assert report["summary"]["handoff_ready"] is False
    # nothing is known to be constructed, so no argument is judged either — and the report shows that zero
    assert report["summary"]["inputs"]["pairs"] == 0


def test_an_open_closure_that_resolves_everything_must_be_closed(tmp_path):
    case = write_case(tmp_path, closure={"status": "open", "inputs": {"open_entry": {"memo": {"sink": "guard"}}}})
    assert [item["code"] for item in coverage(case)["findings"]] == ["value_flow_closure_open"]


def test_a_malformed_closure_or_a_case_before_state_6_is_refused(tmp_path):
    case = write_case(tmp_path, closure={"extra": 1})
    with pytest.raises(ValueFlowError, match="exactly"):
        coverage(case)
    (case / "60_contract_plan.json").unlink()
    with pytest.raises(ValueFlowError, match="State 6"):
        coverage(case)


def test_cli_prints_every_denominator(tmp_path, capsys):
    from design_value_flow import main

    assert main([str(write_case(tmp_path)), "--coverage"]) == 1
    out = capsys.readouterr().out
    assert "outputs        3 of 3 instants sourced" in out
    assert "inputs         1 of 2 scalar arguments of 1 constructing functions have a sink" in out
    assert "collaborators  2 of 2 known collaborators reachable" in out
    assert "[argument_without_sink] ledger.open_entry(memo: str)" in out


def test_a_design_that_names_no_collaborator_has_not_passed_the_collaborator_lens(tmp_path):
    case = write_case(tmp_path, closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}})
    (case / "30_modules.md").write_text(MODULES.replace("`host_clock`", "the clock").replace("`entry_store`", "the store"),
                                        encoding="utf-8")
    report = coverage(case)
    assert report["summary"]["collaborators"]["edges"] == 0
    assert [(item["code"], item["lens"]) for item in report["findings"]] == [("value_flow_lens_judged_nothing", "collaborators")]


def test_a_facade_reaches_the_modules_it_delegates_to(tmp_path):
    case = write_case(tmp_path, notes={"entry": "MUST return the stored entry."},
                      closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}})
    (case / "30_modules.md").write_text(
        MODULES.replace("stored entries through `entry_store`", "stored entries")
        .replace("Nothing else.", "Nothing else.\n\n### Depth assessment\n\n- kind: facade\n- delegates to: `entry_store`"),
        encoding="utf-8")
    report = coverage(case)
    assert codes(report) == [("known_collaborator_unreachable", "ledger")]
    assert report["findings"][0]["collaborator"] == "entry_store"


def test_a_fact_state_1_claims_must_exist_in_the_closure_whatever_follows_its_name(tmp_path):
    """The closure regrouped the release limits under other names; State 1 lists them with values, not types."""
    case = write_case(tmp_path, closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}},
                      models={"EntryDraft": {"identity": "value", "fields": {"headline": "str", "opened_at": "Instant"}}})
    report = coverage(case)
    assert [item["code"] for item in report["findings"]] == ["state1_fact_without_carrier"]
    finding = report["findings"][0]
    assert finding["model"] == "EntryDraft" and finding["facts"] == ["title"] and "headline" in finding["message"]
    assert report["summary"]["carriers"]["without_carrier"] == 1


def test_a_field_named_outright_in_prose_is_checked_and_formal_pseudo_code_is_not(tmp_path):
    case = write_case(tmp_path, closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}})
    (case / "02_rules.md").write_text(
        "# Rules\n\nAn entry is closed once `Entry.closed_at` is present; its label is `Entry.headline`.\n\n"
        "```text\nEntry.is_open -> Entry.closed_at = none\n```\n", encoding="utf-8")
    report = coverage(case)
    assert [(item["code"], item["field"], item["line"]) for item in report["findings"]] == [
        ("named_field_without_carrier", "headline", 3)]
    assert report["summary"]["carriers"]["references"] == 2


def test_a_closed_model_state_1_describes_without_naming_a_fact_stops_the_case(tmp_path):
    case = write_case(tmp_path, closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}})
    (case / "01_models.md").write_text(STATE1.replace("Candidate fields:\n\n- `actor_id`.", "Whoever acts."), encoding="utf-8")
    report = coverage(case)
    assert [(item["code"], item["model"]) for item in report["findings"]] == [("state1_model_without_named_facts", "Actor")]


def test_a_closure_with_no_state_1_behind_it_has_not_passed_the_carrier_lens(tmp_path):
    case = write_case(tmp_path, closure={"inputs": {"open_entry": {"memo": {"sink": "guard"}}}})
    (case / "01_models.md").unlink()
    report = coverage(case)
    assert [(item["code"], item["lens"]) for item in report["findings"]] == [("value_flow_lens_judged_nothing", "carriers")]
