"""M3: the data signals of one note's text (Data Closure contract §4, §6).

A signal is a place where a note may carry data instead of naming its home:
a number, a quoted string, a path, an enumeration of three or more
identifiers, three or more members of one enumeration (M-E1), a mapping
arrow, table markup, or a reference to a design document (decision Q7). The
detector gives no verdict; lint L3 decides whether a signal is covered.

Text inside a data address (`= models.X`, `= rules.…`, `= config.…`) and
inside `the imported X constant` is not searched: it is the address.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ADDRESS_RE = re.compile(r"=\s*(?:models|rules|config)\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
IMPORTED_RE = re.compile(r"\bthe imported [A-Za-z_][A-Za-z0-9_]* constant\b")
MODELS_ADDRESS_RE = re.compile(r"=\s*models\.(?P<name>[A-Za-z_][A-Za-z0-9_]*)")

# A number standing alone: not a digit run inside an identifier (sha256,
# list_v2), not a version or encoding suffix (UTF-8, SHA-256, v3).
NUMBER_RE = re.compile(
    # a grouped number first: `1 048 576`, `1,048,576` is one number
    r"(?<![\w.\-])-?\d{1,3}(?:[ \u00a0\u202f,]\d{3})+(?![\w.,]?\d)(?!\w)"
    r"|(?<![\w.\-])-?\d+(?:\.\d+)?(?![\w.]\w)(?!\w)"
)
_DIGIT_GROUP_SEPARATORS = re.compile(r"[ \u00a0\u202f,]")
DOUBLE_QUOTED_RE = re.compile(r'["\u201c](?P<value>[^"\u201c\u201d\n]{1,200})["\u201d]')
TYPOGRAPHIC_SINGLE_QUOTED_RE = re.compile(r"\u2018(?P<value>[^\u2018\u2019\n]{1,200})\u2019")
# A single-quoted string, not an English apostrophe (`process's`, `others'`).
SINGLE_QUOTED_RE = re.compile(r"(?<![A-Za-z0-9])'(?P<value>[^'\n]{1,200})'(?![A-Za-z0-9])")
BACKTICK_RE = re.compile(r"`(?P<value>[^`\n]{1,200})`")
DOTTED_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*(?:\(\))?")
# A path: rooted (`/proc`, `~/.codex`), with a file extension (`a/b.json`), or of
# three or more segments; `and/or` and `read/write` are words.
PATH_RE = re.compile(
    r"(?<![\w./])(?:~?/[\w.\-]+(?:/[\w.\-]+)*/?"
    r"|[\w.\-]+(?:/[\w.\-]+)*/[\w\-]+\.[A-Za-z]\w*"
    r"|[\w.\-]+/[\w.\-]+/[\w.\-]+(?:/[\w.\-]+)*)"
)
ARROW_RE = re.compile(r"→|↦|⇒|->|=>")
TABLE_RE = re.compile(r"\|[^|\n]*\|[^|\n]*\|")
# Decision Q7: the generator never receives the design documents.
DESIGN_REF_RE = re.compile(
    r"\bStates?\s+[0-6](?:\s*[–-]\s*[0-6])?\b|\b\d\d_[A-Za-z0-9_]+\.(?:md|json)\b|\b\w*_handoff\w*\b"
)
_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
# An item is no English function word: "…, and for each" ends the list before "for".
_NOT_A_WORD = r"(?!(?:for|any|not|the|a|an|so|each|every|its|their|other|all|that|this|which|when|if)\b)"
_ITEM = rf"{_NOT_A_WORD}{_IDENTIFIER}(?:\s*\([^()]*\))?"
# Three or more identifiers: `a, b and c`, `a, b, c or d`, `a, b, c`, `(a, b, c)`.
LIST_RE = re.compile(
    rf"(?<![\w.])(?P<items>{_ITEM}(?:\s*,\s*{_ITEM}){{1,}}(?:\s*,?\s+(?:and|or)\s+{_ITEM})?)(?![\w(])"
)
TUPLE_RE = re.compile(rf"\((?P<items>{_IDENTIFIER}(?:\s*,\s*{_IDENTIFIER}){{1,}})\)")
# One pair of a correspondence written as prose: `list_slot_rows for slots`.
MAPPING_PAIR_RE = re.compile(r"(?<![\w.])(?P<key>[A-Za-z_][A-Za-z0-9]*_[A-Za-z0-9_]*)\s+for\s+(?P<value>[A-Za-z_][\w]*)")
_MAPPING_JOINER_RE = re.compile(r"\s*,\s*(?:and\s+)?")
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Words a list may contain that are no item of it.
_LIST_JOINERS = {"and", "or", "then", "the", "a", "an"}


@dataclass(frozen=True)
class Signal:
    kind: str  # number | quoted | path | list | mapping | enum_members | arrow | table | design_reference
    text: str
    start: int
    items: tuple[str, ...] = field(default=())
    enum: str | None = None


def address_spans(text: str) -> list[tuple[int, int]]:
    return [m.span() for m in ADDRESS_RE.finditer(text)] + [m.span() for m in IMPORTED_RE.finditer(text)]


def addressed_models(text: str) -> set[str]:
    return {m.group("name") for m in MODELS_ADDRESS_RE.finditer(text)}


def _inside(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _items(raw: str) -> tuple[str, ...]:
    raw = re.sub(r"\([^()]*\)", " ", raw)
    words = [w for w in re.split(r"[\s,]+", raw) if w]
    return tuple(w for w in words if w not in _LIST_JOINERS)


def _identifier_like(word: str, names: frozenset[str]) -> bool:
    return "_" in word or any(c.isdigit() for c in word) or word[:1].isupper() or word in names


def detect(
    text: str,
    enums: dict[str, tuple[str, ...]] | None = None,
    names: frozenset[str] = frozenset(),
    field_names: frozenset[str] = frozenset(),
) -> list[Signal]:
    """Every data signal of ``text``.

    ``enums`` maps enumeration names to their members (M-E1, M-E5); without
    it no enum signal is made. ``names`` are declared names and members: a
    list is a signal only when two or more of its items look like
    identifiers (snake_case, CamelCase, a digit, or a declared name), so an
    English series ("no file, no clock and no store") is prose.
    ``field_names`` are model fields: a member that is also a field name does
    not count towards M-E1 (research Q9 §2.4-2)."""
    spans = address_spans(text)
    quoted_spans: list[tuple[int, int]] = []
    found: list[Signal] = []

    def add(signal: Signal) -> None:
        if not _inside(signal.start, spans):
            found.append(signal)

    for regex in (DOUBLE_QUOTED_RE, SINGLE_QUOTED_RE, TYPOGRAPHIC_SINGLE_QUOTED_RE):
        for m in regex.finditer(text):
            quoted_spans.append(m.span())
            add(Signal("quoted", m.group("value"), m.start()))
    for m in BACKTICK_RE.finditer(text):
        quoted_spans.append(m.span())
        if not DOTTED_NAME_RE.fullmatch(m.group("value").strip()):
            add(Signal("quoted", m.group("value"), m.start()))
    design_spans = [m.span() for m in DESIGN_REF_RE.finditer(text)]
    for m in NUMBER_RE.finditer(text):
        # the number of `State 5` is the design reference, not a value
        if not _inside(m.start(), quoted_spans) and not _inside(m.start(), design_spans):
            add(Signal("number", _DIGIT_GROUP_SEPARATORS.sub("", m.group(0)), m.start()))
    for m in PATH_RE.finditer(text):
        if not _inside(m.start(), quoted_spans):
            add(Signal("path", m.group(0), m.start()))
    for m in ARROW_RE.finditer(text):
        add(Signal("arrow", m.group(0), m.start()))
    for m in TABLE_RE.finditer(text):
        add(Signal("table", m.group(0), m.start()))
    for m in DESIGN_REF_RE.finditer(text):
        add(Signal("design_reference", m.group(0), m.start()))
    listed: list[tuple[int, int]] = []
    for regex in (LIST_RE, TUPLE_RE):
        for m in regex.finditer(text):
            # a list in parentheses is one signal, whichever pattern saw it first
            if any(start < m.end() and m.start() < end for start, end in listed):
                continue
            items = _items(m.group("items"))
            if len(set(items)) >= 3 and sum(_identifier_like(i, names) for i in set(items)) >= 2:
                listed.append(m.span())
                add(Signal("list", m.group(0), m.start(), items=items))
    found.extend(_mapping_signals(text, spans))
    if enums:
        found.extend(_enum_signals(text, enums, spans, field_names))
    return sorted(found, key=lambda s: (s.start, s.kind))


def _mapping_signals(text: str, spans: list[tuple[int, int]]) -> list[Signal]:
    """Two or more `key for value` pairs joined by commas: a correspondence
    (§15.2 check 5) written as prose, whatever words the values are."""
    signals, chain = [], []
    for m in MAPPING_PAIR_RE.finditer(text):
        if _inside(m.start(), spans):
            continue
        if chain and _MAPPING_JOINER_RE.fullmatch(text[chain[-1].end():m.start()]):
            chain.append(m)
            continue
        if len(chain) >= 2:
            signals.append(_mapping(text, chain))
        chain = [m]
    if len(chain) >= 2:
        signals.append(_mapping(text, chain))
    return signals


def _mapping(text: str, chain: list[re.Match]) -> Signal:
    return Signal("mapping", text[chain[0].start():chain[-1].end()], chain[0].start(),
                  items=tuple(m.group("key") for m in chain))


def _enum_signals(
    text: str, enums: dict[str, tuple[str, ...]], spans: list[tuple[int, int]], field_names: frozenset[str]
) -> list[Signal]:
    """M-E1: three or more members of one enumeration, a member that is also
    a field name not counted. M-E5: a member shared by several enumerations
    counts only for one the note names (by address or by its type name)."""
    words: dict[str, int] = {}
    for m in WORD_RE.finditer(text):
        if not _inside(m.start(), spans):
            words.setdefault(m.group(0), m.start())
    named = addressed_models(text) | {w for w in words if w in enums}
    owners: dict[str, set[str]] = {}
    for name, members in enums.items():
        for member in members:
            owners.setdefault(member, set()).add(name)
    signals = []
    for name, members in enums.items():
        present = [
            member for member in members
            if member in words and member not in field_names
            and (len(owners[member]) == 1 or name in named)
        ]
        if len(present) >= 3:
            first = min(words[member] for member in present)
            signals.append(Signal("enum_members", ", ".join(present), first, items=tuple(present), enum=name))
    return signals


def member_order(text: str, members: tuple[str, ...]) -> list[str]:
    """The members of one enumeration in the order the text first names them."""
    spans = address_spans(text)
    seen: dict[str, int] = {}
    for m in WORD_RE.finditer(text):
        if m.group(0) in members and not _inside(m.start(), spans):
            seen.setdefault(m.group(0), m.start())
    return sorted(seen, key=seen.__getitem__)
