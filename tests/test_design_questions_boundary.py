"""Decision ownership, required results and carried guarantees survive a round.

Scripted model answers test the protocol, not the semantic accuracy of a model.
The real old/new probes remain necessary before claiming fewer false questions.
"""
from __future__ import annotations

import json

import pytest

import design_questions
from questions_workbench import documents, judge, prompts, service, units

REQUIREMENT = "A9.2: Limit age is a deployment obligation; the service never reads the limit age."
BOUNDARY = "The caller receives only settings that satisfy the accepted policy."
CORPUS = REQUIREMENT + "\n" + BOUNDARY
OPTIONS = ["check in deployment preflight", "check during deployment verification"]
CONSEQUENCES = ["deployment refuses an expired limit", "deployment reports expiry before promotion"]
WITNESS = {"initial": "a caller requests settings", "events": ["the provider returns settings"],
           "outcomes": ["accepted settings", "settings outside the policy"], "observer": "the caller",
           "basis": [BOUNDARY]}


def checked(verdict, state=2):
    return judge.check(verdict, state, CORPUS, None, own_texts=CORPUS,
                       witness_required=True, requirement_required=True)


@pytest.mark.parametrize("state", [2, 5])
def test_an_observer_without_a_requirement_does_not_prove_a_required_choice(state):
    verdict = checked({"kind": "consequential_gap", "quotes": [BOUNDARY],
                       "divergence": "different representations are visible to a caller", "witness": WITNESS}, state)
    assert verdict["kind"] == "hypothesis" and verdict["requirement_missing"]
    assert "deferred_to" not in verdict
    assert units.topic_need({"judgement": verdict}, {"judge": {}}) == units.DISPOSITION


def test_a_required_boundary_outcome_still_blocks_and_its_quote_is_checked():
    verdict = {"kind": "consequential_gap", "decision_owner": 5, "quotes": [BOUNDARY],
               "requirement": BOUNDARY, "divergence": "unacceptable settings break the promised policy", "witness": WITNESS}
    assert checked(verdict, 5)["blocking"] and checked(verdict, 5)["verified"]
    invalid = checked({**verdict, "requirement": "A requirement that the design never accepted."}, 5)
    assert invalid["blocking"] and not invalid["verified"] and "requirement" in invalid["failure"]


def test_refusal_precedence_is_not_rejected_as_an_implementation_word():
    promise = "Authorization failure takes precedence: an unauthenticated caller receives no stored data."
    witness = {**WITNESS, "basis": [promise]}
    verdict = judge.check({"kind": "consequential_gap", "decision_owner": 2, "quotes": [promise],
                           "requirement": promise, "divergence": "reading first discloses data before refusal",
                           "witness": witness}, 2, promise, None, witness_required=True, requirement_required=True)
    assert verdict["kind"] == "consequential_gap" and verdict["verified"] and verdict["blocking"]


@pytest.mark.parametrize("target", [6, 8, "generation", "factory_checks", "deploy"])
def test_later_choices_keep_their_guarantee_and_require_a_disposition(target):
    verdict = checked({"kind": "later_state", "later_state": target, "requirement": REQUIREMENT,
                       "options": OPTIONS, "consequences": CONSEQUENCES})
    assert verdict["verified"] and not verdict["blocking"]
    assert verdict["requirement"] == REQUIREMENT and verdict["options"] == OPTIONS
    assert units.topic_need({"judgement": verdict}, {"judge": {}}) == units.DISPOSITION


@pytest.mark.parametrize("target", [2, 1, 9, True, "anywhere"])
def test_invalid_receiving_layers_are_not_silently_accepted(target):
    verdict = checked({"kind": "later_state", "later_state": target, "requirement": REQUIREMENT})
    assert not verdict["verified"] and verdict["blocking"]


def test_a_future_choice_with_an_invented_guarantee_is_not_verified():
    verdict = checked({"kind": "later_state", "later_state": "deploy", "requirement": "Invented maximum age is thirty days."})
    assert not verdict["verified"] and verdict["blocking"]


def test_a_future_owner_cannot_be_reported_as_a_current_state_gap():
    verdict = checked({"kind": "consequential_gap", "decision_owner": "deploy", "quotes": [REQUIREMENT],
                       "requirement": REQUIREMENT, "divergence": "preflight versus verification", "witness": WITNESS})
    assert not verdict["verified"] and "actual owner" in verdict["failure"]


