# State 5 — Cabinet Web Backend public module operations

These operations are the cross-module surface proven by reviewed State 4 flows. Inputs and outputs name domain meaning; exact Python signatures remain State 6 work. Product capability names remain closed under A16.

## `public_op:capability_policy.resolve_capability`

### Owner

`module:capability_policy`.

### Callers

`module:chatgpt_interaction`.

### Inputs

Exact capability name and channel.

### Outputs

Resolved fixed semantic class and owning operation.

### Observable effect

None.

### Enforces

Unknown or channel-confused names never dispatch.

### Errors

UnknownCapability or ChannelCapabilityDenied.

### State impact

Read-only.

## `public_op:chatgpt_interaction.prepare_chatgpt_proposal`

### Owner

`module:chatgpt_interaction`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Principal context, resolved capability, supplied facts, exact target revision when present.

### Outputs

Typed proposal with uncertainties, validation issues, warnings and target identity.

### Observable effect

Creates ephemeral review/confirmation state only.

### Enforces

Model output is proposal data and never validation, confirmation or authority.

### Errors

ProposalRejected, TargetNotFound, UnsafeInput.

### State impact

No business mutation.

## `public_op:chatgpt_interaction.confirm_chatgpt_effect`

### Owner

`module:chatgpt_interaction`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Principal, proposal identity, exact target revision, acknowledged warnings and confirmation.

### Outputs

Confirmed effect authorization or explicit declined/expired/conflicted result.

### Observable effect

Consumes or expires confirmation state; does not perform the domain effect.

### Enforces

Confirmation cannot authorize another revision, target or warning set.

### Errors

ConfirmationExpired, ConfirmationDeclined, RevisionChanged, WarningNotAcknowledged.

### State impact

Mutates confirmation state only.

## `public_op:chatgpt_interaction.report_composite_outcome`

### Owner

`module:chatgpt_interaction`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Typed domain, custody and synchronization results available for the operation.

### Outputs

Bounded structured composite outcome with independent component statuses.

### Observable effect

None.

### Enforces

Partial success is never collapsed into complete success.

### Errors

SafeProjectionError.

### State impact

Read-only.

## `public_op:access_control.authenticate_request`

### Owner

`module:access_control`.

### Callers

`module:chatgpt_interaction`, `module:web_gateway`, `module:sync_gateway`, `module:runtime_control`.

### Inputs

Channel and presented credential evidence. The bounded abuse context is an
internal access-control classification and cannot be supplied by a caller.

### Outputs

One active M39 containing the authenticated M02 principal and, exactly for the
local-node channel, its bound active compatible M17; otherwise bounded refusal.

### Observable effect

May update abuse counters and append secret-free audit evidence.

### Enforces

Credentials cannot substitute across human, plugin, local-node and operator channels.

### Errors

AuthenticationFailed, CredentialRevoked, Throttled, AuthenticationNotReady.

### State impact

Credential evidence only; no domain mutation.

## `public_op:access_control.authorize_capability`

### Owner

`module:access_control`.

### Callers

`module:chatgpt_interaction`, `module:web_gateway`, `module:sync_gateway`, `module:runtime_control`.

### Inputs

Complete M39 principal context, resolved capability, target identity and
current lifecycle state.

### Outputs

Authorization decision bound to principal, capability and target.

### Observable effect

Appends bounded authorization audit evidence.

### Enforces

Knowing an identifier or possessing another channel credential grants nothing.

### Errors

CapabilityDenied, EntityScopeDenied, PrincipalInactive.

### State impact

No domain mutation.

## `public_op:access_control.enroll_principal`

### Owner

`module:access_control`.

### Callers

`boundary:protected_operator`.

### Inputs

Separately authenticated active owner/operator M39, business identity, channel
and credential enrollment material. The M39 may be absent only for the first
owner at the protected empty-installation bootstrap.

### Outputs

Principal identity plus one-time issued credential result.

### Observable effect

Persists principal/verifier and audit evidence.

### Enforces

Plaintext credential is never durably recoverable or exposed to public channels.

### Errors

