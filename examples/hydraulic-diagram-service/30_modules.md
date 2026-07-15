# State 3 — Module responsibilities

## Goal

This state assigns ownership of knowledge, decisions, invariants, and public capabilities.

Modules are derived from responsibility, not from transport routes, database tables, UI screens, or generic technical verbs.

The target is a set of deep modules with small public APIs and substantial hidden behavior.

---

# 1. Responsibility map

## `domain_models`

### Owns

- shared immutable domain models;
- enum-like taxonomies approved in State 2;
- value objects such as `ActorRef`, `DefinitionRef`, `PortRef`, `TypedValue`, and `PropertyValue`;
- serialization-safe domain DTO shapes.

### Knows

- field structure and type relationships;
- no persistence or transport behavior.

### Must not own

- validation policy;
- catalog lookups;
- revision commits;
- HTTP or MCP serialization rules;
- database mappings.

### Public surface

Exports model types only.

### Depth assessment

This is a stable foundational module, not a business service. Its depth comes from providing a coherent type system used everywhere else.

---

## `catalog`

### Owns

- element definitions and versions;
- connection type definitions and versions;
- port and property definitions;
- definition scope and status lifecycle;
- draft creation;
- activation, rejection, deprecation, and version replacement;
- catalog lookup constrained by diagram/object/global scope;
- catalog validation.

### Knows

- definition invariants;
- scope visibility;
- status transitions;
- version immutability;
- agent-created definition policy;
- estimation references attached to definitions.

### Hides

- how definition versions are stored;
- how scope resolution searches local and global catalogs;
- how activation approval is represented;
- how duplicate definition codes are detected;
- internal validation sequencing.

### Must not own

- diagram instances;
- connection instance validation across a full diagram;
- editor layout;
- estimation package grouping;
- prices or retailer product matching;
- transport handlers.

### Candidate public capabilities

```text
get_element_definition
get_connection_type_definition
resolve_catalog_snapshot
list_available_element_definitions
list_available_connection_types
create_element_definition_draft
create_connection_definition_draft
activate_definition
reject_definition
deprecate_definition
```

### Public API pressure

The final public API should avoid exposing separate low-level methods for ports, properties, and estimation refs. Those are internal parts of definition operations.

### Depth assessment

Deep module. It hides versioning, scope policy, validation, and governance behind catalog-level operations.

---

## `diagram`

### Owns

- diagram identity;
- link to `object_id`;
- diagram lifecycle status;
- working engineering structure;
- element instances;
- connection instances;
- domain authoring operations;
- structural consistency before revision commit.

### Knows

- which elements and connections currently exist;
- how commands alter working state;
- how instance properties are assigned;
- that definitions are pinned by exact version;
- which actor initiated a working change.

### Hides

- internal mutation sequencing;
- element and connection lookup indexes;
- cascade behavior for entity removal;
- temporary working-state representation;
- command composition.

### Must not own

- catalog-definition lifecycle;
- persistence transactions;
- HTTP/MCP request parsing;
- final revision numbering;
- estimation grouping;
- frontend React Flow state.

### Candidate public capabilities

```text
create_diagram
load_working_diagram
add_element
update_element_properties
remove_element
add_connection
update_connection_properties
remove_connection
validate_working_diagram
change_diagram_status
```

### Design note

`load_working_diagram` may later belong to an application facade rather than the pure domain module. It is listed here as a capability need, not a final contract.

### Depth assessment

Deep module. It hides command semantics and aggregate consistency behind diagram authoring operations.

---

## `diagram_policy`

### Owns

- validation of diagram structure against catalog definitions;
- port existence checks;
- connection compatibility;
- property validation;
- authoring-required property checks;
- scope permission for definition use;
- transition validation for diagram status;
- distinction between warnings and blocking violations.

### Knows

- connection compatibility rule order;
- medium compatibility;
- flow semantics compatibility;
- port multiplicity policy;
- property-stage requirements;
- draft versus active validation thresholds.

### Hides

- rule evaluation order;
- aggregation of validation findings;
- mapping from low-level failures to stable issue codes.

### Must not own

- mutation of diagrams;
- catalog activation;
- persistence;
- estimation grouping;
- transport-specific error responses.

### Candidate public capabilities

```text
validate_diagram_structure
validate_element_instance
validate_connection_instance
validate_revision_readiness
```

### Consolidation decision

This remains separate from `diagram` because:

- the rule set is large and independently testable;
- estimation and import flows also need validation;
- keeping rules outside mutation logic prevents a shallow giant aggregate service.

