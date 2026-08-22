# State 7 — Cabinet Backend generation notes

# access_control

authorize_operation: [SECURITY_BOUNDARY] MUST evaluate authorization only for the exact operation supplied by the caller and return the decision without performing the protected business operation.
authorize_operation: [VALIDATION_ERROR] Raise AuthenticationRequiredError when no valid authenticated principal exists and OperationForbiddenError when the authenticated principal lacks authority for the exact requested operation; possession of an entity identifier is never authority.
AccessControlBackend.authenticate: [SECURITY_BOUNDARY] Resolve the supplied local credential to one canonical authenticated principal context and do not expose reusable credential material in the returned context.
AccessControlBackend.authenticate: [VALIDATION_ERROR] Raise AuthenticationRequiredError when the supplied credential cannot establish a valid active local principal.
AccessControlBackend.authorize: [SECURITY_BOUNDARY] Evaluate the principal against the exact operation and current access-control state; keep local service authority distinct from synchronization-node identity.
AccessControlBackend.authorize: [VALIDATION_ERROR] Raise OperationForbiddenError when the authenticated principal is not authorized for the exact requested operation.
PostgresAccessControlBackend.__init__: [SECURITY_BOUNDARY] Bind the concrete backend to the configured PostgreSQL database and credential pepper; fail construction when either input is empty and never log the pepper or database credentials.
PostgresAccessControlBackend.authenticate: [RULE_REFERENCE] Begin progressive delay at = rules.access_control.progressive_delay_after_failures and temporary blocking at = rules.access_control.temporary_block_after_failures.
PostgresAccessControlBackend.authenticate: [RULE_REFERENCE] Keep temporary refusal active for = rules.access_control.temporary_block_seconds and verify credentials using = rules.access_control.credential_hash_algorithm.
PostgresAccessControlBackend.authenticate: [SECURITY_BOUNDARY] Verify the presented bearer secret against one active stored credential, require its principal to remain active, and return a context containing identifiers but no reusable secret.
PostgresAccessControlBackend.authenticate: [VALIDATION_ERROR] Reject malformed, unknown, revoked, delayed, or temporarily blocked credentials with AuthenticationRequiredError before protected state changes.
PostgresAccessControlBackend.authenticate: [BEHAVIOR] Update throttle state and append secret-free security evidence atomically with each authentication outcome; successful authentication resets the active consecutive-failure counter without deleting audit history.
PostgresAccessControlBackend.authorize: [SECURITY_BOUNDARY] Reread current principal and credential state and allow only an exact operation present in the stored capability set; stale context, localhost origin, client name, prompt, or entity identifier is not authority.
PostgresAccessControlBackend.authorize: [VALIDATION_ERROR] Raise AuthenticationRequiredError for a stale or revoked context and OperationForbiddenError for an active principal lacking the exact capability; append refusal evidence without performing the protected operation.
PostgresAccessControlBackend.authorize: [FIELD_ASSIGNMENT] Populate AuthorizationDecision from the exact principal, operation, outcome, timestamp, reason code, and persisted SecurityAuditRecord evidence_id; never fabricate evidence identifiers.
PostgresAccessControlBackend.enroll_local_service: [BEHAVIOR] Generate a cryptographically random bearer secret, persist only its Argon2id verifier, commit principal, credential, and audit records atomically, and return the plaintext exactly once in IssuedServiceCredential.
PostgresAccessControlBackend.rotate_local_service_credential: [BEHAVIOR] Atomically create one replacement credential and revoke every prior active credential for the exact principal while preserving its identity and capabilities; return the new plaintext secret once and never log it.
PostgresAccessControlBackend.revoke_local_service_principal: [BEHAVIOR] Atomically perform terminal principal revocation, revoke all active credentials, and append evidence; never delete security history.
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
PostgresHoldedAttemptRepository.__init__: [SECURITY_BOUNDARY] Bind to the supplied PostgreSQL URL, validate connectivity, treat the URL as secret, and never read environment variables or log credentials.
HttpxHoldedHttpClient.__init__: [VALIDATION_ERROR] Require the verified Holded v1 HTTPS origin, a non-empty API key, and positive finite timeout and response-size bounds according to = rules.holded_transport_backend.
HttpxHoldedHttpClient.__init__: [SECURITY_BOUNDARY] Keep the credential only in the outbound `key` header defined by = rules.holded_transport_backend, enable TLS verification, and never log or return reusable credential material.
PostgresSynchronizationRepository.__init__: [SECURITY_BOUNDARY] Bind to the supplied PostgreSQL URL, validate connectivity, treat the URL as secret, and never read environment variables.
HttpxVpsSynchronizationTransport.__init__: [VALIDATION_ERROR] Require HTTPS without embedded credentials or fragment, a non-empty dedicated node credential, and positive finite bounds.
HttpxVpsSynchronizationTransport.__init__: [SECURITY_BOUNDARY] Verify TLS and never log or return credentials, authorization headers, or unbounded response bodies.
PostgresPlanActualRepository.__init__: [SECURITY_BOUNDARY] Validate the supplied PostgreSQL connection, treat the URL as secret, and read no environment variables.
PostgresHoldedPublicationRepository.__init__: [SECURITY_BOUNDARY] Validate the supplied PostgreSQL connection, treat the URL as secret, and read no environment variables.
PostgresRetentionReleaseRepository.__init__: [SECURITY_BOUNDARY] Validate the supplied PostgreSQL connection, protect the URL, and read no environment variables.
HttpxHoldedHttpClient.create_purchase: [FORBIDDEN_ACTION] Issue exactly one POST per invocation with mutation retries and replaying redirects disabled.
HttpxHoldedHttpClient.list_purchases: [BEHAVIOR] Perform the one read-only bounded Holded v1 list request defined by = rules.holded_transport_backend and return typed summaries in stable document-id order.
HttpxHoldedHttpClient.get_purchase: [BEHAVIOR] Perform one read-only request for the exact document identifier and return bounded external evidence.
PostgresHoldedAttemptRepository.begin: [DEPENDENCY_BOUNDARY] Begin one PostgreSQL transaction on the repository connection used for the exact gateway state transition.
PostgresHoldedAttemptRepository.commit: [BEHAVIOR] Commit only a valid typed attempt transition and expose no partial state.
PostgresHoldedAttemptRepository.rollback: [BEHAVIOR] Roll back the current gateway transaction without deleting prior immutable technical evidence.
PostgresHoldedAttemptRepository.lock_attempt: [BEHAVIOR] Acquire the PostgreSQL uniqueness or row lock for the exact publication attempt before deciding whether POST may be issued.
PostgresHoldedAttemptRepository.load_attempt: [BEHAVIOR] Return the exact persisted technical attempt or None without fabricating a default.
PostgresHoldedAttemptRepository.reserve_attempt: [BEHAVIOR] Reuse an existing reservation only when attempt identity, payload hash, and marker are exactly equivalent; reject conflicts.
PostgresHoldedAttemptRepository.mark_request_issued: [BEHAVIOR] Persist the single-create authority transition before network mutation and reject repeated or skipped issuance.
PostgresHoldedAttemptRepository.append_attempt_outcome: [BEHAVIOR] Append immutable secret-free technical outcome evidence and reject stale or conflicting transitions.
PostgresHoldedAttemptRepository.append_lookup_evidence: [BEHAVIOR] Resolve the exact durable attempt by its unique marker and append immutable read-only recovery evidence without settling Cabinet publication.
PostgresHoldedAttemptRepository.load_attempt_by_marker: [BEHAVIOR] Return the exact attempt for one unique marker or None; reject duplicate persisted markers and never infer an attempt from payload similarity.
PostgresSynchronizationRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact synchronization transition and reject nested begin.
PostgresSynchronizationRepository.commit: [BEHAVIOR] Commit the active typed transition exactly once and expose no partial state.
PostgresSynchronizationRepository.rollback: [FALLBACK] Roll back idempotently, release resources, and preserve the original synchronization failure.
PostgresSynchronizationRepository.lock_synchronization: [BEHAVIOR] Acquire the exact PostgreSQL row or uniqueness lock before deciding whether transport may be issued.
PostgresSynchronizationRepository.reserve_synchronization: [BEHAVIOR] Reuse only an exactly equivalent identity, idempotency-key, and manifest-hash binding; reject conflicts before transport.
PostgresSynchronizationRepository.mark_transfer_issued: [BEHAVIOR] Persist issuance before network mutation and reject repeated or skipped issuance.
PostgresSynchronizationRepository.save_synchronization_outcome: [PROVENANCE] Persist typed conclusive or unknown evidence without deleting prior observations.
PostgresSynchronizationRepository.load_sync_status: [BEHAVIOR] Return the exact committed observation or None and never synthesize a synchronized default.
PostgresSynchronizationRepository.load_synchronization: [BEHAVIOR] Return the exact persisted attempt or None without inferring identity from invoice similarity.
PostgresSynchronizationRepository.reserve_catalogue_publication: [BEHAVIOR] Reuse only an exact catalogue, endpoint, and idempotency binding and reject conflicts before publication.
PostgresSynchronizationRepository.save_catalogue_acknowledgement: [PROVENANCE] Append the exact typed acknowledgement and reject stale or conflicting publication transitions.
PostgresSynchronizationRepository.append_connection_observation: [PROVENANCE] Append secret-free typed connection evidence without changing transfer or archive state.
HttpxVpsSynchronizationTransport.transfer_invoice: [FORBIDDEN_ACTION] Issue at most one service-authorized outbound transfer with transport retries and replaying redirects disabled.
HttpxVpsSynchronizationTransport.reconcile_transfer: [BEHAVIOR] Perform one bounded read-only lookup for the exact persisted synchronization identity.
HttpxVpsSynchronizationTransport.publish_catalogue: [FORBIDDEN_ACTION] Issue at most one service-authorized publication for the exact delivery with replaying redirects and mutation retries disabled.
HttpxVpsSynchronizationTransport.observe_connection: [BEHAVIOR] Perform one bounded read-only authenticated observation and preserve unavailable or incompatible evidence explicitly.
PostgresPlanActualRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact plan/actual transition and reject nested begin.
PostgresPlanActualRepository.commit: [BEHAVIOR] Commit the active typed transition once and expose no partial state.
PostgresPlanActualRepository.rollback: [FALLBACK] Roll back idempotently, release resources, and preserve the original failure.
PostgresPlanActualRepository.lock_estimate: [BEHAVIOR] Serialize immutable snapshot acceptance for the exact PresuPro identity.
PostgresPlanActualRepository.lock_invoice_line: [BEHAVIOR] Serialize match decisions for the exact immutable invoice line before active state is read.
PostgresPlanActualRepository.load_snapshot: [BEHAVIOR] Return the exact immutable snapshot or None and never substitute the latest snapshot.
PostgresPlanActualRepository.load_snapshot_by_content: [BEHAVIOR] Return only the exact PresuPro identity and canonical-content match or None.
PostgresPlanActualRepository.save_snapshot: [PROVENANCE] Append one immutable snapshot and reject conflicting identity or content bindings.
PostgresPlanActualRepository.save_proposals: [PROVENANCE] Append stable non-authoritative proposal evidence without creating confirmed matches.
PostgresPlanActualRepository.load_match_decisions: [DETERMINISM_OR_ORDERING] Return every exact requested decision in match-id order and fail when a pinned identity is absent.
PostgresPlanActualRepository.save_match_decision: [PROVENANCE] Append confirmed, rejected, or invalidated decision history and reject conflicting active confirmation.
PostgresPlanActualRepository.list_active_matches: [DETERMINISM_OR_ORDERING] Return only active confirmed matches for the exact project and snapshot in stable match-id order.
PostgresHoldedPublicationRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact publication transition and reject nested begin.
PostgresHoldedPublicationRepository.commit: [BEHAVIOR] Commit one valid lifecycle transition and expose no partial state.
PostgresHoldedPublicationRepository.rollback: [FALLBACK] Roll back idempotently and preserve the original publication failure.
PostgresHoldedPublicationRepository.lock_publication: [BEHAVIOR] Serialize the exact logical publication before its state is read.
PostgresHoldedPublicationRepository.lock_invoice_revision: [BEHAVIOR] Serialize duplicate-prevention decisions for the exact immutable revision.
PostgresHoldedPublicationRepository.load_publication: [BEHAVIOR] Return exact persisted state or None and never infer it from gateway evidence.
PostgresHoldedPublicationRepository.load_by_invoice_revision: [BEHAVIOR] Return only the publication bound to the exact invoice revision or None.
PostgresHoldedPublicationRepository.reserve_publication: [BEHAVIOR] Reuse only an equivalent logical publication and reject conflicting active state before gateway mutation.
PostgresHoldedPublicationRepository.save_transition: [PROVENANCE] Append valid verified or unresolved lifecycle evidence and reject stale, skipped, or conflicting transitions.
PostgresRetentionReleaseRepository.begin: [DEPENDENCY_BOUNDARY] Open one PostgreSQL transaction for the exact release lifecycle and reject nested begin.
PostgresRetentionReleaseRepository.commit: [BEHAVIOR] Commit one valid evidence transition and expose no partial state.
PostgresRetentionReleaseRepository.rollback: [FALLBACK] Roll back idempotently and preserve the original release failure.
PostgresRetentionReleaseRepository.lock_working_set: [BEHAVIOR] Serialize evaluation and decision changes for the exact project and working-set identity.
PostgresRetentionReleaseRepository.save_evaluation: [PROVENANCE] Append immutable complete-coverage or blocked evaluation evidence.
PostgresRetentionReleaseRepository.load_decision: [BEHAVIOR] Return the exact persisted decision or None without inferring physical release.
PostgresRetentionReleaseRepository.reserve_decision: [BEHAVIOR] Reuse only an equivalent still-valid authorization and reject stale, broadened, or conflicting decisions.

