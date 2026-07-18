# Client Portal Workbench Case

## Purpose

This directory is the design-state workspace for Client Portal, a
client-facing view of an existing renovation project. It preserves agreed
product boundaries and verified external-system facts before domain modeling
or implementation design begins.

## Current maturity

**Status:** Bootstrap complete; iterative design has not started beyond the
agreed product boundary.

Completed inputs:

- State 0 product boundary;
- external boundary audit for Registry and PresuPro;
- Registry integration baseline suitable for local implementation work.

Not started:

- State 1 domain models;
- State 2 rules and invariants;
- State 3 module responsibilities;
- State 4 system flows;
- State 5 public module APIs;
- State 6 contracts and internal functions;
- State 7 behavioral notes and property candidates;
- State 8 assembly;
- State 9 Factory compatibility probe.

The numbered files after `02_external_boundaries.md` are design-state
placeholders. They record expected outputs only and contain no proposed
architecture.

## Design-state files

- [State 0 — Product Boundary](01_product_boundary.md)
- [External Boundaries](02_external_boundaries.md)
- [State 1 — Domain Models](03_domain_models.md)
- [State 2 — Rules and Invariants](04_rules_and_invariants.md)
- [State 3 — Module Responsibilities](05_module_responsibilities.md)
- [State 4 — System Flows](06_system_flows.md)
- [State 5 — Public Module APIs](07_public_apis.md)
- [State 6 — Contracts](08_contracts.md)
- [State 7 — Notes](09_notes.md)
- [Open Questions](open_questions.md)

## External relationships

Registry is the owner of project identity and current project context. Client
Portal may use Registry's typed read boundary and must not create or rewrite a
Registry `project_id`.

PresuPro owns editable presupuesto data and its calculations. It does not yet
provide an immutable, versioned, approved estimate snapshot suitable for
portal publication. Until that contract exists, the case records a temporary
manual-budget mode without treating current mutable PresuPro data or a Holded
factura payload as canonical portal input.

## Why this case stops before `global_spec.json`

The external boundaries are known, but the domain models, lifecycle rules,
module ownership, flows, APIs, contracts, and notes have not been designed in
methodology order. Generating `global_spec.json` now would require placeholder
models and invented behavior. Assembly remains intentionally blocked until the
preceding design states are complete and coherent.
