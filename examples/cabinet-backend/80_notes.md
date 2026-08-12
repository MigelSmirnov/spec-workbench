# State 7 — Cabinet Backend generation notes

# access_control

authorize_operation: [SECURITY_BOUNDARY] Evaluate authorization only for the exact operation supplied by the caller and return the decision without performing the protected business operation.
authorize_operation: [VALIDATION_ERROR] Raise AuthenticationRequiredError when no valid authenticated principal exists and OperationForbiddenError when the authenticated principal lacks authority for the exact requested operation; possession of an entity identifier is never authority.
AccessControlBackend.authenticate: [SECURITY_BOUNDARY] Resolve the supplied local credential to one canonical authenticated principal context and do not expose reusable credential material in the returned context.
AccessControlBackend.authenticate: [VALIDATION_ERROR] Raise AuthenticationRequiredError when the supplied credential cannot establish a valid active local principal.
AccessControlBackend.authorize: [SECURITY_BOUNDARY] Evaluate the principal against the exact operation and current access-control state; keep local service authority distinct from synchronization-node identity.
AccessControlBackend.authorize: [VALIDATION_ERROR] Raise OperationForbiddenError when the authenticated principal is not authorized for the exact requested operation.

# synchronization

synchronize_invoice_work: [RULE_REFERENCE] Preserve delivery as a transport fact and never promote it to durable acceptance; use = rules.synchronization.delivery_implies_durable_acceptance.
synchronize_invoice_work: [ORCHESTRATION] Correlate transfer attempts and reconciliation with the supplied work selection and node identity so an ambiguous transport outcome remains explicitly reconcilable.
synchronize_invoice_work: [BEHAVIOR] Return authentication, compatibility, transport, remote-unavailability, and unresolved-delivery conditions as explicit synchronization outcome states rather than manufacturing an accepted result.
get_sync_status: [BEHAVIOR] Return the currently observed synchronization or replica state without making any durable-archive acceptance claim.
get_sync_status: [BEHAVIOR] Preserve unknown, unavailable, stale, or insufficient observations explicitly instead of fabricating a default synchronized state.

# durable_archive

accept_transfer_manifest: [BEHAVIOR] Accept a manifest only as one durable archive transition over the exact immutable card revision and supplied source replicas; repeated equivalent acceptance must not create a second logical acceptance.
accept_transfer_manifest: [VALIDATION_ERROR] Represent unsupported, integrity-invalid, conflicting, duplicate-review, incomplete, or quarantine-required evidence as the corresponding classified acceptance outcome instead of partially exposing an accepted manifest set.
accept_transfer_manifest: [PROVENANCE] Preserve acceptance evidence that identifies the exact manifest, card revision, and source evidence used for the decision.
verify_durable_acceptance: [BEHAVIOR] Derive the answer only from authoritative local archive evidence for the requested invoice and optional content hash.
verify_durable_acceptance: [BEHAVIOR] Return an explicit not-accepted or not-verifiable outcome when required durable evidence is absent or inconsistent; network delivery evidence is insufficient.
attach_local_source: [BEHAVIOR] Attach verified local source custody to the stable invoice target without rewriting the immutable accepted Invoice Card revision.
attach_local_source: [PROVENANCE] Preserve per-file provenance and verification outcome so repeated identical bytes are distinguishable from silent replacement of a different source.
attach_local_source: [VALIDATION_ERROR] Raise InvoiceNotFoundError when the stable invoice target cannot be resolved and SourceAttachmentRejectedError for unreadable, unsupported, hash-mismatched, wrong-target, or otherwise rejected source input before changing accepted source evidence.
get_source_status: [BEHAVIOR] Report source availability, completeness, attachment outcomes, and failed-verification evidence as distinct observed states.
get_source_status: [VALIDATION_ERROR] Raise InvoiceNotFoundError for an unknown accepted invoice target instead of synthesizing an empty source status.
get_archived_invoice: [BEHAVIOR] Return only an accepted immutable archived revision matching the requested invoice and optional content hash.
get_archived_invoice: [VALIDATION_ERROR] Raise InvoiceNotFoundError when the requested accepted revision cannot be resolved; quarantined-only, missing, or unaccepted revisions are not normal archive truth.

