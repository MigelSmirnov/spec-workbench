# Platform Router

> Living cross-application integration contract for the renovation platform.
>
> Status: architecture working document. This file is intentionally developed alongside application case studies and is not yet a finalized API specification.

## Purpose

The platform contains several planners and applications that work on the same renovation object. They must not form a mesh of pairwise application-to-application integrations.

The Platform Router is the shared integration boundary through which applications discover platform objects, discover participating services and their declared contracts, resolve shared platform data, and exchange versioned results.

The core idea is:

```text
Registry creates object identity
        ↓
all applications work under the same object_id
        ↓
services declare what artifact contracts they produce and consume
        ↓
applications resolve shared versioned platform data
        ↓
applications publish and consume versioned artifacts
        ↓
other planners, PresuPro, exporters, and the client cabinet consume those artifacts
```

Applications should depend on stable platform contracts rather than directly depending on each other.

## Emerging Platform Hub shape

The Platform Router is increasingly expected to become a **Platform Hub** rather than only a static API library.

The current architectural decomposition is:

```text
Platform Hub
│
├── Service Registry
│   who participates in the platform
│
├── Capability / Contract Registry
│   what each service declares it produces and consumes
│
├── Schema Registry
│   the canonical versioned schemas for exchanged artifact types
│
├── Artifact Registry
│   metadata, identity, revisions, provenance, and publication state
│
└── Artifact Store
    published artifact payloads or references to their storage
```

These are logical responsibilities. State 0 does not require them to be separate deployable services or separate databases.

The important boundary is semantic: applications must not discover integration contracts by directly inspecting another application's database or importing another application's internal Python modules.

## Service capability manifests

A participating application should be able to register or otherwise expose a **capability manifest** describing its platform-facing contract.

For the first platform version, a capability manifest is a **service passport**, not a general-purpose remote execution mechanism.

It is expected to describe at least, conceptually:

```text
service identity
service version
artifact types produced
artifact types consumed
supported artifact schema versions
schema references / identities
```

For example, conceptually:

```text
room-planner
    produces:
        room_plan.v1
        room_takeoff.v1
    consumes:
        construction_catalog.v1

cad-exporter
    consumes:
        room_plan.v1
    produces:
        drawing_set.v1
```

The exact manifest schema is deferred.

### Discovery is not compatibility

Service discovery and contract compatibility are separate meanings.

The Platform Hub may know that a new service or artifact type exists without implying that every existing application knows how to consume it.

A consumer is compatible only when it explicitly declares support for the relevant artifact type/schema version.

Therefore applications should not contain producer-specific branching such as:

```text
if producer == room-planner
if producer == tile-planner
```

when the real dependency is an artifact contract.

Instead, compatibility should be expressed through stable contract identities such as:

```text
room_takeoff.v1
tile_takeoff.v1
electrical_takeoff.v1
```

The producer remains important for provenance, but producer identity is not a substitute for a data contract.

### Capability manifests do not own business logic

A capability manifest describes externally usable contracts. It does not become the owner of planner calculations, estimating rules, construction rules, or rendering algorithms.

The Platform Hub must not turn capability discovery into arbitrary cross-service code execution.

A future platform may later introduce typed executable capabilities where a real use case requires them, but that would require an explicit security/authority design and is not implied by this service-discovery decision.

## Schema Registry

Artifact type identity and artifact schema are related but distinct.

Conceptually:

```text
artifact type:
    room_plan.v1

schema:
    exact structural contract for room_plan.v1
```

The Platform Hub should be able to answer which canonical schema belongs to a registered artifact contract and which schema versions a service can consume or produce.

Shared artifact schemas should be language-neutral. JSON Schema and/or OpenAPI components are current candidate representations so the same contracts can later generate or validate:

- Python/Pydantic boundary models and clients;
- TypeScript types and clients for browser applications.

### Schema immutability rule

A published schema version must not silently change incompatibly while retaining the same contract identity.

