# State 3 — Cabinet Kernel module responsibilities

Draft of 2026-10-01. Derived from the accepted State 2 decisions A01–A21. A module
owns one hidden mechanism and has one reason to change; its public surface is
smaller than what it hides. Ownership of each decision is recorded in
`30_trace.json`: one primary owner, and the modules that consume the rule.

The kernel is one process with one writer (K-17), so modules are not services:
they are the parts of one program, and only `store` touches the database and the
data directory. The dependency direction is fixed, from the bottom up:

```text
models, data_provider
canonical_values, clock
store, installation
sandbox, service_invoker
functions, bindings
flows
effects
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
  module, named in its section. Two have several, on purpose: StoredValue M21
  and value bytes are written by whichever module produces or receives the
  value — `flows` for constants, `functions` for trial values, `runs` for flow
  inputs and function outputs, `effects` for service outputs — always
  through `store.put_value_bytes`, which stores equal bytes once (A18 rule 4);
  NodeExecution M23 is written by `effects` for the record that concludes an
  operation element by a send, a pre-send failure or the owner's refusal,
  because it must share `effects`' outcome transaction (A11 rule 1), and by
  `runs` for every other record — an operation element concluded
  `contract_violation` on a misfit input before `effects` is called included
  (A13 rule 3).
- **Reading records.** A module reads what a module it may know owns through
  that module's capability, and never decides from another module's raw
  records. The one exception is `surface` returning records as they are for
  inspection and traces, which it reads through `store` (below), so no module
  grows a read capability for display alone. Otherwise: `flows` reads contract
  versions through `functions.read_contract_version` and bindings through
  `bindings.read_binding`; `effects` reads bindings the same way and a flow
  version's nodes through `flows.read_flow_version`; `runs` reads the pinned
  graph through `flows.read_flow_version`, the pinned code and bounds through
  `functions.read_implementation`, and an operation element's conclusion
  (A11 rule 3) through `effects.operation_element_conclusion`. No module reads
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
  outputs are written by `runs` in its store calls, derived from the trace
  (M19, M20); the reason per flow output not produced, `skipped_by_guard` or
  `not_produced` (A13 rule 7), is computed from the trace when asked and is
  not stored. `runs.read_run` and every `runs` capability that moves a run
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
  contract version is the one named, and checks the case's fit and sizes to it
  on the values and the files' facts, and only then copies each spooled file's
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
  that become non-executable together: skips and upstream failures, all written
  by `runs` in one call. An operation's concluding record is an executed record,
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
  alike (the highest class received), `effects` for service outputs, values and
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
  at run time only `sandbox.probe_sandbox` checks that a sandbox works.
- **Start.** `surface.serve_kernel` runs the start in this order:
  `installation.load_installation`; `bindings.check_installed_instances`;
  `store.open_store`, which takes the lock,
  checks links and removes temporary files; `sandbox.probe_sandbox`;
  `effects.recover_in_flight_attempts`; `runs.recover_running_runs`, which first
  names to `store.remove_run_spool` every ended run that no longer keeps its
  spool (A14 rule 4), then derives again every run not ended — `running`,
  `awaiting_approval` or `pending` — from its records, and then advances the
  runs left `running`; and only then
  the first request (A03 rule 8, A14 rule 5, A18 rule 4).
- **Unconfirmed cleanup.** A03 rule 7 records the execution `crashed` with
  `cleanup_failed` and then stops the kernel; the record comes first, so that
  start-up recovery finds the element concluded and never executes it again.
  `sandbox` only reports that outcome; it stops nothing. The module that called
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
(A08 rule 5); the form of a `service_id` and the
file name suffix of a service record (A08 rule 1). Emitted as module constants
(SPEC_STANDARD 15.3.1); nothing overrides them. Closed sets that are a
model's — classes, statuses, HTTP methods — are `models` enumerations, and the
field names of a manifest record are the fields of its model, not constants.

### Knows

Nothing.

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
```