# registry_context

refresh_registry_context: [RULE_REFERENCE] Treat Registry as an upstream read-only authority and never write back through this operation; use = rules.registry_context.registry_is_read_only_from_cabinet.
refresh_registry_context: [BEHAVIOR] Refresh Registry-derived WorkObject context from the supplied complete observation while preserving Cabinet-owned fields and without inferring deletion merely because an earlier object is absent from a later response.
refresh_registry_context: [VALIDATION_ERROR] Raise RegistryContextUnavailableError when the supplied Registry observation is unavailable, invalid, or cannot be translated and accepted safely; do not partially apply an unverifiable refresh.
validate_card_assignment: [RULE_REFERENCE] Validation may change review evidence but must never rewrite the immutable Card assignment; use = rules.registry_context.registry_status_rewrites_immutable_card.
validate_card_assignment: [BEHAVIOR] Produce explicit assignment-validation evidence against the exact Card revision and current Registry context, preserving unresolved or review-required status when observable evidence does not validate the earlier choice.
validate_card_assignment: [VALIDATION_ERROR] Raise RegistryContextUnavailableError when the current Registry context required to perform the validation cannot be resolved safely.
get_assignment_validation: [BEHAVIOR] Return the current recorded validation evidence for the exact assignment identity without guessing a result from current Registry state.
get_assignment_validation: [VALIDATION_ERROR] Raise AssignmentValidationNotFoundError when no accepted validation evidence exists for the exact requested Card revision context.
get_work_object: [BEHAVIOR] Return the current WorkObject for the exact Registry project identity with Registry-derived and Cabinet-owned context remaining distinguishable.
get_work_object: [VALIDATION_ERROR] Raise RegistryContextUnavailableError when the requested WorkObject or required Registry project context cannot be resolved safely instead of constructing a placeholder object.

# plan_actual

refresh_estimate_snapshot: [BEHAVIOR] Create a new immutable estimate snapshot only when the canonical observed estimate content is not already represented by the same stable source identity.
refresh_estimate_snapshot: [PROVENANCE] Preserve enough source identity and observation evidence for later plan/actual calculations to pin the exact estimate snapshot they consumed.
refresh_estimate_snapshot: [VALIDATION_ERROR] Raise EstimateObservationRejectedError when the PresuPro observation lacks stable source identity or contains unsupported or unprocessable content; never accept a partial snapshot.
calculate_plan_actual: [RULE_REFERENCE] Consume only confirmed matching decisions when calculating plan versus actual; use = rules.plan_actual.confirmed_matches_only.
calculate_plan_actual: [RULE_REFERENCE] Treat source invoice, Registry, and estimate records as immutable inputs; use = rules.plan_actual.source_records_are_immutable.
calculate_plan_actual: [BEHAVIOR] Produce a reproducible analysis pinned to the exact supplied evidence identities and retain explicit unmatched facts and non-blocking warnings instead of silently coercing incomparable inputs.
calculate_plan_actual: [VALIDATION_ERROR] Raise PlanActualPreconditionError when required pinned evidence, assignment context, match references, or unit comparability preconditions are not satisfied.

# holded_publication

request_holded_publication: [RULE_REFERENCE] Permit only the configured single automatic create attempt for one logical publication attempt; use = rules.holded_publication.max_automatic_create_attempts_per_logical_attempt.
request_holded_publication: [RULE_REFERENCE] An ambiguous create outcome must enter reconciliation and must not trigger another automatic create; use = rules.holded_publication.ambiguous_create_allows_automatic_retry.
request_holded_publication: [BEHAVIOR] Bind the logical publication to the exact confirmed Invoice Card revision and preserve an existing equivalent logical publication instead of creating a duplicate obligation; an ambiguous technical create remains reconciliation-pending.
request_holded_publication: [VALIDATION_ERROR] Raise HoldedPublicationIneligibleError when the exact revision fails accepted eligibility, duplicate-prevention, authorization, or required-source preconditions; never manufacture a successful logical publication for an ineligible request.
reconcile_holded_publication: [RULE_REFERENCE] A recovered remote candidate may settle the publication only after full verification; use = rules.holded_publication.recovered_candidate_requires_full_verification.
reconcile_holded_publication: [BEHAVIOR] Reconcile an ambiguous logical attempt using read-only remote evidence and return a settled publication only when the evidence identifies exactly one fully verified matching remote purchase.
reconcile_holded_publication: [VALIDATION_ERROR] Raise HoldedReconciliationRequiredError when zero matches, multiple matches, payload mismatch, lookup failure, or inconsistent attempt evidence leaves the logical publication unresolved or conflicting.

