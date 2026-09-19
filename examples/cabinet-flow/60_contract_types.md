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
