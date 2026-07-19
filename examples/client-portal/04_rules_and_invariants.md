# Client Portal Business Rules and Invariants

## Status

**Requirements baseline; formal invariant ownership is future authoring work**

## Project rules

- Every portal record belongs to exactly one Registry `project_id`.
- An unknown project is rejected; client-supplied context cannot replace
  Registry validation.
- An active project permits authorized portal mutations.
- An archived project is read-only in Client Portal.
- Archiving never deletes portal history.
- Full client-access closure or revocation is a separate future decision and
  is not implied by Registry archival.

## Budget rules

- Planned budget is not calculated from actual expenses.
- Manual mode requires an operator to enter planned material and work amounts.
- A future imported budget may be created only from an explicitly published,
  immutable approved PresuPro snapshot.
- A mutable PresuPro estimate never silently changes the portal budget.
- Transition from manual budget to imported budget is explicit; its detailed
  migration policy remains open.
- Budget totals are derived from Budget Sections and are not primary editable
  totals.

## Expense rules

- An Expense created from OCR requires a stable `recognized_document_id`, a
  supported contract version, a source document reference, and a confirmed,
  complete normalized result.
- One `recognized_document_id` creates at most one Expense; replay of the same
  confirmed result must not create another Expense.
- OCR-service duplicate detection and Client Portal Expense idempotency are
  separate responsibilities.
- The OCR service does not choose `project_id`, confirm the business Expense,
  or allocate it to Budget Sections; those decisions come from the authorized
  operator or intake process.
- Client Portal preserves portable OCR provenance and the source document
  reference, but does not import confidence, provider-specific fields, or raw
  model responses into its Expense data.
- OCR does not change planned budget values.
- Financial actuals are calculated from Expense records, not manually
  overwritten totals.
- Only confirmed Expenses marked for inclusion participate in financial
  totals.
- The sum of an Expense's allocations equals the Expense total.
- Automatic proportional allocation is forbidden.
- An Expense without useful detail may be allocated to `Other expenses`.
- One Document remains one document when the Expense has several allocations.
- Actual materials are derived from included confirmed allocations to Budget
  Sections; `Other expenses` remains separately visible.
- Remaining materials are planned materials minus derived actual materials;
  overspend is shown rather than clamped or hidden.

## Work rules

For each Budget Section with planned work:

```text
completed work value = planned work cost × completion percent
```

- Completion percent is entered manually by an authorized operator and stays
  within 0–100 percent inclusive.
- Overall progress is weighted by planned work cost across work sections.
- A simple arithmetic mean of section percentages is forbidden.
- When no planned work cost exists, overall progress is unavailable rather
  than guessed.

## Payment rules

```text
work balance = completed work value - received payments
```

- Payments total is derived from Work Payment records.
- A positive balance is shown as `Completed ahead of payments`.
- A negative balance is shown by its absolute amount as
  `Unused advance payment`.
- A Work Payment is not a factura and does not create an accounting posting.

## Photo rules

- Every Progress Photo belongs to one project.
- Budget Section association is optional.
- The client gallery is chronological.
- Hiding or removing a photo from the gallery never changes financial data.
- Photographs never determine work completion automatically in the MVP.
