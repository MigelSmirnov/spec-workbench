# State 1 — Cabinet Backend domain models

## Status

Working domain-model baseline for the accepted Cabinet Backend operating cycle.

This state defines Backend-owned concepts, identities, ownership, lifecycle
vocabulary, and relationships. It does not redefine the already implemented
Cabinet Invoice Card V1 contract. It also does not define APIs, SQL tables, ORM
mappings, transport payloads, retry algorithms, or deployment products.

## State 1 boundary

Cabinet Backend must:

1. accept and preserve an existing Invoice Card V1 without changing its meaning;
2. store every accepted Card content revision and its original source bytes;
3. publish a versioned Registry project catalogue to the VPS for offline use;
4. retain evidence of which catalogue was used when an object was selected;
5. import daytime VPS work into the local durable archive idempotently;
6. distinguish received, validated, quarantined, and durably accepted work;
7. validate the selected Registry project after reconnection without erasing the
   user's original Card context;
8. keep PresuPro matching, analytics, synchronization state, duplicate review,
   and Holded publication outside immutable Invoice Card facts.

---

# A. Accepted Invoice Card boundary

## Model M01 — InvoiceCardV1

Invoice Card V1 is an existing Cabinet contract. Backend consumes the complete
canonical Card JSON and validates it using the accepted Cabinet validator or a
contract-compatible implementation.

The Card already owns:

- stable `id`;
- `card_type` and `card_version`;
- lifecycle `status` — `draft`, `confirmed`, or `archived`;
- invoice number and dates;
- supplier and buyer facts;
- currency, lines, totals, and payment transactions;
- required primary `object` block;
- source metadata;
- provenance;
- canonical SHA-256 content revision.

Backend must preserve unknown or currently unused Card fields. It must not
introduce alternative line kinds, payment meanings, arithmetic rules, object
shape, source shape, or invoice revision numbering.

### Meaning

The accepted Cabinet invoice contract consumed and preserved by Backend.

### Identity

entity

### Identity evidence

Substitution: two Cards with equal visible fields are not interchangeable when their stable Card id or canonical revision differs. Continuity: one Card keeps its id while accepted content revisions and lifecycle status change.

### Source of truth

The accepted Cabinet Invoice Card V1 contract; Backend is a preserving consumer.

### Lifecycle

draft -> confirmed -> archived under the Cabinet contract; corrections create content revisions.

### Persistence candidate

Durable complete Card revisions on the nodes required by the operating cycle.

### Open questions

None for identity closure.

## Model M02 — InvoiceCardRevisionReference

Value object pinning one exact accepted Card payload.

Candidate fields:

- `invoice_id`;
- `card_version`;
- `content_hash`;
- `observed_status`;
- `observed_at`.

`content_hash` is the Card revision identity already defined by Cabinet.

---

### Meaning

A pin to one exact accepted Invoice Card payload.

### Identity

value

### Identity evidence

Substitution: equal invoice id, contract version, content hash, status, and observation values are interchangeable. Continuity: the reference does not change; a different revision produces another value.

### Source of truth

Derived from one accepted Invoice Card revision.

### Lifecycle

No independent lifecycle; created as an immutable reference.

### Persistence candidate

Embedded wherever an exact Card revision must be pinned.

### Open questions

None for identity closure.

# B. Shared Backend primitives

## Model M03 — ActorReference

Provenance value object.

Candidate fields:

- `actor_type` — `user`, `agent`, `service`, `import`, or `system`;
- `actor_id`;
- `delegated_by` optional;
- `interaction_id` optional;
- `display_label` optional.

It is not an authentication session.

### Meaning

Provenance identifying the actor context for an action.

### Identity

value

### Identity evidence

Substitution: equal actor and delegation facts carry the same provenance meaning. Continuity: authentication or actor state is not managed through this reference.

### Source of truth

The authenticated or delegated interaction that produced the action.

### Lifecycle

No independent lifecycle.

### Persistence candidate

Embedded in durable evidence records when provenance is required.

### Open questions

None for identity closure.

### Security semantics

`ActorReference` is embedded provenance scoped to the current Cabinet
deployment. It may cross synchronization and audit boundaries, but it is not an
authentication session, reusable credential, or authorization proof. Actor and
delegation identifiers are sensitive audit data; the value contains no secret.

## Model M04 — CabinetNodeIdentity

Identity of one participating Cabinet node.

Candidate fields:

- `node_id`;
- `node_kind` — `vps_cabinet` or `local_backend`;
- `status` — `active` or `revoked`;
- `contract_version`;
- `created_at`;
- `revoked_at` optional.

### Meaning

One participating VPS Cabinet or local Backend node.

### Identity

entity

### Identity evidence

Substitution: records for different node ids are never interchangeable. Continuity: the same node remains identifiable while status and contract version change.

### Source of truth

Cabinet Backend node enrollment and revocation records.

### Lifecycle

active -> revoked.

### Persistence candidate

