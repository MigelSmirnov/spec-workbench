# State 4 — Cabinet Kernel reviewed flows

## Status

Draft of 2026-10-03. The flows of the owner-accepted `40_flow_plan.json`, walked
against the State 3 ownership of `30_modules.md`. They name who triggers, what
crosses each boundary, who decides next, who produces each result and each
failure. They do not yet freeze State 5 public APIs or State 6 Python
signatures; the names of store calls stay the closed set `record_change` of
State 3.

Every flow enters through `module:surface`, which handles one request at a time
to its end (A18 rule 3) and applies A16 rule 1 in its order — size, token,
operation schema, actor — before any operation's own check. A refusal there
reaches no other module and records nothing. A request naming a record that
does not exist is refused as an unknown reference by the module that owns the
record, recording nothing (State 0) — except in the inspection, trace and
repair reads `module:surface` assembles from `store` itself, where `surface`
gives that refusal (State 3, "Inspection, traces and the repair view"); the closed set of refusal codes is State
5's (K-17). Every identity of a content record
is computed by the module that writes it through `module:canonical_values` (A01
rule 1); an equal submission returns the existing record and records nothing for
it (A01 rule 4). A flow references `module:canonical_values` only where its own
steps compute an identity, fit a value to a port or compare disclosure classes.

Every record is written through `module:store`, one call and one transaction
(K-17). A flow references `module:store` only where its own steps use a
capability of it beyond that: reading records, value bytes, the spool, paging,
the start. A step that says "writes" means one such store call by the module
named; a store call that fails changes nothing (A18 rule 3) and the request
is answered as an internal error by `module:surface` (A16 rule 7). Every
timestamp a step records comes from `module:clock`; a flow
references the clock where a step stamps a time it names or sets a deadline.
`module:installation` is referenced wherever its facts are read: the token list
for every request, the manifest source and selected instances, credentials.

## `flow:author_and_admit_function`

### Trigger

An agent with the author right issues a contract version, adds trial cases to
it and submits an implementation; any agent may then try a submitted
implementation on the corpus — trying names an existing implementation and
never runs code that was not submitted (A04 rule 6; State 0, A16 rule 3).

### Boundary

`module:surface` checks the request's token against
`capability:installation.current_token_list` (A16 rules 1–2) and admits the request and decides only whether the caller may make
it. `module:functions` owns every rule of the flow: the contract version and its
ceilings (A02), the slot and its purpose (A01 rule 5), the trial cases and the
corpus (A04 rule 1), trying, admission and the kernel's activation (A04 rules
2–4, 6). `module:sandbox` executes the agent's code and owns how an execution
ends (A03). `module:canonical_values` computes identities, fits values to
ports and orders disclosure classes; it decides nothing about what a failed fit
means. `module:store` holds every record and every byte; it decides
nothing.

`module:installation` gives the current token list; `module:clock` the
sandbox's deadline and the records' times.

Crossing models: the request's contract content enters `module:functions` and
leaves as ContractVersion M03 (and Slot M02 when new); trial values enter as
port values and leave as TrialCase M06 and StoredValue M21; implementation code
enters and leaves as Implementation M05; one implementation, one case's inputs
and the contract's ResourceBounds M04 cross into `module:sandbox`, and one
execution outcome with its outputs crosses back; TrialExecution M07,
AdmissionVerdict M08 and Activation M09 are written by `module:functions`.

### Steps

1. **Issue a contract version.**
   `capability:functions.issue_contract_version` takes the contract content.
   It checks the purpose rule first (A01 rule 5: a new slot name needs a
   purpose; an existing slot refuses a different one), then the A02 rule 1
   conditions in their order, naming the first failure; a bound above its
   ceiling or omitted is refused, never clamped (A02 rule 2). It computes
   `contract_version_id` with `capability:canonical_values.content_identity`; an equal version is returned unchanged and does not
   become current again (A01 rule 4). Otherwise one
   `capability:store.record_change` writes the ContractVersion, and the Slot
   when the name is new, and makes it the slot's current contract version.
   The answer is the version with its identity. Next decision: the agent's.
2. **Add trial cases.** `capability:functions.add_trial_case` takes a contract
   version and the case's input values, expected outputs optional. It checks
   each value against its port with `capability:canonical_values.fit_port_value`,
   ports in name order — presence, carriage, schema,
   size — and the size ceilings `stored_value_bytes_max` and
   `trial_fixture_bytes_max`, naming the first failure (A04 rule 1). A
   request field over those bounds never gets here: `module:surface` refuses
   it at schema validation (A16 rule 4); the check of `module:functions`
   decides for the canonical value and for captured cases, which do not
   arrive as a request field. Value
   bytes and file fixtures go to the content-addressed area through
   `capability:store.put_value_bytes`, which stores equal bytes once (A18 rule
   4); `module:functions` writes their StoredValues — an input with the class its
   contract input port declares, an expected output with the highest class of
   the case's inputs (M21, A07 rule 3) — and the TrialCase in one
   `capability:store.record_change`. The case's place in the corpus is the
   store's order of first addition; an equal case is that case and keeps its
   place. Next decision: the agent's.
3. **Try an implementation (optional, any agent).**
   `capability:functions.try_implementation` names an existing implementation
   and optionally cases. Unknown cases, cases of another contract version, a
   case named twice and an empty corpus (`empty_corpus`) are refused before
   anything executes (A04 rule 6). Each case, in corpus order, is one call of
   `capability:sandbox.execute_function` with the implementation's code, the
   case's inputs and the contract's bounds; the sandbox sets its wall deadline
   with `capability:clock.monotonic_deadline` and returns one outcome of
   the closed A03 rule 5 order and, on success, outputs that fit the output
   ports. `module:functions` stores the outputs through
   `capability:store.put_value_bytes` with the highest class of the case's
   inputs, computed by `capability:canonical_values.highest_disclosure_class`
   (A07 rule 3), compares them with the expected outputs by digest (A04
   rule 3) and writes one TrialExecution per case. No verdict, no activation.
   The answer is the trial evidence per case.
