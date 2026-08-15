# State 1 repair — contract-support models

## Status

This is a bounded State 1 repair discovered while authoring State 6 exact contracts.
It introduces no new product behavior. Every type below packages an input, outcome,
or evidence shape already required by accepted State 2 rules, reviewed State 4
flows, and State 5 public operations.

These types exist so State 6 can use real project types instead of `dict`, `Any`,
implicit tuples, or transport-shaped payloads. They do not replace the existing
entity models in `01_models.md`.

---

## Model M35 — AuthenticatedPrincipalContext

Immutable authenticated-call context. It is not a credential and contains no secret.

Fields:

- `principal_id: str`;
- `principal_kind: str` — accepted values are `user`, `agent`, or `service`;
- `credential_id: str` — stable identifier of the credential used for the call;
- `authenticated_at: datetime`;
- `interaction_id: str | None`.

The current authorization store remains authoritative for revocation and capability
checks; this value does not cache authorization truth.

### Identity

value

### Identity evidence

Substitution: equal authenticated-call facts are interchangeable as context. Continuity: later authentication, revocation, or capability changes produce new context rather than mutate this value.

---

## Model M36 — AuthorizationDecision

Immutable result of checking one exact protected operation.

Fields:

- `principal_id: str`;
- `operation: str`;
- `allowed: bool`;
- `reason_code: str | None`;
- `evidence_id: str`;
- `decided_at: datetime`.

### Identity

value

### Identity evidence

Substitution: equal operation, principal, outcome, evidence, and decision-time facts carry the same authorization meaning. Continuity: every check produces an immutable result; `evidence_id` pins its proof but does not create a continuing decision object.

---

## Model M37 — SynchronizationWorkSelection

Immutable selection of one exact synchronization obligation.

Fields:

- `invoice_id: str`;
- `manifest_id: str`;
- `source_node_id: str`;
- `target_node_id: str`;
- `requested_at: datetime`.

### Identity

value

### Identity evidence

Substitution: equal obligation and endpoint facts select the same work. Continuity: a changed request or manifest produces another selection; no selection lifecycle is tracked.

---

## Model M38 — SynchronizationOutcome

Immutable public outcome preserving transport state separately from durable
acceptance.

Fields:

- `synchronization: InvoiceSynchronization`;
- `receipt: InvoiceTransferReceipt | None`;
- `durable_acceptance: DurableAcceptanceVerification | None`.

A delivered synchronization with no durable proof remains distinguishable from an
accepted import.

### Identity

value

### Identity evidence

Substitution: equal synchronization, receipt, and durable-verification facts are interchangeable as the public outcome. Continuity: it is an immutable returned composition, not the continuing synchronization entity it contains.

---

## Model M39 — SynchronizationStatusObservation

Read-only observation used by retention/release evaluation.

Fields:

- `invoice_id: str`;
- `node_id: str`;
- `synchronization_id: str | None`;
- `replica: InvoiceWorkingReplica | None`;
- `status: str`;
- `observed_at: datetime`.

The value makes no durable-acceptance claim.

### Identity

value

### Identity evidence

Substitution: equal target, status, replica, synchronization, and observation-time facts express the same observation. Continuity: later observations are new values; the referenced synchronization and replica retain their own identities.

---

## Model M40 — DurableAcceptanceVerification

Authoritative read result for exact local durable acceptance.

Fields:

- `invoice_id: str`;
- `content_hash: str | None`;
- `accepted: bool`;
- `required_source_ids: tuple[str, ...]`;
- `verified_source_ids: tuple[str, ...]`;
- `evidence_id: str | None`;
- `verified_at: datetime`.

`accepted = true` is valid only when the accepted durable-local proof is complete.

### Identity

value

### Identity evidence

Substitution: equal acceptance result, covered sources, evidence reference, and verification time are interchangeable. Continuity: re-verification creates a new immutable observation and does not mutate durable archive entities.

---

## Model M41 — LocalSourceFile

One local source-file submission before archive acceptance.

Fields:

- `filename: str`;
- `media_type: str`;
- `content: bytes`;
- `expected_source_id: str | None`;
- `expected_content_hash: str | None`.

Filename and media type never create storage/path authority.

### Identity

value

### Identity evidence

Substitution: equal submitted bytes and declared expectations are interchangeable before acceptance. Continuity: the submission has no independent history; accepted custody is represented by SourceBinary and SourceBinaryReplica entities.

