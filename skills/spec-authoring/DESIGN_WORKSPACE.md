# Design Workspace — Layer 0

> The working knowledge space around the design-state ladder.
>
> It begins before Product Boundary and remains active through Assembly. It is
> not a section of `global_spec.json` and does not extend `SPEC_STANDARD.md`.

## Purpose

The design-state ladder structures knowledge into Product Boundary, Domain Models,
Rules, Responsibilities, Flows, APIs, Contracts, Notes, and Assembly. It assumes
that the material being structured is real, deliberate, and sufficiently complete.

The Design Workspace manages how that material is obtained and governed.

It is simultaneously:

- a sandbox for raw project material;
- a registry of facts, choices, designs, assumptions, and open questions;
- a planner for acquiring missing knowledge;
- a dashboard showing current direction, blockers, and next actions;
- persistent external memory for both the human and the agent.

The workspace is not one ever-growing Markdown document. This file defines the
methodology. [DESIGN_WORKSPACE_FORMAT.md](DESIGN_WORKSPACE_FORMAT.md) defines the
project file layout. Each project owns a separate workspace instance containing
its actual records and evidence.

## Core invariant

> No design state may silently resolve missing knowledge.

Every uncertainty that can change product behavior, models, rules, security,
contracts, architecture, or generated code must be either:

- bound to a source and closed; or
- registered explicitly as `OPEN` or `ASSUMED`.

When required material is missing, the correct action is to stop and acquire it,
not to replace it with a plausible default.

## Responsibility boundary

The Design Workspace answers:

- What do we know?
- Where did it come from?
- What have we deliberately chosen?
- What belongs to us to design?
- What are we only assuming?
- What is still unanswered?
- What blocks the next design state?
- What action should happen next, and who owns it?

The later design states answer:

- How should this verified material be represented in the specification?

`SPEC_STANDARD.md` answers:

- How is the completed specification serialized as `global_spec.json`?

The workspace must not duplicate final models, rules, contracts, or notes. It keeps
source material, decisions, provenance, readiness, and links to the downstream
artifacts that consume them.

## What must be registered

Register an item when a different reasonable answer could change at least one of:

- product semantics or observable behavior;
- actors, permissions, ownership, or access boundaries;
- external compatibility or an imported contract;
- persisted data, lifecycle, or state transitions;
- security, privacy, identity, secrets, or trust boundaries;
- module ownership or a major architectural boundary;
- limits, quotas, timeouts, retention, or failure policy;
- public APIs or generated implementation behavior.

Do not register ordinary implementation details that do not affect the
specification, such as local variable names or private refactorings.

Absence from the registry does not prove that something is not a decision. When a
hidden assumption is discovered, register it immediately.

## Source types

Every closable item has one primary source type.

### Snapshot

Truth belongs to an external system or contract that already exists.

Use for:

- external roles and grants;
- third-party request and response shapes;
- existing session or token claims;
- enum values owned elsewhere;
- database or message formats that must be preserved;
- imported security and compliance requirements.

A Snapshot closes only when representative, sanitized evidence is stored and its
relevant meaning, scope, environment, and limitations are understood. Inventing a
sample does not count.

### Choice

Truth comes from a deliberate selection among valid options.

Use for:

- authentication and authorization mechanisms;
- password or secret storage;
- token format, lifetime, refresh, and revocation strategy;
- session model;
- storage backend;
- retry, timeout, quota, retention, and failure policies;
- other implementation policies that a generator might otherwise default.

A Choice closes only when the selected option and its material parameters are
recorded. A default that nobody selected does not count.

### Design

Truth is owned by the project and exists nowhere else yet.

Use for:

- project-owned entities;
- state machines;
- product workflows;
- layouts and interactions;
- domain concepts invented for this product.

A Design closes only when the intended form or states and the reason for them are
recorded deliberately.

A missing Snapshot may not be reclassified as Design merely because the external
source is inconvenient to obtain.

## Statuses

Active statuses:

- `OPEN` — the question is known but has no sufficient source-backed answer;
- `ASSUMED` — a temporary hypothesis is being used for exploration but is not
  accepted as truth.

Closed statuses:

- `confirmed` — Snapshot evidence has been acquired and interpreted;
- `chosen` — a Choice and its parameters have been deliberately selected;
- `designed` — a project-owned Design and its rationale have been accepted;
- `not_applicable` — the item was reviewed and shown not to apply, with a reason.

Lifecycle statuses:

- `superseded` — replaced by a newer item;
- `invalidated` — its source or reasoning is no longer reliable;
- `needs_reconfirmation` — downstream use must pause until the item is checked;
- `reopened` — a previously closed item is active again.

`OPEN` and `ASSUMED` are never equivalent to closed knowledge.

## Decision authority