EnrollmentConflict, InvalidCredentialMaterial, OperatorDenied.

### State impact

Creates credential state, not business Card identity.

## `public_op:access_control.provision_capability_grant`

### Owner

`module:access_control`.

### Callers

`boundary:protected_operator`.

### Inputs

Authenticated active owner/operator context plus M106 exact target principal,
channel, A16 capability, and optional entity scope.

### Outputs

M107 typed provisioning result identifying the exact grant and whether it was newly created.

### Observable effect

Persists one exact grant and secret-free audit evidence, or reports an exact idempotent replay.

### Enforces

No plugin, browser, synchronization, fixture, or composition caller may infer or mutate a private grant store; cross-channel, inactive-target, unknown, and affix-confused grants fail closed.

### Errors

GrantorDenied, TargetPrincipalInactive, CapabilityDenied, ChannelScopeDenied.

### State impact

Mutates authorization grant state only; no credential or domain Card mutation.

## `public_op:access_control.rotate_credential`

### Owner

`module:access_control`.

### Callers

`boundary:protected_operator`.

### Inputs

Separately authenticated active owner/operator M39, principal identity and
replacement credential material.

### Outputs

Rotation result and one-time replacement credential.

### Observable effect

Activates replacement, revokes prior verifier and audits the transition atomically.

### Enforces

The prior credential cannot start new work after commit.

### Errors

CredentialNotFound, CredentialInactive, RotationConflict, OperatorDenied.

### State impact

Mutates credential lifecycle only.

## `public_op:access_control.revoke_credential`

### Owner

`module:access_control`.

### Callers

`boundary:protected_operator`.

### Inputs

Separately authenticated active owner/operator M39, principal and credential
identity.

### Outputs

Revocation result with effective time.

### Observable effect

Persists revocation and audit evidence.

### Enforces

Revocation is immediate for new operations and reveals no old secret.

### Errors

CredentialNotFound, AlreadyRevoked, OperatorDenied.

### State impact

Mutates credential lifecycle only.

## `public_op:card_workspace.search_provider_cards`

### Owner

`module:card_workspace`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized owner, inert search terms, cursor and bounded limit.

### Outputs

Ordered ProviderCard results and continuation metadata.

### Observable effect

None.

### Enforces

Search terms never become query structure and equal labels never merge identities.

### Errors

InvalidSearch, SearchLimitExceeded.

### State impact

Read-only.

## `public_op:card_workspace.list_project_cards`

### Owner

`module:card_workspace`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized owner, closed filters, cursor and bounded limit.

### Outputs

Ordered ProjectCard results and continuation metadata.

### Observable effect

None.

### Enforces

Registry replica status never rewrites Project Card facts.

### Errors

InvalidFilter, SearchLimitExceeded.

### State impact

Read-only.

## `public_op:card_workspace.get_card_revision`

### Owner

`module:card_workspace`.

### Callers

`module:invoice_exchange`.

### Inputs

Card ID and exact M03 revision/content hash.

### Outputs

Exact typed Card revision or absence.

### Observable effect

None.

### Enforces

A newer revision never substitutes for the requested revision.

### Errors

CardNotFound, RevisionNotFound, IntegrityMismatch.

### State impact

Read-only.

## `public_op:card_workspace.commit_card_revision`

### Owner

`module:card_workspace`.

### Callers

`module:invoice_lifecycle`, `module:project_workspace`.

### Inputs

Typed validated Card, expected M03 revision and effect transaction context.

### Outputs

Committed exact Card revision.

### Observable effect

Creates one canonical revision and advances the Card head atomically.

### Enforces

Stale expected revision or validation issues commit nothing.

### Errors

ValidationRejected, RevisionConflict, CanonicalHashConflict, PersistenceUnavailable.

### State impact

Mutates canonical Card history.

## `public_op:invoice_catalogue.search_invoices`

### Owner

`module:invoice_catalogue`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized owner, closed criteria, cursor and bounded limit.

### Outputs

Ordered Invoice summaries with exact Card revisions.

### Observable effect

None.

### Enforces

Human labels and invoice numbers are search evidence, not identity.

