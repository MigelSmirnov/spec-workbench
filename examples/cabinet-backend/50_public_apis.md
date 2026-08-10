# State 5 — Cabinet Backend public module APIs

## Status

State 5 is in progress. These entries define public cross-boundary operations proven by State 4. They intentionally stop before exact Python signatures, concrete DTO field lists, transport bindings, or private helper functions; those belong to State 6.

---

## `api:access_control.authorize_operation`

### Owner
`module:access_control`

### Callers
Local protected-operation adapters.

### Inputs
Authenticated principal context and one exact protected Cabinet operation identifier.

### Outputs
Authorization decision plus security/audit evidence sufficient for the caller to allow or deny that exact operation.

### Observable effect
May record authorization/security evidence; does not perform the protected business operation itself.

### Enforces
Exact-operation authorization, principal/capability separation, revocation, and local-service versus synchronization-identity boundaries.

### Errors
Unauthenticated principal, revoked credential, insufficient capability, invalid operation vocabulary, security-policy refusal.

### State impact
May append security evidence; must not mutate invoice, Registry, PresuPro, Holded, or retention state.

---

## `api:synchronization.synchronize_invoice_work`

### Owner
`module:synchronization`

### Callers
Synchronization scheduler/adapter.

### Inputs
One exact synchronization work selection and synchronization-node context.

### Outputs
Transfer/delivery/reconciliation outcome that preserves the distinction between delivered and durably accepted.

### Observable effect
May perform authenticated transfer attempts and record transport observations/receipts.

### Enforces
Outbound synchronization identity, retry/reconciliation semantics, transfer identity, and delivery-versus-acceptance separation.

### Errors
Authentication/transport failure, incompatible package/contract, unknown outcome requiring reconciliation, remote unavailability.

### State impact
Mutates synchronization attempt/receipt state only; durable acceptance remains owned by `module:durable_archive`.

---

## `api:synchronization.get_sync_status`

### Owner
`module:synchronization`

### Callers
`module:retention_release`.

### Inputs
Exact transfer, replica, invoice work, or working-set identity required by the release evaluation.

### Outputs
Current synchronization/replica observation without any claim of durable archive acceptance.

### Observable effect
Read-only with respect to business state.

### Enforces
Transport facts remain transport facts.

### Errors
Unknown target, unavailable observation, stale/insufficient synchronization evidence.

### State impact
None beyond optional observation/audit recording.

---

## `api:durable_archive.accept_transfer_manifest`

### Owner
`module:durable_archive`

### Callers
`module:synchronization`.

### Inputs
One exact transfer manifest, immutable Invoice Card revision evidence, and required source evidence presented for local acceptance.

### Outputs
Accepted, already-accepted, rejected, quarantined, or explicit incomplete/failure outcome with durable acceptance evidence when applicable.

### Observable effect
May create durable archive records, source custody, quarantine state, and acceptance evidence atomically under the accepted rules.

### Enforces
Card immutability, manifest idempotency, source integrity, duplicate policy, quarantine policy, and atomic visibility.

### Errors
Unsupported Card/version, integrity/hash failure, conflicting predecessor/evidence, duplicate review, persistence failure, quarantine-required condition.

### State impact
Mutates durable archive state only according to accepted acceptance/quarantine transitions.

---

## `api:durable_archive.verify_durable_acceptance`

### Owner
`module:durable_archive`

### Callers
`module:synchronization`, `module:retention_release`.

### Inputs
Exact archive target or working-set evidence identity.

### Outputs
Authoritative durable-acceptance proof or explicit not-accepted/not-verifiable result.

### Observable effect
Read-only verification of archive truth.

### Enforces
Network delivery or external status can never substitute for local durable proof.

### Errors
Unknown target, missing/unverified required replica, inconsistent archive evidence.

### State impact
None beyond optional verification evidence.

---

## `api:durable_archive.attach_local_source`

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
Unknown invoice, unsupported/unreadable file, hash mismatch, wrong target, storage failure, ambiguous target before invocation.

### State impact
Mutates source evidence only; accepted Card bytes/content hash remain immutable.

---

## `api:durable_archive.get_source_status`

### Owner
`module:durable_archive`

### Callers
Local source-attachment adapters.

### Inputs
Exact accepted invoice/source package identity.

### Outputs
Current source availability, completeness, attachment outcomes, and missing/failed evidence state.

### Observable effect
Read-only.

### Enforces
Truthful distinction among available, missing, and failed-verification evidence.

### Errors
Unknown invoice/source target or unavailable archive evidence.

### State impact
None.

---

## `api:durable_archive.get_archived_invoice`

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
Invoice/revision not found, not accepted, quarantined-only visibility, unavailable required evidence.

### State impact
None.

---

## `api:registry_context.refresh_registry_context`

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
Registry observation/translation failure, invalid project data, incomplete refresh evidence.

### State impact
Mutates Registry-derived local projection only; never writes Registry.

---

## `api:registry_context.validate_card_assignment`

### Owner
`module:registry_context`

### Callers
Registry refresh/assignment-review adapters.

### Inputs
Exact immutable Card assignment context and current Registry/WorkObject context.

### Outputs
Valid assignment or explicit review-required validation evidence.

### Observable effect
May create/update Backend-owned assignment-validation evidence.

### Enforces
Registry status affects classification/review but does not rewrite or reject an otherwise valid immutable Card.

### Errors
Missing/archived/unavailable project context, inconsistent references, insufficient Registry evidence.

### State impact
Mutates validation/review evidence only.

---

