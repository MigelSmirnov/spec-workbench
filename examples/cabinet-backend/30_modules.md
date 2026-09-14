# State 3 — Cabinet Backend module responsibilities

## Goal

This state assigns primary ownership of the accepted State 0–2 knowledge, invariants, lifecycles, and protected capabilities.

Modules are derived from reasons for change and hidden policy, not from HTTP routes, MCP tools, database tables, UI screens, or one module per model.

The VPS Cabinet and Local Cabinet Backend may expose compatible logical Cabinet operations, but transport wrappers do not own Cabinet business rules.

---

# 1. Responsibility map

## `domain_models`

### Owns

- shared State 1 domain/value-model definitions used across Backend responsibilities;
- deterministic declarations of every `kind: interface` Protocol used by
  runtime modules; this is physical type ownership only, while the consuming
  domain module retains policy and implementation responsibility;
- immutable references and evidence shapes;
- enum-like lifecycle vocabularies accepted in States 1–2.

### Knows

- field structure, identity semantics, and type relationships only.

### Must not own

- authentication or authorization policy;
- archive acceptance;
- synchronization sequencing;
- Registry or PresuPro refresh policy;
- Holded publication policy;
- persistence or transport lowering.
- repository, transport, authorization, or unit-of-work implementation behind
  an interface declared in this module.

### Public surface

Exports model types only: every model, enum and interface of the `models` section
is in `imports.internal.models` (the deterministic models producer is selected
only when the export surface covers the whole section).

### Depth assessment

Foundational type module. It is intentionally not a service or orchestration layer.

---

## `access_control`

### Owns

- authentication context accepted at Cabinet Backend protected boundaries;
- local service/agent enrollment, status, capability assignment, rotation, and revocation;
- separation of local service identity from `SyncNodeCredential`;
- mapping accepted OS/IPC peer identity to an enrolled local service principal when that deployment mechanism is used;
- exact-operation authorization for protected local Backend capabilities;
- security audit evidence for authentication, throttling, revocation, and authorization decisions owned by A61, A66, and A67.

### Knows

- principal/credential boundary distinctions;
- local-agent capability grants;
- revoked/active credential state;
- the accepted single-user OS-delegated human baseline;
- machine/service abuse and replay response policy.

### Hides

- credential storage and hashing details;
- peer-identity lookup mechanics;
- throttling counters and security-event persistence;
- capability-set representation.

### Must not own

- Invoice Card business validity;
- archive/import acceptance;
- sync payload semantics;
- Registry/PresuPro business data;
- Holded eligibility;
- HTTP, MCP, CLI, or browser request parsing.

### Candidate public capabilities

```text
authorize_operation
authenticate_local_service
resolve_local_interactive_context
rotate_local_service_credential
revoke_local_service_credential
record_authentication_failure
```

### Boundary note

VPS human login/recovery is owned by VPS Cabinet, not by Local Cabinet Backend. State 3 records the shared policy dependency but does not pull the remote account system into this Backend package.

### Depth assessment

kind: deep
hidden mechanism: identity-separated credential lifecycle — peppered verification, throttle, and audit — behind one authorization surface

Deep security-policy module. It hides identity separation, capability policy, credential lifecycle, and audit behavior behind a small authorization surface.

---

## `durable_archive`

### Owns

- durable acceptance of existing Cabinet Invoice Card V1 revisions into the local archive;
- preservation of exact immutable Card revisions;
- accepted Card validation evidence used for archive acceptance;
- source-binary custody required by local durable acceptance;
- hash verification and source replica status;
- duplicate-candidate review lifecycle;
- import acceptance, rejection, quarantine, and quarantine resolution;
- idempotent manifest acceptance;
- atomic visibility of an accepted manifest required set;
- normal archive visibility versus quarantined/diagnostic visibility;
- source attachment transitions owned by the local Backend;
- explicit incomplete-source acceptance evidence and source-loss decision history;
- reversible source completeness transitions among awaiting_source, source_lost, and complete;
- durable archive evidence required before VPS working-copy release may be authorized.

### Knows

- Card identity and revision immutability rules;
- required-source-set semantics;
- valid, warning, invalid, unsupported-version outcomes;
- duplicate policy;
- import idempotency and predecessor/conflict preconditions;
- source integrity and missing-original semantics;
- atomic acceptance rules from the State 2 import/source decisions.

### Hides

