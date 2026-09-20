# State 3 — Cabinet Flow kernel module boundaries

These boundaries are derived from the accepted State 2 rules A01–A24. A module
owns one named mechanism and one stable reason to change. A module that would
need a second mechanism to explain its surface is two modules. Transport
modules are thin and hold no policy. The facade modules own no mechanism and
say so.

## `models`

### Owns

The immutable vocabulary of typed values and records M01–M46: identities,
revisions, ports, contracts, implementations, trial and admission evidence,
bindings, flow graphs, proofs, activations, runs, node executions, approvals,
grants, reconciliations, proposals, stored values and spooled bytes, together
with the closed value sets each of them names.

### Knows

Only value-level invariants that can be checked without storage, credentials,
transport, clocks or installation configuration.

### Must not own

Identity computation, proof, admission, authority decisions, persistence,
execution, transport or any policy.

### Depth assessment

- kind: deep
- hidden mechanism: type validity of the kernel's shared vocabulary

## `system_clock`

### Owns

A25 and M47: the kernel's only source of current wall-clock and monotonic time,
including the exact canonical wall-clock representation as integer UTC epoch
microseconds.

### Knows

Only KernelInstant M47 and the host wall-clock primitive required by A25.

### Must not own

Time arithmetic of retention, back-off, throttling, lifecycle policy or
authorization; those belong to the modules that apply them. It supplies raw
clock readings and does not own elapsed-duration timeout policy.

### Hides

The two production clock primitives: `time.time_ns()` and
`time.monotonic_ns()`. One `now()` call takes exactly one wall-clock sample and returns
`KernelInstant(epoch_us = sample_ns // 1_000)`. Tests replace the entire
clock dependency with a deterministic implementation; `monotonic_ns()` returns
one raw integer sample, and no consumer patches or reads host time.

### Direct consumers

The injected `system_clock` dependency is used by
`access_control`, `semantic_vocabulary`, `slot_registry`,
`trial_corpus`, `admission`, `slot_activation`,
`operation_bindings`, `flow_proof`, `flow_registry`,
`owner_authority`, `operation_invoker`, `run_executor` and
`value_store`. These modules call `now()` only for timestamps or deadlines
they own. `kernel_surface` and the gateways never manufacture or forward a
"current time" value.

`sandbox_supervisor` and `service_transport` consume
`system_clock.monotonic_ns()` only for local non-persisted timeout measurement.

### Candidate public capabilities

```text
now
monotonic_ns
```

### Depth assessment

- kind: deep
- hidden mechanism: one injected clock module owning both host primitives and their distinct representations

## `identity`

### Owns

A05: the canonical serialization of every content-identified record kind and the
digest computed over it; the minting of stable identities for entities that are
not content-identified; the refusal of caller-supplied identities.

### Knows

Which fields of M20, M23, M24, M30, M32 and M38 are defining content, and that
author, time and rationale never are.

### Must not own

Storage of the identified records, idempotent lookup of an existing record, or
the meaning of any field.

### Hides

Field ordering, number and text normalization, serialization versioning and its
identity-preserving migration, the digest algorithm and the entropy source of
minted identities.

### Candidate public capabilities

```text
identify_contract_version
identify_implementation
identify_trial_case
identify_binding_version
identify_flow_version
digest_value
mint_identity
```

### Depth assessment

- kind: deep
- hidden mechanism: canonical serialization that makes equal content yield one identity

## `installation`

### Owns

A23 and A26: the installation record and its one owner principal; the selection
of one manifest instance per service and the refusal of mixed production and
non-production targets; resolution of credential references at the moment of
use; the immutable ReleaseCeilings M48 shipped with the exact kernel release;
the configured manifest repository revision.

### Knows

M16, M39, M48, instance classes of the manifest, the exact kernel release
identity and the host's protected configuration.

### Must not own

Authentication of requests, invocation of services, or any record of the
operational store other than the installation record.

### Hides

Where and how secrets are kept on the host, how a reference becomes a usable
credential without the value leaving the caller, and start-up validation of the
whole configuration.

### Candidate public capabilities

```text
resolve_service_target
resolve_credential
release_ceilings
manifest_revision
load_installation
```

### Depth assessment

- kind: deep
- hidden mechanism: host-held configuration and secret resolution that no record or request can influence

## `store_continuity`

### Owns

A30 rules 5 to 8: the evidence that the operational store remembers every effect
it began to send — the host's copy of the StoreContinuity M50 effect counter,
kept outside the data directory.

