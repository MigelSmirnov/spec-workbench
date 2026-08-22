# State 7 — Cabinet Backend generation notes

# access_control

authorize_operation: [SECURITY_BOUNDARY] MUST evaluate authorization only for the exact operation supplied by the caller and return the decision without performing the protected business operation.
authorize_operation: [VALIDATION_ERROR] Raise AuthenticationRequiredError when no valid authenticated principal exists and OperationForbiddenError when the authenticated principal lacks authority for the exact requested operation; possession of an entity identifier is never authority.
AccessControlBackend.authenticate: [SECURITY_BOUNDARY] Resolve the supplied local credential to one canonical authenticated principal context and do not expose reusable credential material in the returned context.
AccessControlBackend.authenticate: [VALIDATION_ERROR] Raise AuthenticationRequiredError when the supplied credential cannot establish a valid active local principal.
AccessControlBackend.authorize: [SECURITY_BOUNDARY] Evaluate the principal against the exact operation and current access-control state; keep local service authority distinct from synchronization-node identity.
AccessControlBackend.authorize: [VALIDATION_ERROR] Raise OperationForbiddenError when the authenticated principal is not authorized for the exact requested operation.
LocalAccessControlService.__init__: [DEPENDENCY_BOUNDARY] Retain the exact supplied AccessControlRepository and credential pepper; fail construction when the pepper is empty, never log it, and never open connections or read environment variables.
LocalAccessControlService.authenticate: [ORCHESTRATION] Parse the presented token through parse_service_token, begin one repository transaction, lock the abuse context derived from the credential id, load the throttle state, credential, and principal, verify the secret through verify_service_secret with the retained pepper, and commit exactly once; malformed tokens are refused before any state is read.
LocalAccessControlService.authenticate: [RULE_REFERENCE] Begin progressive delay at = rules.access_control.progressive_delay_after_failures and temporary blocking at = rules.access_control.temporary_block_after_failures.
LocalAccessControlService.authenticate: [RULE_REFERENCE] Keep temporary refusal active for = rules.access_control.temporary_block_seconds; the verifier algorithm is = rules.access_control.credential_hash_algorithm and is applied only through credential_security.
LocalAccessControlService.authenticate: [SECURITY_BOUNDARY] Accept only an active credential of an active principal whose verifier matches; return a context containing identifiers and the authentication time but no reusable secret.
LocalAccessControlService.authenticate: [VALIDATION_ERROR] Reject malformed, unknown, revoked, delayed, or temporarily blocked credentials with AuthenticationRequiredError; a refusal still upserts the throttle state and inserts secret-free audit evidence before rollback-free commit of those rows.
LocalAccessControlService.authenticate: [BEHAVIOR] On failure increment the consecutive-failure counter and compute delay_until or blocked_until from the rules; on success reset the counter to zero, update the credential last_authenticated_at, and insert audit evidence; audit history is never deleted.
LocalAccessControlService.authorize: [SECURITY_BOUNDARY] Reread the current principal and credential for the supplied context and allow only an exact operation present in the stored capability tuple; stale context, localhost origin, client name, prompt, or entity identifier is not authority.
LocalAccessControlService.authorize: [VALIDATION_ERROR] Raise AuthenticationRequiredError for a stale, revoked, or unknown context and OperationForbiddenError for an active principal lacking the exact capability; insert refusal evidence without performing the protected operation.
LocalAccessControlService.authorize: [FIELD_ASSIGNMENT] Populate AuthorizationDecision from the exact principal, operation, outcome, timestamp, reason code, and the evidence_id of the SecurityAuditRecord inserted in the same transaction; never fabricate evidence identifiers.
LocalAccessControlService.enroll_local_service: [BEHAVIOR] Issue the credential through issue_service_credential with the retained pepper, insert the principal, the credential carrying only the verifier, and audit evidence in one transaction, and return the plaintext token exactly once in IssuedServiceCredential.
LocalAccessControlService.rotate_local_service_credential: [BEHAVIOR] Under the principal lock insert one replacement credential and update every prior active credential of the exact principal to revoked while preserving identity and capabilities; return the new token once and never log it.
LocalAccessControlService.revoke_local_service_principal: [BEHAVIOR] Under the principal lock update the principal to its terminal revoked status, update all active credentials to revoked, and insert evidence; never delete security history.
create_access_control_schema: [CONFIG_REFERENCE] MUST idempotently create only the tables named by = config.persistence.principal_table_name and = config.persistence.credential_table_name and = config.persistence.throttle_state_table_name and = config.persistence.security_audit_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresAccessControlRepository.__init__: [SECURITY_BOUNDARY] Bind to the supplied PostgreSQL URL, treat it as secret, never log it, and read no environment variables.
PostgresAccessControlRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact access-control operation and reject nested begin.
PostgresAccessControlRepository.commit: [BEHAVIOR] Commit the active transaction exactly once and release its connection.
PostgresAccessControlRepository.rollback: [FALLBACK] Roll back idempotently, release the connection, and preserve the original failure.
PostgresAccessControlRepository.lock_principal: [BEHAVIOR] Acquire the transaction-scoped lock for the exact principal before its credentials are read or changed.
PostgresAccessControlRepository.lock_abuse_context: [BEHAVIOR] Acquire the transaction-scoped lock for the exact abuse context before throttle state is read or changed.
PostgresAccessControlRepository.load_principal: [BEHAVIOR] Return the exact persisted principal or None and never synthesize one.
PostgresAccessControlRepository.insert_principal: [PROVENANCE] Append one principal row for the exact principal_id inside the active locked transaction; duplicates fail on uniqueness.
PostgresAccessControlRepository.update_principal_status: [PROVENANCE] Write status and revoked_at for the exact existing principal_id inside the active locked transaction; fail when absent and never change display_name, principal_kind, capabilities, or created_at.
PostgresAccessControlRepository.load_credential: [BEHAVIOR] Return the exact persisted credential or None and never synthesize one.
PostgresAccessControlRepository.list_credentials_for_principal: [DETERMINISM_OR_ORDERING] Return every credential of the exact principal with the supplied status in stable issued_at and credential_id order.
PostgresAccessControlRepository.insert_credential: [PROVENANCE] Append one credential row carrying only the verifier for the exact credential_id inside the active locked transaction; duplicates fail on uniqueness.
PostgresAccessControlRepository.update_credential: [PROVENANCE] Write status, revoked_at, and last_authenticated_at for the exact existing credential_id inside the active locked transaction; fail when absent and never change secret_hash, principal_id, issued_at, or rotated_from_credential_id.
PostgresAccessControlRepository.load_throttle_state: [BEHAVIOR] Return the exact persisted throttle state for the abuse context or None.
PostgresAccessControlRepository.upsert_throttle_state: [PROVENANCE] Insert the throttle state by abuse_context_hash or, when it exists, update credential_id, consecutive_failures, delay_until, blocked_until, and updated_at inside the active locked transaction.
PostgresAccessControlRepository.insert_audit_record: [PROVENANCE] Append one immutable secret-free audit row for the exact evidence_id inside the active transaction; never update or delete audit rows.
issue_service_credential: [SECURITY_BOUNDARY] Generate entropy_bytes of cryptographically random secret, return the token as credential_id plus separator plus secret, and return only the Argon2id verifier of the peppered secret; never log the secret or pepper.
parse_service_token: [VALIDATION_ERROR] Raise ValueError for a token without the separator, an unsafe credential id, or an empty secret; never touch storage.
verify_service_secret: [SECURITY_BOUNDARY] Compare the peppered secret against the Argon2id verifier in constant time and return False on any malformed input instead of raising.
create_local_app: [CONFIG_REFERENCE] Read the PostgreSQL URL only from the environment variable named by = config.access_control.database_url_env.
create_local_app: [CONFIG_REFERENCE] Read the credential pepper only from the environment variable named by = config.access_control.credential_pepper_env and use = config.access_control.deployment_owner_uid_env for the offline-owner boundary.
create_local_app: [VALIDATION_ERROR] Fail startup when required environment values are absent or backend initialization fails; never substitute an in-memory, anonymous, or allow-all backend.
enroll_local_agent: [SECURITY_BOUNDARY] MUST permit enrollment only from the offline local administration entry point running as the configured Linux deployment owner; never expose this operation through HTTP or MCP.
enroll_local_agent: [RETURN_SHAPE] Return IssuedServiceCredential exactly once to the invoking owner and never persist or log its credential field.
rotate_local_agent_credential: [SECURITY_BOUNDARY] MUST require the offline Linux-owner boundary and delegate one exact active principal to PostgreSQL rotation.
revoke_local_agent: [SECURITY_BOUNDARY] MUST require the offline Linux-owner boundary and delegate one exact active principal to terminal revocation.

