# Room Planner — State 2: Rules and Invariants

> Status: working draft.
>
> State 1 defines what the Room Planner domain concepts are. This state defines
> the policies that make those models valid, reproducible, and safe to carry
> between Existing, Demolition, Construction, Proposed, takeoff, the browser
> editor, and Platform Hub publication.
>
> This document does not define modules, HTTP routes, persistence tables, or
> Python function contracts.

## Goal

State 2 separates:

- invariants that must always hold;
- acceptance/completeness rules that distinguish editable drafts from immutable
  snapshots;
- deterministic topology/composition rules;
- catalog and provenance consistency rules;
- read-only policy data such as unit compatibility;
- genuinely unresolved calculation/interpolation policies that must remain
  explicit rather than being replaced with defaults.

---

# 1. Stage isolation invariants

1. Existing contains only measured/accepted pre-renovation facts.
2. Demolition contains only removal intent against an exact Existing snapshot.
3. Construction contains only intended new/changed/prepared/finished work against
   exact accepted basis snapshots.
4. Proposed is derived from Existing + applicable Demolition + applicable
   Construction and is never directly edited as a fourth source plan.
5. A model/entity id belonging to one stage does not grant permission to mutate
   the corresponding entity of another stage.
6. Construction intent MUST NOT be copied into Existing merely to simplify
   rendering or persistence.
7. Demolition intent MUST NOT be represented by deleting data from an Existing
   snapshot.
8. A later Existing correction MUST NOT mutate or silently rebind an earlier
   Demolition/Construction snapshot.
9. Browser overlays/colors/layers do not alter these semantic boundaries.

---

# 2. Draft, acceptance, snapshot, and publication invariants

## Working drafts

1. Drafts are mutable private Room Planner state.
2. Draft saves may contain explicitly incomplete values allowed by the State 1
   draft models.
3. Saving a draft does not mint an accepted snapshot.
4. Saving a draft does not publish anything to Platform Hub.
5. Discarding an unpublished draft does not remove accepted/published history.

## Acceptance

1. Acceptance creates a new immutable Room Planner snapshot with a stable
   `snapshot_id`.
2. Acceptance is atomic: failure leaves no partially accepted snapshot.
3. A snapshot never changes after acceptance.
4. A later correction/change creates a later draft and later snapshot rather
   than editing the prior snapshot.
5. Every accepted snapshot is internally self-consistent for its included stage
   scope even when a separate takeoff is not yet available.
6. Fields that mean "unresolved draft choice" MUST NOT survive into an accepted
   snapshot when their accepted model shape requires a concrete value.

## Publication

1. Platform Hub publication is separate from acceptance.
2. Only an accepted immutable Room Planner result may be the source of a normal
   Platform Hub publication.
3. Preview, save, and acceptance MUST NOT implicitly publish.
4. Publish remains an explicit two-step confirmed product action as established
   by State 0.
5. Failed Hub publication leaves the Room Planner snapshot accepted but
   unpublished; the application MUST NOT report success.
6. A Hub publication records/resolves Hub-visible artifact identity and
   provenance; a private `snapshot_id` alone is not cross-service provenance.
7. Publishing a later snapshot never rewrites an earlier Hub publication.

---

# 3. Snapshot basis graph invariants

1. `DemolitionPlanDraft` and `DemolitionPlanSnapshot` reference exactly one
   `ExistingSnapshotRef` basis.
2. `ConstructionPlanDraft` and `ConstructionPlanSnapshot` reference exactly one
   `ExistingSnapshotRef` basis.
3. Construction may reference `DemolitionSnapshotRef | None`.
4. If Construction references a Demolition snapshot, that Demolition snapshot
   MUST itself reference the same Existing snapshot as Construction.
5. A durable basis reference never points to a mutable draft.
6. A basis ref never auto-resolves to "latest".
7. Historical basis refs remain resolvable even when newer snapshots exist.
8. Carry-forward creates a new draft with new basis refs; it never patches the
   basis refs of an old snapshot.
9. Construction carry-forward that depends on Demolition occurs only after the
   target Demolition basis is itself resolved/accepted against the target
   Existing basis.

---

# 4. Canonical geometry and identity rules

## Coordinates

1. Domain plan coordinates are expressed in real-world millimeters using
   `Decimal` values.
2. Screen pixels, viewport transforms, zoom, and pan are never domain
   coordinates.
3. The domain does not infer entity identity from coordinate proximity.
4. Stable entity identity is expressed by ids and accepted correction lineage,
   not by "nearest geometry" heuristics.
5. Two distinct vertices in one source level MUST NOT occupy the exact same
   canonical coordinate; connected walls reuse the same `vertex_id`.
6. No implicit geometric epsilon changes identity. If a later import/measurement
   workflow needs tolerance-based snapping, that tolerance is an explicit
   authoring/import policy and does not redefine stored identity.

