# State 2 — Cabinet Kernel function, sandbox and admission rules

Draft of 2026-09-30. Rules for slots, contracts, implementations, the sandbox,
trial corpora, admission and activation (K-02, K-04, K-05, K-12). Where a text of
`examples/cabinet-flow` State 2 still holds it is reused and named; everything
the kernel removed (vocabulary, delegations, withdrawal, copying of cases,
per-reader ceilings) is left out.

## Accepted decision A01 — identity is computed by the kernel; an equal submission changes nothing

Reuses cabinet-flow decision 05, narrowed to the records this kernel keeps.

### Normative rules

1. `contract_version_id` M03, `implementation_id` M05, `trial_case_id` M06,
   `flow_version_id` M13 and `value_id` M21 are computed by the kernel from the
   facts State 1 names for each, as the SHA-256 of their canonical JSON — RFC 8785
   (JCS), which fixes number formatting, string escaping and key order; a value
   JCS cannot represent (a non-finite number, a duplicate key) is refused where
   it enters, and no Unicode normalization is applied. Lists
   whose order carries no meaning are sorted before hashing — ports by
   (`direction`, `name`), nodes by `node_id`, edges in the edge order of A05,
   constants by (`to_node`, `to_port`) — so the same content in another order has
   the same identity; list values themselves keep their order. A request that
   supplies one of these identities is refused.
2. `trial_execution_id` M07, `binding_id` M11, `run_id` M19, `approval_id` M24 and
   `grant_id` M25 are minted at random by the kernel; one that already exists is
   minted again. A caller never supplies one
   to create a record; it supplies one only to name an existing record.
3. Activation M09 and FlowActivation M18 records are identified by their position
   in the store's one order of records (K-17); a later activation of the same
   implementation or flow version is a new record, never the old one again.
4. Submitting content whose computed identity already exists returns the existing
   record unchanged: its first author and time stay, nothing new is recorded for
   it, and it does not become "the one issued last". In particular an equal
   contract version does not become its slot's current contract version again.
   What an equal implementation submission still does is fixed by A04 rule 2.
5. The purpose of a slot or a flow is taken only from the request that creates it.
   A later request that names an existing slot or flow with a different purpose is
   refused; one with the same purpose, or none, is accepted. A request that
   would create a slot or a flow without a purpose is refused. This check comes
   first among the operation's own checks, after the checks every request
   passes (A16 rule 1: size, token, schema, actor).
6. No issued contract version, implementation, trial case, flow version, value,
   verdict, activation or trace record is edited or deleted by any operation.

### Formal invariants

```text
identity(content_record) = sha256(canonical_json(meaning_facts(record)))
caller_supplied(content_identity) -> refused
exists(identity(submitted)) -> return existing AND record_nothing_for_it
activation_record_identity = store_order_position
purpose(slot | flow) fixed_at_creation
```

### Required tests

1. The same implementation code submitted by two agents at different times is one
   implementation with the first submitter recorded.
2. A request carrying its own `contract_version_id` is refused.
3. Re-issuing an older, equal contract version returns it and leaves the slot's
   current contract version unchanged.
4. Two contract versions differing only in one resource bound have different
   identities.
5. A request naming an existing slot with a different purpose is refused.

### Consequence

"Which code ran" and "which flow ran" each have one answer that no caller can
assert, and repeating a request is always safe.

## Accepted decision A02 — a contract version is valid only within the release ceilings

Closes the State 1 question whether bounds above the ceilings are clamped or
refused.

### Normative rules

1. A contract version is issued only when: every port name is unique within its
   direction; every input port declares a disclosure class and no output port
   declares one (M01); a `file` port declares exactly one media type and a `value`
   port none; every `value_schema` is within the supported schema subset (State 6);
   there is at least one output port; and every field of ResourceBounds M04 is a
   positive integer not above the release ceiling of the same name (A20). When
   several conditions fail, the first in this list is named.
2. A bound above its ceiling is refused, never clamped. The refusal names the
   field and the ceiling. A bound omitted by the author is refused as well: the
   kernel supplies no default, because a default is a value nobody chose.