4. **Submit an implementation.** `capability:functions.submit_implementation`
   takes code for one contract version and computes `implementation_id` from
   the code with the contract version (K-04). A new implementation is written;
   an equal one is that implementation, first submitter kept (A01 rule 4). It
   then reads the corpus in store order through
   `capability:store.read_records` and computes the current corpus digest
   (A04 rule 2):
   - when an AdmissionVerdict for this implementation and this digest exists,
     that verdict is used and nothing executes;
   - otherwise admission runs every case of the corpus in corpus order, each
     through `capability:sandbox.execute_function` and recorded as one
     TrialExecution as in step 3, never stopping early; the verdict is
     `admitted` exactly when the corpus is non-empty and every case passed,
     else `refused` with `empty_corpus` or the first failing case and its
     outcome (A04 rule 3), and is written by `module:functions`.
5. **Activate what is admitted.** On `admitted`, `module:functions` asks
   `capability:functions.current_activation` for the slot's contract version;
   when the implementation is not already current, it writes an Activation by
   the kernel, stamped with `capability:clock.kernel_now`, in the same request (A04 rule 4, K-15: the kernel is the actor).
   When it is already current, nothing is recorded. On `refused`, nothing is
   activated and the current activation keeps serving.
6. `module:surface` returns the implementation with its verdict and, when one
   was written or already current, its activation.

### Outcomes

- A contract version with its identity — new, or the existing equal one; a new
  slot name creates the slot. Produced by `module:functions`.
- A trial case with its identity and corpus place. Produced by
  `module:functions`.
- Trial evidence per case: outcome, output digests, pass or
  `output_mismatch`. Produced by `module:functions` from outcomes produced by
  `module:sandbox`.
- An implementation with its AdmissionVerdict, and when admitted an Activation
  by the kernel, so the slot serves the new code at once. Verdict and
  activation produced by `module:functions`; no human records, edits or waives
  either (A04 rule 8).
- Nothing in this flow touches a service, a flow or a run.

### Errors

- Size, token, schema and actor refusals: produced by `module:surface` before
  any operation (A16 rules 1, 3, 4); an agent without the author right asking
  to issue, add or submit is refused there. A caller-supplied content identity
  is refused by the operation (A01 rule 1).
- A trial value or fixture over its bound as a request field: refused by
  `module:surface` at schema validation, before `module:functions` (A16
  rule 4).
- Purpose, ceiling, port and case-fit refusals, unknown or foreign cases,
  `empty_corpus`: produced by `module:functions`, which names the first failing
  condition of the rule's order. Each refusal records nothing.
- A refused verdict is a result, not an error: it names the first failing case
  and its outcome (`timeout`, `resource_exhausted`, `sandbox_violation`,
  `crashed`, `contract_violation` from `module:sandbox`, or `output_mismatch`
  from `module:functions`). No failure is ever success (State 0).
- Cleanup duty: `module:sandbox` completes an execution only after every
  process is reaped and the exchange directory removed. If it cannot confirm
  that, it reports the execution `crashed` with `cleanup_failed`, output
  discarded (A03 rule 7), and stops nothing itself. `module:functions` writes
  that TrialExecution, then executes no further case and writes no verdict and
  no activation; `module:surface` answers with an internal error and ends the
  process (State 3, "Unconfirmed cleanup"). What was written stays; the next
  submission of the same implementation finds no verdict and runs admission
  again (A04 rule 2).
  No spool is involved: trial values live in the content-addressed area.
- `module:surface` translates every refusal into an answer that carries no
  host path, credential or stack trace (A16 rule 7); an agent receives a
  `personal_data` value of a case or a classified `failure_detail` only as
  digest or length and class (A07 rules 4 and 5).

## `flow:propose_and_accept_binding`

### Trigger

An agent proposes an operation binding for one operation of one service; the
owner accepts it, or leaves it proposed (State 0 question 6).

### Boundary

`module:surface` checks the request's token against
`capability:installation.current_token_list` (A16 rules 1–2) and admits the request: any agent may propose, only the owner
accepts (A16 rule 3). `module:bindings` owns reading the manifest record, the
proposal checks in their order, the digest pin and acceptance (A08).
`module:service_invoker` owns the request-shape rules a binding's ports must
satisfy (A09 rules 2 and 3) and offers them to `module:bindings`; it sends
nothing in this flow. `module:canonical_values` computes the digest of the
operation's capability entry.

`module:installation` gives the token list, the manifest source and the
selected instance.

Crossing models: the proposal — `service_id`, operation name and ports with
their schemas and classes — enters `module:bindings`; the ports cross into
`module:service_invoker` with the operation's method and path and come back as
a shape verdict; the capability entry crosses into `module:canonical_values` and
comes back as `record_digest`; Binding M11 is written by `module:bindings`. The
manifest location and revision fixed at start (M28) and the selected instance
come from the installation.

### Steps

1. **Propose.** `capability:bindings.propose_binding` takes service, operation
   and ports. The proposer states no effect class and no key fields; a request
   that does is refused, because both are copied from the manifest (M11, A08
   rule 5). It refuses a malformed `service_id` before a path is built, reads
   `<manifest_location>/<service_id>.json` at the configured revision, both
   from `capability:installation.manifest_source` (A08 rule 1), and runs the A08 rule 5 checks in their order, naming the first
   failing one: record, duplicate entry names, operation present, effect class
   one of the five, invocable (A08 rule 3, A09 rule 1), the instance
   `capability:installation.selected_instance_name` selects, with an
   `api_base_url` and no repeated required header, key fields (A08 rule 4),
   request shape through `capability:service_invoker.check_request_shape`, then
   the contract-port rules and classes of M01.
