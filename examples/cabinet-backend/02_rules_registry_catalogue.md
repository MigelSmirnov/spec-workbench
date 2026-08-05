# Cabinet Backend — Compact Registry Catalogue Contract

## Status

Accepted clarification for `02_rules.md`.

This rule is based on observed Registry Sandbox behavior recorded in
`registry_discovery.md`. It defines the minimum catalogue projection required by
Cabinet Backend and does not extend the Registry contract.

---

## Accepted decision — minimal Registry catalogue

Cabinet Backend maintains a compact local projection of Registry projects for
Cabinet synchronization and project-assignment workflows.

The catalogue contains only fields already available from the current Registry
project list.

### Catalogue fields

Each catalogue entry contains:

```text
project_id
display_name
address
status
registry_updated_at
```

### Field mapping

| Catalogue field | Registry source |
|---|---|
| `project_id` | `id` |
| `display_name` | `name` |
| `address` | `address` |
| `status` | `status` |
| `registry_updated_at` | `updated_at` |

The value of Registry `id` is preserved unchanged when projected as
`project_id`.

---

## Refresh source

The authoritative refresh source is:

```text
GET /projects?include_archived=true
```

The active-project reference endpoint is not sufficient because it omits address
and freshness evidence.

---

## Refresh semantics

1. Cabinet Backend performs a full catalogue poll.
2. The returned collection is transformed into the compact catalogue projection.
3. The local projection is replaced as one refreshed catalogue observation.
4. Cabinet Backend compares entries by stable `project_id`.
5. `registry_updated_at` is preserved as Registry freshness evidence.
6. No incremental cursor, event stream, tombstone, ETag, or catalogue revision is
   assumed.
7. Missing entries are not interpreted as confirmed deletion.
8. Incremental synchronization requires a future Registry contract and is not part
   of the current baseline.

---

## Status mapping

The current Registry contract exposes only:

```text
active
archived
```

Cabinet Backend maps them as follows:

| Registry status | Cabinet meaning |
|---|---|
| `active` | available for normal automatic project assignment |
| `archived` | unavailable for automatic assignment; manual review required |

Registry currently exposes no distinct completion status.

Therefore:

- `archived` must not be interpreted as `completed`;
- Cabinet Backend must not derive `late_project_cost` from `archived`;
- project completion remains an unresolved business fact until Registry exposes a
  separate authoritative contract.

---

## Missing project behavior

When a referenced `project_id` is absent from the current catalogue:

```text
project_assignment_requires_review = true
```

Cabinet Backend must preserve the invoice and must not infer whether the project:

- never existed;
- was removed outside the public Registry API;
- is temporarily unavailable;
- is hidden by an unknown operational condition.

No replacement project may be selected automatically.

---

## Excluded fields

The current compact catalogue does not include:

```text
customer_ref
created_at
```

These fields are excluded because they require per-project context requests and
are not required by the accepted minimum Cabinet workflow.

Adding either field requires a separate accepted decision.

---

## Formal invariants

For every catalogue entry:

```text
project_id = Registry.id
display_name = Registry.name
address = Registry.address
status = Registry.status
registry_updated_at = Registry.updated_at
```

Automatic assignment is allowed only when:

```text
status = active
```

Manual review is required when:

```text
status = archived
or project_id is absent from the current catalogue
```

Cabinet Backend must not claim:

```text
catalogue_is_incremental = true
catalogue_has_deletion_tombstones = true
archived_means_completed = true
```

---

## Required tests

1. A full Registry list is projected into the five accepted catalogue fields.
2. Registry `id` is preserved unchanged as `project_id`.
3. An active project is available for normal assignment.
4. An archived project requires manual review.
5. An archived project is not classified as completed.
6. A missing project requires manual review and does not reject the invoice.
7. `customer_ref` and `created_at` are not required for catalogue refresh.
8. A refresh does not depend on incremental cursors, ETags, or tombstones.
9. An absent entry is not recorded as confirmed deletion.

---

## Consequence

The current catalogue contract is intentionally small and polling-based.

It is sufficient for Cabinet project selection and safe assignment review without
introducing unsupported Registry capabilities.
