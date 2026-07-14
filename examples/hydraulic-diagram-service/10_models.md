# State 1 — Domain models

## Modeling goal

This state defines the durable domain language of Hydraulic Diagram Service before contracts, modules, storage tables, HTTP routes, or MCP tools are designed.

The model must support:

- persistent diagrams linked to an external `object_id`;
- immutable diagram revisions;
- catalog-backed element and connection instances;
- controlled agent-created definitions;
- editor layout that is separate from engineering structure;
- deterministic estimation-data collection;
- provenance for user, agent, service, and import changes;
- explicit missing requirements instead of invented values.

## Modeling principles

1. React Flow `Node` and `Edge` are frontend representations, not durable domain models.
2. An element definition is not the same thing as an element instance.
3. A connection type definition is not the same thing as a connection instance.
4. Saved revisions identify the exact definition versions they use.
5. Layout may describe presentation but cannot create engineering entities.
6. Agent-created catalog entries are controlled, versioned, scoped records.
7. Estimation output is a projection of a concrete revision, not a second diagram model.
8. Unknown integration details remain outside the domain model behind explicit references and gateways.
9. Generic `dict`, `Any`, and untyped metadata fields are rejected unless the openness is itself part of a defined contract.

---

# 1. Shared value models

## `ActorRef`

### Purpose

Identifies who or what caused a durable change without embedding authentication-provider details into the domain.

### Kind

Value object.

### Created by

Application boundary after authentication or trusted service identification.

### Consumed by

Revision history, catalog governance, audit, estimation provenance.

### Fields

```text
actor_type: ActorType
actor_id: str
label: str | None
```

Candidate `ActorType` values:

```text
user
agent
service
import
system
```

### Invariants

- `actor_id` is required.
- `actor_type` determines the identity namespace.
- `label` is display-only and is not authoritative identity.

### Placeholder resistance

Do not use `created_by: str` everywhere because it loses the difference between user, agent, and service provenance.

---

## `DefinitionRef`

### Purpose

Pins a diagram instance to an exact catalog definition version.

### Kind

Value object.

### Fields

```text
definition_id: str
version: int
```

### Invariants

- `version >= 1`.
- The referenced version is immutable once active or used by a committed revision.

### Placeholder resistance

Do not store only a mutable `definition_id`; historical diagrams must not silently change when the catalog changes.

---

## `PortRef`

### Purpose

Identifies a logical port on an element instance.

### Kind

Value object.

### Fields

```text
element_id: str
port_code: str
```

### Invariants

- `element_id` references an element in the same diagram revision.
- `port_code` exists in the exact `ElementDefinition` version referenced by that element.

---

## `TypedValue`

### Purpose

Represents a property value without allowing arbitrary nested JSON.

### Kind

Tagged scalar value.

### Fields

```text
value_type: PropertyValueType
string_value: str | None
integer_value: int | None
decimal_value: Decimal | None
boolean_value: bool | None
```

Candidate `PropertyValueType` values:

```text
string
integer
decimal
boolean
```

### Invariants

- Exactly one value field is populated.
- The populated field matches `value_type`.
- Unit is not stored here; unit belongs to `PropertyDefinition` or a measured-value model.

### Placeholder resistance

This deliberately avoids `value: Any` and generic JSON blobs.

### Deferred extension

Date, enum, range, and structured measurement types may be added later only when a real domain need appears.

---

## `PropertyValue`

### Purpose

Stores one validated property value on an element or connection instance.

### Kind

Value object.

### Fields

```text
property_code: str
value: TypedValue
source: ValueSource
source_ref: str | None
```

Candidate `ValueSource` values:

```text
user
agent
catalog_default
import
calculated
object_card
```

### Invariants

- `property_code` exists in the corresponding definition version.
- `value` matches the declared property type and allowed values.
- `source_ref` is required when the source is external or calculated and a traceable reference exists.

---

## `EstimationRef`

### Purpose

Provides stable classification hints for Estimator Service without storing prices or final estimate logic.

### Kind

Value object.

### Fields

```text
namespace: str
code: str
role: EstimationRole
```

