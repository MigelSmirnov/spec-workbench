# Frontend Editor — Opening/Aperture Refinement

> Status: accepted Architecture v0 refinement.
>
> This document refines the generic opening discussion in `FRONTEND_EDITOR.md`
> using the Room Planner case as architectural evidence. For opening-related
> building-layer behavior, this document supersedes the older single-`Opening`
> conceptual sketch in `FRONTEND_EDITOR.md` §5.7 and refines the corresponding
> first-spike expectation.

## 1. Aperture and installed element are separate meanings

A reusable building/editor layer must not model a door/window as one decorated
wall object when the application domain distinguishes the wall aperture from the
physical element installed in it.

The generic projection shape is therefore:

```text
wall
  └── opening aperture
        └── optional installed opening element
```

The aperture owns spatial void geometry relative to the wall. The optional
opening element represents a door/window assembly or another product-specific
physical element occupying that aperture.

For Room Planner, the canonical meanings are defined by
`examples/room-planner/10_opening_lifecycle.md`. Shared editor packages consume
those meanings through typed application/layer projections; they do not replace
them with a frontend-only `Opening(kind, svg)` record.

## 2. Scene projections remain separate from canonical domain objects

A renderer-independent building layer may expose conceptual projections such as:

```text
OpeningApertureProjection
    domainRef
    hostWallRef
    profile / derived world geometry
    selection / hit-test capabilities

OpeningElementProjection
    domainRef
    apertureRef
    semantic element kind
    renderer capability key
```

These are scene/layer projections, not new canonical planner entities.

The projection may contain derived outline, hit-test, anchor, and renderer data.
It must not become the authoritative source for wall-relative offset, width,
height, stage lifecycle, or persisted identity.

## 3. Symbol selection cannot own construction semantics

SVG/Konva representation is deliberately downstream from domain meaning.

A symbol or symbol variant MUST NOT silently determine:

- whether an aperture is a doorway, window opening, or unframed opening;
- whether a door/window element physically exists;
- demolition or construction stage meaning;
- opening width/height or host-wall identity;
- hinge side, swing direction, sash behavior, opening direction, or another
  physical fact when that fact affects planning.

If hinge/swing/handing or another visual distinction becomes physically relevant
to a planner, it must first be represented by an explicit domain/product field
owned by that planner. The renderer may then select a compatible symbol variant
from that field.

If the canonical domain does not contain such a fact, the renderer must use a
neutral/non-committal symbol. It must not infer a physical choice from a palette
asset such as `door.single.left` and thereby create a second source of truth.

Purely stylistic variants that do not change domain meaning may remain renderer
or presentation choices, but they must not be consumed as engineering facts.

## 4. Attachment and anchors

Opening apertures are semantically attached to host walls in world/domain
coordinates. Their render position is derived from the host wall plus the
canonical wall-relative profile.

The building layer may expose semantic anchors such as:

```text
opening centre
opening jamb/start
opening jamb/end
opening element attachment
```

Anchor coordinates are derived. Persisted relationships should refer to the
semantic aperture/element identity rather than copied viewport coordinates.

Moving or resizing the host wall must therefore reproject the aperture and its
installed element without stale Canvas/SVG placement data.

## 5. Shared editor tools produce geometry proposals, not stage semantics

The reusable building layer may own common interaction mechanics for:

- selecting an aperture;
- dragging/resizing an aperture profile;
- snapping jambs/centres to world geometry;
- previewing an aperture on a wall;
- hit-testing an installed element;
- projecting an element symbol into an aperture.

But generic editor packages do not decide whether a confirmed profile means
Existing measurement correction, Demolition cutting, Construction create,
Construction alter, or Construction close.

The intended command direction is:

```text
pointer/tool gesture
    ↓
typed aperture geometry proposal
    ↓
host planner/layer operation
    ↓
planner-specific stage command/intent
    ↓
working domain state
```

For Room Planner, the host operation maps confirmed editing intent to the
explicit Existing/Demolition/Construction semantics already defined in the
numbered case documents.

## 6. Room Planner lifecycle projection

The browser/editor projection of the accepted Room Planner model is:

```text
Existing aperture
+ optional Existing opening element
        ↓
Demolition element removal / wall cut overlays
        ↓
Construction create / alter / close intent
        ↓
Derived Proposed aperture scene
```

Important consequences:

- removing a door/window element does not remove the aperture;
- a demolition cut is removal geometry, not the final Proposed aperture;
- Construction owns the positive create/alter/close aperture result;
- a closed Existing aperture has no positive Proposed opening entity;
- a changed aperture is rendered from the Construction result, not by mutating
  the Existing source in place.

## 7. Preview and commit

During pointer interaction the browser may keep a transient candidate
`OpeningProfile` or equivalent projection value.

```text
canonical aperture/profile
        ↓ gesture
transient candidate profile
        ↓ validation/snapping preview
rendered preview
        ↓ confirm
planner command / working draft mutation
```

The transient candidate is not an accepted snapshot, publication, or canonical
aperture until the host planner confirms the corresponding domain operation.

Undo/redo belongs to editor command history; save/accept/publish remain separate
application/domain actions.

## 8. Refined first vertical slice

The Room Planner frontend proof should no longer be phrased only as "one door
attached to a wall". The opening slice should prove:

1. one aperture semantically hosted by a wall using real-world millimetres;
2. an optional installed door element referencing that aperture;
3. independent selection/hit-testing of aperture versus installed element where
   the UI exposes both meanings;
4. neutral SVG symbol projection for the door through the symbol registry;
5. moving/resizing the aperture through transient preview without making the SVG
   asset authoritative;
6. host-wall movement reprojects aperture + element without storing stale scene
   coordinates;
7. serialization contains editable domain/application state and references, not
   Konva nodes or SVG markup.

A later Room Planner interaction slice should additionally prove the
Existing/Demolition/Construction create/alter/close overlays once State 4 flows
and commands are defined.

## 9. Architectural conclusion from Room Planner

The Room Planner case provides evidence for a reusable building-layer rule:

> **An aperture is topology/geometry; an installed door/window is a physical
> element; a symbol is a renderer asset. These three meanings must not collapse
> into one frontend object.**

This refinement changes the shared frontend conceptual model, not the accepted
Room Planner State 1 lifecycle. The Room Planner model remains the canonical
source that exposed the earlier frontend simplification.