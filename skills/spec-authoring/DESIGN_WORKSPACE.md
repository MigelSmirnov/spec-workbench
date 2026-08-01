# Design Workspace — Layer 0

> The working knowledge space around the design-state ladder.
>
> It begins before Product Boundary and remains active through Assembly. It is
> not a section of `global_spec.json` and does not extend `SPEC_STANDARD.md`.

## Purpose

The design-state ladder structures knowledge into product boundaries, domain
models, rules, modules, flows, APIs, contracts, notes, and an assembled
specification. It assumes that the material being structured is real, available,
and understood.

In practice, a project begins as a mixture of:

- conversation;
- existing systems and their actual data;
- documents and screenshots;
- incomplete external contracts;
- security and infrastructure choices;
- product ideas;
- open questions;
- assumptions that have not yet been recognized as assumptions.

The Design Workspace keeps that material outside human and agent memory. It is
simultaneously:

- a sandbox for gathering and interpreting evidence;
- a decision register for deliberate choices;
- a planner for unresolved work;
- a dashboard showing where the design is going and what blocks it;
- an external memory that survives context loss.

The workspace answers a different question from the design states:

```text
Design Workspace: what do we know, why do we believe it, and what is still open?
Design states:     how is that knowledge represented in the specification?
```

## Governing principle

> The specification must never silently resolve an unfilled decision.

Every uncertainty that can change product behavior, security, compatibility,
persistent data, public contracts, or generated architecture must be either:

- bound to a real source and closed;
- recorded as an explicit deliberate choice;
- deliberately designed because the domain is owned by this project; or
- visibly marked as open or assumed.

An absent registry entry is not evidence that no decision exists. Any hidden
assumption that can change the generated result is itself a decision and must be
registered when discovered.

## Relationship to the design-state ladder

The workspace is not merely a one-time State 0 document. It wraps the entire
process:

```text
Design Workspace
  ├── sources and evidence
  ├── decisions and assumptions
  ├── open questions and blockers
  ├── security and operational choices
  ├── progress and next-state readiness
  └── change and invalidation history

        ↓ verified design input

Product Boundary
→ Domain Models
→ Rules and Invariants
→ Module Responsibilities
→ System Flows
→ Public APIs
→ Contracts
→ Notes
→ Assembly
```

The initial workspace must be coherent enough to begin Product Boundary.
However, later states will discover new decisions. Those decisions return to the
workspace, are sourced and closed there, and then propagate back into the owning
design state.

A design state may be explored while some non-entry questions remain open. It
must not be declared stable or used as accepted input for the next state while
its blocking workspace items remain `OPEN` or `ASSUMED`.

## What belongs in the workspace

Register an item when it affects at least one of the following:

- product scope or observable behavior;
- external-system compatibility;
- authentication, authorization, tenancy, secrets, or trust boundaries;
- persistent data shape or ownership;
- public API or integration contract;
- state transitions or failure behavior;
- storage, delivery, deployment, or operational strategy;
- limits, quotas, timeouts, retention, or cost;
- deterministic generation or materialization by the Factory;
- a choice the generator would otherwise make by default.

The workspace may also contain non-binding research and discarded alternatives,
but they must be distinguishable from accepted inputs.

## Source types

Every behavior-affecting decision has one legitimate source type.

| Type | Truth comes from | Typical use | Closure evidence |
| --- | --- | --- | --- |
| **Snapshot** | An external system or contract that already exists | Roles, grants, session claims, API responses, database values, external enums, provider behavior | Actual evidence captured from the source and stored or referenced beside the case |
| **Choice** | A deliberate selection among valid alternatives | Authentication mechanism, password storage, token strategy, database, timeouts, quotas, retry policy | Selected option, concrete parameters, owner, and rationale |
| **Design** | A domain owned by this project and not borrowed from elsewhere | Project-owned entities, state machines, layouts, internal workflows | Deliberately described form, owner, and reason |

The source type is about ownership of truth, not the shape of the final
specification.

A role catalog may later become `models`; a transition table may later become
`rules`; a timeout may later become `config`; an enforcement obligation may
later become a note or property. The workspace records where the knowledge came
from before those states structure it.

### Source-type legitimacy test

Before closing an item, ask:

1. Does an existing external system already own this truth?
2. Is this an implementation or policy option that someone must select?
3. Is this genuinely our domain to invent?

A missing or inconvenient external source does not turn a Snapshot into a
Design. A plausible agent proposal does not turn a Choice into a chosen policy.

## Status model

Each registered item has one status:

- `OPEN` — the question is known but no acceptable source is bound;
- `ASSUMED` — a temporary hypothesis is being used for exploration; it is not
  accepted truth;
- `confirmed` — Snapshot evidence is captured and sufficient for its declared
  scope;
- `chosen` — a Choice is selected with concrete parameters and ownership;
- `designed` — a project-owned Design is deliberate and reasoned;
- `superseded` — replaced by a newer accepted item;
- `invalidated` — its source or assumptions no longer support downstream use.

