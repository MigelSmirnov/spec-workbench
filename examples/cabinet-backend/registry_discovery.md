# Registry discovery for Cabinet Backend

## Status

Factual reconnaissance of the current Registry Sandbox contract and runtime.
This document records observed behavior; it does not introduce a new Cabinet
Backend decision or extend the Registry contract.

Evidence reviewed on 2026-08-05:

- accepted Factory project: `registry_sandbox`;
- accepted base-spec SHA-256:
  `c4118ee96a358fa941ebb577a1b068a1e9440fdcc1d9d6af244be79c9d123f3a`;
- terminal accepted-spec verification run: `20260718_195526`, verdict `PASS`;
- Registry models, rules, service, HTTP runtime, SQLite repository, frontend
  contract, and identity-boundary tests;
- focused runtime tests: 4 passed.

---

## Project statuses

Registry currently accepts exactly two lowercase project statuses:

- `active`;
- `archived`.

New projects always start as `active`. Archiving replaces the stored project
record with the same `id`, status `archived`, and a new UTC `updated_at` value.
There is no Registry status named `completed`, `closed`, `blocked`, or `deleted`.

### Cabinet semantic mapping

| Registry fact | Cabinet category | Reason |
|---|---|---|
| `status = active` | `active` | Registry exposes the project for normal work. |
| `status = archived` | `unavailable` | Registry retains the record, excludes it from active selection, and validation reports `archived`. |
| validation result `not_found` | `unavailable` | No authoritative project record can be resolved. |
| `completed` | No mapping available | Registry has no distinct completion status. |

`archived` must not be interpreted as `completed` without a separate Registry
business contract. The current implementation cannot distinguish a completed
project from one archived for another reason.

---

## Available catalogue fields

### Full project list

`GET /projects?include_archived=true` returns the current project collection as
`ProjectSummary` records:

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Stable Registry-owned project identity. |
| `name` | string | Display name. |
| `address` | string | Required project address. |
| `status` | string | `active` or `archived`. |
| `updated_at` | UTC datetime | Changes on project edit and archive. |

Example based on the shipped Registry fixture:

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "name": "Офис на Гагарина",
  "address": "пл. Гагарина, 1, оф. 410",
  "status": "archived",
  "updated_at": "2026-05-02T12:00:00Z"
}
```

This is the best existing endpoint for a compact Cabinet catalogue. Registry
calls the identity field `id`; Cabinet may project it as `project_id` at its own
boundary without changing the value.

### Active-project reference list

`GET /projects/active` returns only:

```json
{
  "project_id": "11111111-1111-4111-8111-111111111111",
  "display_name": "Квартира на Ленина 5",
  "status": "active"
}
```

This endpoint omits `address` and `updated_at`, so it is insufficient by itself
for a versioned or freshness-aware Cabinet catalogue.

### Per-project context

`GET /projects/{project_id}/context` additionally exposes:

- nested `project_id`, `display_name`, and `status`;
- `address`;
- nullable `customer_ref`;
- `created_at`;
- `registry_updated_at` (the project record's `updated_at`).

There is no bulk context endpoint. Fetching `customer_ref` or `created_at` for a
catalogue requires one context request per project.

---

## Identity, archive, and deletion behavior

- `project_id` is a server-generated UUID and the SQLite primary key.
- Create requests cannot supply `id` or `status`.
- Update requests contain only `name`, `address`, and optional `customer_ref`;
  the path UUID selects the project.
- Editing or archiving preserves the same UUID.
- Archived records remain queryable directly and appear in
  `GET /projects?include_archived=true`.
- Normal lists exclude archived records unless `include_archived=true`.
- Registry exposes no project deletion endpoint, deleted status, `deleted_at`,
  or tombstone model.
- A missing UUID produces `exists=false`, `status=null`, and
  `failure=not_found` from the validation endpoint.

Consequently, Cabinet cannot distinguish a never-existing UUID from a record
removed outside the public Registry API.

---

## Change delivery

The current Registry contract provides collection polling plus per-record
timestamps:

1. call `GET /projects?include_archived=true`;
2. compare each record by stable UUID and `updated_at`;
3. replace the local catalogue projection from the returned collection.

The list is ordered by descending `updated_at`, then by UUID. `updated_at` is a
UTC wall-clock timestamp generated on create, edit, and archive.

Registry currently provides none of the following:

- catalogue version or content hash;
- project revision number;
- `ETag`, `Last-Modified`, or conditional GET;
- `since`, cursor, or incremental change endpoint;
- deletion tombstones;
- webhook, event stream, or change log;
- dedicated export file;
- pagination or an explicit snapshot-completeness marker.

Artifact `version` fields belong to published project artifacts and are not
project or catalogue versions.

---

## API and export limitations

- The only list filter is `include_archived`; there is no server-side status,
  timestamp, or ID-range filter.
- A full list response is not identified as one atomic snapshot.
- `ProjectSummary` omits `customer_ref` and `created_at`.
- `/projects/active` omits all freshness evidence.
- Missing records have no cause or deletion history.
- Timestamp comparison depends on Registry clock behavior and does not provide a
  global monotonic sequence.

For the current small Registry, full polling with `include_archived=true` is the
only supported catalogue-refresh strategy. An incremental algorithm would
require a new Registry contract.

---

## Questions Registry cannot currently answer unambiguously

1. Does `archived` mean completed work, administrative hiding, cancellation, or
   several of these states?
2. Is project completion a separate business fact that Registry must add?
3. Can projects be hard-deleted operationally, and if so, how should consumers
   receive tombstones?
4. Is the full list guaranteed to contain every project visible to the Cabinet
   integration at one consistent observation point?
5. What catalogue version, hash, cursor, or event contract should support safe
   incremental synchronization?
6. Are `name`, `address`, `status`, `updated_at`, and stable UUID sufficient, or
   does Cabinet's compact catalogue also require `customer_ref` and `created_at`?
