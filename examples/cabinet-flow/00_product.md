# State 0 — Cabinet Flow product boundary

## Status

Accepted and corrected on 2026-09-06 after product-design discussion and
closure decisions D0-001 through D0-021.

The correction separates Cabinet Flow's product purpose from its managed
self-extension mechanism. Issue
[MigelSmirnov/spec-workbench#35](https://github.com/MigelSmirnov/spec-workbench/issues/35)
is design input and evidence, not a substitute for this canonical artifact.

Models, modules, storage tables, Python contracts, transport DTOs and
implementation algorithms are intentionally deferred to their owning states.

## Product statement

Cabinet Flow is a conversational operating environment for construction work.

Its primary purpose is to help the human owner bring order to fragmented
incoming work: text, invoice photos, project facts, supplier and contractor
information, estimates, plans, payments, local-system results and other
construction evidence.

Through a conversation with an authorized online agent, the user can provide
unstructured information or ask for an operational result. The agent identifies
the relevant Cabinet context, uses bounded capabilities, composes them through
validated data flows, presents uncertainty and protected effects for review,
and records accepted structured results with their provenance.

Cabinet Flow is not primarily a pipeline for creating functions. Managed
function authoring is the way the operating environment can acquire a missing
ability without turning into unrestricted agent-written application code.

Cabinet Flow is a successor architecture for the current `Cabinet_web`
application. It is a new implementation, not an in-place rewrite and not a new
name for either existing backend component.

## Architectural motivation

Construction operations combine a relatively stable set of identities,
evidence and protected effects with a continually changing set of small working
tasks.

A user may need to compare estimate fields today, associate invoices with
suppliers tomorrow, then check source-line completeness, prepare material data
for a work stage, reconcile planned and actual costs or assemble a Capability
Box for a local estimator.

Implementing every such need as a new conventional application module imposes
a disproportionate cost. The small piece of business logic also requires new
integration structure, dependency wiring, testing context, deployment and
coordination with the rest of the application. Repeating that process makes
Cabinet slow to adapt to ordinary operational change.

Cabinet Flow therefore separates two kinds of behavior.

Stable and security-critical behavior remains in the trusted deterministic
system boundary. This includes durable identity, provenance, storage and
transaction integrity, authorization, source custody, capability registration,
version selection, sandbox isolation, boundary validation, protected-effect
application and execution evidence.

Changeable operational behavior may be represented by small versioned
capabilities with explicit contracts. Examples include comparing accepted
estimate fields, matching an Invoice to a supplier candidate, checking data
completeness, deriving a bounded analysis, preparing planning input or
assembling a Capability Box.

A declarative data flow composes these capabilities without giving one
implementation access to another implementation's internals. The flow makes
ordering, validated data boundaries, selected versions, failures and results
observable.

The architecture is intended to reduce the cost and risk of changing
operational behavior, not merely to make code generation easier. Agent-assisted
authoring is useful because the required operations change; it remains
controlled because generated behavior is untrusted.

The agent must first discover and compose existing accepted capabilities. A new
capability is justified only when the requested operational result exposes a
real bounded behavior gap. A new wording, one-off data value or trivial private
helper is not by itself a new capability.

This separation preserves deep deterministic ownership for stable rules while
allowing small operational transformations to be tested, versioned, activated,
reused, replaced and rolled back independently.

## Construction operations in scope

Cabinet Flow supports the everyday operational work of a small construction
business. Its principal work areas are:

### Suppliers and contractors

- preserve and find supplier Cards;
- preserve and find contractor or performer Cards;
- organize identities, contact information, offered work or materials, service
  area and relevant operational history;
- connect incoming invoices, estimates, purchases, work and project evidence to
  the correct party without treating a name string as durable identity.

### Projects and construction objects

- preserve Cards for projects and physical work objects;
- gather project context that is otherwise scattered across messages,
  documents, invoices, plans and local applications;
- associate operational facts with the correct project or object;
- expose a coherent current view without erasing provenance or unresolved
  conflicts.

### Invoices and source evidence

- accept invoice facts from user text and recognized photos;
- preserve original-source identity separately from extracted facts;
- create and revise structured Invoice information;
- preserve commercial line identity rather than replacing source lines with a
  synthetic aggregate;
- track project/object association, supplier, totals, payments, status,
  provenance and source custody truthfully;
- distinguish a structured result from custody of the original bytes and from
  local archival acceptance.

### Operational analysis

- answer questions across accepted Cabinet data;
- detect missing, inconsistent, duplicated or unassigned information;
- calculate and compare operational totals where the required facts exist;
- surface uncertainty, stale information and provenance rather than silently
  inventing values;
- produce reviewable analysis that can become input to a later flow without
  becoming an untraceable mutation.

### Work-stage planning

- help plan construction stages from current project facts;
- connect planned stages with work, materials, contractors, invoices, estimates
  and dependencies;
- revise plans as new evidence arrives while preserving accepted identity and
  history;
- distinguish an analytical proposal from an authorized persistent change.

### Local estimates

- prepare bounded, structured inputs for the local estimating workflow;
- transfer the exact source-derived and project-related facts required by the
  estimator;
- receive local estimate results and acknowledgements without making Cabinet
  Flow the owner of local estimator internals;
- keep server-side preparation, transport delivery and local durable acceptance
  as separate observable facts.

### Capability Boxes

A Capability Box is a self-described, bounded semantic and trust surface through
which an agent or application publishes work that another authorized participant
may invoke.

A Box declares the schemas and stable semantic identities it understands, the
capabilities it offers, and the authority, disclosure, effect, audit and
provenance rules at its boundary. The host enforces those declarations; a Box
does not grant arbitrary filesystem, database, network or operation access.

The Box itself is not the payload transferred between Cabinet Flow and a local
agent or application. A particular exchange is a capability invocation or
handoff package addressed to a capability published by a Box. It carries the
bounded input, stable identities, exact contract or schema references,
provenance and correlation state required for that exchange.

Cabinet Flow inherits the durable semantic principles demonstrated by
`experiments/cabinet-vault` and `cabinet_box_language.v0`:

- composition is based on declared semantic identity, exact compatible types
  and required authority, not on similar field names;
- derivable projections and plumbing may be generated deterministically;
- unresolved composition fails closed without model or generated-code fallback;
- the agent may choose a composition, but trusted behavior proves, lowers and
  enforces it.

The current Cabinet Vault language remains exploratory evidence and a
compatibility baseline, not an automatically normative wire syntax for Cabinet
Flow. State 1 must decide what is adopted unchanged, versioned or replaced while
preserving these semantic and security properties.

The exact Box definition, invocation and handoff models and delivery protocol
belong to later design states.

## Primary user outcome

The normal user does not need to design a flow or request a new function.

The human owner brings an operational question or incoming evidence to the
conversation. Within delegated authority, the online agent:

1. determines the user's operational intent;
2. identifies the minimum relevant Cabinet facts and source identities;
3. selects existing accepted capabilities;
4. composes or selects a versioned flow when more than one operation is needed;
5. validates data at every capability boundary;
6. returns a useful structured result, analysis, plan, Card proposal or a
   reviewable handoff addressed to a capability published by a Box;
7. shows uncertainty, failures and protected effect previews explicitly;
8. applies persistent or external effects only with the required authority;
9. records enough provenance and execution evidence for the result to be
   understood and revised.

The primary product value is an agent that turns incoming construction chaos
into coherent, traceable operational state and advances real work.

## Managed capability evolution

When existing accepted capabilities cannot produce the requested operational
outcome, the agent may enter a distinct managed capability-evolution mode.

In this mode the authorized agent can:

- describe the missing bounded behavior;
- author a small implementation and declare typed input, output, context, data
  access and effects;
- register an immutable draft implementation against a stable versioned
  behavioral contract;
- execute and inspect the exact version in a sandbox;
- receive explicit admission and effect-policy outcomes;
- activate an accepted version;
- compose it into a versioned declarative flow;
- observe selected versions, validation, trace, failures, effect intents and
  results;
- revise, deactivate or roll back the capability without erasing earlier
  accepted versions.

Capability evolution serves the construction operation. It is not the default
answer to every user request, and absence of a capability is reported
explicitly rather than hidden behind improvised unregistered code.

### Baseline capabilities

The first release does not bootstrap itself by asking the online agent to author
all capabilities at first startup.

A minimum baseline is supplied by the implementation and explicit migration of
accepted legacy behavior. Each baseline capability is reviewed and accepted by
the human owner or release process and records its provider and provenance.
Trusted built-in behavior may publish a capability without pretending to be an
agent-authored slot implementation; that distinction remains visible.

The operational proof uses this accepted baseline. The separate
capability-evolution proof demonstrates how the agent adds a new capability
after a real bounded behavior gap is found.

## Existing-system context

Three existing systems remain distinct:

1. `Cabinet_web` is the current upper GitHub-backed Cabinet application and
   remains working evidence and a temporary legacy provider while behavior is
   migrated capability by capability.
2. `cabinet-web-backend` is the existing VPS/server component. It remains a
   narrow compatibility and transport bridge rather than becoming the product
   owner of Cabinet Flow.
3. `Cabinet Backend` is the independent local archival application. It opens
   bounded synchronization sessions and remains authoritative for local
   archival acceptance and local effects.

The AI Code Factory and its DSL remain compile-time infrastructure. Their
`models`, rules, contracts and notes retain compiler meaning. Runtime
functions, execution context, flows, Boxes and managed capabilities belong to
Cabinet Flow unless a later explicit product decision changes that boundary.

## Authority

The first release has one human owner.

Online, server-side and local agents act only through delegated authority. They
may organize information, propose decisions, author operations, execute
permitted flows and return evidence, but they cannot:

- expand their own permissions;
- grant themselves additional data or effects;
- approve their own protected effects;
- replace a required human decision with another agent's assertion;
- use another actor's credential or grant.

Registration, activation and invocation authority are separate. Activating a
version does not authorize every protected effect during invocation.

Human and machine identities remain distinguishable in execution and effect
evidence.

## Managed activation

Every agent-authored implementation is initially a managed draft.

Automatic activation is permitted only when sandbox evidence proves bounded
computation with schema-conforming input and output and no persistent mutation,
external communication, local-machine action, secret access, system command,
privilege expansion or undeclared effect.

Any uncertainty or protected effect requires explicit human approval.

Activation applies to one immutable implementation version and one
slot-contract version. Changed code creates a new draft. Expanded data access,
effects, dependencies, scope or resource requirements cannot inherit the old
version's authority.

The author's declaration is evidence but is not sufficient proof by itself.

## Slot, implementation, capability and flow boundary

The following terms are distinct.

A **slot contract** is a stable, named and versioned contract for replaceable
behavior. It declares typed input and output schemas, minimum context, effects,
data-access requirements, relevant resource expectations and the validation
boundary visible to composition.

An **implementation version** is one immutable artifact that realizes one slot
contract version. It is identified by the digest of its accepted artifact.
Changing its content creates a new version; changing the contract requires
explicit compatibility or migration handling.

A **capability** is the registered, invocable product operation visible to an
agent or flow. A capability may bind a slot contract to one admitted
implementation version, or it may be published by trusted built-in behavior
whose provider and provenance are explicit. Registration and activation decide
what implementation may provide it; invocation authority separately decides
whether a particular actor may call it with particular data and effects.

A **flow** is a versioned declarative graph of capability invocations. It owns
composition and pins the exact capability bindings, contracts and
implementation versions required for reproducible execution.

The resulting relationship is:

```text
slot contract
→ immutable implementation version
→ admitted capability binding
→ capability invocation in a flow
```

Not every helper function is a slot, and not every capability needs an
agent-authored implementation. Behavior becomes a slot only when it is
meaningful to observe, validate, replace, test and evolve independently.

Implementations do not directly call neighboring implementations. Trusted
behavior validates structural and declared semantic constraints before one
capability invocation's output can become another's input.

A run pins the exact flow, capability binding, contract and implementation
versions. Missing, invalid or semantically unacceptable output is an explicit
failure and is not forwarded as successful data.

Execution data and execution evidence are distinct. Traces record identities,
versions, order, statuses, validation, safe references or digests and effect
intents; they do not copy secrets, unrestricted facts or source bytes merely
for observability.

State 1 must model at least the distinct concepts of slot contract,
implementation version, capability, capability binding, flow and flow node, Box
definition, and capability invocation or handoff package.

## Agent context

Context is bounded by task and operating mode.

For ordinary construction work, the agent receives the user's request, the
public descriptions of relevant accepted capabilities and only the authorized
Cabinet facts and sources required for that task. It does not receive every
implementation body or the whole Cabinet dataset by default.

For capability authoring or revision, the normal context contains the selected
contract, the relevant current implementation, relevant validation failures and
execution evidence, and the explicitly available implementation environment.

For flow composition, the agent may receive the versioned graph and public slot
contracts without receiving every implementation body.

For execution, a slot receives only the minimum authorized immutable input
snapshot and opaque bounded capabilities declared by its contract.

The agent cannot replace, disable or route around trusted scheduling, context
selection, version pinning, validation, isolation, effect evaluation or
evidence capture.

## Non-bypassable execution boundary

All agent-authored code remains untrusted in sandbox and real execution.

Every execution is enclosed by a mandatory trusted boundary. Agent-authored
code never receives:

- a production database connection or storage credential;
- unrestricted network or filesystem access;
- direct access to the long-lived Cabinet Flow process;
- authority to apply persistent, external, secret-bearing, system or local
  effects;
- another actor's identity or grants.

Code returns validated outputs and explicit effect intents. Only trusted
Cabinet Flow behavior may revalidate current authority and apply an accepted
effect.

Each execution has bounded resources and a disposable lifetime. Completion
includes termination of the environment and descendant processes so leaked
memory, processes, connections, files or caches cannot remain owned by the
long-lived service.

Timeout, resource exhaustion, failed cleanup, schema violation and unauthorized
effects are observable failures, never successful execution.

A successful sandbox result is evidence for admission, not a production
transaction. Real execution starts again with current inputs and authority; a
sandbox effect preview cannot later be committed.

## Original-photo ingress

The first release has one supported ingress path for original invoice-photo
bytes: a dedicated Syncthing Inbox.

Syncthing is transport only. A synchronized path, filename, device timestamp,
rename or deletion is not a source identity, processing decision, business
association or custody acknowledgement.

Trusted Cabinet Flow behavior must:

- accept only complete bounded files of an actually supported media type;
- create immutable source identity, content digest, provenance and custody
  state;
- copy accepted original bytes outside the synchronized directory before
  reporting them as held;
- deduplicate repeated delivery by content identity;
- leave new sources unassigned until an authorized flow links them;
- expose an accepted image to the authorized online agent through Cabinet
  Flow's own MCP;
- keep server receipt and local archival acceptance as separate facts;
- rediscover pending or accepted sources after restart without depending only
  on Syncthing events.

The online agent recognizes the source and proposes or applies authorized
structured facts. It does not own original-byte custody. Flows and Boxes carry
source identity and bounded access capability, not a Syncthing path or repeated
uncontrolled copies.

Direct transfer of ChatGPT attachment bytes and a separate browser upload are
not first-release ingress paths.

## MCP ownership

Cabinet Flow owns its online MCP boundary because the agent must inspect and
organize Cabinet information, execute operational flows, create reviewable
results and, when necessary, manage capabilities through the same primary
conversation.

The MCP currently deployed with `cabinet-web-backend` is legacy evidence and
may temporarily proxy accepted operations during migration. It does not define
the target architecture or own Cabinet Flow semantics.

MCP operations are named, typed and bounded. The MCP boundary is not a generic
database, filesystem, code-execution or backend proxy.

## Local integration and offline behavior

Cabinet Flow has one integration with `cabinet-web-backend` for exchange with
the independent local Cabinet Backend.

That bridge may own machine authentication, bounded transport, delivery
acknowledgements, retry and unknown-outcome reconciliation required by the
transport protocol.

It does not own Slot, function, Flow, Box, execution-context, Card, source,
activation, agent-authority or local-archive semantics.

Cabinet Flow remains usable while the local Backend is offline:

- server-owned sources, results and Boxes retain their truthful durable states;
- work requiring a local consumer remains explicitly pending;
- local-only effects stop at the integration boundary;
- reconnection resumes or reconciles the exact exchange idempotently;
- local absence never becomes false completion or loss of accepted input.

The target direction is:

```text
online agent
→ Cabinet Flow MCP
→ Cabinet Flow
→ cabinet-web-backend compatibility bridge
→ local Cabinet Backend
→ local agent or application
```

## First-release proof

The first usable release does not require full legacy parity. It must pass two
distinct proofs so the product purpose is not confused with its extension
mechanism.

### Operational proof

1. An invoice photo arrives through the dedicated Syncthing Inbox.
2. Trusted behavior validates, hashes, registers and holds the source.
3. The authorized online agent retrieves it through Cabinet Flow MCP and
   recognizes its contents.
4. Existing accepted capabilities turn the recognized facts into a reviewable
   structured Invoice result while preserving source and commercial-line
   identity.
5. The result is associated with the correct project or construction object, or
   remains explicitly unassigned when the evidence is insufficient.
6. The agent produces useful analysis or prepares a reviewable capability
   invocation or handoff package addressed to the local estimating Box.
7. Protected persistent or local effects occur only after required human
   authorization.
8. The local side returns a separate acknowledgement when it actually accepts
   delivery.
9. Identity, provenance, versions, validation, pending states, effect outcomes
   and failures remain observable.

This proof demonstrates that Cabinet Flow brings real incoming construction
work into an ordered operational state. It does not require the user to author
a function during the invoice workflow.

### Capability-evolution proof

1. The user requests an operational result that existing accepted capabilities
   cannot produce.
2. The agent identifies and describes the missing bounded behavior instead of
   improvising hidden code.
3. The agent authors a small implementation with a declared contract and
   effects.
4. Cabinet Flow registers an immutable draft and runs it in the mandatory
   sandbox.
5. Admission and effect policy produce an explicit outcome.
6. An accepted version is activated and composed into a versioned flow.
7. The capability can be executed against authorized Cabinet data and later
   revised, deactivated or rolled back.
8. The exact versions, trace, validation and effect outcomes remain observable.

Legacy Cabinet behavior not yet migrated remains available from the current
application.

## Explicit exclusions

Cabinet Flow is not:

- a general-purpose IDE or software factory;
- unrestricted arbitrary-code execution;
- a generic operating-system, filesystem, database or MCP proxy;
- a replacement for the independent local archive;
- a generic integration hub;
- an autonomous agent allowed to expand its authority;
- the owner of AI Code Factory compiler semantics;
- dependent on local Backend availability for unrelated online work.

It is not limited to Invoice processing or estimation. Those are the first
evidence-rich construction workflows, not the complete long-term product
boundary.

## State 0 acceptance

State 0 is accepted because:

- the product is explicitly an operational environment for construction work;
- its principal work areas and observable user outcomes are named;
- ordinary operations and capability evolution are separate modes;
- slot contracts, implementation versions, capabilities and flows have distinct
  meanings;
- the first release has an explicitly accepted baseline and does not depend on
  self-bootstrap;
- Capability Boxes inherit proven Cabinet Vault semantics while invocations and
  handoff payloads remain distinct from Boxes;
- the product and successor boundary are explicit;
- primary actors and authority are explicit;
- the first-release operational and evolution proofs are distinct;
- legacy migration and backend responsibilities are bounded;
- offline behavior and protected effects are truthful;
- trusted isolation is non-bypassable at the product boundary;
- one original-photo ingress and its ownership split are explicit;
- negative product boundaries prevent scope drift;
- remaining implementation choices belong to later design states.

## Feasibility evidence

On 2026-09-05 a live test passed through:

```text
Syncthing device delivery
→ VPS trusted ingress
→ Cabinet MCP get_invoice_source
→ OpenAI Secure MCP Tunnel
→ ChatGPT
```

The returned source identity matched the server registry, SHA-256 matched the
accepted bytes, media was correctly identified as `image/png`, and the online
model received and described the image. The operation remained read-only and
did not create an Invoice Card, invoke OCR or a database, or modify the source.

This proves the transport subsection of the operational path. It does not yet
prove automatic activation, multi-source ordering, hostile-file rejection,
crash recovery, structured Invoice creation, project association, analysis,
Capability Box delivery, managed function admission, flow execution, protected
effects or local archival acknowledgement.
