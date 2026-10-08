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

A unit that was closed and then edited is reviewed for the edit only: the
reviewers get its diff since the text it closed on (found in the case's git
history) and are asked about the change and what it affects; a point quoting
an unchanged passage of that unit, away from the change, is set aside. On
2026-10-07 a one-sentence edit reopened Cabinet Kernel A18, and three
reviewers given the whole decision raised new storage-hardening topics every
round, none about the edit.
"""
from __future__ import annotations

import difflib
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
            found[key] = {"title": title, "digest": _digest(block), "document": name, "text": block}
    if not any(re.fullmatch(r"A\d+", key) for key in found):
        return None
    context = "".join(f"=== {name} ===\n{body}" for doc_state, name, body in texts if doc_state < state)
    found[CONTEXT] = {"title": "agreement of the earlier states' texts with this state", "digest": _digest(context),
                      "document": "", "text": context}
    return found


def closed_digest(summaries: list[dict[str, Any]], key: str) -> str | None:
    """The digest the unit was last closed on: the latest two consecutive
    reviews of it that were clear for it on the same text."""
    reviewed = [s for s in summaries if key in (s.get("scope") or []) and key in (s.get("units") or {})]
    for first, second in reversed(list(zip(reviewed, reviewed[1:]))):
        if (_clear_for(first, key) and _clear_for(second, key)
                and first["units"][key] == second["units"][key]):
            return second["units"][key]
    return None


def change_regions(old: str, new: str, context: int = 3) -> tuple[str, list[str]]:
    """The unified diff of a unit since it was closed, and the text of the
    regions of the current unit the change touches (changed lines with
    `context` lines around them)."""
    old_lines, new_lines = old.splitlines(keepends=True), new.splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(old_lines, new_lines, "closed", "now", n=context))
    regions = []
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    for tag, _, _, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            lo, hi = max(0, j1 - context), min(len(new_lines), max(j2, j1 + 1) + context)
            regions.append("".join(new_lines[lo:hi]))
    return diff, regions


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