2. **Pin.** `module:bindings` computes `record_digest` of the one capability
   entry with `capability:canonical_values.content_identity` (A08 rule 2),
   mints `binding_id` (A01 rule 2) and writes the Binding `proposed` with
   effect class, key fields and digest copied from the manifest. The answer
   is the proposed binding. Next decision: the owner's.
3. **Inspect.** The owner, or any agent, reads the proposal through
   `capability:bindings.read_binding`, as `module:surface` returns it.
4. **Accept.** `capability:bindings.accept_binding`, owner only: an unknown
   `binding_id` is refused; an `accepted` binding is returned unchanged; a
   `proposed` one is read against the manifest again as before a send (A08
   rule 6) and, on the first failing check in A08 rule 5 order, refused naming
   it — `binding_stale` when only the digest differs (A08 rule 7). Otherwise it
   becomes `accepted`. Next decision: the agent's, who composes a flow version
   that names it (`flow:compose_prove_activate_flow`); a version whose proof
   failed only because this binding was `proposed` is proven again without a
   new version (A05 rule 6).

### Outcomes

- A proposed binding with its identity, effect class, key fields and pinned
  digest. Produced by `module:bindings`.
- An accepted binding. Produced by `module:bindings`; only the owner's request
  reaches this step.
- A proposal the owner never accepts stays proposed; nothing expires it.
- The manifest is never written (A08 rule 8); no service is called.

### Errors

- Actor refusal: an agent's acceptance is refused by `module:surface` before
  `module:bindings` sees it (A16 rule 3).
- Manifest mismatch on proposal, and the same checks on acceptance, with
  `binding_stale` for a changed digest: produced by `module:bindings`, the
  first failing check named. A request-shape failure is judged by
  `module:service_invoker` and reported by `module:bindings` as that check.
- A refusal records nothing. No cleanup duty: the flow writes one record at
  most and opens no file but the manifest record, read only.

## `flow:compose_prove_activate_flow`

### Trigger

An agent composes a flow version and asks for its proof; the agent or the owner
asks to activate a proven version.

### Boundary

`module:surface` checks the request's token against
`capability:installation.current_token_list` (A16 rules 1–2) and admits the request: any agent composes and proves; the owner
or any agent asks to activate, an agent only a `read` version (A16 rule 3,
A06). `module:flows` owns composition with its pre-proof refusals, the purpose
rule for flows, the nine-phase proof, the highest effect class and activation
(A05, A06), and the proof-time reach of classes (A07 rule 2).
`module:functions` answers which contract version a function node names;
`module:bindings` answers a binding's status and declared classes.
`module:canonical_values` computes the version's identity, compares schemas by
canonical form and orders classes.

`module:installation` gives the token list.

Crossing models: the version content — nodes, edges, guards, constants, flow
ports, purpose — enters `module:flows` and is written as FlowVersion M13 with
its nodes and edges (M14–M16) and its constants' StoredValues M21; ContractVersion
M03 and Binding M11 cross up into the proof by read; ProofResult M17 leaves as
the answer and is not stored; FlowActivation M18 is written by `module:flows`.

### Steps

1. **Compose.** `capability:flows.compose_flow_version` checks the purpose
   rule first (A01 rule 5: a new flow name needs a purpose and creates the
   flow), then the pre-proof refusals of A05 rule 7 in their order — repeated
   node ids, repeated flow port names, a `file` flow port, a flow input without
   a class, a flow output with one. A refused composition is not a version and
   records nothing. Otherwise it computes `flow_version_id` with
   `capability:canonical_values.content_identity`, sorting order-free lists as
   A01 rule 1 says; an equal version is returned unchanged. A new version is
   written with its constants, each with the class the agent declared (A07
   rule 3).
2. **Prove.** `capability:flows.prove_flow_version` runs the nine phases of
   A05 rule 1 in their fixed order and returns the first failure with its
   phase, node or edge and reason, or `proven`. Phase 1 reads each function
   node's contract version through
   `capability:functions.read_contract_version` and each operation node's
   binding through `capability:bindings.read_binding`, which must be
   `accepted`. Phase 3 compares schemas as equal canonical JSON (A05 rule 2).
   Phase 8 computes the class that can reach each source (A07 rule 2) with
   `capability:canonical_values.highest_disclosure_class` and refuses an edge
   into an input accepting less. The proof also yields the highest effect
   class (A05 rule 5). The answer is the version with its proof result; the
   version is kept either way. Next decision: the agent's — fix and compose
   again, or ask to activate.
3. **Activate.** `capability:flows.activate_flow_version` checks in A06 rule 4
   order: it proves the version again and refuses an unproven one with its
   failure; it refuses an agent asking for a version above `read`, even an
   already active one, and keeps nothing for the owner; it returns the active
   activation unchanged when the version already is active, read through
   `capability:flows.active_flow_version`; otherwise it writes a FlowActivation
   that replaces the previous one at once — by the kernel when the highest
   effect class is `read`, by the owner otherwise. Runs already started keep
   their pinned version (A12 rule 2). Next decision: whoever runs the flow
   (`flow:run_read_only_flow`, `flow:run_effect_with_approval`), and for an
   effectful flow the owner, who may grant standing approvals for its nodes.

### Outcomes

- A flow version with its identity, kept whether proven or not. Produced by
  `module:flows`.
