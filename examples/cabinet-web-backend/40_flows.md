# State 4 — Cabinet Web Backend key system flows

## Status

All planned first-release flows below are reviewed against State 3 ownership.
They expose cross-module needs but do not yet freeze State 5 public APIs or
State 6 Python signatures.

## `flow:query_cabinet_through_chatgpt`

### Trigger

The authenticated owner asks ChatGPT to search providers or invoices, list or
summarize projects, inspect one Invoice, review duplicate candidates, or read
the last complete Registry catalogue.

### Boundary

The plugin reaches each read through its own typed route of the closed A16
catalogue; `module:capability_policy` resolves the exact closed capability,
and `module:access_control` authenticates the tunnel identity and
authorizes the exact read capability. `module:chatgpt_interaction` owns only
proposal, confirmation, and composite-outcome reporting. Reads are owned by
`module:card_workspace`, `module:invoice_catalogue`,
`module:project_workspace`, and `module:registry_replica` according to their
data authority.

### Steps

1. `capability:access_control.authenticate_request` establishes the tunnel-bound
   owner; `capability:capability_policy.resolve_capability` resolves the exact
   closed catalogue entry, and
   `capability:access_control.authorize_capability` checks the exact read scope.
2. Provider and Project catalogue reads use
   `capability:card_workspace.search_provider_cards` and
   `capability:card_workspace.list_project_cards`; a derived Project view uses
   `capability:project_workspace.get_project_summary`.
3. Invoice reads use `capability:invoice_catalogue.search_invoices`,
   `capability:invoice_catalogue.get_invoice`, or
   `capability:invoice_catalogue.find_invoice_duplicates` without accepting a
   duplicate candidate as a merge decision.
4. Offline Registry context uses
   `capability:registry_replica.get_current_registry_catalogue` and preserves
   freshness/staleness explicitly.
5. The route returns the typed result and bounded safe errors directly; no
   effect is created.

### Outcomes

State 0 outcome proven here: "Existing ChatGPT and Card behavior preserved".

The owner receives a typed bounded result, an explicit not-found/ambiguous or
stale-catalogue result, or an authorization/availability refusal. All durable
Card, source, effect, Registry and synchronization state remains unchanged.

### Errors

`module:access_control` owns authentication and authorization refusal. Each
domain module owns its not-found, query-limit, ambiguity, and projection errors.
`module:chatgpt_interaction` translates only bounded safe outcomes and cannot
turn a read into a write or fabricate missing facts.

## `flow:complete_invoice_work_through_chatgpt`

### Trigger

The authenticated owner asks ChatGPT to inspect, prepare, save, update, confirm,
pay, attach metadata to, or archive one Invoice.

### Boundary

Each plugin capability enters through its own typed route; `module:access_control`
authenticates the tunnel identity and authorizes the exact capability.
`module:chatgpt_interaction` owns proposal preparation, explicit confirmation,
and composite-outcome reporting, and asks `module:capability_policy` through
`capability:capability_policy.resolve_capability` for the exact catalogue entry
a proposal names. Invoice reads belong to `module:invoice_catalogue`; Invoice meaning remains in
`module:invoice_validation` and `module:invoice_lifecycle`; canonical commits remain in `module:card_workspace`;
effect identity remains in `module:effect_journal`; transfer-side outcome truth
remains in `module:invoice_exchange`.

### Steps

1. The tunnel identity is authenticated through
   `capability:access_control.authenticate_request`, the exact operation is
   checked through `capability:access_control.authorize_capability`, and the
   typed route admits only a catalogue capability; a proposal naming an unknown capability is rejected by
   `capability:capability_policy.resolve_capability` before any effect exists.
2. `capability:chatgpt_interaction.prepare_chatgpt_proposal` converts model
   output into a review object, retaining missing and uncertain facts.
3. `capability:invoice_validation.prepare_invoice_draft`,
   `capability:invoice_validation.validate_invoice`, and
   `capability:invoice_catalogue.find_invoice_duplicates` produce typed facts,
   warnings, and duplicate candidates without mutation.