Candidate `EstimationRole` values:

```text
material
work
equipment
accessory
measurement
classification
```

### Invariants

- `namespace + code + role` is meaningful to an external estimator contract.
- No price, retailer product ID, or Holded document data is stored here.

---

# 2. Diagram aggregate models

## `Diagram`

### Purpose

Represents the persistent identity and lifecycle of one hydraulic diagram linked to a platform object.

### Kind

Aggregate root identity record.

### Created by

Diagram application service through editor, agent, or service API.

### Modified by

Only lifecycle operations. Engineering content changes create a new `DiagramRevision` rather than mutating old revisions.

### Consumed by

Editor, diagram agent, Estimator Service, estimator agent, revision service.

### Fields

```text
id: str
object_id: str
name: str
system_kind: DiagramSystemKind
status: DiagramStatus
current_revision: int
created_at: datetime
updated_at: datetime
created_by: ActorRef
```

Candidate `DiagramStatus` values:

```text
draft
active
archived
```

`DiagramSystemKind` remains an intentionally open design decision for State 2. It must become a controlled catalog or enum before final specification assembly.

### Lifecycle

```text
draft → active → archived
```

Reactivation policy is unresolved.

### Invariants

- `object_id` is required and externally owned.
- `current_revision >= 0`.
- `current_revision == 0` means the diagram exists but has no committed engineering revision yet.
- A diagram does not contain customer or object master data.
- A diagram may not point to a current revision belonging to another diagram.

### Placeholder resistance

Do not add `metadata: dict`, `settings: dict`, or copied object-card fields for future convenience.

---

## `DiagramRevision`

### Purpose

Represents an immutable committed snapshot of engineering structure and associated editor layout.

### Kind

Immutable aggregate snapshot.

### Created by

Revision commit operation after domain validation.

### Modified by

Never.

### Consumed by

Editor restoration, comparison, estimation-data collector, audit, agents.

### Fields

```text
diagram_id: str
revision: int
schema_version: int
elements: list[DiagramElement]
connections: list[DiagramConnection]
layout: DiagramLayout
created_at: datetime
created_by: ActorRef
change_source: ChangeSource
change_summary: str | None
```

Candidate `ChangeSource` values:

```text
editor
agent
service
import
migration
```

### Invariants

- `revision >= 1`.
- Revision numbers increase monotonically per diagram.
- The snapshot is immutable after commit.
- Element IDs are unique within the revision.
- Connection IDs are unique within the revision.
- Every connection references elements in the same revision.
- Every used catalog definition is pinned by exact version.
- Layout references only entities present in the revision.
- `schema_version` is required.

### Storage decision deferred

The domain model is a full snapshot. Physical persistence may use normalized rows, JSON snapshots, command logs, or a hybrid, but loading a revision must reconstruct this exact model.

### Placeholder resistance

Do not replace `elements`, `connections`, and `layout` with one arbitrary `document: dict`.

---

## `DiagramElement`

### Purpose

Represents one instance of a catalog-defined hydraulic component in a diagram revision.

### Kind

Entity inside `DiagramRevision`.

### Created by

Diagram authoring command using an active or permitted draft `ElementDefinition`.

### Modified by

A working draft may change before commit; committed revision instances are immutable.

### Fields

```text
id: str
definition: DefinitionRef
label: str | None
quantity: Decimal
properties: list[PropertyValue]
```

### Invariants

- `quantity > 0`.
- `definition` resolves to an allowed element definition version.
- Property codes are unique within the instance.
- Required properties defined by the catalog must be present before the relevant validation or estimation stage.
- Extra properties not declared by the definition are rejected.
- Instance data does not duplicate definition ports, names, category, or estimation references.

### Quantity decision

`quantity` is retained because a logical diagram instance may represent multiple identical units in some workflows. Whether the editor permits values other than `1` remains a product decision.

### Placeholder resistance

Do not use `properties: dict[str, Any]`. Values are validated through `PropertyDefinition` and represented as `PropertyValue`.

---

## `DiagramConnection`

### Purpose

