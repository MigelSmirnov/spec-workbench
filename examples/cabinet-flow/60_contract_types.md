# State 6 — Cabinet Flow contract-only types

## Status

Open. These declarations make State 5 boundaries exact without adding product
behavior or changing any State 1 identity. They exist only where the exact
Python contract needs a transport/configuration/result shape that is not itself
a durable domain model.

---

## `ManifestRevisionRef`

Immutable value returned by `module:installation.manifest_revision`.

Fields:

- `repository_revision: str` — exact immutable repository revision;
- `manifest_root_ref: str` — protected logical manifest-root reference, never a
  host filesystem path.

No credential value, host path or mutable "latest" selector is representable.

---

## `CredentialHandle`

Opaque, non-serializable process-local capability returned by
`module:installation.resolve_credential`.

It has no public data fields. It cannot be persisted, logged, traced, placed in
an error, converted to a response model or passed to a sandbox. Only the
authorized component that requested it may use it for the stated purpose. Its
string/repr form must not reveal credential material.

---

## `ManifestOperationProjection`

Immutable projection of one exact manifest operation.

Fields:

- `operation_ref: ManifestOperationRef`;
- `effect_class: str` — the manifest-owned closed effect class;
- `replay: str` — the manifest-owned closed replay behavior;
- `idempotency_key_fields: tuple[str, ...]`;
- `preconditions: tuple[str, ...]`;
- `purpose: str` — bounded manifest purpose text.

The projection contains no credential and no Cabinet binding/approval policy.

---

## `ManifestOperationChange`

Deterministic comparison of one prior manifest operation with the configured
current manifest revision.

Fields:

- `operation_absent: bool`;
- `material_facts_changed: bool`;
- `digest_changed_with_equivalent_invocation_facts: bool`;
- `changed_fact_names: tuple[str, ...]`.

`changed_fact_names` is restricted to the accepted A10/A23 invocation facts:
`channel`, `effect_class`, `replay`, `idempotency_key` and
`preconditions`. All booleans false means the compared operation is unchanged.

---

## `ManifestChannelEndpoint`

Immutable non-secret endpoint facts for one configured service channel.

Fields:

- `channel: str`;
- `base_address: str`;
- `required_header_names: tuple[str, ...]`;
- `credential_binding_refs: tuple[str, ...]`.

Header values and credential values are forbidden.

---

## `ServiceInstanceProjection`

Immutable manifest projection for the installation-selected instance.

Fields:

- `service_id: str`;
- `instance_id: str`;
- `manifest_record_digest: str`;
- `environment_class: str`;
- `endpoints: tuple[ManifestChannelEndpoint, ...]`.

The projection contains only non-secret routing facts and protected credential
binding references; no resolved credential value is representable.


---

## `ContractVersionIdentity`

Exact identity result for a SlotContractVersion definition.

Fields:

- `contract_version_id: str` — digest over defining contract content;
- `canonicalization_version: str` — the kernel-release serialization version
  used to compute that identity.

The author, issue time and rationale are absent from this result.

---

## `CanonicalField`

Internal closed tree used only by `module:identity` while producing canonical
bytes.

Fields:

- `name: str`;
- `value: str | int | bool | bytes | None | tuple[CanonicalField, ...]`.

Sequences are represented by ordered child fields; mappings are represented by
children already ordered by the record-kind canonicalization rule. Floating
point, arbitrary objects, caller-provided identity values and unordered
containers are not admitted to this internal representation.


---

## `ChannelCredentialHandle`

Opaque listener-established credential material/binding handle used only by the
trusted entrance to resolve an actor. It is non-serializable, never persisted,
and has no public representation that can reveal credential material.

---

## `AuthorizationResult`

One-request authorization result from `module:access_control`.

Fields:

- `actor: ActorRef`;
- `effective_disclosure_ceiling: str`.

The value is not a reusable authority token. It carries no owner-only
permission, approval, admission, proof or business result.

---

## `CompareAndSetExpectation`

Immutable store-level expectation captured when a unit of work begins.