## Vertices and walls

1. `vertex_id` is unique inside its owning level/source plan.
2. Every wall endpoint references an existing vertex in that same level/source
   plan.
3. A wall's start and end vertices are different.
4. Wall length is strictly positive.
5. Wall thickness is strictly positive.
6. Within one source plan, duplicate/overlapping wall segments representing the
   same physical boundary are invalid rather than silently stacked.
7. Intersecting wall centerlines that form one connected physical junction must
   share explicit topology rather than crossing as unrelated decorative lines.
8. Construction-wall geometry may overlap Existing geometry only when the
   renovation semantics explicitly require a resulting replacement/adjacent
   construction; semantic stage separation is not a license for contradictory
   Proposed solids.

Exact computational-geometry predicates belong to the future geometry owner,
but implementations MUST enforce these invariants deterministically.

---

# 5. Existing opening and opening-element invariants

1. `ExistingOpening` is an aperture hosted by exactly one Existing wall in the
   same level.
2. Opening width and height are strictly positive.
3. `sill_height_mm >= 0`.
4. The aperture's wall-relative horizontal extent must lie inside its host wall.
5. The aperture's vertical extent must lie inside the applicable Existing wall
   face envelope derived from floor/ceiling geometry.
6. `ExistingOpeningElement` references an Existing opening in the same level.
7. An Existing opening has at most one modeled installed opening element in the
   initial product.
8. `OpeningElementKind.door` is compatible with `OpeningUseKind.doorway`.
9. `OpeningElementKind.window` is compatible with
   `OpeningUseKind.window_opening`.
10. `unframed_opening` has no installed `ExistingOpeningElement`.
11. Removing an opening element does not itself remove or close the aperture.
12. Removing an entire host wall removes its aperture topology in the derived
   demolition/result composition without requiring fake aperture-delete items.

---

# 6. Construction opening lifecycle rules

## Create

1. `CreateConstructionOpening` creates one positive resulting aperture identified
   by `result_opening_id`.
2. If its host is a new Construction wall, no Existing demolition cut is
   required merely to form the aperture.
3. If its host is a retained Existing wall, acceptance requires a compatible
   `NewWallOpeningCut` in the referenced Demolition basis whenever Existing wall
   material must be removed.
4. The resulting profile must fit the resulting host-wall geometry.

## Alter

1. `AlterExistingOpening.source` resolves to one opening in the exact Existing
   basis.
2. Identity-preserving alteration remains on the same semantic Existing host
   wall.
3. Moving an opening to another wall is represented as close old + create new,
   not as identity-preserving alteration.
4. If the target profile requires removal of Existing wall material beyond the
   old aperture, acceptance requires compatible
   `ExistingOpeningEnlargementCut` intent in the Demolition basis.
5. If any part of the old aperture must become solid wall in the target result,
   `infill_system_ref` is required before acceptance.
6. If no infill is physically required, `infill_system_ref` may remain `None`.
7. A changed Existing opening with an installed door/window element requires
   explicit demolition of that existing element when the old element cannot
   physically remain through the change; Room Planner MUST NOT silently assume
   it vanished.

## Close

1. `CloseExistingOpening` produces no Proposed opening.
2. `infill_system_ref` is mandatory.
3. If the Existing opening has an installed door/window element, acceptance of
   a coordinated closure requires explicit removal of that element in the
   Demolition basis.
4. Closing an aperture is Construction work; it is not modeled as deletion from
   Existing or as a demolition-only operation.

## Composition

1. An unchanged Existing aperture appears once in Proposed.
2. A created Construction opening appears once in Proposed.
3. An altered Existing aperture supersedes its old aperture and appears once as
   the Construction result.
4. A closed Existing aperture does not appear in Proposed.
5. Demolition cuts are evidence of removed material, not positive Proposed
   apertures.

---

# 7. Room derivation rules

1. `Room` is derived from physical Room Planner topology; it is not arbitrary
   user-drawn metadata.
2. Room boundary faces must form one deterministic closed boundary according to
   the geometry owner.
3. Room area and perimeter are derived, not independently editable values.
4. Room interiors on one level do not overlap except at shared boundaries.
5. A doorway/window aperture in a physical wall does not by itself eliminate the
   semantic room boundary represented by that wall.
6. Open-plan areas with no physical separating Room Planner boundary remain one
   spatial room in the initial model.
7. The initial product has no virtual/invisible zoning boundary that creates a
   second Room entity.
8. Localized floor/ceiling/treatment polygons do not become rooms merely because
   they subdivide a surface for work intent.

If a later product requirement needs non-physical zones, it requires a new model
concept rather than relaxing `Room` into a generic polygon.

---

# 8. Vertical survey and elevation-surface invariants

## Existing survey

