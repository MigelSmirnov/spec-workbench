# State 1 — Cabinet Web Backend runtime DTO closure

## Model M30 — InvoiceCardLine

Fields: `line_id: str`, `description_original: str`, `description_normalized: str | None`, `classification: str | None`, `quantity: Decimal`, `unit: str`, `unit_price_net: Decimal`, `discount_amount: Decimal`, `net_amount: Decimal`, `tax_rate: Decimal`, `tax_amount: Decimal`, `gross_amount: Decimal`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M106 — CapabilityGrantCommand

Fields: `target_principal_id: str`, `channel: str`, `capability: str`, `entity_scope: EntityScope | None`.

### Identity

value

### Identity evidence

Equal target, channel, exact capability, and scope facts are interchangeable; changing any one of them names a different requested grant.

## Model M107 — CapabilityGrantProvisioningResult

Fields: `target_principal_id: str`, `channel: str`, `capability: str`, `entity_scope: EntityScope | None`, `provisioned_at: datetime`, `created: bool`.

### Identity

value

### Identity evidence

Equal typed provisioning outcomes are interchangeable. `created=False` reports an exact idempotent replay and never a broader pre-existing authority.

## Model M31 — InvoicePayment

Fields: `status: str`, `transactions_json: str`, `paid_total: Decimal`, `outstanding_total: Decimal`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M32 — EstimateSection

Fields: `section_id: str`, `title: str`, `items_json: str`, `net_total: Decimal`, `tax_total: Decimal`, `gross_total: Decimal`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M33 — ShoppingListItem

Fields: `item_id: str`, `estimate_item_id: str`, `description: str`, `planned_quantity: Decimal`, `unit: str`, `unit_price_net: Decimal`, `net_total: Decimal`, `tax_total: Decimal`, `gross_total: Decimal`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M34 — ProjectInvoiceLineMatch

Fields: `invoice_line_id: str`, `estimate_item_id: str | None`, `decision: str`, `reason: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M35 — InvoiceWorkingSetItem

Fields: `invoice_id: str`, `revision: CardRevisionReference`, `manifest_id: str`, `manifest_hash: str`, `required_sources: tuple[SourceContentReference, ...]`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M36 — ArchiveInvoiceCommand

Fields: `invoice_id: str`, `expected_revision: CardRevisionReference`, `authorization: AuthorizationDecision`, `confirmation: ConfirmedEffectAuthorization`, `effect_id: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M37 — AttachInvoiceSourceCommand

Fields: `invoice_id: str`, `expected_revision: CardRevisionReference`, `source: CardSource`, `authorization: AuthorizationDecision`, `effect_id: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M38 — AttachProjectEstimateCommand

Fields: `project_id: str`, `expected_revision: CardRevisionReference`, `estimate: EstimateValidationResult`, `authorization: AuthorizationDecision`, `effect_id: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M39 — AuthenticatedPrincipal

Fields: `principal: CabinetPrincipal`, `actor: ActorReference`, `channel: str`, `authenticated_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M40 — AuthorizationDecision

Fields: `allowed: bool`, `principal_id: str`, `capability: str`, `entity_scope: EntityScope | None`, `decided_at: datetime`, `reason_code: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M41 — BackupRestoreVerificationReport

Fields: `drill_id: str`, `backup_id: str`, `status: str`, `verified_card_revisions: int`, `verified_source_hashes: int`, `started_at: datetime`, `completed_at: datetime | None`, `safe_error_code: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M42 — BackupRestoreVerificationRequest

Fields: `backup_id: str`, `requested_by: ActorReference`, `requested_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M43 — BeginEffectRequest

Fields: `idempotency_key: str`, `operation_kind: str`, `principal_id: str`, `actor: ActorReference`, `target_identity: str | None`, `expected_revision: CardRevisionReference | None`, `request_hash: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M44 — BrowserUploadRequest

Fields: `handoff_id: str`, `handoff_secret: str`, `csrf_token: str`, `display_filename: str | None`, `declared_media_type: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M45 — CanonicalCardRevision

Fields: `reference: CardRevisionReference`, `canonical_json: str`, `created_by: ActorReference`, `created_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M46 — CapabilityResolution

Fields: `capability: str`, `operation_class: str`, `channel: str`, `allowed: bool`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M47 — CardRevisionCommitCommand

Fields: `card_id: str`, `card_type: str`, `expected_content_hash: str | None`, `canonical_json: str`, `validation_issues: tuple[ValidationIssue, ...]`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M48 — CardRevisionCommitResult

Fields: `revision: CardRevisionReference`, `created: bool`, `replayed: bool`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M49 — ChatGptConfirmationRequest

Fields: `proposal_id: str`, `proposal_digest: str`, `effect_id: str`, `target_revision: CardRevisionReference | None`, `capability: str`, `confirmed: bool`, `acknowledged_warning_codes: tuple[str, ...]`, `confirmed_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M50 — ChatGptOutcomeReport

