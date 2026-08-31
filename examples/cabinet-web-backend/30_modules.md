# State 3 — Cabinet Web Backend module boundaries

These boundaries are derived from the accepted State 2 rules and the closed
first-release capability catalogue. A module owns one stable reason to change.
Transport modules are intentionally thin; they do not duplicate application
policy. Dotted capability names from A16 remain product catalogue values and
are not assumed to be Python function names.

## `models`

### Owns

The immutable vocabulary and typed values for M01–M29: identifiers, revisions,
hashes, validation results, Cards, sources, effects, synchronization evidence,
Registry replicas, conflicts, and bounded outcome types.

### Knows

Only value-level invariants that can be checked without storage, credentials,
transport, clocks, or deployment configuration.

### Must not own

Authorization, persistence, workflow transitions, retry behavior, file I/O,
transport serialization, configuration loading, or clock-dependent policy.

### Depth assessment

kind: deep
hidden mechanism: frozen typed value forms (extra=forbid) that make every cross-module payload valid by construction

This is a deliberately dependency-free type kernel. It keeps the same language
across all runtime modules without becoming an anemic policy dumping ground.

## `card_workspace`

### Owns

Canonical Card identity and revision history; canonical-content hashing;
expected-revision commits; type-validator selection; and stable read/search
projections over Provider, Client, Project, and Invoice Cards. It is the primary
owner of A01.

### Knows

M03 and M07–M10, the distinction between canonical and derived facts, the
validation interfaces supplied by Invoice and Project specialists, and the
retained `Clock` port that supplies each revision observation.

### Must not own

Credentials, confirmation UX, idempotency records, source bytes, transport,
Registry ownership, synchronization receipts, or deployment policy.

### Hides

Persistence layout, revision locking, canonical serialization and hashing,
type-aware validator routing, and projection rebuilds.

### Candidate public capabilities

```text
get_card_revision
commit_card_revision
search_provider_cards
list_project_cards
```

### Depth assessment

kind: deep
hidden mechanism: canonical Card revision custody: content-hash identity with optimistic current-selector movement

A small revision-safe surface hides every storage and canonicalization choice.
Invoice and Project behavior depends on this boundary rather than on tables or
files.

## `invoice_catalogue`

### Owns

Revision-exact Invoice reads: enumerating current Invoice Card references,
loading and parsing each canonical revision as `InvoiceCardV1`, indexing
working-set availability for the read views, and duplicate-candidate discovery
under `rules.invoice_duplicate_matching`. It owns `ValidationRejectedError`, the
rejection type every Invoice module raises, because it is the lowest Invoice
module in the dependency order.

### Knows

M05, M07–M11 read projections, `rules.invoice_workspace.card_type` and the
duplicate-matching policy, and the read-only CabinetUnitOfWork query surface.

### Must not own

Card commits, validation checks, lifecycle transitions, authorization, effect
idempotency, source custody, or transfer packaging.

### Hides

Unit-of-work open/begin/rollback sequencing for reads, canonical-JSON parsing,
working-set status indexing, search filtering and ordering, cursor derivation,
and duplicate signal normalization and ordering.

### Candidate public capabilities

```text
search_invoices
get_invoice
find_invoice_duplicates
```

### Depth assessment

kind: deep
hidden mechanism: the invoice read model: canonical revision parsing with deterministic search and duplicate projection

kind: deep
hidden mechanism: the revision-exact Invoice read model — one rolled-back
CabinetUnitOfWork per read, canonical revision parsing, working-set indexing,
and duplicate-signal matching shared by every read capability.

## `invoice_validation`

### Owns

Draft-proposal parsing and provenance checks, and the declared-order evaluation
of `rules.invoice_workspace.validation_checks` producing ordered
`ValidationIssue` tuples and the exact duplicate result. It performs no write.

### Knows

`InvoiceCardV1` field semantics, `rules.invoice_workspace.validation_*`,
`rules.invoice_workspace.rejection_codes.validation`, and the catalogue's
duplicate discovery capability.

### Must not own

Card commits, lifecycle transitions, authorization, revision reads other than
duplicate discovery, or any persistence.

### Hides

