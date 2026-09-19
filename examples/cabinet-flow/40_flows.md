# State 4 — Cabinet Flow kernel key system flows

## Status

All planned flows below are reviewed against State 3 ownership. They expose
cross-module needs and do not yet freeze State 5 public APIs or State 6 Python
signatures. Every request named here has already entered through
`module:mcp_gateway` or `module:http_gateway` and `module:kernel_surface`; the
flow `flow:enter_kernel_surface` describes that entrance once and the other
flows start after it.

## `flow:start_kernel`

### Trigger

The operator starts the kernel process on the installation host.

### Boundary

`module:bootstrap` composes the kernel. `module:installation` validates the
host configuration, `module:operational_store` opens durability,
`module:semantic_vocabulary` holds the seed, `module:operation_bindings` checks
bindings against the manifest, `module:sandbox_supervisor` reports its health,
`module:run_executor` resumes work, and the two gateways open last.

### Steps

1. `capability:bootstrap.start_kernel` constructs every module and asks
   `capability:installation.release_ceilings`,
   `capability:installation.manifest_revision` and
   `capability:installation.resolve_service_target` to validate the whole
   configuration, including the refusal of mixed production and non-production
   targets.
2. Within `capability:operational_store.begin_unit_of_work` and
   `capability:operational_store.commit_unit_of_work`,
   `capability:semantic_vocabulary.seed_vocabulary` installs the seed when the
   registry is empty and changes nothing otherwise.
3. `capability:operation_bindings.sweep_manifest_drift` compares every accepted
   binding with `module:manifest_reader` and suspends or reissues it.
4. `capability:sandbox_supervisor.supervisor_health` must report that no earlier
   cleanup is unconfirmed.
5. `capability:run_executor.resume_runs` reconstructs every non-terminal run
   from durable records.
6. Only then `capability:mcp_gateway.serve_mcp` and
   `capability:http_gateway.serve_http` begin accepting requests.

### Outcomes

The kernel serves requests with validated configuration, a vocabulary, bindings
that agree with the manifest, a healthy supervisor and every earlier run back in
its true state; or it does not start and says why.

### Errors

`module:installation` owns invalid configuration, missing credential references
and mixed targets. `module:operational_store` owns an unavailable or
unmigrated store. `module:sandbox_supervisor` owns an unhealthy supervisor. Any
of them stops start-up before a gateway opens; a partial start never serves.

## `flow:enter_kernel_surface`

### Trigger

Any request arrives on the `mcp` or `http_api` channel.

### Boundary

`module:mcp_gateway` and `module:http_gateway` frame the channel.
`module:access_control` decides who is asking. `module:kernel_surface` owns the
closed operation catalogue and hands the request to the owning deep module.

### Steps

1. The gateway maps the channel request onto one catalogue operation:
   `capability:kernel_surface.inspect`, `capability:kernel_surface.author`,
   `capability:kernel_surface.request_trial`,
   `capability:kernel_surface.activate`, `capability:kernel_surface.run_flow` or
   `capability:kernel_surface.owner_decide`. An unknown operation, unknown field
   or oversized payload is refused here.
2. `capability:access_control.resolve_actor` resolves the authenticated channel
   identity to the owner or to one active delegation, using
   `capability:installation.resolve_credential` for the credential reference and
   `capability:system_clock.now` for throttling.
3. `capability:access_control.authorize_action` checks the kind of action
   against the actor: owner-only actions, authoring rights and the disclosure
   ceiling that later reads apply.
4. `module:kernel_surface` passes the typed request with its ActorRef to the
   owning module and returns that module's bounded typed result.

### Outcomes

The owning module receives a typed request with an accountable actor, or the
caller receives a uniform refusal that reveals nothing about what exists.

### Errors

`module:access_control` owns unauthenticated, revoked, throttled and
not-permitted refusals. `module:kernel_surface` owns malformed and unknown
requests. Neither gateway holds a rule of its own, and no internal error leaves
as a stack trace, a host path or a credential.

## `flow:manage_delegations`

### Trigger

The owner gives an agent access to the kernel, or takes it away.

### Boundary

`module:access_control` owns delegations. `module:installation` holds the
credential the delegation refers to.

### Steps

