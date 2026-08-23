# Room Planner — State 1: Typed Source and Provenance References

> Status: accepted State 1 model refinement.
>
> This document supplements [10_models.md](10_models.md) and
> [10_identity_carry_forward.md](10_identity_carry_forward.md). It closes the
> provisional dependent-intent, Proposed-source, and takeoff-source reference
> shapes. Where these decisions differ from provisional fields in
> `10_models.md`, this document is the later refinement.

## 1. Goal

Room Planner needs typed references that can answer exactly which accepted
snapshot entity or intent produced a dependent result without falling back to
unqualified ids such as:

```text
source_item_ids: list[str]
source_id: str
source_kind: str
metadata: dict
```

The same domain identity must remain usable by:

- Existing correction carry-forward conflicts;
- derived Proposed / To-Be geometry provenance;
- physical takeoff line provenance;
- later deterministic stage specification generation.

These are Room Planner domain references. They do not replace Platform Hub
artifact/publication provenance.

## 2. Standalone source references are snapshot- and level-qualified

Room Planner supports multiple spatial levels. A provenance reference that may
escape the immediate owning level therefore carries enough context to resolve
without relying on a caller's implicit level.

The canonical standalone source reference pattern is:

```text
exact accepted snapshot
+ level_id
+ entity/item id
+ closed source kind
```

A bare `wall_id`, `opening_id`, or `item_id` remains acceptable only where the
owning aggregate already supplies the exact snapshot and level context. It is
not sufficient as a detached provenance reference.

### `ExistingWallSourceRef`

```text
source_kind: Literal['existing_wall']
snapshot: ExistingSnapshotRef
level_id: str
wall_id: str
```

### `ExistingOpeningSourceRef`

```text
source_kind: Literal['existing_opening']
snapshot: ExistingSnapshotRef
level_id: str
opening_id: str
```

### `ExistingRoomSourceRef`

```text
source_kind: Literal['existing_room']
snapshot: ExistingSnapshotRef
level_id: str
room_id: str
```

### `ExistingSurfaceLayerSourceRef`

```text
source_kind: Literal['existing_surface_layer']
snapshot: ExistingSnapshotRef
level_id: str
layer_id: str
```

### `DemolitionItemSourceRef`

```text
source_kind: Literal['demolition_item']
snapshot: DemolitionSnapshotRef
level_id: str
item_id: str
```

### `ConstructionWallSourceRef`

```text
source_kind: Literal['construction_wall']
snapshot: ConstructionSnapshotRef
level_id: str
wall_id: str
```

### `ConstructionOpeningSourceRef`

```text
source_kind: Literal['construction_opening']
snapshot: ConstructionSnapshotRef
level_id: str
opening_id: str
```

### `ConstructionTreatmentSourceRef`

```text
source_kind: Literal['construction_treatment']
snapshot: ConstructionSnapshotRef
level_id: str
item_id: str
```

The source-kind vocabulary is closed. New variants require a real domain source
that must participate in provenance; they must not be introduced merely because
an implementation helper has an id.

## 3. Existing correction lineage refs gain explicit level context

`10_identity_carry_forward.md` introduced `ExistingEntityRef` variants without
an explicit `level_id`. This refinement adds level context so correction lineage
is unambiguous in a multi-level object.

Use:

```text
ExistingWallEntityRef
    entity_kind: Literal['wall']
    level_id: str
    wall_id: str

ExistingOpeningEntityRef
    entity_kind: Literal['opening']
    level_id: str
    opening_id: str

ExistingRoomEntityRef
    entity_kind: Literal['room']
    level_id: str
    room_id: str

ExistingSurfaceLayerEntityRef
    entity_kind: Literal['surface_layer']
    level_id: str
    layer_id: str
```

`ExistingCorrectionLineage.from_snapshot` and `to_snapshot` still provide the
snapshot scope. The entity refs identify the exact level-local entity within
those snapshots.

This does not imply that ids may be freely reused across levels; it simply makes
the reference self-contained and avoids depending on an unstated global-id
invariant.

## 4. `DependentIntentRef` is now closed and typed

Carry-forward conflicts must point to the exact dependent intent whose meaning
could not be preserved.

`DependentIntentRef` is a discriminated union on `source_kind` with these
concrete variants:

```text
DemolitionItemSourceRef
ConstructionWallSourceRef
ConstructionOpeningSourceRef
ConstructionTreatmentSourceRef
```

