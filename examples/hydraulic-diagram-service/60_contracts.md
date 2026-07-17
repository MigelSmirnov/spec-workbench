# State 6 — Exact contracts and generation units

## Goal

This state converts the approved models, module boundaries, flows, Pydantic schemas, and PostgreSQL strategy into exact Python contracts.

The contracts below are transport-neutral unless explicitly marked as HTTP, MCP, SQLAlchemy, or gateway infrastructure.

The first version targets:

```text
Python 3.12+
Pydantic 2.x
SQLAlchemy 2.x
PostgreSQL
```

All domain and application data types referenced below are the Pydantic models defined in `57_pydantic_schemas.md`.

---

# 1. Contract conventions

## IDs

Use `str` at domain boundaries. Persistence adapters may use PostgreSQL UUID columns internally, but must convert to and from the domain string representation.

## Time

Use timezone-aware `datetime` values in UTC.

## Numeric values

Use `Decimal` for quantities, dimensions, measurements, and property values that may affect estimation.

## Failures

Domain and application functions raise explicit domain exceptions for exceptional failures.

Validation that is a normal business outcome returns `ValidationReport` or `EstimationDataPackage(status="incomplete" | "invalid")`.

## Mutation

Pydantic domain models are treated as immutable. Functions return new models rather than mutating inputs.

---

# 2. Exception contracts

Generation unit:

```text
errors
→ hydraulic_diagram/domain/errors.py
```

```python
class DomainError(Exception): ...
class NotFoundError(DomainError): ...
class ConflictError(DomainError): ...
class AuthorizationError(DomainError): ...
class IntegrityError(DomainError): ...
class IntegrationError(DomainError): ...
class PersistenceError(DomainError): ...
```

Required constructor shape:

```python
DomainError.__init__(self, code: str, message: str, entity_id: str | None = None) -> None
```

These exceptions must preserve stable machine-readable codes.

---

# 3. Model-generation contracts

Pydantic model classes are declared in `models`, not as function contracts. Validators that require explicit generated methods use these signatures.

All `model_*` headings in this section are authoring subdivisions assembled by
the Factory into the single deterministic runtime unit `core/models.py`; they
are not independent runtime import paths.

## `model_values`

```python
PropertyValue.validate_source_ref(self) -> PropertyValue
```

## `model_layout`

```python
ElementLayout.normalize_rotation(cls, value: int) -> int
DiagramLayout.validate_unique_references(self) -> DiagramLayout
```

## `model_catalog`

```python
ConnectionVisualDefinition.validate_color(cls, value: str) -> str
PropertyDefinition.validate_value_constraints(self) -> PropertyDefinition
PortDefinition.validate_allowed_connection_codes(self) -> PortDefinition
ElementDefinition.validate_definition_shape(self) -> ElementDefinition
ConnectionTypeDefinition.validate_definition_shape(self) -> ConnectionTypeDefinition
CatalogSnapshot.validate_unique_definition_refs(self) -> CatalogSnapshot
```

## `model_diagram`

```python
Diagram.validate_timestamps(self) -> Diagram
DiagramElement.validate_unique_properties(self) -> DiagramElement
DiagramConnection.validate_connection_shape(self) -> DiagramConnection
DiagramRevision.validate_unique_entities(self) -> DiagramRevision
```

## `model_application`

```python
ValidationReport.validate_is_valid(self) -> ValidationReport
WorkingDiagramResult.validate_unique_entities(self) -> WorkingDiagramResult
CommitRevisionResult.validate_revision_alignment(self) -> CommitRevisionResult
```

## `model_estimation`

```python
ElementEstimationItem.validate_item_shape(self) -> ElementEstimationItem
ConnectionEstimationItem.validate_item_shape(self) -> ConnectionEstimationItem
DiagramMeasurement.validate_sources(self) -> DiagramMeasurement
EstimationDataPackage.validate_package_status(self) -> EstimationDataPackage
```

## `model_change_requests`

```python
DiagramChangeRequest.validate_status_alignment(self) -> DiagramChangeRequest
```

Pydantic-decorated validator method forms may differ slightly in implementation, but semantic inputs and outputs must remain equivalent.

---

# 4. Catalog package

## Package facade

Generation unit:

```text
catalog
→ hydraulic_diagram/domain/catalog/__init__.py
```

Exports:

```python
resolve_catalog_snapshot
list_available_definitions
create_element_definition_draft
create_connection_definition_draft
transition_definition_status
```

