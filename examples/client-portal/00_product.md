# State 0 — Product boundary

## Status

**Authoring pass over the requirements baseline `baseline/01_product_boundary.md` …
`baseline/09_notes.md`. Product decisions in this document were made with the
product owner on 2026-07-18 and supersede the corresponding open questions of
the baseline.**

Migrated to the current Workbench layout on 2026-11-06 (`open_questions.md`
Q15). The text above "Decisions" is the State 0 of 2026-07-18 unchanged but
for paths. "Decisions" numbers the owner decisions the case already holds and
carries, each with its source, the product-level decisions the Factory
accepted for `client_portal_sandbox` between 2026-07-22 and 2026-08-17 while
this case was not updated (`SOURCE.md`, "Divergence"). A migration changes form, not
meaning: nothing in "Decisions" is new to the product; every entry names the
document or the accepted Factory spec change it comes from.

Round-01 (2026-11-06, `questions/state0/round-01/summary.json`) judged 10
topics blocking, most of them about the text of 2026-07-18. The owner decided
on 2026-11-06 that the current service behaviour is accepted and delegated
technical decisions; R0-14 to R0-22 resolve the topics in favour of the
accepted Factory spec and the running service, and the sentences they
contradicted are narrowed in place with the decision cited. Round-02 judged 4
topics blocking (repaired in R0-09, R0-14, R0-17, R0-20); round-03 judged 2:
T11, whether a producer's bearer credential stands in for a session (the
common authorization rule now says so, R0-09), and T23, how the initial staff
password reaches its holder, which uncovered that the accepted service carries
out no email challenge (R0-19, R0-23). Round-04 judged 7 topics blocking,
each a sentence that still stated the former behaviour next to R0-09, R0-14,
R0-15, R0-19, R0-23, or a fact the text left unstated; the sentences are
narrowed in place and R0-24, R0-25 carry the two unstated facts from the
accepted Factory spec. Round-05 judged 4 topics blocking, all on that new
text: what an identical re-publication answers, and how grants and
assignments of an archived project relate to the common authorization rule
and to invariant 5; R0-24, R0-25 and the rule are narrowed to the accepted
spec. Round-06 judged 1: whether reading an import result rechecks the
producer's grant (R0-21: it does not). Round-07 judged 1: the first
administrator against "only administrators create staff accounts" (R0-14
names the R0-07 exception).

On 2026-11-07 the owner removed the staff email challenges from the product
(R0-23): the portal has no email verification, email change or password-reset
challenge, no email delivery boundary, and sends no email. The sentences that
described the deferred challenges are removed or narrowed in place, citing
R0-23; R0-03 is withdrawn by the same decision.

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

- created by an administrator (R0-14); the client does not register;
- no email login, no password, no password reset, no profile management;
- authenticates through an unguessable capability link (`ViewerAccessCredential`)
  issued and re-issuable by an administrator (R0-14); the credential is stored only in a
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
  only as a secure hash; an account authenticates only while it is active,
  and an administrator activates a pending account (R0-19);
- no email challenge and no email: the portal has no email verification, no
  email change confirmed at a new address, no password-reset token and no
  security notification, and sends no message to any address (R0-23);
- an administrative recovery override exists only as an exceptional, heavily
  audited process (R0-20);
- managed sessions with expiry, revocation, and sign-out-everywhere;
- suspending or disabling an account invalidates its active sessions;
- login failures never reveal whether an email exists.

Roles are `operator` and `administrator`. Roles map to closed capability
sets; a role or capability is never accepted as a trusted request field.
Operators hold mutation capabilities for their assigned projects.
Administrators additionally hold access-management capabilities (users,
assignments, client viewers, viewer grants and access links, service
principals, revocation) within their administrative area (R0-14).

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
- no shared secret across integrations; the credential travels only in a
  bearer header (R0-09), and every request resolves to one concrete
  `ServicePrincipal`.

### Common authorization rule