- A proof result: `proven` with the highest effect class, or the first failure.
  Produced by `module:flows`, computed on demand and not stored (A05 rule 6).
- The flow's active version and its FlowActivation naming the kernel or the
  owner as actor (K-15). Produced by `module:flows`.
- A new version inherits no activation, approval or grant (A06 rule 5).

### Errors

- Actor and schema refusals: `module:surface` (A16 rules 1, 3, 4). An agent's
  activation of an effectful version is not an actor refusal: it depends on the
  record named and is refused by `module:flows` (A16 rule 1, A06 rule 3).
- A constant over `stored_value_bytes_max` as a request field: refused by
  `module:surface` at schema validation (A16 rule 4), before composition.
- Purpose and pre-proof refusals: `module:flows`, recording nothing. A
  constant whose value does not fit its port is a proof failure of phase 2,
  not a composition refusal (A05 rules 1 and 7).
- A proof failure is a result, not an error; activation turns it into a
  refusal with the same failure. `module:functions` and `module:bindings`
  only answer reads; they decide nothing for the proof.
- No cleanup duty: composition and activation are single store calls; a proof
  writes nothing.

## `flow:run_read_only_flow`

### Trigger

The owner or an agent runs a flow whose active version has highest effect
class `read` — acceptance case 2: functions the agent just admitted, over
declared read operations, returning an analysis.

### Boundary

`module:surface` checks the request's token against
`capability:installation.current_token_list` (A16 rules 1–2) and admits the request; the owner or any agent may run (A16 rule
3), and it answers only once the run rests or ends (A18 rule 3).
`module:runs` owns the start checks and pins, the order of execution, guards,
maps, failures, the trace other than an operation's concluding record, and the
run's answer (A12, A13, A15). `module:flows` answers the active version and
its graph. `module:functions` answers the current activation and an
implementation's code and bounds. `module:sandbox` executes each function
element. `module:effects` reaches each operation element and writes its
concluding record, even for `read`; for `read` it writes no EffectAttempt and
asks no authority (A10 rule 6). `module:bindings` checks the binding is current
before the send. `module:service_invoker` builds and sends the one request.
`module:canonical_values` fits values and computes identities and classes.

`module:installation` gives the token list, the manifest source, the selected
instance and the credential; `module:clock` the deadlines and the records'
times; `module:store` the run's records, value bytes and spool.

Crossing models: the run's input values enter `module:runs` and become
StoredValues M21 of their port's class; Run M19 pins FlowVersion M13 and one
Implementation M05 per function node; per function element the code, inputs
and ResourceBounds M04 cross into `module:sandbox` and an outcome with outputs
comes back; per operation element `module:runs` passes to `module:effects` the
run id, the pinned version, that the run has not ended, and the element's
inputs; ManifestOperation M10 crosses from `module:bindings` to
`module:service_invoker`; the response's outputs come back as StoredValues of
the binding's declared class; NodeExecution M23 records and WaitingPoint M20
records are the trace and the rest state.

### Steps

1. **Start.** `capability:runs.start_run` checks in A12 rule 1 order and
   refuses the start without creating a run on the first failure: the flow
   has an active version (`capability:flows.active_flow_version`); the request
   supplies exactly the flow's input ports; each value, in port name order,
   fits with `capability:canonical_values.fit_port_value` and is within
   `stored_value_bytes_max`; every function node's contract version has a
   current activation (`capability:functions.current_activation`). It reads
   the pinned graph through `capability:flows.read_flow_version`, writes the
   Run `running` with its pins, starter and start time
   (`capability:clock.kernel_now`), and the input values with their
   identities (`capability:canonical_values.content_identity`) and their port's
   class. It delivers inputs and constants along their edges (A13 rule 3).
2. **Function element.** The next node is the ready node with the smallest
   `node_id` (A13 rule 2), readiness derived from the run's records read
   through `capability:store.read_records`. `module:runs` reads the pinned implementation's code
   and bounds through `capability:functions.read_implementation`, the inputs'
   bytes through `capability:store.read_value_bytes`, and calls
   `capability:sandbox.execute_function`, which sets its wall deadline with
   `capability:clock.monotonic_deadline`. On success it validates each output
   against the source port, then against each target port before delivery;
   a failure against the source port concludes this node, a failure against a
   target port the receiving node, `contract_violation` (A13 rule 3); a value above `stored_value_bytes_max` concludes
   `contract_violation` with `value_too_large` (A15 rule 4). Output classes are
   the highest class received
   (`capability:canonical_values.highest_disclosure_class`, A07 rule 3); files
   go to the run's spool through `capability:store.spool_file`. `module:runs` writes the element's NodeExecution and
   the outputs. A mapped node runs its elements in list order (A13 rule 2, 6).
3. **Read operation element.** `capability:effects.reach_operation_element`
   runs the A09 rule 6 pre-send checks in their order:
   `capability:bindings.check_binding_current` returns the current
   ManifestOperation — read at `capability:installation.manifest_source`,
   with the instance `capability:installation.selected_instance_name` names —
   or `binding_stale`; `capability:service_invoker.prepare_request` judges the
   instance, resolves the credential through
   `capability:installation.resolve_service_credential` and places the inputs,
   JSON values as `capability:canonical_values.canonical_bytes`, naming the
   first failure. A failure concludes `operation_failed` with nothing sent.
   Otherwise `capability:service_invoker.send_prepared_request` sends once,
   within the transport deadline set with
   `capability:clock.monotonic_deadline` — no redirect, proxy or retry — and names the outcome from the `read` column of
   the A09 rule 5 table. `module:effects` writes the concluding NodeExecution
   and the output values, class from the binding, a returned file going to the
   run's spool. `module:runs` reads the
   element's conclusion through
   `capability:effects.operation_element_conclusion`.
