# State 3 — Cabinet Kernel module responsibilities

Draft of 2026-10-01. Derived from the accepted State 2 decisions A01–A21. A module
owns one hidden mechanism and has one reason to change; its public surface is
smaller than what it hides. Each accepted decision has one primary owner, the
module that holds the decision's central mechanism, and consumers. Ownership is
by rule, not by decision: a consumer owns exactly the rules and parts of the
decision its own section below names, and the primary owner owns every rule of
the decision that no other section names, except a rule this text places
outside the running kernel (A20 rule 3, A21), which no module owns. The table
is the one mapping;
`30_trace.json` records the same:

| decision | primary owner | consumers |
|---|---|---|
| A01 | `canonical_values` | `store`, `functions`, `flows`, `runs`, `run_values`, `store_persistence` |
| A02 | `functions` | `canonical_values`, `data_provider` |
| A03 | `sandbox` | `sandbox_runner`, `functions`, `runs`, `surface`, `data_provider` |
| A04 | `functions` | `store`, `sandbox`, `canonical_values` |
| A05 | `flows` | `canonical_values`, `bindings` |
| A06 | `flows` | `surface` |
| A07 | `surface` | `canonical_values`, `flows`, `runs`, `run_values`, `functions`, `effects` |
| A08 | `bindings` | `installation`, `service_invoker`, `effects`, `data_provider` |
| A09 | `service_invoker` | `bindings`, `effects`, `installation`, `data_provider`, `surface` |
| A10 | `effects` | `service_invoker`, `runs`, `surface` |
| A11 | `effects` | `runs`, `run_graph`, `store` |
| A12 | `runs` | `functions`, `flows`, `canonical_values` |
| A13 | `run_graph` | `runs`, `run_values`, `sandbox`, `effects`, `canonical_values`, `data_provider` |
| A14 | `runs` | `run_graph`, `effects`, `store`, `surface` |
| A15 | `runs` | `run_graph`, `run_values`, `store`, `functions`, `effects`, `surface` |
| A16 | `surface` | `installation`, `store`, `data_provider` |
| A17 | `installation` | `service_invoker`, `sandbox` |
| A18 | `store` | `runs`, `surface`, `store_persistence` |
| A19 | `clock` | `sandbox`, `service_invoker`, `functions`, `effects`, `runs`, `bindings`, `flows` |
| A20 | `data_provider` | `canonical_values`, `functions`, `sandbox`, `sandbox_runner`, `service_invoker`, `store`, `runs`, `run_values`, `surface`, `installation`, `bindings` |

The kernel is one process with one writer (K-17), so modules are not services:
they are the parts of one program, and only `store` touches the database and the
data directory. `store` holds the connection and the transaction and decides
which record goes into which row; the row statements themselves are executed by
`store_persistence`, its companion, which only `store` calls, over that
connection (below). The dependency direction is fixed,
from the bottom up:

```text
models
data_provider
canonical_values, clock, store_persistence, sandbox_runner
store, installation
sandbox, service_invoker, run_values
functions, bindings
flows
effects
run_graph
runs
surface
```

The list runs from the bottom of the stack up: a module may know only modules
on earlier lines of the list, never one on a later line, and modules on one
line do not know each other.

A21, the State 0–2 security review, has no runtime owner: it is an evidence
record checked by `design_lint --state 2`, recorded as such in `30_trace.json`.

## Facts several modules touch, and their one owner

- **Class orders.** The disclosure classes (A07 rule 1) and the effect
  classes (M10) are enumerations of `models`, each ordered by its declared order
  (State 1); the members and the order have that one home, and no constant
  repeats them (SPEC_STANDARD 15.4). A member is compared only by its position
  in that order, never as text. Every comparison of disclosure classes goes
  through `canonical_values.highest_disclosure_class`; the highest effect class
  is computed only by `flows` (A05 rule 5). `effects` asks which classes stop
  for approval, take a grant or are `draft-write` (A10), by member;
  `service_invoker` asks only whether a class is `read`, to choose the column of
  the A09 rule 5 table; `bindings` checks that a manifest's `effect_class` is
  a member of the enumeration (A08 rule 5). No other module looks at effect
  classes. The class of an execution for masking (A07
  rule 5) is computed by `surface` from the records it returns.
- **Writing records.** Every record is written through `store`, which owns
  its persistence and the invariants of A18. Most record types have one writing
  module, named in its section. Three have several, on purpose: StoredValue M21
  and value bytes are written by whichever module produces or receives the
  value — `flows` for constants, `functions` for trial values, `runs` for flow
  inputs and function outputs, `run_values` for the values a run derives for
  delivery (below, "Delivering a value"), `effects` for service outputs — always
  through `store.put_value_bytes`, which stores equal bytes once (A18 rule 4);
  SpooledFile M22 and its bytes are written by the module that receives the
  file — `runs` for a function's file output, `effects` for a service's —
  the bytes through `store.spool_file` and the record in that module's change
  that concludes the element;
  NodeExecution M23 is written by `effects` for the record that concludes an
  operation element by a send, a pre-send failure or the owner's refusal,
  because it must share `effects`' outcome transaction (A11 rule 1), and by
  `runs` for every other record — an operation element concluded
  `contract_violation` on a misfit input before `effects` is called included
  (A13 rule 3), and the skips and upstream failures `run_graph` derives as
  drafts.