3. The first contract version of a new slot name creates the slot (M02) and
   requires a purpose. Only an agent with the author right issues contract
   versions.

### Formal invariants

```text
issued(contract) -> for_all bound: 0 < bound <= ceiling(bound.name)
bound > ceiling -> refused   (never clamped)
bound absent -> refused
issued(contract) -> outputs != empty AND unique_port_names AND classes_on_inputs_only
```

### Required tests

1. Every bound exactly at its ceiling is accepted; one unit over is refused with
   the field named.
2. A contract without `memory_bytes` is refused.
3. A contract whose output port declares a disclosure class is refused.
4. A `file` port without a media type, and a `value` port with one, are refused.

### Consequence

What a function may consume is stated by its author and checked once; the sandbox
never has to guess a limit or silently lower one.

## Accepted decision A03 — every function execution runs isolated, bounded and without a clock

Reuses cabinet-flow decisions 06 and 34, narrowed: one isolation mechanism, Python only,
and no detection promises the runtime cannot keep.

### Normative rules

1. Every function execution, in trial and in a run alike, runs in a fresh
   isolated environment created by the sandbox: Linux `bubblewrap` with new user,
   PID, IPC, UTS and network namespaces, no network interface, an environment
   holding only `PYTHONHASHSEED=0` (rule 2), a read-only runtime, and one private exchange directory bounded by
   `sandbox_scratch_bytes_max`. No host directory is mounted except the read-only
   runtime and that exchange directory. There is no in-process or fast path.