### Errors

InvalidSearch, SearchLimitExceeded.

### State impact

Read-only.

## `public_op:invoice_catalogue.get_invoice`

### Owner

`module:invoice_catalogue`.

### Callers

`boundary:chatgpt_plugin`, `module:invoice_lifecycle`, `module:chatgpt_interaction`.

### Inputs

Authorized owner and Invoice Card ID with optional exact revision.

### Outputs

InvoiceCardV1 and revision/validation/source status projection.

### Observable effect

None.

### Enforces

Missing source bytes or sync acceptance remain separate from Card success.

### Errors

InvoiceNotFound, RevisionNotFound.

### State impact

Read-only.

## `public_op:invoice_catalogue.find_invoice_duplicates`

### Owner

`module:invoice_catalogue`.

### Callers

`boundary:chatgpt_plugin`, `module:invoice_validation`, `module:chatgpt_interaction`.

### Inputs

Authorized owner and exact proposal or Invoice revision.

### Outputs

Ordered duplicate candidates with reasons; never a merge decision.

### Observable effect

None.

### Enforces

Candidate similarity cannot merge, archive or confirm a Card.

### Errors

InvoiceNotFound, InvalidDuplicateQuery.

### State impact

Read-only.

## `public_op:invoice_validation.prepare_invoice_draft`

### Owner

`module:invoice_validation`.

### Callers

`boundary:chatgpt_plugin`, `module:chatgpt_interaction`.

### Inputs

Supplied typed facts, uncertainties and optional current Invoice revision.

### Outputs

Draft proposal with missing facts, warnings and calculated fields.

### Observable effect

None.

### Enforces

No OCR/default may invent an unknown required fact.

### Errors

DraftPreparationRejected, UnsupportedInvoiceShape.

### State impact

Read-only proposal.

## `public_op:invoice_validation.validate_invoice`

### Owner

`module:invoice_validation`.

### Callers

`boundary:chatgpt_plugin`, `module:invoice_lifecycle`, `module:chatgpt_interaction`.

### Inputs

Exact InvoiceCardV1 candidate and validation context.

### Outputs

Deterministic M04 validation issues and normalized calculated evidence.

### Observable effect

None.

### Enforces

Validation does not confirm or persist the Invoice.

### Errors

UnsupportedInvoiceVersion.

### State impact

Read-only.

## `public_op:invoice_lifecycle.create_invoice_draft`

### Owner

`module:invoice_lifecycle`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized confirmed save intent, validated draft and idempotent effect context.

### Outputs

New InvoiceCardV1 draft revision.

### Observable effect

Creates Card identity and first draft revision.

### Enforces

Duplicate candidates never auto-merge and missing required facts remain explicit.

### Errors

ValidationRejected, IdempotencyConflict, PersistenceUnavailable.

### State impact

Creates canonical Invoice state.

## `public_op:invoice_lifecycle.update_invoice_draft`

### Owner

`module:invoice_lifecycle`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized save intent, Invoice ID, expected revision and validated changes.

### Outputs

New draft revision under the same Invoice ID.

### Observable effect

Commits one successor revision.

### Enforces

Confirmed content cannot be edited through this operation.

### Errors

InvoiceNotFound, NotDraft, RevisionConflict, ValidationRejected.

### State impact

Mutates canonical Invoice history.

## `public_op:invoice_lifecycle.confirm_invoice`

### Owner

`module:invoice_lifecycle`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized exact-revision confirmation, acknowledged warnings and effect context.

### Outputs

Confirmed successor/current Invoice revision and warnings evidence.

### Observable effect

Commits confirmation lifecycle transition.

### Enforces

Confirmation for revision A cannot authorize revision B.

### Errors

RevisionConflict, ValidationRejected, ConfirmationRequired, WarningNotAcknowledged.

### State impact

Mutates Invoice lifecycle.

## `public_op:invoice_lifecycle.record_invoice_payment`

### Owner

`module:invoice_lifecycle`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized payment facts, Invoice ID, expected revision and effect context.

### Outputs

Successor Invoice revision with payment evidence.

