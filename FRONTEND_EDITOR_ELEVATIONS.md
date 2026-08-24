# Frontend Editor — Wall Elevations and Multi-View Block Refinement

> Status: accepted Architecture v0 refinement.
>
> This document refines `FRONTEND_EDITOR.md` using the Room Planner case as
> evidence for coordinated plan/elevation views and reusable block definitions
> with multiple renderer projections.

## 1. One domain scene, multiple coordinated views

Engineering planners may need several view projections over the same canonical
state.

For Room Planner the minimum pair is:

```text
Plan View
Wall-Face Elevation View
```

These are not separate documents or independent scene models.

```text
canonical planner/domain state
        ├── plan projection
        └── elevation projection
```

Shared editor infrastructure should therefore treat `view` as a projection
capability over stable entity references, not as a separate source of entity
identity.

## 2. Wall-face elevation viewport

A wall elevation is bound to a semantic wall face.

The reusable building layer should be able to project:

- wall-face bounds and finishable area;
- floor and ceiling profile lines;
- openings and opening elements;
- door swing/front projection where meaningful;
- wall niches;
- intersections of ceiling boxes/niches/lowered regions with the face;
- dimensions/anchors;
- furniture/layout blocks that belong to or are visible from the wall face.

The host planner owns which of those projections are editable and what a
confirmed edit means.

## 3. Face-local geometry versus viewport geometry

A building layer may expose a face-local projection coordinate system such as:

```text
u = along canonical wall axis
z = project vertical axis
```

The renderer may map `u/z` to viewport `x/y`, including mirroring for readability.
That renderer transform must be explicit and reversible.

Pointer input follows:

```text
viewport x/y
    ↓ inverse view transform
face-local u/z
    ↓ host/layer command mapping
canonical domain value
```

No mirrored Canvas/SVG coordinate is persisted as if it were canonical wall
orientation.

## 4. Shared selection across views

Selection should use stable semantic refs so plan and elevation can synchronize.

```text
select wall-face niche N7 in plan
        ↓
open/select N7 in elevation
```

and:

```text
select furniture P12 in elevation
        ↓
reveal/select P12 in plan
```

The scene may create separate projection instances for performance/rendering,
but those instances carry the same domain ref and must not become project
identity.

## 5. Multi-view block definition

Reusable engineering/furniture blocks should support multiple renderer assets
under one semantic definition.

Conceptually:

```text
BlockDefinition
    id
    revision
    title/category
    default physical envelope
    anchors/capabilities
    views:
        plan
        front_elevation
        optional side_elevation
        optional other domain-proven views
```

Each view entry references a validated renderer asset (for example SVG) plus the
local coordinate/bounds metadata required to place it deterministically.

The palette sees definition metadata/capabilities. It does not parse the SVG path
structure to discover geometry or semantics.

## 6. One placement, many visual assets

A project placement references one exact block-definition revision and owns its
canonical project geometry.

```text
project placement
    → plan renderer asset in plan view
    → front/side renderer asset in elevation view
```

Changing view is asset/projection selection only. It must not duplicate the
placement or alter canonical dimensions.

A block definition may have different SVG artwork for plan and elevation while
remaining one palette item and one semantic type.

## 7. Neutral fallback projection

A reusable block library will not always have every view asset immediately.

When a compatible view-specific asset is missing, the editor may render a
neutral physical-envelope projection if the canonical/definition dimensions are
known.

Examples:

```text
plan fallback       → rectangle footprint
front fallback      → width × height rectangle
side fallback       → depth × height rectangle
```

Fallbacks must remain visibly neutral and must not fabricate details such as door
handing, cabinet internals, plumbing ports, or manufacturer-specific geometry.

This lets agents/libraries improve block artwork incrementally without making
missing SVG files block basic spatial planning.

## 8. Block library authoring by agents

The multi-view design intentionally supports agent-authored libraries.

A typical authoring flow is:

```text
semantic block definition
        ↓
agent creates/refines plan.svg + front.svg (+ side.svg)
        ↓
validate each SVG + manifest
        ↓
versioned block definition
        ↓
palette automatically exposes supported views/capabilities
```

The application palette remains independent from asset internals. Adding a new
validated view asset should not require custom React palette code.

## 9. Furniture as first multi-view consumer

Furniture/layout blocks are a strong initial consumer because the same item is
useful in plan and wall elevation.

The block library may describe visual semantics and default envelope, while the
owning Room Planner placement keeps project position, orientation, dimensions,
and mounting/height data.

Furniture remains an auxiliary spatial layer; importing the library does not
make the shared frontend runtime responsible for furniture procurement,
manufacturing, estimating, or ergonomic rules.

## 10. Elevation direct manipulation

The reusable building/editor layer may own generic interaction mechanics such as:

- dragging vertical handles;
- dimension handles;
- rectangle/region editing on a wall face;
- face-local snapping;
- selecting/repositioning wall-mounted blocks;
- preview guides/readouts.

The host planner maps those proposals into typed domain/application operations.
Generic React/Konva code must not directly decide whether a rectangle edit means
a niche, opening, finish region, cabinet, or another planner-owned concept.

## 11. Expected Room Planner elevation slice

A useful architecture spike should demonstrate:

1. select a wall face in plan and open its elevation;
2. render floor/ceiling profile and wall extent from canonical geometry;
3. render one opening + door/window element;
4. edit sill/height through face-local preview and one canonical command;
5. render/edit one wall niche;
6. show a ceiling-box/lowered-ceiling intersection line;
7. place one wall-mounted furniture block in elevation and see it reproject in
   plan;
8. place one floor furniture block in plan and see its elevation projection;
9. use plan/front SVG assets from one block definition;
10. fall back to an envelope rectangle when one asset view is absent;
11. synchronize selection across views;
12. undo/redo the canonical edit once, with both views updating.

## 12. Frontend IR consequence

Future `canvas_editor_backend` / scene IR likely needs explicit concepts for:

- view definitions/capabilities;
- semantic view binding (for example selected wall face);
- projection registrations per view;
- cross-view domain refs;
- multi-view block renderer capabilities;
- view-specific tool/command bindings.

Do not encode these as ad-hoc React page state if they repeat across planners.

The exact frontend IR schema remains deferred until the runtime spike proves the
minimal closed shape.
