# Room Planner — State 1: Door Swing and Planned Opening Elements

> Status: accepted State 1 refinement.
>
> This document repairs State 1 after the stabilized product boundary gained the
> requirement that hinged-door opening direction is domain-significant. It also
> closes the related gap that Construction previously modeled positive aperture
> results but not the physical door/window element installed in an aperture.
>
> Where this file refines earlier opening-element shapes, it is normative over
> the provisional forms in `10_opening_lifecycle.md`.

## 1. Canonical hinged-door swing

A hinged-door swing must be independent of camera orientation, SVG variants, and
user-facing words such as "left door" or "opens inward".

The canonical value object is:

```text
DoorSwing
    hinge_jamb: DoorHingeJamb
    swing_to_wall_side: WallSide
```

Candidate closed `DoorHingeJamb` values:

```text
opening_start
opening_end
```

`opening_start` and `opening_end` are defined along the host wall's directed
start → end axis and the aperture's wall-relative profile.

`WallSide` remains the existing closed meaning:

```text
left
right
```

relative to the directed host wall.

Together these two fields determine the plan swing unambiguously. Clockwise /
counter-clockwise display orientation is derived from them; it is not stored as
an independent mutable fact.

## 2. Why `opens_inward` is not canonical

A boolean such as:

```text
opens_inward: bool
```

is not a stable domain representation because an aperture may separate two
interior rooms and either side can be the reference context.

The canonical `swing_to_wall_side` identifies the physical side of the wall into
which the leaf opens. The browser may resolve adjacency and present contextual
labels such as:

```text
opens into Kitchen
opens into Corridor
opens toward exterior
opens inward / outward
```

when room/exterior context makes those labels well-defined.

## 3. Existing opening-element refinement

The earlier generic `ExistingOpeningElement(element_kind=door|window)` is refined
into a closed union because a hinged door carries door-specific swing semantics.

### `ExistingHingedDoorElement`

```text
element_kind: Literal['hinged_door']
element_id: str
opening_id: str
swing: DoorSwing | None
```

`None` means the Existing swing was not observed/recorded. It must never be
replaced by a renderer default and must remain visibly unknown where the UI
presents the door.

### `ExistingWindowElement`

```text
element_kind: Literal['window']
element_id: str
opening_id: str
```

### `ExistingOpeningElement`

Closed discriminated union on `element_kind`:

```text
ExistingHingedDoorElement
ExistingWindowElement
```

Other motion families such as sliding/folding doors require explicit later
variants rather than abusing `DoorSwing`.

## 4. Construction must model positive installed opening elements

A Construction aperture result is not sufficient to describe the final plan when
a new/replacement door or window is intended.

Construction therefore gains explicit positive opening-element installation
intent. Demolition remains responsible for removing any Existing physical
element that is to disappear.

Conceptually:

```text
aperture lifecycle
    Create / Alter / Close

opening-element lifecycle
    retain Existing element
    remove Existing element in Demolition
    install new element in Construction
```

## 5. Installation target

A Construction-installed element may occupy either:

- a retained Existing aperture that remains present; or
- a positive aperture produced by `CreateConstructionOpening` or
  `AlterExistingOpening`.

Use a closed `OpeningElementInstallationTarget` union:

### `RetainedExistingOpeningInstallationTarget`

```text
opening_target_kind: Literal['existing_opening']
opening: ExistingOpeningRef
```

### `ConstructionResultOpeningInstallationTarget`

```text
opening_target_kind: Literal['construction_result_opening']
result_opening_id: str
```

The latter id resolves inside the same Construction draft/snapshot level.

An element cannot target `CloseExistingOpening` because that intent produces no
positive aperture.

## 6. Construction opening-element intent

### Draft hinged door

```text
InstallHingedDoorDraft
    opening_element_intent_kind: Literal['install_hinged_door']
    item_id: str
    result_element_id: str
    target: OpeningElementInstallationTarget
    swing: DoorSwing | None
```

Draft `swing = None` means the door element is being placed before its final
opening direction is decided. It is not a default swing.

### Accepted hinged door

```text
InstallHingedDoor
    opening_element_intent_kind: Literal['install_hinged_door']
    item_id: str
    result_element_id: str
    target: OpeningElementInstallationTarget
    swing: DoorSwing
```

