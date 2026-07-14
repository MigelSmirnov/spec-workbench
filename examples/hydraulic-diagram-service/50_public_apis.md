# State 5 — Public module APIs

## Goal

This state defines the transport-neutral public operations exposed by each deep module.

It does not yet define every internal helper or final Python signature. The purpose is to establish stable cross-module needs before contracts are generated.

A public operation must:

- have a clear owner;
- serve a real caller;
- use concrete domain or application models;
- produce an observable result;
- preserve module boundaries;
- avoid exposing internal sequencing.

---

# 1. Boundary and application DTOs

## `DiagramSummary`

Purpose: compact discovery record for list operations.

```text
diagram_id: str
object_id: str
name: str
system_kind: DiagramSystemKind
status: DiagramStatus
current_revision: int
updated_at: datetime
```

## `CatalogSnapshot`

Purpose: immutable set of exact catalog definitions needed to validate or interpret one diagram revision.

```text
element_definitions: list[ElementDefinition]
connection_definitions: list[ConnectionTypeDefinition]
```

Invariants:

- contains exact referenced versions;
- may also contain currently available definitions for authoring when explicitly requested;
- duplicate definition/version pairs are forbidden.

## `DiagramWorkspace`

Purpose: transport-neutral editor/agent workspace.

```text
diagram: Diagram
current_revision: DiagramRevision | None
catalog: CatalogSnapshot
available_element_definitions: list[ElementDefinition]
available_connection_definitions: list[ConnectionTypeDefinition]
```

It must not contain React Flow nodes or edges.

## `ValidationIssue`

```text
code: str
severity: ValidationSeverity
message: str
entity_type: SourceEntityType | None
entity_id: str | None
property_code: str | None
```

Candidate severities:

```text
warning
blocking
```

## `ValidationReport`

```text
issues: list[ValidationIssue]
is_valid: bool
```

`is_valid` is true only when no blocking issues exist.

## `WorkingDiagramResult`

```text
revision_base: int
working_elements: list[DiagramElement]
working_connections: list[DiagramConnection]
working_layout: DiagramLayout
validation: ValidationReport
```

## `CommitRevisionResult`

```text
diagram: Diagram
revision: DiagramRevision
```

## `Page[T]`

```text
items: list[T]
next_cursor: str | None
```

This is a boundary/application pagination model, not a domain entity.

---

# 2. Typed authoring commands

The public authoring API uses a closed command set instead of generic JSON patches.

## `AddElementCommand`

```text
element_id: str
definition: DefinitionRef
label: str | None
quantity: Decimal
properties: list[PropertyValue]
layout: ElementLayout | None
```

## `SetElementPropertiesCommand`

```text
element_id: str
properties: list[PropertyValue]
```

The command replaces the supplied property codes only; full replacement semantics must be explicit in contracts/notes.

## `RemoveElementCommand`

```text
element_id: str
```

Removal policy for attached connections is owned by `diagram` and must not be chosen by transport.

## `AddConnectionCommand`

```text
connection_id: str
source: PortRef
target: PortRef
connection_type: DefinitionRef
properties: list[PropertyValue]
layout: ConnectionLayout | None
```

## `SetConnectionPropertiesCommand`

```text
connection_id: str
properties: list[PropertyValue]
```

## `RemoveConnectionCommand`

```text
connection_id: str
```

## `UpdateLayoutCommand`

```text
layout: DiagramLayout
```

## `AuthoringCommand`

Closed union of the commands above.

Placeholder rule:

- no `operation: str` plus arbitrary `payload: dict`;
- each command has a concrete schema and intent.

---

# 3. `catalog` public API

## `resolve_catalog_snapshot`

### Caller

`application`, `revision`, `estimation_data` orchestration.

### Input concept

```text
definition_refs: list[DefinitionRef]
```

### Output

```text
CatalogSnapshot
```

### Observable guarantee

Returns every exact requested version or a specific missing-definition failure.

## `list_available_definitions`

### Caller

Editor workspace and diagram-authoring agent.

### Input concept

```text
object_id: str
diagram_id: str
include_drafts: bool
```

### Output

```text
CatalogSnapshot
```

### Guarantee

Applies scope and status visibility rules.

## `create_element_definition_draft`

### Input

Concrete `CreateElementDefinitionDraft` DTO containing definition fields, scope, and actor.

### Output

`ElementDefinition(status=draft)`.

### Guarantee

Validates structure, uniqueness, scope, and provenance.

## `create_connection_definition_draft`

Same responsibility for `ConnectionTypeDefinition`.

## `transition_definition_status`

### Input concept

```text
definition: DefinitionRef
target_status: DefinitionStatus
actor: ActorRef
```

### Output

Updated immutable definition version or lifecycle result.

### Guarantee

Enforces allowed transitions and activation authority.

## Public API review

The module does not expose separate public functions to add ports, properties, or estimation refs. Draft creation owns the complete definition boundary.

---

# 4. `diagram` public API

