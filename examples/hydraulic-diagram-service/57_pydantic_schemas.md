# Concrete Pydantic schemas

## Goal

This document converts the conceptual models from State 1 into concrete Pydantic-oriented schemas before exact function contracts are written.

The schemas are still specification artifacts, not implementation code. They define:

- model names;
- field types;
- discriminators;
- enum values;
- frozen versus mutable behavior;
- local validators;
- cross-field constraints;
- package/generation-unit placement.

All models default to:

```python
ConfigDict(
    extra="forbid",
    validate_assignment=True,
    str_strip_whitespace=True,
)
```

Frozen models add:

```python
frozen=True
```

---

# 1. Enums

Generation unit:

```text
model_enums
→ hydraulic_diagram/domain/models/enums.py
```

All enums inherit from `str, Enum`.

## `ActorType`

```text
user
agent
service
import
system
```

## `DiagramStatus`

```text
draft
active
archived
```

## `DefinitionStatus`

```text
draft
active
deprecated
rejected
```

## `DefinitionScope`

```text
diagram
object
tenant
global
```

## `DiagramSystemKind`

```text
heating
cold_water
hot_water
solar_thermal
```

## `MediumKind`

```text
water
hot_water
cold_water
heating_water
antifreeze_mix
unspecified
```

## `PortKind`

```text
hydraulic
control
sensor
drain
fill
unspecified
```

## `FlowSemantics`

```text
bidirectional
inlet
outlet
supply
return
unspecified
```

## `VisualSide`

```text
top
right
bottom
left
center
```

## `VisualDirection`

```text
up
right
down
left
none
```

## `ConnectionVisualStyle`

```text
solid
dashed
dotted
```

## `ValueSource`

```text
user
agent
catalog_default
import
calculated
object_card
```

## `EstimationRole`

```text
material
work
equipment
accessory
measurement
classification
```

## `ChangeSource`

```text
editor
agent
service
import
migration
```

## `EstimationPackageStatus`

```text
complete
incomplete
invalid
```

## `MeasurementMethod`

```text
count
property_sum
explicit_property
layout_route_length
```

`layout_route_length` exists in the enum but remains forbidden by current rules.

## `ValidationSeverity`

```text
warning
blocking
```

## `ValidationStage`

```text
draft
commit
activation
estimation
```

## `SourceEntityType`

```text
diagram
element
connection
element_definition
connection_definition
property
layout
revision
```

## `ChangeRequestStatus`

```text
open
accepted
rejected
applied
```

---

# 2. Shared model base classes

Generation unit:

```text
model_common
→ hydraulic_diagram/domain/models/common.py
```

## `ClosedModel`

Conceptual shared base:

```text
extra = forbid
validate_assignment = true
str_strip_whitespace = true
```

## `FrozenModel`

Extends `ClosedModel` with:

```text
frozen = true
```

These base classes are implementation conveniences. They do not appear as business models in `global_spec.models` unless the factory requires explicit base-class generation.

---

# 3. Shared value models

Generation unit:

```text
model_common
```

## `ActorRef` — frozen

```text
actor_type: ActorType
actor_id: str = Field(min_length=1, max_length=200)
label: str | None = Field(default=None, max_length=300)
```

Local validation:

- blank `actor_id` rejected after trimming.

## `DefinitionRef` — frozen

```text
definition_id: str = Field(min_length=1, max_length=200)
version: int = Field(ge=1)
```

## `PortRef` — frozen

```text
element_id: str = Field(min_length=1, max_length=200)
port_code: str = Field(min_length=1, max_length=120)
```

## `EstimationRef` — frozen

```text
namespace: str = Field(min_length=1, max_length=120)
code: str = Field(min_length=1, max_length=200)
role: EstimationRole
```

Cross-field validator:

- normalized semantic identity is `(namespace, code, role)`.

## `ObjectRef` — frozen

```text
object_id: str = Field(min_length=1, max_length=200)
```

## `ObjectSnapshot` — frozen

```text
object_id: str = Field(min_length=1, max_length=200)
status: Literal["active", "archived"]
```

