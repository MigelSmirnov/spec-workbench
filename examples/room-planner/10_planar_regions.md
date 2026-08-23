# Room Planner — State 1: Planar Build-Up Regions and Ceiling Boxes

> Status: accepted State 1 refinement.
>
> This document repairs the stabilized State 1 model after State 0 confirmed the
> common authoring pattern `2D footprint + explicit vertical parameter` for floor
> build-up and ceiling boxes/soffits. It is normative where it refines the older
> `FloorPreparationIntent` / ceiling-treatment-only assumptions.

## 1. Do not collapse these concepts into one generic region payload

Floor build-up and ceiling boxes share an authoring pattern but have different
domain meanings and lifecycles.

Do not introduce:

```text
ConstructionRegion
    kind: str
    footprint: polygon
    value_mm: Decimal
    payload: dict
```

Instead keep explicit models:

```text
floor build-up region
    footprint + thickness

ceiling box / soffit
    footprint + drop height
```

The browser may reuse the same polygon-editing mechanics for both without making
the domain model generic.

## 2. Floor build-up intent

The provisional `FloorPreparationIntent(target_surface=...)` is refined for the
initial screed/leveling/fill workflow.

### `FloorBuildUpIntent`

```text
construction_kind: Literal['floor_build_up']
item_id: str
room_id: str
footprint: PlanPolygon
thickness_mm: Decimal
system_ref: ConstructionSystemRef
```

### Meaning

- `footprint` is the authoritative 2D area to which the build-up applies;
- `thickness_mm` is explicit user-entered construction thickness;
- `system_ref` pins the exact Construction Catalog system;
- the source floor surface is resolved from the Construction plan's exact
  Existing/Demolition basis for that room/footprint;
- the target prepared floor surface is derived by offsetting the applicable
  source surface upward by `thickness_mm` over the footprint.

A region may cover a whole room or only part of a room. Several non-conflicting
regions may be used to express different explicit thicknesses.

The initial model does not infer a varying build-up thickness from a desired
absolute target surface. If that authoring mode is introduced later, it requires
an explicit model variant rather than overloading `FloorBuildUpIntent`.

### Construction treatment union refinement

`ConstructionTreatment` replaces the provisional `FloorPreparationIntent` member
with:

```text
FloorBuildUpIntent
```

Wall plaster/putty/paint and ceiling-treatment intents remain separate meanings.

## 3. Existing ceiling box / soffit

A measured Existing box/soffit is a spatial construction with its own footprint
and vertical extent.

### `ExistingCeilingBoxDraft`

```text
box_id: str
room_id: str
footprint: PlanPolygon
drop_height_mm: Decimal | None
label: str | None
```

`None` means the drop has not yet been measured/recorded in the working draft.

### `ExistingCeilingBox`

Accepted Existing shape:

```text
box_id: str
room_id: str
footprint: PlanPolygon
drop_height_mm: Decimal
label: str | None
```

### Meaning

`drop_height_mm` is the vertical drop from the applicable base Existing ceiling
surface to the box underside over the footprint.

The box's underside and vertical side faces are derived geometry. They are not
stored as unrelated manually editable polygons.

### Existing level refinement

Mutable Existing level state gains:

```text
ceiling_boxes: list[ExistingCeilingBoxDraft]
```

Accepted Existing level snapshot gains:

```text
ceiling_boxes: list[ExistingCeilingBox]
```

## 4. Demolition of Existing ceiling boxes

### `ExistingCeilingBoxRef`

```text
box_id: str
```

### `RemoveExistingCeilingBox`

```text
demolition_kind: Literal['remove_ceiling_box']
item_id: str
target: ExistingCeilingBoxRef
```

Removing the box is demolition of a physical construction. The resulting
post-demolition ceiling geometry is derived from the exact Existing basis and the
removal intent.

`DemolitionItem` gains `RemoveExistingCeilingBox` as an explicit variant.

## 5. New Construction ceiling boxes

Ceiling boxes are positive construction geometry, not merely a
`CeilingTreatmentIntent`.

### `ConstructionCeilingBoxDraft`

```text
box_id: str
room_id: str
footprint: PlanPolygon
drop_height_mm: Decimal
system_ref: ConstructionSystemRef | None
```

