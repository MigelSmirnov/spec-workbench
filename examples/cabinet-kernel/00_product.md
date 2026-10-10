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
runs it, asks the owner before each effect of the classes K-08 stops for — a
`draft-write` runs under the owner's activation of the flow instead, except that
sending one again after the owner resolved its unknown outcome `not_applied`
needs a fresh approval, as for every class (K-08) — and records what happened.

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
- **Kernel** — acts on its own only where a decision says so (admission and
  activation on conforming evidence, activation of a proven read-only flow); its
  records name it as the actor, so no automatic step looks like a human decision.
- **Agent-written code** — untrusted forever; runs only inside the sandbox.
- **Outside senders** (employee, supplier, client) — never reach the kernel.
  Their material stays at a microservice's own intake until the owner or an agent
  submits it, which is running a flow (`run a flow`) whose operation node takes
  it from that service — there is no separate submission action. Who sent it
  stays in that service's intake record and reaches a flow only as data; the
  kernel records the owner or agent who started the run.
- **Secrets** — service credentials and tokens live in the installation's
  protected configuration; the kernel never puts one into a function, a flow,
  a trace or an answer. A service's own answer body that echoes one verbatim is
  withheld from everyone, the owner included, and never used as an output; one
  that carries it in another encoding, or inside a file the kernel only moves,
  cannot be recognised and is protected by that answer's class (owner,
  2026-10-07). "The owner receives every value" (K-14) is about personal data,
  not about such a withheld body.
- **Network surface** — one inbound channel, `mcp`, behind the host's reverse
  proxy. The proxy terminates TLS and is the only client of the kernel's
  listener, whose address the installation names and which the host does not
  expose otherwise; tokens therefore travel encrypted up to the proxy. Outbound,
  the kernel calls microservices over their HTTP APIs. Brute-force protection is
  the proxy's, not the kernel's.

## Primary actions

Each action names its observable output and its failure.

| action | who | output | failure |
|---|---|---|---|
| inspect functions, flows, runs, bindings, approvals, standing grants and effect attempts | owner, agent | typed description; to an agent, personal-data values only as digest and class | unknown reference |
| author a function contract or implementation | agent with author right | the version with its identity — an existing one when the content is equal; the first contract of a new slot name creates the slot | invalid contract or code refused with the reason |
| add a trial case | agent with author right | the case — an existing one when the content is equal | a case whose values do not fit the contract's ports is refused |
| try an implementation | agent | trial evidence per case | sandbox violation, timeout, contract violation are failures, never success |
| admit and activate | kernel, when an implementation is submitted | admission over the whole corpus and, when admitted, activation at once | empty corpus or any failing case refuses |
| capture a failed execution into the trial corpus | owner, agent with author right | the trial case every later implementation must pass — an existing one when equal | an execution that succeeded, was skipped, belongs to another contract version, or whose run was already released (its files are gone) is refused |
| release a failed run | owner, agent | the run's spooled files are removed | a run that is not `failed`, or already released, is refused |
| roll a slot back | owner, agent with author right | an earlier implementation of the slot's current contract version is activated again; it must already hold an `admitted` verdict over the current corpus — rollback runs no admission | an implementation not admitted over the current corpus is refused |
| propose an operation binding | agent | proposed binding | manifest mismatch refused |
| accept a binding | owner | accepted binding; accepting an accepted binding returns it | an unknown binding, or a proposed one whose manifest entry no longer matches its pin, is refused; an accepted one is returned whatever the manifest says now, since a changed entry stops its sends (State 2, A08 rules 6–7) |
| compose and prove a flow | agent | the flow version and its proof result — proven, or the first failing edge or node (State 2, A05); the version is kept either way, and the first version of a new flow name creates the flow | an unproven version cannot be activated or run |
| activate a flow | agent or owner asks; the kernel activates a proven read-only version at once; any other version only when the owner asks | active flow version | an unproven version is refused; an agent asking to activate a version with effects is refused and nothing is kept for the owner — the owner activates it by the same action |
| run a flow | owner, agent | a run of the flow's active version, with outputs, or resting `awaiting_approval` / `pending` | a flow with no active version, or a function node whose contract version has no current activation, refuses the start and creates no run; a failed node stops its dependants |
| approve or refuse an effect | owner | the effect runs on the exact input shown; a refusal ends the run `refused` | an approval of a run that has ended can no longer be decided |
| grant a standing approval for a node of a flow's active version, or revoke any active grant | owner | the node of that flow version stops asking, or asks again; granting an already granted node returns the active grant | a `destructive` node or a version that is not active cannot be granted; revoking where no grant is active is refused |
| cancel a run | owner | the run ends `cancelled`; nothing further is sent | a finished run cannot be cancelled |
| resolve an unknown outcome | owner | the effect is recorded applied, or not applied; the run continues, and a resend needs a fresh approval | an attempt that is not `unknown`, or whose run has ended, is refused (State 2, A11) |
| resume a run | owner, agent | the nodes waiting on an unreachable service are tried again, whatever else the run waits for | a run with no node waiting on an unreachable service is refused; nodes waiting on an unknown outcome or on approval are not touched |
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
agent may propose it, only the owner accepts it. A binding pins the digest of
its operation's own record in the service's manifest — the operation's entry, not
the whole service file (owner, 2026-09-30). When that digest no longer matches,
invocation is refused until a new binding is accepted; nothing is reissued
automatically.

