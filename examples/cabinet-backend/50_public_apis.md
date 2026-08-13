# State 5 — Cabinet Backend public module APIs

## Status

State 5 is in progress. These entries define public cross-boundary operations proven by State 4. They intentionally stop before exact Python signatures, concrete DTO field lists, transport bindings, or private helper functions; those belong to State 6. `public_op:*` denotes an owning module's public operation; deterministic HTTP exposure is designed later from accepted operations and contracts.

---

## `public_op:access_control.authorize_operation`

### Owner
`module:access_control`

### Callers
Local protected-operation adapters.

### Inputs
Authenticated principal context and one exact protected Cabinet operation identifier.

### Outputs
Authorization decision plus security/audit evidence for an exact operation that the authenticated principal is permitted to perform.

### Observable effect
May record authorization/security evidence; does not perform the protected business operation itself.

### Enforces
Exact-operation authorization, principal/capability separation, revocation, and local-service versus synchronization-identity boundaries.

### Errors
`AuthenticationRequiredError` when no valid authenticated principal exists. `OperationForbiddenError` when the authenticated principal is revoked, lacks the required exact-operation capability, supplies an operation outside the accepted protected vocabulary, or is refused by the accepted access-control policy.

### State impact
May append security evidence; must not mutate invoice, Registry, PresuPro, Holded, or retention state.

---

## `public_op:synchronization.synchronize_invoice_work`

### Owner
`module:synchronization`

### Callers
Synchronization scheduler/adapter.

### Inputs
One exact synchronization work selection and synchronization-node context.

### Outputs
Transfer/delivery/reconciliation outcome that preserves the distinction between delivered and durably accepted. Authentication failure, transport failure, incompatible package/contract, remote unavailability, and ambiguous delivery are explicit synchronization outcome states rather than implicit success.

### Observable effect
May perform authenticated transfer attempts and record transport observations/receipts.

### Enforces
Outbound synchronization identity, retry/reconciliation semantics, transfer identity, and delivery-versus-acceptance separation.

### Errors
Failure to construct or durably record a synchronization outcome at all. Transport and reconciliation conditions that can be classified are returned in `SynchronizationOutcome` and are not silently promoted to durable acceptance.

### State impact
Mutates synchronization attempt/receipt state only; durable acceptance remains owned by `module:durable_archive`.

---

## `public_op:synchronization.get_sync_status`

### Owner
`module:synchronization`

### Callers
`module:retention_release`.

### Inputs
Exact transfer, replica, invoice work, or working-set identity required by the release evaluation.

### Outputs
Current synchronization/replica observation without any claim of durable archive acceptance. Unknown, unavailable, stale, or insufficient observations remain explicit observation states where the synchronization status model can represent them.

### Observable effect
Read-only with respect to business state.

### Enforces
Transport facts remain transport facts.

### Errors
Failure to obtain or construct a trustworthy synchronization observation at all; the caller must never receive a fabricated default synchronized state.

### State impact
None beyond optional observation/audit recording.

---

## `public_op:durable_archive.accept_transfer_manifest`

### Owner
`module:durable_archive`

### Callers
`module:synchronization`.

### Inputs
One exact transfer manifest, immutable Invoice Card revision evidence, and required source evidence presented for local acceptance.

### Outputs
Accepted, already-accepted, rejected, quarantined, or explicit incomplete/failure outcome with durable acceptance evidence when applicable. Unsupported Card/version, integrity failure, conflicting evidence, duplicate-review requirements, and quarantine requirements are classified acceptance outcomes rather than alternate exception semantics.

### Observable effect
May create durable archive records, source custody, quarantine state, and acceptance evidence atomically under the accepted rules.

### Enforces
Card immutability, manifest idempotency, source integrity, duplicate policy, quarantine policy, and atomic visibility.

### Errors
Persistence or system failure that prevents the archive from atomically recording a trustworthy classified acceptance outcome. Validation, duplicate, integrity, and quarantine conditions that can be classified belong in the returned `InvoiceTransferReceipt`.

### State impact
Mutates durable archive state only according to accepted acceptance/quarantine transitions.

---

## `public_op:durable_archive.verify_durable_acceptance`

### Owner
`module:durable_archive`

### Callers
`module:synchronization`, `module:retention_release`.

### Inputs
Exact archive target or working-set evidence identity.

### Outputs
Authoritative durable-acceptance proof or explicit not-accepted/not-verifiable result. Unknown target, missing/unverified required replica, or inconsistent archive evidence must remain explicit verification outcomes when they can be classified from archive truth.

### Observable effect
Read-only verification of archive truth.