Projection of the Registry `ProjectRecord`; deliberately excludes name,
address, customer and room data (resolved 2026-07-15).

---

# 4. Typed property values

Generation unit:

```text
model_values
→ hydraulic_diagram/domain/models/values.py
```

All value variants are frozen.

## `StringValue`

```text
value_type: Literal["string"] = "string"
value: str
```

## `IntegerValue`

```text
value_type: Literal["integer"] = "integer"
value: int
```

Strict integer validation must reject booleans.

## `DecimalValue`

```text
value_type: Literal["decimal"] = "decimal"
value: Decimal
```

Serialization rule:

- JSON uses a stable string or canonical numeric representation selected once for the project;
- the same policy is used by HTTP, MCP, and persisted snapshots.

## `BooleanValue`

```text
value_type: Literal["boolean"] = "boolean"
value: bool
```

## `TypedValue`

```text
Annotated[
    StringValue | IntegerValue | DecimalValue | BooleanValue,
    Field(discriminator="value_type"),
]
```

## `PropertyValue` — frozen

```text
property_code: str = Field(min_length=1, max_length=120)
value: TypedValue
source: ValueSource
source_ref: str | None = Field(default=None, max_length=300)
```

Model validator:

- `source_ref` is required for `object_card`;
- `source_ref` should be present for `calculated` when a calculation reference exists;
- local validation does not check whether `property_code` exists in a catalog definition.

---

# 5. Layout models

Generation unit:

```text
model_layout
→ hydraulic_diagram/domain/models/layout.py
```

All committed layout models are frozen.

## `Point`

```text
x: Decimal
y: Decimal
```

## `Viewport`

```text
x: Decimal
y: Decimal
zoom: Decimal = Field(gt=0)
```

## `ElementLayout`

```text
element_id: str = Field(min_length=1, max_length=200)
x: Decimal
y: Decimal
rotation_degrees: int
width: Decimal | None = Field(default=None, gt=0)
height: Decimal | None = Field(default=None, gt=0)
```

Field validator:

- normalize rotation to one of `0`, `90`, `180`, `270`.

## `ConnectionLayout`

```text
connection_id: str = Field(min_length=1, max_length=200)
route_points: list[Point] = Field(default_factory=list)
```

List length is checked against config in `layout`, not hardcoded into the model.

## `DiagramLayout`

```text
elements: list[ElementLayout] = Field(default_factory=list)
connections: list[ConnectionLayout] = Field(default_factory=list)
viewport: Viewport
```

Model validator:

- duplicate `element_id` values rejected;
- duplicate `connection_id` values rejected;
- existence of referenced engineering entities remains in `layout.validate_layout`.

---

# 6. Catalog models

Generation unit:

```text
model_catalog
→ hydraulic_diagram/domain/models/catalog.py
```

## `PortVisualAnchor` — frozen

```text
x: Decimal
y: Decimal
side: VisualSide
direction: VisualDirection
```

## `ElementVisualDefinition` — frozen

```text
icon_key: str = Field(min_length=1, max_length=200)
svg_markup: str = Field(min_length=1)
default_width: Decimal = Field(gt=0)
default_height: Decimal = Field(gt=0)
```

Validators:

- `svg_markup` length bounded by `config.catalog.max_svg_markup_bytes`;
- markup must be self-contained and inert: no scripts, event handlers,
  external references, or `foreignObject` (sanitization per State 2 visual
  asset policy).

## `ConnectionVisualDefinition` — frozen

```text
visual_style: ConnectionVisualStyle
color: str = Field(min_length=4, max_length=20)
stroke_width: Decimal = Field(gt=0)
```

Field validator:

- validate supported CSS hex color format in v1.

## `PropertyDefinition` — frozen

```text
code: str = Field(min_length=1, max_length=120)
label: str = Field(min_length=1, max_length=300)
value_type: Literal["string", "integer", "decimal", "boolean"]
unit_code: str | None = Field(default=None, max_length=40)
required_for_authoring: bool = False
required_for_estimation: bool = False
default_value: TypedValue | None = None
allowed_values: list[TypedValue] = Field(default_factory=list)
minimum: Decimal | None = None
maximum: Decimal | None = None
```