4. **Propagate.** In its next store call `module:runs` writes the skips and
   upstream failures that became determined (A13 rules 4, 5), in (`node_id`,
   `map_index`) order (A15 rule 1), then the run's status and waiting points.
   Steps 2–4 repeat until nothing can execute.
5. **Rest or end.** When nothing executes and nothing waits, the run ends
   `succeeded` or `failed` (A13 rule 7) and the spool of a `succeeded` run is
   emptied (A14 rule 4). An element `service_unreachable` waits and the run
   rests `pending` after every other ready node has run (A13 rule 8;
   continued by `flow:wait_resume_resolve_cancel`). `capability:runs.read_run`
   computes the answer from the trace: status, outputs produced, and once
   ended the reason per missing output — `skipped_by_guard` or `not_produced`.
   `module:surface` returns it, masked under A07 for an agent.

### Outcomes

- A run of the active version with its answer: `succeeded`, `failed`, or
  resting `pending`. Produced by `module:runs` from the trace.
- One NodeExecution per concluded element, skip and upstream failure; function
  records by `module:runs`, operation records by `module:effects`.
- No EffectAttempt, no approval and nothing a service keeps: every operation
  is `read` (acceptance case 2, "releasing nothing").

### Errors

- Start refusals of A12 rule 1, no run created: `module:runs`. Actor and schema
  refusals: `module:surface`.
- Function outcomes `timeout`, `resource_exhausted`, `sandbox_violation`,
  `crashed`, `contract_violation`: produced by `module:sandbox`, recorded by
  `module:runs`; port violations on delivery and `value_too_large`: produced
  and recorded by `module:runs`.
- Pre-send failures: `binding_stale` by `module:bindings`, instance, credential
  and input placement by `module:service_invoker`; both concluded
  `operation_failed` by `module:effects`. Send outcomes `operation_refused`,
  `operation_failed` (3xx), `contract_violation`: named by
  `module:service_invoker`, recorded by `module:effects`.
  `service_unreachable` is a wait, not a failure (A13 rule 5).
- A failed node stops only its dependants (`upstream_failed`); independent
  branches finish (K-09).
- Cleanup duty: `module:sandbox` confirms cleanup of each execution or
  reports it `crashed` with `cleanup_failed` (A03 rule 7). `module:runs` then
  writes that element's NodeExecution, advances nothing further and writes no
  run status; `module:surface` answers with an internal error and ends the
  process (State 3, "Unconfirmed cleanup"). The run, left `running`, is
  advanced at the next start (`flow:start_and_recover_kernel`) with that
  element concluded failed. A `failed` run keeps its spool until it is
  released (`flow:capture_failure_and_repair_slot`).

## `flow:run_effect_with_approval`

### Trigger

The owner or an agent runs a flow whose active version the owner activated and
which holds operation nodes above `read` — acceptance case 1: an invoice photo
taken into custody through the owning service's declared operations. The owner
approves or refuses each effect, and may grant or revoke a standing approval
for a node of the active version.

### Boundary

`module:surface` checks the request's token against
`capability:installation.current_token_list` (A16 rules 1–2) and admits the request: anyone who may run starts it; only the
owner approves, refuses, grants and revokes (A16 rule 3). `module:runs` owns
the run, as in `flow:run_read_only_flow`, and checks first whether the run has
ended. `module:effects` owns the element's reach in A11 rule 1 order:
pre-send checks, authority, the in-flight EffectAttempt, the send, the outcome
record; approvals, grants and their coverage by `request_digest` (A10, A11).
`module:bindings` checks the binding is current. `module:service_invoker`
builds the request, its description and `request_digest`, and sends it once.
`module:flows` answers the active version and its nodes for a grant.
`module:canonical_values` computes the request digest and the idempotency key.

`module:installation` gives the token list, the manifest source, the selected
instance and the credential; `module:clock` the transport deadline;
`module:store` value bytes and the spool.

Crossing models: from `module:runs` to `module:effects` the run id, pinned
version, that the run has not ended, and the element's inputs; ManifestOperation
M10 from `module:bindings` to `module:service_invoker`; the request description
and `request_digest` back to `module:effects`; EffectApproval M24 with its
preview, StandingGrant M25 and EffectAttempt M26 written by `module:effects`;
the concluding NodeExecution M23 written by `module:effects` in its outcome
call; the run's status and WaitingPoints M20 written by `module:runs`.

### Steps

1. **Start and reach.** `capability:runs.start_run` starts the run as in
   `flow:run_read_only_flow`; function nodes and `read` nodes execute as
   there. At an operation element above `read`, `module:runs` calls
   `capability:effects.reach_operation_element`. Pre-send checks come first:
   `capability:bindings.check_binding_current`, then
   `capability:service_invoker.prepare_request`, which also returns the
   request's description and its `request_digest`
   (`capability:canonical_values.content_identity` of A10 rule 7's
   description). As in `flow:run_read_only_flow` step 3, the operation is read
   at `capability:installation.manifest_source` for the instance
   `capability:installation.selected_instance_name` names, the credential
   comes from `capability:installation.resolve_service_credential`, JSON values
   are placed as `capability:canonical_values.canonical_bytes`, and file inputs
   are read through `capability:store.read_value_bytes`. A failure concludes
   `operation_failed`; no EffectAttempt is written (A09 rule 6).
2. **Authority.** `module:effects` checks A10 rule 1 as it stands now: a
   `draft-write` node needs nothing at run time — its authority is the version's
   FlowActivation — except a resend after `not_applied`; any other class needs
   an approved, unused approval of this element whose `request_digest` equals
   the one just built, or an active grant for this node of the run's pinned
   version, when the node is not `destructive` and this is not a resend after
   `not_applied`. When both exist the approval is used. Without authority it
   writes one approval `requested` — none when one is already requested — with
   the exact inputs and preview (A10 rule 2), and the element waits with reason
   `owner_approval`. `module:runs` keeps executing every other ready node and
   rests the run `awaiting_approval`; `capability:runs.read_run` gives the
   answer. Next decision: the owner's.
