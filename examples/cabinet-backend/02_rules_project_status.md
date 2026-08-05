# Cabinet Backend — Project Status Handling

## Status

Accepted clarification for `02_rules.md`.

This rule defines how Cabinet Backend interprets project availability for invoice
processing. Registry remains the authoritative source of project status.
Concrete Registry status names and transport fields remain part of the Registry
contract and are not invented here.

---

## Accepted decision — project status does not reject an invoice

Cabinet Backend must preserve a valid confirmed Invoice Card even when the linked
project is completed, archived, blocked, missing, or otherwise unavailable for
normal work.

Project status affects classification and review requirements, not the existence
of the invoice in the durable archive.

### Normative rules

1. Registry is authoritative for the current project status.
2. Cabinet Backend must not infer or rewrite Registry project status.
3. An invoice linked to an active project follows normal processing.
4. An invoice linked to a completed project is accepted and marked as a late
   project cost.
5. A completed project is not automatically reopened by Cabinet Backend.
6. An invoice linked to an archived, blocked, deleted, or otherwise unavailable
   project is preserved but requires manual review of the project assignment.
7. An invoice whose project cannot be found in the current Registry catalogue is
   preserved and requires manual review.
8. Project status alone must never cause deletion, silent rejection, or loss of a
   valid confirmed Invoice Card.
9. Project review state is stored separately from the immutable Invoice Card.
10. A later Registry refresh may resolve the review state without rewriting the
    accepted Invoice Card.
11. Cabinet Backend must not invent a replacement project automatically.
12. Downstream analytics must be able to distinguish:
    - normal project cost;
    - late project cost;
    - project assignment requiring review.

---

## Logical classification

The following semantic categories are normative even if Registry uses different
status names:

### Active

The project is available for normal work.

```text
project_cost_classification = normal
project_assignment_requires_review = false
```

### Completed

The project is formally complete but may still receive legitimate late expenses.

```text
project_cost_classification = late_project_cost
project_assignment_requires_review = false
```

### Unavailable

The project is archived, blocked, deleted, inaccessible, or otherwise unsuitable
for automatic assignment.

```text
project_cost_classification = unresolved
project_assignment_requires_review = true
```

### Unknown

No authoritative project record can be resolved from the current Registry
catalogue.

```text
project_cost_classification = unresolved
project_assignment_requires_review = true
```

---

## Formal invariants

A valid confirmed Invoice Card is not rejected solely because of project status:

```text
invoice_acceptance != rejected_by_project_status
```

For every completed project assignment:

```text
project_cost_classification = late_project_cost
```

For every unavailable or unknown project assignment:

```text
project_assignment_requires_review = true
```

Cabinet Backend cannot mutate Registry lifecycle state:

```text
backend_may_reopen_project = false
backend_may_change_registry_status = false
```

---

## Required tests

1. An invoice for an active project enters normal processing.
2. An invoice for a completed project is accepted and marked
   `late_project_cost`.
3. A completed project is not reopened automatically.
4. An invoice for an archived or blocked project is preserved and marked for
   manual review.
5. An invoice for an unknown project is preserved and marked for manual review.
6. A later Registry refresh may resolve the assignment without changing the
   immutable Invoice Card.
7. No project status causes silent invoice loss.
8. Downstream analytics can distinguish normal, late, and unresolved project
   costs.

---

## Open dependency

The exact mapping from Registry status values to the semantic categories
`active`, `completed`, and `unavailable` remains open until the Registry catalogue
contract is verified.

---

## Consequence

Project completion is an analytical and workflow state, not a hard acceptance
boundary.

Cabinet Backend preserves the invoice, records the project context truthfully,
and escalates only the assignment decision that cannot be made safely.
