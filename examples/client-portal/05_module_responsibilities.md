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

- OCR Service owns recognition, source-document page context, page order,
  recognition provenance, confidence, and duplicate detection.
- Telegram bot owns intake interaction only and contains no OCR logic.
- Operator or intake interaction owns project selection, Expense confirmation,
  and manual allocation; OCR Service owns none of those decisions.
- Client Portal OCR adapter accepts a confirmed normalized OCR-service result,
  validates recognized-document identity and contract version, and transforms
  the external fields into the portal's Expense intake representation.
- The adapter preserves portable provenance and the source document reference,
  enforces idempotent Expense creation, and rejects incomplete or unsupported
  results.
- The adapter does not carry confidence, provider-specific fields, raw model
  responses, or OCR credentials into the portal when they have no business
  meaning.
- Intake failure must not create partial portal financial or media records.
- Reuse of normalized documents by other applications is a future integration,
  not a Client Portal MVP responsibility.

No internal packages, files, dependency graph, framework, or persistence
layout is defined by these responsibility areas.
