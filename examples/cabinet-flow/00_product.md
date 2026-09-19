# State 0 — Cabinet Flow product boundary

## Status

Accepted on 2026-09-19. The owner states product behavior and business logic;
the technical shape is decided by the designing agent and recorded here with its
reason. On that basis the owner confirmed the behavior of this document in plain
terms: the agent reads and computes on its own, every change of data waits for
the owner's approval, routine changes may receive a standing approval, work
waits truthfully when a service is unreachable, and there is one trusted
entrance (D0-046).

This text replaces the State 0 of 2026-09-06 and its correction of 2026-09-15,
kept unchanged in `archive/00_product_20260915_superseded.md`. That document
described three things at once — a kernel, a construction application and an
agent environment — and after the correction it held two incompatible execution
architectures. The owner restated the product on 2026-09-19:

> We are building a system that manages microservices on the dataflow
> philosophy, where the unit is a pluggable function. We need a kernel in which
> an agent can quickly create tools, check them in sandboxes and apply them to
> the microservices. We cannot build every needed process in advance: today it
> is a photo upload, tomorrow third-party data has to be taken, processed by the
> platform and analysed.

The owner also fixed the method: no reduced first version. A deferred part
becomes a stub, and a stub costs tens of Factory runs. Every part named here is
designed to closure before generation.

Models, modules, storage layout, Python contracts, transport DTOs and algorithms
belong to their owning states. Every product decision belongs here.

## Product statement

Cabinet Flow is a dataflow kernel that manages a platform of microservices.

Its unit of behavior is a pluggable function: a small, pure, versioned
implementation of a declared contract. An agent authors such functions, the
kernel proves them in a sandbox, admits them, and composes them with the
declared operations of the platform's microservices into flows. The kernel
executes flows, validates data on every edge, applies effects only through the
microservices' own declared operations, and records an immutable trace.

The product exists because the platform's processes cannot be enumerated in
advance. The stable part of the platform lives in the microservices. The
changing part lives in functions and flows, and changing it must not require a
new application, a new module or a redeployment of any microservice.

Cabinet Flow manages behavior, not code. To change what the platform does, a
function implementation is replaced by hash or a flow version is replaced; the
rest of the system is not read, edited or restarted.

## Origin

The design continues `AI-Native Protocol v1` (2026-04-03,
`jestor_VBC/data/protocol_v1`) and its sketch implementation in the same
repository: a slot is a contract and a hash is an implementation; the agent
reads one slot, not the system; output is validated between nodes; a trace is
data, not a log; replacement is by hash; only a human changes the orchestrator.

The sketch also shows what failed. Every rule it kept only by convention was not
kept: each function received the whole context including secrets, the hash was
copied from a file rather than derived from the code, imports were unchecked,
startup validation only warned, a proposal was never an activation, and the
graph was the orchestrator's code. Cabinet Flow therefore makes each of those
rules structural: the forbidden thing is impossible, not prohibited.

## Decisions

### D0-033 — The product is the kernel

Cabinet Flow is the kernel described here and nothing else. Construction work,
invoices, estimates, the portal and the mobile chat are the first application of
the kernel, recorded in the last section. No construction concept is a kernel
concept.

### D0-034 — Two node kinds, and functions are always pure

A flow has exactly two kinds of node.

A **function node** runs one admitted implementation of one slot contract. A
function is pure: it receives its declared input and returns its declared
output. It has no network, no filesystem beyond its input, no clock, no randomness source, no secret and no handle to any
service. It cannot perform or request an effect.

An **operation node** invokes one declared operation of one microservice. The
kernel performs the invocation. Reading from a service, writing to a service and
calling an external provider such as a language model are all operation nodes.

Consequently an effect is never hidden inside code. It is always a visible node
of the flow whose input arrived over a validated edge, and everything an agent
writes is a pure transformation. This replaces the "effect intent" of the
superseded text: a function does not describe an effect, it produces the data
that an operation node consumes.

