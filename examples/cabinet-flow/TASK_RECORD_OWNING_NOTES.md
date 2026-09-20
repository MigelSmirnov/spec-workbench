# Task — make every record-owning note name the port operations it uses

Self-contained brief for the agent that takes this task. Case: `examples/cabinet-flow`, canonical
branch `agent/cabinet-flow`. Work on your own branch cut from it (`agent/cabinet-flow-record-notes`)
and open a pull request into `agent/cabinet-flow`. Do not export to the Factory and do not start
Route B.

## Why

Factory run 2 generated ten modules that keep their records in module-level dicts, because no note
said how a record reaches the store. The store boundary is now designed (commit `3b219a1`):
`operational_store.begin_unit_of_work(purpose, correlation_id)` returns an `OperationalUnitOfWork`,
an interface of 107 typed record operations over 29 tables; `commit_unit_of_work` /
`rollback_unit_of_work` end it. What is still missing is the last link: the notes of the functions
that own records do not name those operations, so the generator would invent storage again.

Read first, in this order: `RUNTIME_BOUNDARY_INVENTORY_20260920.md`,
`RECORD_PORT_REQUIREMENTS_20260920.md`, the last three sections of `81_module_review.md`, the section
`OperationalUnitOfWork` of `60_contract_types.md`.

## The model to follow

The note of `resolve_actor` in `80_notes.md` is the reference. It names every call the function
makes — `module:installation.resolve_credential`, `module:operational_store.begin_unit_of_work`,
`OperationalUnitOfWork.load_authentication_throttle_state`,
`OperationalUnitOfWork.upsert_authentication_throttle_state`,
`OperationalUnitOfWork.list_owner_principal_by_status`, `module:system_clock.now`,
`module:operational_store.commit_unit_of_work` / `rollback_unit_of_work` — and says which fields it
writes with which values. Two faithful implementations of that note cannot differ in where a record
lives.

## What to do, per function

Scope — every function of these modules that reads or writes a durable record:
`access_control` (`issue_delegation`, `revoke_delegation`, `authorize_action`), `owner_authority`,
`semantic_vocabulary`, `slot_registry`, `trial_corpus`, `admission`, `slot_activation`,
`flow_registry`, `flow_proof`, `operation_bindings`, `run_executor`, `operation_invoker`,
`trace_journal`, `value_store`.

`RECORD_ACCESS_MAP_20260920.json` lists, for each of these functions, the records it reads and
writes, by which key, and what the texts leave undecided (`unclear`). Use it as the work list; verify
each entry against the note, State 5 (`50_public_apis_<module>.md`) and State 1 before relying on it.

For each function rewrite its note in `80_notes.md` so that it:

1. opens one unit with `module:operational_store.begin_unit_of_work`, and ends it with
   `module:operational_store.commit_unit_of_work`, closing any failed unit with
   `module:operational_store.rollback_unit_of_work`. A read-only function does the same and rolls
   back or commits without having written;
2. names, as `OperationalUnitOfWork.<operation>`, every record operation it uses. The only
   operations that exist are the `OperationalUnitOfWork.*` keys of `60_contracts.json`
   (`load_*`, `find_*_by_*`, `list_*_by_*`, `insert_*`, `update_*_<group>`, `upsert_*`);
3. states compare-and-set as a comparison of the caller's expected value with the record loaded in
   that unit, followed by the named `update_*` operation;
4. keeps every behavioural obligation the note already has. You are adding the storage path, not
   changing behaviour. Keep the note's class tag.

Also declare the collaborators for the Factory slicer: in `global_spec.json`,
`imports.module_internal.<module>` must list `operational_store`:
`["begin_unit_of_work", "commit_unit_of_work", "rollback_unit_of_work"]` and, under `models`,
`OperationalUnitOfWork`, `UnitOfWorkCommitResult`, `UnitOfWorkRollbackResult` and every record model
whose operation the module's notes name. See `access_control` there as the example.

## What you must not do

- **Do not invent.** If a function needs an operation that does not exist (a filter on a set of
  values, a delete, a lookup by a field no table is listed by), a field that no model has, or a
  record that has no model (the in-flight effect attempt, the retention reference, the acceptance
  record of a binding version, the installation record), do not add it and do not write a note that
  pretends it exists. Write the rest of the note, and record the gap in
  `RECORD_NOTES_OPEN_POINTS.md`: function, what it needs, which text requires it. Those are design
  decisions and are taken separately.
- Do not change State 0–2 documents, the model closures, `60_contracts.json`, the persistence
  closure, the router closure or any tool under `tools/`.
- Do not use the bare words `inspect`, `author` or `activate` in a note of any module other than
  `kernel_surface`, `http_gateway` and `mcp_gateway`: they are function names of `kernel_surface`
  and the Factory slicer turns them into an import, which closed a fourteen-module import cycle in
  run 2. Write "view", "authoring actor", "put into service". More generally, name a function of
  another module only when this module is meant to call it.
- Do not put workbench labels (`M17`, `A21`) or literal values of a closed vocabulary into a
  normative sentence; refer to `rules.*` / `config.*` addresses as the existing notes do.
- Do not set any module to `PASS` in `81_module_review_status.json`. After your notes change, refresh
  only `slice_sha256` values (sha256 of the `build_slice` packet, as
  `tools/factory_admission_workbench/service.py` computes it) and leave statuses as they are; the
  review is done by the case owner.

## Mechanics

```bash
git fetch origin && git switch -c agent/cabinet-flow-record-notes origin/agent/cabinet-flow
git merge origin/main                      # tools are only as fresh as the branch
git branch --show-current                  # check before every commit

# after editing 80_notes.md
python tools/design_notes.py examples/cabinet-flow --propagate --base-ref HEAD
python tools/design_spec_projection.py --verify examples/cabinet-flow
python tools/design_notes.py examples/cabinet-flow --gate --json          # 0 findings
python tools/design_value_flow.py examples/cabinet-flow                   # 0 errors
python tools/design_assembly.py examples/cabinet-flow --json              # 13/13 ready
python tools/design_decision_witness.py examples/cabinet-flow --coverage  # 29/29
```

Before the pull request also run the import-cycle probe with the Factory's own matching rule; it
must report `cycles 0`:

```bash
/home/smirnov/jestor_VBC/venv/bin/python \
  /home/smirnov/jestor_VBC/exp_vbc/demo/code_factory/outputs/cabinet_flow_preflight/induced_imports.py \
  examples/cabinet-flow/global_spec.json | head -3
```

One commit per module, only the intended files staged (`git diff --cached --name-only`,
`git diff --cached --check`), message in the form of `code_factory/factory_control/GIT_POLICY.md`:
subject `cabinet-flow: <imperative summary>`, then `Why:` / `Route:` / `Safety:` / `Validation:`.
A finding of any gate is a stop: decide it or record it in `RECORD_NOTES_OPEN_POINTS.md`; do not
waive it and do not edit a tool to make it pass.

## Done when

- every function in scope names its unit of work and its `OperationalUnitOfWork.*` operations, or
  is listed in `RECORD_NOTES_OPEN_POINTS.md` with the exact missing piece;
- all six commands above are clean and the probe reports no cycle;
- the pull request describes, per module, how many notes changed and how many open points were
  recorded.
