"""Which design texts a question round reads, and what it asks about them."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEQUENCE = ROOT / "skills" / "spec-authoring" / "authoring_sequence.json"
STATE_HEADING = re.compile(r"^#\s+State\s+(\d+)\b", re.IGNORECASE)


class QuestionScopeError(ValueError):
    pass


def document_state(path: Path) -> int | None:
    """The state a design document belongs to, read from its first heading."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            match = STATE_HEADING.match(line)
            return int(match.group(1)) if match else None
    return None


def design_documents(case: Path, state: int) -> list[tuple[int, Path]]:
    """Top-level documents of states 0..state, in state order."""
    found = []
    for path in sorted(case.glob("*.md")):
        found_state = document_state(path)
        if found_state is not None and found_state <= state:
            found.append((found_state, path))
    return sorted(found, key=lambda item: (item[0], item[1].name))


def question_scope(state: int, sequence_path: Path = SEQUENCE) -> str:
    """The stop rule of a state: which questions belong to it."""
    sequence = json.loads(sequence_path.read_text(encoding="utf-8"))
    for phase in sequence["phases"]:
        if phase.get("semantic_state") == state and phase.get("question_scope"):
            return str(phase["question_scope"])
    raise QuestionScopeError(f"no phase of State {state} declares a question_scope")