### D0-035 — Microservices are known only through the platform manifest

A microservice exists for the kernel only as a record of the platform manifest
(`platform/manifest/` of the Factory): its instances, its operations, and for
every operation the channel, the effect class, the idempotency key, the replay
behavior and the preconditions. The kernel reaches a service by no other path
and invokes no undeclared operation.

The kernel is itself one service of that manifest. It owns no operation of
another service and never writes to another service's store.

The manifest does not type an operation's data. An **operation binding** is the
kernel's immutable, versioned declaration that gives one exact manifest
operation its typed input and output ports under D0-038. An agent may propose a
binding; only the human owner accepts one, because a wrong binding aims an
effect at the wrong data. An operation without an accepted binding is invocable
by nobody, and a binding whose manifest operation has changed or disappeared is
refused rather than guessed.

### D0-036 — Slot, implementation, activation

A **slot contract** is an immutable, versioned declaration: typed input ports,
typed output ports and resource bounds. A function has no configuration: a
constant it needs, such as a tax rate, is a typed literal pinned in the flow
version and delivered over an edge like any other input. A change of a contract
is another contract version. A flow pins contract versions, so an existing flow
never changes meaning under a new version.

An **implementation** is immutable code realizing one contract version. Its
identity is the digest of its content, computed by the kernel. No identity is
assigned, copied or declared by the author.

An **activation** binds one contract version to one admitted implementation.
Earlier implementations are never deleted; rollback is another activation. A
flow run pins the exact implementation it used.

The agent may create new slot contracts and new implementations. It cannot
alter an issued contract version or an admitted implementation.

### D0-037 — Every function execution is sandboxed, trial and real alike

Agent-authored code is untrusted forever. Each execution of a function node —
during trial and during a real flow run — happens in a disposable isolated
environment that contains only the declared input and one exact accepted
language runtime. It has bounded time, memory, output size and process count,
and it ends with the destruction of the environment and every
descendant process.

Any attempt to reach what is not declared, a timeout, resource exhaustion, a
failed cleanup or an output that violates the contract is an observable failure
and never a success.

**Trial** executes one exact implementation against trial inputs that carry the
contract's port types. Trial evidence records the implementation identity, the
input and output digests, the validation verdicts, every denied attempt and the
resources used.

Each contract version has a trial corpus that only grows. A real execution that
failed can be captured into it, so a slot that was repaired stays repaired: every
later implementation must pass every active case.

**Admission** is a deterministic verdict over trial evidence for the whole
active corpus. An empty corpus refuses. Because a function
is pure by construction, admission needs no human: conforming evidence admits
the implementation, anything else refuses it with the reason. Human authority is
spent where effects are, in D0-040.

### D0-038 — Edges are proven by a governed semantic vocabulary

Every port carries a value schema and an exact semantic term. An edge from an
output port to an input port is valid only when both carry the same accepted
term revision with a compatible shape, or when one accepted semantic relation
connects the two terms. Equal primitive types, similar field names and an
agent's judgement are not evidence.

The vocabulary — axes, terms and relations — is governed by the human owner. An
agent may propose an addition; a proposal is not composable until accepted.

An output without an accepted term is valid and may be returned to the caller,
and cannot feed another node.

### D0-039 — A flow is versioned data, proven before it runs

A flow is an immutable, versioned, acyclic graph of function nodes and operation
nodes with typed edges. It has three structural forms and no others: an edge, a
map of one node over a collection-valued edge, and a guard that enables an edge
on a declared closed value of an output port. It has no loops, no embedded code
and no expressions.

An agent composes a flow. The kernel proves it before it can run: every edge
satisfies D0-038, every node pins an existing contract or operation version,
the graph is acyclic, and every required input is supplied. An unproven flow
does not run partially.

