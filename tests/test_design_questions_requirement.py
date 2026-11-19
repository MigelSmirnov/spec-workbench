"""A State 2 gap is a choice that breaks a requirement, not one somebody sees.

Experiment of 2026-11-20 (docs/STATE2_REQUIRED_RESULTS_20261120.md). The
judge of State 2 was asked who would notice a difference, and an observer
exists for every difference: on Portal Deliverer 207 gaps blocked its 59
rounds, and about a fifth of them were choices a requirement told apart. A
phase that declares `gap_needs_requirement` asks first whose question a topic
is, then for the requirement one of its two behaviours breaks, quoted and
checked like any quote; and a topic carried to a later layer may name what
every way of deciding it must keep.
"""
from __future__ import annotations

import pytest

import test_design_questions_dispositions as base
from questions_workbench import documents, judge, prompts, service, units

TEXTS = "Rule one keeps every thing.\n\nRule two drops a thing."
GAP = {"kind": "consequential_gap", "quotes": ["Rule two drops a thing."], "divergence": "a or b; a breaks rule one",
       "witness": base.WITNESS}


def check(judgement: dict, required: bool = True, state: int = 2) -> dict:
    return judge.check(judgement, state, TEXTS, None, witness_required=True, requirement_required=required)


def test_only_state_2_declares_the_rule():
    assert documents.gap_needs_requirement(2) is True
    assert [s for s in documents.question_states() if documents.gap_needs_requirement(s)] == [2]


def test_a_gap_with_a_requirement_found_in_the_texts_blocks():
    kept = check({**GAP, "requirement": "Rule one keeps every thing."})
    assert (kept["kind"], kept["blocking"], kept["verified"]) == ("consequential_gap", True, True)
    assert kept["requirement"] == "Rule one keeps every thing."


def test_a_gap_that_names_no_requirement_is_a_hypothesis_the_author_disposes_of():
    kept = check(GAP)
    assert (kept["kind"], kept["claimed_kind"], kept["blocking"]) == ("hypothesis", "consequential_gap", False)
    assert "no requirement" in kept["requirement_missing"]
    assert units.topic_need({"judgement": kept}, {"judge": {}}) == units.DISPOSITION


def test_a_requirement_not_found_verbatim_blocks_like_every_failed_quote():
    kept = check({**GAP, "requirement": "Rule one keeps most things."})
    assert kept["blocking"] is True and kept["verified"] is False
    assert "requirement" in kept["failure"]


def test_a_state_that_does_not_declare_the_rule_judges_as_before():
    kept = check(GAP, required=False)
    assert (kept["kind"], kept["blocking"]) == ("consequential_gap", True)
    assert "requirement" not in kept
    assert "requirement" not in check({**GAP, "requirement": "Rule one keeps every thing."}, required=False)


def test_a_gap_no_passage_speaks_to_is_still_deferred():
    kept = check({"kind": "consequential_gap", "divergence": "a or b"})
    assert (kept["kind"], kept["blocking"]) == ("consequential_gap", False)
    assert kept["deferred_to"] == judge.DEFERRED_TO


def test_a_later_states_question_with_a_requirement_is_the_authors_to_carry():
    kept = check({"kind": "later_state", "later_state": 7, "why": "temporary names",
                  "requirement": "Rule one keeps every thing."})
    assert (kept["kind"], kept["blocking"], kept["requirement"]) == ("later_state", False, "Rule one keeps every thing.")
    assert units.topic_need({"judgement": kept}, {"judge": {}}) == units.DISPOSITION
    plain = check({"kind": "later_state", "later_state": 7})
    assert units.topic_need({"judgement": plain}, {"judge": {}}) is None


def test_a_later_states_requirement_that_is_not_found_is_dropped_not_blocking():
    kept = check({"kind": "later_state", "later_state": 7, "requirement": "Rule nine."})
    assert kept["verified"] is True and kept["blocking"] is False
    assert "requirement" not in kept and kept["requirement_unverified"] == "Rule nine."
    assert units.topic_need({"judgement": kept}, {"judge": {}}) is None


def test_the_judge_is_told_the_order_only_where_the_rule_is_declared():
    scope = documents.question_scope(2)
    told = prompts.judge_instruction(2, False, None, False, scope, True, requirement=True)
    assert "Whose question is it?" in told and "an observer exists for every difference" in told
    assert told.index("Whose question is it?") < told.index("must the two behaviours be told apart")
    assert '"requirement":' in told and "would notice" not in told
    plain = prompts.judge_instruction(2, False, None, False, scope, True)
    assert "Whose question is it?" not in plain and '"requirement":' not in plain and "would notice" in plain


def test_a_round_of_state_2_records_the_rule_it_was_judged_under(tmp_path):
    case = base.make_case(tmp_path, with_git=True)
    summary = base.ask(case, "gap")
    assert summary["judge_rules"]["gap_needs_requirement"] is True
    assert "gap_needs_requirement" not in judge.rules_record(None)


def test_a_carried_topic_names_what_every_way_must_keep(tmp_path):
    case = base.make_case(tmp_path, with_git=True)
    base.ask(case, "gap")
    entry = service.dispose(case, 2, "T1", "carried", to="7",
                            what="create the folders ahead or as each file is written; check a crash and a repeat",
                            keeps=["Rule one keeps every thing."])
    assert entry["keeps"] == ["Rule one keeps every thing."]
    row = service.carried_items(case, to=7)[0]
    assert row["keeps"] == "Rule one keeps every thing."
    lines = prompts._layer_lines({"carried_in": [row]})[1]
    assert "Every way must keep: Rule one keeps every thing." in lines


def test_what_a_carried_topic_keeps_must_stand_in_the_texts(tmp_path):
    case = base.make_case(tmp_path, with_git=True)
    base.ask(case, "gap")
    with pytest.raises(service.QuestionRoundError, match="do not hold verbatim: INV-99"):
        service.dispose(case, 2, "T1", "carried", to="7", what="decide a or b", keeps=["INV-99"])
    with pytest.raises(service.QuestionRoundError, match="goes with --carried"):
        service.dispose(case, 2, "T1", "accepted", reason="free", keeps=["Rule one keeps every thing."])
