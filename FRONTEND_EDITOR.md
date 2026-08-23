# Frontend Editor

> Living cross-case frontend/editor architecture contract.
>
> Status: **Architecture v0 working document**. The boundaries below are the current
> implementation direction for browser-based engineering planners. Concrete IR
> schemas and third-party dependency choices remain provisional until proven by
> real case studies.

## Purpose

The platform is expected to contain several interactive engineering planners:
Room Planner, Plumbing Planner, Electrical Planner, Tile Planner, and related
future tools. They should not become unrelated React applications that each
reimplement drawing, selection, snapping, layers, geometry, symbols, and editor
state.

The target is a shared browser-first engineering workspace with reusable editor
packages and reusable domain/editor layers. Individual planner applications
remain owners of their own domain behavior, persistence, backend endpoints, and
published artifacts.

The high-level boundary remains:

```text
browser editor
    ↕ explicit application contracts
application backend / domain
    ↕ shared integration contracts
Platform Hub
```

The browser talks to its own application backend for private working state and
interactive editing. Ordinary editor operations do not route through Platform
Hub. Platform Hub remains the cross-application boundary for Registry objects,
shared platform data, published artifacts, publication history, provenance, and
cross-application discovery.

---

# 1. Non-negotiable architectural rules

## 1.1 Domain state is not editor state

Durable domain facts remain meaningful without React, Canvas, SVG, Konva, DOM,
or a particular browser library.

Examples of domain-authoritative data:

- real-world coordinates and dimensions;
- walls, openings, rooms, surfaces, pipes, fixtures, circuits, and other
  planner-owned entities;
- accepted snapshot identities and bases;
- stable domain references;
- validation-relevant parameters;
- persisted working drafts intentionally owned by the application.

Examples of transient frontend state:

- pan and zoom;
- hover;
- current selection;
- active tool;
- drag handles;
- snap hints;
- uncommitted preview geometry;
- cursor state;
- panel expansion/collapse;
- temporary visibility state.

Persistence of a user preference does not automatically make that value domain
truth.

## 1.2 Rendering is a projection

SVG, Canvas, WebGL, DOM, or another renderer is a projection of domain/editor
state. Rendered pixels and scene objects are not an independent source of domain
truth.

```text
canonical domain geometry
        ↓ projection
scene geometry
        ↓ renderer
Canvas / SVG / pixels
```

A renderer may create transient preview geometry during interaction. Accepted
changes return through commands/application operations into canonical world
geometry.

## 1.3 Engineering geometry uses real-world units

Canonical design geometry uses real-world units. For the current planner family,
the base unit is **millimetres**.

Viewport pixels, SVG viewBox units, Canvas backing-store coordinates, device
pixels, zoom, and pan are rendering concerns and must not corrupt real project
dimensions.

The target Room Planner interaction accuracy is millimetre-level. Geometry
algorithms may use higher internal floating-point precision when intersections,
angles, or transforms require it, but committed domain values must follow an
explicit canonical precision/quantization policy. The initial working candidate
is canonical millimetre coordinates with a 1 mm user-edit precision; the exact
storage quantization remains an explicit design decision rather than an implicit
renderer behavior.

## 1.4 React is thin

React owns composition, display, and input wiring. React components must not
become hidden owners of geometry rules, domain calculations, persistence,
publication semantics, or multi-step editor behavior.

Prefer:

```text
button / key / pointer gesture
        ↓
typed command
        ↓
editor/application operation
        ↓
state transition
        ↓
projection
```

instead of implementing business behavior directly inside JSX handlers.

## 1.5 Code reuse, data exchange, and data ownership are separate axes

```text
code reuse
    shared editor packages + reusable layer packages

data exchange
    stable contracts + Platform Hub artifacts

data ownership
    the application/domain backend that owns authoritative working state
```

Sharing a wall layer package does not authorize another planner to write Room
Planner's private database. Rendering a plumbing layer does not make the host
application the plumbing owner. Consuming `room_plan.v1` does not grant wall
editing authority.

