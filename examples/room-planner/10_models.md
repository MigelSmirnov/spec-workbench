# Room Planner — State 1: Domain Models

> Status: working draft.
>
> This state defines the durable domain language required by the stabilized
> State 0 product boundary. It intentionally does not define Python service
> contracts, HTTP endpoints, persistence tables, calculation algorithms,
> interpolation policy, publication wire schemas, or frontend component models.

## Modeling goal

Room Planner needs a model that preserves three independent meanings at the
same time:

1. the measured Existing condition;
2. Demolition intent against an exact Existing basis;
3. Construction intent against an exact Existing basis and, where relevant,
   an exact Demolition basis.

The model must also support multi-level renovation objects, millimeter-oriented
2D geometry, spatially varying floor/ceiling geometry, explicit demolition
assumptions, one active Construction proposal, reproducible physical takeoff,
and immutable historical publication without turning draft/editor state into a
platform artifact.

## Modeling principles

1. Registry `object_id` is the renovation-object identity. Room Planner does not
   invent a parallel platform object identity.
2. Existing, Demolition, and Construction are separate domain aggregates, not
   one generic `Plan(stage: str, data: dict)`.
3. A draft is mutable working state. A historical snapshot is immutable. Exact
   persistence and platform publication mechanics are later concerns.
4. `PROPOSED / TO-BE` is derived from the three source meanings and is not a
   fourth editable source of truth.
5. Browser canvas/SVG objects are presentation models, not durable domain
   models.
6. Plan geometry uses real-world coordinates; screen pixels never become domain
   coordinates.
7. Connected wall geometry is represented explicitly enough that rooms and wall
   faces can be derived deterministically without decorative overlays.
8. Doors and windows are wall openings anchored to wall geometry.
9. Existing vertical survey records the two independent measured facts required
   by State 0: floor elevation and local floor-to-ceiling clear height.
10. A single scalar `floor_level` or `room_height` is not sufficient for the
    Room Planner domain.
11. Demolition-result and Construction-target surfaces are distinct meanings
    even if both are represented by compatible elevation-field value models.
12. Construction Catalog references pin exact technical data versions; catalog
    values are not copied into arbitrary Room Planner metadata.
13. Physical takeoff contains engineering quantities only. Price, labor,
    package conversion, and commercial rounding do not enter these models.
14. Generic `dict`, `Any`, `metadata`, `payload`, and unqualified `status: str`
    fields are rejected.
15. Partial working state is allowed only where its incomplete meaning is
    explicit. Published/reproducible results must not rely on silently missing
    required data.

---

# 1. Shared identity and geometry value models

## `RegistryObjectRef`

### Purpose

Carries the canonical renovation-object identity supplied by Registry without
copying Registry's object-card schema into Room Planner.

### Kind

Value object.

### Fields

```text
object_id: str
```

### Invariants

- `object_id` is required and originates from Registry / Platform Hub object
  discovery.
- Room Planner never generates a substitute `object_id`.

---

## `SpatialLevel`

### Purpose

Identifies one editable floor/level inside the single Room Planner container for
a Registry object.

### Kind

Entity.

### Fields

```text
level_id: str
name: str
```

### Lifecycle

Created inside the Room Planner object-level container and reused by all three
planning meanings. The exact Registry projection for platform-level floor facts
remains deferred because the shared platform contract has not yet defined it.

### Invariants

- `level_id` is unique inside one Room Planner object.
- A level is not represented by creating another Registry object.
- `name` is user-facing identification, not platform identity.

---

## `Point2D`

### Purpose

Represents an authoritative plan coordinate in real-world millimeters.

### Kind

Value object.

### Fields

```text
x_mm: Decimal
y_mm: Decimal
```

### Invariants

- Values are finite real-world coordinates.
- Browser pixels and viewport transforms are never persisted here.

### Modeling note

`Decimal` is retained as the candidate scalar so the model does not lose
fractional-millimeter technical dimensions merely because the editor is
millimeter-oriented. State 2 may tighten allowed precision/quantization.

---

## `PlanVertex`

### Purpose

Provides stable identity for a wall-junction coordinate inside one source plan.
It prevents connected wall geometry from becoming a collection of unrelated
line copies.

### Kind

Entity.

### Fields

```text
vertex_id: str
point: Point2D
```

### Invariants

