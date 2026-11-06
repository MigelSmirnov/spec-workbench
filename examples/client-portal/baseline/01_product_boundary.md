# Client Portal Product Boundary

## Status

**Requirements baseline**

## Purpose

Client Portal gives the client a transparent view of one renovation project:

- planned budget;
- actual expenses and their documents;
- allocation of expenses to budget sections;
- progress of the work;
- value of completed work;
- received work payments;
- photographs of work progress.

The portal is a client view and record of portal-owned facts. It does not
replace the operational systems that create projects, calculate estimates,
perform OCR, receive Telegram submissions, or create invoices. OCR is a
separate external microservice; Telegram bot is an intake interface and does
not own recognition logic.

## Portal ownership

Client Portal owns:

- the local client-facing representation of the project budget;
- confirmed expenses received from an authorized intake process;
- manual allocation of expenses to budget sections or `Other expenses`;
- work payments recorded for the project;
- manually entered work progress;
- progress-photo references, captions, section association, and visibility;
- client-facing aggregates derived from the above records.

## Boundaries outside Portal ownership

Client Portal does not own:

- project identity or creation of `project_id`;
- current Registry project name, address, status, or customer reference;
- PresuPro estimate calculations or mutable estimate lifecycle;
- source pages, page ordering, recognition provenance, confidence, duplicate
  detection, provider/model choice, or any other OCR-service internals;
- Telegram intake and its user interaction;
- accounting records or a full bookkeeping ledger;
- Holded integration;
- factura creation or factura lifecycle;
- operation or administration of internal project microservices.

## Read and write responsibilities

- The portal reads and validates project identity and current project context
  through Registry.
- The portal never creates or rewrites Registry `project_id`.
- The portal accepts only a confirmed normalized recognition result through
  its OCR boundary; it does not perform OCR or depend on an OCR provider/model.
- Project selection, expense confirmation, and Budget Section allocation are
  supplied by an operator or intake process outside the OCR service.
- The portal accepts prepared photo facts from Telegram intake but does not
  contain Telegram intake logic.
- The portal records only portal-owned budget, expense, allocation, progress,
  payment, photo, and presentation facts.
- The portal does not write estimate or factura state to PresuPro in the MVP.

## MVP scope

- Load and display current Registry project context.
- Allow a temporary manual budget organized into client-facing sections.
- Accept confirmed expenses and their document references.
- Protect Expense creation with a stable recognized-document reference so one
  confirmed OCR result cannot create two Expenses.
- Allocate an expense to one section, split it manually across sections, or
  assign it to `Other expenses`.
- Show actual expenses and derived remaining budget values.
- Record manual work progress and derive completed work value.
- Record received work payments and show the work balance.
- Accept progress photos and show a chronological client gallery.
- Present the client dashboard for the selected project.
- Keep an archived project readable while blocking new portal changes.

## Non-goals

- Full accounting or bookkeeping.
- Reuse of a normalized recognized document by other applications; that is a
  separate future integration.
- Automatic factura reconciliation.
- Bank integration.
- Full document workflow or document approval management.
- Automatic progress estimation from photographs.
- Management of internal microservices from the portal.
- Automatic import of a mutable PresuPro estimate.
- Designing the future approved-presupuesto or factura lifecycle.
