# State 0 — Cabinet Backend product boundary

## Status

Accepted product, deployment, trust, and availability boundary.

## Product statement

Cabinet is an AI-assisted personal working system. The user communicates
naturally; the agent organises incoming information; Cabinet preserves the
sources and stores structured, searchable knowledge about purchases, documents,
suppliers, material lists, work objects, and related decisions.

Cabinet is split across two cooperating runtimes because the local working
platform is normally unavailable during the day:

```text
ChatGPT
  → Cabinet application and MCP boundary on VPS
     → continuously available invoice and working-information workspace
     → cached Registry object catalogue
     → authenticated private synchronization
  → Local Cabinet Backend
     → complete PostgreSQL archive and durable source storage
     → Registry, PresuPro, and controlled external integrations
```

ChatGPT and the agent communicate only with Cabinet. Neither receives direct
access to PostgreSQL, local files, Registry, PresuPro, Holded credentials, or a
generic backend API.

## Primary-source boundary

The primary evidence for a purchase is the paper invoice or receipt, a photograph
of it, or a received PDF.

A stored source file is immutable. Cabinet never rewrites it to reflect OCR
corrections or later working decisions.

Cabinet may:

- attach several photographs or files representing the same document;
- extract structured facts from those sources;
- correct and confirm its interpretation of the source;
- preserve the history and provenance of those corrections;
- create or change Cabinet-owned relationships such as object assignment,
  estimate matching, notes, and publication state.

A correction changes Cabinet's understanding, not the original invoice.

## Two-tier Cabinet boundary

### VPS Cabinet

The VPS is continuously available and owns the daytime working lifecycle of
newly captured invoices until they are durably synchronized locally. It may:

- accept invoice photographs and PDFs;
- preserve each received original in protected working storage;
- create a stable `invoice_id` immediately;
- extract, review, correct, confirm, search, and discuss fresh Invoice Cards;
- show a cached catalogue of Registry work objects with freshness information;
- assign a fresh invoice to an object from that cached catalogue;
- retain source evidence, interpretation history, assignment decisions, and
  synchronization evidence;
- synchronize the work to the local Backend when the local platform connects.

The VPS is not merely an upload buffer. It is the usable Cabinet workspace while
the local platform is offline.

### Local Cabinet Backend

The local Backend is the complete durable archive and platform-integration
boundary. It owns:

- the complete Cabinet PostgreSQL archive;
- long-term source-file storage;
- historical Cards, relationships, and decision history;
- versioned Registry object snapshots;
- publication of a compact Registry object catalogue to the VPS;
- validation of assignments made from cached Registry data;
- PresuPro estimate snapshots and accepted matches;
- complete project analytics;
- Holded publication state and other external integration evidence.

Registry and PresuPro remain authoritative for their own object and estimate
data.

## Registry object availability

Registry owns work-object identity and current context:

```text
WorkObject.id = Registry ProjectRecord.id
```

When the local platform is connected, the local Backend reads Registry objects,
stores versioned snapshots, and sends a compact object catalogue to the VPS.

The VPS catalogue exists specifically so Cabinet can work during the normal
offline period. It contains enough information to identify and select an object,
for example:

- `project_id`;
- display name;
- address or short context;
- status;
- Registry version or content hash;
- snapshot capture time.

A user may assign a fresh invoice to an object from this cached catalogue while
the local platform is offline. The assignment is a real Cabinet decision, not
merely a free-text suggestion, but it is marked as based on a specific cached
Registry snapshot.

After reconnection, the local Backend validates the selected `project_id` against
current Registry data. If the object is missing, closed, or materially changed,
Cabinet preserves the earlier choice and raises a warning instead of silently
removing or replacing it.

An invoice may also remain intentionally unassigned.

## Invoice identity and interpretation

One Invoice Card has one stable logical identity across VPS and local storage.
The `invoice_id` created at first capture survives synchronization.

The model distinguishes:

- immutable source artifacts — photographs and PDFs;
- extraction attempts — machine interpretations of those sources;
- confirmed invoice facts — the accepted Cabinet understanding of what the
  document says;
- Cabinet decisions — object assignment, estimate matching, notes, and
  publication state;
- storage copies and synchronization evidence.

Confirmed facts may be corrected when Cabinet previously misunderstood the
source. The old interpretation remains in history; the source itself does not
change.

## Normal operating cycle

```text
local platform connects
→ refresh Registry object snapshots
→ publish compact object catalogue to VPS

local platform goes offline
→ user photographs invoices during the day
→ Cabinet extracts and confirms facts
→ user selects cached Registry objects where appropriate

local platform connects later
→ idempotently transfer originals, interpretations, confirmations, and decisions
→ durably accept the same invoice_id in the local archive
→ validate cached object assignments against current Registry data
→ enable PresuPro matching, complete analytics, and local integrations
```

A timeout must not create a duplicate Invoice Card. VPS source deletion or expiry
may occur only after durable local acceptance and according to retention policy.