### Observable effect

Commits payment evidence without rewriting prior revision.

### Enforces

Payment state is explicit and cannot be inferred from transport or Registry status.

### Errors

InvoiceNotFound, RevisionConflict, InvalidPaymentEvidence.

### State impact

Mutates canonical Invoice history.

## `public_op:invoice_lifecycle.attach_invoice_source_metadata`

### Owner

`module:invoice_lifecycle`.

### Callers

`boundary:chatgpt_plugin`, `module:source_custody`.

### Inputs

Invoice ID, expected revision, M05/M06 identity metadata and effect context.

### Outputs

Successor Invoice revision with source metadata relation.

### Observable effect

Commits metadata only; byte custody remains separate.

### Enforces

Storage location and filename never become logical source identity.

### Errors

InvoiceNotFound, RevisionConflict, SourceIdentityConflict.

### State impact

Mutates Invoice metadata history.

## `public_op:invoice_lifecycle.archive_invoice`

### Owner

`module:invoice_lifecycle`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized confirmed archive effect, Invoice ID and expected revision.

### Outputs

Archived successor/current Invoice revision.

### Observable effect

Commits archive lifecycle transition.

### Enforces

Archive does not delete Card revisions, sources, receipts or release evidence.

### Errors

InvoiceNotFound, RevisionConflict, ConfirmationRequired.

### State impact

Mutates Invoice lifecycle.

## `public_op:project_workspace.get_project_summary`

### Owner

`module:project_workspace`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized Project ID and optional exact revision.

### Outputs

Project summary with source revision identities and explicit gaps.

### Observable effect

None.

### Enforces

Derived summary cannot become canonical fact authority.

### Errors

ProjectNotFound, RevisionNotFound.

### State impact

Read-only.

## `public_op:project_workspace.validate_estimate`

### Owner

`module:project_workspace`.

### Callers

`boundary:chatgpt_plugin`, `module:chatgpt_interaction`.

### Inputs

Project revision and typed estimate proposal.

### Outputs

Validation issues and normalized AcceptedEstimateSnapshot candidate.

### Observable effect

None.

### Enforces

Validation neither attaches nor persists an estimate.

### Errors

ProjectNotFound, EstimateValidationRejected.

### State impact

Read-only proposal.

## `public_op:project_workspace.derive_shopping_list`

### Owner

`module:project_workspace`.

### Callers

`boundary:chatgpt_plugin`, `module:chatgpt_interaction`.

### Inputs

Exact Project/estimate snapshot and closed derivation options.

### Outputs

ShoppingListSnapshot proposal with provenance.

### Observable effect

None.

### Enforces

Derived items do not rewrite estimate or Project facts.

### Errors

EstimateNotFound, DerivationPreconditionFailed.

### State impact

Read-only proposal.

## `public_op:project_workspace.attach_project_estimate`

### Owner

`module:project_workspace`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized Project ID, expected revision, validated estimate and effect context.

### Outputs

Successor Project revision and accepted estimate identity.

### Observable effect

Persists estimate snapshot and exact Project relation.

### Enforces

Stale Project revisions and invalid estimates commit nothing.

### Errors

ProjectNotFound, RevisionConflict, EstimateValidationRejected.

### State impact

Mutates Project artifact state.

## `public_op:project_workspace.save_shopping_list`

### Owner

`module:project_workspace`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized Project/estimate identities, reviewed list and effect context.

### Outputs

Saved ShoppingListSnapshot with provenance.

### Observable effect

Persists one list snapshot.

### Enforces

A saved list remains derived evidence and never canonical estimate truth.

### Errors

ProjectNotFound, EstimateNotFound, StaleDerivation, ValidationRejected.

### State impact

Creates Project artifact state.

## `public_op:effect_journal.begin_effect`

### Owner

`module:effect_journal`.

### Callers

`module:chatgpt_interaction`, `module:invoice_lifecycle`, `module:project_workspace`, `module:source_custody`.

### Inputs

Principal, idempotency identity, operation class, canonical request hash, target and expected revision.

### Outputs