### Knows

M50, the closed continuity states, the host directory the installation names for
its state, and nothing of credentials, manifest or business records.

### Must not own

Opening the store, deciding an approval, sending anything, the owner's identity,
or the record of an effect attempt itself — it counts them, it does not keep
them.

### Hides

The host file that carries the counter, its atomic replacement and flushing, and
what a missing, stale or unreadable copy means.

### Candidate public capabilities

```text
open_continuity
advance_effect_counter
record_host_continuity_counter
confirm_continuity
```

### Depth assessment

- kind: deep
- hidden mechanism: recognizing a store that was put back from an older copy

## `operational_store`

### Owns

Durability of the kernel's own records: one transactional unit of work,
append-only enforcement for evidence records, compare-and-set for the records
A09 and A12 require it for, and the store as one backup unit under A20.

### Knows

The durable record kinds of M01–M49 and which of them are append-only,
compare-and-set or mutable master state.

### Must not own

Any rule about what may be written. It enforces shape, atomicity and
immutability, not meaning. It holds no business fact and no file except trial
fixtures.

### Hides

The database, its schema and migrations, transaction isolation, locking, and the
mapping between records and rows.

The public boundary is the unit of work, and the unit of work is the typed
record port. `begin_unit_of_work` returns one `OperationalUnitOfWork`: an
interface whose operations are the typed record operations of the closed
durable kinds — load by the complete key, find by a declared unique field, list
by an equality filter in a declared order, insert, update of exactly the named
fields — and nothing else. It accepts no table name, SQL fragment, untyped
payload or host path. Its one local implementation is
`SqliteOperationalStoreRepository`, owned by the `operational_store_persistence`
companion module and lowered from `persistence_backend/v3`
(`implementation_obligations`, disposition `local`). Domain modules and
agent-authored tools depend on the interface and never on the class, so storage
layout, migrations and codecs stay replaceable.

Every read and every write of a durable record goes through a unit. The unit
holds the store's one write transaction, which is how compare-and-set is kept:
the owning function compares the caller's expected value with the record it
loaded inside the unit, and nothing can change that record before commit.
Append-only kinds are immutable because the port offers no update or delete for
them.

### Candidate public capabilities

```text
begin_unit_of_work
commit_unit_of_work
rollback_unit_of_work
open_store
```

### Depth assessment

- kind: deep
- hidden mechanism: transactional durability with append-only and compare-and-set guarantees

## `operational_store_persistence`

### Owns

Only the deterministic SQLite repository class and schema function lowered from
`persistence_backend/v3` for the closed operational-store tables.

### Knows

The versioned persistence IR, typed durable models and configured table names.

### Must not own

Unit-of-work policy, domain authorization, business decisions or any public
kernel capability.

### Hides

SQLite schema creation, row codecs and typed load/upsert statements.

### Candidate public capabilities

```text
SqliteOperationalStoreRepository
create_operational_store_schema
```

### Depth assessment

- kind: deep
- hidden mechanism: version-bound SQLite lowering from persistence_backend/v3

## `access_control`

### Owns

A21 and A27: resolution of every authenticated request to the owner or to
exactly one active delegation; issuing and revoking delegations; the closed
list of owner-only actions and its enforcement; exact durable per-credential
throttling that cannot lock the owner out; the ActorRef attached to every
action.

### Knows

M16, M17, M18, M49, the channel a request arrived on, the credential references
of `installation`, and KernelInstant M47 for throttle deadlines.

### Must not own

Approvals, grants, vocabulary or binding acceptance decisions themselves. It
decides who is asking and whether that kind of actor may ask, not what the
answer is.

### Hides

Credential verification per channel, uniform refusal that reveals no record's
existence, revocation taking effect before the next request, and throttling
state.

### Candidate public capabilities

```text
resolve_actor
authorize_action
issue_delegation
revoke_delegation
establish_owner
```

### Depth assessment

- kind: deep
- hidden mechanism: resolution of a channel identity to one accountable actor

## `semantic_vocabulary`

### Owns

A01: the governed registry of axes, terms and relations with their immutable
revisions; the installation seed; vocabulary proposals and their atomic
acceptance or rejection by the owner; retirement that leaves recorded proofs
intact.

### Knows

M01–M04, M06, M07, M45 and the value families M08–M14 as the shapes terms may
name.

### Must not own

Edge proof, port issuance, or any judgement about whether two ports may be
connected. It answers what exists and at which revision.

### Hides

