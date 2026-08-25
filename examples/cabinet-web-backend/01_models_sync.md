# State 1 — Local synchronization boundary models

## Reciprocal backend wire closure

The following models are imported from the accepted `cabinet_backend` boundary
and are not Web-local aliases: `InvoiceCardRevisionReference`,
`StoredInvoiceCardRevision`, `SourceBinaryReplica`, `InvoiceSynchronization`,
`ContentReference`, `VpsInvoiceTransferPackage`,
`SynchronizationWorkSelection`, `TransferReceiptResult`, and
`TransferReceiptErrorCode`.

`VpsInvoiceTransferPackage` is the exact package envelope. Its metadata is
canonical JSON and its source bytes are streamed separately. The envelope never
contains `storage_reference` for a VPS object, a text blob, or base64 bytes.
`InvoiceTransferManifest.card_revisions` has exactly one entry in the first
release. `InvoiceTransferReceipt.accepted_card_hashes` is plural and
`receipt_at` is the timestamp field; Web must not emit the former local names
`accepted_card_hash` or `received_at`.

## Reciprocal model records

## Model M74 — InvoiceCardRevisionReference

Fields: `invoice_id: str`, `card_version: int`, `content_hash: str`,
`observed_status: str`, `observed_at: datetime`.

### Identity

value

## Model M75 — StoredInvoiceCardRevision

Fields: `revision_id: str`, `reference: InvoiceCardRevisionReference`,
`canonical_card: InvoiceCardV1`, `received_at: datetime`,
`received_from_node_id: str`, `received_by: ActorReference`,
`validation_id: str | None`, `predecessor_content_hash: str | None`,
`superseded_by_content_hash: str | None`.

### Identity

entity

## Model M76 — SourceBinaryReplica

Fields: `source_id: str`, `node_id: str`, `storage_zone: str`,
`storage_reference: str`, `stored_hash: str`, `verification_status: str`,
`stored_at: datetime`, `retention_deadline: datetime | None`,
`deleted_at: datetime | None`.

### Identity

entity

## Model M77 — InvoiceSynchronization

Fields: `synchronization_id: str`, `invoice_id: str`, `source_node_id: str`,
`target_node_id: str`, `manifest_hash: str | None`, `status: str`,
`idempotency_key: str`, `started_at: datetime`, `finished_at: datetime | None`,
`safe_error_code: str | None`.

### Identity

entity

## Model M78 — ContentReference

Fields: `content_id: str`, `content_hash: str`, `size_bytes: int`,
`media_type: str`, `display_filename: str | None`.

### Identity

value

## Model M79 — SynchronizationWorkSelection

Fields: `invoice_id: str`, `manifest_id: str`, `source_node_id: str`,
`target_node_id: str`, `requested_at: datetime`.

### Identity

value

## Model M80 — VpsInvoiceTransferPackage

Fields: `synchronization: InvoiceSynchronization`,
`manifest: InvoiceTransferManifest`,
`card_revision: StoredInvoiceCardRevision`,
`source_replicas: tuple[SourceBinaryReplica, ...]`,
`assignment_observation: CardObjectAssignmentObservation | None`.

### Identity

value

## Model M17 — CabinetNodeIdentity

### Meaning

One enrolled Cabinet installation participating in the evening synchronization
boundary: this VPS Cabinet Web node or an authorized local `cabinet_backend`
node.

Candidate fields:

- `node_id`;
- `node_kind`: `vps_cabinet` or `local_backend`;
- `status`: `active` or `revoked`;
- supported contract version;
- created and revoked times.

Credential material is not part of the node entity.

### Identity

entity

### Identity evidence

Substitution: different node IDs are not interchangeable even when deployed
software and capability sets match. Continuity: the same enrolled node remains
identifiable while contract support or active/revoked status changes.

### Source of truth

The Cabinet synchronization enrollment boundary shared by the participating
installations.

### Lifecycle candidate

`active -> revoked`.

### Persistence candidate

Durable on the nodes that authenticate or exchange with the installation.

### Open questions

None.

## Model M18 — RegistryProjectSnapshot

### Meaning

One immutable issued compact observation of a Registry-owned project delivered
by the local Backend for offline use in Cabinet Web.

