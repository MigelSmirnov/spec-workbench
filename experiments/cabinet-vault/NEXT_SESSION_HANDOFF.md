# Cabinet Vault — next session handoff

## Current direction

The experiment is not trying to regenerate the classical Cabinet Backend
application more accurately.

The target remains:

```text
Cabinet durable semantic contract
        ↓
compiled box capabilities / policies / schemas
        ↓
generic local host and declared generic lowerings
        ↓
agent-side composition with independent external boxes/connectors
```

Intended deployment shape:

```text
generic host
+ compiled self-described Cabinet box
+ local durable data/storage
```

Cross-product work is composed outside Cabinet. Cabinet should not permanently
own Registry, PresuPro, Holded, VPS, HTTP, or product-specific transport clients
merely because a workflow crosses those systems.

Core rules:

> Keep meaning durable. Treat everything provably derivable from that meaning as
> a cheap disposable compilation artifact.

> Deterministic implementation may implement declared rules. It must not silently
> extend the language or choose missing product meaning.

## Read first

```text
GENERATED_BACKEND_BOUNDARY_AUDIT.md
GENERIC_HOST_LOWERING_RESULT.md
PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md
```

The old generated classical backend was not repaired.

## Generated-backend boundary audit

Implemented:

```text
tools/cabinet_boundary_audit.py
experiments/cabinet-vault/generated_backend_failure_evidence_v0.yaml
tests/test_cabinet_boundary_audit.py
```

Dispositions:

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

Representative evidence includes the missing interface implementation relation,
lost `psycopg` projection, skipped required verification, external-boundary stub
concentration, authority construction mismatches, and unresolved
PlanActual/RetentionRelease behavior.

Classification success is not backend verification.

## Verification rule

```text
PASS       required evidence executed and passed
FAIL       required evidence executed and failed
UNVERIFIED required evidence was not obtained
SKIP       evidence was not executed
```

For required evidence:

```text
missing -> UNVERIFIED
SKIP    -> UNVERIFIED
```

The real failed generated-backend evidence intentionally keeps a blocking gate.

## Authority semantic split

Artifacts:

```text
experiments/cabinet-vault/cabinet_authority_contract_v0.yaml
tests/test_cabinet_authority_contract.py
tests/test_cabinet_authority_manifest.py
```

Durable authority semantics now include:

```text
principal identity and trust-boundary separation
credential-class non-interchangeability and revocation meaning
exact capability authorization
exact resource scope authorization
host-bound actor/delegation provenance
explicit effect authority
default-deny disclosure authority
append-only audit meaning
```

The following remain generic host mechanisms/lowering rather than Cabinet
semantic identity:

```text
PostgresAccessControlBackend
PostgreSQL
Argon2id
verifier/throttle/session storage
Linux administration command shape
HTTP / MCP / IPC transport choice
```

Open authority questions remain explicit:

```text
AUTH-OQ-001
  smallest generic grant representation across independent boxes

AUTH-OQ-002
  split between generic audit-event vocabulary and Cabinet capability-specific
  event meaning
```

Do not solve them by importing Cabinet role names into the generic host kernel.

## Generic host lowering — structural planner

Artifacts:

```text
experiments/cabinet-vault/generic_host_lowering_contract_v0.yaml
experiments/cabinet-vault/generic_host_profile_candidate_v0.yaml
tools/host_lowering_plan.py
tests/test_generic_host_lowering_contract.py
tests/test_host_lowering_plan.py
```

Planner rules:

```text
GHL-REL-001
GHL-PROJ-001
GHL-VERIFY-001
GHL-VERIFY-002
```

The lowering contract pins the reviewed planner source blob and names
conformance tests. `GHL-SEM-001` is deliberately not implemented by this
structural planner; it has no product-semantic mapping API.

The candidate profile resolves every host requirement of
`cabinet_backend_box_v0.yaml` to one provider and projects:

```text
pydantic
psycopg
```

Expected state:

```text
status = compiled
gaps = []
verification_gate = block
```

All candidate providers remain `UNVERIFIED`.

## Provider verification packets

Artifacts:

```text
experiments/cabinet-vault/generic_host_provider_verification_v0.yaml
tests/test_host_provider_verification.py
```

Packets now exist for:

```text
authority_kernel
typed_schema_kernel
postgres_record_kernel
local_private_byte_vault
protected_configuration_kernel
```

Each packet covers exactly the requirements its profile provider claims and
carries the same runtime dependency declaration.

Important proof obligations include:

```text
authority_kernel
  AUTH-PROBE-001..008

typed_schema_kernel
  invalid input before effect
  closed-schema extra-field rejection
  invalid output before disclosure/settlement
  dependency: pydantic

postgres_record_kernel
  dependency: psycopg
  atomic commit/rollback
  exact-resource locking
  no partial metadata state
  append-only audit persistence

local_private_byte_vault
  opaque host-owned paths
  stage/reopen/hash verification
  conflict exclusion
  atomic publication/recovery
  readiness block on unresolved recovery
  symlink/device/non-regular escape rejection

protected_configuration_kernel
  required secret absence blocks readiness
  secrets never enter caller-visible data/audit
  configuration references do not become business data
```