Fields: `interaction_id: str`, `outcome: CompositeOutcome`, `reported_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M51 — ChatGptProposal

Fields: `proposal_id: str`, `proposal_digest: str`, `capability: str`, `target_revision: CardRevisionReference | None`, `normalized_request: str`, `issues: tuple[ValidationIssue, ...]`, `expires_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M52 — ChatGptProposalRequest

Fields: `interaction_id: str`, `capability: str`, `target_revision: CardRevisionReference | None`, `suggested_content: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M53 — ClosedSyncRequest

Fields: `operation: str`, `request_id: str`, `contract_version: str`, `metadata_json: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M54 — ClosedSyncResponse

Fields: `request_id: str`, `operation: str`, `status: str`, `metadata_json: str`, `safe_error_code: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M55 — CompositeOutcome

Fields: `card_status: str`, `card_revision: CardRevisionReference | None`, `source_status: str`, `synchronization_status: str`, `safe_codes: tuple[str, ...]`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M56 — ConfirmInvoiceCommand

Fields: `invoice_id: str`, `expected_revision: CardRevisionReference`, `authorization: AuthorizationDecision`, `confirmation: ConfirmedEffectAuthorization`, `effect_id: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M57 — ConfirmedEffectAuthorization

Fields: `effect_id: str`, `proposal_id: str`, `proposal_digest: str`, `capability: str`, `target_revision: CardRevisionReference | None`, `principal_id: str`, `expires_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M58 — CreateInvoiceDraftCommand

Fields: `draft: InvoiceDraftProposal`, `authorization: AuthorizationDecision`, `effect_id: str`, `idempotency_key: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M59 — CredentialRevocationCommand

Fields: `principal_id: str`, `credential_id: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M60 — CredentialRevocationResult

Fields: `principal_id: str`, `credential_id: str`, `revoked: bool`, `revoked_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M61 — CredentialRotationCommand

Fields: `principal_id: str`, `credential_id: str`, `channel: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M62 — EffectReconciliation

Fields: `effect: CabinetEffect`, `result: EffectResult | None`, `status: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M63 — EffectReservation

Fields: `effect: CabinetEffect`, `replayed: bool`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M64 — EffectResult

Fields: `effect_id: str`, `status: str`, `result_revision: CardRevisionReference | None`, `safe_error_code: str | None`, `completed_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M65 — EntityScope

Fields: `entity_kind: str`, `entity_id: str`, `revision: CardRevisionReference | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M66 — EstimateValidationInput

Fields: `project_id: str`, `expected_project_revision: CardRevisionReference`, `estimate_id: str`, `version: int`, `currency: str`, `canonical_json: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M67 — EstimateValidationResult

Fields: `normalized_estimate: AcceptedEstimateSnapshot | None`, `net_total: Decimal`, `tax_total: Decimal`, `gross_total: Decimal`, `issues: tuple[ValidationIssue, ...]`, `project_revision: CardRevisionReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M68 — InvoiceCardPage

Fields: `items: tuple[InvoiceCardView, ...]`, `next_cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M69 — InvoiceCardView

Fields: `revision: CardRevisionReference`, `invoice: InvoiceCardV1`, `source_status: str`, `synchronization_status: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M70 — InvoiceDraftInput

Fields: `invoice_id: str | None`, `currency: str`, `canonical_json: str`, `source_provenance: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M71 — InvoiceDraftProposal

Fields: `invoice: InvoiceCardV1`, `issues: tuple[ValidationIssue, ...]`, `duplicate_candidates: tuple[InvoiceDuplicateCandidate, ...]`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M72 — InvoiceDuplicateCandidate

Fields: `invoice_revision: CardRevisionReference`, `reason_codes: tuple[str, ...]`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M73 — InvoiceDuplicateCandidateInput

Fields: `invoice_id: str | None`, `invoice_number: str | None`, `supplier_tax_id: str | None`, `issue_date: date | None`, `gross_total: Decimal | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M74 — InvoiceMutationResult

Fields: `effect_id: str`, `revision: CardRevisionReference | None`, `status: str`, `replayed: bool`, `issues: tuple[ValidationIssue, ...]`, `safe_error_code: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M75 — InvoicePackagePullCommand

Fields: `manifest_id: str`, `idempotency_key: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M76 — InvoiceSearchQuery

Fields: `text: str | None`, `status: str | None`, `date_from: date | None`, `date_to: date | None`, `provider_id: str | None`, `limit: int`, `cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M77 — InvoiceTransferReceiptResult

Fields: `issuance: InvoiceTransferIssuance`, `receipt: InvoiceTransferReceipt`, `recorded: bool`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M78 — InvoiceTransferReconciliation

Fields: `issuance: InvoiceTransferIssuance`, `receipt: InvoiceTransferReceipt | None`, `conflict: SynchronizationConflict | None`, `status: str`, `safe_error_code: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M79 — InvoiceTransferReconciliationRequest

