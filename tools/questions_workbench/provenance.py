"""Where a quoted passage of an earlier state came from: its commit and date.

A judgement that quotes a State 0 or State 1 passage is easier to weigh when
the reader sees when that passage was written. On Registry (2026-10-31) the
State 0 row "erasing an erased customer returns it unchanged" was written on
2026-10-26, a day before the owner introduced revisions (R0-35): the two
promises never met, which made the State 2 question the owner's
(spec-workbench experiments/registry-state2-authoring). Nothing in the texts
says so; only the history does.

For each quote found in an earlier state's document, the longest line of that
document that the quote covers (or the line that holds a short quote) is
looked up with `git log -S` — the first commit that added it. A quote that no
earlier document holds, a document outside git, or a line too short to be
distinctive gets no entry.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

MIN_NEEDLE = 20
QUOTE_SHOWN = 120


def _norm(text: str) -> str:
    return " ".join(str(text).replace("`", "").split())


class QuoteProvenance:
    def __init__(self, case: Path, earlier: list[tuple[int, str, str]]):
        """`earlier`: (state, document name, text) of the states before the asked one."""
        self.case = case
        self.earlier = earlier
        self._cache: dict[tuple[str, str], tuple[str, str] | None] = {}

    def _introduced(self, name: str, needle: str) -> tuple[str, str] | None:
        key = (name, needle)
        if key not in self._cache:
            done = subprocess.run(
                ["git", "-C", str(self.case), "log", "--reverse", "--format=%H %as", "-S", needle, "--", name],
                capture_output=True, text=True)
            first = done.stdout.split("\n", 1)[0].split() if done.returncode == 0 else []
            self._cache[key] = (first[0], first[1]) if len(first) == 2 else None
        return self._cache[key]

    @staticmethod
    def _needle(quote: str, body: str) -> str | None:
        """The longest line of `body` the quote covers, or the line holding it."""
        q = _norm(quote)
        best = None
        for line in body.splitlines():
            stripped = line.strip()
            n = _norm(stripped)
            if len(n) < MIN_NEEDLE:
                continue
            if n in q or q in n:
                if best is None or len(stripped) > len(best):
                    best = stripped
        return best

    def of_quote(self, quote: str) -> dict[str, Any] | None:
        q = _norm(quote)
        if len(q) < 12:
            return None
        for state, name, body in self.earlier:
            if q not in _norm(body):
                continue
            needle = self._needle(quote, body)
            found = self._introduced(name, needle) if needle else None
            entry: dict[str, Any] = {"quote": q[:QUOTE_SHOWN], "state": state, "document": name}
            if found:
                entry["commit"], entry["date"] = found
            return entry
        return None

    def of_judgement(self, judgement: dict[str, Any]) -> list[dict[str, Any]]:
        """Provenance of every earlier-state passage a judgement quotes: its
        quotes, its witness's basis and its contradiction bases."""
        quotes = list(judgement.get("quotes") or [])
        quotes += list((judgement.get("witness") or {}).get("basis") or [])
        quotes += [b.get("rests_on") for b in judgement.get("bases") or [] if b.get("rests_on")]
        seen, found = set(), []
        for quote in quotes:
            if not isinstance(quote, str) or _norm(quote) in seen:
                continue
            seen.add(_norm(quote))
            entry = self.of_quote(quote)
            if entry:
                found.append(entry)
        return found
