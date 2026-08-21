# Generic host lowering — current result

## Status

The Cabinet vault experiment has a machine-addressable generic host lowering plan
for the real archive/source box slice.

Current structural state:

```text
status: compiled
gaps: []
verification_gate: block
runtime_dependencies:
  - pydantic
  - psycopg
```

The gate remains blocked because only one of five required providers is verified.

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
```

## Declared lowering rules

The planner implements exactly:

```text
GHL-REL-001
GHL-PROJ-001
GHL-VERIFY-001
GHL-VERIFY-002
```

The lowering contract binds those rule IDs to the reviewed planner source
fingerprint and conformance cases.

`GHL-SEM-001` remains deliberately outside this structural planner. The planner
has no API for choosing missing product semantics, authority meaning, disclosure,
or effect meaning.

## Provider state

```text
postgres_record_kernel          PASS
authority_kernel                UNVERIFIED
typed_schema_kernel             UNVERIFIED
local_private_byte_vault        UNVERIFIED
protected_configuration_kernel  UNVERIFIED
```

A verified provider does not make the complete host verified.

## PostgreSQL record kernel — PASS

Concrete generic provider:

```text
tools/postgres_record_kernel.py
```

Runtime probe:

```text
tools/postgres_record_kernel_probe.py
```

Executed evidence:

```text
experiments/cabinet-vault/POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
```

The provider and probe runner are fingerprint-bound by
`generic_host_provider_verification_v0.yaml`.

### First runtime execution

The first real PostgreSQL run exposed a provider defect: the composite advisory
lock key contained a NUL separator, and PostgreSQL text fields reject NUL bytes.

This was not treated as an environment failure or bypassed probe. The lock
identity was repaired to a deterministic PostgreSQL-text-safe encoding and a
regression guard was added.

### Successful rerun

A real PostgreSQL runtime then produced:

```text
RECORD-PROBE-001 PASS  psycopg available
RECORD-PROBE-002 PASS  commit + rollback atomicity
RECORD-PROBE-003 PASS  exact-resource locking
RECORD-PROBE-004 PASS  no partial state after failure
RECORD-PROBE-005 PASS  append-only audit persistence
overall status: pass
exit: 0
```

Focused structural guards after the lock repair also passed:

```text
12 passed in 0.64s
```

Therefore `postgres_record_kernel` is promoted to `PASS` for the reviewed
implementation/probe fingerprints.

## What PostgreSQL PASS proves

It closes the first generic lowering failure class exposed by the old generated
backend:

```text
selected PostgreSQL provider relation exists
+ psycopg dependency is explicitly projected
+ dependency imports in the selected runtime
+ transaction rollback is real
+ resource locking is real
+ failed transaction does not leak partial metadata/audit state
+ audit rows are append-only at the database boundary
```

It does not prove any other provider.

## Remaining provider obligations

### authority_kernel — UNVERIFIED

Must prove authentication, bounded grants, exact resource scope, effect policy,
disclosure policy, host-bound actor provenance, revocation, and secret-free audit
semantics under `AUTH-PROBE-001..008`.

### typed_schema_kernel — UNVERIFIED

Must prove input validation before effects, closed-schema extra-field rejection,
and output validation before disclosure/settlement. Runtime dependency:
`pydantic`.

### local_private_byte_vault — UNVERIFIED

Must prove opaque host-owned paths, stage/reopen/hash verification, conflicting
content exclusion, atomic publication/recovery, readiness blocking on unresolved
recovery, and symlink/device/non-regular-file escape rejection.

### protected_configuration_kernel — UNVERIFIED

Must prove required secret absence blocks readiness and protected values cannot
enter caller-visible business data or audit evidence.

## Next implementation boundary

The next concrete provider should be:

```text
local_private_byte_vault
```

Reason: together with the verified `postgres_record_kernel`, it provides the two
stateful mechanisms needed for the first real Cabinet source-custody path.

After the byte-vault packet passes, the experiment can attempt one real
`invoice.source.attach` lowering using:

```text
verified record/transaction/locking provider
+ verified byte-vault provider
+ still-explicit authority/schema/configuration gates
```

Do not call that capability verified while authority, schema, or configuration
providers remain `UNVERIFIED`.

The later capability execution compiler must remain separate from the structural
planner and must not invent missing Cabinet semantics while lowering a capability.
