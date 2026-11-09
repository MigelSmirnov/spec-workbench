"""Closure units: every state with a question round closes unit by unit.

A state of rules is large — Cabinet Kernel State 2 holds 21 decisions, and a
review of all of them raises about fifty topics a round. Closing it as one
text asks for two clear rounds in a row over all of them, and each round
draws two new blocking topics about some decision nobody changed: rounds
80–82 of 2026-10-06 never repeated a blocking topic. A one-line edit to one
decision reopened every decision.

The other states closed as one text until 2026-10-10, and the same arithmetic
held there: any edit reopened the whole state, Cabinet Kernel State 5 ran 107
rounds, and late edits (decision 26 rewrote States 3–5) simply went around the
rounds — nobody re-ran them, and nothing noticed. So every state is cut into
units, each closed on its own:

- one unit per accepted decision (`## Accepted decision Axx`), its heading to
  the next level-2 heading;
- one unit per other level-2 section of the state's documents, and one for a
  document's text before its first section;
- `context`: the documents of the earlier states. They close in their own
  states; this unit asks only whether they and this state agree.

State 7 is cut differently (`module_units`): one unit per module the Factory
generates, whose text is the very prompt the Factory builds for that module's
generator. That is what the generator reads — not the notes of every module,
but its own cut of notes, imports, contracts and models — and where a late
note contradicting an IMPORTS list (Cabinet Kernel decision 25) shows up.

A round reviews the units that need one: never reviewed, or changed since
their latest review. The reviewers read the layer's prompt, each point names
its unit, and a point about another unit is set aside.

A unit is closed by ONE round (owner decision 2026-11-08, #147, comment
6721261089): the latest round that reviewed it, on its current text, raised
no open contradiction against it, and every other topic of that round that
concerns it — a consequential gap, a hypothesis, a judgement whose evidence
failed — has an author disposition (``dispositions.json`` beside the round's
summary): ``fixed`` with a reference to the change, ``carried`` to a named
later layer with what it must decide, or ``accepted`` with the author's reason.
A contradiction takes no disposition: it blocks until a round on the changed
text no longer raises it. "Two clear rounds on the same text" is gone; it is
what made ping-pong (client-portal State 2, rounds 82-90 on A28 and A32).

A topic that names no unit under review (its points name none, ``?``) is
closed as itself, under the key ``NO_UNIT``, and keeps no unit open: every
round reviews the layer as a whole, so the state's latest round is its
latest review. It needs its own disposition (fixed, carried, accepted), and
a contradiction among such topics blocks the state until a round on a
changed text no longer raises it. Until 2026-11-09 such a topic held every
unit of its round open: on client-portal State 1 the unit-less
contradictions of round 49 kept ten unchanged decisions open after round 50
reviewed the three that changed, and no round could ever reach them.

Rounds kept before this rule (no ``closure`` in their summary) keep the
closure they gave: a unit closed by its two latest clear reviews on its
current text stays closed and is never reopened by the new rule.

A unit that was reviewed and then edited is reviewed for the edit only: the
reviewers get its diff since the text of its latest review (found in the
case's git history) and are asked about the change and what it affects; a
point quoting an unchanged passage of that unit, away from the change, is set
aside. On 2026-10-07 a one-sentence edit reopened Cabinet Kernel A18, and
three reviewers given the whole decision raised new storage-hardening topics
every round, none about the edit.
"""
from __future__ import annotations

import difflib
import hashlib
import re
from typing import Any

DECISION_HEADING = re.compile(r"^##\s+Accepted decision\s+(A\d+)\b")
DECISION_KEY = re.compile(r"A\d+")
SECTION_HEADING = re.compile(r"^##\s+(.*\S)\s*$")
CONTEXT = "context"
UNKNOWN = "?"
# the closure key of the topics of a round that name no unit under review
NO_UNIT = "(no unit)"

