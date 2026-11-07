"""The transition protocol (skills/spec-authoring/TRANSITION_PROTOCOL.md).

Each test is one of the proofs issue #147 asks for, on a small fixture:
missing inputs are not success; a carried obligation comes back at its
receiving layer; the question round is given its layer; a closed round does
not hide a blocking result; execution a backend emits is recognised; and a fix
does not reopen what was closed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import design_authoring_next
import design_decision_witness
import design_questions
import flow_closure
import transition
from questions_workbench import service


# ------------------------------------------------------------------ fixtures

MODELS = """# State 1 — Demo models

## Model M01 — Thing

### Identity

entity
"""

RULES = """# State 2 — Demo rules

## Accepted decision A01 — things are counted

### Normative rules

A thing is counted once.

### Formal invariants

- INV-001: a thing is counted once
- INV-002: a count never decreases

### Required tests

{tests}

## Accepted decision A02 — things are named

### Normative rules

A thing has a name.
"""

API = """# State 5 — Public operations

## `public_op:things.record_thing`

### State impact

Writes one Thing.
"""


def _write(path: Path, payload) -> None:
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload, indent=1), encoding="utf-8")


def _case(tmp_path: Path, tests: str = "- INV-001: a thing counted twice is refused.\n"
                                        "- INV-002: a lower count is refused.") -> Path:
    case = tmp_path / "demo"
    case.mkdir(parents=True)
    _write(case / "00_product.md", "# State 0 — Demo\n\nA product.\n")
    _write(case / "01_models.md", MODELS)
    _write(case / "02_rules.md", RULES.format(tests=tests))
    return case


def _contracts(case: Path, functions: dict[str, tuple[str, str]]) -> None:
    """functions: name -> (module, signature)."""
    _write(case / "60_contract_plan.json", {
        "schema_version": "spec_workbench_state6_contract_plan.v1", "status": "closed",
        "functions": [{"function": name, "module": f"module:{module}", "visibility": "internal"}
                      for name, (module, _) in functions.items()]})
    _write(case / "60_contracts.json", {
        "schema_version": "spec_workbench_state6_contracts.v1",
        "contracts": {name: signature for name, (_, signature) in functions.items()}})


def _closure(case: Path, models: dict) -> None:
    _write(case / "60_model_closure_core.json",
           {"schema_version": "spec_workbench_model_closure.v1", "status": "closed", "models": models})


# ---------------------------------------------- 1. missing inputs are no pass

def test_a_state6_without_a_model_closure_is_not_checked_and_stops(tmp_path):
    # client-portal: State 6 was green until the closure was written, then
    # raised 35 fresh_timestamp_without_source (issue #147, second pass, item 1)
    case = _case(tmp_path)
    _write(case / "50_public_apis.md", API)
    _contracts(case, {"record_thing": ("things", "(name: str) -> Thing")})
    report = transition.run_phase(case, "state6_exact_contracts")
    outcomes = {r["check"]: r["outcome"] for r in report["results"]}
    assert outcomes["model_closure"] == "not_checked"
    assert outcomes["time_source"] == "not_checked"
    assert report["ready"] is False
    codes = {f["code"] for f in report["findings"]}
    assert {"model_closure_absent", "time_source_not_checked"} <= codes
    assert all("not a pass" in f["message"] for f in report["findings"] if f.get("outcome") == "not_checked")


def test_with_the_closure_the_same_case_is_checked_and_its_timestamp_needs_a_source(tmp_path):
    case = _case(tmp_path)
    _write(case / "50_public_apis.md", API)
    _contracts(case, {"record_thing": ("things", "(name: str) -> Thing")})
    _closure(case, {"Thing": {"identity": "entity", "fields": {"name": "str", "created_at": "datetime"}}})
    results = {r["check"]: r for r in transition.run_phase(case, "state6_exact_contracts")["results"]}
    assert results["model_closure"]["outcome"] == "closed"
    assert results["time_source"]["outcome"] == "open"
    assert [f["code"] for f in results["time_source"]["findings"]] == ["fresh_timestamp_without_source"]


def test_a_contract_only_model_must_be_introduced_by_a_contract(tmp_path):
    case = _case(tmp_path)
    _contracts(case, {"record_thing": ("things", "(request: RecordRequest) -> Thing")})
    _closure(case, {"Thing": {"identity": "entity", "fields": {"name": "str"}}})
    _write(case / "60_model_closure_contract_types.json", {
        "schema_version": "spec_workbench_model_closure.v1", "status": "closed", "identity_scope": "contract_only",
        "models": {"RecordRequest": {"identity": "value", "fields": {"name": "str"}},
                   "Orphan": {"identity": "value", "fields": {"x": "str"}},
                   "Thing": {"identity": "entity", "fields": {"name": "str"}}}})
    findings = transition.run_check(case, "model_closure")["findings"]
    assert {(f["code"], f["model"]) for f in findings} == {
        ("contract_only_model_unintroduced", "Orphan"), ("state1_model_marked_contract_only", "Thing")}


def test_flow_reachability_without_readable_routes_is_not_checked(tmp_path):
    case = _flow_case(tmp_path, router=False)
    _write(case / "70_router_closure.json", {"schema_version": "x", "items": []})  # authored, not assemblable
    report = flow_closure.coverage(case)
    assert report["summary"]["reachability"] == "not_checked"
    assert [f["code"] for f in report["findings"]] == ["flow_reachability_not_checked"]
    assert transition.run_check(case, "flow_reachability")["outcome"] == "not_checked"


def test_a_witness_whose_check_cannot_be_read_is_not_checked(tmp_path):
    case = _case(tmp_path, "- INV-001, INV-002: refused. [witness: verification:counts_once]")
    report = design_decision_witness.coverage(case, tmp_path / "no-factory")
    assert [(f["code"], f["outcome"], f["severity"]) for f in report["findings"]] == [
        ("witness_unverifiable", "not_checked", "error")]
    assert transition.run_check(case, "decision_witness")["outcome"] == "not_checked"


# ---------------------------- 2. a carried obligation returns to its receiver

def test_every_carried_obligation_names_a_later_phase_and_a_known_check():
    sequence = transition.load_sequence()
    order = [phase["id"] for phase in sequence["phases"]]
    carried = transition.obligations(sequence)
    assert {item["check"] for item in carried} | {c for p in order for c in transition.own_checks(sequence, p)} \
        <= set(transition.CHECKS)
    for item in carried:
        assert item["to"] in order and order.index(item["to"]) > order.index(item["from"]), item
        assert item["obligation"]
    receivers = {(item["from"], item["to"], item["check"]) for item in carried}
    assert ("state1_models", "state6_exact_contracts", "model_closure") in receivers
    assert ("state2_rules_decisions", "state6_exact_contracts", "time_source") in receivers
    assert ("state2_rules_decisions", "decision_witness_resolution", "decision_witness") in receivers
    assert ("state4_reviewed_flows", "state6_exact_contracts", "flow_steps") in receivers
    assert ("state4_reviewed_flows", "state7_notes", "flow_reachability") in receivers


def test_authoring_next_returns_the_layer_and_stops_where_an_obligation_lands(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _contracts(case, {"record_thing": ("things", "(name: str) -> Thing")})
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda *args: None)
    monkeypatch.setattr(design_authoring_next, "_question_gate", lambda *args: None)
    monkeypatch.setattr(design_authoring_next.design_stage6_data, "lint", lambda project: {"summary": {"errors": 0}})
    _write(case / "60_data_closure.json", "{}")
    monkeypatch.setattr(design_authoring_next.design_stage6_contracts, "handoff",
                        lambda project: {"ready": True, "summary": {}, "unresolved_functions": [], "findings": []})
    report = design_authoring_next.next_step(case)
    assert report["phase"] == "state6_exact_contracts" and report["blocked"] is True
    assert {f["carried_from"] for f in report["findings"]} == {"state1_models"}
    assert {(r["check"], r["outcome"]) for r in report["transition_results"]} >= {("model_closure", "not_checked")}
    assert [r["check"] for r in report["layer"]["receives"]] == ["model_closure", "time_source", "flow_steps"]


def test_state2_checks_its_own_required_tests_and_carries_the_binding(tmp_path):
    case = _case(tmp_path, "- INV-001: a thing counted twice is refused.")
    result = transition.run_check(case, "invariant_tests")
    assert result["outcome"] == "open"
    assert [(f["code"], f["invariant"]) for f in result["findings"]] == [("invariant_without_required_test", "INV-002")]
    described = _case(tmp_path / "b")
    assert transition.run_check(described, "invariant_tests")["outcome"] == "carried"


def test_a_binding_covers_only_the_invariants_its_line_names(tmp_path):
    # client-portal A5: one check bound to PLAT-REG-006 stood for PLAT-REG-001/002/007
    case = _case(tmp_path, "- INV-001: refused. [witness: workbench:state2_rules_decisions]\n"
                           "- INV-002: a lower count is refused.")
    report = design_decision_witness.coverage(case, tmp_path)
    assert [(f["code"], f.get("invariant")) for f in report["findings"]] == [("invariant_without_witness", "INV-002")]
    assert report["summary"]["witnessed"] == 0
    both = _case(tmp_path / "b", "- INV-001, INV-002: refused. [witness: workbench:state2_rules_decisions]")
    assert design_decision_witness.coverage(both, tmp_path)["summary"]["witnessed"] == 1


def test_a_tag_on_its_own_continuation_line_binds_only_the_invariant_its_item_names(tmp_path):
    # review r4501731318: the docstring's format puts the tag on the next line
    case = _case(tmp_path, "- INV-001: a thing counted twice is refused.\n"
                           "  [witness: workbench:state2_rules_decisions]\n"
                           "- INV-002: a lower count is refused.")
    report = design_decision_witness.coverage(case, tmp_path)
    assert [(f["code"], f.get("invariant")) for f in report["findings"]] == [("invariant_without_witness", "INV-002")]
    assert report["summary"]["witnessed"] == 0


def test_a_tag_in_an_item_naming_no_invariant_binds_none_of_several(tmp_path):
    case = _case(tmp_path, "- INV-001: refused.\n- INV-002: refused.\n"
                           "- Witness: [witness: workbench:state2_rules_decisions]")
    codes = sorted((f["code"], f.get("invariant")) for f in design_decision_witness.coverage(case, tmp_path)["findings"])
    assert codes == [("invariant_without_witness", "INV-001"), ("invariant_without_witness", "INV-002"),
                     ("witness_binding_ambiguous", None)]


UNIDENTIFIED = RULES.replace("- INV-001: a thing is counted once\n- INV-002: a count never decreases",
                             "- A thing is counted once.\n- A count never decreases.")


def _unidentified(tmp_path: Path, tests: str) -> Path:
    case = _case(tmp_path)
    _write(case / "02_rules.md", UNIDENTIFIED.format(tests=tests))
    return case


def test_one_tag_does_not_stand_for_several_unidentified_invariants(tmp_path):
    # review 5814738409 (#152): A32 had two invariants without identifiers, and
    # one tag for the second made the whole decision witnessed
    case = _unidentified(tmp_path, "- Counted twice is refused.\n"
                                   "- A lower count is refused. [witness: workbench:state2_rules_decisions]")
    report = design_decision_witness.coverage(case, tmp_path)
    codes = sorted(f["code"] for f in report["findings"])
    assert codes == ["invariant_without_identifier", "invariant_without_identifier", "witness_binding_ambiguous"]
    assert report["summary"]["witnessed"] == 0
    assert all(f["severity"] == "error" for f in report["findings"])


def test_word_labels_in_the_item_are_not_an_address(tmp_path):
    # client-portal A22/A25/A29: "closed-once, domain-error-unmasked [witness: ...]"
    case = _unidentified(tmp_path, "- Witnesses: counted-once, never-decreases "
                                   "[witness: workbench:state2_rules_decisions]")
    report = design_decision_witness.coverage(case, tmp_path)
    assert "witness_binding_ambiguous" in {f["code"] for f in report["findings"]}
    assert report["summary"]["witnessed"] == 0


def test_a_mixed_decision_reports_the_invariant_without_an_identifier(tmp_path):
    case = _case(tmp_path)
    _write(case / "02_rules.md", RULES.replace("- INV-002: a count never decreases", "- A count never decreases.")
           .format(tests="- INV-001: refused. [witness: workbench:state2_rules_decisions]"))
    report = design_decision_witness.coverage(case, tmp_path)
    assert [f["code"] for f in report["findings"]] == ["invariant_without_identifier"]
    assert "A count never decreases." in report["findings"][0]["message"]
    assert report["summary"]["witnessed"] == 0


def test_each_identified_invariant_stays_open_without_its_own_check(tmp_path):
    # two invariants, two checks: whichever check is missing, its invariant alone stays open
    tests = ("- INV-001: refused. [witness: workbench:state2_rules_decisions]\n"
             "- INV-002: refused. [witness: workbench:state1_models]")
    both = design_decision_witness.coverage(_case(tmp_path / "both", tests), tmp_path)
    assert both["summary"]["witnessed"] == 1 and both["findings"] == []
    for missing, left in (("state2_rules_decisions", "INV-001"), ("state1_models", "INV-002")):
        case = _case(tmp_path / missing, tests.replace(f"workbench:{missing}", "workbench:no_such_check"))
        report = design_decision_witness.coverage(case, tmp_path)
        assert [(f["code"], f.get("invariant")) for f in report["findings"]] == [
            ("witness_unresolved", None), ("invariant_without_witness", left)]
        assert report["summary"]["witnessed"] == 0


def test_one_unidentified_invariant_is_still_bound_by_one_tag(tmp_path):
    case = _case(tmp_path)
    _write(case / "02_rules.md", RULES.replace("- INV-001: a thing is counted once\n- INV-002: a count never decreases",
                                               "- A thing is counted once.")
           .format(tests="- Counted twice is refused. [witness: workbench:state2_rules_decisions]"))
    report = design_decision_witness.coverage(case, tmp_path)
    assert report["findings"] == [] and report["summary"]["witnessed"] == 1


def test_a_cited_known_gap_marks_its_findings_and_they_still_stop(tmp_path, monkeypatch):
    # an open gap with its finding codes (KG-002 itself is closed by system_clock_backend/v4)
    gaps = tmp_path / "KNOWN_GAPS.md"
    _write(gaps, "## KG-901 — a demo gap\n\nFinding codes: fresh_timestamp_without_source\n")
    monkeypatch.setattr(transition, "KNOWN_GAPS_FILE", gaps)
    monkeypatch.setattr(transition.known_gaps, "__defaults__", (gaps,))
    case = _case(tmp_path)
    _write(case / "02_rules.md", (case / "02_rules.md").read_text() + "\nClock: utcnow. [known_gap: KG-901]\n")
    _write(case / "50_public_apis.md", API)
    _contracts(case, {"record_thing": ("things", "(name: str) -> Thing")})
    _closure(case, {"Thing": {"identity": "entity", "fields": {"created_at": "datetime"}}})
    assert transition.known_gaps()["KG-901"] == {"fresh_timestamp_without_source"}
    result = transition.run_check(case, "time_source")
    assert result["outcome"] == "workbench_gap" and transition.blocking(result)
    assert result["findings"][0]["known_gap"] == "KG-901"
    assert "Do not change the service" in result["findings"][0]["hint"]


def test_kg002_is_closed_and_marks_nothing_any_more():
    assert transition.known_gaps().get("KG-002", set()) == set()


# ------------------- KG-002: a module-level clock is a source for its dependants

MODULES = """# State 3 — Modules