Nodes never call each other. Data moves only over edges, and a value is
validated against the source contract before it leaves a node and against the
target contract before it enters one. Input is validated as strictly as output.

### D0-040 — Authority lives on operation nodes

Every manifest operation has an effect class: `read`, `draft-write`,
`state-transition`, `external-effect` or `destructive`.

A flow whose operation nodes are all `read` is activated by the kernel once
proven, and any authorized agent may run it.

A flow containing any other class is activated only by the human owner, who
approves that exact flow version. At run time each `state-transition`,
`external-effect` and `destructive` node stops for the owner's approval of a
preview showing the exact operation, target and input, unless the owner has
granted that exact flow version a standing approval for that node. A grant
never transfers to another flow version, and a `destructive` node can never be
granted: it always asks. The kernel performs the effect only on the exact input
the owner saw.

The kernel honours the declared replay behavior. It supplies the declared
idempotency key, and it never re-invokes an operation declared `duplicates`
within one run or on recovery without a fresh approval. An outcome it cannot
determine is recorded as unknown and reconciled through the service's declared
read operations, never assumed.

An agent cannot approve its own flow, extend its own authority, or act under
another actor's identity. Human and agent identities stay distinguishable in
every record.

### D0-041 — The trace is immutable data

Every node execution produces one immutable trace record: the run, the node, the
pinned contract, implementation or operation version, input and output by
digest and bounded reference, validation verdicts, status, failure, resources
and time. A status is never successful by default; it becomes successful only
after output validation.

A run pins every version it used and is reproducible from its trace for its
function nodes. A failed node stops its dependants; independent branches finish.
A run rests in `awaiting_approval`, or in `pending` when a required service
instance is unreachable or an effect's outcome is undetermined, and ends
`succeeded`, `failed`, `refused` or, by the owner's decision, `cancelled`.
Nothing is reported complete that did not complete, and no wait ends by
timeout.

Traces carry no secret and no unbounded payload.

### D0-042 — The kernel owns an operational store and no business fact

The kernel durably stores its own records only: the vocabulary, slot contracts,
implementations, trial evidence, admissions, activations, flow versions,
approvals and grants, runs and traces, and the bounded content-addressed values
that edges carry between nodes under a retention policy.

It stores no business fact. Every business fact lives in the microservice that
owns its lifecycle, and the kernel holds at most a digest and a reference. This
narrows D0-031 of the superseded correction, which denied the environment any
store.

### D0-043 — Any agent, a fixed kernel surface

The kernel is indifferent to the agent's provider (D0-028 stands). It exposes
one fixed set of named, typed operations over two channels: `mcp` for an agent
that can author, and `http_api` for a schema client such as the mobile chat.

The surface is fixed and generic: inspect the vocabulary, slots, flows and runs;
author a contract, an implementation or a flow; request trial; run a flow;
read a trace; and, for the owner, approve and grant. A new function or flow
therefore never changes the surface, and a schema client can run a flow authored
a minute earlier without a schema release. This is what removes the limit that
produced the correction of 2026-09-15.

The surface is not a database proxy, a filesystem, a shell or a code-execution
endpoint outside the sandbox.

### D0-044 — The agent sees one slot

For authoring or repair the agent receives one slot contract, its current
implementation, and the recent traces and trial evidence of that slot. For
composition it receives contracts, operation declarations and the vocabulary,
not implementation bodies. It never receives the kernel's store, another
actor's data or a service credential.

The evolution loop is the protocol's, closed by the kernel:

```text
failure or gap → trace → agent reads one slot → new implementation
→ trial in sandbox → admission → activation by new hash → flow runs
```

The agent cannot replace, disable or route around trial, admission, proof, edge
validation, approval or trace capture.

### D0-045 — Knowledge lives in the kernel and the platform, not in an agent

D0-032 stands. A second agent with the same access must be able to continue the
work from the kernel's records, the platform manifest and the repositories
alone.

### D0-047 — A value's disclosure class follows it