Rule evaluation order, indexed field-path construction, issue ordering, and the
proposal-to-invoice consistency checks.

### Candidate public capabilities

```text
prepare_invoice_draft
validate_invoice
```

### Depth assessment

kind: deep
hidden mechanism: ordered evaluation of the declared invoice validation rules over one candidate

kind: deep
hidden mechanism: declared-order rule evaluation over a parsed InvoiceCardV1
with indexed issue construction, shared by proposal preparation and validation.

## `invoice_lifecycle`

### Owns

Invoice lifecycle transitions draft → confirmed → archived and their successor
revisions for payment recording and source-metadata attachment: authorization
and confirmation-binding checks, exact-revision read-modify-write through the
catalogue and validator, `CardRevisionCommitCommand` construction, and the
atomic confirmation producer edge that creates or idempotently retains the exact
`InvoiceWorkingSetItem` and `InvoiceTransferManifest` consumed by local-node
discovery, including M29 assignment-observation production.

### Knows

M05, M07–M11 mutation semantics, `rules.invoice_workspace.lifecycle`,
`rules.invoice_workspace.rejection_codes`, the manifest and working-set policy,
and the revision-safe commit port exposed by `card_workspace`, plus the retained
`Clock` port used once for each operation-level expiry comparison.

### Must not own

Generic Card persistence, raw source custody, ChatGPT confirmation binding,
authorization policy, effect idempotency, read projections, validation rules,
or local transfer packaging.

### Hides

Transition rules, successor derivation, expected-revision enforcement,
manifest and working-set hashing, and the single-transaction sequencing that
keeps Card, manifest, and working set atomic.

### Candidate public capabilities

```text
create_invoice_draft
update_invoice_draft
confirm_invoice
record_invoice_payment
attach_invoice_source_metadata
archive_invoice
```

### Depth assessment

kind: deep
hidden mechanism: guarded invoice lifecycle transitions that commit successors together with transfer evidence

kind: deep
hidden mechanism: the Invoice lifecycle state machine — exact-revision
read-modify-write, validation before commit, and atomic Card/manifest/working-set
commitment shared by every mutation capability.

## `project_workspace`

### Owns

Project summaries, estimate validation and attachment, shopping-list derivation
and persistence, and the existing relationships among M09, M11, M12, and M13.

### Knows

Canonical Project revisions and the typed estimate and shopping-list models.

### Must not own

Registry master data, Invoice transfer, generic Card revision storage,
authorization, or transport concerns.

### Hides

Estimate normalization and validation, shopping-list derivation, project
summary projection, and stale-project revision checks.

### Candidate public capabilities

```text
get_project_summary
validate_estimate
derive_shopping_list
attach_project_estimate
save_shopping_list
```

### Depth assessment

kind: deep
hidden mechanism: project Card mutation with estimate and shopping-list snapshot reconciliation

Five project use cases hide the dependency graph between estimates, lists, and
Project revisions without pretending Registry snapshots are Project facts.

## `capability_policy`

### Owns

The closed A16 catalogue, semantic operation classes, channel visibility, and
the rule that unknown or confused capability names never dispatch.

### Knows

Human read/proposal, human effect, local synchronization, and protected
operator capability sets, plus which classes require authorization,
idempotency, and confirmation.

### Must not own

Business operation implementations, dynamic routing, arbitrary operation
names, credentials, transport parsing, Card state, wall-clock access,
initialization timestamps, or any other clock-derived state.

### Hides

The fixed capability-to-class and capability-to-channel matrix and exact-name
lookup.

### Candidate public capabilities

```text
resolve_capability
list_channel_capabilities
```

### Depth assessment

kind: deep
hidden mechanism: closed capability-catalogue resolution: exact channel/name matching with protected-operator exclusion

The tiny immutable API hides a security-sensitive matrix used by every ingress
boundary. It is policy, not a generic dispatcher.

## `chatgpt_interaction`

### Owns

The A02 proposal/effect boundary for the primary ChatGPT UI: reviewable
proposals, exact-revision confirmation binding, warning acknowledgement,
confirmation expiry or decline, and truthful composite Card/source/sync
outcomes.