Every operation on a project's records — budget, snapshot, expense, document,
progress, payment and photo — checks together: valid active session (for a
service principal, its authenticated bearer credential of R0-09, which needs
no separate session), active principal, access to the concrete `project_id`,
required capability, and Registry project lifecycle policy (R0-15). Creating
and revoking grants and assignments are access management: they check the
session, the active principal and the administrator's access-management
capability (R0-14); creating one also requires the Registry project known and
active, revoking one consults no Registry (R0-24). A producer's read of its
own import result checks only its bearer credential and that it made the
import (R0-21). Knowing a `project_id` or URL grants nothing.

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
  content is answered with a fresh import result of outcome idempotent
  replay that names the existing snapshot, which stays unchanged (R0-25);
  different content for the
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
explicitly, never fabricated or replaced by silent zeros. The one exception
is the project list: a granted project, archived or not, whose Registry
context cannot be obtained at that moment is left out of it rather than
listed without context; once its context is obtained again it is listed
again, archived ones read-only (accepted
Factory change `00ac72f18d9c`, note `list_viewer_projects`; owner
2026-11-06: current service behaviour accepted).

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
budget; review and activate imported budget versions. Client viewers, access
links and project grants are managed by administrators (R0-14).

### Administration

An administrator manages staff accounts, assignments, service principals,
credentials, and revocation within their administrative area.

### Derived values

Actual materials, remaining materials (overspend shown, not clamped),
completed work value (`planned work cost × completion percent`),
cost-weighted overall progress (arithmetic mean forbidden; unavailable when
no planned work cost exists), payments total, and work balance
(`completed work value − received payments`, shown as
`Completed ahead of payments` or `Unused advance payment`, or as balanced
when it is zero) are always
recomputable from their owning records and are never primary editable state.

### Audit

Every significant action records actor provenance: principal (`user_id`,
viewer, or service principal with credential/key version), `project_id`,
action, time, result, and affected business entity. This includes viewer and
grant management, access revocation, expense changes, progress updates,
payment registration, photo publication/visibility changes, budget changes,
snapshot import (with `estimate_id`, `estimate_version`, `contract_version`,
content fingerprint, rejection reasons), and version activation (with the
human staff actor). An action is recorded when it completes or, for a
snapshot import, when the attempt is classified; an operation that fails
on storage or the Registry before that is not recorded (R0-25).

## Currency policy

The portal operates in EUR only. Money uses decimal semantics with explicit
currency and domain-defined rounding. An expense or snapshot carrying a
different currency is rejected with an explicit error; the portal never
converts or guesses. Multi-currency is not designed into the models.

## Persistent data

Conceptual records (physical storage undecided at this state; decided by R0-10):

- client viewers, viewer access credentials (verification form), viewer
  sessions, project viewer grants;
- staff accounts, staff sessions;
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
state; it is decided by State 3 ("Binary storage boundary"), R0-10 and R0-13.

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
and allocation come from the authenticated operator, never from OCR or the
intake interface (R0-17).

### PresuPro (snapshot producer)

Producer of approved estimate snapshots through the portal-owned inbound
publication contract, authenticated as a `ServicePrincipal`. Until the
producer exists, projects use the manual source; connecting the producer
later changes no portal architecture. Estimate calculation, mutable estimate
lifecycle, and factura remain PresuPro/Holded concerns outside the portal.

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
  request data;
- send email or any other message to a staff member, a client or any address
  (R0-23).

## Product invariants visible at State 0

Detailed ownership is deferred to later states.

1. Every project-scoped portal record belongs to exactly one Registry
   `project_id`; the portal never creates project identity (R0-16).
2. Project-scoped access requires session (for a service principal, its
   authenticated bearer credential, R0-09) + active principal + project
   grant/assignment + capability + Registry lifecycle policy; a UUID or URL
   alone grants nothing. The operations without a session are those of R0-15.
3. Viewer capabilities are read-only; roles and capabilities are never
   trusted request fields; no shared secrets; credentials, session tokens,
   access tokens, and passwords are stored only in verification or hash form
   and never logged.
4. Revoked membership/grant blocks new requests immediately; a disabled
   account or principal blocks everything; auth failures reveal neither
   account existence nor project data; all project-scoped queries are bounded
   by the permitted `project_id`.