# synchronization

synchronize_invoice_work: [RULE_REFERENCE] Preserve delivery as a transport fact and never promote it to durable acceptance; use = rules.synchronization.delivery_implies_durable_acceptance.
synchronize_invoice_work: [ORCHESTRATION] Correlate transfer attempts and reconciliation with the supplied work selection and node identity so an ambiguous transport outcome remains explicitly reconcilable.
synchronize_invoice_work: [BEHAVIOR] Return authentication, compatibility, transport, remote-unavailability, and unresolved-delivery conditions as explicit synchronization outcome states rather than manufacturing an accepted result.
get_sync_status: [BEHAVIOR] MUST return the currently observed synchronization or replica state without making any durable-archive acceptance claim.
get_sync_status: [BEHAVIOR] Preserve unknown, unavailable, stale, or insufficient observations explicitly instead of fabricating a default synchronized state.
reconcile_transfer_outcome: [DEPENDENCY_BOUNDARY] MUST delegate read-only reconciliation through the exact supplied SynchronizationService.
publish_registry_catalogue: [DEPENDENCY_BOUNDARY] MUST delegate exact catalogue delivery through the supplied SynchronizationService.
observe_vps_connection: [DEPENDENCY_BOUNDARY] MUST delegate observation through the supplied SynchronizationService.
get_working_set_membership: [DEPENDENCY_BOUNDARY] MUST delegate exact read-only membership through the supplied SynchronizationService.

# durable_archive