### `ConstructionCeilingBox`

Accepted shape:

```text
box_id: str
room_id: str
footprint: PlanPolygon
drop_height_mm: Decimal
system_ref: ConstructionSystemRef
```

### Meaning

- the footprint identifies the plan area of the box;
- the drop height is entered explicitly by the user;
- the selected system is required for an accepted Construction result;
- the underside and vertical side faces are derived deterministically from the
  applicable ceiling surface, footprint, and drop height.

The construction box is not authored as an arbitrary free-form 3D solid.

### Construction level refinement

Mutable Construction level state gains:

```text
ceiling_boxes: list[ConstructionCeilingBoxDraft]
```

Accepted Construction level snapshot gains:

```text
ceiling_boxes: list[ConstructionCeilingBox]
```

## 6. Ceiling treatment remains separate

`CeilingTreatmentIntent` continues to mean preparation/finish applied to a
ceiling surface. It does not create a box/soffit geometry merely because the
renderer displays both as polygons.

A box system may itself define construction-layer quantities through the
Construction Catalog. If later product work requires separately targeting box
underside/side faces with plaster/putty/paint treatments, those addressable
surface targets must be modeled explicitly; they must not be smuggled through
renderer selection ids.

## 7. Derived ceiling-box geometry

The canonical box input is:

```text
room/base ceiling surface
+ footprint
+ drop_height_mm
```

Derived geometry includes conceptually:

```text
box underside surface
vertical side faces along footprint boundary
derived lower clear-height envelope
```

Exact polygon offset/join details and overlap precedence belong to State 2.

The side faces are construction-relevant because they contribute physical area
even though the editor is plan-centric.

## 8. Proposed / To-Be composition

Proposed ceiling geometry includes:

- retained Existing ceiling boxes not removed by Demolition;
- accepted Construction ceiling boxes;
- derived base ceiling/floor surfaces after applicable stage composition.

An Existing box removed by Demolition is absent from Proposed. A Construction box
appears as positive Proposed geometry.

The exact renderer may show boxes as footprint fills/contours with height labels;
that visual form does not alter the domain meaning.

## 9. Provenance refs

Add the following standalone refs.

### `ExistingCeilingBoxSourceRef`

```text
source_kind: Literal['existing_ceiling_box']
snapshot: ExistingSnapshotRef
level_id: str
box_id: str
```

### `ConstructionCeilingBoxSourceRef`

```text
source_kind: Literal['construction_ceiling_box']
snapshot: ConstructionSnapshotRef
level_id: str
box_id: str
```

### `FloorBuildUpIntentSourceRef`

```text
source_kind: Literal['floor_build_up_intent']
snapshot: ConstructionSnapshotRef
level_id: str
item_id: str
```

`ExistingEntityRef` used by correction lineage gains a ceiling-box variant:

```text
ExistingCeilingBoxEntityRef
    entity_kind: Literal['ceiling_box']
    level_id: str
    box_id: str
```

`DependentIntentRef` / Construction takeoff provenance include the applicable
Construction ceiling-box and floor-build-up refs where those intents participate.

## 10. Browser/editor consequence

The browser does not treat screed or boxes as opaque symbol blocks.

Expected interaction projection:

```text
Floor build-up
    region polygon
    + thickness property
    + system property
    + derived target-surface/quantity preview

Ceiling box
    region polygon
    + drop-height property
    + system property
    + derived underside/side-face/clear-height preview
```

Selection handles, polygon vertices, hatch/pattern, thickness labels, heat maps,
and hover overlays are frontend state/projections.

The canonical persisted facts remain the typed footprint, explicit vertical
parameter, exact basis, and system reference.

## 11. Platform Router impact

No new Platform Hub mechanism is introduced.

Published Room Planner results may expose these structured construction regions
and their derived quantities through the existing `room_plan` / `room_takeoff`
artifact boundary. The Hub does not own region editing or geometry derivation.

## State 1 effect

State 1 remains stabilized with this accepted refinement included.

The previous assumption that a future structural/suspended ceiling construction
might require a later model is superseded for ceiling boxes/soffits: they are now
explicit initial-scope construction geometry.
