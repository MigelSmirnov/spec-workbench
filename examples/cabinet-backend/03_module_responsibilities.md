# State 3 — Cabinet Backend module responsibilities

## Status

Experimental first State 3 responsibility derived from the accepted State 2 rules.

This file intentionally contains only one responsibility as a dogfood pass for the
State 2 → State 3 navigation workflow. It does not claim that the complete Cabinet
Backend module decomposition is finished.

---

## Candidate module — `holded_purchase_publication`

### Responsibility

Own the deterministic publication of one exact immutable Invoice Card revision as
one Holded purchase document, including safe handling of ambiguous create outcomes,
read-back verification, and publication reconciliation state.

The module owns the protocol-level decision of whether a Holded purchase publication
is proven successful, remains unknown, or requires reconciliation.

### State 2 evidence

Primary accepted decisions:

- `A51` — create one Holded purchase and verify it by GET;
- `A52` — marker-based Holded purchase create recovery.

The relationship is explicit rather than lexical:

- `A51` delegates ambiguous create recovery to `A52`;
- `A52` requires successful recovered documents to be verified according to `A51`.

Shared names such as `Holded`, `invoice_id`, or `publication_attempt_id` are useful
navigation evidence but are not sufficient by themselves to assign responsibility.

### Knowledge owned

This responsibility owns knowledge of:

- what constitutes one logical Holded purchase publication attempt;
- the maximum automatic create count for that attempt;
- the stable local publication-attempt identity and correlation marker;
- the accepted create → read-back verification sequence;
- the read-only recovery sequence after an ambiguous create outcome;
- the accepted verification fields for the returned Holded purchase;
- the distinction between source Invoice Card totals and Holded-calculated totals;
- the accepted gross-total reconciliation tolerance;
- the deterministic outcomes `created_and_recovered`, `outcome_unknown`,
  `duplicate_conflict`, `verification_failed`, and reconciliation-required states;
- the external Holded document identifier bound to one exact Invoice Card revision.

### Decisions made

The module decides:

- whether a new publication attempt may issue its single create request;
- whether an observed create outcome is clear or ambiguous;
- whether recovery must run instead of another create request;
- whether a recovered marker match count is zero, one, or multiple;
- whether the returned Holded document satisfies the accepted business-field
  verification baseline;
- whether gross totals reconcile within accepted currency precision;
- whether publication is proven successful, remains unknown, or requires manual
  reconciliation.

### Details hidden

Callers must not need to know:

- the exact ordering of POST, list polling, GET, and verification operations;
- how the stable attempt marker is formatted inside the accepted Holded field;
- how bounded recovery polling is sequenced;
- how Holded intermediate rounding evidence is compared and preserved;
- which raw Holded response fields are required to prove successful publication;
- how publication-attempt state is persisted between network operations.

### Candidate public capabilities

The public surface should remain narrow. Candidate capabilities are:

```text
publish_purchase(invoice_revision, actor) -> publication_result
resume_purchase_publication(publication_attempt_id) -> publication_result
```

These are responsibility-level capability names only. Exact contracts and types
belong to later design states and are intentionally not finalized here.

`publish_purchase` owns the first publication attempt and may return a result that
requires later recovery or reconciliation.

`resume_purchase_publication` resumes an already persisted attempt without creating
a second logical attempt or bypassing the one-POST rule.

### Must not own

This module must not own:

- Invoice Card capture, OCR, correction, or semantic duplicate detection;
- mutation of immutable Invoice Card revisions;
- general Holded credential or identity management;
- a generic Holded transport/client implementation shared by unrelated integrations;
- interpretation of unverified numeric Holded status values;
- supplier master-data creation policy beyond the accepted publication evidence;
- Holded purchase update, refund, deletion, attachment, approval, or payment policy;
- HTTP or MCP request/response formatting;
- generic persistence infrastructure;
- project assignment or PresuPro matching policy.

### Dependencies it may use

The responsibility may depend on:

- the accepted immutable Invoice Card revision and publication input models;
- persistence for publication-attempt and publication evidence records;
- a narrow Holded purchase API boundary capable of create, list, and GET operations;
- time/clock access for attempt and verification evidence;
- deterministic hashing/canonicalization used for stored publication evidence.

The transport boundary does not own publication policy. In particular it must not
silently retry purchase creation after an ambiguous outcome.

### Expected consumers

Likely consumers are:

- an application/API orchestration boundary that requests first publication;
- an operator or agent recovery workflow that resumes an ambiguous attempt;
- reconciliation/status views that read the resulting publication evidence.

Consumers must not reproduce the create/recovery/verification policy themselves.

### Primary enforcement ownership

For the A51/A52 publication lifecycle, `holded_purchase_publication` is the candidate
primary enforcement owner of these invariants:

```text
maximum automatic POST count per logical publication attempt = 1
successful publication requires read-back verification
ambiguous create outcome does not authorize automatic repeated POST
recovered marker match alone is not sufficient without business-field verification
one publication record binds to one exact invoice revision hash
Holded recalculation never mutates the immutable Invoice Card revision
```

This ownership is limited to the publication lifecycle represented by A51 and A52.
Other State 2 rules that merely mention Holded are not assigned here without
separate evidence.

### Open boundary checks before accepting this module

Before this candidate becomes a stable State 3 module, verify:

1. whether any other accepted State 2 decision has an explicit dependency on A51 or
   A52 that expands this responsibility;
2. whether publication-attempt persistence belongs inside this module or behind a
   separate storage dependency while this module retains policy ownership;
3. whether later accepted Holded revision/update rules should join this same deep
   module or form a separate responsibility because they change for different
   reasons;
4. whether the platform Holded API boundary already has a stable name that should be
   used as the dependency name without transferring publication-policy ownership to
   that boundary.
