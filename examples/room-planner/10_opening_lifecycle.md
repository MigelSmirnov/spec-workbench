# Room Planner — State 1: Opening Lifecycle and Opening-Change Intent

> Status: accepted State 1 model refinement.
>
> This document supplements [10_models.md](10_models.md),
> [10_identity_carry_forward.md](10_identity_carry_forward.md), and
> [10_source_provenance.md](10_source_provenance.md). It closes the State 1
> question of how existing, removed, created, resized, moved, and closed wall
> openings are represented without mixing Existing, Demolition, Construction,
> and Proposed meanings.

## 1. Opening aperture and installed element are different concepts

The provisional `ExistingOpening` in `10_models.md` mixes two related meanings:
wall aperture geometry and a door/window installed in that aperture. That is
insufficient for demolition because removing a door or window does not
necessarily remove or close the aperture in the wall.

State 1 therefore distinguishes:

```text
opening aperture
    spatial void / wall-topology feature

opening element
    physical door/window assembly occupying an aperture
```

### `ExistingOpening`

`ExistingOpening` remains the measured aperture entity anchored to an Existing
wall. Its geometry is authoritative Existing spatial data.

Refined fields:

```text
opening_id: str
wall_id: str
use_kind: OpeningUseKind
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
```

Candidate closed `OpeningUseKind` values:

```text
doorway
window_opening
unframed_opening
```

`use_kind` classifies the spatial opening/use. It does not prove that a physical
door/window assembly is installed.

### `ExistingOpeningElement`

Represents a removable physical element installed in an Existing aperture.

```text
element_id: str
opening_id: str
element_kind: OpeningElementKind
```

Candidate closed `OpeningElementKind` values:

```text
door
window
```

An unframed opening has no `ExistingOpeningElement`.

Exact leaf/frame/sash/product detail is not introduced at State 1 because the
current product boundary requires spatial renovation planning, not a door/window
product configurator.

## 2. Demolition owns removal, not the final opening result

Demolition describes physical removal against the Existing basis. It does not
own the final aperture that Construction intends to exist.

The provisional `RemoveExistingOpening` variant is superseded because deleting
an aperture is not a faithful representation of removing a door/window assembly.

### `RemoveExistingOpeningElement`

```text
demolition_kind: Literal['remove_opening_element']
item_id: str
target: ExistingOpeningElementRef
```

This removes the installed door/window element while preserving the Existing
aperture unless another demolition/construction intent changes the wall geometry.

### `ExistingOpeningElementRef`

```text
element_id: str
```

The ref is interpreted against the owning Demolition plan's exact Existing
snapshot and level context.

### Opening cuts are explicit demolition geometry

The provisional `WallOpeningDemolitionCut` is refined into two meanings so a cut
cannot ambiguously mean either a brand-new aperture or enlargement of an
existing aperture.

#### `NewWallOpeningCut`

```text
demolition_kind: Literal['new_wall_opening_cut']
item_id: str
wall: ExistingWallRef
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
```

This removes Existing wall material to create aperture space where no Existing
opening is the semantic predecessor.

#### `ExistingOpeningEnlargementCut`

```text
demolition_kind: Literal['existing_opening_enlargement_cut']
item_id: str
target: ExistingOpeningRef
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
```

This records removal of Existing wall material associated with enlarging or
shifting an Existing aperture. The fields describe the demolition cut extent,
not the final Construction opening contract.

The exact geometric relationship between the cut and the old/new aperture is a
State 2 rule.

### Refined `DemolitionItem`

For opening-related work the closed union now includes:

```text
RemoveExistingOpeningElement
NewWallOpeningCut
ExistingOpeningEnlargementCut
```

alongside the already accepted non-opening demolition variants.

Removing an entire Existing wall implicitly removes the aperture topology hosted
by that wall; a second fake `remove opening aperture` item is not required.

## 3. Construction owns the intended aperture lifecycle

A single provisional `ConstructionOpening` cannot say whether it is:

- a completely new aperture;
- a changed successor of an Existing aperture; or
- an Existing aperture that is intentionally closed.

State 1 therefore replaces the single shape with a closed
`ConstructionOpeningIntent` union.

## 4. Shared final-opening geometry value

### `OpeningProfile`

Represents the intended aperture geometry/use relative to its host wall.

```text
use_kind: OpeningUseKind
offset_from_wall_start_mm: Decimal
width_mm: Decimal
sill_height_mm: Decimal
height_mm: Decimal
```

This is a value object. Host identity and lifecycle meaning belong to the
construction intent variant, not to `OpeningProfile`.

## 5. `CreateConstructionOpening`

Creates a new intended aperture with no Existing-opening predecessor.

```text
opening_intent_kind: Literal['create_opening']
item_id: str
result_opening_id: str
wall: ConstructionWallTarget
profile: OpeningProfile
```

The host may be:

- a retained Existing wall; or
- a newly constructed wall.

When the host is an Existing wall, later rules require the necessary Demolition
cut basis before the result can be accepted where Existing wall material must be
removed. When the host is a new Construction wall, no Existing demolition cut is
implied.

## 6. `AlterExistingOpening`

Represents a final aperture that is the semantic successor of one Existing
opening.

```text
opening_intent_kind: Literal['alter_existing_opening']
item_id: str
source: ExistingOpeningRef
result_opening_id: str
profile: OpeningProfile
infill_system_ref: ConstructionSystemRef | None
```

This is the normal model for resize/reposition/use change when the user still
means "this Existing opening, changed" rather than delete-old/create-unrelated.

`infill_system_ref` is explicit Construction input for cases where part of the
old aperture must be rebuilt/closed. It may be `None` in a working draft or when
no infill is physically required. State 2 determines when acceptance requires
it.

Any enlargement/removal of Existing wall material remains Demolition intent and
must be represented separately by the applicable demolition cut. Construction
never fabricates that demolition history from the final profile.

The altered result remains on the same semantic Existing host wall. Moving an
opening to a different wall is modeled as closing/removing the old aperture
meaning and creating a new opening on the other wall, not as identity-preserving
alteration.

## 7. `CloseExistingOpening`

Represents Construction intent to eliminate an Existing aperture by rebuilding
the wall opening area.

```text
opening_intent_kind: Literal['close_existing_opening']
item_id: str
source: ExistingOpeningRef
infill_system_ref: ConstructionSystemRef
```

This produces no Proposed opening entity.

If a physical door/window element exists, its removal remains an explicit
Demolition concern through `RemoveExistingOpeningElement`; closing the aperture
does not silently claim that demolition occurred.

## 8. Refined Construction opening collection

`ConstructionOpeningIntent` is a closed discriminated union on
`opening_intent_kind`:

```text
CreateConstructionOpening
AlterExistingOpening
CloseExistingOpening
```

`ConstructionLevelDraft` is refined from:

```text
openings: list[ConstructionOpening]
```

to:

```text
opening_intents: list[ConstructionOpeningIntent]
```

A later immutable Construction snapshot freezes the same semantic intent shapes.

This avoids a generic `ModifyExistingOpening` payload while still supporting the
full initial lifecycle.

## 9. Proposed / To-Be opening composition

Proposed shows apertures that exist in the resulting spatial state.

Rules at the model level are:

```text
unchanged Existing opening
    → Proposed opening sourced from Existing

CreateConstructionOpening
    → Proposed opening sourced from Construction result

AlterExistingOpening
    → old Existing aperture is superseded
    → one Proposed opening sourced from Construction result

CloseExistingOpening
    → no Proposed opening result
```

Demolition cuts themselves are not fake Proposed openings. They explain removed
material; Construction intent defines the intended positive aperture result.

## 10. Provenance refinement for opening intent versus opening result

`10_source_provenance.md` provisionally used one
`ConstructionOpeningSourceRef` for both dependent intent and positive Proposed
geometry. The opening lifecycle now requires those meanings to be separate.

### `ConstructionOpeningIntentSourceRef`

