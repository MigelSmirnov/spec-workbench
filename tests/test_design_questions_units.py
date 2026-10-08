from __future__ import annotations

import json

import pytest

import design_questions
from questions_workbench import service, units

RULES = """# State 2 — Demo rules

Preamble of the rules.

## Accepted decision A01 — first

Rule one.

## Accepted decision A02 — second

Rule two.

## Carried to later states

Nothing.
"""


class UnitProvider:
    """Reviews from a script; groups points by subject; judges a topic blocking
    exactly when its subject is in `blocking` (as a quoted gap)."""

    name = "fake"

    def __init__(self, reviews: list[list[dict]], blocking: set[str] = frozenset()):
        self.reviews = list(reviews)
        self.blocking = set(blocking)
        self.instructions: list[str] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            listing = text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
            judgements = []
            for line in listing:
                if line[:1] == "T":
                    tid, subject = line.split(": ", 1)
                    if subject in self.blocking:
                        judgements.append({"id": tid, "kind": "consequential_gap", "quotes": ["Rule one."],
                                           "divergence": "a or b; the owner notices"})
                    else:
                        judgements.append({"id": tid, "kind": "indifferent", "why": "no one acts on it"})
            return json.dumps({"judgements": judgements}), {}
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                groups.setdefault(rest[1:rest.index("]")], []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        self.instructions.append(instruction)
        return json.dumps({"open_points": self.reviews.pop(0)}), {}


def _point(subject: str, unit: str | None) -> dict:
    point = {"subject": subject, "kind": "gap", "text": "x", "question": f"what about {subject}?",
             "options": [], "default_guess": "y"}
    if unit is not None:
        point["unit"] = unit
    return point


def _case(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text("# State 0 — Demo\n\nA product.\n", encoding="utf-8")
    (case / "01_models.md").write_text("# State 1 — Demo models\n\n## Model M01 — Thing\n", encoding="utf-8")
    (case / "02_rules.md").write_text(RULES, encoding="utf-8")
    return case


def _ask(case, points=None, blocking=()):
    reviews = [list(points or []), list(points or []), []]
    provider = UnitProvider(reviews, set(blocking))
    return service.ask_round(case, 2, provider), provider


def test_a_state_with_decisions_is_cut_into_decision_section_preamble_and_context_units(tmp_path):
    case = _case(tmp_path)
    texts = [(0, "00_product.md", "# State 0\n"), (2, "02_rules.md", RULES)]
    found = units.units(texts, 2)
    assert list(found) == ["02_rules.md:preamble", "A01", "A02", "02_rules.md:Carried to later states", "context"]
    assert units.units([(1, "01_models.md", "# State 1\n## Model M01 — Thing\n")], 1) is None


def test_the_first_round_reviews_every_unit_and_asks_each_point_to_name_one(tmp_path):
    case = _case(tmp_path)
    summary, provider = _ask(case)
    assert summary["scope"] == ["02_rules.md:preamble", "A01", "A02", "02_rules.md:Carried to later states", "context"]
    assert "Units under review" in provider.instructions[0] and "- A01: Accepted decision A01" in provider.instructions[0]


def test_a_blocking_topic_keeps_only_its_unit_open_and_the_next_round_asks_only_about_it(tmp_path):
    case = _case(tmp_path)
    for _ in range(2):
        summary, _ = _ask(case, [_point("first", "A01")], blocking={"first"})
        assert summary["blocked_units"] == ["A01"] and summary["clear"] is False
    assert summary["open_units"] == ["A01"]
    summary, provider = _ask(case)
    assert summary["scope"] == ["A01"]
    assert "- A02" not in provider.instructions[0]


def test_a_unit_closes_after_two_rounds_clear_for_it_and_the_state_with_its_last_unit(tmp_path):
    case = _case(tmp_path)
    _ask(case, [_point("first", "A01")], blocking={"first"})
    _ask(case)
    assert service.status(case, 2)["open_units"] == ["A01"]
    summary, _ = _ask(case)
    assert summary["closed"] is True
    result = service.status(case, 2)
    assert result["closed"] is True and result["open_units"] == []
    with pytest.raises(service.QuestionRoundError, match="nothing to ask"):
        _ask(case)


def _close_all(case):
    _ask(case)
    _ask(case)
    assert service.status(case, 2)["closed"] is True


def test_editing_one_decision_reopens_only_that_decision(tmp_path):
    case = _case(tmp_path)
    _close_all(case)
    (case / "02_rules.md").write_text(RULES.replace("Rule two.", "Rule two, sharper."), encoding="utf-8")
    assert service.status(case, 2)["open_units"] == ["A02"]
    summary, _ = _ask(case)
    assert summary["scope"] == ["A02"]


def test_editing_an_earlier_state_reopens_only_the_context_unit(tmp_path):
    case = _case(tmp_path)
    _close_all(case)
    (case / "00_product.md").write_text("# State 0 — Demo\n\nA changed product.\n", encoding="utf-8")
    assert service.status(case, 2)["open_units"] == ["context"]


def test_a_point_about_a_closed_unit_is_set_aside(tmp_path):
    case = _case(tmp_path)
    _ask(case, [_point("first", "A01")], blocking={"first"})
    _ask(case, [_point("first", "A01")], blocking={"first"})
    summary, _ = _ask(case, [_point("second", "A02")], blocking={"second"})
    assert summary["set_aside"] == [1, 1, 0] and summary["topics"] == []
    review = json.loads((case / "questions" / "state2" / summary["round"] / "review-1.json").read_text())
    assert review["set_aside"][0]["unit"] == "A02"


def test_a_blocking_point_that_names_no_unit_keeps_every_reviewed_unit_open(tmp_path):
    case = _case(tmp_path)
    summary, _ = _ask(case, [_point("loose", None)], blocking={"loose"})
    assert summary["blocked_units"] == sorted(summary["scope"])
    assert summary["topics"][0]["units"] == [units.UNKNOWN]


def test_rounds_kept_before_units_do_not_close_a_unit(tmp_path):
    case = _case(tmp_path)
    directory = case / "questions" / "state2" / "round-01"
    directory.mkdir(parents=True)
    (directory / "summary.json").write_text(json.dumps({"round": "round-01", "documents": {}, "clear": True,
                                                        "closed": True, "topics": []}), encoding="utf-8")
    summary, _ = _ask(case)
    assert summary["closed"] is False and len(summary["scope"]) == 5


def test_the_human_round_names_units(tmp_path, capsys):
    case = _case(tmp_path)
    summary, _ = _ask(case, [_point("first", "A01")], blocking={"first"})
    text = design_questions._human_round(summary)
    assert "units: reviewed=5 blocked=['A01']" in text and "(A01)" in text


LONG_RULES = """# State 2 — Demo rules

## Accepted decision A01 — first

Rule one.

## Accepted decision A02 — second

1. The first rule of the second decision stays as it was.
2. Filler line one.
3. Filler line two.
4. Filler line three.
5. Filler line four.
6. Filler line five.
7. The last rule of the second decision is about the spool size.
"""


def _git(case, *args):
    import subprocess
    subprocess.run(["git", "-C", str(case), *args], check=True, capture_output=True)


def _git_case(tmp_path):
    case = _case(tmp_path)
    (case / "02_rules.md").write_text(LONG_RULES, encoding="utf-8")
    _git(case, "init", "-q")
    _git(case, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(case, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "closed texts")
    _close_all(case)
    return case


def test_a_closed_unit_edited_later_is_reviewed_for_its_change_only(tmp_path):
    case = _git_case(tmp_path)
    edited = LONG_RULES.replace("about the spool size.", "about the spool size, now bounded.")
    (case / "02_rules.md").write_text(edited, encoding="utf-8")
    summary, provider = _ask(case)
    assert summary["scope"] == ["A02"] and summary["changed_units"] == ["A02"]
    instruction = provider.instructions[0]
    assert "has changed since" in instruction and "+7. The last rule of the second decision is about the spool size, now bounded." in instruction


def test_a_point_on_an_unchanged_passage_of_a_changed_unit_is_set_aside(tmp_path):
    case = _git_case(tmp_path)
    edited = LONG_RULES.replace("about the spool size.", "about the spool size, now bounded.")
    (case / "02_rules.md").write_text(edited, encoding="utf-8")
    old_point = {**_point("old", "A02"), "text": "The first rule of the second decision stays as it was."}
    new_point = {**_point("new", "A02"), "text": "is about the spool size, now bounded."}
    summary, _ = _ask(case, [old_point, new_point], blocking={"old", "new"})
    assert summary["set_aside"] == [1, 1, 0]
    assert [t["topic"] for t in summary["topics"]] == ["new"] and summary["blocked_units"] == ["A02"]
    review = json.loads((case / "questions" / "state2" / summary["round"] / "review-1.json").read_text())
    assert review["set_aside"][0]["set_aside_because"].startswith("an unchanged passage")


def test_without_the_closed_text_in_git_a_changed_unit_is_reviewed_whole(tmp_path):
    case = _case(tmp_path)
    _close_all(case)
    (case / "02_rules.md").write_text(RULES.replace("Rule two.", "Rule two, sharper."), encoding="utf-8")
    summary, provider = _ask(case)
    assert summary["changed_units"] == [] and "has changed since" not in provider.instructions[0]
