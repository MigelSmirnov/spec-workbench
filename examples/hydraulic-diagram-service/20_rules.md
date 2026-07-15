# State 2 — Invariants, rules, config, and constants

## Goal

This state turns unresolved model semantics into explicit policy. It separates:

- invariants that must always hold;
- domain taxonomies and catalogs;
- read-only rules used by validation and estimation-data collection;
- runtime configuration that may change without changing domain meaning.

No HTTP routes, database tables, or function contracts are defined here.

---

# 1. Core invariants

## Diagram identity and ownership

1. Every `Diagram` belongs to exactly one external `object_id` — the Registry project UUID.
2. One `object_id` may own multiple diagrams.
3. Hydraulic Diagram Service does not own customer or object master data.
4. A diagram ID is stable for the lifetime of the diagram.
5. An archived diagram remains readable unless retention policy removes it.
6. When object verification is enabled (`config.database.object_verification_enabled`), a diagram may be created only for an existing, non-archived Registry project; when disabled, `object_id` is stored as an unverified reference.

## Revision invariants

1. Every committed `DiagramRevision` is immutable.
2. Revision numbers increase monotonically per diagram.
3. `Diagram.current_revision` points to the highest committed revision.
4. A commit must include the expected current revision to prevent silent lost updates.
5. A revision identifies exact element and connection definition versions.
6. Historical revisions remain resolvable after catalog definitions are deprecated.
7. A failed commit does not partially persist a revision.

## Engineering structure invariants

1. Element IDs are unique within a revision.
2. Connection IDs are unique within a revision.
3. Every connection endpoint references an element in the same revision.
4. Every referenced port exists in the pinned element definition version.
5. Every connection type exists and is permitted for both endpoints.
6. Instance properties must be declared by the pinned definition version.
7. Required authoring properties must be present before a revision may become active.
8. Unknown properties are rejected.
9. Layout cannot create, delete, or redefine engineering entities.
10. Transient UI state is never part of a committed revision.

## Catalog invariants

1. Active definition versions are immutable.
2. New semantic changes create a new version.
3. Definition codes remain stable across versions of one definition identity.
4. Draft definitions cannot be used outside their allowed scope.
5. Deprecated definitions remain readable but cannot be used for new instances unless policy explicitly permits it.
6. Rejected definitions cannot be used.
7. Agent-created definitions always retain actor and scope provenance.
8. A global active definition requires approval by an authorized human or trusted catalog service.

## Estimation-data invariants

1. Estimation data is built from one explicit diagram revision.
2. The collector uses the exact definition versions pinned by that revision.
3. Equal revision content and equal collector rules produce semantically equal output.
4. Missing values are reported and never guessed.
5. Package items preserve provenance to source element and connection IDs.
6. Prices, retailer products, budgets, and Holded data are forbidden.
7. A complete package contains no blocking missing requirements.
8. An invalid package indicates broken diagram integrity, not merely incomplete estimator properties.
9. HTTP and MCP must call the same collector behavior.

---

# 2. Domain taxonomies

These values are domain catalogs or controlled enums and therefore belong in `models` or `rules`, not runtime `config`.

## `DiagramSystemKind`

Initial supported values (resolved 2026-07-15):

```text
heating
cold_water
hot_water
solar_thermal
```

Deferred values:

```text
drainage
water_treatment
```

Policy:

- A diagram declares a non-empty author-declared set `system_kinds`. Real
  thermal-unit diagrams routinely combine subsystems on one sheet — DHW with
  recirculation fed by a solar collector today, boiler piping plus heating
  tomorrow — so mixing is represented by the set itself.
- The former `mixed_hydraulic` pseudo-kind is removed: it was a placeholder
  for exactly this decision and would have become the majority value,
  carrying no information.
- `system_kinds` serves discovery, listing, and labeling. Engineering
  compatibility is never derived from it; media and flow compatibility is
  owned by connection-level rules.
- New kinds require explicit catalog expansion rather than arbitrary strings.

## `MediumKind`

Initial values:

```text
water
hot_water
cold_water
heating_water
antifreeze_mix
unspecified
```

Policy:

- `unspecified` is allowed only for drafts and non-estimation-ready content.
- Active estimation-ready definitions should use a concrete medium where compatibility depends on it.

## `PortKind`

Initial values:

```text
hydraulic
control
sensor
drain
fill
unspecified
```

Policy:

- Hydraulic connections normally connect hydraulic ports.
- Other kinds require a compatible connection type definition.

## `FlowSemantics`

```text
bidirectional
inlet
outlet
supply
return
unspecified
```

Policy:

- `source` and `target` in serialization do not alone establish physical flow.
- Flow compatibility is evaluated using both endpoint semantics and connection policy.