### K-04 — Contract, implementation, activation (keeps D0-036)

A contract is an immutable versioned declaration of typed ports and resource
bounds. An implementation is immutable code for one contract version, identified
by the digest of the code together with its contract version. An activation binds a contract version to one
admitted implementation; rollback is another activation. A run pins what it uses.

### K-05 — Sandbox, trial, admission (narrows D0-037)

Every function execution, trial and real, runs in a disposable isolated
environment with bounded time, memory, output and processes. Each contract
version has a trial corpus; a failed real execution can be captured into it, so a
repaired slot stays repaired. Admission is a deterministic verdict over the whole
active corpus; an empty corpus refuses. Cases are not copied between contract
versions and not withdrawn.

### K-06 — Edges are proven by schemas (replaces D0-038)

Every port carries a value schema. An edge is valid when both ports carry the
same schema. The kernel has no semantic
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
`destructive`. A proven read-only flow is activated by the kernel as soon as the
owner or an agent asks for it (the action "activate a flow"); any other flow only
by the owner. At run time each `state-transition`, `external-effect` and
`destructive` node stops for the owner's approval of the exact operation, target
and input, unless the owner granted that exact flow version a standing approval
for that node; `destructive` never takes a grant. The kernel supplies the declared
idempotency key and never repeats an effect without a fresh approval.

When the kernel cannot tell whether an effect happened, the run rests `pending`
with reason `outcome_unknown` and only the owner's resolution moves it: applied,
or not applied. An effect resolved as not applied is sent again only with a fresh
approval, even where a standing approval exists. The kernel does not reconcile
outcomes on its own. When the owner refuses an effect, the run ends `refused`.

### K-09 — The trace is data; waiting is truthful (narrows D0-041)

Every node execution writes one immutable trace record: run, node, pinned
versions, input and output by digest, verdicts, status, failure, resources, time.
Nothing is successful by default. A failed node stops only its dependants. A run
rests `awaiting_approval`, or `pending` when a service is unreachable or an
outcome unknown, and ends `succeeded`, `failed`, `refused` or `cancelled`. No wait
ends by itself: a run pending on an unreachable service continues only when the
owner or an agent resumes it; a run pending on an unknown outcome continues only
on the owner's resolution. `refused` means the owner refused an effect;
`cancelled` means the owner cancelled the run. Traces carry no secret and no unbounded payload.

### K-10 — The kernel keeps its own records and files for one run (narrows D0-042)

The kernel stores its own records only: contracts, implementations, trial
evidence, activations, bindings, flow versions, approvals and grants, runs and
traces, and bounded values that edges carry. It stores no business fact. A file
moves between nodes through a spool that belongs to its run and is emptied when
the run ends — except a `failed` run, whose spool stays until the owner or an
agent releases the run, so that its failures can be captured into trial corpora
(K-05); a file that must last is handed to the service that owns it. The only files the
kernel keeps beyond a run are the file fixtures of trial cases. A flow's own
inputs and outputs are values, never files: a file enters a flow from a service
through an operation node and leaves it into a service, so a caller never hands
the kernel a file and never receives one. A
file's media type is its producing port's single media type (K-06), and an edge
between file ports requires the same type; the kernel does not inspect file
content. Values and the records
that name them are kept for as long as the kernel keeps its traces; this kernel
expires nothing. Backup and restore of the kernel's store are an operational
procedure outside the kernel.

### K-11 — One fixed surface over MCP (narrows D0-043)

The kernel exposes one fixed set of typed operations over `mcp`: inspect,
author, try, run, resume, read traces, and the owner's approve, accept, activate,
grant, revoke, resolve and cancel. A new function or flow never changes the surface. The
kernel offers no HTTP surface of its own for schema clients such as the mobile
chat; it is not stubbed. Invoking a microservice over that service's own HTTP API
(K-03) is a different thing and is how operation nodes work.

### K-12 — The agent sees one slot (keeps D0-044)