### Depth assessment

Deep policy module.

---

## `revision`

### Owns

- immutable revision creation;
- expected-current-revision concurrency check;
- revision numbering;
- atomic commit orchestration;
- update of `Diagram.current_revision`;
- revision metadata and provenance;
- revision loading and comparison-ready snapshots.

### Knows

- append-only revision policy;
- commit preconditions;
- atomicity requirements;
- schema-version assignment;
- relationship between diagram identity and revision snapshots.

### Hides

- persistence transaction boundaries;
- snapshot serialization strategy;
- normalized versus JSON physical storage;
- conflict detection implementation.

### Must not own

- domain mutation commands;
- catalog governance;
- connection policy;
- HTTP conflict response formatting;
- estimation collection.

### Candidate public capabilities

```text
commit_revision
get_revision
get_current_revision
list_revisions
```

### Depth assessment

Deep module. It protects immutability, concurrency, and transactional consistency.

---

## `layout`

### Owns

- validation and normalization of `DiagramLayout`;
- consistency between layout references and engineering entities;
- rotation normalization;
- viewport validation;
- route-point limits;
- deterministic default placement for layout-less agent-created diagrams, if adopted.

### Knows

- presentation-only authority rule;
- layout limits from config;
- which transient fields are forbidden.

### Hides

- default-placement algorithm;
- layout normalization;
- validation issue details.

### Must not own

- engineering connectivity;
- physical measurement;
- React Flow-specific node and edge objects;
- image export;
- persistence transactions.

### Candidate public capabilities

```text
validate_layout
normalize_layout
create_default_layout
```

### Consolidation decision

Keep separate from `diagram_policy` because layout uses different invariants and may evolve independently toward calibrated geometry.

### Depth assessment

Moderately deep. It becomes truly deep when deterministic placement or future geometry authority is introduced.

---

## `estimation_data`

### Owns

- deterministic construction of `EstimationDataPackage`;
- estimator-required property inspection;
- element grouping;
- connection grouping;
- supported measurements;
- missing requirements;
- non-blocking warnings;
- provenance to source entities;
- package semantic reproducibility.

### Knows

- grouping equality rules;
- estimator-relevant property flags;
- enabled measurement methods;
- package status semantics;
- collector rule version.

### Hides

- grouping indexes;
- property normalization;
- missing-requirement aggregation;
- semantic package hashing or reproducibility metadata;
- ordering of output items.

### Must not own

- prices;
- retailer matching;
- estimate composition;
- Holded integration;
- diagram mutation;
- catalog activation;
- separate HTTP and MCP business logic.

### Candidate public capabilities

```text
build_estimation_data
```

Possible diagnostic capabilities should preferably be projections of the same result rather than separate business operations:

```text
get_missing_estimation_requirements
inspect_estimation_source
```

### Depth assessment

Very deep module. A small public API hides validation, grouping, measurements, completeness analysis, and provenance.

---

## `change_requests`

### Owns

- creation and lifecycle of `DiagramChangeRequest`;
- read-to-write boundary for estimator agents;
- base revision binding;
- acceptance, rejection, and applied status;
- handoff into normal diagram authoring flow.

### Knows

- who requested the change;
- why it was requested;
- which revision it targets;
- whether it has been applied.

### Hides

- request status transition checks;
- conversion from accepted request into authoring commands;
- audit linking between request and committed revision.

### Must not own

- silent diagram mutation;
- estimation-data collection;
- authorization policy implementation;
- transport handlers.

### Candidate public capabilities

```text
create_change_request
accept_change_request
reject_change_request
mark_change_request_applied
get_change_request
```

### Consolidation decision

Keep separate because it protects an important capability boundary and has its own lifecycle. It may be omitted from the first implementation if estimator write-back is postponed, but the module boundary remains valid.

### Depth assessment

Moderately deep lifecycle module.

---

## `object_gateway` (Registry gateway)

### Owns

- the platform Registry integration (project hub, resolved 2026-07-15);
- translation of the Registry `ProjectRecord` into the internal `ObjectSnapshot` (existence + status only);
- project verification checks when `object_verification_enabled` is true;
- outbound publication of the per-project `hydraulic_diagram` index artifact after revision commits (post-transaction, non-blocking);
- integration timeout and failure mapping.

### Knows

- the Registry endpoint and its known `ProjectRecord` / artifact publication DTOs.

### Hides

