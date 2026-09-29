# State 0 — Cabinet Kernel product boundary

## Status

Accepted by the owner on 2026-09-29. It restarts Cabinet Flow as a
smaller kernel. The design of `examples/cabinet-flow` (State 0 of 2026-09-19 and
States 1–7 grown from it) is frozen as reference: its generated code passed every
gate and linker check while no end-to-end path worked, and three quarters of the
audit findings were decisions nobody had made (Factory
`docs/CABINET_FLOW_SPEC_AUDIT_20260927.md`). Its State 0 was then reviewed against
the two acceptance cases (`docs/CABINET_FLOW_STATE0_REVIEW_20260928.md`), and on
2026-09-29 the owner chose the simplest option on every item. Each decision below
names the D0 decision of 2026-09-19 it keeps, narrows or replaces.

The owner's statement of the product stands:

> We are building a system that manages microservices on the dataflow
> philosophy, where the unit is a pluggable function. We need a kernel in which
> an agent can quickly create tools, check them in sandboxes and apply them to
> the microservices. We cannot build every needed process in advance: today it
> is a photo upload, tomorrow third-party data has to be taken, processed by the
> platform and analysed.

## Product statement

Cabinet Kernel runs flows over the platform's microservices. A flow is a small
proven graph of two kinds of node: a pure function an agent wrote, and a declared
operation of a microservice. The agent writes a function, the kernel tries it in
a sandbox and admits it; the agent composes a flow; the kernel proves the flow,
runs it, asks the owner before any effect, and records what happened.

The stable part of the platform lives in the microservices. The changing part
lives in functions and flows, and changing it needs no new application, module
or redeployment.

## Actors and trust boundaries

- **Owner** — the one human principal. Approves effects, accepts operation
  bindings, activates effectful flows, grants standing approvals, and is the only
  reader of personal data. Reaches the kernel through the agent channel with the owner's token.
- **Agent** — any language-model agent acting for the owner. Reads, authors
  functions and flows, requests trials, runs flows. Holds an agent token
  configured in the installation; the token says whether the agent may author.
- **Personal data** — values of class `personal_data` (K-14) reach an agent
  only as digest and class; the owner alone reads them.
- **Microservices** — known only as records of the platform manifest. The kernel
  calls their declared operations and nothing else; their answers are untrusted
  data until validated at the port.
- **Agent-written code** — untrusted forever; runs only inside the sandbox.
- **Outside senders** (employee, supplier, client) — never reach the kernel.
  Their material stays at a microservice's own intake until the owner or an agent
  submits it; the kernel records only provenance.
- **Secrets** — service credentials and tokens live in the installation's
  protected configuration; they never enter a function, a flow, a trace or an
  answer.
- **Network surface** — one channel, `mcp`, behind the host's reverse proxy.
  Brute-force protection is the proxy's, not the kernel's.

## Primary actions

Each action names its observable output and its failure.

| action | who | output | failure |
|---|---|---|---|
| inspect functions, flows, runs, bindings | owner, agent | typed description; to an agent, personal-data values only as digest and class | unknown reference |
| author a function contract or implementation | agent with author right | new version with its identity | invalid contract or code refused with the reason |
| try an implementation | agent | trial evidence per case | sandbox violation, timeout, contract violation are failures, never success |
| admit and activate | kernel on conforming evidence | activation by hash | empty corpus or any failing case refuses |
| propose an operation binding | agent | proposed binding | manifest mismatch refused |
| accept a binding | owner | accepted binding | — |
| compose and prove a flow | agent | proven flow version or the first failing edge | unproven flow cannot run |
| activate a flow | kernel for read-only flows; owner for effectful ones | active flow version | — |
| run a flow | owner, agent | run with outputs, or resting `awaiting_approval` / `pending` | failed node stops its dependants |
| approve or refuse an effect; grant standing approval | owner | the effect runs on the exact input shown, or does not | — |
| resolve an unknown outcome; resume a pending run | owner (resolve), owner or agent (resume) | run continues | — |
| read a trace | owner, agent | trace records | — |

## Decisions

### K-01 — The product is the kernel (keeps D0-033)

