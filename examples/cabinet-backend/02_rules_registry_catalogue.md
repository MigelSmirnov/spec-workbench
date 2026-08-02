# State 2 — Registry catalogue and offline object rules

## Status

Accepted consolidated rules for publishing Registry project context to the VPS
and using it while the local platform is unavailable.

Registry owns project identity and current context. Cabinet stores immutable,
versioned catalogue snapshots for offline work. This document defines policy and
invariants, not modules, APIs, tables, or implementation order.

## Confirmed Registry boundary

The current Registry contract provides:

- `project_id` as a UUID JSON string;
- `display_name`, `address`, optional opaque `customer_ref`;
- `created_at` and `registry_updated_at`;
- statuses `active` and `archived`;
- `GET /projects/active` and project lookup/validation by ID.

Registry does not currently provide project revision numbers, content hashes,
`closed`, `deleted`, or historical project versions.

## Catalogue construction

1. The normal VPS catalogue contains every project returned by
   `GET /projects/active`.
2. Each entry contains only `project_id`, `display_name`, `address`, optional
   `customer_ref`, `status`, `created_at`, and `registry_updated_at`.
3. `customer_ref` remains opaque and is not treated as a Cabinet Contact,
   PresuPro Client, fiscal identity, or foreign key.
4. Each catalogue has a deterministic Cabinet content hash over canonical
   entries and policy metadata.
5. A catalogue declares its selection policy. A filtered catalogue must never
   present itself as complete.
6. Published catalogue snapshots are immutable. Refresh creates a new catalogue
   ID and hash.

## Publication and replacement

1. Publication is idempotent for the same target, catalogue hash, and
   idempotency key.
2. Delivery does not make a catalogue selectable. The VPS must receive, store,
   and hash-verify the complete snapshot first.
3. The previous verified catalogue remains active until its replacement is
   verified. A failed refresh never removes the last usable catalogue.
4. One VPS has one current selection catalogue pointer.
5. Refresh is attempted:
   - after the local Backend becomes available;
   - manually on request;
   - every 24 hours while continuously connected.
6. Connection events within 15 minutes are coalesced unless refresh is manual.

## Freshness classes

Age is measured from Registry observation time:

- `fresh`: under 48 hours;
- `stale`: 48 hours to under 7 days;
- `very_stale`: 7 days to under 30 days;
- `legacy_verified`: 30 days or older.

Catalogue age must always be visible. Cabinet must not call cached information
current Registry data.

A verified catalogue never expires solely because time passed. Age affects
warnings and acknowledgement, not the identity of projects already present.

- `fresh`: normal selection;
- `stale`: selection with visible age warning;
- `very_stale`: selection after explicit acknowledgement;
- `legacy_verified`: cached projects remain selectable after explicit
  acknowledgement that their current Registry status may have changed.

For a previously used project in a `legacy_verified` catalogue, acknowledgement
is required once per working session before adding invoices. Selecting another
cached project requires acknowledgement for that selection.

## Offline selection

1. Selecting a `project_id` from a verified catalogue is valid Cabinet work even
   when Registry is offline.
2. Selection provenance retains project ID, catalogue ID and hash, the exact
   project entry, freshness class, acknowledgement evidence, actor, time, and
   the resulting Invoice Card revision.
3. The accepted Invoice Card `object` block remains the capture record. Backend
   provenance never silently replaces it.
4. Later Registry name or address changes do not rewrite accepted Card
   revisions.
5. Cabinet must not invent or manually claim a Registry ID absent from the
   current verified catalogue. Such work is saved unassigned or with a free-form
   label and linked later by an explicit Card revision.
6. If no verified catalogue exists, invoice capture remains available, but no
   Registry ID may be claimed.

## Reconnection validation

An assigned Card is validated against current Registry data after reconnection
before new PresuPro matching or current project analytics rely on it.

Normalized outcomes are:

- `valid_active`;
- `valid_archived`;
- `not_found`;
- `registry_unavailable`;
- `inconclusive`.

Rules:

1. Validation never edits an accepted Invoice Card revision.
2. `valid_archived` preserves historical identity and existing invoices, but
   blocks new automatic matching and current-project analytics. Historical use
   requires explicit acknowledgement for the exact Card revision and validation.
3. `not_found` preserves the assignment and history but blocks new matching and
   current-project analytics until explicit review.
4. `registry_unavailable` and `inconclusive` preserve the Card and postpone
   validation-dependent work.
5. With a `legacy_verified` catalogue and unavailable Registry, invoice capture
   and assignment remain allowed; new automatic matching is deferred; historical
   results remain readable; provisional analysis requires a stale-context
   warning.
6. Changing `project_id` requires an explicit new Invoice Card revision.

## Retention

1. The VPS retains the current catalogue plus six previous verified catalogues:
   seven full catalogues total.
2. A full catalogue is not deleted before 30 days of age.
3. Any additional catalogue or project entry required by unsynchronized
   assignment provenance is retained regardless of count or age.
4. After all references are durably accepted locally, an older VPS catalogue may
   be compacted to referenced project entries plus catalogue identity and policy
   evidence.
5. Compaction must preserve what the user saw and selected.
6. The local Backend retains accepted catalogue snapshots, publication evidence,
   referenced entries, and assignment provenance indefinitely in the baseline.

## Invariants

1. `project_id` is the Registry UUID and is never replaced by a label.
2. One catalogue ID maps to one canonical catalogue hash.
3. Only hash-verified catalogue replicas are selectable.
4. Current-catalogue replacement is atomic for the VPS user.
5. Offline assignment records exact catalogue provenance.
6. Cached selection never implies current Registry availability.
7. Catalogue age never invalidates a known Registry project identity.
8. A cached project remains usable for capture with age-dependent warning and
   acknowledgement.
9. Cabinet never assigns a Registry ID absent from the verified catalogue.
10. Archived or missing Registry outcomes never erase historical Cabinet data.
11. New matching requires current safe validation or an explicit historical-use
    decision where allowed.
12. VPS cleanup never removes unresolved assignment provenance.
13. Registry URL is configuration and is never inferred from a hard-coded port.

## Closed baseline values

| Concern | Accepted value |
| --- | --- |
| Fresh | `< 48 hours` |
| Stale warning | `48 hours to < 7 days` |
| Strong warning | `7 days to < 30 days` |
| Legacy verified | `>= 30 days` |
| Continue known project after 30 days | allowed with session acknowledgement |
| Select another cached project after 30 days | allowed with explicit acknowledgement |
| Assign ID absent from catalogue | forbidden |
| New automatic matching without current validation after 30 days | deferred |
| Invoice capture without current validation | allowed |
| Full catalogues retained on VPS | `7` |
| Minimum full-catalogue age before deletion | `30 days` |
| Local accepted catalogue retention | indefinite |
| Refresh after connection | yes |
| Continuous-online refresh | every 24 hours |
| Connection coalescing | 15 minutes |
| Manual refresh | always available |
