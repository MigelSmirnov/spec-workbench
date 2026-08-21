# Generic host lowering — verified provider and capability result

## Status

The Cabinet archive/source experiment now has executed evidence for the complete generic-host provider boundary and one real protected capability path.

```text
host_lowering_plan.status: compiled
host_lowering_plan.gaps: []
host_lowering_plan.verification_gate: pass

invoice.source.attach readiness: pass
attach_expected_missing_source runtime: PASS
```

The old generated classical backend remains intentionally unverified and blocked by `cabinet_boundary_audit.py`. The experiment succeeded by replacing that application-shaped boundary with smaller verified generic mechanisms plus a capability-specific lowering, not by repairing the old backend.

## Verified generic providers

```text
authority_kernel                PASS
typed_schema_kernel             PASS
postgres_record_kernel          PASS
local_private_byte_vault        PASS
protected_configuration_kernel  PASS
```

Each provider is fingerprint-bound and has real executed Termux evidence.

Notable runtime defects found before promotion:

```text
postgres_record_kernel
  embedded NUL in advisory-lock identity
  -> deterministic PostgreSQL-text-safe composite identity

local_private_byte_vault
  Termux Python lacked os.link
  -> per-content flock + same-filesystem atomic rename
```

Provider evidence:

```text
POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
LOCAL_PRIVATE_BYTE_VAULT_RUNTIME_EVIDENCE.md
PROTECTED_CONFIGURATION_KERNEL_RUNTIME_EVIDENCE.md
TYPED_SCHEMA_KERNEL_RUNTIME_EVIDENCE.md
AUTHORITY_KERNEL_RUNTIME_EVIDENCE.md
```

## Capability-specific content validation

`invoice.source.attach` originally remained blocked by one explicit lowering gap:

```text
verified_content_signature
```

That gap is closed by the fingerprint-bound capability execution provider:

```text
bounded_content_validation_kernel
Pillow + pypdf
CONTENT-PROBE-001..005 PASS
exit 0
```

It enforces the declared closed JPEG/PNG/PDF media set with parser-based validation and bounded image safety, rather than trusting filenames, extensions, caller-declared MIME values, or a magic prefix alone.

Evidence:

```text
BOUNDED_CONTENT_VALIDATION_RUNTIME_EVIDENCE.md
```

Current readiness:

```text
status: ready
host_verification_gate: pass
capability_readiness_gate: pass
blocking_gaps: []
```

## First real protected capability execution

Machine lowering:

```text
invoice_source_attach_execution_contract_v0.yaml
invoice_source_attach_runtime_lowering_v0.yaml
```

Runtime implementation:

```text
tools/invoice_source_attach_models.py
tools/invoice_source_attach_runtime.py
tools/invoice_source_attach_runtime_probe.py
```

The first real run exposed a Pydantic-v1 nested `ForwardRef` compatibility defect before byte/metadata effects. The typed model implementation was repaired without changing Cabinet semantics, and a regression guard was added.

Successful rerun:

```text
21 passed in 0.93s
ATTACH-PROBE-001 PASS
ATTACH-PROBE-002 PASS
ATTACH-PROBE-003 PASS
ATTACH-PROBE-004 PASS
ATTACH-PROBE-005 PASS
ATTACH-PROBE-006 PASS
ATTACH-PROBE-007 PASS
status: pass
attach_runtime_exit=0
```

Evidence:

```text
INVOICE_SOURCE_ATTACH_RUNTIME_EVIDENCE.md
```

For the exact `attach_expected_missing_source` case, this proves real composition of:

```text
authority
+ typed boundary
+ PostgreSQL records/transactions/locks/audit
+ private byte vault/publication recovery
+ protected configuration
+ bounded content validation
```

while preserving the declared source/hash, atomicity, recovery, idempotency, conflict, audit, and disclosure invariants.

## Verified scope is intentionally narrow

PASS currently covers:

```text
one file
explicit stable invoice_id
existing expected_source_id
already-accepted invoice
already-declared expected source
expected hash match when declared
replay/conflict/crash-recovery paths
```

It does not prove:

```text
multi-file batch orchestration
source identity generation
invoice-number search/disambiguation
attachment to non-accepted invoice
transport exposure
```

The machine lowering explicitly blocks scope expansion without new executed evidence.

## Architectural conclusion from the experiment

The branch has now demonstrated the intended shape:

```text
durable Cabinet data/authority/policy meaning
        ↓
generic machine-declared verified providers
        ↓
small capability-specific disposable lowering
        ↓
real protected mutation with durable recovery/audit evidence
```

No Cabinet-specific service/repository/router layer was required to execute the verified case.

This is evidence in favor of treating language relations, dependency projection, verification status, provider bindings, and capability execution contracts as first-class machine artifacts rather than generating a classical backend application and patching its stubs.

## Still not resolved by this result

`GHL-SEM-001` remains the rule that missing product meaning must never be chosen by lowering code.

Authority open questions remain:

```text
AUTH-OQ-001
AUTH-OQ-002
```

PlanActual monetary semantics remain reopened:

```text
PA-MONEY-001
PA-MONEY-002
PA-MONEY-003
```

The next branch decision should be whether to stop here as a successful architecture proof and extract reusable workbench changes, or deliberately extend executed evidence to another exact capability/scope.