### Knows

The authenticated owner context, resolved capability class, typed application
ports, M03 revisions, M04 validation, and M16 effect results.

### Must not own

OCR, model confidence, arbitrary tool dispatch, Card persistence, credential
verification, file storage, synchronization state, or domain validation.

### Hides

Plugin request/result projection, proposal tokens, exact-target confirmation
binding, acknowledgement sets, and safe combination of partial outcomes.

### Candidate public capabilities

```text
prepare_chatgpt_proposal
confirm_chatgpt_effect
report_composite_outcome
```

### Depth assessment

kind: deep
hidden mechanism: two-step effect confirmation: proposal digest issuance and exact matching before any mutation

Three interaction operations hide the full safety protocol between a
probabilistic conversational UI and deterministic Cabinet capabilities.

## `credential_vault`

### Owns

The peppered bearer-secret custody mechanics (`module:credential_vault`) for A11: bearer parsing of the
`<credential_id>.<secret_material>` shape, verifier derivation with the
configured pepper, cryptographically random credential minting, timing-safe
verification of a presented bearer against the persisted record, and the
idempotent retirement transition of a credential record.

### Knows

The bearer shape, the configured pepper, `AccessCredentialRecord` identity and
status vocabulary, the operation-scoped `CabinetUnitOfWork` port for credential
records, and timezone-aware UTC issuance timestamps.

### Hides

Secret generation entropy, verifier derivation, and timing-safe comparison; no
plaintext secret is ever persisted, logged, or retained after return.

### Must not own

Principal or node subject resolution, authorization decisions, throttle state,
audit emission, transactions (the caller owns the UoW), or any transport
surface.

### Candidate public capabilities

```text
parse_bearer_credential
derive_credential_verifier
mint_credential
verify_bearer_credential
retire_credential
```

### Depth assessment

kind: deep
hidden mechanism: peppered bearer-secret custody: minting, timing-safe verification, and retirement of credential records

## `abuse_throttle`

### Owns

The authentication failure-throttle state machine (`module:abuse_throttle`) for A11: abuse-context hash
derivation, locked acquisition of `AuthenticationThrottleState`, the active
throttle decision, and the failure and success transitions with their delay and
block latches.

### Knows

`AuthenticationThrottleState` identity and counters, the configured pepper for
context hashing, the operation-scoped `CabinetUnitOfWork` port for throttle
records, timezone-aware UTC observation timestamps, and the declared failure
thresholds.

### Hides

Threshold arithmetic, delay and block latch derivation, and context hashing;
callers see only acquire, decide, and transition operations.

### Must not own

Credential verification, principal resolution, audit emission, transactions
(the caller owns the UoW), or any transport surface.

### Candidate public capabilities

```text
derive_abuse_context_hash
acquire_throttle_state
throttle_active
register_authentication_failure
register_authentication_success
```

### Depth assessment

kind: deep
hidden mechanism: the configured wall-clock failure-window throttle state machine over locked per-context state

## `access_control_errors`

### Owns

The closed public refusal taxonomy shared by the access-control engines,
facade, router error policy, and callers: AuthenticationRequiredError,
AuthenticationThrottledError, and AuthorizationDeniedError.

### Knows

Only the three stable exception identities and their boundary meanings.

### Hides

One cycle-free exception boundary so deep engines never import their facade and
the facade may re-export the same exact types without redefining them.

### Must not own

Authentication, authorization, lifecycle policy, persistence, transactions,
status codes, response bodies, or recovery behavior.

### Candidate public capabilities

```text
AuthenticationRequiredError
AuthenticationThrottledError
AuthorizationDeniedError
```

### Depth assessment

kind: deep
hidden mechanism: stable cycle-free refusal type identity across engines, facade, and transport

## `security_evidence`

### Owns

Fresh collision-resistant identity issuance for append-only M111 security audit
events shared by the access-control engines.

### Knows

The M111 evidence identity rule and UUID4 generation primitive.

### Hides

Audit-event identity entropy and the prohibition on reusing stable domain or
credential identities as security-event primary keys.

### Must not own

Audit policy, event classification, persistence, transactions, credentials,
principal resolution, authorization, or transport.

