# State 2 — Cabinet Kernel run, trace and spool rules

Draft of 2026-09-30. Rules for starting, advancing, waiting, resuming, cancelling
and releasing runs, and for the trace and the spool (K-07, K-09, K-10, K-17).
Reuses cabinet-flow decisions 16–20 where they still hold; retry schedules, retention
periods, store continuity and concurrent execution are gone (K-09, K-10, K-17).

## Accepted decision A12 — a run pins what it executes when it starts, or does not start

Reuses cabinet-flow decision 16, narrowed.

### Normative rules

1. A run starts from the flow's active version. Before any node executes, the
   kernel checks, in this order, and refuses the start without creating a run on
   the first that fails: the flow exists and has an active version; the request
   supplies exactly the flow's input ports; each value, in port name order, fits
   its port's schema and then its size bound —
   for a `many` port, is a JSON array whose every element fits it — and
   is within `stored_value_bytes_max`; every function node's contract version has
   a current activation.
2. The run pins the flow version and, for every function node, the implementation
   of the current activation at start (M19). Nothing recorded later — a new
   activation, a new flow activation, a new binding — changes what the run
   executes.
3. Each flow input value takes its port's class (A07). Two runs on equal inputs
   are two runs; protection against a repeated effect is the owner's approval and
   the idempotency key, never a deduplication of runs.
4. The owner or any agent may start a run of an active version (State 0). The
   starter is recorded and never changes.

### Formal invariants

```text
run_created -> active_version AND inputs_exact_and_valid AND all_function_nodes_served
start_check_failed -> no_run_created
run.pins fixed_at_start
later_record -/> alters(pins(run))
```

### Required tests

1. A run whose flow has no active version, or whose input misses a port, or whose
   function node has no current activation, is refused and no run exists.
   [witness: verification:kernel_a12_start_refused_without_run]
2. A run started before a new activation, a new flow activation or a new
   binding executes, to the end, the flow version and implementations it pinned
   at start, including after a long wait for approval.
   [witness: verification:kernel_a12_pins_survive_later_records]
3. Two runs on equal inputs have distinct identities and traces.
4. A start whose request supplies a port the flow does not declare, or a value
   that misfits its port's schema, or a `many` value that is not a JSON array of
   fitting elements, or a value above `stored_value_bytes_max`, is refused and no
   run exists.
   [witness: verification:kernel_a12_start_inputs_exact_and_valid]

### Consequence

A run means one thing from start to finish, so its trace always reads against
exactly what it executed.

## Accepted decision A13 — a run advances one node at a time, inside the request that moves it

Reuses cabinet-flow decision 17, narrowed by K-17: no concurrent execution, no background
worker.

### Normative rules

1. A run advances only inside a request: the start, an approval, a resolution or a
   resume. The kernel executes until no node can execute any more, then returns
   the run as it rests or ends. Nothing advances a run between requests, except
   the start-up recovery of A14 rule 5.
2. Nodes execute one at a time. The next node is the ready node with the smallest
   `node_id`, by Unicode code point (A05 rule 2); a node is ready when every input
   port holds its value — a mapped node's outputs exist only once it has
   concluded, so its dependants never start from part of them. A mapped node,
   once selected, takes its elements in list order, each once in the pass, and
   runs every one that has no concluded record and does not wait — a concluded element is never executed again — before the next node is
   selected; an element that waits or fails does not stop the elements after it.
3. At start, each flow input's value is delivered along every edge from that
   input, and each constant to its port (constants were validated when the
   version was composed and proven, A05); an edge from a flow input straight to a flow output produces that
   output at once. A flow output holds the value its edge delivered. A value on
   a `many` port is a JSON array, each element of which must fit the
   port's `value_schema`; anything else is a violation of that port. A value is
   validated against the source port when it is produced and against
   the target port before it enters a node; a violation concludes the producing
   node, or the receiving node, `contract_violation`, and the value is not
   delivered. A receiving node concluded so did not run: its NodeExecution names
   what it pinned as `executed`, the inputs it had, no outputs and no resources
   used, and starts and ends at the time of the check. An element that does not
      succeed keeps no output: its NodeExecution names none, a value it produced
   is not stored, and the files its attempt spooled are discarded: no
   SpooledFile record names them and nothing reads them. Their bytes are
   removed at once only by a spool-ceiling refusal (A15 rule 3); after any
   other failure they stay in the run's spool, counted toward
   `spool_run_bytes_max`, until that spool is removed (A18 rule 4) or a later
   write to the same position replaces them — a position being the run, node,
   `map_index`, attempt number, port and list index, which only a retry of
   the same attempt number writes again, after a restart left that attempt
   without a record. Value bytes it published stay in the content-addressed area
   unnamed, reused by equal bytes until the next start removes them (A18 rule
   4); nothing reads either.
