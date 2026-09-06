# State 1 — Canonical read observations and source-set integration

D0-012 distinguishes product source membership from operational file custody.
The current read boundary is Cabinet_web; Cabinet Flow is not yet deployed.
These models close that boundary before runtime contracts are propagated.

## Model M181 — CanonicalSourceFile

### Meaning

One immutable original file in the accepted ordered source observation. The ordinal describes retained file order, never a page number.

Candidate fields:

- `ordinal: int`;
- `content_id: str`;
- `content_sha256: str`;
- `size_bytes: int`;
- `media_type: str`;
- `display_filename: str`;

### Identity

value

### Identity evidence

Equal ordinal, byte identity and provenance can substitute within the same source observation. Different bytes or ordering make another value; no file lifecycle is implied.

### Source of truth

The current Cabinet_web association audit and independently verified immutable original bytes.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in immutable source observations; retained with issued transfer evidence.

### Open questions

None for identity closure.

## Model M182 — CanonicalSourceSetObservation

### Meaning

The exact original-file membership observed for one canonical Invoice revision and its existing logical source. An empty observation exposes missing membership and is not successful complete custody.

Candidate fields:

- `card_id: str`;
- `source_id: str`;
- `card_content_hash: str`;
- `association_audit_sha256: str`;
- `files: tuple[CanonicalSourceFile, ...]`;

### Identity

value

### Identity evidence

Equal Card/source/revision, association evidence and ordered file membership are substitutable. A membership or revision change produces another observation; this value never allocates source identity.

### Source of truth

The single canonical capability owner under D0-008; currently the pinned Cabinet_web repository and its accepted association artifacts.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Retained immutably wherever custody or a delivery obligation references the observation.

### Open questions

None for identity closure.

## Model M183 — CanonicalInvoiceObservation

### Meaning

One lossless read observation of the current canonical Invoice, its original-source set and unchanged legacy capture evidence. It is not a new Card revision or a delivery acceptance.

Candidate fields:

- `card_id: str`;
- `card_raw_sha256: str`;
- `card_content_hash: str`;
- `card: InvoiceCardV1`;
- `source_set: CanonicalSourceSetObservation`;
- `source_set_hash: str`;
- `capture_raw_sha256: str | None`;
- `capture_state: str`;
- `document_completeness: str`;

### Identity

value

### Identity evidence

Equal origin content, original-set observation and capture observation are substitutable. Any changed evidence produces another observation rather than rewriting the referenced product Card.

### Source of truth

The pinned read-only canonical snapshot, checked against its configured origin and expected digest; a caller-supplied digest alone is not authority.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Immutable external read artifact, with original Card and capture bytes retained by their exact raw hashes.

### Open questions

None for identity closure.

## Model M184 — CanonicalInvoiceSnapshot

### Meaning

The complete bounded Invoice inventory read from one explicitly trusted Cabinet_web Git revision. It carries canonical input facts, never a custody or transfer receipt.

Candidate fields:

- `schema_version: str`;
- `repository_commit: str`;
- `association_audit_sha256: str`;
- `invoice_schema_sha256: str`;
- `unassociated_original_count: int`;
- `invoices: tuple[CanonicalInvoiceObservation, ...]`;

### Identity

value

### Identity evidence

Equal pinned origin, audit and complete ordered observations are substitutable. New input creates another immutable snapshot; no independent product lifecycle or writer is introduced.

### Source of truth

An operator-pinned repository revision and the deterministic legacy snapshot schema/emitter. Its trust configuration is outside request data.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Retained in a protected immutable input store for all admissions and issuances that reference it; no product master moves to PostgreSQL.

### Open questions

None for identity closure.

## Model M185 — SourceSetCustodyRecord

### Meaning

One operational working-custody obligation for an exact accepted source-set observation. It supplements the legacy single-file M14 and does not redefine the Card source.

Candidate fields:

- `card_id: str`;
- `source_id: str`;
- `source_set_hash: str`;
- `canonical_snapshot_sha256: str`;
- `canonical_repository_commit: str`;
- `contents: tuple[SourceContentReference, ...]`;
- `custody_status: str`;
- `accepted_at: datetime | None`;
- `rejected_at: datetime | None`;
- `released_at: datetime | None`;
- `rejection_reason: str | None`;
- `actor: ActorReference`;

### Identity

entity

### Identity evidence

Different Card/source-set obligations are not substitutable even if some bytes are deduplicated. The pair (card_id, source_set_hash) remains identifiable from pending verification through stored custody and explicit release.

### Source of truth

This service owns only byte verification, publication and retention evidence. The referenced canonical observation owns logical source membership.

### Lifecycle candidate

Only the operational transitions described in Meaning preserve this entity; immutable issued evidence is never rewritten.

### Persistence candidate

Operational PostgreSQL record plus protected verified working bytes; retained through exact delivery, retry and release obligations.

