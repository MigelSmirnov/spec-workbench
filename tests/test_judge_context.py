"""The judge of a document round reads the topics inline and searches the rest (#147, 2026-11-08)."""
from __future__ import annotations

import json
import subprocess

import pytest

from questions_workbench import judge_context, service

MODELS = """# State 1 — Demo models

## Model M01 — Invoice

An Invoice holds an amount and a due date fixed when it is issued.

## Model M02 — Courier

A Courier carries parcels between depots on a weekly rota.
"""

RULES = """# State 2 — Demo rules

## Accepted decision A1 — Invoice amount

Rule one: an `Invoice` amount never changes once the invoice is issued.

## Accepted decision A2 — Rota length

Rule two: the courier rota repeats every seven days without exception.
"""

TOPIC_UNIT = "Rule one: an `Invoice` amount never changes once the invoice is issued."
QUOTED_EARLIER = "An Invoice holds an amount and a due date fixed when it is issued."
UNRELATED_UNIT = "Rule two: the courier rota repeats every seven days without exception."
UNRELATED_EARLIER = "A Courier carries parcels between depots on a weekly rota."


def _case(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text("# State 0 — Demo\n\nA product that bills.\n", encoding="utf-8")
    (case / "01_models.md").write_text(MODELS, encoding="utf-8")
    (case / "02_rules.md").write_text(RULES, encoding="utf-8")
    return case


def _point(unit: str, text: str) -> dict:
    return {"subject": unit, "kind": "gap", "text": text, "question": f"what does {unit} leave open?",
            "options": [], "default_guess": "y", "unit": unit}


class Provider:
    """Two reviews raise one topic on A1, quoting a State 1 passage; the third
    raises one on A2. Every judged topic gets `verdict`."""

    name = "fake"

    def __init__(self, verdict: dict):
        self.verdict = verdict
        self.reviews = [[_point("A1", QUOTED_EARLIER)], [_point("A1", QUOTED_EARLIER)], [_point("A2", "x")]]
        self.judged: list[tuple[str, str]] = []
        self.files: list[dict[str, str]] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            self.judged.append((instruction, text))
            ids = [line.split(":", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                   if line[:1] == "T"]
            return json.dumps({"judgements": [{"id": i, **self.verdict} for i in ids]}), {}
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                groups.setdefault(rest[1:rest.index("]")], []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        return json.dumps({"open_points": self.reviews.pop(0)}), {}


class FilesProvider(Provider):
    reads_files = True

    def complete_with_files(self, instruction: str, text: str, files: dict[str, str]):
        self.files.append(dict(files))
        return self.complete(instruction, text)


ANSWERED = {"kind": "answered", "quotes": [UNRELATED_EARLIER]}  # a passage the judge found by searching


def test_a_judge_that_reads_files_gets_the_topic_units_and_quoted_passages_inline_only(tmp_path):
    case = _case(tmp_path)
    provider = FilesProvider(ANSWERED)
    summary = service.ask_round(case, 2, provider)
    (instruction, text), = provider.judged
    assert TOPIC_UNIT in text and QUOTED_EARLIER in text
    assert UNRELATED_UNIT not in text and UNRELATED_EARLIER not in text
    # the full texts are files the judge searches, and it is told so
    files = provider.files[0]
    assert files["states/01_models.md"] == MODELS and files["states/02_rules.md"] == RULES
    assert "states/00_product.md" in files
    assert "states/02_rules.md" in instruction
    # a quote found only in a file still stands: the check reads the full texts
    assert summary["topics"][0]["judgement"]["verified"] is True
    assert summary["judge"]["searched_files"] == sorted(files)
    assert "quoted" not in summary["topics"][0]


def test_a_judge_without_files_still_reads_the_round_text_inline(tmp_path):
    case = _case(tmp_path)
    provider = Provider(ANSWERED)
    summary = service.ask_round(case, 2, provider)
    (instruction, text), = provider.judged
    # A2 is under review, so the round text holds it, and so does the judge's
    assert TOPIC_UNIT in text and UNRELATED_UNIT in text
    assert "states/" not in instruction and provider.files == []
    assert "searched_files" not in summary["judge"]


def test_the_check_still_rejects_a_quote_not_in_the_full_texts(tmp_path):
    case = _case(tmp_path)
    provider = FilesProvider({"kind": "answered", "quotes": ["An Invoice may be reissued with a new amount later."]})
    summary = service.ask_round(case, 2, provider)
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "not found verbatim" in judgement["failure"]


def test_a_reopened_state_gives_the_topic_unit_diff_inline_and_the_closed_texts_as_files(tmp_path):
    case = _case(tmp_path)
    run = lambda *a: subprocess.run(["git", "-C", str(case), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                                    check=True, capture_output=True)
    run("init", "-q")
    run("add", ".")
    run("commit", "-q", "-m", "closed")
    (case / "02_rules.md").write_text(RULES.replace("is issued.", "is issued, even by the owner."),
                                      encoding="utf-8")
    provider = FilesProvider(ANSWERED)
    service.ask_round(case, 2, provider, since="HEAD")
    (instruction, text), = provider.judged
    assert "+Rule one: an `Invoice` amount never changes once the invoice is issued, even by the owner." in text
    assert provider.files[0]["closed/02_rules.md"] == RULES
    assert "closed/02_rules.md" in instruction
    assert UNRELATED_UNIT not in text


def test_a_topic_naming_no_unit_brings_every_unit_under_review():
    texts = [(1, "01_models.md", MODELS), (2, "02_rules.md", RULES)]
    topic = {"topic": "?", "questions": [], "units": ["?"], "quoted": []}
    selected = judge_context.select(texts, 2, [topic], ["A1", "A2"], None)
    assert [key for key, _ in selected.own] == ["A1", "A2"]


def test_the_topics_and_their_units_bring_the_earlier_units_they_name():
    texts = [(1, "01_models.md", MODELS), (2, "02_rules.md", RULES)]
    topic = {"topic": "amounts", "questions": ["when is it issued?"], "units": ["A1"], "quoted": []}
    selected = judge_context.select(texts, 2, [topic], ["A1", "A2"], None)
    assert [key for _, _, key, _ in selected.received] == ["01_models.md:Model M01 — Invoice"]


class Malformed(Provider):
    """The first review to arrive answers prose `bad` times before JSON."""

    def __init__(self, verdict: dict, bad: int):
        super().__init__(verdict)
        import threading
        self.lock, self.bad, self.owner, self.calls = threading.Lock(), bad, None, 0

    def complete(self, instruction: str, text: str):
        import threading
        if instruction.startswith(("You judge the topics", "You receive the open points")):
            return super().complete(instruction, text)
        with self.lock:
            if self.owner is None:
                self.owner = threading.get_ident()
            if self.owner == threading.get_ident() and self.bad:
                self.bad -= 1
                self.calls += 1
                return "I could not decide; here are my thoughts.", {}
        return super().complete(instruction, text)


def test_a_review_answering_prose_once_is_asked_again(tmp_path):
    case = _case(tmp_path)
    provider = Malformed(ANSWERED, bad=1)
    summary = service.ask_round(case, 2, provider)
    assert summary["failed_reviews"] == [] and summary["points"] == [1, 1, 1]
    kept = [json.loads(p.read_text()) for p in sorted((case / "questions" / "state2" / "round-01").glob("review-*"))]
    assert sum(1 for r in kept if r.get("retried")) == 1


def test_a_review_answering_prose_twice_is_recorded_failed_and_the_round_goes_on(tmp_path):
    case = _case(tmp_path)
    provider = Malformed(ANSWERED, bad=2)
    provider.reviews = [[_point("A1", QUOTED_EARLIER)], [_point("A1", QUOTED_EARLIER)]]
    summary = service.ask_round(case, 2, provider)
    failed, = summary["failed_reviews"]
    assert "JSON object" in failed["reason"]
    kept = json.loads((case / "questions" / "state2" / "round-01" / failed["review"]).read_text())
    assert kept["open_points"] == [] and len(kept["answers"]) == 2  # nothing fabricated
    assert summary["repeated_topics"] == 1  # the two answering reviews still raise and judge it


def test_a_round_with_fewer_than_two_answering_reviews_is_refused():
    failed = service._failed_review(service.ReviewFailed("no JSON", ["a", "b"]))
    with pytest.raises(service.QuestionRoundError, match="only 1 of 3 reviews answered"):
        service._valid_reviews([failed, dict(failed), {"open_points": []}], "State 2")
    service._valid_reviews([failed, {"open_points": []}, {"open_points": []}], "State 2")