4. A guarded edge delivers only when its guard port's value equals its guard
   value. An input port that can no longer receive a value because every edge into
   it is disabled, or comes from a skipped node, makes its node `skipped_by_guard`
   without executing; this applies transitively and to flow outputs, which are
   then reported `skipped_by_guard` (A05 rule 4).
5. A node is failed when its record's status is `contract_violation`,
   `sandbox_violation`, `timeout`, `resource_exhausted`, `crashed`,
   `operation_refused` or `operation_failed`; `service_unreachable` and
   `outcome_unknown` are waits, not failures, and their dependants wait, until
   the owner's resolution makes the element count as succeeded or failed
   (A11 rule 3). A node an
   input of which comes from a failed node, or from a node itself
   `upstream_failed`, concludes `upstream_failed` without executing; when both
   rule 4 and this rule apply, this rule wins.
6. A mapped node over an empty list runs nothing, asks nothing and sends
   nothing; it writes one NodeExecution `succeeded` — its first record, so number
   1 by A11 rule 1 — with no `map_index`, `executed` naming what it pins and every output an empty list. A
   `many` file port carries a list of files; inside the sandbox it is a list of
   `bytes` (A03). A mapped node concludes only when every element has concluded. It succeeded
   when every element succeeded, and its outputs are then lists in element order,
      each list of the highest class among its elements (A07); an empty list
   takes the highest class among the node's inputs — the list it mapped over
   and every other input — as an execution of the node would have received
   them (M21), so no class is lowered;
   any failed element makes it failed for its dependants. A value list is one
   StoredValue, the JSON array of the elements' values in element order, whose
   `value_schema` is the array schema with the port's schema as `items`, as
   for every value of a `many` port (M21),
   written by `runs` when the list is first delivered — never in an element's
   own store change, which for an operation element is `effects'` — and
   named, like any value, by the records that receive it; a list whose
   canonical bytes exceed `stored_value_bytes_max` is not written: the node is
   then failed for its dependants, which conclude `upstream_failed` and write
   that record (A15 rule 1), derived like the list from the elements'
   records, which stay as they are (A15 rule 4). No record of the node states
   that failure: like the list, it is derived from the elements' records and
   `stored_value_bytes_max`, the same way by every reader of the trace (A15;
   owner, 2026-10-05, as the advance_run note decides). By the same
   derivation the node counts as failed when the run ends (rule 7), so a list
   that feeds only a flow output ends the run `failed`. Only a list that is
   delivered — to a node or a flow output — is measured; an output no edge
   takes fails nothing. Every delivered list of a mapped node is measured
   before any of them is delivered or written: when one exceeds the ceiling,
   none is delivered, and the node fails as above. Mapping over a delivered list gives each element the
   list's class; a file list is the
   elements' SpooledFiles in element order, each keeping its own record, and
   the reference naming it carries the list's class. A non-empty list has no
   record of its own: the elements' NodeExecutions are its durable facts, and
   the list — its StoredValue identity, its files, its class — is derived from
   them in element order whenever it is delivered, after a restart too, and
   then named by every record that receives it. An empty list is named, with
   its class, by the one NodeExecution the node writes over an empty list. A port's
   reference to values names exactly one StoredValue, a `many` value being one
   JSON array.
7. An element's conclusion is its NodeExecution's status, except that an
   `outcome_unknown` record the owner resolved concludes as A11 rule 3 says —
   succeeded, or failed with `applied_outputs_unknown` — and one not yet resolved
   waits. Readiness, rule 5 and this rule use that conclusion. A waiting element
   can still execute, so M19's "no node can run any more" holds only when
   nothing waits: when nothing can
   execute and nothing waits, the run ends: `succeeded` when every node concluded
   succeeded or `skipped_by_guard`; otherwise `failed`.
   Run outputs (M19) hold only produced values. A run that rests returns the
   outputs produced so far; the per-output reasons below are given only once it
   has ended. The run's answer names every flow
   output port with either its value or a reason computed from the trace:
   `skipped_by_guard` when every edge into it was disabled by its guard or comes
   from a node recorded `skipped_by_guard`, otherwise `not_produced`. `refused` and `cancelled` are set only by
   the owner's decisions (A10, A14).
