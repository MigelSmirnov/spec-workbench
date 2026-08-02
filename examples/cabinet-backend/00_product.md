# State 0 — Cabinet Backend product boundary

## Status

Accepted product and deployment boundary corrected against Cabinet Invoice Card
V1, the observed Registry contracts, and the selected personal-platform
architecture.

## Product statement

Cabinet Backend is the durable operational core of Cabinet. It validates and
stores structured Cards, relationships, sources, supplier purchases represented
by Invoice Cards, material lists, accepted decisions, and history in PostgreSQL.

Cabinet is split across two trust zones:

```text
ChatGPT
  → Cabinet application and MCP boundary on VPS
  → authenticated private connection while the local platform is online
  → Cabinet Backend on the user's local machine
  → local PostgreSQL, source files, Registry, and PresuPro
```

ChatGPT and the conversational agent communicate only with Cabinet. Cabinet
Backend is not an MCP server and is not publicly exposed. Cabinet on the VPS is
the only remote client of Cabinet Backend.

The local Cabinet Backend and its PostgreSQL storage are the authoritative
Cabinet source of truth. Registry and PresuPro remain authoritative for their
own project and estimate data. The VPS does not become a second business-data
source of truth merely because it hosts the user-facing Cabinet application.

Registry creates and identifies the platform project. Cabinet opens the same
project through a Work Object whose identity is Registry `project_id`. Cabinet
Backend obtains project context from the local Registry and stores the last
successful context as a durable read-only snapshot.

The normal purchase workflow is simple: the user buys materials, normally pays
at purchase time, and saves the invoice or receipt as an Invoice Card. A
purchase may use several payment transactions and may be assigned to one Work
Object or remain without an object.

For a Registry-backed Work Object, Cabinet Backend may also load the detailed
PresuPro estimate. PresuPro remains the source of the plan; Cabinet uses the
estimate with Invoice Cards so the agent can compare expected and actual
purchases and calculate plan-versus-actual views on demand.

## Deployment and availability boundary

The VPS hosts:

- the user-facing Cabinet application;
- the Cabinet MCP/tool boundary;
- user session and connection state;
- only an explicitly selected minimal cache or transfer buffer.

The user's local platform hosts:

- Cabinet Backend;
- authoritative Cabinet PostgreSQL data;
- original invoice and document files unless a later private-store decision
  replaces local storage;
- Registry;
- PresuPro;
- local adapters used by Cabinet Backend.

The private connection may later be implemented by an overlay network such as
Tailscale, an SSH reverse tunnel, or an equivalent authenticated encrypted
transport. State 0 accepts the boundary, not one specific tunnel product.

When the local machine or private connection is unavailable, Cabinet must show
that the local platform is offline. In the first product, authoritative writes
are rejected rather than silently queued for later execution. Any VPS cache is
explicitly stale/read-only, preserves freshness evidence, and never becomes an
implicit second source of truth.

## Sources of truth

| Concern | Authoritative owner | Cabinet treatment |
| --- | --- | --- |
| Cabinet Cards, accepted relationships, decisions, sources, and history | Local Cabinet Backend | Persist in local PostgreSQL and local/private source storage. |
| Platform project identity and current project context | Registry | Read through local Backend using `project_id`; store a durable read-only snapshot. |
| Invoice Card identity, facts, lifecycle, sources, and payment evidence | Cabinet Backend | Validate and persist locally. |
| Mutable estimate composition, quantities, prices, zones, and totals | PresuPro | Read through local Backend as plan input; never edit or silently call mutable data approved. |
| Agent-proposed and user-confirmed invoice-line-to-estimate matches | Cabinet Backend | Preserve accepted decisions and provenance; suggestions alone are not facts. |
| Accounting document and accounting state | Holded | Publish one eligible confirmed Invoice Card through Holded Gateway. |
| User-facing remote session and MCP interaction | Cabinet VPS application | Authenticate interaction and expose narrow tools; do not own authoritative Cabinet data. |
| Client-visible records | Client Portal | Send only through an agreed intake boundary. |

## Cabinet-to-Backend boundary

Cabinet on the VPS is the sole remote Backend client. It does not receive raw
PostgreSQL, filesystem, Registry, or PresuPro access. The agent receives narrow
Cabinet capabilities rather than Backend, shell, database, or service
credentials.

Human authentication terminates at Cabinet on the VPS. The VPS-to-local link
uses separate machine identity. Cabinet Backend validates every accepted
command, including record state, revisions, scope, confirmation requirements,
and external effects.

No public ports are required for Cabinet Backend, PostgreSQL, Registry,
PresuPro, or original source files. Holded credentials remain inside Holded
Gateway.

## Work Object boundary

A Work Object is Cabinet's local working interface for one Registry project. It
is not a separate project and has no additional Cabinet object identity:

```text
WorkObject.id = Registry ProjectRecord.id
```

One Registry project has zero or one locally persisted Work Object
representation. Cabinet Backend creates it lazily after receiving `project_id`
and successfully obtaining the first Registry project context. Reopening the
same `project_id` resolves to the same Work Object.

Cabinet stores a durable Registry snapshot containing project ID, display name,
address, lifecycle status, customer reference, Registry timestamps, and Cabinet
capture time. Registry remains authoritative for copied values. Ordinary
Cabinet edits and agents cannot rewrite them.

