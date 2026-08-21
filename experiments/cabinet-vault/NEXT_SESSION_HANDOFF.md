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

The generated-backend and host-plan non-zero exits are expected fail-closed
verification behavior, not failures of classification/structure.

## Current generic provider state

```text
postgres_record_kernel          PASS
local_private_byte_vault        PASS
typed_schema_kernel             UNVERIFIED
protected_configuration_kernel  UNVERIFIED
authority_kernel                UNVERIFIED
```

The complete host remains blocked until all required providers are PASS.

## postgres_record_kernel — verified

Artifacts:

```text
tools/postgres_record_kernel.py
tools/postgres_record_kernel_probe.py
experiments/cabinet-vault/POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
```

The first real runtime attempt found an embedded-NUL advisory-lock bug. The lock
identity was repaired to deterministic PostgreSQL-text-safe composite identity.
The rerun produced:

```text
RECORD-PROBE-001 PASS
RECORD-PROBE-002 PASS
RECORD-PROBE-003 PASS
RECORD-PROBE-004 PASS
RECORD-PROBE-005 PASS
exit 0
```

This proves the selected runtime has `psycopg`, atomic commit/rollback,
exact-resource serialization, no partial state after rollback, and append-only
audit persistence.

## local_private_byte_vault — verified

Artifacts:

```text
tools/local_private_byte_vault.py
tools/local_private_byte_vault_probe.py
experiments/cabinet-vault/LOCAL_PRIVATE_BYTE_VAULT_RUNTIME_EVIDENCE.md
```

The first Termux filesystem run found that the selected Python runtime lacks
`os.link`. Publication was repaired to a portable generic mechanism:

```text
per-content flock
+ exact existing-final verification
+ conflict rejection
+ same-filesystem atomic staging -> final rename
+ fsync
+ reopen/hash/size verification
```

The rerun produced:

```text
VAULT-PROBE-001 PASS
VAULT-PROBE-002 PASS
VAULT-PROBE-003 PASS
VAULT-PROBE-004 PASS
VAULT-PROBE-005 PASS
VAULT-PROBE-006 PASS
exit 0
```

The vault owns opaque references, staging verification, content-addressed
publication and committed-publication recovery. Cabinet `source_id` conflict
meaning remains at the capability/record layer under exact resource locking.

## typed_schema_kernel — implementation ready, evidence pending

Artifacts:

```text
tools/typed_schema_kernel.py
tools/typed_schema_kernel_probe.py
tests/test_typed_schema_kernel.py
```

The provider is fingerprint-bound but remains `UNVERIFIED` until execution.
Required probes:

```text
SCHEMA-PROBE-001  invalid typed input rejected before operation/effect
SCHEMA-PROBE-002  undeclared fields rejected at closed caller boundary
SCHEMA-PROBE-003  invalid provider output rejected before disclosure
```

The branch workflow now installs `pydantic` explicitly because it is a declared
runtime projection dependency.

## protected_configuration_kernel — implementation ready, evidence pending

Artifacts:

```text
tools/protected_configuration_kernel.py
tools/protected_configuration_kernel_probe.py
tests/test_protected_configuration_kernel.py
```

The provider is fingerprint-bound but remains `UNVERIFIED` until execution.
Required probes:

```text
CONFIG-PROBE-001  missing required protected configuration blocks ready state
CONFIG-PROBE-002  protected material cannot appear in caller/audit output
CONFIG-PROBE-003  symbolic reference selects exact host provider input without
                  exposing source key or secret as business data
```

## Authority split

Durable authority meaning is declared in:

```text
experiments/cabinet-vault/cabinet_authority_contract_v0.yaml
```

It preserves principal/credential boundary separation, exact capability and
resource scope, host-bound actor provenance, effect authority, default-deny
disclosure, revocation meaning and append-only audit meaning.

Mechanisms such as PostgreSQL credential storage, Argon2id, session/throttle
storage, Linux administration and HTTP/MCP/IPC remain generic lowering choices.

Open questions remain explicit:

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
```

Do not import Cabinet role names into the generic authority kernel to close them.

## PlanActual remains reopened

Do not choose monetary meaning in compiler/adapter code.

```text
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: Invoice Card net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit accepted conversion evidence
```

## Immediate next work

1. Execute `typed_schema_kernel_probe.py` and
   `protected_configuration_kernel_probe.py` in the selected Termux runtime.
2. Record evidence and promote only probes/providers that actually PASS.
3. Implement and verify `authority_kernel` against `AUTH-PROBE-001..008` without
   leaking Cabinet role names into the generic host.
4. Only after all five required providers PASS, compile and execute one real
   `invoice.source.attach` capability without reintroducing service/repository/
   router ownership.
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