An agent may discover questions, collect evidence, propose choices, and draft
project-owned designs. It may mark an item closed only when the declared owner has
provided, selected, approved, or explicitly delegated the answer.

Each material item should identify:

- an owner;
- the scope in which the answer is valid;
- the evidence or rationale;
- the design state it blocks or supports.

Security-sensitive choices should identify the approving security or architecture
owner rather than being accepted merely because they are common defaults.

## Evidence rules

Snapshot evidence must record enough context to prevent an observed accident from
becoming a false contract:

- source system or authority;
- capture date;
- environment and version when relevant;
- whether it is canonical, observed, or advisory;
- known limitations and unknowns;
- sanitization performed;
- relevant positive and negative examples when practical.

Capturing bytes is not sufficient. The semantics needed by downstream design must
be understood.

Real samples must not expose secrets or personal data. Sanitization must preserve
meaningful structure, types, cardinality, and formats, and must document material
substitutions.

## Security strategies

Security is first-class workspace material, not a gap to be filled during code
generation.

The workspace must expose unresolved decisions involving:

- identity and credential ownership;
- authentication flows;
- authorization and grant sources;
- password and secret storage parameters;
- token format, signing, lifetime, refresh, rotation, and revocation;
- session persistence and expiry;
- browser storage and CSRF boundaries;
- encryption, key ownership, audit, retention, and privacy constraints;
- abuse limits, lockout, recovery, and failure behavior.

Each such item is classified as Snapshot, Choice, or Design and remains blocking
until its required parameters are explicit.

## Atomicity and dependencies

A registry item should be atomic enough to be independently sourced, changed, or
invalidated. Broad labels such as `authentication strategy` should be split when
identity provider, flow, token format, lifetime, refresh, revocation, and session
storage can vary independently.

Items may declare dependencies. A closed item must not rely on an `OPEN` or
`ASSUMED` dependency without being marked provisional.

## Dashboard and planner

The dashboard is a compact current view, not the source of truth. It should show:

- current design target;
- accepted direction and recent decisions;
- active blockers;
- next acquisition or decision actions;
- owners;
- readiness of the next design state;
- recently invalidated downstream work.

The registry is the source of truth. Evidence and detailed decision records live in
separate files referenced by registry entries.

The dashboard should normally remain short because closed history is summarized or
filtered out of the active view.

## Gate semantics

Two blocking modes are available:

- `entry` — the design state cannot responsibly begin;
- `closure` — exploration may continue, but the state cannot be stabilized,
  accepted, or used as input to the next state.

A design state must stop when its required entry material is `OPEN`, `ASSUMED`,
invalidated, or awaiting reconfirmation.

A design state must not close while any closure-blocking item remains unresolved.

The required response is operational:

1. state what material is missing;
2. explain why continuing would require invention or a silent default;
3. identify the source type;
4. create or update the registry item;
5. record the owner and next acquisition or decision action;
6. resume only after the gate is satisfied.

## Continuous discovery

Layer 0 is not a one-time intake form. It remains active around every later state.

When a later state discovers a new unresolved fact or choice:

1. register it in the workspace;
2. classify its source type;
3. mark affected work provisional or blocked;
4. acquire or decide the missing content;
5. update downstream artifacts and readiness;
6. return to the design state.

Returning to the workspace is normal process control, not failure.

## Change and invalidation

When a bound source or accepted decision changes, identify every downstream design
artifact that consumed it. Those artifacts must be revalidated before they remain
accepted.

A closed registry item should therefore link to its consumers or use stable IDs
that downstream working artifacts can reference.

No downstream statement may be stronger than its source:

- an observed sample remains an observation unless authority makes it contractual;
- a deliberate choice remains an explicit policy;
- a project-owned design remains owned design;
- unknown behavior remains unknown rather than becoming an invented guarantee.

## Readiness for Product Boundary

Product Boundary may begin only when its entry material is sufficient to state the
product without inventing central facts. At minimum, review:

- goal and observable outcomes;
- actors and ownership boundaries;
- external systems and imported contracts;
- major inputs, outputs, and persisted material;
- material security and privacy constraints;
- known product limits and failure obligations;
- all current entry-blocking questions.

Not every future design decision must be closed before Product Boundary. Decisions
discovered later return to the workspace and block the state that needs them.

## Interaction protocol

When working with a human:

1. show the current target and compact dashboard;
2. distinguish facts, choices, designs, assumptions, and unknowns;
3. do not hide missing information in polished prose;
4. ask for or acquire a small coherent group of blocking items at a time;
5. propose concrete next actions and owners;
6. preserve accepted answers outside conversational memory;
7. resume the ladder only when the relevant gate is closed.

Use [DESIGN_WORKSPACE_FORMAT.md](DESIGN_WORKSPACE_FORMAT.md) to create and maintain
a concrete project workspace.