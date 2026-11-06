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
| `spec/10_models.md` … `spec/80_assembly.md`, `spec/invariant_ledger.json`, `spec/HANDOFF.md` | States 1–8 of the authoring pass of 2026-07-18/19, not yet migrated |
| `baseline/01_product_boundary.md` … `baseline/09_notes.md` | the frozen requirements baseline the authoring pass started from; input, not design |
| `open_questions.md` | the owner's open questions Q1–Q16 |
| `global_spec.json` | the assembly of 2026-07-19; superseded by the accepted Factory spec (`SOURCE.md`) and replaced when State 8 is reached again |

The next phase is `python tools/design_authoring_next.py examples/client-portal`
on this branch. `tools/authoring.py next client-portal` still resolves the
former canonical ref `product-decisions-and-reassembly` until
`PROJECT_INDEX.json` names `agent/client-portal` (a change on `main`).
