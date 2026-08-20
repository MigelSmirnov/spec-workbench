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

## What was completed in the latest pass

The bounded generated-backend architecture probe requested by the previous
handoff is now implemented.

Read:

```text
GENERATED_BACKEND_BOUNDARY_AUDIT.md
```

Primary artifacts:

```text
tools/cabinet_boundary_audit.py
experiments/cabinet-vault/generated_backend_failure_evidence_v0.yaml
tests/test_cabinet_boundary_audit.py
experiments/cabinet-vault/generic_host_lowering_contract_v0.yaml
tests/test_generic_host_lowering_contract.py
.github/workflows/cabinet-vault-experiment.yml
```

The old generated classical backend was not repaired.

## Boundary audit result

The audit uses explicit finding classes and three deterministic dispositions.

### Remove from Cabinet product specification

```text
BOUNDARY_LEAK
```

Representative evidence:

```text
Holded / Synchronization / VPS / HTTP stub concentration
```

Interpretation:

```text
external product/transport responsibilities do not become Cabinet backlog
```

Do not fill these stubs merely to make the classical generated backend run.

### Move to generic host/lowering contract

```text
LANGUAGE_RELATION_GAP
PROJECTION_GAP
VERIFICATION_NOT_EXECUTED
LOWERING_GAP
```

Representative evidence:

```text
missing interface -> selected implementation relation
lost psycopg dependency projection
required semantic/runtime verification skipped
```

`generic_host_lowering_contract_v0.yaml` now declares the first reusable
obligations exposed by these failures:

```text
machine-declared selected implementation relation
dependency-closed lowering projection
fail-closed verification semantics
generic lowering must not choose missing product meaning
```

This contract is deliberately separate from `box_language_v0.yaml`.
The existing box language still describes the rules actually implemented by the
current derivability/composition compiler. Do not add host-lowering behavior to
Python first and document it later; that would recreate the hidden-rule problem.

### Keep and close in Cabinet semantic specification

```text
AUTHORITY_SEMANTIC_GAP
DOMAIN_SEMANTIC_GAP
```

Representative evidence:

```text
audit / principal / credential construction mismatches
PlanActual unresolved domain behavior
RetentionRelease unresolved domain behavior
```

These findings must return to the earliest owning semantic state rather than be
patched in generated constructors, adapters, handlers, or repository code.

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

The generated-backend evidence intentionally produces a blocking verification
gate. A successful classification audit does not verify the old backend.

## Executed evidence status

Historical evidence from 2026-08-20 remains:

```text
experiment suite: 53 passed
built-in adversarial mutation/audit: 3 passed
box language CLI audit: pass, 15 rules, 0 findings
```

Those results predate the newest boundary-audit, generic-host-contract, and
PlanActual semantic-repair changes.

A branch-specific GitHub Actions workflow now exists at:

```text
.github/workflows/cabinet-vault-experiment.yml
```

It is configured to execute the focused Cabinet/box/derivability tests,
`box_language_audit.py`, and the boundary audit while asserting that the failed
backend remains `UNVERIFIED`.

At this handoff, this connector session has not obtained a completed Actions run
result for the new workflow. Therefore the newest changes are **not recorded as
PASS yet**. Workflow configuration is not execution evidence.

## PlanActual repair status

The boundary audit traced the PlanActual failure back to its owning design state.

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

The State 2 monetary decision is therefore now:

```text
REOPENED
```

Quantity semantics remain accepted.

### Open PlanActual decisions

```text
PA-MONEY-001
  choose the authoritative planned item amount and exact monetary/tax basis

PA-MONEY-002
  choose the actual Invoice Card V1 comparison meaning:
  net_amount or gross_amount

PA-MONEY-003
  define direct comparability or explicit accepted conversion evidence
```

No answer has been invented in this branch.

The planned and actual target manifests now reference the reopened State 1/2
decision. The existing derivability tests intentionally remain unresolved until
an explicit semantic choice is supplied. They already prove that the unchanged
compiler closes a mapping when an authoritative source meaning / explicit target
meaning exists.

## Immediate next work

Do not return to generated classical backend repairs.

Proceed in this order:

1. **Obtain executed evidence for the new branch guards.**
   A green workflow may validate experiment tooling and semantic guards only; it
   still must not be described as verification of the old generated backend.

2. **Close the authority semantic contract before trusting generated authority
   code.**
   Inspect principal, credential, grant/resource scope, disclosure, audit-event,
   and allowed-effect semantics under the box/host split. Reuse accepted Cabinet
   semantics where they are genuinely closed; expose any remaining gap rather
   than coercing constructors.

3. **Keep generic lowering separate from product semantics.**
   When implementing the first reusable lowering compiler/runtime, start from
   `generic_host_lowering_contract_v0.yaml`. Make implementation relation,
   dependency closure, and verification rules machine-addressable and tested
   before deterministic code depends on them.

4. **Resolve PlanActual monetary meaning only through an explicit Cabinet product
   decision.**
   Do not choose PA-MONEY-001..003 from field names, types, convenience, or
   adapter context. When a decision is accepted, propagate it from State 1/2 into
   the target/source manifests and require the unchanged derivability compiler to
   close both mappings.

5. **Only after monetary derivability closes**, implement the full deterministic
   monetary PlanActual calculation over proved inputs.

6. Then continue toward compiling `cabinet_backend_box_v0.yaml` into a generic
   host IR/runtime and prove one real archive/source capability without permanent
   service/repository/router ownership.

7. Later define the minimum prepare/execute/observe/settle protocol for external
   effects using Holded as the adversarial case, and classify local/VPS topology.

## Stop conditions

Stop and report a semantic/architectural gap instead of adding code when:

- a generated stub requires a product-specific external client inside Cabinet;
- a deterministic compiler/host decision has no declared machine rule;
- a mapping requires choosing meaning from field names or types alone;
- principal, credential, scope, disclosure, audit, or effect meaning is absent;
- required verification cannot run or has not produced evidence;
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