## `catalog_lookup`

Path:

```text
hydraulic_diagram/domain/catalog/lookup.py
```

```python
resolve_catalog_snapshot(
    definition_refs: list[DefinitionRef],
    element_definitions: list[ElementDefinition],
    connection_definitions: list[ConnectionTypeDefinition],
) -> CatalogSnapshot

list_available_definitions(
    object_id: str,
    diagram_id: str,
    include_drafts: bool,
    element_definitions: list[ElementDefinition],
    connection_definitions: list[ConnectionTypeDefinition],
) -> CatalogSnapshot
```

Private helpers:

```python
_index_element_definitions(
    definitions: list[ElementDefinition],
) -> dict[tuple[str, int], ElementDefinition]

_index_connection_definitions(
    definitions: list[ConnectionTypeDefinition],
) -> dict[tuple[str, int], ConnectionTypeDefinition]

_is_definition_visible(
    status: DefinitionStatus,
    scope: DefinitionScope,
    scope_ref: str | None,
    object_id: str,
    diagram_id: str,
    include_drafts: bool,
) -> bool
```

## `catalog_drafts`

Path:

```text
hydraulic_diagram/domain/catalog/drafts.py
```

Draft input models must be added to `model_catalog`:

```python
class CreateElementDefinitionDraft(FrozenModel): ...
class CreateConnectionDefinitionDraft(FrozenModel): ...
```

Contracts:

```python
create_element_definition_draft(
    draft: CreateElementDefinitionDraft,
    actor: ActorRef,
    created_at: datetime,
    definition_id: str,
    version: int = 1,
) -> ElementDefinition

create_connection_definition_draft(
    draft: CreateConnectionDefinitionDraft,
    actor: ActorRef,
    created_at: datetime,
    definition_id: str,
    version: int = 1,
) -> ConnectionTypeDefinition
```

Private helpers:

```python
_validate_element_visual_asset(
    svg_markup: str,
) -> str

_validate_draft_scope(
    scope: DefinitionScope,
    scope_ref: str | None,
) -> None

_validate_element_draft_uniqueness(
    draft: CreateElementDefinitionDraft,
) -> None

_validate_connection_draft_uniqueness(
    draft: CreateConnectionDefinitionDraft,
) -> None
```

`_validate_element_visual_asset` returns the unchanged markup only after
enforcing the catalog SVG policy and `config.catalog.max_svg_markup_bytes`.
It is shared by agent-created drafts and the seed-import path through
`create_element_definition_draft`; it is not a Pydantic validator or a public
package-facade export.

## `catalog_lifecycle`

Path:

```text
hydraulic_diagram/domain/catalog/lifecycle.py
```

```python
transition_definition_status(
    definition: CatalogDefinition,
    target_status: DefinitionStatus,
    actor: ActorRef,
    allow_global_activation: bool,
) -> CatalogDefinition
```

Private helpers:

```python
_validate_definition_transition(
    current: DefinitionStatus,
    target: DefinitionStatus,
) -> None

_validate_activation_authority(
    definition: CatalogDefinition,
    actor: ActorRef,
    allow_global_activation: bool,
) -> None
```

---

# 5. Diagram policy package

## Facade

Path:

```text
hydraulic_diagram/domain/diagram_policy/__init__.py
```

Exports:

```python
validate_working_diagram
validate_definition_use
```

## `policy_properties`

```python
validate_property_values(
    properties: list[PropertyValue],
    definitions: list[PropertyDefinition],
    stage: ValidationStage,
    entity_type: SourceEntityType,
    entity_id: str,
) -> list[ValidationIssue]

validate_property_value(
    value: PropertyValue,
    definition: PropertyDefinition,
    entity_type: SourceEntityType,
    entity_id: str,
) -> list[ValidationIssue]
```

Private helpers:

```python
_matches_property_type(value: TypedValue, definition: PropertyDefinition) -> bool
_is_allowed_value(value: TypedValue, definition: PropertyDefinition) -> bool
_is_within_numeric_bounds(value: TypedValue, definition: PropertyDefinition) -> bool
```

## `policy_connections`

```python
validate_connection(
    connection: DiagramConnection,
    elements_by_id: dict[str, DiagramElement],
    catalog: CatalogSnapshot,
    connection_usage_by_port: dict[tuple[str, str], int],
) -> list[ValidationIssue]

validate_connection_compatibility(
    source_port: PortDefinition,
    target_port: PortDefinition,
    connection_type: ConnectionTypeDefinition,
) -> list[ValidationIssue]
```