3. **Send.** With authority, one store call writes the EffectAttempt
   `in_flight` naming its approval, grant or FlowActivation, with the
   `idempotency_key` computed from the key fields' values with
   `capability:canonical_values.content_identity` (A08 rule 4) and the attempt
   number the store assigns inside that call
   (State 3, "Attempt numbers"). `capability:service_invoker.send_prepared_request`
   sends once, within the transport deadline set with
   `capability:clock.monotonic_deadline`, the key fields travelling as the
   inputs themselves; a file the service returns goes to the run's spool
   through `capability:store.spool_file`. A second
   store call writes the outcome: the attempt's conclusion from the non-`read`
   column of A09 rule 5, the next NodeExecution, the output values, and the
   approval `used` — unless the attempt ended `not_sent`.
4. **Approve.** The owner's approval enters through
   `capability:runs.continue_after_approval`: `module:runs` refuses if the run
   has ended; `capability:effects.decide_effect_approval` refuses an approval
   that is not `requested`, else records it `approved`; `module:runs` then
   reaches the element again through
   `capability:effects.reach_operation_element`, and the A11 rule 1 order starts
   again, so a pre-send check may still fail and leave the approval unused. The
   request is sent at once, in the owner's request (A10 rule 3), and the run
   advances as far as it can.
5. **Refuse.** The owner's refusal enters the same way;
   `capability:effects.decide_effect_approval` writes the NodeExecution
   `refused_by_owner`, and `module:runs` derives the run `refused` in its next
   call: nothing further is sent, other waiting elements stop waiting without
   records, waiting points are removed and the spool is emptied (A10 rule 3,
   A14 rule 4).
6. **Grant and revoke.** `capability:effects.grant_standing_approval`, owner
   only, grants a node of the flow's active version
   (`capability:flows.active_flow_version`, the node read through
   `capability:flows.read_flow_version`) whose class is not `destructive`; a
   node already granted returns the active grant. A later send of that node in a
   run pinned to that version uses the grant as its authority only where step 2
   lets it: a `state-transition` or `external-effect` send with no matching
   unused approval, not a resend after `not_applied`; a grant for a `read` or
   `draft-write` node is never used (M25, A10 rule 6).
   `capability:effects.revoke_standing_approval` ends an active grant for every
   later send; an element already waiting keeps waiting for an approval. Grants
   move no run.

### Outcomes

- The effect sent once, on the exact request the owner was shown or under the
  owner's grant, with the declared idempotency key; its EffectAttempt `applied`,
  `not_applied`, `not_sent` or `unknown`, and the authority it used. Produced by
  `module:effects`.
- The run resting `awaiting_approval` or `pending`, or ended `succeeded`,
  `failed` or `refused`. Produced by `module:runs`.
- A standing grant, or its revocation. Produced by `module:effects`.

### Errors

- An agent approving, refusing, granting or revoking: refused by
  `module:surface` (A16 rule 3).
- Deciding on an ended run: refused by `module:runs`; deciding an approval that
  is not `requested`: refused by `module:effects` (A10 rule 3). A grant for a
  `destructive` node or for a node of a version that is not active, and a
  revocation with no active grant: refused by `module:effects`.
- Pre-send failures conclude `operation_failed` with the check named, no
  attempt, the approval left unused: `module:bindings` names `binding_stale`,
  `module:service_invoker` the instance, credential or input placement; a
  changed request digest is not a failure — the approval is no authority and the
  element asks again (A10 rule 1).
- Send outcomes: `operation_refused` (attempt `not_applied`) and
  `contract_violation` (attempt `applied`) fail the element; `not_sent` waits
  `service_unreachable`; a possibly-sent request, 3xx or 5xx waits
  `outcome_unknown`. Named by `module:service_invoker`, recorded by
  `module:effects`; both waits are continued by
  `flow:wait_resume_resolve_cancel`.
- Cleanup duty: a crash between the `in_flight` record and the outcome record
  leaves the attempt `in_flight`, turned `unknown` at the next start
  (`flow:start_and_recover_kernel`); the kernel never sends it again on its
  own. The spool is emptied when the run ends other than `failed`.

## `flow:wait_resume_resolve_cancel`

### Trigger

A run rests `pending` or `awaiting_approval`. The owner or an agent resumes
elements waiting on an unreachable service; the owner resolves an unknown
outcome; the owner cancels a run that has not ended.

### Boundary

`module:surface` checks the request's token against
`capability:installation.current_token_list` (A16 rules 1–2) and admits the request: resume by the owner or any agent;
resolve and cancel by the owner only (A16 rule 3). `module:runs` owns the run's
status, its waiting points, resume and cancel, and checks first that the run
has not ended (A13 rule 1, A14). `module:effects` owns the EffectAttempt and
its resolution, and reaches each resumed element in A11 rule 1 order.

`module:installation` gives the token list; `module:store` the run's waiting
points and records.

Crossing models: WaitingPoint M20 records name the elements and reasons;
from `module:runs` to `module:effects` the run id, pinned version, that the run
has not ended, and the element; EffectAttempt M26 is changed by
`module:effects`; the run's status, waiting points and the answer by
`module:runs`.

### Steps

1. **Rest.** A run rests with one waiting point per waiting element, reason
   `owner_approval`, `service_unreachable` or `outcome_unknown`; no time limit
   moves it (A14 rule 1). Waiting points and records are read through
   `capability:store.read_records`. `capability:runs.read_run` gives the answer with the
   outputs produced so far.