## 1.6 Deterministic ownership fails closed

Where a frontend IR/backend claims ownership of a structural area, missing or
invalid decisions must fail validation. An emitter must not silently invent a
plausible implementation.

LLM/agent implementation remains allowed for explicitly irregular areas that are
not owned by a deterministic backend.

---

# 2. Target architecture v0

The intended system is one specification/compiler ecosystem with Python and
frontend backends, plus reusable runtime packages.

```text
                         PRODUCT / DOMAIN SPEC
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
        models                  rules                 contracts
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                         validated canonical IR
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
       Python backends                         Frontend backends
     router/persistence/...                client/layout/editor/forms
              │                                       │
              ▼                                       ▼
            Python                          generated TypeScript
                                                      │
                                                      ▼
                                          planner workspace config
                                                      │
                       ┌──────────────────────────────┼──────────────────────────────┐
                       │                              │                              │
                       ▼                              ▼                              ▼
                shared editor packages        reusable domain layers       app adapter/client
                       │                              │                              │
                       └──────────────────────────────┼──────────────────────────────┘
                                                      ▼
                                               browser workspace
                                                      │
                                                      ▼
                                            own application backend
                                                      │
                                                      ▼
                                                Platform Hub
```

The frontend factory should generate declarations, registrations, typed clients,
and conventional wiring. It should not regenerate thousands of lines of generic
camera, selection, history, pointer, or snapping machinery for every planner.

---

# 3. Reusable package architecture

Package names are provisional; responsibilities and dependency direction are the
important part.

## 3.1 `@factory/editor-core`

Owns generic editor interaction semantics independent of React and a drawing
backend:

- command dispatch;
- command history;
- undo/redo;
- selection model;
- tool lifecycle;
- preview/commit lifecycle;
- transient editor state primitives;
- dirty/clean state hooks;
- generic keyboard-command mapping contracts.

It does not own:

- building geometry;
- Canvas/SVG rendering;
- backend transport;
- planner-specific validation.

## 3.2 `@factory/editor-geometry`

Owns language-level geometry primitives and operations exposed through a stable
platform API:

- `Point`, `Vector`, `Segment`, `Line`, `Ray`, `Rect`, `Polygon`, transforms;
- distance and projection;
- intersections;
- angle calculations;
- local ↔ world transforms;
- world ↔ viewport transforms;
- generic hit-test geometry;
- generic snapping primitives;
- polygon operations where required;
- offset geometry where required.

The public editor API must not expose a third-party geometry library as the
canonical model. A third-party engine may live behind this package.

Initial implementation candidate: `@flatten-js/core`, hidden behind the
`editor-geometry` boundary. This is an implementation candidate, not a platform
contract.

## 3.3 `@factory/editor-scene`

Owns renderer-independent scene composition:

- scene registry;
- layer registry;
- entity-definition registry;
- entity instances/projections;
- semantic anchors;
- relations/connections;
- layer visibility;
- renderer capability registration;
- picking/hit-test capability declarations.

The scene is a projection/composition layer. It must not become a replacement
for canonical planner domain models.

## 3.4 `@factory/editor-canvas`

Owns Canvas-specific projection and interaction adaptation:

- drawing-stage adapter;
- camera integration;
- pointer normalization;
- render loop/invalidation;
- Canvas picking integration;
- Canvas renderer registry;
- image/SVG-symbol placement on Canvas.

Initial implementation candidate: Konva + `react-konva`, hidden behind this
package where practical. Planner layers should not depend directly on Konva
objects as domain data.

## 3.5 `@factory/editor-svg-symbols`

Owns reusable engineering-symbol assets and their machine-readable registry:

- SVG asset loading;
- symbol manifests;
- local symbol coordinate systems;
- symbol bounds/viewBox;
- symbol anchors;
- categories/palette metadata;
- Canvas/SVG projection adapters;
- symbol validation.

