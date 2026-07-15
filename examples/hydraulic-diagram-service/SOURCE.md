# Hydraulic Diagram Service — source context

## Purpose of this case study

This example is the first practical run of the `spec-authoring` skill.

The target is **not** the existing frontend repository itself. The target is a new backend microservice:

> Hydraulic Diagram Service — the source of truth for structured hydraulic diagrams, their catalogs, revisions, editor layout, and deterministic estimation-data packages.

The existing frontend is used as an implementation and domain reference.

## Source repositories

- Existing editor: `MigelSmirnov/hydraulic-diagram-editor`
- Authoring methodology and target specification standard: `MigelSmirnov/spec-workbench`

## Existing product evidence

The current frontend already demonstrates:

- visual placement of hydraulic elements;
- logical ports and port-to-port connections;
- typed line definitions;
- JSON save/load;
- autosave;
- undo/redo;
- PNG export;
- MCP-based diagram editing;
- executable validation before imported JSON replaces editor state;
- separation of JSON persistence and image export;
- catalog-driven element, port, line, and template definitions.

## New backend intent

The backend will serve several clients:

- the visual hydraulic diagram editor;
- a specialized diagram-authoring agent;
- the Estimator Service backend;
- the estimator's agent through agent-facing tools such as MCP;
- future project microservices that need structured diagram data.

The service must not be designed as a persistence wrapper for React Flow JSON. React Flow is a frontend implementation detail.

## Platform context

The platform's common entry point is the **Registry** (project hub and
published artifact catalog, deployed as `code_factory/projects/registry_sandbox`).
All microservices address it. It plays the role previously described as
"Object Card Service":

- a platform object is a Registry **project**: `id: UUID`, `name`, `address`,
  `status: active | archived`, `customer_ref`, plus project rooms;
- the common external `object_id` used by all services **is the Registry
  project UUID**;
- services publish per-project artifacts to the Registry
  (`artifact_type`, `owner_service`, `version`, `schema_version`, `uri`).

The contract is known (HTTP, `ProjectRecord` DTO), but object data must still
not spread into this service's domain model: Hydraulic Diagram Service
consumes only project existence and status through its gateway boundary and
never becomes a second source of truth for object or customer data.

The Estimator Service already has or is planned to have capabilities for:

- agent-driven estimate composition through MCP;
- matching live Brico Depot products and prices;
- saving materials;
- pushing a completed presupuesto to Holded.

These capabilities remain outside Hydraulic Diagram Service.

## Deterministic estimation-data collector

Hydraulic Diagram Service must provide a deterministic collector that converts a concrete diagram revision into a stable package for the Estimator Service.

The collector may:

- group diagram elements;
- count quantities;
- collect connection types and parameters;
- derive measurable lengths when supported by authoritative geometry;
- expose estimation classification references;
- report missing required properties;
- preserve provenance to source diagram entities.

The collector must not:

- calculate prices;
- select Brico Depot products;
- compose the final estimate;
- create a Holded presupuesto;
- invent missing engineering decisions.

## Consumer interfaces

The same domain operation that creates estimation data must be available through multiple transport boundaries:

- service-to-service HTTP API for Estimator Service;
- agent-facing API or MCP tools for the estimator agent.

Transport handlers must not implement independent package-building logic.

## Authoring modes

This case study is an architectural migration, not a literal reconstruction of the current frontend.

Decisions already accepted:

- durable diagram data is independent of React Flow;
- editor layout is separate from engineering structure;
- element definitions are distinct from element instances;
- agent-created definitions are controlled domain records, not arbitrary JSON;
- estimation-data generation is deterministic for fixed diagram and catalog revisions;
- the service stores and exposes revisions;
- API and MCP use the same application/domain operations.

## Current unknowns

The following remain intentionally unresolved and must be localized rather than hidden behind broad placeholders:

- authentication, authorization, tenancy, and service identity model;
- exact property set required by Estimator Service;
- supported hydraulic system taxonomy;
- concrete database technology;
- event bus or synchronous integration strategy;
- retention policy for diagram revisions.

## Resolved product decisions (2026-07-15)

The following former unknowns were decided in a product session and are owned
by the design states noted in parentheses:

- **Estimation handoff contract (PresuPro).** The estimator pulls
  `EstimationDataPackage` from this service (HTTP service-to-service, MCP for
  its agent); nothing is pushed. Matching convention: `EstimationRef`
  (`namespace`, `code`, `role`) uses the single v1 namespace `vbc`, and
  PresuPro resolves codes to its `Material` records through the existing
  `Material.aliases` mechanism — an unmatched code goes to PresuPro's agent
  matching flow, never to silent fabrication. Conversion of a package into an
  `EstimateZone` with items, prices, waste, margin, and IVA is PresuPro's
  domain; this service guarantees each item carries quantity, `unit_code`,
  display `name`, estimation refs, estimator-relevant properties, and source
  provenance. PresuPro-side tasks recorded separately: package-import use
  case + MCP tool, and alias data entered when catalogs are seeded. (State 0
  external systems, State 1 estimation items, State 2 collector rules.)
- **Discovery goes through the Registry; data stays with the services.** The
  estimator starts at the Registry (project list and header data, then
  `list_artifacts(project_id)` to learn which services participate) and
  fetches actual data from the owning services. Therefore this service has a
  v1 duty: maintain one `hydraulic_diagram` index artifact per project
  (payload lists diagrams and their current revisions), updated after each
  revision commit — post-transaction, non-blocking, discovery-only, never a
  second source of truth. Registry-side prerequisite: add `hydraulic_diagram`
  to its artifact types and `hydraulic` to its owner services (separate task
  in the Registry project). (State 0 outcomes and workflows, State 2 commit
  policy, State 4 post-commit flow.)
- **The object entry point is the Registry.** `object_id` is the Registry
  project UUID; the gateway DTO is known (`ProjectRecord`: name, address,
  status, customer_ref). In v1 this service consumes only project existence
  and status (verification before diagram creation); no other object field
  participates in domain behavior. (State 0 external systems, State 1
  `ObjectRef`, State 2 identity invariants.)
- **Pipe length is permanently out of scope for this service.** Diagram layout
  is presentation-only forever; deriving physical pipe lengths and spatial
  pipe routing belongs to a future plumbing service built on the platform's
  room-geometry foundation. Lengths inside a thermal unit enter only as
  explicit validated properties (`explicit_property`). (State 0 non-goals,
  State 2 layout authority policy.)
- **The service stores definition SVG assets.** An agent-created device must
  appear in the palette of every client, so its visual asset (SVG markup,
  default size, port anchors) is stored with the definition version as
  presentation data the estimation path ignores. (State 1
  `ElementVisualDefinition`, State 2 visual asset policy.)
- **Draft approval policy.** A diagram-scoped draft created mid-authoring is
  immediately usable in its owning diagram without human approval; global
  catalog activation requires human or catalog-admin approval. (State 2
  agent-created definition policy.)
- **A diagram declares a non-empty set of system kinds.** Real thermal-unit
  sheets combine subsystems (DHW with recirculation fed by a solar collector;
  boiler piping plus heating), so `system_kinds` is a set over the controlled
  enum `heating | cold_water | hot_water | solar_thermal`; the
  `mixed_hydraulic` pseudo-kind is removed. (State 1 `Diagram`, State 2
  taxonomy.)
- **The base catalog is seeded as data, not code.** Initial palette content
  is imported through the same validated definition mechanism, never baked
  into generated code, so adding a device never triggers factory
  regeneration. (State 0 outcomes, State 4 catalog bootstrap flow.)

## Scope rule

This case study specifies only Hydraulic Diagram Service.

Object Card Service, Estimator Service, Brico Depot integration, and Holded integration are external systems. They are described only to define stable boundaries and required outputs.
