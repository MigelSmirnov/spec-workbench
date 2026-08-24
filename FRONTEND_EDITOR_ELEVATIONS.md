# Frontend Editor — Wall Elevations and Multi-View Block Refinement

> Status: accepted Architecture v0 refinement.
>
> This document refines `FRONTEND_EDITOR.md` using the Room Planner case as
> evidence for coordinated plan/elevation views and reusable frontend block
> definitions with multiple renderer projections. Generic block overlays are
> frontend/editor state; they do not become every planner backend's domain data.

## 1. One domain scene, multiple coordinated views

Engineering planners may need several view projections over the same canonical
owned state.

For Room Planner the minimum pair is:

```text
Plan View
Wall-Face Elevation View
```

These are not separate documents or independent domain scene models.

```text
planner-owned canonical state
        ├── plan projection
        └── elevation projection
```

Shared editor infrastructure should therefore treat `view` as a projection
capability over stable owned entity references, not as a separate source of
identity.

## 2. Wall-face elevation viewport

A wall elevation is bound to a semantic wall face supplied by the building/Room
Planner layer.

The reusable building layer should be able to project:

- wall-face bounds and finishable area;
- floor and ceiling profile lines;
- openings and opening elements;
- door swing/front projection where meaningful;
- wall niches;
- intersections of ceiling boxes/niches/lowered regions with the face;
- dimensions/anchors.

Other frontend-only overlay layers may be composited into the same viewport, but
they do not thereby become building/Room Planner domain entities.

## 3. Face-local geometry versus viewport geometry

A building layer may expose a face-local projection coordinate system such as:

```text
u = along canonical wall axis
z = project vertical axis
```

The renderer may map `u/z` to viewport `x/y`, including mirroring for readability.
That renderer transform must be explicit and reversible.

Pointer input for planner-owned entities follows:

```text
viewport x/y
    ↓ inverse view transform
face-local u/z
    ↓ host/layer command mapping
canonical planner-domain value
```

No mirrored Canvas/SVG coordinate is persisted as if it were canonical wall
orientation.

## 4. Shared selection across views

Planner-owned selection uses stable semantic refs so plan and elevation can
synchronize.

```text
select wall-face niche N7 in plan
        ↓
open/select N7 in elevation
```

Frontend-only overlays may also have editor-layer selection ids so the same
visual overlay can be selected in plan/elevation. Those ids are explicitly not
planner-domain refs.

Scene projection instances created for rendering/performance must not become
canonical project identities.

## 5. Multi-view block definition

Reusable frontend blocks may support multiple renderer assets under one library
definition.

Conceptually:

```text
BlockDefinition
    id
    revision
    title/category
    default visual/spatial envelope
    anchors/capabilities
    views:
        plan
        front_elevation
        optional side_elevation
        optional other proven views
```

Each view entry references a validated renderer asset (for example SVG) plus the
local coordinate/bounds metadata required to place it deterministically.

The palette sees definition metadata/capabilities. It does not parse SVG path
structure to discover semantics.

## 6. Frontend overlay placement is not planner backend data

For generic visual/layout aids such as furniture, the shared editor may create a
frontend overlay placement that references one exact block definition and stores
enough editor-space/world-space placement data to render consistently across
views.

Conceptually, not as a planner-domain contract:

```text
FrontendBlockOverlay
    overlay_id
    definition_ref
    placement/envelope
    optional wall-face attachment for elevation projection
```

The exact frontend IR shape is deferred.

Critical ownership rule:

- `FrontendBlockOverlay` is not automatically serialized into Room Planner,
  Plumbing Planner, Electrical Planner, or another application backend;
- it is not automatically part of that planner's accepted snapshots/artifacts;
- the shared frontend library may be reused by every planner without forcing all
  backends to understand furniture or other foreign visual aids.

If a block corresponds to a planner-owned domain entity, the direction reverses:
the planner domain owns the entity/placement and the shared block library merely
renders it.

## 7. One frontend overlay, many visual assets