- `vertex_id` is unique inside its owning level plan.
- Moving a vertex changes connected geometry in the same source plan only; it
  must not silently mutate another renovation stage.

---

## `PlanPolygon`

### Purpose

Represents a bounded 2D footprint when a floor/ceiling operation applies to a
selected area rather than a whole room.

### Kind

Value object.

### Fields

```text
vertices: list[Point2D]
```

### Invariants

- A valid polygon has at least three distinct vertices.
- Closure/intersection/orientation policy belongs to State 2.

---

## `ProjectDatum`

### Purpose

Identifies the stable project zero/reference used by measured and target
vertical elevations.

### Kind

Entity.

### Fields

```text
datum_id: str
label: str
```

### Invariants

- Elevation values that claim comparability within one Room Planner object use
  the same datum identity unless an explicit later conversion model is added.
- The datum is a measurement reference, not a claim that the building is level.

### Deferred detail

Datum creation/editing workflow and any Registry projection remain open.

---

# 2. Stage and basis reference models

## Candidate `PlanStage` values

```text
existing
demolition
construction
```

`proposed` is deliberately absent because it is derived, not an editable source
stage.

---

## `ExistingRevisionRef`

### Purpose

Pins dependent work to one exact immutable Existing domain snapshot.

### Kind

Value object.

### Fields

```text
revision_id: str
```

---

## `DemolitionRevisionRef`

### Purpose

Pins Construction or takeoff work to one exact immutable Demolition domain
snapshot.

### Kind

Value object.

### Fields

```text
revision_id: str
```

---

## `ConstructionRevisionRef`

### Purpose

Identifies one exact immutable Construction domain snapshot.

### Kind

Value object.

### Fields

```text
revision_id: str
```

### Placeholder resistance

The three typed references are intentionally separate. A generic
`RevisionRef(stage: str, id: str)` would permit invalid basis relationships such
as Demolition depending on Construction.

---

# 3. Existing spatial models

## `ExistingWall`

### Purpose

Represents one measured wall segment in the Existing source of truth.

### Kind

Entity.

### Fields

```text
wall_id: str
start_vertex_id: str
end_vertex_id: str
thickness_mm: Decimal
```

### Invariants

- Both vertices exist in the same Existing level plan.
- Start and end vertices are different.
- `thickness_mm > 0`.
- Construction intent is never stored on this model.

### Vertical meaning

A single scalar wall height is intentionally not stored here. Existing wall-face
vertical extent is derived from the applicable measured floor/ceiling geometry
along the wall. This avoids contradicting State 0's spatially varying vertical
surface requirement.

---

## Candidate `OpeningKind` values

```text
door
window
unframed_opening
```

The taxonomy must remain closed; new kinds are added only when a real modeling
need appears.

---

## `ExistingOpening`

### Purpose

Represents a measured opening anchored to an Existing wall.

### Kind

Entity.

### Fields

```text
opening_id: str
wall_id: str
kind: OpeningKind
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
```

### Invariants

- `wall_id` references an Existing wall in the same level plan.
- Width and height are positive.
- The opening is geometrically contained by the owning wall according to later
  State 2 rules.
- `sill_height_mm` is measured relative to the applicable local floor surface,
  not screen coordinates.

---

## Candidate `WallSide` values

```text
left
right
```

The side is defined relative to the directed wall from `start_vertex_id` to
`end_vertex_id`.

---

## `ExistingWallFaceRef`

### Purpose

Identifies one separately finishable face of an Existing wall.

### Kind

Value object.

### Fields

```text
wall_id: str
side: WallSide
```

---

## `ExistingRoom`

### Purpose

Represents a room/space derived from Existing spatial boundaries while retaining
identity for naming, surface targeting, and revision comparison.

### Kind

Entity with derived geometry.

### Fields

```text
room_id: str
name: str
boundary_faces: list[ExistingWallFaceRef]
```

### Invariants

- Boundary faces belong to walls in the same Existing level plan.
- Room boundary ordering/closure and stable identity carry-forward are State 2
  rules, not arbitrary editor behavior.
- Area/perimeter are derived values and are not independent editable fields.

### Open modeling point

The exact representation for non-wall/open boundaries is not yet proven by the
product scope. Do not add a generic boundary payload until a real case requires
it.

---

## Candidate `ExistingSurfaceLayerRole` values

```text
wall_finish
floor_layer
ceiling_system
ceiling_finish
```