Every probe is currently:

```text
UNVERIFIED
```

Guards require:

```text
PASS probe -> executed=true + recorded evidence
provider PASS -> every required packet probe PASS
```

Do not promote profile status manually.

## Current runtime boundary

Declarative architecture has reached the point where the next advancement requires
**a concrete provider implementation and executed runtime evidence**.

Do not build capability execution and call it verified while providers are only
candidate/UNVERIFIED. That would repeat the failure mode this experiment is meant
to remove.

The best first concrete provider is `postgres_record_kernel` because it directly
exercises the previously lost `psycopg` projection plus transaction and locking
obligations. `local_private_byte_vault` is the natural second provider for the
real `invoice.source.attach` capability.

## Executed evidence status

Historical evidence from 2026-08-20 remains:

```text
experiment suite: 53 passed
built-in adversarial mutation/audit: 3 passed
box language CLI audit: pass, 15 rules, 0 findings
```

Those results predate the newest boundary, authority, host-lowering, provider
packet, and PlanActual changes.

Branch workflow:

```text
.github/workflows/cabinet-vault-experiment.yml
```

It is configured to run the focused box/Cabinet/PlanActual/authority/host tests,
box-language audit, boundary audit, and candidate host plan. It asserts that the
old generated backend and the candidate host plan remain fail-closed.

This connector session has not obtained a completed push-triggered Actions run
result. Therefore the newest changes are **not recorded as PASS yet**. Workflow
configuration is not execution evidence.

## PlanActual status

Read:

```text
examples/cabinet-backend/01_models_plan_actual_monetary_gap.md
examples/cabinet-backend/02_rules_plan_actual_semantic_gap.md
examples/cabinet-backend/03_open_questions.md   # OQ-008
PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md
```

The former aliases:

```text
EstimateItemSnapshot.total
InvoiceLine.total
```

are no longer accepted as closed monetary semantics. PresuPro has no proved
single canonical per-item total for this purpose; Invoice Card V1 has no
`InvoiceLine.total` and exposes distinct `net_amount` and `gross_amount` bases.

State 2 monetary semantics are:

```text
REOPENED
```

Quantity semantics remain accepted.

Open business decisions:

```text
PA-MONEY-001
  authoritative planned item amount + exact monetary/tax basis

PA-MONEY-002
  actual Invoice Card V1 comparison meaning: net_amount or gross_amount

PA-MONEY-003
  direct comparability or explicit accepted conversion evidence
```

No answer has been invented. Derivability remains intentionally unresolved until
explicit source/target meaning is accepted.

## Immediate next work

Do not return to generated classical backend repairs.

Proceed in this order:

1. **Implement one concrete generic provider, starting with
   `postgres_record_kernel`.**
   It must be generic host code, not a Cabinet repository/UoW/service class.

2. **Execute its verification packet.**
   At minimum prove `psycopg` availability in the selected runtime, atomic
   commit/rollback, exact-resource locking, no partial state after failure, and
   append-only audit persistence. Record real evidence before changing provider
   status.

3. **Implement and verify `local_private_byte_vault`.**
   This provides the second half needed for a real `invoice.source.attach` host
   path.

4. **Only after required providers pass**, compile and execute one real
   archive/source capability from `cabinet_backend_box_v0.yaml` without
   reintroducing service/repository/router ownership.

5. Resolve AUTH-OQ-001/AUTH-OQ-002 only as needed for generic provider contracts,
   without leaking Cabinet role names into the host kernel.

6. Resolve PA-MONEY-001..003 only through an explicit Cabinet product decision;
   after acceptance require the unchanged derivability compiler to close both
   monetary mappings before implementing full monetary PlanActual.

7. Later define the minimum prepare/execute/observe/settle protocol for external
   effects using Holded as the adversarial case and classify local/VPS topology.

## Stop conditions

Stop and report a semantic/architectural gap instead of adding code when:

- a generated stub requires a product-specific external client inside Cabinet;
- a deterministic compiler/host decision has no declared machine rule;
- a mapping requires choosing meaning from field names or types alone;
- principal, credential, scope, disclosure, audit, or effect meaning is absent;
- required verification cannot run or has not produced evidence;
- provider status would become `PASS` without executed provider evidence;
- fixing generated code would merely encode a decision absent from the durable
  specification;
- PA-MONEY-001..003 are unresolved and code would have to choose monetary meaning.

## Success criterion

The experiment succeeds when Cabinet's durable definition becomes substantially
smaller than the classical application specification while preserving all real
Cabinet data, authority, policy, invariants, effects, and provenance, and when
all remaining application/lowering structure is either generically declared and
proved or disposable derivation rather than hidden product architecture.