- database transaction boundaries;
- physical source-file layout;
- quarantine staging layout;
- hash-verification sequencing;
- archive indexes and persistence mapping;
- duplicate-review persistence.

### Owned persistent records

```text
StoredInvoiceCard
StoredInvoiceCardRevision
InvoiceCardValidationRecord
DuplicateCandidateReview
SourceBinary
SourceBinaryReplica
InvoiceTransferManifest
InvoiceImport
ImportQuarantine
InvoiceTransferReceipt
IncompleteSourceAcceptance
SourceLossDecision
```

### Must not own

- network delivery state;
- retry scheduling for synchronization transport;
- creation/editing semantics of Invoice Card V1;
- Registry project truth;
- PresuPro plan truth;
- Holded transport or credentials;
- MCP/HTTP request handling.

### Candidate public capabilities

```text
accept_transfer_manifest
get_import_status
resolve_import_quarantine
get_archived_invoice
search_archive
attach_local_source
accept_incomplete_source_evidence
record_source_loss
get_source_status
derive_source_status
verify_durable_acceptance
get_transfer_receipt
```

### Consolidation decision

Archive records, source durability, duplicate handling, import, and quarantine remain one deep responsibility because State 1 identifies them as one durable-acceptance problem and State 2 requires one atomic accepted-set boundary. Splitting them into endpoint-sized services would leak transaction and acceptance sequencing to callers.

### Depth assessment

kind: deep
hidden mechanism: atomic manifest acceptance — card, required sources, and receipt commit as one exact custody transition

Primary deep persistence/domain module for local durable Cabinet custody.

---

## `synchronization`

### Owns

- Backend-initiated synchronization with VPS Cabinet;
- construction and identity of transfer/publication packages from already selected domain content;
- `SyncNodeCredential` use at the synchronization boundary without exposing it to other modules;
- delivery lifecycle, retries, idempotency correlation, unknown-outcome reconciliation, and connection observations;
- transmission and reconciliation of transfer receipts;
- reporting synchronization availability and transport outcome without claiming business acceptance.

### Knows

- node identity and contract compatibility;
- manifest/package hash and idempotency binding;
- delivery versus acceptance distinction;
- outbound-only synchronization direction;
- retry/reconciliation semantics;
- authenticated encrypted private transport requirement.

### Hides

- concrete transport selection;
- request signing/mTLS/Tailscale/SSH details;
- retry timing and connection diagnostics;
- wire serialization.

### Must not own

- Card validation or duplicate policy;
- local durable acceptance decision;
- Registry catalogue contents/filter policy;
- PresuPro matching;
- Holded publication eligibility;
- local agent authorization.

### Candidate public capabilities

```text
synchronize_invoice_work
reconcile_transfer_outcome
get_sync_status
observe_vps_connection
get_working_set_membership
```

### Ownership invariant

`delivered` is a transport fact. Only `durable_archive` may decide `accepted` or `already_accepted` for local invoice import.

### Depth assessment

kind: deep
hidden mechanism: durable reserve-issue-reconcile discipline over the authenticated node transport

Deep boundary module. It hides authenticated transport, retries, reconciliation, and node protocol while remaining ignorant of archive acceptance policy.

---

## `registry_context`

### Owns

- reading accepted Registry project context through the Registry integration boundary;
- immutable Registry project snapshots;
- local `WorkObject` projection keyed by Registry `project_id`;
- compact Registry catalogue construction and freshness/completeness semantics;
- Card object-assignment observations based on exact Card/catalogue context;
- post-reconnection validation of cached/offline project assignment;
- preservation of warnings/review state when Registry context changed or cannot validate the earlier choice.

### Knows

- Registry authority boundary;
- project snapshot/version semantics;
- catalogue selection and freshness rules;
- assignment-validation outcomes;
- the rule that validation never silently rewrites the Card object decision.

### Hides

- Registry client calls;
- snapshot-diff mechanics;
- catalogue indexing;
- WorkObject refresh sequencing.

### Must not own

- Invoice Card editing;
- synchronization transport;
- PresuPro estimate/match rules;
- Holded publication;
- generic agent routing.

### Candidate public capabilities

```text
refresh_registry_context
record_card_assignment_observation
build_registry_catalogue
get_work_object
validate_card_assignment
get_assignment_validation
```

### Depth assessment

kind: deep
hidden mechanism: keyed Registry observation merge with offline assignment validation against exact pinned context

Deep project-context module. It hides Registry observation/versioning and offline-assignment reconciliation behind Cabinet project semantics.