Used by carry-forward conflicts and takeoff provenance.

```text
source_kind: Literal['construction_opening_intent']
snapshot: ConstructionSnapshotRef
level_id: str
item_id: str
```

This can identify any of the three Construction opening-intent variants,
including `CloseExistingOpening`, which has no resulting aperture.

### `ConstructionResultOpeningSourceRef`

Used only for positive resulting aperture geometry in Proposed.

```text
source_kind: Literal['construction_result_opening']
snapshot: ConstructionSnapshotRef
level_id: str
opening_id: str
```

Only `CreateConstructionOpening` and `AlterExistingOpening` produce a
`result_opening_id` resolvable by this ref.

### Narrow-union updates

`DependentIntentRef` replaces provisional `ConstructionOpeningSourceRef` with:

```text
ConstructionOpeningIntentSourceRef
```

`ConstructionQuantitySourceRef` likewise uses:

```text
ConstructionOpeningIntentSourceRef
```

`ProposedOpeningSourceRef` becomes:

```text
ExistingOpeningSourceRef
ConstructionResultOpeningSourceRef
```

This prevents a closed-opening construction intent from being mistaken for a
positive Proposed aperture.

## 11. Existing opening-element provenance

For demolition and future human-readable specification provenance, add the
standalone source ref:

```text
ExistingOpeningElementSourceRef
    source_kind: Literal['existing_opening_element']
    snapshot: ExistingSnapshotRef
    level_id: str
    element_id: str
```

`ExistingEntityRef` used by correction lineage also gains an opening-element
variant only if opening-element identity is preserved across Existing
corrections:

```text
ExistingOpeningElementEntityRef
    entity_kind: Literal['opening_element']
    level_id: str
    element_id: str
```

This is justified because dependent Demolition may target the exact installed
physical element.

## 12. Carry-forward consequences

The accepted carry-forward conflict family remains sufficient.

Examples:

- an `AlterExistingOpening` whose source opening is removed by Existing
  correction → `MissingTargetConflict`;
- an opening whose host-wall relationship changes incoherently →
  `InvalidHostRelationshipConflict`;
- a corrected wall becomes too short for a carried `CreateConstructionOpening`
  or altered profile → `InvalidRelativePlacementConflict`;
- an Existing opening split/reinterpreted ambiguously by correction →
  `AmbiguousTargetConflict`.

Exact predicates belong to State 2.

## 13. Browser-editor consequence

The browser can now render/edit the opening lifecycle without inventing a second
source of truth:

```text
Existing aperture + optional Existing opening element
        ↓ overlays
Demolition element removal / wall cut
        ↓
Construction create / alter / close intent
        ↓
Derived Proposed opening scene
```

Transient drag handles, resize previews, snap guides, and hover/selection remain
frontend-only state under [FRONTEND_EDITOR.md](../../FRONTEND_EDITOR.md).

The frontend may preview an altered profile continuously, but only confirmed
editor actions mutate the Room Planner working draft; preview does not create an
accepted snapshot or Platform Hub publication.

## 14. Platform Router impact

This refinement introduces no new Platform Hub mechanism.

Published Room Planner artifacts must eventually carry the refined opening
semantics through the language-neutral `room_plan` contract, while Platform Hub
continues to own only artifact identity, publication history, discovery, and
cross-artifact provenance.

Door/window editor interaction, aperture construction rules, demolition cut
rules, and infill calculation remain Room Planner responsibilities rather than
Platform Hub business logic.

## 15. State 1 closure effect

This closes the earlier State 1 question "is Demolition cut + Construction
opening enough?" with a refined answer:

- separate Demolition and Construction stages remain correct;
- a generic Construction opening is not sufficient;
- opening change is represented by explicit `create`, `alter`, and `close`
  Construction intent variants;
- wall-material removal remains explicit Demolition cut intent;
- aperture infill is explicit Construction input;
- installed Existing door/window removal is distinct from aperture closure;
- Proposed contains only positive resulting apertures with typed provenance.

No universal opening-modification payload is introduced.