---

## Model M42 — SourceAttachmentItemResult

Immutable per-file attachment outcome.

Fields:

- `filename: str`;
- `source_id: str | None`;
- `content_hash: str`;
- `result: str` — accepted values are `attached`, `already_attached`, or `rejected`;
- `safe_error_code: str | None`.

### Identity

value

### Identity evidence

Substitution: equal file, hash, source, result, and safe-error facts are interchangeable. Continuity: the outcome is issued for one attachment attempt and does not change afterward.

---

## Model M43 — SourceStatus

Read-only source-evidence status for one accepted invoice.

Fields:

- `invoice_id: str`;
- `available_source_ids: tuple[str, ...]`;
- `missing_source_ids: tuple[str, ...]`;
- `failed_source_ids: tuple[str, ...]`;
- `complete: bool`;
- `observed_at: datetime`.

### Identity

value

### Identity evidence

Substitution: equal invoice, availability sets, completeness, failures, and observation time express the same status. Continuity: later archive evidence yields a new status value.

---

## Model M44 — SourceAttachmentBatchResult

Result of one local source-attachment invocation.

Fields:

- `invoice_id: str`;
- `items: tuple[SourceAttachmentItemResult, ...]`;
- `source_status: SourceStatus`.

Partial success remains explicit through the per-item results.

### Identity

value

### Identity evidence

Substitution: equal invoice, ordered item outcomes, and resulting source status are interchangeable. Continuity: the batch result is immutable and has no identity beyond its complete contents.

---

## Model M45 — RegistryProjectObservation

One project row from the accepted full Registry observation defined by A34.

Fields:

- `project_id: str`;
- `display_name: str`;
- `address: str`;
- `status: str`;
- `registry_updated_at: datetime`.

No customer or completion fields are added.

### Identity

value

### Identity evidence

Substitution: equal Registry row facts are interchangeable as one upstream observation. Continuity: Registry changes produce another observation; continuing project identity belongs to Registry and WorkObject, not this value.

---

## Model M46 — RegistryRefreshResult

Immutable summary of one accepted full Registry refresh.

Fields:

- `projects: tuple[RegistryProjectSnapshot, ...]`;
- `work_objects: tuple[WorkObject, ...]`;
- `observed_at: datetime`.

Absence from the refresh does not imply deletion.

### Identity

value

### Identity evidence

Substitution: equal accepted snapshots, work-object results, and observation time express the same refresh result. Continuity: each refresh returns a new immutable summary while contained entities retain their own identities.

---

## Model M58 — RegistryContextRepository

Runtime persistence port owned by `module:registry_context`. It exposes only the
state operations required to apply one complete Registry observation, append
immutable assignment-validation evidence, and read accepted Registry context.

The port is implemented by the Backend PostgreSQL adapter and is supplied by
composition. Business functions do not open database connections, read database
environment variables, or choose transaction policy.

### Kind

interface

### Boundary semantics

- `apply_refresh` atomically persists the complete set of new project snapshots
  and resulting WorkObjects for one observation; no partial refresh becomes
  visible.
- WorkObject merge decisions are made by `module:registry_context` before the
  repository is called. The repository does not infer deletion, completion, or
  replacement projects.
- `append_assignment_validation` is append-only issued evidence and rejects an
  identity conflict instead of overwriting history.
- read methods return only committed records and never synthesize domain values.
- the concrete implementation uses the shared PostgreSQL runtime transaction
  mechanism and fails closed when that runtime is unavailable.

---

## Model M59 — HoldedHttpClient

Runtime transport port for the accepted Holded purchase API subset. The concrete
Backend implementation owns HTTPS request construction, credential injection,
timeouts, bounded response parsing, and safe translation of provider failures.
It does not own logical publication eligibility, automatic retry permission, or
durable attempt history.

### Kind

interface

---

## Model M60 — HoldedGatewayRepository

Durable technical-evidence port owned by `module:holded_gateway`. It exposes the
minimum operations needed to prove whether the single create call has already
been started, append its immutable outcome, and append read-only lookup evidence.

### Kind

interface

### Boundary semantics

- `begin_attempt` durably records the stable attempt identity before HTTP POST
  and rejects a conflicting or already-started identity;
- `finish_attempt` appends one terminal technical outcome without overwriting the
  start evidence;