SVG is preserved deliberately because it is an effective authoring format for
engineering blocks and AI agents can generate or refine it from visual
references.

SVG is **not** the editable domain model.

## 3.6 `@factory/editor-react`

Owns standard React workspace composition:

- viewport shell;
- toolbar;
- palette;
- property panel;
- layer panel;
- status/readout areas;
- command bindings;
- dialogs and standard editor chrome;
- loading/error/validation presentation.

The package consumes editor/domain capabilities; it does not own planner
semantics.

## 3.7 `@factory/editor-routing`

Optional package for connection/path routing:

- straight routes;
- orthogonal routes;
- anchor-direction-aware routing;
- routing preview helpers;
- future obstacle-aware routing if evidence requires it.

Routing used only for display is derived geometry. If a physical route itself is
domain-significant, such as a real pipe run with bends, the route belongs to the
owning domain model instead.

## 3.8 `@factory/editor-export`

Optional export boundary for presentation/document outputs:

- SVG export;
- DXF adapter;
- PDF/drawing adapter;
- image export.

A future implementation may use Maker.js or another CAD/export library behind
this boundary. Export dependencies must not leak into canonical editor/domain
models.

---

# 4. Reusable planner/domain layers

The generic editor packages are complemented by reusable domain/editor layers.
Applications do not import each other as whole applications.

Initial expected layer family:

```text
@planner/building-layer
@planner/plumbing-layer
@planner/electrical-layer
@planner/tiles-layer
@planner/annotations-layer
```

A layer package may expose:

- projection/boundary types;
- renderer registrations;
- tools;
- command declarations;
- semantic anchors;
- hit-test behavior;
- snapping policies;
- property descriptors;
- interaction validation;
- layer metadata.

A layer package must not directly own backend transport or silently persist
itself.

Avoid:

```text
@planner/plumbing-layer
    → fetch('/plumbing/...')
```

Prefer:

```text
plumbing layer
    ↓ typed operation
host application adapter
    ↓ generated/typed client
Plumbing backend
```

---

# 5. Building layer: geometry and topology

The first reusable domain layer should be a building/room geometry layer because
walls, openings, rooms, and surfaces are useful context for most later planners.

## 5.1 Wall model

A wall is not canonically stored as a thick Canvas/SVG stroke or arbitrary
rendered polygon.

The working model is a semantic centreline plus thickness and topology:

```text
WallNode
    id
    positionMm

Wall
    id
    startNodeId
    endNodeId
    thicknessMm
    additional domain properties...
```

The visible wall outline is derived from the centreline, thickness, and join
policy.

```text
node A ───────────── node B       canonical centreline
          +
      thicknessMm
          ↓
      derived wall outline
```

This makes movement, joining, dimensions, openings, surfaces, and downstream
references easier than treating a rendered polygon as the primary model.

## 5.2 Shared nodes and closed wall chains

Walls that meet at a true shared endpoint should share a `WallNode` identity,
not merely happen to contain almost-equal coordinates.

```text
Wall A ───────●
              │
              │ Wall B
```

Dragging the shared node changes all connected wall projections while
preserving topology.

Closed rooms/wall loops should therefore be representable as topology, not only
as visually touching strokes.

## 5.3 Junction kinds

At minimum the geometry design must distinguish:

- endpoint/corner junctions;
- T-junctions;
- crossings/intersections where the domain allows them;
- continuation/collinear joins where useful.

A T-junction is not necessarily two walls with the same endpoint coordinates.
One wall endpoint may be semantically attached to another wall segment.

The exact canonical representation of T-junctions remains to be proven. A likely
shape is a semantic attachment to a wall/segment position rather than duplicated
floating coordinates.

## 5.4 Wall joins and outline generation

The renderer/geometry projection must support wall thickness through corners and
junctions without cracks or accidental overlaps.