5. An archived project's budget, snapshot, expense, document, progress,
   payment and photo records are readable and immutable in the portal (the
   one exception is the empty manual budget of R0-24); no new
   grant or assignment is created for it, while its existing grants and
   assignments keep giving access and can be revoked (R0-24). Archival never
   deletes history and never substitutes for access revocation.
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

Decisions of 2026-07-18 close `open_questions.md` Q1–Q9 as follows:

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
- Session lifetime policy (staff and viewer TTLs, renewal). Decided by R0-06.
- Boundaries of an administrative area when more than one administrator
  exists.
- Concrete transport between PresuPro and the portal — decided by R0-09: a
  bearer header only.
- External binary deletion/retention policy after source intake; portal reads
  authorized objects but never deletes them as a side effect of business
  visibility or archival.
- Presentation ordering and pagination details for lists (Registry list
  ordering is not guaranteed by the platform contract). Ordering is decided
  by State 2 R15; pagination stays absent (R0-01).
- Whether expense corrections keep a visible change history beyond audit
  records.

## Decisions

Owner decisions of the case and product-level decisions of the accepted
Factory spec, numbered so that later states can cite them. R0-01 to R0-06
restate decisions already written above or in the former `spec/HANDOFF.md`;
R0-07 to R0-12 are carried from accepted Factory spec changes (`SOURCE.md`);
R0-13 is the owner decision of 2026-11-06 on Q12; R0-14 to R0-22 resolve the
State 0 question rounds under the owner decision of 2026-11-06, and R0-24,
R0-25 state facts of the accepted spec the text had left unstated.

### R0-01 — Sole-trader operating profile (owner, 2026-07-18)

The product owner is a sole trader (autónomo) with few parallel projects.
Operating simplicity is a first-class constraint; list pagination is absent for
this few-project profile (former HANDOFF key decisions 1 and 14).

### R0-02 — Three principal types, never merged (owner, 2026-07-18)

`StaffAccount`, `ClientViewer` and `ServicePrincipal` as written under
"Principals" (former HANDOFF key decision 2).

### R0-03 — Withdrawn: no Email Delivery Gateway (owner 2026-11-07, replacing owner 2026-07-18)

The owner decision of 2026-07-18 (former HANDOFF key decision 3) made an Email
Delivery Gateway a mandatory external boundary for the staff email challenges.
The owner withdrew it on 2026-11-07 together with the challenges (R0-23): the
portal has no email boundary. Administrative recovery stays an exceptional,
heavily audited flow (R0-20).

### R0-04 — Snapshot import is a push contract owned by the portal (owner, 2026-07-18)

As written under "Approved estimate snapshot" and "Coexistence and transition"
(former HANDOFF key decision 4).

### R0-05 — Backend with a JSON API, EUR gross money, expenses only from OCR intake (owner, 2026-07-18)

Backend and JSON API only; money is EUR, gross (IVA included), decimal,
rounded half up to two places; an Expense is created only through OCR intake
(former HANDOFF key decision 5; "Currency policy").

### R0-06 — Sessions and configuration defaults (owner, 2026-07-19; narrowed by owner 2026-11-07)

Sessions have a fixed expiry with no sliding renewal; the defaults are a staff
session of 12 hours, a viewer session of 30 days, and password hashing with
argon2id (former HANDOFF, "Product-owner confirmation received"). The
self-service password reset and the challenge lifetimes and rate limit the
decision of 2026-07-19 also set were removed with the challenges (R0-23).
This closes the session-lifetime item of "Unresolved decisions for later
states".

### R0-07 — The first administrator is created by a local command, never over HTTP (accepted Factory spec, 2026-08-17)

An empty deployment cannot acquire its first operator through the API, because
creating a staff account needs an authorized administrator. The host operator
runs a local administrative command that creates exactly one active
administrator when no staff account exists, and is refused once any exists. The
command is not an HTTP route and does not appear in the API description; the
email and password are its inputs, read neither from process arguments nor
from the environment nor from a file, and never printed, logged or audited,
except that the success message shows the normalized email to the operator
who supplied it (Factory code `cli/staff_bootstrap.py` 33). Its
outcome is a closed set of exit codes that deployment scripts may branch on
(Factory `6011ac93`, `rules.staff_bootstrap_policy`).