4. Reads return immediately. A draft write requires a clear save request; a
   consequential effect proceeds only through
   `capability:chatgpt_interaction.confirm_chatgpt_effect` bound to the exact
   target revision and warnings.
5. `capability:effect_journal.begin_effect` establishes the principal-scoped
   request identity. The exact selected operation is one of
   `capability:invoice_lifecycle.create_invoice_draft`,
   `capability:invoice_lifecycle.update_invoice_draft`,
   `capability:invoice_lifecycle.confirm_invoice`,
   `capability:invoice_lifecycle.record_invoice_payment`,
   `capability:invoice_lifecycle.attach_invoice_source_metadata`, or
   `capability:invoice_lifecycle.archive_invoice`. It constructs a validated revision and
   `capability:card_workspace.commit_card_revision` performs the atomic expected-
   revision commit.
6. `capability:effect_journal.commit_effect` records the logical result. After
   an ambiguous timeout, `capability:effect_journal.reconcile_effect` is called
   before any retry.
7. `capability:chatgpt_interaction.report_composite_outcome` reports Card,
   source-custody, and synchronization results separately, reading the
   transfer side through `capability:invoice_exchange.get_invoice_transfer_status`.

### Outcomes

State 0 outcomes proven here: "Existing ChatGPT and Card behavior preserved", "Card rejected", "Reconciliation required", and "Duplicate submission or uncertain response".

The result is either a non-mutating review proposal, one committed Invoice
revision, an idempotent prior result, an explicit validation/duplicate/revision
conflict, or an unknown outcome awaiting reconciliation. Model confidence alone
never becomes a stored or confirmed fact.

### Errors

`module:access_control` owns authentication/authorization refusal;
`module:invoice_validation` owns Invoice validation errors and `module:invoice_lifecycle` owns lifecycle errors;
`module:card_workspace` owns stale revision/storage commit errors;
`module:effect_journal` owns idempotency conflicts and ambiguous effect state;
`module:chatgpt_interaction` translates only safe, bounded results for ChatGPT.

## `flow:create_project_artifacts_through_chatgpt`

### Trigger

The owner asks ChatGPT to validate or attach an estimate, derive a shopping
list, or save a reviewed list for one exact Project revision.

### Boundary

The interaction and authorization path uses `module:chatgpt_interaction` and
`module:access_control`. Project rules belong to `module:project_workspace`,
effect replay to `module:effect_journal`, and canonical Project revision commit
to `module:card_workspace`.

### Steps

1. `capability:access_control.authorize_capability` checks the exact owner,
   capability, Project, and lifecycle state.
2. `capability:chatgpt_interaction.prepare_chatgpt_proposal` preserves supplied
   facts and uncertainties without treating the conversation as authority.
3. `capability:project_workspace.validate_estimate` validates an estimate;
   `capability:project_workspace.derive_shopping_list` may derive a projection.
   Neither operation persists an artifact.
4. A save is bound by `capability:chatgpt_interaction.confirm_chatgpt_effect`
   when confirmation is required, then registered by
   `capability:effect_journal.begin_effect`.
5. The selected effect calls
   `capability:project_workspace.attach_project_estimate` or
   `capability:project_workspace.save_shopping_list`; any Project revision
   change crosses `capability:card_workspace.commit_card_revision` atomically.
6. `capability:effect_journal.commit_effect` records one logical outcome.

### Outcomes

The observable outcome is a validation/derivation proposal, one saved artifact
bound to an exact Project revision, an idempotent prior result, or an explicit
validation/stale-revision refusal. Registry snapshots are never rewritten.

### Errors

`module:project_workspace` owns estimate/list semantics and Project relationship
errors. `module:card_workspace` owns revision conflicts. `module:effect_journal`
owns replay conflicts. The ChatGPT boundary never fills missing plan facts.

## `flow:upload_original_source_from_web`

### Trigger

The owner chooses an existing Card/source/revision and requests an upload link,
then submits one original through the protected Web helper before expiry.

### Boundary