Candidate fields aligned with the existing local Backend boundary:

- `snapshot_id` and Registry `project_id`;
- display name, address/compact context, Registry status, and optional customer
  reference;
- Registry version or content hash and Registry timestamps;
- capture time and source contract version.

### Identity

entity

### Identity evidence

Substitution: snapshots with different IDs or source observations are not
interchangeable even if projected fields match. Continuity: the mirrored
Registry project keeps its external project identity while every issued
observation remains immutable snapshot evidence.

### Source of truth

Registry owns project identity and current facts; local `cabinet_backend`
issues the snapshot; Cabinet Web is a preserving replica consumer.

### Lifecycle candidate

Issued immutable snapshot; a later Registry observation creates another
snapshot.

### Persistence candidate

Durable as part of the accepted catalogue replica and any Card assignment
evidence that pins it.

### Open questions

None.

## Model M19 — RegistryCatalogueSnapshot

### Meaning

One immutable compact catalogue of ordered M18 project snapshots generated by
the local Backend for Cabinet Web's offline use.

Candidate fields aligned with the existing local Backend boundary:

- `catalogue_id`, generation time, and source node ID;
- Registry observation time and contract version;
- catalogue content hash;
- ordered project snapshots and project count;
- completeness/filter description when supplied.

### Identity

entity

### Identity evidence

Substitution: catalogue IDs, hashes, and observation times distinguish issued
catalogues even with equal current project fields. Continuity: one issued
catalogue remains fixed; regeneration creates another catalogue.

### Source of truth

Local `cabinet_backend` generates and owns the issued catalogue; Registry owns
the projected project facts.

### Lifecycle candidate

`generated -> delivered`; later policy may classify it stale, but never mutate
it in place.

### Persistence candidate

Durable on the local sender and as an exact accepted replica on Cabinet Web.

### Open questions

None.

## Model M20 — RegistryCatalogueReplica

### Meaning

Cabinet Web's record that one exact M19 catalogue is its current or historical
offline Registry projection.

Candidate fields:

- `catalogue_id`, catalogue content hash, and VPS `node_id`;
- `status`: `received`, `verified`, `current`, `superseded`, or `rejected`;
- received, verified, current, superseded, or rejected times as applicable;
- bounded rejection reason optional.

### Identity

entity

### Identity evidence

Substitution: replicas for different catalogue/node pairs are not
interchangeable. Continuity: one replica remains the same record through
verification and current/superseded classification.

### Source of truth

Cabinet Web owns replica custody/current-selection evidence; M19 and Registry
retain catalogue/project fact authority.

### Lifecycle candidate

`received -> verified -> current -> superseded`, or `received -> rejected`.

### Persistence candidate

Durable replica metadata and exact catalogue content.

### Open questions

None.

## Model M21 — InvoiceTransferManifest

### Meaning

The immutable Cabinet Web-issued description of one exact Invoice work package
available for authenticated local pull.

Candidate fields aligned with the existing local Backend consumer:

- `manifest_id`, version, generation time, and manifest hash;
- exactly one M03 Invoice Card revision and its complete canonical Card payload
  identity/content hash;
- ordered required source IDs with M06 content hashes, byte sizes, media types,
  and safe display filenames;
- included catalogue/assignment provenance references when applicable.

The wire manifest contains logical identities and byte metadata only. Source
bytes follow as bounded streamed parts; a VPS path, storage credential, or local
`storage_reference` is never a manifest or wire field.

### Identity

entity

### Identity evidence

Substitution: different manifest IDs or hashes represent different issued work
packages and retry obligations. Continuity: one issued manifest remains fixed;
changed Card or source contents require another manifest.

### Source of truth

Cabinet Web generates and hashes the manifest from its canonical Invoice Card
revision and verified source custody.

### Lifecycle candidate

Issued immutable snapshot.

### Persistence candidate

Durable on Cabinet Web while delivery, acknowledgement, retention, or audit
obligations remain; preserved by the local consumer as transfer evidence.

### Open questions

None.

## Model M22 — InvoiceTransferIssuance

### Meaning

Cabinet Web's durable record that one authenticated local node requested and
was issued one exact M21 manifest/package. It is transfer-side evidence, not a
claim of local durable acceptance.

Candidate fields:

- `issuance_id`, manifest ID/hash, Invoice ID, and local node ID;
- caller-scoped idempotency identity;
- `status`: `prepared`, `issued`, `acknowledged`, `rejected`, or
  `outcome_unknown`;
- issued/acknowledged times optional;
- bounded receipt result and safe error code optional.

### Identity

entity

### Identity evidence

Substitution: different issuance IDs or node/idempotency scopes are distinct
delivery obligations. Continuity: one issuance remains identifiable from
preparation through issue and acknowledgement or uncertainty.

### Source of truth

Cabinet Web owns transfer-side issuance and acknowledgement evidence. Local
`cabinet_backend` owns its synchronization attempt, import, and durable archive
acceptance.

### Lifecycle candidate

`prepared -> issued -> acknowledged`; `prepared|issued -> rejected |
outcome_unknown`, with reconciliation tied to the same issuance.

### Persistence candidate

Durable while retry/reconciliation or retention obligations remain and retained
as bounded history.

### Open questions

None.

## Model M23 — InvoiceTransferReceipt

### Meaning

Immutable bounded evidence returned by local `cabinet_backend` for the exact
manifest and logical synchronization attempt.

Candidate fields aligned with the existing local Backend contract:

- synchronization and optional import identity;
- idempotency identity, Invoice ID, and manifest hash;
- result: `accepted`, `already_accepted`, `quarantined`, `rejected`, or
  `unknown`;
- accepted Card/source hashes when applicable;
- receipt time and safe error code optional.

### Identity

value

### Identity evidence

Substitution: equal transfer, manifest, result, accepted hashes, and receipt
facts are interchangeable evidence. Continuity: the receipt does not mutate;
later reconciliation returns another evidence value.

### Source of truth

Local `cabinet_backend` issues the receipt from its durable import state;
Cabinet Web preserves but does not reinterpret it.

### Lifecycle candidate

No independent lifecycle; issued immutable evidence.

### Persistence candidate

Durable with M22 for acknowledgement, reconciliation, and retention decisions.

### Open questions

None.

## Model M24 — RegistryCatalogueDelivery

### Meaning

The exact immutable package sent by local `cabinet_backend` to publish one M19
catalogue to Cabinet Web.

Candidate fields aligned with the existing local Backend contract:

- catalogue ID and ordered M18 project snapshots in canonical `project_id`
  order;
- source and target node IDs;
- caller-scoped idempotency identity;
- creation time.

The negotiated contract version is the fixed boundary value
`cabinet-web-sync-v1`, not an invented payload member. Snapshot count and
content identity are derived from the complete immutable ordered snapshots.

### Identity

value

### Identity evidence

Substitution: equal catalogue, ordered projects, endpoints, idempotency, and
creation facts are interchangeable delivery values. Continuity: any changed
fact creates another value.

### Source of truth

Local `cabinet_backend` constructs the delivery from its issued catalogue.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Accepted atomically into M20 plus acknowledgement evidence; the package itself
may be retained for audit/replay proof.

### Open questions

None.

## Model M25 — VpsCatalogueAcknowledgement

### Meaning

Immutable bounded Cabinet Web evidence that one exact catalogue delivery was
accepted, already accepted, or rejected.

Candidate fields aligned with the existing local Backend contract:

- local publication ID and catalogue ID;
- `status`: accepted, already accepted, or rejected;
- acknowledgement time optional;
- safe error code optional.

### Identity

value

### Identity evidence

Substitution: equal publication, catalogue, status, time, and error facts are
interchangeable acknowledgement evidence. Continuity: later observation emits
another value rather than mutating the issued acknowledgement.

### Source of truth

Cabinet Web issues it from durable M20 replica acceptance state.

### Lifecycle candidate

No independent lifecycle; issued immutable evidence.

### Persistence candidate

Durable on Cabinet Web and retained by local `cabinet_backend` with its
publication record.

### Open questions

None.

## Model M26 — LocalBackendConnectionObservation

### Meaning

One bounded Cabinet Web observation made during a local-initiated evening
session about the authenticated node and contract compatibility. It is not an
outbound VPS reachability probe.

Candidate fields:

- `available`, `authenticated`, and `compatible` booleans;
- local node ID and remote contract version when established;
- observation time and last successful session time optional;
- safe error code optional.

