# State 0 — Cabinet Backend product boundary

## Status

Accepted product boundary corrected against Cabinet Invoice Card V1 and the
observed `registry_sandbox` contracts.

## Product statement

Cabinet Backend is the durable operational core of Cabinet. It validates and
stores structured Cards, relationships, sources, supplier purchases represented
by Invoice Cards, material lists, and their history in PostgreSQL.

Registry creates and identifies the platform project. Cabinet opens the same
project through a Work Object whose identity is the Registry `project_id`.
Cabinet obtains current project context through Registry in the same way as
other platform applications and stores the last successful context as a durable
read-only snapshot so the Web UI and conversational agents can continue working
when Registry is temporarily unavailable.

The normal purchase workflow is simple: the user buys materials in a shop or
online, normally pays at the time of purchase, and saves the invoice or receipt
as an Invoice Card. A purchase may use several payment transactions, such as
cash plus card. It may be assigned to one Work Object or remain without an
object.

## Sources of truth

| Concern | Authoritative owner | Cabinet treatment |
| --- | --- | --- |
| Platform project identity and current project context | Registry | Use `project_id` as Work Object identity and store a read-only durable snapshot. |
| Cabinet relationships, notes, purchases, material lists, documents, and history for that project | Cabinet | Own and persist independently of Registry availability. |
| Invoice Card identity, facts, lifecycle, sources, and payment evidence | Cabinet | Validate and persist in PostgreSQL. |
| Mutable estimate composition | PresuPro | Consume as plan input; never edit or silently call it approved. |
| Accounting document and accounting state | Holded | Access only through Holded Gateway. |
| Client-visible records | Client Portal | Send only through an agreed intake boundary. |

## Work Object boundary

A Work Object is Cabinet's local working interface for one Registry project.
It is not a separate project and has no additional Cabinet object identity:

```text
WorkObject.id = Registry ProjectRecord.id
```

The relationship is one Registry project to zero or one locally persisted Work
Object representation. Cabinet creates that representation lazily after it
receives `project_id` and successfully obtains the first Registry project
context. Repeated opening of the same `project_id` resolves to the same Work
Object.

Cabinet stores a durable snapshot of the returned Registry context, including:

- project ID;
- display name;
- address;
- Registry lifecycle status;
- customer reference;
- Registry creation time;
- Registry update time;
- Cabinet capture time.

Registry remains authoritative for these copied values. Ordinary Cabinet edits
and agents cannot rewrite them. Cabinet owns all project-scoped purchases,
material lists, documents, providers, contacts, notes, decisions, revisions,
and history.

When Registry is unavailable, an existing Work Object remains usable from its
last snapshot. Cabinet may display and search it, capture and review purchases,
assign purchases to it, and maintain Cabinet-owned knowledge. Cabinet must
show that the external context is stale or unavailable and must not claim that
the Registry project is currently active.

Cabinet cannot create a new Work Object from an unknown project ID without a
successful first Registry context read.

## Purchase without an object

Invoice Card identity is independent from Work Object identity. An Invoice Card
may be created before any project assignment exists.

The first product distinguishes:

- `unreviewed` — no assignment decision has been made;
- `assigned` — linked to one Work Object by Registry `project_id`;
- `intentionally_unassigned` — reviewed and deliberately left without an
  object;
- `label_only` — free-form source or user wording is preserved as a matching
  hint, but no Work Object is assigned.

A missing assignment never creates a synthetic Work Object. An Invoice Card may
be assigned later. One Invoice Card has at most one current primary assignment.
Multi-object and line-level allocation are deferred.

## Payment boundary

The normal workflow assumes immediate full payment. Split settlement is
represented by several transactions rather than a `mixed` method.

The complete implemented payment-status vocabulary is preserved:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `refunded`.

The first product does not introduce cross-invoice payments, bank
reconciliation, debt collection, or accounts-payable scheduling.

## Registry synchronization

Cabinet records the last successful snapshot and refresh evidence. The first
product distinguishes:

- `current` — the latest Registry read succeeded;
- `stale` — a snapshot exists but freshness is no longer confirmed;
- `unavailable` — the last refresh failed because Registry could not be
  reached;
- `not_found` — Registry explicitly reported that the project does not exist.

Registry status `active` or `archived` remains a separate value inside the
snapshot. Archived projects and their Cabinet data remain readable, but new
project-scoped assignment is rejected by default.

## Current Registry integration

Cabinet follows the existing platform pattern:

1. Registry launches Cabinet with `project_id`.
2. Cabinet requests `GET /projects/{project_id}/context`.
3. Cabinet creates or refreshes the local Work Object representation.
4. If Registry is unavailable later, Cabinet uses the stored snapshot.

The current sandbox does not yet enforce application registration, project
membership, service identity, or push notifications. These are future platform
contracts and are not required for the first Cabinet integration.

## Accepted product decisions

1. PostgreSQL is the selected durable Cabinet database.
2. Work Object identity is the Registry project UUID; no second Cabinet Work
   Object ID is introduced.
3. Work Object creation requires a successful first Registry context read.
4. Registry context is copied into a durable read-only snapshot for autonomous
   Cabinet UI and agent operation.
5. Registry remains authoritative for copied project fields.
6. Registry unavailability does not delete or invalidate an existing Work
   Object.
7. Invoice Cards have their own identity and may exist without a Work Object.
8. An Invoice Card may later be assigned to one Work Object by `project_id`.
9. One Invoice Card has at most one current primary assignment.
10. Multi-object and line-level allocation are deferred.
11. The complete payment vocabulary is preserved.
12. Several payment transactions may represent split settlement.
13. `draft`, `confirmed`, and `archived` are Invoice Card lifecycle states, not
    procurement or delivery states.
14. Cabinet uses the same Registry context-read pattern as other platform
    applications.

## State 0 readiness assessment

The product boundary is stable. State 1 may proceed using the domain models in
`01_models.md`.
