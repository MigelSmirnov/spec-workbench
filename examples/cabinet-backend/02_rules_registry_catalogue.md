# State 2 — Registry catalogue and offline object rules

## Status

Accepted baseline rules for publishing Registry project context to the VPS and
using it while the local platform is unavailable.

This state defines invariants and policy. It does not define modules, endpoints,
SQL tables, transport payloads, or implementation sequencing.

## Confirmed external boundary

Registry is authoritative for project identity and current project context.
The current Registry contract provides:

- `project_id` as a UUID serialized as a JSON string;
- `display_name` for compact presentation;
- `address`;
- optional opaque `customer_ref`;
- `created_at`;
- `registry_updated_at`;
- project status `active` or `archived`;
- `GET /projects/active` for the current active-project list;
- project context and validation lookups by project ID.

Registry currently has no project revision number, content hash, `closed` status,
`deleted` status, or historical project-version log.

---

# A. Catalogue content

## Rule A1 — Active catalogue source

The normal VPS catalogue is built from Registry's current active-project list.

The catalogue MUST NOT infer active projects by filtering arbitrary cached data
when a successful current Registry read is available.

## Rule A2 — Required offline project fields

Each catalogue project entry MUST contain only the compact fields required for
recognition and later validation:

- `project_id`;
- `display_name`;
- `address`;
- optional opaque `customer_ref`;
- `status`;
- `created_at`;
- `registry_updated_at`.

The baseline MUST NOT copy unrelated Registry internals or invent a Cabinet-owned
project version.

## Rule A3 — Customer reference opacity

`customer_ref` is stored and displayed as an opaque Registry value.

Cabinet MUST NOT interpret it as a PresuPro Client, Contact Card, fiscal identity,
or foreign key unless a later explicit contract establishes that meaning.

## Rule A4 — Catalogue identity

Every catalogue snapshot MUST have a deterministic content hash calculated from
its canonical catalogue content and policy metadata.

The catalogue hash identifies Cabinet's immutable offline snapshot. It does not
claim that Registry itself provides content hashes.

## Rule A5 — Catalogue completeness declaration

Every catalogue snapshot MUST declare its selection policy.

Baseline policy:

```text
all projects returned by Registry GET /projects/active
```

A future filtered catalogue requires an explicit policy and MUST NOT silently
present itself as complete.

---

# B. Publication and replacement

## Rule B1 — Immutable publication unit

A published catalogue snapshot is immutable. Refresh creates a new catalogue ID
and hash.

A VPS MUST NOT mutate the stored contents of an already identified catalogue.

## Rule B2 — Idempotent publication

Publishing the same catalogue hash to the same VPS node with the same
idempotency key MUST resolve to one logical publication result.

Retry MUST NOT create duplicate catalogue snapshots or duplicate active replicas.

## Rule B3 — Delivery versus availability

Transport success does not by itself mean the catalogue is usable.

A catalogue becomes available for offline selection only after the VPS has:

- received the complete snapshot;
- verified its canonical hash;
- stored it successfully;
- recorded the exact catalogue ID and generation time.

## Rule B4 — Atomic active-catalogue switch

The VPS MUST keep the previously verified catalogue active until the replacement
catalogue is completely received and verified.

A failed or incomplete refresh MUST NOT leave the VPS without its last valid
catalogue.

## Rule B5 — Single active catalogue pointer

One VPS node has at most one catalogue designated as the current selection
catalogue.

Older catalogues may remain retained for assignment provenance and audit, but
normal object browsing uses the current pointer.

## Rule B6 — Refresh triggers

Catalogue refresh uses a combination of triggers:

1. immediately after a local Backend connection becomes successfully available;
2. manually on explicit user or operator request;
3. once every 24 hours while the local platform remains continuously online.

Repeated connection events within 15 minutes MUST be coalesced into one refresh
attempt unless a manual refresh is requested.

A failed refresh records its own outcome and does not deactivate the last
verified catalogue.

---

# C. Freshness and degraded use

## Rule C1 — Age is always visible