Model validators:

- `default_value.value_type` matches `value_type`;
- every allowed value matches `value_type`;
- `minimum` and `maximum` only allowed for integer/decimal;
- `minimum <= maximum`;
- numeric physical property requires `unit_code` when policy marks it as a measurement;
- duplicate allowed values rejected by canonical value identity.

## `PortDefinition` — frozen

```text
code: str = Field(min_length=1, max_length=120)
label: str = Field(min_length=1, max_length=300)
kind: PortKind
medium: MediumKind
flow_semantics: FlowSemantics
allowed_connection_type_codes: list[str] = Field(default_factory=list)
visual_anchor: PortVisualAnchor
```

Model validator:

- duplicate allowed connection codes rejected.

## `ElementDefinition` — frozen

```text
id: str = Field(min_length=1, max_length=200)
version: int = Field(ge=1)
code: str = Field(min_length=1, max_length=120)
name: str = Field(min_length=1, max_length=300)
category_code: str = Field(min_length=1, max_length=120)
status: DefinitionStatus
scope: DefinitionScope
scope_ref: str | None = Field(default=None, max_length=200)
ports: list[PortDefinition]
properties: list[PropertyDefinition] = Field(default_factory=list)
estimation_refs: list[EstimationRef] = Field(default_factory=list)
visual: ElementVisualDefinition
created_at: datetime
created_by: ActorRef
```

Model validators:

- `scope_ref` required for diagram/object/tenant;
- `scope_ref` forbidden for global;
- unique port codes;
- unique property codes;
- duplicate estimation refs rejected;
- active/deprecated/rejected models remain frozen;
- authorization and lifecycle transitions remain in `catalog`.

## `ConnectionTypeDefinition` — frozen

```text
id: str = Field(min_length=1, max_length=200)
version: int = Field(ge=1)
code: str = Field(min_length=1, max_length=120)
name: str = Field(min_length=1, max_length=300)
category_code: str = Field(min_length=1, max_length=120)
medium: MediumKind
status: DefinitionStatus
scope: DefinitionScope
scope_ref: str | None = Field(default=None, max_length=200)
properties: list[PropertyDefinition] = Field(default_factory=list)
estimation_refs: list[EstimationRef] = Field(default_factory=list)
visual: ConnectionVisualDefinition
created_at: datetime
created_by: ActorRef
```

Validators mirror scope and uniqueness rules from `ElementDefinition`.

## `CatalogSnapshot` — frozen

```text
element_definitions: list[ElementDefinition] = Field(default_factory=list)
connection_definitions: list[ConnectionTypeDefinition] = Field(default_factory=list)
```

Model validator:

- duplicate `(id, version)` pairs rejected independently for each definition kind.

---

# 7. Diagram models

Generation unit:

```text
model_diagram
→ hydraulic_diagram/domain/models/diagram.py
```

## `Diagram` — frozen

```text
id: str = Field(min_length=1, max_length=200)
object_id: str = Field(min_length=1, max_length=200)
name: str = Field(min_length=1, max_length=300)
system_kinds: set[DiagramSystemKind] = Field(min_length=1)
status: DiagramStatus
current_revision: int = Field(ge=0)
created_at: datetime
updated_at: datetime
created_by: ActorRef
```

Model validator:

- `updated_at >= created_at`.

Lifecycle transitions remain in `diagram_policy`.

## `DiagramElement` — frozen

```text
id: str = Field(min_length=1, max_length=200)
definition: DefinitionRef
label: str | None = Field(default=None, max_length=300)
quantity: Decimal = Field(gt=0)
properties: list[PropertyValue] = Field(default_factory=list)
```

Model validator:

- duplicate `property_code` rejected.

Catalog existence and required-property checks remain in policy.

## `DiagramConnection` — frozen

```text
id: str = Field(min_length=1, max_length=200)
source: PortRef
target: PortRef
connection_type: DefinitionRef
properties: list[PropertyValue] = Field(default_factory=list)
```

Model validators:

- source and target cannot be identical;
- duplicate property codes rejected.

Endpoint existence and compatibility remain in policy.

## `DiagramRevision` — frozen

```text
diagram_id: str = Field(min_length=1, max_length=200)
revision: int = Field(ge=1)
schema_version: int = Field(ge=1)
elements: list[DiagramElement] = Field(default_factory=list)
connections: list[DiagramConnection] = Field(default_factory=list)
layout: DiagramLayout
created_at: datetime
created_by: ActorRef
change_source: ChangeSource
change_summary: str | None = Field(default=None, max_length=1000)
```

Model validator:

- duplicate element IDs rejected;
- duplicate connection IDs rejected;
- layout duplicate checks already handled locally;
- graph references and catalog resolution remain in policy.

---

# 8. Validation and application DTOs

Generation unit:

```text
model_application
→ hydraulic_diagram/domain/models/application.py
```

## `ValidationIssue` — frozen

```text
code: str = Field(min_length=1, max_length=160)
severity: ValidationSeverity
message: str = Field(min_length=1, max_length=1000)
entity_type: SourceEntityType | None = None
entity_id: str | None = Field(default=None, max_length=200)
property_code: str | None = Field(default=None, max_length=120)
```

## `ValidationReport` — frozen

```text
issues: list[ValidationIssue] = Field(default_factory=list)
is_valid: bool
```

Model validator:

- `is_valid` must equal absence of blocking issues.

## `DiagramSummary` — frozen

```text
diagram_id: str
object_id: str
name: str
system_kinds: set[DiagramSystemKind]
status: DiagramStatus
current_revision: int = Field(ge=0)
updated_at: datetime
```

## `DiagramWorkspace` — frozen

```text
diagram: Diagram
current_revision: DiagramRevision | None
catalog: CatalogSnapshot
available_element_definitions: list[ElementDefinition] = Field(default_factory=list)
available_connection_definitions: list[ConnectionTypeDefinition] = Field(default_factory=list)
```

## `WorkingDiagramResult` — frozen

```text
revision_base: int = Field(ge=0)
working_elements: list[DiagramElement] = Field(default_factory=list)
working_connections: list[DiagramConnection] = Field(default_factory=list)
working_layout: DiagramLayout
validation: ValidationReport
```

Model validator:

- duplicate element and connection IDs rejected.

## `CommitRevisionResult` — frozen

```text
diagram: Diagram
revision: DiagramRevision
```

Model validator:

- IDs match;
- `diagram.current_revision == revision.revision`.

## `DiagramRevisionSummary` — frozen

```text
diagram_id: str
revision: int = Field(ge=1)
created_at: datetime
created_by: ActorRef
change_source: ChangeSource
change_summary: str | None
```

## `Page[T]`

Generic application model:

```text
items: list[T]
next_cursor: str | None
```

Whether the factory supports Pydantic generics directly must be checked before final assembly. If not, use concrete page models such as `DiagramSummaryPage` and `DiagramRevisionSummaryPage`.

---

# 9. Authoring commands

Generation unit:

```text
model_commands
→ hydraulic_diagram/domain/models/commands.py
```

All commands are frozen input models.

## `AddElementCommand`

```text
command_type: Literal["add_element"] = "add_element"
element_id: str = Field(min_length=1, max_length=200)
definition: DefinitionRef
label: str | None = Field(default=None, max_length=300)
quantity: Decimal = Field(gt=0)
properties: list[PropertyValue] = Field(default_factory=list)
layout: ElementLayout | None = None
```

Validator:

- duplicate property codes rejected.

## `SetElementPropertiesCommand`

```text
command_type: Literal["set_element_properties"] = "set_element_properties"
element_id: str
properties: list[PropertyValue]
```

Validator:

- at least one property;
- duplicate property codes rejected.

## `RemoveElementCommand`

```text
command_type: Literal["remove_element"] = "remove_element"
element_id: str
```

## `AddConnectionCommand`

```text
command_type: Literal["add_connection"] = "add_connection"
connection_id: str
source: PortRef
target: PortRef
connection_type: DefinitionRef
properties: list[PropertyValue] = Field(default_factory=list)
layout: ConnectionLayout | None = None
```