Join behavior may include miter/butt/intersection policies, but the exact policy
must be explicit and deterministic. It must not be whatever a Canvas `lineJoin`
happens to produce if that differs from domain geometry.

The centreline/topology remains canonical; visible outline polygons are derived
unless later domain requirements make a particular boundary independently
meaningful.

## 5.5 Wall movement commands

"Move wall" is not one ambiguous operation. The editor should distinguish
commands such as:

```text
MoveWallNode
    move a shared endpoint/junction

TranslateWall
    move the whole wall with its relevant topology policy

OffsetWall
    move a wall parallel to itself while preserving/repairing joins

ResizeWall / MoveWallEndpoint
    alter one endpoint according to constraints
```

Tools may map gestures to these commands, but command semantics remain explicit
and testable.

## 5.6 Angles and constraints

A wall angle is normally derived from its canonical endpoints:

```text
angle = atan2(end.y - start.y, end.x - start.x)
```

Do not store a redundant mutable angle when it is fully derivable.

Persistent design intent may instead be represented by explicit constraints,
for example:

- horizontal;
- vertical;
- fixed angle;
- perpendicular to another segment;
- parallel to another segment.

Geometry facts and constraints are separate meanings.

## 5.7 Openings, doors, and windows

Openings are semantically attached to walls rather than placed as unrelated
screen objects.

A working conceptual form is:

```text
Opening
    id
    wallId
    offsetMm / attachment position
    widthMm
    kind
    additional domain properties
```

Door/window domain state may include hinge side, swing direction, opening type,
height, or other product-required properties.

The visual block is selected separately through a renderer/symbol definition.

---

# 6. Coordinate-space contract

All engineering editor code must be explicit about coordinate space.

```text
symbol/definition-local
        ↓ local/entity transform
world/domain millimetres
        ↓ camera transform
viewport coordinates
        ↓ device scaling
screen/device coordinates
```

Pointer input travels in the inverse direction before becoming a candidate world
position.

Geometry calculations that change accepted domain state happen in world/domain
space, not viewport pixels.

Renderers may use local coordinates. They must not read arbitrary camera state
and bake screen placement into reusable entity/symbol definitions.

---

# 7. Snapping architecture

Snapping is shared infrastructure, not planner-specific pointer spaghetti.

The pipeline is:

```text
pointer screen position
        ↓ inverse camera transform
raw world position
        ↓
collect snap candidates
        ↓
rank/filter candidates
        ↓
SnapResult
        ↓
transient preview
        ↓ explicit command commit
canonical geometry
```

Expected candidate classes for building/planner editors include:

- grid;
- endpoint/node;
- midpoint;
- segment/wall axis;
- horizontal/vertical alignment;
- angle;
- perpendicular projection;
- intersection;
- extension line;
- semantic anchors supplied by layers.

A `SnapResult` proposes geometry. It does not become authoritative state by
itself.

Layer packages may contribute snap candidates while the shared geometry/editor
runtime owns candidate collection/ranking mechanics.

---

# 8. Definition versus instance

Reusable editor entities distinguish reusable definitions from concrete scene or
domain instances.

```text
EntityDefinition
    stable type/capability identity
    metadata
    default/local geometry when applicable
    anchors
    renderer capability key
    interaction capabilities

EntityInstance / domain entity
    stable instance identity
    definition/type reference where relevant
    authoritative domain state/reference
    transform where relevant
```

Not every domain type must fit a simplistic `x/y/rotation` record. Walls,
polygons, pipes, doors, and electrical symbols have different semantics.

Definitions must not be copied into every instance. Instances must not persist
SVG markup or Canvas scene objects as canonical state.

---

# 9. Semantic anchors

`Anchor` is the shared concept for an explicitly addressable attachment point or
attachment feature.

Possible anchor kinds include:

- wall endpoints;
- wall midpoint;
- wall face;
- room vertex;
- opening attachment;
- plumbing port;
- electrical terminal;
- generic engineering symbol port;
- future domain-specific attachment semantics.

