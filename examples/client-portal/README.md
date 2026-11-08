# Client Portal

## Purpose

Client Portal is a separate client-facing application for one renovation
project. A portal session always operates in the context of one Registry
`project_id` and presents the client with budget, expense, payment, work
progress, and photo information for that project.

## Layout (migration of 2026-11-06, `open_questions.md` Q15)

This case is being migrated to the current Workbench authoring standard. The
design states move one at a time; a state not yet migrated is still in the
former layout under `spec/`.

| path | content |
|---|---|
| `SOURCE.md` | which text is authoritative, the accepted Factory spec the migration carries, classified evidence |
| `00_product.md` | State 0, product frame (migrated) |
| `01_models.md` | State 1, domain models (migrated) |
| `02_rules.md` | State 2, rules and invariants (migrated) |
| `30_modules.md`, `30_trace.json` | State 3, module responsibilities and the A1–A32 ownership trace (migrated) |
| `40_flows.md`, `40_flow_plan.json` | State 4, reviewed flows and their plan (migrated) |
| `50_public_apis.md`, `50_api_plan.json`, `50_exposure_plan.json` | State 5, public module operations, their plan and HTTP exposure (migrated) |
| `60_data_closure.json`, `60_contract_plan.json`, `60_contracts.json`, `60_exception_taxonomy.json` | State 6, pre-contract data closure, contract plan, exact contracts and the ownership of exceptions without a constructor contract (migrated) |
| `70_router_closure.json`, `70_router_context.json`, `70_persistence_closure.json` | post-contract deterministic closures: HTTP routes, router wiring/auth/error policy, persistence backend IR |
| `65_imports.json`, `70_sqlite_unit_of_work_closure.json` | imports closure (`imports.module_internal` is its projection) and the SQLite unit-of-work backend IR |
| `80_notes.md` | State 7, notes (migrated; question rounds closed 2026-11-07) |
| `questions/` | question rounds |
| `spec/80_assembly.md`, `spec/HANDOFF.md` | State 8: the current assembly verification, admission and open items (2026-11-07) |
| `baseline/01_product_boundary.md` … `baseline/09_notes.md` | the frozen requirements baseline the authoring pass started from; input, not design |
| `spec/invariant_ledger.json` | the invariant ledger of 2026-07-19, kept as evidence; the current statements are the `Formal invariants` of `02_rules.md`, which narrowed INV-001, INV-003, INV-004, INV-014 and removed INV-010…INV-013, INV-016 with the email challenges (R0-23) |
| `open_questions.md` | the owner's open questions Q1–Q19 |
| `global_spec.json` | the assembly of 2026-07-19; superseded by the accepted Factory spec (`SOURCE.md`) and replaced when State 8 is reached again |

The next phase is `python tools/design_authoring_next.py examples/client-portal`
on this branch. `tools/authoring.py next client-portal` still resolves the
former canonical ref `product-decisions-and-reassembly` until
`PROJECT_INDEX.json` names `agent/client-portal` (a change on `main`).