The catalogue generation or Registry observation time MUST be available to the
user and agent whenever offline project data is presented or selected.

Cabinet MUST NOT describe a cached catalogue as current Registry data.

## Rule C2 — Freshness classes

Catalogue age is classified from its Registry observation time:

- `fresh`: less than 48 hours old;
- `stale`: at least 48 hours but less than 7 days old;
- `very_stale`: at least 7 days but less than 30 days old;
- `expired_for_assignment`: 30 days old or older.

These thresholds are accepted baseline policy, not unresolved placeholders.
A later product change may revise them explicitly, but implementations MUST NOT
silently choose different values.

## Rule C3 — Behaviour by freshness class

A verified catalogue behaves as follows:

- `fresh`: normal offline selection without freshness warning;
- `stale`: selection remains allowed with a visible warning showing catalogue
  age;
- `very_stale`: selection remains allowed only after explicit acknowledgement
  that current Registry state cannot be confirmed;
- `expired_for_assignment`: browsing and historical explanation remain allowed,
  but a new Registry `project_id` assignment is blocked.

When assignment is blocked by age, invoice capture remains available and the
user may leave the Card unassigned or use a free-form label allowed by Invoice
Card V1.

Age alone never invalidates an assignment already recorded in an accepted Card
revision.

## Rule C4 — No catalogue available

When no verified catalogue exists on the VPS:

- invoice capture and editing remain available;
- the user may leave the Card object unassigned or use a free-form label allowed
  by Invoice Card V1;
- Cabinet MUST NOT invent or claim a validated Registry `project_id`.

## Rule C5 — Registry outage during refresh

A failed Registry refresh does not delete or invalidate the last verified VPS
catalogue.

The failure is recorded separately from catalogue content.

---

# D. Offline object selection

## Rule D1 — Selection is real Cabinet work

Selecting a `project_id` from a verified cached catalogue is a valid offline
Cabinet action when the catalogue is not `expired_for_assignment`.

It is not merely an AI suggestion and does not require Registry to be reachable
at the moment of selection.

## Rule D2 — Exact provenance

An offline selection MUST retain:

- selected `project_id`;
- catalogue ID and catalogue hash;
- the exact project entry or project snapshot used;
- catalogue freshness class at selection time;
- any required stale-catalogue acknowledgement;
- decision time and actor;
- Card revision in which the object context was stored.

## Rule D3 — Invoice Card remains authoritative for capture context

The selected object is written through the accepted Invoice Card V1 `object`
block and normal Cabinet revision workflow.

Backend provenance records MUST NOT replace or silently rewrite that block.

## Rule D4 — Label preservation

The human-readable label captured in the Card remains historical source context.
Later Registry name changes MUST NOT silently rewrite an already accepted Card
revision.

A later Card revision may deliberately update the object context.

---

# E. Reconnection validation

## Rule E1 — Validate after local acceptance

After reconnection, an assigned Card revision MUST be checked against current
Registry data before the assignment is relied upon for new PresuPro matching or
new project analytics.

The Card itself may still be durably archived when Registry is unavailable.

## Rule E2 — Current validation outcomes

The baseline normalizes Registry results into:

- `valid_active` — project exists and is active;
- `valid_archived` — project exists but is archived;
- `not_found` — current Registry record is absent;
- `registry_unavailable` — no current validation result was obtained;
- `inconclusive` — response or identity could not be safely interpreted.

The model MUST NOT use unsupported `project_closed` or `project_deleted`
semantics.

## Rule E3 — Archived project behaviour

An archived project:

- is excluded from new normal selections because the catalogue is built from
  active projects;
- remains a valid historical identity;
- remains readable through stored snapshots and Registry lookup by ID;
- does not invalidate previously captured invoices;
- blocks automatic creation of new PresuPro matches and new current-project
  analytics;
- may be used for historical matching only after an explicit user decision that
  records acknowledgement of the archived status.

The acknowledgement applies to the exact Card revision and Registry validation
result. It is not a permanent reactivation of the Registry project.

## Rule E4 — Not-found behaviour

