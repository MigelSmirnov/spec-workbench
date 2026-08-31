# State 1 repair — Cabinet identity taxonomy

## Status

Accepted closed type vocabulary already named by M01, M02, M17, A03, and A08.
These models define form, not mutable authorization policy. Runtime code receives
the generated enum symbols through the `models` module and never receives the
catalogue values through an LLM prompt.

## Model M136 — ActorType

Values: `human`, `agent`, `service`, `operator`, `system`.

### Identity

value

### Identity evidence

The value classifies immutable M01 provenance. Equal members are
interchangeable and have no lifecycle.

## Model M137 — PrincipalKind

Values: `cabinet_owner`, `local_backend_node`, `operator`.

### Identity

value

### Identity evidence

The value classifies the stable M02 authorization subject. Equal members are
interchangeable; changing a principal's kind does not preserve the accepted
subject meaning.

## Model M138 — CredentialSubjectKind

Values: `principal`, `node`.

### Identity

value

### Identity evidence

The value selects which accepted subject model a credential binds. Equal
members are interchangeable and do not identify a credential.

## Model M139 — CabinetNodeKind

Values: `vps_cabinet`, `local_backend`.

### Identity

value

### Identity evidence

The value classifies an M17 synchronization participant. Equal members are
interchangeable; node continuity remains owned by `node_id`.
