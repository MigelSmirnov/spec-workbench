# Security review evidence for States 0–2

This reference defines the mandatory security review that closes State 2. It is
an authoring gate, not a vulnerability scanner and not an extension of
`global_spec.json`.

The review proves that every required category was considered and has one
explicit outcome:

- `APPLICABLE` — the enforceable decision is recorded in an indexed accepted
  decision;
- `NOT_APPLICABLE` — applicability was checked and a project-specific rationale
  is recorded;
- `UNRESOLVED` — a named open question records the missing decision and State 3
  is blocked.

Silence is never `NOT_APPLICABLE`. The Markdown record is a temporary normative
bridge; source design-state documents remain authoritative and can later be
projected into a structured standard graph without changing their decisions.

## Ownership by design state

### State 0 — trust boundaries

Record the actors and every boundary through which data or commands can enter:

- human and machine actors;
- authentication boundaries;
- browser or other client boundaries;
- external systems;
- webhook and integration boundaries;
- upload and file boundaries;
- secrets and credentials;
- public and private network surfaces.

State 0 answers: which external subjects and systems can send data or commands,
and which data or systems the product trusts. Unknown topology or authority is
an explicit open question, not an implementation default.

### State 1 — security-relevant model semantics

For each affected runtime entity, determine where applicable:

- owner, tenant, or account scope;
- the stable identity used by authorization;
- whether the entity is externally addressable;
- secret or sensitive fields;
- the source of truth for identity and ownership;
- whether the model can cross a trust boundary.

Use the identity already accepted through
`MODEL_IDENTITY_EVIDENCE.md`. Security review may depend on that decision but
must not redefine it. List affected `M*` items in the review evidence so the
model semantics are navigable.

### State 2 — enforceable decisions

Record concrete invariants, forbidden actions, accepted policies, or explicit
open questions. Generic advice such as “use secure practices” does not close a
category. Put a missing decision in the earliest State 0–2 document that owns
it; do not defer it to module design, contracts, notes, or assembly.

## Total review procedure

For every category below:

1. Determine applicability from State 0 boundaries, not from keyword presence.
2. Identify affected indexed models/entities and external boundaries.
3. Find an existing owning accepted decision, or create the decision in the
   earliest owning state.
4. State its invariant, forbidden action, or policy at State 2 when applicable.
5. If the product evidence cannot select one safe decision, create an indexed
   explicit open question, record `UNRESOLVED`, and stop before State 3.
6. Record the category outcome using the canonical grammar below.

`NOT_APPLICABLE` is valid only after these steps and must explain the
project-specific reason. It is not boilerplate to add to every project.

## Required categories

### Authentication / credential abuse

Review brute force, credential stuffing, and session or token lifecycle for
every human and machine authentication boundary. Identify credential scope,
revocation, recovery, replay characteristics, and the owner of abuse controls.

### Secrets

Review secrets in source control and GitHub, logs/errors/traces/artifacts, and
generated or exported files. State where credentials live, where they must not
propagate, and how exposure is revoked or rotated.

### Authorization

Review object-level authorization, tenant/owner scope, privileged operations,
and server-side enforcement independent of UI state. Tie authorization to the
exact stable entity identity accepted in State 1.

### Injection / interpreted input

Review SQL and query structure plus command, template, expression, prompt-tool,
or other interpreter boundaries that the product actually has. The normative
invariant is that runtime or user input must not become executable or query
structure unless a deliberately closed parser or vocabulary accepts it.

Do not add a State 2 instruction to “use parameterized SQL” when a deterministic
backend already guarantees the lowering. The backend owns that mechanism; the
project owns the higher-level input/structure invariant.

### External callbacks / webhooks

For each inbound callback or externally sourced synchronization event, close:

```text
authentication or integrity -> replay -> idempotency -> allowed transition
```

If there is no inbound callback, record why. Outbound integrations and pull
synchronization still require their applicable authenticity, response-integrity,
and replay decisions to be owned elsewhere.

### Browser boundary