This is intentionally a coarse observed-condition role, not a catalog of every
material family.

---

## `ExistingSurfaceLayer`

### Purpose

Gives Demolition a real Existing target for removable finishes/build-up without
requiring Room Planner to pretend every observed legacy material is known in the
Construction Catalog.

### Kind

Entity.

### Fields

```text
layer_id: str
role: ExistingSurfaceLayerRole
target: ExistingSurfaceTarget
observed_thickness_mm: Decimal | None
label: str | None
```

### Invariants

- `target` is a typed Existing surface target.
- `observed_thickness_mm` is present only when the thickness/depth is actually
  observed or otherwise accepted as Existing fact.
- An unknown thickness remains `None`; Room Planner must not fabricate it.
- `label` is descriptive only and cannot substitute for calculation semantics.

---

## `ExistingWallFaceTarget`

```text
target_kind: Literal['wall_face']
wall_face: ExistingWallFaceRef
```

## `ExistingRoomFloorTarget`

```text
target_kind: Literal['room_floor']
room_id: str
```

## `ExistingRoomCeilingTarget`

```text
target_kind: Literal['room_ceiling']
room_id: str
```

## `ExistingSurfaceTarget`

Candidate discriminated union on `target_kind`:

```text
ExistingWallFaceTarget
ExistingRoomFloorTarget
ExistingRoomCeilingTarget
```

---

# 4. Existing vertical survey models

## `ExistingVerticalSampleDraft`

### Purpose

Allows survey entry to be saved before both required vertical facts are known.

### Kind

Value object used only in mutable working state.

### Fields

```text
sample_id: str
point: Point2D
floor_elevation_mm: Decimal | None
clear_height_mm: Decimal | None
```

### Partial-construction semantics

At least one of the two measured values must be present for the sample to exist.
`None` means not yet recorded, not zero and not inferred.

---

## `ExistingVerticalSample`

### Purpose

Represents an accepted complete vertical measurement used by reproducible
Existing geometry.

### Kind

Immutable value object.

### Fields

```text
sample_id: str
point: Point2D
floor_elevation_mm: Decimal
clear_height_mm: Decimal
```

### Derived fact

```text
ceiling_elevation_mm = floor_elevation_mm + clear_height_mm
```

The equality is a domain invariant; interpolation between samples remains a
later rule/algorithm decision.

---

## `ExistingVerticalGridDraft`

### Purpose

Groups editable vertical survey samples for one spatial level.

### Kind

Mutable working value.

### Fields

```text
datum_id: str
samples: list[ExistingVerticalSampleDraft]
```

---

## `ExistingVerticalGrid`

### Purpose

Represents the complete accepted vertical survey inputs included in an immutable
Existing snapshot.

### Kind

Immutable value object.

### Fields

```text
datum_id: str
samples: list[ExistingVerticalSample]
```

### Invariants

- Sample points are unique under the State 2 coordinate-equality rule.
- Grid density, interpolation, incomplete-area behavior, and surface
  reconstruction are intentionally not encoded as fields here.

---

# 5. Existing aggregate models

## `ExistingLevelDraft`

### Fields

```text
level_id: str
vertices: list[PlanVertex]
walls: list[ExistingWall]
openings: list[ExistingOpening]
rooms: list[ExistingRoom]
surface_layers: list[ExistingSurfaceLayer]
vertical_grid: ExistingVerticalGridDraft
```

### Meaning

Mutable measured/observed state for one level. `rooms` are derived domain
entities whose boundary facts must agree with the wall/opening topology.

---

## `ExistingPlanDraft`

### Purpose

Represents the current editable Existing state for the Registry object.

### Kind

Entity.

### Fields

```text
draft_id: str
object_ref: RegistryObjectRef
datum: ProjectDatum
based_on_revision: ExistingRevisionRef | None
levels: list[ExistingLevelDraft]
```

### Lifecycle

- May begin empty for a new Room Planner object.
- May inherit a prior immutable Existing revision.
- May contain incomplete survey data while saved as draft.
- A correction to a published Existing result creates/updates draft state; it
  does not mutate the old revision.

---

## `ExistingLevelSnapshot`

### Fields

```text
level_id: str
vertices: list[PlanVertex]
walls: list[ExistingWall]
openings: list[ExistingOpening]
rooms: list[ExistingRoom]
surface_layers: list[ExistingSurfaceLayer]
vertical_grid: ExistingVerticalGrid
```

