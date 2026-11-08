# State 8 — assembly of `global_spec.json` (current output)

Replaces the State 8 text of the authoring pass of 2026-07-19. Generated on
2026-11-08 from Workbench `agent/client-portal` at `3876e1bc` with the Factory
checkout `code_factory_cp_witnesses` at origin/main `5a3bdec2`. The assembled
file is `../global_spec.json`; it equals its deterministic projection
(`design_spec_projection.py --verify`, admission FA016), and its notes equal
`../80_notes.md` (1090).

## Assembly verification (`tools/design_assembly.py examples/client-portal`)

```text
Assembly verification: 15/15 checks ready; 0 errors; 0 warnings; ready=true
language: ready=true errors=0 warnings=0
modules: ready=true errors=0 warnings=0
identity: ready=true errors=0 warnings=0
fields: ready=true errors=0 warnings=0
data: ready=true errors=0 warnings=0
contracts: ready=true errors=0 warnings=0
external_contracts: ready=true errors=0 warnings=0
notes: ready=true errors=0 warnings=0
closure_gaps: ready=true errors=0 warnings=0
router: ready=true errors=0 warnings=0
persistence: ready=true errors=0 warnings=0
witness: ready=true errors=0 warnings=0
imports: ready=true errors=0 warnings=0
flows: ready=true errors=0 warnings=0
factory: ready=true errors=0 warnings=0
```

Unchanged by the INV-044 change of 2026-11-08 (`completed_work_value`
`Decimal | None`; the three re-written notes re-confirmed in the imports
closure). Against the output before 2026-11-07 (`451ea6de`): identity 160 → 0 (model closure,
32 State 1 models, 64 `contract_only`), closure_gaps 44 → 0 (clock source
`system_clock_backend/v5`, with Workbench #155 for the timestamp the viewer
entry endpoint receives from `enter_viewer_access`), witness 14 → 0 (five new
Factory checks bound; INV-044 only partially, `HANDOFF.md`).

## Revision diagnosis (`tools/design_diagnose.py --factory-root`)

Not re-run on 2026-11-08. On 2026-11-07: every state 0 open. Time · wall: closed, 81 requirements, 0 without a source.
Time · elapsed: closed, 1 requirement, 0 without a source. Factory spec check:
0 errors, time part closed. Factory code check: not checked (no code given);
on the live code it blocks until the next Route B.

## Imports closure (`tools/design_imports.py --coverage`)

195/195 scopes decided, 0 pending, 0 stale, code evidence available,
handoff_ready=true, strict_ready=true.

## Stage 8.1 module review (`tools/design_module_review.py --review`)

Not run on 2026-11-08 (coordinator: Stage 8.1 ledger and admission skipped
until the rounds are cut down). On 2026-11-07: 37 modules, each 0 blocks and
0 review prompts; no ledger (admission FA002).

## Question rounds

On 2026-11-08 only State 2 rounds were run (coordinator). State 0 closed.
State 2 open (17 units, the coverage gaps of `HANDOFF.md`; three blocking
rounds 79-81, stopped by the ping-pong rule); its transition is not ready
(`witness_material`, 52 partial verdicts). Reopened by the INV-044 change
and not asked: State 1 (`Projections and answers`, one clear review of two),
States 3 and 4 (`context`), State 5 (`build_budget_view`,
`build_progress_view`, `context`), State 7 (`financial_policy`,
`derived_views`).
