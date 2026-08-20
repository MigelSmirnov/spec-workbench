# Generic host lowering — first structural result

## Status

The Cabinet vault experiment now has a first machine-addressable generic host
lowering plan for the real archive/source box slice.

This result is **structural and UNVERIFIED**. It does not claim that a generic
host implementation is runnable or behaviorally verified.

## Inputs

```text
experiments/cabinet-vault/cabinet_backend_box_v0.yaml
experiments/cabinet-vault/generic_host_lowering_contract_v0.yaml
experiments/cabinet-vault/generic_host_profile_candidate_v0.yaml
```

Planner:

```text
tools/host_lowering_plan.py
```

Conformance:

```text
tests/test_host_lowering_plan.py
```

## Why this exists

The failed classical Cabinet generation exposed two generic lowering failures:

```text
missing interface -> concrete implementation relation
lost psycopg runtime projection
```

Those failures are not Cabinet business semantics. They belong to reusable host
lowering rules.

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

The first projected third-party runtime dependencies are:

```text
pydantic
psycopg
```

The explicit `psycopg` projection is intentional evidence against the failure
observed in the classical generated backend.

## Verification state

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

`compiled` here means only that the declared interface relations and dependency
projection are structurally closed.

It does **not** mean executable or verified.

The CLI exits non-zero while required provider verification is not `PASS`.

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

## Relationship to Cabinet authority

The candidate `authority_kernel` does not define Cabinet business roles or
credential-storage mechanics.

Durable authority semantics are extracted separately in:

```text
experiments/cabinet-vault/cabinet_authority_contract_v0.yaml
```

That contract preserves principal separation, exact capability/resource scope,
host-bound actor provenance, explicit effect/disclosure authority, revocation
semantics, and audit meaning while classifying PostgreSQL, Argon2id, session
storage, throttling storage, and Linux administration as host mechanisms/lowering.

The Cabinet archive manifest is guarded by:

```text
tests/test_cabinet_authority_contract.py
tests/test_cabinet_authority_manifest.py
```

## Next proof obligations

Do not mark providers `PASS` by editing the profile.

For each provider, obtain executed evidence against a concrete implementation and
record the evidence that satisfies its declared host requirements.

The next useful implementation step is to define the smallest provider
verification packets for:

1. authority enforcement;
2. typed schema validation;
3. PostgreSQL record/transaction/locking/audit behavior;
4. local private byte-vault stage/verify/publish/recovery behavior;
5. protected configuration.

Only after required provider evidence is executed and passed may the host plan
verification gate become `pass`.

A later capability execution compiler must remain separate from this structural
planner and must not invent missing Cabinet semantics while lowering a capability.
