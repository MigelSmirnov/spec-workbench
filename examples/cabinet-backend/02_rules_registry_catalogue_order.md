# State 2 — Registry catalogue publication order

## Accepted decision A79 — published Registry catalogue projects are ordered by project_id (2026-09-14)

Cabinet Web accepts a published Registry catalogue only when its project
snapshots are in strictly ascending `project_id` order
(`rules.registry_publication.snapshot_order_key = project_id`; the rejection is
`PROJECT_ORDER_INVALID`), and its A09 rule 8 hashes that ordered snapshot. The
local Backend's A35 and A72 spoke of "an exact ordered snapshot" without naming
the order. On 2026-09-14 a three-project catalogue delivered in Registry export
order was rejected; the two-project catalogues of 2026-09-05/06 had passed by
chance.

### Normative rules

1. `registry_context.refresh_registry_context` returns the project snapshots
   ordered by ascending `project_id` (code-point order of the identifier
   string). `catalogue_publication.publish_registry_catalogue` hashes and
   delivers the projects in exactly that order; no caller supplies or changes
   the order.
2. The ordered content hash of A72 is computed over that order, so equal
   project sets produce equal hashes whatever order Registry exported them in.
3. Until the rule reaches the generated modules (State 3 notes, then Route B),
   the operator session `deploy/local/sync_session.py` orders the observations
   before refresh and carries a `BOUNDARY DRIFT` marker; the marker is removed
   with the propagation.

### Formal invariants

```text
catalogue_delivery.projects = sorted_by(project_id, ascending)
equal_project_set -> equal_ordered_content_hash
registry_export_order -/> delivery_order
```

### Required tests

1. A catalogue built from Registry observations in arbitrary order is
   delivered in ascending `project_id` order and accepted by Cabinet Web.
   [witness: verification:semantic_flow6_synchronization]
2. Two observations of the same project set in different orders produce one
   ordered content hash and one publication.

### Consequence

The order is a property of the refreshed Registry context, not of the
transport or the caller: `catalogue_publication` stays a pure delivery of what
`registry_context` returns, and the reciprocal Cabinet Web rule has one owner
on this side. The `semantic_flow6_synchronization` check gains the order
assertion when rule 1 propagates.
