#!/usr/bin/env python3
"""Enforce who may change what: generic tooling lives on main, projects own their data.

Project branches (``agent/*`` and any other non-tooling branch) may change only
project-owned paths. Generic tooling paths change only through ``tools/*``
branches merged into ``main``. The check compares the working branch with its
merge base against the base ref and lists every path that violates the rule.

Exit codes: 0 clean, 1 violations, 2 usage/git error.
"""
from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

PROJECT_OWNED = (
    "examples/*/**",
    "examples/*",
    "experiments/*/**",
    "experiments/*",
)
TOOLING_BRANCH_PREFIXES = ("tools/", "main", "master")


class OwnershipError(RuntimeError):
    pass


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo_root), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise OwnershipError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


def is_tooling_branch(branch: str) -> bool:
    return any(branch == prefix.rstrip("/") or branch.startswith(prefix) for prefix in TOOLING_BRANCH_PREFIXES)


def is_project_owned(path: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in PROJECT_OWNED)


def changed_paths(repo_root: Path, base: str, head: str = "HEAD") -> list[str]:
    merge_base = _git(repo_root, "merge-base", base, head).strip()
    out = _git(repo_root, "diff", "--name-only", merge_base, head)
    return sorted(line for line in out.splitlines() if line.strip())


def violations(branch: str, paths: list[str]) -> list[str]:
    if is_tooling_branch(branch):
        return []
    return [path for path in paths if not is_project_owned(path)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="base ref the branch will merge into")
    parser.add_argument("--branch", help="branch name under check (default: current branch)")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        branch = args.branch or _git(args.repo, "branch", "--show-current").strip() or "HEAD"
        paths = changed_paths(args.repo, args.base, args.head)
    except OwnershipError as exc:
        print(f"tools_ownership_check: {exc}", file=sys.stderr)
        return 2
    bad = violations(branch, paths)
    if is_tooling_branch(branch):
        print(f"{branch}: tooling branch, {len(paths)} changed path(s) allowed")
        return 0
    if not bad:
        print(f"{branch}: {len(paths)} changed path(s), all project-owned")
        return 0
    print(f"{branch}: {len(bad)} path(s) outside project ownership; generic tooling changes only on a tools/* branch into main:")
    for path in bad:
        print(f"  {path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