New effect transaction, prior committed result, or conflicting-reuse refusal.

### Observable effect

Persists prepared M16 state when new.

### Enforces

One identity cannot bind to different content or target.

### Errors

IdempotencyConflict, EffectAlreadyInProgress.

### State impact

Mutates effect journal only.

## `public_op:effect_journal.commit_effect`

### Owner

`module:effect_journal`.

### Callers

`module:chatgpt_interaction`, `module:invoice_lifecycle`, `module:project_workspace`, `module:source_custody`.

### Inputs

Prepared effect identity, expected revision proof and typed operation result.

### Outputs

Committed M16 result.

### Observable effect

Atomically settles the effect with its mutation result.

### Enforces

Partial persistence cannot expose committed success.

### Errors

EffectNotPrepared, RevisionConflict, CommitConflict.

### State impact

Mutates effect journal atomically with owned effect.

## `public_op:effect_journal.reconcile_effect`

### Owner

`module:effect_journal`.

### Callers

`module:chatgpt_interaction`.

### Inputs

Principal and exact idempotency/effect identity.

### Outputs

Committed prior result, still-unknown state, or safe retry eligibility.

### Observable effect

May settle recovered journal state; performs no new domain effect.

### Enforces

Unknown outcome is reconciled before mutation retry.

### Errors

EffectNotFound, ReconciliationUnavailable.

### State impact

Read/recovery of effect journal.

## `public_op:source_custody.issue_upload_handoff`

### Owner

`module:source_custody`.

### Callers

`boundary:chatgpt_plugin`, `module:web_gateway`, `module:chatgpt_interaction`.

### Inputs

Authorized human, exact target, expected revision and configured expiry.

### Outputs

M15 handoff identity plus one-time bearer presentation.

### Observable effect

Persists issued handoff verifier.

### Enforces

The bearer is not business data and cannot target arbitrary files.

### Errors

TargetNotFound, RevisionConflict, HandoffLimitExceeded.

### State impact

Creates handoff state only.

## `public_op:source_custody.store_original_source`

### Owner

`module:source_custody`.

### Callers

`module:web_gateway`.

### Inputs

Presented handoff, bounded bytes and caller media declaration.

### Outputs

M14 custody record and exact M06 content reference.

### Observable effect

Consumes handoff and publishes immutable bytes atomically.

### Enforces

Filename/content cannot choose path or executable structure; no server OCR.

### Errors

HandoffInvalid, HandoffExpired, UnsupportedMedia, PayloadTooLarge, IntegrityConflict, StorageUnavailable.

### State impact

Creates custody and immutable byte state.

## `public_op:source_custody.retrieve_original_source`

### Owner

`module:source_custody`.

### Callers

`module:web_gateway`, `module:invoice_exchange`.

### Inputs

Authorized Card/source identity or exact manifest content reference.

### Outputs

Bounded byte stream/value plus verified hash, size and media type.

### Observable effect

None.

### Enforces

Never returns a filesystem path, storage credential or different revision.

### Errors

SourceNotFound, SourceNotStored, IntegrityMismatch, RetrievalUnavailable.

### State impact

Read-only.

## `public_op:source_custody.release_vps_working_set`

### Owner

`module:source_custody`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Confirmed exact M27 membership and effect identity; exact M23 receipt plus local
durable verification with evidence ID and required/verified source membership.

### Outputs

Per-member retained/released/blocked result plus durable release evidence.

### Observable effect

Deletes only eligible working bytes and persists release evidence.

### Enforces

Sync success, inactivity or Registry status never authorize deletion. Receipt
must be accepted/already-accepted for the exact manifest, include the exact Card
hash and all source hashes, and durable required/verified/manifest source IDs
must be equal.

### Errors

ReleaseBlocked, MembershipChanged, VerificationIncomplete, PartialRelease, StorageUnavailable.

### State impact

Mutates working-byte availability; preserves all logical history.

## `public_op:web_gateway.accept_source_upload`

### Owner

`module:web_gateway`.

### Callers

`boundary:browser_http`.

### Inputs

Authenticated browser context, CSRF proof, handoff bearer and bounded body.