- **Reading records.** A module reads what a module it may know owns through
  that module's capability, and never decides from another module's raw
  records. The one exception is `surface` returning records as they are for
  inspection and traces, which it reads through `store` (below), so no module
  grows a read capability for display alone. Otherwise: `flows` reads contract
  versions through `functions.read_contract_version` and bindings through
  `bindings.read_binding`; `effects` reads bindings the same way and a flow
  version's nodes through `flows.read_flow_version`; `runs` reads the pinned
  graph through `flows.read_flow_version` and the pinned code and bounds through
  `functions.read_implementation`, reads every node's ports — a function
  node's from its pinned contract version, an operation node's through
  `bindings.read_binding` — and passes the graph, those ports and the run's
  trace to `run_graph`, which reads no port declaration itself and reads an operation element's conclusion (A11 rule 3)
  through `effects.operation_element_conclusion`. No module reads
  the records of a module above it.
- **Facts passed down.** When a lower module needs a fact a module above owns,
  the caller passes it in the call; the lower module never looks it up. `runs`
  passes to `effects` the run's id, its pinned flow version and that the run has
  not ended, with every call about one of its elements — which is how a grant
  is checked against the pinned version (A10 rule 1) — and passes to
  `functions.add_captured_trial_case` the executed implementation and the
  inputs of the record it captures, spooled files as their SpooledFiles, with
  the contract version the caller named;
  `functions` copies those files' bytes after its checks and writes the
  file-carriage StoredValues for them (M21) and the TrialCase that names them.
- **Inspection, traces and the repair view.** `surface`, which may know every
  module, assembles every read the State 0 inspect and read-a-trace actions
  list, and the repair view of one slot (A15 rule 6, K-12), from the owning
  modules' read capabilities and `store.page_records`. `store.page_records`
  pages one record type in reverse store order under a filter the caller
  gives — a field equal to a value or in a set of values; the exact filter
  forms are State 5's. Which records belong to a list is the caller's filter,
  not `store`'s knowledge. A NodeExecution names the implementation it executed
  (A15 rule 2), not a contract version; so for the repair view `surface` takes
  the slot's contract versions and their implementations from
  `functions.read_slot` and pages the NodeExecutions whose executed
  implementation is in that set, at most `page_size_max`. Runs are listed from
  their records, and each run's answer comes from `runs.read_run`. The
  class used for masking is computed by `surface` itself under A07 rule 5: that
  rule is about what a reader may see, which is `surface`'s. It reads raw records
  only to return them; a value a rule computes — a run's answer, an element's
  conclusion, a slot's current activation — comes from the owning module's
  capability, never from `surface` re-deriving it. It gives the "unknown
  reference" refusal and masks under A07, computing an execution's class from
  the records it returns only (A07 rule 5), and the class of an operation
  execution's `failure_detail` from that class and the output classes
  `bindings.read_binding` declares (A09 rule 7). A run is read through `runs.read_run` (below).
- **Run answers.** The run's status, its WaitingPoints and its produced
  outputs are derived from the trace by `run_graph.plan_run` and written by
  `runs` in its store calls (M19, M20); the reason per flow output not
  produced, `skipped_by_guard` or `not_produced` (A13 rule 7), is derived by
  `run_graph` from the trace when asked and is not stored. `runs.read_run` and every `runs` capability that moves a run
  return that answer. A run that rests
  carries only the outputs produced so far; the reasons appear once it has
  ended (A13 rule 7).
- **Capture.** Capturing a failed execution enters through
  `runs.capture_failed_execution`, which checks first, in this order, the
  record — a function element that ran in the sandbox and did not succeed
  (M06) — and then the run and its spool (A15 rule 5); it then calls
  `functions.add_captured_trial_case` with the record's inputs as references,
  spooled files as their SpooledFiles, and its executed implementation.
  `functions` reads that implementation's own record, checks that its
  contract version is the one named, then checks the complete input tuple and
  refuses any FileFactsRef, even an empty one, before looking up any input
  value or spooled file or reading input bytes. That refusal names FileFactsRef
  and the smallest offending port by Unicode code-point order. Only readable
  references continue to the case's existing fit and size checks on values and
  file facts; only then does it copy each spooled file's
  bytes into the content-addressed area through `store` and adds the case to
  the corpus (A04 rule 1, M06). A refused capture copies nothing.
- **NodeExecution records.** The record's shape is M23 in `models`. The record
  that concludes an operation element — a send, a pre-send failure, a refusal by
  the owner — is built and written by `effects` inside its outcome call (A11
  rule 1), its status being the outcome name of A09 rule 5 or rule 6, or
  `refused_by_owner` for a refusal (A10 rule 3). Every
  other record — function elements, skips, upstream failures, a map over an
  empty list, a receiving element of either kind refused a misfit input (A13
  rule 3) — is built and written by `runs`.
- **Order of records written together.** A15 rule 1 orders the records of nodes
  that become non-executable together: skips and upstream failures, derived by
  `run_graph` as drafts in that order and all written by `runs` in one call. An operation's concluding record is an executed record,
  not one of them; it is written first, in `effects`' own call, and the records
  it makes non-executable follow in `runs`' next call, in (`node_id`,
  `map_index`) order. `runs` then writes the run's status and waiting points and
  returns the run as it now rests or ended; `surface` answers only after that.
- **Attempt numbers.** `store` alone assigns `attempt_number`, inside the
  transaction that writes the record, as the ordinal of the element's
  NodeExecutions (A11 rule 1); no caller passes a number, `effects` included.
  The in-flight EffectAttempt is given the next ordinal when `store` writes it.
  A file spooled before its record is written — a function output, a `read`
  send's file — is named by the element's next ordinal, which the spooling
  module reads as the count of the element's NodeExecutions plus one; `store`
  writes the record under that ordinal only while it is still the next one,
  refusing the change otherwise, and passes no number of its own choosing.
  A requested EffectApproval is given the next ordinal too, without taking
  it: it names the attempt it was requested for (A11 rule 1).
  The outcome call names the EffectAttempt, and `store` gives the concluding
  NodeExecution that attempt's number after checking that it is still the
  element's next ordinal, refusing the call otherwise. Requests are handled one at a time (A18 rule 3), so nothing writes
  a record for that element in between; start-up recovery uses the
  EffectAttempt's number too (A11 rule 4).
