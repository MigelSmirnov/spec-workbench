# Cabinet Backend — Stage 8.1 retention_release module review

Module: `retention_release`

Status: **PASS_INTERNAL_VARIATION**

Slice SHA-256: `98f467b480f627adbcd197ed8d01381bcbc259b5a080458c726096f68ad4aa0a`

Structural review: 15 contracts, 32 notes, 0 blocks, 0 deterministic prompts.

## Finding and repair

The stale packet lacked durable evaluation/decision state, a status contract,
bootstrap composition, and a typed way to resolve the exact working-set
membership whose complete coverage Flow 6 requires.

A75 adds read-only PostgreSQL-authoritative membership through synchronization
and one PostgreSQL retention repository/service. Evaluation verifies every exact
member through synchronization and archive evidence. Authorization locks the
target, reloads membership and all proof, rejects any change or coverage gap, and
records one immutable idempotent decision. Status never implies physical deletion.

## Adversarial re-check

Subset proof, Registry-status authority, stale evaluation, changed membership,
memory-only decisions, fabricated status, or physical deletion inside the domain
operation now violates explicit contracts and notes. Remaining variation is
internal SQL layout, evidence lookup order, helper decomposition, and the physical
adapter used after an exact recorded authorization.

Classification: **PASS_INTERNAL_VARIATION**.
