# Client Portal External Boundaries

## Status and classification

**Audited requirements baseline**

This document separates implemented external facts from Client Portal
requirements and future contracts:

- **CONFIRMED** means available in the inspected sandbox code.
- **REQUIRED** means behavior Client Portal must enforce at its boundary.
- **NOT AVAILABLE** means the needed external contract does not exist yet.

## Registry

### Confirmed active-project list

**CONFIRMED:** Registry provides an active-project list containing:

```text
project_id: UUID
display_name
status
```

The current Registry status set is `active` and `archived`; the active list
contains only active references.

### Confirmed project context

**CONFIRMED:** Registry provides current project context containing:

```text
project_id
display_name
status
address
customer_ref
created_at
registry_updated_at
```

`customer_ref` is optional and is not a complete client or accounting record.
Registry remains the source of truth for these current project values.

### Confirmed project-reference validation

**CONFIRMED:** Registry provides reference validation containing:

```text
project_id
exists
status
is_active
failure
```

Validation distinguishes an active project, an archived project, and an
unknown project. A missing context read and a negative validation result have
different external semantics.

### Additional confirmed Registry data

Registry also exposes project rooms and published artifact references. These
capabilities are not required for the first Client Portal MVP. A Registry
artifact reference is not the approved estimate snapshot itself, and Registry
artifact version must not be treated as PresuPro estimate version.

### Client Portal requirements for Registry

- **REQUIRED:** Registry is the sole source of project identity.
- **REQUIRED:** Client Portal never creates `project_id`.
- **REQUIRED:** Every incoming project reference is checked against Registry;
  client-supplied project names or addresses are not authoritative.
- **REQUIRED:** An unknown project is rejected.
- **REQUIRED:** Registry status controls permission to change portal data.
- **REQUIRED:** An archived project and its history remain readable.
- **REQUIRED:** An archived project accepts no new portal mutations.

### Current Registry limitations

- No production authentication or service-authorization contract is
  confirmed.
- No pagination or stable external ordering contract is confirmed for the
  active-project list.
- Registry has no paused or completed project status.
- Registry context has no project currency, planned dates, human-readable
  project code, or revision.

Evidence baseline:

- `projects/registry_sandbox/api/runtime.py`;
- `projects/registry_sandbox/core/models.py`;
- `projects/registry_sandbox/services/registry/project_service.py`;
- `projects/registry_sandbox/tests/test_project_identity_boundaries.py`.

## OCR Service and Telegram Intake

### Agreed ownership boundary

- **REQUIRED:** OCR is a separate external microservice.
- **REQUIRED:** Telegram bot is an intake interface and owns no OCR logic.
- **REQUIRED:** The OCR service owns source pages, their order, OCR provenance,
  confidence, and duplicate detection within the recognition domain.
- **REQUIRED:** Client Portal neither performs OCR nor depends on a particular
  OCR provider or model.
- **REQUIRED:** Project selection, business confirmation of the Expense, and
  allocation to Budget Sections or `Other expenses` remain outside OCR-service
  responsibility.

### Stable normalized recognition boundary

Client Portal accepts only a confirmed normalized recognition result with the
business meaning of:

```text
recognized_document_id
document_reference
document_type
supplier
document_date
currency
total_amount
normalized_items
recognition_status
confirmed_at
contract_version
```

The boundary may carry a portable provenance reference, but it does not expose
provider-specific responses, raw provider payloads, confidence details, or OCR
credentials to Client Portal.

The Client Portal OCR adapter is required to:

- validate `recognized_document_id`, confirmation state, completeness, and the
  supported contract version;
- transform normalized external values into the portal's internal Expense
  intake representation;
- preserve recognition provenance and the original document reference;
- prevent one recognized document from creating more than one Expense;
- reject an unsupported contract version or incomplete result;
- discard confidence, provider-specific fields, and raw model responses when
  they have no Client Portal business meaning.

Accounting, Holded, and future reuse of normalized documents by other
applications are outside the current OCR-to-Client-Portal integration and MVP.

## PresuPro

### Confirmed mutable estimate data

**CONFIRMED:** The current PresuPro estimate exposes:

- `estimate.id`;
- client name and optional fiscal client data;
- `project_type`;
- mutable status;
- creation and update timestamps;
- ordered zones;
- positions inside each zone;
- mutable position type, including the current `labor` total classification;
- material reference and item name;
- quantity and unit;
- unit price;
- waste percentage;
- margin percentage;
- IVA percentage;
- discount percentage;
- an optional Registry project snapshot.

The Registry snapshot is resolved server-side for linked estimates, while a
standalone estimate can retain PresuPro client data without Registry. This
does not make the estimate a published Client Portal budget.

### Confirmed current totals

**CONFIRMED:** PresuPro calculates whole-estimate totals containing:

```text
materials_subtotal
labor_subtotal
margin_total
discount_total
taxable_subtotal
iva_total
iva_breakdown
grand_total
currency
```

The current implementation returns currency `EUR`, uses mutable estimate data,
and does not expose authoritative planned material/work totals per
client-facing section.

### PresuPro limitation

**REQUIRED:** Client Portal treats the current estimate as internal mutable
PresuPro state. It is not a published portal budget and must not silently
replace a manual or previously imported portal budget.

The following are **NOT AVAILABLE**:

- `approved` as a closed client-publication status;
- estimate version identity;
- an immutable approved snapshot;
- approval timestamp;
- approval actor or source;
- stable section codes;
- ready-made planned materials and planned works by portal section;
- safe lookup of a published estimate by `project_id`;
- idempotent publication of one approved version;
- a Client Portal authorization contract.

Evidence baseline:

- `projects/PresuPro_sandbox/core/models.py`;
- `projects/PresuPro_sandbox/backend/api/routes.py`;
- `projects/PresuPro_sandbox/backend/services/estimates.py`;
- `projects/PresuPro_sandbox/backend/adapters/registry.py`;
- `projects/PresuPro_sandbox/tests/test_registry_project_integration.py`.

### Temporary manual-budget mode

**REQUIRED FOR MVP:** A manually supplied portal budget is allowed until the
published PresuPro boundary exists. Manual entry is a real temporary source,
not evidence that PresuPro approved the budget.

### Future approved-estimate boundary

**NOT AVAILABLE:** PresuPro must eventually provide the business capability to
retrieve an approved immutable estimate snapshot by `project_id` and, when
needed, by a specific version. The later contract must preserve exact source
and approval provenance and must not return the latest mutable row merely
because it exists.

No transport shape, program signature, or lifecycle detail is decided here.

### Deferred presupuesto/factura relationship

```text
approved presupuesto

is not

created factura
```

An approved presupuesto must eventually be able to appear in Client Portal
before a factura exists. The detailed approval, publication, replacement, and
factura lifecycle will be designed separately.
