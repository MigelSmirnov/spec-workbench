# State 0 — Cabinet Backend product boundary

## Status

Accepted product boundary corrected against Cabinet Invoice Card V1 and the
observed `registry_sandbox` contracts.

## Product statement

Cabinet Backend is the durable operational core of Cabinet. An authorized user
or agent submits prepared working information; Cabinet validates and stores
structured Cards, relationships, sources, supplier purchases represented by
Invoice Cards, material lists, and their history in PostgreSQL.

Registry creates the platform project. Cabinet represents that project through
one autonomous Work Object containing Cabinet-owned working knowledge and a
durable copy of the last successfully observed Registry project context. This
replica allows the Cabinet Web UI and conversational agents to continue working
when Registry or the wider platform is temporarily unavailable.

The primary purchase workflow is simple: the user buys materials in a shop or
online, normally pays at the time of purchase, and saves the resulting invoice
or receipt as a Cabinet Invoice Card. One purchase may use more than one payment
method, for example cash and card. A purchase may be linked to one Work Object
or remain explicitly unassigned.

The agent performs extraction, normalization, matching suggestions, and other
heuristic work. Cabinet Backend remains the authority that decides whether
submitted Cabinet data is valid, current, non-duplicated, and safe to persist.

## Product position

Cabinet Backend replaces the current repository-backed Card storage mechanism;
it does not replace the accepted Cabinet Card concept, Registry project
identity, or the implemented Invoice Card V1 fact model.

It is not:

- a generic document database;
- a second Registry;
- a second PresuPro;
- an accounting ledger;
- an accounts-payable system;
- an inventory or procurement workflow;
- a Client Portal database;
- a passive proxy that accepts arbitrary agent JSON.

## Sources of truth

| Concern | Authoritative owner | Cabinet treatment |
| --- | --- | --- |
| Registry project UUID and current platform project context | Registry | Validate the project and persist a durable read-only snapshot for autonomous Cabinet operation. |
| Cabinet Work Object identity, alias, sync evidence, and operational relationships | Cabinet | Own and persist independently of Registry availability. |
| Cabinet Card identity, content, lifecycle, sources, and relationships | Cabinet | Validate and persist in PostgreSQL. |
| Supplier purchase and Invoice Card facts | Cabinet | Preserve structured facts, source provenance, revisions, confirmation, primary object assignment, and payment evidence. |
| Mutable presupuesto and estimate composition | PresuPro | Consume as plan input; never edit or silently call it approved. |
| Holded accounting document and accounting state | Holded | Access only through Holded Gateway and retain typed external links or receipts. |
| Client-visible budget, expenses, allocations, progress, and customer payments | Client Portal | Send only through an agreed intake boundary. |

## Work Object boundary

A Work Object is Cabinet's autonomous working representation of one Registry
project. It is created lazily after Cabinet receives a Registry `project_id`,
validates it, and obtains the first Registry project context.

The relationship is one Registry project to zero or one Cabinet Work Object.
The Work Object has its own stable Cabinet identity and stores
`registry_project_id` as a required unique external identity.

Cabinet copies the Registry project context into a durable snapshot containing
the values required by the Web UI and conversational agents, including project
name, address, Registry lifecycle status, customer reference, Registry creation
time, Registry update time, and Cabinet capture time.

Registry remains the source of truth for those copied fields. Ordinary Cabinet
operations and agents cannot silently edit them. Cabinet may separately own an
optional working alias and all Cabinet relationships, notes, invoices, material
lists, documents, providers, contacts, revisions, and history.

When Registry is unavailable, an existing Work Object remains usable. Cabinet
may display and search the object, capture and review purchases, assign
purchases to the already known Work Object, and maintain Cabinet-owned
knowledge. It must expose that the Registry snapshot may be stale and must not
claim that the external project remains current.

A new Work Object cannot be created from an unknown or unvalidated Registry
UUID. Invoice Cards may exist without a Work Object and must not cause creation
of a synthetic object.

## Registry synchronization