def test_a_missing_product_decision_cannot_be_reported_as_freedom():
    verdict = checked({"kind": "indifferent", "why": "no requirement says which callers are permitted",
                       "owner_question": "Which callers may see these settings?",
                       "options": ["all authenticated callers", "only project owners"],
                       "consequences": ["wider access", "owner-only access"]})
    assert verdict["kind"] == "hypothesis" and verdict["owner_question"]
    assert units.topic_need({"judgement": verdict}, {"judge": {}}) == units.DISPOSITION


def test_the_new_gap_filter_does_not_soften_contradictions_or_standard_violations():
    contrary = "The provider returns settings outside the accepted policy."
    contradiction = judge.check({"kind": "contradiction", "quotes": [BOUNDARY, contrary],
                                  "witness": WITNESS}, 5, CORPUS + "\n" + contrary, None,
                                 witness_required=True, requirement_required=True)
    assert contradiction["kind"] == "contradiction" and contradiction["blocking"]
    rule = "Every public operation belongs to exactly one owning module."
    violation = judge.check({"kind": "standard_violation", "quotes": [BOUNDARY], "rule": rule},
                            5, CORPUS, None, standard=rule, requirement_required=True)
    assert violation["kind"] == "standard_violation" and violation["verified"] and violation["blocking"]
    invalid = judge.check({"kind": "standard_violation", "quotes": ["Invented passage."], "rule": rule},
                          5, CORPUS, None, standard=rule, requirement_required=True)
    assert invalid["kind"] == "standard_violation" and not invalid["verified"] and invalid["blocking"]


def test_following_a_precedent_does_not_lose_a_guarantee_or_follow_a_changed_one():
    prior = checked({"kind": "later_state", "later_state": "deploy", "requirement": REQUIREMENT,
                     "options": OPTIONS, "consequences": CONSEQUENCES})
    inherited = judge.check({"kind": "judged_before", "precedent": "P1"}, 2, CORPUS, None,
                            precedents={"P1": prior}, requirement_required=True)
    assert inherited["verified"] and inherited["requirement"] == REQUIREMENT
    assert inherited["options"] == OPTIONS and inherited["consequences"] == CONSEQUENCES
    assert units.topic_need({"judgement": inherited}, {"judge": {}}) == units.DISPOSITION
    assert not judge.precedent_holds(prior, BOUNDARY)


class Provider:
    name = "scripted-boundary"

    def __init__(self, unit, verdict):
        self.unit, self.verdict = unit, verdict
        self.requests = []

    def complete(self, instruction, text):
        self.requests.append((instruction, text))
        if instruction.startswith("You judge the topics"):
            return json.dumps({"judgements": [{"id": "T1", **self.verdict}]}), {}
        if instruction.startswith("You receive the open points"):
            return json.dumps({"groups": [{"topic": "limit-age validation", "members": ["r1.00", "r2.00", "r3.00"]}]}), {}
        return json.dumps({"open_points": [{"subject": "limit age", "unit": self.unit, "text": REQUIREMENT,
                                             "question": "Where is limit age checked?", "decision_owner": "deploy",
                                             "requirement": REQUIREMENT, "options": OPTIONS,
                                             "consequences": CONSEQUENCES}]}), {}


@pytest.fixture
def case(tmp_path, monkeypatch):
    (tmp_path / "02_rules.md").write_text("# State 2 — Rules\n\n## Accepted decision A09 — Limits\n\n" + REQUIREMENT + "\n")
    monkeypatch.setattr(service, "layer_context", lambda case, state: {
        "state": state, "owns": [], "carries": [], "results": [], "gate_findings": [],
        "ready": True, "verdicts": [], "carried_in": service.carried_items(case, to=state)})
    return tmp_path


