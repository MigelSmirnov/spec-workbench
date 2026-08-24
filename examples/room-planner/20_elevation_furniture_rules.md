# Room Planner — State 2: Wall Elevation and Furniture Layout Rules

> Status: accepted State 2 refinement.
>
> This document defines projection, editing, basis, and furniture-placement rules
> for `00_elevations_furniture.md` and `10_elevations_furniture.md`.

## 1. Wall-face elevation is a projection

1. A wall elevation is derived from one exact selected wall face and the same
   canonical Room Planner working/accepted state used by plan view.
2. The elevation does not own duplicate wall, opening, niche, door, ceiling, or
   furniture entities.
3. Editing in elevation applies typed application/domain changes to canonical
   data and then both plan/elevation views reproject.
4. Closing or reopening the elevation view cannot lose or create project data.
5. Pan/zoom/crop/view orientation are transient editor state unless a later saved
   view feature explicitly persists them.

## 2. Canonical face-local coordinate rule

For a directed wall `start → end`, use conceptual face-local coordinates:

```text
u = distance along wall start → end
z = project vertical/elevation axis
```

Rules:

1. Wall-relative offsets remain measured from canonical wall start.
2. Vertical project/surface calculations use the project datum/elevation axis.
3. Fields already defined as height above local floor (for example sill or
   furniture bottom height) retain that domain meaning; the elevation renderer
   resolves them to `z` using the applicable floor surface.
4. A renderer may visually mirror/reorient the elevation so the selected face is
   convenient to read, but such mirroring is a view transform only.
5. View mirroring MUST NOT mutate wall direction, `WallSide`, door `DoorSwing`,
   niche side, opening offset, or furniture wall offset.

## 3. Cross-view edit consistency

1. The same entity id/ref is used in plan and elevation.
2. Selecting an entity in either view may synchronize selection in the other
   view without introducing another domain identity.
3. A confirmed direct-manipulation edit must resolve to one typed canonical
   change before entering history/undo.
4. Undo/redo applies to the canonical command, not independently to each view.
5. Preview geometry may differ per view but must originate from the same candidate
   domain values.

## 4. Vertical dimension editing

1. Direct elevation handles may propose vertical values such as opening sill,
   opening height, niche sill/height/depth, furniture bottom height, or furniture
   height.
2. Snapping/readout may operate in face-local/elevation coordinates.
3. A drag handle has no authority to silently invent a missing domain value on
   confirmation; the resulting typed command must explicitly carry the value.
4. Where a source floor/ceiling varies spatially, user-facing relative height and
   absolute elevation must be derived consistently from the exact local surface.
5. Validation failures remain visible as preview/conflict state and do not become
   accepted geometry.

## 5. Furniture basis coherence

1. A `FurnitureLayoutDraft`/snapshot uses exact Existing/Demolition/Construction
   basis refs.
2. If a Demolition basis is present, it must be based on the same Existing basis.
3. If a Construction basis is present and itself uses Demolition, the furniture
   layout basis graph must match it coherently.
4. Furniture never binds to a mutable external stage draft as its accepted basis.
5. Correcting/rebasing Room Planner geometry does not silently retarget accepted
   furniture layout snapshots.
6. Carrying a furniture layout to a new plan basis is explicit and must surface
   placements whose host wall/room no longer resolves.

Exact furniture carry-forward conflict variants may reuse the established
missing/ambiguous/invalid-host concepts when implementation reaches that flow;
State 2 does not introduce a generic free-form conflict payload.

## 6. Floor furniture placement

1. `position` must resolve inside the declared room's applicable Proposed floor
   region for an accepted layout.
2. `bottom_offset_mm >= 0`.
3. The floor-supported base elevation is derived from the exact floor surface at
   the placement anchor plus the offset.
4. The furniture envelope is real-world project data and remains positive in all
   dimensions.
5. Rotation is interpreted in plan/world coordinates and normalized according to
   the later canonical angular precision policy.
6. The SVG/Canvas asset's own bounds do not redefine placement dimensions.

## 7. Wall-mounted furniture placement

1. The target wall face must resolve in the exact layout basis.
2. `offset_from_wall_start_mm >= 0` and the placement width must fit the
   applicable wall-face horizontal extent under the canonical anchor convention.
3. `bottom_height_mm >= 0`.
4. The vertical envelope must fit the applicable room-facing wall/ceiling
   envelope if the UI presents an accepted-valid placement.
5. `depth_mm` extends into the room from the targeted face; it must not be
   interpreted relative to screen orientation.
6. Reversing canonical host-wall direction requires deterministic transformation
   of wall-relative furniture offsets just as other wall-hosted geometry does.

## 8. No automatic furniture-domain verdict

1. Room Planner may display dimensions, overlaps, and geometric relationships as
   editor information.
2. It MUST NOT automatically claim that a furniture layout satisfies ergonomic,
   manufacturing, electrical, plumbing, fire, code, or installation requirements
   unless an explicit later domain rule owns that claim.
3. A geometric collision highlight may be introduced as an editor aid, but it
   must be labeled/defined as such rather than treated as a comprehensive fit
   decision.
4. Furniture does not create Room Planner takeoff quantities in the initial
   product.

## 9. Definition revision and reproducibility

1. Every accepted furniture placement pins an exact `FurnitureDefinitionRef`.
2. The referenced definition revision supplies validated renderer/capability
   metadata, not project placement truth.
3. A library asset update under a new revision must not silently change the
   semantic identity/dimensions of an old accepted placement.
4. Historical rendering should resolve the pinned definition revision or fall
   back to a neutral physical-envelope representation if the renderer asset is
   unavailable; it must not bind to "latest" silently.

## 10. Multi-view renderer rule

1. One furniture placement may project through different block assets in plan,
   front elevation, and side elevation.
2. Changing view does not change placement identity.
3. Renderer asset choice is derived from definition capability + viewing
   orientation.
4. If a view-specific asset is unavailable, a neutral envelope projection may be
   used.
5. Renderer fallback MUST NOT fabricate physical details absent from the domain or
   definition metadata.

## 11. Interaction with doors/niches/ceiling geometry

1. Elevation must show canonical opening/niche dimensions and door swing using
   the already accepted rules.
2. Ceiling-box/niche intersections with the selected wall face are derived and
   may be displayed as profile/height lines.
3. Furniture remains an auxiliary layer; it may visually overlap those domain
   features for planning, but overlap alone does not mutate construction intent.
4. A user may use the elevation to adjust construction or furniture independently
   through their owning typed commands.

## 12. Platform Router impact

No new Platform Hub mechanism is required. Wall elevation and furniture layout
remain Room Planner/editor concerns until a later publication contract exposes
an auxiliary layout layer.
