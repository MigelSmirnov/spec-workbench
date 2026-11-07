"""What a document round of States 0-5 reads: the prompt of its layer.

Owner decision 2026-11-08 (#147, comment 6714407801). State 7 reads exactly
the prompt one module's generator gets; States 0-5 read what their layer needs
to do its work, not the history of the specification:

1. the layer's task (the instruction: what it owns, its questions);
2. the layer's own text: the open units, whole, with their diff in the
   instruction; a closed unit of the layer only as a neighbour of an open one,
   through ``referencing`` (and, when ``context`` is open, the closed units
   that speak of what changed below);
3. what the layer receives from earlier layers, verbatim: the earlier-state
   units the open units name (A-numbers) or share an identifier with
   (INV-*, model, function and module names), and, when the agreement with
   the earlier states (``context``) is open, the earlier units its change
   touched. Contradiction bases are quoted from this block, so it carries the
   passages whole;
4. the deterministic results at the handoff and 5. the State 2 witness
   material, both given by the instruction (prompts.layer_scope).

Never a pass by omission: when the selection cannot decide what an open unit
depends on (it names no identifier, or the change of ``context`` cannot be
read), the round says so and reads the earlier states' texts whole.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import units

LAST_STATE = 5  # States 0-5; State 6 is measured on a case with a State 6 document first

INVARIANT_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{1,4}\b")
DECISION = re.compile(r"\bA\d+\b")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CAMEL = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+\b")
SNAKE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
DIFF_HEADER = re.compile(r"^=== .* ===$")


def identifiers(text: str) -> set[str]:
    """The names a passage shares with others: invariant ids, decision keys,
    CamelCase model names, snake_case function and module names, and the names
    in code spans. Plain words are not identifiers."""
    found = set(INVARIANT_ID.findall(text)) | set(DECISION.findall(text))
    found |= set(CAMEL.findall(text)) | set(SNAKE.findall(text))
    for span in CODE_SPAN.findall(text):
        for name in NAME.findall(span):
            if len(name) > 2 and (name[0].isupper() or "_" in name):
                found.add(name)
    return found


ITEM_ID = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+\**`?([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{1,4})\b", re.M)


def defined(key: str, text: str) -> set[str]:
    """The names a unit defines, which others refer to it by: its key, the
    identifiers of its heading (a model, a decision, an operation), and the
    ids its list items declare (``- INV-001:``, ``- R0-23:``). A field name the
    unit merely uses is not one: shared field names would tie every model to
    every other."""
    heading = next((line for line in text.splitlines() if line.startswith("#")), "")
    names = identifiers(heading)
    named = heading.split("—", 1)[1].strip().strip("`") if "—" in heading else ""
    if NAME.fullmatch(named) and named[0].isupper():  # "## Model M12 — Expense"
        names.add(named)
    return names | set(ITEM_ID.findall(text)) | ({key} if DECISION.fullmatch(key) else set())


def mentions(text: str, names: set[str]) -> bool:
    return any(re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", text) for n in names)


@dataclass
class Selection:
    """What the round reads and why."""

    own: list[tuple[str, str]] = field(default_factory=list)            # (key, text) of State N
    received: list[tuple[int, str, str, str]] = field(default_factory=list)  # (state, document, key, text)
    whole: list[str] = field(default_factory=list)                     # reasons the earlier texts are whole
    neighbours: list[str] = field(default_factory=list)


def _earlier_units(texts: list[tuple[int, str, str]], state: int) -> list[tuple[int, str, str, str]]:
    found = []
    for doc_state, name, body in texts:
        if doc_state < state:
            for key, _, block in units.split(name, body):
                found.append((doc_state, name, key, block))
    return found


def select(texts: list[tuple[int, str, str]], state: int, current: dict[str, dict[str, str]],
           scope: list[str], changed: dict[str, tuple[str, list[str]]],
           referencing: dict[str, list[str]] | None = None) -> Selection:
    selection = Selection()
    open_keys = [key for key in scope if key != units.CONTEXT and key in current]
    named: set[str] = set()
    for key in open_keys:
        if not identifiers(current[key]["text"]) - {key}:  # its own key in its heading names nothing else
            selection.whole.append(f"{key} names no identifier, so what it depends on cannot be selected")
        named |= set(DECISION.findall(current[key]["text"]))
    # a closed unit of the layer appears only as a neighbour of an open one,
    # through `referencing` (a closed unit naming a changed decision)
    neighbours = [key for key in current if key not in scope and key != units.CONTEXT
                  and key in (referencing or {})]
    selection.neighbours = neighbours
    for key in current:
        if key in open_keys or key in neighbours:
            selection.own.append((key, current[key]["text"]))
    earlier = _earlier_units(texts, state)
    if units.CONTEXT in scope:
        if units.CONTEXT not in changed:
            selection.whole.append("the agreement with the earlier states is open and its change cannot be "
                                   "read (never closed, or its closed text is not in the history)")
        else:
            lines = {line[1:].strip() for line in changed[units.CONTEXT][0].splitlines()
                     if line[:1] in "+-" and not line.startswith(("+++", "---"))
                     and line[1:].strip() and not DIFF_HEADER.match(line[1:].strip())}
            touched = [u for u in earlier if any(line in u[3] for line in lines)]
            selection.received += [u for u in touched]
            # this layer's closed units that speak of what changed below are its neighbours
            for key in current:
                if (key not in open_keys and key not in neighbours and key != units.CONTEXT
                        and identifiers(current[key]["text"]) & {i for u in touched for i in defined(u[2], u[3])}):
                    selection.own.append((key, current[key]["text"]))
                    selection.neighbours.append(key)
    if selection.whole:
        selection.received = [(s, name, f"{name}:whole", body) for s, name, body in texts if s < state]
        return selection
    taken = {u[2] for u in selection.received}
    own_text = "\n".join(current[key]["text"] for key in open_keys) + "\n" + "\n".join(
        u[3] for u in selection.received)
    own_defined = set()
    for key in open_keys:
        own_defined |= defined(key, current[key]["text"])
    for unit in earlier:
        if unit[2] in taken:
            continue
        # the open units name what it defines, or it names what they define
        if unit[2] in named or mentions(own_text, defined(unit[2], unit[3])) or identifiers(unit[3]) & own_defined:
            selection.received.append(unit)
            taken.add(unit[2])
    order = {(s, name): i for i, (s, name, _) in enumerate(texts)}
    selection.received.sort(key=lambda u: order.get((u[0], u[1]), 0))
    return selection


def render(selection: Selection, texts: list[tuple[int, str, str]], state: int) -> str:
    own_doc = {name for s, name, _ in texts if s == state}
    parts = [f"=== State {state}: {', '.join(sorted(own_doc))} — the units under review"
             + (" and their neighbours" if selection.neighbours else "") + " ===\n\n"
             + "\n".join(text for _, text in selection.own)]
    if selection.whole:
        for s, name, _, body in selection.received:
            parts.append(f"=== {name} (State {s}), whole ===\n\n{body}")
        return "\n\n".join(parts)
    by_doc: dict[tuple[int, str], list[str]] = {}
    for s, name, _, body in selection.received:
        by_doc.setdefault((s, name), []).append(body)
    for (s, name), bodies in by_doc.items():
        parts.append(f"=== {name} (State {s}): the passages this layer receives ===\n\n" + "\n".join(bodies))
    return "\n\n".join(parts)


NOTE = """

What you read. Not the whole specification: the units of State {state} under
review{neighbours}, and, of the earlier states, {received}. Quote a basis only
from what you are given; a passage you are not given is not a basis."""


def note(selection: Selection, state: int) -> str:
    if selection.whole:
        received = ("their texts whole, because " + "; ".join(selection.whole))
    elif selection.received:
        received = ("the passages the units under review depend on: those defining what they name "
                    "(a decision, a model, an operation, an INV-* or R-* id) and those naming what they define")
    else:
        received = "nothing: the units under review name nothing an earlier state holds"
    neighbours = (", with the closed units of this state that name a changed decision or speak of a change below"
                  if selection.neighbours else "")
    return NOTE.format(state=state, neighbours=neighbours, received=received)