`OPEN` and `ASSUMED` are blocking when the item is required for entry to or
stabilization of the current design state.

## Workspace views

One registry may power several human-readable views.

### 1. Direction

A compact statement of:

- what product or capability is being designed;
- the current design state;
- the next intended state;
- the accepted scope;
- explicit non-goals;
- the most important current risks.

This prevents deep work on one entity from erasing the original destination.

### 2. Evidence inventory

A list of real source material:

- sanitized API samples;
- schemas and contracts;
- production or sandbox observations;
- existing code paths and tests;
- policy documents;
- screenshots or exported records;
- interviews or owner statements.

Each evidence item records origin, environment, version or revision when known,
capture date, authority, sanitization, and known limitations.

### 3. Decision board

The complete list of behavior-affecting decisions with source type, status,
owner, dependencies, and target design states.

### 4. Open questions and blockers

A focused view of `OPEN`, `ASSUMED`, invalidated, or conflicting items, ordered
by what they block next.

### 5. Readiness dashboard

A state-oriented view such as:

```text
Current target: Product Boundary

READY
  project goal
  primary actors
  existing Registry project contract
  initial storage ownership

BLOCKED
  production authentication strategy
  session lifecycle

DEFERRED, NOT ENTRY-BLOCKING
  long-term audit retention
```

The dashboard is derived from the registry. It is not a second place to store
truth.

## Decision records

A decision should be atomic enough to change, source, or invalidate
independently. Do not close a broad heading such as `authentication` when token
format, key ownership, lifetime, refresh, revocation, and browser storage remain
independent unknowns.

Recommended fields:

```yaml
- id: SRC-AUTH-001
  topic: security.access_token
  question: What access-token strategy does the product use?
  source_type: choice
  status: chosen

  owner: product-security
  scope:
    environment: production
    design_states:
      - product_boundary
      - rules
      - system_flows

  choice: signed_jwt
  parameters:
    algorithm: ES256
    lifetime_seconds: 900
    issuer: platform_identity

  reason: >
    Services need offline verification while key ownership remains centralized.

  alternatives_considered:
    - opaque_bearer_token

  depends_on:
    - SRC-IDENTITY-001
    - SRC-CLIENTS-001

  consumed_by:
    - product_boundary.security
    - rules.access_token_policy
    - flows.authenticate_request

  blocking:
    state: product_boundary
    mode: closure
```

The exact storage syntax may be Markdown, YAML, or JSON. Stable IDs and semantics
matter more than the serialization format.

## Snapshot requirements

A Snapshot is not closed merely because one real payload was saved.

Record:

- the external owner and system;
- capture date;
- environment;
- version, revision, or endpoint when known;
- authority: canonical, observed, or advisory;
- the stored or referenced evidence path;
- sanitization performed;
- relevant interpretation;
- known unknowns and non-guarantees.

A Snapshot closes only when its relevant semantics are understood well enough
for the next design state. Capturing `{"status": 3}` is insufficient when the
meaning and stability of `3` are unknown.

One observation must not be promoted into a stronger contract than it supports.
Record distinctions such as:

```yaml
known:
  - role is present in every inspected response
unknown:
  - whether new role codes can appear without notice
not_guaranteed:
  - ordering of grants
```

When possible, collect representative positive, empty, boundary, and failure
samples rather than only the happy path.

## Choice requirements

A Choice is closed only when it includes:

- the selected option;
- all behavior-affecting parameters;
- the decision owner or delegated authority;
- a concise reason;
- important rejected alternatives when they clarify the boundary.

An agent may propose a choice. It may not mark the choice `chosen` unless the
declared owner selected it or explicitly delegated the decision.

Silent library, framework, or generator defaults do not count as choices.
Security-sensitive defaults are especially forbidden as closure evidence.

## Design requirements

A Design is closed only when:

- the project genuinely owns the domain;
- its form or states are explicit enough for the target design state;
- the owner is known;
- the reason for the shape is recorded;
- it does not overwrite a real external contract that should have been a
  Snapshot.

Designing from the head is legitimate only here, because the project is the
source.

## Security strategies are first-class workspace material

Security must not be postponed as an implementation detail. The workspace
should expose at least the applicable decisions for:

- identity source and actor types;
- authentication mechanism;
- credential and secret storage;
- password hashing parameters when passwords are owned locally;
- token format, issuer, audience, signature or lookup strategy, and lifetime;
- refresh, revocation, logout, and session lifecycle;
- authorization model, roles, grants, scopes, and resource ownership;
- service-to-service identity;
- tenant isolation;
- browser/mobile storage and CSRF boundary;
- key rotation and secret ownership;
- audit requirements;
- production versus trusted-local deployment assumptions.

Existing identity roles, grants, claims, and session payloads are usually
Snapshots. Mechanisms and parameters are usually Choices. Project-owned access
state machines may be Designs. Do not collapse them into one generic
`security strategy` item.

