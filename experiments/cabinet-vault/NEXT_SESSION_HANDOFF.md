# Cabinet Vault — next session handoff

## Direction

Cabinet is being tested as a self-described local data/authority box compiled into a generic host, not as a permanently product-specific backend application.

```text
Cabinet durable semantic contract
        ↓
compiled capability/policy/schema meaning
        ↓
verified generic host providers
        ↓
verified capability-specific lowerings
        ↓
agent-side composition
```

Deterministic host/runtime code may implement declared rules only. It must not choose missing product meaning or hide a missing lowering behind glue code.

## Experiment milestone reached

Real Termux execution on 2026-08-21 now proves all of the following layers:

```text
generic host structural lowering       PASS
all five required generic providers    PASS
bounded content-validation lowering    PASS
invoice.source.attach readiness        PASS
attach_expected_missing_source runtime PASS
```

The old generated classical backend remains intentionally blocked by the boundary audit. This milestone does not repair or verify that application architecture.

## Verified generic host

```text
authority_kernel                PASS
typed_schema_kernel             PASS
postgres_record_kernel          PASS
local_private_byte_vault        PASS
protected_configuration_kernel  PASS
```

Expected host plan:

```text
status: compiled
gaps: []
verification_gate: pass
runtime_dependencies: [pydantic, psycopg]
exit: 0
```

Provider evidence files:

```text
AUTHORITY_KERNEL_RUNTIME_EVIDENCE.md
TYPED_SCHEMA_KERNEL_RUNTIME_EVIDENCE.md
POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
LOCAL_PRIVATE_BYTE_VAULT_RUNTIME_EVIDENCE.md
PROTECTED_CONFIGURATION_KERNEL_RUNTIME_EVIDENCE.md
```

## Capability readiness — invoice.source.attach

Execution contract:

```text
experiments/cabinet-vault/invoice_source_attach_execution_contract_v0.yaml
```

The former `verified_content_signature` gap is closed by:

```text
bounded_content_validation_kernel
runtime dependencies: Pillow, pypdf
CONTENT-PROBE-001..005 PASS
exit 0
```

Expected readiness:

```text
status: ready
host_verification_gate: pass
capability_readiness_gate: pass
blocking_gaps: []
exit: 0
```

Evidence:

```text
experiments/cabinet-vault/BOUNDED_CONTENT_VALIDATION_RUNTIME_EVIDENCE.md
```

## First protected capability execution — verified narrow case

Runtime lowering:

```text
experiments/cabinet-vault/invoice_source_attach_runtime_lowering_v0.yaml
```

Runtime implementation:

```text
tools/invoice_source_attach_models.py
tools/invoice_source_attach_runtime.py
tools/invoice_source_attach_runtime_probe.py
```

Executed case:

```text
attach_expected_missing_source
exactly one file
explicit invoice_id
explicit existing expected_source_id
already-accepted invoice
already-declared expected source
```

Real Termux result after the Pydantic-v1 model repair:

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
experiments/cabinet-vault/INVOICE_SOURCE_ATTACH_RUNTIME_EVIDENCE.md
```

The runtime proves, for this exact case:

```text
typed input before effects
exact authenticated capability + exact invoice scope
expected source/hash binding
bounded content validation
private byte staging + reopen/hash/size verification
exact PostgreSQL invoice/source locking
atomic metadata_committed journal + pending provenance + durable audit
atomic final byte publication
final byte verification before available state
idempotent equivalent replay
conflicting bytes rejected without replacing accepted evidence
crash-after-metadata recovery to one verified published source
safe output + append-only audit with no raw storage/config/credential disclosure
```

## Runtime defects found and repaired before PASS

```text
postgres_record_kernel
  embedded NUL advisory-lock identity
  -> deterministic PostgreSQL-text-safe identity

local_private_byte_vault
  os.link unavailable in Termux Python
  -> per-content flock + conflict check + atomic rename

invoice.source.attach typed runtime
  Pydantic v1 unresolved nested ForwardRef under postponed annotations
  -> real nested model types + regression guard
```

These are useful experiment evidence: runtime mechanisms were replaceable without changing Cabinet product semantics.

## Verified-scope boundary

The runtime PASS does **not** prove the entire declared batch capability surface.

Still outside executed evidence:

```text
multi_file_batch_orchestration
source_identity_generation_when_expected_source_id_is_absent
invoice_number_search_or_disambiguation
attachment_to_nonaccepted_invoice
transport exposure (HTTP/MCP/IPC)
```

Do not expand the `verified_scope` in `invoice_source_attach_runtime_lowering_v0.yaml` without new executed evidence.

## Architectural result so far

The experiment has now demonstrated one non-trivial protected Cabinet mutation without reintroducing permanent Cabinet service/repository/router ownership:

```text
Cabinet meaning
+ generic verified authority/schema/record/vault/config providers
+ capability-specific disposable lowering
= real protected data mutation with recovery/audit evidence
```

That is the core hypothesis the branch was intended to test.

## Open semantic work remains separate

Authority research questions remain explicit:

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
```

PlanActual remains reopened:

```text
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit conversion evidence
```

Do not close any of these merely because the source-attach runtime passed.

## Immediate next decision

The next step is a scope decision, not an automatic coding task:

1. **Stop the experiment here as a successful proof of the box + generic-host architecture**, and extract the reusable language/tooling changes; or
2. **Extend executed evidence deliberately** to multi-file `invoice.source.attach` orchestration or a second Cabinet capability.

If extending, preserve the same rules: declare machine bindings first, keep missing semantics explicit, fingerprint implementations, execute real evidence, and never broaden PASS beyond the exact executed scope.
