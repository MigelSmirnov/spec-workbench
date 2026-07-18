# State 0 — Product boundary

## Status

**Authoring pass over the requirements baseline `../01_product_boundary.md` …
`../09_notes.md`. Product decisions in this document were made with the
product owner on 2026-07-18 and supersede the corresponding open questions of
the baseline.**

## Product statement

Client Portal is a backend service with an HTTP JSON API that gives a
renovation client a transparent read-only view of their renovation projects —
planned budget, actual expenses with documents, expense allocation, work
progress, completed work value, received payments, and progress photos — while
authorized staff manage the portal-owned facts behind that view.

The portal owns its own identity-and-access contour (staff accounts, client
viewers, service principals) and the client-facing representation of budget,
expenses, allocations, progress, payments, and photos. It consumes project
identity from Registry, confirmed recognition results from the external OCR
boundary, prepared photo facts from Telegram intake, and immutable approved
estimate snapshots published by an authorized producer such as PresuPro.

The frontend dashboard is a separate future application consuming this API and
is outside this specification.

Application resources and commands use JSON. The only non-JSON response is an
authenticated binary download for an already-authorized ExpenseDocument or
ProgressPhoto. The portal streams that object through its own boundary; it
never exposes `file_ref`, a filesystem path, storage credentials, or a
provider URL to the client.

## Principals

Client Portal IAM supports exactly three principal types. They are never
merged into one account model.

### ClientViewer

A permanent read-only viewer identity representing one client, who may have
several simultaneous renovation projects:

- created by an operator; the client does not register;
- no email login, no password, no password reset, no profile management;
- authenticates through an unguessable capability link (`ViewerAccessCredential`)
  issued and re-issuable by an operator; the credential is stored only in a
  secure verification form and can be revoked;
- a successful entry opens a managed `ViewerSession`;
- project visibility is determined server-side from active
  `ProjectViewerGrant` records (one grant = one Registry `project_id`), never
  from URL content;
- all viewer capabilities are read-only; a viewer can never mutate data,
  manage grants, see unassigned projects, or escalate.

Revocation semantics:

- revoking the viewer or its access credential closes all of that client's
  projects;
- revoking one project grant closes only that project;
- archiving a Registry project keeps the grant and the project visible
  read-only.

### StaffAccount

Operator and administrator accounts with full account-based authentication:

- mandatory unique normalized email as login identifier plus password stored
  only as a secure hash; the email is verified through a confirmation
  challenge before the account can authenticate;
- email change is completed only by confirming ownership of the new address;
  the previous address is notified after the completed change; an
  administrative recovery override exists only as an exceptional, heavily
  audited process, never the primary mechanism;
- managed sessions with expiry, revocation, and sign-out-everywhere;
- complete password-reset flow: single-use revocable reset token with limited
  lifetime, delivered by email; a successful reset revokes existing sessions;
- security notifications (password changed, email changed, account suspended
  or disabled) are delivered through the email gateway;
- suspending or disabling an account invalidates its active sessions;
- login failures never reveal whether an email exists.

Roles are `operator` and `administrator`. Roles map to closed capability
sets; a role or capability is never accepted as a trusted request field.
Operators hold mutation capabilities for their assigned projects and manage
client viewers, grants, and access links. Administrators additionally hold
access-management capabilities (users, assignments, revocation) within their
administrative area.

### ServicePrincipal

A named machine identity for inter-service publication (for example the
PresuPro snapshot producer):

- own `service_principal_id`, human-readable source name, active/disabled
  status, creation/rotation/revocation timestamps, audit provenance;
- one or more independently revocable credentials, generated with sufficient
  entropy, shown only at creation or rotation, stored only in verification
  form, rotatable with an overlap period, never carried by staff or viewer
  contours, never logged;
- a closed narrow capability set — import-side only
  (`portal.estimate_snapshot.import`, `portal.estimate_snapshot.read_import_result`);
  never activation, budget/expense management, or access management;
- explicit project scope: allowed source types and allowed projects or
  administrative area; a global producer exists only through an explicitly
  granted capability; every import verifies the principal may publish for the
  given `project_id`;
