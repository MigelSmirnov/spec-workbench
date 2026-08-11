# Normative authoring sequence

This document fixes the authoring order used by Spec Workbench. It exists to
remove ambiguity between numbered design states, intermediate closure artifacts,
and deterministic Factory backends.

`SPEC_STANDARD.md` remains normative for the serialized `global_spec.json`
format. `SKILL.md` remains normative for the semantic meaning of numbered
states. This document is normative for **ordering and prerequisites**.

## Canonical order

```text
State 0  Product frame
  -> State 1  Models
  -> State 2  Rules / decisions
  -> State 3  Module responsibilities and capabilities
  -> State 4  Reviewed end-to-end flows
  -> State 5  Public module operations
  -> pre-contract structured data closure
  -> State 6  Exact contracts and internal functions
  -> deterministic HTTP Router IR closure (when used)
  -> State 7  Notes
  -> adapters / assembly / final validation
  -> Factory handoff
```

The intermediate structured-data closure is **not State 6**. Existing artifacts
and schemas named `60_data_closure.json` / `spec_workbench_state6_data_*` are
retained for compatibility only; their numeric name does not redefine the
semantic state numbering in `SKILL.md`.

Likewise, `70_router_closure.json` is a workbench artifact name, not a statement
that Router Closure is semantic State 7. State 7 remains Notes.

## Required dependency chain for deterministic HTTP assembly

For projects using `rules.http_router_backend` the dependency chain is:

```text
reviewed State 4 flow
  -> State 5 owning public operation and exposure decision
  -> accepted structured data placement
  -> State 6 canonical exact contracts
  -> Router IR / Router Closure
  -> deterministic validation against contracts
  -> official deterministic Route B Factory emitter
```

### Invariants

1. Canonical Python signatures come only from `contracts` / State 6.
2. Router rows never create, infer, duplicate, or override canonical signatures.
3. Legacy router code is evidence only; it cannot be the source of a new
   signature or a normative route by itself.
4. Pre-contract data closure may place already accepted config, persistence,
   rules, properties, or determinism facts, but it cannot consume the State 6
   number or fabricate contract-dependent values.
5. Router Closure is post-contract. A route may be designed only when its
   owning operation and the contracts needed to validate handler/function
   ownership, call arity, parameter paths, and projections are stable.
6. `http_router_backend` present but invalid is a defect. Do not remove it or
   silently fall back to an LLM router path.
7. Artifact filename prefixes are storage conventions, not semantic state
   authority. When a filename conflicts with this sequence, this sequence and
   `SKILL.md` win.

## Compatibility note

The current Cabinet workbench introduced structured-data and Router Closure
artifacts while the tooling was evolving. Their filenames (`60_*`, `70_*`) must
not be used to infer the authoring order. Until they are migrated, tools and
agents must interpret them by purpose:

- `60_data_closure.json`: pre-contract structured-data preparation;
- State 6 authoring: exact contracts and internal functions;
- `70_router_closure.json`: post-contract deterministic HTTP closure workbench;
- State 7 authoring: notes.

Any future orchestration tool must read the machine-readable companion
`authoring_sequence.json` rather than reconstructing order from filenames.