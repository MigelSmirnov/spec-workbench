from __future__ import annotations

import json
import subprocess
from pathlib import Path

from project_navigation import list_projects, project_view, resolve_project


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


def write_index(repo: Path) -> None:
    payload = {
        "schema_version": 1,
        "projects": [
            {
                "id": "demo",
                "title": "Demo Project",
                "group": "demo",
                "canonical_ref": "agent/demo",
                "path": "examples/demo",
                "aliases": ["the demo"],
                "summary": "Indexed demo project.",
            }
        ],
    }
    write(repo / "PROJECT_INDEX.json", json.dumps(payload))


def test_list_projects_uses_curated_index_not_arbitrary_cases(tmp_path: Path):
    repo = init_repo(tmp_path)
    write_index(repo)
    write(repo / "examples" / "unindexed" / "00_product.md")
    commit_all(repo, "base")

    git(repo, "checkout", "-b", "agent/demo")
    write(repo / "examples" / "demo" / "00_product.md")
    write(repo / "examples" / "demo" / "10_models.md")
    write(repo / "examples" / "demo" / "global_spec.json", "{}\n")
    commit_all(repo, "demo")
    git(repo, "checkout", "main")

    rows = list_projects(repo)

    assert [row.id for row in rows] == ["demo"]
    assert rows[0].canonical_ref == "agent/demo"
    assert rows[0].stage_name == "Assembled artifacts"
    assert "examples/unindexed" not in rows[0].read_order


def test_show_resolves_alias_and_returns_minimal_read_order(tmp_path: Path):
    repo = init_repo(tmp_path)
    write_index(repo)
    commit_all(repo, "base")

    git(repo, "checkout", "-b", "agent/demo")
    write(repo / "examples" / "demo" / "AGENTS.md")
    write(repo / "examples" / "demo" / "01_models.md")
    write(repo / "examples" / "demo" / "spec" / "00_product.md")
    write(repo / "examples" / "demo" / "spec" / "10_models.md")
    write(repo / "examples" / "demo" / "spec" / "20_rules.md")
    commit_all(repo, "demo")
    git(repo, "checkout", "main")

    project = resolve_project(repo, "the demo")
    view = project_view(repo, project)

    assert project.id == "demo"
    assert view.path == "examples/demo"
    assert view.stage_name == "Rules & invariants"
    assert view.read_order == (
        "examples/demo/AGENTS.md",
        "examples/demo/spec/00_product.md",
        "examples/demo/spec/10_models.md",
        "examples/demo/spec/20_rules.md",
    )


def test_single_branch_clone_fetches_only_missing_canonical_ref(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.email", "test@example.com")
    git(source, "config", "user.name", "Spec Workbench Test")
    write_index(source)
    commit_all(source, "index")

    git(source, "checkout", "-b", "agent/demo")
    write(source / "examples" / "demo" / "00_product.md")
    write(source / "examples" / "demo" / "10_models.md")
    commit_all(source, "demo")
    git(source, "checkout", "main")

    origin = tmp_path / "origin.git"
    subprocess.run(
        ["git", "clone", "--bare", str(source), str(origin)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    clone = tmp_path / "clone"
    subprocess.run(
        [
            "git",
            "clone",
            "--single-branch",
            "--branch",
            "main",
            str(origin),
            str(clone),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    remote_refs_before = git(
        clone, "for-each-ref", "--format=%(refname:short)", "refs/remotes"
    ).splitlines()
    assert "origin/agent/demo" not in remote_refs_before

    view = project_view(clone, "demo")

    assert view.resolved_ref == "origin/agent/demo"
    assert view.stage_name == "Domain models"
    remote_refs_after = git(
        clone, "for-each-ref", "--format=%(refname:short)", "refs/remotes"
    ).splitlines()
    assert "origin/agent/demo" in remote_refs_after


def _repo_with_origin(tmp_path: Path) -> tuple[Path, Path]:
    """A clone whose local `agent/demo` exists, with origin holding the same branch."""
    source = tmp_path / "source"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.email", "test@example.com")
    git(source, "config", "user.name", "Spec Workbench Test")
    write_index(source)
    commit_all(source, "index")
    git(source, "checkout", "-b", "agent/demo")
    write(source / "examples" / "demo" / "00_product.md")
    commit_all(source, "demo state 0")
    git(source, "checkout", "main")
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "clone", "--bare", str(source), str(origin)], check=True, capture_output=True)
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", str(origin), str(clone)], check=True, capture_output=True)
    git(clone, "config", "user.email", "test@example.com")
    git(clone, "config", "user.name", "Spec Workbench Test")
    git(clone, "branch", "agent/demo", "origin/agent/demo")
    return clone, source


def test_stale_local_branch_does_not_hide_the_canonical_state(tmp_path: Path):
    clone, source = _repo_with_origin(tmp_path)
    # the branch moves on origin: State 1 is authored and pushed elsewhere
    git(source, "checkout", "agent/demo")
    write(source / "examples" / "demo" / "10_models.md")
    commit_all(source, "demo state 1")
    subprocess.run(["git", "push", "-q", str(tmp_path / "origin.git"), "agent/demo"], cwd=source, check=True, capture_output=True)

    view = project_view(clone, "demo")

    assert view.resolved_ref == "origin/agent/demo"
    assert view.stage_name == "Domain models"


def test_local_branch_ahead_of_origin_is_the_authors_view(tmp_path: Path):
    clone, _source = _repo_with_origin(tmp_path)
    git(clone, "checkout", "-q", "agent/demo")
    write(clone / "examples" / "demo" / "10_models.md")
    commit_all(clone, "unpushed state 1")
    git(clone, "checkout", "-q", "main")

    view = project_view(clone, "demo")

    assert view.resolved_ref == "agent/demo"
    assert view.stage_name == "Domain models"