Private helpers:

```python
_validate_medium_compatibility(
    source: MediumKind,
    target: MediumKind,
    connection: MediumKind,
) -> list[ValidationIssue]

_validate_flow_compatibility(
    source: FlowSemantics,
    target: FlowSemantics,
) -> list[ValidationIssue]

_validate_port_multiplicity(
    source: PortRef,
    target: PortRef,
    usage: dict[tuple[str, str], int],
) -> list[ValidationIssue]
```

## `policy_scope`

```python
validate_definition_use(
    definition: CatalogDefinition,
    object_id: str,
    diagram_id: str,
    stage: ValidationStage,
) -> ValidationReport
```

## `policy_report`

```python
validate_working_diagram(
    elements: list[DiagramElement],
    connections: list[DiagramConnection],
    catalog: CatalogSnapshot,
    stage: ValidationStage,
) -> ValidationReport
```

Private helpers:

```python
_build_element_index(elements: list[DiagramElement]) -> dict[str, DiagramElement]
_build_connection_usage(connections: list[DiagramConnection]) -> dict[tuple[str, str], int]
_sort_validation_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]
```

---

# 6. Layout package

Path:

```text
hydraulic_diagram/domain/layout.py
```

```python
validate_layout(
    layout: DiagramLayout,
    element_ids: set[str],
    connection_ids: set[str],
    max_route_points_per_connection: int,
) -> ValidationReport

normalize_layout(layout: DiagramLayout) -> DiagramLayout

create_default_layout(
    elements: list[DiagramElement],
    connections: list[DiagramConnection],
    catalog: CatalogSnapshot,
) -> DiagramLayout
```

`create_default_layout` remains optional for v1. If omitted, it must also be absent from `module_functions`, `imports.internal`, and notes.

Private helpers:

```python
_normalize_element_layout(item: ElementLayout) -> ElementLayout
_normalize_connection_layout(item: ConnectionLayout) -> ConnectionLayout
_validate_layout_references(
    layout: DiagramLayout,
    element_ids: set[str],
    connection_ids: set[str],
) -> list[ValidationIssue]
```

---

# 7. Diagram authoring package

## Facade

Path:

```text
hydraulic_diagram/domain/diagram/__init__.py
```

Exports:

```python
create_diagram
apply_authoring_command
apply_authoring_commands
change_diagram_status
```

## `diagram_creation`

```python
create_diagram(
    diagram_id: str,
    object_id: str,
    name: str,
    system_kinds: set[DiagramSystemKind],
    actor: ActorRef,
    created_at: datetime,
) -> Diagram

change_diagram_status(
    diagram: Diagram,
    target_status: DiagramStatus,
    updated_at: datetime,
) -> Diagram
```

## `diagram_commands`

```python
apply_authoring_command(
    base_revision: DiagramRevision | None,
    command: AuthoringCommand,
    catalog: CatalogSnapshot,
    validation_stage: ValidationStage = ValidationStage.DRAFT,
) -> WorkingDiagramResult

apply_authoring_commands(
    base_revision: DiagramRevision | None,
    commands: list[AuthoringCommand],
    catalog: CatalogSnapshot,
    validation_stage: ValidationStage = ValidationStage.DRAFT,
) -> WorkingDiagramResult
```

Batch semantics:

- commands are applied atomically in memory;
- if one command cannot be applied structurally, raise `DomainError` and return no partial result;
- validation issues that do not prevent command application are accumulated in the final `WorkingDiagramResult`.

## `diagram_elements`

```python
_add_element(
    elements: list[DiagramElement],
    command: AddElementCommand,
    catalog: CatalogSnapshot,
) -> list[DiagramElement]

_set_element_properties(
    elements: list[DiagramElement],
    command: SetElementPropertiesCommand,
) -> list[DiagramElement]

_remove_element(
    elements: list[DiagramElement],
    connections: list[DiagramConnection],
    layout: DiagramLayout,
    command: RemoveElementCommand,
) -> tuple[list[DiagramElement], list[DiagramConnection], DiagramLayout]
```

Removal policy:

- removing an element removes its attached connections and corresponding layout records in the same pure operation.

## `diagram_connections`

