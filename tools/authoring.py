from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


REQUIRED = (
    "tools/authoring.py",
    "tools/authoring_pipeline.py",
    "skills/spec-authoring/authoring_sequence.json",
)


def _git(repo_root: Path, *args: str, check: bool = True) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip() or proc.stdout.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _repo_root() -> Path:
    out = _git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(out.decode().strip()).resolve()


def _has_path(repo_root: Path, ref: str, path: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{ref}:{path}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def _authoring_ref(repo_root: Path) -> str:
    for ref in ("origin/main", "main"):
        if all(_has_path(repo_root, ref, path) for path in REQUIRED):
            return ref
    raise RuntimeError(
        "current branch does not contain the central authoring pipeline and no updated "
        "origin/main or main ref is available; run 'git fetch origin main' and retry"
    )


def main() -> int:
    repo_root = _repo_root()
    ref = _authoring_ref(repo_root)
    archive = _git(
        repo_root,
        "archive",
        "--format=tar",
        ref,
        "tools",
        "skills/spec-authoring/authoring_sequence.json",
    )
    with tempfile.TemporaryDirectory(prefix="spec-workbench-authoring-") as tmp:
        tmp_dir = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            bundle.extractall(tmp_dir)
        proc = subprocess.run(
            [sys.executable, str(tmp_dir / "tools" / "authoring.py"), *sys.argv[1:]],
            cwd=repo_root,
        )
        return proc.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"authoring bridge: {exc}", file=sys.stderr)
        raise SystemExit(2)
