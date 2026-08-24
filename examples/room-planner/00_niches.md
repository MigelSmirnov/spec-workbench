# Room Planner — State 0: Ceiling and Wall Niches

> Status: accepted State 0 refinement.
>
> This document extends the stabilized Room Planner product boundary after
> confirming that recessed niches are common construction geometry and their
> surfaces/quantities must be calculated separately.

## 1. Niches are construction geometry, not renderer decoration

Room Planner must support recessed niches in at least two initial forms:

```text
ceiling niche / light recess
wall-face niche / recess
```

A niche changes the physical surface envelope. It is therefore domain-significant
geometry even though the editor remains 2D-centric.

A niche must not be represented only as:

- a hatch;
- an SVG symbol;
- a Canvas group;
- a text annotation;
- a generic finish-region flag.

The browser may use those visual forms to project a niche, but the authoritative
facts remain structured geometry and explicit depth.

## 2. Common 2D authoring principle

The initial product continues to avoid arbitrary free-form 3D solid authoring.

A niche is authored through a 2D description on its host surface plus an explicit
recess depth:

```text
2D niche extent on host surface
        +
recess_depth_mm
        +
Construction Catalog system where construction work is intended
        ↓
derived recessed surface + side faces + physical quantities
```

The recess depth is user-entered physical data, not inferred from a renderer
symbol or camera.

## 3. Ceiling niche / light recess

A ceiling niche is a locally recessed area above the applicable room-facing
ceiling surface.

The user authors it in plan by drawing/selecting a 2D footprint and entering its
recess depth.

Conceptually:

```text
ceiling niche
    room scope
    + plan footprint
    + recess_depth_mm
```

For Construction, an exact catalog-backed system is also selected before
acceptance.

Room Planner derives at least:

- the recessed/back ceiling surface over the footprint;
- vertical transition/side faces around the exposed footprint boundary;
- the local clear-height increase inside the niche;
- separate physical areas/quantities for the niche back and side faces where
  calculation semantics require them.

A ceiling niche is opposite in geometric direction to a ceiling box/soffit:

```text
ceiling box
    projects/downsteps into the room

ceiling niche
    recesses/upsteps away from the room
```

They remain separate domain meanings even when both are edited as 2D regions.

## 4. Wall-face niche

A wall niche is a recess into one specific room-facing wall face. It does not
pass through the wall like an aperture/opening.

The user authors its face-local rectangle by specifying/drawing:

- horizontal position along the host wall;
- width;
- vertical position/height;
- recess depth into the wall face.

Conceptually:

```text
wall face
    + rectangular niche extent
    + recess_depth_mm
```

Room Planner derives at least:

- the niche back face;
- the two vertical jamb/side faces;
- the top face;
- the bottom/sill face;
- the removed/recessed portion of the original wall-face surface;
- the resulting net finishable wall/niche areas.

A wall niche is not an opening aperture. It remains associated with exactly one
wall face and does not create passage through the host wall.

## 5. Existing, Demolition, and Construction meaning

Existing may record measured ceiling or wall niches when they physically exist
and affect spatial/surface quantities.

Construction may create new niches with explicit depth and exact construction
system selection.

Demolition associated with creating a niche in retained Existing construction
must remain explicit where Existing material is physically removed. The exact
cut/removal model is a later State 1/2 refinement if the niche is created in an
Existing substrate; Construction must not fabricate demolition history merely
from the final niche geometry.

Closing/filling an Existing niche is Construction work, not deletion of the
Existing fact.

## 6. Separate quantity meaning

Niches must be separately addressable for physical quantity calculation because
their geometry introduces surfaces that differ from the unrecessed host surface.

Examples:

```text
ceiling niche:
    back area
    transition/side area

wall niche:
    back area
    jamb/side areas
    top area
    sill/bottom area
```

The exact finish/system formulas belong to State 2 and Construction Catalog
rules. Room Planner owns geometric surface/volume derivation; PresuPro retains
pricing/labor/commercial responsibilities.

## 7. Browser/editor consequence

Niches are not opaque palette symbols.

Expected editing behavior:

```text
ceiling niche
    region tool in plan
    + depth/system properties

wall niche
    wall-face/local-rectangle tool
    + depth/system properties
```

The browser may render outlines, fills, labels, edge marks, or preview shading.
Those visual objects do not become canonical niche geometry.

## 8. Platform Router impact

This refinement introduces no new Platform Hub mechanism. Room Planner may
publish niche geometry and derived quantities through the already established
room-plan/takeoff artifact boundary.

## State 0 effect

State 0 remains stabilized with this refinement included. Ceiling boxes/soffits,
floor build-up regions, and niches are all initial-scope 2D-authored construction
geometry, but their domain meanings remain explicit and separate.