accept_transfer_manifest: [BEHAVIOR] Accept a manifest only as one durable archive transition over the exact immutable card revision and supplied source replicas; repeated equivalent acceptance must not create a second logical acceptance.
accept_transfer_manifest: [VALIDATION_ERROR] Represent unsupported, integrity-invalid, conflicting, duplicate-review, incomplete, or quarantine-required evidence as the corresponding classified acceptance outcome instead of partially exposing an accepted manifest set.
accept_transfer_manifest: [PROVENANCE] Preserve acceptance evidence that identifies the exact manifest, card revision, and source evidence used for the decision.
accept_transfer_manifest: [BEHAVIOR] Preserve a valid confirmed Card separately from source completeness: an incomplete source set is quarantined or remains awaiting explicit acceptance, while an accepted IncompleteSourceAcceptance may admit the exact Card revision with truthful awaiting_source status; never represent missing bytes as stored.
verify_durable_acceptance: [BEHAVIOR] Derive the answer only from authoritative local archive evidence for the requested invoice and optional content hash.
verify_durable_acceptance: [BEHAVIOR] Return an explicit not-accepted or not-verifiable outcome when required durable evidence is absent or inconsistent; network delivery evidence is insufficient.
attach_local_source: [BEHAVIOR] Attach verified local source custody to the stable invoice target without rewriting the immutable accepted Invoice Card revision.
attach_local_source: [PROVENANCE] Preserve per-file provenance and verification outcome so repeated identical bytes are distinguishable from silent replacement of a different source.
attach_local_source: [VALIDATION_ERROR] Raise InvoiceNotFoundError when the stable invoice target cannot be resolved and SourceAttachmentRejectedError for unreadable, unsupported, hash-mismatched, wrong-target, or otherwise rejected source input before changing accepted source evidence.
attach_local_source: [RULE_REFERENCE] Accept only configured source media using = rules.source_security.accepted_media_types and enforce the accompanying content-signature, bounded-parsing, metadata-trust, and finite-size-limit requirements in the same source_security policy.
attach_local_source: [CONFIG_REFERENCE] Reject each source file whose byte length exceeds = config.source_upload.max_file_size_bytes before content parsing or persistence; the configured deployment value is not module-owned state.
attach_local_source: [BEHAVIOR] Commit each accepted source identity, verified replica, provenance, and recomputed SourceStatus as one atomic transition; concurrent identical requests have one logical result, conflicting bytes for one source identity cannot both commit, and no check-then-insert path may expose duplicate identity, partial success, or prematurely cleared missing-source state.
accept_incomplete_source_evidence: [SECURITY_BOUNDARY] Require authorization for the exact incomplete-source acceptance operation; possession of an invoice or decision identifier is not authority.
accept_incomplete_source_evidence: [BEHAVIOR] Record immutable auditable evidence for the exact Card revision and exact missing source references, then return awaiting_source status without claiming absent bytes are stored.
accept_incomplete_source_evidence: [VALIDATION_ERROR] Raise InvoiceNotFoundError for an unknown exact accepted revision and SourceAttachmentRejectedError for empty, stale, mismatched, already-complete, or conflicting acceptance evidence before changing normal archive visibility.
record_source_loss: [SECURITY_BOUNDARY] Require authorization for the exact source-loss operation and bind the decision to every affected missing source reference.
record_source_loss: [BEHAVIOR] Append immutable SourceLossDecision evidence and return source_lost status; never delete prior source, Card, acceptance, or loss evidence or mark an available verified source as lost, and allow later verified attachment to restore complete while retaining the decision history.
get_source_status: [BEHAVIOR] Report complete, awaiting_source, and source_lost separately together with available, missing, failed-verification, and active loss-decision evidence.
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

refresh_estimate_snapshot: [BEHAVIOR] MUST create a new immutable estimate snapshot only when the canonical observed estimate content is not already represented by the same stable source identity.
refresh_estimate_snapshot: [PROVENANCE] Preserve enough source identity and observation evidence for later plan/actual calculations to pin the exact estimate snapshot they consumed.
refresh_estimate_snapshot: [VALIDATION_ERROR] Raise EstimateObservationRejectedError when the PresuPro observation lacks stable source identity or contains unsupported or unprocessable content; never accept a partial snapshot.
propose_invoice_line_matches: [DEPENDENCY_BOUNDARY] MUST delegate through the exact supplied PlanActualService; proposals never become decisions implicitly.
record_match_decision: [DEPENDENCY_BOUNDARY] MUST delegate the exact explicit decision through the supplied PlanActualService.
get_unmatched_items: [DEPENDENCY_BOUNDARY] MUST delegate exact unmatched reads through the supplied PlanActualService and never fabricate placeholder items.
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
get_holded_publication_status: [DEPENDENCY_BOUNDARY] MUST delegate exact status reads through the supplied HoldedPublicationService.

# holded_gateway