2. The runtime is one Python interpreter with its standard library and nothing
   else, fixed by the kernel release (State 0 questions 4 and 17: photo processing
   is the agent's own work outside the kernel), started with a fixed
   hash seed (`PYTHONHASHSEED=0`) so that set and dict ordering repeats. Adding a
   library is a new kernel release.
3. An implementation is a Python module that defines a top-level function `run`
   taking one argument, a dict with one entry per input port, and returning a dict
   with exactly one entry per output port. A `value` port carries the JSON value
   decoded to Python (`dict`, `list`, `str`, `int`, `float`, `bool`, `None`); a
   `file` port carries `bytes`, and a `many` port a Python `list` of its element
   type — of `bytes` for a `many` file port, each element validated like a single
   one. A mapped node (M14) calls `run` once per element
   with that element in place of the mapped port's list.
4. Before loading the module, the in-sandbox runner replaces every clock and
   randomness entry point of the standard library (`time`, `datetime` current-time
   functions, `os.urandom`, `random` seeding, `secrets`) with one that raises, and
   installs an audit hook that raises on socket, subprocess, `ctypes` and on
   opening any path outside the exchange directory and the read-only runtime.
   The replaced entry points are exactly: `time.time`, `time.time_ns`,
   `time.monotonic`, `time.monotonic_ns`, `time.perf_counter`,
   `time.perf_counter_ns`, `time.process_time`, `time.process_time_ns`,
   `time.localtime`, `time.gmtime`, `time.ctime` and `time.asctime` when called
   without an argument, `datetime.datetime.now`, `datetime.datetime.utcnow`,
   `datetime.datetime.today`, `datetime.date.today`, `os.urandom`,
   `os.getrandom`, `uuid.uuid1`, `uuid.uuid4`, every function of `secrets` (its
   `__all__` without the class `SystemRandom`, which is trapped as
   `random.SystemRandom`; for release v1: `choice`, `compare_digest`,
   `randbelow`, `randbits`, `token_bytes`, `token_hex`, `token_urlsafe`), and
   the module-level functions of `random` (`random.random`, `randint`, `choice`
   and every other function the module exports), any method of
   `random.SystemRandom`, and `random.Random` constructed without a seed or with
   `None`; `random.Random(seed)`
   with an explicit seed stays usable. The list is closed for the release; an
   entry point found missing is added by a new release. "Every function the
   module exports" is the release interpreter's `random.__all__` without the
   classes `Random` and `SystemRandom`; for release v1 (CPython 3.12, A20 rule 3)
   it is, written out: `betavariate`, `binomialvariate`, `choice`, `choices`,
   `expovariate`, `gammavariate`, `gauss`, `getrandbits`, `getstate`,
   `lognormvariate`, `normalvariate`, `paretovariate`, `randbytes`, `randint`,
   `random`, `randrange`, `sample`, `seed`, `setstate`, `shuffle`, `triangular`,
   `uniform`, `vonmisesvariate`, `weibullvariate` (pre-contract data closure,
   2026-10-03). Each trap, before raising, writes its hit to the
   runner's channel to the parent, which user code cannot unsend; any recorded hit makes the
   execution `sandbox_violation` under the order of rule 5, even when the code
   catches it and returns a conforming output: `timeout` and `resource_exhausted`
   still come first. These traps classify ordinary attempts; the isolation of
   rule 1 is the security boundary, not the traps.
5. ResourceBounds M04 are enforced from outside the environment with `setrlimit`
   (address space, processes) and the parent's own wall deadline and output
   count. The output count is the sum of the canonical JSON bytes of every
   `value` output and the bytes of every `file` output of the one call of `run` —
   for a `many` file output, the sum of its elements' bytes. Outcomes are closed and checked in this order, the first that holds
   deciding: wall deadline passed — `timeout`; a limit hit (memory, process count,
   scratch, `output_bytes`) — `resource_exhausted`; a trap of rule 4 raised —
   `sandbox_violation`; the module failed to load, has no `run`, raised, or the
   process exited abnormally — `crashed`; the returned dict does not have exactly
   the output ports, or a value fails its port's schema, or a file output is not
   `bytes` — `contract_violation`; otherwise the execution succeeded. Output over
   the bound is a failure, never truncated.
6. Nothing the code prints or raises is interpreted by the kernel. The kernel keeps
   at most `failure_detail_bytes_max` of it as `failure_detail`, and only for the
   exception type and message, never stdout.
7. An execution completes only after every process of the environment is reaped
   and the exchange directory is removed. If that cannot be confirmed the output
   is discarded, the execution is recorded `crashed` with detail
   `cleanup_failed`, and the kernel process stops; runs it left `running` are
   recovered on the next start (A14 rule 5).
8. The kernel checks at start, before recovery and before the surface opens,
   that `bubblewrap` is present and that one probe execution succeeds; without
   both it does not start, and says why. A running kernel therefore always has
   a sandbox.

### Formal invariants

```text
function_executed -> inside(fresh_bubblewrap_environment)
environment = {python_stdlib_runtime, code, inputs, exchange_dir}
network(environment) = absent AND env_vars(environment) = {PYTHONHASHSEED=0}

trap_raised -> outcome = sandbox_violation   (even if output conforms)
outcome = first_of(timeout, resource_exhausted, sandbox_violation, crashed,
                   contract_violation, succeeded)
cleanup_unconfirmed -> output_discarded AND kernel_process_stops
```

### Required tests

1. Code that calls `time.time()`, `os.urandom`, opens a socket or reads `/etc`
   concludes `sandbox_violation`, also when it swallows the error and returns a
   conforming output.
2. A busy loop ends `timeout`; an allocation loop and a fork loop end
   `resource_exhausted`; no process survives.
3. An output one byte over `output_bytes` is `resource_exhausted`, not truncated.
4. A module without `run`, and one with a syntax error, are `crashed`; neither
   raises inside the kernel process. Submitting code never compiles, imports
   or parses it — the kernel process never interprets agent text (A16 rule 5)
   — so a module that cannot load is stored as an implementation like any
   other, its trial executions are `crashed` and admission refuses it (A04
   rule 3). State 0's "invalid … code refused" is the refusal of the request
   itself: code over its bound or a request off its schema (A16 rule 4).
5. A returned dict with an extra key is `contract_violation`.
6. The same implementation on the same input yields the same output digest twice.
7. With `bubblewrap` absent the kernel does not start and names the missing
   sandbox.

### Consequence

Agent code stays untrusted forever at no cost: it can compute and do nothing
else, and every way it can end has one name.

## Accepted decision A04 — admission runs the whole corpus in one order; a submission activates what it admits

Reuses cabinet-flow decisions 07, 08 and 09, narrowed by K-05 (no withdrawal, no copying)
and K-17 (no compare-and-set: one writer). Closes the State 1 questions of the
admission order and of resubmitting an equal implementation.

### Normative rules

1. A trial case is authored only by an agent with the author right, and captured
   from a failed execution only by the owner or such an agent (State 0). Either
   way it is added only when its input values fit the contract version's input
   ports, its expected outputs, when present, fit the output ports, and every
   value is within `stored_value_bytes_max` and every file within
   `trial_fixture_bytes_max` — the first failing condition in this order is
   named, ports taken in name order and, for one port, presence, carriage,
   schema, then size. The corpus of a contract version is its
   cases in the order they were first added — the store's order (K-17). A case
   equal to an existing one is that case and keeps its place.
2. Submitting an implementation — new, or equal to an existing one — runs
   admission unless an AdmissionVerdict M08 for that implementation and the
   current corpus digest already exists, in which case that verdict is used. The
   corpus digest is the SHA-256 of the canonical JSON of the list of its
   `trial_case_id`s in corpus order.
   Admission executes the implementation on every case of the corpus, in corpus
   order, each as one TrialExecution M07, and never stops early.
3. A case passes when the execution succeeded and, if the case states expected
   outputs, every output's digest equals the expected one — a file output is
   recorded in the TrialExecution by digest, size and media type, keeps no bytes,
   and is compared with the expected file fixture by digest; a `many` file output
   equals its expected list when both have the same length and the digests are
   equal position by position, so order and repetitions count; outputs that
   validate but differ are `output_mismatch`. The verdict is `admitted` exactly
   when the corpus is non-empty and every case passed; otherwise `refused` with
   reason `empty_corpus`, or with the first case in corpus order that did not
   pass and its outcome.
4. An `admitted` verdict is followed at once, in the same request, by an
   Activation M09 by the kernel — unless that implementation already is the
   current activation, in which case nothing is recorded. A `refused` verdict
   activates nothing and leaves the current activation serving.
5. Rollback activates an earlier implementation of the slot's current contract
   version that already holds an `admitted` verdict over the current corpus; it
   runs no admission. Naming the implementation that is already current returns
   the current activation and records nothing. An implementation without such a
   verdict is refused; to
   re-admit an earlier implementation over a grown corpus the agent submits it
   again under rule 2.
6. Trying an implementation (State 0 action), by any agent,
   executes an existing implementation on the cases of its contract version's
   corpus that the request names, all of them when it names none, in corpus
   order, records one TrialExecution per case and returns them. A request naming
   an unknown case, a case of another contract version, or one case twice is
   refused before anything executes, and so is a try on an empty corpus, as
   `empty_corpus`. It computes no
   verdict and activates nothing.
7. Capturing a failed execution (M06 rule, State 0 action) adds a case and so
   changes the corpus digest; the serving implementation keeps serving. It
   visibly lacks a verdict over the current corpus when the slot is inspected,
   and serves until another implementation is activated.
8. No actor records, edits or waives a verdict. Admission requires no human:
   a function has no effect for a human to weigh (K-02).

### Formal invariants

```text
corpus_order = order_first_added
admitted <-> corpus != empty AND for_all case IN corpus: passed(case)
refused.reason = empty_corpus OR first_in_corpus_order(not passed)

submit(impl) AND verdict(impl, current_corpus) = admitted
  AND current_activation != impl  -> new Activation(by kernel)
rollback(impl) -> exists verdict(impl, current_corpus) = admitted
verdict -> set_only_by_kernel
```

### Required tests

1. An implementation for a contract version with no cases is refused as
   `empty_corpus` and nothing is activated.
2. With cases c1, c2, c3 added in that order and c2, c3 failing, the reason names
   c2; the verdict still records three executions.
3. Submitting an admitted implementation activates it; submitting it again changes
   nothing.
4. After a failed run is captured, submitting the earlier implementation again runs
   admission over the grown corpus; it is activated only when it passes.
5. A rollback to an implementation with no verdict over the current corpus is
   refused.
6. No operation lets the owner or an agent set a verdict.

### Consequence

A repaired slot stays repaired, the verdict always says which case failed first,
and changing or undoing behaviour is one request.