### R0-08 — Administrators discover the projects they grant (accepted Factory spec, 2026-08-08)

To grant a viewer a project, an administrator lists the active Registry
projects through an authenticated portal operation that requires the
access-management capability; a denied authorization stops before Registry is
asked. A viewer's own project discovery stays the grant-based path of "Client
view" (Factory `fae77f99`).

### R0-09 — A viewer's session travels only in a browser cookie; a producer only in a bearer header (accepted Factory spec, 2026-08-01)

After a successful entry with the access link, the viewer's session is held in
a host-only, HTTP-only, secure, same-site-strict cookie; no viewer credential is
ever readable by page script. Viewer browser routes accept only that cookie, and
a viewer sign-out is refused unless it comes from the portal's own public
origin (entry is rate limited, not origin-checked; Factory code
`runtime/transport_guard.py` 136–146). Viewers can restore and end their session explicitly. Service
principals authenticate only with a bearer header (Factory `35a0a09c`,
`babd5e52`, `51d19fdf`; `rules.http_transport_policy.browser_session`).

### R0-10 — One deployment: one SQLite database, one local binary root, configured by environment (accepted Factory spec, 2026-07-22 to 2026-08-16)

The portal runs as one service with one SQLite database file and one local
directory under which `file_ref` resolves to stored bytes; the binary read
bound `binary_max_read_bytes` stays a deployment setting. The service is
configured only by environment variables, which it validates when it starts,
and answers only on the trusted hosts it is
configured with; wildcard hosts and origins are refused. This decides the
"physical storage undecided" of "Persistent data" (Factory `4bdaa008`,
`38626cc7`, `dc351917`, `8387e0a3`, `d1280708`; `config.persistence`,
`config.runtime_environment_variables`).

### R0-11 — Public liveness and readiness answers (accepted Factory spec, 2026-07-31)

The service answers an unauthenticated liveness and readiness check that
changes no product state and discloses no path, credential, schema, dependency
version, configuration or exception (Factory `21658368`,
`rules.http_transport_policy.health`).

### R0-12 — Protected binaries are delivered as exact bytes (accepted Factory spec, 2026-08-01)

An authorized document or photo is answered as its exact stored bytes, never
inside a JSON envelope or a redirect. Its media type is recognized from the
content and must be on a closed list per object kind; the download name is
derived from the object kind and id, never from a stored name or caption. An
unknown, cross-project or hidden read is answered the same way, so the caller
cannot tell them apart; a refused document read answers that way also when
its stored content is missing, oversize or unlisted, while a photo whose
stored content cannot be delivered fails as an explicit storage-unavailable
error (Factory
`babd5e52`, `rules.binary_delivery_policy`; Factory code
`domain/photo_management.py`; owner 2026-11-06: current service behaviour
accepted; technical decisions delegated).

### R0-13 — The portal's file boundary stays read-only (owner, 2026-11-06; Q12)

The State 3 binary boundary is kept: the portal reads binaries behind
`file_ref` and never accepts uploads. A separate future intake service places
binaries and supplies the references. Until the hand-over between that service
and the portal is decided (Q12 questions 1–5), operator placement of binaries
stays the declared temporary route, outside the API.

### R0-14 — Access management is administrator-only (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

Creating, revoking and re-issuing client viewers, their access links and
project grants, staff accounts and assignments, service principals, their
credentials and producer grants all require the access-management capability,
which only administrators hold (R2). The one exception is the first
administrator of R0-07: the local bootstrap command creates it outside every
portal operation, needs no capability, and is refused once any staff account
exists. Operators work on the projects assigned to them. This is the accepted spec's behaviour: every such route is
`/admin/…` with `authorize_access_management` (`rules.http_router_backend`).
Resolves round-01 T12 and round-07 T9.

### R0-15 — Which operations need no session (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

The common authorization rule binds project-scoped operations. Without a
session the portal answers only: staff login, viewer entry with an access
link, and the liveness and readiness checks (R0-11). Staff login proves the
account's credentials and viewer entry proves the capability secret of the
access link; the liveness and readiness checks disclose nothing. The portal
has no email-challenge or password-reset operation (R0-23).
Producer operations authenticate with the bearer credential of R0-09.
Resolves round-01 T7 and round-04 T3.

