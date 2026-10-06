"""Closure units: a state with accepted decisions closes decision by decision.

A state of rules is large — Cabinet Kernel State 2 holds 21 decisions, and a
review of all of them raises about fifty topics a round. Closing it as one
text asks for two clear rounds in a row over all of them, and each round
draws two new blocking topics about some decision nobody changed: rounds
80–82 of 2026-10-06 never repeated a blocking topic. A one-line edit to one
decision reopened every decision.

So such a state is cut into units, each closed on its own:

- one unit per accepted decision (`## Accepted decision Axx`), its heading to
  the next level-2 heading;
- one unit per other level-2 section of the state's documents, and one for a
  document's text before its first section;
- `context`: the documents of the earlier states. They close in their own
  states; this unit asks only whether they and this state's units agree.

A round reviews the units that are not closed; the reviewers read every text,
but each point names its unit, and a point about a closed unit is set aside.
A unit is closed when the two latest rounds that reviewed it were clear for it
on the same text, and the text has not changed since. The state is closed
when every unit is.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

DECISION_HEADING = re.compile(r"^##\s+Accepted decision\s+(A\d+)\b")
SECTION_HEADING = re.compile(r"^##\s+(.*\S)\s*$")
CONTEXT = "context"
UNKNOWN = "?"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split(name: str, text: str) -> list[tuple[str, str, str]]:
    """(key, title, text) of each unit of one document, in document order."""
    found: list[tuple[str, str, list[str]]] = []
    key, title, lines = f"{name}:preamble", f"{name}, before its first section", []
    for line in text.splitlines(keepends=True):
        section = SECTION_HEADING.match(line)
        if section:
            if lines:
                found.append((key, title, lines))
            decision = DECISION_HEADING.match(line)
            key = decision.group(1) if decision else f"{name}:{section.group(1)}"
            title, lines = section.group(1), []
        lines.append(line)
    if lines:
        found.append((key, title, lines))
    return [(k, t, "".join(body)) for k, t, body in found]


def units(texts: list[tuple[int, str, str]], state: int) -> dict[str, dict[str, str]] | None:
    """The units of `state` as {key: {title, digest}}, or None when the state's
    documents hold no accepted decision (it then closes as one text)."""
    found: dict[str, dict[str, str]] = {}
    for doc_state, name, body in texts:
        if doc_state != state:
            continue
        for key, title, block in split(name, body):
            found[key] = {"title": title, "digest": _digest(block)}
    if not any(re.fullmatch(r"A\d+", key) for key in found):
        return None
    context = "".join(f"=== {name} ===\n{body}" for doc_state, name, body in texts if doc_state < state)
    found[CONTEXT] = {"title": "agreement of the earlier states' texts with this state", "digest": _digest(context)}
    return found


def _clear_for(summary: dict[str, Any], key: str) -> bool:
    return key not in set(summary.get("blocked_units") or [])


def closed(summaries: list[dict[str, Any]], current: dict[str, dict[str, str]]) -> dict[str, bool]:
    """Per unit: closed by the two latest rounds that reviewed it, on its current text."""
    result = {}
    for key, unit in current.items():
        reviewed = [s for s in summaries if key in (s.get("scope") or []) and key in (s.get("units") or {})]
        last = reviewed[-2:]
        result[key] = (len(last) == 2 and all(_clear_for(s, key) for s in last)
                       and all(s["units"][key] == unit["digest"] for s in last))
    return result


def blocked(topics: list[dict[str, Any]], scope: list[str]) -> list[str]:
    """Units a round's blocking topics keep open. A blocking topic that names no
    unit under review keeps every unit under review open."""
    hit: set[str] = set()
    for topic in topics:
        if not (topic.get("judgement") or {}).get("blocking"):
            continue
        named = [u for u in topic.get("units") or [] if u in scope]
        hit.update(named or scope)
    return sorted(hit)