Cabinet records the last successful Registry snapshot and synchronization
evidence. The first product distinguishes:

- `current` — the latest Registry read succeeded;
- `stale` — a snapshot exists but freshness is no longer confirmed;
- `unavailable` — the last Registry refresh failed because the service could
  not be reached;
- `not_found` — Registry explicitly reported that the project does not exist.

Registry project status `active` or `archived` remains separate inside the
snapshot.

Temporary unavailability does not erase the last successful snapshot or
Cabinet-owned data. Archived Registry projects and their Work Objects remain
readable, but new operational assignment is rejected by default.

## Purchase and assignment boundary

One Invoice Card represents one supplier purchase or invoice. It preserves
supplier and buyer facts, document numbers and dates, normalized lines, source
wording, totals, payable amount, source evidence, payment evidence, and
`draft`, `confirmed`, or `archived` Cabinet lifecycle state.

One Invoice Card has at most one current primary object assignment in the first
complete product. Assignment is distinguishable as:

- not yet reviewed;
- assigned to one Work Object;
- intentionally unassigned;
- represented only by a free-form label until a Work Object is identified.

Multi-object and line-level allocations are deferred and do not belong to
Invoice Card V1 facts.

## Payment boundary

The normal user workflow assumes immediate full payment, including split
cash/card settlement represented by several payment transactions.

The backend preserves the complete implemented payment-status vocabulary for
source fidelity:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `refunded`.

The first product does not introduce a payment shared by several Invoice Cards,
bank reconciliation, accounts-payable scheduling, debt collection, or a
separate cross-invoice payment aggregate.

## Offline operation

While Registry is unavailable, Cabinet may use an existing Work Object snapshot
to:

- display and search project context;
- capture, review, and search invoices;
- assign invoices to the already known Work Object;
- maintain material lists, documents, providers, contacts, and notes;
- support agents with explicit stale-context evidence.

Cabinet may not:

- create a new platform project;
- create a new Work Object for an unvalidated project ID;
- edit Registry-owned snapshot fields;
- claim that stale Registry context is current;
- reactivate an archived Registry project.

## Current Registry limitation

The observed Registry sandbox implements project identity, lifecycle,
validation, launch context, and project-context reads. It does not yet
implement:

- registered application identity;
- project-to-application membership;
- Cabinet participation checks;
- attach/detach operations;
- service authentication;
- Registry events, subscriptions, or webhooks.

These are future platform contracts. Cabinet must not pretend that application
registration or participation is already enforced.

## Accepted product decisions

1. Cabinet Backend owns Cabinet operational Cards and cross-Card
   relationships.
2. PostgreSQL is the selected durable Cabinet database.
3. A Work Object is Cabinet's autonomous representation of exactly one Registry
   project.
4. A Work Object has its own stable Cabinet identity and one required unique
   `registry_project_id`.
5. Work Object creation requires a successful initial Registry validation and
   project-context read.
6. Registry project context is copied into a durable read-only snapshot for
   offline Cabinet UI and agent operation.
7. Registry remains authoritative for copied project identity fields.
8. Registry unavailability does not delete or invalidate an existing Work
   Object.
9. Invoice Cards may exist without a Work Object.
10. One Invoice Card has one primary object assignment in the first product.
11. A purchase may be explicitly unassigned and later assigned.
12. Multi-object and line-level allocation are deferred.
13. The normal purchase flow is immediate full payment.
14. The complete payment vocabulary `unknown`, `unpaid`, `partially_paid`,
    `paid`, and `refunded` is preserved.
15. Several payment transactions may represent split settlement such as cash
    plus card.
16. Draft, confirmed, and archived are Invoice Card lifecycle states, not
    procurement or delivery states.
17. Registry application registration, participation, service identity, and
    notifications are future platform contracts.
18. Holded integration remains a dedicated Gateway.
19. Client Portal publication remains explicit, versioned, and idempotent once
    the required external contracts exist.

## State 0 readiness assessment

The product boundary is stable. State 1 may proceed using the domain models in
`01_models.md`.