# Summaries kept from 2026-11-08 close by one round with dispositions; a
# summary without it was kept under the two-clear-rounds rule.
CLOSURE_RULE = "single_round"
# The judged kinds that leave nothing to the author: the texts answer the
# topic, a later state owns it, a precedent on unchanged passages settled it,
# no one acts on it, or the change did not touch it.
SETTLED_KINDS = frozenset({"answered", "answered_later", "judged_before", "later_state", "indifferent",
                           "preexisting", "generator_text"})
CONTRADICTION = "contradiction"
# A verified violation of the state's SPEC_STANDARD sections asks what a
# contradiction asks: a change of the text and one round on it (judge.py).
CHANGE_KINDS = frozenset({CONTRADICTION, "standard_violation"})
DISPOSITION = "disposition"
# why a unit needs a round
NEVER_REVIEWED = "never reviewed"
CHANGED = "changed since its latest review"
EVIDENCE_CHANGED = "the evidence its bindings rest on changed"
UNVERIFIED = "a contradiction whose quotes were not verified"


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
    result, seen = [], {}
    for k, t, body in found:
        seen[k] = seen.get(k, 0) + 1
        result.append((k if seen[k] == 1 else f"{k} #{seen[k]}", t, "".join(body)))
    return result


def units(texts: list[tuple[int, str, str]], state: int) -> dict[str, dict[str, str]]:
    """The units of `state` as {key: {title, digest, document, text}}: the
    sections of its documents, and `context` when an earlier state exists."""
    found: dict[str, dict[str, str]] = {}
    for doc_state, name, body in texts:
        if doc_state != state:
            continue
        for key, title, block in split(name, body):
            found[key] = {"title": title, "digest": _digest(block), "document": name, "text": block}
    earlier = [(name, body) for doc_state, name, body in texts if doc_state < state]
    if earlier:
        context = "".join(f"=== {name} ===\n{body}" for name, body in earlier)
        found[CONTEXT] = {"title": "agreement of the earlier states' texts with this state",
                          "digest": _digest(context), "document": "", "text": context}
    return found


def module_units(prompts: dict[str, str]) -> dict[str, dict[str, str]]:
    """The units of State 7: one per generated module, its text the prompt the
    Factory builds for that module's generator."""
    return {module: {"title": f"the Factory's prompt for generating `{module}`", "digest": _digest(prompt),
                     "document": module, "text": prompt}
            for module, prompt in prompts.items()}


def closed_digest(summaries: list[dict[str, Any]], key: str) -> str | None:
    """The digest of the text the unit was last reviewed on, or None: the base
    of the diff a changed unit is reviewed for. One round per change: a unit
    edited after its latest review is reviewed for that edit, whether or not
    that review closed it."""
    reviewed = [s for s in summaries if key in (s.get("scope") or []) and key in (s.get("units") or {})]
    return reviewed[-1]["units"][key] if reviewed else None


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


def referencing(current: dict[str, dict[str, str]], changed: list[str], scope: list[str]) -> dict[str, list[str]]:
    """Closed units that name a decision changed since its own closure: {unit:
    [changed decisions it names]}. Only decision keys (`A15`) are names a text
    uses; a unit already under review and `context` are not listed. On
    Registry State 2 (2026-10-31) A15 rule 6 was reversed while A14, closed
    since round 3, kept a rule 5 that contradicted it; A14 came back into a
    round only because its rule 3 happened to be edited too."""
    decisions = [key for key in changed if DECISION_KEY.fullmatch(key)]
    found: dict[str, list[str]] = {}
    for key, unit in current.items():
        if key in scope or key == CONTEXT:
            continue
        named = [d for d in decisions if re.search(rf"(?<![\w-]){re.escape(d)}(?![\w-])", unit["text"])]
        if named:
            found[key] = named
    return found


def _clear_for(summary: dict[str, Any], key: str) -> bool:
    return key not in set(summary.get("blocked_units") or [])


def topic_units(topic: dict[str, Any], scope: list[str]) -> list[str]:
    """The units under review a topic names; [] when it names none: such a
    topic closes as itself (``NO_UNIT``), not through the units."""
    return [u for u in topic.get("units") or [] if u in scope]


