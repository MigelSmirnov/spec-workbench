# Room Planner — State 0: Wall Elevations and Furniture Layout

> Status: accepted State 0 refinement.
>
> This document adds a wall-elevation authoring view and manual furniture layout
> to the stabilized Room Planner product boundary. It preserves the browser-first,
> 2D-authoring direction: plan and elevation are coordinated projections of one
> spatial domain model, not independent drawings.

## 1. Wall elevation is a required editor view

Room Planner needs a wall-elevation / unfolded-wall workflow in addition to the
plan view.

The elevation view is used to inspect and edit vertical relationships that are
awkward or ambiguous in plan, including:

- opening sill and head heights;
- door/window element placement and door swing projection;
- wall niches and their vertical extent;
- wall-face treatment regions where later product scope requires them;
- ceiling/base-ceiling lines and lowered ceiling/box consequences;
- local floor line and clear-height consequences;
- vertical placement and dimensions of furniture/layout blocks.

The elevation is not a separately authored copy of the room. It is a projection
of the same authoritative wall/opening/surface/furniture data used by plan view.

```text
canonical Room Planner working state
        ├── plan projection
        └── wall-face elevation projection
```

Editing from either view changes the same working-domain facts through explicit
application/editor commands.

## 2. Elevations are wall-face centric

A wall has two semantically different faces. An elevation therefore addresses a
specific wall face rather than only a wall id.

Conceptually:

```text
wall identity
+ wall side / face
        ↓
wall-face elevation view
```

The view must preserve deterministic correspondence to wall-relative geometry.
The browser may orient/flip the viewport for usability, but that display transform
must not change canonical wall direction, `WallSide`, opening offsets, door swing,
or persisted dimensions.

## 3. Height entry belongs naturally in elevation

The elevation view is a primary interaction surface for entering vertical
parameters.

Examples include:

```text
opening sill height
opening height
wall-niche sill / height / recess depth
furniture bottom elevation / height
ceiling-box drop shown at the wall intersection
```

The property panel and direct dimension handles may both expose these values, but
accepted domain values remain real-world millimetres. Dragging a visual handle is
only an input gesture that proposes a new domain value.

## 4. Manual furniture layout is in scope as a spatial planning aid

Room Planner may support manual placement of furniture and similar room-layout
blocks so the renovation professional can reason about the planned space in both
plan and elevation views.

This refines the earlier out-of-scope statement only narrowly:

- **manual placement and visual spatial planning are in scope**;
- automatic domain decisions that furniture/kitchens/equipment "fit" or satisfy
  ergonomic/code rules remain out of scope unless introduced explicitly later;
- furniture pricing, procurement, manufacturing/BOM, labor, and commercial
  estimating are not Room Planner responsibilities.

Furniture layout is therefore useful spatial context, not a new estimating
subsystem.

## 5. Furniture uses the reusable block library, not custom React components

Furniture items should use the shared versioned block-definition / SVG-library
architecture.

A block definition may provide several validated renderer assets for the same
semantic item, for example:

```text
plan
front_elevation
side_elevation
```

The palette consumes manifest metadata and capabilities. It does not parse or
understand the internal SVG paths.

The block definition does not own the item's project placement or project
identity. A Room Planner furniture placement references a definition and stores
its own real-world position/dimensions/mounting data.

## 6. Multi-view assets represent one block definition

Plan and elevation SVGs for the same furniture item are renderer projections of
one reusable definition, not different project objects.

```text
FurnitureDefinition F42
    ├── plan asset
    ├── front-elevation asset
    └── optional side-elevation asset

FurniturePlacement P7
    → definition F42
    → one canonical project placement
```

Changing editor view selects another projection of `P7`; it must not create a
second placement.

If a definition lacks an elevation asset, the editor may use a validated neutral
fallback derived from its physical envelope, but must not fabricate detailed
construction semantics.

## 7. Furniture does not silently become Construction work

Furniture placement is a distinct layout meaning. Placing a sofa/cabinet/block
must not create drywall, finish, Demolition, or Construction takeoff merely
because it is visible in the Room Planner scene.

A furniture item may be used as spatial context while designing walls, doors,
niches, ceiling regions, or services, but those domains retain their own explicit
intent and quantity models.

Future built-in/custom joinery that Room Planner is expected to quantify would
require an explicit product/model decision rather than being inferred from the
furniture library.

## 8. Publication boundary

Furniture layout may be retained in Room Planner working/accepted plan state and
may be included as an auxiliary structured layer of `room_plan` when publication
contracts are defined.

It does not participate in `room_takeoff` unless a later explicit product scope
assigns physical quantity responsibility to Room Planner.

## 9. Frontend/editor consequence

The browser workspace now needs coordinated view modes at minimum:

```text
Plan
Wall Elevation
```

Selection should be able to move between them through stable domain references.
For example, selecting a wall face or niche in plan can open/select the same
entity in elevation; selecting a door/furniture placement in elevation can reveal
it in plan.

No Canvas/Konva/SVG scene object becomes the cross-view identity.

## 10. Platform Router impact

This product refinement introduces no new Platform Hub mechanism.

If furniture layout is later exposed cross-application through `room_plan`, its
language-neutral artifact schema belongs to the normal Room Planner publication
contract. The Platform Hub does not own furniture editing, wall elevations, or
block rendering.