## `things`

### Owns

Things.

### Knows

- `clock` — the time of a write.

### Must not own

Nothing.

### Depth assessment

Deep.

## `others`

### Owns

Other things.

### Knows

Nothing.

### Must not own

Nothing.

### Depth assessment

Deep.

## `clock`

### Owns

The one reading of the host wall clock.

### Knows

Nothing.

### Must not own

Nothing.

### Depth assessment

Deep.
"""

API2 = API + """
## `public_op:others.record_other`

### State impact

Writes one Thing.
"""

V4_CLOCK = {"schema_version": "spec_workbench_system_clock_backend_closure.v1", "status": "closed",
            "backend_ir": {"kind": "system_clock_backend", "schema_version": 4,
                           "backend": {"emitter": "python_host_naive_utc_clock_v1"},
                           "wiring": {"module": "clock", "function": "utc_now"},
                           "time": {"policy": "rules.time_source_policy", "read": "per_call",
                                    "representation": "naive_utc_datetime"}}}


def _clock_case(tmp_path: Path) -> Path:
    case = _case(tmp_path)
    _write(case / "30_modules.md", MODULES)
    _write(case / "50_public_apis.md", API2)
    _contracts(case, {"record_thing": ("things", "(name: str) -> Thing"),
                      "record_other": ("others", "(name: str) -> Thing"),
                      "utc_now": ("clock", "() -> datetime")})
    _closure(case, {"Thing": {"identity": "entity", "fields": {"created_at": "datetime"}}})
    _write(case / "70_system_clock_closure.json", V4_CLOCK)
    return case


def test_a_module_that_knows_the_v4_clock_has_a_time_source_and_one_that_does_not_has_none(tmp_path):
    import design_closure_gaps

    case = _clock_case(tmp_path)
    assert design_closure_gaps.declared_clock_function(case) == ("clock", "utc_now")
    assert design_closure_gaps.clock_consumers(case) == {"things"}
    result = transition.run_check(case, "time_source")
    assert [(f["code"], f["contract"]) for f in result["findings"]] == [
        ("fresh_timestamp_without_source", "record_other")]


def test_once_imports_are_decided_only_an_importing_module_has_the_clock(tmp_path):
    import design_closure_gaps

    case = _clock_case(tmp_path)
    spec = {"rules": {"system_clock_backend": V4_CLOCK["backend_ir"]},
            "imports": {"module_internal": {"others": {"clock": ["utc_now"]}, "things": {"models": ["Thing"]}}}}
    # Knows says things, the decided imports say others: the imports are the dependency
    assert design_closure_gaps.clock_consumers(case, spec) == {"others"}
    assert design_closure_gaps.clock_consumers(case, {**spec, "imports": {"module_internal": {
        "others": {"clock": ["something_else"]}}}}) == set()


NOTES_V4 = """# State 7 — Notes