Fields:

- `record_family: str`;
- `record_id: str`;
- `expected_version: str | int | None`.

It is persistence concurrency evidence only and never a domain authorization
decision.

---

## `UnitOfWorkHandle`

Opaque, single-use transaction handle scoped to one calling module, one closed
record-family purpose and one transaction. It cannot be serialized, reused after
commit/rollback, or used to address SQL/table/path details.

---

## `UnitOfWorkCommitResult`

Fields:

- `transaction_id: str`;
- `committed_record_versions: tuple[tuple[str, str | int], ...]`.

The result exists only after an all-or-nothing durable commit.

---

## `UnitOfWorkRollbackResult`

Fields:

- `rolled_back: bool`;
- `already_rolled_back: bool`.

A committed unit of work can never be represented as rolled back.


---

## `BindingAcceptanceResult`

Exact owner-acceptance result for one proposed binding version.

Fields:

- `binding: OperationBinding`;
- `version: OperationBindingVersion`;
- `acceptance_record_ref: str`.

The result names the immutable acceptance evidence; it cannot alter manifest
facts or substitute another version.

---

## `BindingDriftItem`

One deterministic manifest-drift result for an accepted binding version.

Fields:

- `binding_id: str`;
- `binding_version_ref: str`;
- `status: str` — exactly one of the accepted drift outcomes documented by
  State 5;
- `prior_manifest_record_digest: str`;
- `current_manifest_record_digest: str | None`;
- `changed_fact_names: tuple[str, ...]`;
- `replacement_binding_version_ref: str | None`.

A replacement reference is present only for the accepted automatic reissue case.

---

## `BindingDriftReport`

Fields:

- `items: tuple[BindingDriftItem, ...]`.

Items are deterministically ordered by binding identity/version.


---

## `VocabularySeedResult`

Deterministic installation-seed result.

Fields:

- `installed_entry_refs: tuple[str, ...]`;
- `installed_revision_refs: tuple[str, ...]`;
- `already_initialized: bool`.

The lists are deterministically ordered and contain only the release-owned seed
bundle; no external "latest" vocabulary is consulted.

---

## `TermRevisionView`

Exact term-revision lookup result.

Fields:

- `revision: SemanticTermRevision`;
- `term_id: str`;
- `axis_id: str`;
- `term_status: str`;
- `axis_status: str`.

Historical revisions remain representable after either stable entity retires.

---

## `AxisProposalContent`

Complete candidate content for a semantic axis entry or revision.

Fields:

- `axis_id: str | None`;
- `display_name: str`;
- `meaning: str`;
- `value_family: str`;
- `qualifier_contract_ref: str | None`.

A revision identity is never accepted from the caller.

---

## `TermProposalContent`

Complete candidate content for a semantic term entry or revision.

Fields:

- `term_id: str | None`;
- `axis_id: str`;
- `display_name: str`;
- `meaning: str`;
- `value_schema_ref: str`;
- `required_qualifier_kind: str | None`;
- `subject_kind: str | None`;
- `temporal_role: str | None`.

A term-revision identity is never accepted from the caller.

---

## `RelationProposalContent`

Complete candidate content for a semantic relation entry or revision.

Fields:

- `relation_id: str | None`;
- `source_term_revision_ref: str`;
- `target_term_revision_ref: str`;
- `source_schema_ref: str`;
- `target_schema_ref: str`;
- `relation_kind: str`;
- `loss_class: str`;
- `required_slot_ref: str | None`.

A relation-revision identity is never accepted from the caller.

---

## `VocabularyProposalContent`

Closed State 6 union:

`AxisProposalContent | TermProposalContent | RelationProposalContent`.

The variant determines the proposal kind; no separate free-form kind may
contradict the content.

---

## `VocabularyDecisionResult`

Owner decision result for one exact VocabularyProposal.

Fields:

- `proposal: VocabularyProposal`;
- `governed_entry_ref: str | None`;
- `issued_revision_ref: str | None`.