---

## `plan_actual`

### Owns

- immutable PresuPro estimate snapshots used by Cabinet;
- invoice-line-to-estimate match proposals and accepted/rejected match decisions;
- invalidation of matches when pinned source inputs cease to be valid;
- plan-versus-actual calculations from exact pinned Card, estimate, assignment, match, and conversion inputs;
- warnings and refusal when units/inputs do not permit a valid comparison;
- reproducible forecast/analysis assumptions when a forecast is requested.

### Knows

- PresuPro authority boundary;
- comparable Invoice Line and Estimate Item meanings;
- accepted matching cardinality;
- quantity/unit conversion preconditions;
- calculation semantics for planned, actual, variance, remaining quantity, averages, and forecasts.

### Hides

- PresuPro client details;
- matching candidate ranking mechanics;
- analysis aggregation/indexing;
- cache strategy for derived results.

### Must not own

- mutation of PresuPro estimates;
- mutation of Invoice Card facts;
- Registry project identity;
- archive import;
- Holded publication.

### Candidate public capabilities

```text
refresh_estimate_snapshot
propose_invoice_line_matches
record_match_decision
calculate_plan_actual
get_unmatched_items
```

### Depth assessment

kind: deep
hidden mechanism: pinned-snapshot semantic join — one active confirmed match per line over immutable evidence

Deep analytical module. It owns the semantic join between Cabinet purchase facts and PresuPro plan data while keeping both sources of truth unchanged.

---

## `holded_publication`

### Owns

- Cabinet business eligibility for publishing one exact confirmed Invoice Card revision;
- publication lifecycle and user-visible publication state;
- explicit publication intent and exact-target confirmation boundary;
- correlation of one business publication with technical gateway attempts/results;
- reconciliation policy when a technical outcome is unknown;
- prevention of duplicate logical publication from repeated Cabinet requests.

### Knows

- confirmed-card eligibility rules;
- publication attempt markers and business verification requirements;
- separation of publication from PresuPro matching;
- which gateway outcome may settle, retry, or reconcile a publication.

### Hides

- publication state-machine sequencing;
- business verification used after ambiguous technical outcomes;
- mapping between Cabinet publication and gateway receipt history.

### Must not own

- Holded credentials;
- raw HTTP calls/retries;
- generic invoice archive acceptance;
- PresuPro analysis;
- Registry snapshots.

### Candidate public capabilities

```text
request_holded_publication
get_holded_publication_status
reconcile_holded_publication
```

### Depth assessment

kind: deep
hidden mechanism: one logical publication lifecycle per exact revision with read-back settlement

Deep business-control module. It owns whether Cabinet is allowed to publish and how that business obligation settles, not the external HTTP mechanism.

---

## `holded_transport`

### Owns

- the verified Holded Invoicing v1 purchase origin and paths;
- the `key` credential-header codec;
- purchase payload and response field mappings;
- bounded HTTP execution with TLS verification and no redirect/retry replay.

### Knows

The verified Holded v1 wire contract closed by `rules.holded_transport_backend`; nothing of Cabinet publication meaning.

### Hides

- httpx construction;
- JSON serialization and bounded response reads;
- Holded wire field names.

### Must not own

- Cabinet publication eligibility or settlement;
- attempt persistence or single-create authority;
- environment reads;
- Holded update, attachment, approval, payment, deletion, or refund operations.

### Candidate public capabilities

```text
holded_wire_date
```

### Depth assessment

kind: deep
hidden mechanism: bounded verified-TLS execution of the closed Holded v1 purchase wire

Deterministic infrastructure deep module. Its entire implementation is emitted
from `rules.holded_transport_backend`; it exposes only
`HttpxHoldedHttpClient` to bootstrap.

---

## `holded_gateway`

### Owns

- Holded credential containment through the supplied HTTP port;
- technical retry policy permitted by the accepted Holded rules;
- immutable technical attempt evidence/receipts;
- technical lookup/recovery operations needed by `holded_publication` after an unknown outcome;
- redaction of Holded secrets from logs and ordinary business data.

### Knows

- Holded external API contract;
- technical request/response schemas;
- remote identifiers and transport failure classifications;
- technical idempotency/recovery capabilities actually offered by Holded.

### Hides

- concrete HTTP client and wire configuration, owned by `holded_transport`;
- credential loading, owned by bootstrap;

### Must not own