A conflict therefore cannot point accidentally to an Existing wall when it is
supposed to identify the Demolition or Construction intent being carried.

The snapshot carried by each ref makes a conflict self-contained even when it
is stored or inspected outside its surrounding carry-forward result.

### Carry-forward conflict refinement

The `intent` field of every conflict defined in
`10_identity_carry_forward.md` is now exactly:

```text
intent: DependentIntentRef
```

No `intent_id: str`, `stage: str`, generic payload, or free-form reason is used
as a replacement.

## 5. Proposed / To-Be provenance

Proposed remains a derived composition. It is not a fourth editable source of
truth.

The composition as a whole is understood against exact accepted bases:

```text
ProposedCompositionBasis
    existing_basis: ExistingSnapshotRef
    demolition_basis: DemolitionSnapshotRef | None
    construction_basis: ConstructionSnapshotRef | None
```

The basis refs say which accepted source results participate in the composition.
Individual Proposed elements additionally identify where the positive geometry
that exists in the resulting view comes from.

### `ProposedWallSourceRef`

Closed discriminated union on `source_kind`:

```text
ExistingWallSourceRef
ConstructionWallSourceRef
```

A retained Existing wall points to its Existing source. A newly constructed
wall points to its Construction source.

### `ProposedOpeningSourceRef`

Closed discriminated union on `source_kind`:

```text
ExistingOpeningSourceRef
ConstructionOpeningSourceRef
```

A retained Existing opening points to its Existing source. An opening introduced
by Construction points to its Construction source.

### Required provenance fields

The provisional Proposed models from `10_models.md` are refined so that:

```text
ProposedWall
    source: ProposedWallSourceRef
    ...derived geometry...

ProposedOpening
    source: ProposedOpeningSourceRef
    ...derived geometry...
```

The exact derived geometry fields remain governed by the geometry model and
later rules; the provenance field is no longer open.

### Removed Existing geometry is not a fake Proposed element

An Existing wall/opening removed by Demolition is absent from Proposed. Room
Planner must not create a synthetic `removed` Proposed entity merely to carry a
source ref.

Why an Existing element is absent is reproducible from:

```text
ProposedCompositionBasis.demolition_basis
+ the exact Demolition items in that snapshot
```

This keeps Proposed a model of the resulting spatial state rather than mixing
result geometry with demolition history entries.

### Proposed rooms

A Proposed room is derived from the resulting boundary topology and may not have
a one-to-one source room after split/merge/reconfiguration. Room Planner must not
invent a generic room source id.

Its provenance is therefore boundary-derived: the room boundary is composed of
Proposed wall/opening geometry whose source refs are typed. A later rule may also
carry an optional preserved Existing room identity when correction/topology
lineage proves it, but such a convenience field is not required to make the
room reproducible and is not added speculatively here.

## 6. Typed takeoff provenance

A takeoff line must identify the concrete Room Planner intent/geometry source
that caused the physical quantity without using a list of arbitrary strings.

### Construction quantity sources

`ConstructionQuantitySourceRef` is a closed discriminated union on
`source_kind`:

```text
ConstructionWallSourceRef
ConstructionOpeningSourceRef
ConstructionTreatmentSourceRef
```

The provisional `ConstructionQuantityLine` is refined to:

```text
ConstructionQuantityLine
    quantity_scope: Literal['construction']
    line_id: str
    system_ref: ConstructionSystemRef
    component_id: str
    measure: PhysicalMeasure
    sources: list[ConstructionQuantitySourceRef]
```

A line may aggregate several typed Construction sources when one physical output
is intentionally aggregated across multiple owned items. The exact aggregation
and deterministic ordering rules belong to State 2.

A treatment on a retained Existing wall still uses its
`ConstructionTreatmentSourceRef` as the takeoff source. The treatment itself
contains the typed target back to the Existing basis; the takeoff line does not
need to duplicate the whole target graph.

### Demolition quantity source

The provisional `DemolitionQuantityLine.demolition_item_id: str` is refined to:

```text
DemolitionQuantityLine
    quantity_scope: Literal['demolition']
    line_id: str
    source: DemolitionItemSourceRef
    measure: PhysicalMeasure
```

The referenced Demolition item carries its typed Existing target and any
explicit removal-thickness assumption used by the calculation.

