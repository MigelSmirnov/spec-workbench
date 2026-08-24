# Room Planner — State 1: Wall Elevation Projection and Furniture Layout Models

> Status: accepted State 1 refinement.
>
> This document repairs the stabilized State 1 model after State 0 added a
> wall-face elevation editor view and manual furniture layout. It intentionally
> adds durable furniture/layout data but does **not** add an `ElevationDrawing`
> entity: elevation is a projection of canonical domain state.

## 1. No separate elevation drawing model

Room Planner must not persist a second drawing that duplicates walls, openings,
niches, ceiling edges, or furniture only because the user is looking at a wall
frontally.

The elevation projection is derived from:

```text
selected wall face
+ canonical wall/opening/niche data
+ floor/ceiling surfaces
+ ceiling regions intersecting the face
+ furniture placements visible from that face
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
the owning field semantics (for example opening sill height), while absolute
surface/elevation calculations remain tied to the project datum.

## 3. Furniture definition reference

Furniture placement references a reusable, versioned semantic block definition.

### `FurnitureDefinitionRef`

```text
definition_id: str
definition_revision: str
```

The referenced definition may expose renderer assets such as plan/front/side SVG
views, palette metadata, anchors, and default dimensions through the shared block
library. Those assets are not copied into Room Planner placement state.

A placement pins an exact definition revision so historical accepted layouts do
not silently change meaning when a library definition is revised.

## 4. Physical envelope is project data

Room Planner stores explicit placement dimensions independent of SVG internals.

### `FurnitureEnvelope`

```text
width_mm: Decimal
height_mm: Decimal
depth_mm: Decimal
```

All values are strictly positive in accepted state.

The envelope is the spatial planning envelope used by plan/elevation projection.
It does not claim a manufacturing-accurate solid model.

A renderer asset may contain richer visual detail, but SVG bounds are not allowed
to redefine these physical dimensions.

## 5. Floor furniture placement

Represents furniture or a room-layout block primarily located from plan and
supported by the floor surface.

### `FloorFurniturePlacement`

```text
placement_kind: Literal['floor']
placement_id: str
room_id: str
definition_ref: FurnitureDefinitionRef
position: Point2D
rotation_deg: Decimal
envelope: FurnitureEnvelope
bottom_offset_mm: Decimal
```

### Meaning

- `position` is the canonical plan anchor for the placement;
- `rotation_deg` is a world-plan rotation, not a renderer transform copied from
  Konva;
- the bottom elevation is derived from the applicable floor surface at the
  placement anchor plus `bottom_offset_mm`;
- normal floor-standing furniture uses `bottom_offset_mm = 0`;
- a positive offset may represent an intentionally elevated/free-standing layout
  item without requiring a wall mount.

Exact anchor convention within the envelope (for example centre versus defined
origin) must be deterministic and belongs to the block-definition contract.

## 6. Wall-mounted furniture placement

Represents a block whose authoritative placement is relative to one wall face,
for example an upper kitchen cabinet or wall shelf.

### `WallFurniturePlacement`

```text
placement_kind: Literal['wall_face']
placement_id: str
room_id: str
definition_ref: FurnitureDefinitionRef
target: ExistingWallFaceRef | ConstructionWallFaceRef
offset_from_wall_start_mm: Decimal
bottom_height_mm: Decimal
envelope: FurnitureEnvelope
```

### Meaning

- `offset_from_wall_start_mm` locates the placement along the directed host wall;
- `bottom_height_mm` is the vertical height above the applicable local finished
  floor at the placement position;
- `depth_mm` extends from the targeted room-facing wall face into the room;
- the wall face, not a Canvas coordinate, determines mounting orientation.

A wall-mounted placement may be edited conveniently in elevation while remaining
visible/selectable in plan.

## 7. Closed furniture placement union

`FurniturePlacement` is a discriminated union on `placement_kind`:

```text
FloorFurniturePlacement
WallFurniturePlacement
```

Additional mount families require real product evidence. Do not add generic
`transform: dict` or arbitrary per-block placement payloads.

## 8. Furniture layout is an auxiliary aggregate, not a renovation stage

Furniture is spatial planning context and therefore remains separate from
Existing, Demolition, and Construction meanings.

### `FurnitureLayoutDraft`

```text
layout_id: str
object_ref: RegistryObjectRef
existing_basis: ExistingSnapshotRef
demolition_basis: DemolitionSnapshotRef | None
construction_basis: ConstructionSnapshotRef | None
based_on_snapshot: FurnitureLayoutSnapshotRef | None
placements: list[FurniturePlacement]
```

### `FurnitureLayoutSnapshotRef`

```text
snapshot_id: str
```

### `FurnitureLayoutSnapshot`

```text
snapshot_id: str
object_ref: RegistryObjectRef
existing_basis: ExistingSnapshotRef
demolition_basis: DemolitionSnapshotRef | None
construction_basis: ConstructionSnapshotRef | None
placements: list[FurniturePlacement]
```

The exact Proposed composition implied by the basis refs must be coherent under
the same Existing → Demolition → Construction basis rules already used elsewhere.

Furniture layout acceptance freezes spatial planning context but does not create
construction work or takeoff quantities.

## 9. Cross-view identity

Plan and elevation views address the same `placement_id` and the same wall/opening
/niche ids.

Examples:

```text
select wall niche N7 in plan
    → open wall-face elevation
    → select N7

move wall cabinet P12 in elevation
    → same P12 reprojects in plan
```

No `plan_instance_id` / `elevation_instance_id` pair is introduced.

## 10. Furniture block library versus project placement

The reusable definition owns presentation/capability metadata such as:

```text
plan renderer asset
front-elevation renderer asset
side-elevation renderer asset
semantic anchors
default envelope
palette category
```

Room Planner placement owns:

```text
placement identity
project position / host face
project envelope
project rotation / vertical placement
exact definition revision reference
```

The palette therefore does not need to know SVG path structure and Room Planner
does not persist SVG markup in project state.

## 11. No automatic fit semantics

The presence of `FurnitureEnvelope` allows the browser to render dimensions,
overlays, and user-driven spatial comparison. It does not authorize Room Planner
to declare ergonomic/code/installation fit automatically.

Any future collision warning may be a geometric editor aid only if its meaning is
explicitly defined. Domain decisions such as kitchen design compliance, furniture
manufacturability, or installation clearance remain outside current scope.

## 12. Publication and provenance

A `FurnitureLayoutSnapshot` may later be embedded/referenced as an auxiliary
structured layer of `room_plan` publication while retaining its exact plan basis.

It is not a source for `room_takeoff` in the initial product.

Block-definition distribution/versioning is a shared frontend/library concern;
if a future Platform Hub catalog is needed for cross-application block
resolution, that requirement must be added to `PLATFORM_ROUTER.md` first rather
than invented privately here.

## 13. Frontend consequence

The browser should treat wall elevation as another projection capability over
existing domain refs and furniture as a selectable/editable auxiliary layer.

Plan/elevation asset switching is renderer behavior. Stable project identities,
wall-relative coordinates, vertical dimensions, and physical envelopes remain
canonical domain data.

## 14. Platform Router impact

No new Platform Hub mechanism is introduced by this State 1 refinement.