### Outputs

Safe HTTP-facing upload result mapped from typed custody outcome.

### Observable effect

Transport parsing only; downstream custody may store bytes.

### Enforces

Cross-origin, invalid CSRF and active content fail closed.

### Errors

BrowserAuthenticationFailed, CsrfRejected, RequestTooLarge, SafeResponseMappingError.

### State impact

Gateway state only; no independent business mutation.

## `public_op:web_gateway.serve_source_download`

### Owner

`module:web_gateway`.

### Callers

`boundary:browser_http`.

### Inputs

Authenticated browser context and exact Card/source retrieval request.

### Outputs

Attachment response with verified media type, safe filename and security headers.

### Observable effect

None.

### Enforces

No inline active content, path disclosure, credential or permissive CORS.

### Errors

BrowserAuthenticationFailed, AuthorizationDenied, SourceUnavailable.

### State impact

Read-only gateway.

## `public_op:sync_gateway.observe_sync_compatibility`

### Owner

`module:sync_gateway`.

### Callers

`boundary:local_backend`.

### Inputs

Active node request and presented contract version.

### Outputs

M26 compatibility/availability observation with bounded safe code.

### Observable effect

Persists bounded connection observation when configured.

### Enforces

Incompatibility exposes no package or broader capability.

### Errors

NodeAuthenticationFailed, ContractIncompatible, ServiceNotReady.

### State impact

Observation only.

## `public_op:invoice_exchange.discover_invoice_work`

### Owner

`module:invoice_exchange`.

### Callers

`boundary:local_backend`.

### Inputs

Authorized node, compatibility context, cursor and bounded limit.

### Outputs

Bounded M27 page with ordered items containing Invoice ID, exact M03 revision
and content hash, immutable manifest ID/hash, ordered source IDs/hashes/sizes/
media types/safe filenames, and an opaque continuation cursor.

### Observable effect

May retain the exact observed membership used for later issue.

### Enforces

Never exports Provider, Client, Project, estimate or shopping-list data; cursor
and limit are bounded and do not weaken the point-in-time observation.

### Errors

NodeScopeDenied, ContractIncompatible, DiscoveryUnavailable.

### State impact

Read plus optional immutable observation.

## `public_op:invoice_exchange.pull_invoice_package`

### Owner

`module:invoice_exchange`.

### Callers

`boundary:local_backend`.

### Inputs

Node, exact discovered `manifest_id` and caller-scoped idempotency identity.

### Outputs

M21 metadata, exact Card revision, unchanged M29 assignment observation,
bounded streamed source byte parts, and M22 issuance.

### Observable effect

Persists issuance before exposing bytes.

### Enforces

One package contains one exact revision. JSON/metadata is at most 8 MiB, each
source is at most 30 MiB, and the logical package is at most 40 MiB. Bytes are
streamed, not base64 JSON; no VPS path, credential, or `storage_reference`
crosses the wire. Delivery never means local acceptance.

### Errors

WorkNotFound, ManifestChanged, PackageTooLarge, ContractIncompatible, OutcomeUnknown.

### State impact

Creates immutable issuance/protocol state.

## `public_op:invoice_exchange.record_invoice_transfer_receipt`

### Owner

`module:invoice_exchange`.

### Callers

`boundary:local_backend`.

### Inputs

Authenticated node, M22 issuance identity and exact M23 receipt.

### Outputs

Accepted/already-accepted/non-complete receipt outcome.

### Observable effect

Persists matched receipt or classified refusal.

### Enforces

Wrong-node or mismatched manifest/hash cannot acknowledge issuance.

### Errors

IssuanceNotFound, ReceiptMismatch, NodeScopeDenied, ReceiptConflict.

### State impact

Mutates transfer evidence only.

## `public_op:invoice_exchange.reconcile_invoice_transfer`

### Owner

`module:invoice_exchange`.

### Callers

`boundary:local_backend`, `module:source_custody`.

### Inputs

Exact issuance/synchronization identity, node scope and optional expected manifest hash.

### Outputs

Current issuance, receipt, durable-verification references or explicit unknown/conflict.

