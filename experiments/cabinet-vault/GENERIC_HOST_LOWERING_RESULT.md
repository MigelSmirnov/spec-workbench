# Generic host lowering — first structural result

## Status

The Cabinet vault experiment now has a first machine-addressable generic host
lowering plan for the real archive/source box slice.

This result is **structural and UNVERIFIED**. It does not claim that a generic
host implementation is runnable or behaviorally verified.

## Inputs

```text
experiments/cabinet-vault/cabinet_backend_box_v0.yaml
experiments/cabinet-vault/cabinet_authority_contract_v0.yaml
experiments/cabinet-vault/generic_host_lowering_contract_v0.yaml
experiments/cabinet-vault/generic_host_profile_candidate_v0.yaml
experiments/cabinet-vault/generic_host_provider_verification_v0.yaml
```

Planner and guards:

```text
tools/host_lowering_plan.py
tests/test_host_lowering_plan.py
tests/test_host_provider_verification.py
tests/test_cabinet_authority_contract.py
tests/test_cabinet_authority_manifest.py
```

## Why this exists

The failed classical Cabinet generation exposed generic lowering failures:

```text
missing interface -> concrete implementation relation
lost psycopg runtime projection
required verification skipped while the route appeared complete
```

Those failures are not Cabinet business semantics. They belong to reusable host
lowering rules and verification gates.

The planner therefore answers only:

1. does every declared box host requirement resolve to exactly one selected
   provider relation?;
2. is the runtime projection closed over every dependency declared by those
   selected providers?;
3. has every required provider verification actually produced `PASS` evidence?

It does not choose product fields, domain meanings, authority scope, effects, or
disclosure policy. Those are already declared by the box contract or remain a
semantic gap.

## Declared planner rules

The planner exports exactly:

```text
GHL-REL-001
GHL-PROJ-001
GHL-VERIFY-001
GHL-VERIFY-002
```

`generic_host_lowering_contract_v0.yaml` binds those rule IDs to the exact
reviewed `tools/host_lowering_plan.py` blob and names their conformance tests.

`GHL-SEM-001` is deliberately not declared as implemented by this planner. The
planner has no field-mapping or product-semantic choice API. A future execution
compiler must bind that semantic guard explicitly before it can introduce any
fallback behavior.

## Candidate profile

`generic_host_profile_candidate_v0.yaml` supplies one candidate provider for each
host requirement of `cabinet_backend_box_v0.yaml`.

Provider groups are:

```text
authority_kernel
typed_schema_kernel
postgres_record_kernel
local_private_byte_vault
protected_configuration_kernel
```

The profile contains no product-specific dependency.

The projected third-party runtime dependencies are:

```text
pydantic
psycopg
```

The explicit `psycopg` projection is intentional evidence against the failure
observed in the classical generated backend.

## Structural result

Every candidate provider currently declares:

```text
required: true
status: UNVERIFIED
```

Therefore the expected plan is:

```text
status: compiled
verification_gate: block
gaps: []
runtime_dependencies:
  - pydantic
  - psycopg
```

`compiled` here means only that declared interface relations and dependency
projection are structurally closed.

It does **not** mean executable or verified. The CLI exits non-zero while any
required provider verification is not `PASS`.

## Fail-closed conformance cases

The test suite requires:

- a missing provider relation to produce `IMPLEMENTATION_RELATION_MISSING`;
- two providers for one required interface to produce
  `AMBIGUOUS_IMPLEMENTATION_RELATION`;
- removing `psycopg` from runtime projection to produce
  `RUNTIME_DEPENDENCY_NOT_PROJECTED`;
- required `SKIP` verification to normalize to `UNVERIFIED`;
- the verification gate to pass only when every selected required provider is
  `PASS`;
- the planner implementation rule set and source fingerprint to match the
  declared lowering contract exactly.

## Authority split

The candidate `authority_kernel` does not define Cabinet business roles or
credential-storage mechanics.

`cabinet_authority_contract_v0.yaml` preserves durable semantics for principal
separation, exact capability/resource scope, host-bound actor provenance,
explicit effect/disclosure authority, revocation meaning, and audit meaning.

PostgreSQL, Argon2id, session/verifier/throttling storage, Linux administration,
and transport choice remain host mechanisms/lowering.

The archive box manifest is guarded so an agent cannot supply its own authority
evidence and every capability explicitly declares grant, scope, effect,
disclosure, and audit requirements.

## Provider verification packets

`generic_host_provider_verification_v0.yaml` now defines the minimum proof
obligations for all five candidate providers.

### authority_kernel

Covers authentication, bounded grants, exact resource scope, effect policy, and
disclosure policy. Its probes are the `AUTH-PROBE-001..008` vocabulary declared
by `cabinet_authority_contract_v0.yaml`.

### typed_schema_kernel

Must prove invalid input rejection before effects, rejection of undeclared fields
for closed boundary schemas, and output validation before disclosure/settlement.
Its packet explicitly carries the `pydantic` runtime dependency.

### postgres_record_kernel

Must prove the `psycopg` dependency is present in the selected runtime plus
transaction atomicity/rollback, exact-resource locking, absence of partial state,
and append-only audit persistence.

### local_private_byte_vault

Must prove host-owned opaque paths, stage/reopen/hash verification, conflicting
content exclusion, atomic publication/recovery, readiness blocking on unresolved
recovery, and path/symlink/device escape rejection.

### protected_configuration_kernel

Must prove required secret configuration fails closed when absent and protected
values cannot enter caller-visible business data or audit evidence.

Every packet probe is currently `UNVERIFIED`.

The packet guards require:

```text
one packet per candidate provider
packet requirements == provider satisfies requirements
packet runtime dependencies == provider runtime dependencies
PASS probe -> executed=true + non-empty recorded evidence
provider PASS -> every packet probe PASS
```

Therefore no provider may be promoted to `PASS` merely by editing the candidate
profile.

## Current blocking boundary

The declarative architecture work has now reached the point where further
promotion requires **real provider implementations and executed runtime evidence**.

Without that evidence, implementing a capability execution runtime and calling it
verified would repeat the exact failure mode exposed by the classical generation.

The next runtime work must begin with one concrete provider implementation and run
its packet probes. A useful first provider is the PostgreSQL record kernel because
it directly exercises the previously lost `psycopg` projection plus transaction
and locking obligations. The byte-vault provider is the next natural pair for the
real `invoice.source.attach` capability.

A later capability execution compiler must remain separate from this structural
planner and must not invent missing Cabinet semantics while lowering a capability.