A current `not_found` result MUST NOT erase the Card assignment or delete linked
history.

It creates an attention condition requiring explicit review and blocks new
matching or current-project analytics for that assignment.

## Rule E5 — Registry unavailable or inconclusive

`registry_unavailable` and `inconclusive` do not invalidate the stored Card.
They postpone new matching and current-project analytics until a current safe
validation or an explicit historical-use decision exists.

## Rule E6 — Registry name or address changes

A change to display name, address, customer reference, or `registry_updated_at`
does not change `project_id` identity.

The latest Registry snapshot is used for current presentation. The snapshot used
at capture remains retained for provenance.

## Rule E7 — Explicit correction only

Changing the assigned `project_id` requires an explicit Cabinet Card revision.
Validation records cannot silently replace one project with another.

---

# F. Historical catalogues and retention

## Rule F1 — Provenance retention

A catalogue referenced by any retained Card assignment provenance MUST remain
reconstructable from retained data even after it is no longer the current VPS
catalogue.

This may be satisfied by retaining the full catalogue or the exact referenced
project entry plus catalogue identity and policy evidence.

## Rule F2 — VPS catalogue retention

The VPS retains:

- the current verified catalogue;
- the six immediately preceding verified catalogues, for seven full catalogues
  total;
- every additional catalogue or project entry still required by unsynchronized
  assignment provenance.

A full catalogue MUST NOT be deleted before it is 30 days old. After durable
local acceptance of all references to an older catalogue, the VPS may compact it
to the exact referenced project entries plus catalogue identity and policy
evidence.

Compaction MUST preserve the ability to explain what the user saw and selected.

## Rule F3 — VPS cleanup safety

Deleting or compacting an old catalogue from VPS working storage MUST NOT remove
the only copy of assignment provenance that has not yet been durably accepted
locally.

## Rule F4 — Local durable history

The local Backend retains all accepted catalogue snapshots, publication
receipts, referenced project entries, and assignment provenance indefinitely in
the baseline.

The expected data volume is small, and deleting unreferenced catalogue history
would add policy and recovery complexity without meaningful product benefit.
A future retention change requires an explicit migration and audit-preservation
plan.

---

# G. Invariants

1. `project_id` is the Registry UUID and is never replaced by a display label.
2. One immutable catalogue ID maps to one canonical catalogue hash.
3. A catalogue replica is selectable only after hash verification.
4. Replacing the current catalogue is atomic from the VPS user's perspective.
5. Offline assignment always records the exact catalogue provenance when known.
6. Cached selection does not imply current Registry availability.
7. Registry validation never silently edits an accepted Invoice Card revision.
8. Archived and not-found outcomes never erase historical Cabinet relationships.
9. New normal project selection uses active projects only.
10. A catalogue 30 days old or older cannot provide a new Registry ID assignment.
11. New PresuPro matching requires current safe Registry validation or an explicit
    archived historical-use acknowledgement.
12. The VPS retains seven full verified catalogues and never removes unresolved
    assignment provenance.
13. The local Backend retains accepted catalogue history indefinitely in the
    baseline.
14. Registry URL is configuration and MUST NOT be inferred from a hard-coded
    platform port.

---

# H. Closed baseline values

The following values are accepted for the baseline:

| Concern | Accepted value |
| --- | --- |
| Fresh catalogue | `< 48 hours` |
| Stale warning | `48 hours to < 7 days` |
| Strong warning and acknowledgement | `7 days to < 30 days` |
| Block new Registry ID assignment | `>= 30 days` |
| Full catalogues retained on VPS | `7` |
| Minimum full-catalogue age before deletion | `30 days` |
| Local accepted catalogue retention | indefinite |
| Automatic refresh after connection | yes |
| Continuous-online refresh | every 24 hours |
| Connection refresh coalescing window | 15 minutes |
| Manual refresh | always available |
| Archived project for new matching | blocked by default; explicit historical acknowledgement required |

These are product rules. They MUST NOT be replaced by implementation defaults or
left as unspecified configuration during later design states.
