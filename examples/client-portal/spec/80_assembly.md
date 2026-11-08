# State 8 — assembly of `global_spec.json` (current output)

Generated on 2026-11-08 (evening, after the email-challenge sweep) from
Workbench `agent/client-portal` at `22df7e39`, with the clean Factory
checkout `code_factory_cp_witnesses` at origin/main `9409b8e2` (#190 merged,
accepted `018b2e2e`) (`SPEC_WORKBENCH_FACTORY_ROOT`). `global_spec.json`
sha256 `cbcc75374b82a3ffda85edb4a933275dc3844572a78bc5f3e83a843ab3caf9ef`. The assembled file is `../global_spec.json`.
It equals its deterministic projection (`design_spec_projection.py
--verify`, admission FA016), and its notes equal `../80_notes.md` (1090).
`tools/authoring.py next client-portal` stops at `state8_assembly`: every
earlier state is closed on its current texts.

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

## State 8 transition (`tools/transition.py --phase state8_assembly`)

`ready=true`: 1 check, 0 blocking, 1 carried. `witness_material` carries 54
`witness_assertion_carried` (Factory checks that assert their item's
invariants only in part) to Factory verification,
MigelSmirnov/code-factory#189 (`90_factory_target.json`
`factory_checks_issue`). Verdicts (`design_questions.py judge-checks`): 69
bindings, 15 asserts, 54 partial, 0 does_not, 0 not_checked.

## Imports closure (`tools/design_imports.py --coverage`, strict)

195/195 scopes decided, 0 pending, 0 stale, code evidence available,
handoff_ready=true, strict_ready=true. Since 2026-11-08 the closure carries
the type imports the Factory slicer and Spec Inspector need (FA015):
`AuditRepository` in the nine modules that call `append_audit`, and
`StaffBootstrapPort` with `AuditRecord` (the port operation's signature) in
`staff_bootstrap_cli`. Each is an `annotates` use.

## Stage 8.1 module review (`tools/design_module_review.py --review`)

37 modules, each 0 deterministic blocks. Ledger
`../81_module_review_status.json`: closed, 37/37 PASS, slice hashes current
(refreshed after the sweep: content changed in `staff_identity` only, which
rests on State 7 round 20; the other 36 by decision line numbers).
The 19 model-generated modules rest on their State 7 round on the current
generation prompt. The 18 emitted modules rest on their emitter IR and the
assembly. No separate per-module adversarial review was run.

## Stage 9 admission (`tools/design_factory_admission.py --update-existing`)

Factory read: `code_factory_cp_witnesses` (clean, `9409b8e2`); the main
`code_factory` checkout was not used. Status `READY_TO_EXPORT`: 22 checks,
17 PASS, 5 NOT_APPLICABLE, 0 BLOCK, 0 WARN.

| check | result |
|---|---|
| FA001 | PASS — Workbench source committed and clean |
| FA014 | PASS — case pinned to `client_portal_sandbox` |
| FA002 | PASS — Stage 8.1 closed, every slice hash current |
| FA003 | PASS — assembly ready |
| FA004 | PASS — SPEC_STANDARD.md and SPEC_STANDARD_INDEX.md byte-identical |
| FA009 | PASS — supported SPEC_STANDARD revision |
| FA020 | NOT_APPLICABLE — every Factory accepts standard_version 2 |
| FA021 | NOT_APPLICABLE — no standard backend owning a fixed function set |
| FA010 | PASS — implementation obligations cover every interface dependency |
| FA013 | NOT_APPLICABLE — no master persistence needing a backend closure |
| FA017 | PASS — no opaque carrier; every lowered repository reachable |
| FA011 | NOT_APPLICABLE — no verified external-contract evidence |
| FA012 | PASS — closure-gap fuses clean |
| FA016 | PASS — `global_spec.json` equals its projection |
| FA022 | PASS — imports decided, `module_internal` is the projection, code agrees |
| FA005 | PASS — Factory canonical validator accepts the spec |
| FA015 | PASS — Factory Spec Inspector accepts the spec (was 10 `module_type_surface_incomplete`) |
| FA018 | PASS — every module cut, no induced import collision, every changed address reaches a module |
| FA019 | PASS — every state with a question round closed unit by unit |
| FA006 | NOT_APPLICABLE — no semantic runtime-test handoff |
| FA007 | PASS — replacement of the existing canonical spec authorized |
| FA008 | PASS — Factory toolchain clean and fingerprinted |

## Revision diagnosis (`tools/design_diagnose.py --factory-root --code-root`)

`--case examples/client-portal --factory-root code_factory_cp_witnesses
--code-root code_factory_cp_witnesses/projects/client_portal_sandbox`:

- States 1, 2, 3, 4, 6, 7, the data closure, the deterministic closures,
  the imports closure, Stage 8 and Stage 9: 0 open each.
  `witness_material` is carried (54).
- Time: wall closed, 81 requirements, 0 without a source; elapsed closed,
  1 requirement, 0 without a source.
- Factory spec check: 0 errors, time part closed.
- Factory code check: open, 46 findings. The live code predates the clock
  source: `authority_module_missing` (`system_clock` is absent from the
  scanned tree), and `clock_dependency_bypassed` in the modules that still
  read `datetime.utcnow()` themselves. The findings close with the next
  Route B; they are not spec findings.

## Export

```bash
cd /home/smirnov/jestor_VBC/exp_vbc/demo/spec-workbench-worktrees/client-portal-migration
SPEC_WORKBENCH_FACTORY_ROOT=/home/smirnov/jestor_VBC/exp_vbc/demo/code_factory_cp_witnesses \
python tools/export_to_factory.py --case client-portal \
  --project client_portal_sandbox \
  --factory-root /home/smirnov/jestor_VBC/exp_vbc/demo/code_factory_cp_witnesses \
  --update-existing
```

The same command with `--check` runs the admission gate without writing.
#190 exported `018b2e2e`. The sweep is exported with `--factory-root` the
worktree `code_factory_cp_export2` (branch
`spec/client-portal-staff-auth-note` from origin/main `9409b8e2`); merge is
the owner's. No Route B or deploy was run.
