# State 2 — Cabinet Backend import and durable-acceptance rules

## Accepted decision A20 — VPS-to-local import and durable acceptance

### Status

Accepted baseline rules for VPS-to-local Invoice Card import.

This document defines invariants, state transitions, rejection and quarantine
semantics, idempotency, and archive visibility. It does not define modules,
public APIs, SQL tables, transport protocols, or implementation algorithms.

### Scope

These rules govern one `InvoiceTransferManifest` containing existing Cabinet
Invoice Card V1 revisions, referenced source binaries, and capture provenance.

They distinguish:

```text
transport delivery
→ local validation
→ quarantine or rejection
→ durable archive acceptance
→ receipt and VPS retention decision
```

---

### Normative rules

The lettered sections below are the normative rules of this decision: core
invariants (A), accepted Card lifecycle policy (B), manifest completeness and
atomic acceptance (C), validation outcomes (D), quarantine rules (E),
duplicate handling (F), state transitions (G), reconciliation and retention
consequences (H), archive visibility and downstream eligibility (I), and the
primary enforcement ownership for later State 3 (J).

### Formal invariants

```text
invoice_id AND content_hash <-> one_accepted_revision
accepted_revision = immutable
same_manifest_replayed -> same_import
business_acceptance = atomic(card, required_sources)
transport_outcome -/> business_acceptance
```

### A. Core invariants

#### A.1 Card identity

1. The Card `id` is the logical invoice identity.
2. Import never replaces that identity with a local ID.
3. The same `invoice_id` and same Card `content_hash` identify the same Card
   revision on every Cabinet node.
4. Two different canonical payloads must not be stored under the same
   `content_hash`.

#### A.2 Immutable accepted revisions

1. A locally stored `StoredInvoiceCardRevision` is immutable.
2. A correction creates another Card revision through accepted Cabinet Card
   operations.
3. Import must preserve every accepted Card payload exactly; it must not
   normalize, enrich, or rewrite the Card during storage.
4. Backend-owned Registry, PresuPro, duplicate, synchronization, and publication
   records remain outside the Card payload.

#### A.3 Source bytes

1. Source bytes are immutable under one binary content hash.
2. A source reference is locally durable only when the required bytes are stored
   and their hash is verified.
3. Metadata-only receipt is not equivalent to durable source acceptance.
4. A corrupt or mismatched binary must never be presented as the Card's verified
   original.

#### A.4 Transport versus acceptance

1. `InvoiceSynchronization.status = delivered` means only that the target
   received the manifest package.
2. Delivery does not imply Card validity, source completeness, duplicate
   resolution, or durable archive acceptance.
3. Only `InvoiceImport.status = accepted` or `already_accepted` permits an
   `accepted` receipt.
4. Quarantined work remains outside normal archive queries, analytics, matching,
   and Holded eligibility.

#### A.5 Idempotency

1. One idempotency key is bound to one exact manifest hash.
2. Reusing the same key with the same manifest resolves to the same logical
   synchronization and import outcome.
3. Reusing the same key with a different manifest is rejected as an idempotency
   conflict.
4. A retry must not create another logical invoice, Card revision, source binary,
   import, or duplicate review for content already known.
5. `already_accepted` is a successful idempotent result, not an error.

---

### B. Accepted Card lifecycle policy

#### B.1 Draft synchronization

Draft Invoice Cards may be transferred and durably archived.

Rationale:

- the VPS must not be the only durable location for valuable daytime work;
- synchronization is backup and archive transfer, not business confirmation;
- Card lifecycle remains governed by Cabinet Card operations.

A locally accepted draft:

- remains `draft`;
- is searchable in the archive with its draft status;
- is excluded from Holded publication;
- is excluded from confirmed actual totals by default;
- may later receive a confirmed Card revision with the same `invoice_id`.

#### B.2 Confirmed and archived Cards

1. Confirmed Cards may be accepted and become eligible inputs for later
   operations, subject to their own rules.
2. Archived Cards and archived revisions remain importable for history and
   reconciliation.
3. Import never changes `draft`, `confirmed`, or `archived` status.

---

### C. Manifest completeness and atomic acceptance

#### C.1 Manifest identity

A manifest is immutable and must identify:

- every included canonical Card payload and content hash;
- every required source ID and expected binary hash;
- sizes and media types needed for verification;
- capture/catalogue provenance included in the transfer;
- manifest format version and manifest hash.

#### C.2 Required source set

For each Card revision, the required source set is derived from its accepted
Invoice Card V1 source metadata and the transfer policy in force when the
manifest is created.

The manifest must explicitly distinguish:

- source bytes included in this package;
- source bytes already known and verified locally;
- source metadata whose Card state explicitly says the file is not stored.

#### C.3 Atomic business acceptance

Local durable acceptance is atomic at the manifest's required-set boundary:

1. all included Card payloads pass contract validation;
2. all mandatory source bytes are either verified in this import or already
   verified locally;
3. all content hashes match;
4. the manifest is internally complete;
5. no unresolved blocking duplicate decision exists;
6. the complete accepted set is committed before the import becomes visible as
   `accepted`.

A partial package may be physically preserved in quarantine, but it must not be
partially committed to the normal archive and reported as accepted.

#### C.4 Card `file_status = not_stored`

A Card revision whose accepted source metadata explicitly states
`file_status = not_stored` may be durably archived without source bytes only when:

- the Card is valid under Invoice Card V1;
- the absence is represented explicitly, not caused by transport loss;
- the import records source availability as `missing` rather than `verified`;
- later binary attachment creates and transfers a new Card revision through the
  accepted `invoice_attach_source` workflow.

Such a Card must not be presented as having a verified original.

---

### D. Validation outcomes

#### D.1 Valid Card

A valid Card may proceed to duplicate review and source verification.

#### D.2 Valid with warnings

A Card with validator warnings may be accepted when the Card already contains the
required acknowledgement evidence defined by Invoice Card V1.

Backend must not invent acknowledgement on import.

#### D.3 Invalid Card

A Card that fails the accepted validator is not accepted into the normal archive.

It is:

- rejected when the failure is final for the received payload; or
- quarantined when validator compatibility, missing package components, or
  operator investigation prevents a safe final decision.

Validation never repairs the payload automatically.

#### D.4 Unsupported Card version

An unsupported `card_version` is quarantined, not silently downgraded or parsed
as V1.

It may later be resolved by adding a compatible validator or by receiving a
supported Card revision.

---

### E. Quarantine rules

#### E.1 Quarantine reasons

The baseline quarantine reasons are:

- `missing_source_bytes`;
- `hash_mismatch`;
- `invalid_card_needs_review`;
- `unsupported_card_version`;
- `incomplete_manifest`;
- `duplicate_review`;
- `idempotency_conflict`;
- `operator_review`.

#### E.2 Quarantine behavior

1. Quarantine preserves received evidence without declaring business acceptance.
2. A quarantined import is not included in normal archive search results unless
   an explicit diagnostic view is requested.
3. It is excluded from matching, analytics, and publication.
4. The VPS retains its authoritative working copy and required source bytes.
5. Resolving quarantine must preserve the original import and resolution
   evidence.
6. Resolution may produce `accepted`, `rejected`, or `discarded`; it must not
   rewrite the original receipt history.

#### E.3 Hash mismatch

A hash mismatch is never repaired by trusting the received bytes or changing the
expected hash.

Resolution requires a new verified transfer or an explicit investigation that
identifies which accepted source is authoritative.

---

### F. Duplicate handling

#### F.1 Exact revision replay

If the local archive already contains the same `invoice_id` and `content_hash`,
import returns `already_accepted` after confirming that required source content
is also present or explicitly absent under the accepted Card state.

#### F.2 Same invoice ID, new revision

A new content hash under an existing `invoice_id` is treated as another Card
revision, not a duplicate invoice, when it is connected to accepted Cabinet
revision history and passes optimistic-concurrency/predecessor checks available
in the manifest.

If the relationship cannot be established safely, the import enters conflict or
quarantine rather than choosing a winner.

#### F.3 Different invoice IDs, possible same real document

Possible duplicate signals may include:

- equal verified source binary hash;
- same supplier tax identity, invoice number, date, and gross/payable amount;
- strong overlap of source and normalized line facts;
- an existing Cabinet duplicate candidate recorded by accepted operations.

These signals create `DuplicateCandidateReview`; they do not automatically merge
or delete Cards.

#### F.4 Blocking duplicate conditions

The baseline blocks normal acceptance only when a verified source binary hash is
already owned by another logical invoice and no accepted explicit decision says
that both Cards intentionally refer to the same source.

Other duplicate signals permit durable archival acceptance but keep an open
review warning. This preserves work while avoiding destructive automatic merge.

#### F.5 Confirmed duplicate resolution

Confirming two Cards as duplicates does not silently merge their histories.
Resolution must identify:

- the retained logical invoice;
- the duplicate Card disposition;
- preserved source and revision references;
- the deciding actor and reason.

Exact merge/archive mechanics belong to a later focused rule set.

---

### G. State transitions

#### G.1 Synchronization

