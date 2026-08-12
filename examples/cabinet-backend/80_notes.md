# State 7 — Cabinet Backend generation notes

# access_control

authorize_operation: [SECURITY_BOUNDARY] Evaluate authorization only for the exact operation supplied by the caller and return the decision without performing the protected business operation.
authorize_operation: [VALIDATION_ERROR] Reject an unauthenticated, revoked, or otherwise ineligible principal instead of treating possession of an entity identifier as authority.
AccessControlBackend.authenticate: [SECURITY_BOUNDARY] Resolve the supplied local credential to one canonical authenticated principal context and do not expose reusable credential material in the returned context.
AccessControlBackend.authorize: [SECURITY_BOUNDARY] Evaluate the principal against the exact operation and current access-control state; keep local service authority distinct from synchronization-node identity.

# synchronization

synchronize_invoice_work: [RULE_REFERENCE] Preserve delivery as a transport fact and never promote it to durable acceptance; use = rules.synchronization.delivery_implies_durable_acceptance.
synchronize_invoice_work: [ORCHESTRATION] Correlate transfer attempts and reconciliation with the supplied work selection and node identity so an ambiguous transport outcome remains explicitly reconcilable.
synchronize_invoice_work: [VALIDATION_ERROR] Surface authentication, compatibility, transport, and unresolved-outcome failures explicitly rather than manufacturing an accepted result.
get_sync_status: [BEHAVIOR] Return the currently observed synchronization or replica state without making any durable-archive acceptance claim.
get_sync_status: [VALIDATION_ERROR] Report unknown or unavailable observation targets explicitly instead of fabricating a default synchronized state.

# durable_archive

accept_transfer_manifest: [BEHAVIOR] Accept a manifest only as one durable archive transition over the exact immutable card revision and supplied source replicas; repeated equivalent acceptance must not create a second logical acceptance.
accept_transfer_manifest: [VALIDATION_ERROR] Reject or quarantine unsupported, integrity-invalid, conflicting, or incomplete evidence instead of partially exposing an accepted manifest set.
accept_transfer_manifest: [PROVENANCE] Preserve acceptance evidence that identifies the exact manifest, card revision, and source evidence used for the decision.
verify_durable_acceptance: [BEHAVIOR] Derive the answer only from authoritative local archive evidence for the requested invoice and optional content hash.
verify_durable_acceptance: [VALIDATION_ERROR] Return an explicit not-verifiable outcome when required durable evidence is absent or inconsistent; network delivery evidence is insufficient.
attach_local_source: [BEHAVIOR] Attach verified local source custody to the stable invoice target without rewriting the immutable accepted Invoice Card revision.
attach_local_source: [PROVENANCE] Preserve per-file provenance and verification outcome so repeated identical bytes are distinguishable from silent replacement of a different source.
attach_local_source: [VALIDATION_ERROR] Reject unreadable, unsupported, hash-mismatched, wrong-target, or otherwise ambiguous source input before changing accepted source evidence.
get_source_status: [BEHAVIOR] Report source availability, completeness, attachment outcomes, and failed-verification evidence as distinct observed states.
get_source_status: [VALIDATION_ERROR] Do not synthesize an empty source status for an unknown invoice or unavailable archive target.
get_archived_invoice: [BEHAVIOR] Return only an accepted immutable archived revision matching the requested invoice and optional content hash.
get_archived_invoice: [VALIDATION_ERROR] Do not expose quarantined-only, missing, or unaccepted revisions as normal archive truth.

# registry_context

refresh_registry_context: [RULE_REFERENCE] Treat Registry as an upstream read-only authority and never write back through this operation; use = rules.registry_context.registry_is_read_only_from_cabinet.
refresh_registry_context: [BEHAVIOR] Refresh Registry-derived WorkObject context from the supplied complete observation while preserving Cabinet-owned fields and without inferring deletion merely because an earlier object is absent from a later response.
refresh_registry_context: [VALIDATION_ERROR] Reject invalid or untranslatable project observations rather than partially applying an unverifiable refresh.
validate_card_assignment: [RULE_REFERENCE] Validation may change review evidence but must never rewrite the immutable Card assignment; use = rules.registry_context.registry_status_rewrites_immutable_card.
validate_card_assignment: [BEHAVIOR] Produce explicit assignment-validation evidence against the exact Card revision and current Registry context, preserving unresolved status when evidence is insufficient.
get_assignment_validation: [BEHAVIOR] Return the current recorded validation evidence for the exact assignment identity without guessing a result from current Registry state.
get_assignment_validation: [VALIDATION_ERROR] Report missing validation evidence explicitly rather than returning a fabricated valid result.
get_work_object: [BEHAVIOR] Return the current WorkObject for the exact Registry project identity with Registry-derived and Cabinet-owned context remaining distinguishable.
get_work_object: [VALIDATION_ERROR] Report an unknown or unavailable WorkObject explicitly instead of constructing a placeholder object.

# plan_actual