@pytest.mark.parametrize("target", [5, "deploy"])
def test_the_round_carries_the_guarantee_options_and_consequences_to_its_receiver(case, target, capsys):
    provider = Provider("A09", {"kind": "later_state", "later_state": target, "requirement": REQUIREMENT,
                                "options": OPTIONS, "consequences": CONSEQUENCES})
    summary = service.ask_round(case, 2, provider)
    assert summary["judge_rules"]["decision_boundary"] == 1
    assert summary["awaiting_disposition"] == ["T1"] and not summary["closed"]
    # The reviewer supplied the guarantee too: the judge must receive more than the title.
    assert any("layer choice:" in text and REQUIREMENT in text for instruction, text in provider.requests
               if instruction.startswith("You judge"))
    assert "preserve:" in design_questions._human_round(summary)
    with pytest.raises(service.QuestionRoundError, match="--keeps"):
        service.dispose(case, 2, "T1", "carried", to=str(target), what="select a validation mechanism",
                        keeps=["An obligation that was never accepted."])
    entry = service.dispose(case, 2, "T1", "carried", to=str(target), what="select a validation mechanism")
    assert entry["keeps"] == [REQUIREMENT] and entry["options"] == OPTIONS
    carried = service.carried_items(case, to=target)[0]
    assert carried["consequences"] == CONSEQUENCES
    assert service.status(case, 2)["closed"]
    assert design_questions.main(["carried", str(case)]) == 0
    assert REQUIREMENT in capsys.readouterr().out
    if target == 5:
        (case / "50_public_api.md").write_text("# State 5 — Public API\n\n## Operation read_settings\n\n" + BOUNDARY)
        unit = next(iter(service.state_texts(case, 5).units))
        receiver = Provider(unit, {"kind": "indifferent", "why": "either exact form preserves the caller promise"})
        service.ask_round(case, 5, receiver)
        instruction = receiver.requests[0][0]
        assert REQUIREMENT in instruction and all(option in instruction for option in OPTIONS)
        assert all(consequence in instruction for consequence in CONSEQUENCES)


def test_the_product_owner_question_reaches_round_status_and_human_output(case, capsys):
    provider = Provider("A09", {"kind": "hypothesis", "why": "a product choice is missing",
                                "owner_question": "May deployment proceed with an expired limit?",
                                "options": ["refuse", "allow"], "consequences": ["delayed rollout", "expired protection"]})
    summary = service.ask_round(case, 2, provider)
    assert summary["owner_questions"][0]["question"].startswith("May deployment")
    assert not summary["closed"]
    assert service.status(case, 2)["owner_questions"] == summary["owner_questions"]
    assert design_questions.main(["status", str(case), "--state", "2"]) == 1
    assert "ask owner (round-01 T1)" in capsys.readouterr().out


def test_factory_return_guidance_is_available_without_a_remembered_case_or_phase(capsys):
    assert design_questions.main(["guide", "--factory-return", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["state"] is None and result["factory_return"]
    text = " ".join(result["author_guidance"])
    assert "exact diagnostic" in text and "State 6" in text and "dict.items" in text
    assert "owning state" in text and "carried" in text


def test_scope_reaches_both_review_and_judge_and_distinguishes_contradiction_from_detail():
    for state in (2, 5):
        assert documents.gap_needs_requirement(state)
        review = prompts.ask_instruction(state, documents.question_scope(state))
        instruction = prompts.judge_instruction(state, False, scope=documents.question_scope(state),
                                                witness=True, requirement=True)
        assert "Keep the broad task" in review and "Do not demand its implementation" in review
        assert "Different levels of detail alone" in review and "Mere difference in detail" in instruction
        assert instruction.index("1. Establish the decision owner") < instruction.index("2. If it belongs")
        assert "an observer of a difference is not sufficient" in instruction
        assert "product decision itself is absent" in instruction
    assert not documents.gap_needs_requirement(7)


def test_state7_receives_carried_choices_as_context_without_changing_factory_prompts(tmp_path, monkeypatch):
    from test_design_questions_gates import Provider as ModuleProvider, _notes_case, _point

    case, factory = _notes_case(tmp_path, monkeypatch)
    carried = [{"state": 2, "round": "round-01", "topic": "T1", "to": 7,
                "what": "choose the validation implementation", "keeps": [REQUIREMENT],
                "options": OPTIONS, "consequences": CONSEQUENCES}]
    monkeypatch.setattr(service, "layer_context", lambda case, state: {
        "state": state, "owns": [], "carries": [], "results": [], "gate_findings": [],
        "ready": True, "verdicts": [], "carried_in": carried})
    provider = ModuleProvider([_point("validation choice")])
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    assert all(REQUIREMENT in instruction for instruction in provider.instructions)
    assert all(REQUIREMENT in text for text in provider.judged)
    assert all(REQUIREMENT not in text for text in provider.inputs)
    for module in summary["scope"]:
        kept = case / "questions/state7" / summary["round"] / "prompts" / f"{module}.txt"
        assert REQUIREMENT not in kept.read_text()