### Depth assessment

- kind: deep
- hidden mechanism: one home of every policy value, compiled into typed
  constants, so no module defines a second default (A20 rule 1)

## `canonical_values`

### Owns

A01 rules 1 and 4: canonical JSON (RFC 8785) and the SHA-256 identities of
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

A19: the one source of kernel timestamps and of monotonic deadlines. Nothing
else in the kernel reads a clock.

### Knows

Nothing.

### Must not own

Any decision based on time; no time limit decides anything (A14 rule 1).

### Hides

The wall and monotonic clocks, and their replacement by a fixed clock in tests.

### Candidate public capabilities

```text
kernel_now
monotonic_deadline
```

### Depth assessment

- kind: deep
- hidden mechanism: the only reader of the host clocks, replaceable as a whole
  in tests (A19 rule 1)

## `store`

### Owns

A18: the data directory and the one SQLite database, the exclusive start lock,
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

`models`, `canonical_values`, `data_provider`.

### Must not own

Deciding which ended runs' spools are removed at start — that half of A18
rule 4 follows A14 rule 4 and belongs to `runs`; `store` removes what it is told. Who
may change what, when a run's spool is emptied or released (that is
`runs`), or any outcome of a node.

### Hides

SQLite, the schema, transactions, file layout under the data directory, atomic
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

### Depth assessment

- kind: deep
- hidden mechanism: one writer whose every change is whole or absent, and one
  order of records nobody else can produce

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

`models`, `data_provider`.

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

A03: every execution of agent code, trial and real alike — the fresh
`bubblewrap` environment, the in-sandbox runner and its traps, limits enforced
from outside, the closed outcome order, the bounded `failure_detail`, confirmed
cleanup, reporting an execution whose cleanup cannot be confirmed as `crashed`
with `cleanup_failed` (above, "Unconfirmed cleanup"), and the start probe.

### Knows

`models`, `data_provider`, `canonical_values` (output fit), `clock` (monotonic
deadline).

### Must not own

Which implementation runs, what its outputs mean for a run or a verdict, where
files go next, any retry, or stopping the process — it reports, and its caller
records before `surface` stops.

### Hides

Namespaces and mounts, the runner and the exchange directory, `setrlimit`,
the trap channel, process reaping.

### Candidate public capabilities

```text
execute_function
probe_sandbox
```

### Depth assessment

- kind: deep
- hidden mechanism: untrusted code computes and does nothing else, and every way
  it ends has one name

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

Which element is reached next, what a run's status is, or the trace of
function nodes (`runs`).

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

## `runs`

### Owns

A12–A15: starting a run and pinning, advancing one node at a time inside the
request that moves it, guards, maps and failures, waiting points, resume,
cancel, the run's spool and its release, which ended runs no longer keep a
spool at start, start-up recovery of every run not ended (derived again from
its records, then advanced when left `running`), the conditions of
capturing a failed execution (A15 rule 5), and the trace: every
NodeExecution other than the one `effects` writes to conclude an operation
element by a send, a pre-send failure or the owner's refusal, the
order of records written together (A15 rule 1), and the class of function
outputs and flow inputs (A07 rule 3).

### Knows

`models`, `data_provider`, `canonical_values`, `clock`, `store`, `sandbox`,
`functions` (current activation, a function node's ports), `bindings` (an
operation node's ports, through `bindings.read_binding`), `flows` (active
version), `effects`.

### Must not own

Approval coverage, attempt numbers or the send (`effects`), the proof
(`flows`), or who may start, resume or cancel (`surface`).

### Hides

Readiness, the smallest-`node_id` choice, element order, skip and upstream
failure propagation, run conclusion, the spool lifecycle.

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
- hidden mechanism: the same flow on the same inputs always executes in the
  same order, and a run is always in the state it truly is in

## `surface`

### Owns

A16: the one MCP entrance — request size, token comparison in constant time
against the installation's current list, the operation schemas and their
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

Every module's public capabilities.

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
