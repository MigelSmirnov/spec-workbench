# External Boundaries

## Status

**Audited baseline, reconciled with the current sandbox boundaries**

The original evidence report is
`../code_factory/client_portal_external_contract_audit.md` in the sibling AI
Code Factory repository. Registry and PresuPro received additive integration
work after that audit; the current typed boundaries below supersede the older
"missing dedicated validation" and "client-supplied Registry snapshot"
findings. The approved-estimate findings remain unresolved.

## Registry

### Current available contracts

Registry exposes these typed HTTP reads:

```text
GET /projects/active
  -> list[ProjectReference]

GET /projects/{project_id}/validate
  -> ProjectValidationResult

GET /projects/{project_id}/context
  -> ProjectContext
```

The corresponding service operations are `list_active_projects`,
`validate_project_reference`, and `get_project_context`. Cross-application
consumers use the HTTP boundary, not Registry's database or repository methods.

### Current `ProjectContext`

```text
ProjectReference
  project_id: UUID
  display_name: str
  status: str

ProjectContext
  project: ProjectReference
  address: str
  customer_ref: str | None
  created_at: datetime
  registry_updated_at: datetime

ProjectValidationResult
  project_id: UUID
  exists: bool
  status: str | None
  is_active: bool
  failure: str | None
```

### Confirmed invariants

- Registry creates the UUID `project_id`; create and update requests cannot
  supply or replace it.
- Renaming or updating project context does not change `project_id` through the
  public boundary.
- The current closed project status set is `active` and `archived`.
- `/projects/active` returns only active project references.
- Validation distinguishes active, archived, and missing references without
  requiring direct database access.
- A missing context read returns 404; a missing validation read returns a typed
  negative result.
- Archived projects are excluded from the active list and cannot receive new
  Registry rooms or published Registry artifacts.
- Registry owns current project context. Downstream copies are snapshots, not
  independently editable current project records.

Current evidence:

- `projects/registry_sandbox/core/models.py`;
- `projects/registry_sandbox/services/registry/project_service.py`;
- `projects/registry_sandbox/api/runtime.py`;
- `projects/registry_sandbox/tests/test_project_identity_boundaries.py`.

### Current limitations

- No authentication or service-authorization contract is implemented by the
  sandbox HTTP boundary.
- Active-project reads have no pagination contract.
- No stable external sorting guarantee is declared for the active list.
- Registry has no paused or completed project status.
- Registry project context has no project currency, planned start/end dates,
  human-readable project code, or revision/version.
- Successful context retrieval does not itself grant permission for a consumer
  to create new linked data.
- Registry's estimate artifact record stores a reference, not the immutable
  presupuesto snapshot itself; its artifact version must not be treated as a
  PresuPro estimate version.

## PresuPro

### Current mutable estimate capabilities

PresuPro currently owns an editable `Estimate` identified by a string ID. It
contains ordered `EstimateZone` values, each containing `EstimateItem` values.
New estimates begin with status `draft`; updates replace the current stored
record for the same estimate ID. There is no retained estimate revision
history.

PresuPro supports two project-link modes:

- standalone estimates omit `project_id` and keep their own client data without
  calling Registry;
- Registry-linked estimates accept `project_id`, validate and fetch context
  server-side, and store a `RegistryProjectSnapshot` while retaining independent
  PresuPro client data.

Client-supplied `registry_project` snapshots are rejected. A linked request
maps Registry not-found, inactive, and dependency failures to distinct HTTP
outcomes.

### Current available totals

`EstimateTotals` currently exposes:

```text
materials_subtotal: float
labor_subtotal: float
margin_total: float
taxable_subtotal: float
iva_total: float
grand_total: float
currency: str = "EUR"
discount_total: float
iva_breakdown: dict[str, float]
```

The calculation distinguishes labor only when `EstimateItem.type == "labor"`;
other item types contribute to materials. It applies waste, discount, margin,
and IVA using float arithmetic and rounded amounts. These are whole-estimate
totals. Authoritative material/work totals per zone are not currently exposed.

Current read capabilities include the mutable estimate, its current totals,
and filtered estimate lists. They do not provide an immutable approved version
for a project.

Current evidence:

- `projects/PresuPro_sandbox/core/models.py`;
- `projects/PresuPro_sandbox/backend/services/estimates.py`;
- `projects/PresuPro_sandbox/backend/api/routes.py`;
- `projects/PresuPro_sandbox/backend/adapters/registry.py`;
- `projects/PresuPro_sandbox/tests/test_registry_project_integration.py`.

### Current limitations

- Estimate status remains an unrestricted runtime string; there is no enforced
  approval lifecycle or transition graph.
- Status `accepted` is required for Holded conversion, but does not create an
  immutable approved portal snapshot.
- There is no estimate version/revision or retained history for overwritten
  estimates.
- There is no `approved_at` or approval provenance.
- Zones have a name and list position, but no stable section ID/code or explicit
  sort-order field.
- Per-zone material and work planned amounts are not exposed as authoritative
  values.
- Currency is hard-coded in calculated totals rather than carried by a
  versioned approved snapshot.
- IVA values exist, but an explicit tax-inclusion mode does not.
- Physical deletion and current-record replacement are incompatible with an
  immutable publication history.
- There is no Client Portal publication operation or stored publication
  snapshot.

### Missing published estimate contract

PresuPro does not currently expose an immutable, versioned, approved estimate
snapshot. Therefore Client Portal must not use any of these as its canonical
published budget:

- the current mutable `Estimate` record;
- `status == "accepted"` by itself;
- an invoicing preview;
- a Holded document payload;
- a Registry estimate-artifact reference without a PresuPro snapshot.

### Current temporary manual-budget mode

For the pilot, budget information is supplied manually within the Client Portal
product boundary. This is a temporary source, not a PresuPro-approved snapshot
and not evidence of approval. Its data model and migration behavior remain for
later design states.

### Future required `get_approved_estimate()` contract

PresuPro will need a public read operation named conceptually
`get_approved_estimate()`. It must provide a retained immutable approved version
suitable for Client Portal rather than the latest mutable row or a provider
payload.

The operation's arguments, output model, version-selection semantics, approval
provenance, section identity, tax semantics, error behavior, and publication
policy are intentionally not defined here. They depend on unresolved PresuPro
business decisions and later Client Portal design states.

### Deferred presupuesto/factura decision

```text
approved estimate

!=

factura
```

The current baseline must not equate approval or portal publication with Holded
invoice creation. The exact lifecycle relationship between an approved
presupuesto and a factura is intentionally postponed.
