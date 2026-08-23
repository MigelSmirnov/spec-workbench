# Frontend Editor — Planar Surface/Construction Region Refinement

> Status: accepted Architecture v0 refinement.
>
> This document refines `FRONTEND_EDITOR.md` using the Room Planner floor
> build-up and ceiling-box workflows as architectural evidence. It defines a
> reusable frontend distinction between symbol/entity placement and planar-region
> authoring.

## 1. Symbol placement and region authoring are different editor capabilities

A shared engineering workspace should not treat every drawable thing as a palette
block.

Two important interaction families are:

```text
symbol / discrete-entity placement
    door element
    plumbing fixture
    electrical symbol
    equipment block

planar-region authoring
    floor screed/build-up region
    ceiling box/soffit footprint
    surface treatment region
    future bounded area operations
```

Both may appear in the same toolbar/palette shell, but they must lower to
different capabilities and commands.

## 2. Region tools do not use SVG as their canonical shape

A planar-region tool edits canonical world-space polygon geometry.

Typical pipeline:

```text
activate region tool
    ↓
pointer/snapping creates candidate world polygon
    ↓
property entry (thickness/drop/system/...)
    ↓
planner-specific typed domain intent/entity
    ↓
derived scene projection
```

The renderer may display:

- translucent fill;
- hatch/pattern;
- boundary stroke;
- handles;
- thickness/drop text;
- elevation labels;
- contours/heat maps;
- derived side/underside preview.

These visual forms are projections. An SVG hatch or Canvas polygon is not the
canonical region data.

## 3. Common polygon editing mechanics may be shared

A reusable region-editing capability may own generic mechanics such as:

- create polygon;
- select polygon;
- move vertex;
- insert/remove vertex;
- translate region;
- snap vertices/edges;
- show area/perimeter readouts;
- preview derived geometry supplied by the host layer;
- command-history integration.

It does not own what the region means.

The host planner/layer decides whether a confirmed polygon becomes:

```text
FloorBuildUpIntent
ConstructionCeilingBox
ceiling finish region
future tile zone
another explicit domain concept
```

Do not create a generic persisted `Region(kind, payload)` solely because the
frontend mechanics are reusable.

## 4. Property metadata versus domain authority

A tool/palette manifest may declare which property editor capability is needed,
for example conceptually:

```text
floor-build-up tool
    polygon = required
    property panel = thickness + construction system

ceiling-box tool
    polygon = required
    property panel = drop height + construction system
```

The manifest may drive standard UI generation, labels, controls, and tool
registration. It does not become the source of accepted engineering values.

A default shown in a property editor becomes domain state only when the user
explicitly confirms/applies it through the host planner operation.

## 5. Ceiling box: domain entity, region interaction

A ceiling box/soffit has its own construction identity and lifecycle, so it is a
domain entity even though its authoring gesture is "draw an area".

Frontend projection:

```text
ConstructionCeilingBox
    footprint
    drop height
    system
        ↓
CeilingBoxProjection
    plan polygon
    height label
    derived underside preview
    derived side-face preview / inspection
```

The browser does not require the user to draw the box as six 3D faces.

The 3D-relevant scene geometry is derived from the canonical 2D footprint plus
vertical drop and base ceiling surface.

## 6. Floor build-up: domain intent/region, not discrete block

A floor build-up/screed region is an area operation rather than a movable symbol.

Frontend projection:

```text
FloorBuildUpIntent
    footprint
    thickness
    system
        ↓
FloorBuildUpProjection
    plan fill/hatch
    thickness label
    target elevation preview
    volume preview
```

The renderer may offer a heat map or elevation comparison, but target geometry is
computed from the canonical source surface + explicit thickness.

## 7. Scene registry implications

`@factory/editor-scene` should not require every selectable scene item to have an
SVG/entity definition.

Scene capabilities need to accommodate at least:

```text
discrete entity projection
region/polygon projection
surface/field projection
annotation projection
```

The exact shared scene IR remains open, but the runtime boundary must not force
planar regions into fake symbol instances.

## 8. Palette architecture

A visible palette may combine several item kinds while keeping their semantics
explicit.

Conceptually:

```text
PaletteItem
    symbol placement capability
or
    region tool capability
or
    command/action capability
```

The palette only needs registration metadata. It must not inspect SVG internals
or embed planner business logic.

Examples:

```text
Door
    → symbol/entity placement workflow

Screed
    → floor-build-up region tool

Ceiling box
    → ceiling-box region tool
```

This is why an agent can add/revise a symbol asset without teaching the palette
its SVG structure, while region tools can be registered without inventing SVG
assets at all.

## 9. Snapping and region editing

Region drawing reuses shared world-space snapping infrastructure.

Useful candidates include:

- wall faces/axes;
- wall endpoints;
- room boundary vertices;
- existing region edges/vertices;
- grid;
- horizontal/vertical alignment;
- intersections.

A snap result proposes world geometry only. It does not choose floor thickness,
ceiling drop, construction system, or planner stage meaning.

## 10. Multi-view future compatibility

The canonical `footprint + vertical parameter` representation is intentionally
compatible with a future section/3D preview:

```text
2D canonical region
    + vertical semantics
        ↓
derived section / 3D visualization
```

A future 3D viewer may render the box volume or floor build-up thickness without
turning its mesh into a second editable source of truth.

## 11. First Room Planner evidence slice

After the wall/opening spike, the next frontend evidence slice should prove:

1. draw one floor-build-up polygon in millimetres;
2. enter explicit thickness and preview target floor/volume;
3. draw one ceiling-box polygon;
4. enter explicit drop height and preview lowered underside/clear height;
5. edit polygon vertices through shared region mechanics;
6. undo/redo region commands;
7. serialize domain/application state without Canvas/Konva polygons;
8. prove that neither workflow requires an SVG symbol asset.

## 12. Architectural conclusion

> **How something is drawn is not its domain class.**
>
> A ceiling box can be a domain entity authored by a polygon tool. A screed can
> be a domain construction region authored by the same polygon mechanics. A door
> can be a discrete domain element rendered by an SVG symbol. The shared editor
> should reuse interaction capabilities without collapsing these meanings.