- Cabinet publication eligibility;
- choosing the Invoice Card revision to publish;
- user confirmation policy;
- Registry or PresuPro rules;
- archive acceptance.

### Candidate public capabilities

```text
create_holded_purchase
lookup_holded_purchase
get_holded_attempt_result
```

### Trace inputs

- A51
- A52
- A71

### Depth assessment

kind: deep
hidden mechanism: single-create attempt authority — durable reservation, one POST, bounded read-only recovery

Deep external-integration adapter. It is separate because credentials, remote protocol knowledge, retry behavior, and technical reconciliation change independently from Cabinet publication policy.

---

## Withdrawn — `retention_release`

> **Withdrawn by A76** (`02_rules_flow6_ownership_repair.md`, 2026-08-23): the VPS working set, its release policy and this surface belong to Cabinet Web. Kept as design history; not assembled.

### Owns

- eligibility to release/delete VPS working replicas after durable local acceptance;
- manual-release baseline and its exact preconditions;
- retention evidence and release decision history;
- prevention of deletion when required local replicas are missing/unverified;
- distinction among unsynchronized evidence, synchronized working copy, local legal/accounting retention, and external-system copies;
- idempotent repeated release decisions.

### Knows

- durable-acceptance proof from `durable_archive`;
- replica/retention state required for release;
- the accepted rule that Registry status changes do not automatically delete VPS evidence.

### Hides

- retention-deadline computation;
- release decision persistence;
- node-replica eligibility checks.

### Must not own

- physical storage deletion implementation on every node;
- Registry lifecycle truth;
- synchronization transport;
- user/account deletion semantics for Holded or backups.

### Candidate public capabilities

```text
evaluate_vps_release
request_manual_vps_release
get_retention_status
```

### Depth assessment

Policy module. It exists because evidence release has independent safety invariants and must not be an incidental side effect of synchronization or Registry status.

---

## Withdrawn — `retention_release_persistence`

> **Withdrawn by A76** (`02_rules_flow6_ownership_repair.md`, 2026-08-23): the VPS working set, its release policy and this surface belong to Cabinet Web. Kept as design history; not assembled.

### Owns

- `PostgresRetentionReleaseRepository`: the PostgreSQL storage shape for
  release evaluations and decisions;
- one transaction and one exact working-set lock per service operation;
- immutable append of evaluation and decision rows with uniqueness on the
  exact project and working-set target.

### Hides

- psycopg connection handling;
- table, column, and index names;
- row/model codecs for nested evaluation evidence.

### Must not own

- release eligibility, equivalence, or conflict decisions;
- idempotent reuse of an existing decision;
- physical VPS deletion;
- environment reads.

### Depth assessment

Deterministic persistence module. It implements the `RetentionReleaseRepository`
Protocol from `models` as plain reads and appends; `retention_release` decides
whether a stored decision may be reused. See
`30_modules_persistence_boundary.md`.

---

## `holded_publication_persistence`

### Owns

- `PostgresHoldedPublicationRepository`: the PostgreSQL storage shape for
  logical Holded publications;
- one transaction and the exact publication and invoice-revision locks per
  service operation;
- plain append of a new logical publication and plain update of its
  lifecycle fields.

### Knows

The closed logical-publication projection and the `HoldedPublicationRepository` Protocol; no business meaning beyond exact typed facts.

### Hides

- psycopg connection handling;
- table, column, and index names;
- row/model codecs for the card revision reference.

### Must not own

- publication eligibility, equivalence reuse, or duplicate rejection;
- lifecycle transition validity;
- gateway calls or Holded evidence interpretation;
- environment reads.

### Candidate public capabilities

```text
create_holded_publication_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL transaction with exact publication and revision locks

Deterministic persistence module. It implements the `HoldedPublicationRepository`
Protocol from `models` as plain reads, one append, and one field update;
`holded_publication` decides which transitions are valid. See
`30_modules_persistence_boundary.md`.

---

## `registry_context_persistence`

### Owns

- `PostgresRegistryContextRepository`: the PostgreSQL storage shape for
  WorkObjects and assignment-validation evidence;
- one transaction and the catalogue lock per service operation;
- listing of all WorkObjects, keyed upsert of WorkObjects, append and exact
  lookup of validations.

### Knows

The closed WorkObject and validation projections and the `RegistryContextRepository` Protocol; no business meaning beyond exact typed facts.

### Hides

- psycopg connection handling;
- table, column, and index names;
- row/model codecs for card revision references and warning codes.

### Must not own

- the Registry merge itself: which objects are new, refreshed, or unresolved;
- Registry status meaning, assignment eligibility, freshness, or validation
  outcomes;
- environment reads.

### Candidate public capabilities

```text
create_registry_context_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL transaction with the catalogue lock and keyed WorkObject upserts