8. While some elements wait, every other ready node keeps executing within the
   request (K-09); the run then rests `awaiting_approval` when any element waits
   for the owner's approval, otherwise `pending`.

### Formal invariants

```text
advance(run) -> inside(start | approve | resolve | resume | startup_recovery)
next_node = min(node_id, ready_nodes)
executing_nodes_at_once <= 1

port_unreachable_by_guard -> skipped_by_guard   (transitive)
input_from(failed | upstream_failed) -> upstream_failed   (wins over skip)
conclusion(element) = status(node_execution) unless resolved(outcome_unknown) -> A11
run.succeeded <-> for_all node: conclusion IN {succeeded, skipped_by_guard}
```

### Required tests

1. Two ready nodes `b` and `a` execute `a` first, every time.
   [witness: verification:kernel_a13_next_node_min_node_id]
2. A duplicate-check guard that disables the save branch yields `skipped_by_guard`
   on the save node and on the flow output behind it, and a `succeeded` run.
   [witness: verification:kernel_a13_guard_skip_transitive_run_succeeds]
3. One failing element of three fails the mapped node, keeps three records, and
   concludes its dependants `upstream_failed`.
   [witness: verification:kernel_a13_failed_input_gives_upstream_failed]
4. With two independent branches, a failure in one lets the other finish; the run
   ends `failed` with the other branch's output marked produced.
   [witness: verification:kernel_a13_any_failure_ends_run_failed]
5. Starting a run whose first operation node needs approval returns the run
   `awaiting_approval` after executing every function it could.
6. Between two requests a resting run gains no NodeExecution and no status
   change; the next approval, resolution or resume advances it inside that
   request, which returns only when no node can execute.
   [witness: verification:kernel_a13_advance_only_inside_request]
7. In one run of a flow with two independent function nodes, the second node's
   NodeExecution starts no earlier than the first one's ended.
   [witness: verification:kernel_a13_one_node_executes_at_a_time]
8. A node with one input from a failed node and another whose only edge is
   disabled by its guard concludes `upstream_failed`, not `skipped_by_guard`.
   [witness: verification:kernel_a13_upstream_failed_wins_over_skip]
9. An element recorded `outcome_unknown` keeps its dependants waiting while its
   EffectAttempt is `unknown`; resolved `applied` for a binding without output
   ports, its dependants execute; resolved `applied` for a binding with output
   ports, they conclude `upstream_failed`; its NodeExecution keeps
   `outcome_unknown` throughout.
   [witness: verification:kernel_a13_resolved_unknown_conclusion]

### Consequence

The same flow on the same inputs always executes in the same order, and bad data
never travels one step further than the node that produced it.

## Accepted decision A14 — waiting is truthful, and only people end it

Reuses cabinet-flow decision 18, narrowed by K-09: no timed retries, no reconciliation.

### Normative rules

1. A run rests with a WaitingPoint M20 for every element that waits, with reason
   `owner_approval`, `service_unreachable` or `outcome_unknown`. No time limit
   ends, fails, approves or retries anything. When a run ends, its waiting points
   are removed; the trace keeps what happened.
2. Resume, by the owner or an agent, sends again, in (`node_id`, `map_index`)
   order — an element without `map_index` before index 0 — every element waiting
   on `service_unreachable`. Each is reached again by the order of A11 rule 1, so
   its authority is checked as it stands at the resume (A10 rule 1): a `read`
   element asks none (A10 rule 6); for a `draft-write` element, the flow activation under which the run started,
   unless it is a resend after `not_applied`; otherwise its unused approval
   (M24), which is used first when both exist, or a grant still active; an element whose grant was revoked meanwhile
   waits for approval instead. All these resends come first; only then does the
   run advance as A13 says. A run with no such element is refused;
   elements waiting on approval or on an unknown outcome are not touched.
3. Cancel, by the owner only, ends a run that has not ended as `cancelled`:
   nothing further is sent, every concluded record stays, undecided approvals can
   no longer be decided, and the spool is emptied.
4. A run's spool is emptied when it ends `succeeded`, `refused` or `cancelled`.
   A `failed` run keeps its spool until the owner or an agent releases it; release
   removes the files, records who and when, and is refused for a run that is not
   `failed` or was already released (K-10). The record that ends or releases the
   run is written first and stands; the files are removed after it, and a
   removal that fails or is interrupted fails nothing: what is left is removed
   at the next start (A18 rule 4), and from that record on no file of the run
   is served.
