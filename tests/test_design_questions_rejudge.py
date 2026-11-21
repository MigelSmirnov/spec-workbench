"""A verdict kept under other judge rules is checked again on an unchanged unit.

A recorded State 7 verdict was revisited only when the module's prompt changed
(units.unit_state). client-portal `financial_policy` round 23 T1-T3 are three
§2 "violations" of the Factory's own `model_copy` line; #175 keeps such a
passage as `generator_text`, but the module's prompt never changed, so the
verdicts kept blocking FA019. Every round now keeps the judge rules its
verdicts were checked under (judge.RULES_VERSION, the standard sections'
digest), `status` names the modules held open by verdicts kept under other
rules, and `design_questions.py rejudge` applies `judge.check` to the round's
kept judge answers again, keeping the result as a new round and the old round
as it was written."""
from __future__ import annotations

import json

import pytest

import design_questions
from questions_workbench import judge, service, units
from test_design_questions_gates import Provider, _notes_case, _point
from test_design_questions_standard import BOILERPLATE, PASSAGE, RULE, Judging, QuotingBoilerplate, _rule_point


def _boilerplate_case(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    (factory / "tools/generate_agent.py").write_text(
        "def build_prompt(local_spec, models_code=None):\n"
        "    return ('Module: ' + local_spec['module_name'] + '\\nNOTES:\\n' + '\\n'.join(local_spec['notes'])\n"
        f"            + '\\n\\n' + {BOILERPLATE!r} + '\\n')\n", encoding="utf-8")
    return case, factory


def _under_old_rules(monkeypatch):
    """Judge as before #175: a violation anywhere in the prompt blocks, and the
    round keeps no judge rules (rounds before versioning)."""
    real = judge.check

    def old(*args, **kwargs):
        kwargs.pop("violation_texts", None)
        return real(*args, **kwargs)

    monkeypatch.setattr(judge, "check", old)
    return real


def _asked_under_old_rules(case, factory, monkeypatch):
    real = _under_old_rules(monkeypatch)
    provider = QuotingBoilerplate([{**_point("model_copy", text=BOILERPLATE), "kind": "standard_violation",
                                    "rule": RULE, "section": "2"}], {"model_copy": RULE})
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    path = service.rounds_dir(case, 7) / summary["round"] / "summary.json"
    kept = json.loads(path.read_text(encoding="utf-8"))
    kept.pop("judge_rules")
    path.write_text(json.dumps(kept), encoding="utf-8")
    monkeypatch.setattr(judge, "check", real)
    return summary, path


def test_a_round_keeps_the_judge_rules_its_verdicts_were_checked_under(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    summary = service.ask_round(case, 7, Provider(), factory_root=factory)
    assert summary["judge_rules"]["version"] == judge.RULES_VERSION
    assert summary["judge_rules"] == service._current_rules(7) and summary["judge_rules"]["standard"]
    assert judge.rules_record(None) == {"version": judge.RULES_VERSION, "standard": None}


def test_a_module_held_by_verdicts_of_older_rules_closes_by_a_rejudgement(tmp_path, monkeypatch):
    """client-portal State 7 round 23, `financial_policy` T1-T3."""
    case, factory = _boilerplate_case(tmp_path, monkeypatch)
    summary, path = _asked_under_old_rules(case, factory, monkeypatch)
    assert summary["blocked_units"] == ["store", "surface"]
    written = path.read_bytes()
    result = service.status(case, 7, factory)
    assert result["closed"] is False and result["needs_round"] == []
    assert result["needs_rejudge"] == ["store", "surface"] and "design_questions.py rejudge" in result["reason"]
    with pytest.raises(service.QuestionRoundError, match="no unit of State 7 needs a round"):
        service.ask_round(case, 7, Provider(), factory_root=factory)

    again = service.rejudge(case, 7, "store", factory)
    assert again["round"] == "round-02" and again["scope"] == ["store"] and again["reviews"] == 0
    assert again[units.REJUDGE] == {"of": "round-01", "unit": "store", "judge_rules": None}
    assert again["judge_rules"] == service._current_rules(7)
    topic = again["topics"][0]
    assert topic["id"] == "store:T1" and topic["judgement"]["kind"] == judge.GENERATOR_TEXT
    assert topic["judgement"]["blocking"] is False
    assert topic["rejudged"]["round"] == "round-01"
    assert topic["rejudged"]["judgement"]["kind"] == "standard_violation"
    assert again["open_units"] == ["surface"] and again["closed"] is False
    assert path.read_bytes() == written  # the earlier round stays as it was written
    round_dir = service.rounds_dir(case, 7) / "round-02"
    assert (round_dir / "prompts" / "store.txt").is_file() and not list(round_dir.glob("review-*"))

    result = service.status(case, 7, factory)
    assert result["open_units"] == ["surface"] and result["needs_rejudge"] == ["surface"]
    assert design_questions.main(["rejudge", str(case), "--state", "7", "--unit", "surface",
                                  "--factory-root", str(factory)]) == 0
    assert service.status(case, 7, factory)["closed"] is True


def test_a_rejudgement_keeps_a_violation_of_a_note_blocking(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    summary = service.ask_round(case, 7, Judging([_rule_point("prefix", RULE)], {"prefix": RULE}),
                                factory_root=factory)
    path = service.rounds_dir(case, 7) / summary["round"] / "summary.json"
    kept = json.loads(path.read_text(encoding="utf-8"))
    kept["judge_rules"] = {"version": 1, "standard": kept["judge_rules"]["standard"]}
    path.write_text(json.dumps(kept), encoding="utf-8")
    again = service.rejudge(case, 7, "store", factory)
    judgement = again["topics"][0]["judgement"]
    assert judgement["kind"] == "standard_violation" and judgement["blocking"] is True
    assert again["contradiction_units"] == ["store"] and "store" in again["open_units"]
    # the next round is asked on a changed text, as before
    with pytest.raises(service.QuestionRoundError, match="under the current judge rules"):
        service.rejudge(case, 7, "store", factory)


def test_a_rejudgement_carries_the_dispositions_of_the_round_it_checks(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    summary = service.ask_round(case, 7, Provider([_point("size")], blocking={"size"}), factory_root=factory)
    topic = next(t["id"] for t in summary["topics"] if t["units"] == ["store"])
    service.dispose(case, 7, topic, "carried", to="generation", what="the size limit")
    path = service.rounds_dir(case, 7) / summary["round"] / "summary.json"
    kept = json.loads(path.read_text(encoding="utf-8"))
    kept.pop("judge_rules")
    path.write_text(json.dumps(kept), encoding="utf-8")
    again = service.rejudge(case, 7, "store", factory)
    assert "store" not in again["open_units"]
    entries = json.loads((service.rounds_dir(case, 7) / again["round"] / "dispositions.json")
                         .read_text(encoding="utf-8"))["dispositions"]
    assert entries == [{**entries[0], "rejudged_from": summary["round"]}] and entries[0]["topic"] == topic
    assert len(service.carried_items(case, "generation")) == 1  # listed once, where it was given
    # a later disposition finds the topic in its latest round without --round
    assert service.dispose(case, 7, topic, "accepted", reason="kept")["disposition"] == "accepted"


@pytest.mark.parametrize("what,match", [
    ("changed", "changed since round-01"),
    ("current", "under the current judge rules"),
    ("unknown", "has no unit"),
    ("document", "rejudge checks State 7 verdicts"),
])
def test_a_rejudgement_refuses(tmp_path, monkeypatch, what, match):
    case, factory = _boilerplate_case(tmp_path, monkeypatch)
    if what == "current":
        service.ask_round(case, 7, Provider(), factory_root=factory)
    else:
        _asked_under_old_rules(case, factory, monkeypatch)
    if what == "changed":
        spec = json.loads((case / "global_spec.json").read_text(encoding="utf-8"))
        spec["notes"][0] = "- save: [PRECONDITION] MUST refuse a record over the size limit."
        (case / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")
    state, unit = (2, "store") if what == "document" else (7, "nowhere" if what == "unknown" else "store")
    with pytest.raises(service.QuestionRoundError, match=match):
        service.rejudge(case, state, unit, factory)


def test_a_rejudgement_is_no_round_of_the_layer(tmp_path, monkeypatch):
    """The topics naming no unit, the precedents and the hypotheses are read
    from the rounds that asked reviewers: a re-judgement reviews one unit."""
    asked = {"round": "round-01", "closure": units.CLOSURE_RULE, "scope": ["a", "b"], "units": {"a": "x", "b": "y"},
             "judge": {}, "topics": [{"id": "T1", "units": ["?"], "runs": [1, 2],
                                      "judgement": {"kind": "contradiction", "verified": True, "blocking": True}}]}
    again = {"round": "round-02", "closure": units.CLOSURE_RULE, units.REJUDGE: {"of": "round-01", "unit": "a"},
             "scope": ["a"], "units": {"a": "x", "b": "y"}, "judge": {}, "topics": []}
    assert units.no_unit_state([asked, again])["contradictions"] == ["T1"]
    assert units.asked([asked, again]) == [asked]
    assert units.latest_review([asked, again], "a") is again and units.latest_review([asked, again], "b") is asked