1. All comparable elevations inside one object use the same `ProjectDatum`
   identity unless a future explicit conversion model is introduced.
2. `ExistingVerticalSample.floor_elevation_mm` is measured relative to the
   project datum.
3. `ExistingVerticalSample.clear_height_mm > 0`.
4. For every complete sample:

```text
ceiling_elevation_mm = floor_elevation_mm + clear_height_mm
```

5. Accepted Existing vertical samples are complete; draft samples may be partial
   only according to the draft model.
6. Sample coordinates are unique in one accepted vertical grid.
7. Missing measurements remain missing; Room Planner MUST NOT invent measured
   values merely to complete a surface.

## Elevation surfaces

1. `ConstantElevationSurface` is valid only when the user/domain intent truly
   defines a constant target/result; it is not an automatic fallback for an
   incomplete measured grid.
2. An `ElevationSurfaceSet` may contain several explicit patches, but overlap,
   precedence, gap handling, continuity, and interpolation require one
   deterministic policy before accepted derived quantities may depend on them.
3. Existing measured surface reconstruction, post-demolition derived surfaces,
   and Construction target surfaces remain semantically distinct even when they
   share compatible value shapes.

### State 2 open policy: vertical reconstruction

The following still requires an explicit decision before State 2 stabilizes:

- how grid samples are interpolated;
- what happens outside the measured sample hull;
- whether missing local samples block only the affected area or the whole
  requested calculation;
- how overlapping target patches compose;
- how discontinuities/steps are represented rather than accidentally smoothed.

No implementation may choose these silently.

---

# 9. Existing correction lineage invariants

1. `ExistingCorrectionLineage` connects exactly one accepted Existing snapshot
   to one later accepted Existing snapshot.
2. Lineage records semantic identity evidence; it is not renovation Demolition.
3. Preserved lineage maps one entity to exactly one same-kind successor.
4. Split lineage maps one source to at least two same-kind successors.
5. Merged lineage maps at least two same-kind sources to one successor.
6. Removed lineage has no successor.
7. Added lineage has no source.
8. Within one correction pair, a source entity cannot simultaneously be
   preserved and removed/split/merged in contradictory relations.
9. A target entity cannot be claimed as unrelated successors by contradictory
   lineage relations.
10. All dependency-relevant Existing entities whose identity changes between the
    two snapshots must have explicit lineage; carry-forward never fills a missing
    relation by nearest-coordinate guessing.
11. Opening-element lineage follows the same rules when dependent Demolition
    targets the installed physical element.

---

# 10. Carry-forward rules

1. Carry-forward consumes accepted source snapshot(s), accepted target Existing
   snapshot, and accepted Existing correction lineage.
2. It produces a new draft; it never mutates the source snapshot.
3. Preserved identity may be mapped automatically only after the carried intent
   is revalidated against target geometry.
4. Removed target → `MissingTargetConflict`.
5. Split/otherwise non-unique successor → `AmbiguousTargetConflict` unless the
   dependent intent itself has a deterministic one-to-many meaning explicitly
   defined by a later rule.
6. Preserved target whose relative geometry no longer fits →
   `InvalidRelativePlacementConflict`.
7. Changed host relation that invalidates meaning →
   `InvalidHostRelationshipConflict`.
8. Surface/room topology that no longer maps uniquely →
   `InvalidSurfaceTargetConflict`.
9. The carry-forward engine MUST NOT choose one candidate solely because it is
   geometrically closest.
10. Non-conflicting automatic carry-forward is still draft state and requires
    user acceptance before becoming a snapshot.

---

# 11. Construction Catalog and accepted Construction invariants

1. Construction Catalog technical facts are external versioned data resolved
   through the Platform Hub boundary.
2. A `ConstructionSystemRef` always identifies an exact system in an exact
   catalog revision.
3. Historical snapshots never rebind a system ref to a newer catalog revision.
4. Every accepted `ConstructionWall` has a non-null system ref.
5. Draft wall geometry may have `system_ref = None`; acceptance may not.
6. Every accepted Construction treatment has a concrete system ref.
7. Opening infill has a concrete system ref whenever infill is required.
8. If a Construction snapshot contains any catalog-backed system refs, its
   `catalog_ref` must identify the same exact catalog revision used by those
   refs.
9. One accepted Construction snapshot MUST NOT mix system refs from different
   catalog revisions.
10. Wall thickness and the selected wall system must be mutually compatible.
    The selected system/catalog rules are not allowed to silently override an
    incompatible spatial thickness, and Room Planner must not silently rewrite
    the user's geometry to fit a system.
11. If required catalog data cannot be resolved, affected calculations remain
    unavailable/incomplete; no technical fallback constant is fabricated.

---

# 12. Takeoff invariants and unit policy

## Scope and provenance

