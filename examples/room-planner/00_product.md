# Room Planner — State 0: Product Boundary

> Status: early working draft.
>
> This document records product-level decisions only. Concrete modules, Python contracts, HTTP endpoints, persistence schemas, and implementation algorithms are intentionally deferred.

## Product goal

Room Planner is a browser-based spatial planning application for renovation projects.

Its primary responsibility is to create and maintain an accurate spatial model of an existing renovation object: walls, connected geometry, rooms, openings, dimensions, and other spatial facts needed by downstream planning applications.

The editor must support practical construction work rather than act as a general-purpose CAD replacement.

## Platform object identity

Room Planner does not create renovation objects.

Registry is the platform entry point and creates the object card and canonical object identity.

Room Planner must:

- request the current objects available from Registry;
- open/work against an existing Registry object;
- associate all persisted and published Room Planner results with the Registry `object_id`;
- never create a parallel independent object identity.

## Platform integration boundary

Room Planner participates in the shared platform through the living [Platform Router](../../PLATFORM_ROUTER.md) contract.

The Platform Router document is intentionally developed alongside this case study. Integration requirements discovered while designing Room Planner should be added there when they are genuinely shared platform concerns.

Room Planner should not integrate directly with every downstream application.

Instead, it should publish a versioned spatial artifact associated with a Registry object. Downstream applications should consume that artifact through the shared platform boundary.

The exact adapter module, API operations, DTOs, and transport are deferred to later design states.

## Primary output

The primary domain artifact produced by Room Planner is provisionally named:

`room_plan`

A room plan is expected to represent the authoritative Room Planner result for a Registry object revision, including spatial geometry and the provenance/version information required by the platform.

The exact schema is deferred to the domain-model state.

## Relationship to PresuPro

PresuPro is the estimating application that consumes planning outputs.

Room Planner must make the data required for estimating available as a platform artifact, but Room Planner must not contain PresuPro-specific estimating logic.

PresuPro should consume published Room Planner results through the shared platform boundary rather than through a private Room Planner-to-PresuPro API.

## Relationship to downstream planners

Room Planner is expected to be an upstream spatial source for additional specialized planners.

Current examples include possible planners for:

- drywall construction;
- floor survey / floor leveling;
- electrical planning;
- plumbing planning;
- other renovation domains discovered later.

A specialized planner may consume Room Planner geometry without transferring ownership of its own domain logic into Room Planner.

## Product responsibility boundary

Room Planner owns spatial planning concerns such as:

- wall and connected-node geometry;
- rooms derived from spatial boundaries;
- wall openings such as doors and windows;
- construction-oriented dimensions;
- accurate placement in real-world units;
- the editable spatial representation of the object;
- publication of the resulting room-plan artifact.

Room Planner does not own specialized construction calculation simply because the calculation uses room geometry.

Examples currently considered outside Room Planner responsibility:

- drywall system/material calculation;
- floor-leveling engineering and material calculation;
- estimating and pricing;
- electrical engineering rules;
- plumbing engineering rules;
- client-cabinet behavior.

Room Planner may later visualize data from those systems as overlays without becoming the owner of their business rules.

## Precision constraint

The product is intended for real renovation work and must support millimeter-oriented spatial accuracy.

Screen pixels are not the domain coordinate system. Exact representation and interaction rules will be designed in later states.

## Frontend/backend constraint

The interactive Room Planner editor is currently expected to run in the browser.

The current AI Code Factory generates Python backend code only. This is a platform implementation constraint to keep in mind during later architecture work, but it does not change the Room Planner product boundary.

The browser editor and generated Python backend must therefore meet through explicit contracts rather than assuming that the Factory generates the frontend editor.

## Observable user outcomes discovered so far

A user can select an existing renovation object and work on its spatial plan.

The user should be able to produce a precise room plan that can be saved, revised, and consumed by other platform applications.

Changes to the room plan should result in a new identifiable revision rather than silently replacing the provenance of downstream work.

## Unresolved product questions

- Which wall/opening/object operations are mandatory for the first usable Room Planner release?
- Does Room Planner itself own drawing/PDF/SVG export, or does a separate renderer/exporter create those artifacts?
- Which non-spatial measurements belong directly to Room Planner and which should be separate survey artifacts?
- Which specialized planners are definitely in the platform roadmap versus only possible future applications?
- What information from Room Planner must PresuPro consume for its first integration?
- What parts of a room plan may be exposed directly to the client cabinet?
- What collaboration, locking, revision, and approval behavior is required?

## Cross-document rule

Any shared integration requirement discovered while progressing through later Room Planner design states must be evaluated against [PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md).

If it is a platform-wide exchange concern, update the Platform Router document rather than inventing a Room Planner-specific platform protocol.