### Candidate public capabilities

```text
issue_security_audit_id
```

### Depth assessment

kind: deep
hidden mechanism: collision-resistant append-only security-event identity issuance

## `authentication_admission`

### Owns

The A11 channel-authentication transaction: caller-independent bounded abuse
classification, credential verification, throttle transitions, exact
M02/M17 subject resolution, reciprocal local-node contract validation, and
secret-free authentication audit evidence.

### Knows

M02, M17, M39, M108, M110 and M111; `credential_vault`, `abuse_throttle`, and
`security_evidence`; the UoW factory, pepper, Clock, channel vocabulary, and
`cabinet-web-sync-v1`.

### Hides

The complete commit-on-bounded-refusal versus rollback-on-unexpected-failure
protocol and construction of one complete authenticated M39.

### Must not own

Capability grants, principal enrollment, credential rotation/revocation,
transport extraction, Card policy, or caller-supplied abuse buckets.

### Candidate public capabilities

```text
derive_authentication_abuse_context
authenticate_channel_request
resolve_trusted_browser_owner
```

### Depth assessment

kind: deep
hidden mechanism: channel authentication transaction joining credential, throttle, M02/M17 binding, and audit evidence

## `capability_grants`

### Owns

The A03 exact capability-grant mechanism: complete scope canonicalization,
current principal/node lifecycle revalidation, exact grant evaluation, and
idempotent protected grant provisioning with audit evidence.

### Knows

M02, M17, M39, M65, M109 and M111; the closed A16 catalogue, UoW factory,
Clock, `security_evidence`, and the canonical `cabinet-scope-v1` encoding.

### Hides

Collision-resistant scope identity, exact grant lookup, lifecycle revalidation,
provisioning idempotency, and transaction rollback boundaries.

### Must not own

Credential verification, throttling, principal enrollment, credential
lifecycle, transport, or business mutations.

### Candidate public capabilities

```text
derive_entity_scope_key
evaluate_capability_grant
persist_capability_grant
```

### Depth assessment

kind: deep
hidden mechanism: exact persisted capability matrix over canonical complete entity scope

## `principal_lifecycle`

### Owns

Protected initial-owner bootstrap, later principal enrollment, atomic credential
rotation, and credential revocation with separately authenticated M39 operator
proof and append-only audit evidence.

### Knows

M02, M39, M59, M61, M85, M108 and M111; UoW factory, pepper, Clock,
`credential_vault`, and `security_evidence`.

### Hides

The one-time empty-installation bootstrap exception, owner/operator proof,
credential locking, atomic replacement/retirement, one-time bearer return, and
rollback on every refusal or unexpected failure.

### Must not own

Request authentication, abuse throttling, capability evaluation/provisioning,
transport, node synchronization, or Card policy.

### Candidate public capabilities

```text
bootstrap_or_enroll_principal
rotate_principal_credential
revoke_principal_credential
```

### Depth assessment

kind: deep
hidden mechanism: protected principal and credential lifecycle transaction with one-time secret return

## `access_control`

### Owns

The stable A03/A11 public access-control facade and its retained dependency
bundle. It exposes authentication, authorization, principal enrollment, grant
provisioning, credential rotation/revocation, and principal resolvers while
delegating each hidden mechanism to its named deep module.

### Knows

The retained `CabinetUnitOfWorkFactory`, credential pepper and `Clock`, M39
shape, channel labels, owner/local-node resolver postconditions, and the exact
call signatures of `authentication_admission`, `capability_grants`, and
`principal_lifecycle`.

### Must not own

Credential verification, throttle transitions, transactions, grant storage,
scope canonicalization, lifecycle mutation, audit identity generation,
business identity, Card mutations, transport sessions, or domain policy.

### Hides

The stable public surface, dependency projection into the three deep engines,
and fail-closed resolver postconditions. It does not reproduce or partially
inline any delegated transaction.

### Candidate public capabilities

```text
authenticate_request
authorize_capability
enroll_principal
provision_capability_grant
rotate_credential
revoke_credential
```

### Depth assessment