### `RoomTakeoffSnapshot` basis terminology

Consistent with `10_identity_carry_forward.md`, the reproducible takeoff uses
snapshot terminology:

```text
RoomTakeoffSnapshot
    takeoff_snapshot_id: str
    object_ref: RegistryObjectRef
    existing_basis: ExistingSnapshotRef
    demolition_basis: DemolitionSnapshotRef | None
    construction_basis: ConstructionSnapshotRef | None
    catalog_ref: ConstructionCatalogRef | None
    lines: list[TakeoffLine]
```

State 2 must enforce that every line-level source belongs to the exact stage
snapshot carried by the takeoff basis. A historical takeoff never silently
rebinds line sources to a newer stage or catalog snapshot/revision.

## 7. Narrow unions are preferred over one universal source union

The concrete source-ref variants are reusable, but fields use the narrowest
valid union:

```text
carry-forward conflict intent
    → DependentIntentRef

Proposed wall source
    → ProposedWallSourceRef

Proposed opening source
    → ProposedOpeningSourceRef

Construction quantity sources
    → ConstructionQuantitySourceRef

Demolition quantity source
    → DemolitionItemSourceRef
```

Do not introduce one universal `RoomPlannerSourceRef` in every field merely for
convenience. A broad union would allow semantically invalid references, such as
a demolition item pretending to be the source of a Proposed wall or an Existing
room pretending to be a Construction quantity source.

When these unions are later lowered into `global_spec.json`, each discriminated
union must list its concrete variants directly rather than relying on union-of-
union nesting.

## 8. Domain provenance versus Platform Hub provenance

These typed refs answer an internal/domain question:

> Which exact Room Planner snapshot entity or intent produced this derived
> element, conflict, or physical quantity?

Platform Hub provenance answers a different platform question:

> Which published Hub artifact/publication revisions were the basis of this
> published result?

The two layers are connected but not interchangeable.

When a Room Planner snapshot/takeoff is published, the Platform Hub publication
must carry Hub-resolvable artifact/publication provenance according to
[PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md). A Room Planner-private
`snapshot_id` is not a substitute for Hub artifact identity.

A published artifact payload may still contain typed Room Planner element/source
refs where its language-neutral artifact schema requires element-level
provenance. Those refs remain scoped by the exact published Room Planner
snapshot represented by the artifact contract.

No new Platform Hub mechanism is introduced by this refinement.

## 9. Placeholder resistance closure

The provisional placeholder from `10_models.md`:

```text
ConstructionQuantityLine.source_item_ids: list[str]
```

is superseded and no longer an accepted State 1 model shape.

This refinement also rejects:

- `source_id: str` without a closed source type and snapshot context;
- `intent_id: str` without a typed stage-specific ref;
- `sources: list[str]`;
- a generic source `payload` or `metadata` object;
- one universal source union where a narrower union can rule out invalid
  references;
- relying on coordinate similarity to recover provenance that should already be
  represented by accepted identity/lineage.

## 10. Platform Router impact

This state refinement introduces **no new Platform Hub capability**.

It preserves the existing boundary recorded in
[PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md):

- Room Planner owns its internal domain entity/intent provenance;
- Platform Hub owns published artifact identity, discovery, immutable platform
  history, and cross-artifact provenance;
- published dependent results must retain exact Hub-resolvable basis provenance;
- element-level source refs may be part of a later artifact payload schema but
  do not replace Hub artifact/publication lineage.

## 11. State 1 closure effect

This refinement closes these previously explicit State 1 model questions:

1. `DependentIntentRef` is now a closed typed union;
2. Proposed wall/opening provenance uses closed source refs;
3. takeoff line provenance no longer uses `source_item_ids: list[str]` or bare
   demolition item ids;
4. standalone multi-level source refs are qualified by snapshot and level;
5. Existing correction lineage entity refs are level-qualified.

Remaining State 1 closure work is now limited to the smaller model questions
already identified in `10_models.md`:

- whether initial room boundaries require explicit non-wall boundary edges;
- whether changed openings in retained Existing walls are fully modeled by
  Demolition cut + Construction opening or require another explicit variant;
- the minimum ceiling treatment/system taxonomy;
- whether every accepted/publishable Construction wall requires a Construction
  Catalog system ref;
- Registry/Platform Hub level projection only if the shared platform contract
  becomes concrete enough during this state.
