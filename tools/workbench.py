from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


NAV_FILES = ("tools/workbench.py", "tools/project_navigation.py", "PROJECT_INDEX.json")


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _repo_root() -> Path:
    out = _git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(out.strip()).resolve()


def _has_path(repo_root: Path, ref: str, path: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{ref}:{path}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def _navigation_ref(repo_root: Path) -> str:
    for ref in ("origin/main", "main"):
        if all(_has_path(repo_root, ref, path) for path in NAV_FILES):
            return ref
    raise RuntimeError(
        "current branch does not contain the central project navigator and no updated "
        "origin/main or main ref is available; run 'git fetch origin main' and retry"
    )


def main() -> int:
    repo_root = _repo_root()
    ref = _navigation_ref(repo_root)
    with tempfile.TemporaryDirectory(prefix="spec-workbench-nav-") as tmp:
        tmp_dir = Path(tmp)
        for source in ("tools/workbench.py", "tools/project_navigation.py"):
            target = tmp_dir / Path(source).name
            target.write_text(_git(repo_root, "show", f"{ref}:{source}"), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(tmp_dir / "workbench.py"), *sys.argv[1:]],
            cwd=repo_root,
        )
        return proc.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"workbench bridge: {exc}", file=sys.stderr)
        raise SystemExit(2)