kind: facade
delegates to: `authentication_admission`, `capability_grants`, `principal_lifecycle`

The module remains the accepted public A03 access-control boundary, but each
operation is now a typed delegation or resolver projection. It remains
independent of HTTP and MCP and contains no second copy of a deep mechanism.

## `effect_journal`

### Owns

The A04 principal-scoped idempotency identity, canonical request binding,
atomic expected-revision effect commit, committed-result replay, conflicting
reuse rejection, and unknown-outcome reconciliation state.

### Knows

M03 and M16, operation class, exact target, request hash, principal scope, an
injected mutation transaction, and the retained `Clock` port for effect
evidence timestamps.

### Must not own

Domain validation, authorization, user confirmation, transport retry loops,
source content, or synchronization-specific receipt truth.

### Hides

Durable effect records, concurrency locking, transaction boundaries, replayed
result storage, request canonicalization, and recovery after timeouts.

### Candidate public capabilities

```text
begin_effect
commit_effect
reconcile_effect
```

### Depth assessment

kind: deep
hidden mechanism: the principal-scoped idempotency journal: canonical request binding with commit, replay, and conflict outcomes

The three operations hide difficult concurrency and retry behavior shared by
otherwise independent domain effects.

## `source_custody`

### Owns

M05/M06/M14/M15 lifecycle; bounded non-executable original-byte validation and
immutable storage; single-use upload handoffs; authorized retrieval; and the
explicit evidence-backed release of eligible VPS working bytes.

### Knows

Exact Card/source/revision targets, approved media catalogue, A13 limits,
receipt/hash verification needed by A10, authorized human context, and the
retained `Clock` port for custody evidence timestamps.

### Must not own

OCR, previews, Card confirmation, local durable acceptance, filenames as paths,
public static serving, or automatic cleanup from inactivity or Registry status.

### Hides

Content identification, hashing, server-chosen storage keys, immutable blob
publication, handoff bearer verification, release eligibility, and retained
custody evidence.

### Candidate public capabilities

```text
issue_upload_handoff
store_original_source
retrieve_original_source
release_vps_working_set
```

### Depth assessment

kind: deep
hidden mechanism: the verified byte-custody chain: staged upload, atomic commit, and verified re-read through the byte-store port

Four custody operations hide file-system safety, concurrent handoff use, byte
identity, and conservative release without becoming a document processor.

## `web_gateway`

### Owns

The A07 private-listener browser boundary: same-origin mutation enforcement,
CSRF context, inert output encoding, security headers, bounded upload/download
HTTP handling, and safe response projection.

### Knows

Authenticated browser context, typed ports for application capabilities and
source custody, and the retained `Clock` port for upload-boundary observations.
It knows no persistence representation.

### Must not own

Authorization decisions, domain validation, storage paths, Card mutations,
credential lifecycle, or plugin/local-node authentication.

### Hides

HTTP parsing, request size enforcement at the application edge, CSRF tokens,
content disposition, response headers, template escaping, and stable error
mapping.

### Candidate public capabilities

```text
serve_browser_request
accept_source_upload
serve_source_download
```

### Depth assessment

kind: deep
hidden mechanism: bounded browser ingress: CSRF and handoff verification with bounded streaming into custody

This is intentionally a thin but security-critical adapter. Its public surface
is transport-shaped and all business decisions remain behind typed ports.

## `sync_gateway`

### Owns

The local-node transport boundary: bounded request parsing, compatibility
observation, machine authentication handoff, and bounded response/error
serialization; each synchronization capability enters through its own typed
route, never through a generic dispatch envelope.

### Knows

M17 and M26, the sync-only A16 catalogue, A13 request limits, and the
access-control port that proves the active local node.

### Must not own

Human capabilities, arbitrary proxying, package or catalogue truth, credential
verification, Card mutation, or last-write-wins conflict policy.

### Hides

Wire framing, version negotiation input, timeout boundary, request correlation,
safe error projection, and rejection of unknown sync operations.

### Candidate public capabilities

```text
observe_sync_compatibility
```

### Depth assessment

kind: facade
delegates to: `access_control`

