# Room Planner — State 2: Wall Elevation Projection Rules

> Status: accepted State 2 correction/refinement.
>
> This document defines wall-elevation projection/editing rules and explicitly
> removes the earlier furniture-layout rules from Room Planner domain policy.
> Generic furniture/layout blocks belong to shared frontend/editor infrastructure.

## 1. Wall-face elevation is a projection

1. A wall elevation is derived from one exact selected wall face and the same
   canonical Room Planner working/accepted state used by plan view.
2. The elevation does not own duplicate wall, opening, niche, door, ceiling, or
   construction entities.
3. Editing Room Planner-owned geometry in elevation applies typed
   application/domain changes to canonical data and then both plan/elevation
   views reproject.
4. Closing or reopening the elevation view cannot lose or create Room Planner
   project data.
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
3. Fields defined as height above local floor retain that domain meaning; the
   elevation renderer resolves them to `z` using the applicable floor surface.
4. A renderer may visually mirror/reorient the elevation for readability, but
   mirroring is a view transform only.
5. View mirroring MUST NOT mutate wall direction, `WallSide`, `DoorSwing`, niche
   side, opening offset, or any other Room Planner-owned canonical geometry.

## 3. Cross-view edit consistency

1. The same Room Planner entity id/ref is used in plan and elevation.
2. Selecting an owned entity in either view may synchronize selection in the
   other view without introducing another domain identity.
3. A confirmed direct-manipulation edit must resolve to one typed canonical
   Room Planner change before entering history/undo.
4. Undo/redo applies to the canonical command, not independently to each view.
5. Preview geometry may differ per view but must originate from the same candidate
   domain values.

## 4. Vertical dimension editing

1. Direct elevation handles may propose Room Planner-owned vertical values such
   as opening sill, opening height, niche sill/height/depth, or other explicit
   vertical parameters owned by the selected domain concept.
2. Snapping/readout may operate in face-local/elevation coordinates.
3. A drag handle has no authority to silently invent a missing domain value on
   confirmation; the resulting typed command must explicitly carry the value.
4. Where a source floor/ceiling varies spatially, user-facing relative height and
   absolute elevation must be derived consistently from the exact local surface.
5. Validation failures remain preview/conflict state and do not become accepted
   geometry.

## 5. Frontend-only block overlay isolation

1. Generic furniture/layout blocks rendered by the shared frontend are not Room
   Planner domain entities.
2. Room Planner validation MUST NOT require, accept, snapshot, rebase, publish, or
   calculate takeoff from generic frontend overlay placement state.
3. Room Planner APIs MUST NOT gain furniture/layout CRUD merely because the
   browser workspace displays those overlays.
4. Frontend overlay ids are editor-layer identities and MUST NOT be accepted as
   Room Planner wall/opening/niche/source refs.
5. A reusable block library may consume Room Planner projection/snapping context
   without transferring data ownership to Room Planner backend.
6. If a different planner owns a block-like domain entity, that planner's rules
   own its validity and persistence even when the same shared renderer is reused.

## 6. Interaction with doors, niches, and ceiling geometry

1. Elevation must show canonical opening/niche dimensions and door swing using
   the already accepted rules.
2. Ceiling-box/niche intersections with the selected wall face are derived and
   may be displayed as profile/height lines.
3. Shared frontend overlays may visually overlap Room Planner geometry for human
   planning, but overlap alone does not mutate construction intent or create a
   Room Planner validation result.
4. Room Planner direct-manipulation commands operate only on concepts Room
   Planner owns.

## 7. Multi-view renderer boundary

Multi-view SVG/block behavior belongs to the shared frontend architecture, not to
Room Planner State 2 domain rules.

Room Planner only requires that renderer projections of its own domain concepts
remain derived from canonical state and that view transforms cannot change domain
meaning.

Generic block-library behavior, including plan/front/side assets and neutral
fallbacks, is defined in `../../FRONTEND_EDITOR_ELEVATIONS.md`.

## 8. No furniture basis/carry-forward rules

The earlier rules for `FurnitureLayoutDraft`, furniture basis coherence,
accepted furniture placements, and furniture carry-forward are withdrawn.

Those types are no longer Room Planner models, so Room Planner State 2 must not
validate or implement them.

If shared frontend overlay persistence later becomes necessary, its lifecycle and
reconciliation rules require an explicitly owned shared-workspace design.

## 9. Platform Router impact

No new Platform Hub mechanism is required.

Wall elevation remains a Room Planner editor projection. Generic frontend block
overlays are excluded from Room Planner publication/provenance rules.
