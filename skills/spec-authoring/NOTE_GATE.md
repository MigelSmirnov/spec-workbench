# State 7 Notes authoring gate

This document defines the Workbench authoring gate applied after deterministic structural closure and before final specification assembly. `SPEC_STANDARD.md` remains normative for the serialized note syntax and closed `NOTE_CLASS` registry. `note_gate.json` is the machine-readable companion for the deterministic gate implemented by `tools/notes_workbench/gate.py`.

## Purpose

State 7 notes are written manually for the downstream LLM generator. The Workbench must reject structural note defects and surface cheap machine-detectable ambiguity before the note set is accepted. The gate does not attempt to understand arbitrary prose or choose between competing product meanings.

A note set is ready only when every deterministic `BLOCK` and every author-review finding is resolved.

## Gate levels

- `PASS` — no finding is emitted.
- `REVIEW` — the syntax is valid, but the class set or multiplicity exposes potentially competing obligations. The author must reconcile or rewrite the notes before handoff.
- `BLOCK` — the note cannot be accepted as valid State 7 input.

`REVIEW` is fail-closed for State 7 handoff. It is not an assertion that the notes are contradictory; it is an assertion that the Workbench can cheaply prove they need explicit author resolution.

## Deterministic BLOCK checks

The gate checks all non-heading, non-empty lines in `80_notes.md` and blocks when:

1. the line is not exactly `<scope>: [NOTE_CLASS] prose`;
2. the scope is not an exact State 6 contract symbol or exact module name;
3. the marker is not in the closed registry from `note_gate.json`;
4. a reference class omits its required address namespace;
5. an address of the form `= config.*`, `= models.*`, or `= rules.*` does not resolve to closed structured data;
6. the prose is an explicit semantic stub such as `TODO`, `TBD`, `implement ...`, `handle errors appropriately`, `validate input correctly`, or equivalent registered placeholder form;
7. a State 6 callable has neither a State 7 note nor a deterministic implementation owner.

Malformed or unknown notes are never silently skipped.

## Callable completeness

State 6 is the canonical callable inventory. Every callable in `60_contracts.json` must be accounted for before State 7 handoff:

- a callable that still requires LLM generation must have at least one exact-scope State 7 note;
- a callable whose complete implementation is owned by deterministic assembly does not require redundant prose notes.

For `http_router_backend/v1`, a handler with `emission: "table"` is a deterministic completeness exemption because its authorization, delegate, typed argument refs and return behavior are already closed in router IR. An `emission: "irregular"` handler is not exempt: deterministic routing owns only its registration, while the handler body still requires generation guidance.

This rule is intentionally about implementation ownership, not about naming conventions. A future deterministic backend may add another exemption only when the Workbench can prove from structured artifacts that it owns the callable implementation completely.

## Cross-note consistency

`NOTE_CLASS` is used as an authoring signal, not as an automatic semantic resolver. `note_gate.json` declares two cheap forms of cross-note checks:

- **cardinality** — a class such as `RETURN_SHAPE` may be single-per-scope; repeated instances require review because they may describe competing outcomes;
- **suspicious pairs** — selected pairs on the same scope require review because they commonly overlap on one behavioral axis, for example `VALIDATION_ERROR + FALLBACK`.

A suspicious pair is not automatically invalid. The author resolves the finding by making conditions/precedence explicit, removing or rewriting a competing note, or moving the deciding fact to its existing deterministic owner. When an observable relation can be expressed as a Factory property, a property is a valid way to make the resolution machine-checkable, but properties are not mandatory for every pair.

Do not expand the pair table to all combinations. Add only relations that recur as useful authoring diagnostics across projects.

## Semantic stubs

A syntactically valid note may still be useless to generation. Explicit placeholder forms are `BLOCK`, not advisory review. This is intentionally narrower than full semantic-under-specification detection: the deterministic gate catches forms that can be identified without interpreting project meaning.

Broader placeholder resistance remains an authoring review question: could a function still be implemented as an empty value, constant success, or trivial forwarding call without violating its accepted notes and structured obligations? If yes, return to the owning design state or strengthen the notes.

## Official commands

```bash
python tools/design_notes.py examples/<case> --gate --json
python tools/design_notes.py examples/<case> --handoff --json
```

`design_authoring_next.py` keeps the project in `state7_notes` until the handoff is ready.

## Cabinet dogfood

`examples/cabinet-backend/80_notes.md` is the first project-level dogfood case. Its notes are authored only after the Cabinet structured data, exact contracts, per-route Router Closure, and global Router context are closed enough to provide deterministic homes for values and transport structure. Notes reference those homes rather than copying their values into prose.