create_holded_purchase: [ORCHESTRATION] MUST perform the one technical remote create for the supplied already-authorized payload and stable publication-attempt identity, then persist immutable technical outcome evidence.
create_holded_purchase: [SECURITY_BOUNDARY] Keep Holded credentials inside the gateway boundary and redact reusable secret material from logs, returned business objects, and ordinary attempt evidence.
create_holded_purchase: [BEHAVIOR] Preserve credential failure, remote rejection, timeout, malformed response, or ambiguous network outcome as explicit immutable technical attempt evidence rather than retrying the mutation or claiming remote failure/success without proof.
lookup_holded_purchase: [BEHAVIOR] MUST perform read-only recovery lookup using the supplied stable attempt marker and optional document identifier and return observed technical match evidence without mutating Holded.
lookup_holded_purchase: [BEHAVIOR] Preserve zero-match, multi-match, malformed-response, unknown-document, and transport-failure observations explicitly as lookup evidence for publication reconciliation.

# retention_release

evaluate_vps_release: [RULE_REFERENCE] Evaluate release under the manual-release baseline; use = rules.retention_release.mode.
evaluate_vps_release: [RULE_REFERENCE] Require authoritative durable local verification before allowing release; use = rules.retention_release.require_durable_local_verification_before_release.
evaluate_vps_release: [RULE_REFERENCE] Registry status alone must never authorize release; use = rules.retention_release.registry_status_may_trigger_release.
evaluate_vps_release: [BEHAVIOR] Return an allowed evaluation for the exact affected working set and include the evidence identity on which the decision depends without performing physical deletion.
evaluate_vps_release: [VALIDATION_ERROR] Raise VpsReleaseBlockedError when durable replica proof, synchronization observation, working-set identity, or retention evidence is missing, inconsistent, or does not satisfy the accepted release preconditions.
request_manual_vps_release: [BEHAVIOR] Record an explicit release decision only for the exact target covered by a still-applicable allowed evaluation; repeated equivalent requests must be idempotent and return the existing equivalent decision.
request_manual_vps_release: [VALIDATION_ERROR] Raise VpsReleaseBlockedError when the evaluation is stale, mismatched, newly ineligible, or conflicts with the requested target instead of authorizing physical deletion.
get_retention_status: [DEPENDENCY_BOUNDARY] MUST delegate exact decision reads through the supplied RetentionReleaseService.

# deterministic HTTP seams

create_app: [ORCHESTRATION] Construct the application using the already-declared deterministic router wiring and bind the supplied access-control backend into application state without adding business policy.
extract_bearer_credential: [SECURITY_BOUNDARY] MUST extract only the accepted bearer credential from the request boundary without interpreting business authorization.
extract_bearer_credential: [VALIDATION_ERROR] Raise AuthenticationRequiredError when the required bearer authentication material is absent or malformed.
resolve_local_principal: [SECURITY_BOUNDARY] MUST resolve the extracted credential through the access-control backend and return the canonical principal context used by protected handlers.
resolve_local_principal: [VALIDATION_ERROR] Propagate AuthenticationRequiredError when the extracted credential cannot establish a valid local principal.
attach_local_source_handler: [ORCHESTRATION] Own only the multipart transport transformation that cannot be lowered by the deterministic table router, then delegate archive policy to attach_local_source.
attach_local_source_handler: [DEPENDENCY_BOUNDARY] Do not duplicate source-acceptance, authorization, archive, or persistence policy inside the irregular HTTP companion handler.
refresh_estimate_snapshot_handler: [DEPENDENCY_BOUNDARY] MUST obtain the exact PlanActualService bound to request.app.state.plan_actual and pass it to refresh_estimate_snapshot.
calculate_plan_actual_handler: [DEPENDENCY_BOUNDARY] MUST obtain the exact PlanActualService bound to request.app.state.plan_actual and pass it to calculate_plan_actual.
request_holded_publication_handler: [DEPENDENCY_BOUNDARY] MUST obtain the exact HoldedPublicationService bound to request.app.state.holded_publication and pass it to request_holded_publication.
reconcile_holded_publication_handler: [DEPENDENCY_BOUNDARY] MUST obtain the exact HoldedPublicationService bound to request.app.state.holded_publication and pass it to reconcile_holded_publication.
evaluate_vps_release_handler: [DEPENDENCY_BOUNDARY] MUST obtain the exact RetentionReleaseService bound to request.app.state.retention_release and pass it to evaluate_vps_release.
request_manual_vps_release_handler: [DEPENDENCY_BOUNDARY] MUST obtain the exact RetentionReleaseService bound to request.app.state.retention_release and pass it to request_manual_vps_release.

