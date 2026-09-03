"""Transport-neutral Spec Workbench authoring pipeline API.

CLI and future MCP transports must call this module. It resolves a logical
project through PROJECT_INDEX.json, materializes its canonical ref read-only in
a temporary git worktree, and delegates phase selection to design_authoring_next.
"""
from __future__ import annotations

import contextlib
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterator

import design_authoring_next
import project_navigation


class AuthoringPipelineError(RuntimeError):
    pass


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise AuthoringPipelineError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def find_repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    return Path(_git(start, "rev-parse", "--show-toplevel").strip()).resolve()


def sequence() -> dict[str, Any]:
    return design_authoring_next.load_sequence()


def _materialize(repo_root: Path, ref: str, target: Path) -> None:
    _git(repo_root, "worktree", "add", "--detach", "--quiet", str(target), ref)


def _remove_worktree(repo_root: Path, target: Path) -> None:
    _git(repo_root, "worktree", "remove", "--force", str(target), check=False)
    _git(repo_root, "worktree", "prune", check=False)


@contextlib.contextmanager
def materialized_project(
    repo_root: Path, project_or_query: Any
) -> Iterator[tuple[project_navigation.ProjectView, Path]]:
    """Yield (view, case_root) on a temporary read-only worktree of the canonical ref.

    Every transport answers from the project's canonical ref, never from
    whatever branch a working checkout happens to sit on. The worktree is
    removed when the context exits; callers must not write into it or hand its
    paths out beyond the context.
    """
    repo_root = repo_root.resolve()
    view = project_navigation.project_view(repo_root, project_or_query)
    with tempfile.TemporaryDirectory(prefix="spec-workbench-authoring-") as tmp:
        target = Path(tmp) / "repo"
        _materialize(repo_root, view.resolved_ref, target)
        try:
            yield view, target / view.path
        finally:
            _remove_worktree(repo_root, target)


def project_next(repo_root: Path, project_query: str) -> dict[str, Any]:
    """Resolve one logical project and return its next authoring phase.

    The materialized project checkout is read-only from the pipeline's point of
    view: the sequencer and gates only inspect it. Authoring mutations remain an
    explicit user/agent action on the canonical project branch.
    """
    with materialized_project(repo_root, project_query) as (view, case_root):
        payload = design_authoring_next.next_step(
            case_root,
            display_path=view.path,
        )

    action = payload.get("action")
    if action is not None:
        # Low-level tool metadata is useful to agents/MCP, but its shell command
        # assumes a materialized project checkout. The top-level pipeline owns
        # that checkout, so transports must not execute the rendered command
        # blindly after this call returns.
        action["execution"] = "pipeline_managed_project_checkout"
        action["command"] = None

    return {
        "schema_version": "spec_workbench_project_authoring.v1",
        "project": {
            "id": view.id,
            "title": view.title,
            "canonical_ref": view.canonical_ref,
            "resolved_ref": view.resolved_ref,
            "path": view.path,
        },
        "authoring": payload,
    }