```python
_add_connection(
    connections: list[DiagramConnection],
    command: AddConnectionCommand,
    catalog: CatalogSnapshot,
) -> list[DiagramConnection]

_set_connection_properties(
    connections: list[DiagramConnection],
    command: SetConnectionPropertiesCommand,
) -> list[DiagramConnection]

_remove_connection(
    connections: list[DiagramConnection],
    layout: DiagramLayout,
    command: RemoveConnectionCommand,
) -> tuple[list[DiagramConnection], DiagramLayout]
```

## `diagram_working_state`

```python
_create_empty_working_result() -> WorkingDiagramResult

_create_working_result_from_revision(
    revision: DiagramRevision,
) -> WorkingDiagramResult

_apply_layout_command(
    result: WorkingDiagramResult,
    command: UpdateLayoutCommand,
) -> WorkingDiagramResult
```

---

# 8. Revision package

## Facade

Path:

```text
hydraulic_diagram/domain/revision/__init__.py
```

Exports:

```python
commit_revision
```

Queries remain application/repository operations rather than pure domain functions.

## `revision_commit`

```python
commit_revision(
    diagram: Diagram,
    expected_current_revision: int,
    working: WorkingDiagramResult,
    actor: ActorRef,
    change_source: ChangeSource,
    created_at: datetime,
    schema_version: int,
    change_summary: str | None,
    diagram_repository: DiagramRepository,
    revision_repository: RevisionRepository,
    unit_of_work: UnitOfWork,
) -> CommitRevisionResult
```

Private helpers:

```python
_validate_expected_revision(
    diagram: Diagram,
    expected_current_revision: int,
) -> None

_build_revision(
    diagram: Diagram,
    working: WorkingDiagramResult,
    actor: ActorRef,
    change_source: ChangeSource,
    created_at: datetime,
    schema_version: int,
    change_summary: str | None,
) -> DiagramRevision

_advance_diagram_revision(
    diagram: Diagram,
    revision: DiagramRevision,
) -> Diagram
```

The implementation must keep the transaction short and must not call external services inside the transaction.

---

# 9. Estimation-data package

## Facade

Path:

```text
hydraulic_diagram/domain/estimation_data/__init__.py
```

Exports only:

```python
build_estimation_data
```

## `estimation_collector`

```python
build_estimation_data(
    diagram: Diagram,
    revision: DiagramRevision,
    catalog: CatalogSnapshot,
    collector_rule_version: str,
    package_id: str,
    generated_at: datetime,
) -> EstimationDataPackage
```

Private orchestration helpers:

```python
_determine_package_status(
    validation: ValidationReport,
    requirements: RequirementAnalysis,
) -> EstimationPackageStatus
```

## `estimation_element_items`

```python
collect_element_items(
    elements: list[DiagramElement],
    catalog: CatalogSnapshot,
) -> list[ElementEstimationItem]

build_element_group_key(
    element: DiagramElement,
    definition: ElementDefinition,
) -> tuple[str, int, tuple[tuple[str, str], ...]]
```

Private helpers:

```python
_select_estimator_properties(
    properties: list[PropertyValue],
    definitions: list[PropertyDefinition],
) -> list[PropertyValue]

_merge_element_group(
    existing: ElementEstimationItem,
    element: DiagramElement,
) -> ElementEstimationItem
```

## `estimation_connection_items`

```python
collect_connection_items(
    connections: list[DiagramConnection],
    catalog: CatalogSnapshot,
) -> list[ConnectionEstimationItem]

build_connection_group_key(
    connection: DiagramConnection,
    definition: ConnectionTypeDefinition,
) -> tuple[str, int, str, tuple[tuple[str, str], ...]]
```

Private helpers:

```python
_resolve_connection_quantity(
    connection: DiagramConnection,
    definition: ConnectionTypeDefinition,
) -> tuple[Decimal, str]

_merge_connection_group(
    existing: ConnectionEstimationItem,
    connection: DiagramConnection,
    quantity: Decimal,
) -> ConnectionEstimationItem
```

## `estimation_measurements`

```python
collect_measurements(
    revision: DiagramRevision,
    catalog: CatalogSnapshot,
) -> list[DiagramMeasurement]

build_count_measurements(
    revision: DiagramRevision,
) -> list[DiagramMeasurement]

build_property_sum_measurements(
    revision: DiagramRevision,
    catalog: CatalogSnapshot,
) -> list[DiagramMeasurement]

build_explicit_property_measurements(
    revision: DiagramRevision,
    catalog: CatalogSnapshot,
) -> list[DiagramMeasurement]
```

