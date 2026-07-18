# Client Portal Business Contracts

## Status

**Requirements baseline; these are business exchanges, not program signatures**

## Registry → Client Portal: Project Context

- **Producer:** Registry.
- **Consumer:** Client Portal project view and mutation guard.
- **Required data:** project identity, display name, status, address, optional
  customer reference, creation time, and Registry freshness time; validation
  also supplies existence, activity, and failure meaning.
- **Business guarantees:** Registry owns identity and current context; returned
  identity matches the requested project; archived context remains readable.
- **Invalid states:** malformed or mismatched identity, unknown project used as
  real context, or archived project treated as mutable.
- **Idempotency expectation:** repeated reads create no portal business record;
  a later Registry revision may legitimately return fresher current context.
- **Provenance:** Registry identity and freshness timestamp remain attached to
  the local representation.

## Telegram Intake → Client Portal: Confirmed Expense

- **Producer:** external Telegram/OCR intake after operator confirmation.
- **Consumer:** Client Portal Expenses and Documents area.
- **Required data:** project identity, stable intake identity, supplier,
  document date, total amount, confirmation fact, inclusion choice, one
  document reference, allocations, and confirmation provenance.
- **Business guarantees:** one confirmed intake result creates one Expense and
  one Document reference; allocation sum equals Expense total.
- **Invalid states:** unconfirmed OCR output, unknown or archived project,
  missing total or document reference, automatic allocation guess, or
  allocation mismatch.
- **Idempotency expectation:** replay of the same stable intake identity does
  not duplicate the Expense or Document.
- **Provenance:** intake identity, confirmation time, and confirming operator
  reference remain traceable; OCR internals are not client data.

## Telegram Intake → Client Portal: Progress Photo

- **Producer:** external Telegram intake after operator project selection.
- **Consumer:** Client Portal Photos area.
- **Required data:** project identity, stable intake identity, external file
  reference, photo date, optional section, optional caption, visibility, and
  publication provenance.
- **Business guarantees:** the photo belongs to one project; section is
  optional; publication never changes financial or progress facts.
- **Invalid states:** unknown or archived project, missing file reference,
  cross-project section, or client-visible credentials.
- **Idempotency expectation:** replay of the same stable intake identity does
  not create another Progress Photo.
- **Provenance:** intake source, publication time, and operator reference remain
  traceable without exposing Telegram internals to the client.

## Operator → Client Portal: Work Progress Update

- **Producer:** authorized operator.
- **Consumer:** Client Portal Work Progress area and derived dashboard values.
- **Required data:** project identity, work-section identity, manual completion
  percentage, update time, and operator provenance.
- **Business guarantees:** percentage applies to one work section; completed
  value and overall progress are derived, not submitted as authoritative.
- **Invalid states:** unknown or archived project, unknown/cross-project
  section, percentage outside its allowed range, or photo-derived progress.
- **Idempotency expectation:** applying the same update again leaves the same
  current progress and does not create a financial fact.
- **Provenance:** update time and operator reference remain visible to audit
  needs, even though history retention is not yet required.

## Operator → Client Portal: Work Payment

- **Producer:** authorized operator.
- **Consumer:** Client Portal Payments area and derived work balance.
- **Required data:** project identity, stable payment identity, amount, payment
  date, descriptive reference, and recording provenance.
- **Business guarantees:** one payment fact contributes once to payments total;
  it does not create a factura or accounting posting.
- **Invalid states:** unknown or archived project, invalid amount, missing
  payment identity, or representation as an invoice.
- **Idempotency expectation:** replay of the same payment identity does not
  increase payments total twice.
- **Provenance:** recording time and operator/source reference remain
  traceable.

## PresuPro → Client Portal: Approved Estimate Snapshot — future

**NOT AVAILABLE**

- **Producer:** future PresuPro approval/publication boundary.
- **Consumer:** Client Portal Budget area.
- **Required data:** project identity, estimate identity, immutable version,
  approval status/time/actor, currency and tax meaning, stable ordered section
  identity, planned materials and planned work by section, totals, and source
  provenance.
- **Business guarantees:** the snapshot is immutable, explicitly approved for
  portal use, addressable by project and version, and distinct from a factura.
- **Invalid states:** draft or mutable estimate, missing version or approval
  provenance, project mismatch, unstable section identity, or Holded payload
  substituted for the snapshot.
- **Idempotency expectation:** importing the same approved version repeatedly
  produces one imported budget version; conflicting content for the same
  identity/version is rejected.
- **Provenance:** estimate identity, exact version, approval facts, PresuPro
  source, and portal import time remain distinguishable.

The manual-to-imported migration and publication authority remain open and
must be resolved before this future contract becomes available.
