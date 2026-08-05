# State 2 — accepted follow-up rules

## Status

Accepted normative continuation of `02_rules.md`.

This document consolidates State 2 decisions that were accepted after A1–A3 but
were not yet merged into the large primary rules file. It does not redefine the
State 1 system boundary or the Cabinet web application contract.

The next editorial pass may merge these sections into `02_rules.md` without
changing their meaning.

---

# B. Duplicate handling

## Accepted decision B1 — semantic duplicate detection belongs to Cabinet

Semantic duplicate detection is owned by the Cabinet web application during the
interactive user workflow. Cabinet Backend does not repeat heuristic duplicate
search by supplier, invoice number, date, amount, line similarity, OCR text, or
other business signals.

### Normative rules

1. Cabinet resolves suspected semantic duplicates before publishing a confirmed
   Invoice Card for synchronization.
2. Cabinet Backend protects against technical duplication only:
   - repeated delivery of the same transfer manifest;
   - repeated import of the same Card content revision;
   - repeated attachment of the same source binary.
3. Repeating the same immutable payload must be idempotent and must not create a
   second logical invoice, revision, import, or source replica.
4. A new confirmed content revision for an existing `invoice_id` is a normal Card
   revision and is not a duplicate invoice.
5. If two accepted Invoice Cards are later discovered to describe the same real
   invoice, resolution requires an explicit human decision.
6. Cabinet Backend must not automatically merge, delete, or rewrite either Card.
7. A manual duplicate resolution may link the records and exclude one from chosen
   downstream views, but both accepted histories and their evidence remain
   auditable.

### Required tests

1. Repeating one manifest does not create a second import.
2. Repeating one Card content hash does not create a second revision.
3. Reattaching identical bytes to the same source target is idempotent.
4. A different confirmed content hash for the same `invoice_id` is accepted as a
   revision rather than classified as a duplicate.
5. Two different invoice IDs are never merged automatically by Backend.

### Consequence

Cabinet owns semantic understanding; Cabinet Backend owns deterministic identity,
idempotency, persistence, and audit.

---

# C. PresuPro estimates and matching

## Accepted decision C1 — PresuPro semantic analysis belongs to Cabinet

Cabinet performs the semantic and assisted analysis that connects purchased goods
to estimates. This includes cases where estimate prices refer to one supplier but
actual purchases were made from another supplier.

Cabinet Backend does not choose the relevant estimate, infer product equivalence,
or independently create semantic matches.

### Normative rules

1. Cabinet may use AI and human confirmation to analyse invoice lines against one
   or more PresuPro estimates.
2. Cabinet Backend stores imported immutable estimate projections and accepted
   matching decisions.
3. Backend may verify that referenced invoices, Card revisions, lines, estimate
   snapshots, and estimate items exist.
4. Backend must not confirm a semantic match merely because textual descriptions,
   prices, suppliers, or quantities look similar.
5. A suggestion is not analytical truth until Cabinet submits a confirmed
   decision with sufficient provenance.
6. Deterministic totals and reports may be calculated from confirmed decisions;
   semantic interpretation remains outside Backend.

### Consequence

Cabinet answers why two commercial items should be treated as corresponding.
Cabinet Backend records exactly what was confirmed and calculates from that fact.

---

## Accepted decision C2 — accepted Estimate Snapshots are immutable

An estimate accepted from PresuPro is stored as an immutable `EstimateSnapshot`.
PresuPro does not edit an already accepted estimate in place for Backend purposes.
A changed estimate is represented by a new snapshot.

### Normative rules

1. Cabinet Backend never overwrites an accepted Estimate Snapshot.
2. Existing snapshots remain available for historical and reproducible analysis.
3. Every `InvoiceLineEstimateMatch` references one exact Estimate Snapshot and one
   exact item in that snapshot.
4. Arrival of a new estimate does not alter or invalidate historical matches to
   an older estimate automatically.
5. Backend must not transfer old matches to a new snapshot automatically.
6. Analysis against a newer estimate requires new Cabinet decisions.
7. The relationship between successive PresuPro estimates remains an integration
   question until PresuPro exposes an accepted version, family, or predecessor
   contract.

### Formal invariant

```text
accepted EstimateSnapshot content is immutable
```

A new content identity must create a new snapshot record rather than mutate an
existing one.

### Required tests

1. Reimporting identical estimate content is idempotent.
2. Different estimate content creates a new snapshot.
3. Existing matches continue to reference their original snapshot.
4. A new snapshot receives no copied confirmed matches by default.

---

## Accepted decision C3 — unmatched purchases are normal analytical facts

An invoice line may have no matching item in the analysed estimate. This is not a
Card validation error and does not block invoice acceptance.

### Normative rules

1. One invoice line has at most one active confirmed estimate-item match in the
   current baseline.
2. Splitting one invoice line across several estimate items is not supported in
   the current baseline.
3. A line without a confirmed match remains explicitly unmatched.
4. Unmatched status may represent additional work, a consumable, delivery, a
   tool, a substitution, an omitted estimate item, or another Cabinet explanation.
5. Cabinet owns semantic classification and explanation of the unmatched line.
6. Cabinet Backend stores the confirmed result and optional explanation
   provenance; it does not invent a category.
7. Unmatched lines remain available to coverage and variance analytics.

### Required tests

1. An invoice containing unmatched lines is accepted normally.
2. An unmatched line does not create a placeholder estimate item.
3. Backend rejects attempts to create two simultaneous active confirmed matches
   for one line.
4. Rejecting or removing a match returns the line to explicit unmatched status
   without changing the Invoice Card.

---

# D. Source package semantics