Both references are present only for acceptance. Rejection returns the same
proposal in final rejected state and no governed revision.


---

## `RunFileDescriptor`

Immutable safe description of one live SpooledBytes object.

Fields:

- `spooled_ref: SpooledBytes`;
- `content_digest: str`;
- `size_bytes: int`;
- `observed_media_type: str`;
- `disclosure_class: str`;
- `producer_run_id: str`;
- `producer_node_id: str`;
- `producer_port_id: str`.

No host spool path is representable.

---

## `OwnerStatementRequest`

Closed input to deterministic owner-statement rendering.

Fields:

- `statement_kind: str`;
- `target_refs: tuple[str, ...]`;
- `service_operation_refs: tuple[str, ...]`;
- `effect_classes: tuple[str, ...]`;
- `preview_port_ids: tuple[str, ...]`;
- `motivating_refs: tuple[str, ...]`.

Every reference names already accepted/pinned evidence. Agent-authored prose is
not part of this value.

---

## `OwnerStatement`

Fields:

- `text: str`;
- `digest: str`.

The digest binds the deterministic bounded text to every fact represented by the
corresponding OwnerStatementRequest.

---

## `EffectAuthorization`

Authoritative one-attempt result from `module:owner_authority`.

Fields:

- `status: str` — `authorized`, `approval_required` or `denied`;
- `authority_kind: str | None` — `approval` or `standing_grant` only when
  authorized;
- `authority_ref: str | None`;
- `covered_input_digests: tuple[str, ...]`;
- `reason: str | None`.

An authorized value is scoped to the exact run/node/binding/instance/input set
used to request it and is not reusable for another attempt.


---

## `BoundedByteStream`

Opaque one-pass byte source whose maximum readable length is fixed before use.
It exposes no host path and cannot be rewound into an unbounded buffer.

## `BoundedByteSink`

Opaque bounded destination supplied by an execution/transport boundary. It
accepts bytes only up to its declared ceiling and exposes no arbitrary host
path.

## `BoundedReadLease`

Opaque read-only lease over one already identified byte object. The lease is
bound to one digest and byte length, is non-serializable, and cannot extend the
source object's retention/lifetime.

---

## `RunFileAccess`

Purpose-scoped result of `run_spool.describe_file`.

Fields:

- `descriptor: RunFileDescriptor`;
- `read_lease: BoundedReadLease | None`.

The lease is present only when the caller/purpose is authorized to read those
exact bytes.

---

## `FileDeliveryResult`

Fields:

- `content_digest: str`;
- `delivered_bytes: int`;
- `observed_media_type: str`;
- `complete: bool`.

No destination or spool path is included.

---

## `RunSpoolCleanupResult`

Fields:

- `files_removed: int`;
- `bytes_removed: int`;
- `failures: tuple[str, ...]`.

A non-empty failure list means cleanup was not reported complete.

---

## `StoredValueRead`

Disclosure-aware read result.

Fields:

- `metadata: StoredValue`;
- `content: bytes | BoundedReadLease | None`;
- `content_unavailable_reason: str | None`.

Exactly one of content or an unavailable reason is present. A `byte_stream`
trial fixture is returned only as a bounded read lease.

---

## `DisclosureDerivation`

Fields:

- `disclosure_class: str`;
- `input_value_refs: tuple[str, ...]`.

The class is derived only from the exact execution inputs.

---

## `ValueExpiryResult`

Fields:

- `content_removed: int`;
- `content_retained: int`;
- `failures: tuple[str, ...]`.

Removed bytes are never returned.

---

## `SandboxFileInput`

Validated file input for one sandbox execution.

Fields:

- `port_id: str`;
- `source: SpooledBytes | StoredValue`;
- `content_digest: str`;
- `size_bytes: int`;
- `observed_media_type: str`.

A StoredValue source is permitted only for a trial fixture.

---

## `SandboxCollectedValue`

Fields:

- `port_id: str`;
- `canonical_bytes: bytes`.

The bytes are bounded collection output and are not yet a StoredValue until the
caller performs contract validation.

---

