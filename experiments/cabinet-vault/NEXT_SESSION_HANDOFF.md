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

The central rule remains:

> Keep meaning durable. Treat everything provably derivable from that meaning as
> a cheap disposable compilation artifact.

And the compiler/host rule remains:

> Deterministic implementation may implement declared rules. It must not silently
> extend the language or choose missing product meaning.

## Latest completed architecture passes

Read first:

```text
GENERATED_BACKEND_BOUNDARY_AUDIT.md
GENERIC_HOST_LOWERING_RESULT.md
```

The old generated classical backend was not repaired.

### Generated-backend boundary audit

Implemented artifacts:

```text
tools/cabinet_boundary_audit.py
experiments/cabinet-vault/generated_backend_failure_evidence_v0.yaml
tests/test_cabinet_boundary_audit.py
```

The audit classifies failures into three dispositions.

Remove from Cabinet product specification:

```text
BOUNDARY_LEAK
```

Move to generic host/lowering:

```text
LANGUAGE_RELATION_GAP
PROJECTION_GAP
VERIFICATION_NOT_EXECUTED
LOWERING_GAP
```

Keep and close in Cabinet semantic specification:

```text
AUTHORITY_SEMANTIC_GAP
DOMAIN_SEMANTIC_GAP
```

Representative evidence includes the missing interface implementation relation,
lost `psycopg` projection, skipped required runtime/semantic verification,
external-boundary stub concentration, authority construction mismatches, and
unresolved PlanActual/RetentionRelease behavior.

Classification success is not backend verification.

## Verification remains fail closed

Use only:

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

The real failed generated-backend evidence intentionally keeps a blocking
verification gate.

## Authority semantic split

The accepted classical access-control design was separated into durable authority
meaning versus generic host mechanism.

Artifacts:

```text
experiments/cabinet-vault/cabinet_authority_contract_v0.yaml
tests/test_cabinet_authority_contract.py
tests/test_cabinet_authority_manifest.py
```

Durable Cabinet/box authority semantics now include:

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

The following are not Cabinet semantic identity:

```text
PostgresAccessControlBackend
PostgreSQL
Argon2id
verifier/throttle/session storage
Linux administration command shape
HTTP / MCP / IPC transport choice
```

These are host mechanisms/lowerings.

The archive box manifest is guarded so caller inputs cannot supply host-owned
authorization evidence, every protected capability declares grant/scope/effect/
disclosure/audit requirements, and effectful capabilities bind actor authority
from authenticated host context.

Two authority questions remain explicit rather than hidden:

```text
AUTH-OQ-001
  smallest generic grant representation across independent boxes

AUTH-OQ-002
  split between generic audit-event vocabulary and Cabinet capability-specific
  event meaning
```

Do not solve these by importing Cabinet role names into the generic host kernel.

## Generic host lowering — first structural plan

Artifacts:

```text
experiments/cabinet-vault/generic_host_lowering_contract_v0.yaml
experiments/cabinet-vault/generic_host_profile_candidate_v0.yaml
tools/host_lowering_plan.py
tests/test_generic_host_lowering_contract.py
tests/test_host_lowering_plan.py
```

The planner implements exactly these declared rules:

```text
GHL-REL-001
GHL-PROJ-001
GHL-VERIFY-001
GHL-VERIFY-002
```

The lowering contract pins the reviewed planner source blob and names
conformance tests. `GHL-SEM-001` is deliberately not declared implemented by the
planner: the planner has no field/domain semantic-choice API.

The candidate profile supplies one provider relation for every host requirement
of `cabinet_backend_box_v0.yaml` and explicitly projects:

```text
pydantic
psycopg
```

The expected structural result is:

```text
status = compiled
gaps = []
verification_gate = block
```

Every candidate provider remains:

```text
required = true
status = UNVERIFIED
```

Therefore structural compilation is not executable verification. Do not mark a
provider `PASS` by editing the profile; obtain executed evidence against a
concrete provider implementation.

## Executed evidence status

Historical evidence from 2026-08-20 remains:

```text
experiment suite: 53 passed
built-in adversarial mutation/audit: 3 passed
box language CLI audit: pass, 15 rules, 0 findings
```

Those results predate the newest boundary, authority, host-lowering, and
PlanActual changes.

A branch-specific GitHub Actions workflow exists at:

```text
.github/workflows/cabinet-vault-experiment.yml
```

It is configured to run the focused box/Cabinet/PlanActual/authority/host-plan
tests, the box-language audit, the boundary audit, and the candidate host plan.
It asserts both expected fail-closed states:

```text
old generated backend -> verification_gate = block
candidate host plan    -> verification_gate = block
```

This connector session still has not obtained a completed push-triggered Actions
run result. Therefore the newest changes are **not recorded as PASS yet**.
Workflow configuration is not execution evidence.

## PlanActual repair status

Read:

```text
examples/cabinet-backend/01_models_plan_actual_monetary_gap.md
examples/cabinet-backend/02_rules_plan_actual_semantic_gap.md
examples/cabinet-backend/03_open_questions.md   # OQ-008
PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md
```

The previous monetary decision used:

```text
planned_amount = EstimateItemSnapshot.total
actual_amount = InvoiceLine.total
```

Later factual probes proved those aliases are not closed source-contract facts:

- PresuPro has no single proved canonical per-item total for this purpose;
- Invoice Card V1 has no `InvoiceLine.total` and instead exposes distinct
  `net_amount` and `gross_amount` meanings with different bases.

The State 2 monetary decision is now:

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

No answer has been invented in this branch. Existing derivability tests remain
intentionally unresolved until explicit source/target meanings are accepted.

## Immediate next work

Do not return to generated classical backend repairs.

Proceed in this order:

1. **Obtain executed evidence for the branch guards when available.**
   A green workflow validates experiment tooling/guards only; it does not verify
   the old generated backend.

2. **Define provider verification packets, not more Cabinet service classes.**
   For each candidate host provider, specify the minimum executable evidence
   required to change its status from `UNVERIFIED` to `PASS`:

   ```text
   authority_kernel
   typed_schema_kernel
   postgres_record_kernel
   local_private_byte_vault
   protected_configuration_kernel
   ```

3. **Resolve AUTH-OQ-001 and AUTH-OQ-002 only as far as required by those
   verification packets.**
   Keep Cabinet role names and product workflow labels outside the generic host
   language.

4. **Prove one real archive/source capability through the generic host boundary.**
   Use `cabinet_backend_box_v0.yaml`; do not reintroduce service/repository/router
   ownership. The capability execution path may advance only after required
   provider relations, dependency projection, authority/effect/disclosure policy,
   and verification evidence are explicit.

5. **Resolve PlanActual monetary meaning only through an explicit Cabinet product
   decision.**
   Do not choose PA-MONEY-001..003 from field names, types, convenience, or
   adapter context. After acceptance, propagate the decision into semantic
   manifests and require the unchanged derivability compiler to close both
   mappings.

6. Only after monetary derivability closes, implement the full deterministic
   monetary PlanActual calculation over proved inputs.

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
- PA-MONEY-001..003 are still unresolved and code would have to choose a
  monetary meaning.

## Success criterion

The experiment succeeds when Cabinet's durable definition becomes substantially
smaller than the classical application specification while preserving all real
Cabinet data, authority, policy, invariants, effects, and provenance, and when
all remaining application/lowering structure is either generically declared and
proved or disposable derivation rather than hidden product architecture.
