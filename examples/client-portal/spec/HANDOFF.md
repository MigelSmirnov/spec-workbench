# Handoff — Client Portal (current)

Replaces the handoff written before the export of 2026-11-08. State of
`agent/client-portal` on 2026-11-08 (evening) after the sweep for remnants
of the removed staff email challenges, checked against the clean Factory
checkout `code_factory_cp_witnesses` at origin/main `9409b8e2` (#190
merged: accepted spec `018b2e2e`). The assembly, admission and diagnosis
results are in `80_assembly.md`; the semantic diff, for the owner, is
`SEMANTIC_DIFF.md` (against `018b2e2e` first, then against `459ac96c`).

## Lost behaviours from the Route B verify of 071062af (2026-11-10, later) — read this first

#210 merged (spec `071062af`); Route B passed generation, linker and deploy;
verify triage (code-factory #214) found three spec gaps, restored in
`27fc1ab2`: expense view order (A27, `_project_expense_summary`),
`ScopedNotFoundError` from `build_progress_view`/`build_payment_view`
without an active version (INV-044, overview NOT_CONFIGURED), and
`issue_viewer_access` refusing a missing or revoked viewer before any write
(INV-008). With code-factory #211 `get_budget_version` is named in
`build_budget_view` (no induced import). State 7 r36 clear; Stage 8.1 39/39;
admission READY_TO_EXPORT 18/0/0 against Factory `97675d94`.
`global_spec.json` sha256 `43e2c70c…`.

## Cleanup after the Route B verify of b3bfb504 (2026-11-10)

Route B on `b3bfb504` generated, linked and deployed; verify failed on spec
causes (after the harness fix code-factory #208). Owner-approved cleanup,
Workbench main `cc7120cf` (#182 notes gate) merged, Factory checkout
`code_factory_cp_witnesses` at origin/main `784d834d` (#209). Not exported
here; see the export PR. `global_spec.json` sha256 `071062af…`.

- Repository methods: 46 DEPENDENCY_BOUNDARY notes name, per function and
  per repository, every repository method the accepted code calls ("MUST
  make its own reads/writes, wherever its other notes call for them, of the
  records the <Interface> holds through M of the <accessor> repository of
  that transaction ..."); naming the interface makes the Factory slicer
  import it and carry the named contracts (staff_identity 0 -> 12,
  derived_views gains the budget/expense/photo/section methods).
- Legacy surface: the 74 `PortalTransaction.get_*/list_*/insert_*/update_*/
  upsert_*` contracts and their 195 notes retired; notes that still pointed
  at them now name the repository.
- Lost behaviours: viewer-entry client identity (A25 rule rewritten,
  data-provider constants `VIEWER_ENTRY_CLIENT_IDENTITY_MAX_CHARACTERS`,
  `VIEWER_ENTRY_CLIENT_IDENTITY_UNKNOWN`, transport_guard notes, test carried
  to Factory checks: `verification/client_portal_transport_guard_check.py`
  asserts it but no command runs it); `ExpenseConflictError` for a missing
  or other-project expense in four expense_management operations.
- Rounds: State 2 r115–r117, State 3 r54–r56, State 4 r51–r52, State 5
  r43–r44, State 7 r32–r35; all closed. Stage 8.1 39/39 PASS. Admission
  READY_TO_EXPORT 18/0/0.

Tool conflict (reported, not patched): a repository method that shares its
name with another module's function cannot be named in a note without the
Factory slicer inducing an import of that function (§7). derived_views
names `list_project_progress`/`list_project_payments` (the #182 gate
requires a ProjectTrackingRepository method; the same-named project_tracking
functions are induced, as before b3bfb504) and describes the read of one
budget version by id without naming `get_budget_version`.

## Re-export after the Route B stop at expense_intake (2026-11-09, night)

`3fd38bcc` was exported (code-factory #203, with #204 config and #205 v1
catalog proof, all merged). Route B generated 28 modules and stopped at
`expense_intake`: "missing required import: validate_eur_amount from
domain.financial_policy" — the import was declared but no note obliged it
(the note was lost in `a7cccf89`).

Sweep (by hand; no tool reports it yet — a tool PR is proposed): imported
callables of model-written modules that no note or contract of the module
names, i.e. what Factory `validate_generated_coverage` requires to be
imported. 22 hits in 12 modules; the accepted code calls every one, so all
are behaviour to name, none dropped:
expense_intake validate_eur_amount (lost; note restored: after the context
checks, before projection, strictly positive, FinancialValidationError
propagates); snapshot_import and budget_management validate_eur_amount;
append_audit in staff_identity, viewer_access, service_identity,
snapshot_import, budget_management, expense_management, expense_intake,
photo_management; authorize_access_management (staff_identity,
viewer_access, service_identity); conceal_authentication_failure
(viewer_access, service_identity); validate_project_reference
(authorization_guard); parse_verification_secret, verify_secret
(service_identity); _normalize_staff_email, _validate_new_password
(staff_bootstrap); load_runtime_settings (staff_bootstrap_cli).
Commits `2ac4a641`, `a5e4f58c`, `587ef729`, `75387ade`. Re-sweep 0 hits.
State 7 rounds 29–31 closed; Stage 8.1 39/39 PASS; admission
READY_TO_EXPORT 18/0/0 against Factory `6a27ae44`. `global_spec.json`
sha256 `b3bfb504…`.

## READY_TO_EXPORT (2026-11-09, late)

Admission `--update-existing` (no export): **READY_TO_EXPORT**, 18 PASS, 0
blocks, 0 warnings, against Factory `code_factory_cp_witnesses` at origin/main
`2a9db30e` (#202). Workbench main `a2b20fc5` merged (#178, #179).
`global_spec.json` sha256 `3fd38bcc…`. Not exported; no Route B.

Since the evening section below:

- Owner chose (b): a `rules` policy no module reads is legitimate when its
  `kind` is declared in the Factory's `tools/gate_rules_reads.py` (§15.3.1
  fourth home). `bbe9bb0f`: the Consequences of `transaction_guard_policy`,
  `model_immutability_policy`, `exception_payload_policy` cite it;
  `design_factory_slices` names the three under `rules_read_by_gate`;
  FA018 "every rules namespace has a reader". State 2 r114 clear; context
  rounds State 3 r53, State 4 r50, State 5 r42 clear.
- State 7 r28: `design_questions.py rejudge … --unit financial_policy`
  re-judged round 23 T1–T3 `generator_text` (#178); State 7 closed.
- Stage 8.1 hashes recomputed (`fbe8fe3d`), 39/39 PASS.

Both owner/tool items of the evening section are resolved. Next is the
owner's export decision.

## Toward READY_TO_EXPORT (2026-11-09, evening)

Branch `agent/client-portal`, Workbench main `bcd03125` merged (#175, #176,
#177). Factory checkout for prompts and checks: `code_factory_cp_witnesses`
detached at origin/main `ae0726fd` (#201). Question rounds need
`SPEC_WORKBENCH_FACTORY_ROOT` set to that checkout (without it the State 7
prompts are built by the sibling `code_factory`, whose normalizer rejects
binary_storage_backend v2). Not exported; no Route B, no PR merged.
`global_spec.json` sha256 `3fd38bcc…`.

Done (owner decisions of 2026-11-09, each its own commit):

- `9d6e18a2` Q10: the owner confirmed the re-validation from the
  instance's dumped field values (A7, `SOURCE.md`).
- `e4f5be23` enum members by declared NAME everywhere: 63 notes, 71
  `AuditAction`/`Capability` members (`VIEWER_CREATE`,
  `PORTAL_ACCESS_MANAGE`, …); `check_note_draft` and lint L6: 0 blocking.
- `f8b269e6` 13 `rules` namespaces without a reader retired through
  `60_data_closure.json` `retired` (audit_entity_id_policy,
  audit_result_reason_policy, clock_policy, derived_view_ordering,
  idempotency_identities, money_policy, producer_scope_policy,
  project_guard_sequence, project_list_ordering, registry_status_policy,
  staff_identity_input_policy, status_transitions,
  verification_envelope_policy); decisions' Consequences rewritten.
  **Kept**: `transaction_guard_policy`, `model_immutability_policy` (read by
  `kind` by Factory `tools/code_invariant_gates.py`) and
  `exception_payload_policy` (activation key of
  `verification/exception_payload_check.py`) — see owner question 1.
- `6ac66aac` binary_storage through `runtime_settings` (#201):
  `RuntimeSettings.binary_storage_root`/`binary_max_read_bytes`, the two
  rows target them, `binary_storage_backend` schema_version 2,
  `imports.module_internal.binary_storage.runtime_settings`
  (`SEMANTIC_DIFF.md`). Closes the State 2 FA019 item of the morning.
- `bc738392` the last dotted `PortalStore.begin` removed (#176): flow
  closure 0 stops; 33 import scopes re-decided (hash only).
- `db94be20` found while closing State 3: the case spec never declared the
  start-up table constraint `BINARY_MAX_READ_BYTES <= MAX_BINARY_RESPONSE_BYTES`
  that A14 requires and the running `runtime/settings.py` has; the current
  Factory emitter compiles it only from the table, so a regeneration would
  have dropped it. Declared (`constraints`, `constraint_kinds`).

Rounds (one state at a time): State 2 r110–r113 closed (T6/r111 fixes,
path handling carried to generation, the constraint test carried to
factory_checks); State 1 r53 clear; State 3 r50–r52 closed; State 4 r49
clear; State 5 r37–r41 closed (callers, refusal of `load_runtime_settings`);
State 6 has no document; State 7 r27: the 13 changed modules clear.
Stage 8.1 third pass: 39/39 PASS, hashes current (`81_module_review.md`).
Checks: assembly 15/15, imports strict_ready, slices 39/39 0 findings,
projection in sync, notes gate 1086/0 blocks.

Admission `--update-existing` (no export): BLOCKED, 17 PASS, 1 block:
FA019 State 7 `financial_policy` (round 23 T1–T3, the Factory prompt's
model_copy line). FA002 PASS.

For the owner / tools:

1. **Three Factory-gate namespaces** (State 2 r110 T2–T4, verified
   §15.3.1 "dead data"): retire them (the two code-invariant checks and the
   exception payload check go dormant for this project), or a
   standard/tool change that names a policy a Factory gate reads as an
   allowed home (like `time_source_policy`). The later State 2 rounds,
   which review only changed units, did not raise them again, so State 2
   shows closed; the finding stands.
2. **Tool gap (#175 follow-up)**: a recorded State 7 verdict is revisited
   only when the unit's prompt changes (`questions_workbench/units.py`
   `unit_state`), so `financial_policy`'s r23 T1–T3, which #175 would judge
   `generator_text`, stay open and block FA019. Needs a re-judge of an
   unchanged unit (or `ask --module` outside `--probe`); no case text
   change is justified.

## Toward READY_TO_EXPORT (2026-11-09, morning)

Branch `agent/client-portal`, Workbench main merged (#173, #174). Factory
checkout for prompts and checks: `code_factory_cp_witnesses` detached at
origin/main `76ff8512` (#200). Not exported; no Route B, no PR merged.
`global_spec.json` sha256 `d545b52d…`.

Done:

- `3b943d13` owner decision: the Registry URL is read only through
  `runtime_settings` — `REGISTRY_BASE_URL` a required row targeting
  `RuntimeSettings.registry_base_url`; `_registry_url` calls
  `load_runtime_settings` at each Registry call; `REGISTRY_BASE_URL_VARIABLE`
  removed; `runtime_settings` moved before `registry_gateway` in
  `module_order`. A missing, empty or whitespace-only URL now stops the start
  (and the bootstrap command); an unusable non-empty one still fails each
  call as `transport_error`. Behaviour change: `SEMANTIC_DIFF.md`.
- `04cd3253`… State 2 round-101 standard violations and test gaps fixed;
  rounds 102–109 and their fixes (A6 failure order, A16 control set,
  INV-037/INV-041/CFG-001/CFG-002 tests, prose rules addresses replaced by
  the path each value reaches code by). The carried rules namespaces
  (`registry_status_policy`, `project_guard_sequence`, `producer_scope_policy`,
  `idempotency_identities`, … 13 in all) are read by no module or backend:
  each Consequence now says so. Retiring them like FA018 did is an owner
  question.
- `54ebf13f` State 7 notes of the 16 review modules in the standard's forms,
  Q10 mechanism, ProgressPhoto nullable (owner). `0a1ee28f` round-23 fixes:
  plain enumeration members named by the emitter's NAME, dotted-value ones
  (`AuditAction`, `Capability`) by value (#167) — except `project_tracking`'s
  two, named `PAYMENT_REGISTER`/`PROGRESS_UPDATE` after rounds 24–25; new
  builder `build_replayed_expense_operation_outcome` (IR defect); new
  constant `SERVICE_KEY_VERSION_FIRST`; `ProjectTrackingRepository` named in
  the notes so its surface reaches the prompt. One `PortalStore.begin` stays
  in `_authorize_project_operation` (flow closure reads only dotted calls).
- Stage 8.1 closed: 39/39 PASS (`81_module_review.md`).

Rounds closed: State 0 (r35), 1 (r52), 3 (r49), 4 (r48), 5 (r36). Open:

- **State 2** (r103/r107/r108/r109, unit-less): the two binary storage rows
  (`BINARY_STORAGE_ROOT`, `BINARY_MAX_READ_BYTES`) reach generated code
  outside `RuntimeSettings` — the emitted `binary_storage` reads them itself,
  as the Factory binary storage backend is built. A standard violation that
  takes no disposition: it needs a Factory/standard decision (give the
  backend settings fields, or name the backend an allowed reader in §6.11).
- **State 7** `financial_policy` r23 T1–T3: the judge reads the Factory
  prompt's own record-construction line (#200) as an unclassified note
  with code syntax. A Factory prompt question; the module's notes are
  unchanged.

Admission `--update-existing` (no export): BLOCKED, 17 PASS, 1 warning
(codec coverage incomplete: `budget_repository` is model-written), 1 block:
FA019 for the two items above. FA002 PASS.

Other for the owner/tools: Q10 — `model_validate(instance,
from_attributes=True)` returns a same-class instance unchanged under the
emitted model config, so the note re-validates from the dumped values
(SOURCE.md "Owner decisions of 2026-11-09"); notes propagation reports a
pre-existing "Factory blockers" count of 88, 89 after the new builder
(not a gate here); the workbench MCP server runs tools from
`spec-workbench-worktrees/workbench-mcp` (main 42 commits behind), so its
answers for this case fail to project — the checks above used the same
service functions from this branch.

## Record construction on `record_construction_backend/v1` (2026-11-08/09) — read this first

Owner decision 2026-11-08: every record a model-written module builds from its
inputs is built by an emitted builder of the new deterministic module
`record_builders` (SPEC_STANDARD 6.13, Workbench #170). Not exported; no
Route B, no deploy. Factory checkout: `code_factory_cp_witnesses` at main
`9a8a5c14`. Workbench main merged at `7f8af7ff` (#171).

Done (commits on `agent/client-portal`):

- `1db2c06b` States 1–6 and the IR: `70_record_construction_closure.json`,
  86 builders for 74 construction sites; owner decisions Q01–Q12 recorded
  (`SOURCE.md` table; Q07 answered again the same day: a section allocation
  is named by its plan in the active version). Two IR defects fixed:
  `confirmed_at` converts `naive_utc` (A28), and the two credential-issue
  builders take `credential_id` from the caller, who issues the secret for it
  first.
- `b3d01e50` State 7: notes of 16 modules name the builders and keep only
  behaviour; propagated (`--replace-all`), 1085 notes.
- `776ba023` imports closure: builder edges accepted with `code_outdated`
  against the accepted code `459ac96c`; strict_ready.
- this commit: the gap list `spec/record_construction_gaps.json` is removed
  (its content is the IR; git keeps it at `7316b443`).

Checks: `design_record_construction --coverage` 0 findings (RC001–RC015),
`design_imports --coverage` strict_ready, notes gate 0 blocks, projection
`--verify` in sync (tool only since Workbench #172, merged at `2708670a`;
the case script is deleted, the result is byte-identical). State 8
`design_assembly` 15/15, 0 errors; `design_diagnose` no open finding (State 2
`witness_material` not checkable, as before); Factory `normalize_spec`
passes. Admission `--update-existing`: BLOCKED on FA002 (Stage 8.1: 16
modules `AMBIGUITY`, `81_module_review.md`) and FA019 (rounds), nothing else.

Rounds (one state at a time, one round per change):

- State 0 r34: clear, **closed**.
- State 1 r49: 3 blocking (two §5 violations, one photo contradiction) fixed
  in `ae1afb08`; r50 on the fix clear. Still open: ten unchanged units hold
  r49's topics T1/T3/T9 because the judge attributed them to no unit, and a
  unit-less topic holds every unit under review until that unit's text
  changes (`questions_workbench/units.py` `topic_units`) — a tool question.
  `f72843a3` changed M17 again (RegistryFailureKind): one State 1 round due.
- State 2 r101: 21 blocking. Fixed T9 (A30 vs Q12); T16, T20 accepted (Q11),
  T6 carried to factory_checks. Open and pre-existing: 8 verified standard
  violations against SPEC_STANDARD edition 3 (prose `rules.*`/`config.*`
  addresses in A30 and the policy tables, clock IR addresses, the Registry URL
  outside `runtime_settings`), 9 test-specification gaps and a hypothesis
  awaiting disposition. One round due on `c2fde183`/`50cd85cd`.
- State 3 r43: 3 blocking fixed in `f72843a3` (T4 disposed fixed); one round due.
- State 4 r45: T2 fixed in `4ab32bb2`, T1 accepted; one round due.
- State 5 r33: 5 contradictions (Q03, Q09, Q12 not yet carried into State 5
  and A30) fixed in `50cd85cd`; one round due.
- State 7 r22: 93 blocking over 16 modules; 7 caused by the migration notes
  fixed in `a4e6b444`. The rest is in `81_module_review.md` (§2 note forms,
  the Factory prompt's `model_copy` line, enum NAME vs value, Q10 mechanism).

Waits on the projector fix (`tools/projector-record-builders`, `cb901290`):
`experiments/client-portal/frame_record_builders.py` (untracked, never
committed) places `record_builders` in `module_order`/`module_paths`, sets
its edge to `data_provider` and — a gap the pending fix does not cover — its
export surface `imports.internal.record_builders` (every builder of the IR),
without which no consumer edge is importable. After that PR merges: merge
main, re-project without the script, check that `imports.internal` still
carries the builders.

Behaviour changes against the running service (`SEMANTIC_DIFF.md`): Q07
(section allocation name), Q09 (decoding boundary), Q10 (typed refusal of an
incomplete publication), Q12 (Registry path `projects/active`, a live bug
fix), plus the credential_id and confirmed_at corrections.

## Rebuild by SPEC_STANDARD, data first (2026-11-08, night) — read this first

Owner decision 2026-11-08: rebuild the whole specification by SPEC_STANDARD,
starting with the data structures. Not exported; no Route B, no deploy.
`global_spec.json` sha256 `a5bbe66c…`
(`a5bbe66cc438e15730d72b5cc9dbbec003fb9b4698d9f8c3df6d9442d426aa36`), 38
modules (new: `data_provider`), 1094 notes. Factory checkout used:
`code_factory_cp_witnesses` detached at origin/main `89eaed39`.

Done (commits on `agent/client-portal`):

- `7c345323` data D01–D30 of the owner-checked register
  (`docs/INSTRUMENT_INVENTORY_20261108.md` §5.1): 34 constants of the new
  deterministic `data_provider` (`70_data_provider_closure.json`,
  data_provider_backend v2), four new enumerations and nine row models,
  moved leaves removed from `rules`/`config`, notes name each value by
  address. Per-group homes and form decisions: `SOURCE.md` "Data placement".
- `13d99e7a` field maps — withdrawn by `a7cccf89` on the owner's correction
  (prose maps are not checkable). The construction sites are the gap list
  `spec/record_construction_gaps.json` (`f92cc3cd`): 84 sites, 1080 target
  fields, 26 open; `SOURCE.md` "Record construction".
- `8ce72100` §2 code forms removed from 256 notes of the 16 LLM modules
  (dotted navigation, calls, keyword syntax, `Enum.MEMBER`).
- `f10c45fc` State 1 records M38–M46 for the row models.
- `a7cccf89` the rounds' contradictions fixed (States 0–5 named moved
  addresses; A30 called the moved values deployment knobs; Knows lists).

Checks at `a5bbe66c`: `design_assembly` 15/15, Factory `validate_spec` 0
errors, notes gate 0 blocks, `design_imports --coverage` strict_ready,
`design_diagnose` no open finding (State 2 `witness_material` not
checkable, as before). Admission `--update-existing`: BLOCKED on two checks
only — FA002 (Stage 8.1 ledger stale; the owner holds it invalid and a real
review comes later, so it was not rewritten) and FA019 (question rounds).

Open:

- **Rounds.** One round per changed state ran on the first texts: State 1
  r48 clear; State 2 r100, 3 r42, 4 r44, 5 r32, 7 r21 found contradictions,
  fixed in `a7cccf89` (gap topics disposed). The re-rounds on the fixed
  texts were stopped by the host for low memory and have no record:
  States 0–5 and 7 each need one round (`design_questions.py ask
  examples/client-portal --state N`), one state at a time.
- **Owner questions:** the Registry URL is read from the environment by
  `registry_gateway`, outside `runtime_settings` (§6.11); seven construction
  sites where notes and running code disagree or no source exists (gap
  list `open`); the record construction structure itself.
- **Tool gaps** (reported, not patched): the projector places no module
  without State 6 contracts and removes no dropped `rules` namespace
  (`experiments/client-portal/frame_data_provider.py` does both); the
  Factory validator does not accept a member name of an enumeration whose
  values contain dots (`AuditAction`, `Capability`) while the generator
  surface shows only such names, so those members are named in hyphenated
  words; the flow closure reads obliged calls only from dotted forms, so
  methods keep their qualified name (`PortalStore.begin`).

## Where the case stands

- **Exported once, re-export of the sweep pending merge.** Factory #190
  accepted `018b2e2e`. The sweep below changes two notes and gives
  `global_spec.json` sha256 `cbcc7537…` (`cbcc75374b82a3ffda85edb4a933275dc3844572a78bc5f3e83a843ab3caf9ef`).
  It is exported to Factory branch `spec/client-portal-staff-auth-note`,
  MigelSmirnov/code-factory#192 (commit `334b5534`, CI green: 4/4), not
  merged by the agent. Export `--check` READY_TO_EXPORT,
  `verify_workbench_handoff` valid, Spec Inspector PASS (BLOCK 0, WARN 0),
  `route_b_affected --changed global --require-complete` exit 0 (37
  modules, `removed_modules` []). No Route B or deploy was run.
- States 0-5 and 7 are closed on their current texts (`status` per state:
  closed, ready). `authoring next` stops at `state8_assembly`, which is
  ready. Admission reads `READY_TO_EXPORT` (22 checks: 17 PASS, 5
  NOT_APPLICABLE).
- `90_factory_target.json` names `factory_checks_issue`
  MigelSmirnov/code-factory#189. The 54 partial witness verdicts are carried
  there by `witness_material` and do not block.
- The running service still differs from the spec until the next Route B:
  the email routes, 0.00 instead of `None` (INV-044), direct clock reads
  (`design_diagnose` Factory code check: 46 findings) and
  `BootstrapAlreadyCompleted`.

## Sweep of 2026-11-08: remnants of the removed staff email challenges

Owner decision: a spec contradiction is fixed at once, before Route B. The
Factory verification agent found that the State 7 note of
`change_staff_status` still said "an account left unverified could never
authenticate", while `authenticate_staff` decides nothing on
`email_verified_at` (R0-23, A3).

Swept: every authored layer (`00_product.md` … `80_notes.md`, the plans and
closures, `65_imports.json`, `global_spec.json`, `README.md`,
`spec/invariant_ledger.json`) for `unverified`, `email_verified_at`,
`verification`, `challenge`, `email_deliver`, `pending_verification`, the
six removed routes and the six removed audit actions. What stays true and
was kept: activation of a `pending_verification` account records
`email_verified_at`; the first administrator and the recovery override set
it; the account view shows it. Records of the removal (the "Withdrawn" and
"Carried changes" passages, the rejected imports of the removed
`staff_challenges` symbols, `SOURCE.md`, `open_questions.md` Q19) state
history and contradict nothing. `global_spec.json` holds none of the six
routes, the six audit actions, the challenge models or errors.

| file, address | old text | new text |
|---|---|---|
| `80_notes.md` `change_staff_status` [FIELD_ASSIGNMENT] | "…at that same captured timestamp: while the self-service verification challenge has no storage, the administrator performing the activation is what vouches for the address, and an account left unverified could never authenticate." | "…at that same captured timestamp, because the administrator performing the activation is what vouches for the address; the recorded value is a record only, and sign-in decides nothing on it." |
| `80_notes.md` `change_staff_status` [BEHAVIOR] (audit) | "…because suspending or disabling an account ends its sessions and outstanding challenges; the outstanding challenges that entry also names have no persistence while that slice is deferred, so this function revokes none of them by declaration rather than by omission." | "…because suspending or disabling an account ends its sessions; the account has nothing else to revoke." |
| `02_rules.md` "Invariant ledger overview" | "Full statements live in `invariant_ledger.json`." (the ledger keeps INV-014 "…with a verified email", INV-001 "(verified email for staff)", the challenge tokens of INV-003/004, INV-010…013, 016) | "`invariant_ledger.json` is the evidence of 2026-07-19 whose rows were distributed into the decisions (Status above). It keeps wording the owner withdrew with the email challenges (R0-23): …" |
| `README.md` ledger row | "its rows are the formal invariants of `02_rules.md`" | "its rows were distributed into the decisions of `02_rules.md`, and it keeps the email-challenge wording the owner withdrew (R0-23)" |

`spec/invariant_ledger.json` itself is unchanged (evidence). No behaviour
changes: activation still sets `email_verified_at`, sign-in still requires
an active account and a matching password, suspension and disabling still
revoke the sessions — as the accepted `018b2e2e` already says elsewhere.

Commits: `c28dc1b9` (notes), `19ba0aff` (ledger pointer), `fd1d2d11`
(rounds), `10a066a4` (r19 fix), `11060e68` (pointer reworded), `57ac7149`
(rounds), `22df7e39` (Stage 8.1 ledger).

Rounds (one per change; provider `codex-cli:gpt-5.6-sol:medium`; input
characters per request; the judge's files written apart):

| state, round | unit | requests | review (each) | grouping | judge inline (instr + text); files apart | blocking | outcome |
|---|---|---|---|---|---|---|---|
| 2 r98 | Invariant ledger overview | 3 | 9,295 | — | — | 0 | clear, 0 points |
| 3 r40 | context | 3 | 129,723 | — | — | 0 | clear |
| 4 r42 | context | 3 | 130,131 | — | — | 0 | clear |
| 5 r30 | context | 5 | 129,708 | 2,258 | 50,670 (6,134 + 44,536); 1,181,548 | 3 | T4 INV-001, T5 INV-051, T7 PLAT-REG-003: each "newly authoritative" against its decision's exceptions — caused by the pointer's wording "the current statements are each decision's Formal invariants"; reworded `11060e68` |
| 7 r19 | staff_identity | 5 | 47,572 | 853 | 45,690 (2,933 + 42,757) | 1 | T1: "sign-in depends on the active status alone" vs `authenticate_staff`'s active status and matching password; fixed `10a066a4` |
| 2 r99 | Invariant ledger overview (reworded) | 5 | 9,602 | 4,141 | 23,855 (6,296 + 17,559); 997,306 | 0 | clear; 4 judged topics, all `answered` |
| 3 r41 | context | 5 | 130,030 | 965 | 10,216 (6,105 + 4,111); 1,042,513 | 0 | clear; 1 judged topic `answered` |
| 4 r43 | context | 3 | 130,438 | — | — | 0 | clear, 0 points |
| 5 r31 | context | 4 | 130,015 | 720 | — | 0 | clear; two single-review topics, not judged; r30 T4/T5/T7 did not recur |
| 7 r20 | staff_identity | 3 | 46,311 | — | — | 0 | clear, 0 points |

No topic needed a disposition: the contradictions were fixed and their one
round on the fix did not raise them again; every other judged topic was
`answered`.

After the rounds: imports closure strict-ready (195/195, the
`change_staff_status` scope re-decided twice, `--draft` 0 pending, then its
`basis_sha256` set to the gate's current value); State 8 assembly 15/15
ready; State 8 transition ready (54 carried, code-factory#189); Stage 8.1
ledger: all 37 slice hashes refreshed — content changed in
`staff_identity` only, the other 36 by decision line numbers (02_rules.md
grew by three lines) — `staff_identity` rests on State 7 r20; admission
`READY_TO_EXPORT` (17 PASS, 5 NOT_APPLICABLE).

Factory consequences: none for behaviour, so Factory PR #191 (verification
config) is unaffected. The removed-module cleanup record of #190 is not
re-added (reasons in the Factory PR).

## Pass of 2026-11-08 on the single-round rule (#163)

One round per change. A contradiction was fixed and then asked once on the
fix. Every other judged topic got a disposition. Provider
`codex-cli:gpt-5.6-sol:medium`. Input characters per request, measured with
the wrapper around `design_questions.py`. The judge's files are written to
its working directory and listed apart, not added in.

| state, round | units | requests | review (each) | grouping | judge inline (instr + text); files apart | blocking | outcome |
|---|---|---|---|---|---|---|---|
| 3 r37 | context | 5 | 3 × 247,764 (35,993 + 211,771) | 2,858 | 33,163 (6,105 + 27,058); 1,034,298 | 2 | T2 contradiction fixed `43efdb67`; T4 gap carried to 7 |
| 2 r96 | A28 (fix of r37 T2) | 5 | 3 × 65,944 (5,579 + 60,365) | 937 | 35,311 (6,296 + 29,015); 995,850 | 1 | T2 gap carried to factory_checks; no contradiction |
| 3 r38 | context (fix) | 3 | 3 × 126,651 (4,193 + 122,458) | — | — | 0 | clear, r37 T2 not raised again |
| 4 r40 | context | 5 | 3 × 242,913 (37,137 + 205,776) | 2,146 | 24,904 (6,101 + 18,803); 1,075,853 | 0 | clear |
| 5 r28 | build_budget_view, build_progress_view, context | 5 | 3 × 307,759 (38,511 + 269,248) | 578 | 36,462 (6,134 + 30,328); 1,173,638 | 0 | clear |
| 7 r17 | 12 modules | 40 | 36 reviews, 11,264-47,791 | 4 grouping/judge requests, 578-41,598 | — | 1 | staff_bootstrap_cli:T1 contradiction and photo_management:T1 gap, both fixed `8a9cf144` |
| 7 r18 | photo_management, staff_bootstrap_cli (fix) | 6 | 3 × 16,933; 3 × 30,778 | — | — | 0 | clear |
| 2 r97 | A28 (CLK-002 binding) | 3 | 3 × 65,096 (4,668 + 60,428) | — | — | 0 | clear |
| 3 r39 | context (binding) | 5 | 3 × 125,799 (3,278 + 122,521) | 655 | 23,319 (6,105 + 17,214); 1,035,417 | 0 | clear |
| 4 r41 | context (binding) | 3 | 3 × 114,915 (3,633 + 111,282) | — | — | 0 | clear |
| 5 r29 | context (binding) | 5 | 3 × 122,360 (3,259 + 119,101) | 633 | 22,818 (6,134 + 16,684); 1,174,554 | 0 | clear |

State 1 was already closed (round 47) when the pass started.

Changes made in this pass:

- **FA015 type imports** (`11f65b98`): `AuditRepository` `annotates`, basis
  `contract` (the signature of `append_audit`), in budget_management,
  expense_intake, expense_management, photo_management, project_tracking
  (and its two operations), service_identity, snapshot_import,
  staff_identity and viewer_access. `StaffBootstrapPort` in
  `staff_bootstrap_cli.run_bootstrap_cli`. The earlier rejections ("the
  value only passes through the call") judged the accepted code, not the
  surface the slicer needs. The Workbench imports model can express this.
- **A28 CLK-002 owners** (`43efdb67`, State 3 r37 T2): the clock source
  gives one reading per call. The viewer-entry rate limit of A25 owns its
  one reading per request and its window, as State 3 `system_clock`
  "Must not own" requires.
- **Supplied offset-aware times** (`e8499f77`, State 3 r37 T4 carried to 7).
  Principle by the operating profile: one stored meaning per timestamp, the
  instant. The notes of import_snapshot, create_expense_from_recognition,
  publish_progress_photo and issue_service_credential convert an
  offset-aware value to UTC, keeping its instant, before storing it
  offset-naive. An offset-naive value is taken as UTC.
- **State 7 r17 fixes** (`8a9cf144`): `AuditRecord` added to
  `staff_bootstrap_cli`. Its prompt showed
  `StaffBootstrapPort.create_if_empty(..., audit: AuditRecord)` once the port
  was in its surface. `_classify_photo_replay` compares the supplied
  `photo_date` in its stored form.
- **CLK-002 bound** (`5ac1900d`) to `transport_guard_client_portal`, which
  requires that a wall-clock jump does not release a limited viewer.
  `decision_witness_resolution` had blocked: CLK-002 was added in rounds
  92-95 without a binding.

Carried by disposition (`design_questions.py carried`):

- State 2 r96 T2 → `factory_checks` (code-factory #189): the CLK-002 witness
  shows that the viewer-entry rate limit is the only caller of
  `monotonic_seconds`.
- State 3 r37 T4 → State 7: done in `e8499f77`; State 7 r17/r18 asked it.

Witness verdicts after this pass: `judge-checks` re-judged the 18 bindings
of the six checks whose items changed (6 requests, 13,131-83,366
characters), then the three checks of the A28 Witnesses item (3 requests,
13,626-29,396). In all: 69 bindings, 15 asserts, 54 partial, 0 does_not.
A24 on `service_identity_consumer_uow` was `does_not` in the first run and
`partial` after its file set changed (judge variance). The A28 Witnesses
item names CLK-001 and CLK-002, so each of its three tags binds both
invariants (protocol rule). All three are partial.

## INV-044: missing data must not look like zero (owner, 2026-11-08)

"«Нет данных» не должно выглядеть как ноль". A section without a progress
record now has `completed_work_value = None` (was `Decimal` 0, while its
percent was already `None`), and is left out of `completed_work_total`, as
it is left out of overall progress. `completed_work_total` stays `Decimal`:
the work balance subtracts payments from it. Layers: State 1
`BudgetSectionView`, `ProgressSectionView` (`Decimal | None`), M32, overall
progress over sections with a recorded progress; State 2 A9 (rule, carried
change, INV-044 text, its witness item); State 5 outputs of
`build_budget_view`, `build_progress_view`; State 6
`60_model_closure_contracts.json`; State 7 notes `build_progress_view`
[RETURN_SHAPE], `_project_budget_sections` and `_project_progress`
[FIELD_ASSIGNMENT]; `global_spec.json` by projection and note propagation.
`SOURCE.md` records the deviation from 459ac96c.

**Known code/spec difference:** the running service still returns 0.00
for such a section (Factory `application/derived_views.py`). It changes
only with a future Route B regenerating `derived_views`; no export, Route B
or deploy was done.

**Remaining item, Factory (separate Factory PR, coordinator):**
`budget_derivation_client_portal` records the section's
`completed_work_value` without asserting it; its verdict for INV-044 is
`partial` ("It does not assert that completed_work_value is None when
progress is missing"). The check must assert `None`. A9's binding is kept.

## Witness verdicts (`design_questions.py judge-checks`)

The table below is the judgement of the morning of 2026-11-08 (68 bindings).
The current counts are in the pass above (69 bindings: 15 asserts, 54
partial); every partial binding is carried to code-factory #189.

Nine Required tests items named several checks for different invariants in
one item; by the protocol each tag then binds all invariants of the item.
They were split one item per tag group (A4, A8, A9, A11, A13, A16, A18,
A19, A30). That narrows no invariant: it removes claims the items never
meant (e.g. that the photo check asserts INV-009). Before the split 53 of 68
were partial; after it 51, then 52 on the final texts.

Asserts (16): A1 `authorization_guard`; A4, A15 `registry_linkage`; A8
`snapshot_import_sqlite_uow` (INV-021), `expense_intake_uow` (INV-030);
A11 `end_to_end_walkthrough` (INV-005), `viewer_credential_reissue`
(INV-008); A19 `expense_management_uow` (INV-033); A20
`progress_manual_value`; A21 `budget_derivation` (INV-050); A22
`staff_identity_uow`; A23 `staff_bootstrap`; A29 `staff_bootstrap_store`,
`staff_bootstrap_cli`; A31 `workbench:state2_rules_decisions`; A32
`dependency_pins` (DEP-001). (Check names without the `_client_portal`
suffix.)

Partial (52) — each a real finding: the check asserts less than the
invariant it is bound to. Owner of each: the Factory check (extend it,
code-factory #189), never a narrowed invariant or binding text. Since #161
they block at State 8 (`witness_material`), not in the State 2 round. The
texts of A18, A21, A28 and A32 changed on 2026-11-08 (below), so their
bindings are judged again at State 8.

| decision | check | binds | what it does not assert |
|---|---|---|---|
| A2 | `authorization_guard_client_portal` | INV-007 | It does not attempt viewer access management or comprehensively assert that every viewer capability is read-only. |
| A3 | `staff_identity_uow_client_portal` | INV-014 | It does not attempt authentication after the account is changed to disabled, so the full active-only rule is not asserted. |
| A4 | `authorization_guard_client_portal` | INV-001, INV-017, PLAT-REG-003 | It does not fully prove first-failure ordering, uniqueness of active staff assignments, or reject a Registry validation result whose returned UUID differs from the requested UUID. |
| A4 | `staff_identity_uow_client_portal` | INV-004 | The check does not compare exception payloads or responses for indistinguishability and does not assert that authentication failures expose no project data. |
| A5 | `authorization_guard_client_portal` | PLAT-REG-006 | It does not assert absence of a stored Registry snapshot or that live context is fetched afresh rather than treated as cached current truth. |
| A5 | `derived_views_uow_client_portal` | PLAT-REG-006 | The check does not assert the absence of a current Registry snapshot or that archived context remains readable while granting no mutation permission. |
| A5 | `registry_linkage_client_portal` | PLAT-REG-001, PLAT-REG-002, PLAT-REG-007 | PLAT-REG-002 and PLAT-REG-007 are asserted, and unknown-project refusals plus read-only gateway behavior cover substantial parts of PLAT-REG-001. However, the no-generation assertion only scans for direct uuid1/uuid3/uuid4/uuid5 assignments, and the stored-ID assertion subtracts seeded project IDs, so it is weaker than proving that every portal-stored project_id was Registry-issued and that the Registry is the only possible creator. |
| A6 | `derived_views_uow_client_portal` | PLAT-REG-005 | It does not cover the complete closed failure-kind table or explicitly exclude cached and client-supplied fallback context. |
| A6 | `api_transport_financial_policy_registry_gateway_client_portal` | PLAT-REG-005 | It does not exercise the entire closed RegistryFailureKind table or assert that failures never fall back to cached, client-supplied, or fabricated context. |
| A7 | `expense_recognition_projection_client_portal` | INV-031 | It does not test every named invalid form at every required boundary: unsupported versions are not refused at decoding or tested over HTTP, while incomplete and provider-carrying validation-bypassing objects are not passed to create_expense_from_recognition, and incomplete bodies are not tested over HTTP. |
| A8 | `service_identity_consumer_uow_client_portal` | INV-009 | It does not test the corresponding uniqueness rule for viewer_id and project_id. |
| A8 | `viewer_access_sqlite_uow_client_portal` | INV-009 | It does not test or assert uniqueness for (service_principal_id, project_id). |
| A8 | `project_tracking_audit_writer_sqlite_uow_client_portal` | INV-042 | The check asserts idempotent replay by payment_id and rejects a conflicting replay without creating another payment. It does not assert that WorkPayment is never a factura or accounting posting, or that payments total is derived. |
| A8 | `photo_management_uow_client_portal` | INV-043 | It does not assert that visibility-only changes preserve all progress data or any financial data. |
| A9 | `project_tracking_audit_writer_sqlite_uow_client_portal` | INV-037 | It does not assert that all monetary values are EUR or that foreign-currency input is explicitly rejected and never converted. |
| A9 | `snapshot_import_sqlite_uow_client_portal` | INV-037 | It does not assert two-decimal monetary semantics, ROUND_HALF_UP behavior, or directly verify that conversion never occurs. |
| A9 | `derived_views_uow_client_portal` | INV-041 | The check verifies one completed-work calculation and only that overall progress exists when planned work cost exists. It neither asserts the exact R9 overall-progress result nor asserts that progress is unavailable when no planned work cost exists. |
| A9 | `budget_derivation_client_portal` | INV-044 | The check asserts negative overspend behavior, explicit missing completion, and not-configured project views. It explicitly does not assert that completed_work_value is None when progress is absent; that value is merely recorded and is described as 0.00. |
| A10 | `staff_identity_uow_client_portal` | INV-015 | It does not inspect administrator actor provenance, absence of email in the record, or failure atomicity between the change and audit append. |
| A11 | `authorization_guard_client_portal` | INV-005, INV-006 | It does not test revoked credentials or prove that disabled service principals and disabled staff have no usable credentials. |
| A11 | `staff_identity_uow_client_portal` | INV-006 | It verifies that a suspended staff account cannot authenticate and that its existing session is unusable. It does not test credentials or sessions after staff disablement, and it does not test disabled service principals. |
| A11 | `service_identity_consumer_uow_client_portal` | INV-006 | It does not test suspended or disabled staff accounts or whether their sessions are invalidated. |
| A12 | `authorization_guard_client_portal` | INV-029 | It supplies no import content and does not assert that authorization occurs before content validation. |
| A12 | `service_identity_consumer_uow_client_portal` | INV-029 | It does not execute a producer import or establish that authorization occurs before content validation. |
| A13 | `staff_identity_uow_client_portal` | INV-051 | For selected actions passed through _one_audit, the check requires exactly one record of that action. It neither covers every catalog action nor asserts actor provenance or service-actor key_version. |
| A13 | `snapshot_import_sqlite_uow_client_portal` | INV-053 | It does not verify that those additional audit rows also have result "rejected". |
| A14 | `expense_intake_uow_client_portal` | INV-034 | It does not directly assert the general exactly-one-document constraint regardless of allocation count or verify that binary data cannot be stored in the record. |
| A16 | `staff_identity_uow_client_portal` | INV-018 | It does not test Unicode casefolding, syntax validation generally, or refusal of whitespace. |
| A16 | `credential_security_policy_client_portal` | INV-019 | It does not test rejection of passwords violating the R16 length or control-character rules. |
| A17 | `credential_security_policy_client_portal` | INV-003 | It does not inspect persisted session tokens, viewer access tokens, or service credentials, and it does not check logs or prove that any credential type is stored only in verification/hash form. |
| A17 | `staff_identity_uow_client_portal` | INV-003 | The check verifies that tested staff passwords are not persisted as plaintext. It does not establish hashed-only storage for session tokens, viewer tokens, or service credentials, and it does not inspect logs for any credential type. |
| A18 | `budget_management_sqlite_uow_client_portal` | INV-022, INV-023, INV-024, INV-025 | It does not assert that a producer lacks activation capability or cannot activate its own import, imported-plan immutability, activation atomicity under a failure during activation, or that automatic linking exclusively uses source_key and forbids display-name matching. |
| A18 | `snapshot_import_sqlite_uow_client_portal` | INV-020 | It does not attempt or detect mutation or deletion of an already accepted snapshot. |
| A18 | `budget_derivation_client_portal` | INV-026, INV-027, INV-028 | The check behaviorally asserts import immutability/conflicts, expense-plan separation, read-time recomputation after each named mutation, read purity, activation refusal with no writes, and preservation of sections/progress. However, the claims that no table stores any derived value and no service/store path can remove a section are only heuristic name/string/surface scans, so some violating implementations could escape detection. |
| A19 | `expense_intake_uow_client_portal` | INV-032, INV-036 | The configured run does not execute the management scenarios, so it does not assert atomic amount correction with allocation adjustment or the invariant at every later commit point. |
| A19 | `expense_management_uow_client_portal` | INV-032, INV-036 | It does not inject a failure between amount correction and allocation replacement to establish rollback atomicity, so the claim that correction and adjustment are atomic at every commit point is only weakly covered. |
| A19 | `derived_views_uow_client_portal` | INV-035 | It does not seed or test an unconfirmed expense, so the confirmed-only condition is unasserted. |
| A21 | `snapshot_import_sqlite_uow_client_portal` | INV-052 | It does not test update or deletion attempts against either import records or audit records. |
| A22 | `transaction_guard_client_portal` | TXN-001, TXN-002 | It does not establish that the original domain-error object reaches the caller unchanged, because it only matches the expected exception type and does not check object identity or contents. |
| A23 | `staff_identity_uow_client_portal` | entity_id canonical | It does not examine every audit record or assert that entity_id is absent for entities without IDs. |
| A24 | `derived_views_uow_client_portal` | read value unchanged | It checks that one use case does not change the status of its supplied grant objects. It does not establish that every repository value read by any use case remains unchanged. |
| A24 | `service_identity_consumer_uow_client_portal` | read value unchanged | The check verifies preservation of selected principal values and that one rejected grant-revocation path does not invoke repository mutation. It does not assert that every repository value remains unchanged after every use case that reads it. |
| A25 | `runtime_behavior_client_portal` | TRN-001, TRN-002, TRN-003 | However, it does not prove the rejected host/body requests never reach handlers, and its logging assertions cover one query secret and query-string omission rather than every credential, cookie, or secret. |
| A25 | `transport_guard_client_portal` | TRN-001, TRN-003 | The installed guard is exercised and required to refuse untrusted-host and oversized-body requests. The logging check is weaker than TRN-003: it tests one synthetic record made only from non-secret inputs for a short list of forbidden words, without injecting credential or cookie values or inspecting actual emitted log lines. |
| A25 | `api_transport_financial_policy_registry_gateway_client_portal` | TRN-002 | It does not test a foreign Origin on viewer sign-out, so it does not assert that sign-out is refused cross-origin. |
| A26 | `snapshot_import_sqlite_uow_client_portal` | recorded reason equals exception reason | It does not compare a raised exception's own `reason` value with the recorded reason or vary message text to establish message independence. |
| A27 | `derived_views_uow_client_portal` | same order every read | It does not read the same records repeatedly and compare the results, so it only asserts a weaker form of repeatable ordering. |
| A28 | `service_identity_consumer_uow_client_portal` | CLK-001 | It does not cover TTL-derived expiries or preservation of source-supplied times such as a supplied service-credential expires_at. |
| A28 | `staff_bootstrap_client_portal` | CLK-001 | The check asserts that created_at and updated_at share one timestamp and additionally compares audit.occurred_at, but it does not assert equality for every other portal-owned event timestamp, such as email_verified_at, nor exercise TTL-derived expiries or preservation of source-supplied times. |
| A30 | `runtime_settings_client_portal` | required configuration | It does not assert the existence or configuration-driven values of every timeout, TTL, rate limit, and bound; for example, the request/body and binary-size bounds are only supplied in BASE_ENV and never independently tested. |
| A30 | `binary_storage_content_client_portal` | bound existence | The check asserts that the binary read bound exists, is configured with a valid positive numeric value, does not exceed the response ceiling, and rejects oversized content. It does not assert the existence or configurability of every timeout, TTL, rate limit, or other bound; the viewer rate-limit settings are only supplied as configuration inputs. |
| A32 | `dependency_release_gate_client_portal` | DEP-002 | It does not require the snapshot to originate from a public advisory source: the source URL/database metadata is not validated and the release permits FACTORY_OSV_EXPORT_URL to supply an arbitrary export, so the full DEP-002 claim is only partially asserted. |

Judge variance seen: A10 (INV-015) was `asserts` in the first judgement and
`partial` after re-judging the same check for other items; A24 on
`service_identity_consumer_uow` went `partial` → `does_not` → `partial`;
A32 DEP-002 went `asserts` → `partial` when its text changed (the finding
holds: `FACTORY_OSV_EXPORT_URL` may name any export).

Several invariants are covered only jointly by two checks (INV-009 viewer
and service grants; INV-037 rounding and currency; PLAT-REG-005,
PLAT-REG-006, INV-003, INV-029 split across checks). The per-binding
judgement has no form for joint coverage: each binding is judged against
the whole invariant. Workbench gap, to the Workbench owner.

## State 2 rounds 79-81 of 2026-11-08, before #161 (input size per request)

| round | requests | reviews | grouping | judge (instruction + text + files) | blocking |
|---|---|---|---|---|---|
| 79 | 5 | 3 × 286,883 | 21,164 | 848,480 (4,653 + 289,578 + 554,249) | 35 |
| 80 | 5 (+6 check re-judgements) | 3 × 292,923 | 17,200 | 842,995 | 32 |
| 81 | 5 (+2 check re-judgements) | 3 × 282,853 | 19,529 | 837,231 | 30 |

A review is about 87k of instruction and 200k of texts; the round now fits
the provider (limit 1,048,576), the judge request being the largest at
~840k. Check judgements: first pass 30 requests (856,820 characters in all,
median 26,221, max 82,943), second pass 15 (377,767, max 39,491),
re-judgements in rounds 80/81: 6 (12,823-83,291) and 2 (12,790, 28,560).
State 1 rounds 46-47 (run before the coordinator's limit): 5 requests each,
reviews 66,730 / 67,519, judge 719,934 / 718,543 (644,377 of it files).

Fixes taken in rounds 79-80 (simplest code-backed form): A10 INV-015 names
its enhanced audit (A13's `staff.recovery_override` record); A18 INV-026 a
conflicting re-publication changes no business state and is recorded as
its import result and audit; A28 one wall reading per operation plus the
audit writer's own, derived expiry = instant + TTL while a supplied one is
kept, source times stored offset-naive UTC, invariant `CLK-001`; A31 the
three outcomes of the security-review procedure (NOT_APPLICABLE carries a
rationale and resolves to neither a decision nor an open question — the
invariant is narrowed to what the procedure and its gate decide); A32
DEP-002 covers every installed distribution, with the age limits named as
the deploy route's `max_snapshot_age`, `max_environment_age`.

Open after round 81 (17 units): A4, A5, A6, A7, A8, A9, A11, A13, A16,
A18, A19, A21, A22, A25, A28, A30, A32 — the coverage gaps of the table
above, plus singletons on A28 (where in an operation the one wall reading
happens; accepted forms of source-supplied datetimes) and A32 (whether the
vulnerable-image rule covers builds or only deploys).

## State 2 rounds 82-95 (2026-11-08, after #161)

Run with `--since 451ea6de` (the round-81 `closed_at`), provider
`codex-cli:gpt-5.6-sol:medium`, 5 requests per round (3 reviews, grouping,
judge). Input characters per request:

| round | review (each of 3) | grouping | judge (instruction + text + files) | blocking | blocked units |
|---|---|---|---|---|---|
| 82 | 239,236 | 4,109 | 811,853 (5,411 + 252,193 + 554,249) | 10 | A18, A21, A28, A32 |
| 83 | 245,051 | 1,879 | 807,080 | 2 | A28, A32 |
| 84 | 175,189 | 1,695 | 761,903 | 1 | A32 |
| 85 | 166,010 | 3,455 | 762,766 | 5 | A28, A32 |
| 86 | 166,136 | 5,113 | 770,126 | 6 | A28, A32 |
| 87 | 166,136 | 4,389 | 767,038 | 3 | A28, A32 |
| 88 | 168,297 | 3,725 | 768,008 | 5 | A28, A32 |
| 89 | 169,061 | 2,231 | 761,508 | 4 | A28, A32 |
| 90 | 169,950 | 4,753 | 769,344 | 2 | A32 |
| 91 | 165,937 | 8,484 | 782,086 | 2 | A28 |
| 92 | 167,594 | 7,854 | 786,956 | 3 | A18, A28 |
| 93 | 151,714 | 2,956 | 62,893 inline (6,296 + 56,597); files 981,942 apart | 2 | A18, A28 |
| 94 | 167,917 | 2,204 | 70,834 inline (6,296 + 64,538); files 982,469 apart | 0 | — |
| 95 | 167,917 | 2,364 | 65,030 inline (6,296 + 58,734); files 982,469 apart | 0 | — |

Two attempts (rounds 83 and 85) failed after their three reviews on a
review answer that was not valid JSON and saved nothing; they were rerun
(3 more requests each at the sizes above). Round 87 repeats round 86 on the
same text (a retry loop treated `ask`'s exit 1 for "not closed" as a
failure). The judge's 554,249 characters of files are constant: the later
states' texts it reads for `answered_later`.

No round raised a check's coverage as a blocking topic. The reviewers still
asked "which existing check is bound to CLK-002" in rounds 83-90; the judge
set it aside each time (`answered`, `judged_before`). Workbench defect, to
the Workbench owner: the State 2 review prompt still invites questions about
bound checks.

What changed in the decisions (`02_rules.md`), each on its substance:

- A18 INV-027 (r82 T6, T12): the test covers every write of an owning
  record, budget-version activation included (the list read as exhaustive
  and left activation out), and forbids stored values of a derived view,
  not every derived column (an import's content fingerprint is stored by
  the models).
- A21 INV-050 (r82 T7): every overview component (budget, expenses,
  progress, payments, photos) equals a recomputation, not only budget and
  payments.
- A28 (r82 T5, T9, T11; r85 T9): `document_date` and `payment_date` are
  calendar dates kept as supplied, not instants (they were listed among
  UTC instants, against the State 1 models); "no arithmetic" is the clock
  source's, an operation derives an expiry as instant + TTL; CLK-001 now
  states one wall reading from the clock source, the only reader of the
  host clocks, derived expiry = instant + TTL, supplied times and dates
  kept; its test covers every timestamp-writing operation with the clock
  fixed.
- A32 (r82 T2, T8, T10; r83 T6): OSV (ecosystem PyPI) is the advisory
  source; the checked set is every distribution installed in the image
  (rule 3 said pins and their resolved libraries, DEP-002 every installed
  one); a deploy is the start of the service from an image (DEP-002 said
  "ships", its test "starts"); a passing rebuild under the same pins may
  deploy. How the snapshot is obtained and verified and how a version is
  matched to an advisory is the deploy route's and its State 8 witness's
  (code-factory #189); the age limits stay the deploy route's values.
- Rounds 83-90 drove A28 and A32 into witness mechanics (OSV export
  completeness, transport authentication, PEP 440 matching; clock
  instrumentation, read counts). On the coordinator's instruction those
  additions were removed before round 91 and the simplest form above kept.

Open after round 91 (blocking, A28), verbatim:

- T1 "Clock-source and reading-count verification for read-only
  current-time checks": "CLK-001 governs current-time comparisons, but its
  Required test omits operations that compare persisted expiry without
  writing timestamps."
- T2 "Elapsed-clock source, request scope, reading count, use, and
  non-persistence policy": "The later operation text resolves that the
  reading is per viewer-entry attempt, but State 2 still supplies no formal
  invariant or Required test for any elapsed-clock property." (Round 82 T9
  raised the same; a CLK-002 added for it in rounds 82-90 was removed with
  the mechanics before round 91.)

Round 92 (owner approved closing A28 on substance, coordinator
2026-11-08): CLK-001 extended to every read of the current time, writing a
timestamp or comparing it with a stored one (expiry checks included), one
wall reading per operation from the clock source; new CLK-002 (owner: the
clock source): elapsed durations are measured only through the clock
source's monotonic reading, used within one process, never persisted and
never compared with or mixed into wall-clock values. Required tests items
at the same level. Round 91's two A28 topics did not recur (r92 T7
`answered`, T17 `answered_later`). Status and A32 closed; open units A18,
A28.

Open after round 92 (blocking: 3), verbatim:

- T11 (A18, consequential_gap) "INV-027 permissibility and handling of
  stored derived values or caches": "The detailed test forbids every
  stored derived-view value and answers the cache question, but the
  generic Required-test sentence still requires refusal of an undefined
  violating input to a read-only recomputation."
- T15 (A28, consequential_gap) "CLK-001 architectural check prohibiting
  direct host-clock reads outside the clock source": "The Required test
  says how to observe an operation's clock-source use but does not say
  what check demonstrates the global architectural prohibition on every
  direct host-clock read."
- T16 (A18, contradiction) "INV-020 behavior when an existing snapshot
  identity is republished with conflicting content": "The unqualified
  INV-020 Required-test outcome says a violating import changes nothing,
  while the detailed required test expressly requires a changed
  re-publication to append its import result and audit."

Round 93 (owner approved fixing the three round-92 topics; on 404d1ccd,
origin/main with Workbench #162 merged: narrower judge input, review retry,
no bound-check invitation). A18: the eight generic carried-over items "a
focused test at X showing the invariant holds; a violating input is refused
and changes nothing" were removed; INV-020 and INV-022…INV-025 got detailed
items at the "what must be shown" level beside their witness tags
(INV-026…028 kept theirs). CLK-001's Required tests item adds that no module
other than the clock source reads the host wall or monotonic clock directly.

Round 93 sizes: each review 151,714 (12,622 instruction + 139,092 text);
grouping 2,956; judge 62,893 inline (6,296 instruction + 56,597 text).
Since #162 the judge's files (981,942) are written to its working
directory and read by search, not sent in the prompt; they are not part
of the request size. In rounds 82-92 the judge column above still adds
them in.

Open after round 93 (blocking: 2; open units A18, A28), verbatim:

- T4 (A18, contradiction) "Whether idempotent snapshot re-publication
  permits any persistent writes": "The Required test's unqualified no-change
  outcome conflicts with the product rule requiring two new persistent
  records for every classified idempotent replay." Quotes: "a
  re-publication of its identity with the same content changes nothing,"
  and "An attempt the import classifies — accepted, idempotent replay,
  integrity conflict, or a rejection — is recorded as a fresh immutable
  import result with a fresh `import_id` and its `snapshot.import` audit;".
  A defect of the new INV-020 item written for round 93: a same-content
  replay should also say it is recorded as its import result and audit.
  Not edited (one round only).
- T7 (A28, consequential_gap) "Whether CLK-002 requires exactly one
  monotonic-clock read per viewer-entry request": "Although the normative
  rule requires one elapsed reading per request, neither CLK-002 nor its
  Required tests item says that the test must demonstrate that read-count
  requirement."

Round 92's T11, T15, T16 did not recur as such (T16's replay question
returned as T4 on the new text). No round-93 topic is about a bound
check.

Round 94 (coordinator, fixing both round-93 topics):
- T4: the INV-020 item now says a same-content re-publication is an
  idempotent replay and that either a replay or a conflict leaves the
  snapshot unchanged, changes no business state and is recorded as its own
  import result and `snapshot.import` audit. The same "nothing stored /
  changes nothing" wording covered the classified snapshot replay in A8:
  its table row, INV-021 and INV-021's generic Required tests item now say
  the same (no snapshot stored, no business state changed, own import
  result and audit; the request is answered with the result, not the
  snapshot, `00_product.md`). The expense, photo and payment replay rows
  of A8 were left as they are: no text records anything for them.
- T7: CLK-002 and its Required tests item say one elapsed (monotonic)
  reading per viewer-entry request, as the normative rule does.

Round 94: 5 requests; reviews 167,917 each (17,646 + 150,271), grouping
2,204, judge 70,834 inline (6,296 + 64,538), files 982,469 apart.
Blocking 0, the round is clear; topics: A28 ×2 `judged_before`, A8
`answered`, A8 ×2 `answered_later`. Open units: A8, A18, A28 (each needs
a second clear review on its current text; A8 reopened by this edit).

Round 95 (confirmation, text unchanged since round 94): 6 requests — one
review answered invalid JSON and was asked once more (#162 retry), so 4
review requests of 167,917 (17,646 + 150,271); grouping 2,364; judge
65,030 inline (6,296 + 58,734), files 982,469 apart. Blocking 0, clear;
topics: A28 `later_state`, A28 `judged_before`, A8 `judged_before`, A8
`answered`. Round closed; `status --state 2`: closed true, ready true.

Reopened and not asked (coordinator: State 2 only; unchanged after round
95, `status` per state): State 1
(`Projections and answers`), States 3 and 4 (`context`), State 5
(`build_budget_view`, `build_progress_view`, `context`), State 7
(`financial_policy`, `derived_views`) — the same units as before round 82;
the State 2 edits enter the `context` of States 3-5. State 0 stays closed.

## Other open items

- **Export.** #190 accepted `018b2e2e`. The sweep's re-export (`cbcc7537…`)
  is on Factory branch `spec/client-portal-staff-auth-note`, made in the
  worktree `code_factory_cp_export2` from origin/main `9409b8e2`; merge is
  the owner's. The main `code_factory` checkout was not used.
- **Route B** must start from the spec the owner merges: `cbcc7537…` once
  the sweep's PR is merged (not `018b2e2e`).
- **Factory checks, code-factory #189** (owner: Factory): 54 partial
  bindings (`transition.py --phase state8_assembly`), INV-044's `None`
  assertion in `budget_derivation_client_portal`, and the CLK-002
  sole-caller witness (State 2 r96 T2).
- **Route B** (owner: coordinator, after export): the live code has 46
  Factory code-check findings on the clock source and still serves the
  removed email routes and the 0.00 of INV-044.
- **Known residue: `email_deliveries`** (owner, 2026-11-08). The storage
  schema revision stays 13. The `email_deliveries` table, the outbox of the
  removed staff email challenges, stays in live databases; the new code
  neither creates nor reads it. The design has no migration form: the
  persistence closure, SPEC_STANDARD §15.7 (versioning rules and
  expand/contract, but no form to declare a step such as dropping a table)
  and the Factory emitter (`storage_schema_revision` is only a setting
  value there) all lack one. This is a Workbench and Factory gap. The table
  is dropped manually after Route B with the owner's approval, or by a
  later revision once a migration form exists. See `SEMANTIC_DIFF.md`.
- **Stage 8.1** evidence is the State 7 rounds and the emitter IR. No
  separate per-module adversarial review was run (ledger `semantic_evidence`).
- **Workbench gaps** (owner: Workbench):
  - A witness-tag-only edit to a State 2 Required tests item reopens the
    State 2 unit and the `context` of States 3-5. QUESTIONS.md says a
    `[witness: …]` tag is only text of its item. Binding CLK-002 cost four
    rounds (r97, r39, r41, r29), none of which raised anything.
  - The per-binding judgement still has no form for joint coverage, and a tag
    binds every invariant of its item (the A28 Witnesses item now binds
    CLK-001 and CLK-002 to each of three checks).
  - `imports_scope_stale` after a note edit has no command that re-records
    `basis_sha256` once the author has re-read the candidates. `--draft`
    leaves the stale hash; the hash was set by hand to the gate's `current`
    value, with no candidate pending.
  - The Factory slicer adds the signature types of a port's operations to a
    prompt only in part: `StaffAccount` appeared in `staff_bootstrap_cli`'s
    IMPORTS without a declaration, `AuditRecord` did not (Factory, to the
    coordinator).
- The workbench MCP `check_note_draft` answers from the pushed ref; the
  notes of this pass were checked with the local `design_notes --gate`.
