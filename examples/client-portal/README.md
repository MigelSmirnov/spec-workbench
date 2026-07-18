# Client Portal Requirements Baseline

## Purpose

Client Portal is a separate client-facing application for one renovation
project. A portal session always operates in the context of one Registry
`project_id` and presents the client with budget, expense, payment, work
progress, and photo information for that project.

The documents in this directory form one technical assignment split by topic.
They are requirements input for a future specification-authoring pass; they
are not an assembled specification and do not define implementation.

## Current baseline

- Registry already provides a reliable boundary for project identity,
  validation, and current project context.
- PresuPro currently provides an editable estimate and calculated totals, but
  not a published immutable budget suitable for Client Portal.
- A manually entered portal budget is temporarily allowed for the MVP.
- An approved PresuPro snapshot is a future source and is explicitly marked
  unavailable wherever it is referenced.
- An approved presupuesto is not a factura. Their detailed lifecycle
  relationship remains unresolved.

## Maturity

The product requirements and external facts are recorded. Formal domain
design, invariant landing, module design, exact contracts, behavioral notes,
Factory assembly, and compatibility verification are separate future work.
No `global_spec.json` belongs in this requirements baseline.

## Navigation

- [Product boundary](01_product_boundary.md)
- [External boundaries](02_external_boundaries.md)
- [Business entities](03_domain_models.md)
- [Business rules and invariants](04_rules_and_invariants.md)
- [Product responsibility areas](05_module_responsibilities.md)
- [User and integration flows](06_system_flows.md)
- [Required external capabilities](07_public_apis.md)
- [Business contracts](08_contracts.md)
- [Cross-cutting requirements notes](09_notes.md)
- [Open questions](open_questions.md)

## Future specification work

Another authoring pass must use these documents in methodology order, resolve
the recorded open questions with the product owner, and only then design the
formal models, APIs, contracts, notes, and `global_spec.json`.
