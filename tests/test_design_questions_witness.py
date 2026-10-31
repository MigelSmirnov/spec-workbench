"""Witnesses, contradiction bases, units reopened by reference, quote provenance.

QUESTIONS.md, "A blocking topic needs a witness" and the sections after it.
"""
from __future__ import annotations

import json
import subprocess

from questions_workbench import judge, prompts, service, units

RULES = """# State 2 — Demo rules

## Accepted decision A01 — erasing

1. Erasing writes an entry of its own whatever it removed.

## Accepted decision A02 — no-op

1. An accepted action that changes nothing writes no entry, as A01 rule 1 allows.

## Accepted decision A03 — lists

1. Lists are ordered by name.
"""

PRODUCT = "# State 0 — Demo\n\nThe erasure leaves an entry of its own naming the date.\n"
MODELS = "# State 1 — Demo models\n\n## Model M01 — Entry\n\nAn entry records one change.\n"

WITNESS = {"initial": "a log with one entry", "events": ["the owner erases before a date older than every entry"],
           "outcomes": ["an erasure entry is written", "nothing is written"], "observer": "the owner reading the log",
           "basis": ["Erasing writes an entry of its own whatever it removed."]}
CONTRADICTION = {"kind": "contradiction",
                 "quotes": ["Erasing writes an entry of its own whatever it removed.",
                            "An accepted action that changes nothing writes no entry"]}


class Provider:
    """Scripted reviews; points grouped by subject; every judged topic gets `verdict`."""

    name = "fake"

    def __init__(self, reviews, verdict):
        self.reviews, self.verdict = list(reviews), verdict
        self.instructions: list[str] = []
        self.judged: list[str] = []

    def complete(self, instruction, text):
        if instruction.startswith("You judge the topics"):
            self.instructions.append(instruction)
            self.judged.append(text)
            ids = [line.split(":", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                   if line[:1] == "T"]
            return json.dumps({"judgements": [{"id": i, **self.verdict} for i in ids]}), {}
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                groups.setdefault(rest[1:rest.index("]")], []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        self.instructions.append(instruction)
        return json.dumps({"open_points": self.reviews.pop(0)}), {}


def point(subject, unit="A01", witness=None):
    p = {"subject": subject, "kind": "gap", "text": "x", "question": f"what about {subject}?",
         "options": [], "default_guess": "y", "unit": unit}
    if witness:
        p["witness"] = witness
    return p


def make_case(tmp_path, git=False):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text(PRODUCT, encoding="utf-8")
    (case / "01_models.md").write_text(MODELS, encoding="utf-8")
    (case / "02_rules.md").write_text(RULES, encoding="utf-8")
    if git:
        run(case, "init", "-q")
        commit(case, "first")
    return case


def run(case, *args):
    return subprocess.run(["git", "-C", str(case), *args], check=True, capture_output=True, text=True).stdout


def commit(case, message, date="2026-10-26T10:00:00"):
    run(case, "add", "-A")
    subprocess.run(["git", "-C", str(case), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                    "-m", message, "--date", date], check=True,
                   env={"GIT_COMMITTER_DATE": date, "PATH": "/usr/bin:/bin"}, capture_output=True)


def twice(subject="erasure", unit="A01"):
    return [[point(subject, unit)], [point(subject, unit)], []]


# ---- 1. a blocking topic needs a witness ------------------------------------

def test_a_contradiction_without_a_witness_is_a_hypothesis_and_does_not_block(tmp_path):
    case = make_case(tmp_path)
    summary = service.ask_round(case, 2, Provider(twice(), CONTRADICTION))
    j = summary["topics"][0]["judgement"]
    assert j["kind"] == judge.HYPOTHESIS and j["claimed_kind"] == "contradiction" and j["blocking"] is False
    assert j["witness_missing"] == "no witness"
    assert summary["hypothesis_topics"] == 1 and summary["clear"] is True


def test_a_contradiction_with_a_witness_blocks_and_keeps_it(tmp_path):
    case = make_case(tmp_path)
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "witness": WITNESS}))
    j = summary["topics"][0]["judgement"]
    assert j["kind"] == "contradiction" and j["blocking"] is True and j["witness"]["observer"]