## `api:registry_context.get_assignment_validation`

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
Unknown assignment or unavailable validation evidence.

### State impact
None.

---

## `api:registry_context.get_work_object`

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
Unknown WorkObject, unavailable project context, unresolved source presence.

### State impact
None.

---

## `api:plan_actual.refresh_estimate_snapshot`

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
Invalid/missing source identity, unprocessable content, unsupported observation, persistence failure.

### State impact
Appends immutable estimate evidence only.

---

## `api:plan_actual.calculate_plan_actual`

### Owner
`module:plan_actual`

### Callers
Plan/actual request adapters.

### Inputs
Exact pinned invoice revision evidence, WorkObject/project context, immutable EstimateSnapshot, confirmed matching decisions, and accepted conversion/forecast assumptions when applicable.

### Outputs
Reproducible plan-versus-actual result with pinned evidence identities, unmatched facts, warnings/refusals, and deterministic calculated values.

### Observable effect
Produces analytical artifact/result; does not rewrite source facts.

### Enforces
Confirmed matches only, explicit unmatched state, comparability preconditions, reproducibility, and source immutability.

### Errors
Missing pinned evidence, unresolved project assignment where required, incomparable units/quantities, invalid match reference, unsupported calculation precondition.

### State impact
May persist derived analytical evidence/cache if implementation chooses; source records remain unchanged.

---

## `api:holded_publication.request_holded_publication`

### Owner
`module:holded_publication`

### Callers
Authorized local protected-operation adapters.

### Inputs
Exact confirmed Invoice Card revision identity, authorized actor context, and accepted publication prerequisites/evidence.

### Outputs
Logical publication outcome/state including verified success, eligibility refusal, unknown/reconciliation-required state, or existing logical publication.

### Observable effect
May create logical publication/attempt state and invoke the technical Holded gateway while hiding its sequencing from callers.

### Enforces
Eligibility, exact revision binding, duplicate logical publication prevention, one-attempt correlation, and verified-success requirement.

### Errors
Ineligible invoice/source/context, existing conflicting publication, gateway technical failure, verification failure, unknown outcome.

### State impact
Mutates logical publication lifecycle; never mutates Invoice Card facts.

---

## `api:holded_publication.reconcile_holded_publication`

### Owner
`module:holded_publication`

### Callers
Authorized local protected-operation adapters.

### Inputs
Exact logical publication/attempt identity currently requiring reconciliation.

### Outputs
Settled verified publication, still-unknown state, conflict/reconciliation-required result, or explicit failure evidence.

### Observable effect
May advance logical publication lifecycle using read-only gateway recovery evidence.

### Enforces
No automatic second POST after ambiguous create; only verified remote evidence may settle publication.

### Errors
Unknown attempt, zero/multiple marker matches, payload mismatch, lookup/GET failure, inconsistent attempt evidence.

### State impact
Mutates logical publication/reconciliation state only.

---

## `api:holded_gateway.create_holded_purchase`

### Owner
`module:holded_gateway`

### Callers
`module:holded_publication`.

### Inputs
One exact already-authorized Holded purchase attempt payload and stable attempt marker/identity.

### Outputs
Immutable technical attempt result including returned remote identifier/response evidence or ambiguous/failure classification.

### Observable effect
Performs the single permitted remote create mutation for that logical attempt.

### Enforces
Holded credential secrecy, exact request contract, maximum automatic POST count of one, raw response preservation, secret redaction.

### Errors
Credential failure, transport timeout, remote rejection, malformed response, ambiguous network outcome.

### State impact
Persists technical attempt evidence; does not decide Cabinet publication eligibility/success.

---

## `api:holded_gateway.lookup_holded_purchase`

### Owner
`module:holded_gateway`

### Callers
`module:holded_publication`.

### Inputs
Stable publication attempt marker and/or canonical Holded document identifier when available.

### Outputs
Read-only remote lookup/GET evidence and technical match classification needed by publication reconciliation.

### Observable effect
Remote reads only.

### Enforces
Recovery uses observed Holded evidence without hidden mutation or business interpretation of unknown status values.

### Errors
Lookup/GET transport failure, zero/multiple matches, malformed response, unknown document.

### State impact
May append technical observation evidence only.

---

## `api:retention_release.evaluate_vps_release`

### Owner
`module:retention_release`

### Callers
Manual-release adapters.

### Inputs
Exact Registry `project_id` or working-set identity plus the release request context.

### Outputs
Allowed/blocked release evaluation with exact affected set and required durable/replica evidence.

### Observable effect
May record evaluation evidence; performs no physical deletion.

### Enforces
Manual baseline, durable-local proof before release, no Registry-status deletion authority, exact working-set scope.

### Errors
Missing/unverified durable replicas, unavailable synchronization observation, unknown working set, inconsistent retention evidence.

### State impact
May append retention evaluation/audit state only.

---

## `api:retention_release.request_manual_vps_release`

### Owner
`module:retention_release`

### Callers
Manual-release adapters after an allowed evaluation.

### Inputs
Exact eligible working-set identity, explicit actor decision, and accepted release-evaluation evidence.

### Outputs
Recorded authorized release decision or blocked/idempotent/conflicting decision result.

### Observable effect
Records authorization for physical VPS working-copy release; a storage adapter performs the later physical effect.

### Enforces
Explicit manual intent, exact target, durable preconditions, decision idempotency, and audit history.

### Errors
Eligibility no longer satisfied, stale/mismatched evidence, conflicting target, duplicate request with incompatible evidence.

### State impact
Mutates release-decision history only; does not itself delete physical replicas.