## `SandboxCollectedFile`

Fields:

- `port_id: str`;
- `content_digest: str`;
- `size_bytes: int`;
- `observed_media_type: str`;
- `spooled_ref: SpooledBytes | None`;
- `read_lease: BoundedReadLease | None`.

Real-run file output uses a run-spool reference; trial collection may expose
only the bounded read lease needed by the caller to validate evidence.

---

## `SandboxResourceUsage`

Fields:

- `wall_time_ms: int`;
- `cpu_time_ms: int`;
- `memory_bytes_peak: int`;
- `output_bytes: int`;
- `scratch_bytes_peak: int`;
- `process_count_peak: int`.

These are observed usage facts, never authorization or timeout inputs.

---

## `DeniedAttemptEvidence`

Fields:

- `kind: str`;
- `detail: str | None`.

Detail is bounded and scrubbed; it contains no secret or business value above
the permitted evidence class.

---

## `SandboxExecutionResult`

Fields:

- `outcome: str`;
- `runtime_revision_ref: str`;
- `enforced_bounds: ResourceBounds`;
- `resources_used: SandboxResourceUsage`;
- `denied_attempts: tuple[DeniedAttemptEvidence, ...]`;
- `cleanup_confirmed: bool`;
- `value_outputs: tuple[SandboxCollectedValue, ...]`;
- `file_outputs: tuple[SandboxCollectedFile, ...]`.

A completed result is still untrusted until the caller validates every output
against the exact contract.

---

## `SandboxSupervisorHealth`

Fields:

- `healthy: bool`;
- `supported_runtime_revision_refs: tuple[str, ...]`;
- `reason: str | None`.

An unresolved cleanup leak or unverifiable required runtime is unhealthy.

---

## `TransportMetadataField`

One bounded request metadata field already declared by the accepted
manifest/binding.

Fields:

- `name: str`;
- `value: str`.

It cannot introduce an undeclared header/channel/host selector.

---

## `ObservedHeader`

One response header that the manifest contract explicitly permits to be
reported.

Fields:

- `name: str`;
- `value: str`.

---

## `TransportResult`

Immutable result of one bounded service exchange.

Fields:

- `response_bytes: bytes | None`;
- `response_file: SpooledBytes | None`;
- `observed_status: str | int | None`;
- `observed_headers: tuple[ObservedHeader, ...]`;
- `service_instance_ref: str`;
- `elapsed_ns: int`;
- `request_bytes: int`;
- `response_bytes_count: int`;
- `send_classification: str | None`;
- `failure_reason: str | None`.

At most one response body representation is present. Service timestamps remain
service data and never become KernelInstant.

---

## `OperationAttemptResult`

Immutable conclusion of one exact operation attempt.

Fields:

- `run_id: str`;
- `node_id: str`;
- `map_index: int | None`;
- `attempt_number: int`;
- `binding_version_ref: str`;
- `service_instance_ref: str`;
- `input_digests: tuple[str, ...]`;
- `idempotency_key_digest: str | None`;
- `status: str`;
- `output_value_refs: tuple[str, ...]`;
- `output_file_refs: tuple[SpooledBytes, ...]`;
- `transport: TransportResult | None`;
- `failure_reason: str | None`.

`outcome_unknown` is a first-class status and is never coerced to success or
failure.



---

## `TypedValueDraft`

Strict typed value supplied at an authoring/run surface before it becomes a
StoredValue.

Fields:

- `port_id: str`;
- `semantic_term_revision_ref: str`;
- `value_schema_ref: str`;
- `canonical_bytes: bytes | None`;
- `byte_stream: BoundedByteStream | None`;
- `media_type: str | None`.

Exactly one content representation is present. `byte_stream` is permitted only
for the trial-fixture carriage accepted by the target contract; ordinary flow
inputs are value carriage only.

---

## `TrialCopySkip`

Fields:

- `source_trial_case_ref: str`;
- `reason: str`.

## `TrialCopyReport`

Fields:

- `copied_trial_case_refs: tuple[str, ...]`;
- `skipped: tuple[TrialCopySkip, ...]`.

---

## `ActiveCorpusSnapshot`

Fields:

- `contract_version_ref: str`;
- `active_cases: tuple[TrialCase, ...]`;
- `corpus_digest: str`;
- `withdrawn_cases: tuple[TrialCase, ...]`.

Surface serialization may reduce case contents according to disclosure; the
internal admission/activation form names the exact evidence.

---

## `RunAdvanceResult`

Fields:

- `run: FlowRun`;
- `node_execution_refs: tuple[str, ...]`;
- `output_value_refs: tuple[str, ...]`.

Only evidence appended during the bounded advance pass appears in the two
reference lists.

---

## `RunRecoveryItem`

Fields:

- `run_id: str`;
- `outcome: str`;
- `waiting_reasons: tuple[str, ...]`;
- `unknown_outcome_refs: tuple[str, ...]`;
- `failure_reason: str | None`.

## `RunRecoveryReport`

Fields:

- `items: tuple[RunRecoveryItem, ...]`.

The report never resolves an unknown effect by assumption.

---

## `RunStatusView`

Fields:

- `run_id: str`;
- `status: str`;
- `waiting_on: tuple[str, ...]`;
- `flow_activation_ref: str`;
- `created_at: KernelInstant`;
- `ended_at: KernelInstant | None`;
- `output_value_refs: tuple[str, ...]`;
- `partial: bool`.

Content is fetched separately through disclosure-aware value reads.

---

## `NodeExecutionDraft`

Exact append-only evidence supplied to `trace_journal.record_node_execution`
after the owning execution path has concluded.

Fields:

- `run_id: str`;
- `node_id: str`;
- `map_index: int | None`;
- `attempt_number: int`;
- `executed_ref: str`;
- `runtime_revision_ref: str | None`;
- `enforced_bounds: ResourceBounds | None`;
- `service_instance_ref: str | None`;
- `idempotency_key_digest: str | None`;
- `approval_ref: str | None`;
- `grant_ref: str | None`;
- `input_value_refs: tuple[str, ...]`;
- `output_value_refs: tuple[str, ...]`;
- `input_file_refs: tuple[SpooledBytes, ...]`;
- `output_file_refs: tuple[SpooledBytes, ...]`;
- `input_validation: tuple[str, ...]`;
- `output_validation: tuple[str, ...]`;
- `denied_attempts: tuple[DeniedAttemptEvidence, ...]`;
- `resources_used: SandboxResourceUsage | None`;
- `status: str`;
- `failure_reason: str | None`;
- `failure_detail: str | None`;
- `started_at: KernelInstant`;
- `ended_at: KernelInstant`.

No credential, process log or service free text outside the bounded scrubbed
failure detail is representable.

---

## `RunTracePage`

Fields:

- `executions: tuple[NodeExecution, ...]`;
- `next_page_cursor: str | None`;
- `partial: bool`.

---

## `SlotEvidencePage`

Fields:

- `executions: tuple[NodeExecution, ...]`;
- `trial_execution_refs: tuple[str, ...]`;
- `next_page_cursor: str | None`.

The page is scoped to one exact slot/contract version.

---

## `ImplementationRecordView`

Fields:

- `implementation: Implementation`;
- `code_digest: str`;
- `code_ref: str`;
- `code_bytes: bytes | None`.

Code bytes are present only for the closed `sandbox_execution` purpose.

---

## `SlotAuthoringView`

Fields:

- `slot: Slot`;
- `contract_versions: tuple[SlotContractVersion, ...]`;
- `implementations: tuple[ImplementationRecordView, ...]`;
- `next_page_cursor: str | None`.

Corpus, activation and execution evidence are intentionally absent.

---

## `CompositionView`

Fields:

- `contract_versions: tuple[SlotContractVersion, ...]`;
- `binding_versions: tuple[OperationBindingVersion, ...]`;
- `vocabulary_revision_refs: tuple[str, ...]`;
- `next_page_cursor: str | None`.

