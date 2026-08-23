# Frontend Editor — Door Swing Refinement

> Status: accepted Architecture v0 refinement.
>
> This document refines the shared browser/editor architecture after Room Planner
> established hinged-door opening direction as canonical domain data.

## 1. Door swing is domain input to rendering

The frontend pipeline is:

```text
canonical DoorSwing
    + aperture/host-wall geometry
        ↓
building-layer projection
        ↓
renderer/symbol selection + transform
        ↓
Konva / SVG scene
```

The reverse dependency is forbidden. Selecting or rendering an SVG variant does
not create engineering swing semantics.

## 2. Generic building-layer projection

A reusable building layer may project a hinged door approximately as:

```text
HingedDoorProjection
    domainRef
    apertureRef
    hingeWorldPoint
    swingSide
    leafClosedSegment
    optional swingArc
    rendererCapabilityKey
```

These are derived scene values. The canonical source remains the planner-owned
`DoorSwing` plus host aperture/wall geometry.

## 3. Wall-relative semantics

The shared building layer must understand that opening/door semantics may be
relative to a directed wall axis.

It may derive:

- aperture start/end world positions;
- hinge world position;
- leaf direction/arc;
- side-of-wall placement;
- semantic opening anchors.

It must not persist these derived world points as replacements for the canonical
wall-relative data.

## 4. Symbol catalog mapping

A symbol registry may define compatible visual variants for hinged doors, but
variant names are renderer data.

For example, a registry may contain assets that visually correspond to canonical
combinations of:

```text
hinge_jamb = opening_start | opening_end
swing_to_wall_side = left | right
```

The mapping is deterministic from canonical semantics to renderer capability.

A palette item such as `door.single.left` MUST NOT be interpreted as a domain
value by string parsing. If the user deliberately chooses a physical swing from
a palette/tool, the tool emits a typed command containing canonical
`DoorSwing`; renderer selection happens afterward.

## 5. Existing unknown swing

When an Existing hinged door has unknown swing, the frontend must not choose one
of the physical swing variants just because a door symbol is required.

Possible neutral presentation strategies include:

- a leaf-less door/frame indication;
- a dedicated unknown-swing symbol;
- another clearly non-committal representation.

The exact visual style is not architectural, but it must not imply an accepted
hinge/swing choice absent from domain data.

## 6. User interaction

Door editing should expose explicit operations such as:

```text
SetDoorHingeJamb
SetDoorSwingSide
FlipDoorHinge
FlipDoorSwingSide
```

or an equivalent small typed command set.

A visual flip gesture may be convenient, but it must lower to explicit canonical
semantics before mutating working domain state.

Dragging/resizing the aperture is a different operation and must not silently
flip door swing.

## 7. Inward/outward presentation

The frontend may combine canonical wall-side swing with room/exterior adjacency
to show user-friendly labels:

```text
opens into Bedroom
opens into Hall
opens outward
opens inward
```

Those labels are projections. They are not stored by the shared editor as the
canonical swing value.

If adjacency is ambiguous, show the stable wall-side/space description rather
than inventing inward/outward semantics.

## 8. Frontend proof slice refinement

The Room Planner frontend spike should prove a hinged door with:

1. canonical aperture attachment to a wall;
2. explicit canonical hinge jamb;
3. explicit canonical swing-to-wall-side;
4. deterministic SVG/Konva projection from those values;
5. interactive hinge/swing flip through typed commands;
6. wall movement/reversal handling without changing physical swing;
7. neutral rendering for an Existing door whose swing is unknown;
8. serialization with no SVG/Konva scene state as canonical door data.

## 9. Architectural conclusion

> Door swing is engineering state. Symbol handedness is a rendering of that
> state, not its source.

The Room Planner case therefore strengthens the shared frontend rule that visual
assets may encode presentation variants but must never become a hidden domain
model.