`module:chatgpt_interaction` initiates and later reports the cross-channel
handoff. Authentication and exact authorization belong to
`module:access_control` and are obtained through
`capability:access_control.authenticate_request` and
`capability:access_control.authorize_capability`. Handoff and byte custody belong
to `module:source_custody`; HTTP/CSRF/output safety belongs to
`module:web_gateway`; Invoice metadata remains in `module:invoice_lifecycle`.

### Steps

1. `capability:source_custody.issue_upload_handoff` creates one short-lived,
   single-use handoff for the exact target after authorization. The bearer is
   shown only to the protected upload context.
2. `capability:web_gateway.accept_source_upload` enforces private-listener,
   same-origin, CSRF, and bounded HTTP rules and passes data, never a caller path.
3. `capability:source_custody.store_original_source` verifies handoff state,
   size, identified media type and hash, then atomically publishes immutable
   bytes while consuming the handoff.
4. If metadata must be linked to an Invoice revision,
   `capability:effect_journal.begin_effect` surrounds
   `capability:invoice_lifecycle.attach_invoice_source_metadata`, followed by
   `capability:effect_journal.commit_effect`.
5. `capability:chatgpt_interaction.report_composite_outcome` can report Card and
   custody results independently.

### Outcomes

State 0 outcomes proven here: "Card accepted, source attachment incomplete" and "Invalid or mismatched source".

Success proves only Cabinet Web custody of exact bytes and their logical source
link. Replayed equal bytes are idempotent. Invalid, expired, consumed,
unsupported, oversized, malformed, mismatched, or unauthorized submissions
produce no false stored state and never imply local Backend acceptance.

### Errors

`module:web_gateway` translates HTTP/CSRF/output errors;
`module:source_custody` owns handoff, media, hash, storage, and retrieval policy;
`module:invoice_lifecycle` owns metadata-link validation; and
`module:effect_journal` owns ambiguous metadata effects. No error reveals a
storage path, credential, bearer, or active uploaded content.

## `flow:download_original_source_from_web`

### Trigger

The authenticated owner requests one original belonging to an exact authorized
Card/source pair through the protected same-origin Web helper.

### Boundary

`module:web_gateway` owns the HTTP response boundary, `module:access_control`
owns exact principal/capability/entity authorization, and
`module:source_custody` owns byte lookup and custody truth.

### Steps

1. `capability:access_control.authenticate_request` establishes the protected
   browser owner and `capability:access_control.authorize_capability` checks the
   exact Card/source retrieval scope; knowing an identifier is insufficient.
2. `capability:source_custody.retrieve_original_source` resolves the immutable
   accepted M06 bytes and verified media metadata without returning a filesystem
   path or storage credential.
3. `capability:web_gateway.serve_source_download` emits a bounded non-executable
   attachment response with safe filename projection, verified media type,
   anti-sniffing and no active inline rendering.

### Outcomes

The result is the exact authorized immutable original, not-found/not-stored,
authorization refusal, or a bounded custody/read failure. Retrieval changes no
Card, custody, effect, synchronization, or release state.

### Errors

`module:access_control` owns authentication and authorization errors;
`module:source_custody` owns absent/released/corrupt byte evidence;
`module:web_gateway` owns safe HTTP translation. No error exposes internal
storage layout, bearer values, secrets, or unbounded external text.

## `flow:confirmed_invoice_enters_vps_working_set`

### Trigger

The owner confirms one Invoice Card through the normal ChatGPT or Web UI flow.

### Boundary

`module:invoice_lifecycle` owns the confirmation transition and the producer
edge that derives the working-set item and manifest from the committed
revision. Canonical Card commits belong to `module:card_workspace`; verified
source custody evidence belongs to `module:source_custody`; effect identity and
idempotent replay belong to `module:effect_journal`; local discovery and package
issuance belong to `module:invoice_exchange`, which reads the producer output
and never derives it.

### Steps

1. `capability:invoice_lifecycle.confirm_invoice` commits the exact successor
   revision through `capability:card_workspace.commit_card_revision` and verified
   source membership under its existing effect boundary.
2. In the same durable transition it creates or idempotently retains one
   immutable `InvoiceWorkingSetItem` and `InvoiceTransferManifest` for that
   revision. The manifest has exactly one `card_revisions` entry and immutable
   source references.