Revision issuance, duplicate-content detection, the atomic step from accepted
proposal to issued revision, and lookup of a relation by its exact term pair.

### Candidate public capabilities

```text
seed_vocabulary
term_revision
find_relation
submit_proposal
decide_proposal
retire_entry
```

### Depth assessment

- kind: deep
- hidden mechanism: owner-governed revisioned registry of meaning

## `slot_registry`

### Owns

Slots, their immutable contract versions and submitted implementations: issuance
of a contract version only when every port names an accepted term revision, a
known schema and a permitted carriage; idempotent submission of implementation
bytes; retirement of a slot.

### Knows

M05, M19–M23 and injected M48; accepted term revisions through
`semantic_vocabulary`; offered sandbox runtime revisions from the release; and
`identity` for content-derived contract and implementation identities.

### Must not own

Trial, admission, activation, or execution. It never runs, judges or selects an
implementation.

### Hides

Port verification against the vocabulary, clamping of resource bounds to the
release ceilings, storage of code bytes under their digest, and the bounded
slot/contract/implementation view an authoring agent receives. Corpus,
activation and execution evidence remain owned by their modules and are
composed only at `module:kernel_surface`.

### Candidate public capabilities

```text
create_slot
issue_contract_version
submit_implementation
contract_version
implementation_record
retire_slot
slot_authoring_view
```

### Depth assessment

- kind: deep
- hidden mechanism: immutable registration of contracts and code against the vocabulary

## `trial_corpus`

### Owns

A07: the append-only corpus of trial cases per contract version, including
fixture files; validation of a case against the contract's ports; capture of a
concluded node execution as a case; withdrawal with the owner requirement for
protected cases; explicit copying of still-valid cases to a new contract
version.

### Knows

M24, M38 of retention class `trial_corpus`, M41 and M46 as capture sources,
exact contract versions through `slot_registry`, and the injected M48 trial
fixture/text ceilings.

### Must not own

Execution of a case or any verdict about an implementation.

### Hides

Case validation, the rule that decides when a withdrawal needs the owner,
copying a file out of a live run's spool, and corpus reads bounded by the
reader's disclosure ceiling.

### Candidate public capabilities

```text
add_trial_case
capture_trial_case
withdraw_trial_case
copy_cases_to_version
active_corpus
```

### Depth assessment

- kind: deep
- hidden mechanism: a growing regression corpus no author can quietly shorten

## `sandbox_supervisor`

### Owns

A06: every execution of agent-authored code. Creation of the disposable
environment from one runtime revision, delivery of validated inputs and files,
enforcement of bounds from outside, detection and recording of denied attempts,
collection of outputs, confirmed destruction, and refusal of further executions
after an unconfirmed cleanup.

### Knows

M21, M22, injected M48 and the exact M23 implementation record/body fetched
from `slot_registry`; the validated inputs of one execution; and the media
type and size a file port accepts.

### Must not own

What the output means, whether it conforms to the contract's ports, where it
goes next, or any retry. It reports what happened during one execution.

### Hides

The isolation technology, runtime image verification, the absence of network,
clock, entropy and environment, scratch limits, process accounting, the input
and output channel, and cleanup confirmation.

### Candidate public capabilities

```text
execute_function
supervisor_health
```

### Depth assessment

- kind: deep
- hidden mechanism: disposable, externally bounded isolation in which code can compute and do nothing else

## `admission`

### Owns

A08: running one implementation over the whole active corpus and the
deterministic verdict with every applicable refusal reason.

### Knows

M25, M26, exact contract/implementation metadata through `slot_registry`, the
active corpus from `trial_corpus`, and execution through
`sandbox_supervisor`.

### Must not own

Activation, the corpus itself, or any human input. No surface operation reaches
the verdict.

### Hides

Trial orchestration, validation of trial outputs against the contract,
expected-output comparison by digest, detection of an incomplete trial, and
re-evaluation against a corpus that has grown.

### Candidate public capabilities

```text
run_trial
decide_admission
current_admission
```

### Depth assessment

- kind: deep
- hidden mechanism: a verdict that is a pure function of evidence over the whole corpus

## `slot_activation`

### Owns

A09: selection of the implementation that serves a contract version, by
compare-and-set; rollback as a new activation with a reason and a fresh
admission; the derived `known_failing` state; the answer to "what serves this
contract version now".

### Knows