def test_an_incomplete_witness_does_not_count(tmp_path):
    for broken, reason in [({**WITNESS, "outcomes": ["same", "same"]}, "fewer than two"),
                           ({**WITNESS, "events": []}, "no event"),
                           ({**WITNESS, "basis": ["a passage nobody wrote anywhere"]}, "not found verbatim"),
                           ({k: v for k, v in WITNESS.items() if k != "observer"}, "no observer")]:
        problem = judge.witness_problem(broken, judge._norm(RULES))
        assert problem and reason in problem


def test_a_quote_failure_still_blocks_before_any_witness_question(tmp_path):
    case = make_case(tmp_path)
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "quotes": ["nobody wrote this one"]}))
    j = summary["topics"][0]["judgement"]
    assert j["blocking"] is True and "failure" in j and j["kind"] == "contradiction"


def test_the_judge_is_told_to_ask_for_a_witness_in_document_states_only():
    assert "hypothesis" in prompts.judge_instruction(2, False, witness=True)
    assert '"witness"' in prompts.judge_instruction(2, False, witness=True)
    assert "hypothesis" not in prompts.judge_instruction(7, False)


def test_a_single_review_with_a_witness_is_judged_without_one_it_is_not(tmp_path):
    case = make_case(tmp_path)
    reviewer_witness = {k: v for k, v in WITNESS.items() if k != "basis"}
    provider = Provider([[point("erasure", witness=reviewer_witness), point("lists", "A03")], [], []],
                        {**CONTRADICTION, "witness": WITNESS})
    summary = service.ask_round(case, 2, provider)
    judged = [t["topic"] for t in summary["topics"] if "judgement" in t]
    assert judged == ["erasure"] and summary["witness_singletons"] == 1
    assert "reviewer's witness" in provider.judged[0]


def test_the_next_round_asks_reviewers_for_a_witness_of_each_hypothesis(tmp_path):
    case = make_case(tmp_path)
    service.ask_round(case, 2, Provider(twice(), CONTRADICTION))
    provider = Provider([[], [], []], CONTRADICTION)
    service.ask_round(case, 2, provider)
    assert "Hypotheses of the previous round" in provider.instructions[0]
    assert "- erasure (no witness)" in provider.instructions[0]


def test_a_hypothesis_is_never_offered_as_a_precedent(tmp_path):
    case = make_case(tmp_path)
    service.ask_round(case, 2, Provider(twice(), CONTRADICTION))
    assert service._precedents(case, 2) == []


# ---- 2. a contradiction names what each side rests on --------------------

def test_a_contradiction_keeps_its_bases_and_names_the_unsupported_side(tmp_path):
    case = make_case(tmp_path)
    bases = [{"passage": CONTRADICTION["quotes"][0],
              "rests_on": "The erasure leaves an entry of its own naming the date."},
             {"passage": CONTRADICTION["quotes"][1], "rests_on": ""}]
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "witness": WITNESS, "bases": bases}))
    j = summary["topics"][0]["judgement"]
    assert j["bases"][0]["rests_on"].startswith("The erasure leaves")
    assert j["unsupported_sides"] == [CONTRADICTION["quotes"][1]]


def test_a_basis_not_found_in_the_earlier_states_fails_the_judgement(tmp_path):
    case = make_case(tmp_path)
    bases = [{"passage": "x", "rests_on": "a promise nobody ever made anywhere"}]
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "witness": WITNESS, "bases": bases}))
    j = summary["topics"][0]["judgement"]
    assert j["blocking"] is True and "earlier states" in j["failure"]