Conceptually, registration may bind an artifact contract to an immutable schema identity/hash:

```text
room_plan.v1
    ↓
schema identity/hash ABC123
```

Published artifacts can then preserve both their artifact contract version and exact schema identity when reproducibility requires it.

An incompatible structural change should produce a new contract version such as `room_plan.v2` rather than mutating the meaning of `room_plan.v1` in place.

The exact compatibility policy, schema hashing algorithm, and registration lifecycle are deferred.

## Existing platform systems

### Registry

Registry is the platform entry point and the authority that creates the renovation object card.

Other applications, including Room Planner:

- MUST NOT create platform objects independently;
- MUST be able to request the current list of objects available from Registry;
- MUST use Registry object identity when publishing or requesting platform data.

The exact Registry API is not defined here yet. It will be recorded when the first application flow requires a concrete contract.

### PresuPro

PresuPro is the estimating application that consumes results produced by planners and other applications.

PresuPro should consume platform artifacts rather than requiring every producer to implement a dedicated PresuPro-specific integration.

PresuPro owns pricing, labor/work costing, estimate composition, and conversion of physical quantities into purchasable package counts when commercial package conversion or whole-package rounding is required.

Upstream planners should publish reproducible physical quantities for the construction scope they own rather than embedding pricing or package-rounding logic.

PresuPro may also publish its own versioned result so that downstream applications can consume estimate-related data without a direct PresuPro dependency.

## Shared platform data: Construction Catalog

A shared versioned platform concept provisionally named **Construction Catalog** has been identified.

Its purpose is to provide technical construction/material parameters that may be consumed by multiple applications without hard-coding those values independently in each application.

Examples include:

- normalized material consumption rates;
- construction-system component definitions;
- layer definitions;
- stud/profile spacing rules;
- fastener spacing or consumption rules;
- technical thickness and density parameters where needed;
- package-size or similar technical material facts when downstream commercial conversion requires them;
- other measurable technical parameters required for deterministic quantity calculations.

The Construction Catalog is **not** a shared business-logic library.

It supplies technical facts/parameters. Each consuming application remains the owner of the calculation that applies those parameters to its own domain model.

For example:

```text
Construction Catalog
    mortar consumption rate
            ↓
Room Planner
    applies rate to net wall area + selected thickness
            ↓
room_takeoff
    physical quantity
            ↓
PresuPro
    pricing / work costing / package conversion
```

The exact ownership service, catalog schema, persistence model, and API are not yet defined.

### Catalog versioning requirement

Applications that publish calculations derived from Construction Catalog data must retain enough provenance to identify which catalog revision/version was used.

A later catalog change must not silently alter the meaning of an already published historical artifact.

## Artifact exchange model

An application does not conceptually "send its data to another application".

Instead, it publishes a result associated with a Registry object.

That result is called an **artifact**.

Current artifact families discovered so far include:

- `room_plan`
- `room_takeoff`
- `tile_plan` (provisional)
- `electrical_plan`
- `plumbing_plan`
- `estimate`
- `drawing_set`
- `client_package`

Additional artifact types MUST be introduced only when a real application requirement requires them.

Room Planner currently owns drywall and floor-leveling/fill quantity concerns directly, so separate `drywall_plan` or `floor_leveling_plan` artifacts are not assumed at this stage.

## Artifact Registry and Artifact Store

Published artifacts need a shared discovery location so consumers can find available results for a Registry object without querying every application separately.

The Platform Hub should therefore provide an Artifact Registry capable of answering questions such as:

- which artifact types exist for a Registry object;
- which revisions exist;
- which revision is currently published/applicable;
- which service produced an artifact;
- which schema contract/schema identity was used;
- which upstream artifacts or shared-data revisions produced it.

The Artifact Registry is distinct from an application's private working storage.

An application may keep drafts, editor state, internal entities, or transient calculations in its own persistence. Publication creates a platform-visible artifact.

Conceptually:

```text
Room Planner private working state
        ↓ publish
Platform Artifact Registry / Store
        ↓
immutable/versioned room_plan or room_takeoff
```

### Shared storage does not mean shared application tables

A common Artifact Store is acceptable and desirable.

A database directly shared as mutable internal storage by all applications is not.

Applications MUST NOT coordinate by reading or writing each other's internal tables.

The logical storage shape may initially be simple, for example:

```text
PostgreSQL
    artifact metadata
    small JSON/JSONB artifact payloads

object/file storage later when needed
    DXF
    PDF
    images
    large JSON payloads
```

Whether metadata and payloads begin in one PostgreSQL database or use separate object storage is an implementation decision for later states. The architectural rule is that access goes through the platform artifact boundary rather than direct cross-service database access.

## Artifact identity and provenance

Every exchanged artifact is expected to carry enough identity to support versioning and provenance.

Conceptually:

```text
artifact_id
object_id
artifact_type
schema_version
schema_identity/hash
revision
producer
created_at
publication_status
source_artifacts[]
source_data_revisions[]
```

These fields are architectural requirements, not yet finalized wire schemas.

`source_artifacts` allows downstream results to record exactly which upstream artifact revisions they were derived from.

`source_data_revisions` is a provisional concept for shared versioned data dependencies such as Construction Catalog revisions. Its final representation is unresolved.

Example:

```text
room_takeoff revision 12
├── room_plan revision 12
└── construction_catalog revision 7
```

and downstream:

```text
estimate revision 18
├── room_takeoff revision 12
├── electrical_plan revision 4
└── plumbing_plan revision 3
```

This provenance should make stale downstream results detectable when an upstream artifact or shared technical-data dependency receives a newer applicable revision.

## Room Planner platform outputs

Two Room Planner outputs are currently distinguished.

### `room_plan`

The spatial/construction-intent artifact used by downstream planners and platform consumers.

It represents the Room Planner-owned domain result, including the spatial baseline/proposed meaning required by later contracts.

### `room_takeoff`

The physical-quantity artifact derived from a specific `room_plan` plus an identified Construction Catalog revision/version.

It exists so that PresuPro and other consumers do not need to duplicate Room Planner geometry, drywall, plaster, putty, paint, or floor-fill calculation logic.

The artifact should eventually preserve enough provenance to trace quantities back to their source plan and source elements.

`room_plan` and `room_takeoff` are two artifacts from one application boundary; this distinction does not imply separate backend services.

Room Planner does not own production drawing generation in its initial scope. A downstream renderer/exporter may consume a published `room_plan` revision and publish a derived `drawing_set` or other client-facing drawing artifact with provenance back to that Room Planner revision.

## Platform contract rule

Shared platform contracts SHOULD be language-neutral.

The canonical contract may later be expressed through OpenAPI and/or JSON Schema so that the same boundary can produce:

- Python/Pydantic models and clients for generated backends;
- TypeScript types and clients for browser applications.

The shared contract MUST NOT become a library of cross-application business logic.

For example, it may define artifact references, catalog references, service manifests, schema identities, and publication semantics, but it must not own operations such as drywall calculation, wall drawing, estimate calculation, tile layout, or electrical design rules.

## Application adapter rule

Each application that participates in the platform should expose one explicit integration boundary to the Platform Hub.

During specification authoring, this boundary should be carried through the design pipeline as an external adapter/integration dependency.

The application remains the owner of its domain behavior. The Platform Hub owns only discovery, shared contract/schema semantics, and artifact exchange.

For Room Planner this means, conceptually:

```text
Room Planner domain
        ↓
Platform Hub adapter
        ├── Registry object discovery
        ├── Construction Catalog resolution
        ├── service/schema contract discovery when needed
        └── artifact publication/resolution
```

The concrete module, functions, contracts, and transport are intentionally deferred until the corresponding design states.

## Client cabinet rule

The client cabinet should consume published client-facing artifacts instead of integrating directly with every planner.