## Availability behavior

### Local platform offline

Available:

- source capture and preservation;
- OCR and extraction;
- correction and confirmation of invoice facts;
- search and discussion inside the VPS working set;
- browsing the cached Registry object catalogue;
- assigning an invoice to a cached object;
- intentionally leaving an invoice unassigned.

Unavailable or limited:

- current Registry refresh and current-status guarantees;
- current PresuPro estimate retrieval;
- full historical search outside the VPS working set;
- complete plan-versus-actual analysis;
- durable estimate matching against local project data;
- local integration actions such as Holded publication.

### Local platform connected

Cabinet refreshes object data, validates cached assignments, downloads fresh
invoice work, and makes full archive, PresuPro, analytics, and integration
functions available.

## Sources of truth

| Concern | Authoritative owner | Cabinet treatment |
| --- | --- | --- |
| Original paper document | External real-world source | Preserve received photos or PDFs as immutable evidence. |
| Received source file before local acceptance | VPS Cabinet | Protect and use it until durable transfer. |
| Complete durable source archive | Local Cabinet Backend | Store and verify long term. |
| Cabinet interpretation and confirmation of invoice facts | Cabinet | Preserve corrections, confirmation, and provenance. |
| Work-object identity and current context | Registry | Cache versioned snapshots locally and on VPS. |
| Offline invoice-to-object assignment | Cabinet, based on cached Registry snapshot | Permit immediately; validate after reconnection. |
| Mutable estimate composition | PresuPro | Retain versioned snapshots for matching and analysis. |
| Accepted invoice-line-to-estimate matches | Local Cabinet Backend | Preserve decisions and provenance. |
| Accounting document and accounting state | Holded | Publish through Holded Gateway. |
| User session and MCP interaction | Cabinet VPS | Authenticate interaction and expose narrow tools. |

## PresuPro and plan-versus-actual

The local Backend obtains detailed PresuPro plan data for a `project_id`,
including zones, positions, quantities, units, prices, waste, margin, discount,
IVA, and totals.

Invoice Line meanings remain comparable with PresuPro Estimate Item meanings.
Semantic equivalence across retailers belongs to the agent. Suggested matches
affect analysis only after acceptance.

In the baseline:

- one Invoice Line has at most one active Estimate Item match;
- many Invoice Lines may match one Estimate Item;
- splitting one line across several estimate items is deferred;
- plan-versus-actual and forecasts are calculated on demand.

## Holded publication

One eligible set of confirmed invoice facts may be published through Holded
Gateway. The local Backend owns business eligibility and publication evidence;
Holded Gateway owns credentials, transport, retries, reconciliation, and
technical receipts.

Publication is independent from PresuPro matching.

## Security boundary

- The local Backend, PostgreSQL, Registry, PresuPro, and local durable files are
  not publicly exposed.
- VPS-to-local synchronization uses authenticated encrypted private transport.
- The VPS protects invoice originals, extracted fiscal data, and the cached
  Registry object catalogue.
- User authentication terminates at Cabinet VPS; machine identity separately
  authenticates synchronization.
- The agent receives narrow Cabinet tools, never raw storage or service
  credentials.
- Source hashes, idempotency, confirmation, assignment provenance, and
  authorization are enforced at their owning boundaries.

## Accepted decisions

1. Cabinet is a general personal working assistant; invoice capture is one core
   workflow inside it.
2. The local platform is normally unavailable during daytime field work.
3. Cabinet VPS remains useful and authoritative for fresh unsynchronized work.
4. Original photographs and PDFs are immutable source evidence.
5. Cabinet may correct its extraction and interpretation without changing the
   source.
6. A stable `invoice_id` is created at first capture and survives synchronization.
7. Registry owns work-object identity and current context.
8. The local Backend publishes a versioned compact Registry object catalogue to
   the VPS.
9. Users may assign fresh invoices to cached Registry objects while offline.
10. Cached assignments are validated after local reconnection; invalidation does
    not silently erase the original user decision.
11. Invoice Cards may remain intentionally unassigned.
12. Synchronization transfers sources, interpretation history, confirmations,
    assignments, and provenance idempotently.
13. The local Backend is the complete durable archive and integration boundary.
14. Full PresuPro, historical analytics, and durable matching require the local
    Backend.
15. Product matching is heuristic agent work; accepted matches are Cabinet
    decisions.
16. Plan-versus-actual results are derived on demand.
17. Holded publication remains a separate controlled integration.

## State 0 readiness assessment

The product boundary now reflects the real operating cycle: Registry objects are
cached before disconnection, invoices are captured and assigned on the VPS during
the day, and all new work is transferred and validated when the local platform
connects later.

State 1 must model immutable source evidence, extraction and correction history,
confirmed invoice facts, cached Registry catalogues, offline assignment
provenance, post-reconnection validation, and idempotent transfer to the durable
local archive.
