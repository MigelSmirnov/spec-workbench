# Room Planner — State 0: Wall Elevations and Shared Frontend Block Overlay

> Status: accepted State 0 correction/refinement.
>
> This document keeps wall-elevation authoring inside the Room Planner product,
> while correcting an earlier ownership mistake: furniture and similar reusable
> layout blocks are a shared **frontend/editor capability**, not Room Planner
> backend/domain data.

## 1. Wall elevation is a required editor view

Room Planner needs a wall-elevation / unfolded-wall workflow in addition to the
plan view.

The elevation view is used to inspect and edit Room Planner-owned vertical
relationships that are awkward or ambiguous in plan, including:

- opening sill and head heights;
- door/window element placement and door swing projection;
- wall niches and their vertical extent;
- wall-face treatment regions where later product scope requires them;
- ceiling/base-ceiling lines and lowered ceiling/box consequences;
- local floor line and clear-height consequences.

The elevation is not a separately authored copy of the room. It is a projection
of the same authoritative Room Planner wall/opening/surface/construction data used
by plan view.

```text
canonical Room Planner working state
        ├── plan projection
        └── wall-face elevation projection
```

Editing Room Planner concepts from either view changes the same working-domain
facts through explicit application/editor commands.

## 2. Elevations are wall-face centric

A wall has two semantically different faces. An elevation therefore addresses a
specific wall face rather than only a wall id.

Conceptually:

```text
wall identity
+ wall side / face
        ↓
wall-face elevation view
```

The browser may orient/flip the viewport for usability, but that display transform
must not change canonical wall direction, `WallSide`, opening offsets, door swing,
niche placement, or persisted dimensions.

## 3. Height entry belongs naturally in elevation

The elevation view is a primary interaction surface for entering Room
Planner-owned vertical parameters, for example:

```text
opening sill height
opening height
wall-niche sill / height / recess depth
ceiling-box drop shown at the wall intersection
```

The property panel and direct dimension handles may both expose these values, but
accepted domain values remain real-world millimetres. Dragging a visual handle is
only an input gesture that proposes a new Room Planner domain value.

## 4. Shared frontend blocks are not Room Planner domain

The shared engineering workspace may provide furniture, appliances, sanitary
fixtures, equipment silhouettes, or other reusable visual/layout blocks as a
frontend capability.

These blocks are useful spatial context in plan and elevation, but Room Planner
backend ownership remains limited to Room Planner's own renovation domain.

Therefore a generic furniture/layout block placed in the browser:

- is not Existing, Demolition, Construction, Proposed, or takeoff data;
- is not persisted in a Room Planner snapshot;
- is not published inside `room_plan` or `room_takeoff` merely because it is
  visible in the Room Planner workspace;
- does not require Room Planner API endpoints, persistence tables, basis refs, or
  carry-forward logic;
- does not transfer ownership of furniture/kitchen/equipment semantics into Room
  Planner.

If a future planner genuinely owns a type of placed equipment, that planner may
model its own domain entity and use the same shared block library only as its
renderer/palette layer.

## 5. Reusable multi-view block library is shared frontend infrastructure

A reusable block definition may provide several validated renderer assets for one
visual/semantic library item:

```text
plan
front_elevation
side_elevation
```

The palette consumes manifest metadata and capabilities. It does not parse or
understand the internal SVG paths.

The same library may be reused by Room Planner, Plumbing Planner, Electrical
Planner, and other planner frontends. Reuse of the frontend library does not
imply that every planner backend knows or stores those blocks.

The exact frontend-only placement/overlay representation belongs to the shared
frontend/editor architecture in `../../FRONTEND_EDITOR_ELEVATIONS.md`, not to the
Room Planner domain model.

## 6. Frontend overlay persistence is a separate concern

The initial Room Planner backend has no responsibility to durably persist generic
frontend block overlays.

If the platform later needs shared overlay state to survive browser sessions or
move between devices, that requires an explicit shared-workspace persistence
boundary. It must not be introduced by silently adding foreign-layout fields to
each planner backend.

Local/session frontend persistence may be evaluated by the frontend architecture
without changing Room Planner domain ownership.

## 7. Frontend/editor consequence

The browser workspace needs coordinated view modes at minimum:

```text
Plan
Wall Elevation
```

Room Planner domain selection should move between them through stable Room Planner
refs. Shared frontend overlay blocks may also project into both views using their
own editor-layer identity, but those overlay ids are not Room Planner domain ids.

No Canvas/Konva/SVG scene object becomes canonical Room Planner identity.

## 8. Platform Router impact

This correction introduces no new Platform Hub mechanism.

Wall elevation remains a Room Planner editor projection. Generic frontend block
libraries/overlays remain frontend/editor concerns and are not added to Room
Planner publication provenance.

## State 0 effect

The earlier wording that manual furniture layout was Room Planner product/domain
state is superseded.

The accepted boundary is now:

```text
Room Planner backend/domain
    → owns only Room Planner renovation concepts

Shared browser workspace
    → may additionally render/edit reusable frontend-only block overlays
```