---

## `ExistingPlanSnapshot`

### Purpose

Represents an immutable, reproducible Existing domain result from which
historical publication and dependent renovation stages can take their basis.

### Kind

Immutable entity.

### Fields

```text
revision_id: str
object_ref: RegistryObjectRef
datum: ProjectDatum
levels: list[ExistingLevelSnapshot]
```

### Invariants

- A snapshot is never edited in place.
- Later corrections create later snapshots.
- Platform artifact identity/publication metadata are not embedded here; they
  belong to the Platform Hub boundary and later contract state.

---

# 6. Demolition intent models

## `ExistingWallRef`

```text
wall_id: str
```

## `ExistingOpeningRef`

```text
opening_id: str
```

## `ExistingSurfaceLayerRef`

```text
layer_id: str
```

These refs are interpreted only against the exact `ExistingRevisionRef` carried
by the owning Demolition plan.

---

## `RemoveExistingWall`

```text
demolition_kind: Literal['remove_wall']
item_id: str
target: ExistingWallRef
```

## `RemoveExistingOpening`

```text
demolition_kind: Literal['remove_opening']
item_id: str
target: ExistingOpeningRef
```

## `RemoveExistingSurfaceLayer`

### Purpose

Represents removal of an observed finish/build-up and carries an explicit user
assumption when actual removable thickness is not known.

```text
demolition_kind: Literal['remove_surface_layer']
item_id: str
target: ExistingSurfaceLayerRef
assumed_removal_thickness_mm: Decimal | None
```

### Invariants

- When the referenced Existing layer has a reliable observed thickness, later
  quantity rules use that fact and do not silently replace it with an
  assumption.
- When physical quantity requires thickness/depth and Existing does not know it,
  `assumed_removal_thickness_mm` must be supplied before that quantity can be
  treated as complete.
- The assumption is user-supplied planning input, not fabricated measurement.

---

## `WallOpeningDemolitionCut`

### Purpose

Represents demolition geometry that creates or enlarges an opening in an
Existing wall instead of deleting the whole wall.

```text
demolition_kind: Literal['wall_opening_cut']
item_id: str
wall: ExistingWallRef
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
```

### Modeling note

This is demolition scope only. The final/new opening that exists after
Construction is represented separately in Construction intent.

---

## `DemolitionItem`

Candidate discriminated union on `demolition_kind`:

```text
RemoveExistingWall
RemoveExistingOpening
RemoveExistingSurfaceLayer
WallOpeningDemolitionCut
```

The union is intentionally closed. Additional demolition meanings such as a
future specialized ceiling operation must be introduced as explicit variants,
not hidden in `payload`.

---

## `DemolitionLevelDraft`

```text
level_id: str
items: list[DemolitionItem]
```

## `DemolitionPlanDraft`

### Purpose

Represents mutable Demolition intent against one exact Existing basis.

### Kind

Entity.

### Fields

```text
draft_id: str
object_ref: RegistryObjectRef
existing_basis: ExistingRevisionRef
based_on_revision: DemolitionRevisionRef | None
levels: list[DemolitionLevelDraft]
```

### Invariants

- Every Existing target resolves inside `existing_basis`.
- A corrected Existing basis does not silently retarget this draft. Carry-forward
  is an explicit later operation with conflict review.

---

## `DemolitionSurfaceResult`

### Purpose

Represents derived post-demolition floor/ceiling geometry where removals change
surface elevations. It is a derived result, not a second Existing source.

### Kind

Derived immutable value.

### Fields

```text
level_id: str
floor_surface: ElevationSurfaceSet | None
ceiling_surface: ElevationSurfaceSet | None
```

The exact reconstruction algorithm and when these fields are required belong to
later states.

---

## `DemolitionPlanSnapshot`

### Purpose

Immutable Demolition result preserving its exact Existing basis.

### Kind

Immutable entity.

### Fields

```text
revision_id: str
object_ref: RegistryObjectRef
existing_basis: ExistingRevisionRef
levels: list[DemolitionLevelDraft]
surface_results: list[DemolitionSurfaceResult]
```

### Modeling note

The snapshot reuses the same closed demolition item shapes as the draft but is
immutable. A later implementation may introduce distinct frozen model classes
if Pydantic immutability requirements make that clearer; it must not change the
domain fields or meaning silently.