M27, exact contract/implementation metadata through `slot_registry`, the
current admission from `admission`, the exact active corpus from
`trial_corpus`, and slot-scoped concluded execution evidence from
`trace_journal` needed to derive when the serving implementation is known to
fail a captured regression case.

### Must not own

Admission evidence, flow authority, or the pinning of a run. It answers what is
current; `run_executor` pins it.

### Hides

Concurrency of competing activations, staleness detection of an admission,
derivation of `known_failing`, and the refusal to return to an implementation
that fails a newer case.

### Candidate public capabilities

```text
activate_implementation
rollback_activation
serving_activation
contract_health
```

### Depth assessment

- kind: deep
- hidden mechanism: selection by hash where every change and every undo is one appended record

## `manifest_reader`

### Owns

The kernel's read-only projection of the platform manifest at the configured
repository revision: service records, their digests, instances, operations and
each operation's channel, effect class, replay, idempotency key and
preconditions.

### Knows

The manifest record format and the repository revision from `installation`.

### Must not own

Bindings, suspension decisions, invocation or any write to the manifest.

### Hides

Locating and parsing manifest records, computing record digests, comparing the
facts of one operation between two digests, and resolving an instance's address
and required headers.

### Candidate public capabilities

```text
manifest_operation
operation_facts_changed
service_instance
```

### Depth assessment

- kind: deep
- hidden mechanism: a digest-pinned projection of what services declare about themselves

## `operation_bindings`

### Owns

A10: binding proposals, owner-accepted binding versions with effect class and
replay copied from the manifest, the outcome-read and preview requirements of
effectful bindings, automatic reissue on an immaterial manifest change, and
suspension when the manifest operation changed or disappeared.

### Knows

M28, M29, M30, M05; accepted term revisions through
`semantic_vocabulary`; manifest facts from `manifest_reader`; and owner
decisions through `owner_authority`.

### Must not own

Invocation, replay handling, approvals of effects or the manifest itself.

### Hides

Checking a proposal against the manifest, the difference between a material and
an immaterial manifest change, the suspension sweep at start-up and before
invocation, and the plain-words acceptance request.

### Candidate public capabilities

```text
propose_binding
accept_binding_version
binding_for_invocation
sweep_manifest_drift
retire_binding
```

### Depth assessment

- kind: deep
- hidden mechanism: owner-accepted typing of service operations that cannot drift from the manifest

## `flow_proof`

### Owns

A02, A03 and A04: the whole-graph proof of one flow version — node pinning, edge
basis by exact term or exact relation, carriage and media compatibility,
cardinality and mapping, static derivation and checking of disclosure classes,
single supply of inputs, acyclicity, reachability, guards on closed values and
required outputs not behind guards — reporting every finding.

### Knows

M05, M32–M36, the vocabulary through `semantic_vocabulary`, contract versions
through `slot_registry` and binding versions through `operation_bindings`.

### Must not own

The flow registry, activation, execution, or any suggestion of a composition.
It judges a graph; it never edits one.

### Hides

Graph traversal, relation lookup, schema acceptance without coercion,
propagation of disclosure classes through function nodes, and deterministic
ordering of findings.

### Candidate public capabilities

```text
prove_flow
```

### Depth assessment

- kind: deep
- hidden mechanism: a complete, deterministic proof that a graph is well formed and every edge means something

## `flow_registry`

### Owns

A11: flows and their immutable versions, derivation of the highest effect class,
kernel activation of proven read-only versions, owner activation of every other
version, return to an earlier version as a new activation, and retirement.

### Knows

M31, M32, M37, the proof from `flow_proof`, effect classes of pinned binding
versions and owner decisions through `owner_authority`.

### Must not own

Proof, approvals of individual effects, grants or execution.

### Hides

Idempotent registration of a graph by content identity, the rule that no version
inherits anything from another, and the composition view an agent receives
without implementation bodies.

### Candidate public capabilities

```text
create_flow
register_flow_version
activate_flow_version
current_flow_activation
retire_flow
composition_view
```

### Depth assessment

- kind: deep
- hidden mechanism: versioned graphs whose right to run is decided by their highest effect

## `owner_authority`

### Owns

A12 and A13: every decision that is the owner's about an effect. Approval
previews bound to the digest of all inputs, whole-collection approvals of mapped
nodes, single use of an approval, standing grants on one node of one flow
version with the destructive exclusion, revocation, the listing of grants and of
runs waiting for the owner, and the kernel-generated plain-words statements used
for binding acceptance, flow activation, approvals and grants.

### Knows