1. Through `capability:kernel_surface.owner_decide`, the owner calls
   `capability:access_control.issue_delegation` with the agent's label, channel,
   authoring right and disclosure ceiling; the record stores a credential
   reference and `capability:identity.mint_identity` gives it a stable identity.
2. `capability:access_control.revoke_delegation` ends a delegation before the
   next request. Runs it started continue under `module:run_executor`.
3. Each change is one `capability:operational_store.begin_unit_of_work` and
   `capability:operational_store.commit_unit_of_work`.

### Outcomes

An agent can act in the owner's name within stated limits, or can no longer act.
No delegation expresses an owner-only action.

### Errors

`module:access_control` refuses any attempt to issue or revoke by a non-owner,
and an unknown credential reference is refused by `module:installation`.

## `flow:extend_vocabulary`

### Trigger

A flow proof refused an edge for lack of a basis, or a valid output had no term,
and an agent or the owner proposes a new axis, term or relation.

### Boundary

`module:semantic_vocabulary` owns the registry and proposals.
`module:owner_authority` words the question for the owner.

### Steps

1. `capability:semantic_vocabulary.term_revision` and
   `capability:semantic_vocabulary.find_relation` show that the needed meaning
   or relation does not exist.
2. `capability:semantic_vocabulary.submit_proposal` records the candidate with
   its plain statement and the finding that motivated it.
3. `capability:owner_authority.owner_statement` presents the question in the
   owner's words, separate from any agent-supplied text.
4. The owner's `capability:semantic_vocabulary.decide_proposal` accepts it,
   issuing exactly one revision in one unit of work, or rejects it.
5. `capability:semantic_vocabulary.retire_entry` retires a term or relation that
   should no longer be cited, leaving recorded proofs intact.

### Outcomes

The vocabulary gains one accepted revision that edges may now cite, or stays
unchanged. A proposal is never usable as a basis.

### Errors

`module:semantic_vocabulary` owns duplicate-content refusal and the atomicity of
acceptance. `module:access_control` refuses a decision by anyone but the owner.

## `flow:author_function`

### Trigger

An agent with authoring delegation meets a need no function covers, or a slot
whose implementation must be replaced.

### Boundary

`module:slot_registry` owns slots, contract versions and code.
`module:trial_corpus` owns the cases. `module:identity` computes every
identity.

### Steps

1. Through `capability:kernel_surface.inspect`, the authoring view is
   composed from `capability:slot_registry.slot_authoring_view` for the slot,
   contract versions and submitted implementations,
   `capability:trial_corpus.active_corpus` for cases,
   `capability:slot_activation.serving_activation` and
   `capability:slot_activation.contract_health` for the current selection, and
   `capability:trace_journal.slot_evidence` for recent execution evidence, all
   within the actor's disclosure ceiling. No owning module fabricates the other
   modules' part of the view.
2. Through `capability:kernel_surface.author`, a new step calls
   `capability:slot_registry.create_slot` and
   `capability:slot_registry.issue_contract_version` after every port is
   verified against `module:semantic_vocabulary` and bounds are clamped to
   `capability:installation.release_ceilings`; the identity comes from
   `capability:identity.identify_contract_version`.
3. Through `capability:kernel_surface.author`,
   `capability:slot_registry.submit_implementation` stores the code bytes under
   the identity from `capability:identity.identify_implementation`. A caller's
   own identity is refused; equal bytes return the existing record.
4. Through `capability:kernel_surface.author`,
   `capability:trial_corpus.add_trial_case` adds typed cases, including fixture
   files, identified by `capability:identity.identify_trial_case` and stored
   through `capability:value_store.put_value` with
   `capability:identity.digest_value`.
5. Through `capability:kernel_surface.author`, a step that should never be used
   again is ended by `capability:slot_registry.retire_slot`; flow versions that
   pin it keep what they pinned.

### Outcomes

A contract version, an implementation and a non-empty corpus exist, ready for
trial. Nothing has run and nothing is active.

### Errors

`module:slot_registry` owns untyped ports, unknown schemas, unpermitted carriage
and a retired slot. `module:trial_corpus` owns a case that does not validate
against the ports. `module:identity` owns refusal of a supplied identity.

## `flow:admit_and_activate_function`

### Trigger

An agent requests trial of a submitted implementation and, once admitted, its
activation.

### Boundary

`module:admission` owns the verdict, `module:sandbox_supervisor` every
execution, `module:trial_corpus` the corpus, `module:slot_activation` the
selection.

