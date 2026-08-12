# Stage 7.1 — Semantic E2E review handoff

This is a Workbench authoring/review stage, not a new `global_spec.json` section and not a change to `SPEC_STANDARD.md`.

Use this stage after deterministic structural closure and the State 7 Notes gate, before declaring Notes semantically closed.

## Why this stage exists

A note can be syntactically valid, correctly classified, fully addressed, and still permit two materially different implementations. Reviewing notes one line at a time is insufficient because ambiguity often exists across a complete business flow: ownership, guards, state transitions, external effects, recovery, and terminal outcomes.

Stage 7.1 reviews **observable business semantics**, not implementation uniqueness.

The question is not:

> Can this function be implemented in more than one way?

That is normally fine.

The question is:

> Can two materially different observable behaviors both satisfy the same accepted specification slice?

If yes, the specification is not semantically closed.

## Primary input

Start from the State 4 business flows. For each `flow:*`, construct a semantic slice from the already accepted design:

- State 0/1 product and model meaning when needed to recover intent;
- State 2 rules/invariants;
- State 3 module ownership;
- State 4 flow definition;
- State 5 public-operation semantics;
- State 6 contracts, data closure, and exception taxonomy;
- deterministic post-State-6 structures such as Router Closure when relevant;
- State 7 Notes.

Prefer the Factory/normalizer module slicing machinery when possible. Do not invent a second incompatible context builder merely for this review.

## Behavior graph

For each business flow recover a compact semantic graph with these node/edge roles:

```text
actor / external trigger
        ↓
business intent
        ↓
public operation(s)
        ↓
guards / business decisions
        ↓
state transition(s)
        ↓
external side effect(s), if any
        ↓
recovery / reconciliation, if needed
        ↓
observable terminal outcome
```

The graph is a review artifact. It does not need to be consumed by Factory.

A graph is acceptable when:

- every material trigger has a defined entry;
- every material decision has an owner;
- every state transition has a defined precondition and observable consequence;
- an external mutation is guarded by the accepted business decision that permits it;
- ambiguous external outcomes have an explicit recovery/reconciliation path;
- forbidden transitions are absent;
- every accepted terminal business outcome is reachable;
- no material behavior is introduced solely by the reviewer.

## Adversarial ambiguity question

For every flow, and for every generated callable that participates materially in the flow, ask exactly once:

> Construct the strongest materially different alternative observable semantics that still satisfies this complete specification slice.

Classify the answer:

- `PASS` — no materially different observable semantics can be constructed;
- `PASS_INTERNAL_VARIATION` — alternatives differ only in implementation detail, not observable behavior;
- `AMBIGUITY` — two materially different observable behaviors remain permitted.

For `AMBIGUITY`, record:

```text
scope / flow:
interpretation_A:
interpretation_B:
material_difference:
missing_constraint_owner: upstream_business | structure | property | note
```

Do not silently choose one interpretation. Return the finding to its owning design state.

## Placeholder-resistance question

Using the same full semantic slice, ask:

> Can a trivial implementation (`None`, empty DTO/collection, constant success, blind forwarding, unconditional exception, or equivalent skeleton behavior) satisfy the accepted specification?

If yes, the callable/flow is not semantically closed even if the deterministic Notes gate passes.

## Semantic scenarios: tests before code

For each material branch in the behavior graph, write implementation-independent acceptance scenarios before generated code exists.

Use Given / When / Then over domain facts and observable effects, not private helpers, mocks, ORM methods, framework internals, or implementation classes.

Example:

```text
given:
  an eligible immutable invoice revision
  no equivalent logical publication
  the remote create result is ambiguous
when:
  publication is requested
then:
  exactly one remote create attempt exists
  the logical publication is reconciliation-pending
  no automatic second create is issued
  the immutable invoice revision is unchanged
```

These are **semantic pseudotests**. They are requirements on future code, not tests derived from existing code.

Later, generated-code validation may bind the same scenarios to real fixtures/callables and turn them into runtime acceptance tests. The direction must remain:

```text
business meaning
→ semantic scenario
→ specification
→ generated implementation
→ runtime acceptance test
```

Never reverse this into tests that merely encode whatever implementation happened to be generated.

## Minimum scenario set per flow

Do not target a fixed scenario count. Cover the graph's material branches. A useful minimum heuristic is:

- happy path;
- primary refusal/precondition failure;
- ambiguity/recovery path when the flow has external uncertainty;
- idempotent/repeated request path when repetition matters;
- invariant-preservation case for immutable or authority boundaries.

If a meaningful `Then` cannot be written without guessing, that is itself a Stage 7.1 finding.

## Handoff result

A flow is `semantic_closed` only when:

1. its behavior graph can be reconstructed from accepted sources;
2. the adversarial ambiguity question produces no unresolved `AMBIGUITY`;
3. placeholder resistance passes;
4. its material graph branches have semantic scenarios with unambiguous observable `Then` clauses;
5. any discovered gap has been returned to and resolved in its true owning state.

Do not modify product semantics merely to make the review pass.

## Cabinet dogfood

The Cabinet-specific first handoff lives at:

`examples/cabinet-backend/71_semantic_e2e_handoff.md`

Start there for the first Stage 7.1 execution.