## `create_diagram`

### Input concept

```text
object_id
name
system_kind
actor
```

### Output

`Diagram`.

### Guarantee

Creates a draft diagram with `current_revision = 0`.

## `apply_authoring_command`

### Input concept

```text
base_revision: DiagramRevision | None
command: AuthoringCommand
catalog: CatalogSnapshot
```

### Output

`WorkingDiagramResult`.

### Guarantee

Applies one typed command while preserving aggregate consistency and returning validation findings.

## `apply_authoring_commands`

### Input concept

```text
base_revision: DiagramRevision | None
commands: list[AuthoringCommand]
catalog: CatalogSnapshot
```

### Output

`WorkingDiagramResult`.

### Decision

Batch application is public because agents may construct a coherent multi-step change. The operation must be deterministic and fail according to an explicit atomic-versus-partial policy in State 6.

## `change_diagram_status`

### Input

```text
diagram: Diagram
target_status: DiagramStatus
actor: ActorRef
```

### Output

Updated `Diagram`.

### Guarantee

Applies only allowed lifecycle transitions.

## Public API review

Low-level functions such as `find_element`, `remove_attached_edges`, or `replace_property` remain private.

---

# 5. `diagram_policy` public API

## `validate_working_diagram`

### Input

```text
elements
connections
catalog
stage: ValidationStage
```

### Output

`ValidationReport`.

Candidate stages:

```text
draft
commit
activation
estimation
```

### Guarantee

Runs structure, property, compatibility, and stage-specific checks.

## `validate_definition_use`

### Input

```text
definition
object_id
diagram_id
operation_stage
```

### Output

`ValidationReport`.

### Guarantee

Evaluates scope and status permission for use.

## Public API review

Individual medium, flow, port, and property validators remain internal. Callers request policy decisions, not rule fragments.

---

# 6. `layout` public API

## `validate_layout`

### Input

```text
layout: DiagramLayout
element_ids: set[str]
connection_ids: set[str]
```

### Output

`ValidationReport`.

## `normalize_layout`

### Input

`DiagramLayout`.

### Output

Normalized `DiagramLayout`.

### Guarantee

Normalizes rotation, coordinates, viewport, and route point representation without changing engineering structure.

## `create_default_layout`

### Input concept

```text
elements
connections
catalog
```

### Output

`DiagramLayout`.

### Status

Provisional. Include only if agent-created diagrams must be viewable without supplied layout in v1.

---

# 7. `revision` public API

## `commit_revision`

### Input concept

```text
diagram: Diagram
expected_current_revision: int
working: WorkingDiagramResult
actor: ActorRef
change_source: ChangeSource
change_summary: str | None
```

### Output

`CommitRevisionResult`.

### Guarantee

- reruns commit-stage validation through owned collaborators;
- creates one immutable snapshot;
- increments revision monotonically;
- atomically updates `Diagram.current_revision`;
- rejects stale expected revisions.

## `get_revision`

### Input

```text
diagram_id
revision
```

### Output

`DiagramRevision`.

## `get_current_revision`

### Input

`diagram_id`.

### Output

`DiagramRevision | None`.

## `list_revisions`

### Input

```text
diagram_id
cursor
page_size
```

### Output

`Page[DiagramRevisionSummary]`.

## Public API review

Revision numbering, transaction handling, and snapshot persistence remain hidden.

---

# 8. `estimation_data` public API

## `build_estimation_data`

### Input

```text
revision: DiagramRevision
catalog: CatalogSnapshot
collector_rule_version: str
```

### Output

`EstimationDataPackage`.

### Guarantee

- validates integrity required for collection;
- groups estimate-relevant elements and connections;
- builds supported measurements;
- reports blocking missing requirements;
- preserves provenance;
- produces stable ordering;
- never invents missing values;
- never adds price or retailer data.

## Diagnostic projection policy

`get_missing_estimation_requirements` should not be a second collector implementation. Application or transport may return `package.missing_requirements` from the main result.

## Public API review

One primary operation confirms that this is a deep module.

---

# 9. `change_requests` public API

## `create_change_request`

### Input

```text
diagram_id
base_revision
requested_by
reason_code
reason
changes
```

### Output

`DiagramChangeRequest(status=open)`.

## `transition_change_request`

### Input

```text
request
target_status
actor
resulting_revision | None
```

### Output

Updated `DiagramChangeRequest`.

### Guarantee

Enforces request lifecycle and links `applied` status to a resulting revision.

## `get_change_request`

Returns one request by ID.

---

# 10. Repository ports

Repository interfaces express domain needs and are public only to application/revision modules.

## `DiagramRepository`

```text
get(diagram_id) -> Diagram | None
save(diagram) -> None
list_by_object_id(object_id, cursor, page_size) -> Page[DiagramSummary]
```

## `RevisionRepository`

