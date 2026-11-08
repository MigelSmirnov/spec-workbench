"""What the judge of a document round reads inline when it can search files.

Owner decision 2026-11-08 (#147). The judge decides a few repeated topics, each
carrying the reviewers' verbatim quotes, yet it was given the whole round text:
on client-portal State 2 the same ~210k-character layer prompt the reviewers
got. The later states' documents were already files it searches (``later/``);
the round text now goes the same way. Inline it gets only:

- the topics, with the reviewers' questions, points and quotes (prompts.judge_input);
- the units of State N the topics concern (``topic["units"]``; a topic naming
  no unit concerns every unit under review), each with its diff when the round
  has the texts the state was closed with;
- the units of State N and of the earlier states that hold a passage the topics
  quote, and the earlier-state units whose definitions the topics or their
  units name (layer_prompt.resolves: an A-number, an INV-* or R-* id, a model,
  function or module name), one step: the judge searches the files for more;
- the precedents and the layer block, as before.

Everything else is a file in the judge's working directory: the full texts of
States 0..N under ``states/``, the later documents under ``later/``, and, for a
reopened state, the texts it was closed with under ``closed/``.

Nothing here touches the check: judge.check still receives the full texts from
the caller and finds every quote verbatim in them.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Any

from . import layer_prompt, units
from .provider import LATER_DIR

STATES_DIR = "states"
CLOSED_DIR = "closed"
MIN_QUOTE = 12  # judge._found: a shorter quote is not checkable, nor selectable


def _norm(text: str) -> str:
    return " ".join(str(text).replace("`", "").split())


@dataclass
class Context:
    """What the judge reads inline, and the files it may search."""

    own: list[tuple[str, str]] = field(default_factory=list)          # (key, text) of State N the topics concern
    quoted_own: list[tuple[str, str]] = field(default_factory=list)   # other State N units holding a quoted passage
    diffs: dict[str, str] = field(default_factory=dict)               # key -> diff since the state was closed
    received: list[tuple[int, str, str, str]] = field(default_factory=list)  # (state, document, key, text) earlier
    files: dict[str, str] = field(default_factory=dict)               # path in the working directory -> body


def topic_quotes(point: Any) -> list[str]:
    """The passages a reviewer's point quotes: its text, the other side of a
    contradiction, and its witness's basis."""
    if not isinstance(point, dict):
        return []
    found = [point.get("text"), point.get("other_text")]
    witness = point.get("witness")
    if isinstance(witness, dict):
        found += [b for b in witness.get("basis") or [] if isinstance(b, str)]
    return [q for q in found if isinstance(q, str) and len(_norm(q)) >= MIN_QUOTE]


def files(texts: list[tuple[int, str, str]], later: dict[str, str] | None,
          old: dict[str, str] | None) -> dict[str, str]:
    found = {f"{STATES_DIR}/{name}": body for _, name, body in texts}
    found.update({f"{LATER_DIR}/{name}": body for name, body in (later or {}).items()})
    if old is not None:
        found.update({f"{CLOSED_DIR}/{name}": body for name, body in old.items()})
    return found


def select(texts: list[tuple[int, str, str]], state: int, topics: list[dict[str, Any]], scope: list[str],
           old: dict[str, str] | None, later: dict[str, str] | None = None) -> Context:
    context = Context(files=files(texts, later, old))
    current = units.units(texts, state)
    keys: list[str] = []

    def take(into: list[str], found: list[str]) -> None:
        into.extend(k for k in found if k not in into)

    for topic in topics:
        named = [u for u in topic.get("units") or [] if u in current and u != units.CONTEXT]
        unknown = not topic.get("units") or any(u not in current for u in topic["units"])
        # a topic naming no unit, or one this state does not hold, concerns every unit under review
        take(keys, named + ([k for k in scope if k in current and k != units.CONTEXT] if unknown else []))
    context.own = [(k, current[k]["text"]) for k in current if k in keys]
    if old is not None:
        before = units.units([(s, name, old.get(name, "")) for s, name, _ in texts], state)
        for key, text in context.own:
            context.diffs[key] = "".join(difflib.unified_diff(
                (before.get(key) or {}).get("text", "").splitlines(True), text.splitlines(True),
                f"{key} (closed)", f"{key} (now)", n=2)) or "(unchanged since the state was closed)\n"

    earlier = layer_prompt._earlier_units(texts, state)
    definitions = {u[2]: layer_prompt.defined(u[2], u[3]) for u in earlier}
    chosen: list[str] = []
    quoted_own: list[str] = []
    quotes = [_norm(q) for t in topics for q in t.get("quoted") or []]
    for quote in quotes:
        take(chosen, [u[2] for u in earlier if quote in _norm(u[3])])
        take(quoted_own, [k for k in current if k not in keys and k != units.CONTEXT
                          and quote in _norm(current[k]["text"])])
    # what the topics and their units name that an earlier unit defines: one
    # step, not closed over (the judge searches the files for the rest)
    for key, text in context.own:
        take(chosen, layer_prompt.resolves(text, layer_prompt.defined(key, text), earlier, definitions))
    for topic in topics:
        said = "\n".join([str(topic.get("topic", "")), *map(str, topic.get("questions") or [])])
        take(chosen, layer_prompt.resolves(said, set(), earlier, definitions))
    context.quoted_own = [(k, current[k]["text"]) for k in current if k in quoted_own]
    by_key = {u[2]: u for u in earlier}
    position = {u[2]: i for i, u in enumerate(earlier)}
    context.received = sorted((by_key[k] for k in chosen), key=lambda u: position[u[2]])
    return context


def render(context: Context, state: int) -> str:
    parts = []
    head = f"=== State {state}: the units the topics concern"
    if context.diffs:
        head += ", each with its change since the state was closed"
    blocks = []
    for key, text in context.own:
        block = text.rstrip("\n")
        if key in context.diffs:
            block += f"\n\nChange of {key} since the state was closed:\n```diff\n{context.diffs[key]}```"
        blocks.append(block)
    parts.append(head + " ===\n\n" + ("\n\n".join(blocks) or "(none named)"))
    if context.quoted_own:
        parts.append(f"=== State {state}: other units holding a passage the topics quote ===\n\n"
                     + "\n".join(text for _, text in context.quoted_own))
    by_doc: dict[tuple[int, str], list[str]] = {}
    for s, name, _, body in context.received:
        by_doc.setdefault((s, name), []).append(body)
    for (s, name), bodies in by_doc.items():
        parts.append(f"=== {name} (State {s}): the passages the topics quote or name ===\n\n" + "\n".join(bodies))
    return "\n\n".join(parts)