- no shared secret across integrations; transport protection (bearer, signed
  request, mTLS, gateway) is permitted but inside the domain every request
  resolves to one concrete `ServicePrincipal`.

### Common authorization rule

Every operation checks together: valid active session, active principal,
access to the concrete `project_id`, required capability, and Registry
project lifecycle policy. Knowing a `project_id` or URL grants nothing.

## Budget sources

The portal supports two first-class budget sources; neither is a temporary
scheme:

```text
manual
approved_estimate_snapshot
```

### Manual budget

An authorized operator maintains ordered client-facing Budget Sections with
planned material and work amounts. Section identity is stable and is not its
display name.

### Approved estimate snapshot (inbound publication contract)

The publication contract belongs to Client Portal as an inbound integration
boundary. The portal does not poll PresuPro and does not depend on a PresuPro
read API that does not exist today:

```text
PresuPro or another authorized producer
→ publishes Approved Estimate Snapshot (push)
→ Client Portal validates and imports the exact version
```

Snapshot identity is `estimate_id + estimate_version` for one `project_id`.
Minimum snapshot data: `estimate_id`, `estimate_version`, `project_id`,
`approved_at`, `approved_by`, currency, tax mode, sections, source
provenance, `published_at`, `contract_version`. Each section carries
`source_section_id`, `source_section_code`, `display_name`, `sort_order`,
`material_planned`, `work_planned`. Section display name is never section
identity.

Import rules:

- an accepted snapshot is immutable; a new version never overwrites, mutates,
  or deletes an older one;
- re-publishing the same `estimate_id + estimate_version` with identical
  content idempotently returns the existing result; different content for the
  same identity is rejected as an integrity conflict (content fingerprint
  recorded);
- import and activation are distinct actions: the producer imports, a human
  operator/administrator reviews and activates; a producer can never activate
  its own import;
- at most one budget version is active per project at any time;
- PresuPro `accepted` status does not mean approved-for-portal; publication
  requires a separate PresuPro approval action; an approved presupuesto is
  not a factura and no factura is required for publication;
- `approved_by` inside the snapshot is source-system provenance and never
  substitutes for the authenticated portal actor.

### Coexistence and transition

A project may start with a manual budget and later move to an imported
snapshot. The transition is explicit:

- a newly imported version is never activated silently;
- manual sections are never rewritten in place;
- expenses and allocations are never deleted by a source or version change;
- existing allocations require explicit mapping to the sections of the newly
  activated version; matching stable section identifiers may link
  automatically; a renamed section with the same stable identifier remains
  the same section; sections without a stable correspondence require manual
  mapping; matching by display name alone is forbidden;
- unmapped expenses stay visible and must be resolved by an operator;
- `Other expenses` persists independently of budget versions;
- payments and photos do not depend on budget version changes.

## Primary outcomes

### Client view

An authenticated viewer sees the list of their assigned projects, opens one,
and reads: Registry project context, budget summary with source and ordered
sections, included and excluded confirmed expenses with `Other expenses`
separate, client-visible documents, work progress and completed work value,
payments and work balance, and the chronological photo gallery. Archived
projects expose the same reads in read-only mode. Unavailable data is shown
explicitly, never fabricated or replaced by silent zeros.

### Expense intake

The OCR adapter accepts a confirmed normalized recognition result (stable
`recognized_document_id`, supported `contract_version`, complete confirmed
content) together with operator-supplied project selection and allocation.
One recognized document creates at most one Expense with one Document;
replay is idempotent. Provenance and the source document reference are
preserved; confidence, provider-specific fields, and raw model responses
never enter the portal.

### Operator management

For an active project an operator can: correct, include, or exclude an
expense; allocate or manually split it across sections or `Other expenses`
(allocation sum equals the expense total; automatic proportional split is
forbidden); update manual work progress per section (0–100%); register work
payments (idempotent by stable payment identity); publish progress photos and
manage caption, section association, and visibility; maintain the manual
budget; review and activate imported budget versions; manage client viewers,
access links, and project grants.

### Administration

