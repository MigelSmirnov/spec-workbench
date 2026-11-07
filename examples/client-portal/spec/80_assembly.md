# State 8 — assembly of `global_spec.json` (current output)

Replaces the State 8 text of the authoring pass of 2026-07-19. Generated on
2026-11-07 from Workbench `agent/client-portal` at `451ea6de` with the Factory
checkout `code_factory` main `cc1910be`. The assembled file is
`../global_spec.json`; it equals its deterministic projection
(`design_spec_projection.py --verify`, admission FA016).

## Assembly verification (`tools/design_assembly.py examples/client-portal`)

```text
Assembly verification: 12/15 checks ready; 218 errors; 0 warnings; ready=false
language: ready=true errors=0 warnings=0
modules: ready=true errors=0 warnings=0
identity: ready=false errors=160 warnings=0
fields: ready=true errors=0 warnings=0
data: ready=true errors=0 warnings=0
contracts: ready=true errors=0 warnings=0
external_contracts: ready=true errors=0 warnings=0
notes: ready=true errors=0 warnings=0
closure_gaps: ready=false errors=44 warnings=0
router: ready=true errors=0 warnings=0
persistence: ready=true errors=0 warnings=0
witness: ready=false errors=14 warnings=0
imports: ready=true errors=0 warnings=0
flows: ready=true errors=0 warnings=0
factory: ready=true errors=0 warnings=0
```

What stays open, by owner:

- `identity` (160): no `60_model_closure_*.json` in the case (State 1 owns the
  models; the closure is written with State 6). A validated closure exists but
  lands only together with the clock source, because alone it turns the State 6
  time-source check from not checked into 35 open findings (`HANDOFF.md`).
- `closure_gaps` (44): 35 `fresh_timestamp_without_source` and 9
  `ambient_time_note`; the operations read the time themselves (coordinator
  decision of 2026-11-06, `SOURCE.md`). Closed by the clock source of
  SPEC_STANDARD §6.9 version 5 except one finding the Workbench cannot close
  (`HANDOFF.md`, workbench gap).
- `witness` (14): A7, A15, A20, A32 have no witness tag; PLAT-REG-002,
  PLAT-REG-004, PLAT-REG-007 (A4, A5), INV-044 (A9), INV-008 (A11) and INV-028
  (A18) have no Factory check that asserts them; INV-026, INV-027 (A18),
  INV-050 (A21) and PLAT-REG-001 (A5) only partially (State 2 round-76).

## Imports closure (`tools/design_imports.py --coverage`)

195/195 scopes decided, 0 pending, 0 stale, code evidence available,
handoff_ready=true, strict_ready=true.

## Stage 8.1 module review (`tools/design_module_review.py --review`)

Not reachable in the sequence while the assembly is not ready; run for
information on every one of the 36 modules: 0 blocks and 0 review prompts each.
No ledger is recorded (admission FA002).

## Question rounds

States 0, 1, 2, 3, 4, 5 and 7 closed on their current texts (admission FA019).