## `DefinitionStatus`

```text
draft
active
deprecated
rejected
```

Allowed transitions:

```text
draft → active
draft → rejected
active → deprecated
```

Forbidden transitions:

```text
rejected → active
active → draft
deprecated → active
```

A new active replacement is created as a new version.

## `DefinitionScope`

```text
diagram
object
tenant
global
```

Policy:

- `diagram` requires `scope_ref = diagram_id`.
- `object` requires `scope_ref = object_id`.
- `tenant` remains disabled until tenancy is defined.
- `global` has no `scope_ref`.
- Narrower scopes may use broader definitions, but broader scopes may not use narrower definitions.

## `DiagramStatus`

```text
draft
active
archived
```

Allowed transitions:

```text
draft → active
draft → archived
active → archived
```

Reactivation is intentionally unsupported in the first version. A later policy may add `archived → active` with explicit audit requirements.

---

# 3. Connection compatibility rules

## Compatibility decision order

A connection is valid only when all checks pass in this order:

1. Both elements exist.
2. Both logical ports exist in pinned definition versions.
3. The endpoints are not the same logical port.
4. The connection type is active or historically permitted for the operation.
5. The connection type code is allowed by both ports when allow-lists are present.
6. Port kinds are compatible with the connection category.
7. Media are compatible.
8. Flow semantics are not contradictory.
9. Required connection properties are present and valid.

## Medium compatibility

Initial policy:

- Equal concrete media are compatible.
- `water` is compatible with `hot_water` and `cold_water` only when the connection definition explicitly declares generic-water compatibility.
- `unspecified` may connect in drafts but produces a blocking estimation requirement.
- `antifreeze_mix` is incompatible with potable-water media unless a connection definition explicitly permits both.

## Flow compatibility

Initial policy:

- `bidirectional` is compatible with any non-contradictory endpoint.
- `outlet` to `inlet` is valid.
- `supply` to `supply` is invalid unless a special manifold policy permits it.
- `return` to `return` is invalid unless a special manifold policy permits it.
- `inlet` to `inlet` and `outlet` to `outlet` are invalid.
- `unspecified` is allowed in drafts and becomes a validation warning or estimation blocker depending on the definition.

## Port multiplicity

Default policy:

- One logical port may have one connection.
- Definitions may declare multi-connect ports in a future version.
- Until then, a second connection to the same port is rejected.

This avoids silently modeling manifolds through accidental multi-edge behavior.

---

# 4. Property policy

## Validation

A `PropertyValue` is valid only when:

- its `property_code` exists in the pinned definition version;
- its type matches `PropertyDefinition.value_type`;
- allowed values are respected;
- numeric bounds are respected;
- no duplicate code exists on one entity;
- required values are present at the relevant lifecycle stage.

## Required stages

`required_for_authoring`:

- required before a revision can be activated;
- may be missing in an uncommitted working draft if validation reports it.

`required_for_estimation`:

- required for a complete `EstimationDataPackage`;
- absence does not necessarily invalidate the diagram itself;
- absence creates `MissingEstimationRequirement`.

## Defaults

- Catalog defaults may be applied only when `PropertyDefinition.default_value` exists.
- Applied defaults preserve `source = catalog_default`.
- A default must not be invented by an agent or collector.

## Units

Initial unit codes:

```text
unit
mm
cm
m
m2
m3
l
l_min
bar
kw
celsius
percent
```

Policy:

- Units are stable codes, not localized labels.
- Numeric property definitions that represent physical quantities must declare a unit.
- Conversion policy is deferred; initial values are stored in the declared unit.

---

# 5. Diagram revision policy

## Commit behavior

A revision commit requires:

```text
diagram_id
expected_current_revision
working engineering snapshot
working layout
actor
change_source
optional change summary
```

Policy:

- If `expected_current_revision` differs from the stored current revision, the commit is rejected as a conflict.
- Validation runs before persistence.
- The revision and the update of `Diagram.current_revision` are atomic.
- Revisions are append-only.
- Revision deletion is forbidden through normal application APIs.

## Snapshot strategy

Domain rule:

- Each revision must be reconstructable as a complete immutable snapshot.

Implementation freedom:

- full JSON snapshot;
- normalized revision tables;
- command log plus snapshot;
- hybrid storage.

The storage choice must not alter domain behavior.

## Registry index publication (resolved 2026-07-15)

Platform discovery pattern: participation is learned from the Registry, data
is fetched from the owning service. Therefore:

- the service maintains exactly one `hydraulic_diagram` index artifact per
  Registry project; its payload lists the project's diagrams with their
  current committed revisions;
- the index is refreshed after a successful revision commit, strictly outside
  the commit transaction;
