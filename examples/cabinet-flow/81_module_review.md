# Stage 8.1 — assembled module semantic review

## Verdict

All 28 assembled module slices are `PASS`. Each slice was checked against the four Workbench adversarial questions: no materially different observable behavior, trivial implementation, missing accepted refusal/effect/invariant, or source-free behavior remains admissible. Exact packet hashes are recorded in `81_module_review_status.json`.

## Module results

| Module | Contracts | Notes | Structural findings | Semantic result |
|---|---:|---:|---:|---|
| `models` | 0 | 0 | 0 | PASS |
| `system_clock` | 1 | 0 | 0 | PASS |
| `identity` | 9 | 9 | 0 | PASS |
| `installation` | 4 | 4 | 0 | PASS |
| `operational_store` | 3 | 3 | 0 | PASS |
| `access_control` | 4 | 4 | 0 | PASS |
| `semantic_vocabulary` | 8 | 8 | 0 | PASS |
| `slot_registry` | 9 | 9 | 0 | PASS |
| `trial_corpus` | 5 | 5 | 0 | PASS |
| `sandbox_supervisor` | 2 | 2 | 0 | PASS |
| `admission` | 2 | 2 | 0 | PASS |
| `slot_activation` | 4 | 4 | 0 | PASS |
| `manifest_reader` | 3 | 3 | 0 | PASS |
| `operation_bindings` | 5 | 5 | 0 | PASS |
| `flow_proof` | 1 | 1 | 0 | PASS |
| `flow_registry` | 8 | 8 | 0 | PASS |
| `owner_authority` | 9 | 9 | 0 | PASS |
| `service_transport` | 1 | 1 | 0 | PASS |
| `operation_invoker` | 2 | 2 | 0 | PASS |
| `value_store` | 4 | 4 | 0 | PASS |
| `run_spool` | 4 | 4 | 0 | PASS |
| `trace_journal` | 3 | 3 | 0 | PASS |
| `run_executor` | 5 | 5 | 0 | PASS |
| `kernel_surface` | 6 | 6 | 0 | PASS |
| `mcp_gateway` | 1 | 1 | 0 | PASS |
| `http_gateway` | 9 | 1 | 0 | PASS |
| `bootstrap` | 1 | 1 | 0 | PASS |
| `operational_store_persistence` | 30 | 0 | 0 | PASS |

## Deterministic surfaces

Domain and contract-only models, SQLite persistence, the fixed HTTP router, and the system clock are closed by versioned structured IR. The SQLite emitter owns only `operational_store_persistence`; the behavioral UnitOfWork boundary remains in `operational_store`. Tagged union wrappers preserve every closed State 6 variant without untagged unions.

## Value-flow closure delta (2026-09-20)

The slices of 27 modules moved after the value-flow closure
(`python tools/design_value_flow.py examples/cabinet-flow --coverage`: outputs 34 of 34,
inputs 59 of 59, collaborators 55 of 55). Each slice was compared with its state at
`origin/agent/cabinet-flow` (`fdd423d`) and reviewed against the intended change only.

- **Anchors only** — `identity`, `installation`, `manifest_reader`, `bootstrap`,
  `sandbox_supervisor`, `service_transport` (plus one named manifest read), `value_store`,
  `run_spool`, `trace_journal`: line-number references shifted by inserted lines; no contract,
  note or model of the module changed. `system_clock`: the two reviewed flows now name
  `capability:system_clock.monotonic_ns`, as the State 4 plan already required.
- **Named collaborators** — `admission`, `slot_activation`, `trial_corpus`, `slot_registry`,
  `operation_bindings`, `owner_authority`, `flow_registry`, `run_executor`: notes now name the
  exact operations State 5 already assigned to them, and the module imports those contracts
  with their models. No new behaviour: a module that cannot call its collaborator invents
  what it would have returned, which is the variation this closes.
- **Instants** — every required `KernelInstant` of a constructed record names
  `module:system_clock.now` in the note of the function that writes it; `request_trial`
  returns the verdict of `admission.run_trial`; `cancel_run` keeps the stored `created_at`.
- **Lifecycle facts State 5 already promised** — `Flow` and `Slot` gain `retired_by`,
  `retired_at`, `retirement_reason`; `AgentDelegation` and `StandingGrant` gain
  `revocation_reason`; `FlowRun` gains `cancellation_reason`; `VocabularyProposal` gains
  `agent_rationale`. All optional, written once; the SQLite closure carries the columns.
- **A10 engaged** — only the owner accepts a binding version, so
  `OperationBindingVersion.accepted_by` / `accepted_at` are absent on a proposed version and
  written once by `accept_binding_version`; `binding_for_invocation` refuses a version whose
  `accepted_at` is absent. This removes the sentinel instant a generator had to invent.

Adversarial question per module — can two faithful implementations now differ observably? —
answered no for every changed slice: each added sentence removes a choice (which operation,
which clock, which field), none adds one. All 28 modules remain PASS.

## Instants a module handles but does not produce (2026-09-20, after the run stopped at `run_spool`)

Factory run `cabinet_flow-route-b-20260920T140105Z` generated 20 modules and stopped at
`run_spool`: the candidate defined a host-clock helper it never called, because
`SpooledBytes.released_at` exists and no note said where an instant of this module comes from.
The value-flow lens judges required instants of returned records; an optional instant of a
handled record is outside it. Reviewed and closed in the three modules that handle
instant-bearing records without reaching the clock: `run_spool` (`receive_file`,
`release_run_files`), `trace_journal` (`record_node_execution` takes the draft's instants) and
`kernel_surface` (`run_flow`, `inspect` return stored instants). Each note now states the origin
and that no clock is read — a statement of source, not of style. No behaviour changed; slices
moved by the added sentences and by shifted line anchors only. All 28 modules remain PASS.

Open design question, not decided here: `SpooledBytes.released_at` ("when the spool entry was
emptied") has no writer in any contract — `release_run_files` deletes the objects and returns
counts. The field is only ever read as a liveness check.

## ReleaseCeilings brought back to State 1 (2026-09-20)

The closure of `ReleaseCeilings` (M48) carried seven names found nowhere else in the case
(`max_value_bytes`, …, `max_resource_bounds`), while State 1 and `config.release_ceilings` list
seventeen ceilings by name and `service_transport` names `transport_timeout_ms_max`. The Factory
build fell on `ceilings.transport_timeout_ms_max`. The closure now carries exactly the seventeen
State 1 names, each `int`, equal to the `config.release_ceilings` keys. No contract, note or rule
used the seven names. Slices moved only where the model surface is shown; all 28 modules remain PASS.