- lookup evidence is append-only;
- reads return committed evidence only;
- the concrete implementation uses the shared PostgreSQL transaction mechanism
  and never decides publication success.

---

## Model M61 — CredentialProvider

Application-lifecycle secret boundary used only by concrete runtime constructors.
It resolves a closed allow-list of deployment-owned secret keys without placing
secret values in deterministic config, domain models, business-module imports,
or ordinary logs.

### Kind

interface

### Boundary semantics

- only keys supplied by the composition binding may be resolved;
- missing, empty, or inaccessible required secrets fail construction;
- secret values are returned only to the concrete adapter constructor that owns
  the corresponding credential boundary;
- the provider is never exposed to HTTP handlers or business operations.

---

## Model M62 — HoldedPurchaseLookupRecord

Immutable restart-surviving record that binds one technical Holded lookup
observation to its stable publication attempt.

Fields:

- `record_id: str`;
- `publication_attempt_id: str`;
- `evidence: HoldedPurchaseLookupEvidence`.

### Identity

entity

### Identity evidence

Substitution: two records with different record ids remain distinct audit events
even when their lookup evidence is equal. Continuity: the issued record is
immutable; another lookup creates another record.

### Persistence candidate

Durable issued evidence.

---

## Model M47 — PresuProEstimateObservation

One current PresuPro estimate observation presented for immutable snapshot
acceptance under A43.

Fields:

- `presupro_estimate_id: str`;
- `project_id: str`;
- `presupro_updated_at: datetime`;
- `status: str`;
- `locked: bool`;
- `canonical_content: str`;
- `observed_at: datetime`.

`canonical_content` is the deterministic serialized estimate content used for
content hashing and snapshot construction; it is not a generic application DTO.

### Identity

value

### Identity evidence

Substitution: equal upstream estimate facts, canonical content, and observation time are interchangeable. Continuity: a changed PresuPro observation becomes another value; accepted continuity is represented by EstimateSnapshot.

---

## Model M48 — HoldedPurchasePayloadItem

Typed item in the currently accepted Holded purchase-create contract A51.

Fields:

- `name: str`;
- `desc: str | None`;
- `units: Decimal`;
- `subtotal: Decimal`;
- `discount: Decimal | None`;
- `tax: Decimal`;
- `sku: str | None`.

### Identity

value

### Identity evidence

Substitution: equal typed purchase-line fields are interchangeable in the outbound contract. Continuity: it is immutable payload content with no independent lifecycle.

---

## Model M49 — HoldedPurchaseAttemptPayload

Typed first-publication payload accepted by A51/A52.

Fields:

- `apply_contact_defaults: bool`;
- `contact_code: str`;
- `contact_name: str`;
- `desc: str`;
- `date: str`;
- `approve_doc: bool`;
- `items: tuple[HoldedPurchasePayloadItem, ...]`;
- `invoice_num: str`;
- `currency: str`.

The `desc` field carries the stable non-financial attempt marker required by A52.

### Identity

value

### Identity evidence

Substitution: equal complete create payloads are interchangeable for the same technical call. Continuity: attempt history belongs to HoldedPublicationAttempt; this payload does not change independently.

---

## Model M50 — HoldedPurchaseLookupEvidence

Immutable technical result of bounded read-only Holded recovery lookup.

Fields:

- `attempt_marker: str`;
- `match_count: int`;
- `document_id: str | None`;
- `raw_status: int | None`;
- `business_verified: bool`;
- `outcome: str` — accepted values are `verified_match`, `payload_mismatch`,
  `outcome_unknown`, or `duplicate_conflict`;
- `observed_at: datetime`.

It contains technical evidence only; `module:holded_publication` owns the logical
publication classification.

### Identity

value

### Identity evidence

Substitution: equal lookup target, matches, verification, outcome, and observation time are interchangeable technical evidence. Continuity: repeated recovery lookup issues another observation rather than mutating prior evidence.

---

## Model M51 — VpsReleaseRequestContext

Immutable context of one explicit manual release evaluation.

Fields:

- `requested_by: ActorReference`;
- `requested_at: datetime`;
- `working_set_id: str | None`.

At least one of Registry `project_id` (the operation argument) or `working_set_id`
must identify the exact target before evaluation.

### Identity

value

### Identity evidence

Substitution: equal requester, request time, and working-set target carry the same request context. Continuity: it is immutable input to evaluation and is not a tracked release request entity.

---

## Model M52 — VpsReleaseEvaluation