### Open questions

None for identity closure.

## Model M186 — RegisterCanonicalSourceSetCommand

### Meaning

An authorized request to verify and register working originals for one existing canonical revision, including a confirmed Invoice. It cannot edit Card metadata or capture proof.

Candidate fields:

- `invoice_id: str`;
- `expected_card_content_hash: str`;
- `source_set_hash: str`;
- `canonical_snapshot_sha256: str`;
- `effect_id: str`;
- `actor: ActorReference`;

### Identity

value

### Identity evidence

Equal exact target, input observation and effect scope are substitutable. A changed input is another command; effect-id conflict is owned by the journal, not mutable command state.

### Source of truth

An authenticated operator selects the configured trusted snapshot and exact canonical target; the service resolves all Card and file facts from that source.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Immutable request evidence while its idempotency and custody obligations remain open.

### Open questions

None for identity closure.

## Model M187 — SourceSetRegistrationResult

### Meaning

The exact committed custody outcome of source registration, with truthful replay information. Rejection before a record exists is an explicit error, not an empty success.

Candidate fields:

- `custody: SourceSetCustodyRecord`;
- `replayed: bool`;

### Identity

value

### Identity evidence

Equal retained custody outcome and replay fact are substitutable. Later custody transitions produce another result observation; this value has no lifecycle.

### Source of truth

The committed source-custody transition and effect journal.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Returned observation; the custody record and effect journal retain durable truth.

### Open questions

None for identity closure.

## Model M188 — AdmitCanonicalInvoiceCommand

### Meaning

An authorized request to make an already canonical Invoice revision visible as ready or pending integration work, independently of Card confirmation.

Candidate fields:

- `invoice_id: str`;
- `expected_card_content_hash: str`;
- `source_set_hash: str`;
- `canonical_snapshot_sha256: str`;
- `effect_id: str`;
- `actor: ActorReference`;

### Identity

value

### Identity evidence

Equal exact canonical target and effect request are substitutable. Different content is another command and cannot reuse a prior idempotency identity.

### Source of truth

The authenticated operator and configured canonical read boundary. The command cannot supply a replacement Card or fabricate source/capture evidence.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Immutable request evidence retained for exact idempotent admission and replay.

### Open questions

None for identity closure.

## Model M189 — CanonicalInvoiceAdmissionRecord

### Meaning

One continuing operational admission obligation for a canonical Invoice revision and exact original set. It is visible while custody or capture prerequisites are missing, and pins an immutable manifest once ready.

Candidate fields:

- `invoice_id: str`;
- `revision: CardRevisionReference`;
- `source_set_hash: str`;
- `canonical_snapshot_sha256: str`;
- `canonical_repository_commit: str`;
- `capture_raw_sha256: str | None`;
- `status: str`;
- `manifest_id: str | None`;
- `manifest_hash: str | None`;
- `pending_reasons: tuple[str, ...]`;
- `actor: ActorReference`;
- `created_at: datetime`;
- `updated_at: datetime`;

### Identity

entity

### Identity evidence

Distinct Invoice/revision/source-set obligations are not interchangeable. The pair (invoice_id, source_set_hash) retains continuity as exact missing prerequisites are resolved; an issued manifest and its receipt are never rewritten.

### Source of truth

The integration admission operation owns readiness and delivery evidence only. Canonical Card content and source membership remain with the current product capability owner.

### Lifecycle candidate

Only the operational transitions described in Meaning preserve this entity; immutable issued evidence is never rewritten.

### Persistence candidate

Operational PostgreSQL admission record. It references immutable canonical input rather than storing an authoritative product Card.

### Open questions

None for identity closure.

## Model M190 — CanonicalInvoiceAdmissionResult

### Meaning

The exact committed pending or ready admission observation and its replay outcome. Pending admission is not an archive receipt or a hidden omission from discovery.

Candidate fields:

- `admission: CanonicalInvoiceAdmissionRecord`;
- `replayed: bool`;

### Identity

value

### Identity evidence

Equal admission observation and replay fact are substitutable. A later operational transition produces another result rather than mutating this value.

### Source of truth

The committed admission transition and effect journal.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Returned observation; the admission record and effect journal own durable state.

### Open questions

None for identity closure.

## Model M191 — SourceSetFileRetrievalRequest

### Meaning

An exact immutable original selection inside one registered Card/source set. It never selects the first image implicitly or grants access merely through content knowledge.

Candidate fields:

- `card_id: str`;
- `source_id: str`;
- `source_set_hash: str`;
- `content_hash: str`;

### Identity

value

### Identity evidence

Equal Card/source/set/file selection is substitutable. A different file or set is another value; access authority is separately enforced.

### Source of truth

The caller selects an existing reference; committed source-set membership and authorization validate the request.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Transient read request; no independent persistence or lifecycle.

### Open questions

None for identity closure.
