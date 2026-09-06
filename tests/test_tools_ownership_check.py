from __future__ import annotations

import subprocess
from pathlib import Path

import tools_ownership_check as check


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "tools").mkdir()
    (repo / "tools" / "x.py").write_text("x = 1\n")
    (repo / "examples" / "demo").mkdir(parents=True)
    (repo / "examples" / "demo" / "00_product.md").write_text("# p\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def test_project_branch_may_change_only_its_data(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "agent/demo")
    (repo / "examples" / "demo" / "00_product.md").write_text("# p2\n")
    (repo / "experiments" / "demo").mkdir(parents=True)
    (repo / "experiments" / "demo" / "note.md").write_text("n\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "data")
    paths = check.changed_paths(repo, "main")
    assert paths == ["examples/demo/00_product.md", "experiments/demo/note.md"]
    assert check.violations("agent/demo", paths) == []
    assert check.main(["--base", "main", "--branch", "agent/demo", "--repo", str(repo)]) == 0


def test_project_branch_touching_tools_is_rejected(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "agent/demo")
    (repo / "tools" / "x.py").write_text("x = 2\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_x.py").write_text("def test(): pass\n")
    (repo / "AGENTS.md").write_text("rules\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "tools")
    paths = check.changed_paths(repo, "main")
    assert check.violations("agent/demo", paths) == ["AGENTS.md", "tests/test_x.py", "tools/x.py"]
    assert check.main(["--base", "main", "--branch", "agent/demo", "--repo", str(repo)]) == 1


def test_tooling_branch_may_change_anything(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "tools/land")
    (repo / "tools" / "x.py").write_text("x = 3\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "tools")
    paths = check.changed_paths(repo, "main")
    assert paths == ["tools/x.py"]
    assert check.violations("tools/land", paths) == []
    assert check.main(["--base", "main", "--branch", "tools/land", "--repo", str(repo)]) == 0


def test_ownership_patterns_are_exact() -> None:
    assert check.is_project_owned("examples/demo/global_spec.json")
    assert check.is_project_owned("examples/demo/tools/backend.py")
    assert check.is_project_owned("experiments/cabinet-vault/tools/kernel.py")
    assert not check.is_project_owned("tools/design_lint.py")
    assert not check.is_project_owned("skills/spec-authoring/SPEC_STANDARD.md")
    assert not check.is_project_owned("PROJECT_INDEX.json")
    assert not check.is_project_owned("examples")
