# Design Workspace Format

This document defines the file layout and record shapes for a concrete project
workspace. The governing methodology is [DESIGN_WORKSPACE.md](DESIGN_WORKSPACE.md).

A workspace is a directory, not a monolithic document.

## Recommended layout

```text
workspace/
├── dashboard.md
├── decisions.yaml
├── questions.yaml
├── sources/
├── choices/
├── designs/
└── archive/
```

Only `dashboard.md`, `decisions.yaml`, and `questions.yaml` are expected at startup.
Other directories are created when needed.

## Source of truth

- `decisions.yaml` is the authoritative registry of source-bound facts, choices,
  project-owned designs, assumptions, and lifecycle state.
- `questions.yaml` is the active acquisition and clarification queue.
- `dashboard.md` is a compact human-readable projection of the registries.
- `sources/` contains sanitized external evidence.
- `choices/` contains detailed records for material implementation or policy
  selections.
- `designs/` contains detailed records for project-owned domain design.
- `archive/` contains inactive material when keeping it in active files would make
  them difficult to review.

The dashboard must not become the only place where a decision exists.

## `dashboard.md`

The dashboard should answer, at a glance:

- What design state are we preparing or stabilizing?
- What direction has already been accepted?
- What blocks progress?
- What should happen next?
- Who owns each next action?
- Which completed work was invalidated recently?

Recommended shape:

```markdown
# Design Workspace

## Current target

Prepare verified input for Product Boundary.

## Accepted direction

- Existing corporate IAM owns employee identity.
- The product does not store employee passwords.

## Blocking

| ID | Missing material | Type | Owner | Next action |
|---|---|---|---|---|
| IAM-ROLES | Production role catalogue | Snapshot | integration | Export sanitized role data |
| SESSION-LIFETIME | Session expiry policy | Choice | security | Select idle and absolute limits |

## Readiness

| Design state | Status | Reason |
|---|---|---|
| Product Boundary | BLOCKED | Two entry items remain open |
| Domain Models | NOT READY | Product Boundary is not stable |

## Recently changed

- None.
```

Keep detailed evidence and rationale outside the dashboard.

## `decisions.yaml`

Each registry entry uses a stable ID.

Required fields:

```yaml
- id: IAM-ROLES
  question: Which external roles and grants exist?
  source_type: snapshot
  status: confirmed
  owner: integration-team
  scope:
    environment: production
    external_system: corporate-iam
  required_for:
    state: product-boundary
    gate: entry
```

Depending on source type, add one of the following closures.

### Snapshot closure

```yaml
  evidence:
    - path: sources/iam/roles.production.sanitized.json
      captured_at: 2026-08-01
      environment: production
      authority: observed
      sanitized: true
  interpretation:
    known:
      - role.code and role.grants are present in all captured records
    unknown:
      - whether new role codes may appear without notice
    not_guaranteed:
      - role ordering
```

### Choice closure

```yaml
  choice: argon2id
  parameters:
    memory_kib: 65536
    iterations: 3
    parallelism: 1
  reason: Meets the approved security baseline within the deployment memory budget.
  alternatives_considered:
    - bcrypt
    - scrypt
  approval:
    approved_by: security-owner
    approved_at: 2026-08-01
  details: choices/password-storage.md
```

### Design closure

```yaml
  design:
    states:
      - draft
      - submitted
      - approved
      - rejected
    terminal_states:
      - approved
      - rejected
  reason: Explicit lifecycle states prevent contradictory boolean flags.
  approval:
    approved_by: product-owner
    approved_at: 2026-08-01
  details: designs/document-lifecycle.md
```

### Active unresolved entry

```yaml
- id: SESSION-LIFETIME
  question: What are the idle and absolute session limits?
  source_type: choice
  status: OPEN
  owner: security-owner
  required_for:
    state: rules
    gate: closure
  next_action: Select both limits and document the operational rationale.
```

### Assumption

```yaml
- id: IAM-SESSION-CLAIMS
  question: Which claims are guaranteed in the session?
  source_type: snapshot
  status: ASSUMED
  owner: integration-team
  assumption: user_id and roles are probably present
  required_for:
    state: domain-models
    gate: entry
  next_action: Capture and interpret a sanitized production session payload.
```

Optional common fields:

```yaml
  depends_on:
    - CLIENT-TYPES
  consumed_by:
    - product-boundary.identity
    - models.UserSession
  supersedes: OLD-SESSION-POLICY
  notes:
    - Free-form working note, not normative specification prose.
```

## `questions.yaml`

This file is the action queue. It may duplicate IDs from `decisions.yaml`, but it
must not duplicate their full reasoning or evidence.

```yaml
- id: IAM-ROLES
  priority: blocking
  owner: integration-team
  action: Export and sanitize the production role catalogue.
  expected_result: sources/iam/roles.production.sanitized.json
  due: null

- id: SESSION-LIFETIME
  priority: blocking
  owner: security-owner
  action: Select idle and absolute session limits.
  expected_result: Updated decision SESSION-LIFETIME with parameters and approval.
  due: null
```

Remove or archive a question after the corresponding registry item closes.

## `sources/`

Store actual external evidence without secrets or personal data.

Recommended naming:

```text
sources/<system>/<subject>.<environment>.<sanitization>.<extension>
```

Examples:

```text
sources/iam/roles.production.sanitized.json
sources/iam/session.production.sanitized.json
sources/payments/webhook-error.sandbox.sanitized.json
sources/vendor/openapi-v3.2.yaml
```

When a file alone cannot carry context, add a neighbouring metadata file:

```yaml
source_system: corporate-iam
captured_at: 2026-08-01
environment: production
authority: observed
sanitized: true
substitutions:
  - Replaced user identifiers with stable synthetic identifiers.
limitations:
  - Only interactive employee sessions were sampled.
```

Do not commit credentials, cookies, bearer tokens, private keys, personal data, or
unredacted production payloads.

## `choices/`

Use a detailed record when a Choice needs trade-offs, operational consequences, or
approval context that would make `decisions.yaml` noisy.

Suggested sections:

```markdown
# Session strategy

## Decision

Rotating refresh tokens with 15-minute access tokens.

## Parameters

...

## Context

...

## Alternatives

...

## Consequences

...

## Approval

...
```

Small choices may remain entirely in `decisions.yaml`.

## `designs/`

Use for project-owned concepts that need diagrams, examples, state tables, or
rationale before they are structured into specification models and rules.

These are working design records, not substitutes for the eventual
`global_spec.json` sections.

## `archive/`

Archive only inactive material:

- superseded decisions;
- closed questions no longer useful in the active queue;
- old dashboard snapshots when history is valuable;
- evidence replaced by a newer authoritative version.

Never archive an active blocker merely to make the dashboard green.

## Scaling rules

To prevent workspace sprawl:

1. Keep the dashboard as a projection of active work.
2. Keep registry entries compact and link to detailed files.
3. Store raw material in its native format rather than copying it into Markdown.
4. Split only independently changeable decisions.
5. Do not register details that cannot affect the specification.
6. Archive inactive records without deleting provenance.
7. Use stable IDs so downstream artifacts can reference decisions without copying
   their contents.

## Starter template

Copy `templates/design-workspace/` into a project or case-study directory and fill
it incrementally. The template is intentionally small; directories for evidence
and detailed records are added only when they become necessary.