This is an intentionally thin trust-boundary adapter. Protocol state belongs to
the exchange modules, so transport replacement cannot rewrite sync policy.

## `invoice_exchange`

### Owns

The A08 evening pull protocol: Invoice-only work discovery from the durable
working-set producer, immutable M21 manifests, node-scoped M22 issuance, exact
`VpsInvoiceTransferPackage` delivery (canonical metadata plus streamed bytes),
M23 receipt acceptance, unchanged M29 transport, reconciliation, and explicit
M28 conflict outcomes.

### Knows

Available exact Invoice revisions and source membership, active node identity,
content hashes, contract compatibility, immutable source retrieval ports, and
the retained `Clock` port for discovery and issuance observations.

### Must not own

Provider/Client/Project export, local import decisions, automatic VPS release,
Card editing, credentials, or transport-success-as-durable-acceptance.

### Hides

Manifest canonicalization against the accepted `cabinet_backend` wire models,
package assembly, issuance locking, repeat pulls, receipt matching, unknown-
outcome recovery, and incompatibility/conflict classification.

### Candidate public capabilities

```text
discover_invoice_work
pull_invoice_package
record_invoice_transfer_receipt
reconcile_invoice_transfer
get_invoice_transfer_status
```

### Depth assessment

kind: deep
hidden mechanism: manifest-driven invoice transfer: issuance, package streaming, and receipt/reconciliation state

Four protocol operations hide immutable package construction and distributed
delivery ambiguity while keeping the local Backend authoritative for import.

## `registry_replica`

### Owns

The A09 complete Registry catalogue acceptance, canonical hash verification,
idempotent acknowledgement, monotonic source-observation rule, atomic replica
commit/current selection, and freshness projection.

### Knows

M18–M20 and M24–M25, authenticated node identity, contract compatibility, and
the current accepted catalogue observation.

### Must not own

Registry master data, Project Card facts, inferred project deletion/completion,
transport parsing, credentials, or partial-current state.

### Hides

Catalogue ordering and hash checks, replay detection, transactional replica
replacement, stale-publication refusal, acknowledgements, and freshness
calculation.

### Candidate public capabilities

```text
publish_registry_catalogue
get_current_registry_catalogue
```

### Depth assessment

kind: deep
hidden mechanism: registry catalogue replication: published snapshot acceptance with a current-selector latch

Two operations hide the entire atomic replica protocol and preserve the
external ownership boundary even while the local system is offline.

## `data_provider`

### Owns

The single deterministic home of declared scalar policy constants and closed
policy tables — identifier prefixes, hash-algorithm identifiers, protocol
versions, reported status scalars, the A16 capability catalogue rows, the A01
validation check tables, and the A05 byte-signature catalogue — emitted as
typed module constants from the closed `rules.data_provider_backend` IR.

### Knows

Only the closed data-provider IR: constant names, their declared value types,
their declared values, and the State 1 row models the record tables
instantiate.

### Must not own

Behavior of any kind: no lookups, no validation, no interpretation, no
authorization, no defaults beyond the declared values, and no second home for
a value already owned by `models` or `config`.

### Hides

The literal values themselves. Consumers import symbols and receive the
access signature; the values never enter an LLM prompt (SPEC_STANDARD §15.9).

### Public surface