An administrator manages staff accounts, assignments, service principals,
credentials, and revocation within their administrative area.

### Derived values

Actual materials, remaining materials (overspend shown, not clamped),
completed work value (`planned work cost × completion percent`),
cost-weighted overall progress (arithmetic mean forbidden; unavailable when
no planned work cost exists), payments total, and work balance
(`completed work value − received payments`, shown as
`Completed ahead of payments` or `Unused advance payment`) are always
recomputable from their owning records and are never primary editable state.

### Audit

Every significant action records actor provenance: principal (`user_id`,
viewer, or service principal with credential/key version), `project_id`,
action, time, result, and affected business entity. This includes viewer and
grant management, access revocation, expense changes, progress updates,
payment registration, photo publication/visibility changes, budget changes,
snapshot import (with `estimate_id`, `estimate_version`, `contract_version`,
content fingerprint, rejection reasons), and version activation (with the
human staff actor).

## Currency policy

The portal operates in EUR only. Money uses decimal semantics with explicit
currency and domain-defined rounding. An expense or snapshot carrying a
different currency is rejected with an explicit error; the portal never
converts or guesses. Multi-currency is not designed into the models.

## Persistent data

Conceptual records (physical storage undecided at this state):

- client viewers, viewer access credentials (verification form), viewer
  sessions, project viewer grants;
- staff accounts, staff sessions; email verification challenges, pending
  email changes, password-reset tokens (all challenge secrets in
  verification form); email delivery records;
- service principals, service credentials (verification form), producer
  scopes;
- manual budgets with ordered budget sections;
- imported approved estimate snapshots with their sections (immutable,
  multi-version) and import results;
- budget version activation state and section mapping decisions;
- expenses, expense allocations, documents;
- work progress per section, work payments;
- progress photos;
- audit records.

Document and photo binaries stay outside business records; records hold
stable file references. The binary storage boundary is undecided at this
state.

## External systems

### Registry

Sole owner of project identity and current context. The portal consumes the
confirmed HTTP boundary (`/projects/active`, `/projects/{id}/validate`,
`/projects/{id}/context`) per the platform Registry contract: server-side
validation before linked writes, UUID identity matching, typed failure
translation, no client-supplied context as authority, no direct database or
model access. Registry status (`active`/`archived`) controls the mutation
policy; the portal never creates `project_id`. Registry archival is
independent from viewer-grant revocation.

### OCR Service and Telegram intake

OCR is an external microservice owning recognition, source pages, provenance,
confidence, and duplicate detection. Telegram bot is an intake interface
only. The portal accepts only the versioned confirmed normalized recognition
contract and prepared photo facts; project selection, expense confirmation,
and allocation come from the operator or intake process, never from OCR.

### PresuPro (snapshot producer)

Producer of approved estimate snapshots through the portal-owned inbound
publication contract, authenticated as a `ServicePrincipal`. Until the
producer exists, projects use the manual source; connecting the producer
later changes no portal architecture. Estimate calculation, mutable estimate
lifecycle, and factura remain PresuPro/Holded concerns outside the portal.

### Email Delivery Gateway

Delivery-only boundary for staff-account mail: email-verification,
email-change, and password-reset challenges plus security notifications. The
portal owns challenge creation, purpose binding, expiry, single-use
semantics, revocation, rate limits, verification-form token storage, message
kind and addressing, and audit; the gateway only delivers messages. The
portal never trusts the gateway with authorization decisions or challenge
validity, and delivery success or failure never counts as address
confirmation.

## Explicit non-goals

Client Portal does not:

- render the frontend dashboard (separate application over this API);
- perform OCR or depend on an OCR provider or model;
- contain Telegram intake logic;
- create projects or own Registry data;
- calculate or mutate PresuPro estimates;
- create facturas, accounting postings, or Holded documents;
- own full accounting or bank integration;
- convert currencies;
- estimate progress from photographs;
- reuse normalized recognized documents for other applications (future
  separate integration);
- store document or photo binaries inside business records;
- use one shared secret for integrations or accept roles/capabilities from
  request data.

## Product invariants visible at State 0