For repair an agent receives one contract, its current implementation and that
slot's recent traces and trial evidence; for composition, contracts, bindings and
not implementation bodies.

### K-13 — Knowledge lives in the kernel and the platform (keeps D0-045)

A second agent with the same access continues the work from the kernel's
records, the platform manifest and the repositories alone. "The repositories"
are the platform's git repositories the platform manifest names (the manifest's
own and each service's); the kernel keeps every implementation's code in its
own records and depends on no repository to run, admit or roll back. Which
repositories exist and who may read them is the platform's, not the kernel's.

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
is removing its token, and it takes effect at the agent's next request: the kernel
reads the token list again whenever it has changed. Tokens are compared in
constant time. The owner's actions,
each agent's and the kernel's own are distinguishable in every record.

### K-16 — One installation drives one set of instances (keeps D0-048)

An installation selects one manifest instance per service; no flow, run or agent
chooses another. Effectful flows are rehearsed on an installation of disposable
rigs: the owner runs a second kernel installation whose services select their
`disposable_rig` instances, and runs the flow there as anywhere else. The
rehearsal is the owner's practice, not a kernel step — no kernel requires,
records or checks one, and activating a flow does not depend on it.

State 2 reads "one" as "at most one": an installation may leave a service
without an instance; that service is not invocable, and no binding for it can be
proposed or accepted (A17 rule 4, A08 rules 5 and 7).

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
- No authority over how an agent reaches a microservice directly. An agent's own
  access to a service — as for processing a photo (decision 17) — is granted by
  that service and the owner outside the kernel; the kernel neither gives nor
  checks it, and its personal-data promise (K-14) covers what the kernel itself
  returns.
- No HTTP surface of the kernel's own, no automatic outcome reconciliation, no
  semantic vocabulary, no store-continuity mechanism and no value expiry in this
  kernel.

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

5. **Value retention.** Kept as long as traces; nothing expires in this kernel
   (K-10). The owner accepted the recommendation.
6. **Missing actions.** Cancel a run and revoke a standing approval are owner
   actions; a binding proposal that is not accepted simply stays proposed. The
   owner accepted the recommendation.
7. **A refused effect** ends the run `refused` (K-08). The owner accepted the
   recommendation.
8. **Resend after an unknown outcome** needs a fresh approval even under a
   standing approval (K-08). The owner accepted the recommendation.
9. **File fixtures of trial cases** are the only files the kernel keeps beyond a
   run (K-10). The owner accepted the recommendation.

10. **Actor of automatic steps.** Records name the kernel as the actor of what
    it does on its own (K-15). The owner accepted the recommendation.
11. **Rollback of a slot** is an action of the owner or an agent with the author
    right: activate an earlier implementation admitted over the current corpus
    (K-04). The owner accepted the recommendation.
12. **Revoking an agent token** takes effect at the agent's next request (K-15).
    The owner accepted the recommendation.
13. **Provenance of outside material** stays in the receiving service's intake
    record; the kernel records only who submitted it to a flow. The owner accepted
    the recommendation.
14. **An approval whose effect was never sent** (the service was unreachable)
    stays valid on resume for the same input; it is used only when the effect is
    sent. The owner accepted the recommendation.
15. **Spool of a failed run** stays until the owner or an agent releases the run,
    so failures with file inputs can be captured (K-10). The owner's choice.
16. **What a binding pins** (2026-09-30, raised by the State 2 question rounds):
    the digest of its operation's own record in the manifest, so an edit to
    another operation of the same service stops nothing (K-03). The owner accepted
    the recommendation.
17. **Libraries in the sandbox** (2026-09-30): the Python standard library only.
    Photo processing is not a kernel function: the agent processes a photo itself,
    outside the kernel, with its own access to the service that holds the photo —
    never through the kernel, which hands no caller a file — and the kernel moves
    the file between services. The
    owner's answer.
18. **What an approval covers** (2026-10-01, raised by State 2 round 17): the
    fully built request as the owner was shown it — method, URL, headers and
    body. Any difference at send, whatever caused it (the inputs, or an
    instance's address or headers changed by a restart), asks again. The
    credential's value is never shown, so rotating it voids nothing. The owner
    accepted the recommendation. A difference voids the approval, not a
    standing grant: where the owner's active grant covers the node, the send
    goes under the grant without asking (A10 rule 1; owner, 2026-10-03, raised
    by State 2 round 30).
    For a `multipart/form-data` body, the boundary between its parts and the
    `content-length` it changes are the kernel's framing, not a difference:
    the parts themselves — name, filename, media type and content — are what
    the owner was shown and what must not differ (A10 rule 7; owner,
    2026-10-06, raised by State 2 round 80).

## Open questions

None.
