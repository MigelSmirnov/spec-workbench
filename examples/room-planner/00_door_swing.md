# Room Planner — State 0: Door Swing Product Requirement

> Status: stabilized State 0 product-boundary refinement.
>
> This document supplements the stabilized State 0 product boundary. It records
> a product requirement discovered while validating the Room Planner domain
> against the browser-editor architecture. Detailed models and rules belong to
> later design states.

## Door opening direction is product-significant

For hinged doors, Room Planner must preserve enough information to show and
reason about the real opening direction of the door in plan.

The user must be able to distinguish at least:

- which jamb/side of the aperture carries the hinge;
- to which physical side of the host wall the leaf swings;
- consequently, whether the door opens into one adjacent room/space or the
  other, and for an exterior boundary whether that corresponds to inward versus
  outward opening.

This is not merely a renderer/SVG choice. The opening direction affects practical
renovation planning, clearance review, communication, and the interpretation of
the resulting plan.

## Aperture and door element remain separate

The earlier State 1 distinction remains product-correct:

```text
wall aperture
    spatial opening in the wall

installed/planned door element
    physical door occupying an aperture
```

A door swing belongs to the door element, not to the aperture itself. An
unframed doorway may have the same aperture geometry without any door swing.

Likewise removing a door element does not by itself close the aperture.

## Existing and Construction meanings

Room Planner must be able to record the opening direction of an Existing hinged
door when known.

Construction must also be able to represent the intended installed hinged door
in a retained, created, or altered aperture, including its intended opening
direction.

Replacing a door is therefore semantically:

```text
Existing door element
    ↓ Demolition remove element
Construction install door element with intended swing
```

rather than mutating the Existing door in place.

## Inward/outward terminology

The canonical domain must not rely only on a free-standing boolean such as
`opens_inward` because "inward" depends on which adjacent room/space or exterior
side is being used as the reference.

The durable representation must instead preserve an unambiguous geometric swing
relative to the aperture/host wall. The browser may derive user-facing labels
such as:

```text
opens into Kitchen
opens into Corridor
opens inward
opens outward
```

when the adjacent-space context makes those labels meaningful.

The exact local-coordinate representation is a State 1 decision.

## Renderer consequence

A left/right door SVG variant must not create the opening direction. The
renderer selects a compatible visual variant from canonical door-swing data.

If canonical swing data is absent in an incomplete draft, the editor must not
silently invent a physically meaningful direction merely to draw a conventional
door symbol.

## Scope boundary

This refinement establishes hinged-door opening direction only. Detailed door
product configuration, hardware, leaf construction, fire rating, manufacturer
catalog data, and arbitrary door families remain outside the current product
boundary unless a later requirement introduces them explicitly.

Sliding, folding, double-leaf, or other door-motion families require an explicit
later product/model extension if they need different semantics. They are not
silently represented as hinged-door swing variants.

## Platform Router impact

No new Platform Hub mechanism is introduced. Door swing is Room Planner domain
data carried in the future `room_plan` contract when the corresponding stage is
published. Platform Hub owns artifact exchange/provenance, not door-opening
business semantics.
