from __future__ import annotations

import json

import pytest

import design_questions
from questions_workbench import documents, service


class FakeProvider:
    """Answers reviews from a script and groups points by their subject."""

    name = "fake"

    def __init__(self, reviews: list[list[dict]]):
        self.reviews = list(reviews)

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                subject = rest[1:rest.index("]")]
                groups.setdefault(subject, []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        return json.dumps({"open_points": self.reviews.pop(0)}), {"total_tokens": 1}


def _case(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text("# State 0 — Demo\n\nA product.\n", encoding="utf-8")
    (case / "01_models.md").write_text("# State 1 — Demo models\n\n## Model M01 — Thing\n", encoding="utf-8")
    (case / "02_rules.md").write_text("# State 2 — Demo rules\n", encoding="utf-8")
    (case / "notes.md").write_text("no state heading\n", encoding="utf-8")
    return case


def _point(subject: str) -> dict:
    return {"subject": subject, "kind": "identity", "text": "x", "question": f"who mints {subject}?",
            "options": [], "default_guess": "uuid"}


def test_documents_are_the_states_up_to_the_asked_one(tmp_path):
    case = _case(tmp_path)
    assert [p.name for _, p in documents.design_documents(case, 1)] == ["00_product.md", "01_models.md"]


def test_every_design_state_up_to_5_declares_a_question_scope():
    for state in range(6):
        assert documents.question_scope(state)


def test_a_topic_raised_by_two_reviews_keeps_the_state_open(tmp_path):
    case = _case(tmp_path)
    provider = FakeProvider([[_point("M01")], [_point("M01"), _point("M02")], []])
    summary = service.ask_round(case, 1, provider)
    assert summary["closed"] is False
    assert summary["repeated_topics"] == 1
    assert summary["topics"][0]["runs"] == [1, 2]
    assert (case / "questions" / "state1" / "round-01" / "review-3.json").is_file()
    assert service.status(case, 1)["closed"] is False


def test_single_review_topics_close_the_state_until_the_texts_change(tmp_path):
    case = _case(tmp_path)
    service.ask_round(case, 1, FakeProvider([[_point("M01")], [_point("M02")], []]))
    assert service.status(case, 1)["closed"] is True
    (case / "01_models.md").write_text("# State 1 — Demo models\n\nchanged\n", encoding="utf-8")
    result = service.status(case, 1)
    assert result["closed"] is False and result["stale"] is True


def test_rounds_are_numbered_and_kept(tmp_path):
    case = _case(tmp_path)
    service.ask_round(case, 1, FakeProvider([[], [], []]))
    service.ask_round(case, 1, FakeProvider([[], [], []]))
    assert service.status(case, 1)["round"] == "round-02"


def test_a_round_needs_the_state_document_and_two_reviews(tmp_path):
    case = _case(tmp_path)
    with pytest.raises(service.QuestionRoundError):
        service.ask_round(case, 3, FakeProvider([[], [], []]))
    with pytest.raises(service.QuestionRoundError):
        service.ask_round(case, 1, FakeProvider([[]]), runs=1)


def test_status_without_a_round_is_open(tmp_path, capsys):
    case = _case(tmp_path)
    assert design_questions.main(["status", str(case), "--state", "1"]) == 1
    assert "no question round yet" in capsys.readouterr().out