2. **Resume.** `capability:runs.resume_run` refuses a run with no element
   waiting on `service_unreachable`. Otherwise it reaches every such element
   again in (`node_id`, `map_index`) order through
   `capability:effects.reach_operation_element`, authority checked as it
   stands at the resume (A14 rule 2): for a `draft-write` element that is not
   a resend after `not_applied`, the flow activation under which the run
   started; otherwise the unused approval first, then a grant still active;
   an element whose grant was revoked waits for approval instead.
   Only after all resends does the run advance (A13). Elements waiting on
   approval or an unknown outcome are not touched.
3. **Resolve.** The owner's resolution enters through
   `capability:runs.continue_after_resolution`: `module:runs` refuses if the
   run has ended; `capability:effects.resolve_unknown_outcome` refuses an
   attempt that is not `unknown`, else sets it `applied` or `not_applied` with
   `resolved_by` — the only record of the resolution; no NodeExecution is
   written (A11 rule 3). `module:runs` reads the element's conclusion: applied
   without output ports — succeeded; applied with output ports — failed,
   `applied_outputs_unknown`; not applied — waits `owner_approval` for a fresh
   approval, even under a grant, and the resend is the next attempt
   (`flow:run_effect_with_approval` step 4). The run advances.
4. **Cancel.** `capability:runs.cancel_run` refuses an ended run; otherwise it
   ends the run `cancelled`: nothing further is sent, concluded records stay,
   waiting points are removed, undecided approvals can no longer be decided,
   an `unknown` attempt stays `unknown` (A11 rule 5), and the spool is emptied
   (A14 rule 3).

### Outcomes

- A resumed run advanced as far as it can, resting again or ended. Produced by
  `module:runs`, each resend's outcome by `module:effects`.
- A resolved attempt, `applied` or `not_applied`, with the owner as
  `resolved_by`. Produced by `module:effects`; the run's consequence by
  `module:runs`.
- A cancelled run with its trace intact and no spool. Produced by
  `module:runs`.

### Errors

- An agent resolving or cancelling: refused by `module:surface`.
- Resume with no unreachable wait, resolve or cancel on an ended run: refused
  by `module:runs`. Resolve of an attempt that is not `unknown`: refused by
  `module:effects`.
- A resend may fail its pre-send checks or end with any outcome of
  `flow:run_effect_with_approval` step 3; each is recorded there.
- Cleanup duty: cancel empties the spool; the kernel never claims an outcome
  for an `unknown` attempt, cancelled or not.

## `flow:capture_failure_and_repair_slot`

### Trigger

A function element of a run failed. The owner or an agent with the author
right captures the failed execution into its contract version's corpus; an
agent repairs the slot; the owner or an agent releases the failed run; the
owner or an agent with the author right may roll the slot back.

### Boundary

`module:surface` checks the request's token against
`capability:installation.current_token_list` (A16 rules 1–2) and admits the request — capture and rollback by the owner or an
agent with the author right; release by the owner or any agent (A16 rule 3) —
and assembles the repair view (A15 rule 6, K-12). `module:runs` owns the
conditions of capture, copying the spooled inputs, and the release (A14 rule
4, A15 rule 5). `module:functions` owns adding the case, admission and
rollback (A04). `module:store` holds the content-addressed area, the spool and
paging. `module:canonical_values` fits the captured values and computes the
case's identity.

`module:installation` gives the token list.

Crossing models: NodeExecution M23 of the failed element and Run M19 are read
by `module:runs`; the spooled input files cross into the content-addressed
area through `module:store` and become digests; from `module:runs` to
`module:functions` the pinned contract version, the record's inputs and those
digests; TrialCase M06 and its StoredValues M21 written by `module:functions`;
for the repair view, the slot's contract versions and implementations and a
page of NodeExecutions cross into `module:surface`.

### Steps

1. **Capture.** `capability:runs.capture_failed_execution` reads the record
   through `capability:store.read_records` and checks, in this
   order, the record — an executed function element that did not succeed
   (M06) — then the run and its spool: not ended, or ended `failed` and not
   released (A15 rule 5). It copies the spooled input files into the
   content-addressed area — read through `capability:store.read_value_bytes`,
   stored through `capability:store.put_value_bytes` — and calls `capability:functions.add_captured_trial_case`
   with the pinned contract version, the inputs and the file digests.
   `module:functions` checks that the record's contract version is the one
   named, fits each value with `capability:canonical_values.fit_port_value`
   and each fixture against `trial_fixture_bytes_max` (A04 rule 1), computes
   `trial_case_id` with `capability:canonical_values.content_identity` and
   writes the file-carriage StoredValues, each with the class its contract
   input port declares (M21), and the TrialCase; an equal case is
   that case. The corpus digest changes; the serving implementation keeps
   serving and visibly lacks a verdict over the current corpus (A04 rule 7).
2. **Repair view.** `module:surface` takes the slot's contract versions and
   implementations from `capability:functions.read_slot` and pages, through
   `capability:store.page_records`, the NodeExecutions whose executed
   implementation is in that set, newest first, at most `page_size_max`
   (A15 rule 6); it masks under A07.
3. **Repair.** The agent submits a new implementation through
   `capability:functions.submit_implementation`; admission runs over the grown
   corpus and activates it when admitted (`flow:author_and_admit_function`
   steps 4–5). Re-submitting an earlier implementation re-runs admission the
   same way (A04 rule 5).
4. **Release.** `capability:runs.release_run` refuses a run that is not
   `failed` or was already released; otherwise it records who and when, and
   `capability:store.remove_run_spool` removes the run's files (A14 rule 4).
   Captured fixtures remain.