A designed hinged door therefore cannot enter an accepted Construction snapshot
without an explicit swing.

### Window installation

```text
InstallWindow
    opening_element_intent_kind: Literal['install_window']
    item_id: str
    result_element_id: str
    target: OpeningElementInstallationTarget
```

### `ConstructionOpeningElementIntent`

Accepted closed union:

```text
InstallHingedDoor
InstallWindow
```

The mutable draft collection uses the corresponding draft shapes where partial
values are explicitly allowed.

## 7. Construction aggregate refinement

`ConstructionLevelDraft` gains:

```text
opening_element_intents: list[ConstructionOpeningElementIntentDraft]
```

The accepted Construction level/snapshot gains:

```text
opening_element_intents: list[ConstructionOpeningElementIntent]
```

This collection is separate from aperture `opening_intents`.

Replacing a door therefore remains explicit:

```text
Demolition:
    RemoveExistingOpeningElement(old door)

Construction:
    InstallHingedDoor(new door, explicit swing)
```

If the Existing aperture is unchanged, the new door targets that retained
Existing opening. If the aperture is altered, it targets the resulting
Construction opening identity.

## 8. Proposed opening-element result

Proposed must represent positive installed elements separately from positive
apertures.

### `ConstructionResultOpeningElementSourceRef`

```text
source_kind: Literal['construction_result_opening_element']
snapshot: ConstructionSnapshotRef
level_id: str
element_id: str
```

### `ProposedOpeningElementSourceRef`

Closed union:

```text
ExistingOpeningElementSourceRef
ConstructionResultOpeningElementSourceRef
```

### `ProposedOpeningElement`

Conceptually:

```text
result_element_id: str
opening_id: str
element_kind: ProposedOpeningElementKind
swing: DoorSwing | None
source: ProposedOpeningElementSourceRef
```

For a proposed hinged door, `swing` is present. For a proposed window it is
absent by variant rather than interpreted as unknown door data.

A retained Existing hinged door carries its Existing swing, including an
explicit unknown if the survey did not record it. A Construction-installed
hinged door always carries an explicit accepted swing.

## 9. Proposed composition consequences

```text
Existing door retained and not removed
    → Proposed opening element sourced from Existing

Existing door removed, no replacement
    → aperture may remain, Proposed has no installed door element

Existing door removed + Construction installs new door
    → Proposed element sourced from Construction

Construction creates/alters aperture + installs door
    → Proposed aperture + Proposed door are separate positive results

Construction closes aperture
    → no Proposed aperture and therefore no Proposed opening element
```

A symbol is never the source of these results.

## 10. Provenance and carry-forward refs

Construction opening-element installation is a dependent intent and a possible
takeoff source. Add:

```text
ConstructionOpeningElementIntentSourceRef
    source_kind: Literal['construction_opening_element_intent']
    snapshot: ConstructionSnapshotRef
    level_id: str
    item_id: str
```

`DependentIntentRef` and `ConstructionQuantitySourceRef` gain this explicit
variant.

The positive Proposed element uses
`ConstructionResultOpeningElementSourceRef`, not the intent ref, preserving the
same intent-versus-result separation already established for apertures.

## 11. Wall direction stability

DoorSwing is expressed relative to the directed host wall. Therefore reversing a
wall's stored start/end orientation is not a harmless serialization rewrite.

Any operation that intentionally reverses the host wall direction while
preserving the same world geometry must also transform all wall-relative opening
profiles and door-swing semantics so the physical aperture and leaf swing remain
unchanged in world space.

The exact transformation belongs to State 2, but the model must not treat wall
orientation as disposable once wall-relative semantics exist.

## 12. Frontend consequence

The browser has enough canonical information to select/render the correct swing
arc/symbol variant without owning the decision:

```text
DoorSwing
    ↓
building-layer projection
    ↓
symbol/renderer variant
```

Pointer tools may preview changing hinge jamb or swing side, but confirmation
must emit a typed Room Planner domain command/intent rather than only swapping an
SVG asset.

For an Existing door with unknown swing, the renderer uses an explicit
unknown/neutral presentation and must not choose a physical opening direction.

## 13. Platform Router impact

No new Platform Hub mechanism is required. The future language-neutral
`room_plan` schema must carry door-element/swing semantics where relevant so a
published plan remains reproducible across browser and downstream renderers.