M42, M43, the binding version's purpose, effect class and preview ports, the
input digests of the node and the file previews from `run_spool`.

### Must not own

Who the owner is, invocation of the effect, or the run's state machine. It
answers whether this exact effect is authorized now.

### Hides

Preview digest computation, invalidation of an approval when an input changes,
grant coverage evaluation including suspended bindings and a suspended owner,
and the separation of generated statements from agent-supplied text.

### Candidate public capabilities

```text
request_approval
decide_approval
authorization_for_effect
grant_standing_approval
revoke_standing_approval
owner_statement
waiting_for_owner
```

### Depth assessment

- kind: deep
- hidden mechanism: binding the owner's decision to the exact effect it was shown

## `service_transport`

### Owns

One request to one service instance on the channel the manifest declares, with
the credential resolved at the moment of sending, bounded in time and size,
following no redirect to another host, streaming a file body from or into the
run spool.

### Knows

Injected M48 transport timeout ceiling, the instance address and headers from
`manifest_reader`, a credential reference from `installation`, and the three
channels `http_api`, `mcp` and `operator`.

### Must not own

Idempotency, replay, retries, outcome interpretation or validation of the
response against ports.

### Hides

Per-channel request construction, authenticated transport, timeouts, response
size limits and the classification of a transport failure as certainly not sent
or possibly sent.

### Candidate public capabilities

```text
send_request
```

### Depth assessment

- kind: deep
- hidden mechanism: one bounded, credentialed exchange with an untrusted service

## `operation_invoker`

### Owns

A14 and A15: invocation of an operation node. The idempotency key, the durable
in-flight record before a non-read call, the replay rules per declared behavior,
validation of the response against the binding's output ports, conclusion as
refused, failed, unreachable or unknown, and reconciliation of an unknown
outcome through the binding's read operation.

### Knows

M30, M41, M44, the run's in-flight attempts, authorization from
`owner_authority`, the binding from `operation_bindings` and transport through
`service_transport`.

### Must not own

The run's scheduling, the decision to ask the owner, or transport details.

### Hides

Key derivation, the ordering of durable record and call, when re-invocation is
permitted, treating an "already exists" refusal as an applied effect, bounded
back-off, and never using a service's free text as evidence.

### Candidate public capabilities

```text
invoke_operation
reconcile_outcome
```

### Depth assessment

- kind: deep
- hidden mechanism: replay-safe invocation that finds out rather than assumes

## `value_store`

### Owns

A20 and the run-time half of A03: content-addressed storage of bounded values,
the size ceiling, retention by class with removal that keeps the description,
retention as the longest any naming record requires, the disclosure class
recorded on each value, and reads that return content or only digest, term and
class according to the reader's ceiling.

### Knows

M38, injected M48, the retention periods of A20, run terminal states and the
disclosure ceiling of the reading actor.

### Must not own

Files in flight, trace records, or any business meaning of a value.

### Hides

Deduplication by digest, reference counting across runs, corpus and approvals,
the expiry sweep that never touches a non-terminal run, and derivation of a
function output's class from the classes it received.

### Candidate public capabilities

```text
put_value
read_value
derive_output_class
expire_values
```

### Depth assessment

- kind: deep
- hidden mechanism: evidence retention that outlives content and never exceeds the reader's ceiling

## `run_spool`

### Owns

M46: files in flight within one run. Receiving a file from a node, computing its
digest, observing its size and media type from the bytes, refusing a file a port
does not accept, delivering it to the next node, showing it to the owner in a
preview, the per-run size bound, and release at the run's terminal state.

### Knows

Injected M48, the media types and size ceiling of a `byte_stream` port, the
run's state, and the leading bytes of a file.

### Must not own

Decoding, rendering, thumbnailing or parsing a file, custody of a file the
business must keep, or trial fixtures.

### Hides

Spool layout on the host, streaming without holding a file in memory, media
type identification from content, deduplication within a run, and guaranteed
removal.

### Candidate public capabilities

```text
receive_file
describe_file
deliver_file
release_run_files
```

### Depth assessment

- kind: deep
- hidden mechanism: identified, bounded, short-lived carriage of files the kernel never interprets

## `trace_journal`

### Owns

A19: the append-only record of every concluded node attempt; the rule that
success is written only after validation; scrubbing of failure detail; identity
of what executed; reads bounded by disclosure ceiling and, for repair, by slot.

### Knows

M41, M18, injected M48 failure-detail ceiling, the identities of
implementations, runtime revisions, binding versions and service instances, and
value digests.