Deterministic persistence module. It implements the `RegistryContextRepository`
Protocol from `models` as plain reads, one keyed upsert, and one append;
`registry_context` derives the merged catalogue. See
`30_modules_persistence_boundary.md`.

---

## `holded_gateway_persistence`

### Owns

- `PostgresHoldedAttemptRepository`: the PostgreSQL storage shape for
  technical Holded attempts and read-only lookup observations;
- one transaction and the exact attempt lock per gateway state transition;
- plain append of an attempt, plain update of its outcome fields, plain
  append of lookup evidence, exact reads by attempt id and unique marker.

### Knows

The closed attempt and lookup-observation projections and the `HoldedAttemptRepository` Protocol; no business meaning beyond exact typed facts.

### Hides

- psycopg connection handling;
- table, column, and index names;
- row/model codecs for the observed remote document.

### Must not own

- reservation equivalence or conflict decisions;
- single-create authority: whether POST may be issued;
- outcome classification or transition validity;
- environment reads or Holded HTTP.

### Candidate public capabilities

```text
create_holded_gateway_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL transaction with the exact attempt lock and unique-marker reads

Deterministic persistence module. It implements the `HoldedAttemptRepository`
Protocol from `models` as plain reads, appends, and one field update;
`holded_gateway` decides reuse, issuance, and outcome transitions. See
`30_modules_persistence_boundary.md`.

---

## `catalogue_publication`

### Owns

- idempotent delivery of one compact Registry catalogue snapshot to the VPS
  Cabinet after `registry_context` has produced it;
- the `RegistryCataloguePublication` lifecycle: binding by catalogue id,
  target node and idempotency key, reuse of an equivalent publication,
  rejection of a conflicting one, and the transition written after the
  transport acknowledgement;
- reporting the acknowledgement outcome and safe error code without
  interpreting catalogue contents.

### Knows

- catalogue identity and ordered content hash;
- idempotency binding and conflict rules;
- `CataloguePublicationStatus` transitions.

### Hides

- transport selection and wire serialization (`VpsSynchronizationTransport`);
- storage shape (`CataloguePublicationRepository`).

### Candidate public capabilities

```text
publish_registry_catalogue
```

### Must not own

- Registry catalogue contents or filter policy;
- invoice transfer, transfer receipts, or durable acceptance;
- connection observation or reconciliation of invoice transfers.

### Depth assessment

kind: deep
hidden mechanism: idempotency-bound catalogue publication lifecycle over an exact ordered snapshot

Split out of `synchronization` (decision 2026-08-23): invoice transfer and
catalogue publication share only the transport; each has its own state machine,
repository methods and wire models, and regenerations of the merged module
were the least stable in the factory. One public operation hides the whole
lifecycle; `synchronization` keeps the invoice transfer path only.

---

## `catalogue_publication_persistence`

### Owns

- `PostgresCataloguePublicationRepository`: the PostgreSQL storage shape for
  `RegistryCataloguePublication` rows (`registry_catalogue_publications`);
- one transaction per lifecycle transition; plain appends, field updates and
  the exact read by idempotency binding.

### Knows

The closed projection of `registry_catalogue_publications` and the `CataloguePublicationRepository` Protocol; no business meaning beyond exact typed facts.

### Hides

- psycopg connection handling, table, column and index names, codecs.

### Must not own

- equivalence, conflict or transition decisions;
- VPS transport; environment reads.

### Candidate public capabilities

```text
create_catalogue_publication_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL transaction over the idempotency-bound publication row lifecycle

Deterministic persistence module emitted from `rules.persistence_backend`; it
implements the `CataloguePublicationRepository` Protocol from `models`.

---

## `synchronization_persistence`

### Owns

- `PostgresSynchronizationRepository`: the PostgreSQL storage shape for
  synchronization attempts and connection observations;
- one transaction and the exact synchronization lock per lifecycle
  transition;
- plain appends, plain field updates, and exact reads by id or idempotency
  binding.

### Knows

The closed synchronization-attempt and connection-observation projections and the `SynchronizationRepository` Protocol; no business meaning beyond exact typed facts.

### Hides