A planner may publish a domain artifact such as `room_plan`, while a rendering/export stage may publish a client-facing artifact such as a PDF, SVG, drawing set, or client package.

The exact publication policy is not yet defined.

## API ledger

This section is intentionally incremental.

Concrete API operations MUST be added only when an application design flow requires them. Each added operation should record:

- consumer;
- producer/owner;
- purpose;
- request semantics;
- response semantics;
- versioning behavior;
- failure behavior;
- idempotency expectations where relevant;
- provenance implications.

### Required capabilities discovered so far

The following are requirements, not final endpoint signatures:

1. Discover/list current Registry objects available to an application.
2. Register or resolve participating platform services.
3. Resolve a service's capability manifest / declared produced and consumed artifact contracts.
4. Register or resolve canonical versioned artifact schemas.
5. Determine declared producer/consumer compatibility for an artifact contract/schema version without assuming every service understands every discovered artifact type.
6. Resolve versioned Construction Catalog data required by an application calculation.
7. Resolve the exact Construction Catalog revision/version used by a previously published calculation when reproducibility is required.
8. Publish a versioned artifact for a Registry object with its artifact contract/schema identity and provenance.
9. List/discover published artifacts available for a Registry object.
10. Resolve an artifact for a Registry object, including an explicit revision and/or the current/latest applicable published revision.
11. Preserve artifact provenance and source revision references, including shared data revisions when applicable.
12. Expose selected published artifacts to downstream applications such as PresuPro, exporters, and the client cabinet.

No HTTP paths or final DTOs are defined yet.

## Quantity/pricing boundary

A platform planner may publish physical quantities derived from its owned domain logic.

PresuPro owns pricing, labor/work costing, estimate composition, and conversion of physical quantities into purchasable package counts when required.

Current working rule:

```text
planner geometry + planner rules + Construction Catalog technical data
        ↓
physical quantities
        ↓
PresuPro
        ↓
package conversion/rounding + prices + work costs + estimate
```

Upstream planners MUST NOT perform commercial whole-package rounding as part of their physical takeoff responsibility. Construction Catalog may provide package size or similar technical facts, while PresuPro owns the commercial conversion/rounding decision.

## Evolution rule

This document is a living platform contract.

When an application case study discovers a new integration requirement:

1. determine whether the requirement belongs to the application domain or to the shared platform boundary;
2. if shared, record the requirement here first;
3. add a concrete API contract only when the relevant design state is ready for it;
4. propagate the resulting adapter dependency through the application's later design states;
5. ensure the final application specification references the same platform contract rather than inventing a private application-specific variant.

When a new application joins the platform, existing applications should not require producer-specific code changes merely to discover that the service exists. The new service should declare its platform-facing contracts through the capability/schema registration model. Existing consumers become compatible only when they already support, or are explicitly upgraded to support, those artifact contracts.

By final assembly, this file should contain enough stabilized material to serve as the design source for the Platform Hub/router API layer itself.

## Open questions

- Is the Platform Hub one independent service, a gateway over several services, or a set of logical responsibilities initially hosted together?
- Which component owns service registration lifecycle and health/availability status?
- Is service registration static/configured, startup-driven, or explicitly administered?
- Which system owns artifact persistence and revision assignment?
- Are artifact metadata and small payloads initially stored together in PostgreSQL/JSONB, with file/object storage introduced only for larger payloads?
- What exact schema compatibility policy distinguishes backward-compatible evolution from a required new artifact contract version?
- Is Construction Catalog a standalone service, a platform module behind the Hub, or another implementation shape?
- Which artifacts, schemas, and catalog revisions are immutable after publication/registration?
- What publication states are required?
- How does authentication and authorization propagate between Registry, Platform Hub, and consuming applications?
- How are stale dependent artifacts surfaced to users?
- Does the client cabinet receive domain artifacts directly or only derived client-facing artifacts?
- When, if ever, should declarative capability manifests evolve into executable typed capabilities with explicit authority/effect semantics?
