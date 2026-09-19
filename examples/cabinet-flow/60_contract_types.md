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