Represents one logical connection between two ports on element instances.

### Kind

Entity inside `DiagramRevision`.

### Fields

```text
id: str
source: PortRef
target: PortRef
connection_type: DefinitionRef
properties: list[PropertyValue]
```

### Invariants

- Source and target elements exist in the same revision.
- Source and target ports exist in the corresponding element definition versions.
- Source and target must not be the same logical port.
- Connection type compatibility must be validated against both ports.
- Property codes are unique and declared by the connection type definition.
- Engineering connectivity is independent of rendered edge geometry.

### Direction decision

The domain does not assume that every hydraulic connection has a fixed source-to-target flow direction. `source` and `target` may be stable endpoint labels for identity and serialization only. Flow semantics, where required, belong to port or system policy.

### Placeholder resistance

Do not store raw React Flow handle IDs or edge objects as the authoritative connection.

---

# 3. Catalog models

## `ElementDefinition`

### Purpose

Defines a reusable hydraulic component type that may be instantiated in diagrams.

### Kind

Versioned catalog aggregate.

### Created by

Catalog administration, migration, or an authorized agent-created draft workflow.

### Modified by

New versions are created; used versions remain immutable.

### Consumed by

Editor palette, diagram validation, agent authoring, layout rendering metadata, estimation-data collector.

### Fields

```text
id: str
version: int
code: str
name: str
category_code: str
status: DefinitionStatus
scope: DefinitionScope
scope_ref: str | None
ports: list[PortDefinition]
properties: list[PropertyDefinition]
estimation_refs: list[EstimationRef]
visual: ElementVisualDefinition
created_at: datetime
created_by: ActorRef
```

Candidate `DefinitionStatus` values:

```text
draft
active
deprecated
rejected
```

Candidate `DefinitionScope` values:

```text
diagram
object
tenant
global
```

`tenant` remains provisional until the platform tenancy model is known.

### Invariants

- `version >= 1`.
- `code` is stable across versions of the same definition identity.
- Port codes are unique within the definition version.
- Property codes are unique within the definition version.
- Active versions are immutable.
- `scope_ref` is required for diagram, object, or tenant scopes.
- A diagram may use a definition only when scope policy permits it.
- Deprecated versions remain readable for historical revisions.

### Agent-created definitions

An agent may create a draft definition but cannot bypass validation or silently overwrite an active definition version.

Approval and activation policy is deferred to State 2.

### Placeholder resistance

Do not represent an agent-created element as a free-form SVG plus arbitrary properties. Ports, properties, scope, estimation refs, and provenance are explicit.

---

## `PortDefinition`

### Purpose

Defines one logical connection point on an element definition.

### Kind

Value object inside `ElementDefinition`.

### Fields

```text
code: str
label: str
kind: PortKind
medium: MediumKind
flow_semantics: FlowSemantics
allowed_connection_type_codes: list[str]
visual_anchor: PortVisualAnchor
```

Candidate `FlowSemantics` values:

```text
bidirectional
inlet
outlet
supply
return
unspecified
```

### Invariants

- `code` is stable within the definition identity where compatibility is intended.
- Medium and connection compatibility are domain data, not UI conditionals.
- Visual anchor does not define engineering compatibility.

### Open decisions

`PortKind`, `MediumKind`, and connection compatibility policy must be defined in State 2.

---

## `PortVisualAnchor`

### Purpose

Defines the default symbol-local anchor used by the editor to render a port.

### Kind

Value object.

### Fields

```text
x: Decimal
y: Decimal
side: VisualSide
direction: VisualDirection
```

### Invariants

- Coordinates are symbol-local.
- This model affects rendering and route endpoints but not logical connectivity.
- Rotation transforms the anchor in the frontend or layout adapter; rotated coordinates are not persisted as a new port definition.

---

## `PropertyDefinition`

### Purpose

Defines one allowed property on an element or connection type.

### Kind

Value object inside a catalog definition.

### Fields

```text
code: str
label: str
value_type: PropertyValueType
unit_code: str | None
required_for_authoring: bool
required_for_estimation: bool
default_value: TypedValue | None
allowed_values: list[TypedValue]
minimum: Decimal | None
maximum: Decimal | None
```

