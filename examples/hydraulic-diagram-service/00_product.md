# State 0 — Product boundary

## Product statement

Hydraulic Diagram Service is a backend microservice that stores, versions, validates, and exposes structured hydraulic diagrams linked to a platform object through an external `object_id`.

It is the source of truth for:

- hydraulic diagram identity and lifecycle;
- durable engineering structure;
- diagram elements and their properties;
- port-to-port connections;
- catalog definitions used by saved diagrams;
- editor layout associated with a diagram revision;
- deterministic estimation-data packages derived from a concrete revision.

The service is not a generic file store and is not a backend wrapper around React Flow JSON.

## Primary clients

### Visual diagram editor

Uses the service to:

- create and open diagrams;
- load catalog definitions;
- save diagram changes;
- store editor layout;
- load and compare revisions;
- request validation results.

### Diagram-authoring agent

Uses controlled authoring operations to:

- create diagrams;
- add or update element instances;
- connect ports;
- fill required properties;
- create draft element or connection definitions when existing catalog entries are insufficient;
- validate and publish a new diagram revision.

The agent never writes directly to the database and must pass the same domain validation as other clients.

### Estimator Service backend

Uses a service-to-service API to:

- list diagrams associated with an `object_id`;
- request estimation data for an explicit diagram revision;
- inspect structured missing requirements and warnings;
- trace package items back to source elements and connections.

### Estimator agent

Uses agent-facing tools such as MCP to:

- discover diagrams for an object;
- request the same deterministic estimation package used by Estimator Service;
- inspect missing requirements;
- inspect source diagram entities and catalog definitions;
- prepare a structured request for a diagram correction when required.

Read access and diagram-authoring access are separate capabilities.

## Primary user and system outcomes

### Diagram lifecycle

A client can create a diagram linked to an external object and retrieve it later by diagram ID or object ID.

### Structured authoring

A client can add catalog-backed element instances, assign validated property values, and connect logical ports.

### Durable revision

A coherent set of diagram changes can be committed as a new immutable revision with actor and source provenance.

### Editor restoration

The visual editor can restore both engineering structure and its associated layout without making React Flow structures the durable domain model.

### Agent extensibility

When an existing element type is insufficient, an authorized agent can create a controlled draft definition with explicit ports, properties, estimation references, scope, and provenance.

### Estimation-data delivery

Estimator Service or its agent can request a deterministic `EstimationDataPackage` for a fixed diagram revision and fixed catalog definition versions.

### Incomplete-data reporting

If the diagram is insufficient for estimation, the service returns structured missing requirements and warnings rather than inventing values or returning a vague failure.

## Persistent data

The service persists at least these conceptual records:

- diagrams;
- immutable diagram revisions or revision snapshots;
- element instances;
- connection instances;
- element definitions and versions;
- connection type definitions and versions;
- property definitions and validated values;
- editor layouts associated with revisions;
- estimation-data package metadata or reproducibility references;
- actor and change provenance;
- draft definition status and scope.

The physical storage model remains undecided at this state.

## External systems

### Object Card Service

Future source of truth for object and customer data.

Current stable boundary:

- Hydraulic Diagram Service stores the external `object_id`;
- detailed object data is retrieved through a gateway when needed;
- the future DTO remains unresolved;
- the service must not become a second source of truth for customer or object data.

### Estimator Service

Owns:

- estimate composition;
- work and material positions;
- pricing;
- Brico Depot matching;
- material persistence for estimation purposes;
- final presupuesto;
- Holded integration.

Hydraulic Diagram Service supplies structured diagram-derived inputs only.

### Agent runtime / MCP host

Provides agent execution and tool transport. Agent availability must not affect deterministic estimation-data generation from a valid diagram.

## Explicit non-goals

Hydraulic Diagram Service does not:

- calculate prices or budgets;
- select retail products;
- communicate with Brico Depot;
- create or push Holded documents;
- own object or customer master data;
- render the frontend canvas;
- persist transient UI state such as selection, hover, or open panels;
- allow clients to store arbitrary unvalidated diagram JSON;
- perform hydraulic engineering calculations unless introduced as a separately specified capability;
- let the estimator agent silently mutate a diagram through read-oriented estimation tools.

## Current workflow boundaries

### Direct estimator workflow

```text
Estimator Service
→ request EstimationDataPackage for diagram revision
→ receive complete package or structured missing requirements
→ build estimate outside Hydraulic Diagram Service
```

### Agent-assisted estimator workflow

```text
Estimator agent
→ discover object diagrams
→ request EstimationDataPackage
→ inspect missing requirements and source entities
→ request or perform an authorized diagram correction through authoring capability
→ request the package again
→ compose estimate outside Hydraulic Diagram Service
```

### Diagram authoring workflow

```text
Editor or diagram agent
→ load catalog and current revision
→ apply validated commands
→ validate working diagram
→ commit immutable revision
→ optionally request estimation package
```

## Product invariants visible at State 0

These are product-level invariants; detailed ownership is deferred to later states.

1. Every diagram is linked to exactly one external `object_id`.
2. One external object may have multiple hydraulic diagrams.
3. A saved diagram revision identifies the exact catalog definition versions it uses.
4. React Flow data is not the authoritative durable engineering model.
5. Editor layout cannot create engineering entities that do not exist in the diagram revision.
6. Agent writes pass the same domain validation as UI or service writes.
7. Estimation data for fixed diagram and catalog revisions is deterministic.
8. Estimation packages preserve provenance to source diagram entities.
9. Missing engineering or estimation data is reported explicitly and is never fabricated.
10. HTTP and MCP expose the same underlying application/domain behavior.
11. Estimator-facing read tools do not silently modify the diagram.
12. Hydraulic Diagram Service is not a source of truth for customer, price, budget, or retail-product data.

## Explicit integration placeholder

The Object Card Service integration is intentionally incomplete until its real entry point and DTO are available.

Allowed placeholder boundary:

```text
ObjectGateway
→ get object data by object_id
```

Forbidden spread of that placeholder:

- `object_data: dict` inside diagram models;
- duplicated customer records owned by this service;
- business rules that depend on unknown object fields without declaring them as unresolved requirements.

## Unresolved decisions for later states

- Supported diagram system kinds and whether a diagram may contain several systems.
- Diagram statuses and publication lifecycle.
- Exact identity model for users, agents, and services.
- Draft-definition approval and visibility rules.
- Whether agent-created definitions may be scoped to diagram, object, tenant, or global catalog.
- Exact property types and units needed by the estimator.
- Whether layout routes are authoritative measurements or presentation only.
- How optimistic concurrency is represented when committing revisions.
- Whether estimation packages are persisted or built on demand.
- Whether diagram revisions store full snapshots, commands, or both.

## State 0 readiness assessment

The product boundary is sufficiently stable to begin domain-model design because:

- the service's source-of-truth responsibilities are explicit;
- primary clients and observable outcomes are known;
- external ownership boundaries are explicit;
- the estimator data collector has a narrow responsibility;
- the unavailable Object Card integration is localized;
- current unknowns are recorded rather than hidden behind generic data structures.