Durable on the Cabinet systems that authenticate or exchange with the node.

### Open questions

None for identity closure.

### Security semantics

`CabinetNodeIdentity` is externally addressable at the synchronization boundary
and scopes one installation. Its stable node identity selects the installation
subject but authorizes nothing without the separate active credential accepted
by A61. Credential material is not a field of this entity and must not cross in
business payloads.

## Model M05 — ContentReference

Value object referencing immutable content.

Candidate fields:

- `content_kind`;
- `content_id`;
- `content_hash`;
- `size_bytes` optional;
- `media_type` optional.

---

### Meaning

A typed reference to immutable content bytes.

### Identity

value

### Identity evidence

Substitution: equal kind, id, hash, size, and media type identify the same immutable content. Continuity: content changes create another reference rather than mutating this value.

### Source of truth

Derived from the referenced immutable content.

### Lifecycle

No independent lifecycle.

### Persistence candidate

Embedded in manifests, records, and evidence that pin content.

### Open questions

None for identity closure.


### Security semantics

`ContentReference` may cross manifest and audit boundaries and pins exact immutable bytes. Its ID, hash, size, and media type identify data but are not authorization proof and grant no path or retrieval authority. It contains no secret.

# C. Accepted Card archive

## Model M06 — StoredInvoiceCard

Local archive identity for one logical Invoice Card.

Candidate fields:

- `invoice_id` — equal to Card `id`;
- `card_version`;
- `current_content_hash`;
- `current_status`;
- `first_received_at`;
- `last_received_at`;
- `durable_at` optional;
- `archive_status` — `active` or `archived`.

### Meaning

The local archive root for one logical Invoice Card.

### Identity

entity

### Identity evidence

Substitution: equal current fields do not make two invoice ids interchangeable. Continuity: one invoice id remains the same archive root across revisions, receipt times, durability, and archive status.

### Source of truth

Card id supplies identity; Cabinet Backend owns the archive record.

### Lifecycle

received -> durable; active -> archived, with immutable revisions retained.

### Persistence candidate

Durable in the local archive.

### Open questions

None for identity closure.

### Security semantics

`StoredInvoiceCard` is a sensitive fiscal entity in the current Cabinet owner
scope. Its stable `invoice_id` is the exact object-level authorization target,
not proof that a caller may read or mutate it. Revisions and references may cross
the VPS/local boundary only through authenticated Cabinet operations.

## Model M07 — StoredInvoiceCardRevision

Immutable storage record for one exact canonical Card JSON payload.

Candidate fields:

- exact Card revision reference;
- complete canonical Card payload;
- `received_at`;
- `received_from_node_id`;
- `received_by`;
- validation record reference;
- predecessor content hash optional;
- superseded-by content hash optional.

A later Cabinet correction is another Card content revision. Backend does not
split it into a competing invoice-facts schema.

### Meaning

The immutable archive record for one exact canonical Card payload.

### Identity

entity

### Identity evidence

Substitution: records with different invoice id or content hash are distinct even if projected fields match. Continuity: the issued revision keeps stable identity and is linked into predecessor and supersession history without mutation.

### Source of truth

The accepted Card id plus canonical content revision; Backend owns archival evidence.

### Lifecycle

Issued immutable snapshot; may gain external predecessor/supersession links without rewriting payload facts.

### Persistence candidate

Durable in the Card archive.

### Open questions

None for identity closure.

## Model M08 — InvoiceCardValidationRecord

Deterministic validation evidence.

Candidate fields:

- `validation_id`;
- exact Card revision reference;
- validator contract and version;
- `result` — `valid`, `valid_with_warnings`, or `invalid`;
- error codes;
- warning codes;
- acknowledgement evidence optional;
- `validated_at`.

Validation never silently rewrites the Card.

### Meaning

Deterministic evidence of validating one exact Card revision.

### Identity

entity

### Identity evidence

Substitution: validation runs with different validation ids, validator versions, or acknowledgement evidence are not interchangeable. Continuity: one validation record keeps stable identity while its issued result remains immutable.

### Source of truth

Cabinet Backend validation operation over the accepted Card contract.

### Lifecycle

Issued once with valid, valid_with_warnings, or invalid result.

### Persistence candidate

Durable validation history.

### Open questions

None for identity closure.

## Model M09 — DuplicateCandidateReview

Review record for possible duplicate logical invoices.

Candidate fields:

- `review_id`;
- incoming Card revision reference;
- candidate invoice IDs and revision hashes;
- matching reasons and evidence;
- `status` — `open`, `not_duplicate`, `confirmed_duplicate`, or `resolved`;
- decision actor and time optional;
- resolution reference optional.

Duplicate candidates are not automatically merged.

---

### Meaning

A human-reviewable case for a possible duplicate logical invoice.

### Identity

entity

### Identity evidence

Substitution: two review ids remain distinct cases even with equal candidates. Continuity: the same review moves from open to a recorded decision or resolution.