```text
pending
→ transferring
→ delivered
| failed
| cancelled
| unknown_outcome
```

`unknown_outcome` may later reconcile to `delivered`, `failed`, or a settled
receipt result. It is not safe to assume failure.

#### G.2 Import

```text
received
→ validating
→ accepted
| already_accepted
| quarantined
| rejected
```

A quarantined import may later resolve to:

```text
quarantined → accepted | rejected
```

#### G.3 Quarantine

```text
open → resolved | discarded
```

`resolved` requires linked evidence and the resulting import state.

#### G.4 Receipt

Receipt results are immutable observations:

- `accepted`;
- `already_accepted`;
- `quarantined`;
- `rejected`;
- `unknown`.

A later reconciliation creates a superseding receipt rather than editing an
issued receipt in place.

---

### H. Reconciliation and retention consequences

#### H.1 Unknown transport outcome

When the VPS does not know whether delivery or import occurred, it retries using
the same idempotency key and exact manifest hash or asks for reconciliation by
that identity.

It must not generate a new invoice ID or new idempotency key merely because a
response was lost.

#### H.2 VPS deletion eligibility

VPS source bytes and working records are not eligible for retention expiry until
there is durable evidence that:

- the exact required Card revisions were accepted locally;
- all required source bytes were verified locally, or their explicit
  `not_stored` state was accepted;
- the receipt is `accepted` or `already_accepted`;
- no open conflict or quarantine remains for that required set.

Actual retention durations and backup periods remain configurable policy to be
defined separately.

---

### I. Archive visibility and downstream eligibility

#### I.1 Normal archive visibility

Only accepted and already-accepted imports contribute records to normal local
archive queries.

#### I.2 Matching and analytics

- Draft Cards may be archived but do not participate in confirmed actual totals
  by default.
- Only confirmed Card revisions may participate in accepted PresuPro matches and
  complete plan-versus-actual analysis.
- Quarantined, rejected, and conflict-blocked content is excluded.

#### I.3 Holded

Only an exact locally accepted and confirmed Card revision may become a candidate
for Holded publication. Import acceptance alone does not grant publication
eligibility.

---

### J. Primary enforcement ownership for later State 3

State 3 must assign one primary enforcement owner for each invariant group:

- canonical Card revision and archive integrity;
- source-byte durability and verification;
- import acceptance and quarantine;
- idempotency and receipt reconciliation;
- duplicate decision policy.

These groups may be hidden inside one deep durable-acceptance responsibility.
They must not be split into endpoint-sized forwarding modules merely because the
state machine has several records.

---

### Required tests

1. Replaying the same idempotency key with the same manifest returns the same
   [witness: verification:witness_A20]
   logical outcome and creates no duplicate records.
2. Reusing an idempotency key with a different manifest is rejected as an
   idempotency conflict.
3. An incomplete manifest or a missing mandatory source is quarantined without
   partially exposing the package as accepted archive content.
4. A source hash mismatch is quarantined and is not repaired by changing the
   expected hash or trusting the received bytes.
5. An unsupported Card version is quarantined without being downgraded or parsed
   as Invoice Card V1.
6. Replaying an already accepted Card revision with its required source content
   returns `already_accepted`.
7. A safely related new content hash under an existing `invoice_id` creates a new
   immutable Card revision; an unsafe or unproven relationship enters conflict or
   quarantine.
8. A verified source binary already owned by another logical invoice blocks
   normal acceptance until an explicit duplicate decision exists.
9. Quarantined content is excluded from normal archive queries, matching,
   analytics, and publication.
10. An accepted receipt is issued only after atomic durable acceptance of the
    complete required set.
11. An unknown transport outcome is reconciled using the same idempotency key and
    exact manifest hash rather than a new invoice identity.
12. VPS source bytes remain ineligible for retention release until the exact Card
    revisions and required sources have durable accepted evidence and no blocking
    quarantine remains.

### Consequence

Import is a deterministic, idempotent, and atomic acceptance boundary: the
archive holds exactly what Cabinet published, quarantine absorbs everything
questionable without loss, and downstream eligibility flows only from durable
verified custody.

### K. Remaining import-policy questions

The following remain open for later State 2 documents:

1. exact VPS retention and backup durations;
2. whether draft Cards appear in ordinary user search by default or only with a
   status filter;
3. exact duplicate scoring beyond verified binary equality;
4. explicit merge/archive workflow after confirmed duplicate resolution;
5. authorization for quarantine and duplicate decisions;
6. compatibility window for future Invoice Card versions;
7. batch manifests containing several logical invoices, if later required.
