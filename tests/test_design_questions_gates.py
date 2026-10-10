"""Question rounds cover late decisions: units for every state, and the
carried closure of a state closed as one text."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from questions_workbench import documents, service

MODULES = """# State 3 — Demo modules

Why the modules are cut this way.

## Module store

1. The store keeps every record.
2. Filler one.
3. Filler two.
4. Filler three.
5. Filler four.
6. Filler five.
7. The store refuses a record over the size limit.

## Module surface

The surface serves the owner.
"""


class Provider:
    """Clear reviews unless `points` are given; groups by subject; judges every
    topic as a quoted gap (blocking) when its subject is in `blocking`."""

    name = "fake"

    def __init__(self, points: list[dict] | None = None, blocking: set[str] = frozenset()):
        self.points = points or []
        self.blocking = set(blocking)
        self.instructions: list[str] = []
        self.inputs: list[str] = []
        self.judged: list[str] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            listing = text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
            judgements = []
            for line in listing:
                if line[:1] == "T":
                    tid, subject = line.split(": ", 1)
                    if subject in self.blocking:
                        judgements.append({"id": tid, "kind": "consequential_gap", "divergence": "a or b; the owner notices"})
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
        self.inputs.append(text)
        return json.dumps({"open_points": list(self.points)}), {}


def _point(subject: str, unit: str | None = None, text: str = "x") -> dict:
    point = {"subject": subject, "kind": "gap", "text": text, "question": f"what about {subject}?",
             "options": [], "default_guess": "y"}
    if unit:
        point["unit"] = unit
    return point


def _git(case: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(case), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          check=True, capture_output=True, text=True)
    return done.stdout


def _commit(case: Path, message: str) -> None:
    _git(case, "add", "-A")
    _git(case, "commit", "-qm", message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _legacy_round(case: Path, state: int, number: int) -> None:
    """A round kept before units existed: clear, on the documents as they are."""
    directory = service.rounds_dir(case, state) / f"round-{number:02d}"
    directory.mkdir(parents=True)
    digests = {p.name: _sha(p) for _, p in documents.design_documents(case, state)}
    (directory / "summary.json").write_text(json.dumps({
        "schema_version": service.SCHEMA, "state": state, "round": directory.name, "documents": digests,
        "reviews": 3, "points": [0, 0, 0], "judge": {"provider": "fake"}, "repeated_topics": 0,
        "blocking_topics": 0, "clear": True, "closed": number > 1, "topics": [],
    }), encoding="utf-8")


def _closed_as_one_text(tmp_path: Path) -> Path:
    """A State 3 closed as one text by two clear rounds, all committed."""
    case = tmp_path / "demo"
    case.mkdir()
    (case / "30_modules.md").write_text(MODULES, encoding="utf-8")
    _git(case, "init", "-q")
    _commit(case, "State 3 texts")
    _legacy_round(case, 3, 1)
    _legacy_round(case, 3, 2)
    _commit(case, "State 3 closed")
    return case


# 1. Units for every state


def test_a_state_without_decisions_reviews_its_sections_as_units(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "30_modules.md").write_text(MODULES, encoding="utf-8")
    summary = service.ask_round(case, 3, Provider())
    assert summary["scope"] == ["30_modules.md:preamble", "30_modules.md:Module store", "30_modules.md:Module surface"]
    summary = service.ask_round(case, 3, Provider())
    assert summary["closed"] is True and service.status(case, 3)["closed"] is True


# 1. A state closed as one text carries its closure to every unit


def test_a_state_closed_as_one_text_is_closed_unit_by_unit_on_that_text(tmp_path):
    case = _closed_as_one_text(tmp_path)
    result = service.status(case, 3)
    assert result["closed"] is True and result["carried"] is True and result["units"] == 3


def test_after_a_late_edit_only_the_edited_section_is_reviewed_and_by_its_diff(tmp_path):
    case = _closed_as_one_text(tmp_path)
    (case / "30_modules.md").write_text(MODULES.replace("over the size limit.", "over the size limit, now 1 MiB."),
                                        encoding="utf-8")
    result = service.status(case, 3)
    assert result["closed"] is False and result["open_units"] == ["30_modules.md:Module store"]
    assert result["changed_units"] == ["30_modules.md:Module store"] and result["closed_at"]
    unchanged = {"subject": "old", "kind": "gap", "text": "The store keeps every record.", "question": "?",
                 "options": [], "default_guess": "y", "unit": "30_modules.md:Module store"}
    provider = Provider([unchanged, _point("new", "30_modules.md:Module store", "the size limit, now 1 MiB.")],
                        blocking={"old", "new"})
    summary = service.ask_round(case, 3, provider)
    assert summary["scope"] == ["30_modules.md:Module store"]
    assert summary["changed_units"] == ["30_modules.md:Module store"]
    assert "+7. The store refuses a record over the size limit, now 1 MiB." in provider.instructions[0]
    assert "- 30_modules.md:Module surface" not in provider.instructions[0]
    # the point quoting the unchanged first rule is set aside; the one on the change is kept
    assert [t["topic"] for t in summary["topics"]] == ["new"] and summary["set_aside"] == [1, 1, 1]
    assert summary["carried"]["from"] == ["round-01", "round-02"]
    assert service.status(case, 3)["open_units"] == ["30_modules.md:Module store"]


def test_the_carried_closure_survives_the_first_unit_rounds(tmp_path):
    case = _closed_as_one_text(tmp_path)
    (case / "30_modules.md").write_text(MODULES.replace("serves the owner.", "serves the owner only."),
                                        encoding="utf-8")
    service.ask_round(case, 3, Provider())
    summary = service.ask_round(case, 3, Provider())
    assert summary["scope"] == ["30_modules.md:Module surface"] and summary["closed"] is True
    assert service.status(case, 3)["closed"] is True


def test_a_state_never_closed_as_one_text_carries_nothing(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "30_modules.md").write_text(MODULES, encoding="utf-8")
    _legacy_round(case, 3, 1)  # one clear round, not closed
    result = service.status(case, 3)
    assert result["closed"] is False and len(result["open_units"]) == 3