## Concrete adapter implementations
create_holded_gateway_schema: [CONFIG_REFERENCE] MUST idempotently create only the tables named by = config.persistence.holded_attempt_table_name and = config.persistence.holded_lookup_evidence_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresHoldedAttemptRepository.__init__: [SECURITY_BOUNDARY] Bind to the supplied PostgreSQL URL, validate connectivity, treat the URL as secret, and never read environment variables or log credentials.
HttpxHoldedHttpClient.__init__: [VALIDATION_ERROR] Require the verified Holded v1 HTTPS origin, a non-empty API key, and positive finite timeout and response-size bounds according to = rules.holded_transport_backend.
HttpxHoldedHttpClient.__init__: [SECURITY_BOUNDARY] Keep the credential only in the outbound `key` header defined by = rules.holded_transport_backend, enable TLS verification, and never log or return reusable credential material.
create_synchronization_schema: [CONFIG_REFERENCE] MUST idempotently create only the tables named by = config.persistence.synchronization_table_name and = config.persistence.catalogue_publication_table_name and = config.persistence.connection_observation_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresSynchronizationRepository.__init__: [SECURITY_BOUNDARY] Bind to the supplied PostgreSQL URL, validate connectivity, treat the URL as secret, and never read environment variables.
create_plan_actual_schema: [CONFIG_REFERENCE] MUST idempotently create only the tables named by = config.persistence.estimate_snapshot_table_name and = config.persistence.match_proposal_table_name and = config.persistence.estimate_match_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresPlanActualRepository.__init__: [SECURITY_BOUNDARY] Validate the supplied PostgreSQL connection, treat the URL as secret, and read no environment variables.
create_holded_publication_schema: [CONFIG_REFERENCE] MUST idempotently create only the tables named by = config.persistence.holded_publication_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresHoldedPublicationRepository.__init__: [SECURITY_BOUNDARY] Validate the supplied PostgreSQL connection, treat the URL as secret, and read no environment variables.
create_retention_release_schema: [CONFIG_REFERENCE] MUST idempotently create only the evaluation and decision tables named by = config.persistence.retention_evaluation_table_name and = config.persistence.retention_decision_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresRetentionReleaseRepository.__init__: [SECURITY_BOUNDARY] Validate the supplied PostgreSQL connection, protect the URL, and read no environment variables.
HttpxHoldedHttpClient.create_purchase: [FORBIDDEN_ACTION] Issue exactly one POST per invocation with mutation retries and replaying redirects disabled.
HttpxHoldedHttpClient.list_purchases: [BEHAVIOR] Perform the one read-only bounded Holded v1 list request defined by = rules.holded_transport_backend and return typed summaries in stable document-id order.
HttpxHoldedHttpClient.get_purchase: [BEHAVIOR] Perform one read-only request for the exact document identifier and return bounded external evidence.
PostgresHoldedAttemptRepository.begin: [DEPENDENCY_BOUNDARY] Begin one PostgreSQL transaction on the repository connection used for the exact gateway state transition.
PostgresHoldedAttemptRepository.commit: [BEHAVIOR] Commit only a valid typed attempt transition and expose no partial state.
PostgresHoldedAttemptRepository.rollback: [BEHAVIOR] Roll back the current gateway transaction without deleting prior immutable technical evidence.
PostgresHoldedAttemptRepository.lock_attempt: [BEHAVIOR] Acquire the PostgreSQL uniqueness or row lock for the exact publication attempt before deciding whether POST may be issued.
PostgresHoldedAttemptRepository.load_attempt: [BEHAVIOR] Return the exact persisted technical attempt or None without fabricating a default.
PostgresHoldedAttemptRepository.insert_attempt: [PROVENANCE] Append one new technical attempt row for the exact publication_attempt_id inside the active locked transaction; a second row for the same publication_attempt_id or attempt_marker fails on uniqueness and never replaces an existing attempt.
PostgresHoldedAttemptRepository.update_attempt: [PROVENANCE] Write request_started_at, request_finished_at, outcome, document_id, and safe_error_code for the exact existing publication_attempt_id inside the active locked transaction; fail when the row is absent and never insert or change publication_id, invoice_id, invoice_revision_hash, canonical_holded_payload_hash, or attempt_marker.
PostgresHoldedAttemptRepository.insert_lookup_evidence: [PROVENANCE] Append one immutable secret-free lookup observation row keyed by attempt_marker and observed_at inside the active transaction; never update, delete, or settle any attempt or publication state.
PostgresHoldedAttemptRepository.load_attempt_by_marker: [BEHAVIOR] Return the exact attempt for one unique marker or None; reject duplicate persisted markers and never infer an attempt from payload similarity.
PostgresSynchronizationRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact synchronization transition and reject nested begin.
PostgresSynchronizationRepository.commit: [BEHAVIOR] Commit the active typed transition exactly once and expose no partial state.
PostgresSynchronizationRepository.rollback: [FALLBACK] Roll back idempotently, release resources, and preserve the original synchronization failure.
PostgresSynchronizationRepository.lock_synchronization: [BEHAVIOR] Acquire the exact PostgreSQL row or uniqueness lock before deciding whether transport may be issued.
PostgresSynchronizationRepository.insert_synchronization: [PROVENANCE] Append one new synchronization row for the exact synchronization_id inside the active locked transaction; a second row for the same synchronization_id or the same invoice, target node, and idempotency key fails on uniqueness and never replaces an existing attempt.
PostgresSynchronizationRepository.update_synchronization: [PROVENANCE] Write status, started_at, finished_at, and safe_error_code for the exact existing synchronization_id inside the active locked transaction; fail when the row is absent and never insert or change invoice_id, source_node_id, target_node_id, manifest_hash, or idempotency_key.
PostgresSynchronizationRepository.list_synchronizations_for_invoice: [DETERMINISM_OR_ORDERING] Return every persisted synchronization attempt for the exact invoice and target node in stable started_at descending and synchronization_id order; never synthesize a synchronized default.
PostgresSynchronizationRepository.load_synchronization: [BEHAVIOR] Return the exact persisted attempt or None without inferring identity from invoice similarity.
PostgresSynchronizationRepository.load_synchronization_by_idempotency: [BEHAVIOR] Return the exact attempt bound to invoice_id, target_node_id, and idempotency_key or None; more than one persisted row is a storage failure, and identity is never inferred from invoice similarity.
PostgresSynchronizationRepository.insert_catalogue_publication: [PROVENANCE] Append one new catalogue publication row for the exact publication_id inside the active transaction; a second row for the same publication_id or the same catalogue, target node, and idempotency key fails on uniqueness and never replaces an existing publication.
PostgresSynchronizationRepository.load_catalogue_publication_by_idempotency: [BEHAVIOR] Return the exact publication bound to catalogue_id, target_node_id, and idempotency_key or None; more than one persisted row is a storage failure.
PostgresSynchronizationRepository.update_catalogue_publication: [PROVENANCE] Write status, completed_at, acknowledged_at, and safe_error_code for the exact existing publication_id inside the active transaction; fail when the row is absent and never insert or change catalogue_id, source_node_id, target_node_id, idempotency_key, or requested_at.
PostgresSynchronizationRepository.insert_connection_observation: [PROVENANCE] Append one immutable secret-free connection observation row keyed by observed_at inside the active transaction; never update, delete, or change transfer or archive state.
PostgresPlanActualRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact plan/actual transition and reject nested begin.
PostgresPlanActualRepository.commit: [BEHAVIOR] Commit the active typed transition once and expose no partial state.
PostgresPlanActualRepository.rollback: [FALLBACK] Roll back idempotently, release resources, and preserve the original failure.
PostgresPlanActualRepository.lock_estimate: [BEHAVIOR] Serialize immutable snapshot acceptance for the exact PresuPro identity.
PostgresPlanActualRepository.lock_invoice_line: [BEHAVIOR] Serialize match decisions for the exact immutable invoice line before active state is read.
PostgresPlanActualRepository.load_snapshot: [BEHAVIOR] Return the exact immutable snapshot or None and never substitute the latest snapshot.
PostgresPlanActualRepository.load_snapshot_by_content: [BEHAVIOR] Return only the exact PresuPro identity and canonical-content match or None.
PostgresPlanActualRepository.save_snapshot: [PROVENANCE] Append one immutable snapshot and reject conflicting identity or content bindings.
PostgresPlanActualRepository.save_proposals: [PROVENANCE] Append stable non-authoritative proposal evidence without creating confirmed matches.
PostgresPlanActualRepository.load_match_decisions: [DETERMINISM_OR_ORDERING] Return every stored decision whose match_id is in the requested set, in stable match-id order, and omit absent identities without failing; pinned-identity completeness is checked by the service.
PostgresPlanActualRepository.insert_match_decision: [PROVENANCE] Append one new decision row for the exact match_id inside the active locked transaction; a second row for the same match_id fails on uniqueness and never replaces existing history.
PostgresPlanActualRepository.update_match_status: [PROVENANCE] Write status, decided_at, actor, explanation, and invalidation_reason for the exact existing match_id inside the active locked transaction; fail when the row is absent and never insert or change invoice_revision, invoice_line_id, estimate_snapshot_id, or estimate_item_id.
PostgresPlanActualRepository.list_matches_for_line: [DETERMINISM_OR_ORDERING] Return every stored decision bound to the exact invoice revision and invoice_line_id in stable match-id order, including rejected and invalidated history, and never filter by policy.
PostgresPlanActualRepository.list_matches_for_snapshot: [DETERMINISM_OR_ORDERING] Return every decision bound to the exact estimate snapshot with the supplied status in stable match-id order; which status counts as active is decided by the caller.
PostgresHoldedPublicationRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact publication transition and reject nested begin.
PostgresHoldedPublicationRepository.commit: [BEHAVIOR] Commit one valid lifecycle transition and expose no partial state.
PostgresHoldedPublicationRepository.rollback: [FALLBACK] Roll back idempotently and preserve the original publication failure.
PostgresHoldedPublicationRepository.lock_publication: [BEHAVIOR] Serialize the exact logical publication before its state is read.
PostgresHoldedPublicationRepository.lock_invoice_revision: [BEHAVIOR] Serialize duplicate-prevention decisions for the exact immutable revision.
PostgresHoldedPublicationRepository.load_publication: [BEHAVIOR] Return exact persisted state or None and never infer it from gateway evidence.
PostgresHoldedPublicationRepository.load_by_invoice_revision: [BEHAVIOR] Return only the publication bound to the exact invoice revision or None.
PostgresHoldedPublicationRepository.insert_publication: [PROVENANCE] Append one new logical publication row for the exact publication_id and immutable card revision inside the active locked transaction; a second row for the same publication_id or the same card revision and idempotency key fails on uniqueness and never replaces an existing publication.
PostgresHoldedPublicationRepository.update_publication: [PROVENANCE] Write status, external_document_id, completed_at, and safe_outcome_code for the exact existing publication_id inside the active locked transaction; fail when the row is absent and never insert or change card_revision, idempotency_key, or created_at.
PostgresRetentionReleaseRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact release lifecycle and reject nested begin.
PostgresRetentionReleaseRepository.commit: [BEHAVIOR] Commit one valid evidence transition and expose no partial state.
PostgresRetentionReleaseRepository.rollback: [FALLBACK] Roll back idempotently and preserve the original release failure.
PostgresRetentionReleaseRepository.lock_working_set: [BEHAVIOR] Serialize evaluation and decision changes for the exact project and working-set identity.
PostgresRetentionReleaseRepository.save_evaluation: [PROVENANCE] Append immutable complete-coverage or blocked evaluation evidence.
PostgresRetentionReleaseRepository.load_decision: [BEHAVIOR] Return the exact persisted decision or None without inferring physical release.
PostgresRetentionReleaseRepository.insert_decision: [PROVENANCE] Append one immutable decision row for the exact project and working-set target inside the active locked transaction; a second decision for the same target fails on uniqueness and never replaces or updates the stored decision.

