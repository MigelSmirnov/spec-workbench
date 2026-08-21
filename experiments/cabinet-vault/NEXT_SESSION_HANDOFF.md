# Cabinet Vault — next session handoff

## Direction

Cabinet is being tested as a self-described local data/authority box compiled into
a generic host, not as a permanently product-specific backend application.

```text
Cabinet durable semantic contract
        ↓
compiled box capabilities / policies / schemas
        ↓
verified generic host providers
        ↓
verified capability-specific lowerings
        ↓
agent-side composition
```

Deterministic host/runtime code may implement declared rules only. It must not
choose missing product meaning or hide a missing lowering behind glue code.

## Verified generic host

Real Termux execution on 2026-08-21 produced PASS evidence for all five required
host providers:

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

The old generated-backend boundary audit remains intentionally blocked; verified
generic host providers are not a repair of the classical generated backend.

## Capability readiness — invoice.source.attach

Machine contract:

```text
experiments/cabinet-vault/invoice_source_attach_execution_contract_v0.yaml
```

Readiness compiler:

```text
tools/capability_execution_readiness.py
```

The former `verified_content_signature` lowering gap is now closed by the selected
generic execution provider:

```text
bounded_content_validation_kernel
runtime dependencies: Pillow, pypdf
```

Real Termux evidence:

```text
CONTENT-PROBE-001 PASS
CONTENT-PROBE-002 PASS
CONTENT-PROBE-003 PASS
CONTENT-PROBE-004 PASS
CONTENT-PROBE-005 PASS
status: pass
exit: 0
```

Evidence:

```text
experiments/cabinet-vault/BOUNDED_CONTENT_VALIDATION_RUNTIME_EVIDENCE.md
```

Therefore expected capability readiness is now:

```text
host_verification_gate: pass
capability_readiness_gate: pass
status: ready
blocking_gaps: []
exit: 0
```

The content validator does not trust filename, extension or caller media type
alone. JPEG/PNG use Pillow structural verification/full decode with decompression
bomb protection; PDF uses strict pypdf structural parsing. Parser libraries remain
lowering choices, not Cabinet product identity.

## First real runtime case — implementation ready, evidence pending

Runtime lowering:

```text
experiments/cabinet-vault/invoice_source_attach_runtime_lowering_v0.yaml
```

Implementation:

```text
tools/invoice_source_attach_models.py
tools/invoice_source_attach_runtime.py
tools/invoice_source_attach_runtime_probe.py
```

The first executed case is intentionally narrow:

```text
attach_expected_missing_source
exactly one file
explicit invoice_id
explicit expected_source_id
already-accepted invoice
already-declared expected source
```

It does not invent a source identity, search by invoice number, or implement
multi-file batch orchestration.

Declared runtime order:

```text
typed input
→ exact authority / exact invoice scope
→ expected source + hash binding
→ bounded content validation
→ byte staging + reopen/hash verification
→ exact invoice lock + exact source/publication lock
→ atomic metadata_committed journal + pending source provenance + durable audit
→ commit PostgreSQL metadata
→ atomic final byte publication
→ final reopen/hash verification
→ settlement transaction: publication=published + source=available
→ safe typed result
```

A crash after metadata commit intentionally leaves `metadata_committed` plus the
staging/final references as host-owned recovery state. Startup recovery must
finish publication before the source can become available.

Runtime verification obligations:

```text
ATTACH-PROBE-001 exact target/authority before effects
ATTACH-PROBE-002 source/hash/content validation before staging/commit
ATTACH-PROBE-003 success becomes available only after published final bytes verify
ATTACH-PROBE-004 equivalent replay is idempotent
ATTACH-PROBE-005 conflicting bytes cannot replace accepted evidence
ATTACH-PROBE-006 post-metadata interruption recovers to one published result
ATTACH-PROBE-007 output/audit disclose no storage refs, config keys or credentials
```

Current runtime status:

```text
implementation_ready_unverified
```

Do not mark this runtime PASS until `tools/invoice_source_attach_runtime_probe.py`
executes all seven probes with exit 0 against a real PostgreSQL runtime and real
filesystem vault.

## Runtime configuration for the probe

Both values are protected host configuration and are consumed through
`protected_configuration_kernel`:

```text
SPEC_WORKBENCH_TEST_POSTGRES_DSN
SPEC_WORKBENCH_ATTACH_VAULT_ROOT
```

The probe creates its own temporary PostgreSQL schema and a unique child vault
under the configured root, then removes both after execution.

## Important defects already found and repaired in this experiment

```text
postgres_record_kernel
  embedded NUL advisory-lock identity
  -> deterministic PostgreSQL-text-safe identity

local_private_byte_vault
  os.link unavailable in Termux Python
  -> per-content flock + conflict check + atomic rename

content-validation lowering
  initially absent
  -> explicit Pillow/pypdf relation + runtime projection + executed probes
```

These failures are evidence for keeping runtime mechanisms cheap, replaceable and
verification-gated rather than embedding them into Cabinet semantics.

## Authority open questions remain explicit

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
```

Current authority PASS does not close these globally.

## PlanActual remains reopened

```text
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit conversion evidence
```

Do not choose those meanings in runtime/compiler code.

## Immediate next work

1. Pull the branch in Termux and run the focused runtime guards.
2. Confirm `capability_execution_readiness.py` returns `ready/pass/exit 0`.
3. Start the dedicated PostgreSQL probe cluster if it is stopped.
4. Set `SPEC_WORKBENCH_TEST_POSTGRES_DSN` and an explicit absolute
   `SPEC_WORKBENCH_ATTACH_VAULT_ROOT`.
5. Run `tools/invoice_source_attach_runtime_probe.py`.
6. If all `ATTACH-PROBE-001..007` PASS with exit 0, record evidence and promote
   only this single-source runtime case.
7. Only after that decide whether to generalize to multi-file batch execution or
   another Cabinet capability.

## Stop conditions

Stop and report a gap instead of adding code when:

- source identity would need to be invented;
- invoice number would be used as a mutation key;
- content validation would rely on filename/MIME/prefix guessing;
- source would become available before final byte verification;
- a hidden runtime transition would be required;
- protected storage/config/credentials would enter caller output or audit;
- unresolved PlanActual monetary meaning would be chosen by code.
