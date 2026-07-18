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
Telegram intake receives a document
→ OCR is performed locally outside Client Portal
→ operator confirms the extracted expense data
→ project and manual allocation are selected
→ confirmed Expense and one Document reference are sent to Client Portal
→ Client Portal validates the active project and the allocation total
→ derived financial totals are recalculated
```

Unconfirmed OCR output is never a portal Expense. Repeated delivery of the same
confirmed result does not create a duplicate Expense or Document.

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