5. On start, before the surface accepts a request, the kernel turns every
   `in_flight` EffectAttempt into `unknown` (A11 rule 4) and then derives every
   run that has not ended — `running`, `awaiting_approval` or `pending` — again
   from its records, oldest first in store order, rewriting a stored status or
   waiting point that lags them (a decided approval, a resolved attempt, an
   outcome whose run change was lost), and advances, as the
   kernel actor, every run that derivation leaves `running`: a
   function element without a
   concluded record is executed again, which is safe because it is pure; a `read`
   element without one is sent again; an operation element of another class with
   neither a concluded record nor an EffectAttempt was never sent and is advanced
   as if reached for the first time — an approved, unused approval covers it
   only while the rebuilt request has its `request_digest` (A10 rules 1 and 7).
6. Everything a resume or a restart needs is in the store before it is acted on:
   records of concluded attempts, decided approvals, and in-flight attempts before
   their request (K-17).
7. A store failure can leave a run's stored status behind its records. Any
   request answered `internal_error` therefore stops the kernel once the
   answer is sent, so the next start derives every run (rule 5) before any
   request touches one.

### Formal invariants

```text
wait_elapsed -/> state_change
resume -> resend(service_unreachable elements) ONLY
resume AND none_waiting_unreachable -> refused
cancel -> actor = owner AND run_not_ended
spool_emptied <- ended(succeeded | refused | cancelled) OR released(failed)
startup: in_flight -> unknown; running runs advanced by kernel before surface opens
```

### Required tests

1. With a service down, a run rests `pending`, its independent read branch
   finishes, and a resume after the service returns completes it without new
   inputs.
   [witness: verification:kernel_a14_resume_resends_unreachable]
2. A resume of a run waiting only for approval is refused.
   [witness: verification:kernel_a14_resume_without_unreachable_refused]
3. Restarting the kernel during a function execution executes it again with the
   same output digest; during an effect it yields `unknown` and no second request.
   [witness: verification:kernel_a14_restart_in_flight_becomes_unknown]
4. A cancelled run executes nothing further, keeps its trace and has no spool.
   [witness: verification:kernel_a14_cancel_empties_spool_keeps_trace]
5. A `failed` run keeps its spooled files until released; releasing twice is
   refused.
   [witness: verification:kernel_a14_failed_spool_kept_until_release]
6. Runs resting on `owner_approval`, on `service_unreachable` and on
   `outcome_unknown` are unchanged — status, waiting points and records — after
   the clock is moved past any interval: nothing is retried, failed or approved.
   [witness: verification:kernel_a14_elapsed_wait_changes_nothing]
7. A resume of a run with one element waiting on `service_unreachable`, one on
   approval and one on `outcome_unknown` sends only the first again; the other
   two waiting points stay as they were.
   [witness: verification:kernel_a14_resume_leaves_other_waits_untouched]
8. A cancel by an agent, or of a run that has ended, does not cancel the run: it
   keeps its status, its trace and its spool.
   [witness: verification:kernel_a14_cancel_owner_only_unended_only]
9. A run that spooled a file and ends `succeeded`, and one that spooled a file
   and ends `refused`, keep no spooled file.
   [witness: verification:kernel_a14_spool_emptied_on_succeeded_refused]
10. After a restart, the first request the surface answers finds no
    EffectAttempt `in_flight` and every run that derivation left `running`
    already advanced by the kernel.
    [witness: verification:kernel_a14_recovery_completes_before_surface]

### Consequence

The owner can switch the machine off or take a week to answer, and every run is
still in the state it was truly in.

## Accepted decision A15 — the trace is immutable, bounded and holds no payload

Reuses cabinet-flow decisions 19 and 20, narrowed by K-10: no retention periods, one
spool, files only as fixtures beyond a run.

### Normative rules

1. Every concluded attempt at an element, every skipped node and every
   `upstream_failed` node writes exactly one NodeExecution M23 — an owner's
   resolution of an unknown outcome writes none (A11). A mapped node's trace is
   its elements' records; it has a record of its own, without `map_index`, only
   when it ran no element: over an empty list (A13 rule 6), or when it was
   skipped or `upstream_failed` before any element. Records of nodes that become
   non-executable together are written in (`node_id`, `map_index`) order, a
   record without `map_index` before index 0, as in A14 rule 2. No operation edits
   or deletes one. `succeeded` is written only after the outputs validated.
2. A record names what executed by identity — the implementation or the binding —
   and its inputs and outputs by `value_id` or spooled-file facts. It holds no
   value, no file, no credential, no header value and no text beyond
   `failure_detail_bytes_max`.