- **Spool ceilings.** `store.spool_file` alone checks both ceilings of A15
  rule 3 — the file against `spool_file_bytes_max`, the run's spooled files
  plus this one against `spool_run_bytes_max` — and on a refusal keeps nothing
  of that file or of any file the same attempt spooled before it; files of
  earlier attempts stay. The module that spooled concludes the element:
  `runs` for a function output (`resource_exhausted`), `effects` for a service
  output (`contract_violation`, the attempt `applied`). `service_invoker`
  judges only the response ceiling and never sees the run's spool.
- **Idempotency key.** `effects` computes the EffectAttempt's
  `idempotency_key` from the key fields of the ManifestOperation that
  `bindings.check_binding_current` returns and the element's inputs, with
  `canonical_values` (A08 rule 4).
- **Classes of stored values and spooled files.** The module that writes a
  StoredValue M21 or a SpooledFile M22 sets its class, by one rule (A07 rule 3)
  computed with `canonical_values.highest_disclosure_class`: `flows` for
  constants (the class the composing agent declared, A07 rule 2), `runs` for
  flow inputs (the port's class) and for function outputs, values and files
  alike (the highest class received), `run_values` for the values it derives
  for delivery (a list element its list's class, a list the highest class of
  its elements, an empty list the highest class of the node's inputs, A13
  rule 6), `effects` for service outputs, values and
  files alike (the binding's declared class), `functions` for trial cases and
  trial outputs (a case input, authored or captured, the class its contract
  input port declares; an expected output and a trial output, the highest class
  of the case's inputs; M21).
- **Owner decisions on effects.** Whether the run has ended is checked first
  by `runs`, which owns the run's status; whether the approval is `requested` or
  the attempt `unknown` is then checked by `effects`, which owns those records
  (A10 rule 3, A11 rule 3). `effects` never reads a run's status. Approve, refuse and resolve enter through
  `runs.continue_after_approval` and `runs.continue_after_resolution`, because
  each moves the run (A13 rule 1); the decision records themselves are written
  by `effects.decide_effect_approval` and `effects.resolve_unknown_outcome`,
  which `runs` calls first; after an approval `runs` reaches the element again
  through `effects.reach_operation_element`, which sends at once in the same
  request (A10 rule 3). Grant and revoke move no run and go to `effects`
  directly: a grant is given only for a node of the active version (A10 rule
  5, through `flows.active_flow_version`), and a send uses a grant for the
  run's pinned version (A10 rule 1).
- **Run state after an element.** The element's records are the truth; the
  run's status and WaitingPoints M20 are derived from them and written by `runs`
  in its next store call. A crash between the two leaves a run `running`, which
  start-up recovery advances (A14 rule 5); nothing has to share the outcome
  transaction. A `refused_by_owner` record ends its run `refused` whenever
  `runs` next derives the run, so a crash before `runs` writes the status sends
  nothing more: recovery derives `refused` before reaching any element.
- **Instance facts.** The instance's `api_base_url`, `required_headers` and
  class come from the manifest, read by `bindings`; the instance name and the
  credential header come from `installation`. The start check that no
  credential header has the name of a required header or of a header the
  kernel sets itself, `host` included (A09 rule 1), is
  `bindings.check_installed_instances`, a required start step that `surface`
  calls right after `installation.load_installation` and before the store is
  opened; it reads only the installation and the manifest, never the store. At send `service_invoker` judges only the
  instance facts the ManifestOperation carries, and reads nothing from
  `installation` but the credential.
- **Stopping after an internal error.** `surface` owns it: every failure it
  answers `internal_error` — a store failure, an unconfirmed cleanup, any
  unexpected exception — is answered first, and then `surface.serve_kernel`
  ends the process with a non-zero status, so the next start derives every
  run (A14 rules 5 and 7). No other module ends the process.
- **Pre-send order.** `effects` runs A09 rule 6 in its order: first
  `bindings.check_binding_current`, which returns the current ManifestOperation
  M10 — method, path, key fields, effect class, and the `base_url`,
  `required_headers` and `instance_class` of the instance whose name
  `installation.selected_instance_name` gives (A08 rule 2), absent when none is
  selected — or `binding_stale`. `bindings` judges only the record itself (A08 rule 6) and
  passes the instance facts on as read, even when missing. Then
  `service_invoker.prepare_request` with that operation owns every instance
  failure in A09 rule 6's order — no selected instance, no `api_base_url`, a
  plain `http` target not allowed, a repeated required header, an invalid
  required header (A09 rules 1, 4 and 6, A08 rule 5) — resolves the
  credential through `installation` and places the inputs, in that order,
  naming the first failure.
- **`read` against other classes.** `service_invoker` applies the A09 rule 5
  table, choosing its column by the effect class in the ManifestOperation it is
  given; `effects` writes an EffectAttempt, asks authority and computes a key
  only for classes other than `read` (A08 rule 4, A10).
- **Pinned versions.** The pinned Python dependencies and sandbox runtime of A20
  rule 3 are a release artifact built and checked outside the running kernel;
  at run time only `sandbox.probe_sandbox` checks that a sandbox works. No
  module owns them: the release that builds the kernel selects, records and
  verifies them, and `data_provider` holds no pin.
- **Start.** `surface.serve_kernel` runs the start in this order:
  `installation.load_installation`; `bindings.check_installed_instances`;
  `store.open_store`, which takes the lock,
  checks links and removes temporary files; `sandbox.probe_sandbox`;
  `effects.recover_in_flight_attempts`; `runs.recover_running_runs`, which first
  names to `store.remove_run_spool` every ended run that no longer keeps its
  spool (A14 rule 4), then derives again every run not ended — `running`,
  `awaiting_approval` or `pending` — from its records (below, "Recovering a
  waiting point"), rewriting a stored status or waiting point that lags
  them, and advances every run that derivation leaves `running`; and only then
  the first request (A03 rule 8, A14 rule 5, A18 rule 4).
- **Unconfirmed cleanup.** A03 rule 7 records the execution `crashed` with
  `cleanup_failed` and then stops the kernel; the record comes first, so that
  start-up recovery finds the element concluded and never executes it again.
  `sandbox` reports that outcome with `SandboxResult.stop_required` true and stops nothing. The module that called
  `sandbox.execute_function` writes the execution's record in its usual store
  call — `runs` the NodeExecution, `functions` the TrialExecution — then does
  nothing more in that request: no further element, no further case, no
  verdict, no activation, no run status. It returns the stop to its caller, and
  `surface` ends the process: during a request after answering it as an
  internal error (A16 rule 7), during the start by stopping the start. The
  run is left `running`; the next start's recovery advances it from there with
  that element concluded failed, so its dependants conclude `upstream_failed`
  and independent branches go on (A13 rule 5, A14 rule 5); an interrupted admission has no verdict, so the next
  submission of that implementation runs it again (A04 rule 2).
- **Nothing copied for a refused capture.** Only `functions`, after every
  check of the capture has passed (above, "Capture"), copies a spooled file
  into the content-addressed area, so a refused capture copies nothing and
  owner decision 9 holds: the only files kept beyond a run are trial-case
  fixtures. Only a store failure between the
  copy and the case's write can leave bytes no record names; they are never
  served and enter no case (A18 rule 4).
- **Delivering a value** (decision 32). `run_graph` names, for each element
  of the next ready node, where each input comes from: a record already
  written, the element of a list at a `map_index`, or a list a mapped node's
  elements produced, which it has `run_values.assemble_mapped_lists` build and
  measure without writing — every delivered list of the node against
  `stored_value_bytes_max`, so a list over it fails the node with no record
  (A13 rule 6, A15 rule 4). `runs` hands each source with its receiving port
  to `run_values.deliver_input`, which writes what the source still needs
  written through `store.record_change` and only then checks it with
  `canonical_values.fit_port_value`, returning the written reference or the
  misfit. No module below `runs` reads a value that is not written, and no
  value reaches `sandbox` or `effects` unchecked. The empty list of a mapped
  node over an empty list is built by `run_values.empty_list_outputs` and
  written by `runs` with the node's one NodeExecution (A13 rule 6).
- **Recovering a waiting point** (decision 32). Recovery has no rule of its
  own about a waiting point. At start `runs` derives every run not ended with
  `run_graph`, which asks `effects.operation_element_conclusion` for each
  operation element: a wait that still holds stands, with its present reason;
  an element whose approval the owner approved — a refused one ends the run
  `refused` through its `refused_by_owner` record — or whose attempt the owner resolved
  `not_applied`, is not reached and so is ready. A run derived `running` is
  advanced with `runs`' own advance, which reaches every ready element while
  other elements still wait (A13 rule 8) — after `not_applied` the reach
  requests a fresh approval (A11 rule 3) — and writes the status it ends at; a
  run derived still waiting is not advanced, only its lagging status and
  waiting points are rewritten (A11 rule 4, A14 rule 5).
- **The runner** (decision 32). `sandbox_runner` owns the program that runs
  inside the environment, its text, its command line and the reading of the
  report it sends to the parent; `sandbox` owns the environment's launch, the
  exchange directory and every judgement from outside. Every descriptor the
  runner writes to reaches it by inheritance (`pass_fds`) at the number the
  parent's own descriptor has, and the runner learns that number from its
  command line; nothing renumbers a descriptor.
- **Continuation tokens.** `surface` checks the token's form; whether it names
  a record of that type is answered by `store.page_records`, which refuses
  one that does not (A16 rule 6).

## `models`

### Owns

The State 1 records M01–M28 as plain typed data, with their closed status and
class enumerations. No behaviour.

### Knows

Nothing.

### Must not own

Validation, identity computation, persistence or any rule about when a record
may change.

### Depth assessment

- kind: deep
- hidden mechanism: type validity of the kernel's shared vocabulary; a rule
  placed here would have no single owner

## `data_provider`

### Owns

A20: the release constants generated code reads — one `RELEASE_CEILING_<NAME>`
per ceiling with the values of release v1; the closed lists of trapped
standard-library entry points of A03 rule 4 and the sandbox environment of A03
rule 1; the minimum token length of A16 rule 1; the instance classes that allow
plain `http` and the class an absent or unknown one counts as (A09 rule 4); the
headers the kernel sets itself and the one of them an instance may set instead
(A08 rule 5); the form of a `service_id` and the file name suffix of a service
record (A08 rule 1). Emitted as module constants (SPEC_STANDARD 15.3.1);
nothing overrides them. Closed sets that are a model's — classes, statuses,
HTTP methods — are `models` enumerations, and the field names of a manifest
record are the fields of its model, not constants. What code reads about the
members of such an enumeration — the conclusion each NodeExecution status gives
(A13 rules 5 and 7), what each node conclusion means for the run and for its
dependants (A13 rules 5 and 7), the status a run rests in for each wait reason
(A13 rule 8), whether an HTTP method carries a body (A09 rule 2) — is a
correspondence over that taxonomy (SPEC_STANDARD 15.2): a table here keyed by
the enumeration, total over its members, whose cells name members. The rules
that read these tables stay their owners': A13's are `run_graph`'s, A09's
`service_invoker`'s; this module holds only the values.

### Knows

`models`: the row models of its tables and the enumerations their cells name.

### Must not own

A default for a value nobody chose, a value read from the environment or the
configuration, or any check that uses a ceiling — each check belongs to the
module whose rule it is.

### Hides

The literal values: consumers import the symbols, and the values never enter a
generator's prompt (SPEC_STANDARD 15.9).

### Candidate public capabilities

```text
RELEASE_CEILING_<NAME> (one per A20 ceiling)
SANDBOX_TRAPPED_FUNCTIONS
SANDBOX_TRAPPED_WITHOUT_ARGUMENT
SANDBOX_TRAPPED_CLASS
SANDBOX_UNSEEDED_CONSTRUCTOR
SANDBOX_ENVIRONMENT
ACCESS_TOKEN_LENGTH_MIN
PLAIN_HTTP_INSTANCE_CLASSES
DEFAULT_INSTANCE_CLASS
KERNEL_SET_HEADER_NAMES
INSTANCE_SETTABLE_HEADER_NAMES
SERVICE_ID_PATTERN
MANIFEST_RECORD_FILE_SUFFIX
EXECUTION_STATUS_CONCLUSIONS
NODE_CONCLUSION_EFFECTS
EDGE_DELIVERY_RULES
WAIT_REASON_RESTING_STATUSES
HTTP_METHOD_BODIES
```

### Depth assessment

- kind: deep
- hidden mechanism: one home of every policy value, compiled into typed
  constants, so no module defines a second default (A20 rule 1)

## `canonical_values`

### Owns

A01 rules 1 and 4: canonical JSON (RFC 8785), the one measure of a JSON text's
depth (A20 rule 1), and the SHA-256 identities of
content records and values computed from it, with order-free lists sorted as
A01 rule 1 says. The supported `value_schema` subset and validation of a value
against a port: presence, carriage, schema, size, a `many` value as an array
of fitting elements, in that order (A04 rule 1, A12 rule 1, A13 rule 3). The
highest class of a set (A07 rule 3), compared by the disclosure-class order
that `models` declares (A07 rule 1); it neither defines nor repeats that order.

### Knows

`models`, `data_provider`.

### Must not own

Where a value is stored, who may see it, or what a failed fit concludes for a
node, a run or a request — the caller decides that.

### Hides

JCS number and string encoding, refusal of values JCS cannot represent, the
sorting keys of each content record, the schema subset interpreter.

### Candidate public capabilities

```text
canonical_bytes
json_depth
content_identity
fit_port_value
highest_disclosure_class
```

### Depth assessment

- kind: deep
- hidden mechanism: one canonical form from which every identity and every
  "same schema" comparison follows

## `clock`

### Owns

A19: the one source of kernel timestamps and of monotonic readings, from which
a bounded wait derives its deadline. Nothing else in the kernel reads a clock.

### Knows

Nothing.

### Must not own

Any decision based on time; no time limit decides anything (A14 rule 1).

### Hides

The wall and monotonic clocks, and their replacement by a fixed clock in tests.

### Candidate public capabilities

```text
kernel_now
monotonic_ns
```

### Depth assessment

- kind: deep
- hidden mechanism: the only reader of the host clocks, replaceable as a whole
  in tests (A19 rule 1)

## `store`

### Owns

A18: the data directory and the one SQLite database — the one connection, opened
at start, and the one transaction of every change — the exclusive start lock,
the content-addressed area of value bytes and file fixtures, the per-run spool,
publishing a file only complete and digest-checked, refusal of symbolic links,
start-time removal of temporary files, and removal of the spools `runs` names.
`attempt_number` as the ordinal of an element's NodeExecutions, computed inside
the transaction that writes one (A11 rule 1). Every
change is one call and one transaction (K-17). The one store order of records:
activation identity by position (A01 rule 3), corpus order (A04 rule 1), list
paging positions (A16 rule 6). No record of A01 rule 6 is ever edited or
deleted.

### Knows

`models`, `canonical_values`, `data_provider`, `store_persistence`.

### Must not own

Deciding which ended runs' spools are removed at start — that half of A18
rule 4 follows A14 rule 4 and belongs to `runs`; `store` removes what it is told. Who
may change what, when a run's spool is emptied or released (that is
`runs`), or any outcome of a node.

### Hides

The SQLite connection and its transactions, which record goes into which row
and in what order rows are read, file layout under the data directory, atomic
rename, opening without following links.

### Candidate public capabilities

```text
open_store
put_value_bytes
read_value_bytes
spool_file
remove_run_spool
record_change
read_records
page_records
```

`record_change` stands for the closed set of one-transaction calls the other
modules make; State 5 names each one. `read_value_bytes` returns the bytes a
StoredValue M21 or a SpooledFile M22 names, from the content-addressed area or
the run's spool; the caller names the record, never a place (owner,
2026-10-03, raised by State 4 round 3). A spooled file whose run no longer
holds its spool is refused.

Every read and write of a row goes through one typed record port,
`StoreRepository`: an interface whose operations are the typed row operations
of the closed record types — load by the complete key, find by store position,
list by an equality filter in store order, insert, and, for the five records
whose lifecycle fields change (OperationBinding, Run, EffectApproval,
StandingGrant, EffectAttempt), update of the row in place — and nothing else.
It accepts no table name, SQL fragment, untyped payload or path. Its one
implementation is `SqliteStoreRepository`, owned by `store_persistence` and
lowered from `persistence_backend/v3` (`implementation_obligations`,
disposition `local`). `store` builds it over its own connection inside the
transaction it opened, and keeps everything a row operation does not say:
opening, committing and rolling back the transaction, the order of store
positions, attempt numbers and minted identities, which rows a relation or a
page reads and how they combine, the files and their durability, and the lock.

### Depth assessment

- kind: deep
- hidden mechanism: one writer whose every change is whole or absent, and one
  order of records nobody else can produce

## `store_persistence`

### Owns

Only the deterministic SQLite repository class and schema function lowered from
`persistence_backend/v3` for the store's closed tables: one table per record
type of `store.read_records` and one for the store-position counter. A row is
the store's envelope of one record: its store position, its record type, the
fields a lookup filters on, and the record itself, whole.

### Knows

`models`.

### Must not own

The connection or its transaction, store positions, attempt numbers, minted
identities, which rows a relation or a page reads, any file, or any rule of
another module — all of these are `store`'s. It is part of the store module of
A18: only `store` calls it, inside the transaction `store` opened, so no other
module touches the database through it.

### Hides

SQLite table creation, row codecs and the typed insert, load, list and update
statements.

### Candidate public capabilities

```text
SqliteStoreRepository
create_store_schema
```

### Depth assessment

- kind: deep
- hidden mechanism: version-bound SQLite lowering from persistence_backend/v3

## `sandbox_runner`

### Owns

The inside of an execution (decision 32): the program that runs in the
environment — it sets the environment variables, the `setrlimit` limits of
A03 rule 5 and the traps and audit hook of A03 rule 4 before it loads the
code, counts the code's tasks against `process_count`, loads the code, calls
`run` once as A03 rule 3 says, pre-counts the outputs and sends them —; the
text of that program, the command line it is started with, and the reading of
the report it sent to the parent: trap hits, resource hits, the exception that
escaped, the returned outputs.

### Knows

`models`, `data_provider` (the trap lists, the sandbox environment, the
runtime paths, the scratch ceiling).

### Must not own

Starting, watching or killing the environment, the wall deadline, the output
count that decides, the outcome order, cutting `failure_detail`, cleanup —
all `sandbox`'s; which code runs or what an outcome means for a run or a
verdict.

### Hides

The runner's source text, how each trap is installed (on the module or as a
method, by the object the path names before its last dot, decision 31), the
audit hook and its task count, how the runner reads its inputs and frames its
messages on the channel.

### Candidate public capabilities

```text
runner_source
runner_arguments
read_runner_report
```

### Depth assessment

- kind: deep
- hidden mechanism: everything that happens inside the environment, behind one
  text, one command line and one decoded report; `sandbox` never learns how a
  trap is installed or how a message is framed
- the runner is a string: it runs in another interpreter and is never imported
  by the kernel. The Factory's reflection gate
  (`code_invariant_gates.reflective_access_findings`) judges calls in a
  module's syntax tree, not the contents of a string, so the runner's
  `setattr` stays legal while the module's own code calls none

## `installation`

### Owns

A17: the configuration file and its start checks — a regular private file of
the kernel's user, tokens at least 43 characters and pairwise distinct; the
re-read of the token list on every request when the file's digest changes, and
the state "no valid list" after a failed re-read — including a file that
cannot be read, which counts as changed (A16 rule 2) — in which `current_token_list`
returns none and `surface` refuses every request, with
the four checks of A16 rule 2; the selected manifest instance per service; the
manifest location and revision fixed at start (M28); resolution of a service
credential only when a request to that service is built.

### Knows

`models`, `data_provider`, `canonical_values`.

### Must not own

Comparing a presented token with the list (that is `surface`), reading the
manifest (that is `bindings`), or building a request.

### Hides

The configuration format, the file-mode checks, the credential reference
resolution on the host.

### Candidate public capabilities

```text
load_installation
current_token_list
selected_instance_name
resolve_service_credential
manifest_source
```

### Depth assessment

- kind: deep
- hidden mechanism: what the kernel may reach and with which secret is decided
  on the host and cannot be changed from a request

## `sandbox`

### Owns

A03: every execution of agent code, trial and real alike, from outside — the
fresh `bubblewrap` environment and its launch, the exchange directory, every
descriptor passed by inheritance at its own number, the runner started with
the command line `sandbox_runner` gives; the wall deadline and the output
count kept from outside, the closed outcome order, the bounded
`failure_detail`, confirmed cleanup, reporting an execution whose cleanup
cannot be confirmed as `crashed` with `cleanup_failed` (above, "Unconfirmed
cleanup"), and the start probe. What happens inside the environment is
`sandbox_runner`'s (above, "The runner").

### Knows

`models`, `data_provider`, `canonical_values` (output fit), `clock` (monotonic
readings for the wall deadline), `sandbox_runner`.

### Must not own

Which implementation runs, what its outputs mean for a run or a verdict, where
files go next, any retry, or stopping the process — it reports, and its caller
records before `surface` stops; the runner's text, traps or limits.

### Hides

Namespaces and mounts, the exchange directory, descriptor inheritance, the
wall deadline and the kill through a pidfd, process reaping.

### Candidate public capabilities

```text
execute_function
probe_sandbox
```

### Depth assessment

- kind: deep
- hidden mechanism: untrusted code computes and does nothing else, and every way
  it ends has one name

## `run_values`

### Owns

A13 rule 3's delivery check and the values of rule 6 (decision 32): every
StoredValue M21 a run derives for delivery and no NodeExecution names — the
element a mapped element receives from its list, and a mapped node's value
list, the canonical array of its elements' values —, measuring every
delivered list of a mapped node against `stored_value_bytes_max` before any
of them is written or delivered (A15 rule 4), writing each through
`store.record_change` before it is checked or passed on, and
`canonical_values.fit_port_value` against the receiving port; the reference
to a mapped node's file list; the empty lists of a mapped node over an empty
list, built for the node's own record; and the class of each of these values
(A07 rule 3, A13 rule 6).

### Knows

`models`, `data_provider`, `canonical_values`, `store`.

### Must not own

Which element receives a value next, which list is delivered, or what a misfit
or a list over the ceiling concludes for an element, a node or a run
(`run_graph`, `runs`); any NodeExecution; a function's or a service's outputs.

### Hides

Slicing a JSON array, the canonical array of the elements' values, the size
measure, the order write-then-check.

### Candidate public capabilities

```text
assemble_mapped_lists
deliver_input
record_flow_output
empty_list_outputs
```

### Depth assessment

- kind: deep
- hidden mechanism: a value reaches a node only once written and checked; the
  signature returns a written reference or a misfit, so no caller can pass on
  an unchecked value or read an unwritten one

## `service_invoker`

### Owns

A09: building one HTTP request from a binding, the selected instance and the
node's inputs — URL, query and body encoding, headers, the credential — and
sending it once with no redirect, proxy or retry; the outcome table of A09 rule
5; the pre-send checks of the instance and the inputs (A09 rule 6). Withholding
any body that echoes the credential before it becomes an output or `failure_detail`
(A09 rule 7), since only it holds the credential at the answer. The request
description and its `request_digest` (A10 rule 7), since only the builder knows
what will be sent. The shape rules a binding's ports must satisfy to be
invocable (A09 rules 2 and 3), offered to `bindings`.

### Knows

`models`, `data_provider`, `canonical_values`, `installation`, `clock`.

### Must not own

Whether a send is authorised, any EffectAttempt or approval record, or whether
a binding is stale.

### Hides

HTTP transport, percent-encoding, multipart construction, TLS policy by
instance class, response size counting and decoding.

### Candidate public capabilities

```text
check_request_shape
prepare_request
send_prepared_request
```

### Depth assessment

- kind: deep
- hidden mechanism: one request per attempt whose every ending has one name
  that says whether the effect may have happened

## `functions`

### Owns

A02 and A04: slots and contract versions with their ceilings check, the
purpose rule of A01 rule 5 for slots, implementations, trial cases and the
corpus, trying an implementation, admission and the kernel's activation of
what it admits, rollback, and adding a captured case to the corpus once
`runs` has checked the capture (A15 rule 5).

### Knows

`models`, `data_provider`, `canonical_values`, `clock`, `store`, `sandbox`.

### Must not own

Execution itself (`sandbox`), which implementation a run uses after it started
(`runs` pins it), or who may author (`surface`).

### Hides

Case validation, corpus digest, the never-stop-early admission over the whole
corpus, verdict reuse for an unchanged corpus, the activation rule.

### Candidate public capabilities

```text
issue_contract_version
read_contract_version
read_slot
read_implementation
submit_implementation
add_trial_case
try_implementation
roll_back_slot
add_captured_trial_case
current_activation
```

### Depth assessment

- kind: deep
- hidden mechanism: a growing regression corpus decides, with no human, which
  code serves a contract

## `bindings`

### Owns

A08: reading one service record at the configured revision, the operation's
`record_digest`, proposal checks in their fixed order, the owner's acceptance,
and the stale check before every send.

### Knows

`models` (effect classes), `data_provider`, `canonical_values`, `clock`,
`store`, `installation`, `service_invoker` (request shape).

### Must not own

Sending, the request's encoding, authority, or writing the manifest.

### Hides

The manifest record format, the `exposed_as.http_api` and `idempotency_key`
parsing, the digest of one capability entry.

### Candidate public capabilities

```text
propose_binding
read_binding
check_installed_instances
accept_binding
check_binding_current
```

### Depth assessment

- kind: deep
- hidden mechanism: the kernel's picture of a service cannot drift from the
  manifest silently

## `flows`

### Owns

A05 and A06: composition of flow versions with its pre-proof refusals, the
purpose rule of A01 rule 5 for flows, the nine-phase proof with the first
failure, the highest effect class, and activation by the kernel or the owner.
The proof-time reach of disclosure classes (A07 rule 2).

### Knows

`models` (effect classes), `data_provider`, `canonical_values`, `clock`,
`store`, `functions` (contract versions), `bindings` (binding status and
declared classes).

### Must not own

Executing a flow, approvals or grants, or anything a run decides.

### Hides

Graph checks, the fixed phase and edge orders, the can-both-deliver rule of
guarded edges, cycle detection, class reach.

### Candidate public capabilities

```text
compose_flow_version
read_flow_version
prove_flow_version
activate_flow_version
active_flow_version
```

### Depth assessment

- kind: deep
- hidden mechanism: one deterministic answer to "why is this flow not proven"

## `effects`

### Owns

A10 and A11: reaching an operation element in the order of A11 rule 1 —
pre-send checks, authority, the in-flight record, the send, the outcome record
— approvals and their coverage by `request_digest`, standing grants and their
revocation, EffectAttempts — whose numbers `store` assigns ("Attempt numbers")
—, the owner's resolution of an
unknown outcome, and turning `in_flight` into `unknown` at start.

### Knows

`models`, `data_provider`, `canonical_values`, `clock`, `store`, `bindings`
(current check), `service_invoker` (prepare and send), `flows` (the active
version and its nodes, for a grant).

### Must not own

Which element is reached next or what a run's status is (`run_graph`), or the
trace of function nodes (`runs`).

### Hides

The approval, grant and attempt lifecycles and the two store calls around every
send, so that an effect is never sent twice without a fresh decision.

### Candidate public capabilities

```text
reach_operation_element
operation_element_conclusion
decide_effect_approval
resolve_unknown_outcome
grant_standing_approval
revoke_standing_approval
recover_in_flight_attempts
```

### Depth assessment

- kind: deep
- hidden mechanism: an effect leaves the kernel only on an input the owner
  covered, once, and an unknown outcome is never guessed
- one module, not three: the approval, the grant and the attempt change in the
  same two store calls around one send (A11 rule 1), so splitting them would
  split one transaction topology

## `run_graph`

### Owns

A13 rules 2, 4, 5, 7 and 8 as one derivation that writes nothing (decision
32): from a run, its pinned flow version and its trace, the conclusion of every
element — a function element's from its NodeExecution, an operation element's
from `effects.operation_element_conclusion` —, which nodes are ready and the
next one by the smallest `node_id`, with its elements in list order and where
each input comes from; whether each edge is enabled, disabled or not yet
decided, the guard read from the `guard_port` of the edge's own source node
(M15); the `skipped_by_guard` and `upstream_failed` records that became
determined, as drafts in (`node_id`, `map_index`) order (A15 rule 1); the
WaitingPoints (A14 rule 1); the status the run stops in; its produced outputs
and the reason of every missing one.

### Knows

`models`, `data_provider` (conclusion and edge-delivery tables), `store` (value bytes),
`run_values` (mapped lists), `effects` (an operation element's conclusion); no
clock — the time of a draft is the `now` `runs` passes.

### Must not own

Any write, executing or reaching an element, delivering or checking a value,
the size measure of a list (`run_values`), or when the run is advanced (`runs`).

### Hides

Readiness, the smallest-`node_id` choice, element order, guard evaluation, skip
and upstream failure propagation, run conclusion.

### Candidate public capabilities

```text
plan_run
```

### Depth assessment

- kind: deep
- hidden mechanism: one deterministic answer to "where does this run stand and
  what executes next", the same from any reader and after any restart

## `runs`

### Owns

A12, A14, A15 and A13 rule 1: starting a run and pinning; advancing it inside
the request that moves it, as the one loop that asks `run_graph` where the run
stands, has `run_values` deliver each input, executes a function element
through `sandbox` and reaches an operation element through `effects`, and
writes the run's progress; resume, cancel, the run's spool and its release,
which ended runs no longer keep a spool at start, start-up recovery of every
run not ended (above, "Recovering a waiting point"), the conditions of
capturing a failed execution (A15 rule 5), and the trace: every NodeExecution
other than the one `effects` writes to conclude an operation element by a
send, a pre-send failure or the owner's refusal — `run_graph`'s drafts
included —, and the class of function outputs and flow inputs (A07 rule 3).

### Knows

`models`, `data_provider`, `canonical_values`, `clock`, `store`, `sandbox`,
`run_values`, `functions` (current activation, a function node's ports),
`bindings` (an operation node's ports, through `bindings.read_binding`), `flows`
(active version), `effects`, `run_graph`.

### Must not own

Readiness, guards, propagation or the run's derived status (`run_graph`), the
values derived for delivery and their check (`run_values`), approval coverage,
attempt numbers or the send (`effects`), the proof (`flows`), or who may start,
resume or cancel (`surface`).

### Hides

The order of one advance, the store calls that move a run, element execution,
the spool lifecycle.

### Candidate public capabilities

```text
start_run
continue_after_approval
continue_after_resolution
resume_run
cancel_run
release_run
recover_running_runs
read_run
capture_failed_execution
```

### Depth assessment

- kind: deep
- hidden mechanism: a run moves only inside a request, in one order of steps,
  and every step is recorded before the next one

## `surface`

### Owns

A16: the one MCP entrance — request size, token comparison in constant time
against the installation's current list, the depth of the message (A20), the operation schemas and their
bounds, the actor table of A16 rule 3, handling one request at a time to its
end, run advancement included (A18 rule 3), paging parameters, the reads of
inspection, traces and the repair view of a slot (A15 rule 6), and responses that
carry no secret, path or stack trace; ending the process when a module returns
the stop of an unconfirmed cleanup, after that module has written its record
(above, "Unconfirmed cleanup"). The single rule that an agent receives a
`personal_data` value or file only as digest and class, and a classified
`failure_detail` only as length and class (A07 rules 4 and 5). The order of
process start, every step required, as "Start" above lists it: installation,
the installed instances, store, sandbox probe, `in_flight` recovery, run
recovery, and only then the first request (A03 rule 8, A09 rule 1, A14 rule 5,
A18).

### Knows

Every module's public capabilities, except `store_persistence`, which only
`store` calls.

### Must not own

Any operation's own checks or records; it decides only whether a request
reaches an operation and what of the answer a caller may see.

### Hides

The MCP protocol, request schemas, the masking of personal data, error
sanitising.

### Candidate public capabilities

```text
serve_kernel
```

### Depth assessment

- kind: deep
- hidden mechanism: one entrance and one list of who may do what, so nothing an
  agent sends becomes the owner's decision

## Carried from State 2

Two single-review topics of round 19 that change no rule of State 2; closed in
the state named, by the module named:

- State 5, `effects`: which of several approved, unused approvals with the same
  `request_digest` is used — possible after owner decision 18 when a restart
  changes a header and changes it back. Closed: State 5, closed question 2.
- State 6, `bindings` and `effects`: whether a send whose declared
  idempotency-key field is `null` is refused.
- State 5, `effects`: which FlowActivation M18 a `draft-write` send names as its
  authority (A10 rule 6) when the run's version was activated more than once.
  Closed: State 5, closed question 3.