### Invariants

- Default and allowed values match `value_type`.
- Numeric bounds apply only to numeric types.
- `minimum <= maximum` when both exist.
- A default does not replace required user or agent knowledge unless policy explicitly permits it.

### Placeholder resistance

This model prevents undocumented arbitrary properties and makes missing estimator data detectable.

---

## `ElementVisualDefinition`

### Purpose

Stores catalog-level rendering metadata needed by the editor without embedding React components in the domain.

### Kind

Value object inside `ElementDefinition`.

### Fields

```text
icon_key: str
default_width: Decimal
default_height: Decimal
```

### Deferred decisions

Whether raw SVG assets are stored by this service, referenced by key, or managed in a frontend asset registry is unresolved. The initial model uses `icon_key` as a stable reference.

### Placeholder resistance

Do not use `visual: dict`; only known cross-client rendering metadata belongs here.

---

## `ConnectionTypeDefinition`

### Purpose

Defines a reusable pipe, line, or cable connection type.

### Kind

Versioned catalog aggregate.

### Fields

```text
id: str
version: int
code: str
name: str
category_code: str
medium: MediumKind
status: DefinitionStatus
scope: DefinitionScope
scope_ref: str | None
properties: list[PropertyDefinition]
estimation_refs: list[EstimationRef]
visual: ConnectionVisualDefinition
created_at: datetime
created_by: ActorRef
```

### Invariants

- Active versions are immutable.
- Property codes are unique.
- Scope rules match `ElementDefinition` scope rules.
- Historical revisions remain resolvable after deprecation.

---

## `ConnectionVisualDefinition`

### Purpose

Stores transport-neutral visual style metadata for an editor.

### Kind

Value object.

### Fields

```text
visual_style: ConnectionVisualStyle
color: str
stroke_width: Decimal
```

Candidate `ConnectionVisualStyle` values:

```text
solid
dashed
dotted
```

### Invariants

- Visual style does not determine engineering compatibility.
- Color is presentation metadata, not material identity.

---

# 4. Layout models

## `DiagramLayout`

### Purpose

Stores editor presentation for one exact diagram revision.

### Kind

Value object inside `DiagramRevision` or separately persisted record keyed by revision.

### Created by

Visual editor or controlled import.

### Consumed by

Visual editor restoration and image export clients.

### Fields

```text
elements: list[ElementLayout]
connections: list[ConnectionLayout]
viewport: Viewport
```

### Invariants

- Every `ElementLayout.element_id` references a revision element.
- Every `ConnectionLayout.connection_id` references a revision connection.
- Duplicate layout entries are rejected.
- Missing layout may be tolerated for agent-created engineering data if deterministic default placement exists; that policy is deferred.
- Selection, hover, open panels, and other transient UI chrome are not persisted.

### Placeholder resistance

Layout is not stored as raw React Flow state.

---

## `ElementLayout`

### Purpose

Stores position and orientation of one element instance.

### Fields

```text
element_id: str
x: Decimal
y: Decimal
rotation_degrees: int
width: Decimal | None
height: Decimal | None
```

### Invariants

- `rotation_degrees` is normalized to supported increments.
- Width and height overrides, when present, are positive.
- Layout does not duplicate label, properties, ports, or definition identity.

---

## `ConnectionLayout`

### Purpose

Stores optional presentation route points for one connection.

### Fields

```text
connection_id: str
route_points: list[Point]
```

### Invariants

- Route points are presentation geometry unless a later rule explicitly promotes them to authoritative measurement geometry.
- Estimation length must not be calculated from route points until that authority decision is made.

---

## `Point`

```text
x: Decimal
y: Decimal
```

---

## `Viewport`

```text
x: Decimal
y: Decimal
zoom: Decimal
```

### Invariants

- `zoom > 0`.

---

# 5. Estimation-data models

## `EstimationDataPackage`

### Purpose

Provides a deterministic, version-pinned package of diagram-derived data to Estimator Service and estimator agents.

### Kind

