from __future__ import annotations

import subprocess
from pathlib import Path

from workbench import (
    case_state_from_files,
    list_cases,
    next_primary_state,
    repo_status,
)


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "commit", "-m", message)


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Spec Workbench Test")
    return repo


def write(path: Path, text: str = "# state\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_stage_progress_uses_primary_design_states():
    state = case_state_from_files(
        "demo",
        "main",
        [
            "00_product.md",
            "10_models.md",
            "55_generation_units.md",
            "56_pydantic_modeling.md",
        ],
    )
    assert state.stage_code == 10
    assert state.stage_name == "Domain models"
    assert next_primary_state(state) == "20 Rules & invariants"
    assert state.numbered_docs == 4


def test_global_spec_marks_assembly_complete():
    state = case_state_from_files(
        "demo",
        "main",
        ["00_product.md", "70_notes.md", "global_spec.json"],
    )
    assert state.assembled
    assert state.stage_name == "Assembly complete"
    assert next_primary_state(state) == "done"


def test_list_finds_case_that_exists_only_on_another_branch(tmp_path: Path):
    repo = init_repo(tmp_path)
    write(repo / "examples" / "base-case" / "00_product.md")
    commit_all(repo, "base")

    git(repo, "checkout", "-b", "agent/room-planner")
    write(repo / "examples" / "room-planner" / "00_product.md")
    commit_all(repo, "room")
    git(repo, "checkout", "main")

    rows = list_cases(repo)
    by_case = {row.case: row for row in rows}

    assert by_case["base-case"].ref == "main (worktree)"
    assert by_case["room-planner"].ref == "agent/room-planner"
    assert by_case["room-planner"].stage_code == 0


def test_list_does_not_repeat_identical_inherited_case(tmp_path: Path):
    repo = init_repo(tmp_path)
    write(repo / "examples" / "base-case" / "00_product.md")
    write(repo / "examples" / "base-case" / "10_models.md")
    commit_all(repo, "base")

    git(repo, "checkout", "-b", "feature")
    write(repo / "examples" / "feature-only" / "00_product.md")
    commit_all(repo, "feature")
    git(repo, "checkout", "main")

    rows = list_cases(repo)
    base_rows = [row for row in rows if row.case == "base-case"]
    assert len(base_rows) == 1
    assert base_rows[0].ref == "main (worktree)"


def test_status_separates_current_and_other_ref_cases(tmp_path: Path):
    repo = init_repo(tmp_path)
    write(repo / "examples" / "base-case" / "00_product.md")
    commit_all(repo, "base")

    git(repo, "checkout", "-b", "feature")
    write(repo / "examples" / "feature-only" / "00_product.md")
    commit_all(repo, "feature")
    git(repo, "checkout", "main")

    status = repo_status(repo)
    assert [row.case for row in status.current_cases] == ["base-case"]
    assert [row.case for row in status.other_cases] == ["feature-only"]