### Source of truth

Cabinet Backend duplicate-review workflow.

### Lifecycle

open -> not_duplicate | confirmed_duplicate | resolved.

### Persistence candidate

Durable review and decision history.

### Open questions

None for identity closure.

# D. Source binary archive

## Model M10 — SourceBinary

Immutable binary object corresponding to source metadata in an Invoice Card.

Candidate fields:

- `source_id` — from Card `source.source_id`;
- owning `invoice_id`;
- source kind from the Card;
- binary content hash;
- media type;
- size bytes;
- original filename optional;
- first received time;
- `byte_status` — `available`, `missing`, `quarantined`, `corrupt`, or `deleted`.

The Card remains authoritative for accepted source metadata. `SourceBinary`
records byte handling and verification.

### Meaning

The immutable source-byte object named by Invoice Card source metadata.

### Identity

entity

### Identity evidence

Substitution: source ids are not interchangeable even when bytes happen to hash equally. Continuity: one source id remains identifiable while byte availability and retention status change.

### Source of truth

Invoice Card owns accepted source metadata; Backend owns byte custody state.

### Lifecycle

available | missing | quarantined | corrupt -> deleted when policy permits.

### Persistence candidate

Durable wherever the operating cycle requires source-byte custody.

### Open questions

None for identity closure.

### Security semantics

`SourceBinary` contains sensitive documentary evidence in the current Cabinet
owner scope. Its stable source identity is externally addressable only through
authorized Cabinet file operations. Filename and media metadata never grant path
or execution authority; verified bytes may cross the VPS/local boundary through
the accepted transfer workflow.

## Model M11 — SourceBinaryReplica

Storage record for one binary on one Cabinet node.

Candidate fields:

- `source_id`;
- `node_id`;
- `storage_zone` — `vps_working` or `local_durable`;
- storage reference;
- stored hash;
- verification status — `pending`, `verified`, or `failed`;
- stored time;
- retention deadline optional;
- deletion time optional.

A Card may temporarily reference a source whose bytes are not yet available.
That condition is explicit and is not equivalent to durable local acceptance.

---

### Meaning

The custody record for one source binary on one Cabinet node and storage zone.

### Identity

entity

### Identity evidence

Substitution: replicas on different nodes or zones are operationally distinct. Continuity: one replica identity persists while verification, retention, and deletion state change.

### Source of truth

Cabinet Backend storage custody for the source, node, and zone tuple.

### Lifecycle

pending -> verified | failed; retained -> deleted when policy permits.

### Persistence candidate

Durable replica metadata; referenced bytes live in the named storage zone.

### Open questions

None for identity closure.


### Security semantics

`SourceBinaryReplica` is custody metadata scoped to an exact source, Cabinet node, and storage zone. Its storage reference is Backend-internal and must not become a client path or URL. Replica identity and status do not authorize byte retrieval.

# E. Registry catalogue and offline object work

## Model M12 — RegistryProjectSnapshot

Immutable projection of one Registry project.

Candidate fields:

- `snapshot_id`;
- `project_id`;
- display name;
- address or compact context;
- Registry status;
- customer reference optional;
- Registry version or content hash;
- Registry timestamps;
- `captured_at`;
- source contract version.

Registry remains authoritative for project identity and current context.

### Meaning

An immutable issued projection of one externally identified Registry project.

### Identity

entity

### Identity evidence

Substitution: equal projected fields do not make snapshots with different ids or Registry observations interchangeable. Continuity: the mirrored project keeps Registry project identity; each issued observation has snapshot semantics.

### Source of truth

Registry owns project identity and current facts; Backend owns the issued snapshot record.

### Lifecycle

Issued immutable snapshot; a later Registry observation creates another snapshot.

### Persistence candidate

Durable when used in catalogues, assignments, validation, or historical evidence.

### Open questions

None for identity closure.

## Model M13 — RegistryCatalogueSnapshot

Immutable compact project catalogue prepared for offline VPS use.

Candidate fields:

- `catalogue_id`;
- `generated_at`;
- `generated_by_node_id`;
- Registry observation time;
- Registry contract version;
- catalogue content hash;
- included project snapshot references;
- project count;
- completeness or filter description optional.

The catalogue exposes its age. It is usable offline but never claims Registry is
currently reachable.

### Meaning

An immutable compact Registry project catalogue issued for offline VPS use.

### Identity

entity

### Identity evidence

Substitution: catalogue ids, content hashes, and observation times distinguish releases even with overlapping projects. Continuity: one issued catalogue remains fixed; regeneration creates another catalogue entity.

### Source of truth

Cabinet Backend generates the catalogue from Registry observations.

### Lifecycle

generated -> available -> expired by later policy; never mutated in place.

### Persistence candidate

Durable on local archive and cached on VPS through replica records.

### Open questions

None for identity closure.

## Model M14 — RegistryCataloguePublication

Backend record of publishing one catalogue snapshot from local to VPS.