refresh_estimate_snapshot: [BEHAVIOR] Create a new immutable estimate snapshot only when the canonical observed estimate content is not already represented by the same stable source identity.
refresh_estimate_snapshot: [PROVENANCE] Preserve enough source identity and observation evidence for later plan/actual calculations to pin the exact estimate snapshot they consumed.
refresh_estimate_snapshot: [VALIDATION_ERROR] Reject observations with missing stable source identity or unprocessable content rather than accepting a partial snapshot.
calculate_plan_actual: [RULE_REFERENCE] Consume only confirmed matching decisions when calculating plan versus actual; use = rules.plan_actual.confirmed_matches_only.
calculate_plan_actual: [RULE_REFERENCE] Treat source invoice, Registry, and estimate records as immutable inputs; use = rules.plan_actual.source_records_are_immutable.
calculate_plan_actual: [BEHAVIOR] Produce a reproducible analysis pinned to the exact supplied evidence identities and retain explicit unmatched facts and warnings instead of silently coercing incomparable inputs.
calculate_plan_actual: [VALIDATION_ERROR] Refuse calculation when required pinned evidence, assignment context, match references, or unit comparability preconditions are not satisfied.

# holded_publication

request_holded_publication: [RULE_REFERENCE] Permit only the configured single automatic create attempt for one logical publication attempt; use = rules.holded_publication.max_automatic_create_attempts_per_logical_attempt.
request_holded_publication: [RULE_REFERENCE] An ambiguous create outcome must enter reconciliation and must not trigger another automatic create; use = rules.holded_publication.ambiguous_create_allows_automatic_retry.
request_holded_publication: [BEHAVIOR] Bind the logical publication to the exact confirmed Invoice Card revision and preserve an existing equivalent logical publication instead of creating a duplicate obligation.
request_holded_publication: [VALIDATION_ERROR] Refuse publication when eligibility, exact-target, authorization, or required source evidence is not satisfied.
reconcile_holded_publication: [RULE_REFERENCE] A recovered remote candidate may settle the publication only after full verification; use = rules.holded_publication.recovered_candidate_requires_full_verification.
reconcile_holded_publication: [BEHAVIOR] Reconcile an ambiguous logical attempt using read-only remote evidence and keep the publication unresolved when the evidence does not identify exactly one verified matching remote purchase.
reconcile_holded_publication: [VALIDATION_ERROR] Treat zero matches, multiple matches, payload mismatch, lookup failure, or inconsistent attempt evidence as explicit reconciliation outcomes rather than success.

# holded_gateway

create_holded_purchase: [ORCHESTRATION] Perform the one technical remote create for the supplied already-authorized payload and stable publication-attempt identity, then persist immutable technical outcome evidence.
create_holded_purchase: [SECURITY_BOUNDARY] Keep Holded credentials inside the gateway boundary and redact reusable secret material from logs, returned business objects, and ordinary attempt evidence.
create_holded_purchase: [VALIDATION_ERROR] Preserve timeout or ambiguous network outcomes as ambiguous technical evidence rather than retrying the mutation or claiming remote failure/success without proof.
lookup_holded_purchase: [BEHAVIOR] Perform read-only recovery lookup using the supplied stable attempt marker and optional document identifier and return observed technical match evidence without mutating Holded.
lookup_holded_purchase: [VALIDATION_ERROR] Preserve zero-match, multi-match, malformed-response, unknown-document, and transport-failure outcomes explicitly.

# retention_release

evaluate_vps_release: [RULE_REFERENCE] Evaluate release under the manual-release baseline; use = rules.retention_release.mode.
evaluate_vps_release: [RULE_REFERENCE] Require authoritative durable local verification before allowing release; use = rules.retention_release.require_durable_local_verification_before_release.
evaluate_vps_release: [RULE_REFERENCE] Registry status alone must never authorize release; use = rules.retention_release.registry_status_may_trigger_release.
evaluate_vps_release: [BEHAVIOR] Return an allowed or blocked evaluation for the exact affected working set and include the evidence identity on which that evaluation depends without performing physical deletion.
evaluate_vps_release: [VALIDATION_ERROR] Block evaluation when durable replica, synchronization observation, working-set identity, or retention evidence is missing or inconsistent.
request_manual_vps_release: [BEHAVIOR] Record an explicit release decision only for the exact target covered by a still-applicable allowed evaluation; repeated equivalent requests must not create conflicting decisions.
request_manual_vps_release: [VALIDATION_ERROR] Reject stale, mismatched, newly ineligible, or conflicting release evidence instead of authorizing physical deletion.

# deterministic HTTP seams

create_app: [ORCHESTRATION] Construct the application using the already-declared deterministic router wiring and bind the supplied access-control backend into application state without adding business policy.
extract_bearer_credential: [SECURITY_BOUNDARY] Extract only the accepted bearer credential from the request boundary and reject absent or malformed authentication material without interpreting business authorization.
resolve_local_principal: [SECURITY_BOUNDARY] Resolve the extracted credential through the access-control backend and return the canonical principal context used by protected handlers.
attach_local_source_handler: [ORCHESTRATION] Own only the multipart transport transformation that cannot be lowered by the deterministic table router, then delegate archive policy to attach_local_source.
attach_local_source_handler: [DEPENDENCY_BOUNDARY] Do not duplicate source-acceptance, authorization, archive, or persistence policy inside the irregular HTTP companion handler.
