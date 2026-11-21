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
   touched; then, until nothing is added, what those passages name in turn
   (Entry -> Money). Contradiction bases are quoted from this block, so it
   carries the passages whole;
4. the deterministic results at the handoff and 5. the State 2 witness
   material, both given by the instruction (prompts.layer_scope).

Never a pass by omission: when the selection cannot show what an open unit
depends on (it names nothing an earlier state defines and nothing earlier
names what it defines; its own definitions do not count), or the change of
``context`` cannot be read, the round says so and reads the earlier states'
texts whole. State 0 has no earlier state: nothing is missing there.

Measured on client-portal (2026-11-08, #147 comment 6721261089), the
selection fell back to whole texts for 16 of 16 State 0 units, 33 of 42 State
1 units, 25 of 41 State 2 units, and even a unit that resolved read about the
whole of the earlier texts (State 2 median 127k of 127k), because:

- an earlier passage was a whole level-2 section: State 0's "Decisions" holds
  every R0-nn as a level-3 section, so citing R0-23 brought all of them, and
  R0-23 was never a defined name (only list items and the level-2 heading
  were read). A level-2 section whose level-3 headings define names is now
  cut into those level-3 passages, each verbatim, each defining what its
  heading names (``### R0-23 — …``, ``### StaffAccount``);
- model numbers (``M32``) were not identifiers, and a section cited by its
  quoted title (State 0 ("Operator management")) resolved nothing;
- a qualified heading (`public_op:derived_views.build_budget_view`) defined
  its module and `public_op` too, so every unit naming the module was taken
  as naming the operation, and the closure (kept until nothing is added,
  owner review r4504187842) carried that through most of the earlier states.
  Such a heading now defines its last name only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import units

LAST_STATE = 5  # States 0-5; State 6 is measured on a case with a State 6 document first

INVARIANT_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{1,4}\b")
DECISION = re.compile(r"\bA\d+\b")
MODEL_KEY = re.compile(r"\bM\d+\b")
QUOTED = re.compile(r"[\"“«]([^\"”»\n]{3,80})[\"”»]")
SUBSECTION = re.compile(r"^###\s+(.*\S)\s*$")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CAMEL = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+\b")
SNAKE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
DIFF_HEADER = re.compile(r"^=== .* ===$")


def identifiers(text: str) -> set[str]:
    """The names a passage shares with others: invariant ids, decision keys,
    CamelCase model names, snake_case function and module names, and the names
    in code spans. Plain words are not identifiers."""
    found = set(INVARIANT_ID.findall(text)) | set(DECISION.findall(text)) | set(MODEL_KEY.findall(text))
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
    # a qualified heading (`public_op:derived_views.build_budget_view`) defines
    # its last name; the qualifiers are names it uses, not defines: taken as
    # definitions they tied every operation of a module to every unit naming it
    for span in CODE_SPAN.findall(heading):
        segments = [n for n in re.split(r"[.:]", span) if n]
        if len(segments) > 1:
            names -= set(segments[:-1])
            names.add(segments[-1])
    # a heading that is one code span defines that name, however short (`api`)
    whole = re.fullmatch(r"#+\s+`([A-Za-z_][A-Za-z0-9_]*)`\s*", heading.strip())
    if whole:
        names.add(whole.group(1))
    named = heading.split("—", 1)[1].strip().strip("`") if "—" in heading else ""
    if NAME.fullmatch(named) and named[0].isupper():  # "## Model M12 — Expense"
        names.add(named)
    names |= set(ITEM_ID.findall(text)) | ({key} if DECISION.fullmatch(key) else set())
    # a model is also named by the field that refers to it (ServicePrincipal ->
    # service_principal_id), the only way a model text names another one
    return names | {_snake(n) + "_id" for n in names if CAMEL.fullmatch(n)}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def mentions(text: str, names: set[str]) -> bool:
    return any(re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", text) for n in names)


@dataclass
class Selection:
    """What the round reads and why."""

    own: list[tuple[str, str]] = field(default_factory=list)            # (key, text) of State N
    received: list[tuple[int, str, str, str]] = field(default_factory=list)  # (state, document, key, text)
    whole: list[str] = field(default_factory=list)                     # reasons the earlier texts are whole
    neighbours: list[str] = field(default_factory=list)
    # the passages an open unit names or that name what it defines, before the
    # closure and whether or not the round falls back to the whole texts
    direct: list[tuple[int, str, str, str]] = field(default_factory=list)
    depth: dict[str, int] = field(default_factory=dict)                 # received key -> closure steps from an open unit (0: direct)
    named_by: dict[str, str] = field(default_factory=dict)              # received key -> the chosen passage that named it


def _pieces(key: str, block: str) -> list[tuple[str, str]]:
    """A level-2 unit as the passages a later layer receives: whole, or, when
    its level-3 headings define names (``### R0-23 — …``), its text before the
    first of them and each level-3 section, verbatim. Concatenated they are
    the unit's text."""
    parts: list[tuple[str, list[str]]] = [(key, [])]
    for line in block.splitlines(keepends=True):
        sub = SUBSECTION.match(line)
        if sub:
            parts.append((f"{key} / {sub.group(1)}", []))
        parts[-1][1].append(line)
    if len(parts) == 1 or not any(identifiers(lines[0]) for _, lines in parts[1:]):
        return [(key, block)]
    seen: dict[str, int] = {}
    found = []
    for name, lines in parts:
        seen[name] = seen.get(name, 0) + 1
        found.append((name if seen[name] == 1 else f"{name} #{seen[name]}", "".join(lines)))
    return [piece for piece in found if piece[1].strip()]


def _earlier_units(texts: list[tuple[int, str, str]], state: int) -> list[tuple[int, str, str, str]]:
    """The passages of the earlier states a layer can receive: their level-2
    units, cut into level-3 sections where those define names (``_pieces``)."""
    found = []
    for doc_state, name, body in texts:
        if doc_state < state:
            for key, _, block in units.split(name, body):
                for piece_key, piece in _pieces(key, block):
                    found.append((doc_state, name, piece_key, piece))
    return found


def _title(text: str) -> str:
    """The title of a passage's own heading. Headings inside a passage do not
    count: quoted words match them too often, and a whole section would come
    with each (client-portal States 3-5: median input 111k -> 134k)."""
    heading = next((line for line in text.splitlines() if line.startswith("#")), "")
    return heading.lstrip("#").strip().lower()


OPERATION_HEADING = re.compile(r"^#+\s+`?(?:public_op|op|operation):", re.M)


def _closes(unit: tuple[int, str, str, str]) -> bool:
    """Whether the selection's closure runs through this passage: a model
    (``## Model M12 — Expense``), a decision (``## Accepted decision A7``,
    ``### R0-23 — …``, or a passage whose items declare ids such as INV-*),
    or an operation (``## `public_op:…` ``)."""
    state, _, key, text = unit
    heading = next((line for line in text.splitlines() if line.startswith("#")), "")
    return bool(DECISION.fullmatch(key) or DECISION.search(heading) or (state == 1 and re.match(r"^##\s+Model\b", heading))
                or INVARIANT_ID.search(heading) or ITEM_ID.search(text) or OPERATION_HEADING.match(heading))


def resolves(text: str, exclude: set[str], earlier: list[tuple[int, str, str, str]],
             definitions: dict[str, set[str]]) -> list[str]:
    """Keys of the earlier units whose definitions ``text`` names, its own
    definitions aside, and of those it cites by their quoted title
    (State 0 ("Operator management"))."""
    quoted = {q.strip().lower() for q in QUOTED.findall(text)}
    return [unit[2] for unit in earlier
            if mentions(text, definitions[unit[2]] - exclude) or (quoted and _title(unit[3]) in quoted)]


def select(texts: list[tuple[int, str, str]], state: int, current: dict[str, dict[str, str]],
           scope: list[str], changed: dict[str, tuple[str, list[str]]],
           referencing: dict[str, list[str]] | None = None) -> Selection:
    selection = Selection()
    open_keys = [key for key in scope if key != units.CONTEXT and key in current]
    # a closed unit of the layer appears only as a neighbour of an open one,
    # through `referencing` (a closed unit naming a changed decision)
    neighbours = [key for key in current if key not in scope and key != units.CONTEXT
                  and key in (referencing or {})]
    selection.neighbours = neighbours
    for key in current:
        if key in open_keys or key in neighbours:
            selection.own.append((key, current[key]["text"]))
    earlier = _earlier_units(texts, state)
    by_key = {unit[2]: unit for unit in earlier}
    definitions = {unit[2]: defined(unit[2], unit[3]) for unit in earlier}
    chosen: list[str] = []

    def take(keys: list[str]) -> None:
        chosen.extend(k for k in keys if k not in chosen)

    # 1. each open unit's own links: what it names that an earlier unit defines,
    #    and the earlier units naming what it defines. None found: the input
    #    cannot be shown to suffice, so the earlier texts are read whole.
    for key in open_keys:
        text = current[key]["text"]
        own = defined(key, text)
        links = resolves(text, own, earlier, definitions)
        links += [unit[2] for unit in earlier if own and unit[2] not in links and mentions(unit[3], own)]
        if not links and earlier:  # State 0 has no earlier state to depend on
            selection.whole.append(f"{key} names nothing an earlier state defines and nothing earlier names "
                                   "what it defines, so what it depends on cannot be selected")
        take(links)
    if units.CONTEXT in scope:
        if units.CONTEXT not in changed:
            selection.whole.append("the agreement with the earlier states is open and its change cannot be "
                                   "read (never closed, or its closed text is not in the history)")
        else:
            lines = {line[1:].strip() for line in changed[units.CONTEXT][0].splitlines()
                     if line[:1] in "+-" and not line.startswith(("+++", "---"))
                     and line[1:].strip() and not DIFF_HEADER.match(line[1:].strip())}
            touched = [u[2] for u in earlier if any(line in u[3] for line in lines)]
            take(touched)
            # this layer's closed units that speak of what changed below are its neighbours
            moved = {name for k in touched for name in definitions[k]}
            for key in current:
                if (key not in open_keys and key not in selection.neighbours and key != units.CONTEXT
                        and mentions(current[key]["text"], moved)):
                    selection.own.append((key, current[key]["text"]))
                    selection.neighbours.append(key)
    order = {(s, name): i for i, (s, name, _) in enumerate(texts)}
    position = {unit[2]: i for i, unit in enumerate(earlier)}

    def in_order(keys: list[str]) -> list[tuple[int, str, str, str]]:
        return sorted((by_key[k] for k in keys), key=lambda u: (order.get((u[0], u[1]), 0), position[u[2]]))

    selection.direct = in_order(chosen)
    selection.depth = {key: 0 for key in chosen}
    if selection.whole:
        selection.received = [(s, name, f"{name}:whole", body) for s, name, body in texts if s < state]
        return selection
    # 2. close the selection: a chosen passage brings what it names in turn
    #    (Entry -> Money, A12 -> A7), until nothing is added, by the
    #    definitions of models, decisions and operations (owner review
    #    r4504187842 of #157). A module of State 3 or a plain section is taken
    #    when an open unit names it, but the closure does not run through it:
    #    a module names every decision it owns and each decision the modules
    #    it touches, and through them the closure reached most of the earlier
    #    states for every State 5 operation (client-portal, 2026-11-08).
    closing = {k: names for k, names in definitions.items() if _closes(by_key[k])}
    closing_units = [u for u in earlier if u[2] in closing]
    frontier = list(chosen)
    while frontier:  # breadth first, so a passage's depth is its fewest steps from an open unit
        key = frontier.pop(0)
        found = [k for k in resolves(by_key[key][3], definitions[key], closing_units, closing) if k not in chosen]
        take(found)
        frontier += found
        for k in found:
            selection.depth[k], selection.named_by[k] = selection.depth[key] + 1, key
    selection.received = in_order(chosen)
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

What you read: the units of State {state} under review{neighbours}, and, of the
earlier states, {received}. Quote a basis only from what you are given."""


def note(selection: Selection, state: int) -> str:
    if selection.whole:
        received = ("their texts whole, because " + "; ".join(selection.whole))
    elif selection.received:
        received = "the passages they depend on: those defining what they name and those naming what they define"
    else:
        received = "nothing: the units under review name nothing an earlier state holds"
    neighbours = ", with closed neighbours that name or speak of a change" if selection.neighbours else ""
    return NOTE.format(state=state, neighbours=neighbours, received=received)


# ---------------------------------------------------------------- the route
#
# A reading measured against the selection by a probe (service.probe_round),
# never by a round of a case. On client-portal and registry (57 rounds of
# States 3-5 kept under the single-round rule, texts rebuilt as each round read
# them, 2026-11-13) the closure was most of what a review read - a median of
# 170-204k characters against 47-92k of direct links - while of 258 verified
# topics 225 stood on the state's own text or a direct link, 13 on a passage
# one closure step away, none on a passage further, and 20 on a passage the
# selection never gave (a section no identifier names: "Facts several modules
# touch, and their one owner", "Actors and trust boundaries"), which the judge
# found by searching files. The route gives a review what the judge has:
# inline the units under review and their direct links, the earlier states
# whole as files, and an index of every earlier passage not inline - what it
# defines and which given passage names it. Nothing is cut, and nothing falls
# back to the whole texts: a unit whose links cannot be selected is searched for.

SELECTION, ROUTE = "selection", "route"
READINGS = (SELECTION, ROUTE)
ROUTE_NAMES = 6


def render_route(selection: Selection, texts: list[tuple[int, str, str]], state: int, files_dir: str) -> str:
    """The round text of the route: the units under review, their direct links
    verbatim, and the index of the other earlier passages, found in the files
    under `files_dir`."""
    own_doc = {name for s, name, _ in texts if s == state}
    parts = [f"=== State {state}: {', '.join(sorted(own_doc))} — the units under review"
             + (" and their neighbours" if selection.neighbours else "") + " ===\n\n"
             + "\n".join(text for _, text in selection.own)]
    by_doc: dict[tuple[int, str], list[str]] = {}
    for s, name, _, body in selection.direct:
        by_doc.setdefault((s, name), []).append(body)
    for (s, name), bodies in by_doc.items():
        parts.append(f"=== {name} (State {s}): the passages the units under review name, or that name what they "
                     "define ===\n\n" + "\n".join(bodies))
    inline = {unit[2] for unit in selection.direct}
    lines = []
    for s, name, key, body in _earlier_units(texts, state):
        if key in inline or not body.strip():
            continue
        title = key.split(":", 1)[1] if key.startswith(f"{name}:") else key
        names = sorted(defined(key, body) - {key})[:ROUTE_NAMES]
        line = f"- {files_dir}/{name} · {title} ({len(body):,} characters)"
        if names:
            line += f" — defines {', '.join(names)}"
        if key in selection.named_by:
            line += f" — named by {selection.named_by[key]}"
        lines.append(line)
    if lines:
        parts.append("=== ROUTE: the other passages of the earlier states, each in the file it is listed under ===\n\n"
                     + "\n".join(lines))
    return "\n\n".join(parts)


ROUTE_NOTE = """

What you read: the units of State {state} under review{neighbours}, and, of the
earlier states, {given}. The earlier states' texts are whole in the files
{files} of your working directory, and the ROUTE at the end of the text lists
every passage of them not given above: what it defines, and which given passage
names it. Before you raise a point, follow the route: read in the files the
passages that the units under review, or the passages given, depend on —
those named by a given passage first, then any section whose title bears on
the unit (a rule for several modules, an actor, a trust boundary). Do not
raise a point a passage in the files answers. Quote verbatim, from the text or
from the files."""


def route_note(selection: Selection, state: int, files: list[str]) -> str:
    given = ("the passages they name and those naming what they define, verbatim" if selection.direct
             else "no passage inline: the units under review name nothing an earlier state defines")
    neighbours = ", with closed neighbours that name or speak of a change" if selection.neighbours else ""
    return ROUTE_NOTE.format(state=state, neighbours=neighbours, given=given, files=", ".join(files))


def record(selection: Selection, text: str, reading: str = SELECTION) -> dict:
    """What a round keeps of what its reviews read: how much, which earlier
    passages and how far each is from a unit under review, and why the earlier
    texts were read whole when they were. Until 2026-11-13 a round kept none of
    it (a Codex review reports no usage), so the size of a State 3-5 review was
    seen only by measuring it again."""
    given = selection.direct if reading == ROUTE else selection.received
    return {"reading": reading,
            "text_characters": len(text),
            "own": [key for key, _ in selection.own],
            "neighbours": list(selection.neighbours),
            "whole": list(selection.whole),
            "received_characters": sum(len(body) for _, _, _, body in given),
            "received": [{"state": s, "key": key, "characters": len(body),
                          **({"depth": selection.depth[key]} if key in selection.depth else {})}
                         for s, _, key, body in given]}