3. A file produced during a run is written to that run's spool below the data
   directory (A18), with its digest and size, and read from there by the next node.
   A spooled file above `spool_file_bytes_max`, or a run whose spooled files
   together exceed `spool_run_bytes_max`, concludes the producing element
   `resource_exhausted` (for an operation, A09's `contract_violation`); only the
   files of that attempt are discarded, and files spooled earlier in the run
   stay.
4. A value a node produces — a function output or a service output — above
   `stored_value_bytes_max` is checked only after the execution or the response
   has otherwise succeeded, so A03's `resource_exhausted` for `output_bytes` wins
   when both hold; it concludes the element `contract_violation` with detail
   `value_too_large`; a mapped node's value list above it fails the node for
   its dependants without changing any element's record (A13 rule 6); a constant or a trial value above it is refused when
   authored, by the surface's request bound (A16 rule 4) before any check of
   composition or of the trial case; a flow input above it refuses the start (A12).
5. Capturing a failed execution into a trial corpus (M06) is allowed only for
   a function node's execution that ran in the sandbox — its record names the
   resources it used — and did not succeed; a node that concluded without
   running, a receiving node refusing a misfit input among them, is not
   captured. It is allowed only while
   its run still holds its spool — the run has not ended, or ended `failed` and
   was not released — and is refused otherwise, since its files may be gone.
   These checks, in this order, come before the case is built, and so before an
   equal existing case is returned (A04 rule 1). It
   copies its inputs,
   spooled files included, into the case as values and file fixtures; a file
   fixture above `trial_fixture_bytes_max` refuses the capture. This is the only
   way a run's file outlives its run (K-10).
6. For repair an agent receives one slot's contract, its current implementation,
   its trial cases and executions, and the latest NodeExecutions, in reverse store
   order, that executed an implementation of any contract version of that slot, at most
   `page_size_max` of them (K-12), under A07.
7. The trace is the only source the kernel uses to explain or continue a run;
   process logs are never an input to a kernel decision.

### Formal invariants

```text
concluded_attempt | skip | upstream_failed -> exactly_one_node_execution
node_execution immutable
payload IN node_execution -> never
spooled_file -> belongs_to(one run) AND size <= spool_file_bytes_max
sum(spool(run)) <= spool_run_bytes_max
file_outlives_run -> captured_as_fixture
```

### Required tests

1. No operation alters a written NodeExecution.
   [witness: verification:kernel_a15_node_execution_immutable]
2. A function that raises after printing a secret-shaped string leaves a bounded
   `failure_detail` without it.
   [witness: verification:kernel_a15_failure_detail_bounded_no_secret]
3. A function writing a file one byte over `spool_file_bytes_max` concludes
   `resource_exhausted` and leaves nothing in the spool.
   [witness: verification:kernel_a15_spool_file_ceiling]
4. A function whose second spooled file brings its run's spool one byte over
   `spool_run_bytes_max` concludes `resource_exhausted`; only that attempt's
   files are discarded and the file spooled earlier stays.
   [witness: verification:kernel_a15_spool_run_ceiling]
5. Capturing a failed execution whose input was a spooled photo creates a case
   whose fixture has the photo's digest; after release the run's spool is empty
   and the fixture remains.
   [witness: verification:kernel_a15_file_outlives_run_only_as_fixture]
6. A run with a three-element mapped node, a skipped node and an
   `upstream_failed` node holds exactly one NodeExecution per element, none of
   the mapped node's own, and one per skipped and per `upstream_failed` node; an
   owner's resolution of an unknown outcome adds none.
   [witness: verification:kernel_a15_one_record_per_conclusion]

### Consequence

The trace is the kernel's memory of what it did, and it can be trusted because
nobody, the kernel included, can rewrite it.

## Carried to later states

Questions the State 2 rounds raised that change no rule here; they belong to the
state named and must be closed there:

- State 5: the inspection operation through which the owner reads a spooled
  file's bytes (A10 rule 2) — its request, its size and paging limits; once the
  run's spool is emptied or released the bytes are gone and the request is
  refused.
- State 6: the supported JSON Schema subset and the syntax of idempotency-key
  fields, as State 1 carries; canonical bytes are RFC 8785 (A01).
- Release build: the frozen list of trapped standard-library entry points —
  closed: A03 rule 4 lists them, and the release passes them as data (A20).
- State 5: the closed set of reason codes a refusal or an `operation_failed`
  detail names — only where a caller acts on the difference (K-17); State 2 fixes
  which check is named first.
- State 6: the encoding of a list continuation token (A16 rule 6 fixes its
  meaning: a store position).
