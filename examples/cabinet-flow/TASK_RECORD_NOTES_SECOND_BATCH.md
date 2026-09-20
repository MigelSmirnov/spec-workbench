# Task — second batch of record-owning notes

Same repository, rules, mechanics and gates as `TASK_RECORD_OWNING_NOTES.md` (read its sections
"Where", "What you must not do" and "Mechanics" first). Branch:
`agent/cabinet-flow-record-notes-2` from `origin/agent/cabinet-flow`, pull request into
`agent/cabinet-flow`.

The first batch recorded 17 open points in `RECORD_NOTES_OPEN_POINTS.md`. The case owner decided the
ones that are model shape (see the last section of `81_module_review.md`): new records
`EffectAttempt` and `BindingLifecycleEvent`, new fields, new port operations. The notes below can
now be completed. Change only these notes; add the storage sentences and the field values, keep every
existing obligation. `resolve_actor`, `invoke_operation`, `request_approval` and `retire_entry` are
the reference for how a note names operations *and* says which field gets which value.

| Function | What the note must now say |
|---|---|
| `accept_binding_version` | append one `BindingLifecycleEvent` of kind `accepted` with `OperationalUnitOfWork.insert_binding_lifecycle_event`: `event_id` = binding, kind and version joined in that order, `actor` the owner, `statement` the owner statement, `occurred_at` one `module:system_clock.now`. A repeated request is answered from `OperationalUnitOfWork.load_binding_lifecycle_event`. `OperationBindingVersion` is not updated: remove any use of an acceptance update. |
| `sweep_manifest_drift` | append `suspended` / `reissued` events the same way, `actor` absent, `manifest_record_digest` the compared record, `statement` the changed fact names. |
| `retire_binding` | append a `retired` event with actor, reason and instant; replay of the first retirement is answered from the stored event. |
| `binding_for_invocation`, `binding_version` | an accepted version is one that has an `accepted` event: `OperationalUnitOfWork.list_binding_lifecycle_event_by_binding_id`. |
| `authorization_for_effect` | the new parameters `map_index` and `attempt_number` form the attempt identity (run, node, map index, attempt number joined in that order) written into `consumed_attempt_refs`; the absence of another active grant or of an earlier consumption is decided by listing inside the same unit — the unit is the store's one writer, so list-then-write is atomic. |
| `advance_run`, `resume_runs` | in-flight attempts are read with `OperationalUnitOfWork.list_effect_attempt_by_run_id` / `list_effect_attempt_by_status`; they never write an `EffectAttempt` (that is `invoke_operation`). |
| `reconcile_outcome` | concludes the reconciled attempt with `OperationalUnitOfWork.update_effect_attempt_conclusion` when the determination is final. |
| `record_node_execution` | `node_execution_id` = run, node, map index and attempt number joined in that order, so a repeated draft finds the first record with `OperationalUnitOfWork.load_node_execution`; `contract_version_ref` is copied from the draft. |
| `slot_evidence` | selects by `contract_version_ref` — if no list operation by that field exists, record it as an open point instead of inventing one. |
| `find_duplicate_revision` | candidates come from `OperationalUnitOfWork.list_semantic_axis_revision_by_meaning` / `list_semantic_term_revision_by_meaning` and, for relations, the existing list by source and target; equality of the remaining content fields is compared in the function. |
| `seed_vocabulary` | each seed entry is looked up by its key with the `load_*` operations; the seed revisions carry `accepted_by` = the installation owner resolved with `OperationalUnitOfWork.list_owner_principal_by_status` and `issued_at` = one `module:system_clock.now`. |
| `capture_trial_case` | the origin is the existing fields `origin` and `origin_node_execution_ref`; remove wording that asks for another carrier. |
| `withdraw_trial_case` | "ever contributed to an admitted verdict" = some `TrialExecution` of `OperationalUnitOfWork.list_trial_execution_by_trial_case_ref` is named in `considered_trial_executions` of an admitted `AdmissionVerdict` from `OperationalUnitOfWork.list_admission_verdict_by_contract_version_ref_and_implementation_ref`. |
| `waiting_for_owner` | one `list_effect_approval_by_status` and one `list_standing_grant_by_status` per requested status, merged and paged in the function in ascending identity order. |

Out of scope and to be left exactly as they are: `put_value`, `expire_values`, `read_value`,
`submit_implementation` (value and code bytes — boundary 6, not decided), and everything in
`store_continuity`, `installation`, `operational_store`, `bootstrap`.

When a row cannot be written because an operation or field is still missing, do not invent it:
update `RECORD_NOTES_OPEN_POINTS.md` — remove the points this batch closes, keep or add the rest.
