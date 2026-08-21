# Cabinet Vault — next session handoff

## Direction

The experiment tests Cabinet as a locally running self-described data/authority
box compiled into a generic host, not as a permanently product-specific backend
application.

Target shape:

```text
Cabinet durable semantic contract
        ↓
compiled box capabilities / policies / schemas
        ↓
generic host + verified generic providers
        ↓
agent-side composition with independent external boxes/connectors
```

Core rules:

> Keep meaning durable. Treat everything provably derivable from that meaning as
> disposable compilation output.

> Deterministic compiler/host code may implement declared rules only. It must not
> silently extend the language or choose missing product meaning.

## Read first

```text
GENERATED_BACKEND_BOUNDARY_AUDIT.md
GENERIC_HOST_LOWERING_RESULT.md
POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md
```

The old generated classical backend remains diagnostic evidence. Do not repair
its external integration stubs by hand.

## Boundary audit

The failed generated backend is classified into three dispositions:

```text
BOUNDARY_LEAK
  -> remove from Cabinet product specification

LANGUAGE_RELATION_GAP
PROJECTION_GAP
VERIFICATION_NOT_EXECUTED
LOWERING_GAP
  -> generic host/lowering contract

AUTHORITY_SEMANTIC_GAP
DOMAIN_SEMANTIC_GAP
  -> keep and close in Cabinet semantic specification
```

Required verification remains fail closed:

```text
PASS       executed and passed
FAIL       executed and failed
UNVERIFIED required evidence not obtained
SKIP       not executed; never equivalent to PASS
```

## Executed experiment evidence

A real Termux run on 2026-08-21 executed the focused experiment suite:

```text
114 passed in 2.25s
```

Box language audit:

```text
pass
15 rules
exit 0
```

Generated-backend boundary audit:

```text
status: classified
verification_gate: block
exit: 2
```

Candidate host plan before provider promotion:

```text
status: compiled
gaps: []
verification_gate: block
runtime_dependencies: [psycopg, pydantic]
exit: 2
```

`git diff --check` passed.

## Generic host provider state

Current candidate profile:

```text
postgres_record_kernel          PASS
authority_kernel                UNVERIFIED
typed_schema_kernel             UNVERIFIED
local_private_byte_vault        UNVERIFIED
protected_configuration_kernel  UNVERIFIED
```

The complete host remains blocked because every required provider must be PASS.

## PostgreSQL record kernel — verified

Implementation:

```text
tools/postgres_record_kernel.py
```

Probe runner:

```text
tools/postgres_record_kernel_probe.py
```

Machine packet:

```text
experiments/cabinet-vault/generic_host_provider_verification_v0.yaml
```

Executed evidence:

```text
experiments/cabinet-vault/POSTGRES_RECORD_KERNEL_RUNTIME_EVIDENCE.md
```

The first real runtime attempt found a provider bug: an embedded NUL in the
composite advisory-lock key was invalid PostgreSQL text. The provider was fixed
to use deterministic text-safe composite identity and a regression guard was
added.

After the fix:

```text
12 passed in 0.64s

RECORD-PROBE-001 PASS  psycopg imports
RECORD-PROBE-002 PASS  commit/rollback atomicity
RECORD-PROBE-003 PASS  exact-resource locking
RECORD-PROBE-004 PASS  no partial state after failure
RECORD-PROBE-005 PASS  append-only audit persistence
record_probe_exit=0
```

This is sufficient to promote only `postgres_record_kernel` to PASS for the
fingerprint-bound implementation and probe runner.

## Authority split

Durable Cabinet authority semantics remain in:

```text
experiments/cabinet-vault/cabinet_authority_contract_v0.yaml
```

They include principal separation, credential-class non-interchangeability,
exact capability/resource scope, host-bound actor provenance, effect authority,
default-deny disclosure, revocation meaning, and append-only audit meaning.

PostgreSQL, Argon2id, verifier/session/throttle storage, Linux administration,
and transport choices remain generic mechanisms/lowering rather than Cabinet
semantic identity.

Open authority questions remain:

```text
AUTH-OQ-001  smallest generic grant representation across boxes
AUTH-OQ-002  generic audit vocabulary vs Cabinet-specific event meaning
```

Do not solve them by importing Cabinet role names into the generic host kernel.

## PlanActual remains reopened

The previous aliases:

```text
EstimateItemSnapshot.total
InvoiceLine.total
```

are not accepted as closed monetary semantics.

Open decisions:

```text
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison meaning: net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit conversion evidence
```

Do not hide these choices in an adapter, compiler heuristic, or generated code.

## Immediate next work

Proceed in this order:

1. **Implement `local_private_byte_vault` as a generic provider.**
   It must own opaque storage/staging references and must not expose raw paths to
   Cabinet callers.

2. **Execute VAULT-PROBE-001..006.**
   Prove stage/reopen/hash verification, exact conflict behavior, publication
   atomicity/recovery, readiness blocking after unresolved recovery, and
   symlink/device/non-regular-file escape rejection.

3. **Then implement/verify the smallest typed schema and protected configuration
   providers needed by the archive/source slice.**

4. **Verify authority_kernel before calling a protected capability verified.**

5. **Only after all required providers pass**, execute one real
   `invoice.source.attach` capability from `cabinet_backend_box_v0.yaml` without
   reintroducing Cabinet service/repository/router ownership.

6. Resolve PA-MONEY-001..003 only through an explicit Cabinet product decision.

## Stop conditions

Stop and report a semantic/architectural gap instead of adding code when:

- a generated stub requires a product-specific external client inside Cabinet;
- a deterministic host/compiler decision has no declared machine rule;
- a mapping requires field-name/type guessing;
- principal/scope/disclosure/effect meaning is absent;
- provider status would become PASS without executed evidence;
- PlanActual code would have to choose unresolved monetary meaning.

## Success criterion

Cabinet's durable definition should become substantially smaller than the
classical application specification while preserving real data, authority,
policy, invariants, effects, and provenance. Remaining runtime structure should
be generic declared-and-proved host machinery or disposable derived composition,
not hidden product architecture.