- psycopg connection handling;
- table, column, and index names;
- row/model codecs.

### Must not own

- reservation equivalence, issuance authority, or outcome classification;
- VPS transport;
- environment reads.

### Candidate public capabilities

```text
create_synchronization_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL transaction with the exact synchronization lock and idempotency-bound reads

Deterministic persistence module. It implements the `SynchronizationRepository`
Protocol from `models` as plain reads, appends, and field updates;
`synchronization` decides reuse, issuance, and transitions. `load_sync_status`
stays on the port until the working-set/replica storage decision is taken
(`30_modules_persistence_boundary.md`, open items).

---

## `plan_actual_persistence`

### Owns

- `PostgresPlanActualRepository`: the PostgreSQL storage shape for estimate
  snapshots, match proposals, and match decisions;
- one transaction and the exact estimate and invoice-line locks per service
  operation;
- plain appends, one status update, exact and set reads in stable order.

### Knows

The closed snapshot, proposal, and decision projections and the `PlanActualRepository` Protocol; no business meaning beyond exact typed facts.

### Hides

- psycopg connection handling;
- table, column, and index names;
- row/model codecs for snapshot items and revision references.

### Must not own

- snapshot reuse by canonical content, proposal scoring, or match policy;
- the "at most one active confirmed match" invariant or pinned-identity
  completeness;
- plan/actual formulas;
- environment reads.

### Candidate public capabilities

```text
create_plan_actual_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL transaction with exact estimate and invoice-line locks in stable order

Deterministic persistence module. It implements the `PlanActualRepository`
Protocol from `models` as plain reads, appends, and one field update;
`plan_actual` decides reuse, conflicts, and completeness. See
`30_modules_persistence_boundary.md`.

---

## `durable_archive_persistence`

### Owns

- `PostgresArchiveUnitOfWork`: the PostgreSQL storage shape for the
  invoice card head, immutable card revisions, source identities and
  replicas, transfer manifests and receipts, byte-publication journal rows,
  and acceptance/loss decisions;
- one metadata transaction and the exact invoice lock per archive operation;
- plain appends, keyed upserts/field updates, and exact or ordered reads.

### Knows

The closed archive table projections — card head, revisions, sources, replicas, manifests, receipts, journal, decisions — and the `ArchiveUnitOfWork` Protocol; no business meaning beyond exact typed facts.

### Hides

- psycopg connection handling;
- table, column, and index names;
- row/model codecs for canonical cards, references, and hash tuples.

### Must not own

- acceptance equivalence, quarantine, or incomplete-source policy;
- `rules.archive_byte_publication` state transitions;
- byte custody (`SourceByteStore`);
- environment reads.

### Candidate public capabilities

```text
create_durable_archive_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL unit-of-work with the exact invoice lock over the archive table registry

Deterministic persistence module. It implements the `ArchiveUnitOfWork`
Protocol from `models` as plain reads, appends, and field updates;
`durable_archive` composes them into accepted transitions. See
`30_modules_persistence_boundary.md`.

---

## `source_byte_store`

### Owns

- `LocalFilesystemSourceByteStore`: the local two-phase byte store — exclusive
  staging writes verified by reopen, content-addressed final references,
  same-filesystem atomic rename;
- the opaque reference scheme beneath the configured root.

### Knows

The configured storage root, the two-phase write discipline, and the opaque reference scheme; nothing about which bytes matter.

### Hides

- directory layout, file modes, fsync discipline;
- reference validation against traversal, symlink escape, and non-regular
  files.

### Must not own

- publication lifecycle state (`rules.archive_byte_publication` transitions
  belong to `durable_archive`);
- archive metadata or PostgreSQL;
- environment reads.

### Candidate public capabilities

```text
stage
publish
verify
final_reference_for
remove_staging
```

### Depth assessment

kind: deep
hidden mechanism: two-phase content-addressed byte custody with atomic same-filesystem rename

Deterministic infrastructure deep module. Its entire implementation is emitted
from `rules.source_byte_store_backend` (SPEC_STANDARD §6.5); it exposes only
`LocalFilesystemSourceByteStore` to bootstrap.

---

## `credential_security`

### Owns

- issuance of a random service secret and its presentable token envelope;
- the Argon2id verifier of the peppered secret and its constant-time check;
- token parsing into selector and secret.

### Knows

The token envelope format and Argon2id parameters closed by `rules.credential_security_backend`; no principal or policy state.

### Hides

Argon2id parameterization, pepper application, entropy sourcing, and the token envelope encoding.

### Must not own

- principals, credentials, throttle, or audit storage;
- authentication or authorization policy;
- environment reads (the pepper is supplied by the caller).

### Candidate public capabilities

```text
issue_service_credential
parse_service_token
verify_service_secret
```

### Depth assessment

kind: deep
hidden mechanism: peppered Argon2id verification with constant-time comparison behind a fixed token envelope

Deterministic infrastructure deep module emitted from
`rules.credential_security_backend` (SPEC_STANDARD §6.6); exposes three pure
functions to `access_control`.

---

## `access_control_persistence`

### Owns

- `PostgresAccessControlRepository`: storage shape for principals,
  credential verifiers, throttle state, and security audit evidence;
- one transaction and the exact principal / abuse-context locks per
  operation.

### Knows

The closed table projections and identity keys of principals, credential verifiers, throttle state, and audit rows, and the `AccessControlRepository` Protocol; no business meaning beyond exact typed facts.

### Hides

psycopg connection handling; table, column, and index names; row/model codecs for principals, verifiers, throttle state, and audit rows.

### Must not own

- throttle thresholds, capability evaluation, or lifecycle transitions;
- cryptography;
- environment reads.

### Candidate public capabilities

```text
create_access_control_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL transaction with exact principal and abuse-context locks over the access-control tables