Relations should persist semantic references where possible:

```text
entity A + anchor outlet
        ↓
entity B + anchor inlet
```

rather than stale render coordinates.

General rule:

> **Persist semantic references; derive render coordinates.**

If a connection path is merely visual, its rendered geometry is derived from the
current anchor positions. If the path itself is physically meaningful, the
owning domain explicitly stores it.

---

# 10. SVG engineering-symbol architecture

SVG remains a first-class reusable **asset format** even when the primary scene
renderer is Canvas.

This is intentional:

- SVG scales cleanly;
- engineering blocks are naturally represented as vector symbols;
- agents can generate SVG effectively from visual references;
- symbols can be reviewed visually;
- assets can be versioned independently from editor code;
- one symbol can be reused by several planners.

## 10.1 Symbol definition

A symbol is an asset plus machine-readable semantics, not merely a loose SVG
file.

Conceptually:

```text
SymbolDefinition
    id
    title
    category
    svgAsset
    viewBox/local bounds
    defaultSizeMm where meaningful
    anchors[]
    renderer = svg
    optional variant/parameter metadata
```

The exact schema is deferred until the first implementation.

## 10.2 Clean local SVG rule

Generated SVG symbols should:

- use a local `viewBox`;
- avoid project/world absolute coordinates;
- contain no application/editor state;
- contain no executable JavaScript;
- avoid external network dependencies;
- keep semantic attachment points in the symbol manifest/anchor metadata rather
  than guessing them from path shapes.

The runtime controls world position, scale, rotation, selection, and viewport
projection.

## 10.3 Palette generation

The palette should read a validated symbol registry rather than hard-code every
item in React.

```text
SVG assets + symbol manifests
        ↓ validate
symbol registry
        ↓
palette categories/items
```

Adding an accepted symbol definition should therefore make the symbol available
to any compatible planner palette without custom palette code.

## 10.4 Agent-generated symbols

LLM/agent image-to-SVG generation is an authoring-time tool, not a runtime
requirement.

```text
visual reference
        ↓ agent
candidate SVG
        ↓ review/validation
versioned symbol asset
        ↓ deterministic registry/runtime
all compatible planners
```

Once accepted, the symbol is ordinary versioned input and does not require an
LLM to render.

## 10.5 Parametric symbols

Do not begin with a general parametric-SVG language unless evidence requires it.
Early versions may use explicit variants such as:

```text
door.single.left
door.single.right
door.double
door.sliding
```

A richer parametric renderer may be introduced later for repeated cases that
cannot be represented cleanly by variants plus runtime scale/rotation.

---

# 11. Cross-planner workspace composition

The planner family should converge on a common workspace capable of composing
multiple domain layers.

```text
shared engineering workspace
        │
        ├── building / room layer
        ├── plumbing layer
        ├── electrical layer
        ├── tile layer
        └── annotations / auxiliary layers
```

This allows, for example:

- Plumbing Planner to open Room Planner wall/room geometry as context;
- Electrical Planner to render building and plumbing references;
- Room Planner to display or locally sketch plumbing/electrical overlays when
  useful;
- several planners to reuse the same doors/windows/symbols, camera, snapping,
  selection, and measurement behavior.

Shared rendering capability must not erase domain ownership.

---

# 12. Layer ownership modes

Rendering, selecting, editing, persisting, and publishing are separate
capabilities.

The current working model has three modes.

## 12.1 `owned`

The host application owns authoritative working state for the layer.

```text
render = yes
select = yes
edit = yes
persist through host backend = yes
publish under host contracts = when product flow allows
```

Example: building/walls in Room Planner; plumbing in Plumbing Planner.

## 12.2 `reference`

The host consumes another domain's accepted/published/resolved state for context.

```text
render = yes
select/inspect = optional
edit authoritative source = no
persist foreign authoritative state = no
publish foreign domain = no
```