---

# 7. Reusable elevation-surface models

## `ElevationSample`

```text
point: Point2D
elevation_mm: Decimal
```

## `ElevationGridSurface`

```text
surface_shape: Literal['grid']
samples: list[ElevationSample]
```

## `ConstantElevationSurface`

```text
surface_shape: Literal['constant']
elevation_mm: Decimal
```

## `ElevationSurface`

Candidate discriminated union on `surface_shape`:

```text
ElevationGridSurface
ConstantElevationSurface
```

## Candidate `HorizontalSurfaceKind` values

```text
floor
ceiling
```

## `ElevationSurfacePatch`

### Purpose

Represents one horizontal floor/ceiling surface definition over a selected
plan footprint. This supports State 0's requirement to adjust a selected area
rather than only a whole room.

```text
patch_id: str
surface_kind: HorizontalSurfaceKind
footprint: PlanPolygon
surface: ElevationSurface
```

## `ElevationSurfaceSet`

```text
patches: list[ElevationSurfacePatch]
```

### Deferred rules

Overlap, continuity, gap handling, interpolation, precedence, and derived mesh
construction belong to State 2 / later implementation design. The model only
preserves the explicit source data needed to make those decisions.

---

# 8. Construction geometry and intent models

## `ConstructionWall`

### Purpose

Represents a new wall that Construction intends to create.

### Kind

Entity.

### Fields

```text
wall_id: str
start_vertex_id: str
end_vertex_id: str
thickness_mm: Decimal
system_ref: ConstructionSystemRef | None
```

### Partial-construction semantics

`system_ref is None` is allowed in a working draft only when geometry is being
laid out before a construction system is selected. It means "unresolved
construction system", not "use a default". Later completeness rules must block
system-dependent takeoff when this value is unresolved.

---

## `ConstructionOpening`

### Purpose

Represents the opening that Construction intends to exist in a new or retained
wall.

### Kind

Entity.

### Fields

```text
opening_id: str
wall: ConstructionWallTarget
kind: OpeningKind
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
```

---

## `ExistingWallTarget`

```text
wall_source: Literal['existing']
wall_id: str
```

## `NewConstructionWallTarget`

```text
wall_source: Literal['construction']
wall_id: str
```

## `ConstructionWallTarget`

Candidate discriminated union on `wall_source`:

```text
ExistingWallTarget
NewConstructionWallTarget
```

An Existing target is always resolved against the Construction plan's explicit
`existing_basis`.

---

## `ConstructionWallFaceRef`

```text
wall: ConstructionWallTarget
side: WallSide
```

---

## `ConstructionCatalogRef`

### Purpose

Pins Room Planner calculation inputs to an exact shared Construction Catalog
revision/version.

### Kind

Value object.

### Fields

```text
catalog_revision_id: str
```

### Platform note

This is a domain reference only. Exact Platform Hub DTO/schema identity is a
later boundary-contract decision.

---

## `ConstructionSystemRef`

### Purpose

Identifies a selected technical construction/finish system inside an exact
Construction Catalog revision.

### Kind

Value object.

### Fields

```text
system_id: str
catalog_revision_id: str
```

### Invariants

- The referenced system is resolved from the exact catalog revision.
- Room Planner must not silently rebind the ref to a newer catalog revision.

---

## `WallPlasterIntent`

```text
construction_kind: Literal['wall_plaster']
item_id: str
target: ConstructionWallFaceRef
thickness_mm: Decimal
system_ref: ConstructionSystemRef
```

## `WallPuttyIntent`

```text
construction_kind: Literal['wall_putty']
item_id: str
target: ConstructionWallFaceRef
system_ref: ConstructionSystemRef
```

## `WallPaintIntent`

```text
construction_kind: Literal['wall_paint']
item_id: str
target: ConstructionWallFaceRef
system_ref: ConstructionSystemRef
```

## `FloorPreparationIntent`

```text
construction_kind: Literal['floor_preparation']
item_id: str
target_surface: ElevationSurfaceSet
system_ref: ConstructionSystemRef
```

## `CeilingTreatmentIntent`

```text
construction_kind: Literal['ceiling_treatment']
item_id: str
target_surface: ElevationSurfaceSet
system_ref: ConstructionSystemRef
```

## `ConstructionTreatment`

Candidate discriminated union on `construction_kind`:

```text
WallPlasterIntent
WallPuttyIntent
WallPaintIntent
FloorPreparationIntent
CeilingTreatmentIntent
```

### Modeling note

This taxonomy is intentionally limited to product responsibilities already
named in State 0. It does not yet claim the final ceiling-system catalog or all
future construction-system families.

---

## `ConstructionLevelDraft`

```text
level_id: str
vertices: list[PlanVertex]
walls: list[ConstructionWall]
openings: list[ConstructionOpening]
target_surfaces: ElevationSurfaceSet
treatments: list[ConstructionTreatment]
```

### Semantic boundary

Only work to be created/changed/prepared/finished lives here. Retained Existing
geometry is referenced through the plan basis and derived Proposed composition;
it is not copied into Construction as if newly built.

---

## `ConstructionPlanDraft`

### Purpose

Represents the single active Construction proposal required by the initial
product.

### Kind

Entity.

### Fields

```text
draft_id: str
object_ref: RegistryObjectRef
existing_basis: ExistingRevisionRef
demolition_basis: DemolitionRevisionRef | None
catalog_ref: ConstructionCatalogRef | None
based_on_revision: ConstructionRevisionRef | None
levels: list[ConstructionLevelDraft]
```

### Partial-construction semantics

- `demolition_basis` is `None` when the proposal does not depend on a Demolition
  result.
- `catalog_ref` may be unresolved while editing geometry, but any calculation
  that requires catalog technical data must remain incomplete until an exact
  revision is resolved.
- There is no `variant_id` or A/B/C branch list in the initial product.

---

## `ConstructionPlanSnapshot`

### Purpose

Immutable Construction result preserving exact planning and catalog basis.

### Kind

Immutable entity.

### Fields

```text
revision_id: str
object_ref: RegistryObjectRef
existing_basis: ExistingRevisionRef
demolition_basis: DemolitionRevisionRef | None
catalog_ref: ConstructionCatalogRef | None
levels: list[ConstructionLevelDraft]
```

A snapshot never changes when a newer Existing, Demolition, Construction, or
Construction Catalog revision appears.

---

# 9. Proposed / To-Be derived models

## `ProposedLevel`

### Purpose

Represents the spatial result of composing one exact Existing basis with the
applicable Demolition and Construction intent for review/calculation.

### Kind

Derived value.

### Candidate fields

```text
level_id: str
walls: list[ProposedWall]
openings: list[ProposedOpening]
rooms: list[ProposedRoom]
floor_surface: ElevationSurfaceSet | None
ceiling_surface: ElevationSurfaceSet | None
```

### Invariants

- It is derived; users do not directly persist arbitrary edits into
  `ProposedLevel`.
- Every proposed element retains provenance to its Existing and/or Construction
  source so later takeoff does not lose origin.

### Open modeling point

The exact `ProposedWall` / `ProposedOpening` source-provenance union should be
finalized after the carry-forward/conflict model below is resolved. Do not use
untyped source ids as a shortcut.

---

# 10. Physical quantity / takeoff models

## Candidate `MeasureDimension` values

```text
length
area
volume
mass
count
```

## Candidate `MeasureUnit` values

```text
m
m2
m3
kg
piece
```

Additional units require a real Construction Catalog/product need; they are not
added speculatively.

---

## `PhysicalMeasure`

### Purpose

Carries one engineering quantity without commercial meaning.

### Kind

Value object.

### Fields

```text
dimension: MeasureDimension
value: Decimal
unit: MeasureUnit
```

### Invariants

- Dimension and unit are compatible according to State 2 rules.
- Price, currency, package count, discount, and labor do not belong here.

---

## `ConstructionQuantityLine`

### Purpose

Represents a physical quantity for a Construction Catalog-backed component or
system output.

```text
quantity_scope: Literal['construction']
line_id: str
system_ref: ConstructionSystemRef
component_id: str
measure: PhysicalMeasure
source_item_ids: list[str]
```

### Placeholder-resistance note

`source_item_ids` is temporarily constrained to Room Planner-owned item
identities but must be replaced by a typed source-reference union before State 1
is stabilized. It is recorded here as an explicit defect/open item, not accepted
as final model shape.

---

## `DemolitionQuantityLine`

### Purpose

Represents a physical demolition quantity tied to exact demolition intent and,
where applicable, explicit assumed removal thickness.