Derived output DTO with reproducibility metadata.

### Created by

Deterministic estimation-data collector.

### Modified by

Never. A new package is built for another diagram or catalog revision.

### Consumed by

Estimator Service backend and estimator agent.

### Fields

```text
package_id: str
object_id: str
diagram_id: str
diagram_revision: int
schema_version: int
status: EstimationPackageStatus
element_items: list[ElementEstimationItem]
connection_items: list[ConnectionEstimationItem]
measurements: list[DiagramMeasurement]
missing_requirements: list[MissingEstimationRequirement]
warnings: list[EstimationWarning]
generated_at: datetime
```

Candidate `EstimationPackageStatus` values:

```text
complete
incomplete
invalid
```

### Invariants

- Same diagram revision, same referenced definition versions, and same collector rules produce semantically identical content.
- `complete` requires no blocking missing requirements.
- `invalid` means diagram integrity prevents safe collection.
- Package items preserve references to source entities.
- Package contains no prices, retailer products, final estimate positions, or Holded data.

### Persistence decision

Whether the package is persisted or generated on demand is deferred. Reproducibility metadata is required in either case.

---

## `ElementEstimationItem`

### Purpose

Groups estimate-relevant element instances that are equivalent under collector rules.

### Fields

```text
definition: DefinitionRef
estimation_refs: list[EstimationRef]
quantity: Decimal
properties: list[PropertyValue]
source_element_ids: list[str]
```

### Invariants

- `quantity` equals the deterministic aggregation of source instances and instance quantities.
- Source IDs are unique.
- Grouped instances share the same estimator-relevant property values.
- Definition version is pinned.

---

## `ConnectionEstimationItem`

### Purpose

Groups estimate-relevant connection instances.

### Fields

```text
connection_type: DefinitionRef
estimation_refs: list[EstimationRef]
quantity: Decimal
unit_code: str
properties: list[PropertyValue]
source_connection_ids: list[str]
```

### Invariants

- Quantity and unit are derived through explicit collector rules.
- No length is fabricated when authoritative geometry is unavailable.
- Definition version is pinned.

---

## `DiagramMeasurement`

### Purpose

Represents a deterministic measured or counted value derived from the diagram.

### Fields

```text
code: str
value: Decimal
unit_code: str
source_entity_type: SourceEntityType
source_entity_ids: list[str]
method: MeasurementMethod
```

Candidate `MeasurementMethod` values:

```text
count
property_sum
layout_route_length
explicit_property
```

`layout_route_length` must remain disabled until route geometry authority is accepted in State 2.

### Invariants

- Method is explicit.
- Sources are traceable.
- Unsupported measurements are reported as missing requirements, not guessed.

---

## `MissingEstimationRequirement`

### Purpose

Describes one blocking piece of information required to produce a complete estimation package.

### Fields

```text
code: str
entity_type: SourceEntityType
entity_id: str | None
property_code: str | None
reason: str
required_by: str
can_agent_resolve: bool
```

### Invariants

- Requirement is specific enough for a client or agent to locate the source problem.
- `reason` is human-readable but `code` drives automation.
- Missing requirements do not carry invented suggested values.

---

## `EstimationWarning`

### Purpose

Reports non-blocking uncertainty or degraded output.

### Fields

```text
code: str
message: str
entity_type: SourceEntityType | None
entity_id: str | None
```

### Invariants

- Warnings never substitute for blocking requirements.

---

# 6. Agent and correction boundary models

## `DiagramChangeRequest`

### Purpose

Allows an estimator agent or another read-oriented consumer to request a diagram correction without silently mutating the diagram through estimation APIs.

### Kind

Integration command DTO, not part of a committed diagram revision.

### Fields

```text
id: str
diagram_id: str
base_revision: int
requested_by: ActorRef
reason_code: str
reason: str
changes: list[RequestedDiagramChange]
status: ChangeRequestStatus
created_at: datetime
```

Candidate `ChangeRequestStatus` values:

```text
open
accepted
rejected
applied
```

### Invariants