### Identity

value

### Identity evidence

Substitution: equal node, compatibility, timestamps, and safe result facts are
interchangeable observations. Continuity: a later session creates another
observation.

### Source of truth

Cabinet Web's authenticated session boundary observes the inbound local
connection; it never infers local archive availability from elapsed time alone.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Latest successful/failed observation may be durable for user-visible freshness
and operations; individual observations are bounded historical evidence.

### Open questions

None.

## Model M27 — InvoiceWorkingSetMembership

### Meaning

An immutable observation of which exact Invoice Card revisions and required
sources Cabinet Web currently retains as available for local pull.

Candidate fields:

- `working_set_id` and VPS node ID;
- ordered work items, each containing `invoice_id`, exactly one M03 revision
  identity/content hash, `manifest_id`/manifest hash, and ordered required
  source IDs with content hashes, byte sizes, media types, and safe display
  filenames;
- observation time and an opaque continuation cursor when the observation is a
  bounded discovery page.

Only Invoice work appears. A discovery page is a point-in-time observation;
the local Backend selects an exact returned `manifest_id` for pull rather than
reconstructing membership or choosing a newer revision implicitly.

### Identity

value

### Identity evidence

Substitution: equal working-set identity, ordered membership, node, and time
facts are interchangeable. Continuity: changed membership creates another
observation value.

### Source of truth

Cabinet Web's canonical Card availability and M14 source custody state.

### Lifecycle candidate

No independent lifecycle; later membership is a new observation.

### Persistence candidate

Calculated for discovery and optionally retained when exact issuance or release
evidence must pin the observed set.

### Open questions

None.

## Model M28 — SynchronizationConflict

### Meaning

One durable review obligation created when Cabinet Web and local
`cabinet_backend` present incompatible accepted Invoice revision evidence and
the conflict cannot be resolved by idempotent replay or exact receipt lookup.
It never rewrites either revision by arrival order.

Candidate fields:

- `conflict_id` and Invoice ID;
- exact Cabinet Web M03 revision;
- bounded local current revision/acceptance reference;
- common predecessor reference optional;
- conflict reason and detection time;
- `status`: `open` or `resolved`;
- explicit resolution evidence and resolved time optional.

### Identity

entity

### Identity evidence

Substitution: different conflict IDs are distinct human review obligations even
when they involve the same Invoice. Continuity: one conflict remains
identifiable from detection until an explicit resolution is recorded.

### Source of truth

Cabinet Web owns its conflict record and attempted revision evidence; each
application remains authoritative for its own accepted revision and receipt
facts.

### Lifecycle candidate

`open -> resolved`; no automatic last-write-wins transition.

### Persistence candidate

Durable conflict and resolution history.

### Open questions

None.

## Model M29 — CardObjectAssignmentObservation

### Meaning

Immutable Cabinet Web-produced provenance describing the object/project context
captured for one exact Invoice Card revision and transported with its Invoice
package. It is an observation, not permission for either sync peer to invent a
Registry mapping.

Candidate fields aligned with the existing local Backend consumer:

- `observation_id` and exact M03 Invoice Card revision;
- explicit Registry `project_id` optional;
- object label optional;
- catalogue ID and Registry snapshot ID optional;
- bounded decision context and observation time.

An explicit `project_id` is valid only with the catalogue/snapshot provenance
from which the owner selected it. Without that exact selection, the observation
remains `label_only`, `unassigned`, or `needs_review` according to its supplied
facts; an opaque Card ID or matching label is never mapping evidence.

### Identity

entity

### Identity evidence

Substitution: equal observation ID, exact Card revision, assignment facts,
provenance, decision context, and time are interchangeable. Continuity: a later
Card revision or assignment decision creates another immutable observation.

### Source of truth

Cabinet Web's confirmed Invoice capture/domain path produces the observation.
Synchronization transports it, and local `cabinet_backend` may persist it
unchanged but cannot derive or rewrite the project assignment.

### Lifecycle candidate

No independent lifecycle; issued immutable evidence.

### Persistence candidate

Durable with the exact Invoice revision/manifest on Cabinet Web and with the
accepted transfer evidence on the local consumer.

### Open questions

None.