No `layout_route_length` function exists in v1.

## `estimation_requirements`

Add internal Pydantic model:

```python
class RequirementAnalysis(FrozenModel):
    missing_requirements: list[MissingEstimationRequirement]
    warnings: list[EstimationWarning]
```

Contracts:

```python
analyze_estimation_requirements(
    revision: DiagramRevision,
    catalog: CatalogSnapshot,
) -> RequirementAnalysis

find_missing_element_requirements(
    elements: list[DiagramElement],
    catalog: CatalogSnapshot,
) -> list[MissingEstimationRequirement]

find_missing_connection_requirements(
    connections: list[DiagramConnection],
    catalog: CatalogSnapshot,
) -> list[MissingEstimationRequirement]
```

Private helpers:

```python
_deduplicate_requirements(
    requirements: list[MissingEstimationRequirement],
) -> list[MissingEstimationRequirement]

_sort_requirements(
    requirements: list[MissingEstimationRequirement],
) -> list[MissingEstimationRequirement]
```

## `estimation_assembly`

```python
assemble_estimation_package(
    package_id: str,
    diagram: Diagram,
    revision: DiagramRevision,
    collector_rule_version: str,
    status: EstimationPackageStatus,
    element_items: list[ElementEstimationItem],
    connection_items: list[ConnectionEstimationItem],
    measurements: list[DiagramMeasurement],
    requirements: RequirementAnalysis,
    generated_at: datetime,
) -> EstimationDataPackage
```

Private helpers:

```python
_sort_element_items(items: list[ElementEstimationItem]) -> list[ElementEstimationItem]
_sort_connection_items(items: list[ConnectionEstimationItem]) -> list[ConnectionEstimationItem]
_sort_measurements(items: list[DiagramMeasurement]) -> list[DiagramMeasurement]
```

---

# 10. Change-request package

This package is optional for v1. If included:

```python
create_change_request(
    request_id: str,
    diagram_id: str,
    base_revision: int,
    requested_by: ActorRef,
    reason_code: str,
    reason: str,
    changes: list[RequestedDiagramChange],
    created_at: datetime,
) -> DiagramChangeRequest

transition_change_request(
    request: DiagramChangeRequest,
    target_status: ChangeRequestStatus,
    resulting_revision: int | None = None,
) -> DiagramChangeRequest
```

Private helper:

```python
_validate_change_request_transition(
    current: ChangeRequestStatus,
    target: ChangeRequestStatus,
) -> None
```

---

# 11. Repository protocols

Generation unit:

```text
repository_ports
→ hydraulic_diagram/application/ports/repositories.py
```

Use `typing.Protocol`.

```python
class DiagramRepository(Protocol):
    def get(self, diagram_id: str) -> Diagram | None: ...
    def save(self, diagram: Diagram) -> None: ...
    def list_by_object_id(
        self,
        object_id: str,
        cursor: str | None,
        page_size: int,
    ) -> DiagramSummaryPage: ...

class RevisionRepository(Protocol):
    def get(self, diagram_id: str, revision: int) -> DiagramRevision | None: ...
    def get_current(self, diagram_id: str) -> DiagramRevision | None: ...
    def list(
        self,
        diagram_id: str,
        cursor: str | None,
        page_size: int,
    ) -> DiagramRevisionSummaryPage: ...
    def append(self, revision: DiagramRevision) -> None: ...

class CatalogRepository(Protocol):
    def get_element_definition(self, ref: DefinitionRef) -> ElementDefinition | None: ...
    def get_connection_definition(self, ref: DefinitionRef) -> ConnectionTypeDefinition | None: ...
    def list_visible_definitions(
        self,
        object_id: str,
        diagram_id: str,
        include_drafts: bool,
    ) -> CatalogSnapshot: ...
    def save_element_definition(self, definition: ElementDefinition) -> None: ...
    def save_connection_definition(self, definition: ConnectionTypeDefinition) -> None: ...

class ChangeRequestRepository(Protocol):
    def get(self, request_id: str) -> DiagramChangeRequest | None: ...
    def save(self, request: DiagramChangeRequest) -> None: ...

class UnitOfWork(Protocol):
    def __enter__(self) -> UnitOfWork: ...
    def __exit__(self, exc_type: object, exc: BaseException | None, tb: object) -> bool | None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

Use concrete page models instead of `Page[T]` unless factory support for Pydantic generics is confirmed:

```python
class DiagramSummaryPage(FrozenModel): ...
class DiagramRevisionSummaryPage(FrozenModel): ...
```

---

# 12. External ports

Generation unit:

```text
external_ports
→ hydraulic_diagram/application/ports/external.py
```

```python
class ObjectGateway(Protocol):
    def get_object_snapshot(self, object_id: str) -> ObjectSnapshot: ...
    def publish_diagram_index(
        self,
        object_id: str,
        index: DiagramIndexArtifact,
    ) -> None: ...

