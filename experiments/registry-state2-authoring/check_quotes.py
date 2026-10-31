"""Check every pinned passage at its commit, and every [q:key] cited.

    python experiments/registry-state2-authoring/check_quotes.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "model"))
from sources import Q  # noqa: E402


def norm(t: str) -> str:
    return " ".join(t.replace("`", "").split())


def show(sha: str, path: str) -> str | None:
    if path == "-":      # a commit message
        out = subprocess.run(["git", "log", "-1", "--format=%B", sha], capture_output=True, text=True, cwd=HERE)
    else:
        out = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True, text=True, cwd=HERE)
    return out.stdout if out.returncode == 0 else None


def cited() -> set[str]:
    keys: set[str] = set()
    for p in HERE.rglob("*"):
        if p.suffix in (".md", ".json", ".patch") and "model_run" not in p.parts:
            keys |= set(re.findall(r"\[q:([A-Za-z0-9_.\-]+)\]", p.read_text(encoding="utf-8")))
    return keys


def main() -> int:
    miss = []
    for k, (sha, path, text) in Q.items():
        body = show(sha, path)
        if body is None or norm(text) not in norm(body):
            miss.append(f"{k}: not found at {sha}:{path}")
    miss += [f"cited key {k} not in sources.Q" for k in sorted(cited() - set(Q))]
    print(f"{len(Q)} passages, {len(cited())} cited keys")
    for m in miss:
        print("MISS", m)
    print("OK" if not miss else f"{len(miss)} miss(es)")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
