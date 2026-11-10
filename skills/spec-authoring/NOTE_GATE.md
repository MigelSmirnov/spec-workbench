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
6. a note names a declared data-provider record table (a `record_tuple`
   constant of `rules.data_provider_backend`) without naming its access: the
   same note must contain at least one declared field of the table's row
   model — the match is then spelled in the row vocabulary, e.g.
   `one imported CAPABILITY_GRANTS row whose channel equals command.channel
   and capability equals command.capability` — or must name a delegate
   contract whose own notes spell that access (delegation is resolved as a
   fixpoint over the naming graph). See "Table access must be named" below;
7. the prose is an explicit semantic stub such as `TODO`, `TBD`, `implement ...`, `handle errors appropriately`, `validate input correctly`, or equivalent registered placeholder form;
8. a State 6 callable has neither a State 7 note nor a deterministic implementation owner.
9. a callable returns a spec-declared interface, or a transport handler's note
   exposes a transport-to-interface adaptation boundary, but its State 7 notes do not
   both identify concrete implementation/adapter ownership and explicitly
   prohibit instantiating the interface itself.
10. a scope's note routes an operation through a port it does not take as a
    parameter — `through|via [only] the <accessor> repository|port`, the
    accessor being a contract that returns one interface, or `through|via
    <Interface>` — and no note of that scope names a method of the port. See
    "Port access must be named" below (`port_methods_unnamed`);
11. a class declares, under the same names, methods of the interface one of
    its accessors returns, and no accepted State 2 decision names the copy as
    `Class.method`. See "One operation, one owner" below
    (`duplicate_contract_surface`).

Malformed or unknown notes are never silently skipped.

The interface-construction check does not apply merely because a callable
receives an interface-typed parameter. Those injected dependencies are closed
structurally by `implementation_obligations`. It applies where generated code
must produce the runtime object, preventing Python `Protocol` declarations from
being called as if they were concrete classes.

## Table access must be named

`SPEC_STANDARD` §15.9 hides data values from the generator and hands it the
access signature instead. For a record table the signature includes the
match: a note that names the table but not the predicate leaves the access
to invention — measured failures produced filters on cells that do not
exist. The rule is closed, not lexical guessing: the note either names at
least one declared row-model field (any field naming counts — the author is
trusted to spell the whole predicate once forced into the row vocabulary),
or names the contract that owns the access. The finding always prescribes
the fill: the declared field list and the predicate template.

Scalar, tuple, and mapping constants are exempt: their access is the import
itself, and their values may legitimately double as structural vocabulary.

## Port access must be named

The Factory slicer hands a module only the contracts its notes name. A note
that reaches persistence "only through the staff_access repository of that
transaction" names the accessor `PortalTransaction.staff_access ->
StaffAccessRepository` and nothing the generator can call on what it returns:
the prompt lists the accessor and none of the port's operations, and the
generator invents them. client_portal spec b3bfb504: `staff_identity` called
eight `StaffAccessRepository` methods that do not exist and `derived_views` two
`BudgetRepository` methods; `viewer_access`, whose notes said "calling
get_viewer_session of the viewer_access repository", came out right.

A scope that routes through a port therefore names, in one of its notes, each
port method it calls, as an address the flow closure resolves:
`<method> of the <accessor> repository`, `<method> of the <Interface>`,
`Interface.method`, or `param.method` through its own contract. It is also
closed when the note names the interface by name together with a method of it
(a named interface is imported and the prompt lists its operations exactly), or
names a callable that takes the port as a parameter (`with the imported
append_audit into the audit repository of that transaction`). A port the
scope's own contract takes as a parameter is exempt: it is imported, and the
prompt lists an imported interface's operations. The gate proves that at least
one method is named; naming every method the operation calls is the author's
obligation. The Factory's draft gate stops the other side
(`undeclared_port_method`, code-factory `tools/draft_static_gates.py`).

## One operation, one owner

A class whose accessor returns an interface (`PortalTransaction.expenses ->
ExpenseRepository`) and which also declares that interface's methods under the
same names (`PortalTransaction.get_expense_aggregate`) shows the generator one
operation under two owners. It picks either, and reads the accessor as if it
were the repository (`transaction.expenses.get_expense_aggregate`). The copy
blocks unless an accepted State 2 decision names it as `Class.method`: keeping
a transitional copy is then a decision with an owner, not an accident of an
earlier shape.

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
