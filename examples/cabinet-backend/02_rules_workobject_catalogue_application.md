# Cabinet Backend — WorkObject Catalogue Application

## Status

Accepted clarification for `02_rules.md`.

This rule closes the question of how Cabinet applies the Registry catalogue to
`WorkObject`.

It defines a one-way projection from Registry into Cabinet. Cabinet never mutates
Registry and never synchronizes `WorkObject` data back to Registry.

---

## Accepted decision — one-way WorkObject projection

For every Registry project known to Cabinet, Cabinet maintains a corresponding
`WorkObject`.

`WorkObject` is a Cabinet-owned local copy of project data used by Cabinet
workflows.

The relationship is one-way:

```text
Registry project -> Cabinet WorkObject
```

There is no reverse synchronization.

---

## Normative rules

1. Registry remains authoritative for Registry-owned project fields.
2. Cabinet must not create, edit, archive, reopen, delete, or otherwise mutate
   Registry projects.
3. Cabinet must not send `WorkObject` changes back to Registry.
4. Cabinet stores all Registry projects, including both `active` and `archived`
   projects.
5. A catalogue refresh creates a `WorkObject` when no local object exists for the
   Registry `project_id`.
6. A catalogue refresh updates Registry-derived fields in an existing
   `WorkObject`.
7. A catalogue refresh must not overwrite Cabinet-owned local fields.
8. Registry-derived fields and Cabinet-owned fields must remain distinguishable.
9. An archived Registry project remains stored as a `WorkObject`.
10. If a project is absent from a later Registry catalogue response, Cabinet does
    not delete the existing `WorkObject`.
11. Absence from one refresh is recorded as unresolved source availability, not
    as confirmed deletion.
12. Cabinet must not automatically replace one `WorkObject` with another project.
13. One Registry `project_id` maps to at most one current Cabinet `WorkObject`.
14. A `WorkObject` must preserve the stable Registry `project_id` used to create
    it.

---

## Registry-derived fields

The current Registry-derived projection contains:

```text
project_id
display_name
address
status
registry_updated_at
```

These fields are refreshed from the compact Registry catalogue defined by A34.

---

## Cabinet-owned fields

Any field created exclusively for Cabinet workflows is Cabinet-owned.

Examples may include local presentation, workflow, notes, assignment, or
application state.

The exact Cabinet-owned field set belongs to the Cabinet contract and is not
defined by this rule.

Registry refresh must never overwrite a Cabinet-owned field merely because the
corresponding Registry project changed.

---

## Refresh behavior

For every catalogue entry:

### WorkObject does not exist

Cabinet creates a new `WorkObject` with:

```text
registry_project_id = catalogue.project_id
registry-derived fields = catalogue values
```

### WorkObject already exists

Cabinet updates only Registry-derived fields.

```text
registry-derived fields <- latest catalogue values
Cabinet-owned fields <- unchanged
```

### Existing WorkObject is absent from refreshed catalogue

Cabinet preserves the `WorkObject`.

```text
work_object_deleted = false
registry_presence = unresolved
```

No confirmed deletion is inferred.

---

## Status behavior

### Active Registry project

The corresponding `WorkObject` remains available for normal Cabinet workflows.

### Archived Registry project

The corresponding `WorkObject` remains stored.

Its Registry status is updated to `archived`, and it is not treated as available
for normal automatic project assignment.

Archiving in Registry does not delete or archive Cabinet-owned information.

---

## Formal invariants

One-way ownership:

```text
Cabinet_may_mutate_Registry = false
WorkObject_changes_flow_to_Registry = false
```

Stable identity:

```text
one Registry project_id -> at most one current WorkObject
```

Refresh safety:

```text
Registry refresh updates only Registry-derived fields
```

Retention:

```text
archived Registry project -> WorkObject remains stored
missing catalogue entry -> WorkObject remains stored
```

---

## Required tests

1. A new Registry project creates one corresponding `WorkObject`.
2. Repeating the same catalogue refresh does not create a duplicate
   `WorkObject`.
3. A Registry name or address change updates the Registry-derived fields.
4. A Registry refresh does not overwrite Cabinet-owned fields.
5. An archived project remains stored as a `WorkObject`.
6. An archived project is not available for normal automatic assignment.
7. A project absent from a later catalogue response does not delete its
   `WorkObject`.
8. A missing catalogue entry is not interpreted as confirmed deletion.
9. Cabinet performs no Registry mutation during create, update, archive, or
   retention handling.
10. Local `WorkObject` changes never produce Registry writes.

---

## Consequence

Cabinet keeps a durable local `WorkObject` for every Registry project it has
observed.

Registry supplies authoritative project facts. Cabinet copies and refreshes those
facts for local use while preserving its own local state independently.

This decision closes `OQ-004`.