3. Any available `CardObjectAssignmentObservation` is pinned to the revision
   and later carried unchanged by `module:invoice_exchange`; no project is
   inferred from an Invoice ID or label.
4. `capability:invoice_exchange.discover_invoice_work` reads this durable
   producer output in stable order;
   an empty working set is truthful only when no confirmed eligible Invoice
   exists.

### Invariants

`confirm_invoice` success -> durable discovery item and immutable manifest;
changed revision/source set -> new manifest; repeated confirmation -> one
logical producer item; failed confirmation -> no discoverable transfer item.

### Outcomes

State 0 outcome proven here: "Backend temporarily unavailable" — the confirmed revision and its bytes wait for the next local session without claiming acceptance.

Success leaves exactly one committed confirmed revision, one immutable
`InvoiceTransferManifest`, and one `InvoiceWorkingSetItem` for that revision,
discoverable in stable order. Repeated confirmation of the same revision is
idempotent and creates no second manifest or item. Failure at any step leaves
no confirmed revision, manifest, or working-set item and no discoverable
transfer work.

### Errors

`module:invoice_lifecycle` owns confirmation-binding, stale-revision,
validation, and custody rejections; `module:card_workspace` owns revision
conflicts; `module:source_custody` owns missing or unverified custody;
`module:effect_journal` owns idempotency conflicts and unknown outcomes. No
error fabricates custody, manifest, or working-set evidence.

## `flow:pull_invoice_package_to_local_backend`

### Trigger

During the evening connection, the one enrolled local Backend node initiates
compatibility observation, discovers Invoice work, and requests an exact package.

### Boundary

`module:sync_gateway` owns wire parsing and safe responses. Authentication uses
`module:access_control`. Protocol state and truth belong to
`module:invoice_exchange`; exact Card and byte reads use `module:card_workspace`
and `module:source_custody`.

### Steps

1. `capability:sync_gateway.observe_sync_compatibility` rejects incompatible
   contract revisions before package issue.
2. `capability:access_control.authenticate_request` and
   `capability:access_control.authorize_capability` establish one M39 containing
   the exact active M02 machine principal and its bound active compatible M17
   node plus sync-only scope; each closed sync operation enters through its
   own typed route, which passes only `context.node` to Invoice domain
   operations.
3. `capability:invoice_exchange.discover_invoice_work` returns a bounded M27
   page containing only exact available Invoice IDs, Card revision/content
   hashes, immutable manifest IDs/hashes, ordered source metadata, and an opaque
   continuation cursor.
4. The exchange reads exact Card content through
   `capability:card_workspace.get_card_revision` and opens each required source
   through `capability:source_custody.retrieve_original_source`, resolves the exact
   discovered immutable manifest, durably records issuance, then
   `capability:invoice_exchange.pull_invoice_package` streams the exact Card,
   M29 assignment observation, and bounded source byte parts. It never emits
   base64 JSON, a VPS path, credential, or either peer's `storage_reference`.
5. A later exact receipt is checked through
   `capability:invoice_exchange.record_invoice_transfer_receipt`. A timeout or
   uncertain response uses `capability:invoice_exchange.reconcile_invoice_transfer`
   without issuing a second logical package.

### Outcomes

State 0 outcomes proven here: "Complete success", "Reconciliation required", and "Duplicate submission or uncertain response".

Outcomes distinguish available work, exact package issuance, accepted or
already-accepted local custody, quarantine/rejection, incompatibility, conflict,
and unknown awaiting reconciliation. HTTP success is never local durable proof.

### Errors

`module:sync_gateway` owns malformed/version/serialization errors;
`module:access_control` owns node authentication and scope refusal;
`module:invoice_exchange` owns manifests, issuance, receipts, conflicts, and
reconciliation. Card/byte modules report unavailable exact evidence without
substituting newer revisions or unrelated data.

## `flow:publish_registry_catalogue_from_local_backend`

### Trigger

The authenticated local Backend submits one complete Registry catalogue
delivery after its evening Registry observation.

### Boundary

