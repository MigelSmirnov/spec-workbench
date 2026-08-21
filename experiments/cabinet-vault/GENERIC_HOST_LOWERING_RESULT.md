# Generic host lowering — current result

## Status

The Cabinet archive/source box has a machine-addressable generic host lowering
plan with all structural relations and runtime dependency projection closed.

Current state:

```text
status: compiled
gaps: []
verification_gate: block
runtime_dependencies:
  - pydantic
  - psycopg
```

The gate is blocked by exactly one required provider: `authority_kernel`.

## Provider state

```text
typed_schema_kernel             PASS
postgres_record_kernel          PASS
local_private_byte_vault        PASS
protected_configuration_kernel  PASS
authority_kernel                UNVERIFIED
```

A provider is promoted only from fingerprint-bound executed evidence. The host
verification gate passes only when all five required providers are PASS.

## Verified provider evidence

### postgres_record_kernel

```text
RECORD-PROBE-001..005 PASS
exit 0
```

Real PostgreSQL execution proved `psycopg` availability, commit/rollback,
exact-resource locking, no partial state after rollback, and append-only audit.
The first run exposed an embedded-NUL advisory-lock bug; it was repaired before
promotion.

Evidence:

```text
experiments/cabinet-vault/POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
```

### local_private_byte_vault

```text
VAULT-PROBE-001..006 PASS
exit 0
```

Real Termux filesystem execution proved opaque references, staged reopen/hash
verification, content-addressed conflict protection, restart recovery, blocking
unrecoverable publication state, and symlink/non-regular-file fail-closed
behavior. The first run exposed unavailable `os.link`; publication was repaired
to per-content `flock` + same-filesystem atomic rename before promotion.

Evidence:

```text
experiments/cabinet-vault/LOCAL_PRIVATE_BYTE_VAULT_RUNTIME_EVIDENCE.md
```

### protected_configuration_kernel

```text
CONFIG-PROBE-001..003 PASS
exit 0
```

The selected runtime proved missing required protected configuration blocks ready
state, protected values cannot escape through caller/audit output, and symbolic
references select exact host-owned provider inputs without turning secret/source
mechanism into business data.

Evidence:

```text
experiments/cabinet-vault/PROTECTED_CONFIGURATION_KERNEL_RUNTIME_EVIDENCE.md
```

### typed_schema_kernel

```text
SCHEMA-PROBE-001..003 PASS
status: pass
exit 0
```

The selected Termux runtime proved invalid input rejection before effects,
closed-boundary extra-field rejection, and invalid output rejection before typed
disclosure. The provider supports compatible Pydantic validation APIs without
making a Pydantic major version part of Cabinet semantics.

Evidence:

```text
experiments/cabinet-vault/TYPED_SCHEMA_KERNEL_RUNTIME_EVIDENCE.md
```

## Final provider boundary: authority_kernel

Candidate implementation and probe are now fingerprint-bound:

```text
tools/authority_kernel.py
tools/authority_kernel_probe.py
tests/test_authority_kernel.py
```

Required executed obligations remain:

```text
AUTH-PROBE-001  caller-supplied authorization decision cannot authorize
AUTH-PROBE-002  revoked principal/credential loses future authority
AUTH-PROBE-003  exact capability + exact resource scope required
AUTH-PROBE-004  synchronization credential rejected at local-agent boundary
AUTH-PROBE-005  local-agent credential rejected as synchronization authority
AUTH-PROBE-006  undeclared effect/disclosure denied
AUTH-PROBE-007  actor bound from authenticated principal
AUTH-PROBE-008  audit evidence contains no reusable credential material
```

The candidate grant/policy/audit representation is generic host machinery. It
does not claim the open research questions `AUTH-OQ-001` or `AUTH-OQ-002` are
closed and contains no Cabinet role vocabulary.

## Lowering rules

The structural planner still implements exactly:

```text
GHL-REL-001
GHL-PROJ-001
GHL-VERIFY-001
GHL-VERIFY-002
```

`GHL-SEM-001` remains outside the structural planner. No host/compiler step may
choose missing product semantics, authority meaning, effect meaning, disclosure
meaning, or PlanActual monetary meaning.

## Next boundary

Execute `AUTH-PROBE-001..008` in the selected runtime. If all eight PASS with
exit 0, promote `authority_kernel` and re-run the host lowering plan. At that
point the expected verification gate becomes `pass`.

Only then compile and execute one real `invoice.source.attach` capability through
the verified generic providers, without reintroducing Cabinet service/repository/
router ownership.