Validators:

- source and target differ;
- duplicate property codes rejected.

## `SetConnectionPropertiesCommand`

```text
command_type: Literal["set_connection_properties"] = "set_connection_properties"
connection_id: str
properties: list[PropertyValue]
```

## `RemoveConnectionCommand`

```text
command_type: Literal["remove_connection"] = "remove_connection"
connection_id: str
```

## `UpdateLayoutCommand`

```text
command_type: Literal["update_layout"] = "update_layout"
layout: DiagramLayout
```

## `AuthoringCommand`

```text
Annotated[
    AddElementCommand
    | SetElementPropertiesCommand
    | RemoveElementCommand
    | AddConnectionCommand
    | SetConnectionPropertiesCommand
    | RemoveConnectionCommand
    | UpdateLayoutCommand,
    Field(discriminator="command_type"),
]
```

---

# 10. Estimation-data models

Generation unit:

```text
model_estimation
→ hydraulic_diagram/domain/models/estimation.py
```

All models are frozen.

## `ElementEstimationItem`

```text
definition: DefinitionRef
name: str = Field(min_length=1, max_length=300)
estimation_refs: list[EstimationRef] = Field(default_factory=list)
quantity: Decimal = Field(gt=0)
unit_code: str = Field(min_length=1, max_length=40)
properties: list[PropertyValue] = Field(default_factory=list)
source_element_ids: list[str]
```

Validators:

- source list non-empty and unique;
- duplicate property codes rejected;
- duplicate estimation refs rejected.

`name` and `unit_code` serve the PresuPro handoff: `name` is projected from
the pinned definition version; `unit_code` defaults to the count unit `ud`.

## `ConnectionEstimationItem`

```text
connection_type: DefinitionRef
name: str = Field(min_length=1, max_length=300)
estimation_refs: list[EstimationRef] = Field(default_factory=list)
quantity: Decimal = Field(gt=0)
unit_code: str = Field(min_length=1, max_length=40)
properties: list[PropertyValue] = Field(default_factory=list)
source_connection_ids: list[str]
```

Validators mirror element item uniqueness rules.

## `DiagramMeasurement`

```text
code: str = Field(min_length=1, max_length=160)
value: Decimal
unit_code: str = Field(min_length=1, max_length=40)
source_entity_type: SourceEntityType
source_entity_ids: list[str]
method: MeasurementMethod
```

Validator:

- source IDs non-empty and unique;
- current domain rules reject `layout_route_length` during collection, not at schema construction.

## `MissingEstimationRequirement`

```text
code: str = Field(min_length=1, max_length=160)
entity_type: SourceEntityType
entity_id: str | None = Field(default=None, max_length=200)
property_code: str | None = Field(default=None, max_length=120)
reason: str = Field(min_length=1, max_length=1000)
required_by: str = Field(min_length=1, max_length=200)
can_agent_resolve: bool
```

## `EstimationWarning`

```text
code: str = Field(min_length=1, max_length=160)
message: str = Field(min_length=1, max_length=1000)
entity_type: SourceEntityType | None = None
entity_id: str | None = None
```

## `EstimationDataPackage`

```text
package_id: str = Field(min_length=1, max_length=200)
object_id: str = Field(min_length=1, max_length=200)
diagram_id: str = Field(min_length=1, max_length=200)
diagram_revision: int = Field(ge=1)
schema_version: int = Field(ge=1)
collector_rule_version: str = Field(min_length=1, max_length=80)
status: EstimationPackageStatus
element_items: list[ElementEstimationItem] = Field(default_factory=list)
connection_items: list[ConnectionEstimationItem] = Field(default_factory=list)
measurements: list[DiagramMeasurement] = Field(default_factory=list)
missing_requirements: list[MissingEstimationRequirement] = Field(default_factory=list)
warnings: list[EstimationWarning] = Field(default_factory=list)
generated_at: datetime
```

Model validators:

- `complete` forbids missing requirements;
- `invalid` may contain blocking integrity-derived requirements or warnings according to assembly policy;
- duplicate package item grouping identities rejected;
- stable ordering is created by `estimation_assembly`, not silently reordered by the model.

---

# 11. Change-request models

Generation unit:

```text
model_change_requests
→ hydraulic_diagram/domain/models/change_requests.py
```

The broad optional-field model is replaced with discriminated variants.

## `SetPropertyChange`

```text
change_type: Literal["set_property"] = "set_property"
entity_type: Literal["element", "connection"]
entity_id: str
property_code: str
suggested_value: TypedValue | None = None
notes: str | None = None
```

## `RemoveEntityChange`

```text
change_type: Literal["remove_entity"] = "remove_entity"
entity_type: Literal["element", "connection"]
entity_id: str
notes: str | None = None
```

## `ReviewRequiredChange`

```text
change_type: Literal["review_required"] = "review_required"
entity_type: SourceEntityType
entity_id: str | None = None
notes: str
```

## Deferred variants

The following require exact authoring payload decisions and remain deferred:

```text
AddElementChange
ReplaceDefinitionChange
AddConnectionChange
```

## `RequestedDiagramChange`

For v1:

```text
Annotated[
    SetPropertyChange | RemoveEntityChange | ReviewRequiredChange,
    Field(discriminator="change_type"),
]
```

## `DiagramChangeRequest`

```text
id: str
diagram_id: str
base_revision: int = Field(ge=1)
requested_by: ActorRef
reason_code: str
reason: str
changes: list[RequestedDiagramChange]
status: ChangeRequestStatus
resulting_revision: int | None = Field(default=None, ge=1)
created_at: datetime
```

Model validators:

- at least one change;
- `applied` requires `resulting_revision`;
- non-applied statuses forbid `resulting_revision`.

---

# 12. Public model facade

Generation unit:

```text
models
→ hydraulic_diagram/domain/models/__init__.py
```

The facade re-exports public model types from all model generation units.

Other packages should import from:

```python
from hydraulic_diagram.domain.models import Diagram, DiagramRevision, AuthoringCommand
```

Internal generation files may import concrete siblings directly when needed, but public consumers should use the facade.

---

# 13. Model module order

Candidate order:

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
model_change_requests
models
```

The exact order must respect imports discovered during contract assembly.

---

# 14. Pydantic validator ownership

## Generated inside model units

- duplicate codes within one model;
- local field normalization;
- scope/scope_ref coherence;
- minimum/maximum coherence;
- discriminator correctness;
- local status/result field coherence;
- list-local uniqueness;
- exact extra-field rejection.

## Generated in domain policy units

- referenced entity existence;
- catalog definition existence;
- port compatibility;
- scope permission in current object/diagram context;
- graph-wide connectivity;
- required properties by lifecycle stage;
- optimistic concurrency;
- authorization;
- revision atomicity.

---

# 15. Corrections to earlier documents

This document supersedes these conceptual shapes:

- `TypedValue` with several optional value fields;
- broad `RequestedDiagramChange` with operation plus optional payload fields;
- any informal model that lacks `extra="forbid"` semantics;
- any use of free strings where a controlled enum is defined here.

Earlier documents remain useful for intent and ownership, but State 6 contracts must use the concrete schemas from this document.

---

# 16. Remaining model decisions before final global spec

- exact decimal JSON serialization;
- whether the factory supports Pydantic generic models such as `Page[T]`;
- exact Pydantic version and syntax expected by the factory;
- whether enum/catalog values are generated as classes, constants, or both;
- whether draft working state requires a dedicated `WorkingDiagram` model;
- whether `DiagramChangeRequest` is included in v1;
- exact object gateway result model;
- idempotency request models;
- authorization resource reference model.

These do not block moving to function contracts, except the exact Pydantic version must be confirmed before code-generation notes are finalized.

## Readiness assessment

The model layer is ready for State 6 contract design because:

- all major data shapes are concrete;
- generic dictionaries are absent;
- unions are discriminated;
- local and domain validation ownership is separated;
- model files are bounded generation units;
- public facade imports are defined;
- exact function signatures can now use stable Pydantic types.