def _topic_concerns(topic: dict[str, Any], summary: dict[str, Any], key: str) -> bool:
    """Whether a topic of `summary` keeps the unit `key` open. In a round kept
    before the single-round rule a topic naming no unit concerned every unit
    under review, and those rounds keep the closure they gave."""
    scope = list(summary.get("scope") or [])
    named = topic_units(topic, scope)
    if not named and summary.get("closure") != CLOSURE_RULE:
        return key in scope
    return key in named


def topic_need(topic: dict[str, Any], summary: dict[str, Any]) -> str | None:
    """What a topic of a round asks of the author: CONTRADICTION (a change of
    the text and a round on it; a contradiction or a standard violation), DISPOSITION (fixed, carried or accepted), or
    None. A topic no judge saw — raised by one review without a witness — asks
    nothing; in a round kept before the judge, a topic two reviews raised
    needs a disposition."""
    if "judge" not in summary:
        return DISPOSITION if len(topic.get("runs") or []) >= 2 else None
    judgement = topic.get("judgement")
    if not isinstance(judgement, dict):
        return None
    kind = judgement.get("kind")
    if kind in CHANGE_KINDS:
        # verified or not: an unverified contradiction or standard violation is not downgraded
        return CONTRADICTION
    if not judgement.get("verified"):
        return DISPOSITION if judgement.get("blocking", True) else None
    if kind in SETTLED_KINDS:
        return None
    return DISPOSITION  # consequential_gap (quoted, deferred or recorded), hypothesis


def disposed(summary: dict[str, Any], topic_id: str, unit: str) -> dict[str, Any] | None:
    """The author's disposition of a topic for a unit: one naming that unit,
    or one naming no unit (it covers every unit of the topic, and is the
    disposition of a topic that names none)."""
    found = None
    for entry in summary.get("dispositions") or []:
        if entry.get("topic") != topic_id:
            continue
        if entry.get("unit") == unit:
            return entry
        if not entry.get("unit"):
            found = entry
    return found


def _legacy_closed(reviewed: list[dict[str, Any]], key: str, digest: str,
                   evidence: dict[str, str] | None) -> bool:
    """The two-clear-rounds closure of rounds kept before the single-round rule."""
    last = reviewed[-2:]
    return (len(last) == 2 and all(s.get("closure") != CLOSURE_RULE for s in last)
            and all(_clear_for(s, key) for s in last)
            and all(s["units"][key] == digest for s in last)
            and (evidence is None or not any(evidence_changed(s, key, evidence) for s in last)))


def unit_state(summaries: list[dict[str, Any]], key: str, digest: str,
               evidence: dict[str, str] | None = None) -> dict[str, Any]:
    """Whether one unit is closed on its text `digest`, and what keeps it open.

    - ``needs_round``: why a round must review it (never reviewed, changed
      since its latest review, its evidence changed, or an unverified
      contradiction), or None;
    - ``contradictions``: topic ids of its latest round that raise one against
      it — closed only by a changed text and a round on it;
    - ``awaiting``: topic ids of that round that need an author disposition;
    - ``carried``: what that round's dispositions carry to later layers.
    """
    reviewed = [s for s in summaries if key in (s.get("scope") or []) and key in (s.get("units") or {})]
    state: dict[str, Any] = {"closed": False, "rule": None, "round": None, "needs_round": None,
                             "contradictions": [], "unverified": [], "awaiting": [], "carried": []}
    if not reviewed:
        state["needs_round"] = NEVER_REVIEWED
        return state
    last = reviewed[-1]
    state["round"] = last.get("round")
    if _legacy_closed(reviewed, key, digest, evidence):
        state.update(closed=True, rule="two_clear_rounds")
        return state
    if last["units"][key] != digest:
        state["needs_round"] = CHANGED
        return state
    if evidence is not None and evidence_changed(last, key, evidence):
        state["needs_round"] = EVIDENCE_CHANGED
        return state
    _close_on_topics(state, last, key, lambda topic: _topic_concerns(topic, last, key))
    return state