```text
quantity_scope: Literal['demolition']
line_id: str
demolition_item_id: str
measure: PhysicalMeasure
```

The referenced Demolition item carries the geometric target and any explicit
assumption used to derive the quantity.

---

## `TakeoffLine`

Candidate discriminated union on `quantity_scope`:

```text
ConstructionQuantityLine
DemolitionQuantityLine
```

---

## `RoomTakeoffSnapshot`

### Purpose

Represents a reproducible physical-quantity result for downstream publication
without transferring Room Planner geometry/calculation ownership to PresuPro.

### Kind

Immutable entity/output model.

### Fields

```text
takeoff_revision_id: str
object_ref: RegistryObjectRef
existing_basis: ExistingRevisionRef
demolition_basis: DemolitionRevisionRef | None
construction_basis: ConstructionRevisionRef | None
catalog_ref: ConstructionCatalogRef | None
lines: list[TakeoffLine]
```

### Invariants

- Every line belongs to demolition or construction scope explicitly.
- A catalog-dependent takeoff pins the exact catalog revision.
- A takeoff never contains prices, labor cost, package counts, or commercial
  rounding.
- Later plan/catalog revisions never silently change an old takeoff snapshot.

---

# 11. Stage specification artifact model boundary

State 0 requires lightweight Existing and Demolition specification artifacts,
conceptually an image plus a structured list with provenance.

State 1 does **not** yet define their Platform Hub wire schema because State 0
explicitly deferred:

- final artifact type names;
- image format;
- structured-list schema;
- whether payloads are embedded or referenced;
- publication packaging.

The domain models above must nevertheless make those artifacts deterministic:

- `ExistingPlanSnapshot` is sufficient source for an Existing specification;
- `DemolitionPlanSnapshot` plus demolition physical quantities are sufficient
  source for a Demolition specification;
- exact source publication/provenance references are attached at the later
  Platform Hub boundary rather than stored as rendering metadata inside domain
  geometry.

No AI narrative/report model is introduced.

---

# 12. Draft, snapshot, and publication lifecycle boundary

The current model deliberately distinguishes only:

```text
mutable working draft
immutable domain snapshot
platform publication record/artifact
```

The first two are Room Planner domain concerns. The third belongs to the shared
Platform Hub contract.

A later State 1 closure decision is still required for the word **accepted** in
State 0:

- Does acceptance create an immutable internal snapshot before platform
  publication?
- Or is the immutable Room Planner snapshot created only as part of explicit
  publication?

Until that is decided, the models above use `*Snapshot` as the immutable domain
basis concept without asserting exactly when its identity is minted.

This question must be resolved before State 1 is marked stabilized because
Demolition/Construction basis references depend on it.

---

# 13. Existing correction and dependent-plan carry-forward

State 0 requires an Existing correction to preserve old history and to carry
unambiguous Demolition/Construction intent forward while surfacing conflicts.

The following model facts are already fixed:

- old `ExistingPlanSnapshot` remains immutable;
- a new `ExistingPlanDraft` may be based on that snapshot;
- existing Demolition/Construction drafts remain pinned to their old
  `existing_basis` until an explicit carry-forward operation occurs;
- carry-forward must produce either an unambiguous mapped result or an explicit
  conflict; it must not silently retarget ids.

The exact conflict model is **not yet stabilized**. Before State 1 closes we
need typed variants for at least the conflict classes actually required by the
geometry model (for example target deleted, target split, target moved beyond
identity preservation, or opening/wall relationship invalidated). Do not use
`conflicts: list[dict]` or `reason: str` as the final model.

---

# 14. Model ownership/source matrix

| Model family | Created by | Read by | Mutable? | Persists? |
| --- | --- | --- | --- | --- |
| Registry/object refs | Platform boundary | all stage aggregates | no | as references |
| Spatial levels/datum | Room Planner working domain | all stages | yes in draft | yes |
| Existing draft | renovation professional/editor | geometry, demolition preparation | yes | yes |
| Existing snapshot | Room Planner snapshot/publication workflow | demolition, construction, history, takeoff | no | yes |
| Demolition draft | renovation professional/editor | proposed composition, takeoff | yes | yes |
| Demolition snapshot | Room Planner snapshot/publication workflow | construction, history, takeoff | no | yes |
| Construction draft | renovation professional/editor | proposed composition, takeoff | yes | yes |
| Construction snapshot | Room Planner snapshot/publication workflow | history, takeoff, downstream artifacts | no | yes |
| Proposed view | derived domain logic | editor/review/takeoff | no source edits | transient/derived |
| Construction Catalog refs | Platform boundary | construction/takeoff | no | as references |
| Takeoff snapshot | Room Planner calculation domain | PresuPro/platform consumers | no | yes when retained/published |

