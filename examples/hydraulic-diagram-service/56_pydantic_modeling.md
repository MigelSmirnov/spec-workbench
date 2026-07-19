# Pydantic modeling rules

## Purpose

The code-generation factory is optimized for Pydantic models. Therefore, domain and boundary models in this case study must be designed so they can be generated as explicit Pydantic models rather than informal dataclasses or arbitrary dictionaries.

This does not change domain ownership. It changes how model constraints, unions, validation, serialization, and transport boundaries are expressed in the final specification.

## Base rule

> Every durable domain model, command model, application DTO, and transport-neutral result model is represented as a Pydantic model unless it is a simple enum or protocol interface.

Repository interfaces, gateways, and service protocols are not Pydantic models.

---

# Model configuration

All specification-generated Pydantic models should default to strict closed schemas.

Target semantics:

```python
model_config = ConfigDict(
    extra="forbid",
    validate_assignment=True,
    str_strip_whitespace=True,
)
```

Additional configuration may be applied per model:

- `frozen=True` for immutable value objects and committed snapshots;
- `use_enum_values=False` so domain enums remain enums in Python;
- `populate_by_name=True` only when aliases are actually required;
- `from_attributes=True` only for explicit ORM or adapter boundaries.

Do not enable permissive extra fields merely to support future expansion.

## Immutability

Use frozen Pydantic models for:

- `ActorRef`;
- `DefinitionRef`;
- `PortRef`;
- `TypedValue` variants;
- `PropertyValue`;
- catalog definition versions once constructed;
- committed `DiagramRevision`;
- `EstimationDataPackage` and its items.

Working-state and command models may remain mutable only when a concrete implementation need exists. Prefer producing new validated models over mutating shared instances.

---

# Enums

Controlled taxonomies should be generated as `str, Enum` types.

Examples:

```python
class ActorType(str, Enum): ...
class DiagramStatus(str, Enum): ...
class DefinitionStatus(str, Enum): ...
class DefinitionScope(str, Enum): ...
class MediumKind(str, Enum): ...
class PortKind(str, Enum): ...
class FlowSemantics(str, Enum): ...
class ValidationSeverity(str, Enum): ...
```

Rules:

- no free-form strings for controlled lifecycle states;
- enum values are stable wire values;
- display labels do not replace enum values;
- taxonomy expansion is explicit in `models` or `rules`.

---

# Typed values

The earlier conceptual `TypedValue` model should not be implemented as one model with four optional value fields. That shape permits invalid combinations and requires complex cross-field validation.

Prefer a discriminated union of concrete Pydantic models:

```python
class StringValue(BaseModel):
    value_type: Literal["string"]
    value: str

class IntegerValue(BaseModel):
    value_type: Literal["integer"]
    value: int

class DecimalValue(BaseModel):
    value_type: Literal["decimal"]
    value: Decimal

class BooleanValue(BaseModel):
    value_type: Literal["boolean"]
    value: bool

TypedValue = Annotated[
    StringValue | IntegerValue | DecimalValue | BooleanValue,
    Field(discriminator="value_type"),
]
```

This is a correction to the conceptual model from State 1.

Benefits:

- invalid field combinations are impossible;
- generated JSON Schema is explicit;
- HTTP and MCP share the same input schema;
- agent tool schemas become easier to understand;
- the LLM has less room to produce placeholder values.

---

# Authoring commands

`AuthoringCommand` should also be a discriminated union.

Each command model receives a stable literal discriminator:

```text
command_type = add_element
command_type = set_element_properties
command_type = remove_element
command_type = add_connection
command_type = set_connection_properties
command_type = remove_connection
command_type = update_layout
```

Conceptual shape:

```python
AuthoringCommand = Annotated[
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

Do not use:

```text
operation: str
payload: dict
```

The discriminated union is important for both API validation and MCP tool generation.

---

# Catalog and estimation-source unions (added 2026-07-17)

The specification standard normatively forbids untagged unions in type
positions. Three contracts used `ElementDefinition | ConnectionTypeDefinition`
(and a four-way variant in estimation-source inspection). They are replaced by
declared discriminated unions over a single shared tag field.

Tag field on the participating models, vocabulary aligned with the existing
`SourceEntityType` enum:

```text
DiagramElement.entity_kind           = Literal['element'] = 'element'
DiagramConnection.entity_kind        = Literal['connection'] = 'connection'
ElementDefinition.entity_kind        = Literal['element_definition'] = 'element_definition'
ConnectionTypeDefinition.entity_kind = Literal['connection_definition'] = 'connection_definition'
```

The field is additive with a constant default: previously persisted revision
payloads and definition rows without it remain valid, and serialized output
gains an explicit kind marker.

Declared unions:

```python
CatalogDefinition = Annotated[
    ElementDefinition | ConnectionTypeDefinition,
    Field(discriminator="entity_kind"),
]

EstimationSourceEntity = Annotated[
    DiagramElement
    | DiagramConnection
    | ElementDefinition
    | ConnectionTypeDefinition,
    Field(discriminator="entity_kind"),
]
```

Contract impact (state 60): `transition_definition_status` takes and returns
`CatalogDefinition`; `transition_definition_status_use_case` returns
`CatalogDefinition` (its `definition_kind: Literal["element", "connection"]`
lookup parameter is unchanged — it selects the repository getter);
`inspect_estimation_source` returns `EstimationSourceEntity`.

---

# Requested diagram changes

`RequestedDiagramChange` should use the same principle.

However, operations with structurally different payloads should become separate models rather than one model with many optional fields.

Candidate variants:

```text
SetPropertyChange
AddElementChange
ReplaceDefinitionChange
AddConnectionChange
RemoveEntityChange
ReviewRequiredChange
```

The current broad `RequestedDiagramChange` model remains conceptual and must be refined before final `models` assembly.

---

# Field constraints

Use Pydantic field constraints to encode local structural validity.

Examples:

- IDs and codes: `min_length=1`;
- names and labels: explicit max lengths from config or model rules;
- revision and version numbers: `ge=0` or `ge=1`;
- quantities: `gt=0`;
- viewport zoom: `gt=0`;
- width and height: `gt=0` when present;
- page size: bounded by config at application validation;
- lists such as ports, properties, route points: bounded by declared config limits.

Use `Decimal` rather than binary `float` for quantities, dimensions, measurements, and values that may later affect estimation.

Do not encode cross-entity rules solely as field constraints. Port compatibility, catalog lookup, scope access, and revision integrity remain domain policy.

---

# Validators

## Field validators

Use field validators for local normalization and single-field constraints not expressible directly through annotations.

Examples:

- stable code normalization;
- color format validation;
- rotation normalization when normalization is part of model construction;
- stripping and rejecting blank identifiers.

## Model validators

Use model validators for local cross-field invariants.

Examples:

- `scope_ref` required for diagram/object/tenant scopes and forbidden for global scope;
- minimum must not exceed maximum;
- default value must match property value type;
- `complete` estimation package cannot contain blocking missing requirements;
- applied change request requires resulting revision reference.

## Domain service validation

Do not move graph-wide or repository-dependent behavior into Pydantic validators.

The following remain in domain modules:

- referenced definition existence;
- port existence in a pinned definition;
- compatibility between endpoints;
- uniqueness across a full revision where assembly context is needed;
- scope permission requiring object/diagram context;
- optimistic concurrency;
- catalog lifecycle authorization.

Pydantic validates model integrity. Domain policy validates system meaning.

---

# Extra-field policy

Default:

```text
extra = forbid
```

This is especially important for:

- agent tool inputs;
- authoring commands;
- catalog definition drafts;
- imported diagram documents;
- estimation-data packages;
- external API DTOs.

Unknown fields should fail explicitly rather than be ignored or stored as metadata.

A genuinely open external payload must be isolated in a dedicated integration model with a documented reason. It must not spread into the core domain.

---

# Serialization boundaries

Pydantic models are the canonical serialization boundary for:

- HTTP request and response DTOs;
- MCP tool inputs and outputs;
- persisted revision snapshots when JSON storage is used;
- catalog definition import/export;
- estimation-data packages.

Use explicit serialization modes:

- JSON-compatible mode for transport and snapshots;
- Python mode for internal domain operations;
- stable enum and decimal serialization policy defined once.

Do not manually assemble nested response dictionaries in HTTP or MCP handlers.

---

# Persistence separation

Pydantic models do not imply that the database must store one JSON blob.

Repository adapters may map Pydantic domain models to:

- normalized SQL rows;
- JSON/JSONB snapshots;
- hybrid tables;
- document records.

The repository owns this mapping.

Do not add ORM fields, session objects, SQL identifiers, or database-specific metadata to core Pydantic models unless they are genuine domain fields.

---

# Pydantic model authoring sections and Factory unit

The model set is divided into the conceptual sections below so each family can
be reviewed independently. The current Factory deterministic-model convention,
however, assembles the complete runtime model surface into one generation unit:

```text
models → core/models.py
```

The `model_*` names below are authoring subdivisions, not separately generated
runtime modules.

Possible responsibilities:

- `enums.py`: controlled `str, Enum` types;
- `common.py`: `ActorRef`, `DefinitionRef`, `PortRef`, pagination and issue primitives where appropriate;
- `values.py`: discriminated `TypedValue` union and `PropertyValue`;
- `diagram.py`: `Diagram`, `DiagramRevision`, `DiagramElement`, `DiagramConnection`;
- `catalog.py`: definitions, ports, property definitions, visual definitions;
- `layout.py`: layout models;
- `estimation.py`: package and collection result models;
- `commands.py`: discriminated authoring commands;
- `change_requests.py`: change-request models and variants;
- `application.py`: workspace, summaries, reports, commit results.

`core.models` is the stable runtime model API used by every generated consumer.

---

# Factory specification implications

The future `global_spec.json` should:

1. include every Pydantic model in `models` with all fields and concrete types;
2. describe discriminators and closed unions in model notes or supported model metadata;
3. include Pydantic validators as explicit contracts when the factory generates validator functions or methods;
4. include `[SCHEMA_CONSTRAINT]` notes for `extra="forbid"`, frozen behavior, discriminators, and required cross-field invariants;
5. keep domain-policy functions outside Pydantic model validators;
6. keep the conceptual model families explicit in design-state documents;
7. assemble and expose all runtime model classes through `core.models`, the
   Factory-supported deterministic model boundary.

Authoring subsection names:

```text
model_enums
model_common
model_values
model_diagram
model_catalog
model_layout
model_estimation
model_commands
model_change_requests
model_application
models
```

The single generated `models` unit owns and exports the public model types.

---

# Placeholder resistance specific to Pydantic

Reject:

```python
class Payload(BaseModel):
    data: dict[str, Any]
```

Reject:

```python
class Command(BaseModel):
    operation: str
    payload: dict[str, Any]
```

Reject permissive defaults such as:

```text
extra = allow
```

Reject unions that can only be distinguished by guessing field presence.

Reject cross-field models composed of many optional values when a discriminated union represents the domain more precisely.

Reject Pydantic validators that perform database calls or hidden external I/O.

---

# Decision for State 6

Before creating exact function contracts:

1. revise conceptual models into concrete Pydantic shapes;
2. define enums and discriminated unions;
3. split model generation into bounded files;
4. identify local Pydantic validators;
5. keep graph-wide policy in domain modules;
6. use these generated models in all function signatures.

State 6 must not create contracts against the older informal `TypedValue` shape or generic command payloads.