Every value carries one of three disclosure classes: `open`,
`business_confidential` or `personal_data`. An operation binding declares the
class of what a service returns and the highest class each of its inputs
accepts. A function cannot lower a class: the kernel gives a function's output
the highest class among what that execution received. The flow proof refuses an
edge that would deliver a value to an input accepting less, so personal data of
a client cannot reach an external provider through any chain of functions
unless the owner accepted a binding that says it may.

An agent delegation has a disclosure ceiling, and the surface returns to an
agent no value above it.

### D0-048 — One installation drives one set of instances

A kernel installation selects one manifest instance per service. No flow, run or
agent can choose another. An effectful flow is rehearsed on an installation
whose instances are disposable rigs, never through a switch inside the
installation that drives production.

### D0-046 — One trusted entrance

The kernel has exactly one human principal, the owner. Every agent acts under
the owner's delegation, and every approval and grant is the owner's. The kernel
has no second user, no roles and no invitation mechanism.

Material from anyone else — an employee sending a photo from a site, a supplier,
a client — never reaches the kernel as that person's action. It arrives at a
microservice's own intake, stays there as unaccepted material, and enters a flow
only when the owner, or an agent under the owner's delegation, submits it. The
kernel records the owner as the actor and the outside sender only as provenance
of the data.

Opening the kernel to another principal is a change of this State 0, not a
configuration.

## Superseded

- D0-030's statement that managed function authoring "loses its sandbox" is
  withdrawn. Its graduation ladder remains true for platform tools outside the
  kernel and is not a kernel mechanism.
- D0-031's "no environment store" is narrowed by D0-042. Its Box remains the
  transfer unit between microservices and is outside the kernel.
- "Effect intent", "Capability Box", "CapabilityInvocation", "HandoffPackage",
  "MCP ownership", the three access planes, Syncthing ingress and the bridge to
  the local Backend are not kernel concepts. Where they still hold they are
  facts of the first application or of a microservice.
- D0-028, D0-029 and D0-032 stand and are restated by D0-043 and D0-045.

## Explicit exclusions

- No message broker and no stream processing; a flow run is a bounded graph
  execution.
- No general workflow language: no loops, expressions or scripts inside a flow.
- No effectful, stateful or network-capable function.
- No business data store, reporting database or search index in the kernel.
- No management of the microservices' deployment, scaling or configuration; the
  kernel invokes their declared operations and nothing else.
- No agent-to-agent trust: one agent's assertion never replaces a proof, an
  admission or an owner approval.

## First application — Cabinet

The platform's current services are the VPS journal, the `cabinet-web-backend`
plugin, the local Cabinet Backend, PresuPro and the client portal, each already
recorded in the platform manifest. Two cases qualify the kernel, and both are
required:

1. **Photo upload.** A flow of operation nodes and function nodes takes an
   original invoice photo into custody through the owning service's declared
   operations. It qualifies effect classes, approval, replay and the `pending`
   state.
2. **Third-party data and analysis.** The agent meets a need no function covers,
   authors the missing functions, proves and admits them, composes a read-only
   flow over declared read operations and returns an analysis, within one
   conversation and without a release of anything. It qualifies authoring,
   sandbox, admission, activation, proof and the fixed surface.

The kernel is accepted as working only when both cases pass against the real
service instances, and when each refusal named in D0-037 through D0-041 is shown
by a bounded negative case.

## Consequences for the existing State 1

Models M01–M15 (semantic registry and value families) remain and serve D0-038.
Their references to Cards, HandoffPackages and the Cabinet Flow source registry
are first-application vocabulary and are revised when State 1 is completed.

`STATE0_ACCEPTANCE_CHECKLIST.md` was derived from the superseded text. Its
sandbox, versioning, flow-execution and agent-context sections carry over; its
ingress, handoff and access-plane sections belong to the first application. It
is re-derived from this document once the owner accepts it.
