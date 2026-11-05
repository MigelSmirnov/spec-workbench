# Client Portal Open Product Questions

## Status

**Open; no decision is made by this requirements baseline**

1. What is the complete lifecycle of an approved presupuesto, including the
   point of immutability, replacement, withdrawal, and retention?
2. What is the detailed relationship between an approved presupuesto and a
   factura, given that approval and invoice creation are distinct facts?
3. Which actor or external system is authorized to publish an approved
   presupuesto to Client Portal?
4. How are approved snapshots versioned, selected, superseded, retained, and
   addressed?
5. How does a project move from a manual portal budget to an imported approved
   snapshot without losing history or misrepresenting existing data?
6. Who has authority to approve a presupuesto for client publication, and what
   future approval workflow supplies that decision?
7. Does Client Portal need a separate client-access close or revoke action in
   addition to Registry archival?
8. How are changes in a later approved presupuesto reflected when the portal
   already contains Expenses, allocations, progress, and payments?
9. How are internal PresuPro zones mapped to stable client-facing Budget
   Sections?

## Operational questions discovered after the baseline

### Q10 — Recovery after one-time service credential delivery is lost

Observed on 2026-11-04 while onboarding the PresuPro estimate producer for
`Proyecto Demo Facebook`:

- creating a service principal succeeds independently of credential issuance;
- credential issuance persists an active credential and returns its plaintext
  exactly once;
- the administrative HTTP surface exposes create, issue, revoke, grant and
  status-change operations, but no operation to list or read service
  principals and their non-secret credential metadata;
- if the response is lost, or the operator fails after issuance but before
  durably recording `principal_id` and `credential_id`, the plaintext is
  correctly unrecoverable, yet the administrator also cannot address the
  unknown active credential through the supported HTTP API to revoke it.

Questions requiring an explicit product/security decision:

1. Must the administrative API expose a list/read projection for service
   principals, credential metadata, and producer grants so an administrator
   can locate and revoke an orphaned credential?
2. Should credential issuance require an operator-supplied idempotency key or
   a prepare/confirm protocol, or is recovery by listing metadata and rotating
   credentials sufficient?
3. Must the one-time-secret response contract be shared by operator tooling so
   a response-shape mismatch cannot silently strand an active credential?
4. What recovery procedure and audit evidence are required when principal
   creation and credential issuance succeed but local secret custody fails?

Until this is decided, an operator must not blindly repeat principal or
credential creation after an ambiguous or lost response. The incident must be
reconciled and the orphaned credential revoked through an authorized
administrative recovery procedure first.

### Q11 — Accepted snapshot cannot reach human activation

Observed on 2026-11-04 with the accepted PresuPro snapshot for `Proyecto Demo
Facebook`:

- `snapshot.publish` accepted and durably stored the immutable snapshot;
- the accepted import deliberately does not create `PortalSection`,
  `SectionPlan`, or `BudgetVersion` records;
- `activate_budget_version` requires an already existing `version_id` and is
  correctly restricted to a human staff capability;
- no public operation materializes an accepted snapshot into an inactive
  candidate BudgetVersion for that human to review and activate.

Which boundary owns materialization?

1. Does an accepted import atomically create an inactive snapshot-backed
   BudgetVersion and its stable sections/plans, while leaving activation to a
   human?
2. Or must staff explicitly call a separate idempotent "prepare budget from
   snapshot" operation before activation?
3. What identity makes materialization replay-safe, and what happens when the
   active manual budget already has progress, allocations, expenses, and
   payments?

Until this is decided, a kernel scenario may publish and report an accepted
snapshot, but must not claim that the client-visible budget was updated.

### Q12 — The binary intake the design relies on was never built

`spec/30_modules.md` (State 3, "Binary storage boundary") makes
`binary_storage` an opaque read boundary: "OCR/Telegram intake remains
responsible for placing the binary and supplying a stable reference; the
portal does not become an upload or recognition system." No such intake
exists.

Observed on 2026-11-05 while giving the client of the Registry project
`52b132d7-0a94-44e7-9aab-63a77ca770f2` (Ponent 13) access with three progress
photos:

- `photo.publish` correctly accepts only a `file_ref` and is replay-safe by
  `intake_id`;
- the bytes behind that `file_ref` were placed by an operator over SSH and
  `docker cp` into the portal binary volume, outside every declared surface;
- expense documents arrive the same way through `tools/portal_import` (an
  operator package copied into the container);
- the owner's workplace (cabinet_kernel on the owner's PC) reaches the portal
  only over HTTPS and therefore cannot supply a photo at all.

Owner decision 2026-11-06: **keep the State 3 decision.** The portal stays a
read boundary for binaries; a separate intake service places binaries and
supplies references. Uploading into the portal itself was considered and
rejected as the larger architectural change.

Questions this leaves to the portal contract:

1. How does the intake service hand a placed binary to the portal: a shared
   binary store the portal reads, or a portal-owned "accept reference"
   operation that verifies existence, size and media type before any record
   points at it?
2. Who owns the `file_ref` namespace (`photos/<project_id>/…`,
   `expenses/…`), and may two services write into it?