### Must not own

Scheduling, validation itself, stored content or process logs.

### Hides

Append-only enforcement, bounded and class-scrubbed failure text, and the
slot-scoped view that withholds the rest of a run.

### Candidate public capabilities

```text
record_node_execution
run_trace
slot_evidence
```

### Depth assessment

- kind: deep
- hidden mechanism: an unrewritable, secret-free memory of what executed

## `run_executor`

### Owns

A16, A17, A18 and A28: creation of a run with everything pinned and every input
validated; data-driven readiness; validation of a value at the source port and
at the target port; mapping; guards; failure propagation to dependants only;
the run's states and their truthful meaning; exact persisted retry ordinal and
deadline for timed waits; waiting without timeout; durable resumption after
restart; cancellation.

### Knows

M39, M40, M47, the pinned flow version and proof, exact function contract
versions through `slot_registry`, serving activations from `slot_activation`,
bindings from `operation_bindings`, and the conclusions returned by
`sandbox_supervisor` and `operation_invoker`.

### Must not own

Isolation, invocation, approval decisions, storage of values or files, or the
trace's immutability. It decides what runs next and what the run's state is.

### Hides

The readiness computation, concurrency of independent branches, element-wise
execution of mapped nodes, the state machine with its waiting reasons, and
reconstruction of a run's position from durable records alone.

### Candidate public capabilities

```text
create_run
advance_run
resume_runs
cancel_run
run_status
```

### Depth assessment

- kind: deep
- hidden mechanism: durable dataflow execution of one pinned graph to a truthful end

## `kernel_surface`

### Owns

A22: the closed catalogue of named, typed kernel operations and their bounded
request and response schemas, identical in meaning on every channel; refusal of
unknown operations, unknown fields and oversized payloads; treatment of
agent-supplied text as data.

### Knows

The operations of the deep modules it exposes, injected M48 surface/text/page
ceilings and the ActorRef resolved by `access_control`.

### Must not own

Any rule of the modules it delegates to, any transport, or any authoring
convenience that would make the catalogue depend on what has been authored.

### Hides

Nothing of its own. It hides from every channel which deep module answers an
operation, so a channel cannot reach a module's capability that the catalogue
does not name.

### Public surface

```text
inspect
author
request_trial
activate
run_flow
owner_decide
```

### Depth assessment

- kind: facade
- delegates to: `access_control`, `semantic_vocabulary`, `slot_registry`, `trial_corpus`, `admission`, `slot_activation`, `operation_bindings`, `flow_registry`, `flow_proof`, `owner_authority`, `run_executor`, `trace_journal`, `value_store`

## `mcp_gateway`

### Owns

The `mcp` channel: mapping of MCP tool calls onto the operations of
`kernel_surface` and of their results back, for an agent that can author.

### Knows

The MCP protocol and the surface catalogue.

### Must not own

Authentication decisions, schemas of its own, or any operation absent from the
surface catalogue.

### Hides

Nothing of its own beyond the MCP protocol framing.

### Public surface

```text
serve_mcp
```

### Depth assessment

- kind: facade
- delegates to: `kernel_surface`, `access_control`

## `http_gateway`

### Owns

The `http_api` channel: the published schema of the same surface catalogue for a
schema client, the owner's means of access, and delivery of owner previews
including files.

### Knows

HTTP, the surface catalogue and that its published schema never changes when a
function, binding or flow is authored.

### Must not own

Authentication decisions, operations of its own, a browser application, or
static serving of any stored content.

### Hides

Nothing of its own beyond HTTP framing and the published schema document.

### Public surface

```text
serve_http
```

### Depth assessment

- kind: facade
- delegates to: `kernel_surface`, `access_control`

## `bootstrap`

### Owns

Composition of the kernel at start-up: construction of every module with its
collaborators, one read of ReleaseCeilings M48 through `installation` and
injection of that immutable value into every relevant consumer, start-up
validation, the manifest drift sweep, supervisor health, and resumption of
non-terminal runs before the gateways accept requests.

### Knows

Every module's constructor dependencies, M48 injection targets and the start-up
order.

### Must not own

Any rule, decision or state.

### Hides

Nothing of its own beyond construction order.

### Public surface

```text
start_kernel
```

### Depth assessment

- kind: facade
- delegates to: `installation`, `operational_store`, `system_clock`, `operation_bindings`, `sandbox_supervisor`, `run_executor`, `mcp_gateway`, `http_gateway`