```text
CAPABILITY_GRANTS
COMPONENT_STATUS_SEPARATOR
CONTENT_FORMAT_SIGNATURES
CUSTODY_OPERATION_KIND
DUPLICATE_CANDIDATE_FIELD_ORDER
DUPLICATE_CANDIDATE_FIELD_SOURCES
DUPLICATE_INVOICE_ID_MATCH_REQUIRES_EXACT_IDENTITY
DUPLICATE_MINIMUM_MATCH_FIELDS
DUPLICATE_NO_COMPARABLE_FIELDS_RESULT
DUPLICATE_POLICY_VERSION
DUPLICATE_REASON_CODE_PREFIX
DUPLICATE_STABLE_ORDER
ESTIMATE_CHECKS
ESTIMATE_STATUS_ACCEPTED
ESTIMATE_VALIDATION_ISSUE_SEVERITY
INVOICE_CARD_TYPE
INVOICE_CARD_VERSION
INVOICE_VALIDATION_CHECKS
ISSUANCE_ID_PREFIX
MANIFEST_CARD_REVISION_COUNT
MANIFEST_HASH_ALGORITHM
MANIFEST_HASH_FIELDS
MANIFEST_ID_PREFIX
MANIFEST_VERSION
NODE_CONTRACT_VERSION
PENDING_CUSTODY_STATUS
PROJECT_CARD_TYPE
PROTECTED_OPERATOR_CAPABILITIES
PROVIDER_CARD_TYPE
READINESS_COMPONENTS
REQUEST_HASH_ALGORITHM
REVISION_HASH_ALGORITHM
REVISION_OBSERVED_STATUS
SHOPPING_LIST_ID_PREFIX
SHOPPING_LIST_ID_SEPARATOR
SHOPPING_LIST_STATUS_ISSUED
SOURCE_NOT_STORED_STATUS
SOURCE_PROVENANCE_KEY
STORED_CUSTODY_STATUS
SYNCHRONIZATION_UNAVAILABLE_STATUS
VALIDATION_ISSUE_MESSAGE
VALIDATION_ISSUE_ORDER
VALIDATION_ISSUE_SEVERITY
WORKING_SET_AVAILABLE_STATUS
WORKING_SET_ID_PREFIX
```

### Depth assessment

kind: deep
hidden mechanism: deterministic compilation of declared policy data into typed importable constants

The module deliberately has no callable surface. Its implementation is
compiler-owned; project differences live entirely in accepted structured IR.

## `runtime_settings`

### Owns

The one deterministic conversion of declared deployment inputs into the
immutable M135 `RuntimeSettings` snapshot accepted by A18.

### Knows

M134–M135 and only the closed runtime-settings data IR: declared input names,
types, requiredness, defaults, normalization, targets, and project-declared
cross-setting constraints.

### Must not own

Business policy, readiness checks, service construction, storage access,
request handling, product-specific implicit constraints, or a second settings
provider.

### Hides

Environment lookup, normalization, positive-integer parsing, default
selection, typed construction, and fail-closed validation ordering.

### Candidate public capabilities

```text
load_runtime_settings
```

### Depth assessment

kind: deep
hidden mechanism: deterministic runtime-input compilation into one validated immutable settings snapshot

The module deliberately has one narrow entrypoint. Its implementation is
compiler-owned; project differences live entirely in accepted structured IR.

## `runtime_control`

### Owns

Readiness gating, backup execution metadata, and isolated restore verification
exposed only at the protected operator boundary.

### Knows

The already validated M135 runtime settings snapshot, durable-store health,
edge/runtime limit agreement, contract compatibility, backup coverage, and
restore cadence.

### Must not own

Domain defaults, per-request safety overrides, public operator endpoints,
ordinary business exports, secrets in backup payloads, or deployment release
approval.

### Hides

Startup dependency checks, health aggregation, backup-set enumeration, restore
drill orchestration, and readiness reasons.

### Candidate public capabilities

```text
evaluate_readiness
verify_backup_restore
```

### Depth assessment

kind: deep
hidden mechanism: readiness and recovery proof over one unit-of-work probe and byte-store verification

The runtime exposes a narrow readiness/operator surface while hiding startup and
recovery coordination across all durable modules. Dependency release gating
remains a deployment process, not runtime behavior.

## State 3 boundary review

- Canonical data is owned once: Cards by `card_workspace`, bytes by
  `source_custody`, transfer evidence by `invoice_exchange`, and external
  catalogue replicas by `registry_replica`.
- `capability_policy`, `access_control`, and `effect_journal` answer different
  questions: what exists, who may invoke it, and whether one logical effect has
  already happened.
- ChatGPT is the primary interaction boundary, but it owns no extracted fact,
  credential, Card, file, or synchronization truth.
- Browser and local-node transports are explicit trust boundaries with typed
  downstream ports and no generic operation, filesystem, URL, query, or shell
  surface.
- A12 remains cross-cutting because every ingress and persistence boundary must
  preserve data/code separation. A14 and A15 are release/evidence obligations,
  not invented runtime services.