### Steps

1. Through `capability:kernel_surface.request_trial`,
   `capability:admission.run_trial` takes `capability:trial_corpus.active_corpus`
   and runs the implementation on every case with
   `capability:sandbox_supervisor.execute_function`. A trial fixture remains a
   `StoredValue` of carriage `byte_stream`; admission supplies its validated
   bounded stream directly to the sandbox supervisor and never creates
   `SpooledBytes` for a trial.
2. `capability:admission.decide_admission` records the verdict with every
   applicable refusal reason. No actor can supply or alter it.
3. Through `capability:kernel_surface.activate`,
   `capability:slot_activation.activate_implementation` re-checks
   `capability:admission.current_admission` against the corpus as it stands and
   records the activation by compare-and-set.
4. `capability:slot_activation.serving_activation` now names the new
   implementation and `capability:slot_activation.contract_health` reports
   whether the contract version is `known_failing`.
5. When the change was a mistake,
   `capability:slot_activation.rollback_activation` records a new activation of
   an earlier implementation with a reason, provided it is admitted over the
   present corpus.

### Outcomes

The contract version is served by a new implementation, selected by hash, with
the earlier one kept; or admission is refused with reasons the agent can act on.

### Errors

`module:admission` owns an empty corpus, a missing trial execution and a
non-conforming trial. `module:sandbox_supervisor` owns denied attempts, bounds,
crashes and failed cleanup. `module:slot_activation` owns a stale admission, a
lost compare-and-set and a rollback to an implementation that fails a newer
case.

## `flow:repair_slot_from_failure`

### Trigger

A function node failed or produced a wrong result in a real run.

### Boundary

`module:trace_journal` holds what happened. `module:trial_corpus` makes the
failure permanent evidence. Authoring and admission then proceed as in
`flow:author_function` and `flow:admit_and_activate_function`.

### Steps

1. Through `capability:kernel_surface.inspect`,
   `capability:trace_journal.slot_evidence` gives the agent the recent node
   executions and trial executions of that one slot, within its ceiling and
   without the rest of the run.
2. Through `capability:kernel_surface.author`,
   `capability:trial_corpus.capture_trial_case` turns the failed execution into
   a case, copying a file input out of the live run through
   `capability:run_spool.describe_file`. A `personal_data` file is refused to
   the agent and is completed only through
   `capability:kernel_surface.owner_decide`.
3. Through `capability:kernel_surface.inspect`,
   `capability:slot_activation.contract_health` derives the current serving
   contract's health from `capability:trial_corpus.active_corpus` and
   `capability:trace_journal.slot_evidence`. It reports `known_failing` with
   the exact captured case while the same activation keeps serving; no mutable
   health record is written.
4. The agent authors a repaired implementation; it is admitted only by passing
   the grown corpus, and its activation clears `known_failing`.
5. When the contract itself must change, through
   `capability:kernel_surface.author`,
   `capability:trial_corpus.copy_cases_to_version` carries the still-valid
   cases to the new contract version.
6. Through `capability:kernel_surface.author`, a wrong unprotected case is
   removed from effect only by
   `capability:trial_corpus.withdraw_trial_case`; a protected case is refused
   to the agent and withdrawn only through
   `capability:kernel_surface.owner_decide`.

### Outcomes

The failure is a permanent case of the corpus and the slot is served by an
implementation that passes it.

### Errors

`module:trial_corpus` owns refusal of an agent's withdrawal of a protected case
and of a personal-data capture without the owner. `module:trace_journal` owns
the refusal to show another slot's executions.

## `flow:connect_service`

### Trigger

A service recorded in the platform manifest — the platform's own or a third
party's API — must become usable in flows, or the manifest changed.

### Boundary

`module:manifest_reader` projects the manifest. `module:operation_bindings` owns
bindings. `module:owner_authority` words the acceptance request. The agent
writes no network code.

### Steps

1. `capability:manifest_reader.manifest_operation` returns the operation's
   facts at the record's digest, and `capability:manifest_reader.service_instance`
   the instance the installation targets.
2. `capability:operation_bindings.propose_binding` records typed input and
   output ports, preview ports and the outcome-read binding; effect class,
   replay and idempotency key are copied from the manifest, and the identity
   comes from `capability:identity.identify_binding_version`.