record_thing: [OBSERVABLE_OUTCOME] MUST stamp the thing with the current time.
"""


def test_a_decided_empty_imports_table_hands_the_clock_to_nobody(tmp_path):
    # review 5812625435: an explicit empty module_internal is a decision, not
    # "imports undecided"; Knows must not stand in for it
    import design_closure_gaps

    case = _clock_case(tmp_path)
    _write(case / "80_notes.md", NOTES_V4)
    assert design_closure_gaps.clock_consumers(case) == {"things"}          # undecided: Knows
    _write(case / "global_spec.json", {"rules": {"system_clock_backend": V4_CLOCK["backend_ir"]},
                                       "imports": {"module_internal": {}}})
    assert design_closure_gaps.decided_imports(case, design_closure_gaps.load_spec(case)) == {}
    assert design_closure_gaps.clock_consumers(case, design_closure_gaps.load_spec(case)) == set()
    time_source = transition.run_check(case, "time_source")
    assert sorted(f["contract"] for f in time_source["findings"]) == ["record_other", "record_thing"]
    ambient = transition.run_check(case, "ambient_time")
    assert [(f["code"], f["contract"]) for f in ambient["findings"]] == [("ambient_time_note", "record_thing")]


def test_the_imports_closure_table_is_the_authoritative_decision(tmp_path):
    import design_closure_gaps

    case = _clock_case(tmp_path)
    _write(case / "80_notes.md", NOTES_V4)
    # a table that decides nothing about the clock: no consumer, whatever Knows says
    _write(case / "65_imports.json", {"schema_version": "x", "scopes": {"things.record_thing": {"uses": []}}})
    assert design_closure_gaps.clock_consumers(case) == set()
    assert len(transition.run_check(case, "time_source")["findings"]) == 2
    assert transition.run_check(case, "ambient_time")["outcome"] == "open"
    # the table decides that record_thing calls the clock: things is a consumer, others is not
    _write(case / "65_imports.json", {"schema_version": "x", "scopes": {"things.record_thing": {"uses": [
        {"symbol": "utc_now", "provider": "clock", "as": "calls", "basis": "note"}]}}})
    assert design_closure_gaps.clock_consumers(case) == {"things"}
    assert [f["contract"] for f in transition.run_check(case, "time_source")["findings"]] == ["record_other"]
    assert transition.run_check(case, "ambient_time")["outcome"] == "closed"


def test_without_a_declared_module_level_clock_nothing_is_a_source(tmp_path):
    import design_closure_gaps

    case = _clock_case(tmp_path)
    (case / "70_system_clock_closure.json").unlink()
    assert design_closure_gaps.clock_consumers(case) == set()
    assert len(transition.run_check(case, "time_source")["findings"]) == 2
    open_closure = dict(V4_CLOCK, status="open")
    _write(case / "70_system_clock_closure.json", open_closure)
    assert design_closure_gaps.clock_consumers(case) == set()


def test_the_state6_contract_gate_recognises_the_same_dependants(tmp_path):
    import design_stage6_contracts

    case = _clock_case(tmp_path)
    rows = [{"function": f, "signature": s, "module": f"module:{m}", "resolved": True}
            for f, (m, s) in {"record_thing": ("things", "(name: str) -> Thing"),
                              "record_other": ("others", "(name: str) -> Thing")}.items()]
    found = design_stage6_contracts._time_source_findings(case, rows)
    assert [f["contract"] for f in found] == ["record_other"]


# ------------------------------------- 3. the round is given its layer

class LayerProvider:
    """Reviews from a script; every topic judged indifferent; keeps what it was asked."""

    name = "fake"

    def __init__(self, reviews):
        self.reviews = list(reviews)
        self.instructions: list[str] = []
        self.judged: list[str] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            ids = [line.split(":", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                   if line[:1] == "T"]
            return json.dumps({"judgements": [{"id": i, "kind": "indifferent", "why": "no one acts"} for i in ids]}), {}
        if instruction.startswith("You receive the open points"):
            keys = [line.split(": ", 1)[0] for line in text.splitlines()]
            return json.dumps({"groups": [{"topic": "one", "members": keys}]}), {}
        self.instructions.append(instruction)
        return json.dumps({"open_points": self.reviews.pop(0)}), {}


def _ask(case, points=None):
    provider = LayerProvider([list(points or []), list(points or []), []])
    return service.ask_round(case, 2, provider), provider


POINT = {"subject": "A01", "unit": "A01", "kind": "gap", "text": "counted once", "question": "how?"}


def test_the_state2_round_is_asked_with_what_it_owns_receives_carries_and_its_findings(tmp_path):
    case = _case(tmp_path, "- INV-001: a thing counted twice is refused.")
    summary, provider = _ask(case, [POINT])
    asked = provider.instructions[0]
    assert "The transition of State 2" in asked
    assert "where time comes from" in asked                       # owns
    assert "-> state6_exact_contracts (confirmed by time_source)" in asked   # carries
    assert "[open] invariant_without_required_test" in asked      # its own check, now
    assert "it is not the history you give" in asked
    assert "DETERMINISTIC RESULTS AT THIS TRANSITION" in provider.judged[0]
    assert summary["layer"]["ready"] is False and summary["transition_ready"] is False
    assert {"check": "invariant_tests", "from": "state2_rules_decisions", "outcome": "open", "findings": 1} \
        in summary["layer"]["results"]


CHECK_SCRIPT = """def test_counted_once():
    store = Store()
    store.record("a")
    assert store.record("a") is REFUSED  # INV-001 only: nothing here lowers a count
