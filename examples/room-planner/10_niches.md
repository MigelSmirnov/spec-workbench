# Room Planner — State 1: Ceiling and Wall Niche Models

> Status: accepted State 1 refinement.
>
> This document repairs stabilized State 1 after State 0 added recessed ceiling
> and wall niches as initial-scope construction geometry. It follows the same
> product principle as ceiling boxes: author in 2D, store explicit depth, derive
> the 3D-relevant surfaces needed for planning and quantity calculation.

## 1. Keep ceiling and wall niches explicit

Ceiling and wall niches share the meaning "recess into a host surface" but use
different canonical coordinate systems.

Do not collapse them into:

```text
SurfaceNiche
    surface_kind: str
    geometry: dict
    depth_mm: Decimal
```

Use explicit niche families so invalid cross-surface shapes are not representable.

---

## 2. Ceiling niche models

A ceiling niche is authored in plan coordinates because its host surface is
horizontal/plan-addressable.

### `ExistingCeilingNicheDraft`

```text
niche_id: str
room_id: str
footprint: PlanPolygon
recess_depth_mm: Decimal | None
label: str | None
```

### `ExistingCeilingNiche`

```text
niche_id: str
room_id: str
footprint: PlanPolygon
recess_depth_mm: Decimal
label: str | None
```

`recess_depth_mm` is the vertical distance upward from the applicable base
Existing room-facing ceiling surface to the niche back surface.

### `ConstructionCeilingNicheDraft`

```text
niche_id: str
room_id: str
footprint: PlanPolygon
recess_depth_mm: Decimal
system_ref: ConstructionSystemRef | None
```

### `ConstructionCeilingNiche`

```text
niche_id: str
room_id: str
footprint: PlanPolygon
recess_depth_mm: Decimal
system_ref: ConstructionSystemRef
```

The accepted Construction niche therefore pins the exact technical construction
system. The niche back and transition faces are derived; they are not independent
editable polygons.

### Level aggregate refinements

Mutable Existing level state gains:

```text
ceiling_niches: list[ExistingCeilingNicheDraft]
```

Accepted Existing level state gains:

```text
ceiling_niches: list[ExistingCeilingNiche]
```

Mutable Construction level state gains:

```text
ceiling_niches: list[ConstructionCeilingNicheDraft]
```

Accepted Construction level state gains:

```text
ceiling_niches: list[ConstructionCeilingNiche]
```

---

## 3. Wall-face niche models

A wall niche is local to one wall face rather than to the wall as a through
opening.

Its canonical rectangular face extent mirrors the useful wall-relative opening
coordinates but adds an explicit recess depth and face identity.

### `ExistingWallNicheDraft`

```text
niche_id: str
wall_face: ExistingWallFaceRef
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
recess_depth_mm: Decimal | None
label: str | None
```

### `ExistingWallNiche`

```text
niche_id: str
wall_face: ExistingWallFaceRef
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
recess_depth_mm: Decimal
label: str | None
```

`wall_face.side` makes the niche face-specific. The same wall may therefore have
a niche on one face without implying a matching recess on the opposite face.

### `ConstructionWallNicheDraft`

```text
niche_id: str
target: ConstructionWallFaceRef
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
recess_depth_mm: Decimal
system_ref: ConstructionSystemRef | None
```

### `ConstructionWallNiche`

```text
niche_id: str
target: ConstructionWallFaceRef
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
recess_depth_mm: Decimal
system_ref: ConstructionSystemRef
```

`ConstructionWallFaceRef` already distinguishes retained Existing versus new
Construction wall targets. This lets one niche model describe positive final
construction geometry without losing the host-wall stage meaning.

### Level aggregate refinements

Mutable Existing level state gains:

```text
wall_niches: list[ExistingWallNicheDraft]
```

Accepted Existing level state gains:

```text
wall_niches: list[ExistingWallNiche]
```

Mutable Construction level state gains:

```text
wall_niches: list[ConstructionWallNicheDraft]
```