`module:sync_gateway` accepts the bounded wire request;
`module:access_control` proves the active local node; `module:registry_replica`
owns catalogue validation and current-replica selection.

### Steps

1. The typed publication route admits only the exact publication operation
   and bounded payload.
2. `capability:access_control.authenticate_request` and
   `capability:access_control.authorize_capability` enforce the M39 principal,
   bound node, reciprocal contract, and installation scope; Registry receives
   only the verified `context.node`.
3. `capability:registry_replica.publish_registry_catalogue` verifies delivery,
   identity, count, order, version, hash, replay identity, and observation time.
4. The complete replica and current selector commit atomically. Exact replay
   returns the earlier acknowledgement; an older or conflicting publication
   cannot replace current.
5. Human reads use
   `capability:registry_replica.get_current_registry_catalogue`, including
   freshness and last-publication facts.

### Outcomes

Readers see either the prior complete catalogue or the new complete catalogue,
never a partial mixture. Offline or stale remains visible. No outcome rewrites a
Project Card or infers completion/deletion from Registry status.

### Errors

The gateway owns bounded transport errors, access control owns authentication,
and `module:registry_replica` owns malformed, incompatible, hash, replay,
monotonicity, and atomic-commit outcomes. Technical failure leaves the prior
complete current replica intact.

## `flow:release_verified_vps_working_set`

### Trigger

The owner explicitly asks ChatGPT to release one exact VPS working set or listed
source members after local synchronization.

### Boundary

`module:chatgpt_interaction` owns exact review/confirmation;
`module:access_control` owns authorization; `module:invoice_exchange` provides
receipt reconciliation; `module:source_custody` owns eligibility and physical
byte release; `module:effect_journal` owns one logical release effect.

### Steps

1. `capability:access_control.authorize_capability` checks the exact owner and
   target. `capability:chatgpt_interaction.prepare_chatgpt_proposal` presents
   members, retained facts, and missing verification.
2. `capability:invoice_exchange.reconcile_invoice_transfer` establishes exact
   accepted/already-accepted receipt evidence and required durable verification.
3. Release is blocked unless the receipt is accepted/already-accepted for the
   exact manifest, includes the Card hash and every source hash, and local
   durable verification is accepted with a non-empty evidence ID and exact
   equality of required, verified, and manifest source IDs. Registry status and
   inactivity are ignored.
4. `capability:chatgpt_interaction.confirm_chatgpt_effect` binds confirmation to
   the reviewed members and evidence. `capability:effect_journal.begin_effect`
   records its idempotency identity.
5. `capability:source_custody.release_vps_working_set` removes only eligible
   working bytes and retains Card/source/hash/receipt/release evidence.
6. `capability:effect_journal.commit_effect` records the result and
   `capability:chatgpt_interaction.report_composite_outcome` distinguishes full,
   partial, blocked, and safely retryable outcomes.

### Outcomes

Release is blocked, completes for the exact eligible set, replays an earlier
result, or remains partial/unknown and retryable. Synchronization itself never
deletes bytes, and all logical/history evidence survives successful release.

### Errors

`module:invoice_exchange` owns receipt truth; `module:source_custody` owns
eligibility and storage execution; `module:effect_journal` owns idempotency and
unknown effect state; ChatGPT translates the exact safe outcome without
claiming complete release after partial failure.

## `flow:rotate_or_revoke_credential`

### Trigger

A protected host operator enrolls a principal, provisions one exact capability
grant, or rotates or revokes one exact human, plugin, local-node, or operator
credential; this flow is never exposed as a normal plugin/browser/sync
capability.

### Boundary

`module:runtime_control` confirms the protected operator/runtime boundary and
`capability:runtime_control.evaluate_readiness`. `module:access_control` owns
authentication, authorization, and credential lifecycle.

### Steps

1. `capability:access_control.authenticate_request` authenticates the operator
   context without accepting another channel's credential.
2. `capability:access_control.authorize_capability` binds the exact lifecycle
   action and target identity.