create_durable_archive_schema: [CONFIG_REFERENCE] MUST idempotently create only the tables named by = config.persistence.invoice_card_table_name and = config.persistence.invoice_card_revision_table_name and = config.persistence.source_binary_table_name and = config.persistence.source_replica_table_name and = config.persistence.transfer_manifest_table_name and = config.persistence.transfer_receipt_table_name and = config.persistence.byte_publication_table_name and = config.persistence.incomplete_source_acceptance_table_name and = config.persistence.source_loss_decision_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresArchiveUnitOfWork.__init__: [SECURITY_BOUNDARY] MUST treat database_url as secret configuration and MUST NOT log it or include it in safe errors.
PostgresArchiveUnitOfWork.lock_invoice: [BEHAVIOR] MUST acquire PostgreSQL serialization for the exact invoice before mutable acceptance or source state is read.
PostgresArchiveUnitOfWork.insert_publication: [PROVENANCE] MUST append one new ArchiveBytePublication row for the exact publication_id inside the active invoice-locked transaction; a second row for the same publication_id fails on uniqueness and the row is never replaced.
LocalFilesystemSourceByteStore.__init__: [VALIDATION_ERROR] MUST require an absolute private root whose staging and final directories support same-filesystem atomic rename.
LocalFilesystemSourceByteStore.final_reference_for: [PATH_OR_ARTIFACT_POLICY] MUST return the opaque content-addressed final reference for a lowercase hex sha256 digest without touching the filesystem; the layout of that reference is owned by the store and is never composed by callers.
LocalFilesystemSourceByteStore.stage: [PATH_OR_ARTIFACT_POLICY] MUST create a private candidate beneath the configured staging root, flush it, reopen it, and verify exact hash and size before returning an opaque reference.
LocalFilesystemSourceByteStore.stage: [VALIDATION_ERROR] Raise ValueError when publication_id is not a token of [A-Za-z0-9._-], when content length differs from expected_size, or when the sha256 of content differs from expected_hash; the caller treats that as a file-local rejection.
LocalFilesystemSourceByteStore.verify: [SECURITY_BOUNDARY] MUST resolve only store-created opaque references beneath the configured root and reject traversal, symlink escape, devices, and non-regular files.
LocalFilesystemSourceByteStore.publish: [PATH_OR_ARTIFACT_POLICY] MUST use same-filesystem atomic rename to a content-addressed final reference; an existing final file may be reused only after exact verification and different bytes MUST NOT be overwritten.
LocalFilesystemSourceByteStore.remove_staging: [FORBIDDEN_ACTION] MUST remove only the exact staging candidate and MUST NOT remove final or previously published content.
PostgresArchiveUnitOfWork.begin: [BEHAVIOR] MUST open exactly one PostgreSQL transaction for the current service operation and reject nested begin.
PostgresArchiveUnitOfWork.commit: [BEHAVIOR] MUST commit the current transaction exactly once and release its connection; commit without an active transaction is an error.
PostgresArchiveUnitOfWork.rollback: [FALLBACK] MUST rollback the current transaction idempotently and release its connection without hiding the original archive failure.
PostgresArchiveUnitOfWork.load_card_revision: [BEHAVIOR] MUST return only the exact accepted immutable revision selected by invoice_id and content_hash or None; the current revision is resolved by the caller through the StoredInvoiceCard head.
PostgresArchiveUnitOfWork.list_source_replicas: [DETERMINISM_OR_ORDERING] MUST return every replica whose source_id is in the supplied set in stable source_id and stored_at order; an empty set yields an empty result, and the invoice's source ids come from load_source_binaries.
PostgresArchiveUnitOfWork.list_publications_in_states: [DETERMINISM_OR_ORDERING] MUST return every publication whose state is in the supplied set in stable created_at and publication_id order; an empty set yields an empty result; which states count as pending is decided by the caller.
PostgresArchiveUnitOfWork.update_publication_state: [PROVENANCE] MUST write state, updated_at, and failure_code for the exact existing publication_id inside the active transaction; MUST fail when the row is absent and MUST NOT insert or change source_id, invoice_id, content_hash, size_bytes, staging_reference, final_reference, or created_at.
PostgresArchiveUnitOfWork.load_publication: [BEHAVIOR] MUST return the exact ArchiveBytePublication selected by publication_id or None and MUST NOT synthesize a state.
PostgresArchiveUnitOfWork.list_transfer_receipts: [DETERMINISM_OR_ORDERING] MUST return every durable receipt for the exact invoice in stable receipt_at descending and synchronization_id order; selection by manifest hash or accepted content hash belongs to the caller.
PostgresArchiveUnitOfWork.load_source_binaries: [BEHAVIOR] MUST return all source identities for the exact invoice in stable source_id order.
PostgresArchiveUnitOfWork.insert_transfer_manifest: [PROVENANCE] MUST append one immutable manifest row for the exact manifest_id inside the active invoice-locked transaction; duplicates fail on uniqueness.
PostgresArchiveUnitOfWork.insert_card_revision: [PROVENANCE] MUST append one immutable card revision row for the exact invoice_id and content_hash inside the active invoice-locked transaction; duplicates fail on uniqueness and the canonical_card is never rewritten.
PostgresArchiveUnitOfWork.update_card_revision_succession: [PROVENANCE] MUST write superseded_by_content_hash for the exact existing invoice_id and content_hash inside the active transaction; MUST fail when the row is absent and MUST NOT change any other field.
PostgresArchiveUnitOfWork.insert_source_replicas: [PROVENANCE] MUST append every supplied replica row keyed by source_id and node_id inside the active invoice-locked transaction; duplicates fail on uniqueness and no row is replaced.
PostgresArchiveUnitOfWork.insert_transfer_receipt: [PROVENANCE] MUST append one immutable receipt row for the exact synchronization_id inside the active invoice-locked transaction; duplicates fail on uniqueness.
PostgresArchiveUnitOfWork.insert_source_binary: [PROVENANCE] MUST append one source identity row for the exact source_id inside the active invoice-locked transaction; a second row for the same source_id or the same invoice_id and content_hash fails on uniqueness so that conflicting bytes for one identity cannot both commit.
PostgresArchiveUnitOfWork.load_invoice_card: [BEHAVIOR] MUST return the exact StoredInvoiceCard head selected by invoice_id or None and MUST NOT synthesize a card.
PostgresArchiveUnitOfWork.upsert_invoice_card: [PROVENANCE] MUST insert the StoredInvoiceCard head by invoice_id or, when it exists, update only card_version, current_content_hash, current_status, last_received_at, durable_at, and archive_status inside the active invoice-locked transaction; MUST NOT change first_received_at or delete the row.
PostgresArchiveUnitOfWork.insert_incomplete_source_acceptance: [PROVENANCE] MUST append the exact immutable acceptance evidence and MUST NOT replace prior decisions.
PostgresArchiveUnitOfWork.insert_source_loss_decision: [PROVENANCE] MUST append the exact immutable loss evidence and MUST NOT delete source or acceptance history.
create_registry_context_schema: [CONFIG_REFERENCE] MUST idempotently create only the tables named by = config.persistence.work_object_table_name and = config.persistence.assignment_validation_table_name on a connection it opens from database_url and closes; MUST NOT read environment variables or log the URL.
PostgresRegistryContextRepository.__init__: [SECURITY_BOUNDARY] MUST treat database_url as secret configuration, validate connectivity, and MUST NOT log the URL.
PostgresRegistryContextRepository.begin: [DEPENDENCY_BOUNDARY] MUST use one PostgreSQL connection and transaction per service operation and reject nested begin.
PostgresRegistryContextRepository.commit: [BEHAVIOR] MUST commit the active transaction exactly once and release its connection.
PostgresRegistryContextRepository.rollback: [FALLBACK] MUST rollback idempotently and release its connection without hiding the original error.
PostgresRegistryContextRepository.lock_catalogue: [BEHAVIOR] MUST acquire PostgreSQL serialization for one complete Registry catalogue replacement.
PostgresRegistryContextRepository.list_work_objects: [BEHAVIOR] MUST return every committed WorkObject in stable project_id order inside the active transaction and MUST NOT filter, synthesize, or reorder by observation.
PostgresRegistryContextRepository.load_work_object: [BEHAVIOR] MUST return the exact committed WorkObject or None.
PostgresRegistryContextRepository.load_assignment_observation: [BEHAVIOR] MUST return the exact stored CardObjectAssignmentObservation for the invoice_id and content_hash or None and MUST NOT derive one from the card or the catalogue.
PostgresRegistryContextRepository.insert_assignment_observation: [PROVENANCE] MUST append one immutable observation row for the exact observation_id inside the active transaction; a second observation for the same card revision fails on uniqueness.
PostgresRegistryContextRepository.save_assignment_validation: [PROVENANCE] MUST append immutable validation evidence and MUST NOT replace a different decision.
PostgresRegistryContextRepository.load_assignment_validation: [BEHAVIOR] MUST return the exact persisted validation or None.
PostgresRegistryContextRepository.upsert_work_objects: [BEHAVIOR] MUST insert each supplied WorkObject by stable project_id or, when the row exists, update only registry_snapshot_id, last_seen_at, and attention_status from the supplied object inside the active locked transaction; MUST NOT delete rows or change first_seen_at.
