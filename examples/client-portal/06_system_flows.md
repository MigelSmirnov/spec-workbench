# Client Portal User and Integration Flows

## Status

**Requirements baseline; implementation orchestration is not defined**

## Open project portal

```text
Client opens portal for one project
→ project reference is validated through Registry
→ current project context is loaded
→ active or archived portal mode is determined
→ dashboard is displayed
```

An unknown project does not open a portal. Registry unavailability is shown as
an external dependency failure, not as fabricated project context. An archived
project opens in read-only mode.

## Add confirmed expense

```text
Telegram bot receives a document as an intake interface
→ document is submitted to the external OCR Service
→ OCR Service produces a normalized recognized document
→ operator confirms the Expense and selects project and manual allocation
→ confirmed normalized result and operator context reach Client Portal OCR adapter
→ adapter validates recognized_document_id, contract version, and completeness
→ adapter preserves provenance and document reference and prepares Expense intake
→ Client Portal validates the active project and allocation total
→ one idempotent Expense is created
→ derived financial totals are recalculated
```

Unconfirmed OCR output is never a portal Expense. Repeated delivery of the same
`recognized_document_id` does not create a duplicate Expense or Document. OCR
provider/model details, confidence, and raw responses do not enter the portal.

## Miscellaneous expense

```text
Receipt has no useful itemization
→ operator selects Other expenses
→ Expense is confirmed
→ Expense contributes to the included project total
→ amount is shown separately under Other expenses
```

## Split expense

```text
One Document
→ one Expense
→ several manual Expense Allocations
→ allocation sum must equal Expense total
```

No automatic proportional split is performed, and the Document is not copied
for each allocation.

## Update work progress

```text
Operator selects a Budget Section with planned work
→ operator enters completion percentage
→ completed work value is recalculated
→ overall cost-weighted progress is recalculated
```

Photographs do not set the completion percentage.

## Register payment

```text
Operator records a Work Payment
→ payments total is recalculated
→ work balance is recalculated
→ positive or negative balance meaning is displayed
```

This flow records a portal payment fact only; it does not create a factura or
an accounting entry.

## Publish progress photo

```text
Photo arrives through Telegram intake
→ project is selected
→ optional Budget Section and caption are added
→ prepared photo reference is sent to Client Portal
→ photo appears in the chronological client gallery
```

The photo binary stays outside the Progress Photo business record. Repeated
delivery of the same intake item does not create a duplicate photo.

## Archive project

```text
Registry status becomes archived
→ portal remains readable
→ all portal mutation operations are blocked
→ historical records remain available
```

Archival does not by itself close client access; that policy remains open.

## Future approved budget import

**NOT AVAILABLE**

```text
PresuPro explicitly approves presupuesto for portal publication
→ immutable approved snapshot is created
→ Client Portal imports the exact approved version
→ source, version, approval, and import provenance are recorded
```

The transition from an existing manual budget is explicit and remains an open
product decision. This flow does not create or depend on a factura lifecycle.
