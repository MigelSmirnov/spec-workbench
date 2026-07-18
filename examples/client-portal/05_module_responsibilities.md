# Client Portal Product Responsibility Areas

## Status

**Requirements baseline; these are functional areas, not software modules**

## Project Context

- Obtain the current project from Registry.
- Verify that the project exists and interpret its active/archive status.
- Present current Registry context without claiming ownership of it.
- Apply read-only mode to the whole portal when the project is archived.

## Budget

- Maintain planned values for the current client-visible budget.
- Record whether the source is manual or a future approved snapshot.
- Present ordered Budget Sections and derived budget totals.
- Prevent mutable PresuPro data from silently replacing the current budget.

## Expenses and Documents

- Accept already confirmed Expense and Document facts.
- Maintain explicit allocations to Budget Sections or `Other expenses`.
- Support correction, inclusion, and exclusion of an Expense while active.
- Keep one Document associated with one Expense regardless of allocation count.
- Let the client inspect expense evidence without exposing OCR internals.

## Work Progress and Payments

- Maintain manual completion percentage for work sections.
- Derive completed work value and cost-weighted overall progress.
- Record Work Payments.
- Derive payments total and work balance without treating payments as facturas.

## Photos

- Accept prepared photo references.
- Associate a photo with the project and optionally a Budget Section.
- Maintain caption and client visibility.
- Present the chronological client gallery.

## Dashboard

- Assemble the client-facing view of Registry context, budget, expenses,
  progress, payments, and photos.
- Show unavailable data explicitly.
- Derive aggregates from their owning records; the dashboard owns no separate
  primary financial state.

## Integration Intake

- Telegram reception, OCR, OCR confidence, and operator confirmation occur
  outside Client Portal.
- Client Portal accepts only prepared, confirmed data from that boundary.
- Intake failure must not create partial portal financial or media records.

No internal packages, files, dependency graph, framework, or persistence
layout is defined by these responsibility areas.