Example: Plumbing Planner rendering Room Planner geometry.

## 12.3 `draft`

The host may let the user locally sketch/propose another domain's entities
without becoming their authoritative owner.

```text
render = yes
edit local proposal = yes
persist as host-private overlay = explicit product decision
write foreign authoritative backend = no
publish foreign authoritative artifact = no
```

A draft may later be transferred/opened in the owning planner and validated
there before becoming owned state.

The transfer protocol remains open.

## 12.4 Ownership rule

> **Rendering capability is not data ownership.**
>
> **Editing capability is not persistence authority.**
>
> **Importing a layer package is not authorization to mutate the layer owner's
> backend.**

This is the basis for allowing "draw almost anything anywhere" without mixing
backend data ownership.

---

# 13. Planner applications become workspace configurations

If the boundaries above hold across real applications, planner frontends become
small configurations of the same engineering workspace.

```text
Room Planner
    shared editor shell
    + building owned layer
    + demolition/construction capabilities
    + optional plumbing/electrical reference or draft layers
    + Room Planner adapter/client

Plumbing Planner
    shared editor shell
    + building reference layer
    + plumbing owned layer
    + optional electrical reference/draft layer
    + Plumbing adapter/client

Electrical Planner
    shared editor shell
    + building reference layer
    + electrical owned layer
    + optional plumbing reference layer
    + Electrical adapter/client
```

They may reuse most frontend mechanics while retaining different authoritative
models, backend endpoints, validation rules, and Platform Hub artifacts.

---

# 14. Browser ↔ Backend ↔ Platform Hub boundary

A planner frontend uses its own application backend as its authoritative
persistence/application boundary.

```text
Browser workspace
    ↓ host application API
Application Backend
    ↓ shared integration contracts
Platform Hub
```

A foreign layer package does not add foreign backend endpoints to the host
application.

If Room Planner displays a plumbing draft, Room Planner does not suddenly gain
canonical plumbing CRUD endpoints. If Plumbing Planner renders walls, it does
not gain authority over Room Planner's private working database.

Cross-application durable exchange remains artifact/contract-based through
Platform Hub, consistent with `PLATFORM_ROUTER.md`.

The application backend may resolve foreign published/reference data for the
browser, but Platform Hub is not the application's backend-for-frontend for
ordinary editor operations.

---

# 15. Frontend factory and deterministic generation

The frontend should not be generated as a fresh arbitrary React application for
each planner.

The preferred pipeline is:

```text
product/domain decisions
        ↓
canonical specification
        ↓
frontend IR / structured policies
        ↓ validation
runtime registrations + generated TypeScript
        ↓
shared editor packages
        ↓
small planner-specific irregular islands
```

Strong deterministic-generation candidates:

1. TypeScript domain/boundary types from canonical models.
2. Typed application API clients.
3. Screen/navigation registration.
4. Layer registration and stable draw order.
5. Command catalog and toolbar/key/context-menu bindings.
6. Standard transient state declarations.
7. Forms/property panels from typed field metadata.
8. Symbol registries and palette catalogs.
9. Renderer capability registration.
10. Standard snapping/selection/history policies.
11. Standard React workspace composition.
12. Request/response DTOs and error mappings.

Prose/LLM remains appropriate for semantic behavior that does not yet have a
stable closed IR and for intentionally irregular UX/geometry implementations.

Repeated note shapes across planners are evidence that a new structured IR or
runtime capability is missing.

---

# 16. Candidate frontend IR backends

Do not start with one giant `frontend` schema. Current provisional families:

```text
react_app_backend/v1
canvas_editor_backend/v1
form_backend/v1
api_client_backend/v1
symbol_catalog_backend/v1       # candidate
```

Possible responsibilities:

## `react_app_backend/v1`

- screens/navigation;
- layout composition;
- standard panels;
- dialogs;
- state/view bindings;
- command bindings.

## `canvas_editor_backend/v1`