Review XSS-relevant output, session and cookie semantics, allowed origins/CORS,
and state-changing request protection where applicable. Browser or client state
is never an authorization authority.

### Files and artifacts

Close these separately:

- payload type, size, and content acceptance;
- filename and path ownership;
- executable versus non-executable treatment;
- storage isolation;
- authorization for later retrieval.

Accepting a media type does not by itself close path safety, execution, storage,
or retrieval.

### Concurrency

Review read-modify-write races, single-use tokens/promocodes/credits, atomic
state transitions, and duplicate submission or idempotency. For every
`read -> check -> mutate` operation, state the invariant that must remain true
under concurrent calls and the owner of atomicity.

### Dependencies

Identify externally maintained libraries. When the product or deployment makes
dependency exposure operationally relevant, record the vulnerability and update
policy or leave an explicit blocking question. Do not invent a dependency
programme for a product with no such operational requirement.

## Canonical authoring grammar

Place exactly one `### Security review` section inside an indexed State 2
accepted decision. The section begins with the exact marker:

```markdown
### Security review

Security review: PERFORMED
```

Then record exactly one line for every required category, using the stable keys
below:

```markdown
- authentication_credential_abuse: APPLICABLE; references: A12; affected: M03, authentication boundary
- secrets: NOT_APPLICABLE; rationale: the product has no credentials, tokens, or deployment secrets
- authorization: UNRESOLVED; references: A20, OQ-004; affected: M08, public API boundary
- injection_interpreted_input: APPLICABLE; references: A21; affected: search input
- external_callbacks_webhooks: NOT_APPLICABLE; rationale: all integrations are outbound and no external event enters the product
- browser_boundary: NOT_APPLICABLE; rationale: the product has no browser or script-capable client
- files_artifacts: NOT_APPLICABLE; rationale: the product accepts, creates, stores, and retrieves no files or artifacts
- concurrency: APPLICABLE; references: A22; affected: M10
- dependencies: NOT_APPLICABLE; rationale: no deployed runtime or externally maintained dependency is in scope
```

Fields are separated by semicolons. `references` is a comma-separated list of
indexed keys. An `APPLICABLE` record must resolve to at least one accepted
decision. An `UNRESOLVED` record must resolve to at least one explicit open
question; it may also cite already accepted partial decisions. A
`NOT_APPLICABLE` record must contain a non-empty `rationale`. `affected` is
review evidence and navigation guidance; lint does not infer its semantic
completeness.

The accepted security-review decision and every referenced decision/question
remain ordinary `decision` or `open_question` items. Do not add `kind=security`,
a JSON registry, compiler metadata, or a security-specific editor.

## Normative examples

### Object access / IDOR

Wrong:

```text
order_id exists -> return order
```

Right:

```text
actor is authorized for exact Order entity -> operation allowed
```

Knowledge of a stable ID is not authorization proof.

### UI-only restriction

Hiding a button is not security enforcement. Every action that changes protected
state has a server-side enforcement owner.

### Webhook

An external event closes authenticity/integrity, replay, idempotency, and the
allowed state transition as one boundary decision.

### Upload

Payload acceptance, storage/path safety, execution policy, owner scope, and
later retrieval authorization are distinct obligations.

### Race-sensitive mutation

For `read -> check -> mutate`, record the invariant that remains true under
concurrent calls and the responsibility that owns the atomic transition.

## Gate execution

Before State 2 -> State 3:

1. Read this reference and perform the total review.
2. Use `design_index.py` to inspect affected `M*`, `A*`, source-key decisions,
   and `OQ-*` items.
3. Use `design_editor.py` for structural changes to existing indexed items.
4. Run `python tools/design_lint.py examples/<case> --state 2`.
5. Treat every missing/invalid outcome, unresolved reference, and
   `UNRESOLVED` category as BLOCK.

The lint proves review structure and addressability only. It does not claim that
the product is secure or detect XSS, injection, IDOR, credential abuse, or any
other vulnerability from prose.
