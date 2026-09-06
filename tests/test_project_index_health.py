from __future__ import annotations

import json
import subprocess
from pathlib import Path

from workbench import project_rows, unindexed_cases


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


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


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "commit", "-m", message)


def test_list_preserves_stale_index_entry_as_warning(tmp_path: Path):
    repo = init_repo(tmp_path)
    write(
        repo / "PROJECT_INDEX.json",
        json.dumps(
            {
                "projects": [
                    {
                        "id": "gone",
                        "title": "Gone Project",
                        "canonical_ref": "agent/gone",
                        "path": "examples/gone",
                    }
                ]
            }
        ),
    )
    commit_all(repo, "index")

    rows = project_rows(repo)

    assert len(rows) == 1
    assert rows[0]["id"] == "gone"
    assert rows[0]["status"] == "stale"
    assert rows[0]["stage_name"] == "Unavailable"
    assert "agent/gone" in str(rows[0]["problem"])


def test_status_reports_case_missing_from_index(tmp_path: Path):
    repo = init_repo(tmp_path)
    write(repo / "PROJECT_INDEX.json", json.dumps({"projects": [], "reference_cases": []}))
    write(repo / "examples" / "new-project" / "00_product.md")
    commit_all(repo, "new unindexed case")

    assert unindexed_cases(repo) == ["new-project"]


def test_reference_case_is_not_reported_as_unindexed(tmp_path: Path):
    repo = init_repo(tmp_path)
    write(
        repo / "PROJECT_INDEX.json",
        json.dumps(
            {
                "projects": [],
                "reference_cases": [
                    {
                        "id": "reference",
                        "canonical_ref": "main",
                        "path": "examples/reference",
                    }
                ],
            }
        ),
    )
    write(repo / "examples" / "reference" / "00_product.md")
    commit_all(repo, "reference")

    assert unindexed_cases(repo) == []