Implementation bodies are never present.

---

## `ContractHealthView`

Fields:

- `contract_version_ref: str`;
- `serving_activation: SlotActivation | None`;
- `admission_fresh: bool`;
- `known_failing: bool`;
- `failing_trial_case_refs: tuple[str, ...]`;
- `failing_execution_refs: tuple[str, ...]`.

Stale admission without failure evidence is represented by
`admission_fresh = false` and `known_failing = false`.

---

## `WaitingForOwnerPage`

Fields:

- `pending_approvals: tuple[EffectApproval, ...]`;
- `active_grants: tuple[StandingGrant, ...]`;
- `grant_execution_counts: tuple[tuple[str, int], ...]`;
- `next_page_cursor: str | None`.

Only the active owner may receive this page.


---

## `CompositionFilter`

Bounded exact-reference filter for the authoring composition view.

Fields:

- `slot_refs: tuple[str, ...]`;
- `binding_refs: tuple[str, ...]`;
- `semantic_term_revision_refs: tuple[str, ...]`;
- `effect_classes: tuple[str, ...]`.

Empty tuples mean no restriction for that dimension; arbitrary query languages
are not accepted.

---

## `WaitingForOwnerFilter`

Bounded exact-reference filter.

Fields:

- `run_refs: tuple[str, ...]`;
- `flow_version_refs: tuple[str, ...]`;
- `service_instance_refs: tuple[str, ...]`.

No free-form query or store selector is accepted.

---

## `InspectRequest`

Fields:

- `inspection_kind: str`;
- `resource_ref: str | None`;
- `query_refs: tuple[str, ...]`;
- `page_cursor: str | None`;
- `page_size: int | None`.

The inspection kind belongs to the release-fixed catalogue.

## `SurfaceViewItem`

Closed State 6 union of the views/records that `inspect` may return:

`SemanticAxis | SemanticAxisRevision | SemanticTerm | SemanticTermRevision |
SemanticRelation | SemanticRelationRevision | Slot | SlotContractVersion |
ImplementationRecordView | TrialCase | ActiveCorpusSnapshot |
OperationBinding | OperationBindingVersion | Flow | FlowVersion | FlowProof |
FlowActivation | FlowRun | RunStatusView | RunTracePage | SlotEvidencePage |
StoredValueRead | CompositionView | ContractHealthView`.

## `InspectResult`

Fields:

- `inspection_kind: str`;
- `items: tuple[SurfaceViewItem, ...]`;
- `next_page_cursor: str | None`.

---

## `SlotDraft`

Fields: `name: str`, `purpose: str`.

## `ContractVersionDraft`

Fields:

- `slot_id: str`;
- `input_ports: tuple[SemanticPort, ...]`;
- `output_ports: tuple[SemanticPort, ...]`;
- `resource_bounds: ResourceBounds`;
- `runtime_revision: SandboxRuntimeRevision`.

## `ImplementationDraft`

Fields:

- `contract_version_ref: str`;
- `entry_point: str`;
- `code_bytes: bytes`;
- `rationale: str`;
- `motivating_trace_refs: tuple[str, ...]`.

## `TrialCaseDraft`

Fields:

- `contract_version_ref: str`;
- `inputs: tuple[TypedValueDraft, ...]`;
- `expected_outputs: tuple[TypedValueDraft, ...] | None`.

## `BindingProposalDraft`

Fields:

- `operation_ref: ManifestOperationRef`;
- `input_ports: tuple[SemanticPort, ...]`;
- `output_ports: tuple[SemanticPort, ...]`;
- `purpose: str`;
- `preview_ports: tuple[str, ...]`;
- `outcome_read_binding_ref: str | None`.

## `FlowDraft`

Fields: `name: str`, `purpose: str`.

## `FlowVersionDraft`

Fields:

- `flow_id: str`;
- `flow_inputs: tuple[SemanticPort, ...]`;
- `flow_outputs: tuple[SemanticPort, ...]`;
- `nodes: tuple[FlowNode, ...]`;
- `edges: tuple[FlowEdge, ...]`;
- `constants: tuple[FlowConstant, ...]`.