- HTTP client details;
- authentication headers;
- retries;
- external schema evolution.

### Must not own

- object/customer master data;
- diagram business rules;
- generic arbitrary object dictionaries;
- persistence of copied customer records.

### Candidate public capability

```text
get_object_snapshot
```

### Current placeholder policy

The module may initially provide a local or disabled adapter, but its return model must be defined only from real integration evidence.

### Depth assessment

Adapter boundary. Not a deep domain module, but essential for containing the known placeholder.

---

## `repositories`

### Owns

- persistence interfaces for diagrams, revisions, catalog definitions, layouts, and change requests;
- transaction abstraction required by revision commit;
- storage retrieval semantics.

### Knows

- domain persistence needs, not business policy.

### Hides

- SQL or document-store details;
- table or collection names;
- serialization format;
- query implementation.

### Must not own

- validation decisions;
- status transitions;
- estimation grouping;
- transport errors;
- external object integration.

### Candidate public abstractions

```text
DiagramRepository
RevisionRepository
CatalogRepository
ChangeRequestRepository
UnitOfWork
```

### Consolidation decision

Do not create one generic `Repository[T]`. Each repository expresses domain-specific retrieval and atomicity needs.

### Depth assessment

Infrastructure boundary. Depth comes from hiding persistence technology while preserving domain semantics.

---

## `application`

### Owns

- use-case orchestration across domain modules;
- loading required aggregates and catalog snapshots;
- calling domain authoring behavior;
- invoking policy validation;
- committing revisions;
- building estimation data;
- enforcing capability-level authorization supplied by the identity boundary;
- mapping domain outcomes into transport-neutral application results.

### Knows

- use-case sequence;
- which repositories and modules are required;
- transactional application boundaries;
- read versus authoring capability separation.

### Hides

- orchestration from HTTP and MCP handlers;
- domain loading sequence;
- consistent error/result mapping.

### Must not own

- domain rule implementation;
- SQL;
- HTTP request objects;
- MCP protocol objects;
- frontend models.

### Candidate public use cases

```text
create_diagram
get_diagram
list_object_diagrams
apply_diagram_command
commit_diagram_revision
get_diagram_revision
build_diagram_estimation_data
create_definition_draft
change_definition_status
create_diagram_change_request
```

### Depth assessment

Deep application facade when kept use-case-oriented. Avoid a generic `DiagramService` with dozens of unrelated methods.

---

## `http_api`

### Owns

- HTTP routing;
- request parsing;
- authentication/dependency wiring;
- DTO conversion;
- status-code mapping;
- response serialization;
- pagination parameters.

### Knows

- transport contract only.

### Hides

- framework-specific route wiring from the application layer.

### Must not own

- catalog policy;
- diagram mutation logic;
- estimation grouping;
- direct database access;
- separate behavior from MCP.

### Public surface

HTTP routes only.

### Depth assessment

Thin boundary by design.

---

## `mcp_api`

### Owns

- MCP tool registration;
- tool input validation;
- tool output serialization;
- agent-friendly descriptions;
- capability-scoped tool exposure.

### Knows

- MCP transport and tool metadata.

### Hides

- protocol mechanics from application use cases.

### Must not own

- diagram or catalog business logic;
- independent estimation-data building;
- direct persistence;
- automatic escalation from read to authoring capability.

### Public surface

Agent tools only.

### Depth assessment

Thin transport boundary.

---

# 2. Modules intentionally not created

## No `utils`

Shared helpers must remain private to their owning module or become named domain value modules.

## No generic `manager`

Lifecycle ownership is split among `diagram`, `revision`, `catalog`, and `change_requests`.

## No generic `validator`

Validation is owned by `diagram_policy`, `catalog`, and `layout` according to domain responsibility.

## No generic `services`

Use cases live in `application`; domain behavior remains in domain modules.

## No separate `estimator_client`

Hydraulic Diagram Service is consumed by Estimator Service. It does not call Estimator Service to compose estimates.

## No React Flow adapter in the backend core

A frontend-specific adapter may exist at the HTTP DTO boundary or in the frontend repository, but it is not part of the durable domain architecture.

---

# 3. Dependency direction

Proposed dependency direction:

```text
domain_models
    ↓
catalog, diagram_policy, layout
    ↓
diagram, estimation_data, change_requests
    ↓
revision
    ↓
application
    ↓
http_api, mcp_api
```

Infrastructure implementations point inward through interfaces:

```text
repositories implementations → repository interfaces used by application/revision
object gateway adapter → object_gateway interface used by application
```