### Enforces
Network delivery or external status can never substitute for local durable proof.

### Errors
Failure to read or evaluate authoritative archive evidence at all. Missing or inconsistent evidence that can be classified must not be converted into a fabricated positive proof.

### State impact
None beyond optional verification evidence.

---

## `public_op:durable_archive.attach_local_source`

### Owner
`module:durable_archive`

### Callers
Authorized local source-attachment adapters.

### Inputs
Stable `invoice_id`, one or more local source files, actor/provenance context, and any exact expected-source target evidence.

### Outputs
Per-file attachment result plus resulting source availability/completeness evidence.

### Observable effect
May add verified source custody/provenance and update Backend-owned source availability state without rewriting the Invoice Card.

### Enforces
Stable mutation identity, media/hash verification, expected-source matching, provenance, idempotent repeated bytes, and no silent replacement.

### Errors
`InvoiceNotFoundError` when the stable accepted invoice target cannot be resolved. `SourceAttachmentRejectedError` when submitted evidence is unsupported, unreadable, wrong-target, hash-mismatched, ambiguous, or otherwise rejected by accepted archive policy. Unexpected persistence/system failure is not a normal attachment result.

### State impact
Mutates source evidence only; accepted Card bytes/content hash remain immutable.

---

## `public_op:durable_archive.accept_incomplete_source_evidence`

### Owner
`module:durable_archive`

### Callers
Authorized local protected-operation adapters.

### Inputs
One immutable IncompleteSourceAcceptance decision and exact-operation authorization.

### Outputs
Updated truthful SourceStatus for the exact invoice.

### Observable effect
Records auditable acceptance of an exact confirmed Card revision with an explicitly identified incomplete source set.

### Enforces
Explicit user intent, exact revision/source binding, authorization, idempotent decision replay, and preservation of missing-source truth.

### Errors
`InvoiceNotFoundError` for an unknown exact revision and `SourceAttachmentRejectedError` for stale, mismatched, empty, or conflicting acceptance evidence.

### State impact
May admit the Card to normal archive truth with `awaiting_source`; never claims missing bytes are stored and never rewrites Card content.

---

## `public_op:durable_archive.record_source_loss`

### Owner
`module:durable_archive`

### Callers
Authorized local protected-operation adapters.

### Inputs
One immutable SourceLossDecision and exact-operation authorization.

### Outputs
Updated truthful SourceStatus for the exact invoice.

### Observable effect
Appends source-loss evidence and changes affected missing-source status to `source_lost`.

### Enforces
Exact affected source identity, authorization, immutable history, idempotent replay, and reversible recovery by later verified attachment.

### Errors
`InvoiceNotFoundError` for an unknown invoice and `SourceAttachmentRejectedError` for empty, already available, wrong-target, stale, or conflicting loss evidence.

### State impact
Changes source completeness evidence only; it neither deletes source/Card history nor blocks later return to `complete`.

---

## `public_op:durable_archive.get_source_status`

### Owner
`module:durable_archive`

### Callers
Local source-attachment adapters.

### Inputs
Exact accepted invoice/source package identity.

### Outputs
Current source availability, completeness, attachment outcomes, and missing/failed evidence state for an existing accepted archive target.

### Observable effect
Read-only.

### Enforces
Truthful distinction among available, missing, and failed-verification evidence.

### Errors
`InvoiceNotFoundError` when the requested accepted invoice/source target cannot be resolved. Missing or failed source evidence for an existing invoice remains part of the returned source status rather than becoming a fabricated empty result.

### State impact
None.

---

## `public_op:durable_archive.get_archived_invoice`

### Owner
`module:durable_archive`

### Callers
`module:plan_actual`, `module:holded_publication`.

### Inputs
Stable invoice identity and, when required, exact immutable revision identity.

### Outputs
Exact accepted immutable Invoice Card revision plus archive evidence required by the caller.

### Observable effect
Read-only.

### Enforces
Callers consume accepted immutable archive truth rather than mutable transport payloads.

### Errors
`InvoiceNotFoundError` when the exact accepted invoice or revision cannot be resolved. Missing, unaccepted, or quarantined-only revisions are not returned as normal archive truth.

### State impact
None.

---

## `public_op:registry_context.refresh_registry_context`

### Owner
`module:registry_context`

### Callers
Registry refresh scheduler/adapter.

### Inputs
One accepted full Registry project observation from the integration boundary.

### Outputs
Refreshed compact Registry context and WorkObject projection summary/evidence.

### Observable effect
Creates/updates Registry-derived WorkObject fields while preserving Cabinet-owned fields and existing objects absent from a later response.

