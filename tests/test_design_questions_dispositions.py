"""One round per change, closed by the author's dispositions.

Owner decision 2026-11-08 (#147, comment 6721261089): a state of States 0-7
is closed when the latest round on its current text has no open
contradiction and every other judged topic of that round has an author
disposition — fixed (with the change), carried (to a named later layer, with
what it must decide) or accepted (with the reason). "Two clear rounds on the
same text" is gone. States closed under the old rule stay closed.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import design_authoring_next
import design_questions
import transition
from questions_workbench import documents, prompts, service, units

RULES = """# State 2 — Demo rules

## Accepted decision A01 — first

Rule one keeps every thing.

## Accepted decision A02 — second

Rule two drops a thing.
"""

WITNESS = {"initial": "a thing exists", "events": ["the owner reads it"], "outcomes": ["a", "b"],
           "observer": "the owner", "basis": ["Rule one keeps every thing."]}
VERDICTS = {
    "gap": {"kind": "consequential_gap", "quotes": ["Rule one keeps every thing."], "divergence": "a or b; the owner notices",
            "witness": WITNESS},
    "contradiction": {"kind": "contradiction", "quotes": ["Rule one keeps every thing.", "Rule two drops a thing."], "witness": WITNESS},
    "hypothesis": {"kind": "contradiction", "quotes": ["Rule one keeps every thing.", "Rule two drops a thing."]},   # no witness
    "answered": {"kind": "answered", "quotes": ["Rule one keeps every thing."]},
    "deferred": {"kind": "consequential_gap", "divergence": "a or b; the owner notices"},
}


class Provider:
    """Reviews from a script; one topic per subject; each judged by VERDICTS[subject]."""

    name = "fake"

    def __init__(self, points: list[dict] | None = None):
        self.points = list(points or [])
        self.instructions: list[str] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            judgements = []
            for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines():
                if line[:1] == "T":
                    tid, subject = line.split(": ", 1)
                    judgements.append({"id": tid, **VERDICTS[subject]})
            return json.dumps({"judgements": judgements}), {}
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                groups.setdefault(rest[1:rest.index("]")], []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        self.instructions.append(instruction)
        return json.dumps({"open_points": list(self.points)}), {}


def point(subject: str, unit: str = "A01") -> dict:
    return {"subject": subject, "unit": unit, "kind": "gap", "text": "Rule one keeps every thing.", "question": f"{subject}?"}


def git(case: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(case), *args], check=True, capture_output=True, text=True).stdout


def make_case(tmp_path: Path, with_git: bool = False) -> Path:
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text("# State 0 — Demo\n\nA product.\n", encoding="utf-8")
    (case / "01_models.md").write_text("# State 1 — Demo models\n\n## Model M01 — Thing\n", encoding="utf-8")
    (case / "02_rules.md").write_text(RULES, encoding="utf-8")
    if with_git:
        git(case, "init", "-q")
        git(case, "config", "user.email", "t@t")
        git(case, "config", "user.name", "t")
        commit(case, "texts")
    return case


def commit(case: Path, message: str) -> str:
    git(case, "add", "-A")
    git(case, "commit", "-q", "--allow-empty", "-m", message)
    return git(case, "rev-parse", "HEAD").strip()


def ask(case: Path, *subjects: str, unit: str = "A01") -> dict:
    points = [point(s, unit) for s in subjects]
    return service.ask_round(case, 2, Provider(points))


@pytest.fixture(autouse=True)
def clean_transition(monkeypatch):
    # the transition is tested in test_transition.py; here only the rounds matter
    monkeypatch.setattr(service, "layer_context", lambda case, state: {
        "state": state, "owns": ["what State 2 decides"], "carries": [], "results": [], "gate_findings": [],
        "ready": True, "verdicts": [], "carried_in": []})


# ---------------------------------------------------------------- closure

def test_a_state_closes_when_every_gap_and_hypothesis_of_its_round_has_a_disposition(tmp_path):
    case = make_case(tmp_path, with_git=True)
    summary = ask(case, "gap", "hypothesis", "answered")
    kinds = {t["topic"]: t["judgement"]["kind"] for t in summary["topics"]}
    assert kinds == {"gap": "consequential_gap", "hypothesis": "hypothesis", "answered": "answered"}
    assert summary["closed"] is False and summary["open_units"] == ["A01"]
    ids = {t["topic"]: t["id"] for t in summary["topics"]}
    assert summary["awaiting_disposition"] == sorted([ids["gap"], ids["hypothesis"]])   # answered needs none
    service.dispose(case, 2, ids["gap"], "carried", to="6", what="the contracts fix which of a or b is returned")
    status = service.status(case, 2)
    assert status["closed"] is False and status["awaiting_disposition"] == {"A01": [ids["hypothesis"]]}
    service.dispose(case, 2, ids["hypothesis"], "accepted", reason="rule one and rule two never meet in one call")
    status = service.status(case, 2)
    assert status["closed"] is True
    assert status["closed_by"]["single_round"] == len(service.state_texts(case, 2).units)
    assert status["unit_status"]["A01"]["carried"] == [
        {"topic": ids["gap"], "to": 6, "what": "the contracts fix which of a or b is returned"}]
    # no further round on the same text
    with pytest.raises(service.QuestionRoundError, match="nothing to ask"):
        ask(case)


def test_a_gap_without_a_disposition_keeps_its_unit_open_and_is_not_asked_again(tmp_path):
    case = make_case(tmp_path)
    summary = ask(case, "gap")
    assert summary["open_units"] == ["A01"]
    status = service.status(case, 2)
    assert status["closed"] is False and status["needs_round"] == []
    assert status["awaiting_disposition"] == {"A01": ["T1"]}
    assert "wait for the author's disposition" in status["reason"]
    with pytest.raises(service.QuestionRoundError, match="no unit of State 2 needs a round"):
        ask(case, "gap")


def test_a_deferred_gap_needs_a_disposition_too(tmp_path):
    case = make_case(tmp_path)
    summary = ask(case, "deferred")
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is False and judgement["deferred_to"]
    assert summary["awaiting_disposition"] == ["T1"]


def test_an_open_contradiction_blocks_and_takes_no_disposition(tmp_path):
    case = make_case(tmp_path)
    summary = ask(case, "contradiction")
    assert summary["contradiction_units"] == ["A01"] and summary["closed"] is False
    with pytest.raises(service.QuestionRoundError, match="contradiction: it takes no disposition"):
        service.dispose(case, 2, "T1", "accepted", reason="we like it")
    status = service.status(case, 2)
    assert status["contradictions"] == {"A01": ["T1"]} and status["needs_round"] == []
    with pytest.raises(service.QuestionRoundError, match="hold an open contradiction"):
        ask(case)
    # closed by a change of the text and one round on it that no longer raises it
    (case / "02_rules.md").write_text(RULES.replace("Rule one keeps every thing.", "Rule one, as rule two allows."), encoding="utf-8")
    summary = ask(case)
    assert summary["scope"] == ["A01"] and summary["closed"] is True


def test_a_fix_is_reviewed_by_one_round_on_its_change_whose_topics_get_dispositions_in_turn(tmp_path):
    case = make_case(tmp_path, with_git=True)
    summary = ask(case, "gap")
    commit(case, "round-01")
    (case / "02_rules.md").write_text(RULES.replace("Rule one keeps every thing.", "Rule one, refusing b."), encoding="utf-8")
    fix = commit(case, "A01 decides b is refused")
    assert service.dispose(case, 2, "T1", "fixed", ref="HEAD")["ref"] == fix
    status = service.status(case, 2)
    assert status["needs_round"] == ["A01"] and status["changed_units"] == ["A01"]
    provider = Provider([{**point("gap"), "text": "Rule one, refusing b."}])
    summary = service.ask_round(case, 2, provider)
    assert summary["scope"] == ["A01"] and summary["changed_units"] == ["A01"]
    assert "+Rule one, refusing b." in provider.instructions[0]          # reviewed on the diff
    assert summary["awaiting_disposition"] == ["T1"]                     # its own topic in turn
    service.dispose(case, 2, "T1", "accepted", reason="refusing b is the owner's choice")
    assert service.status(case, 2)["closed"] is True


def test_fixed_needs_a_commit_that_changes_the_case_after_the_round(tmp_path):
    case = make_case(tmp_path, with_git=True)
    before = git(case, "rev-parse", "HEAD").strip()
    ask(case, "gap")
    commit(case, "round-01")
    with pytest.raises(service.QuestionRoundError, match="needs --ref"):
        service.dispose(case, 2, "T1", "fixed", ref="")
    with pytest.raises(service.QuestionRoundError, match="not a commit"):
        service.dispose(case, 2, "T1", "fixed", ref="no-such-ref")
    with pytest.raises(service.QuestionRoundError, match="does not follow the round"):
        service.dispose(case, 2, "T1", "fixed", ref=before)
    empty = commit(case, "nothing")
    with pytest.raises(service.QuestionRoundError, match="changes nothing"):
        service.dispose(case, 2, "T1", "fixed", ref=empty)


@pytest.mark.parametrize("to, ok", [("3", True), ("state8", True), ("generation", True),
                                    ("factory_checks", True), ("deploy", True),
                                    ("2", False), ("1", False), ("9", False), ("later", False), ("6x", False)])
def test_carried_needs_a_later_layer_from_the_closed_set_and_what_it_decides(tmp_path, to, ok):
    case = make_case(tmp_path)
    ask(case, "gap")
    if ok:
        entry = service.dispose(case, 2, "T1", "carried", to=to, what="decide a or b")
        assert entry["to"] in (3, 8, "generation", "factory_checks", "deploy")
    else:
        with pytest.raises(service.QuestionRoundError, match="carried to"):
            service.dispose(case, 2, "T1", "carried", to=to, what="decide a or b")
    with pytest.raises(service.QuestionRoundError, match="--what"):
        service.dispose(case, 2, "T1", "carried", to="6", what="  ")


def test_accepted_needs_a_reason(tmp_path):
    case = make_case(tmp_path)
    ask(case, "gap")
    with pytest.raises(service.QuestionRoundError, match="--reason"):
        service.dispose(case, 2, "T1", "accepted", reason=" ")
    assert service.dispose(case, 2, "T1", "accepted", reason="the owner's choice")["reason"] == "the owner's choice"
    kept = json.loads((service.rounds_dir(case, 2) / "round-01" / service.DISPOSITIONS_FILE).read_text())
    assert kept["dispositions"][0]["topic_text"] == "gap"


def test_a_topic_that_needs_nothing_and_an_unknown_topic_are_refused(tmp_path):
    case = make_case(tmp_path)
    ask(case, "answered")
    with pytest.raises(service.QuestionRoundError, match="needs no disposition"):
        service.dispose(case, 2, "T1", "accepted", reason="r")
    with pytest.raises(service.QuestionRoundError, match="has no topic T9"):
        service.dispose(case, 2, "T9", "accepted", reason="r")


def test_a_disposition_for_one_unit_leaves_the_others_of_the_topic_open(tmp_path):
    case = make_case(tmp_path)
    loose = {"subject": "gap", "kind": "gap", "text": "Rule one keeps every thing.", "question": "?"}   # names no unit
    summary = service.ask_round(case, 2, Provider([loose]))
    assert set(summary["open_units"]) == set(summary["scope"])
    service.dispose(case, 2, "T1", "accepted", unit="A01", reason="A01 is fine")
    assert "A01" not in service.status(case, 2)["open_units"]
    with pytest.raises(service.QuestionRoundError, match="does not concern unit"):
        service.dispose(case, 2, "T1", "accepted", unit="A77", reason="r")


def test_the_cli_disposes_and_lists_what_was_carried(tmp_path, capsys):
    case = make_case(tmp_path)
    ask(case, "gap")
    assert design_questions.main(["dispose", str(case), "--state", "2", "--topic", "T1",
                                  "--carried", "deploy", "--what", "the host decides the retention"]) == 0
    assert design_questions.main(["status", str(case), "--state", "2"]) == 0
    out = capsys.readouterr().out
    assert "closed=true" in out and "carried T1 -> deploy" in out
    assert design_questions.main(["carried", str(case), "--to", "deploy"]) == 0
    assert "State 2 round-01 T1 -> deploy: the host decides the retention" in capsys.readouterr().out
    assert design_questions.main(["dispose", str(case), "--state", "2", "--topic", "T1",
                                  "--carried", "1", "--what", "x"]) == 2


def test_a_carried_item_reaches_the_receiving_state_and_authoring_next(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    ask(case, "gap")
    service.dispose(case, 2, "T1", "carried", to="3", what="which module owns rule one")
    assert service.carried_items(case, to=3)[0]["what"] == "which module owns rule one"
    assert service.status(case, 3)["carried_in"][0]["topic"] == "T1"
    monkeypatch.undo()   # the real transition of State 3
    assert transition.carried_in(case, 3)[0]["what"] == "which module owns rule one"
    context = {"state": 3, "owns": [], "carries": [], "results": [], "gate_findings": [],
               "carried_in": transition.carried_in(case, 3)}
    assert "[carried by the author] which module owns rule one (State 2 round-01 T1)" in prompts.layer_scope(context)
    sequence = design_authoring_next.load_sequence()
    payload = design_authoring_next._result(sequence=sequence, project=case, project_text="demo",
                                            phase="state3_module_responsibilities", blocked=False, reason="r")
    assert payload["carried_dispositions"]["received"][0]["what"] == "which module owns rule one"
    assert payload["carried_dispositions"]["by_layer"] == {"state3": 1}


# ---------------------------------------------------------------- old closures

def _legacy(case: Path, number: int, scope: list[str], topics: list[dict] | None = None,
            blocked: list[str] | None = None) -> None:
    """A round kept under the two-clear-rounds rule (no `closure` in its summary)."""
    read = service.state_texts(case, 2)
    directory = service.rounds_dir(case, 2) / f"round-{number:02d}"
    directory.mkdir(parents=True)
    (directory / "summary.json").write_text(json.dumps({
        "schema_version": service.SCHEMA, "state": 2, "round": directory.name, "documents": read.digests,
        "reviews": 3, "points": [0, 0, 0], "judge": {"provider": "fake"}, "repeated_topics": len(topics or []),
        "blocking_topics": 0, "clear": not blocked, "closed": False, "topics": topics or [],
        "units": {k: u["digest"] for k, u in read.units.items()}, "scope": scope,
        "blocked_units": blocked or []}), encoding="utf-8")


def test_a_unit_closed_by_two_clear_rounds_stays_closed_under_the_new_rule(tmp_path):
    case = make_case(tmp_path)
    keys = list(service.state_texts(case, 2).units)
    # its last round judged a deferred gap and a hypothesis: the new rule would ask dispositions
    hypothesis = {"topic": "h", "runs": [1, 2], "id": "T1", "units": ["A01"],
                  "judgement": {"kind": "hypothesis", "verified": True, "blocking": False}}
    _legacy(case, 1, keys)
    _legacy(case, 2, keys, [hypothesis])
    status = service.status(case, 2)
    assert status["closed"] is True and status["closed_by"]["two_clear_rounds"] == len(keys)
    assert status["awaiting_disposition"] == {}
    with pytest.raises(service.QuestionRoundError, match="nothing to ask"):
        ask(case)


def test_a_unit_with_one_old_clear_round_closes_by_the_new_rule_with_its_dispositions(tmp_path):
    case = make_case(tmp_path)
    keys = list(service.state_texts(case, 2).units)
    gap = {"topic": "g", "runs": [1, 2], "id": "T1", "units": ["A01"],
           "judgement": {"kind": "consequential_gap", "verified": True, "blocking": True}}
    _legacy(case, 1, keys, [gap], blocked=["A01"])
    status = service.status(case, 2)
    assert status["open_units"] == ["A01"] and status["awaiting_disposition"] == {"A01": ["T1"]}
    service.dispose(case, 2, "T1", "accepted", round_name="round-01", reason="the owner's choice")
    assert service.status(case, 2)["closed"] is True