Construction work, invoices, estimates, the portal and the mobile chat are the
first application, not kernel concepts.

### K-02 — Two node kinds; functions are pure (keeps D0-034)

A function node runs one admitted implementation of one contract: declared input
in, declared output out, no network, no filesystem beyond its input, no clock, no
randomness, no secret, no service handle. An operation node invokes one declared
operation of one microservice; only the kernel performs it. An effect is never
hidden in code.

### K-03 — Services through the manifest and owner-accepted bindings (narrows D0-035)

A microservice exists for the kernel only as a platform-manifest record. An
operation binding gives one manifest operation typed input and output ports; an
agent may propose it, only the owner accepts it. A binding pins the manifest
record's digest. When the record's digest no longer matches, invocation is
refused until a new binding is accepted; nothing is reissued automatically.

### K-04 — Contract, implementation, activation (keeps D0-036)

A contract is an immutable versioned declaration of typed ports and resource
bounds. An implementation is immutable code for one contract version, identified
by the digest of its content. An activation binds a contract version to one
admitted implementation; rollback is another activation. A run pins what it uses.

### K-05 — Sandbox, trial, admission (narrows D0-037)

Every function execution, trial and real, runs in a disposable isolated
environment with bounded time, memory, output and processes. Each contract
version has a trial corpus; a failed real execution can be captured into it, so a
repaired slot stays repaired. Admission is a deterministic verdict over the whole
active corpus; an empty corpus refuses. Cases are not copied between contract
versions and not withdrawn.

### K-06 — Edges are proven by schemas (replaces D0-038)

Every port carries a value schema. An edge is valid when the source schema is
accepted by the target schema without coercion. The kernel has no semantic
vocabulary: nobody would maintain it, and the protection it offered against
wiring equal shapes of different meaning is carried where harm can happen — the
owner activates every flow that changes anything and approves each risky effect
on its exact input. A read-only flow wired wrongly yields a wrong analysis and
changes nothing. If agents confuse meanings in practice, meaning labels can be
added later as data.

A file port accepts exactly one media type; a function that can produce two
kinds of file has two ports. A file's media type is therefore its port's.

### K-07 — A flow is versioned data, proven before it runs (keeps D0-039)

A flow is an immutable, acyclic graph with three structural forms: an edge, a map
of a node over a collection, and a guard on a declared closed value. No loops,
code or expressions. The kernel proves it whole before it can run; data moves
only over edges and is validated leaving one node and entering the next.

### K-08 — Authority lives on operation nodes (narrows D0-040)

Effect classes are `read`, `draft-write`, `state-transition`, `external-effect`,
`destructive`. A read-only flow is activated by the kernel once proven; any other
flow only by the owner. At run time each `state-transition`, `external-effect` and
`destructive` node stops for the owner's approval of the exact operation, target
and input, unless the owner granted that exact flow version a standing approval
for that node; `destructive` never takes a grant. The kernel supplies the declared
idempotency key and never repeats an effect without a fresh approval.

When the kernel cannot tell whether an effect happened, the run rests `pending`
with reason `outcome_unknown` and the owner decides: applied, or not applied and
may be sent again. The kernel does not reconcile outcomes on its own.

### K-09 — The trace is data; waiting is truthful (narrows D0-041)

Every node execution writes one immutable trace record: run, node, pinned
versions, input and output by digest, verdicts, status, failure, resources, time.
Nothing is successful by default. A failed node stops only its dependants. A run
rests `awaiting_approval`, or `pending` when a service is unreachable or an
outcome unknown, and ends `succeeded`, `failed`, `refused` or `cancelled`. No wait
ends by itself: a pending run continues only when the owner or an agent resumes
it. Traces carry no secret and no unbounded payload.

### K-10 — The kernel keeps its own records and files for one run (narrows D0-042)

The kernel stores its own records only: contracts, implementations, trial
evidence, activations, bindings, flow versions, approvals and grants, runs and
traces, and bounded values that edges carry. It stores no business fact. A file
moves between nodes through a spool that belongs to its run and is emptied when
the run ends; a file that must last is handed to the service that owns it. A
file's media type is its producing port's single media type (K-06), and an edge
between file ports requires the same type; the kernel does not inspect file
content. Backup and restore of
the kernel's store are an operational procedure outside the kernel.