# holded_gateway

create_holded_purchase: [ORCHESTRATION] Perform the one technical remote create for the supplied already-authorized payload and stable publication-attempt identity, then persist immutable technical outcome evidence.
create_holded_purchase: [SECURITY_BOUNDARY] Keep Holded credentials inside the gateway boundary and redact reusable secret material from logs, returned business objects, and ordinary attempt evidence.
create_holded_purchase: [BEHAVIOR] Preserve credential failure, remote rejection, timeout, malformed response, or ambiguous network outcome as explicit immutable technical attempt evidence rather than retrying the mutation or claiming remote failure/success without proof.
lookup_holded_purchase: [BEHAVIOR] Perform read-only recovery lookup using the supplied stable attempt marker and optional document identifier and return observed technical match evidence without mutating Holded.
lookup_holded_purchase: [BEHAVIOR] Preserve zero-match, multi-match, malformed-response, unknown-document, and transport-failure observations explicitly as lookup evidence for publication reconciliation.

# retention_release

evaluate_vps_release: [RULE_REFERENCE] Evaluate release under the manual-release baseline; use = rules.retention_release.mode.
evaluate_vps_release: [RULE_REFERENCE] Require authoritative durable local verification before allowing release; use = rules.retention_release.require_durable_local_verification_before_release.
evaluate_vps_release: [RULE_REFERENCE] Registry status alone must never authorize release; use = rules.retention_release.registry_status_may_trigger_release.
evaluate_vps_release: [BEHAVIOR] Return an allowed evaluation for the exact affected working set and include the evidence identity on which the decision depends without performing physical deletion.
evaluate_vps_release: [VALIDATION_ERROR] Raise VpsReleaseBlockedError when durable replica proof, synchronization observation, working-set identity, or retention evidence is missing, inconsistent, or does not satisfy the accepted release preconditions.
request_manual_vps_release: [BEHAVIOR] Record an explicit release decision only for the exact target covered by a still-applicable allowed evaluation; repeated equivalent requests must be idempotent and return the existing equivalent decision.
request_manual_vps_release: [VALIDATION_ERROR] Raise VpsReleaseBlockedError when the evaluation is stale, mismatched, newly ineligible, or conflicts with the requested target instead of authorizing physical deletion.

# deterministic HTTP seams

create_app: [ORCHESTRATION] Construct the application using the already-declared deterministic router wiring and bind the supplied access-control backend into application state without adding business policy.
extract_bearer_credential: [SECURITY_BOUNDARY] Extract only the accepted bearer credential from the request boundary without interpreting business authorization.
extract_bearer_credential: [VALIDATION_ERROR] Raise AuthenticationRequiredError when the required bearer authentication material is absent or malformed.
resolve_local_principal: [SECURITY_BOUNDARY] Resolve the extracted credential through the access-control backend and return the canonical principal context used by protected handlers.
resolve_local_principal: [VALIDATION_ERROR] Propagate AuthenticationRequiredError when the extracted credential cannot establish a valid local principal.
attach_local_source_handler: [ORCHESTRATION] Own only the multipart transport transformation that cannot be lowered by the deterministic table router, then delegate archive policy to attach_local_source.
attach_local_source_handler: [DEPENDENCY_BOUNDARY] Do not duplicate source-acceptance, authorization, archive, or persistence policy inside the irregular HTTP companion handler.
