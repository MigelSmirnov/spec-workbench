# Generic host lowering — verified provider result

## Status

The Cabinet archive/source box now has a machine-addressable generic host lowering
plan with structural relations, runtime dependency projection, and every required
provider verification closed by executed evidence.

Expected current plan:

```text
status: compiled
gaps: []
verification_gate: pass
runtime_dependencies:
  - pydantic
  - psycopg
```

This is the first point in the experiment where the generic-host verification
gate is expected to pass. It does **not** make the old generated classical backend
verified; `cabinet_boundary_audit.py` intentionally continues to classify that
failed backend with a blocking verification gate.

## Provider state

```text
authority_kernel                PASS
typed_schema_kernel             PASS
postgres_record_kernel          PASS
local_private_byte_vault        PASS
protected_configuration_kernel  PASS
```

Every provider is fingerprint-bound to its reviewed implementation and probe
runner in `generic_host_provider_verification_v0.yaml`. Promotion requires
executed probe evidence; editing the profile alone is insufficient.

## Executed evidence

### postgres_record_kernel

```text
RECORD-PROBE-001..005 PASS
exit 0
```

Real PostgreSQL execution proved `psycopg` availability, atomic commit/rollback,
exact-resource locking, no partial state after rollback, and append-only audit.
The first run exposed an embedded-NUL advisory-lock defect; the implementation was
repaired before promotion.

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
references select exact host-owned provider inputs without turning mechanism
values into business data.

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
disclosure. The provider does not make a Pydantic major version part of Cabinet
semantics.

Evidence:

```text
experiments/cabinet-vault/TYPED_SCHEMA_KERNEL_RUNTIME_EVIDENCE.md
```

### authority_kernel

```text
AUTH-PROBE-001..008 PASS
status: pass
exit 0
```

The selected Termux runtime proved caller-supplied authority cannot authorize a
protected invocation, revocation removes future authority, exact resource scope
is required, local-agent and synchronization credential classes are not
interchangeable, undeclared effects/disclosures are denied, actor provenance is
host-bound, and audit evidence contains no reusable credential material.

Evidence:

```text
experiments/cabinet-vault/AUTHORITY_KERNEL_RUNTIME_EVIDENCE.md
```

The candidate grant/policy/audit representation remains generic host machinery.
This result does **not** declare `AUTH-OQ-001` or `AUTH-OQ-002` globally resolved
and introduces no Cabinet role vocabulary.

## Lowering rules

The structural planner still implements exactly:

```text
GHL-REL-001
GHL-PROJ-001
GHL-VERIFY-001
GHL-VERIFY-002
```

`GHL-SEM-001` remains outside the structural planner. Provider verification does
not authorize a compiler to choose missing product semantics, effect meaning,
disclosure meaning, or PlanActual monetary meaning.

## What is now closed

For the selected candidate host profile, the experiment has evidence that:

```text
all declared host requirements resolve to one provider
all selected runtime dependencies are projected
all five required providers have executed PASS evidence
```

Therefore `host_lowering_plan.py` should now return `verification_gate: pass` and
exit `0` for `cabinet_backend_box_v0.yaml` +
`generic_host_profile_candidate_v0.yaml`.

## Capability-level readiness is separate

The first protected capability now has a machine-addressable execution contract:

```text
experiments/cabinet-vault/invoice_source_attach_execution_contract_v0.yaml
```

Readiness compiler and guards:

```text
tools/capability_execution_readiness.py
tests/test_capability_execution_readiness.py
```

This compiler checks the exact `invoice.source.attach` capability surface,
deterministic lowering steps, preconditions, provider verification, audit and
disclosure bindings before executable composition is allowed.

Expected current result:

```text
host_verification_gate: pass
capability_readiness_gate: block
blocking gap:
  LOWERING_GAP verified_content_signature
```

The gap is deliberate and concrete. The product specification already requires a
closed accepted media set, content-signature verification, bounded parsing and
malformed-document rejection. What is missing is a selected generic bounded
content-validation implementation relation and its runtime projection.

The execution contract explicitly forbids closing that gap with filename,
extension, caller-declared media type, a magic prefix alone, an unbounded parser,
or a hidden product-specific adapter.

## Next boundary

Select and verify the smallest generic bounded content-validation lowering for the
accepted JPEG/PNG/PDF source policy. Declare its implementation relation and
runtime dependencies before code, then re-run capability readiness.

Only when the capability readiness gate passes should the first real
`attach_expected_missing_source` execution be implemented through the verified
authority, schema, record, byte-vault, configuration and audit providers. Do not
reintroduce Cabinet service/repository/router ownership merely to compose them.
