# Cabinet Vault — next session handoff

## Direction

The experiment treats Cabinet as a locally running self-described data/authority
box compiled into a generic host, not as a permanently product-specific backend
application.

```text
Cabinet durable semantic contract
        ↓
compiled box capabilities / policies / schemas
        ↓
generic host + verified generic providers
        ↓
agent-side composition with independent external boxes/connectors
```

Keep product meaning durable. Deterministic host/compiler code may implement only
declared rules and must not choose missing product meaning.

## Read first

```text
GENERATED_BACKEND_BOUNDARY_AUDIT.md
GENERIC_HOST_LOWERING_RESULT.md
AUTHORITY_KERNEL_RUNTIME_EVIDENCE.md
POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
LOCAL_PRIVATE_BYTE_VAULT_RUNTIME_EVIDENCE.md
PROTECTED_CONFIGURATION_KERNEL_RUNTIME_EVIDENCE.md
TYPED_SCHEMA_KERNEL_RUNTIME_EVIDENCE.md
invoice_source_attach_execution_contract_v0.yaml
PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md
```

## Executed provider evidence

Real Termux execution on 2026-08-21 established the baseline and then closed all
five required generic providers:

```text
authority_kernel                PASS
typed_schema_kernel             PASS
postgres_record_kernel          PASS
local_private_byte_vault        PASS
protected_configuration_kernel  PASS
```

The expected generic host plan is now:

```text
status: compiled
gaps: []
verification_gate: pass
runtime_dependencies: [pydantic, psycopg]
exit: 0
```

The old generated-backend audit remains intentionally blocked. Verified generic
host providers are not a repair or verification of the classical generated
backend.

Provider evidence files:

```text
AUTHORITY_KERNEL_RUNTIME_EVIDENCE.md
TYPED_SCHEMA_KERNEL_RUNTIME_EVIDENCE.md
POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
LOCAL_PRIVATE_BYTE_VAULT_RUNTIME_EVIDENCE.md
PROTECTED_CONFIGURATION_KERNEL_RUNTIME_EVIDENCE.md
```

Important runtime defects found and repaired before promotion:

```text
postgres_record_kernel
  embedded NUL in advisory lock identity
  -> deterministic PostgreSQL-text-safe composite identity

local_private_byte_vault
  Termux Python lacked os.link
  -> per-content flock + conflict check + same-filesystem atomic rename + fsync
```

Pydantic major version remains a lowering/runtime choice rather than Cabinet
semantics.

## Capability execution readiness — new boundary

Machine contract:

```text
experiments/cabinet-vault/invoice_source_attach_execution_contract_v0.yaml
```

Readiness compiler and guards:

```text
tools/capability_execution_readiness.py
tests/test_capability_execution_readiness.py
```

The contract copies the exact `invoice.source.attach` input/output/effects,
requires list, disclosure policy, audit requirement, and deterministic lowering
from `cabinet_backend_box_v0.yaml` and binds each step to a verified provider or
an explicit gap.

Expected state:

```text
host_verification_gate: pass
capability_readiness_gate: block
```

Exactly one blocking gap is currently declared:

```text
LOWERING_GAP: verified_content_signature
```

Why it blocks:

The Cabinet box requires a closed accepted media set, content-signature
verification, bounded parsing, and rejection of malformed documents. The current
generic host profile does not yet declare a concrete content-validation
implementation relation/runtime dependency. Filename, extension, caller media
type, or a magic prefix alone are not sufficient and must not be introduced as a
hidden fallback.

This is a capability-level lowering gap, not a missing Cabinet product decision.
The accepted product meaning is already clear: unsafe/malformed content must not
become a verified source replica. What remains is a generic bounded validation
mechanism relation.

## First execution case after the gap closes

The first executable case is intentionally narrow:

```text
attach_expected_missing_source
```

It repairs one already-declared missing source for one already-accepted invoice.
It requires:

```text
explicit invoice_id stable target
each file has expected_source_id
expected_source_id exists in declared expected_sources
calculated hash equals expected hash when the Card declares one
```

It does not define source identity generation when `expected_source_id` is absent
and does not implement invoice-number search/disambiguation.

Once content validation is resolved and verified, the real attachment must prove:

```text
exact capability + exact invoice authority
typed input before effects
expected source/hash binding
size and bounded content validation
stage + reopen/hash/size verification
exact invoice lock
one metadata transaction for journal + source transition
atomic metadata commit
atomic final byte publication
final reopen/hash/size verification
idempotent equivalent replay
conflicting content rejection
append-only durable audit
no raw storage/staging/final references in output
```

Do not reintroduce Cabinet service/repository/router ownership merely to wire the
providers together.

## Authority open questions remain explicit

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
```

Authority provider PASS does not close these globally.

## PlanActual remains reopened

```text
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: Invoice Card net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit accepted conversion evidence
```

Do not choose these meanings in compiler/adapter code.

## Immediate next work

1. Re-run the updated host/provider guards and `host_lowering_plan.py` in Termux;
   host gate should return `pass`, exit 0.
2. Run `capability_execution_readiness.py`; it should intentionally return
   `block`, exit 2, with exactly one `LOWERING_GAP` for
   `verified_content_signature`.
3. Select the smallest generic bounded content-validation lowering that can prove
   the accepted JPEG/PNG/PDF content rules without trusting filename/media type or
   doing unbounded parsing.
4. Declare its implementation relation and runtime dependencies before code;
   execute verification evidence before marking the capability ready.
5. Only then execute the real `attach_expected_missing_source` case through the
   verified generic providers.
6. Keep PlanActual monetary mapping blocked until PA-MONEY-001..003 are explicit
   accepted Cabinet product decisions.

## Stop conditions

Stop and report a semantic/architectural gap instead of adding code when:

- a product-specific external client would be embedded inside Cabinet;
- a host/compiler decision has no declared machine rule;
- field-name/type guessing would choose domain meaning;
- principal/scope/disclosure/effect meaning is missing;
- content validation would rely only on filename, caller media type, or prefix
  guessing;
- capability composition would introduce behavior absent from the durable box
  contract;
- unresolved PlanActual monetary meaning would have to be chosen by code.

## Success criterion

Cabinet's durable definition becomes substantially smaller than the classical
application specification while preserving real data, authority, policy,
invariants, effects and provenance. Remaining runtime structure is generic,
declared and proved, or disposable derived composition rather than hidden product
architecture.