3. Initial owner enrollment uses `capability:access_control.enroll_principal`
   with no actor only at the protected empty-installation boundary. Every later
   enrollment, rotation, and revocation supplies the separately authenticated
   active owner/operator M39; an M01 inside a command is never authority. The
   issued credential is authenticated before
   `capability:access_control.provision_capability_grant` may idempotently bind
   one exact target, channel, A16 capability, and optional entity scope; no
   private grant store is part of composition. Rotation uses
   `capability:access_control.rotate_credential` to activate the
   replacement and revoke the prior verifier atomically. Revocation uses
   `capability:access_control.revoke_credential` and creates no replacement.
4. Plaintext replacement material is returned/injected once at the protected
   boundary and never enters business data, prompts, URLs, or logs.
5. Readiness is reevaluated when the changed credential is required for startup
   or a protected channel.

### Outcomes

The business principal/node identity remains unchanged; exact grant replay is
reported without broadening authority, and the prior credential cannot begin
new work immediately. Failure leaves a bounded auditable result without
revealing whether guessed secret material was close or valid.

### Errors

`module:runtime_control` owns unavailable protected configuration/readiness.
`module:access_control` owns grantor/target/channel/scope validation, exact
grant identity, verifier, lifecycle, throttle, atomic rotation, and audit
errors. There is no public recovery, private-store fixture contract, or
plaintext retrieval.

## `flow:verify_backup_restore_and_readiness`

### Trigger

The scheduled protected operator process performs a restore drill, or startup
must decide whether required durable state and prior verification are healthy.

### Boundary

Operator access is checked by `module:access_control`; backup selection,
isolated restoration, evidence comparison, and readiness belong to
`module:runtime_control`.

### Steps

1. `capability:access_control.authenticate_request` and
   `capability:access_control.authorize_capability` enforce the protected
   `backup.verify_restore` operation.
2. `capability:runtime_control.verify_backup_restore` selects a declared backup,
   restores it into isolation, and checks exact Card revisions, source hashes
   and relationships, custody/effect/transfer/Registry/release evidence.
3. Ordinary business backup material is checked not to contain reusable
   secrets; protected host secret recovery remains separate.
4. Verification evidence records the exact backup identity, result, time, and
   bounded failures. It does not alter production business state.
5. `capability:runtime_control.evaluate_readiness` combines required config,
   credential presence, durable-store health, contract compatibility, edge/app
   limit agreement, and recovery evidence into a fail-closed readiness result.

### Outcomes

A backup becomes recoverable only after successful isolated verification.
Readiness is explicit and bounded; missing dependencies or incompatible state
produce not-ready rather than a degraded anonymous/public fallback.

### Errors

`module:access_control` owns operator denial. `module:runtime_control` owns
backup integrity, relationship mismatch, missing coverage, isolated cleanup,
configuration, and readiness errors. Drill failure preserves production state
and produces actionable protected evidence without secrets.

## `flow:compose_runtime_from_typed_settings`

### Trigger

The Cabinet Web process starts and must construct its single application graph
before accepting traffic or running recovery.

### Boundary

`module:runtime_settings` alone reads and validates declared deployment inputs.
`module:bootstrap` owns composition and injects the resulting immutable M135
snapshot into runtime consumers.

### Steps

1. `module:bootstrap` calls
   `capability:runtime_settings.load_runtime_settings` exactly once.
2. The provider resolves the required environment selector, parses only the
   declared inputs, applies declared defaults and project constraints, and
   constructs M135 without consulting product policy implicitly.
3. Any missing required input, invalid value, or violated declared relation
   aborts startup before a database connection, recovery action, service, or
   HTTP application is constructed.
4. `module:bootstrap` passes the same M135 value to behavioral consumers and
   passes its typed database URL to the PostgreSQL UoW factory.
5. Consumers read only their required M135 fields. They do not read env,
   dereference config data, copy defaults, or create another provider.

### Outcomes

Exactly one validated configuration snapshot supplies the complete runtime
graph, or startup fails closed without a partially constructed application.

### Errors

`module:runtime_settings` owns missing, malformed, out-of-domain, and
cross-setting validation failure. `module:bootstrap` owns construction and
dependency-startup failure after settings have been accepted.