A frontend overlay placement may use different view assets without duplicating
the overlay:

```text
frontend overlay P7
    → plan asset in plan view
    → front/side asset in elevation view
```

Changing view is asset/projection selection only.

For planner-owned domain entities, the same rule applies to rendering, except the
placement comes from the owning domain model rather than frontend overlay state.

## 8. Neutral fallback projection

A reusable block library will not always have every view asset immediately.

When a compatible view-specific asset is missing, the editor may render a neutral
envelope projection if sufficient definition/overlay dimensions are available.

```text
plan fallback       → rectangle footprint
front fallback      → width × height rectangle
side fallback       → depth × height rectangle
```

Fallbacks must not fabricate engineering facts such as door handing, plumbing
ports, cabinet internals, or manufacturer-specific geometry.

## 9. Block library authoring by agents

The multi-view design intentionally supports agent-authored libraries.

```text
block definition / reference image
        ↓
agent creates/refines plan.svg + front.svg (+ side.svg)
        ↓
validate SVGs + manifest
        ↓
versioned frontend block definition
        ↓
palette exposes it automatically
```

The application palette remains independent from asset internals. Adding a new
validated view asset should not require custom React palette code.

## 10. Furniture is a frontend-only first consumer

Furniture/layout blocks are a strong first consumer of this shared capability
because the same visual item is useful in plan and elevation.

In the current architecture they are generic frontend overlays, not Room Planner
backend/domain entities.

This means a Room Planner user may place a sofa/cabinet visually for planning
without creating:

- Room Planner Pydantic models;
- Room Planner DB records;
- Room Planner basis/carry-forward relationships;
- `room_plan`/`room_takeoff` payload data;
- Room Planner furniture CRUD endpoints.

If a later owning application models kitchen/furniture semantics, it may reuse the
same blocks while keeping authoritative data in that owning application.

## 11. Frontend overlay persistence is separate architecture

The shared editor may initially keep generic overlays in browser/session/editor
state.

If durable cross-session or cross-device overlay persistence becomes required,
introduce an explicit shared-workspace owner/storage contract. Do not solve it by
silently extending every planner backend with foreign overlay fields.

This persistence decision remains open and does not block the reusable library or
basic layout aid.

## 12. Elevation direct manipulation

The reusable building/editor layer may own generic interaction mechanics such as:

- dragging vertical handles;
- dimension handles;
- rectangle/region editing on a wall face;
- face-local snapping;
- preview guides/readouts.

Planner-owned edits map through the host planner into typed domain/application
operations.

Frontend-only block movement remains an editor-overlay operation and must not call
a planner backend endpoint unless that planner explicitly owns the represented
concept.

## 13. Expected Room Planner elevation slice

A useful architecture spike should demonstrate:

1. select a wall face in plan and open its elevation;
2. render floor/ceiling profile and wall extent from canonical Room Planner
   geometry;
3. render one opening + door/window element;
4. edit sill/height through face-local preview and one Room Planner command;
5. render/edit one wall niche;
6. show a ceiling-box/lowered-ceiling intersection line;
7. place one generic frontend furniture overlay and show it in plan/elevation;
8. use plan/front SVG assets from one block definition;
9. fall back to an envelope rectangle when one asset view is absent;
10. prove that moving the generic furniture overlay creates **no Room Planner
    backend write**;
11. synchronize Room Planner-owned selection across views;
12. undo/redo a Room Planner canonical edit once, with both views updating.

## 14. Frontend IR consequence

Future frontend IR likely needs explicit concepts for:

- view definitions/capabilities;
- semantic view binding (for example selected wall face);
- projection registrations per view;
- planner-domain refs versus frontend-overlay refs;
- multi-view block renderer capabilities;
- overlay placement state;
- view-specific tools/bindings;
- explicit persistence ownership (`none/session/shared-workspace/domain-owner` or
  another proven closed model).

Do not encode repeated behavior as ad-hoc React page state, but also do not lower
frontend overlay schemas into planner backend domain models merely because the
workspace composes them visually.