Candidate fields:

- `publication_id`;
- `catalogue_id`;
- source and target node IDs;
- idempotency key;
- `status` — `pending`, `transferring`, `accepted`, `failed`, or
  `unknown_outcome`;
- requested, completed, and acknowledged times;
- safe error code optional.

### Meaning

The business record of publishing one catalogue snapshot to a target node.

### Identity

entity

### Identity evidence

Substitution: publication ids and idempotency keys distinguish publication obligations. Continuity: the same publication progresses through transfer and outcome states.

### Source of truth

Cabinet Backend catalogue publication workflow.

### Lifecycle

pending -> transferring -> accepted | failed | unknown_outcome.

### Persistence candidate

Durable publication and reconciliation history.

### Open questions

None for identity closure.

## Model M15 — RegistryCatalogueReplica

Record that one exact catalogue snapshot is available on one Cabinet node.

Candidate fields:

- `catalogue_id`;
- `node_id`;
- `stored_at`;
- verification status;
- expiry time optional.

### Meaning

The availability record for one exact catalogue on one Cabinet node.

### Identity

entity

### Identity evidence

Substitution: replicas on different nodes are not interchangeable. Continuity: the same catalogue-node record persists through verification and expiry state.

### Source of truth

Cabinet Backend custody evidence for the catalogue and node tuple.

### Lifecycle

stored -> verified or failed; may expire.

### Persistence candidate

Durable replica metadata on the systems that track catalogue availability.

### Open questions

None for identity closure.

## Model M16 — WorkObject

Cabinet working projection for one Registry project.

```text
WorkObject.id = Registry ProjectRecord.id
```

Candidate fields:

- `project_id`;
- current Registry snapshot reference;
- first seen time;
- last seen time;
- Cabinet attention status — `active`, `historical`, or `needs_attention`.

Cabinet owns relationships, invoices, notes, matches, and history linked to the
Registry `project_id`; it does not own Registry name, address, or lifecycle.

### Meaning

Cabinet's working representative of one Registry project.

### Identity

entity

### Identity evidence

Substitution: equal projected fields do not make different Registry project ids interchangeable. Continuity: the same project id anchors Cabinet relationships while snapshots and attention status change.

### Source of truth

Registry owns project identity and current context; Cabinet owns linked work and attention state.

### Lifecycle

active | historical | needs_attention as Registry observations change.

### Persistence candidate

Durable Cabinet relationship root keyed by Registry project id.

### Open questions

None for identity closure.

## Model M17 — CardObjectAssignmentObservation

Backend interpretation of the primary object context already stored in the Card
`object` block.

Candidate fields:

- exact Card revision reference;
- observed `object.card_id` optional;
- observed `object.label` optional;
- catalogue ID used during capture optional;
- Registry project snapshot used during capture optional;
- decision context — `online_current`, `offline_cached`, `label_only`, or
  `unassigned`;
- observed time.

This record adds provenance that Invoice Card V1 does not carry. It does not
replace the Card `object` block.

### Meaning

Backend provenance for the object context observed in one exact Card revision.

### Identity

entity

### Identity evidence

Substitution: observations for different Card revisions or capture contexts are not interchangeable. Continuity: one issued observation remains fixed and is the stable subject of later validations.

### Source of truth

The accepted Card object block plus capture-time Backend catalogue provenance.

### Lifecycle

Issued immutable observation; later Card revisions create new observations.

### Persistence candidate

Durable when assignment provenance is available.

### Open questions

None for identity closure.

## Model M18 — ObjectAssignmentValidation

Post-reconnection validation against current Registry data.

Candidate fields:

- `validation_id`;
- exact Card revision reference;
- observed project ID optional;
- current Registry snapshot reference optional;
- `result` — `valid`, `project_missing`, `project_closed`,
  `materially_changed`, `registry_unavailable`, or `inconclusive`;
- validated time and actor;
- warnings and safe details.

A non-valid result does not erase the original Card context. Changing the object
requires an explicit new Card revision through Cabinet.

---

### Meaning

A post-reconnection validation of one observed Card assignment against Registry.

### Identity

entity

### Identity evidence

Substitution: different validation ids, source observations, or Registry snapshots are distinct evidence. Continuity: one issued validation remains identifiable and immutable.

### Source of truth

Cabinet Backend validation against a current Registry observation.

### Lifecycle

Issued with valid, project_missing, project_closed, materially_changed, registry_unavailable, or inconclusive result.

### Persistence candidate

Durable validation history.

### Open questions

None for identity closure.

# F. VPS-to-local transfer and import

## Model M19 — InvoiceTransferManifest

Immutable description of one exact work package sent by the VPS.

Candidate fields:

- `manifest_id`;
- invoice ID;
- included complete Card payloads and content hashes;
- included source IDs, binary hashes, sizes, and media types;
- included Registry-catalogue provenance records;
- included Backend decision references when applicable;
- canonical manifest version;
- generated time;
- manifest hash.