Immutable allow/block evaluation for one exact VPS working set.

Fields:

- `project_id: str`;
- `working_set_id: str`;
- `allowed: bool`;
- `durable_evidence: tuple[DurableAcceptanceVerification, ...]`;
- `sync_observations: tuple[SynchronizationStatusObservation, ...]`;
- `blocked_reason_code: str | None`;
- `evaluated_at: datetime`.

No physical deletion occurs during evaluation.

### Identity

value

### Identity evidence

Substitution: equal target, allow/block result, complete evidence, reason, and evaluation time are interchangeable. Continuity: changed evidence requires a new evaluation; no evaluation state is mutated.

---

## Model M53 — VpsReleaseDecision

Immutable recorded manual release decision.

Fields:

- `decision_id: str`;
- `project_id: str`;
- `working_set_id: str`;
- `actor: ActorReference`;
- `evaluation: VpsReleaseEvaluation`;
- `result: str` — accepted values are `authorized`, `blocked`, `idempotent`, or
  `conflict`;
- `decided_at: datetime`.

The physical VPS adapter consumes an authorized decision but cannot broaden its
target or weaken its evidence.

### Identity

entity

### Identity evidence

Substitution: decisions with different `decision_id` values are not interchangeable even when their projected target and result match, because each records a distinct authorization obligation and provenance. Continuity: an equivalent repeated manual-release request resolves to the existing decision with the same stable `decision_id`; the issued decision remains immutable.

---

## Model M55 — PlanActualRequest

Immutable application request that pins the accepted evidence used for one plan/actual calculation.

Fields:

- `invoice_revisions: tuple[InvoiceCardRevisionReference, ...]`;
- `project_id: str`;
- `estimate_snapshot_id: str`;
- `match_ids: tuple[str, ...]`;
- `assumption_ids: tuple[str, ...]`.

The DTO carries identities only; it never embeds mutable replacements for accepted source records.

### Identity

value

### Identity evidence

Substitution: equal pinned revision, project, snapshot, match, and assumption identities request the same calculation. Continuity: changing any pinned evidence creates another request; no request history or mutation is tracked.

### Meaning

The complete evidence selection for a reproducible plan/actual calculation.

### Source of truth

Constructed by the application caller from accepted Cabinet evidence identities.

### Lifecycle

No independent lifecycle; consumed as immutable calculation input.

### Persistence candidate

Runtime input; durable persistence is not required.

### Open questions

None for identity closure.

---

## Model M56 — IncompleteSourceAcceptance

Immutable auditable decision permitting one exact confirmed Card revision to enter normal archive truth with explicitly incomplete source evidence.

Fields:

- `acceptance_id: str`;
- `card_revision: InvoiceCardRevisionReference`;
- `missing_source_references: tuple[ContentReference, ...]`;
- `actor: ActorReference`;
- `reason: str`;
- `decided_at: datetime`.

### Identity

entity

### Identity evidence

Substitution: decisions with different acceptance ids, actors, revisions, or missing-source sets are not interchangeable. Continuity: replay of the same accepted decision resolves to the existing immutable evidence identified by `acceptance_id`.

### Meaning

Explicit authorization evidence for accepting incomplete source custody without claiming missing bytes were stored.

### Source of truth

Cabinet Backend durable archive records the authorized decision.

### Lifecycle

Issued immutable evidence; later attachment changes source completeness but never erases this history.

### Persistence candidate

Durable issued decision evidence.

### Open questions

None for identity closure.

---

## Model M57 — SourceLossDecision

Immutable evidence that an authorized actor declared exact required source references unrecoverable.

Fields:

- `decision_id: str`;
- `invoice_id: str`;
- `source_references: tuple[ContentReference, ...]`;
- `actor: ActorReference`;
- `explanation: str | None`;
- `decided_at: datetime`.

### Identity

entity

### Identity evidence

Substitution: decisions with different ids, actors, targets, or affected sources are not interchangeable. Continuity: one issued loss decision remains immutable in history even if later verified attachment restores source completeness.

### Meaning

Auditable evidence supporting the `source_lost` archive status for exact missing originals.

### Source of truth

Cabinet Backend durable archive records the authorized manual decision.

### Lifecycle

Issued immutable evidence; may later be historically superseded by recovered verified custody without deletion.

### Persistence candidate

Durable issued decision evidence.

### Open questions

None for identity closure.
