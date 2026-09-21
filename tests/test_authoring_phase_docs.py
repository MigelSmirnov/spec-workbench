"""Every authoring phase owns its own reading list; `authoring next` returns it."""

from __future__ import annotations

import re
from pathlib import Path

import design_authoring_next

ROOT = Path(__file__).resolve().parents[1]


def _headings(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {m.group(1).strip() for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.M)}


def test_every_phase_declares_existing_docs() -> None:
    sequence = design_authoring_next.load_sequence()
    for phase in sequence["phases"]:
        docs = phase.get("docs")
        assert docs, f"{phase['id']} has no docs"
        for doc in docs:
            path = ROOT / doc["path"]
            assert path.is_file(), f"{phase['id']}: {doc['path']} does not exist"
            assert doc.get("why"), f"{phase['id']}: {doc['path']} has no why"
            if doc.get("section"):
                assert doc["section"] in _headings(path), (
                    f"{phase['id']}: section {doc['section']!r} not found in {doc['path']}"
                )


def test_read_policy_is_phase_scoped() -> None:
    sequence = design_authoring_next.load_sequence()
    policy = sequence["read_policy"]
    assert policy["always"] == ["AGENTS.md"]
    assert (ROOT / "AGENTS.md").is_file()


def test_next_step_returns_phase_docs(tmp_path: Path) -> None:
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text("# Product\n", encoding="utf-8")
    payload = design_authoring_next.next_step(case)
    sequence = design_authoring_next.load_sequence()
    expected = design_authoring_next._phase(sequence, payload["phase"])["docs"]
    assert payload["read"] == [
        {k: v for k, v in doc.items() if k in {"path", "section", "why"}} for doc in expected
    ]


MAX_QUESTIONS = 5
MAX_WORDS = 30


def test_phase_questions_are_few_short_and_questions() -> None:
    """What a gate cannot judge is asked, briefly. A sixth question means a gate is missing."""
    sequence = design_authoring_next.load_sequence()
    asked = 0
    for phase in sequence["phases"]:
        questions = phase.get("questions") or []
        assert len(questions) <= MAX_QUESTIONS, f"{phase['id']} asks {len(questions)} questions"
        assert len(set(questions)) == len(questions), f"{phase['id']} repeats a question"
        for question in questions:
            assert question.endswith("?"), f"{phase['id']}: not a question: {question!r}"
            assert len(question.split()) <= MAX_WORDS, f"{phase['id']}: too long: {question!r}"
        asked += len(questions)
    assert asked, "no phase asks anything"


def test_no_phase_sends_the_author_to_the_skill() -> None:
    """The skill is an entry page. Method text reaches the author through `authoring next`."""
    sequence = design_authoring_next.load_sequence()
    for phase in sequence["phases"]:
        for doc in phase["docs"]:
            assert not doc["path"].endswith("/SKILL.md"), f"{phase['id']} still reads SKILL.md"


def test_skill_stays_an_entry_page() -> None:
    lines = (ROOT / "skills/spec-authoring/SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 60, f"SKILL.md grew to {len(lines)} lines; method text belongs to authoring_sequence.json"


def test_next_step_returns_purpose_and_questions(tmp_path: Path) -> None:
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text("# Product\n", encoding="utf-8")
    payload = design_authoring_next.next_step(case)
    phase = design_authoring_next._phase(design_authoring_next.load_sequence(), payload["phase"])
    assert payload["purpose"] == phase.get("purpose", "")
    assert payload["ask"] == (phase.get("questions") or [])