3. `capability:owner_authority.owner_statement` states in plain words what the
   operation does, in which service, what it may change and which disclosure
   class each input accepts.
4. The owner's `capability:operation_bindings.accept_binding_version` makes the
   binding usable.
5. On a manifest change, `capability:operation_bindings.sweep_manifest_drift`
   uses `capability:manifest_reader.operation_facts_changed` to suspend the
   binding or reissue an identical version.
6. `capability:operation_bindings.retire_binding` ends a binding no flow should
   use again.

### Outcomes

A service operation is an operation node with typed ports the owner accepted, or
the proposal is refused because it disagrees with the manifest.

### Errors

`module:operation_bindings` owns a proposal contradicting the manifest, an
effectful binding without outcome-read or preview ports, and suspension.
`module:manifest_reader` owns an absent service, operation or instance.

## `flow:compose_and_activate_flow`

### Trigger

An agent composes function nodes and operation nodes to answer a request.

### Boundary

`module:flow_registry` owns flows and activations. `module:flow_proof` judges the
graph. `module:owner_authority` and the owner decide when the flow can change
anything.

### Steps

1. `capability:flow_registry.composition_view` gives the agent contracts,
   binding versions and the vocabulary, without implementation bodies.
2. `capability:flow_registry.create_flow` and
   `capability:flow_registry.register_flow_version` record the graph under the
   identity from `capability:identity.identify_flow_version`.
3. `capability:flow_proof.prove_flow` checks the whole graph — pinning, edge
   basis, carriage, cardinality, disclosure, inputs, cycles, reachability,
   guards — and reports every finding.
4. `capability:flow_registry.activate_flow_version` activates a proven read-only
   version by the kernel at once. For any other version it requires the owner,
   who sees `capability:owner_authority.owner_statement` naming every non-read
   node.
5. `capability:flow_registry.current_flow_activation` names the version that
   runs by default, and `capability:flow_registry.retire_flow` ends a flow.

### Outcomes

A proven flow version is runnable — immediately when it only reads, after the
owner's activation otherwise — or the agent holds the complete list of findings.

### Errors

`module:flow_proof` owns every proof finding. `module:flow_registry` owns
activation of an unproven version and an agent's attempt to activate an
effectful one.

## `flow:run_read_only_flow`

### Trigger

The owner or an agent runs an activated flow whose operation nodes only read,
such as taking third-party data and analysing it.

### Boundary

`module:run_executor` owns the run. `module:sandbox_supervisor` executes function
nodes, `module:operation_invoker` and `module:service_transport` operation
nodes, `module:value_store` and `module:run_spool` carry data,
`module:trace_journal` records.

### Steps

1. Through `capability:kernel_surface.run_flow`,
   `capability:run_executor.create_run` pins the flow activation, every
   `capability:slot_activation.serving_activation`, every
   `capability:operation_bindings.binding_for_invocation` and the
   `capability:installation.resolve_service_target`, and validates each input.
2. `capability:run_executor.advance_run` executes ready nodes. An operation node
   goes to `capability:operation_invoker.invoke_operation`, which sends one
   bounded request through `capability:service_transport.send_request` and
   validates the response against the output ports.
3. A function node goes to `capability:sandbox_supervisor.execute_function`.
   Files reach it through `capability:run_spool.receive_file` and
   `capability:run_spool.deliver_file`.
4. Each validated output is stored by `capability:value_store.put_value` with
   the class from `capability:value_store.derive_output_class`, and each
   concluded attempt is written by
   `capability:trace_journal.record_node_execution`, all in one unit of work per
   node.
5. `capability:run_executor.run_status` reports the run's state;
   `capability:trace_journal.run_trace` and `capability:value_store.read_value`
   return the result within the reader's disclosure ceiling.

### Outcomes

The run ends `succeeded` with validated outputs, `failed` with partial outputs
labelled partial, or rests `pending` while a service is unreachable. No state of
any service changed.

### Errors

`module:run_executor` owns invalid inputs, an unserved contract version, failure
propagation and the run's state. `module:sandbox_supervisor` owns execution
failures, `module:operation_invoker` refused, failed and unreachable operations,
`module:value_store` oversized values and `module:run_spool` unaccepted files.

## `flow:run_effectful_flow_with_approval`

### Trigger