class CapabilityAuthorizer(Protocol):
    def require_capability(
        self,
        actor: ActorRef,
        capability: str,
        resource_id: str | None,
    ) -> None: ...
```

`ObjectSnapshot` is defined from Registry evidence (resolved 2026-07-15):
`object_id` plus `status: Literal["active", "archived"]`.
`DiagramIndexArtifact` is the payload of the per-project `hydraulic_diagram`
Registry artifact: the project's diagrams with their current committed
revisions. `publish_diagram_index` is invoked post-commit, outside the
transaction, and its failure is logged, never raised into the commit result.

Do not invent object or customer fields beyond this projection.

---

# 13. Application use cases

Generation units should be split by responsibility rather than one `use_cases.py` mega-file.

## `application_diagrams`

```python
create_diagram_use_case(
    object_id: str,
    name: str,
    system_kinds: set[DiagramSystemKind],
    actor: ActorRef,
    diagram_id: str,
    now: datetime,
    diagram_repository: DiagramRepository,
    authorizer: CapabilityAuthorizer,
    object_gateway: ObjectGateway | None,
) -> Diagram

get_diagram_workspace(
    diagram_id: str,
    actor: ActorRef,
    diagram_repository: DiagramRepository,
    revision_repository: RevisionRepository,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> DiagramWorkspace

list_object_diagrams(
    object_id: str,
    actor: ActorRef,
    cursor: str | None,
    page_size: int,
    diagram_repository: DiagramRepository,
    authorizer: CapabilityAuthorizer,
) -> DiagramSummaryPage

change_diagram_status_use_case(
    diagram_id: str,
    target_status: DiagramStatus,
    actor: ActorRef,
    now: datetime,
    diagram_repository: DiagramRepository,
    authorizer: CapabilityAuthorizer,
) -> Diagram
```

## `application_authoring`

```python
apply_diagram_command_use_case(
    diagram_id: str,
    base_revision: int,
    command: AuthoringCommand,
    actor: ActorRef,
    revision_repository: RevisionRepository,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> WorkingDiagramResult

apply_diagram_commands_use_case(
    diagram_id: str,
    base_revision: int,
    commands: list[AuthoringCommand],
    actor: ActorRef,
    revision_repository: RevisionRepository,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> WorkingDiagramResult

commit_diagram_revision_use_case(
    diagram_id: str,
    expected_current_revision: int,
    working: WorkingDiagramResult,
    actor: ActorRef,
    change_source: ChangeSource,
    change_summary: str | None,
    now: datetime,
    schema_version: int,
    diagram_repository: DiagramRepository,
    revision_repository: RevisionRepository,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
    unit_of_work: UnitOfWork,
    object_gateway: ObjectGateway,
) -> CommitRevisionResult
```

`object_gateway` serves only the post-commit Registry index publication; it
is never called while the unit of work is open.

## `application_catalog`

```python
list_available_definitions_use_case(
    object_id: str,
    diagram_id: str,
    include_drafts: bool,
    actor: ActorRef,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> CatalogSnapshot

create_element_definition_draft_use_case(
    draft: CreateElementDefinitionDraft,
    actor: ActorRef,
    definition_id: str,
    now: datetime,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> ElementDefinition

create_connection_definition_draft_use_case(
    draft: CreateConnectionDefinitionDraft,
    actor: ActorRef,
    definition_id: str,
    now: datetime,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> ConnectionTypeDefinition

transition_definition_status_use_case(
    definition_ref: DefinitionRef,
    definition_kind: Literal["element", "connection"],
    target_status: DefinitionStatus,
    actor: ActorRef,
    allow_global_activation: bool,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> CatalogDefinition
```

## `application_estimation`

```python
build_diagram_estimation_data(
    diagram_id: str,
    revision: int | None,
    actor: ActorRef,
    collector_rule_version: str,
    package_id: str,
    now: datetime,
    diagram_repository: DiagramRepository,
    revision_repository: RevisionRepository,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> EstimationDataPackage

inspect_estimation_source(
    diagram_id: str,
    revision: int,
    entity_type: SourceEntityType,
    entity_id: str,
    actor: ActorRef,
    revision_repository: RevisionRepository,
    catalog_repository: CatalogRepository,
    authorizer: CapabilityAuthorizer,
) -> EstimationSourceEntity
```

## `application_change_requests`

Optional v1 contracts:

```python
create_diagram_change_request_use_case(...) -> DiagramChangeRequest
transition_diagram_change_request_use_case(...) -> DiagramChangeRequest
get_diagram_change_request_use_case(...) -> DiagramChangeRequest
```

Do not include these in final assembly if the package is deferred.

---

# 14. PostgreSQL infrastructure contracts

## `database`

```python
create_engine_from_settings(settings: DatabaseSettings) -> Engine
create_session_factory(engine: Engine) -> sessionmaker[Session]
```

## `persistence_serializers`

```python
serialize_diagram_revision(revision: DiagramRevision) -> dict[str, object]
deserialize_diagram_revision(payload: dict[str, object]) -> DiagramRevision

serialize_element_definition(definition: ElementDefinition) -> dict[str, object]
deserialize_element_definition(payload: dict[str, object]) -> ElementDefinition

serialize_connection_definition(definition: ConnectionTypeDefinition) -> dict[str, object]
deserialize_connection_definition(payload: dict[str, object]) -> ConnectionTypeDefinition
```

These functions must use Pydantic validation and canonical serialization. They must not accept `Any`.

## SQLAlchemy repositories

```python
class SqlAlchemyDiagramRepository:
    def __init__(self, session: Session) -> None: ...
    def get(self, diagram_id: str) -> Diagram | None: ...
    def save(self, diagram: Diagram) -> None: ...
    def list_by_object_id(...) -> DiagramSummaryPage: ...

class SqlAlchemyRevisionRepository:
    def __init__(self, session: Session) -> None: ...
    def get(...) -> DiagramRevision | None: ...
    def get_current(...) -> DiagramRevision | None: ...
    def list(...) -> DiagramRevisionSummaryPage: ...
    def append(self, revision: DiagramRevision) -> None: ...

class SqlAlchemyCatalogRepository:
    def __init__(self, session: Session) -> None: ...
    def get_element_definition(...) -> ElementDefinition | None: ...
    def get_connection_definition(...) -> ConnectionTypeDefinition | None: ...
    def list_visible_definitions(...) -> CatalogSnapshot: ...
    def save_element_definition(...) -> None: ...
    def save_connection_definition(...) -> None: ...

class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None: ...
    def __enter__(self) -> SqlAlchemyUnitOfWork: ...
    def __exit__(...) -> bool | None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

No repository function may run `VACUUM`, `VACUUM FULL`, or schema migrations.

---

# 15. HTTP and MCP boundary policy

Exact route and tool signatures will be designed after application contracts stabilize.

Boundary rule:

```text
request Pydantic DTO
→ application use case
→ response Pydantic DTO
```

HTTP and MCP handlers must not:

- call repositories directly;
- build estimation items;
- validate port compatibility;
- assign revision numbers;
- write JSONB directly;
- convert generic dictionaries into domain state without Pydantic validation.

---

# 16. Candidate `module_functions`

```text
model_enums:
  enum classes

model_common:
  ClosedModel
  FrozenModel
  ActorRef
  DefinitionRef
  PortRef
  EstimationRef
  ObjectRef

model_values:
  StringValue
  IntegerValue
  DecimalValue
  BooleanValue
  PropertyValue

model_layout:
  Point
  Viewport
  ElementLayout
  ConnectionLayout
  DiagramLayout

model_catalog:
  PortVisualAnchor
  ElementVisualDefinition
  ConnectionVisualDefinition
  PropertyDefinition
  PortDefinition
  ElementDefinition
  ConnectionTypeDefinition
  CatalogSnapshot
  CreateElementDefinitionDraft
  CreateConnectionDefinitionDraft

model_diagram:
  Diagram
  DiagramElement
  DiagramConnection
  DiagramRevision

model_application:
  ValidationIssue
  ValidationReport
  DiagramSummary
  DiagramWorkspace
  WorkingDiagramResult
  CommitRevisionResult
  DiagramRevisionSummary
  DiagramSummaryPage
  DiagramRevisionSummaryPage

model_commands:
  command model classes

model_estimation:
  estimation model classes
  RequirementAnalysis

catalog_lookup:
  resolve_catalog_snapshot
  list_available_definitions
  private lookup helpers

catalog_drafts:
  create_element_definition_draft
  create_connection_definition_draft
  private validation helpers

catalog_lifecycle:
  transition_definition_status
  private lifecycle helpers

policy_properties:
  validate_property_values
  validate_property_value
  private property helpers

policy_connections:
  validate_connection
  validate_connection_compatibility
  private compatibility helpers

policy_scope:
  validate_definition_use

policy_report:
  validate_working_diagram
  private report helpers

layout:
  validate_layout
  normalize_layout
  optional create_default_layout

diagram_creation:
  create_diagram
  change_diagram_status

diagram_commands:
  apply_authoring_command
  apply_authoring_commands

diagram_elements:
  element command helpers

diagram_connections:
  connection command helpers

diagram_working_state:
  working-state helpers

revision_commit:
  commit_revision
  private revision helpers

estimation_element_items:
  collect_element_items
  build_element_group_key
  private helpers

estimation_connection_items:
  collect_connection_items
  build_connection_group_key
  private helpers

estimation_measurements:
  collect_measurements
  build_count_measurements
  build_property_sum_measurements
  build_explicit_property_measurements

estimation_requirements:
  analyze_estimation_requirements
  find_missing_element_requirements
  find_missing_connection_requirements
  private helpers

estimation_assembly:
  assemble_estimation_package
  private sorting helpers

estimation_collector:
  build_estimation_data
  private status helper

repository_ports:
  repository Protocol classes

external_ports:
  ObjectGateway
  CapabilityAuthorizer

application_diagrams:
  diagram read/lifecycle use cases

application_authoring:
  authoring and commit use cases

application_catalog:
  catalog use cases

application_estimation:
  estimation use cases

persistence_database:
  engine/session factory functions

persistence_serializers:
  Pydantic JSONB serializers

persistence_orm_models:
  SQLAlchemy mapped classes

persistence_diagram_repository:
  SqlAlchemyDiagramRepository

persistence_revision_repository:
  SqlAlchemyRevisionRepository

persistence_catalog_repository:
  SqlAlchemyCatalogRepository

persistence_unit_of_work:
  SqlAlchemyUnitOfWork
```

---

# 17. Candidate module order

```text
model_enums
model_common
model_values
model_layout
model_catalog
model_diagram
model_application
model_commands
model_estimation
models
errors
catalog_lookup
catalog_drafts
catalog_lifecycle
catalog
policy_properties
policy_connections
policy_scope
policy_report
diagram_policy
layout
diagram_creation
diagram_elements
diagram_connections
diagram_working_state
diagram_commands
diagram
repository_ports
external_ports
revision_commit
revision
estimation_element_items
estimation_connection_items
estimation_measurements
estimation_requirements
estimation_assembly
estimation_collector
estimation_data
application_diagrams
application_authoring
application_catalog
application_estimation
application
persistence_orm_models
persistence_serializers
persistence_database
persistence_diagram_repository
persistence_revision_repository
persistence_catalog_repository
persistence_unit_of_work
http_api
mcp_api
```

This order remains provisional until `imports.internal` is assembled.

---

# 18. Contract placeholder review

Rejected:

```python
process(data: dict) -> dict
save_snapshot(payload: Any) -> None
apply_patch(operation: str, payload: dict) -> DiagramRevision
build_estimation_data(data: dict) -> list[dict]
validate(value: object) -> bool
```

Accepted explicit uncertainty:

- change requests may be deferred from v1;
- default layout may be deferred;
- exact HTTP/MCP contracts follow after application contracts;
- exact ORM column definitions belong to persistence assembly.

## Readiness assessment

State 6 is ready for classified notes and final global-spec assembly because:

- public and internal functions have exact typed signatures;
- deep modules are split into bounded generation units;
- Pydantic models are used consistently;
- PostgreSQL persistence is isolated behind protocols and adapters;
- estimation-data generation has one public facade and several narrow internal units;
- batch authoring semantics are explicit;
- transaction and concurrency ownership are explicit;
- remaining unknowns are localized and visible.