- `base_revision` is explicit.
- Applying the request uses normal authoring commands and creates a new revision.
- Estimator-facing read operations do not apply it automatically.

---

## `RequestedDiagramChange`

### Purpose

Describes a proposed correction in a structured but non-authoritative form.

### Fields

```text
entity_type: SourceEntityType
entity_id: str | None
operation: RequestedChangeOperation
property_code: str | None
suggested_value: TypedValue | None
notes: str | None
```

Candidate `RequestedChangeOperation` values:

```text
set_property
add_element
replace_definition
add_connection
remove_entity
review_required
```

### Constraint

Complex authoring payloads for add/replace operations remain unresolved. Do not finalize this model into `global_spec.json` until real authoring commands are designed.

This model is included to preserve the read/write capability boundary, not to define all mutation contracts prematurely.

---

# 7. External integration boundary model

## `ObjectRef`

### Purpose

Represents the only currently stable dependency on Object Card Service.

### Fields

```text
object_id: str
```

### Constraint

No `ObjectSnapshot` is included yet because its real fields and entry point are unavailable.

Future object data must arrive through a gateway DTO designed from actual integration evidence.

### Placeholder boundary

Acceptable unresolved interface:

```text
ObjectGateway.get_object_snapshot(object_id)
```

Unacceptable domain leakage:

```text
object_data: dict
customer_data: dict
```

---

# 8. Model ownership summary

The following ownership is provisional and will be finalized in State 3:

```text
Diagram, DiagramRevision, DiagramElement, DiagramConnection
→ diagram responsibility

ElementDefinition, ConnectionTypeDefinition, property and port definitions
→ catalog responsibility

DiagramLayout and layout value objects
→ layout responsibility

EstimationDataPackage and estimation items
→ estimation_data responsibility

DiagramChangeRequest
→ change_request or authoring coordination responsibility

ActorRef and DefinitionRef
→ shared domain value models
```

---

# 9. Placeholder resistance review

## Rejected placeholders

- React Flow `Node[]` and `Edge[]` as durable schema.
- `Diagram.document: dict`.
- `DiagramElement.properties: dict[str, Any]`.
- `ElementDefinition.metadata: dict`.
- mutable catalog definitions without version pinning.
- `created_by: str` without actor type.
- estimator output containing arbitrary `items: list[dict]`.
- missing data represented only as a warning string.
- agent access represented as direct database writes.
- copied Object Card data without a real contract.

## Deliberately unresolved decisions

- exact `DiagramSystemKind` values;
- exact `PortKind`, `MediumKind`, units, and categories;
- definition activation and approval policy;
- tenant model;
- revision persistence strategy;
- whether route geometry is authoritative for length;
- estimator-required properties;
- whether `quantity != 1` is allowed for diagram elements;
- whether estimation packages are stored;
- exact mutation payloads for `DiagramChangeRequest`.

These remain visible design questions and are not hidden behind generic data structures.

---

# 10. Draft `models` projection for the future global specification

This is a preview of the eventual `models` section, not yet the final JSON.

```text
ActorRef
DefinitionRef
PortRef
TypedValue
PropertyValue
EstimationRef
Diagram
DiagramRevision
DiagramElement
DiagramConnection
ElementDefinition
PortDefinition
PortVisualAnchor
PropertyDefinition
ElementVisualDefinition
ConnectionTypeDefinition
ConnectionVisualDefinition
DiagramLayout
ElementLayout
ConnectionLayout
Point
Viewport
EstimationDataPackage
ElementEstimationItem
ConnectionEstimationItem
DiagramMeasurement
MissingEstimationRequirement
EstimationWarning
DiagramChangeRequest
RequestedDiagramChange
ObjectRef
```

## State 1 readiness assessment

The core model layer is sufficiently developed to begin State 2 because:

- durable engineering structure is independent of frontend implementation;
- instances and versioned definitions are separated;
- required values have explicit typed representations;
- revisions and provenance are explicit;
- layout authority is constrained;
- estimation output and missing requirements are concrete;
- the Object Card uncertainty is localized;
- remaining unknowns are policy and taxonomy decisions appropriate for the next state.