The owner or an agent runs an owner-activated flow that changes something, such
as taking an invoice photo from one service and giving it into custody.

### Boundary

As in `flow:run_read_only_flow`, with `module:owner_authority` deciding whether
each effect is authorized now.

### Steps

1. The run is created and advances as in `flow:run_read_only_flow` until a node
   whose binding is `state-transition`, `external-effect` or `destructive`. A
   `draft-write` node proceeds without asking.
2. `capability:owner_authority.authorization_for_effect` finds an active
   standing grant for that node of that flow version, or
   `capability:owner_authority.request_approval` builds a preview — the purpose,
   instance, effect class, preview values and the file from
   `capability:run_spool.describe_file` — bound to the digest of all inputs; the
   run rests `awaiting_approval` and appears in
   `capability:owner_authority.waiting_for_owner`.
3. The owner's `capability:owner_authority.decide_approval` approves or denies.
   A mapped node receives one decision for the whole collection.
4. `capability:operation_invoker.invoke_operation` records the in-flight attempt
   durably, derives the idempotency key, and sends exactly the approved inputs.
5. `capability:owner_authority.grant_standing_approval` and
   `capability:owner_authority.revoke_standing_approval` let the owner stop or
   resume being asked for one non-destructive node of one flow version.
6. At the run's terminal state `capability:run_spool.release_run_files` empties
   the spool.

### Outcomes

The effect happened once, on exactly what the owner saw; or the owner denied it
and the run ended `refused` with no call made; or the run waits without limit.

### Errors

`module:owner_authority` owns a changed input that discards an approval, a grant
on a destructive node and any non-owner decision. `module:operation_invoker`
owns the service's refusal and an unknown outcome.

## `flow:recover_unknown_outcome_and_restart`

### Trigger

A response to an effectful call was lost, the kernel restarted during a run,
the long-lived `boundary:kernel_process` reaches a module-owned retry wake-up
for a pending run, or the owner cancels a waiting run. A wake-up only asks the
executor to re-evaluate durable state; elapsed time by itself never changes the
run's status or authorizes an effect.

### Boundary

`module:run_executor` owns resumption and the run's state.
`module:operation_invoker` finds out what happened by reading the owning service.

### Steps

1. `capability:run_executor.resume_runs` rebuilds each non-terminal run from
   durable records. A function node without a conclusion is executed again; an
   effectful node with an in-flight record and no conclusion is concluded
   `outcome_unknown`.
2. `capability:operation_invoker.reconcile_outcome` invokes the binding's read
   operation and records `effect_applied`, `effect_not_applied` or
   `still_undetermined`.
3. On `effect_applied` the service's validated outputs become the node's outputs
   and `capability:run_executor.advance_run` continues. On `effect_not_applied`
   the node may be attempted again under the declared replay behavior, asking the
   owner again for a `duplicates` operation. Otherwise the run keeps resting and
   reconciliation repeats with back-off timed by `capability:system_clock.now`.
4. `capability:run_executor.cancel_run` lets the owner end a waiting run; the
   record states whether an effect's outcome was still undetermined.

### Outcomes

The run continues from what truly happened, without a second effect and without
losing an input, an approval or a value.

### Errors

`module:operation_invoker` owns an unreachable read operation and refuses to
treat a service's free text as evidence. `module:run_executor` owns the refusal
to execute a dependant on a guess.

## `flow:expire_evidence`

### Trigger

The long-lived `boundary:kernel_process` starts a bounded maintenance sweep
when stored-content retention deadlines may have elapsed. The sweep is
idempotent and may run again after restart.

### Boundary

`module:value_store` owns retention of values. `module:run_spool` owns files of
runs that ended.

### Steps

1. `capability:value_store.expire_values`, using `capability:system_clock.now`,
   removes the content of `run_evidence` values past their period — sooner for
   `personal_data` — keeping digest, term, schema and class, and never touching
   a value named by a non-terminal run, a trial case or an approval.
2. `capability:run_spool.release_run_files` removes any file of a run that
   reached a terminal state.
3. `capability:operational_store.rollback_unit_of_work` leaves everything
   unchanged when a sweep cannot complete.

### Outcomes

The kernel still explains every run by digests and verdicts, and holds no
content longer than the rules allow.

### Errors

`module:value_store` owns the refusal to expire anything still required.
