# Room Planner — State 1: Wall Elevation Projection Boundary

> Status: accepted State 1 correction/refinement.
>
> This document keeps the wall-face elevation projection and explicitly retracts
> the previously proposed Room Planner furniture/layout domain models. Generic
> furniture/layout blocks belong to shared frontend/editor infrastructure, not to
> Room Planner backend state.

## 1. No separate elevation drawing model

Room Planner must not persist a second drawing that duplicates walls, openings,
niches, ceiling edges, or construction geometry merely because the user is
looking at a wall frontally.

The elevation projection is derived from:

```text
selected wall face
+ canonical wall/opening/niche data
+ floor/ceiling surfaces
+ ceiling regions intersecting the face
+ other Room Planner-owned geometry visible on that face
```

Viewport orientation, crop, pan/zoom, selected wall face, hidden layers, and
render-only dimensions are editor state unless a later explicit saved-view
feature is introduced.

## 2. Canonical wall-face local coordinates

A wall-face elevation uses the existing directed wall and `WallSide` semantics.

Conceptually:

```text
u = distance along directed host wall start → end
z = project vertical/elevation axis
```

The canonical domain models continue to store their existing wall-relative and
vertical values. The elevation renderer may transform those values into view
coordinates but must not create a second persisted `x/y` geometry for the same
feature.

User-facing dimensions may be shown relative to local floor where that matches
the owning field semantics, while absolute surface/elevation calculations remain
tied to the project datum.

## 3. Elevation adds no new Room Planner aggregate

State 1 does not add an `ElevationDrawing`, `ElevationModel`, or other durable
aggregate for this view.

Existing Room Planner entities already provide the needed identity and geometry:

- wall / wall face;
- opening / opening element / door swing;
- wall niche;
- floor and ceiling surfaces;
- ceiling boxes/niches and other Room Planner-owned construction geometry.

The elevation is therefore a projection concern for later module/flow/frontend
states, not a new durable source of truth.

## 4. Previously proposed furniture domain models are retracted

The following shapes from the earlier version of this document are **not** Room
Planner domain models and must not be implemented in the Room Planner backend:

```text
FurnitureDefinitionRef
FurnitureEnvelope
FloorFurniturePlacement
WallFurniturePlacement
FurniturePlacement
FurnitureLayoutDraft
FurnitureLayoutSnapshotRef
FurnitureLayoutSnapshot
```

They must not appear in:

- Room Planner Pydantic/domain models;
- Room Planner persistence;
- Room Planner snapshot/basis graphs;
- Room Planner carry-forward logic;
- `room_plan` or `room_takeoff` contracts merely as generic furniture layout;
- Room Planner public APIs.

This is an ownership correction, not a rename.

## 5. Shared frontend block overlays stay outside State 1 domain models

The shared browser workspace may maintain frontend/editor-only block definitions
and overlay placements for furniture or other visual planning aids.

Their reusable library schema, multi-view SVG assets, editor placement state, and
palette behavior belong to the repository-level frontend architecture, especially
`../../FRONTEND_EDITOR_ELEVATIONS.md`.

Room Planner may provide projection geometry/snap context to that frontend layer,
but the Room Planner backend does not become the owner of the overlay.

If another planner owns a placed domain concept, that planner defines its own
canonical entity and may reuse the same frontend block definition for rendering.

## 6. Cross-view identity applies only to owned domain refs

For Room Planner-owned concepts, plan and elevation views address the same stable
refs.

Examples:

```text
select wall niche N7 in plan
    → open wall-face elevation
    → select N7

edit opening O4 height in elevation
    → same O4 reprojects in plan
```

No `plan_instance_id` / `elevation_instance_id` pair is introduced.

Frontend-only overlay instances may have editor-layer ids for interaction, but
those ids are outside the Room Planner domain identity system.

## 7. No Room Planner publication/provenance for generic frontend overlays

Generic frontend furniture/layout overlays do not create Room Planner snapshots,
Room Planner basis refs, takeoff provenance, or Platform Hub publication entries.

If shared overlay persistence/publication is ever needed, it requires a separate
ownership decision outside Room Planner rather than an implicit extension of the
Room Planner artifact schema.

## 8. Frontend consequence

The browser treats wall elevation as another projection capability over Room
Planner domain refs while independently allowing shared frontend overlay layers.

Conceptually:

```text
Room Planner canonical state
        ├── plan projection
        └── wall elevation projection

shared frontend overlay layer
        ├── plan block projection
        └── elevation block projection
```

The two can be visually composed without becoming one backend data model.

## 9. Platform Router impact

No new Platform Hub mechanism is introduced.

Generic frontend overlay placement is explicitly excluded from Room Planner
artifact/provenance responsibilities.

## State 1 effect

State 1 remains stabilized after this correction. The previous furniture/layout
aggregate proposal is withdrawn; no replacement Room Planner backend model is
needed.