PostgresArchiveUnitOfWork.__init__: [SECURITY_BOUNDARY] MUST treat database_url as secret configuration and MUST NOT log it or include it in safe errors.
PostgresArchiveUnitOfWork.lock_invoice: [BEHAVIOR] MUST acquire PostgreSQL serialization for the exact invoice before mutable acceptance or source state is read.
PostgresArchiveUnitOfWork.save_publication: [BEHAVIOR] MUST persist the publication journal in the same transaction as its associated archive mutation and reject skipped, stale, or conflicting publication-state transitions.
LocalFilesystemSourceByteStore.__init__: [VALIDATION_ERROR] MUST require an absolute private root whose staging and final directories support same-filesystem atomic rename.
LocalFilesystemSourceByteStore.stage: [PATH_OR_ARTIFACT_POLICY] MUST create a private candidate beneath the configured staging root, flush it, reopen it, and verify exact hash and size before returning an opaque reference.
LocalFilesystemSourceByteStore.verify: [SECURITY_BOUNDARY] MUST resolve only store-created opaque references beneath the configured root and reject traversal, symlink escape, devices, and non-regular files.
LocalFilesystemSourceByteStore.publish: [PATH_OR_ARTIFACT_POLICY] MUST use same-filesystem atomic rename to a content-addressed final reference; an existing final file may be reused only after exact verification and different bytes MUST NOT be overwritten.
LocalFilesystemSourceByteStore.remove_staging: [FORBIDDEN_ACTION] MUST remove only the exact staging candidate and MUST NOT remove final or previously published content.
PostgresArchiveUnitOfWork.begin: [BEHAVIOR] MUST open exactly one PostgreSQL transaction for the current service operation and reject nested begin.
PostgresArchiveUnitOfWork.commit: [BEHAVIOR] MUST commit the current transaction exactly once and release its connection; commit without an active transaction is an error.
PostgresArchiveUnitOfWork.rollback: [FALLBACK] MUST rollback the current transaction idempotently and release its connection without hiding the original archive failure.
PostgresArchiveUnitOfWork.load_card_revision: [BEHAVIOR] MUST return only the exact accepted immutable revision selected by invoice_id and optional content_hash.
PostgresArchiveUnitOfWork.load_source_replicas: [BEHAVIOR] MUST return replicas for the exact invoice in stable source_id and stored_at order.
PostgresArchiveUnitOfWork.load_pending_publications: [BEHAVIOR] MUST return only staged or metadata_committed publication records in stable created_at and publication_id order.
PostgresArchiveUnitOfWork.mark_publication_published: [BEHAVIOR] MUST permit only metadata_committed to published after final-byte verification and MUST reject stale or skipped transitions.
PostgresArchiveUnitOfWork.mark_publication_failed: [BEHAVIOR] MUST preserve failure evidence and reject transition from published to failed.
PostgresArchiveUnitOfWork.load_transfer_receipt: [BEHAVIOR] MUST return only the exact durable receipt for invoice_id and optional content_hash.
PostgresArchiveUnitOfWork.load_source_binaries: [BEHAVIOR] MUST return all source identities for the exact invoice in stable source_id order.
PostgresArchiveUnitOfWork.save_transfer_acceptance: [BEHAVIOR] MUST persist manifest, immutable card revision, replicas, and receipt as one transaction and MUST NOT expose partial acceptance.
PostgresArchiveUnitOfWork.save_source_attachment: [BEHAVIOR] MUST persist source identity, replica metadata, and ArchiveBytePublication in the active invoice-locked transaction.
PostgresArchiveUnitOfWork.save_incomplete_source_acceptance: [PROVENANCE] MUST append the exact immutable acceptance evidence and MUST NOT replace prior decisions.
PostgresArchiveUnitOfWork.save_source_loss_decision: [PROVENANCE] MUST append the exact immutable loss evidence and MUST NOT delete source or acceptance history.
PostgresRegistryContextRepository.__init__: [SECURITY_BOUNDARY] MUST treat database_url as secret configuration, validate connectivity, and MUST NOT log the URL.
PostgresRegistryContextRepository.begin: [DEPENDENCY_BOUNDARY] MUST use one PostgreSQL connection and transaction per service operation and reject nested begin.
PostgresRegistryContextRepository.commit: [BEHAVIOR] MUST commit the active transaction exactly once and release its connection.
PostgresRegistryContextRepository.rollback: [FALLBACK] MUST rollback idempotently and release its connection without hiding the original error.
PostgresRegistryContextRepository.lock_catalogue: [BEHAVIOR] MUST acquire PostgreSQL serialization for one complete Registry catalogue replacement.
PostgresRegistryContextRepository.load_work_object: [BEHAVIOR] MUST return the exact committed WorkObject or None.
PostgresRegistryContextRepository.save_assignment_validation: [PROVENANCE] MUST append immutable validation evidence and MUST NOT replace a different decision.
PostgresRegistryContextRepository.load_assignment_validation: [BEHAVIOR] MUST return the exact persisted validation or None.
PostgresRegistryContextRepository.merge_work_objects: [BEHAVIOR] MUST atomically merge the typed projection by stable project_id, preserve Cabinet-owned fields and absent existing objects, and MUST NOT expose mixed catalogue observations.