- scene/layer catalog;
- layer ownership/capability declarations;
- tool catalog;
- gesture-command bindings;
- selection policy;
- history policy;
- camera policy;
- snapping policy;
- renderer registry;
- preview/commit behavior.

## `form_backend/v1`

- editable fields;
- controls/widgets from closed metadata;
- validation projection;
- grouping/order;
- read-only/editable policy;
- submit command/API binding.

## `api_client_backend/v1`

- application endpoints exposed to the browser;
- parameters/body/result;
- auth boundary;
- error mapping;
- serialization;
- deterministic typed client generation.

## `symbol_catalog_backend/v1` candidate

Only introduce after real use proves the schema. Candidate ownership:

- symbol metadata;
- asset identities;
- categories;
- anchors;
- default dimensions;
- allowed variants;
- deterministic registry/palette generation.

Presence of a valid backend-owned IR should mean deterministic/fail-closed
emission. Irregular components/tools remain explicit owners rather than silent
fallbacks.

---

# 17. Reuse from the existing specification system

Do not create a second independent truth model for frontend generation.

Strong reuse candidates from the existing specification standard:

- `models`;
- `config`;
- `rules`;
- `properties`;
- `determinism`;
- classified notes;
- dependency graph and affected-set analysis;
- fail-closed validation;
- schema/backend versioning;
- deterministic emitter conventions;
- explicit dependency surfaces;
- case-study authoring methodology.

The current Python contract notation is language-bound. Long term, application
boundaries may need a canonical language-neutral contract representation that
can lower to both Python and TypeScript.

```text
canonical API/data contract
        ├── Python / Pydantic / router
        └── TypeScript client / DTOs
```

OpenAPI/JSON Schema may be emitted interoperability artifacts without becoming a
second manually maintained source of truth.

---

# 18. Editable persistence versus rendered export

Saving an editable planner model and exporting a visual/document artifact are
separate operations.

```text
editable/domain working state
        ↓ persistence contract
private application working storage

editable/domain state
        ↓ renderer/export projection
SVG / Canvas / PDF / DXF / image
```

Rendered SVG, Canvas pixels, PDF, PNG, or DXF must not accidentally become the
only editable source of truth.

Loading durable editable state should eventually follow explicit version/migrate/
validate/replace semantics appropriate to the owning backend/domain.

---

# 19. Initial implementation stack candidates

These are implementation hypotheses, not normative platform dependencies.

## Canvas interaction/rendering

Candidate: **Konva + react-konva** behind `@factory/editor-canvas`.

Use for:

- Canvas scene rendering;
- pointer events;
- hit detection;
- transforms;
- layer redraw/invalidation;
- rendering SVG-derived images/paths where appropriate.

Do not use Konva nodes/serialization as the canonical project model.

## Geometry

Candidate: **`@flatten-js/core`** behind `@factory/editor-geometry`.

Use for low-level intersections, distances, polygons, transforms, and related
geometry where it proves suitable.

Do not leak Flatten-specific types through canonical planner contracts unless a
later decision intentionally standardizes them.

## Symbols

Canonical authoring format candidate: **SVG assets + validated manifests**.

SVG remains useful even if Canvas/Konva is the main interactive renderer.

## Export

Candidate to evaluate later: **Maker.js** or another CAD-oriented export adapter
behind `@factory/editor-export`.

No export dependency is selected by Architecture v0.

---

# 20. First vertical slice / proof of architecture

Before designing a large frontend IR, prove the runtime/package boundaries with
a small Room Planner slice.

The first spike should support:

1. world coordinates in millimetres;
2. four walls forming a closed rectangle through shared nodes;
3. thick-wall projection from centreline + thickness;
4. clean corner joins;
5. dragging a shared corner node while connected walls remain closed;
6. translating/offsetting a wall through explicit commands;
7. at least one T-junction;
8. endpoint/intersection/horizontal/vertical snapping;
9. zoom/pan without changing domain dimensions;
10. one door attached to a wall;
11. the door rendered from an SVG symbol definition;
12. automatic palette population from a symbol registry;
13. one foreign example layer, such as a local plumbing draft line, to prove
    that rendering/editing capability does not imply backend ownership;
