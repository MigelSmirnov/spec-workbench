# Room Planner — State 2: Ceiling and Wall Niche Rules

> Status: accepted State 2 refinement.
>
> This document defines validity, derived geometry, quantity separation, and
> browser-preview rules for the niche models introduced by `00_niches.md` and
> `10_niches.md`.

## 1. Recess depth semantics

1. `recess_depth_mm` is measured away from the room-facing host surface into the
   construction.
2. Accepted niche depth is strictly greater than zero.
3. The depth is canonical domain data and MUST NOT be inferred from renderer
   perspective, shadow, SVG geometry, or a palette preset.
4. Existing draft depth may remain unknown only where the corresponding draft
   model explicitly permits `None`.
5. Construction acceptance requires explicit depth and exact system reference.

---

## 2. Ceiling niche geometry

A ceiling niche is resolved against the applicable base room-facing ceiling
surface before the niche is applied.

For every position `p` inside the niche footprint where the base ceiling is
defined:

```text
niche_back_elevation(p)
    = base_ceiling_elevation(p) + recess_depth_mm
```

Rules:

1. Positive recess depth moves the niche back/upward away from the room.
2. The back surface follows local variation of the base ceiling while remaining a
   constant vertical offset above it.
3. The footprint must be valid and lie inside the applicable room ceiling region.
4. Undefined base-ceiling geometry anywhere required by the footprint blocks
   acceptance/calculation.
5. Ceiling niche footprints do not overlap other accepted ceiling niche
   footprints in the initial product unless a later explicit precedence/stacking
   model is introduced.
6. A niche may be adjacent to a lowered ceiling region/box. The resulting step
   geometry is derived from the exact neighboring surfaces rather than renderer
   draw order.

---

## 3. Wall niche geometry and through-wall guard

A wall niche is resolved on exactly one wall face.

Its face-local rectangle must satisfy:

```text
offset >= 0
width > 0
height > 0
sill_height >= 0
```

and must fit inside the applicable host wall-face extent.

For the initial product:

```text
0 < recess_depth_mm < host_wall_thickness_mm
```

The strict upper bound intentionally keeps a wall niche distinct from a through
opening. If the intended recess reaches/passes through the wall, the user/domain
must use the explicit opening lifecycle instead of silently reclassifying a
niche.

If later wall systems require a more precise residual-substrate rule than total
wall thickness, that technical constraint belongs to the exact Construction
Catalog/system rule and must tighten this invariant explicitly.

---

## 4. Separately derived niche geometry

Niche geometry must remain separately measurable even when the surrounding
surface receives the same finish system.

### Ceiling niche components

At minimum derive:

```text
mouth_plan_area
back_surface_area
transition_side_area
```

For a horizontal/constant-offset host patch, the transition side area is:

```text
footprint_plan_perimeter * recess_depth_mm
```

For a spatially varying host surface, exact side geometry is derived from the
host/back boundaries; renderer approximations are not authoritative.

### Wall niche components

For the initial rectangular wall niche derive:

```text
mouth_area
back_area
left_jamb_area
right_jamb_area
top_area
bottom_area
```

For a planar host wall face:

```text
mouth_area = width * height
back_area = width * height
left_jamb_area = recess_depth * height
right_jamb_area = recess_depth * height
top_area = recess_depth * width
bottom_area = recess_depth * width
```

The original unrecessed host-face contribution is reduced by `mouth_area`; the
niche internal faces are added as separate surface geometry.

---

## 5. Net finishable area and separate reporting

1. A retained/constructed niche changes the net finishable geometry of its host
   surface.
2. The host wall/ceiling surface MUST NOT count the niche mouth as if the original
   flat surface remained there.
3. Niche back/transition/jamb/top/bottom surfaces are calculated separately from
   the unrecessed host surface.
4. Takeoff may aggregate these surfaces when a construction system explicitly
   permits aggregation, but the calculation must retain typed niche provenance
   so the contribution can be reproduced/audited.
5. UI/specification outputs SHOULD be able to present niche quantities separately
   because the product workflow requires niches to be independently countable.
6. Separate reporting does not imply pricing/work-item ownership; PresuPro still
   owns commercial interpretation.

---

## 6. Existing and Construction composition

1. Retained Existing niches remain part of Proposed surface geometry.
2. New Construction niches contribute their derived recessed geometry to
   Proposed.
3. Closing/filling an Existing niche requires explicit Construction intent before
   the niche disappears from Proposed; an Existing snapshot is never edited away.
4. Creating a niche in retained Existing material may additionally require
   Demolition intent where material removal is part of the planned scope.
5. Construction positive geometry and Demolition material removal remain separate
   meanings even when they refer to the same intended niche location.

The exact demolition niche-cut variants remain a State 1 repair only when
separate demolition cut/volume output is required by the product workflow; no
implicit demolition is fabricated from Construction geometry.

---

## 7. Interaction with ceiling boxes / lowered regions

1. A ceiling niche and a ceiling box are opposite signed changes relative to
   their applicable base surface.
2. `ConstructionCeilingBox.drop_height_mm` lowers the room-facing surface.
3. `ConstructionCeilingNiche.recess_depth_mm` raises/recesses the room-facing
   surface.
4. Adjacent box/niche regions may form explicit vertical transition faces.
5. Overlapping box/niche regions require a deterministic base/precedence model;
   the initial product rejects ambiguous overlap rather than using collection or
   renderer order.

---

## 8. Browser preview and editing

The browser may preview:

- niche footprint/rectangle editing;
- depth labels;
- host surface subtraction;
- back/side-face derived geometry;
- local clear-height changes;
- separate component areas;
- validation such as wall-depth approaching through-opening thickness.

The generic building/editor layer may own snapping, face-local coordinate
conversion, selection handles, and derived display geometry. Room Planner owns
niche semantics, acceptance, system selection, and persistence.

---

## 9. Determinism

Equal host geometry + equal niche canonical input + equal rules must derive
semantically equal niche geometry and measurements.

Niche calculation must not depend on:

- SVG path shape;
- Canvas/Konva node geometry;
- viewport zoom;
- scene render order;
- arbitrary polygon traversal order where orientation has no domain meaning.

---

## 10. Platform Router impact

No new Platform Hub mechanism is introduced. Niche validation, derived geometry,
and physical quantity separation remain Room Planner domain responsibilities.
