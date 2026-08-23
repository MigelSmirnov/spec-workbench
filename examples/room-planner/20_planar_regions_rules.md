# Room Planner — State 2: Planar Region Construction Rules

> Status: accepted State 2 refinement.
>
> This document defines rules for the planar floor-build-up and ceiling-box
> models introduced by `00_planar_regions.md` and `10_planar_regions.md`.

## 1. Vertical parameter semantics

1. `FloorBuildUpIntent.thickness_mm` is a vertical construction thickness along
   the project elevation axis.
2. `ConstructionCeilingBox.drop_height_mm` and
   `ExistingCeilingBox.drop_height_mm` are vertical drops along the same project
   elevation axis.
3. These values are not distances measured normal to an arbitrarily sloped
   surface.
4. The browser may display local/derived heights in different views, but it MUST
   NOT reinterpret the stored vertical parameter according to camera or surface
   orientation.
5. Accepted thickness/drop values are strictly greater than zero.

## 2. Footprint validity

1. A floor-build-up or ceiling-box footprint is a valid `PlanPolygon` under the
   canonical polygon rules.
2. The footprint belongs to exactly one level and declared room scope.
3. The accepted footprint must lie within the applicable physical room region.
4. A region may touch the room boundary.
5. A footprint crossing into another room is invalid unless a later model
   explicitly introduces a multi-room construction region.
6. Polygon render handles/vertices are editor projections of the canonical
   footprint, not separate persistent geometry.

## 3. Floor build-up source and target surface

The source for a Construction floor-build-up region is the exact floor surface
resolved from the Construction basis immediately before that build-up is
applied:

```text
Existing floor
    - applicable Demolition/removal result
        = source prepared/substrate surface
```

For every plan position `p` inside the footprint where the source elevation is
defined:

```text
target_floor_elevation(p)
    = source_floor_elevation(p) + thickness_mm
```

Rules:

1. The build-up does not silently flatten an existing slope; constant thickness
   follows the source surface vertically.
2. If the source surface is undefined over any required part of the footprint,
   the region is incomplete/invalid for acceptance and quantity calculation.
3. Different adjacent regions may use different explicit thicknesses and may
   therefore intentionally create a step/discontinuity at their shared boundary.
4. Such a discontinuity is explicit construction intent because it follows from
   region geometry + entered thickness; it is not interpolation noise.
5. Overlapping accepted floor-build-up footprints on the same source surface are
   invalid in the initial product because no stacking/precedence relation is yet
   modeled.
6. A future stacked-layer workflow requires an explicit ordered model rather than
   relying on collection order.

## 4. Floor build-up physical volume

Because `thickness_mm` is a constant vertical offset over the plan footprint, the
geometric build-up volume is deterministic from plan area and thickness:

```text
volume_mm3 = footprint_plan_area_mm2 * thickness_mm
```

Converted engineering output may be expressed in `m3` according to the existing
unit policy.

The Construction Catalog may add system-specific consumption/density/component
rules, but it does not replace the Room Planner-owned geometric volume.

No package count, commercial reserve, price, or labor calculation is introduced.

## 5. Ceiling-box base and underside surface

A Construction ceiling box is resolved against the applicable base ceiling
surface before that box is applied.

For every position `p` inside the footprint where base ceiling elevation is
defined:

```text
box_underside_elevation(p)
    = base_ceiling_elevation(p) - drop_height_mm
```

Rules:

1. The box follows the base ceiling's local variation while remaining a constant
   vertical drop below it.
2. If the base ceiling surface is undefined over part of the footprint, the box
   is incomplete/invalid for acceptance.
3. The resulting clear height below the box is derived against the applicable
   floor surface and must remain observable to the user.
4. Accepted Construction box footprints do not overlap one another in the
   initial product; nested/stacked boxes require an explicit later stacking
   relation rather than implicit ordering.
5. Adjacent boxes may share boundaries when their geometry remains valid.

## 6. Ceiling-box vertical side faces

The vertical side faces are derived along the footprint boundary between the base
ceiling and the lowered underside.

For constant vertical drop:

```text
side_face_area
    = footprint_plan_perimeter * drop_height
```

for the complete exposed perimeter before any later adjacency/occlusion rule.

The underside surface area is the derived surface area of the base ceiling patch
translated downward by `drop_height_mm`; it is not automatically assumed equal
to plan area when the base surface is sloped/non-planar.

Exact handling of shared/hidden side faces between adjacent constructions is a
geometry rule and must not depend on renderer overdraw.

## 7. Existing and Demolition box rules

1. An accepted Existing ceiling box has explicit measured `drop_height_mm`.
2. Unknown Existing box height may exist only in working draft form.
3. Removing an Existing ceiling box through `RemoveExistingCeilingBox` removes
   that box geometry from the derived post-demolition ceiling result.
4. Demolition removal does not automatically create a new Construction box.
5. Existing correction lineage governs whether a dependent demolition target can
   carry forward to a corrected box identity.

## 8. Construction completeness

An accepted `FloorBuildUpIntent` requires:

- valid room/footprint;
- explicit `thickness_mm > 0`;
- exact `ConstructionSystemRef`;
- resolvable source floor surface over the complete footprint.

An accepted `ConstructionCeilingBox` requires:

- valid room/footprint;
- explicit `drop_height_mm > 0`;
- exact `ConstructionSystemRef`;
- resolvable base ceiling surface over the complete footprint.

A renderer default, last-used property value, or palette preset MUST NOT silently
satisfy a missing domain field unless the user explicitly applies that value to
the working draft.

## 9. Proposed composition

1. Proposed floor surface includes accepted floor-build-up offsets over their
   footprints.
2. Proposed ceiling geometry includes retained Existing boxes plus accepted
   Construction boxes, excluding Existing boxes removed by Demolition.
3. Proposed side/underside geometry is derived from canonical region data and
   exact bases.
4. Region fills/hatches/contours have no authority over Proposed composition.

## 10. Browser preview

The browser may preview:

- polygon editing;
- thickness/drop labels;
- target elevation consequences;
- local clear height;
- floor volume;
- box underside/side-face areas;
- validation conflicts.

Preview values remain transient until a confirmed application command updates
the working draft.

The generic region editor may own polygon editing/snapping mechanics but MUST NOT
choose the semantic operation or fabricate thickness/drop/system values.

## 11. State 2 quantity-policy effect

This refinement closes part of the broader quantity policy left open in
`20_rules.md`:

- floor build-up geometric volume is explicitly based on footprint plan area ×
  vertical thickness;
- ceiling-box underside/side geometry is explicitly derived from footprint,
  base ceiling surface, and vertical drop.

Construction Catalog consumption rules, finish treatment quantities, and
canonical engineering rounding remain governed by the remaining State 2 work.

## 12. Platform Router impact

No new Platform Hub mechanism is required. These are Room Planner domain rules.