### Meaning

The immutable issued description of one exact VPS work package.

### Identity

entity

### Identity evidence

Substitution: manifest ids and hashes distinguish packages and retry obligations. Continuity: one issued manifest remains fixed; changed contents require another manifest.

### Source of truth

The sending Cabinet node generates and hashes the canonical manifest.

### Lifecycle

Issued immutable snapshot.

### Persistence candidate

Durable on sender and receiver for transfer and import evidence.

### Open questions

None for identity closure.

### Security semantics

`InvoiceTransferManifest` crosses the VPS/local trust boundary and is addressed
by its stable manifest identity and content hash. It contains sensitive entity
and artifact references but no credential. Knowledge of a manifest id or hash
does not authenticate its sender or authorize an import transition.

## Model M20 — InvoiceSynchronization

Transport process for one manifest.

Candidate fields:

- `synchronization_id`;
- invoice ID;
- source and target node IDs;
- manifest hash;
- `status` — `pending`, `transferring`, `unknown_outcome`, `delivered`,
  `failed`, or `cancelled`;
- idempotency key;
- started and finished times optional;
- safe error code optional.

`delivered` means the target received the package. It does not by itself mean
that the package was validated or committed to the durable archive.

### Meaning

The transport process for one invoice transfer manifest.

### Identity

entity

### Identity evidence

Substitution: synchronization ids remain distinct transport processes even for the same invoice. Continuity: one synchronization keeps identity through transfer, uncertainty, delivery, failure, or cancellation.

### Source of truth

Cabinet Backend synchronization workflow.

### Lifecycle

pending -> transferring -> unknown_outcome | delivered | failed | cancelled.

### Persistence candidate

Durable until outcome and reconciliation obligations are closed; retained as history locally.

### Open questions

None for identity closure.

## Model M21 — InvoiceImport

Local Backend process that validates and commits one delivered manifest.

Candidate fields:

- `import_id`;
- synchronization ID and manifest hash;
- invoice ID;
- `status` — `received`, `validating`, `quarantined`, `accepted`, `rejected`,
  or `already_accepted`;
- received time;
- validation completed time optional;
- durable commit time optional;
- rejection or quarantine reason codes;
- accepted Card hashes;
- accepted source hashes;
- duplicate-review reference optional.

This separation prevents transport success from being mistaken for durable
business acceptance.

### Meaning

The local durable-acceptance process for one delivered manifest.

### Identity

entity

### Identity evidence

Substitution: import ids and idempotent manifest identity distinguish logical imports. Continuity: the same import progresses from receipt through validation to one terminal business result.

### Source of truth

Local Cabinet Backend import workflow.

### Lifecycle

received -> validating -> quarantined | accepted | rejected | already_accepted.

### Persistence candidate

Durable local import history.

### Open questions

None for identity closure.

## Model M22 — ImportQuarantine

Record for a package that arrived but cannot yet be accepted or rejected safely.

Candidate fields:

- `quarantine_id`;
- import ID;
- missing or invalid component references;
- reason — `missing_source_bytes`, `hash_mismatch`, `invalid_card`,
  `unsupported_card_version`, `incomplete_manifest`, `duplicate_review`, or
  `operator_review`;
- opened time;
- status — `open`, `resolved`, or `discarded`;
- resolution evidence optional.

Quarantine preserves the received package without presenting it as part of the
normal durable archive.

### Meaning

The preserved review case for an import that cannot yet be accepted or rejected safely.

### Identity

entity

### Identity evidence

Substitution: different quarantine ids or imports are distinct obligations. Continuity: one quarantine remains identifiable from opening through resolution or discard.

### Source of truth

Local Cabinet Backend import policy and operator evidence.

### Lifecycle

open -> resolved | discarded.

### Persistence candidate

Durable while open and retained with import evidence.

### Open questions

None for identity closure.

## Model M23 — InvoiceTransferReceipt

Durable target evidence returned to the VPS.

Candidate fields:

- synchronization ID;
- import ID optional;
- idempotency key;
- invoice ID;
- manifest hash;
- `result` — `accepted`, `already_accepted`, `quarantined`, `rejected`, or
  `unknown`;
- accepted Card and source hashes;
- receipt time;
- safe error code optional.

A retry with the same idempotency key and manifest must resolve to the same
logical import and must not create a second invoice.

### Meaning

Immutable target evidence of the outcome known for one transfer and import.

### Identity

value

### Identity evidence

Substitution: equal synchronization, import, idempotency, manifest, result, hashes, and time facts carry the same evidence. Continuity: the issued receipt does not mutate; later reconciliation issues another receipt value if the known outcome changes.

### Source of truth

The target Cabinet Backend issues it from durable import state.

### Lifecycle

Issued immutable snapshot.

### Persistence candidate

Durable on target and retained by sender for reconciliation.

### Open questions

None for identity closure.

## Model M24 — InvoiceWorkingReplica