- publication is non-blocking and best-effort: Registry unavailability never
  fails or delays a commit; a stale index is corrected by the next successful
  publication;
- the index is discovery data only — consumers must fetch actual diagram and
  estimation data from this service; the index is never a second source of
  truth;
- prerequisite recorded for the Registry project: artifact type
  `hydraulic_diagram`, owner service `hydraulic`.

---

# 6. Agent-created definition policy

## Draft creation

An authorized agent may create a draft definition when:

- no usable active definition exists;
- the requested scope is `diagram` or `object` by default;
- ports and property definitions are explicit;
- provenance is recorded;
- the definition passes structural catalog validation.

## Activation

Initial activation policy:

- diagram-scoped and object-scoped drafts may be activated by an authorized diagram owner or trusted service.
- global activation requires explicit human or catalog-admin approval.
- tenant activation remains disabled.

## Draft usability (resolved 2026-07-15)

The authoring workflow is synchronous: an agent creates a missing device
while a diagram is being drawn. Therefore:

- a diagram-scoped draft is immediately visible and usable in its owning
  diagram without human approval;
- a diagram containing draft-backed elements may be committed as a revision;
- the estimation collector accepts draft-backed items but marks each of them
  with an explicit warning naming the draft definition, so the estimator sees
  that a non-approved definition contributed to the package;
- outside its owning scope a draft remains invisible until activation.

## Catalog bootstrap (resolved 2026-07-15)

The base global catalog is seeded as data through the same definition
mechanism: the import runs under catalog-admin authority, passes full
structural validation, and produces `active` global definitions with system
provenance. No definition — seeded or agent-created — is represented in
generated code; adding a device never requires factory regeneration.

## Visual assets (resolved 2026-07-15)

Applies to every definition creation path (agent draft, seed import). The
purpose is asset hygiene, not threat defense: the SVG author is a
nondeterministic agent, and the stored asset must render identically in every
client, offline, and in image export.

- a definition version carries its immutable visual asset: `svg_markup`,
  default size, and port anchors;
- the SVG must be self-contained and inert: no scripts, no event handlers,
  no external references, no `foreignObject` — otherwise the same catalog
  entry renders differently across clients and breaks export;
- asset size is limited by one generous config value (candidate:
  `config.catalog.max_svg_markup_bytes`), because the catalog ships inside
  every `CatalogSnapshot` and a single oversized agent drawing would bloat
  every workspace load; the limit exists to keep the constraint concrete
  rather than "reasonable";
- the visual asset is presentation-only: rejection of a bad asset is a
  validation error, but the asset never defines ports, properties, or any
  engineering semantics, and estimation ignores it.

The `catalog` definition-creation boundary owns enforcement. Both agent draft
creation and catalog seed import pass `svg_markup` through the same catalog
visual-asset validator before an `ElementDefinition` is constructed or
persisted. Pydantic owns only local field shape (non-empty string and positive
dimensions); it does not parse or sanitize SVG and does not read runtime
catalog config.

## Promotion

Promotion does not mutate scope in place.

```text
local active definition
→ reviewed new global definition identity/version
```

Historical revisions keep their original reference.

## Prohibited agent behavior

An agent must not:

- overwrite active definitions;
- publish global definitions without approval;
- create arbitrary properties not declared in the draft;
- store raw executable code in definitions;
- use an unvalidated draft outside its permitted scope.

---

# 7. Layout authority policy

## Decision (permanent, resolved 2026-07-15)

Layout is presentation data, not authoritative engineering measurement — and
this is a permanent boundary of this service, not a temporary limitation.

Therefore:

- route points may be saved and restored;
- route points may support rendering;
- route points never determine pipe length for estimation;
- element positions and symbol dimensions are not physical building coordinates.

## Platform ownership of physical length

A thermal-unit schematic is topological. Physical pipe lengths derive from
building geometry, which on the platform is owned by the room-geometry
foundation service; spatial pipe routing and length derivation belong to a
future plumbing service built on that foundation. This service will never
grow a floor-plan model.

## Consequence for estimation

Connection length is complete only when provided through an explicit validated property (`explicit_property`).

The collector must emit a missing requirement when length is required but unavailable.

---

# 8. Estimation-data collector rules

## Input

The collector receives:

- one committed `DiagramRevision`;
- all exact referenced definition versions;
- current collector rule version.

## Output status

`complete`:

- diagram integrity is valid;
- all estimator-required properties are present;
- all required measurements are available.

`incomplete`:

- diagram integrity is valid;
- one or more estimator-required values are missing.

`invalid`:

- broken references, incompatible connections, duplicate identities, or invalid property values prevent safe collection.

## Element grouping

Element instances may be grouped only when all of these match:

- same definition ID and version;
- same estimation refs;
- same estimator-relevant property values;
- same unit semantics.