Accepted Construction level state gains:

```text
wall_niches: list[ConstructionWallNiche]
```

---

## 4. Niche geometry is derived from host + extent + depth

### Ceiling niche

Canonical inputs:

```text
base ceiling surface
+ plan footprint
+ recess_depth_mm
```

Derived geometry:

```text
niche back surface
transition/side faces around exposed footprint boundary
local clear-height increase
```

### Wall niche

Canonical inputs:

```text
host wall face
+ wall-relative rectangle
+ recess_depth_mm
```

Derived geometry:

```text
niche back face
left/right jamb faces
top face
bottom/sill face
host-face opening/recess area removed from the unrecessed finishable face
```

These derived faces are calculation/projection geometry, not independent source
entities in State 1.

---

## 5. Niche versus opening aperture

A wall niche is not an `ExistingOpening` / Construction opening result.

```text
opening aperture
    passes through / connects across wall thickness according to opening model

wall niche
    recesses one wall face to finite depth
    does not create passage through the wall
```

The model must not convert a niche to an opening merely because
`recess_depth_mm` approaches wall thickness. State 2 defines the validity bound;
if the intended geometry is a through opening, the user/domain must use the
opening lifecycle explicitly.

---

## 6. Existing correction and identity

Niches that survive an Existing correction as the same physical recess preserve
identity even if their measured dimensions/depth are corrected.

`ExistingEntityRef` gains:

```text
ExistingCeilingNicheEntityRef
    entity_kind: Literal['ceiling_niche']
    level_id: str
    niche_id: str

ExistingWallNicheEntityRef
    entity_kind: Literal['wall_niche']
    level_id: str
    niche_id: str
```

Split/merge/remove/add correction semantics follow the already accepted lineage
family rather than geometry matching.

---

## 7. Provenance refs

Add standalone refs:

```text
ExistingCeilingNicheSourceRef
    source_kind: Literal['existing_ceiling_niche']
    snapshot: ExistingSnapshotRef
    level_id: str
    niche_id: str

ExistingWallNicheSourceRef
    source_kind: Literal['existing_wall_niche']
    snapshot: ExistingSnapshotRef
    level_id: str
    niche_id: str

ConstructionCeilingNicheSourceRef
    source_kind: Literal['construction_ceiling_niche']
    snapshot: ConstructionSnapshotRef
    level_id: str
    niche_id: str

ConstructionWallNicheSourceRef
    source_kind: Literal['construction_wall_niche']
    snapshot: ConstructionSnapshotRef
    level_id: str
    niche_id: str
```

Construction takeoff provenance includes the applicable Construction niche refs.
Proposed geometry may retain Existing or Construction niche provenance through
narrow niche-specific source unions.

---

## 8. Demolition boundary

Creating a final niche in a retained Existing substrate may require physical
material removal. The positive Construction niche model does not itself claim
that demolition happened.

For initial State 1, demolition may continue to represent known removable
surface/build-up layers explicitly. A substrate-cut model is introduced only
where the product/calculation workflow requires demolition volume or cut geometry
as a first-class separate output; it must then be an explicit niche-cut variant,
not inferred silently from the Construction niche.

Closing/filling an Existing niche is likewise Construction work and must not be
modeled by deleting the Existing niche fact.

---

## 9. Browser/editor consequence

Ceiling and wall niches reuse region/shape editing mechanics but not symbol-block
semantics.

```text
Ceiling niche tool
    draw/edit plan footprint
    set recess depth + system

Wall niche tool
    choose wall face
    draw/edit face-local rectangle
    set recess depth + system
```

The browser may render hatch, outline, shadow, depth labels, face handles, or a
pseudo-3D preview. Those projections do not become canonical niche data.

---

## 10. Platform Router impact

No new Platform Hub mechanism is introduced. Niche geometry/provenance remains
Room Planner-owned and later maps through the existing room-plan/takeoff artifact
boundary.

## State 1 effect

State 1 remains stabilized with this accepted refinement included.