5. **Roll back.** `capability:functions.roll_back_slot` activates an earlier
   implementation of the slot's current contract version that holds an
   `admitted` verdict over the current corpus; naming the current one returns
   its activation and records nothing; it runs no admission (A04 rule 5).

### Outcomes

- A trial case every later implementation of the contract version must pass.
  Produced by `module:functions` once `module:runs` has checked the capture.
- The repair view of one slot. Assembled by `module:surface` from the owning
  modules' reads.
- A repaired slot: a new verdict and activation. Produced by
  `module:functions`.
- A released run with no spool. Produced by `module:runs`.
- A rolled-back slot. Produced by `module:functions`.

### Errors

- Actor refusals: `module:surface`.
- Capture refusals — a succeeded or skipped element, an operation element, a
  run released or ended other than `failed` (files gone), a foreign contract
  version, a value or fixture that does not fit or is too large: `module:runs`
  for the record and the run, `module:functions` for the contract version and
  the fit, the first failing check named.
- Release of a run that is not `failed` or already released: `module:runs`.
  Rollback to an implementation without an `admitted` verdict over the current
  corpus: `module:functions`.
- Cleanup duty: capture copies files before the run's spool can go; files
  copied before `module:functions` refuses the case stay in the
  content-addressed area, named by no record (State 3, "Bytes left by a
  refused capture"); release
  is the only removal of a failed run's spool, and the content-addressed copy
  of a captured file is the only file that outlives its run (K-10).

## `flow:start_and_recover_kernel`

### Trigger

The host starts the kernel process — first start, a restart, or after the
kernel stopped itself on unconfirmed sandbox cleanup (A03 rule 7).

### Boundary

`module:surface` owns the start order and opens the entrance only at its end
(A16, A18). `module:installation` loads and checks the configuration (A17).
`module:bindings` checks the installed instances against the manifest (A09 rule
1). `module:store` takes the lock, checks the data directory and removes
temporary files and the spools it is told to (A18). `module:sandbox` probes
the sandbox (A03 rule 8). `module:effects` turns `in_flight` attempts into
`unknown` (A11 rule 4). `module:runs` decides which ended runs' spools go and
advances the runs left `running` (A14 rules 4, 5).

`module:clock` gives the recovery time.

Crossing models: the configuration file into `module:installation`, which
yields tokens, selected instances, credential headers and the manifest source
(M28); those instances and the manifest records into `module:bindings`; the
list of ended runs without a kept spool from `module:runs` to `module:store`;
EffectAttempt M26 and the concluding NodeExecution M23 written by
`module:effects`; NodeExecutions and run statuses written by `module:runs`.

### Steps

1. `capability:surface.serve_kernel` calls, in this order, every step
   required and stopping the start with its reason on the first failure:
2. `capability:installation.load_installation`: the file is a regular private
   file of the kernel's user; tokens at least 43 characters and pairwise
   distinct (A16 rule 1, A17 rule 1).
3. `capability:bindings.check_installed_instances`: no credential header has,
   case-insensitively, the name of a required header of its instance or of a
   header the kernel sets itself, `host` included (A09 rule 1). It reads only the installation —
   `capability:installation.selected_instance_name` and
   `capability:installation.manifest_source` — and the manifest, never the
   store.
4. `capability:store.open_store`: the exclusive lock, private directory, no
   symbolic link, removal of temporary files (A18 rules 1, 2, 4).
5. `capability:sandbox.probe_sandbox`: `bubblewrap` is present and one probe
   execution succeeds (A03 rule 8).
6. `capability:effects.recover_in_flight_attempts`: every `in_flight` attempt
   becomes `unknown`, and when its attempt has no NodeExecution yet the
   `outcome_unknown` record is written with the attempt's number, its start
   time and the recovery time from `capability:clock.kernel_now` as end (A11 rule 4), and the approval the attempt
   named, if any, is marked `used` (A11 rule 1). The service is not asked.
7. `capability:runs.recover_running_runs`: first names to
   `capability:store.remove_run_spool` every ended run that does not keep its
   spool (A14 rule 4, A18 rule 4); then, as the kernel actor, advances every
   run left `running`, oldest first: a function element without a concluded
   record is executed again; a `read` element without one is sent again; an
   operation element of another class with neither a concluded record nor an
   EffectAttempt is reached as for the first time, an unused approval covering
   it only while the rebuilt request has its `request_digest` (A14 rule 5).
   Each run is then derived — a `refused_by_owner` record ends it `refused`
   before any element is reached.
8. Only then does `module:surface` accept the first request.

### Outcomes

- A running kernel with a working sandbox, no `in_flight` attempt and no run
  left `running`; every run rests or has ended truthfully. Produced by the
  modules named in each step.
- Spools of ended runs that keep none are gone; spools of `failed` unreleased
  runs stay.

### Errors

- Each start check failing stops the start and names why: configuration file
  mode, owner or token rules (`module:installation`); a credential header
  colliding with a required header or a kernel-set header (`module:bindings`); lock held, directory
  not private, a symbolic link (`module:store`); sandbox missing or probe
  failing (`module:sandbox`). The surface never opens; there is no partial
  start.
- During run recovery, an element fails or waits exactly as in a request;
  nothing is decided by time.
- Cleanup duty: if a re-executed function's cleanup cannot be confirmed,
  `module:runs` writes its NodeExecution `crashed` with `cleanup_failed`,
  advances nothing further, and `module:surface` stops the start (State 3,
  "Unconfirmed cleanup"). The next start finds that element concluded and does
  not execute it again: its dependants conclude `upstream_failed`, so a cleanup
  failure stops the kernel at most once per element and never loops.