14. undo/redo through commands;
15. serialization of editable domain state without serializing Canvas/Konva
    scene objects.

The purpose of the spike is architectural evidence, not UI polish.

If this slice requires planner code to reach into Konva internals, duplicates
world geometry in pixels, stores stale connection coordinates, or performs
backend calls inside reusable layers, the package boundaries should be corrected
before adding more planner features.

---

# 21. Frontend-aware authoring rule

Starting from early design states, every durable model used by an interactive
case should be checked with this question:

> Can the browser editor render, identify, select, reference, and edit the
> concept without inventing a second source of domain truth?

This is a domain-model completeness check, not permission to add React/Canvas
fields to domain models.

A useful progression is:

```text
State 1 — domain data sufficient for projection and stable references
State 2 — validation/topology/snap constraints
State 3 — frontend/backend/domain responsibilities and layer ownership
State 4 — interaction flows, commands, preview/commit semantics
State 5 — public application API required by the browser
State 6 — exact request/response contracts, DTOs, and deterministic frontend IR
```

Framework-specific implementation should be delayed until the relevant product
and interaction decisions are known.

---

# 22. Frontend context manifests

Frontend requirements should not be maintained by copying domain prose into this
file.

A case may define an explicit context manifest, for example:

```text
examples/room-planner/frontend_context.json
```

The manifest lists exact repository-relative Markdown sources/headings relevant
to frontend work. `tools/frontend_context.py` may build deterministic working
context from those declared dependencies.

The manifest is an explicit dependency map, not semantic search. Missing files,
headings, or invalid fields must fail closed rather than silently omitting a
frontend dependency.

Generated context is not canonical source; the referenced design documents
remain authoritative.

---

# 23. Open design questions

The following remain intentionally open until implementation/case evidence exists:

1. Is the proposed package split (`core`, `geometry`, `scene`, `canvas`,
   `svg-symbols`, `react`, `routing`) correct, or should some packages begin
   merged?
2. Does Konva remain sufficiently thin for engineering-editor requirements after
   the first wall/junction spike?
3. Does `@flatten-js/core` cover the required intersection/offset/polygon
   operations cleanly, or should `editor-geometry` use another engine?
4. What exact canonical coordinate quantization is used at commit time: 1 mm,
   sub-mm storage with 1 mm UI snapping, or another policy?
5. What is the canonical T-junction representation?
6. Which wall-join policies are domain-significant versus pure projection?
7. Are rooms canonical entities, derived closed regions, or both under different
   lifecycle states?
8. What is the minimal common `LayerDefinition` schema?
9. Which layer capabilities must be explicit: render, select, inspect, edit,
   snap, persist, publish, export?
10. What is the smallest useful closed command IR?
11. Which preview/commit rules are genuinely shared across planners?
12. Which semantic anchors are generic and which must remain domain-owned?
13. How is a foreign `draft` layer transferred into its owning planner while
    preserving provenance and preventing accidental ownership changes?
14. Which symbol metadata belongs in a future `symbol_catalog_backend/v1`?
15. When are SVG variants enough, and when is a parametric symbol renderer
    justified?
16. Which React layout decisions are stable enough for deterministic lowering?
17. What becomes the canonical language-neutral contract representation for
    Python + TypeScript lowering?
18. Which existing Python-factory dependency/affected-set tools can operate on
    language-neutral symbols without redesign?
19. Which frontend backend should be implemented first after the runtime spike?
20. Which export formats need canonical domain-level semantics versus adapter-only
    rendering?

Until these questions have evidence, Architecture v0 defines boundaries and the
implementation direction without pretending the final frontend IR schema is
already known.
