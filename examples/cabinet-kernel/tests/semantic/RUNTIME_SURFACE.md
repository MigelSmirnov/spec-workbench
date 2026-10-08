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

## Named capabilities

What a test needs beyond the calls: the Factory fixture provides each as
an attribute of `semantic_runtime` under this name. Each is used only by
the witnesses the next section lists for it.

| capability | meaning |
|---|---|
| `installation` | the installation's configuration file: `owner_token`, `agent_token(name)`, `set_agent_tokens([AgentToken])`, `set_owner_token(token)`, `write_config_text(text)`, `set_config_mode(mode)`, `select_instance(service_id, instance_name)`, `set_credential(service_id, header_name, secret_value)` (writes an owner-only secret file and its reference; `None` references a missing file), `write_secret(service_id, value)`, `set_manifest_revision(revision)` |
| `clock` | the kernel clock (`clock.kernel_now`) injected by the fixture: `set(epoch_us)`, `advance(ms=0, days=0)`; `fix_monotonic(ns)` fixes its monotonic source |
| `mcp_request(operation, request, *, token=None, raw=None)` | one request over the MCP entrance: `request` the fields as sent, unknown ones included, `token` (default: the actor's), `raw` exact bytes; returns the answer or raises with `code` and `reason` |

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