def _close_on_topics(state: dict[str, Any], summary: dict[str, Any], key: str, concerns) -> None:
    """Fill `state` from the topics of `summary` that `concerns` selects: the
    contradictions it holds, the topics awaiting a disposition for `key`, and
    what the dispositions carried; closed when nothing of it is left."""
    for index, topic in enumerate(summary.get("topics") or [], 1):
        need = topic_need(topic, summary)
        if need is None or not concerns(topic):
            continue
        topic_id = str(topic.get("id") or f"#{index}")
        if need == CONTRADICTION:
            verified = (topic.get("judgement") or {}).get("verified", True)
            state["contradictions" if verified else "unverified"].append(topic_id)
            continue
        entry = disposed(summary, topic_id, key)
        if entry is None:
            state["awaiting"].append(topic_id)
        elif entry.get("disposition") == "carried":
            state["carried"].append({"topic": topic_id, "to": entry.get("to"), "what": entry.get("what")})
    if state["unverified"]:
        state["needs_round"] = UNVERIFIED
    state["closed"] = not (state["contradictions"] or state["unverified"] or state["awaiting"])
    state["rule"] = CLOSURE_RULE if state["closed"] else None


def no_unit_state(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """The closure of the topics that name no unit under review (``NO_UNIT``),
    in the shape of ``unit_state``. Every round reviews the layer as a whole,
    so they are judged on the state's latest round only, if it was kept under
    the single-round rule: a contradiction among them blocks until a round on
    a changed text no longer raises it, any other needs its own disposition.
    They keep no unit open."""
    state: dict[str, Any] = {"closed": True, "rule": None, "round": None, "needs_round": None,
                             "contradictions": [], "unverified": [], "awaiting": [], "carried": []}
    last = summaries[-1] if summaries else None
    if last is None or last.get("closure") != CLOSURE_RULE:
        return state
    state["round"] = last.get("round")
    scope = list(last.get("scope") or [])
    _close_on_topics(state, last, NO_UNIT, lambda topic: not topic_units(topic, scope))
    return state


def states(summaries: list[dict[str, Any]], current: dict[str, dict[str, str]],
           evidence: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    """``unit_state`` of every unit, and ``NO_UNIT`` when the topics naming no
    unit leave something open or carried."""
    found = {key: unit_state(summaries, key, unit["digest"], evidence) for key, unit in current.items()}
    layer = no_unit_state(summaries)
    if not layer["closed"] or layer["carried"]:
        found[NO_UNIT] = layer
    return found


def closed(summaries: list[dict[str, Any]], current: dict[str, dict[str, str]],
           evidence: dict[str, str] | None = None) -> dict[str, bool]:
    """Per unit: closed on its current text (``unit_state``).

    `evidence` maps a unit to the digest of what its bindings rest on (the
    checks its decision's witness tags name). A review that recorded another
    evidence digest for the unit (`unit_evidence`) judged other evidence, so it
    does not close the unit: a changed check reopens exactly the decisions bound
    to it. A review that recorded none (kept before evidence was recorded) is
    taken as it stands. Without `evidence` the closure is on the text alone."""
    return {key: value["closed"] for key, value in states(summaries, current, evidence).items()}


def evidence_changed(summary: dict[str, Any], key: str, evidence: dict[str, str]) -> bool:
    recorded = (summary.get("unit_evidence") or {}).get(key)
    return recorded is not None and recorded != evidence.get(key)


def blocked(topics: list[dict[str, Any]], scope: list[str]) -> list[str]:
    """Units a round's blocking topics keep open, and ``NO_UNIT`` when a
    blocking topic names no unit under review: it blocks as itself."""
    hit: set[str] = set()
    for topic in topics:
        if not (topic.get("judgement") or {}).get("blocking"):
            continue
        hit.update(topic_units(topic, scope) or [NO_UNIT])
    return sorted(hit)
