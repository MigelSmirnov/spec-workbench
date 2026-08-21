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
POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
LOCAL_PRIVATE_BYTE_VAULT_RUNTIME_EVIDENCE.md
PROTECTED_CONFIGURATION_KERNEL_RUNTIME_EVIDENCE.md
TYPED_SCHEMA_KERNEL_RUNTIME_EVIDENCE.md
PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md
```

## Executed experiment evidence

Real Termux execution on 2026-08-21 established:

```text
focused experiment suite: 114 passed in 2.25s
box language audit: pass, 15 rules, exit 0
generated-backend boundary audit: classified, gate block, exit 2
candidate host structural plan: compiled, gaps [], gate block, exit 2
git diff --check: pass
```

Later provider execution established four PASS providers:

```text
postgres_record_kernel          PASS
local_private_byte_vault        PASS
protected_configuration_kernel  PASS
typed_schema_kernel             PASS
authority_kernel                UNVERIFIED
```

The complete host remains blocked until `authority_kernel` also produces
fingerprint-bound executed evidence.

## Verified providers

### postgres_record_kernel

```text
RECORD-PROBE-001..005 PASS
exit 0
```

The first real runtime attempt exposed an embedded-NUL advisory-lock bug. The
provider was repaired to use deterministic PostgreSQL-text-safe composite lock
identity before promotion.

### local_private_byte_vault

```text
VAULT-PROBE-001..006 PASS
exit 0
```

The first Termux run exposed missing `os.link`. Publication was repaired to
per-content `flock` + conflict check + same-filesystem atomic rename + fsync +
reopen/hash/size verification. The generic vault does not absorb Cabinet
`source_id` conflict semantics.

### protected_configuration_kernel

```text
CONFIG-PROBE-001..003 PASS
exit 0
```

Missing required secret configuration blocks ready state; protected values do
not enter caller/audit output; symbolic references select host-owned inputs
without exposing the source key or secret as business data.

### typed_schema_kernel

```text
SCHEMA-PROBE-001..003 PASS
status: pass
exit 0
```

The selected Termux runtime initially lacked `pydantic`; Pydantic v2 installation
attempted a `pydantic-core` build and failed. The provider intentionally supports
the Pydantic v1 validation API as a lowering/runtime choice. A compatible runtime
was selected and the fingerprint-bound probe then passed. No Pydantic major
version becomes Cabinet product semantics.

## authority_kernel — candidate ready, evidence pending

Artifacts:

```text
tools/authority_kernel.py
tools/authority_kernel_probe.py
tests/test_authority_kernel.py
experiments/cabinet-vault/cabinet_authority_contract_v0.yaml
```

The implementation is fingerprint-bound in
`generic_host_provider_verification_v0.yaml` but remains `UNVERIFIED` until the
selected runtime executes all eight probes:

```text
AUTH-PROBE-001  caller-supplied authorization_decision cannot authorize
AUTH-PROBE-002  revoked principal/credential loses future authority
AUTH-PROBE-003  exact capability + exact resource scope required
AUTH-PROBE-004  synchronization credential rejected at local-agent boundary
AUTH-PROBE-005  local-agent credential rejected as synchronization authority
AUTH-PROBE-006  undeclared effect/disclosure denied
AUTH-PROBE-007  protected mutation actor bound from authenticated principal
AUTH-PROBE-008  audit evidence contains no reusable credential material
```

The candidate uses generic principal, credential, exact grant, capability policy,
actor binding and sanitized audit records. This is an executable candidate
representation only; it does **not** claim `AUTH-OQ-001` or `AUTH-OQ-002` are
closed and contains no Cabinet role names.

## Authority open questions remain explicit

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
```

Do not close these merely because the candidate provider can execute the current
archive/source authority obligations.

## PlanActual remains reopened

```text
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: Invoice Card net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit accepted conversion evidence
```

Do not choose these meanings in compiler/adapter code.

## Immediate next work

1. Execute the authority unit/guard set and `tools/authority_kernel_probe.py` in
   the selected Termux runtime.
2. If and only if `AUTH-PROBE-001..008` all PASS with exit 0, record evidence and
   promote `authority_kernel`.
3. Re-run `host_lowering_plan.py`; with five required providers PASS its
   verification gate should become `pass` rather than `block`.
4. Then compile and execute one real `invoice.source.attach` capability using the
   verified generic authority/schema/record/vault/config providers, without
   reintroducing Cabinet service/repository/router ownership.
5. Keep PlanActual monetary mapping blocked until PA-MONEY-001..003 are explicit
   accepted Cabinet product decisions.

## Stop conditions

Stop and report a semantic/architectural gap instead of adding code when:

- a product-specific external client would be embedded inside Cabinet;
- a host/compiler decision has no declared machine rule;
- field-name/type guessing would choose domain meaning;
- principal/scope/disclosure/effect meaning is missing;
- a provider would become PASS without executed evidence;
- unresolved PlanActual monetary meaning would have to be chosen by code.

## Success criterion

Cabinet's durable definition becomes substantially smaller than the classical
application specification while preserving real data, authority, policy,
invariants, effects and provenance. Remaining runtime structure is generic,
declared and proved, or disposable derived composition rather than hidden product
architecture.
