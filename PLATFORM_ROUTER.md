# Platform Router

> Living cross-application integration contract for the renovation platform.
>
> Status: architecture working document. This file is intentionally developed alongside application case studies and is not yet a finalized API specification.

## Purpose

The platform contains several planners and applications that work on the same renovation object. They must not form a mesh of pairwise application-to-application integrations.

The Platform Router is the shared integration boundary through which applications discover platform objects, resolve shared platform data, and exchange versioned results.

The core idea is:

```text
Registry creates object identity
        ↓
all applications work under the same object_id
        ↓
applications resolve shared versioned platform data
        ↓
applications publish and consume versioned artifacts
        ↓
other planners, PresuPro, and the client cabinet consume those artifacts
```

Applications should depend on stable platform contracts rather than directly depending on each other.

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

PresuPro owns pricing, labor/work costing, and estimate composition. Upstream planners should publish reproducible physical quantities for the construction scope they own rather than embedding pricing logic.

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
    pricing / work costing
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

## Artifact identity and provenance

Every exchanged artifact is expected to carry enough identity to support versioning and provenance.

Conceptually:

```text
artifact_id
object_id
artifact_type
schema_version
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

## Platform contract rule

Shared platform contracts SHOULD be language-neutral.

The canonical contract may later be expressed through OpenAPI and/or JSON Schema so that the same boundary can produce:

- Python/Pydantic models and clients for generated backends;
- TypeScript types and clients for browser applications.

The shared contract MUST NOT become a library of cross-application business logic.

For example, it may define artifact references, catalog references, and publication semantics, but it must not own operations such as drywall calculation, wall drawing, estimate calculation, tile layout, or electrical design rules.

## Application adapter rule

Each application that participates in the platform should expose one explicit integration boundary to the Platform Router.

During specification authoring, this boundary should be carried through the design pipeline as an external adapter/integration dependency.

The application remains the owner of its domain behavior. The Platform Router owns only the exchange boundary and shared platform semantics.

For Room Planner this means, conceptually:

```text
Room Planner domain
        ↓
Platform Router adapter
        ├── Registry object discovery
        ├── Construction Catalog resolution
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
2. Resolve versioned Construction Catalog data required by an application calculation.
3. Resolve the exact Construction Catalog revision/version used by a previously published calculation when reproducibility is required.
4. Publish a versioned artifact for a Registry object.
5. Resolve an artifact for a Registry object, including the current/latest applicable revision.
6. Preserve artifact provenance and source revision references, including shared data revisions when applicable.
7. Expose selected published artifacts to downstream applications such as PresuPro and the client cabinet.

No HTTP paths or final DTOs are defined yet.

## Quantity/pricing boundary

A platform planner may publish physical quantities derived from its owned domain logic.

PresuPro owns pricing and labor/work costing.

Current working rule:

```text
planner geometry + planner rules + Construction Catalog technical data
        ↓
physical quantities
        ↓
PresuPro
        ↓
prices + work costs + estimate
```

Commercial packaging conversion and whole-package rounding are intentionally unresolved. They must not be implicitly assigned to a component until the product workflow requires that decision.

## Evolution rule

This document is a living platform contract.

When an application case study discovers a new integration requirement:

1. determine whether the requirement belongs to the application domain or to the shared platform boundary;
2. if shared, record the requirement here first;
3. add a concrete API contract only when the relevant design state is ready for it;
4. propagate the resulting adapter dependency through the application's later design states;
5. ensure the final application specification references the same platform contract rather than inventing a private application-specific variant.

By final assembly, this file should contain enough stabilized material to serve as the design source for the platform router/API layer itself.

## Open questions

- Is the Platform Router an independent service, a gateway over several services, or a contract boundary implemented by another platform component?
- Which system owns artifact persistence and revision assignment?
- Is Construction Catalog a standalone service, a platform module behind the router, or another implementation shape?
- Which artifacts and catalog revisions are immutable after publication?
- What publication states are required?
- How does authentication and authorization propagate between Registry and consuming applications?
- How are stale dependent artifacts surfaced to users?
- Does the client cabinet receive domain artifacts directly or only derived client-facing artifacts?
- Who owns commercial package conversion/rounding when physical quantities must become purchasable package counts?