```text
get(diagram_id, revision) -> DiagramRevision | None
get_current(diagram_id) -> DiagramRevision | None
list(diagram_id, cursor, page_size) -> Page[DiagramRevisionSummary]
append(revision) -> None
```

## `CatalogRepository`

```text
get_element_definition(ref) -> ElementDefinition | None
get_connection_definition(ref) -> ConnectionTypeDefinition | None
list_visible_definitions(object_id, diagram_id, include_drafts) -> CatalogSnapshot
save_element_definition(definition) -> None
save_connection_definition(definition) -> None
```

## `ChangeRequestRepository`

```text
get(request_id) -> DiagramChangeRequest | None
save(request) -> None
```

## `UnitOfWork`

```text
begin
commit
rollback
```

The final Python shape may be a context manager. The semantic requirement is one atomic revision transaction.

## Placeholder resistance

No generic `Repository[T]` is introduced.

---

# 11. External ports

## `ObjectGateway`

```text
get_object_snapshot(object_id) -> ObjectSnapshot
```

`ObjectSnapshot` remains undefined until real integration evidence is available.

For v1, application policy may allow object verification to be disabled through config while still requiring `object_id`.

## `CapabilityAuthorizer`

Purpose: transport-neutral authorization decision.

Candidate operation:

```text
require_capability(actor, capability, resource_ref) -> None
```

Candidate capabilities:

```text
diagram.read
diagram.author
diagram.archive
catalog.read
catalog.draft.create
catalog.activate.local
catalog.activate.global
estimation.read
change_request.create
change_request.review
```

Exact identity and tenancy semantics remain external.

---

# 12. `application` public use cases

These are the operations called by HTTP and MCP boundaries.

## Diagram discovery and reading

```text
create_diagram
get_diagram_workspace
get_diagram_revision
list_diagram_revisions
list_object_diagrams
```

## Authoring

```text
apply_diagram_command
apply_diagram_commands
commit_diagram_revision
change_diagram_status
```

## Catalog

```text
list_available_definitions
create_element_definition_draft
create_connection_definition_draft
transition_definition_status
```

## Estimation data

```text
build_diagram_estimation_data
inspect_estimation_source
```

## Change requests

```text
create_diagram_change_request
transition_diagram_change_request
get_diagram_change_request
```

### Application API rule

Each use case:

- authorizes one capability;
- loads required state through ports;
- calls domain owners;
- persists through repository ports;
- returns transport-neutral models;
- does not contain duplicated domain rules.

---

# 13. HTTP surface candidate

Routes are illustrative and not yet contracts.

```text
POST   /diagrams
GET    /diagrams/{diagram_id}
GET    /objects/{object_id}/diagrams
GET    /diagrams/{diagram_id}/revisions
GET    /diagrams/{diagram_id}/revisions/{revision}
POST   /diagrams/{diagram_id}/commands
POST   /diagrams/{diagram_id}/revisions
PATCH  /diagrams/{diagram_id}/status
GET    /diagrams/{diagram_id}/revisions/{revision}/estimation-data

GET    /catalog/definitions
POST   /catalog/elements/drafts
POST   /catalog/connections/drafts
POST   /catalog/definitions/{definition_id}/versions/{version}/status

POST   /diagram-change-requests
GET    /diagram-change-requests/{request_id}
POST   /diagram-change-requests/{request_id}/status
```

HTTP handlers call application use cases only.

---

# 14. MCP surface candidate

## Read tools

```text
list_object_diagrams
get_diagram_workspace
get_diagram_revision
build_estimation_data
inspect_estimation_source
list_available_definitions
```

## Authoring tools

```text
create_diagram
apply_diagram_command
apply_diagram_commands
commit_diagram_revision
create_element_definition_draft
create_connection_definition_draft
```

## Change-request tools

```text
create_diagram_change_request
get_diagram_change_request
```

Capability exposure determines which tools an agent receives.

MCP tools must not bypass the application API.

---

# 15. Public API placeholder review

## Rejected APIs

```text
save_diagram(data: dict)
process_diagram(payload: Any)
validate(data: dict)
get_estimator_data() -> list[dict]
agent_action(name: str, payload: dict)
update_definition(metadata: dict)
```

## Why rejected

They preserve unresolved schema, ownership, lifecycle, or result semantics.

## Remaining decisions for contracts

- exact Python representation of command unions;
- atomic or partial behavior for command batches;
- whether working drafts are client-held or server-held;
- exact application result/error model;
- exact `ObjectSnapshot` contract;
- idempotency input model;
- exact pagination cursor type;
- whether `create_default_layout` is v1;
- whether change requests are v1 or deferred.

---

## State 5 readiness assessment

State 5 is sufficiently stable to begin exact contract design because:

- every public operation has a clear owner and caller;
- cross-module data shapes are concrete;
- authoring uses typed commands;
- catalog, revision, and estimation internals remain hidden;
- HTTP and MCP share one application API;
- estimator data has one canonical builder;
- repository ports express domain needs rather than generic persistence;
- unresolved integration details remain localized.