1. Every final takeoff line is explicitly demolition or construction scope.
2. Demolition and Construction quantities are never merged merely because they
   use the same unit/material wording.
3. Every line has typed Room Planner source provenance from the exact snapshot
   carried by the takeoff basis.
4. A line source from another snapshot is invalid.
5. Catalog-backed Construction quantities pin the exact Construction Catalog
   revision.
6. Prices, currency, labor cost, commercial package counts, discounts, and
   commercial whole-package rounding are forbidden.

## `PhysicalMeasure` compatibility policy

The initial closed dimension/unit compatibility table is:

| dimension | allowed unit |
| --- | --- |
| `length` | `m` |
| `area` | `m2` |
| `volume` | `m3` |
| `mass` | `kg` |
| `count` | `piece` |

A new unit requires a real domain/catalog need and an explicit model/rule update.

Final takeoff measure values are non-negative. Zero-contribution intermediate
results may occur during calculation, but final deterministic output SHOULD omit
zero-value lines unless a later downstream contract proves that explicit zero
rows carry required meaning.

## Determinism

Equal accepted basis snapshots + equal catalog revision + equal rule versions
must produce semantically equal takeoff output.

Final line ordering must be deterministic and must not depend on dictionary,
database, or traversal accident. The exact canonical sort/aggregation key is a
remaining State 2 decision because it depends on the final calculation-line
aggregation policy.

### State 2 open policy: quantity calculation

Before State 2 stabilizes, Room Planner still needs explicit calculation policy
for at least:

- gross versus net wall-face area rules around openings;
- wall/drywall component quantities;
- plaster/putty/paint consumption application;
- floor fill/leveling volume from source and target surfaces;
- ceiling treatment quantities;
- demolition length/area/volume selection per demolition meaning;
- deterministic aggregation key and rounding/precision for engineering
  quantities (not commercial package rounding).

These values/formulas must use Construction Catalog technical data where owned by
that catalog and MUST NOT be hidden in prose defaults.

---

# 13. Browser preview and transient editor invariants

1. Browser viewport, zoom, pan, hover, selection, handles, guides, snap previews,
   drag ghosts, and temporary what-if geometry are transient frontend state.
2. Transient editor state is never included in an accepted Room Planner snapshot
   or Platform Hub artifact merely because it is visible on screen.
3. Browser rendering is a projection of authoritative domain geometry; rendered
   SVG/Canvas/WebGL shapes are not a second source of spatial truth.
4. During a preview, the browser may display derived Proposed geometry,
   quantities, clear heights, and validation consequences without mutating the
   accepted basis.
5. A preview becomes working domain state only through an explicit confirmed
   editor action.
6. Confirming an editor action mutates the working draft, not an accepted
   snapshot in place.
7. Save, accept, and publish remain distinct operations in the UI and domain.

Shared frontend/editor architecture continues to follow
[FRONTEND_EDITOR.md](../../FRONTEND_EDITOR.md).

---

# 14. Determinism and ordering invariants

1. Lists whose order has domain meaning preserve that meaning explicitly.
2. Collections whose order has no domain meaning must receive a canonical
   deterministic ordering before hashing, comparison, snapshot serialization,
   artifact generation, or takeoff output.
3. Generated ids MUST NOT depend on Python object address, unordered iteration,
   or browser render order.
4. Historical snapshot serialization must be stable enough that semantically
   equal content does not change merely because a database returned rows in a
   different order.
5. Proposed composition from the same exact bases and same rules must be
   semantically deterministic.

Exact canonical serialization/hashing belongs to later contract/implementation
work unless Platform Hub schema identity requires an earlier shared decision.

---

# 15. Platform Router impact

This initial State 2 slice introduces no new Platform Hub mechanism.

It consumes the already accumulated shared requirements in
[PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md):

- Registry object identity;
- exact Construction Catalog revision resolution;
- artifact publication separate from private drafts;
- immutable publication history;
- exact basis/provenance links;
- Hub-resolvable publication/artifact provenance.

Room Planner geometry validity, stage acceptance, carry-forward, opening
lifecycle, quantity calculation, and browser preview policy remain application
domain responsibilities and MUST NOT migrate into Platform Hub business logic.

---

# 16. State 2 open decisions

State 2 is **not stabilized yet**. The main remaining rule/policy decisions are:

1. vertical-grid interpolation, extrapolation, steps/discontinuities, and patch
   precedence;
2. detailed physical quantity formulas and Construction Catalog parameter use;
3. engineering quantity precision/rounding and canonical aggregation/order;
4. exact deterministic room/topology derivation rules where the conceptual
   invariants above are insufficient for implementation;
5. any acceptance/publication eligibility rule exposed by those calculations
   that cannot be expressed with the current State 1 models.

If resolving one of these requires inventing a new domain entity/field rather
than a rule, return to State 1 and repair the model before continuing.
