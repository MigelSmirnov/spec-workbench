# `semantic_runtime` — the fixture surface the witness tests use

The tests in this directory are the witnesses of the accepted decisions
(`[witness: verification:kernel_aNN_*]` in the Required tests). They are
written before the kernel is generated and never rewritten to fit it. The
Factory project supplies the `semantic_runtime` pytest fixture and binds each
call below to the generated public operations; the assertions stay as written.

This file is the one list of that surface. A test calls nothing that is not
listed here; a test that needs a new call adds it here first, in the same
change.

## Conventions

- **Names.** A call is named after the State 5 public operation it reaches
  (`50_public_apis.md`, without the module prefix); its arguments are the
  operation's Inputs, named and shaped as the State 6 models
  (`60_model_closure_*.json`) — a model is passed as a dict of its fields, an
  enum as its value string.
- **Results.** A call returns the operation's output model; tests read its
  fields by name. An enum field may come back as an enum or its value string:
  tests compare `getattr(x, "value", x)`.
- **Refusals.** A refusal raises; the test reads its code (State 5, "Closed
  set of refusal codes") as `exc.code` through `pytest.raises`.
- **Store.** Each test gets a fresh, empty kernel store.
- **Actor.** The fixture acts as the actor the MCP surface would determine
  (State 5 catalogue): an author agent for `issue_contract_version`, the owner
  for owner-only operations; a test that is about the actor passes `actor=`
  explicitly.
- **What the fixture fills in.** Only what the tested decision does not depend
  on, and each such default is named below.
- **Installation.** The fixture installs the kernel with the owner, agent
  `author` (with the author right) and agent `helper` (without it), no
  service selected, no credential and an empty manifest. `actor=` takes an
  Actor M27 dict (`{"kind": "owner", "agent_name": None}`, `{"kind":
  "agent", "agent_name": "author"}`). When omitted, the actor is the owner for
  every operation the owner may call (State 5 catalogue), otherwise agent
  `author`.
- **Refusal reason.** A refusal carries `exc.reason` beside `exc.code`
  (RefusalAnswer). A test reads the reason only where a decision makes it
  name something (A02 rule 2: the field).
- **Kernel start.** The kernel starts at the first call or capability that
  needs it. A capability that configures the installation or the manifest
  shapes that start when used before it, and takes effect at
  `restart()` when used after — except the token list, which the kernel
  re-reads before each request (A16 rule 2).
- **Values in requests** are JSON text (`json_text`) and files base64 text,
  as the State 6 request models (`RequestJsonValue`, `RequestFile`,
  `RequestFileList`, `RequestConstant`); answers are the MCP surface's answer
  models (`handle_*` in `60_contracts.json`), masked for an agent under A07
  rules 4–5. Lists read through `page_records` come newest first (A16 rule
  6).

## Calls

| call | operation | defaults the fixture supplies |
|---|---|---|
| `issue_contract_version(slot_id, purpose, inputs, outputs)` → `contract_version_id` | `functions.issue_contract_version` | resource bounds within the installation's ceilings (A02 rule 2 refuses omitted ones) when `resource_bounds` is not given; `resource_bounds=` (ResourceBoundsRequest) is sent as given, a field set to `None` omitted from the request |
| `compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges, constants)` → ComposedFlowVersion | `flows.compose_flow_version` | — |
| `prove_flow_version(flow_version_id)` → ProofResult (M17) | `flows.prove_flow_version` | — |
| `add_trial_case(contract_version_id, inputs, expected_outputs=None)` → ShownAddedTrialCase | `functions.add_trial_case` | — |
| `submit_implementation(contract_version_id, code)` → ShownSubmission | `functions.submit_implementation` | — |
| `roll_back_slot(slot_id, implementation_id)` → Activation (M09) | `functions.roll_back_slot` | — |
| `read_slot(slot_id)` → SlotHistory | `functions.read_slot` (MCP `get_slot`) | — |
| `read_contract_version(contract_version_id)` → ContractVersion (M03) | `functions.read_contract_version` | — |
| `read_implementation(implementation_id)` → ShownImplementationRead | `functions.read_implementation` | — |
| `active_flow_version(flow_id)` → FlowAnswer | `flows.active_flow_version` (MCP `get_flow`) | — |
| `page_records(record_type, record_filter=None, page_size=None, continuation_token=None)` → RecordPageAnswer | `store.page_records` (MCP `list_records`) | `page_size_default` when `page_size` is not given (A16 rule 6) |
| `try_implementation(implementation_id, trial_case_ids=())` → tuple[ShownTrialExecution] | `functions.try_implementation` | — |
| `activate_flow_version(flow_version_id)` → FlowActivation (M18) | `flows.activate_flow_version` | — |
| `start_run(flow_id, inputs)` → ShownRun | `runs.start_run` | — |
| `capture_failed_execution(execution, contract_version_id)` → ShownTrialCase | `runs.capture_failed_execution` | — |
| `get_repair_view(slot_id, page_size=None, continuation_token=None)` → RepairView | MCP `get_repair_view` (State 5 catalogue: `functions.read_slot`, `read_contract_version`, `read_implementation`, `store.page_records`) | `page_size_default` when `page_size` is not given |
| `propose_binding(service_id, operation_name, inputs, outputs)` → OperationBinding (M11) | `bindings.propose_binding` | — |
| `accept_binding(binding_id)` → OperationBinding (M11) | `bindings.accept_binding` | — |
| `continue_after_approval(approval_id, decision)` → ShownRun | `runs.continue_after_approval` (MCP `decide_effect_approval`) | — |
| `grant_standing_approval(flow_id, node_id)` → StandingGrant (M25) | `effects.grant_standing_approval` | — |
| `read_run(run_id)` → ShownRun | `runs.read_run` (MCP `get_run`) | — |
| `read_binding(binding_id)` → OperationBinding (M11) | `bindings.read_binding` (MCP `get_binding`) | — |
| `resume_run(run_id)` → ShownRun | `runs.resume_run` | — |
| `continue_after_resolution(attempt, resolution)` → ShownRun | `runs.continue_after_resolution` (MCP `resolve_unknown_outcome`) | — |
| `cancel_run(run_id)` → ShownRun | `runs.cancel_run` | — |
| `revoke_standing_approval(grant_id)` → StandingGrant (M25) | `effects.revoke_standing_approval` | — |

## Named capabilities

What a test needs beyond the calls: the Factory fixture provides each as
an attribute of `semantic_runtime` under this name. Each is used only by
the witnesses the next section lists for it.

| capability | meaning |
|---|---|
| `installation` | the installation's configuration file: `owner_token`, `agent_token(name)`, `set_agent_tokens([AgentToken])`, `set_owner_token(token)`, `write_config_text(text)`, `set_config_mode(mode)`, `select_instance(service_id, instance_name)`, `set_credential(service_id, header_name, secret_value)` (writes an owner-only secret file and its reference; `None` references a missing file), `write_secret(service_id, value)`, `set_manifest_revision(revision)` |
| `clock` | the kernel clock (`clock.kernel_now`) injected by the fixture: `set(epoch_us)`, `advance(ms=0, days=0)`; `fix_monotonic(ns)` fixes its monotonic source |
| `mcp_request(operation, request, *, token=None, raw=None)` | one request over the MCP entrance: `request` the fields as sent, unknown ones included, `token` (default: the actor's), `raw` exact bytes; returns the answer or raises with `code` and `reason` |
| `restart()` | stop the kernel process and start it again on the same data directory and configuration; returns StartOutcome (`started`, `exit_code`, `stderr`) |
| `kernel_exited()` | the exit status of the kernel process when it ended on its own since its last start, `None` while it runs |
| `host` | host conditions for the next start: `remove_bubblewrap()`, `set_env(name, value)` |
| `sandbox_executions()` | per sandbox execution, observed from outside it: `network_interfaces`, `mounts` (host paths), `exchange_directory`, `processes_left` after completion |
| `sandbox_runtime_paths()` | the host paths the release mounts read-only as the sandbox runtime |
| `faults` | injected faults: `unconfirmed_cleanup(nth=1)` (the nth sandbox execution from now cannot confirm its cleanup), `fail_store_change(change_name)`, `crash_during_value_write()`, `place_symlink(relative_path, target)` |
| `manifest` | the platform manifest the installation reads: `write_record(service_id, record, *, revision=None, file_name=None)` writes a record shaped as State 6 ManifestServiceRecord without `record_digest` in the platform's raw form (instance class as `class`, instances keyed by name; extra members of a capability, such as `note`, and an `exposed_as` without `http_api` written as given) at `revision` (default: the configured one) under `file_name` (default `<service_id>.json`); `write_record_text(...)` writes raw text; `new_revision()` makes a later revision starting as a copy of the configured one |
| `stub_service()` | an HTTP service on loopback: `base_url`, `authority`; `on(method, path, status=200, json=None, body=None, headers=None, action=None)` sets the answer of a route, `action` one of `drop_after_request` (close after reading the request, no status line), `refuse_connection`, `redirect` (with `Location` in `headers`), `kill_kernel` (SIGKILL the kernel once the request arrived, before answering), `hold`; `set_down(flag)`; `requests` (method, target, headers as on the wire, body, peer) |
| `store_dump()` | every byte the store holds (database and value area), for "appears in no record" |
| `KernelStopped` | the exception a call in progress raises when the fixture killed the kernel under it |

## Places the surface cannot reach yet

A Required test that cannot be stated through the calls above, and needs a
capability rather than a call (a stub service, a kernel restart, a process
observer), is listed here with its witness and the capability it needs. It
is not written around.

| witness | capability needed |
|---|---|
| `kernel_a01_equal_submission_returns_existing` | `installation` (a second author agent), `clock` (two submissions at known, different times) |
| `kernel_a01_caller_supplied_identity_refused` | `mcp_request`: a request carrying a field no call has (`contract_version_id`) |
| `kernel_a01_equal_contract_not_made_current` | `clock` (the first issue time stays) |
| `kernel_a01_activation_identity_is_store_position` | `clock` (an activation asked again keeps its time) |
| `kernel_a03_deadline_and_limits_classified` | `sandbox_executions()`: no process survives an execution |
| `kernel_a03_kernel_refuses_start_without_sandbox` | `host.remove_bubblewrap()`, `restart()`: a start on a host without `bubblewrap` |
| `kernel_a03_fresh_env_no_network_no_host_mounts` | `sandbox_executions()`, `sandbox_runtime_paths()`: the environment inspected from outside |
| `kernel_a03_unconfirmed_cleanup_stops_kernel` | `faults.unconfirmed_cleanup()`, `kernel_exited()`, `restart()`: a cleanup that cannot be confirmed, and the process stopping |
| `kernel_a04_verdict_set_only_by_kernel` | `mcp_request`: requests carrying a verdict field, by the owner and by an author |
| `kernel_a05_proof_recomputed_on_demand` | `manifest.write_record`, `installation.select_instance`, `stub_service()`: an accepted binding needs a manifest record and a selected instance |
| `kernel_a05_highest_effect_class_max_or_read` | `manifest.write_record`, `installation.select_instance`, `stub_service()` |
| `kernel_a06_effectful_flow_owner_only_activation` | `manifest.write_record`, `installation.select_instance`, `stub_service()` |
| `kernel_a06_activation_proves_version_again` | `manifest.write_record`, `installation.select_instance`, `stub_service()` |
| `kernel_a06_new_version_inherits_nothing` | `manifest.write_record`, `installation.select_instance`, `stub_service()`; `stub.requests` (nothing sent without approval) |
| `kernel_a07_proof_refuses_class_above_accepted` | `manifest.write_record`, `installation.select_instance`, `stub_service()` |
| `kernel_a07_agent_gets_personal_data_as_digest` | `manifest.write_record`, `installation.select_instance`, `stub_service()` |
| `kernel_a07_preview_hides_personal_data_from_agent` | `manifest.write_record`, `installation.select_instance`, `stub_service()` |
| `kernel_a08_invocable_only_single_http_route` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential` |
| `kernel_a08_non_read_key_field_must_be_input_port` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential` |
| `kernel_a08_digest_covers_only_own_capability_entry` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `manifest.new_revision`, `installation.set_manifest_revision`, `restart()` |
| `kernel_a08_changed_digest_stale_nothing_sent` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `manifest.new_revision`, `installation.set_manifest_revision`, `restart()`, `stub.requests` |
| `kernel_a08_record_read_only_at_pinned_path` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `manifest.write_record(file_name=, revision=)`, `manifest.new_revision` |
| `kernel_a08_several_http_routes_not_invocable` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential` |
| `kernel_a09_possibly_sent_outcome_unknown_no_retry` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `drop_after_request`, `stub.requests` |
| `kernel_a09_read_5xx_service_unreachable` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a09_non_read_4xx_not_applied` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a09_non_read_2xx_applied_even_if_invalid` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a09_no_redirect_plain_http_restricted` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, two stubs, stub action `redirect`, `stub.requests` |
| `kernel_a09_credential_echo_error_body_withheld` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests`, `store_dump()` |
| `kernel_a09_credential_echo_2xx_no_output_stored` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests`, `store_dump()` |
| `kernel_a09_read_unsent_or_unanswered_unreachable` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub actions `refuse_connection` and `drop_after_request`, `stub.requests` |
| `kernel_a10_gated_send_waits_for_approval` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a10_approval_scoped_per_element` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a10_grant_authorizes_never_destructive` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a10_revoked_grant_no_longer_authorizes` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a10_only_owner_decides_grants_revokes` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential` |
| `kernel_a10_approval_bound_to_request_digest` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.set_down`, `manifest.new_revision`, `installation.set_manifest_revision`, `installation.write_secret`, `restart()` |
| `kernel_a10_used_approval_and_grant_do_not_cover_resend` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `drop_after_request`, `stub.requests` |
| `kernel_a10_no_decision_changes_nothing` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `clock.advance` (days pass) |
| `kernel_a10_grant_bound_to_flow_version` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `stub.requests` |
| `kernel_a11_restart_turns_in_flight_unknown` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `kill_kernel`, `KernelStopped`, `restart()` |
| `kernel_a11_applied_no_outputs_succeeds_one_execution` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `drop_after_request` |
| `kernel_a11_not_applied_fresh_approval_next_attempt` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `drop_after_request` |
| `kernel_a11_applied_with_outputs_fails_element` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `drop_after_request` |
| `kernel_a11_unknown_blocks_dependants` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `drop_after_request`, `clock.advance`, `restart()` |
| `kernel_a11_attempt_number_is_execution_ordinal` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, stub action `drop_after_request` |
| `kernel_a12_pins_survive_later_records` | `manifest.write_record`, `installation.select_instance`, `stub_service()`, `installation.set_credential`, `clock.advance` (a long wait for approval) |