When Registry is unavailable but Cabinet Backend remains online, an existing
Work Object remains usable from its last snapshot. Cabinet cannot create a new
Work Object from an unknown project ID without a successful first Registry read.

## Purchase without an object

Invoice Card identity is independent from Work Object identity. An Invoice Card
may be created before project assignment.

The first product distinguishes:

- `unreviewed`;
- `assigned`;
- `intentionally_unassigned`;
- `label_only`.

A missing assignment never creates a synthetic Work Object. One Invoice Card
has at most one current primary assignment. Multi-object allocation is deferred.

## PresuPro contract and plan-versus-actual

For the selected `project_id`, Cabinet Backend must be able to obtain detailed
PresuPro plan data including source identity or freshness, zones, positions,
item kind, name, material reference when present, quantity, unit, unit price,
waste, margin, discount, IVA, and calculated totals.

Cabinet Invoice Line fields are intentionally aligned with comparable PresuPro
item fields. Product names may differ between retailers, so semantic
equivalence belongs to the agent:

```text
PresuPro estimate item
+ Cabinet invoice line
→ agent proposes semantic equivalence
→ user confirms, rejects, or corrects when needed
→ Cabinet Backend may retain the accepted match
→ agent calculates plan-versus-actual on demand
```

Suggested matches never affect calculations until accepted. In the baseline,
one Invoice Line matches at most one estimate item, while several Invoice Lines
may match one estimate item. Partial distribution of one line across several
estimate items is deferred.

Derived analysis may include planned versus actual unit price, actual and
remaining quantity, planned versus actual amount, average actual unit price,
forecast final cost with an explicit basis, unmatched items, and variance by
item, zone, or Work Object. These results are not durable Invoice Card facts.

## Holded publication

A confirmed eligible Invoice Card may be published as one accounting document
through Holded Gateway. Cabinet Backend decides business eligibility and fixes
the exact Invoice Card revision. Holded Gateway owns credentials, provider
transport, retries, reconciliation, and technical receipts.

Holded publication is independent from PresuPro matching and analytics.

## Payment boundary

The normal workflow assumes immediate full payment. Split settlement is
represented by several transactions rather than a `mixed` method.

The accepted payment-status vocabulary is:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `refunded`.

The first product does not introduce cross-invoice payments, bank
reconciliation, debt collection, or accounts-payable scheduling.

## Registry synchronization

Cabinet records the last successful snapshot and refresh evidence:

- `current`;
- `stale`;
- `unavailable`;
- `not_found`.

Registry lifecycle status remains separate. Archived projects and their Cabinet
data remain readable, but new project-scoped assignment is rejected by default.

## Current integration flow

1. The user opens Cabinet on the VPS.
2. Cabinet establishes the authenticated private connection to the local
   Cabinet Backend when the local platform is online.
3. Registry launch or selection provides `project_id` through the local platform
   boundary.
4. Cabinet Backend requests Registry project context and creates or refreshes the
   Work Object.
5. Cabinet Backend may obtain the PresuPro estimate for the same project.
6. Cabinet returns only the required structured result to the VPS application.
7. If the local platform is offline, Cabinet rejects authoritative operations
   and may show only explicitly cached stale/read-only context.

The current sandboxes do not yet enforce production service identity or project
membership. Their absence does not define the production security model.

## Accepted product and architecture decisions

1. Cabinet application and MCP boundary run on the VPS.
2. Cabinet Backend, authoritative PostgreSQL data, original source files,
   Registry, and PresuPro run in the user's local platform trust zone.
3. Cabinet VPS is the only remote client of Cabinet Backend.
4. ChatGPT and the agent never connect directly to Cabinet Backend.
5. Backend, PostgreSQL, Registry, PresuPro, and source files are not publicly
   exposed.
6. VPS-to-local communication uses authenticated encrypted private transport.
7. The local platform is intentionally connect-on-demand.
8. Authoritative writes are rejected, not silently queued, while the local
   Backend is offline in the first product.
9. The VPS is not a second source of truth; any cache is explicit, minimal,
   stale-labelled, and revocable.
10. Cabinet Backend validates persisted changes and external effects even when
    requests originate from an authenticated Cabinet session.
11. Work Object identity is Registry project UUID; no second Cabinet Work Object
    ID is introduced.
12. Work Object creation requires a successful first Registry context read.
13. Registry context is copied into a durable read-only local snapshot.
14. Invoice Cards have their own identity and may exist without a Work Object.
15. One Invoice Card has at most one current primary assignment.
16. Multi-object allocation is deferred.
17. PresuPro is authoritative for plan data.
18. Product-name matching is heuristic work owned by the agent.
19. Suggested matches do not affect calculations until accepted.
20. One Invoice Line matches at most one estimate item in the baseline; many
    Invoice Lines may match one estimate item.
21. Plan-versus-actual results are calculated on demand.
22. A confirmed eligible Invoice Card may be published independently through
    Holded Gateway.
23. Holded credentials remain inside Holded Gateway.
24. The complete payment vocabulary is preserved.
25. `draft`, `confirmed`, and `archived` are Invoice Card lifecycle states.

## State 0 readiness assessment

The product, deployment, trust, and source-of-truth boundaries are stable enough
for State 1 domain work. Detailed tunnel technology, cache policy, local backup,
VPS session implementation, service credentials, and operational recovery
remain explicit security questions rather than undefined defaults.
