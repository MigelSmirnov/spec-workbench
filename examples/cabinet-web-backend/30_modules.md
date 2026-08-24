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

This is a deliberately dependency-free type kernel. It keeps the same language
across all runtime modules without becoming an anemic policy dumping ground.

## `card_workspace`

### Owns

Canonical Card identity and revision history; canonical-content hashing;
expected-revision commits; type-validator selection; and stable read/search
projections over Provider, Client, Project, and Invoice Cards. It is the primary
owner of A01.

### Knows

M03 and M07–M10, the distinction between canonical and derived facts, and the
validation interfaces supplied by Invoice and Project specialists.

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

A small revision-safe surface hides every storage and canonicalization choice.
Invoice and Project behavior depends on this boundary rather than on tables or
files.

## `invoice_workspace`

### Owns

Invoice draft preparation, type validation, duplicate-candidate discovery,
confirmation lifecycle, payment recording, source-metadata attachment, archive
semantics, M29 assignment-observation production for the exact Invoice
revision, and the producer edge that atomically creates or idempotently retains
the exact `InvoiceWorkingSetItem` and `InvoiceTransferManifest` consumed by
local-node discovery.

### Knows

M05, M07–M11 and their existing Cabinet meanings, plus the revision-safe commit
port exposed by `card_workspace`.

### Must not own

Generic Card persistence, raw source custody, ChatGPT confirmation binding,
authorization, effect idempotency, or local transfer packaging.

### Hides

Invoice field normalization, calculated totals, duplicate signals, lifecycle
transition rules, warnings, and construction of validated Card revisions.

### Candidate public capabilities

```text
search_invoices
get_invoice
find_invoice_duplicates
prepare_invoice_draft
validate_invoice
create_invoice_draft
update_invoice_draft
confirm_invoice
record_invoice_payment
attach_invoice_source_metadata
archive_invoice
```

### Depth assessment

The surface follows meaningful Invoice use cases while hiding their validation
and lifecycle machinery. It does not expose generic field mutation.

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
names, credentials, transport parsing, or Card state.

### Hides

The fixed capability-to-class and capability-to-channel matrix and exact-name
lookup.

### Candidate public capabilities

```text
resolve_capability
list_channel_capabilities
```

### Depth assessment

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

Three interaction operations hide the full safety protocol between a
probabilistic conversational UI and deterministic Cabinet capabilities.

## `access_control`

### Owns

Principal and credential enrollment, protected A03 capability-grant
provisioning, authentication, authorization, rotation, revocation, channel
separation, abuse throttling, and bounded security audit events under A11.

### Knows

M02 and M17 identities, fixed capability classes, credential status, channel,
entity scope, current lifecycle state, and configured throttle limits.

### Must not own

Business identity, Card mutations, effect idempotency, transport sessions,
secret recovery through public channels, or domain-specific decisions.

### Hides

One-way verifiers, timing-safe comparison, exact grant identity and idempotent
provisioning, credential lifecycle transitions, authorization matrix
evaluation, throttle counters, and secret-free audit details.

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

The module exposes identity and authorization decisions while hiding all secret
material and credential mechanics. It remains independent of HTTP and MCP.

## `effect_journal`

### Owns

The A04 principal-scoped idempotency identity, canonical request binding,
atomic expected-revision effect commit, committed-result replay, conflicting
reuse rejection, and unknown-outcome reconciliation state.

### Knows

M03 and M16, operation class, exact target, request hash, principal scope, and
an injected mutation transaction.

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

The three operations hide difficult concurrency and retry behavior shared by
otherwise independent domain effects.

## `source_custody`

### Owns

M05/M06/M14/M15 lifecycle; bounded non-executable original-byte validation and
immutable storage; single-use upload handoffs; authorized retrieval; and the
explicit evidence-backed release of eligible VPS working bytes.

### Knows

Exact Card/source/revision targets, approved media catalogue, A13 limits,
receipt/hash verification needed by A10, and authorized human context.

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

Four custody operations hide file-system safety, concurrent handoff use, byte
identity, and conservative release without becoming a document processor.

## `web_gateway`

### Owns

The A07 private-listener browser boundary: same-origin mutation enforcement,
CSRF context, inert output encoding, security headers, bounded upload/download
HTTP handling, and safe response projection.

### Knows

Authenticated browser context and typed ports for application capabilities and
source custody. It knows no persistence representation.

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

This is intentionally a thin but security-critical adapter. Its public surface
is transport-shaped and all business decisions remain behind typed ports.

## `sync_gateway`

### Owns

The local-node transport boundary: bounded request parsing, compatibility
observation, machine authentication handoff, typed synchronization dispatch,
and bounded response/error serialization.

### Knows

M17 and M26, the sync-only A16 catalogue, A13 request limits, and typed ports
for Invoice exchange and Registry publication.

### Must not own

Human capabilities, arbitrary proxying, package or catalogue truth, credential
verification, Card mutation, or last-write-wins conflict policy.

### Hides

Wire framing, version negotiation input, timeout boundary, request correlation,
safe error projection, and rejection of unknown sync operations.

### Candidate public capabilities

```text
observe_sync_compatibility
serve_sync_request
```

### Depth assessment

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
content hashes, contract compatibility, and immutable source retrieval ports.

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
```

### Depth assessment

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

Two operations hide the entire atomic replica protocol and preserve the
external ownership boundary even while the local system is offline.

## `runtime_control`

### Owns

Loading and validating the finite A13 configuration, readiness gating,
composition of runtime modules, backup execution metadata, and isolated restore
verification exposed only at the protected operator boundary.

### Knows

Required credential/configuration presence, durable-store health, edge/runtime
limit agreement, contract compatibility, backup coverage, and restore cadence.

### Must not own

Domain defaults, per-request safety overrides, public operator endpoints,
ordinary business exports, secrets in backup payloads, or deployment release
approval.

### Hides

Configuration provenance, startup dependency checks, health aggregation,
backup-set enumeration, restore drill orchestration, and readiness reasons.

### Candidate public capabilities

```text
evaluate_readiness
verify_backup_restore
```

### Depth assessment

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
