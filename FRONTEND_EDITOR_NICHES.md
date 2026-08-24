# Frontend Editor — Niche / Recess Refinement

> Status: accepted Architecture v0 refinement.
>
> This document adds shared building-layer guidance from the Room Planner niche
> case. It supplements `FRONTEND_EDITOR.md`, `FRONTEND_EDITOR_OPENINGS.md`, and
> `FRONTEND_EDITOR_PLANAR_REGIONS.md`.

## 1. Niche is not a symbol block

A niche/recess changes host-surface geometry. It is not an opaque reusable SVG
block whose internal path defines engineering meaning.

The shared editor should distinguish:

```text
symbol/block capability
    place discrete reusable entity asset

region/surface capability
    author structured host-surface geometry
```

Ceiling and wall niches belong to the second family.

## 2. Two editing coordinate modes

### Ceiling niche

Use plan/world XY editing:

```text
plan footprint
+ recess depth property
```

The scene derives the raised/recessed back surface and transition edges from the
canonical Room Planner data.

### Wall niche

Use host-wall-face local coordinates:

```text
wall face selection
+ horizontal offset/width
+ vertical sill/height
+ recess depth
```

The editor may expose this as a rectangle drawn/dragged on a wall-face elevation
or as property-assisted plan/elevation editing. The exact UX remains case-flow
work; the canonical data must not become screen coordinates.

## 3. Derived scene geometry

The building layer may expose derived projections such as:

```text
NicheMouthProjection
NicheBackProjection
NicheTransitionFaceProjection
```

for picking, preview, labels, and quantity overlays.

These projections are not persisted canonical niche surfaces merely because they
are selectable. Their geometry is regenerated from host + canonical niche input.

## 4. Separate quantity overlays

The browser should be able to present niche contributions independently from the
flat host surface, for example:

```text
wall niche
    back: ... m2
    sides/jambs: ... m2
    top: ... m2
    sill: ... m2

ceiling niche
    back: ... m2
    transitions: ... m2
```

This display is a projection of Room Planner calculation output. Frontend code
must not recompute conflicting business formulas from Canvas shapes.

## 5. Symbol library remains independent

A niche may visually contain a light strip, fixture, shelf, or another symbol,
but those are separate entities/layers.

For example:

```text
ceiling niche geometry
    + optional lighting symbol/reference
```

The niche does not embed arbitrary SVG markup as its canonical definition, and
placing a lighting symbol does not create/redefine niche geometry.

## 6. Shared tool direction

Reusable editor packages may provide generic mechanics:

```text
DrawPlanRegion
DrawWallFaceRectangle
ResizeRegion
ResizeFaceRectangle
SetDepth
```

The host planner maps those geometric proposals to specific semantic operations:

```text
CreateCeilingNiche
CreateWallNiche
EditExistingNicheMeasurement
...
```

The generic tool must not decide construction/demolition lifecycle itself.

## 7. Architecture conclusion

> **A niche is a host-surface recess with structured depth; its visible inner
> faces are derived projections, not an SVG block definition.**

This keeps the symbol library simple while allowing niche geometry and quantities
to remain deterministic and reusable across browser renderers.