Record describing which exact Card revisions and source bytes are available on
one Cabinet node.

Candidate fields:

- invoice ID;
- node ID;
- accepted Card content hashes;
- current Card hash optional;
- source manifest hash;
- role — `vps_working`, `local_durable`, or `read_only_cache`;
- updated time.

### Meaning

The availability record for exact Card and source content on one Cabinet node.

### Identity

entity

### Identity evidence

Substitution: replicas on different invoice-node pairs are not interchangeable. Continuity: one invoice-node replica remains the same while available revisions, role, and update time change.

### Source of truth

Cabinet Backend custody state for the invoice and node tuple.

### Lifecycle

working or cached availability changes as content transfers or is retained.

### Persistence candidate

Durable replica metadata on participating nodes.

### Open questions

None for identity closure.

## Model M25 — SynchronizationConflict

Exceptional record for incompatible accepted Card revisions or Backend decisions
on two nodes.

Candidate fields:

- `conflict_id`;
- invoice ID;
- affected record type;
- VPS and local references;
- common predecessor optional;
- reason;
- detected time;
- status — `open` or `resolved`;
- explicit resolution evidence optional.

Source bytes are immutable. Conflicts concern Card JSON revisions or
Backend-owned operational decisions.

### Meaning

An exceptional case for incompatible accepted revisions or operational decisions on nodes.

### Identity

entity

### Identity evidence

Substitution: conflict ids represent distinct resolution obligations. Continuity: one conflict remains identifiable from detection until explicit resolution.

### Source of truth

Cabinet Backend conflict detection and resolution evidence.

### Lifecycle

open -> resolved.

### Persistence candidate

Durable conflict and resolution history.

### Open questions

None for identity closure.

## Model M26 — LocalBackendConnectionObservation

VPS-side reachability observation.

Candidate fields:

- `status` — `online`, `offline`, `unauthorized`, `incompatible`, or `unknown`;
- Backend node ID optional;
- contract version optional;
- observed time;
- last success time optional;
- safe error code optional.

---

### Meaning

A VPS-side timestamped observation of local Backend reachability and compatibility.

### Identity

value

### Identity evidence

Substitution: equal status, node, contract, timestamps, and safe error facts are interchangeable. Continuity: the observation itself does not change; another probe creates another value.

### Source of truth

The VPS Cabinet connectivity probe.

### Lifecycle

Issued immutable observation.

### Persistence candidate

Temporary for live decisions; latest and historical observations may be persisted when operational evidence requires it.

### Open questions

None for identity closure.

# G. PresuPro projection and matching

## Model M27 — EstimateReference

Value object containing:

- `estimate_id`;
- `project_id`;
- PresuPro version, content hash, or observed update time;
- PresuPro status optional.

### Meaning

A pin to one externally owned PresuPro estimate observation.

### Identity

value

### Identity evidence

Substitution: equal estimate, project, version or hash, time, and status facts identify the same reference. Continuity: the reference does not own estimate mutation; a changed estimate produces another value.

### Source of truth

PresuPro owns estimate and project identity and status.

### Lifecycle

No independent lifecycle.

### Persistence candidate

Embedded in snapshots, matches, and analysis inputs.

### Open questions

None for identity closure.

## Model M28 — EstimateSnapshot

Immutable local projection used for repeatable analysis.

Candidate fields:

- `snapshot_id`;
- estimate reference;
- currency;
- zones;
- items;
- totals;
- captured time;
- source contract version.

PresuPro remains authoritative for mutable estimate composition.

### Meaning

An immutable issued local projection of one PresuPro estimate for repeatable analysis.

### Identity

entity

### Identity evidence

Substitution: snapshot ids and PresuPro observations distinguish analytical evidence. Continuity: one issued snapshot remains fixed while later estimate changes create another snapshot.

### Source of truth

PresuPro owns estimate composition; Backend owns the issued snapshot record.

### Lifecycle

Issued immutable snapshot.

### Persistence candidate

Durable when used by accepted matches or repeatable analysis.

### Open questions

None for identity closure.

## Model M29 — EstimateItemSnapshot

Read-only comparable projection including stable item identity when available,
zone, type, description, material reference, quantity, unit, unit price, waste,
margin, discount, IVA, and totals.

### Meaning

The immutable comparable projection of one estimate item inside an exact Estimate Snapshot.

### Identity

entity

### Identity evidence

Substitution: externally stable item identity and containing estimate snapshot distinguish items even when commercial fields match. Continuity: the mirrored estimate item keeps its source identity; each issued projection has snapshot semantics.

### Source of truth

PresuPro owns estimate-item identity and facts; Backend owns the issued projection.

### Lifecycle

Issued immutable snapshot within an EstimateSnapshot.

### Persistence candidate

Persisted as part of the containing EstimateSnapshot.

### Open questions

None for identity closure.

## Model M30 — EstimateMatchSuggestion

Ephemeral agent proposal connecting one exact Card line to one exact Estimate
Item Snapshot. It is not analytical truth.