"""


def _factory_with_check(tmp_path: Path, case: Path) -> Path:
    import yaml

    factory = tmp_path / "factory"
    (factory / "verification" / "configs").mkdir(parents=True)
    _write(factory / "verification" / "counts_once_check.py", CHECK_SCRIPT)
    _write(factory / "verification" / "configs" / "Demo.yaml", yaml.safe_dump({"checks": {"commands": [
        {"name": "counts_once", "cwd": "../..", "command": ["python", "verification/counts_once_check.py"]}]}}))
    _write(case / "90_factory_target.json", {"factory_project": "Demo"})
    return factory


class SufficiencyProvider(LayerProvider):
    """The judge finds the binding insufficient: the check asserts INV-001 only."""

    ITEM = "- INV-001, INV-002: refused. [witness: verification:counts_once]"

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            ids = [line.split(":", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                   if line[:1] == "T"]
            verdict = {"kind": "consequential_gap", "quotes": [self.ITEM],
                       "divergence": "a lower count is accepted or refused; the owner notices",
                       "witness": {"initial": "a thing counted twice", "events": ["the owner lowers the count"],
                                   "outcomes": ["refused", "accepted"], "observer": "the owner",
                                   "basis": ["## Accepted decision A01 — things are counted"]}}
            return json.dumps({"judgements": [{"id": i, **verdict} for i in ids]}), {}
        return super().complete(instruction, text)


def test_the_round_judges_a_binding_on_the_check_content_it_is_given(tmp_path, monkeypatch):
    # review r4501731322: a check's name proves it exists, not what it asserts
    _clean_gate(monkeypatch)
    case = _case(tmp_path, SufficiencyProvider.ITEM)
    factory = _factory_with_check(tmp_path, case)
    monkeypatch.setenv("SPEC_WORKBENCH_FACTORY_ROOT", str(factory))
    assert transition.run_check(case, "witness_material")["outcome"] == "closed"
    point = {**POINT, "text": SufficiencyProvider.ITEM, "question": "does counts_once assert INV-002?"}
    provider = SufficiencyProvider([[point], [point], []])
    summary = service.ask_round(case, 2, provider)
    asked = provider.instructions[0]
    assert "Evidence of the bindings under review" in asked
    assert "A01 binds INV-001, INV-002 to verification:counts_once" in asked
    assert "INV-001 only: nothing here lowers a count" in asked          # the check's own content
    assert "INV-001 only: nothing here lowers a count" in provider.judged[0]
    digest = __import__("hashlib").sha256(CHECK_SCRIPT.encode()).hexdigest()
    assert summary["layer"]["materials"] == [{"decision": "A01", "witness": "verification:counts_once",
                                              "status": "available",
                                              "files": [{"path": "verification/counts_once_check.py",
                                                         "sha256": digest}]}]
    assert summary["blocked_units"] == ["A01"] and summary["clear"] is False


def test_a_binding_whose_check_cannot_be_read_is_not_judged_sufficient(tmp_path, monkeypatch):
    _clean_gate(monkeypatch)
    case = _case(tmp_path, SufficiencyProvider.ITEM)
    _write(case / "90_factory_target.json", {"factory_project": "Demo"})
    monkeypatch.setenv("SPEC_WORKBENCH_FACTORY_ROOT", str(tmp_path / "no-factory"))
    result = transition.run_check(case, "witness_material")
    assert result["outcome"] == "not_checked" and transition.blocking(result)
    assert [f["code"] for f in result["findings"]] == ["witness_material_not_checked"]
    summary, provider = _ask(case)
    assert "NOT CHECKED:" in provider.instructions[0]
    assert summary["transition_ready"] is False


# ------------------------------- 4. a closed round hides no blocking result

def _clean_gate(monkeypatch, findings=()):
    # the State 2 lint of this tiny case asks for a security review; the gate
    # itself is tested in test_design_lint.py, here only its results matter
    monkeypatch.setattr(transition, "_gate_findings", lambda project, state: list(findings))


def test_a_state_closed_by_its_rounds_is_not_ready_while_its_transition_stops(tmp_path, capsys, monkeypatch):
    _clean_gate(monkeypatch)
    case = _case(tmp_path, "- INV-001: a thing counted twice is refused.")
    _ask(case)
    summary, _ = _ask(case)
    assert summary["closed"] is True and summary["transition_ready"] is False
    result = service.status(case, 2, with_transition=True)
    assert result["closed"] is True and result["ready"] is False
    assert "the transition does not hold" in result["reason"]
    assert [f["code"] for f in result["transition"]["findings"]] == ["invariant_without_required_test"]
    assert design_questions.main(["status", str(case), "--state", "2"]) == 1
    assert "ready=false" in capsys.readouterr().out


# ------------------------------ 5. execution a backend emits is recognised

FLOWS = """# State 4 — Flows