Detailed ownership is deferred to later states.

1. Every portal record belongs to exactly one Registry `project_id`; the
   portal never creates project identity.
2. Access requires session + active principal + project grant/assignment +
   capability + Registry lifecycle policy; a UUID or URL alone grants
   nothing.
3. Viewer capabilities are read-only; roles and capabilities are never
   trusted request fields; no shared secrets; credentials, session tokens,
   access tokens, challenge tokens, and passwords are stored only in
   verification or hash form and never logged; challenge tokens are
   purpose-bound, single-use, and time-limited.
4. Revoked membership/grant blocks new requests immediately; a disabled
   account or principal blocks everything; auth failures reveal neither
   account existence nor project data; all project-scoped queries are bounded
   by the permitted `project_id`.
5. An archived project is readable and immutable in the portal; archival
   never deletes history and never substitutes for access revocation.
6. One `recognized_document_id` creates at most one Expense; one Document
   remains one document across allocations; unconfirmed OCR output never
   becomes an Expense.
7. Allocation sum equals the expense total; automatic proportional
   allocation is forbidden; only confirmed included expenses join financial
   totals.
8. Planned budget never derives from actual expenses; a mutable PresuPro
   estimate never silently changes the portal budget.
9. An accepted snapshot is immutable and versioned; same identity + same
   content is idempotent, same identity + different content is an integrity
   conflict; import ≠ activation; at most one active budget version per
   project; a producer never activates its own import.
10. Budget source transitions are explicit; section identity is stable and
    never its display name; allocations survive version changes through
    explicit mapping.
11. All derived financial and progress values are deterministic and
    recomputable from owning records; missing data is explicit, never
    guessed, zeroed, or clamped.
12. Every significant action carries actor provenance to audit.
13. All money is EUR with decimal semantics; foreign currency input is
    rejected explicitly.

## Resolved baseline open questions

Decisions of 2026-07-18 close `../open_questions.md` as follows:

- Q1–Q2 (approved presupuesto lifecycle, presupuesto vs factura): closed for
  the portal boundary — the portal consumes explicitly approved immutable
  snapshots; approval is a separate PresuPro action; no factura involvement.
  The internal PresuPro approval workflow stays on the PresuPro side.
- Q3 (publication authority): an authorized producer `ServicePrincipal`
  publishes; humans activate.
- Q4 (versioning/retention): append-only immutable versions addressed by
  `estimate_id + estimate_version`; explicit activation; full retention.
- Q5, Q8 (manual→imported migration, later versions vs existing data):
  explicit transition with stable-identifier mapping, manual resolution of
  unmapped expenses, preservation of expenses/payments/photos.
- Q6 (approval authority): PresuPro-side approval action; outside the portal.
- Q7 (client-access closure): solved by viewer/grant revocation, independent
  of Registry archival.
- Q9 (zone → section mapping): the producer publishes stable
  `source_section_id`/`source_section_code`; name-based matching forbidden.

## Unresolved decisions for later states

- Mandatory MFA for operator/administrator accounts.
- Session lifetime policy (staff and viewer TTLs, renewal).
- Boundaries of an administrative area when more than one administrator
  exists.
- Concrete transport between PresuPro and the portal (bearer / signed
  request / mTLS) — does not affect domain semantics.
- External binary deletion/retention policy after source intake; portal reads
  authorized objects but never deletes them as a side effect of business
  visibility or archival.
- Presentation ordering and pagination details for lists (Registry list
  ordering is not guaranteed by the platform contract).
- Whether expense corrections keep a visible change history beyond audit
  records.

## State 0 readiness assessment

The product boundary is stable enough to begin domain-model design because:

- principals, their lifecycles, and the common authorization rule are
  explicit;
- both budget sources and their coexistence/transition rules are decided;
- the inbound snapshot contract is owned by the portal and fully specified at
  the business level;
- external ownership boundaries (Registry, OCR/Telegram, PresuPro) are
  explicit and confirmed by the audited baseline;
- every baseline open question is either closed by a recorded decision or
  listed above as a bounded unresolved decision, not hidden behind generic
  abstractions.