### R0-16 — Project-scoped records and records without a project (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

Budget, snapshot, expense, progress, payment and photo records, grants and
assignments each belong to exactly one Registry project. Principals, their
sessions and credentials and the first
administrator created by R0-07 belong to no project; an audit record names a
project when its action has one. Resolves round-01 T17.

### R0-17 — Intake decisions come from the authenticated operator (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

An expense is created when an authenticated staff member with mutation
capability on the project submits the confirmed recognition result with the
project and the allocation; a progress photo is published the same way. The
intake interface and OCR decide nothing. The portal trusts that authenticated
staff submission and records its `provenance_ref`; it does not verify
independently that the content came from the OCR service, which has no
principal of its own in the portal. Which principal calls these
operations for binaries placed by the future intake service is Q12 question 3
and is not designed here. Resolves round-01 T8.

### R0-18 — A new expense document is client-visible (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

An expense document is visible to the client from its creation; staff may hide
it and show it again. A progress photo's visibility is given when it is
published. This is the running service's behaviour (Factory code
`application/expense_intake.py`, `client_visible=True`). Resolves round-01
T10.

### R0-19 — Staff onboarding (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

An administrator creates a staff account with its email, role and an initial
password the administrator chooses and submits in that creation request; the
account is `pending_verification`, and the portal keeps only the password's
hash. The administrator hands the initial password to the holder outside the
portal: no portal answer or message carries it back, and nothing logs it.
The administrator then activates the account (`pending_verification` →
`active`); the holder logs in with the initial password and changes it
(accepted contracts `create_staff_account`, `change_staff_status`,
`change_staff_password`). No email is sent and no challenge is confirmed on
the way (R0-23). Resolves round-01 T32, round-03 T23 and round-04 T31.

### R0-20 — The recovery override replaces the login email (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

The exceptional recovery override is an administrator action that replaces a
staff account's login email with a given address, sets its "email verified" mark (R0-23), and is
audited as `staff.recovery_override` atomically with the change; it is the
one operation that changes a login email, and an exceptional one (accepted
contract `perform_recovery_override`). No product operation recovers a sole administrator who has lost both password
and email: the bootstrap command of R0-07 refuses once any staff account
exists, and such a recovery stays a host-level operation outside the product
(owner 2026-11-06: current service behaviour accepted; technical decisions
delegated). Resolves round-01 T34.

### R0-21 — A producer reads its own import results (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

A producer reads an earlier import result by its `import_id`; the result is
returned only to the principal that made the import, and any other request is
answered as not found (accepted contract `get_snapshot_import_result`). The
read needs only the authenticated bearer credential of that principal: it
does not recheck the producer's project grant or the Registry lifecycle, so a
result stays readable after the grant is revoked or the project archived
(Factory code `application/snapshot_import.py`). Resolves round-01 T41 and
round-06 T6; where the `import_id` comes from is R0-25.

### R0-22 — Planned amounts are gross; `tax_mode` is provenance (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

A snapshot's planned amounts are already gross (IVA included); its `tax_mode`
is stored as provenance and never triggers recalculation (former State 1
decision 3, State 2 R9). Resolves round-01 T1.

### R0-23 — No staff email challenges and no email (owner 2026-11-07)

The owner decided on 2026-11-07 to remove the staff email challenge feature
because no email is ever needed (the decision in the owner's words:
`SOURCE.md`, deviation of 2026-11-07). The portal therefore has no email
verification, no email change confirmed at a new address, no password reset,
no security notification and no email delivery, and sends no email to any
address. A staff account's email is its login identifier only. The principals,
staff roles, staff login and logout, staff administration, viewers, producers
and the first-administrator command are unchanged.

A staff account keeps a recorded "email verified" mark: the administrator's
activation, the first administrator's creation (R0-07) and the recovery
override (R0-20) set it, and the account view shows it. The mark grants and
refuses nothing; an account signs in while it is active.