### Observable effect

May persist newly observed exact receipt; never reissues a package.

### Enforces

Timeout cannot trigger a second mutation and conflicts never use last-write-wins.

### Errors

IssuanceNotFound, ReconciliationUnavailable, ReceiptConflict, RevisionConflict.

### State impact

Read/recovery of protocol evidence.

## `public_op:invoice_exchange.get_invoice_transfer_status`

### Owner

`module:invoice_exchange`.

### Callers

`module:chatgpt_interaction`.

### Inputs

Exact Invoice ID and Card revision reference.

### Outputs

M132 transfer status: source custody status, issuance status when a package was issued, and the local Backend receipt result and safe code when a receipt exists.

### Observable effect

None.

### Enforces

Transport success never becomes local durable acceptance; without a receipt the status stays issued, acknowledged, or not issued.

### Errors

ResourceNotFoundError for an unknown revision.

### State impact

Read-only.

## `public_op:registry_replica.publish_registry_catalogue`

### Owner

`module:registry_replica`.

### Callers

`boundary:local_backend`.

### Inputs

Authenticated node and exact M24 delivery using the negotiated
`cabinet-web-sync-v1` boundary: catalogue ID, canonical `project_id` ordering,
endpoints, idempotency, creation time, and ordered snapshots. Count and content
identity are derived from the complete snapshots, not additional wire fields.

### Outputs

M25 acknowledgement and new/current replica identity.

### Observable effect

Atomically persists complete replica and current selection.

### Enforces

Partial, older or conflicting delivery never becomes current. Completeness and
content identity are verified from the canonical ordered snapshot sequence.

### Errors

CatalogueMalformed, CatalogueHashMismatch, ContractIncompatible, StalePublication, PublicationConflict.

### State impact

Mutates Registry replica protocol state.

## `public_op:registry_replica.get_current_registry_catalogue`

### Owner

`module:registry_replica`.

### Callers

`boundary:chatgpt_plugin`.

### Inputs

Authorized human read or publication verification context.

### Outputs

M20 replica/current catalogue and freshness/last-publication evidence.

### Observable effect

None.

### Enforces

Stale remains truthful; Registry snapshot never becomes Project Card authority.

### Errors

CatalogueUnavailable.

### State impact

Read-only.

## `public_op:runtime_control.evaluate_readiness`

### Owner

`module:runtime_control`.

### Callers

`boundary:protected_operator`.

### Inputs

Validated deployment configuration and current dependency health evidence.

### Outputs

Bounded ready/not-ready result with protected reason codes.

### Observable effect

May persist health/restore observation evidence.

### Enforces

Missing credentials, durable state, edge agreement or compatibility means not ready.

### Errors

ConfigurationInvalid, DependencyUnavailable.

### State impact

Operational observation only.

## `public_op:runtime_control.verify_backup_restore`

### Owner

`module:runtime_control`.

### Callers

`boundary:protected_operator`.

### Inputs

Operator authorization, backup identity and isolated restore target.

### Outputs

Restore verification covering Cards, sources and all required protocol evidence.

### Observable effect

Creates protected verification evidence and cleans isolated runtime.

### Enforces

A backup is not recoverable until exact relationships and hashes pass.

### Errors

BackupNotFound, RestoreFailed, IntegrityMismatch, CoverageIncomplete, IsolationCleanupFailed.

### State impact

No production business mutation.

## `public_op:runtime_settings.load_runtime_settings`

### Owner

`module:runtime_settings`.

### Callers

`boundary:process_startup`; `module:bootstrap` is the composition owner that
invokes the imported provider exactly once.

### Inputs

The closed structured runtime-settings declaration and current process
environment.

### Outputs

One immutable M135 `RuntimeSettings` snapshot.

### Observable effect

Reads declared process environment values only.

### Enforces

Requiredness, normalization, positive-integer parsing, declared defaults,
closed environment identity, exact targets, and project-declared constraints.

### Errors

MissingSetting, InvalidSetting, RuntimeSettingConstraintViolation.

### State impact

No durable state; fail-closed startup input only.