Fields: `issuance_id: str`, `manifest_hash: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M80 — InvoiceValidationInput

Fields: `invoice: InvoiceCardV1`, `expected_revision: CardRevisionReference | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M81 — InvoiceValidationResult

Fields: `normalized_invoice: InvoiceCardV1`, `issues: tuple[ValidationIssue, ...]`, `duplicate_candidates: tuple[InvoiceDuplicateCandidate, ...]`, `revision_context: CardRevisionReference | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M82 — InvoiceWorkDiscoveryQuery

Fields: `limit: int`, `cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M83 — InvoiceWorkPage

Fields: `membership: InvoiceWorkingSetMembership`, `next_cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M84 — IssuedPrincipalCredential

Fields: `principal: CabinetPrincipal`, `credential_id: str`, `channel: str`, `secret: str`, `issued_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M85 — PrincipalEnrollmentCommand

Fields: `principal_kind: str`, `channel: str`, `display_label: str | None`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M86 — ProjectCardPage

Fields: `items: tuple[ProjectSummary, ...]`, `next_cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M87 — ProjectListQuery

Fields: `status: str | None`, `client_id: str | None`, `limit: int`, `cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M88 — ProjectMutationResult

Fields: `effect_id: str`, `project_revision: CardRevisionReference | None`, `artifact_id: str | None`, `status: str`, `issues: tuple[ValidationIssue, ...]`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M89 — ProjectSummary

Fields: `project_revision: CardRevisionReference`, `project: ProjectCard`, `estimate: AcceptedEstimateSnapshot | None`, `shopping_lists: tuple[ShoppingListSnapshot, ...]`, `invoice_links: tuple[ProjectInvoiceLink, ...]`, `gap_codes: tuple[str, ...]`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M90 — ProviderCardPage

Fields: `items: tuple[ProviderCard, ...]`, `next_cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M91 — ProviderSearchQuery

Fields: `text: str | None`, `service: str | None`, `area: str | None`, `language: str | None`, `limit: int`, `cursor: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M92 — ReadinessEvaluationRequest

Fields: `include_backup_evidence: bool`, `observed_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M93 — ReadinessReport

Fields: `ready: bool`, `component_statuses: tuple[str, ...]`, `safe_error_codes: tuple[str, ...]`, `observed_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M94 — RecordInvoicePaymentCommand

Fields: `invoice_id: str`, `expected_revision: CardRevisionReference`, `payment_json: str`, `authorization: AuthorizationDecision`, `effect_id: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M95 — RegistryCatalogueView

Fields: `catalogue: RegistryCatalogueSnapshot | None`, `replica: RegistryCatalogueReplica | None`, `freshness: str`, `last_publication_at: datetime | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M96 — SaveShoppingListCommand

Fields: `proposal: ShoppingListProposal`, `authorization: AuthorizationDecision`, `effect_id: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M97 — ShoppingListDerivationRequest

Fields: `project_id: str`, `project_revision: CardRevisionReference`, `estimate_id: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M98 — ShoppingListProposal

Fields: `project_revision: CardRevisionReference`, `estimate: AcceptedEstimateSnapshot`, `items_json: str`, `net_total: Decimal`, `tax_total: Decimal`, `gross_total: Decimal`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M99 — SourceCustodyResult

Fields: `custody: SourceCustodyRecord`, `content: SourceContentReference | None`, `status: str`, `replayed: bool`, `safe_error_code: str | None`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M100 — SourceRetrievalRequest

Fields: `card_id: str`, `source_id: str`, `authorization: AuthorizationDecision`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M101 — SyncCompatibilityRequest

Fields: `node_id: str`, `contract_version: str`, `observed_at: datetime`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M102 — UpdateInvoiceDraftCommand

Fields: `invoice_id: str`, `expected_revision: CardRevisionReference`, `proposal: InvoiceDraftProposal`, `authorization: AuthorizationDecision`, `effect_id: str`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M103 — UploadHandoffCommand

Fields: `card_id: str`, `source_id: str`, `expected_revision: CardRevisionReference`, `authorization: AuthorizationDecision`, `actor: ActorReference`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M104 — VpsWorkingSetReleaseCommand

Fields: `working_set_id: str`, `manifest_id: str`, `invoice_revision: CardRevisionReference`, `required_source_hashes: tuple[str, ...]`, `receipt: InvoiceTransferReceipt`, `durable_evidence_id: str`, `verified_source_hashes: tuple[str, ...]`, `authorization: AuthorizationDecision`, `confirmation: ConfirmedEffectAuthorization`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.

## Model M105 — VpsWorkingSetReleaseResult

Fields: `working_set_id: str`, `released_source_ids: tuple[str, ...]`, `preserved_evidence_ids: tuple[str, ...]`, `status: str`.

### Identity

value

### Identity evidence

Equal typed transport and application facts are interchangeable.