3. Which principal calls `photo.publish` and expense intake for intake-placed
   binaries: the staff member, or a `ServicePrincipal` with an intake-only
   capability and project grants (as for snapshot producers)?
4. What does the portal do with a `file_ref` whose bytes are absent, replaced,
   or larger than `binary_max_read_bytes`?
5. What is `intake_source` for the new path, and is it a closed vocabulary?

Until this is decided, operator placement stays the declared temporary route,
marked as outside the API in `platform/manifest/client_portal.json`.

### Q13 — A viewer's access codes cannot be listed

Observed on 2026-11-05 for viewer `9636b10b-f170-465d-8cf7-fd0c75bc2842`: the
one-time access code was shown once and missed by the owner; a new code was
issued. `viewer.issue_credential` leaves older codes valid until revoked, but
the API exposes no list or read of a viewer's credentials, so the old
`credential_id` could only be found by reading the portal database.

1. Must the administrative API expose a read projection of a viewer's
   credential metadata (id, created_at, revoked_at; never the secret)?
2. Should issuing a code for a viewer optionally revoke that viewer's previous
   active codes in the same transaction?
3. Is this one decision with Q10 (service credentials), i.e. one recovery
   model for every one-time secret?

### Q14 — Onboarding a client is not replay-safe

`viewer.create` has no key and no list route for a project's viewers;
`budget.put_section` without a `section_id` creates a new section on every
call; replay of `budget.open_manual` and `budget.activate` is unverified.
On 2026-11-05 the operator tooling had to guard these by intent flags and by
looking up its own section by display name.

1. Must a project's viewers be listable (display name, status, grant), so a
   tool can ask whether a client already has access?
2. Does a manual budget section need a caller-supplied stable key, like
   `source_key` for imported snapshots, instead of the display name?
3. What is the intended replay behaviour of opening and activating a manual
   budget version?

### Q15 — Review of the case against the current Workbench standard

Recorded 2026-11-06. The case predates the current authoring standard:

- the Workbench gateway reports State 1 as "not indexed as canonical models"
  and cannot read the case text (`design_context`, `find_absence` fail);
- `90_factory_target.json` is absent, so the case names no Factory project,
  and Factory `client_portal_sandbox` names no Workbench case;
- the Factory spec was accepted on 2026-08-17 (32 inspector WARN, 456
  partially parsed or unparsed notes, OTK verdict WARN);
- this branch and `origin/product-decisions-and-reassembly` have diverged.

Before Q11–Q14 or new functionality are designed, the case must be migrated to
the current standard and linked to its Factory project, so that portal changes
can follow the Workbench → Factory route.

### Q16 — Estimate capability box for the client's own chat agent

Owner requirement 2026-11-06. For every accepted estimate version the client
can download, from the cabinet, an **estimate box**: one self-describing
package the client hands to their own chat agent (ChatGPT or similar) to get
explanations and reports in the form they want. It is the counterpart of the
Cabinet Estimator Box (`box_index`, `scope_manifest`, `agent_task_markdown`),
which prepares an estimate; this box follows an accepted one and carries no
open uncertainty.

Intended content (to be closed in State 1):

- the accepted estimate version: zones, lines, quantities, units, unit prices,
  IVA rate and amounts, totals;
- the owner's open-book model (owner, 2026-11-06): materials carry their
  purchase price and a disclosed margin of 5–10 %, and every purchase invoice
  of the object is listed with its amount and a reference the client can open
  in the cabinet;
- provenance: Registry project, PresuPro estimate id and revision, acceptance
  date, the Holded invoice reference when one exists;
- verification facts: what was checked and how (estimate accepted, totals
  recomputed and equal, IVA rates supported, invoice issued from this
  version, purchases reconciled against the plan by Cabinet: bought outside
  the plan, planned but not bought, net variance), each as data, not prose;
- an agent guide: what the box is, how to read it, what is verified, what is
  not (no legal or tax advice, no recomputation under other rules), and the
  contact for questions;
- a content hash over everything above.

It is produced by a cabinet_kernel scenario: read the accepted PresuPro
estimate → a pure, admitted function builds the box → publish to the portal
as a producer. The same input yields the same box and the same hash.

Questions for the portal:

1. Where does the box live: inside the immutable snapshot (Q11), as its own
   versioned record next to it, or as an ExpenseDocument-like downloadable
   document? A JSON record avoids the binary intake of Q12.
2. Open book is the rule, so purchase prices, margins and invoices are in the
   box. What still stays out, and who decides it per field: supplier account
   or contact data on invoices, internal notes, labour cost breakdown, store
   links? How is a purchase invoice referenced so that the box and the
   cabinet's ExpenseDocument show the same document (same hash)?
3. Visibility: a box becomes client-visible only after a staff decision, like
   photos and documents, or on publication?
4. Download contract for viewers: format (one Markdown file with an embedded
   JSON block, or an archive), media type, file name, and whether earlier
   versions stay downloadable after a later one is accepted.
5. The guide is text the portal hands to a third-party agent. What keeps it
   descriptive only — generated from data by the admitted function, never
   free text from staff — so that the box cannot instruct the client's agent
   beyond explaining the estimate?
6. Personal data: the client's own name, NIF and address may be in the box;
   nothing about other clients, staff accounts or internal notes may.
