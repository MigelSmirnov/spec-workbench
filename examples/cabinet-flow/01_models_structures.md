# State 1 — Cabinet Flow embedded value structures

## Status

Added on 20 September 2026 while closing the model surface. Every model here
already existed in M01–M49 as a sentence — "each naming the node, port or edge",
"names and exact versions", "one value per port" — without a name or a field. A
sentence cannot be typed, stored or checked, so each becomes a value model.
None of them adds behaviour, a lifecycle or a durable identity.

## Model M50 — PostalAddress

### Meaning

One structured postal address used as the place facts of a PlaceValue M09.

Candidate fields:

- `address_lines: tuple[str, ...]`;
- `locality: str`;
- `region: str | None`;
- `postal_code: str | None`;
- `country_code: str`;

`country_code` is the two-letter ISO 3166-1 code. The address is carried as written by its source; the kernel never geocodes, normalizes or completes it.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M51 — FlowEndpoint

### Meaning

One end of a FlowEdge M34: where a value leaves or where it arrives.

Candidate fields:

- `endpoint_kind: str`;
- `node_id: str | None`;
- `port_id: str | None`;
- `constant_id: str | None`;

`endpoint_kind` is `flow_input`, `constant`, `node_output`, `node_input` or `flow_output`. A source is a `flow_input`, a `constant` or a `node_output`; a target is a `node_input` or a `flow_output`. `node_id` is present exactly for the two node kinds, `constant_id` exactly for `constant`, and `port_id` for every kind except `constant`.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M52 — CompositionBasis

### Meaning

Why the two ends of a FlowEdge M34 may be connected.

Candidate fields:

- `basis_kind: str`;
- `semantic_term_revision_ref: str | None`;
- `relation_revision_ref: str | None`;

`basis_kind` is `same_term` or `relation`. `same_term` carries the shared semantic-term revision and no relation; `relation` carries the exact SemanticRelationRevision M07 reference and no term. The relation is referenced, never embedded: an accepted revision is immutable.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M53 — FlowGuard

### Meaning

The condition under which a FlowEdge M34 is enabled.

Candidate fields:

- `guard_port_id: str`;
- `enabling_value: str`;

`guard_port_id` names one output port of the edge's source node whose value schema is a closed set; `enabling_value` is the one member of that set that enables the edge.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M54 — ProofFinding

### Meaning

One finding of a FlowProof M36 and the place in the graph it concerns.

Candidate fields:

- `finding_code: str`;
- `node_id: str | None`;
- `port_id: str | None`;
- `edge_index: int | None`;

`finding_code` is one member of the closed finding set of M36. `edge_index` is the position of the edge in the canonical edge order of the proven flow version, because an edge has no identifier of its own. At least one of the three locations is present.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M55 — RunWait

### Meaning

One node a FlowRun M40 is stopped at, and why.

Candidate fields:

- `node_id: str`;
- `reason: str`;
- `retry_ordinal: int | None`;
- `retry_not_before: KernelInstant | None`;

`reason` is `owner_approval`, `service_unreachable`, `binding_suspended` or `outcome_unknown`. `retry_ordinal` and `retry_not_before` are present exactly for `service_unreachable` and `outcome_unknown`.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M56 — InFlightEffectAttempt

### Meaning

One non-read operation a FlowRun M40 recorded durably before invoking it.

Candidate fields:

- `node_id: str`;
- `map_index: int | None`;
- `attempt_number: int`;
- `idempotency_key_digest: str`;

`map_index` is present only for a mapped node. The entry is cleared only by the concluding NodeExecution M41; an entry found at restart is an effect whose outcome is unknown.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M57 — ServiceInstanceTarget

### Meaning

The one manifest instance of one service that a ServiceTarget M39 selects.

Candidate fields:

- `service_name: str`;
- `instance_name: str`;
- `instance_class: str`;

`instance_class` is `local_dev`, `disposable_rig` or `production`.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M58 — PortValidation

### Meaning

The verdict of validating the values of one direction against the ports of a contract.

Candidate fields:

- `verdict: str`;
- `violated_port_id: str | None`;
- `violated_rule: str | None`;

`verdict` is `conforming` or `not_conforming`. The violated port and rule are present exactly when the verdict is `not_conforming`.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M59 — LibraryVersion

### Meaning

One library a SandboxRuntimeRevision M22 offers, at its exact version.

Candidate fields:

- `name: str`;
- `version: str`;

The version is exact, never a range.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M60 — WithdrawnTrialCase

### Meaning

One trial case an AdmissionVerdict M26 excluded because it was withdrawn.

Candidate fields:

- `trial_case_ref: str`;
- `withdrawal_reason: str`;

The reason is the one recorded on the TrialCase M24 when it was withdrawn.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M61 — AdmissionRefusal

### Meaning

One reason an AdmissionVerdict M26 refused an implementation.

Candidate fields:

- `reason: str`;
- `trial_execution_ref: str | None`;

`reason` is `empty_corpus`, `missing_trial_execution`, `non_conforming_trial`, `runtime_withdrawn` or `slot_retired`. The execution reference is present exactly for `non_conforming_trial`.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.

## Model M62 — PortValue

### Meaning

One value bound to the port it belongs to.

Candidate fields:

- `port_id: str`;
- `value: StoredValue | SourceReference`;

Used wherever State 1 says "one value per port": the inputs and expected outputs of a TrialCase M24 and the inputs and outputs of a FlowRun M40. A trial case carries only StoredValue; a flow run input may instead be a SourceReference M13. The binding to the port is part of the fact; a bare sequence of values would lose it.

### Identity

value

### Identity evidence

Substitution: equal field values are interchangeable. Continuity: the value never changes; a correction is another value.

### Source of truth

The model that embeds it.

### Lifecycle candidate

No independent lifecycle.