## `VocabularyProposalDraft`

Fields:

- `content: VocabularyProposalContent`;
- `motivating_refs: tuple[str, ...]`;
- `agent_rationale: str | None`.

## `AuthorPayload`

Closed union:

`SlotDraft | ContractVersionDraft | ImplementationDraft | TrialCaseDraft |
BindingProposalDraft | FlowDraft | FlowVersionDraft | VocabularyProposalDraft`.

## `AuthorRequest`

Fields:

- `command: str`;
- `payload: AuthorPayload`.

The command is release-fixed and must match the concrete payload variant.
Caller-supplied content identities are not representable in these drafts.

## `AuthorResult`

Fields:

- `record_kind: str`;
- `record_ref: str`.

---

## `TrialRequest`

Fields:

- `contract_version_ref: str`;
- `implementation_ref: str`.

## `ActivationRequest`

Fields:

- `activation_kind: str`;
- `contract_version_ref: str | None`;
- `implementation_ref: str | None`;
- `flow_id: str | None`;
- `flow_version_ref: str | None`;
- `proof_ref: str | None`;
- `expected_current_activation_ref: str | None`;
- `reason: str | None`.

The activation kind fixes which reference set is valid; mixed slot/flow targets
are refused.

## `ActivationResult`

Fields:

- `activation: SlotActivation | FlowActivation`;
- `current_activation_ref: str`.

## `RunFlowRequest`

Fields:

- `flow_ref: str`;
- `inputs: tuple[TypedValueDraft, ...]`.

## `RunFlowResult`

Fields:

- `run: FlowRun`;
- `status: RunStatusView`.

## `OwnerDecisionRequest`

Fields:

- `decision_kind: str`;
- `target_ref: str`;
- `secondary_ref: str | None`;
- `expected_status: str | None`;
- `expected_revision_ref: str | None`;
- `decision: str`;
- `reason: str | None`;
- `owner_statement_digest: str | None`.

The decision kind is release-fixed and determines which target/reference/status
fields are legal. Agent prose never substitutes for the kernel statement.

## `OwnerDecisionResult`

Fields:

- `record_kind: str`;
- `decision_record_ref: str`;
- `resulting_state_ref: str`.

---

## `SurfaceRequest`

Closed union:

`InspectRequest | AuthorRequest | TrialRequest | ActivationRequest |
RunFlowRequest | OwnerDecisionRequest`.

## `SurfaceResponse`

Closed union:

`InspectResult | AuthorResult | AdmissionVerdict | ActivationResult |
RunFlowResult | OwnerDecisionResult`.

---

## `HttpRequestContext`

Fields:

- `request_id: str`;
- `credential: ChannelCredentialHandle`;
- `body_size: int`.

No caller-selected module/path target is represented after fixed-route parsing.

## `HttpRequestEnvelope`

Fields:

- `context: HttpRequestContext`;
- `operation: str`;
- `payload: SurfaceRequest`.

## `HttpResponseEnvelope`

Fields:

- `status_code: int`;
- `result: SurfaceResponse | None`;
- `error_code: str | None`;
- `error_message: str | None`.

Error text is bounded and sanitized.

---

## `McpRequestEnvelope`

Fields:

- `request_id: str`;
- `credential: ChannelCredentialHandle`;
- `operation: str`;
- `payload: SurfaceRequest`.

## `McpResponseEnvelope`

Fields:

- `request_id: str`;
- `result: SurfaceResponse | None`;
- `error_code: str | None`;
- `error_message: str | None`.

---

## `KernelReadiness`

Fields:

- `manifest_revision: ManifestRevisionRef`;
- `store_ready: bool`;
- `sandbox_ready: bool`;
- `binding_sweep_ready: bool`;
- `runs_resumed: bool`;
- `mcp_ready: bool`;
- `http_ready: bool`;
- `ready: bool`;
- `failures: tuple[str, ...]`.

No credential value or host path is present.
