# State 0 — Cabinet Backend product boundary

## Status

Accepted product, deployment, trust, and availability boundary.

## Product statement

Cabinet is an AI-assisted working system for invoices, documents, suppliers,
material lists, project context, and plan-versus-actual analysis. It is split
across two cooperating Cabinet runtimes rather than one always-online backend.

```text
ChatGPT
  → Cabinet application and MCP boundary on VPS
     → VPS Invoice Workspace for fresh invoices
     → authenticated private synchronization
  → Local Cabinet Backend
     → local PostgreSQL and durable source files
     → local Registry and PresuPro
```

ChatGPT and the agent communicate only with Cabinet. Neither receives direct
access to PostgreSQL, local files, Registry, PresuPro, Holded credentials, or a
generic backend API.

## Two-tier Cabinet boundary

### VPS Cabinet

The VPS is continuously available and owns the working lifecycle of newly
captured invoices until they are durably synchronized locally. It may:

- accept invoice photographs and PDFs;
- preserve the received original in protected VPS storage;
- create a stable `invoice_id` immediately;
- extract, validate, edit, search, discuss, and confirm a fresh Invoice Card;
- retain its revisions and synchronization evidence;
- expose narrow Cabinet tools to the agent;
- synchronize the same logical Invoice Card to the local Backend when the local
  platform is available.

This is not merely a temporary upload buffer. A fresh invoice must remain useful
while the local platform is offline.

### Local Cabinet Backend

The local Backend is the durable full-system archive and platform-integration
boundary. It owns:

- the complete Cabinet PostgreSQL archive;
- long-term source-file storage;
- historical Cards and relationships;
- Work Objects and Registry snapshots;
- PresuPro estimate snapshots and accepted matches;
- complete project analytics;
- Holded publication state and other external integration evidence.

Registry and PresuPro remain authoritative for their own project and estimate
data.

## Logical identity and authority

One Invoice Card has one stable logical identity across VPS and local storage.
The `invoice_id` created on the VPS is preserved during synchronization.

Authority is revision-scoped:

- before first successful synchronization, the VPS copy is authoritative for
  that fresh invoice;
- after synchronization, the local Backend is the durable archive and primary
  owner;
- in the first product, a synchronized VPS invoice becomes read-only or follows
  an explicit checked-out revision policy; unrestricted two-way editing is not
  assumed;
- neither side silently overwrites a newer revision on the other side.

The VPS is therefore an authoritative workspace for unsynchronized fresh
invoices, but not a complete second copy of all Cabinet business data.

## Invoice synchronization

The normal fresh-invoice flow is:

```text
capture on VPS
→ create stable Invoice Card draft
→ review and confirm source facts
→ sync_state = remote_only
→ local platform connects
→ idempotent transfer of original plus revisions
→ local Backend validates and accepts the same invoice_id
→ sync_state = synchronized
```

Every transfer is revision-aware and idempotent. A timeout must not cause a
second Invoice Card to be created. The VPS deletes or expires its stored source
only after durable local acceptance and according to the retention policy.

## Availability behavior

When the local platform is offline, Cabinet still supports fresh-invoice work:

- capture and source preservation;
- OCR/extraction;
- draft creation and correction;
- confirmation of invoice facts;
- search and discussion among invoices retained in the VPS working set.

The following remain unavailable or explicitly limited until local connection:

- validated Registry Work Object creation or assignment;
- current PresuPro estimate retrieval;
- full historical search outside the VPS working set;
- complete project plan-versus-actual analysis;
- durable estimate matching against local project data;
- Holded publication when that action is owned by the local integration path.

Cabinet may preserve a label or assignment suggestion while offline, but it must
not claim a validated Registry assignment without the local Registry boundary.

## Sources of truth

| Concern | Authoritative owner | Cabinet treatment |
| --- | --- | --- |
| Unsynchronized fresh Invoice Card and its received original | VPS Invoice Workspace | Work with it fully until local acceptance. |
| Synchronized and historical Cabinet archive | Local Cabinet Backend | Persist in local PostgreSQL and durable source storage. |
| Platform project identity and current project context | Registry | Read through local Backend using `project_id`; retain a read-only snapshot. |
| Mutable estimate composition and plan calculations | PresuPro | Read through local Backend; retain observed version evidence for matches and analysis. |
| Accepted invoice-line-to-estimate matches | Local Cabinet Backend | Preserve decisions and provenance. |
| Accounting document and accounting state | Holded | Publish through Holded Gateway. |
| User session and MCP interaction | Cabinet VPS | Authenticate the user-facing interaction and expose narrow tools. |

## Work Object boundary

A Work Object is Cabinet's local working interface for one Registry project:

```text
WorkObject.id = Registry ProjectRecord.id
```

One Registry project has at most one persisted Work Object. Initial creation
requires a successful Registry context read through the local Backend.

Invoice identity is independent from Work Object identity. A fresh VPS invoice
may remain `unreviewed`, `intentionally_unassigned`, or `label_only` until the
local platform validates an `assigned` state.

## PresuPro and plan-versus-actual

The local Backend obtains detailed PresuPro plan data for a `project_id`,
including zones, positions, quantities, units, prices, waste, margin, discount,
IVA, and totals.

Invoice Line fields remain intentionally comparable with PresuPro Estimate Item
fields. Semantic equivalence across retailers belongs to the agent. Suggested
matches affect analysis only after acceptance.

In the baseline:

- one Invoice Line has at most one active Estimate Item match;
- many Invoice Lines may match one Estimate Item;
- partial distribution of one line across several estimate items is deferred;
- plan-versus-actual and forecasts are calculated on demand.

## Holded publication

One eligible confirmed Invoice Card revision may be published through Holded
Gateway. The local Backend owns business eligibility and publication evidence;
Holded Gateway owns credentials, transport, retries, reconciliation, and
technical receipts.

Publication is independent from PresuPro matching.

## Security boundary

- Cabinet Backend, PostgreSQL, Registry, PresuPro, and local durable files are
  not publicly exposed.
- VPS-to-local synchronization uses authenticated encrypted private transport.
- The VPS protects invoice originals and structured fiscal data because it now
  holds real working records.
- User authentication terminates at Cabinet VPS; machine identity separately
  authenticates VPS-to-local synchronization.
- The agent receives narrow Cabinet tools, never raw storage or service
  credentials.
- Revision checks, idempotency, confirmation requirements, and authorization are
  enforced at each owning boundary.

## Accepted decisions

1. Cabinet VPS remains useful when the local platform is offline.
2. New invoices may be captured, reviewed, confirmed, searched, and discussed on
   the VPS.
3. A stable `invoice_id` is created at first capture and survives synchronization.
4. The VPS is authoritative for an unsynchronized fresh Invoice Card revision.
5. The local Backend is the complete durable archive and platform-integration
   boundary after synchronization.
6. Synchronization transfers the original, structured facts, revisions, and
   provenance idempotently.
7. Synchronized VPS records are not freely edited in two places in the baseline.
8. Full Registry, PresuPro, historical analytics, and durable project matching
   require the local Backend.
9. No public local Backend, PostgreSQL, Registry, or PresuPro ports are required.
10. Work Object identity equals Registry `project_id`.
11. Invoice Cards may exist without a Work Object.
12. Product matching is heuristic agent work; accepted matches are Cabinet
    decisions.
13. Plan-versus-actual results are derived on demand.
14. Holded publication remains a separate controlled integration.

## State 0 readiness assessment

The two-tier product and trust boundary is accepted. State 1 must model remote
invoice authority, synchronization, revision ownership, source retention, local
connection state, and conflict behavior alongside the existing Cabinet domain.