## Gate semantics

Every item declares what it blocks.

- `entry` — the target state must not begin without it;
- `closure` — exploration may continue, but the state cannot be accepted or
  used as stable input for the next state;
- `non_blocking` — explicitly deferred, with a reason and a state before which
  it must be revisited.

The workspace is ready to begin Product Boundary when:

- the direction and initial scope are visible;
- known external systems have source owners;
- foundational identity, security, data-source, and integration questions are
  registered;
- no entry-blocking item is `OPEN` or `ASSUMED`;
- the remaining uncertainty is visible rather than silently filled.

A later design state is ready to close when every workspace item blocking that
state is closed and consumed by the appropriate design artifact.

## Discovery loop

New questions will appear during modeling, rule design, flows, contracts, and
notes. This is expected.

When a new behavior-affecting uncertainty appears:

1. stop treating it as local prose;
2. create or reopen a workspace item;
3. classify its legitimate source type;
4. mark the affected state as not stable;
5. acquire evidence, choose, or design;
6. propagate the result into the earliest owning design state;
7. update downstream artifacts that depended on the old assumption.

Do not solve a newly discovered product or security decision inside a contract
or note merely because that is where it became visible.

## Change and invalidation

Sources and decisions change. When a bound item changes:

- create a replacement or reopen the item;
- preserve the previous decision as superseded evidence;
- identify every `consumed_by` design artifact;
- mark affected states for revalidation;
- do not leave downstream artifacts silently bound to stale knowledge.

No downstream statement may be stronger than its source. Observed behavior
remains observed behavior; a deliberate choice remains an explicit choice; an
invented domain remains owned design.

## Sensitive data and sanitization

Real evidence must be structurally and semantically faithful, not
secret-bearing.

Before storing evidence beside a case:

- remove credentials, tokens, cookies, private keys, and secrets;
- anonymize personal data and internal identifiers when they are not semantically
  required;
- preserve types, cardinality, field presence, relevant formats, and edge cases;
- document substitutions and redactions;
- never commit production secrets to make a Snapshot appear more real.

A sanitized sample remains valid evidence only when sanitization does not erase
the property being studied.

## Suggested case layout

```text
examples/<case>/
├── workspace/
│   ├── README.md                 # direction and dashboard
│   ├── decisions.yaml            # source-bound decision registry
│   ├── open_questions.md         # optional rendered blocker view
│   └── sources/
│       ├── registry/
│       ├── identity/
│       └── provider-x/
├── 01_product_boundary.md
├── 02_domain_models.md
└── ...
```

The repository may begin with a simpler `sources.md`. Split it only when the
workspace becomes hard to review. Do not create a document hierarchy before
there is material to organize.

## Minimal working artifact

For a small case, one Markdown table is sufficient:

| ID | Question | Type | Status | Owner | Evidence or decision | Blocks |
| --- | --- | --- | --- | --- | --- | --- |
| `SRC-IAM-001` | What roles does the existing IAM return? | Snapshot | `confirmed` | integration | `workspace/sources/iam/roles.sanitized.json` | Product Boundary entry |
| `SRC-AUTH-002` | How are access tokens verified? | Choice | `chosen` | security | JWT ES256, 15 min, platform issuer | Product Boundary closure |
| `SRC-DOC-003` | What is the document lifecycle? | Design | `designed` | product | draft → submitted → approved/rejected | Domain Models closure |
| `SRC-SESSION-004` | What revokes a session? | Choice | `OPEN` | security | — | Product Boundary closure |

This minimal artifact already provides the essential external memory:

- where the project is going;
- what has been agreed;
- what evidence exists;
- what remains open;
- what the next design state is allowed to do.

## Anti-patterns

Reject these uses of the workspace:

- treating conversation as confirmation without evidence or ownership;
- storing a real sample but inventing the semantics of its fields;
- marking an agent recommendation as a chosen security policy;
- classifying an unavailable external contract as project-owned Design;
- using one broad decision to hide independently open parameters;
- creating a dashboard whose status is maintained separately from the registry;
- moving unresolved choices directly into `rules`, `config`, models, contracts,
  or notes;
- collecting evidence indefinitely without converting it into design input;
- storing secrets or personal data merely to preserve realism.

## Completion test

The Design Workspace is healthy when a new human or agent can answer, without
reconstructing the entire conversation:

1. What are we building and what is outside scope?
2. What state of the design ladder are we in?
3. What real source material has been collected?
4. Which facts came from external systems?
5. Which implementation and security strategies were deliberately selected?
6. Which domains were intentionally designed by us?
7. What is still `OPEN` or merely `ASSUMED`?
8. What blocks the next state?
9. Where has each closed decision been consumed?
10. What became stale when a source or decision changed?

The objective is not maximal documentation. The objective is a visible,
source-bound path from scattered project knowledge to a specification that does
not require the author, agent, or code generator to fill important voids from
memory or defaults.