### Meaning

An ephemeral agent proposal connecting one exact Card line to one exact estimate-item snapshot.

### Identity

value

### Identity evidence

Substitution: equal inputs and proposal facts are interchangeable because the suggestion owns no accepted decision or history. Continuity: it is not mutated into truth; acceptance creates an InvoiceLineEstimateMatch entity.

### Source of truth

Calculated by the matching agent from pinned Card and estimate inputs.

### Lifecycle

Ephemeral proposal; accepted or discarded by a separate decision.

### Persistence candidate

Runtime only unless included as provenance in a separate accepted decision record.

### Open questions

None for identity closure.

## Model M31 — InvoiceLineEstimateMatch

Backend-owned decision entity.

Candidate fields:

- `match_id`;
- exact confirmed Card revision and line ID;
- exact estimate snapshot and item reference;
- `status` — `confirmed`, `rejected`, or `invalidated`;
- decided time and actor;
- explanation optional;
- invalidation reason optional.

Baseline cardinality:

- one invoice line has at most one active confirmed estimate-item match;
- one estimate item may have many matched invoice lines;
- splitting one invoice line across several estimate items is deferred.

Card field `matched_material_id` may assist material identification but is not a
confirmed PresuPro Estimate Item match.

---

### Meaning

The Backend-owned decision linking one confirmed Card line to one estimate item snapshot.

### Identity

entity

### Identity evidence

Substitution: match ids are distinct decisions even when endpoints match. Continuity: one match remains identifiable while status changes or it is invalidated.

### Source of truth

Cabinet Backend matching decision and actor evidence.

### Lifecycle

confirmed | rejected; confirmed -> invalidated when accepted policy requires it.

### Persistence candidate

Durable decision history.

### Open questions

None for identity closure.

# H. Analytics

## Model M32 — PlanActualAnalysis

Calculated view assembled from:

- one exact Estimate Snapshot;
- locally accepted confirmed Invoice Card revisions;
- valid or explicitly accepted object assignments;
- confirmed estimate matches;
- explicit forecast assumptions.

It may contain planned amount, actual amount, average actual price, remaining
quantity, variance, unmatched coverage, warnings, and forecasts.

Fresh VPS-only Cards may be searched and discussed, but complete project analysis
requires the local archive and a PresuPro snapshot.

---

### Meaning

A calculated plan-versus-actual view for pinned estimate, Card, assignment, match, and forecast inputs.

### Identity

value

### Identity evidence

Substitution: analyses with equal pinned inputs and calculation assumptions are interchangeable. Continuity: the view has no independent mutation; changed inputs produce a recalculated value.

### Source of truth

Calculated by Cabinet Backend from the named immutable and accepted inputs.

### Lifecycle

Calculated on demand; no independent lifecycle.

### Persistence candidate

Not required as a mutable record; may be cached only with complete input provenance.

### Open questions

None for identity closure.

# I. Holded publication

## Model M33 — HoldedPublication

Business record for publishing one exact confirmed Card revision.

Candidate fields:

- `publication_id`;
- exact Card revision reference;
- idempotency key;
- `status` — `pending`, `succeeded`, `failed`, `ambiguous`, or `cancelled`;
- external document ID optional;
- created and completed times;
- safe outcome details.

### Meaning

The business record for publishing one exact confirmed Card revision to Holded.

### Identity

entity

### Identity evidence

Substitution: publication ids and idempotency keys represent distinct external side-effect obligations. Continuity: one publication remains identifiable through pending and terminal outcomes.

### Source of truth

Cabinet Backend publication workflow; Holded owns the external document outcome.

### Lifecycle

pending -> succeeded | failed | ambiguous | cancelled.

### Persistence candidate

Durable publication and reconciliation history.

### Open questions

None for identity closure.

### Security semantics

`HoldedPublication` is accounting-sensitive evidence owned by Local Cabinet
Backend and crosses the Holded integration boundary. Stable invoice, publication,
and Holded document identities are exact authorization and reconciliation
targets, not authority. Holded credentials remain outside this entity and inside
the dedicated gateway.

## Model M34 — HoldedPublicationAttempt

Technical attempt belonging to one `HoldedPublication`. Retries create attempts,
not new business publications.

Holded publication is independent from PresuPro matching.

---

### Meaning

One technical attempt belonging to a HoldedPublication business record.

### Identity

entity

### Identity evidence

Substitution: retries are distinct attempts even when request facts match. Continuity: one attempt keeps stable identity and one issued outcome; retry creates another attempt.

### Source of truth

Cabinet Backend Holded integration attempt evidence.

### Lifecycle

started -> succeeded | failed | ambiguous as later State 2 policy names the exact states.

### Persistence candidate

Durable as technical evidence under its business publication.

### Open questions

None for identity closure.

# J. Remaining Cabinet Cards

Backend remains the durable core for the wider Cabinet product direction:

- `ProviderCard`;
- `ContactCard`;
- `MaterialListCard` and `MaterialListItem`;
- `DocumentCard`;
- project-linked notes and relationships.

Their shapes belong to their accepted Cabinet Card specifications. Backend State
1 must not invent replacement schemas for them.

---

# K. Relationship map

```text
Registry Project 1 -> 0..* RegistryProjectSnapshots
RegistryCatalogueSnapshot 1 -> 0..* RegistryProjectSnapshots
RegistryCatalogueSnapshot 1 -> 0..* CataloguePublications and Replicas

StoredInvoiceCard 1 -> 1..* StoredInvoiceCardRevisions
StoredInvoiceCardRevision 1 -> 0..* ValidationRecords
StoredInvoiceCard 1 -> 0..* DuplicateCandidateReviews
StoredInvoiceCard 1 -> 0..* SourceBinaries
SourceBinary 1 -> 1..* SourceBinaryReplicas
StoredInvoiceCardRevision 1 -> 0..1 CardObjectAssignmentObservation
CardObjectAssignmentObservation 1 -> 0..* ObjectAssignmentValidations

InvoiceTransferManifest 1 -> 1 InvoiceSynchronization
InvoiceSynchronization 1 -> 0..1 InvoiceImport
InvoiceImport 1 -> 0..1 ImportQuarantine
InvoiceImport 1 -> 1 InvoiceTransferReceipt

Invoice Card Line 1 -> 0..1 active confirmed EstimateMatch
Estimate Item 1 -> 0..* matched Invoice Card Lines
StoredInvoiceCard 1 -> 0..* HoldedPublications
```

---

# L. Persisted versus calculated

Persisted on VPS for the working set:

- accepted Invoice Card JSON revisions;
- source binaries and storage state;
- cached Registry catalogue snapshots;
- catalogue provenance for selected objects;
- synchronization manifests, states, and receipts;
- minimal connection and session state.

Persisted locally:

- complete accepted Cabinet Card archive;
- durable source binary replicas;
- validation, import, quarantine, and duplicate-review history;
- Registry project and catalogue snapshots;
- catalogue publication and object-validation history;
- Estimate Snapshots and accepted matches;
- Holded publication evidence;
- other accepted Cabinet Cards and relationships.

Calculated on demand:

- validation presentation from stored findings;
- totals across invoices;
- average actual prices;
- remaining planned quantities;
- plan-versus-actual variance;
- coverage and forecasts.

---

# M. Degraded-operation matrix

## Local platform offline

Available:

- Invoice Card V1 creation and update through accepted Cabinet operations;
- source capture and VPS preservation;
- deterministic Card validation and confirmation;
- search and discussion inside the VPS working set;
- browsing the cached Registry catalogue;
- selecting a cached object in the Card `object` block;
- preserving all work for later transfer.

Unavailable or limited:

- current Registry refresh and validation;
- current PresuPro retrieval;
- complete historical search;
- durable estimate matching and full analytics;
- local integration actions.

## Transfer delivered but import quarantined

The VPS retains its authoritative working copy. The local package is preserved
for repair or review but is excluded from normal local archive queries,
analytics, matching, and Holded publication until accepted.

## Local Backend online, Registry unavailable

Existing Registry snapshots remain readable. New validation records
`registry_unavailable` or `inconclusive`; Card object context is not erased.

## PresuPro unavailable

Cards and accepted matches remain readable. Fresh current-plan analysis may be
unavailable unless a suitable Estimate Snapshot exists.

## Holded unavailable

Capture, synchronization, object validation, matching, and analytics remain
available. Publication records failure or ambiguity.

---

# N. State 1 closure questions

Questions requiring State 2 policy or local-platform evidence:

1. Which exact Invoice Card validator version must Backend use, and how are newer
   Card versions negotiated?
2. May draft Cards enter the durable archive, or does normal acceptance require
   `confirmed`?
3. Which source-byte states permit acceptance when Card metadata says
   `file_status = not_stored`?
4. Must Card payloads and mandatory source bytes commit atomically, or may a
   quarantined partial import later become accepted?
5. Which duplicate signals block acceptance, require acknowledgement, or only
   open review?
6. What exact fields belong in the compact VPS Registry catalogue?
7. Is the catalogue complete for all active projects or filtered?
8. How old may a catalogue be before Cabinet warns or blocks selection?
9. Which Registry changes require attention for a previously selected project?
10. How is `unknown_outcome` reconciled for catalogue publication and invoice
    transfer?
11. What VPS retention and backup policy protects unsynchronized work?
12. How does Cabinet select the relevant PresuPro estimate for a project?
13. Which PresuPro changes invalidate accepted matches?
14. How is a corrected confirmed Card handled after successful Holded
    publication?
15. Which additional Cabinet Card types require their own VPS working lifecycle?

State 2 will define invariants, transitions, validation and acceptance policy,
synchronization and reconciliation rules, retention, and calculation semantics.
