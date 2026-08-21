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
PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md
```

## Executed experiment evidence

Real Termux execution on 2026-08-21 established the focused baseline:

```text
focused experiment suite: 114 passed in 2.25s
box language audit: pass, 15 rules, exit 0
generated-backend boundary audit: classified, gate block, exit 2
initial candidate host structural plan: compiled, gaps [], gate block, exit 2
git diff --check: pass
```

Provider execution then closed all five required generic providers:

```text
authority_kernel                PASS
typed_schema_kernel             PASS
postgres_record_kernel          PASS
local_private_byte_vault        PASS
protected_configuration_kernel  PASS
```

The expected current host plan is now:

```text
status: compiled
gaps: []
verification_gate: pass
runtime_dependencies: [pydantic, psycopg]
exit: 0
```

The old generated-backend audit remains intentionally blocked. Do not confuse
verified generic host providers with repair of the classical generated backend.

## Provider evidence

### postgres_record_kernel

```text
RECORD-PROBE-001..005 PASS
exit 0
```

Real PostgreSQL execution proved dependency presence, transaction rollback,
exact-resource locking, no partial state, and append-only audit. The first run
found and closed an embedded-NUL advisory-lock defect.

### local_private_byte_vault

```text
VAULT-PROBE-001..006 PASS
exit 0
```

Real Termux filesystem execution proved opaque references, stage/reopen/hash
verification, content-addressed conflict behavior, restart recovery, readiness
blocking on unrecoverable committed publication, and symlink/non-regular-file
failure. The first run found unavailable `os.link`; publication was repaired to
per-content `flock` + same-filesystem atomic rename.

### protected_configuration_kernel

```text
CONFIG-PROBE-001..003 PASS
exit 0
```

Missing required protected configuration blocks ready state; protected values do
not enter caller/audit output; symbolic references select host-owned inputs
without becoming business data.

### typed_schema_kernel

```text
SCHEMA-PROBE-001..003 PASS
status: pass
exit 0
```

Invalid input is rejected before effects, undeclared caller fields are rejected,
and invalid output is rejected before disclosure. Pydantic major version remains
a lowering/runtime choice rather than Cabinet semantics.

### authority_kernel

```text
AUTH-PROBE-001..008 PASS
status: pass
exit 0
```

The selected runtime proved caller-supplied authority cannot authorize a protected
invocation, revocation removes future authority, exact resource scope is required,
local-agent and synchronization credential classes are not interchangeable,
undeclared effects/disclosures are denied, actor provenance is host-bound, and
audit evidence contains no reusable credential material.

The candidate representation remains generic host machinery. `AUTH-OQ-001` and
`AUTH-OQ-002` remain explicit open questions and are not closed by provider PASS.

## PlanActual remains reopened

```text
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: Invoice Card net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit accepted conversion evidence
```

Do not choose these meanings in compiler/adapter code.

## Immediate next work

1. Re-run the updated provider/host guards and `host_lowering_plan.py` in Termux.
   The host plan should now return `verification_gate: pass` and exit 0.
2. Before executing product behavior, create a machine-addressable execution
   contract for `invoice.source.attach` from the existing box
   `deterministic_lowering`; do not hide composition rules in Python glue.
3. Execute one real source attachment through the verified authority, schema,
   record, byte-vault, configuration and audit providers.
4. Prove exact invoice targeting, expected-source/hash binding, byte staging and
   verification, one metadata transaction, atomic final publication, final-byte
   verification, idempotent replay, conflict rejection, and no disclosure of raw
   storage references.
5. Do not reintroduce Cabinet service/repository/router ownership merely to wire
   the providers together.
6. Keep PlanActual monetary mapping blocked until PA-MONEY-001..003 are explicit
   accepted Cabinet product decisions.

## Stop conditions

Stop and report a semantic/architectural gap instead of adding code when:

- a product-specific external client would be embedded inside Cabinet;
- a host/compiler decision has no declared machine rule;
- field-name/type guessing would choose domain meaning;
- principal/scope/disclosure/effect meaning is missing;
- capability composition would introduce behavior absent from the durable box
  contract;
- unresolved PlanActual monetary meaning would have to be chosen by code.

## Success criterion

Cabinet's durable definition becomes substantially smaller than the classical
application specification while preserving real data, authority, policy,
invariants, effects and provenance. Remaining runtime structure is generic,
declared and proved, or disposable derived composition rather than hidden product
architecture.
