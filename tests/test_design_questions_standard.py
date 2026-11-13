"""A question round gives its reviewers and its judge the SPEC_STANDARD sections
its phase lists in `docs`, verbatim; a passage that breaks one of their rules
is a standard_violation, both quotes checked mechanically, blocking like a
contradiction (owner decision 2026-11-08, #147 comment 6724353913).

client-portal `expense_intake` passed State 7 rounds 18-20 on contradictions
alone, then Route B stopped it at `model_constructor_unknown_field`: the
round's reviewer never saw the standard the notes are written by."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from notes_authoring import standard
from questions_workbench import documents, judge, prompts, service
from test_design_questions_gates import Provider, _notes_case, _point

STANDARD_DOC = "skills/spec-authoring/SPEC_STANDARD.md"
# a rule of SPEC_STANDARD §2, a section state7_notes lists in docs
RULE = "Нота без префикса запрещена."
PASSAGE = "The record fits the size limit."


def _listed(state: int) -> list[str]:
    sequence = json.loads(documents.SEQUENCE.read_text(encoding="utf-8"))
    return [d["section"] for p in sequence["phases"] if p.get("semantic_state") == state and p.get("question_scope")
            for d in p.get("docs") or [] if d.get("path") == STANDARD_DOC and d.get("section")]


# 1. The sections are the phase's own, cut verbatim by the standard's extractor


@pytest.mark.parametrize("state", documents.question_states())
def test_a_round_gets_exactly_the_standard_sections_its_phase_lists(state):
    sections = documents.standard_sections(state)
    assert [s["text"] for s in sections] == [standard.section(ref)["text"] for ref in _listed(state)]


def test_state7_gets_its_four_sections_and_never_the_whole_standard():
    sections = documents.standard_sections(7)
    assert [s["section"] for s in sections] == ["2", "15.3.1", "7", "15.9"]
    whole = (documents.ROOT / STANDARD_DOC).read_text(encoding="utf-8")
    assert sum(len(s["text"]) for s in sections) < len(whole) / 4
    assert RULE in sections[0]["text"]


def test_the_state7_instruction_carries_the_sections_verbatim_and_asks_for_violations():
    sections = documents.standard_sections(7)
    instruction = prompts.module_ask_instruction(7, documents.question_scope(7), None, None, sections)
    assert "contradicts itself" in instruction  # contradictions are asked as before
    assert '"kind":"standard_violation"' in instruction and '"rule":' in instruction
    assert all(s["text"] in instruction for s in sections)


def test_a_state_whose_phase_lists_no_section_is_asked_as_before():
    for state in (0, 4):
        assert documents.standard_sections(state) == []
        assert (prompts.ask_instruction(state, documents.question_scope(state), [])
                == prompts.ASK.format(state=state, scope=documents.question_scope(state)))
    assert "standard_violation" not in prompts.judge_instruction(4, False)
    assert "SPEC_STANDARD" not in prompts.judge_input("texts", [], None)


def test_a_document_state_that_lists_a_section_gives_it_to_its_reviewers(tmp_path):
    instruction = prompts.ask_instruction(1, documents.question_scope(1), documents.standard_sections(1))
    assert standard.section("5. models")["text"] in instruction and "standard_violation" in instruction


# 2. The judge checks both quotes mechanically


def _violation(**over):
    return {"kind": "standard_violation", "quotes": [PASSAGE], "rule": RULE, "section": "2", **over}


def test_a_verified_violation_blocks_without_a_witness():
    kept = judge.check(_violation(), 7, f"- save: {PASSAGE}", None, standard=f"## 2. notes\n{RULE}\n",
                       witness_required=True)
    assert kept["verified"] is True and kept["blocking"] is True and kept["kind"] == "standard_violation"
    assert kept["rule"] == RULE and kept["section"] == "2"


@pytest.mark.parametrize("judgement,given,failure", [
    (_violation(rule="Каждая нота обязана перечислять все поля модели."), RULE, "rule of a standard violation"),
    (_violation(quotes=["A passage the prompt does not hold."]), RULE, "passage of a standard violation"),
    (_violation(), None, "only when the round gave"),
])
def test_a_violation_whose_quote_fails_is_unverified(judgement, given, failure):
    kept = judge.check(judgement, 7, f"- save: {PASSAGE}", None, standard=given)
    assert kept["verified"] is False and kept["blocking"] is True and failure in kept["failure"]


# 3. In a round: the violation blocks like a contradiction


class Judging(Provider):
    """Judges a topic whose subject is in `violations` a standard_violation with that rule."""

    def __init__(self, points, violations: dict[str, str], **kwargs):
        super().__init__(points, **kwargs)
        self.violations = violations
        self.judge_instructions: list[str] = []

    def complete(self, instruction, text):
        if instruction.startswith("You judge the topics") and self.violations:
            self.judge_instructions.append(instruction)
            self.judged.append(text)
            listing = text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
            judgements = []
            for line in listing:
                if line[:1] == "T":
                    tid, subject = line.split(": ", 1)
                    if subject in self.violations:
                        judgements.append({"id": tid, "kind": "standard_violation", "quotes": [PASSAGE],
                                           "rule": self.violations[subject], "section": "2"})
                    elif subject in self.contradictions:
                        judgements.append({"id": tid, "kind": "contradiction", "quotes": self.contradictions[subject]})
                    else:
                        judgements.append({"id": tid, "kind": "indifferent", "why": "no one acts on it"})
            return json.dumps({"judgements": judgements}), {}
        return super().complete(instruction, text)


def _rule_point(subject: str, rule: str) -> dict:
    return {**_point(subject, text=PASSAGE), "kind": "standard_violation", "rule": rule, "section": "2"}


def test_a_verified_violation_blocks_the_module_and_takes_no_disposition(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    provider = Judging([_rule_point("prefix", RULE)], {"prefix": RULE})
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    assert all(RULE in i for i in provider.instructions)  # every reviewer got the sections
    assert "standard_violation" in provider.judge_instructions[0]
    assert all("THE RULES OF THIS STATE: SPEC_STANDARD SECTIONS" in t and RULE in t for t in provider.judged)
    assert f"breaks SPEC_STANDARD §2: {RULE}" in provider.judged[0]  # the reviewer's rule reaches the judge
    topic = next(t for t in summary["topics"] if "store" in t["units"])
    assert topic["judgement"]["kind"] == "standard_violation" and topic["judgement"]["blocking"] is True
    assert "store" in summary["blocked_units"] and "store" in summary["contradiction_units"]
    with pytest.raises(service.QuestionRoundError, match="standard violation: it takes no disposition"):
        service.dispose(case, 7, topic["id"], "accepted", reason="we like it")
    assert service.status(case, 7, factory)["contradictions"]["store"] == [topic["id"]]


def test_a_violation_closes_when_the_text_changes_and_one_round_no_longer_raises_it(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    service.ask_round(case, 7, Judging([_rule_point("prefix", RULE)], {"prefix": RULE}), factory_root=factory)
    spec = json.loads((case / "global_spec.json").read_text(encoding="utf-8"))
    spec["notes"][0] = "- save: [PRECONDITION] MUST refuse a record over the size limit."
    (case / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")
    summary = service.ask_round(case, 7, Provider(), factory_root=factory)
    # store for its change; surface, whose prompt lacks the passage, for its unverified topic
    assert summary["scope"] == ["store", "surface"] and summary["changed_units"] == ["store"]
    assert summary["closed"] is True


def test_a_violation_quoting_a_rule_the_sections_do_not_state_is_unverified(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    invented = "Каждая нота обязана перечислять все поля модели."
    summary = service.ask_round(case, 7, Judging([_rule_point("invented", invented)], {"invented": invented}),
                                factory_root=factory)
    judgement = summary["topics"][0]["judgement"]
    assert judgement["verified"] is False and "not found verbatim" in judgement["failure"]
    assert service.status(case, 7, factory)["unit_status"]["store"]["needs_round"]


def test_contradictions_are_judged_as_before_beside_the_sections(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    spec = json.loads((case / "global_spec.json").read_text(encoding="utf-8"))
    spec["notes"][1] += " Like every module it may import pydantic."
    (case / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")
    quotes = ["The surface imports nothing outside the standard library.", "it may import pydantic."]
    provider = Provider([_point("pydantic", text="it may import pydantic.")], contradictions={"pydantic": quotes})
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    judged = {t["units"][0]: t["judgement"] for t in summary["topics"]}
    assert judged["surface"]["kind"] == "contradiction" and judged["surface"]["blocking"] is True
    assert "standard_violation" not in judged["surface"]


# 3b. In State 7 only the module's notes are design text


# the Factory's own closing instruction (code-factory#200), not a note of any module
BOILERPLATE = ("Any other model value: derive a changed value with value.model_copy(update={...}) "
               "or construct a new instance.")


def test_a_state7_violation_quoting_no_note_is_the_generators_text_and_asks_nothing():
    prompt = f"Module: store\nNOTES:\n- save: {PASSAGE}\n\n{BOILERPLATE}\n"
    notes = f"- save: {PASSAGE}"
    given = f"## 2. notes\n{RULE}\n"
    kept = judge.check(_violation(quotes=[BOILERPLATE]), 7, prompt, None, standard=given, violation_texts=notes)
    assert kept["kind"] == judge.GENERATOR_TEXT and kept["claimed_kind"] == "standard_violation"
    assert kept["verified"] is True and kept["blocking"] is False and "outside_notes" in kept
    # a violation in a note still blocks, quoted with the prompt's bullet or without
    for quotes in ([PASSAGE], [f"- save: {PASSAGE}"]):
        kept = judge.check(_violation(quotes=quotes), 7, prompt, None, standard=given,
                           violation_texts=f"save: {PASSAGE}")
        assert kept["kind"] == "standard_violation" and kept["blocking"] is True
    # a passage found nowhere is still unverified, and blocks
    kept = judge.check(_violation(quotes=["A passage the prompt does not hold."]), 7, prompt, None,
                       standard=given, violation_texts=notes)
    assert kept["verified"] is False and kept["blocking"] is True


def test_notes_in_prompt_are_the_specification_notes_the_prompt_carries():
    notes = ["save: [BEHAVIOR] MUST keep `the record`.", "serve: [BEHAVIOR] MUST serve."]
    prompt = "IMPORTS:\n...\nREQUIREMENTS (notes — implement these):\n- save: [BEHAVIOR] MUST keep the record.\n"
    assert prompts.notes_in_prompt(notes, prompt) == ["save: [BEHAVIOR] MUST keep `the record`."]


def test_the_state7_reviewer_and_judge_are_told_only_the_notes_are_design_text():
    sections = documents.standard_sections(7)
    instruction = prompts.module_ask_instruction(7, documents.question_scope(7), None, None, sections)
    assert "never\nreport it as a standard_violation" in instruction
    assert "breaks a rule of\nthese sections" in instruction and "the notes of the prompt" in instruction
    layer = prompts.module_layer_judge([], ["- save: x"])
    assert "THIS MODULE'S NOTES" in layer and "- save: x" in layer
    assert prompts.module_layer_judge([]) is None


class QuotingBoilerplate(Judging):
    """Judges every topic a standard_violation of the Factory's closing instruction."""

    def complete(self, instruction, text):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            ids = [line.split(": ", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                   if line[:1] == "T"]
            return json.dumps({"judgements": [
                {"id": tid, "kind": "standard_violation", "quotes": [BOILERPLATE], "rule": RULE, "section": "2"}
                for tid in ids]}), {}
        return super().complete(instruction, text)


def test_a_round_does_not_hold_a_module_on_the_factorys_own_instruction(tmp_path, monkeypatch):
    """client-portal State 7 round 23, `financial_policy` T1-T3: the judge read the
    Factory's `model_copy` line as an unclassified note with code syntax."""
    case, factory = _notes_case(tmp_path, monkeypatch)
    (factory / "tools/generate_agent.py").write_text(
        "def build_prompt(local_spec, models_code=None):\n"
        "    return ('Module: ' + local_spec['module_name'] + '\\nNOTES:\\n' + '\\n'.join(local_spec['notes'])\n"
        f"            + '\\n\\n' + {BOILERPLATE!r} + '\\n')\n", encoding="utf-8")
    provider = QuotingBoilerplate([{**_point("model_copy", text=BOILERPLATE), "kind": "standard_violation",
                                    "rule": RULE, "section": "2"}], {"model_copy": RULE})
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    assert all("THIS MODULE'S NOTES" in t for t in provider.judged)
    assert "- save: [PRECONDITION] The record fits the size limit." in provider.judged[0]
    kinds = {t["units"][0]: t["judgement"]["kind"] for t in summary["topics"]}
    assert kinds == {"store": judge.GENERATOR_TEXT, "surface": judge.GENERATOR_TEXT}
    assert summary["blocking_topics"] == 0 and summary["contradiction_units"] == []
    assert service.status(case, 7, factory)["closed"] is True


# 4. A probe asks closed modules and records nothing in the case


def test_a_probe_asks_every_module_closed_or_not_and_records_no_round(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    service.ask_round(case, 7, Provider(), factory_root=factory)
    assert service.status(case, 7, factory)["closed"] is True
    rounds = sorted(p.name for p in service.rounds_dir(case, 7).iterdir())
    out = tmp_path / "probe"
    provider = Judging([_rule_point("prefix", RULE)], {"prefix": RULE})
    summary = service.probe_round(case, 7, provider, out, factory_root=factory)
    assert summary["scope"] == ["store", "surface"] and summary["blocking_topics"] == 2
    assert summary["modules"]["store"]["kinds"] == {"standard_violation": 1}
    assert summary["standard_sections"] == ["2", "15.3.1", "7", "15.9"]
    # the round is kept in `out`, never as a round of the case: the state stays closed
    assert sorted(p.name for p in service.rounds_dir(case, 7).iterdir()) == rounds
    assert service.status(case, 7, factory)["closed"] is True
    assert (out / "summary.json").is_file() and (out / "prompts" / "store.txt").is_file()
    assert (out / "review-store-3.json").is_file()
    # every request's input size is logged
    kinds = [r["kind"] for r in summary["requests"]]
    assert kinds.count("review") == 6 and kinds.count("group") == 2 and kinds.count("judge") == 2
    review = next(r for r in summary["requests"] if r["kind"] == "review" and r["module"] == "store")
    assert review["total_chars"] == review["instruction_chars"] + review["text_chars"] > len(RULE)


def test_a_probe_offers_no_precedent(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    service.ask_round(case, 7, Judging([_point("old")], {"_": RULE}), factory_root=factory)  # judged indifferent
    provider = Judging([_point("old")], {"_": RULE})
    service.probe_round(case, 7, provider, tmp_path / "probe", factory_root=factory, modules=["store"])
    assert all("PRIOR JUDGEMENTS" not in text for text in provider.judged)


@pytest.mark.parametrize("state,out,modules,match", [
    (6, "probe", None, "State 7 module by module"),
    (7, "demo/questions/probe", None, "outside the case"),
    (7, "probe", ["models"], "not generated modules"),
])
def test_a_probe_refuses(tmp_path, monkeypatch, state, out, modules, match):
    case, factory = _notes_case(tmp_path, monkeypatch)
    with pytest.raises(service.QuestionRoundError, match=match):
        service.probe_round(case, state, Provider(), tmp_path / out, factory_root=factory, modules=modules)
