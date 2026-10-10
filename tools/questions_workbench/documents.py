"""Which design texts a question round reads, and what it asks about them."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEQUENCE = ROOT / "skills" / "spec-authoring" / "authoring_sequence.json"
STATE_HEADING = re.compile(r"^#\s+State\s+(\d+)\b", re.IGNORECASE)
# State 7 is asked module by module, on the prompts the Factory builds (units.py).
MODULE_STATE = 7
SPEC_FILE = "global_spec.json"
FACTORY_ROOT_ENV = "SPEC_WORKBENCH_FACTORY_ROOT"


class QuestionScopeError(ValueError):
    pass


def text_state(text: str) -> int | None:
    """The state a design text belongs to, read from its first heading."""
    for line in text.splitlines():
        if line.startswith("#"):
            match = STATE_HEADING.match(line)
            return int(match.group(1)) if match else None
    return None


def document_state(path: Path) -> int | None:
    """The state a design document belongs to, read from its first heading."""
    return text_state(path.read_text(encoding="utf-8"))


def design_documents(case: Path, state: int) -> list[tuple[int, Path]]:
    """Top-level documents of states 0..state, in state order."""
    found = []
    for path in sorted(case.glob("*.md")):
        found_state = document_state(path)
        if found_state is not None and found_state <= state:
            found.append((found_state, path))
    return sorted(found, key=lambda item: (item[0], item[1].name))


def later_documents(case: Path, state: int) -> list[tuple[int, Path]]:
    """Top-level documents of the states after `state`, in state order."""
    found = []
    for path in sorted(case.glob("*.md")):
        found_state = document_state(path)
        if found_state is not None and found_state > state:
            found.append((found_state, path))
    return sorted(found, key=lambda item: (item[0], item[1].name))


def question_scope(state: int, sequence_path: Path = SEQUENCE) -> str:
    """The stop rule of a state: which questions belong to it."""
    sequence = json.loads(sequence_path.read_text(encoding="utf-8"))
    for phase in sequence["phases"]:
        if phase.get("semantic_state") == state and phase.get("question_scope"):
            return str(phase["question_scope"])
    raise QuestionScopeError(f"no phase of State {state} declares a question_scope")


def question_states(sequence_path: Path = SEQUENCE) -> list[int]:
    """The states that declare a question_scope, in order."""
    sequence = json.loads(sequence_path.read_text(encoding="utf-8"))
    return sorted({int(p["semantic_state"]) for p in sequence["phases"]
                   if p.get("question_scope") and p.get("semantic_state") is not None})


def factory_root() -> Path | None:
    """The Factory checkout SPEC_WORKBENCH_FACTORY_ROOT names, or the sibling
    `code_factory`; None when there is none."""
    override = os.environ.get(FACTORY_ROOT_ENV)
    if override:
        return Path(override)
    for candidate in (ROOT.parent / "code_factory", ROOT.parent.parent / "code_factory"):
        if (candidate / "tools" / "generate_agent.py").is_file():
            return candidate
    return None