### Enforces
Registry authority, one-way projection, accepted field set, no inferred deletion/completion, and stable `project_id` identity.

### Errors
`RegistryContextUnavailableError` when the supplied Registry observation is unavailable, invalid, incomplete, or cannot be translated and accepted safely. No partial unverifiable refresh is a normal result.

### State impact
Mutates Registry-derived local projection only; never writes Registry.

---

## `public_op:registry_context.validate_card_assignment`

### Owner
`module:registry_context`

### Callers
Registry refresh/assignment-review adapters.

### Inputs
Exact immutable Card assignment context and current Registry/WorkObject context.

### Outputs
Valid assignment or explicit review-required validation evidence. Archived project status, changed Registry facts, or otherwise review-worthy but observable context may produce review evidence without rewriting the immutable Card.

### Observable effect
May create/update Backend-owned assignment-validation evidence.

### Enforces
Registry status affects classification/review but does not rewrite or reject an otherwise valid immutable Card.

### Errors
`RegistryContextUnavailableError` when the current Registry observation required to perform a trustworthy validation is unavailable or cannot be accepted safely. Observable disagreement or review-worthy status is returned as validation evidence rather than guessed away.

### State impact
Mutates validation/review evidence only.

---

## `public_op:registry_context.get_assignment_validation`

### Owner
`module:registry_context`

### Callers
Registry/assignment adapters and downstream presentation surfaces.

### Inputs
Exact invoice/Card assignment identity.

### Outputs
Current assignment validation/review evidence and relevant observed Registry context.

### Observable effect
Read-only.

### Enforces
Unresolved facts remain unresolved rather than guessed.

### Errors
`AssignmentValidationNotFoundError` when no accepted assignment-validation evidence exists for the exact requested Card revision context.

### State impact
None.

---

## `public_op:registry_context.get_work_object`

### Owner
`module:registry_context`

### Callers
`module:plan_actual`.

### Inputs
Stable Registry `project_id`/WorkObject identity.

### Outputs
Exact current Cabinet WorkObject projection with Registry-derived and Cabinet-owned context kept distinguishable.

### Observable effect
Read-only.

### Enforces
One Registry project maps to at most one current WorkObject and Registry-derived facts remain source-attributed.

### Errors
`RegistryContextUnavailableError` when the requested WorkObject or Registry context required to resolve it cannot be obtained safely. The operation must not construct a placeholder WorkObject.

### State impact
None.

---

## `public_op:plan_actual.refresh_estimate_snapshot`

### Owner
`module:plan_actual`

### Callers
Plan/actual request or refresh adapters.

### Inputs
One current PresuPro estimate observation with stable PresuPro identity and accepted observable content/timestamps/context.

### Outputs
Exact immutable EstimateSnapshot identity, whether newly accepted or idempotently already known.

### Observable effect
May append one immutable EstimateSnapshot when canonical content changed.

### Enforces
Immutable snapshots, content-based idempotency, stable source identity, no inferred estimate lineage.

### Errors
`EstimateObservationRejectedError` when stable source identity is missing or the observation is unsupported, invalid, or unprocessable. Unexpected persistence/system failure is not an accepted partial snapshot.

### State impact
Appends immutable estimate evidence only.

---

## `public_op:plan_actual.calculate_plan_actual`

### Owner
`module:plan_actual`

### Callers
Plan/actual request adapters.

### Inputs
Exact pinned invoice revision evidence, WorkObject/project context, immutable EstimateSnapshot, confirmed matching decisions, and accepted conversion/forecast assumptions when applicable.

### Outputs
Reproducible plan-versus-actual result with pinned evidence identities, explicit unmatched facts, warnings that do not invalidate the calculation, and deterministic calculated values.

### Observable effect
Produces analytical artifact/result; does not rewrite source facts.

### Enforces
Confirmed matches only, explicit unmatched state, comparability preconditions, reproducibility, and source immutability.

### Errors
`PlanActualPreconditionError` when pinned project/invoice/estimate/match evidence is missing, incompatible, unresolved, or otherwise insufficient for a reproducible calculation, including unsupported unit-comparability preconditions.

### State impact
May persist derived analytical evidence/cache if implementation chooses; source records remain unchanged.

---

## `public_op:holded_publication.request_holded_publication`

### Owner
`module:holded_publication`

### Callers
Authorized local protected-operation adapters.

### Inputs
Exact confirmed Invoice Card revision identity, authorized actor context, and accepted publication prerequisites/evidence.

### Outputs
Logical publication state for an eligible request: verified success, an explicitly reconciliation-pending state after an ambiguous technical create outcome, or an existing equivalent logical publication.