def test_a_basis_quoted_from_this_state_is_not_an_earlier_basis(tmp_path):
    case = make_case(tmp_path)
    bases = [{"passage": "x", "rests_on": "Lists are ordered by name."}]
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "witness": WITNESS, "bases": bases}))
    assert "earlier states" in summary["topics"][0]["judgement"]["failure"]


def test_a_contradiction_without_bases_is_marked(tmp_path):
    case = make_case(tmp_path)
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "witness": WITNESS}))
    assert summary["topics"][0]["judgement"]["bases_missing"] is True


# ---- 3. a closed unit naming a changed decision is asked again ------------

def test_units_naming_a_changed_decision_are_found():
    current = units.units([(2, "02_rules.md", RULES)], 2)
    assert units.referencing(current, ["A01"], scope=["A01"]) == {"A02": ["A01"]}
    assert units.referencing(current, ["A01"], scope=["A01", "A02"]) == {}
    assert units.referencing(current, ["A03"], scope=["A03"]) == {}
    # A1 is not A01, and A011 is not A01
    assert units.referencing({"X": {"text": "see A011 and A1"}}, ["A01"], []) == {}


def test_editing_a_closed_decision_reopens_the_closed_decisions_that_name_it(tmp_path):
    case = make_case(tmp_path, git=True)
    silent = {"kind": "indifferent", "why": "no one acts on it"}
    for _ in range(2):
        service.ask_round(case, 2, Provider([[], [], []], silent))
    commit(case, "two clear rounds")
    (case / "02_rules.md").write_text(RULES.replace("whatever it removed", "only when it removed one"),
                                      encoding="utf-8")
    commit(case, "edit A01")
    provider = Provider([[], [], []], silent)
    summary = service.ask_round(case, 2, provider)
    assert summary["changed_units"] == ["A01"]
    assert summary["referenced_by_change"] == {"A02": ["A01"]}
    assert summary["scope"] == ["A01", "A02"]
    assert "it names A01, which" in provider.instructions[0]
    # a clear review of the referencing unit on its unchanged text keeps it closed
    assert "A02" not in summary["open_units"]


# ---- 4. where a quoted earlier passage came from --------------------------

def test_a_judgement_keeps_the_commit_and_date_of_each_earlier_passage_it_quotes(tmp_path):
    case = make_case(tmp_path, git=True)
    first = run(case, "rev-parse", "HEAD").strip()
    (case / "00_product.md").write_text(PRODUCT + "\nA later promise about revisions of every record.\n",
                                        encoding="utf-8")
    commit(case, "R0-35", date="2026-10-27T10:00:00")
    second = run(case, "rev-parse", "HEAD").strip()
    bases = [{"passage": CONTRADICTION["quotes"][0],
              "rests_on": "The erasure leaves an entry of its own naming the date."},
             {"passage": CONTRADICTION["quotes"][1], "rests_on": "A later promise about revisions of every record."}]
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "witness": WITNESS, "bases": bases}))
    found = {p["quote"]: p for p in summary["topics"][0]["judgement"]["provenance"]}
    erasure = found["The erasure leaves an entry of its own naming the date."]
    assert erasure["commit"] == first and erasure["date"] == "2026-10-26" and erasure["state"] == 0
    later = found["A later promise about revisions of every record."]
    assert later["commit"] == second and later["date"] == "2026-10-27"
    # the passages of the asked state itself get no entry
    assert all(p["state"] < 2 for p in found.values())


def test_provenance_is_skipped_quietly_outside_git(tmp_path):
    case = make_case(tmp_path)
    bases = [{"passage": "x", "rests_on": "The erasure leaves an entry of its own naming the date."}]
    summary = service.ask_round(case, 2, Provider(twice(), {**CONTRADICTION, "witness": WITNESS, "bases": bases}))
    entry = summary["topics"][0]["judgement"]["provenance"][0]
    assert entry["document"] == "00_product.md" and "commit" not in entry