### K-11 — One fixed surface over MCP (narrows D0-043)

The kernel exposes one fixed set of typed operations over `mcp`: inspect,
author, try, run, read traces, and the owner's approve, accept, activate, grant,
resolve and resume. A new function or flow never changes the surface. The
`http_api` channel for schema clients such as the mobile chat is not part of this
kernel; it is not stubbed.

### K-12 — The agent sees one slot (keeps D0-044)

For repair an agent receives one contract, its current implementation and that
slot's recent traces and trial evidence; for composition, contracts, bindings and
not implementation bodies.

### K-13 — Knowledge lives in the kernel and the platform (keeps D0-045)

A second agent with the same access continues the work from the kernel's
records, the platform manifest and the repositories alone.

### K-14 — Disclosure classes are checked in the proof (narrows D0-047)

Every value carries `open`, `business_confidential` or `personal_data`. A binding
declares the class a service returns and the highest class each input accepts; a
function's output takes the highest class its execution received. The flow proof
refuses an edge that would deliver a value to an input accepting less.

An agent never receives a `personal_data` value: wherever the surface would
return one to an agent, it returns the value's digest and class instead. The
owner receives every value. This is one rule of the surface, not a per-agent
ceiling and not a redaction inside each operation.

### K-15 — One owner, agent tokens (narrows D0-046)

The kernel has exactly one human principal. Agents act for the owner with tokens
configured in the installation, each marked may-author or not; revoking an agent
is removing its token. Tokens are compared in constant time. The owner's actions
and each agent's are distinguishable in every record.

### K-16 — One installation drives one set of instances (keeps D0-048)

An installation selects one manifest instance per service; no flow, run or agent
chooses another. Effectful flows are rehearsed on an installation of disposable
rigs.

### K-17 — One process, one writer, guarantees only where effects leave (new)

The kernel is one process with one store and one writer. A change is one call in
one transaction inside the store module; callers do not open, name or pass
transactions. Idempotency keys, exact replay and outcome handling exist only on
operation nodes, where an effect leaves the kernel; other operations are plain
calls that succeed or refuse. A refusal carries a distinct code only where some
caller acts on the difference; otherwise one refusal with a reason for the trace.

## Explicit exclusions

- No message broker, stream processing, retry scheduler or durable workflow
  engine; a flow run is a bounded graph execution that rests when it must wait.
- No general workflow language: no loops, expressions or scripts in a flow.
- No effectful, stateful or network-capable function.
- No business data store, reporting database or search index.
- No management of microservice deployment, scaling or configuration.
- No agent-to-agent trust.
- No `http_api` channel, no automatic outcome reconciliation, no semantic
  vocabulary, no store-continuity mechanism in this kernel.

## Acceptance

The kernel is accepted when both cases pass against the real service instances
and each refusal of K-05 through K-09 is shown by a bounded negative case:

1. **Photo upload.** A flow takes an original invoice photo into custody through
   the owning service's declared operations; it shows effect classes, the
   owner's approval on the exact input, the idempotency key and `pending`.
2. **Third-party data and analysis.** Within one conversation the agent writes
   the missing functions, tries and admits them, composes a read-only flow over
   declared read operations and returns an analysis, releasing nothing.

## How this case is designed

Every design state asks first who uses what it adds; an obligation without a
user is removed, not refined. Before a module is generated, the generator's own
model lists the choices the specification leaves it; each is closed by pointing
at the text that answers it, by data, or by the owner's decision, and closed
means the question no longer comes back. After generation the code is checked
against the obligations of its notes, not only against gates of form.

## Questions settled on 2026-09-29

1. **Meaning labels (terms).** None in this kernel; edges are proven by schema
   (K-06). The owner accepted the recommendation.
2. **Media type of a function's file output.** A file port has exactly one media
   type (K-06). The owner accepted the recommendation.
3. **Agents and personal data.** An agent receives personal-data values only as
   digest and class (K-14). The owner accepted the recommendation.
4. **Sandbox language.** Functions are written in Python only. The owner's
   answer.

## Open questions

None.
