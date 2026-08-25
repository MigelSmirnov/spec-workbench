# Cabinet Backend — Stage 8.1 plan_actual module review

Module: `plan_actual`

Status: **PASS_INTERNAL_VARIATION**

Slice SHA-256: `6ac5f75fcf5cf46993b7d2d9676f1ce007711d1c497424dfec2ba6cb69c1c8f1`

Structural review: 24 contracts, 46 notes, 0 blocks, 0 deterministic prompts.

## Finding and repair

The stale packet exposed five owned capabilities but only snapshot refresh and
calculation contracts. It allowed memory-only snapshots and matches, implicit
proposal confirmation, fabricated unmatched results, and calculations that did
not resolve pinned evidence through authoritative boundaries.

A73 closes the runtime mechanism with one PostgreSQL `PlanActualRepository` and
cohesive `PlanActualService`. Immutable snapshots and proposals append; proposals
are non-authoritative; explicit match decisions are durable and serialized per
invoice line; only active confirmed decisions contribute; unmatched identities
are exact and stable ordered. Calculation resolves immutable Card evidence through
the supplied archive service and project context through the supplied Registry
service. Bootstrap constructs and injects the exact service without fallback.

## Adversarial re-check

A trivial or materially different observable implementation can no longer return
empty analysis, synthesize a current snapshot, treat similarity as confirmation,
hide unmatched facts, bypass exact evidence resolution, or maintain match state
only in memory without violating explicit contracts and notes.

Remaining variation is internal: SQL schema/index layout, proposal ranking within
the typed evidence contract, helper decomposition, caching, and equivalent
arithmetic execution that preserves the accepted semantic result.

Classification: **PASS_INTERNAL_VARIATION**.