A staff member who has lost the password has no recovery inside the product:
the password changes only through its holder presenting the current one.

This replaces the decision of 2026-11-06 that kept the challenges as a
deferred feature (accepted spec sha256 `459ac96c…`, where they answered with
the concealed rejection and changed nothing) and closes `open_questions.md`
Q19.

### R0-24 — Archival freezes a project's records, not the revocation of access to it (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

An archived Registry project is readable and refuses every mutation of its
budget, snapshot import and activation, expense, document, progress, payment
and photo records (accepted `rules.registry_status_policy`: archived reads,
never mutates), with one named exception: a staff read of a project's
progress list, when the project has no manual budget version yet, creates
that empty manual budget version, also for an archived project (Factory code
`domain/project_tracking.py` 50–60, `api/router.py` 434–438); no other
operation changes the budget of an archived project. Grants and assignments belong to the project (R0-16) but are
access management, not these records: no new viewer grant, staff assignment
or producer grant is created for an archived project, because each creation
validates that the Registry reports the project as existing and active (the
answer's `exists` and `is_active` flags, which the Registry keeps in step
with its status; accepted notes
`grant_viewer_project`, `assign_staff_project`, `grant_producer_project`).
An existing grant or assignment is not new access: it keeps giving read
access, also after the viewer receives a new access link or the staff
account is reinstated, because neither operation consults the Registry
(accepted notes `issue_viewer_access`, `change_staff_status`). Revoking an
existing viewer grant, staff assignment or producer grant does not consult the
Registry and succeeds for an archived project, also while the Registry is
unavailable, so archival never stands in for revocation (accepted notes
`revoke_viewer_project`, `revoke_staff_project_assignment`; Factory code
`application/viewer_access.py`, `application/staff_identity.py`,
`application/service_identity.py`). Resolves round-04 T33 and round-05 T12, T13, T26.

### R0-25 — The portal assigns every `import_id` (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

The producer never supplies an `import_id`. Before the import, the import
route checks the producer's access: its authenticated bearer credential, its
scope and grant for the project, its capability, and that the Registry knows
the project as active. A refusal there — failed authentication, an unknown,
ungranted or archived project, a refused capability — is answered with that
access error and recorded nowhere (Factory code `api/router.py`
`publish_snapshot_endpoint`; accepted `rules.http_router_backend`). An
attempt the import classifies — accepted, idempotent replay, integrity
conflict, or a rejection — is recorded as a fresh immutable import result
with a fresh `import_id` and its `snapshot.import` audit; the import request
is answered with that result, never with the snapshot itself. An import
that fails before it classifies the attempt (a storage or Registry failure,
R6) is answered as that failure and records nothing, neither an import
result nor an audit record. How the import treats access that changes after the route's
check is the import operation's (State 4 `flow:import_estimate_snapshot`).
Recording access-refused attempts is a missing feature (Q20). A producer that lost an
answer re-publishes the same snapshot: identical content is answered as an
idempotent replay with a new `import_id` naming the same accepted snapshot
(accepted notes `_build_import_record`, `import_snapshot`; Factory code
`application/snapshot_import.py`). Resolves round-04 T40 and round-05 T9.

## Open questions

Recorded in `open_questions.md`; none is designed by this migration (owner,
2026-11-06). Q19, the email challenges, is closed by the owner's removal of
2026-11-07 (R0-23).

- Q10 — recovery after a lost one-time service credential response.
- Q11 — what turns an accepted snapshot into a candidate budget version for
  human activation.
- Q12 — the hand-over between the future intake service and the portal (the
  boundary itself is decided, R0-13).
- Q13 — listing a viewer's access codes (its premise is corrected; issuing a
  code already revokes the earlier ones).
- Q14 — replay-safe onboarding of a client.
- Q16 — the estimate box for the client's own chat agent.
- Q20 — recording snapshot import attempts the import route refuses on
  access (R0-25).
- Still open from the authoring pass of 2026-07-19: staff MFA; administrative
  area boundaries beyond the single current area; pagination beyond the few-project profile (R0-01); expense
  correction history beyond audit; `SnapshotImportRecord` retention; external
  binary deletion and retention.

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