### Observable effect
May create logical publication/attempt state and invoke the technical Holded gateway while hiding its sequencing from callers.

### Enforces
Eligibility, exact revision binding, duplicate logical publication prevention, one-attempt correlation, and verified-success requirement.

### Errors
`HoldedPublicationIneligibleError` when the exact revision fails accepted eligibility, duplicate-prevention, authorization, or required-source preconditions. Technical ambiguity that cannot be settled by the create path remains a reconciliation-pending publication state rather than being reported as successful publication.

### State impact
Mutates logical publication lifecycle; never mutates Invoice Card facts.

---

## `public_op:holded_publication.reconcile_holded_publication`

### Owner
`module:holded_publication`

### Callers
Authorized local protected-operation adapters.

### Inputs
Exact logical publication/attempt identity currently requiring reconciliation.

### Outputs
Settled verified publication after read-only recovery evidence identifies exactly one fully verified matching remote purchase.

### Observable effect
May advance logical publication lifecycle using read-only gateway recovery evidence.

### Enforces
No automatic second POST after ambiguous create; only verified remote evidence may settle publication.

### Errors
`HoldedReconciliationRequiredError` when zero matches, multiple matches, payload mismatch, lookup/GET failure, inconsistent attempt evidence, or other unresolved/conflicting evidence prevents a verified settlement.

### State impact
Mutates logical publication/reconciliation state only.

---

## `public_op:holded_gateway.create_holded_purchase`

### Owner
`module:holded_gateway`

### Callers
`module:holded_publication`.

### Inputs
One exact already-authorized Holded purchase attempt payload and stable attempt marker/identity.

### Outputs
Immutable technical attempt result including returned remote identifier/response evidence or explicit credential, transport, remote-rejection, malformed-response, or ambiguous-outcome classification.

### Observable effect
Performs the single permitted remote create mutation for that logical attempt.

### Enforces
Holded credential secrecy, exact request contract, maximum automatic POST count of one, raw response preservation, secret redaction.

### Errors
Failure to construct or durably preserve trustworthy technical attempt evidence at all. Classifiable remote and transport outcomes belong in `HoldedPublicationAttempt` and do not authorize hidden mutation retries.

### State impact
Persists technical attempt evidence; does not decide Cabinet publication eligibility/success.

---

## `public_op:holded_gateway.lookup_holded_purchase`

### Owner
`module:holded_gateway`

### Callers
`module:holded_publication`.

### Inputs
Stable publication attempt marker and/or canonical Holded document identifier when available.

### Outputs
Read-only remote lookup/GET evidence and technical match classification, including zero-match, multi-match, malformed-response, unknown-document, and transport-failure observations needed by publication reconciliation.

### Observable effect
Remote reads only.

### Enforces
Recovery uses observed Holded evidence without hidden mutation or business interpretation of unknown status values.

### Errors
Failure to obtain or construct trustworthy lookup evidence at all. Classifiable lookup outcomes remain evidence for `holded_publication` and are not silently converted to verified success.

### State impact
May append technical observation evidence only.

---

## `public_op:retention_release.evaluate_vps_release`

### Owner
`module:retention_release`

### Callers
Manual-release adapters.

### Inputs
Exact Registry `project_id` or working-set identity plus the release request context.

### Outputs
Allowed release evaluation with the exact affected set and the durable/replica evidence that proves the accepted release preconditions.

### Observable effect
May record evaluation evidence; performs no physical deletion.

### Enforces
Manual baseline, durable-local proof before release, no Registry-status deletion authority, exact working-set scope.

### Errors
`VpsReleaseBlockedError` when durable-local proof, synchronization observation, working-set identity, or retention evidence is missing, unavailable, inconsistent, or otherwise fails the accepted release preconditions.

### State impact
May append retention evaluation/audit state only.

---

## `public_op:retention_release.request_manual_vps_release`

### Owner
`module:retention_release`

### Callers
Manual-release adapters after an allowed evaluation.

### Inputs
Exact eligible working-set identity, explicit actor decision, and accepted release-evaluation evidence.

### Outputs
Recorded authorized release decision, or the existing equivalent decision for an idempotent repeated request.

### Observable effect
Records authorization for physical VPS working-copy release; a storage adapter performs the later physical effect.

### Enforces
Explicit manual intent, exact target, durable preconditions, decision idempotency, and audit history.

### Errors
`VpsReleaseBlockedError` when eligibility is no longer satisfied or the supplied evaluation is stale, mismatched, conflicting, or otherwise insufficient for the requested target.

### State impact
Mutates release-decision history only; does not itself delete physical replicas.