Exact storage tables/ORM/persistence classes are later-state concerns.

---

# 15. Explicit State 1 open decisions

These are model decisions that must be resolved before this state is
`stabilized`:

1. **Accepted vs published snapshot identity** — when exactly an immutable
   stage basis id is minted.
2. **Carry-forward conflict union** — the closed typed conflict variants needed
   when Existing corrections affect Demolition/Construction intent.
3. **Proposed source refs** — the closed typed provenance refs for retained,
   removed, and newly constructed geometry.
4. **Takeoff source refs** — replace provisional `source_item_ids: list[str]`
   with a typed discriminated union so quantity provenance cannot point to the
   wrong kind of object.
5. **Room boundary edge completeness** — determine whether the initial usable
   product needs non-wall/open boundary edges; if yes, model them explicitly.
6. **Construction opening responsibility** — confirm whether a changed opening
   in a retained Existing wall is fully represented by Demolition cut +
   Construction opening, or whether another explicit modification variant is
   required.
7. **Ceiling treatment taxonomy** — State 0 leaves exact ceiling systems open;
   confirm the minimum domain variants before freezing `ConstructionTreatment`.
8. **Catalog-backed wall system selection** — confirm whether every published
   Construction wall must reference a catalog system or whether some valid
   geometry-only wall class exists.
9. **Level/Registry projection** — only if Platform Router/Registry defines
   shared floor identity during this state; otherwise `SpatialLevel.level_id`
   remains Room Planner-local under the canonical object.

Questions intentionally belonging to State 2 or later are not blockers here:
coordinate tolerance, polygon validity policy, grid density, interpolation,
surface reconstruction, quantity formulas, opening-fit validation, publication
HTTP contracts, database layout, rendering format, and authorization policy.

---

# 16. Placeholder resistance audit

The draft currently rejects the following shortcuts:

- no generic `Plan.data` payload;
- no `metadata: dict` on geometry;
- no single generic stage model that permits semantic mixing;
- no screen-pixel coordinates;
- no decorative door/window overlays;
- no scalar room-wide floor level/height replacing the vertical grid;
- no fabricated demolition thickness;
- no catalog "latest" pointer in historical snapshots;
- no pricing fields in takeoff;
- no generic client-history/publication metadata inside Room Planner geometry;
- no direct editor mutation of Proposed/To-Be results;
- no parallel Construction variants in the initial product.

One provisional placeholder remains intentionally visible:
`ConstructionQuantityLine.source_item_ids: list[str]`. State 1 is not ready to
stabilize until it is replaced by typed source references.

---

# 17. Platform Router impact

This state introduces **no new Platform Hub mechanism** beyond the shared
requirements already recorded in `../../PLATFORM_ROUTER.md`.

The domain model consumes the existing shared requirements for:

- canonical Registry `object_id`;
- exact Construction Catalog revision resolution;
- immutable publication history;
- exact basis/provenance links between stage publications;
- artifact publication/discovery separate from private working state;
- language-neutral later artifact contracts.

Room Planner-specific `ExistingRevisionRef`, `DemolitionRevisionRef`,
`ConstructionRevisionRef`, and `ConstructionCatalogRef` are domain references,
not a competing platform protocol. Their later wire representation must map to
the Platform Hub contract registry/artifact provenance model rather than create
a private Room Planner-to-consumer API.

If closure of the `accepted vs published snapshot identity` question requires a
new platform-visible lifecycle concept, `PLATFORM_ROUTER.md` must be updated at
that time before Room Planner invents it privately.

---

# State 1 readiness status

The core domain language is now concrete enough to continue model review, but
State 1 is **not stabilized yet**.

The highest-priority closure order is:

1. accepted/published basis identity;
2. correction carry-forward conflict types;
3. typed Proposed and takeoff source references;
4. remaining opening/ceiling/catalog model questions;
5. final placeholder audit.

Only after those model decisions are closed should Room Planner proceed to
State 2 rules and invariants.