## `flow:serve_thing`

1. The route calls `capability:things.get_thing`.
2. The store begins a transaction, creating the table:
   `capability:thing_repository.create_thing_schema`.
"""


def _flow_case(tmp_path: Path, notes: str = "", router: bool = True) -> Path:
    case = _case(tmp_path)
    _write(case / "40_flows.md", FLOWS)
    _contracts(case, {
        "get_thing": ("things", "(store: ThingStore, name: str) -> Thing"),
        "ThingStore.__init__": ("thing_store", "(self, database_url: str) -> None"),
        "ThingStore.begin": ("thing_store", "(self) -> ThingTransaction"),
        "ThingTransaction.things": ("thing_store", "(self) -> ThingRepository"),
        "create_thing_schema": ("thing_repository", "(connection: object) -> None"),
    })
    _write(case / "70_persistence_closure.json", {"schema_version": "spec_workbench_persistence_closure.v1",
                                                  "status": "closed", "backend_ir": {"repositories": [{
        "repository": "SqliteThingRepository", "module": "thing_repository",
        "schema_function": "create_thing_schema", "methods": []}]}})
    _write(case / "70_sqlite_unit_of_work_closure.json", {
        "schema_version": "spec_workbench_sqlite_unit_of_work_backend_closure.v1", "status": "closed",
        "backend_ir": {"kind": "sqlite_unit_of_work_backend", "schema_version": 1,
                       "wiring": {"module": "thing_store", "error_class": "StoreError", "store_class": "ThingStore",
                                  "transaction_class": "ThingTransaction", "context_interface": "ThingContext"},
                       "accessors": [{"accessor": "things", "repository": "SqliteThingRepository"}]}})
    if router:
        _write(case / "global_spec.json", {"rules": {"http_router_backend": {
            "routes": [{"delegate": {"function": "get_thing"}}]}}})
    _write(case / "80_notes.md", notes)
    return case


def test_a_schema_the_unit_of_work_backend_creates_on_begin_is_reached_without_a_note_of_its_own(tmp_path):
    # client-portal: 12 create_*_schema steps are called by PortalStore.begin,
    # emitted by sqlite_unit_of_work_backend; the caller wrote store.begin()
    case = _flow_case(tmp_path, "get_thing: [ORCHESTRATION] MUST open its transaction with store.begin().\n")
    report = flow_closure.coverage(case)
    assert report["findings"] == [] and report["summary"]["reachability"] == "checked"


def test_a_dotted_class_method_in_a_note_is_a_call(tmp_path):
    case = _flow_case(tmp_path, "get_thing: [ORCHESTRATION] MUST call ThingStore.begin once.\n")
    assert flow_closure.coverage(case)["findings"] == []


def test_without_a_caller_of_begin_the_backend_step_stays_unreached(tmp_path):
    case = _flow_case(tmp_path, "get_thing: [ORCHESTRATION] MUST return the thing.\n")
    report = flow_closure.coverage(case)
    assert [(f["code"], f["capability"]) for f in report["findings"]] == [
        ("flow_capability_unreached", "capability:thing_repository.create_thing_schema")]


def test_flow_steps_at_state6_need_no_notes(tmp_path):
    case = _flow_case(tmp_path, router=False)
    (case / "80_notes.md").unlink()
    assert transition.run_check(case, "flow_steps")["outcome"] == "closed"


# ---------------------------- 6. a fix does not reopen what was closed

def test_a_changed_deterministic_result_reopens_no_unit(tmp_path, monkeypatch):
    # rounds are asked while the gate reports a finding; the finding goes away
    # (a tool fix, a later artifact): the closed units stay closed
    _clean_gate(monkeypatch, [{"code": "some_gate_finding", "severity": "error", "message": "x"}])
    case = _case(tmp_path)
    _ask(case)
    summary, _ = _ask(case)
    assert summary["closed"] is True and summary["transition_ready"] is False
    _clean_gate(monkeypatch)
    after = service.status(case, 2, with_transition=True)
    assert after["closed"] is True and after["open_units"] == [] and after["ready"] is True
    assert after["transition"]["digest"] != summary["layer"]["digest"]


def test_binding_one_invariant_reopens_only_its_decision(tmp_path):
    case = _case(tmp_path)
    _ask(case)
    _ask(case)
    text = (case / "02_rules.md").read_text()
    _write(case / "02_rules.md", text.replace("- INV-002: a lower count is refused.",
                                              "- INV-002: a lower count is refused. [witness: workbench:state2_rules_decisions]"))
    assert service.status(case, 2)["open_units"] == ["A01"]
    summary, provider = _ask(case)
    assert summary["scope"] == ["A01"]
    assert "- A02" not in provider.instructions[0]


# ------------------- State 7: the module review is asked against its obligations

def test_a_state7_module_review_is_asked_against_the_obligations_it_takes_part_in(tmp_path, monkeypatch):
    # review r4501731320: the State 7 reviewer must see the flow and time
    # obligations its module executes, beside the Factory's own prompt
    import test_design_questions_gates as gates

    case, factory = gates._notes_case(tmp_path, monkeypatch)
    _write(case / "40_flows.md", "# State 4 — Flows\n\n## `flow:serve_thing`\n\n"
                                 "1. `capability:store.save` stores the thing.\n")
    context = {"state": 7, "owns": [], "carries": [], "gate_findings": [], "materials": [], "ready": False,
               "results": [{"check": "flow_reachability", "from": "state4_reviewed_flows", "outcome": "open",
                            "obligation": "every step is called", "findings": [
                                {"code": "flow_capability_unreached", "flow": "flow:serve_thing",
                                 "capability": "capability:store.save", "message": "x"}]}]}
    monkeypatch.setattr(service, "layer_context", lambda case, state: context)
    point = {"subject": "save", "kind": "unmet_obligation", "text": "- save: [PRECONDITION] The record fits the size limit.",
             "question": "which note calls save in flow:serve_thing?"}
    provider = gates.Provider(points=[point])
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    store = [i for i, t in zip(provider.instructions, provider.inputs) if "Module: store" in t]
    surface = [i for i, t in zip(provider.instructions, provider.inputs) if "Module: surface" in t]
    assert store and all("flow:serve_thing needs capability:store.save" in i for i in store)
    assert surface and not any("flow:serve_thing" in i for i in surface)   # limited to the module
    # the Factory prompt is given and kept as the Factory built it
    prompt = service.state_texts(case, 7, factory).units["store"]["text"]
    assert any(t.endswith(prompt) and "flow:serve_thing" not in t for t in provider.inputs if "Module: store" in t)
    kept = service.rounds_dir(case, 7) / summary["round"] / "prompts" / "store.txt"
    assert kept.read_text(encoding="utf-8") == prompt
    assert any("OBLIGATIONS THIS MODULE TAKES PART IN" in j and "capability:store.save" in j for j in provider.judged)
    assert summary["transition_ready"] is False


# ------------- review 5812269729: workbench gates and changed evidence

def test_a_workbench_binding_gives_the_round_the_gate_implementation(tmp_path, monkeypatch):
    # review r4501770397: the gate's name was given, not what it checks; flows
    # does not prove "a thing is counted once", and the round must see that
    _clean_gate(monkeypatch)
    case = _case(tmp_path, "- INV-001, INV-002: refused. [witness: workbench:flows]")
    assert transition.run_check(case, "witness_material")["outcome"] == "closed"
    summary, provider = _ask(case)
    asked = provider.instructions[0]
    assert "A01 binds INV-001, INV-002 to workbench:flows" in asked
    assert "def coverage(project: Path, *, reachability: bool = True)" in asked   # flow_closure's own code
    source = (Path(flow_closure.__file__)).read_text(encoding="utf-8")
    digest = __import__("hashlib").sha256(source.encode()).hexdigest()
    assert summary["layer"]["materials"][0]["files"] == [{"path": "tools/flow_closure.py", "sha256": digest}]


def test_a_facade_check_resolves_to_the_implementation_it_delegates_to():
    files, _ = design_decision_witness.workbench_sources("closure_gaps")
    assert [f["path"] for f in files] == ["tools/assembly_workbench/checks.py#_closure_gap_coverage",
                                          "tools/design_closure_gaps.py"]
    assert design_decision_witness.workbench_sources("no_such_gate") == ([], "no_such_gate is not a Workbench check")


def test_an_unknown_workbench_gate_is_not_checked(tmp_path):
    case = _case(tmp_path, "- INV-001, INV-002: refused. [witness: workbench:no_such_gate]")
    result = transition.run_check(case, "witness_material")
    assert result["outcome"] == "not_checked"


def test_a_changed_check_reopens_only_the_decision_bound_to_it(tmp_path, monkeypatch):
    # review r4501770401: A01 closed on a test of INV-001; the external test
    # loses its assertion, the design text does not change
    _clean_gate(monkeypatch)
    case = _case(tmp_path, SufficiencyProvider.ITEM)
    factory = _factory_with_check(tmp_path, case)
    monkeypatch.setenv("SPEC_WORKBENCH_FACTORY_ROOT", str(factory))
    _ask(case)
    _ask(case)
    assert service.status(case, 2, with_transition=True)["ready"] is True
    _write(factory / "verification" / "counts_once_check.py", CHECK_SCRIPT.replace("assert ", "# was: assert "))
    result = service.status(case, 2, with_transition=True)
    assert result["open_units"] == ["A01"] and result["evidence_changed"] == ["A01"]
    assert result["closed"] is False and result["ready"] is False
    summary, provider = _ask(case)
    assert summary["scope"] == ["A01"] and summary["evidence_reopened"] == ["A01"]
    assert "Units closed on their text whose evidence changed: A01" in provider.instructions[0]
    assert "# was: assert" in provider.instructions[0]
    assert summary["closed"] is False                  # one review on the new evidence is not two
    summary, _ = _ask(case)
    assert summary["closed"] is True and service.status(case, 2)["open_units"] == []


class PrecedentProvider:
    """Groups points by subject (the topic is the subject); judges each topic
    with `verdicts[subject]`; keeps what the judge was shown."""

    name = "fake"

    def __init__(self, points, verdicts):
        self.points, self.verdicts = points, verdicts
        self.instructions: list[str] = []
        self.judged: list[str] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            judgements = []
            for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines():
                if line[:1] == "T":
                    tid, subject = line.split(": ", 1)
                    judgements.append({"id": tid, **self.verdicts[subject]})
            return json.dumps({"judgements": judgements}), {}
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                groups.setdefault(rest[1:rest.index("]")], []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        self.instructions.append(instruction)
        return json.dumps({"open_points": list(self.points)}), {}


def test_a_judgement_on_old_evidence_is_no_precedent_after_the_check_changes(tmp_path, monkeypatch):
    # review r4501801651: the binding was judged sufficient, the test then lost
    # its assertion; the old "answered" must not close A01 again as judged_before
    _clean_gate(monkeypatch)
    case = _case(tmp_path, SufficiencyProvider.ITEM)
    factory = _factory_with_check(tmp_path, case)
    monkeypatch.setenv("SPEC_WORKBENCH_FACTORY_ROOT", str(factory))
    points = [{"subject": "binding", "unit": "A01", "kind": "gap", "text": "x", "question": "is counts_once enough?"},
              {"subject": "naming", "unit": "A02", "kind": "gap", "text": "y", "question": "which name?"}]
    answered = {"binding": {"kind": "answered", "quotes": [SufficiencyProvider.ITEM]},
                "naming": {"kind": "answered", "quotes": ["A thing has a name."]}}
    for _ in range(2):
        summary = service.ask_round(case, 2, PrecedentProvider(points, answered))
    assert summary["closed"] is True
    before = {p["topic"]: p for p in service._precedents(case, 2)}
    assert set(before) == {"binding", "naming"}

    _write(factory / "verification" / "counts_once_check.py", CHECK_SCRIPT.replace("assert ", "# was: assert "))
    stale = before["binding"]["id"]
    provider = PrecedentProvider(points[:1], {"binding": {"kind": "judged_before", "precedent": stale}})
    summary = service.ask_round(case, 2, provider)
    assert summary["scope"] == ["A01"]
    shown = provider.judged[0].split("=== TOPICS TO JUDGE ===")[0]
    assert "Reopened because their evidence changed: A01" in shown
    prior = shown.split("=== PRIOR JUDGEMENTS (non-blocking, verified) ===")[1] if "PRIOR JUDGEMENTS" in shown else ""
    assert ": binding" not in prior                 # the judgement on the old evidence is not offered
    assert ": naming" in prior                      # an unaffected decision keeps its precedent
    judgement = summary["topics"][0]["judgement"]
    assert judgement["verified"] is False and judgement["blocking"] is True
    assert summary["blocked_units"] == ["A01"]


def test_a_v5_clock_is_read_by_its_wall_operation_and_handed_to_its_dependants(tmp_path):
    # system_clock_backend/v5 (KG-003): the wall operation is wall_clock_function
    import design_closure_gaps

    case = _clock_case(tmp_path)
    v5 = {**V4_CLOCK, "backend_ir": {**V4_CLOCK["backend_ir"], "schema_version": 5,
                                     "backend": {"emitter": "python_host_naive_utc_and_elapsed_clock_v1"},
                                     "wiring": {"module": "clock", "wall_clock_function": "utc_now",
                                                "elapsed_clock_function": "monotonic_seconds"}}}
    _write(case / "70_system_clock_closure.json", v5)
    assert design_closure_gaps.declared_clock_function(case) == ("clock", "utc_now")
    assert design_closure_gaps.clock_consumers(case) == {"things"}
    assert [f["contract"] for f in transition.run_check(case, "time_source")["findings"]] == ["record_other"]
