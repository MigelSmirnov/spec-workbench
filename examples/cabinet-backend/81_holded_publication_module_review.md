# Cabinet Backend — Stage 8.1 holded_publication module review

Module: `holded_publication`

Status: **PASS_INTERNAL_VARIATION**

Slice SHA-256: `5a50387fa440b2e87833781ba484f5dd04b15ce0d8865796c97898ad76ea7118`

Structural review: 17 contracts, 36 notes, 0 blocks, 0 deterministic prompts.

## Finding and repair

The stale packet constrained A51/A52 verification but lacked a logical
publication repository/unit-of-work, composition boundary, and status contract.
It allowed memory-only duplicate prevention and settlement state.

A74 introduces one PostgreSQL repository and cohesive publication service over
the exact archive and Holded gateway. Exact revision locking/uniqueness precedes
the sole create; every verified or unresolved transition is durable; ambiguous
outcomes reconcile read-only; status returns exact committed state or a typed
not-found error. Bootstrap injects the exact service without fallback.

## Adversarial re-check

Memory-only lifecycle state, a second create after ambiguity, technical-response
success, unverified marker settlement, fabricated status, direct HTTP/archive
persistence, or a changed revision binding now violates explicit contracts and
notes. Remaining variation is internal SQL layout, helper decomposition, evidence
indexing, and equivalent A51 comparison execution.

Classification: **PASS_INTERNAL_VARIATION**.