Deterministic persistence module emitted from `persistence_backend/v3`; it
implements the `AccessControlRepository` Protocol from `models` as plain
reads, appends, field updates, and one keyed upsert.

---

## `api`

### Owns

Exactly the HTTP assembly emitted by `http_router_backend/v1`: route table,
typed request/response projection, and dependency storage on the application
object.

### Knows

The accepted protected routes, the emitted handler signatures, and the
`api_irregular` transport helpers the deterministic table calls.

### Must not own

Authorization policy, archive acceptance, matching, publication, retention,
or synchronization policy; no business rule lives in transport assembly.

### Hides

FastAPI wiring, route registration order, request parsing, and response
serialization behind the emitted typed handlers.

### Candidate public capabilities

```text
create_app
```

### Depth assessment

kind: facade
delegates to: `access_control`, `durable_archive`, `synchronization`, `catalogue_publication`, `registry_context`, `plan_actual`, `holded_publication`

Deterministically emitted transport shell: every operation is a typed
delegation to one accepted application capability.

---

## `data_provider`

### Owns

Exactly the closed product-data constants emitted deterministically from
`rules.data_provider_backend` (python_constant_data_v1): abuse thresholds,
credential hash algorithm name, accepted media types, supported manifest
versions, status-transition tables, the Holded read-back projection mapping and
tolerances, and the plan/actual proposal scoring data.

### Knows

Only the accepted `rules.data_provider_backend` IR it is emitted from.

### Must not own

Behavior, policy interpretation, persistence, configuration loading, models,
or any computed value.

### Hides

The encoding of accepted product data as Python constants behind plain named
symbols, so no LLM-generated module ever receives a value in its prompt.

### Candidate public capabilities

```text
constants
```

### Depth assessment

kind: deep
hidden mechanism: deterministic emission of the closed product-data constants from the accepted IR

## `system_clock`

### Owns

Exactly the concrete `SystemClock` implementation of the `Clock` port.

### Knows

Only the `Clock` interface and the host timezone-aware UTC wall clock.

### Must not own

Business policy, persistence, configuration loading, scheduling, cached time,
or service construction.

### Hides

The per-call `datetime.now(timezone.utc)` wall-clock read behind the narrow
`Clock.now` interface.

### Candidate public capabilities

```text
now
```

### Depth assessment

kind: deep
hidden mechanism: per-call timezone-aware UTC wall-clock read behind the narrow Clock.now interface

Emitted deterministically from `system_clock_backend/v1`; one shared instance
is constructed by bootstrap and handed to every evidence-stamping service.

---

# 2. Boundary adapters are not policy modules

The following are expected adapters or deployment surfaces, not primary owners of Cabinet rules:

```text
VPS HTTP/browser handlers
VPS MCP/tool wrapper
Local Backend MCP/tool wrapper
Local HTTP/IPC/CLI wrapper
PostgreSQL repositories
filesystem/blob adapters
Registry client
PresuPro client
```

They may validate transport shape, authenticate through `access_control`, call one or more accepted application capabilities, and translate results. They must not duplicate authorization, archive acceptance, matching, publication, retention, or synchronization policy.