Quantity equals the sum of instance quantities.

## Connection grouping

Connections may be grouped only when all of these match:

- same connection definition ID and version;
- same estimation refs;
- same estimator-relevant property values;
- same quantity unit.

## Measurements

Enabled methods:

```text
count
property_sum
explicit_property
```

Disabled method:

```text
layout_route_length
```

## Item units and names (resolved 2026-07-15)

Every package item is self-describing for the estimator:

- element items carry an explicit `unit_code`: the count unit `ud` unless the
  pinned definition declares another quantity unit; the unit is never left
  implicit;
- connection items carry the unit declared by their measurement method;
- every item's `name` is projected from its pinned definition version at
  collection time, so PresuPro renders positions without catalog lookups;
- grouping keys include `unit_code`: items with different units are never
  merged.

until authoritative geometry is introduced.

## Missing requirements

A missing requirement must contain:

- stable code;
- entity type;
- entity ID where applicable;
- property code where applicable;
- reason;
- responsible consumer or rule;
- whether an agent may resolve it.

The collector never supplies a suggested value unless that value comes from an explicit catalog default.

## Determinism

The package semantic identity depends on:

```text
diagram_id
diagram_revision
referenced definition versions
collector_rule_version
```

Timestamps and generated package IDs are excluded from semantic equality.

---

# 9. API capability policy

This is domain-facing policy, not route design.

## Read capabilities

Estimator backend and estimator agent may:

- list diagrams for an object;
- read a committed revision;
- build estimation data;
- inspect missing requirements;
- inspect source entities and definition versions.

## Authoring capabilities

Editor and diagram-authoring agent may:

- create diagrams;
- create working changes;
- add or update elements;
- add or remove connections;
- create draft definitions;
- validate working state;
- commit revisions.

## Separation rule

Estimator read capability must not silently grant authoring capability.

An estimator agent may submit a `DiagramChangeRequest`, but applying it requires authoring authorization and normal validation.

---

# 10. Runtime config

These values are operational knobs and belong in `config`.

```text
revision.max_change_summary_length = 1000
revision.max_elements_per_revision = 5000
revision.max_connections_per_revision = 10000
catalog.max_ports_per_definition = 64
catalog.max_properties_per_definition = 128
catalog.max_allowed_values_per_property = 256
layout.max_route_points_per_connection = 256
estimation.max_missing_requirements = 1000
api.default_page_size = 50
api.max_page_size = 200
```

Policy:

- Limits prevent abuse and pathological payloads.
- Changing these values does not change domain meaning.
- Exceeding a limit returns explicit validation failure.

Not config:

- allowed state transitions;
- medium compatibility;
- definition scope rules;
- required estimation properties;
- grouping semantics.

Those belong in `rules` or versioned catalogs.

---

# 11. Draft rules projection for global specification

Candidate `rules` sections:

```text
diagram_status_transitions
definition_status_transitions
definition_scope_policy
connection_compatibility
medium_compatibility
flow_compatibility
port_multiplicity
property_validation_policy
revision_commit_policy
agent_definition_policy
layout_authority_policy
estimation_collection_policy
estimation_grouping_policy
api_capability_policy
```

Candidate `config` sections:

```text
revision limits
catalog limits
layout limits
estimation output limits
API pagination defaults
```

Candidate model catalogs:

```text
DiagramSystemKind
MediumKind
PortKind
FlowSemantics
DefinitionStatus
DefinitionScope
DiagramStatus
PropertyValueType
unit codes
```

---

# 12. Placeholder resistance review

## Rejected policy placeholders

- “connect compatible ports” without compatibility order.
- “agent may add new elements” without scope and activation rules.
- “calculate pipe length from diagram” while layout is not authoritative.
- “required properties” without authoring-versus-estimation stages.
- “handle concurrent edits” without expected revision checks.
- “use reasonable limits” without config values.
- “return warnings” without blocking versus non-blocking distinction.

## Deliberately deferred decisions

- exact estimator property requirements per catalog definition;
- tenant identity and authorization model;
- calibrated physical geometry;
- object-card DTO;
- event publication policy;
- revision retention and archival storage;
- reactivation of archived diagrams;
- multi-connect port support;
- unit conversion.

These are localized extension points, not generic placeholders in current models.

---

## State 2 readiness assessment

State 2 is sufficiently stable to begin module responsibility design because:

- core invariants are explicit;
- lifecycle transitions are defined;
- connection compatibility has an evaluation order;
- agent-created definitions have controlled scope and activation;
- layout authority is resolved for the first version;
- estimation completeness and determinism are defined;
- runtime knobs are separated from domain policy;
- remaining unknowns are isolated behind future capabilities or external boundaries.