More explicit allowed dependencies:

```text
catalog → domain_models
layout → domain_models

diagram_policy → domain_models + catalog read models/rules

diagram → domain_models + diagram_policy interfaces + catalog snapshots

estimation_data → domain_models + diagram_policy + catalog snapshots

revision → domain_models + diagram_policy + layout + repositories

change_requests → domain_models + repositories

application → all use-case modules + repository interfaces + object_gateway

http_api → application + transport DTOs
mcp_api → application + transport DTOs
```

Forbidden dependencies:

```text
domain modules → HTTP or MCP
catalog → diagram instances
diagram_policy → persistence
estimation_data → retailer or price integrations
repositories → domain policy decisions
http_api or mcp_api → database implementations directly
```

---

# 4. Public API design pressure

The current module map suggests these primary cross-module capabilities:

```text
catalog.resolve_catalog_snapshot
catalog.create_definition_draft
catalog.transition_definition_status

diagram.create_diagram
diagram.apply_authoring_command
diagram.validate_working_state

revision.commit_revision
revision.get_revision
revision.list_revisions

estimation_data.build_estimation_data

change_requests.create_change_request
change_requests.transition_change_request

object_gateway.get_object_snapshot
```

This list is intentionally smaller than the full set of internal operations.

The next state must test whether callers can remain ignorant of internal sequencing.

---

# 5. Candidate module paths

```text
src/hydraulic_diagram/domain/models.py
src/hydraulic_diagram/domain/catalog.py
src/hydraulic_diagram/domain/diagram.py
src/hydraulic_diagram/domain/diagram_policy.py
src/hydraulic_diagram/domain/layout.py
src/hydraulic_diagram/domain/estimation_data.py
src/hydraulic_diagram/domain/change_requests.py
src/hydraulic_diagram/domain/revision.py

src/hydraulic_diagram/application/use_cases.py
src/hydraulic_diagram/application/ports.py

src/hydraulic_diagram/infrastructure/persistence/
src/hydraulic_diagram/infrastructure/object_card/

src/hydraulic_diagram/api/http/
src/hydraulic_diagram/api/mcp/
```

Path names are provisional. The responsibility boundaries are more important than exact directories.

---

# 6. Module order candidate

For eventual `module_order`:

```text
domain_models
catalog
diagram_policy
layout
diagram
estimation_data
change_requests
repositories
object_gateway
revision
application
http_api
mcp_api
```

The exact order may change after contracts reveal narrower dependency needs.

---

# 7. Deep-module review

## Clearly deep

- `catalog`
- `diagram`
- `diagram_policy`
- `revision`
- `estimation_data`
- `application`

## Moderately deep

- `layout`
- `change_requests`

## Thin by design

- `http_api`
- `mcp_api`
- `object_gateway`
- repository implementations

Thin boundaries are acceptable because they adapt transports or infrastructure. They must not accumulate product decisions.

---

# 8. Placeholder resistance review

## Rejected module placeholders

- `DiagramManager`
- `HydraulicService`
- `AgentService`
- `EstimatorHelper`
- `ValidationUtils`
- `DataProcessor`
- `CommonRepository`

Each of these hides unresolved ownership.

## Resolved ownership questions

- Catalog lifecycle belongs to `catalog`.
- Instance mutation belongs to `diagram`.
- compatibility and structural validation belong to `diagram_policy`.
- immutable commit and concurrency belong to `revision`.
- editor presentation policy belongs to `layout`.
- estimator package construction belongs to `estimation_data`.
- read-to-write estimator requests belong to `change_requests`.
- transport orchestration belongs to `http_api` or `mcp_api` only.
- cross-module use-case orchestration belongs to `application`.

## Deliberately unresolved

- whether working drafts are persisted as first-class records;
- whether `change_requests` is included in the first release;
- exact authorization port and identity model;
- exact repository interfaces;
- whether catalog and diagram commands use one generic command envelope or typed commands.

These questions belong to flow and public-API design, not to generic catch-all modules.

---

## State 3 readiness assessment

State 3 is sufficiently stable to begin key flow design because:

- every major invariant has a primary owner;
- domain modules are separated from transports and persistence;
- estimator data has one clear owner;
- HTTP and MCP are thin adapters to shared application use cases;
- the Registry integration is contained in one adapter boundary;
- no generic utility, manager, validator, or service module is required;
- dependency direction is explicit;
- deep and intentionally thin modules are distinguished.