## Accepted decision D1 — one logical source package per Invoice Card

One Invoice Card is associated with one logical `SourcePackage`. The package may
contain one or many files that together represent the original evidence used to
produce or support the Card.

### Normative rules

1. A source package may contain one photograph, several ordered photographs, a
   PDF, or a combination of source files.
2. Several photographs of a long receipt or invoice are parts of one logical
   source package, not separate invoices.
3. Cabinet produces one confirmed Invoice Card from the complete working source
   package.
4. Cabinet Backend preserves the declared file identities and display order.
5. The package is complete only when all expected parts are available and verified
   locally, except parts explicitly declared as not stored by the Card contract.
6. Missing one expected part makes the source package incomplete without deleting
   or invalidating the accepted Card.
7. Additional supporting originals may be attached later, including a PDF found
   after photographs were synchronized.
8. A late attachment records actor, time, origin, filename, media type, calculated
   hash, and whether it fills an expected missing part or adds supplementary
   evidence.
9. Adding source bytes never rewrites the immutable accepted Invoice Card.
10. If source metadata inside the Card must change, Cabinet must produce a new
    confirmed Card revision.

### Required tests

1. Three ordered photographs can form one complete source package.
2. Absence of one declared photograph produces an incomplete package.
3. Adding the missing verified photograph completes the package.
4. Adding a later PDF preserves the original photographs and provenance.
5. Repeating an identical attachment does not create a duplicate binary record.

---

# E. Registry project validation and local decisions

## Accepted decision E1 — a closed Registry project does not invalidate an invoice

An invoice may legitimately be issued, received, corrected, refunded, or processed
after the related project has been closed in Registry.

### Normative rules

1. A confirmed Invoice Card referencing an existing but closed Registry project is
   eligible for normal archival acceptance.
2. `project_closed` is contextual information, not a Card validation failure.
3. Backend preserves the project status observed at validation time.
4. The closed status may be shown as a warning or used by downstream policies, but
   it must not erase the Card's original object context.
5. Late invoices, final invoices, refunds, corrections, and additional charges may
   remain linked to a closed project.
6. Any separate restriction on Holded publication or project reporting must be
   specified explicitly and must not be inferred merely from project closure.

### Required tests

1. A valid confirmed Card for a closed existing project is accepted.
2. The validation record preserves `project_closed` context.
3. The Card's object block remains unchanged.
4. Existing project-linked history remains queryable after closure.

---

## Accepted decision E2 — missing or unresolved project assignment requires review, not data loss

A confirmed Invoice Card may arrive with no usable Registry project assignment or
with a project identifier that cannot currently be resolved. This may occur when
an invoice is created between projects, before a project exists in Registry, or
with stale or incorrect context.

### Normative rules

1. Failure to resolve a project does not discard the Card or its source package.
2. Backend accepts the invoice into the durable archive when all independent Card
   and source acceptance requirements are satisfied.
3. The project assignment state becomes `unresolved` or `needs_review`.
4. The invoice is excluded from project-specific analytics until a project
   assignment decision is confirmed.
5. The invoice is not automatically published to Holded while the required
   project assignment remains unresolved.
6. A later project assignment may reference an existing Registry project or a
   project created after the invoice was accepted.
7. No arbitrary project is created automatically to satisfy the missing link.
8. The original object context from the Card is always preserved for audit.

### Required tests

1. A Card with no resolved project is preserved and marked for review.
2. Its source evidence remains accessible.
3. It does not enter project-specific analysis before resolution.
4. It does not become Holded-eligible solely through archival acceptance.
5. A later explicit assignment makes it eligible for the downstream operations
   whose other requirements are satisfied.

---

## Accepted decision E3 — Backend project assignment decisions do not edit Invoice Card

A local project reassignment or resolution is Backend-owned operational evidence.
It does not modify the immutable Invoice Card payload received from Cabinet.

### Normative rules

1. Cabinet Backend never edits the stored Card `object` block.
2. A local assignment decision references:
   - the exact Invoice Card revision;
   - the selected Registry `project_id`;
   - the previous unresolved or conflicting context;
   - the deciding actor;
   - decision time;
   - reason or evidence.
3. Replacing a local assignment creates a new auditable decision or supersedes the
   previous decision explicitly; history is not overwritten silently.
4. The effective Backend assignment may be used for local analytics and eligible
   integrations while the original Card remains unchanged.
5. If Cabinet later issues a new confirmed Card revision with corrected object
   data, Backend stores that revision normally and reconciles the separate local
   decision without rewriting either history.
6. Backend must not synthesize and publish a modified Card revision on Cabinet's
   behalf.

### Formal invariant

```text
stored_card_payload_after_acceptance = stored_card_payload_at_acceptance
```

Backend-owned decisions may change effective operational interpretation but not
Card bytes or content hash.

### Required tests

1. Adding a local project assignment leaves the Card payload and content hash
   unchanged.
2. Changing an assignment preserves the previous decision history.
3. A later corrected Cabinet revision is stored as a new revision.
4. Removing a local decision restores unresolved interpretation without mutating
   the Card.

---

# F. Open integration dependency recorded by these decisions

## PresuPro estimate lineage

The Backend baseline requires immutable estimate snapshots but does not yet assume
how PresuPro identifies successive estimates.

The following remain open until PresuPro is inspected or extended:

- whether PresuPro exposes estimate versions;
- whether successive estimates share an `estimate_family_id`;
- whether a new estimate references its predecessor;
- whether replacement and independent additional estimates are distinguishable.

This is an explicit integration dependency, not a placeholder implementation.
Backend remains correct by treating every accepted snapshot as independently
immutable until a stronger PresuPro contract is accepted.
