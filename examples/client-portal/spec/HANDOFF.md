# Handoff — Client Portal (current)

Replaces the handoff of the authoring pass of 2026-07-19 (its key decisions
are carried into the states that own them, `SOURCE.md`). State of
`agent/client-portal` on 2026-11-07 at `0411761c`, checked against the
Factory checkout at `5a3bdec2`; the assembly result is `80_assembly.md`.

## Where the case stands

- States 0–7 migrated; the clock source (SPEC_STANDARD §6.9 version 5) and the
  model closure have landed together (`SOURCE.md`, "one clock source").
- Assembly ready: 15/15 checks, 0 errors (identity 160 → 0, closure gaps
  44 → 0, witness 14 → 0).
- Revision diagnosis (`tools/design_diagnose.py`): every state 0 open; time
  wall closed (81 requirements, 0 without a source), elapsed closed (1, 0);
  Factory validator 0 errors.
- Imports closure ready (195/195 scopes, strict).
- Question rounds closed for States 0, 1, 3, 4, 5 and 7. **State 2 is open
  and cannot be asked** (Workbench gap below); `tools/authoring.py next
  client-portal` stops at `state2_rules_decisions`.

## Factory admission (`tools/design_factory_admission.py --update-existing`)

| check | result | owner |
|---|---|---|
| FA001, FA003, FA004, FA005, FA007, FA008, FA009, FA010, FA012, FA014, FA016, FA017, FA018, FA022 | PASS | — |
| FA006, FA011, FA013, FA020, FA021 | not applicable | — |
| FA019 | BLOCK: State 2 rounds open (14 units) | Workbench gap below |
| FA002 | BLOCK: no Stage 8.1 ledger | after State 2 closes (slices must be final) |
| FA015 | BLOCK: Factory Spec Inspector, 10 `module_type_surface_incomplete` | imports owner, below |

FA007 passes only with `--update-existing` (an export replaces the accepted
spec; the export itself is not part of this pass).

## Workbench gap: the State 2 round does not fit the provider

`design_questions.py ask --state 2` fails before any review: the Codex
provider refuses an input above 1,048,576 characters; the round's is
1,229,851 (instruction 1,015,608, almost all of it binding materials; texts
214,243). The scope is 21 units (the 14 open, plus A6, A12, A30, A31 and three
text units that reference changed decisions). `design_decision_witness`
`binding_material` gives every `[witness: …]` tag its check files in full,
so one file is repeated once per binding: 1.09M characters of materials hold
509k of distinct files (25). `MATERIAL_LIMIT` caps one binding (60k); nothing
caps or deduplicates the round. The case cannot shorten this honestly: the
bindings are true, and merging the new items per check (already done) saved
only 126k. Needed from the Workbench (`tools/questions_workbench/prompts.py`
`_materials`, or `binding_material`): each file once per round by digest, and
an input budget that splits the units over several reviews. Until then State 2
stays open and FA019 blocks.

## Witness bindings (State 2, identifier form)

Each check was read at Factory `5a3bdec2` and run green there.

| check | binds | coverage |
|---|---|---|
| `registry_linkage_client_portal` | PLAT-REG-004 (A4); PLAT-REG-001, PLAT-REG-002, PLAT-REG-007 (A5); INV-054, INV-055 (A15) | full |
| `viewer_credential_reissue_client_portal` | INV-008 (A11) | full |
| `expense_recognition_projection_client_portal` | INV-031 (A7) | full |
| `progress_manual_value_client_portal` | INV-040 (A20) | full |
| `budget_derivation_client_portal` | INV-026, INV-027, INV-028 (A18); INV-050 (A21) | full |
| `budget_derivation_client_portal` | INV-044 (A9) | **partial** |

INV-044 partial: the check shows the negative remaining, completion `None`
for a section without progress and the unconfigured views, but records
without asserting that such a section's `completed_work_value` reads 0 (the
budget view types it as a non-optional `Decimal`). Whether that is "missing
data replaced by zero" (INV-044) is a decision of A9 and the State 1 view
model, for the owner; the running service is unchanged.

## Other open items

- FA015: the Factory Spec Inspector requires a module importing `append_audit`
  to import `AuditRepository` too (nine modules), and `staff_bootstrap_cli`
  `StaffBootstrapPort`; the Workbench imports gate accepts the current table.
  Same 10 findings as before this pass. Owner: imports closure (decide the
  type uses), or the Factory/Workbench rule discrepancy.
- On the live code the Factory time-source gate blocks under
  `rules.time_source_policy` until the next Route B regenerates the consumers
  (they still read the host clocks; `65_imports.json` marks the 45 uses
  `code_outdated`).
- Stage 8.1: every one of the 37 modules has 0 blocks and 0 review prompts;
  no ledger is written until State 2 closes, since a State 2 fix may change
  the slices.
