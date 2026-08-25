# Generated Cabinet Backend — boundary audit result

## Status

The bounded classification pass requested by `NEXT_SESSION_HANDOFF.md` is now
implemented on `agent/cabinet-vault-experiment`.

This is an architecture audit, not a repair of the failed generated classical
backend.

The failed generated backend remains **UNVERIFIED**. Known failed or skipped
evidence is intentionally not converted into a green result.

## Artifacts

```text
experiments/cabinet-vault/tools/cabinet_boundary_audit.py
experiments/cabinet-vault/generated_backend_failure_evidence_v0.yaml
tests/test_cabinet_boundary_audit.py
experiments/cabinet-vault/generic_host_lowering_contract_v0.yaml
tests/test_generic_host_lowering_contract.py
.github/workflows/cabinet-vault-experiment.yml
```

The audit consumes explicit finding classes. It does not infer architecture from
product names, file names, field names, or stub names.

## Three dispositions

The handoff classes now map deterministically to the three architectural buckets.

| Finding class | Disposition |
| --- | --- |
| `BOUNDARY_LEAK` | remove from Cabinet product specification |
| `LANGUAGE_RELATION_GAP` | generic host/lowering contract |
| `PROJECTION_GAP` | generic host/lowering contract |
| `VERIFICATION_NOT_EXECUTED` | generic host/lowering contract |
| `LOWERING_GAP` | generic host/lowering contract |
| `AUTHORITY_SEMANTIC_GAP` | keep and close in Cabinet semantic specification |
| `DOMAIN_SEMANTIC_GAP` | keep and close in Cabinet semantic specification |

The classifier does not repair any finding. It states where the repair is owned.

## Representative failed-run evidence

The evidence manifest records the bounded failures called out in the handoff:

- missing machine relation between an interface port and its concrete selected
  implementation;
- lost `psycopg` dependency projection;
- skipped required semantic/runtime verification;
- concentrated stubs at Holded, Synchronization, VPS, and HTTP boundaries;
- audit/principal/credential construction mismatches;
- unresolved PlanActual domain methods;
- unresolved RetentionRelease domain methods.

These observations remain diagnostic evidence. They are not a generated-code
backlog.

## Verification semantics

The audit distinguishes classification success from backend verification.

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

The aggregate verification gate passes only when every required probe is `PASS`.

The real failed-run evidence therefore produces a blocking verification gate by
design. A successfully executed audit must not make the old backend appear
verified.

## Generic host/lowering result

`generic_host_lowering_contract_v0.yaml` extracts only reusable mechanism
obligations demonstrated by the failed run:

- machine-declared selected implementation relations;
- dependency-closed lowering projection;
- fail-closed verification semantics;
- prohibition on generic lowerings choosing missing product meaning.

The contract also lists reusable host primitives such as transaction/locking,
record persistence, blob custody, schema validation, authentication, grant
enforcement, audit persistence, transport exposure, and startup recovery.

It has no Registry, PresuPro, Holded, or VPS dependency.

The existing `box_language_v0.yaml` was deliberately not expanded to pretend that
a host-lowering compiler already implements these contracts. The box language
continues to describe the currently implemented derivability/composition rules.

## Boundary-leak result

The Holded/Synchronization/VPS/HTTP stub concentration is classified as
`BOUNDARY_LEAK`.

Disposition:

```text
remove product-specific external client/transport ownership from Cabinet box
```

Do not fill these generated stubs merely to make the classical backend execute.
Cabinet should retain only its local semantic/evidence side of a cross-authority
operation; external capability execution is composed independently.

## Authority result

Generated audit/principal/credential mismatches are classified as
`AUTHORITY_SEMANTIC_GAP`.

Disposition:

```text
keep and close principal / credential / grant / scope / disclosure / audit / effect
semantics in the durable Cabinet box/host contract
```

These decisions must not be repaired by constructor coercion or transport code.

## Domain result — PlanActual

The monetary PlanActual issue was traced back to the owning design state.

New/updated design-state artifacts:

```text
examples/cabinet-backend/01_models_plan_actual_monetary_gap.md
examples/cabinet-backend/02_rules_plan_actual_semantic_gap.md
```

The State 2 monetary decision is now **REOPENED** because later source probes
proved that its old aliases were not source-contract facts:

```text
EstimateItemSnapshot.total
InvoiceLine.total
```

No replacement meaning was invented.

Open business decisions are now explicit:

```text
PA-MONEY-001 authoritative planned item amount + basis
PA-MONEY-002 Invoice Card V1 net_amount or gross_amount
PA-MONEY-003 comparability / explicit conversion evidence
```

Quantity semantics remain accepted. Full monetary PlanActual analysis fails
closed until these decisions are accepted and the unchanged derivability compiler
proves the selected source meanings.

The planned and actual amount target manifests now reference the reopened State 2
decision and State 1 refinement rather than describing the old aliases as an
accepted rule.

## CI / execution evidence

A branch-specific GitHub Actions workflow now exists at:

```text
.github/workflows/cabinet-vault-experiment.yml
```

It is configured to run the Cabinet/box/derivability focused tests, enforce the
box-language audit, and execute the generated-backend boundary audit expecting a
blocking verification result for the failed backend evidence.

At the time this document was written, this connector session had not obtained a
completed GitHub Actions run result. Therefore no new test suite is recorded here
as `PASS` yet.

This is intentional evidence discipline: workflow configuration is not execution
evidence.

## Next implementation work

1. Obtain executed CI evidence for the new audit/host-contract/derivability guards.
2. Keep external product/transport code outside the Cabinet semantic boundary.
3. Use `generic_host_lowering_contract_v0.yaml` when implementing the first real
   generic host lowering; do not hide implementation-relation or dependency
   projection rules in Python.
4. Close Cabinet authority semantics before trusting generated authority code.
5. Resolve PA-MONEY-001 through PA-MONEY-003 only from an explicit Cabinet
   business decision and factual source-contract evidence.
6. After that decision, update only the target/source semantic manifests needed
   for the selected meanings and require the unchanged derivability compiler to
   close both mappings.
7. Only then implement the full deterministic monetary PlanActual calculation.
