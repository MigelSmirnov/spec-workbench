# State 1 — ChatGPT effects and source ingress models

## Model M14 — SourceCustodyRecord

### Meaning

Cabinet Web's durable record that exact original bytes for one CardSource are
pending, stored, rejected, or released from the VPS working set. It does not
replace source identity inside the Card.

Candidate fields:

- owning `card_id` and `source_id`;
- accepted M06 content reference when bytes are stored;
- `custody_status`: `pending_upload`, `stored`, `rejected`, or `released`;
- accepted/rejected/released times optional;
- bounded rejection reason optional;
- actor provenance.

### Identity

entity

### Identity evidence

Substitution: custody obligations for different Card/source pairs are not
interchangeable. Continuity: the same custody record remains the subject while
bytes move from pending to stored and later become eligible for release.

### Source of truth

Cabinet Web's verified byte-ingress and retention evidence; M05 owns logical
source identity.

### Lifecycle candidate

`pending_upload -> stored | rejected`; `stored -> released` only after later
accepted retention policy. Re-upload after rejection remains the same logical
source but produces separately verified content evidence.

### Persistence candidate

Durable while any upload, local-pull, retry, retention, or audit obligation is
open; retained as bounded history after release.

### Open questions

None for identity closure.

## Model M15 — SourceUploadHandoff

### Meaning

One short-lived, narrowly scoped authorization for the human owner to upload
original bytes for an already identified Card/source pair through the
secondary Web surface.

Candidate fields:

- `handoff_id`;
- exact `card_id`, `source_id`, and expected M03 Card revision;
- issuing M02 principal and M01 actor provenance;
- `status`: `issued`, `consumed`, `expired`, or `revoked`;
- issued and expiry times;
- consumed/revoked time optional.

The bearer secret used to present the handoff is protected credential material
and is not stored or returned as a domain field after issuance.

### Identity

entity

### Identity evidence

Substitution: different handoff IDs are distinct single-use authorization
obligations even for the same source. Continuity: one handoff remains the same
entity as it is consumed, expires, or is revoked.

### Source of truth

Cabinet Web's protected upload authorization boundary.

### Lifecycle candidate

`issued -> consumed | expired | revoked` with no reactivation.

### Persistence candidate

Durable or transactionally protected until terminal status; bounded audit
evidence retained without reusable secret material.

### Open questions

None.

## Model M16 — CabinetEffect

### Meaning

One logical state-changing Cabinet Web operation requested through ChatGPT
plugin or the secondary browser, used to preserve idempotent outcome and exact
target revision evidence.

Candidate fields:

- `effect_id` and caller-scoped idempotency identity;
- operation kind from the closed accepted Cabinet capability set;
- authenticated principal and actor provenance;
- exact target identity and expected revision when applicable;
- canonical request content hash;
- `status`: `prepared`, `committed`, `rejected`, or `outcome_unknown`;
- committed result revision or bounded rejection/error evidence optional;
- created and completed times optional.

It is not an arbitrary operation selector or generic payload container.

### Identity

entity

### Identity evidence

Substitution: different effect IDs or idempotency scopes represent distinct
logical write obligations. Continuity: one effect remains identifiable from
preparation through one durable outcome or reconciliation.

### Source of truth

Cabinet Web's effect/idempotency boundary, with the type-specific existing
application operation authoritative for business validation and mutation.

### Lifecycle candidate

`prepared -> committed | rejected | outcome_unknown`; an unknown outcome is
reconciled to the same effect and never blindly recreated.

### Persistence candidate

Durable for every effect whose retry could duplicate or overwrite a logical
change; retained as bounded audit/idempotency evidence.

### Open questions

None.

