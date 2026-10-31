"""Check that every pinned passage exists verbatim at its commit.

    python experiments/registry-state2-investigation/check_quotes.py

Also checks the passages the packet and the witnesses cite (by key), and that
every version's commit exists. White space is normalised and Markdown code
marks dropped, as tools/questions_workbench/judge.py does; nothing else is.
Exit status 1 on any miss.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "model"))
from sources import Q, VERSIONS  # noqa: E402


def norm(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def show(sha: str, path: str) -> str | None:
    out = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True, text=True, cwd=HERE)
    return out.stdout if out.returncode == 0 else None


def cited_keys() -> set[str]:
    keys: set[str] = set()
    for path in list(HERE.glob("packet/*.md")) + list(HERE.glob("route/*.md")) + [HERE / "REPORT.md",
                                                                                  HERE / "model" / "TRACEABILITY.md"]:
        if path.exists():
            keys |= set(re.findall(r"\[q:([A-Za-z0-9_.\-]+)\]", path.read_text(encoding="utf-8")))
    wpath = HERE / "witnesses" / "witnesses.json"
    if wpath.exists():
        for w in json.loads(wpath.read_text(encoding="utf-8"))["witnesses"]:
            keys |= set(w.get("basis", []))
    return keys


def main() -> int:
    misses = []
    cache: dict[tuple[str, str], str | None] = {}
    for key, (sha, path, text) in Q.items():
        body = cache.setdefault((sha, path), show(sha, path))
        if body is None or norm(text) not in norm(body):
            misses.append(f"{key}: not found at {sha}:{path}")
    for name, v in VERSIONS.items():
        if subprocess.run(["git", "cat-file", "-e", v["sha"]], cwd=HERE).returncode:
            misses.append(f"version {name}: commit {v['sha']} missing")
    unknown = sorted(k for k in cited_keys() if k not in Q)
    misses += [f"cited key {k} is not in sources.Q" for k in unknown]
    print(f"{len(Q)} passages, {len(VERSIONS)} versions, {len(cited_keys())} cited keys")
    for m in misses:
        print("MISS", m)
    print("OK" if not misses else f"{len(misses)} miss(es)")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