`api` owns only the functions emitted by `http_router_backend/v1`. Transport helpers that the deterministic table calls but does not emit are physically owned by `api_irregular`; this includes multipart lowering and the local-principal resolver. Those helpers delegate credential verification and authorization decisions to `access_control` and do not own security policy.

A tool name is not a module boundary. Compatible VPS/local tools may map to different capability availability while sharing the same Cabinet semantic operation.

---

# 3. Primary State 2 enforcement ownership

| State 2 concern | Primary State 3 owner |
| --- | --- |
| local agent/service identity, capability authorization, credential separation | `access_control` |
| authentication abuse/revocation for Local Backend machine/service boundaries | `access_control` |
| Card revision preservation, source verification, import, quarantine, duplicate handling | `durable_archive` |
| atomic source attachment and missing-original local transitions | `durable_archive` |
| Backend-initiated VPS transfer, retry, reconciliation, node transport | `synchronization` |
| Registry snapshots, offline catalogue semantics, WorkObject context, assignment validation | `registry_context` |
| PresuPro snapshots, match decisions, plan-versus-actual | `plan_actual` |
| Cabinet Holded eligibility/publication lifecycle | `holded_publication` |
| Holded v1 HTTP wire contract and credential-header containment | `holded_transport` |
| Holded single-create authority and technical receipts | `holded_gateway` |
| VPS working-copy release and retention eligibility | `retention_release` |
| dependency vulnerability/update policy | deployment/release process, not a runtime Cabinet module |
| runtime interpreted-input invariant | each owning boundary/module; adapters cannot turn input into executable structure |

The interpreted-input rule remains cross-cutting in application, but each module enforces it at the boundary where that module deliberately interprets a closed vocabulary. No generic `security_utils` module owns all input safety.

---

# 4. Dependency direction candidates

Allowed conceptual direction for later State 4–6 refinement:

```text
transport/tool adapters
    -> access_control
    -> owning application module

synchronization
    -> durable_archive (status/receipt capabilities only)
    -> registry_context (exact catalogue publication input only)

durable_archive
    -> domain_models
    -> access_control for protected external operations

registry_context
    -> domain_models

plan_actual
    -> durable_archive read capabilities
    -> registry_context read capabilities
    -> domain_models

holded_publication
    -> durable_archive read capabilities
    -> holded_gateway
    -> domain_models

retention_release
    -> durable_archive durable-acceptance evidence
    -> synchronization/replica status read capability

<x>_persistence
    -> domain_models Protocol and persisted models only
    -> no service, rule, or policy import
```

This is not final import wiring. State 4 flows must prove each cross-module need before State 5 freezes public APIs.

---

# 5. Forbidden responsibility leaks

1. `synchronization` must never mark an invoice durably accepted merely because bytes were delivered.
2. persistence adapters must never decide Card validity, duplicate policy, retention release, or publication eligibility.
3. MCP/HTTP/local wrappers must never implement Cabinet business rules or enlarge caller capabilities.
4. `registry_context` must never rewrite the Invoice Card object decision because Registry changed.
5. `plan_actual` must never rewrite PresuPro plan facts or Invoice Card facts.
6. `holded_gateway` must never decide whether Cabinet is allowed to publish.
7. `holded_publication` must never receive or expose reusable Holded credentials.
8. `access_control` must never interpret knowledge of an entity ID as authorization.
9. `retention_release` must never treat Registry close/archive state alone as authority to delete source evidence.
10. no module may reuse `SyncNodeCredential` as local agent/service authority.

---

# 6. State 3 readiness check

State 3 is ready for State 4 flow design when:

1. every accepted State 2 invariant has one primary enforcement owner or an explicit deployment-process owner;
2. transport and storage adapters remain policy-free;
3. local agent/service authorization is separate from synchronization identity;
4. durable acceptance is separate from network delivery;
5. Registry, PresuPro, and Holded source-of-truth boundaries are preserved;
6. Holded business publication remains separate from its technical gateway;
7. source retention/release is not an incidental synchronization side effect;
8. candidate public capabilities are treated as needs, not frozen contracts;
9. no new domain entity or product behavior is introduced only to make a module convenient.

## Current assessment

The responsibility map is internally consistent with the accepted State 0–2 decisions and is ready for deterministic State 3 lint/review. State 4 must next walk the major end-to-end flows before public APIs are finalized.
