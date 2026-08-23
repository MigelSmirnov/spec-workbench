# Frontend Editor

> Living cross-case frontend/editor architecture contract.
>
> Status: architecture working document. This file is developed alongside
> browser-based case studies in the same way that `PLATFORM_ROUTER.md` accumulates
> shared Platform Hub requirements.

## Purpose

Interactive applications need a frontend contract without turning transient UI
state into domain truth or forcing every case study to invent its frontend
boundary again.

For Room Planner the initial delivery target is a **browser editor**. A separate
desktop application is not required by the current product boundary. A future
desktop shell may host the same web application if a real requirement appears,
but no desktop-specific domain model is introduced now.

The architectural shape is:

```text
browser editor
    ↕ explicit application contracts
application backend / domain
    ↕ shared integration contracts
Platform Hub
```

The browser talks to its own application backend for private working state and
interactive editing. It does not route ordinary editor operations through the
Platform Hub.

The Platform Hub remains the shared integration boundary for Registry objects,
Construction Catalog data, published artifacts, publication history, provenance,
and cross-application discovery.

## Authoritative state versus frontend state

The frontend consumes and edits application domain data, but rendered pixels and
interaction state are not domain data.

### Domain-authoritative data

Examples include:

- real-world coordinates and dimensions;
- walls, openings, rooms, surfaces, and stage intent;
- accepted snapshot identities and bases;
- typed provenance/source references;
- validation-relevant construction parameters;
- persisted working drafts that the application intentionally owns.

These facts must remain meaningful without a particular browser library.

### Frontend-only transient state

Examples include:

- viewport pan and zoom;
- current selection and hover state;
- active editor tool/mode;
- drag handles and temporary guides;
- snap hints and cursor previews;
- temporary unconfirmed geometry;
- local panel expansion/collapse;
- purely visual visibility toggles.

These values must not leak into Platform Hub artifacts or accepted domain
snapshots merely because the browser needs them to render an editor.

A later product requirement may justify persisting selected user preferences,
but persistence does not automatically make a value part of the renovation
domain.

## Rendering rule

The browser may use SVG, Canvas, WebGL, DOM, or another suitable rendering
technology. That choice is an implementation detail until a later frontend
architecture decision requires otherwise.

The browser rendering is a **projection of domain geometry**. The rendered scene
must not become an independent geometric source of truth.

For example:

```text
ExistingWall + vertices + thickness
        ↓ browser projection
visible wall shape
```

Dragging or editing may create a transient visual preview, but accepted editor
changes must be expressed back through domain/application operations in
real-world coordinates.

Production drawing/document export is a separate concern. An interactive SVG or
Canvas scene does not imply that Room Planner itself owns production DXF/PDF/SVG
artifact generation.

## Frontend-aware authoring rule

Starting in State 1, every durable domain model used by an interactive case
should be checked with this question:

> Can the browser editor render, identify, select, and edit the concept without
> inventing a second source of domain truth?

This is a model-completeness check, not permission to add React/component fields
to domain models.

Later design states should become progressively more frontend-specific:

```text
State 1 — domain data sufficient for editor projection
State 2 — validation/snap/topology rules that constrain editing
State 3 — frontend/backend/domain responsibilities
State 4 — concrete interaction flows and preview/commit semantics
State 5 — public application API required by the browser
State 6 — exact request/response contracts and DTOs
```

Framework components, event handlers, canvas library APIs, and visual styling
should not be designed before the relevant flows and public contracts are known.

## Frontend context manifests

Frontend requirements should not be maintained by copying domain model prose
into this file.

A case may define a machine-readable frontend context manifest, for example:

```text
examples/room-planner/frontend_context.json
```

The manifest contains explicit repository-relative Markdown source paths and
exact headings that are relevant to frontend work. The tool:

```bash
python tools/frontend_context.py \
  --manifest examples/room-planner/frontend_context.json
```

builds a deterministic working context containing:

- this living frontend boundary when listed by the manifest;
- selected product/frontend constraints;
- selected canonical domain-model sections;
- selected accepted refinements such as provenance or carry-forward models.

The generated context is not canonical source. The referenced Markdown sources
remain authoritative.

### Fail-closed rule

The manifest is an explicit dependency map, not a semantic search query.

If a referenced Markdown file, heading, or manifest field is invalid, the tool
must fail instead of silently omitting the dependency. This makes renamed or
removed models visible during authoring.

The tool must not infer frontend requirements from words such as `wall`, `view`,
`render`, or `editor`, and it must not parse arbitrary model semantics from
prose. Authors explicitly declare which canonical sections matter.

## What belongs in this living contract

Add a requirement here when it is shared frontend/editor architecture rather
than a Room Planner-only domain decision. Examples:

- browser versus desktop delivery boundary;
- authoritative-domain versus transient-editor-state separation;
- rendering-as-projection rule;
- preview/commit separation shared by interactive editors;
- cross-application overlay conventions if they become shared;
- generated TypeScript/client contract expectations if adopted platform-wide;
- accessibility/input-device requirements if they become common platform rules.

Room Planner-specific geometry, demolition semantics, construction systems, and
quantity rules remain in the Room Planner design-state documents.

## Relationship to Platform Hub

`FRONTEND_EDITOR.md` and `PLATFORM_ROUTER.md` accumulate different knowledge:

```text
FRONTEND_EDITOR.md
    browser/editor architecture and interaction boundary

PLATFORM_ROUTER.md
    cross-service Platform Hub integration and artifact boundary
```

A frontend may consume data that originated from the Platform Hub through its
application backend, but this does not make the Hub the application's
backend-for-frontend.

If a future platform feature needs a genuinely shared browser-to-Hub contract,
that requirement must be recorded explicitly in both affected architecture
boundaries rather than appearing accidentally in one case implementation.

## Frontend factory direction

The current working direction is to avoid treating every planner frontend as a
fresh React/TypeScript code-generation problem.

The preferred architecture is a **specification compiler with frontend
backends/emitters**, analogous to deterministic backend emitters already used by
the Python factory. React and Canvas are target runtime technologies, not the
source of product truth.

The key separation is:

```text
product/domain decisions
        ↓
canonical specification / frontend IR
        ↓
validation
        ↓
deterministic lowering where the IR is closed
        ↓
TypeScript/React declarations + shared editor runtime
        ↓
LLM/agent only for explicitly irregular behavior
```

A missing semantic decision must not be silently invented by an emitter. If a
frontend IR block claims ownership of an area, invalid or incomplete IR should
fail closed. LLM fallback is acceptable only for an area that is explicitly not
owned by deterministic IR.

### One compiler, multiple backends

The long-term shape should be one specification system rather than an unrelated
Python factory and frontend factory:

```text
                   PRODUCT SPEC
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
     models           rules           contracts
        │               │                │
        └───────────────┼────────────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ▼                           ▼
   Python backends             Frontend backends
          │                           │
    persistence                 api_client
    router                      react_app
    models                      canvas_editor
    etc.                        forms
          │                           │
          ▼                           ▼
       Python                    TypeScript
                                 + shared
                               Editor Runtime
```

The existing Python factory is therefore a first family of compiler backends,
not necessarily a separate architectural system.

## Shared editor runtime instead of repeated generated code

For browser planners and drawing editors, generic interaction machinery should
preferably be implemented once as a reusable editor runtime rather than emitted
again for each project.

Repeated platform-level concerns likely include:

- scene/layer management;
- camera and real-world ↔ viewport coordinate transforms;
- pan and zoom;
- pointer normalization;
- selection and hover;
- hit testing;
- tool lifecycle;
- command dispatch;
- undo/redo history;
- preview versus commit lifecycle;
- snapping infrastructure;
- drag/move/resize interaction primitives;
- renderer registration;
- keyboard shortcut binding;
- generic toolbar/context-menu command invocation.

Conceptually:

```text
React shell
 ├── Toolbar
 ├── PropertyPanel
 ├── LayerPanel
 └── EditorViewport
          │
          ▼
     Editor Runtime
     ├── Scene
     ├── Camera
     ├── Selection
     ├── ToolController
     ├── CommandBus
     ├── History
     ├── HitTest
     ├── Snapping
     └── Renderer
              │
              ▼
        project declarations
        ├── entity types
        ├── tools
        ├── commands
        ├── constraints
        ├── renderers
        └── rules
```

The factory should generate or compile project declarations and wiring into this
runtime. It should not regenerate generic pointer, history, camera, and
selection algorithms unless a real project requirement makes them irregular.

This is intentionally compatible with the rendering-as-projection rule: the
runtime projects authoritative/domain state and transient interaction previews;
it does not become a second domain model.

## Frontend generation surface

The following areas are strong candidates for deterministic generation or
lowering when their source decisions are closed and machine-readable:

1. TypeScript domain/boundary types from canonical models.
2. Typed browser API clients from application/public contracts.
3. Route/screen registration from a closed navigation catalog.
4. Store/state shape for declared frontend state.
5. Reducers or command wiring for declared state transitions.
6. Forms and property panels from typed field/UI metadata.
7. Toolbar, menu, context-menu, and keyboard shortcut bindings from a command catalog.
8. Canvas/SVG layer registration and stable rendering order.
9. Generic selection, history, pan/zoom, camera, and pointer wiring through the editor runtime.
10. Snapping and editing constraints when represented as structured rules.
11. Entity renderer registration when shape semantics fit a closed renderer DSL/registry.
12. Standard React layout composition from a machine-readable layout tree.
13. Request/response DTOs, loading/error boundaries, and query keys when these derive from declared application contracts.

Areas expected to remain more irregular include highly specialized geometry,
auto-routing, novel direct-manipulation behavior, bespoke visualization, unusual
animation, and intentionally custom interaction patterns for which no stable
cross-case IR yet exists.

## Commands as the primary interaction contract

Planner frontends should be modeled primarily as state + commands + effects +
views, not as a collection of React event-handler implementations.

Typical commands may include:

```text
AddWall
MoveSelection
ResizeRoom
ConnectNode
DeleteSelection
DuplicateSelection
SetProperty
SelectAll
Undo
Redo
ZoomToFit
```

A command contract may eventually declare, in structured form:

- typed input;
- preconditions;
- authoritative state transition or delegated application operation;
- transient preview behavior where relevant;
- history behavior;
- side effects;
- resulting selection/focus behavior;
- validation and constraint policy.

The same command can then be invoked by toolbar actions, keyboard shortcuts,
context menus, or Canvas gestures without duplicating business behavior in each
UI entry point.

Conceptually:

```text
toolbar button ─┐
keyboard binding ├──> command ───> application/editor state transition
canvas gesture  ─┘
```

This reduces generated React code and makes interaction semantics independently
validatable.

## Thin React rule

React components should remain presentation/wiring boundaries in the same sense
that an application HTTP router should remain a thin transport boundary.

A component may:

- render declared state;
- project domain/editor state into visual components;
- bind user input to commands;
- bind forms to typed values;
- display validation/error/loading state;
- compose reusable editor/runtime components.

A component should not become the hidden owner of domain calculations, geometry
policy, persistence semantics, publication rules, or command behavior merely
because the interaction originates from a button or pointer event.

Prefer:

```text
Button / gesture
      ↓
dispatch typed command
      ↓
editor/application behavior
```

over embedding multi-step domain behavior directly inside React handlers.

## Candidate versioned frontend backends

Do not begin with one giant `frontend` schema. Separate concerns into versioned
backend-owned IR families when repeated cases prove the boundary.

Current candidates are:

```text
react_app_backend/v1
canvas_editor_backend/v1
form_backend/v1
api_client_backend/v1
```

Possible responsibilities:

### `react_app_backend/v1`

- screen catalog;
- navigation;
- layout composition;
- standard panels;
- component instances;
- state/view bindings;
- dialogs/modals;
- command bindings.

### `canvas_editor_backend/v1`

- scene/layer catalog;
- tool catalog;
- commands and gesture bindings;
- selection policy;
- history policy;
- camera policy;
- snapping policy;
- hit-test policy;
- renderer registry;
- preview/commit rules.

### `form_backend/v1`

- editable model/DTO fields;
- widget/control selection from closed metadata;
- validation projection;
- grouping/order;
- read-only versus editable fields;
- command or API submit binding.

### `api_client_backend/v1`

- application endpoint exposure to the browser;
- typed parameters/body/result;
- authentication boundary where applicable;
- error mapping;
- request/response serialization;
- deterministic client generation.

These names and exact schemas are provisional. A backend should be introduced
only after multiple real cases reveal a stable class of decisions.

### Regular versus irregular ownership

A useful pattern is the existing deterministic-router distinction between normal
table-driven emission and explicit irregular ownership.

Frontend backends should follow the same principle:

```text
regular declaration
    → validated deterministic emitter/runtime registration

irregular declaration
    → explicit owner module/component/tool
    → LLM/handwritten implementation
```

An irregular area must be explicit. It must not appear because a deterministic
emitter encountered an unknown field and guessed a fallback implementation.

## Reuse from the existing specification standard

Several existing specification concepts are already largely language-neutral
and should be reused instead of duplicated for frontend authoring.

Strong reuse candidates:

- `models` as canonical domain/DTO structure;
- `config` for build/runtime product knobs;
- `rules` for structured read-only policies;
- `properties` for observable invariants where the expression subset applies;
- `determinism` for explicit repeatability requirements;
- classified notes for semantic requirements that are not yet captured by a closed IR;
- dependency graph and affected-set analysis;
- fail-closed validators;
- schema/backend versioning;
- deterministic emitter conventions;
- explicit imports/dependency surfaces;
- authoring states and case-study methodology.

Frontend-specific structured policy should prefer extending the same overall
specification system rather than creating prose-only frontend requirements.

### Contracts need a language-neutral direction

The current Python contract notation is valuable but ultimately language-bound.
A future compiler may need a canonical language-neutral contract representation
from which both Python and TypeScript signatures can be lowered.

Conceptually:

```text
canonical contract
      ├──> Python signature / Pydantic boundary
      └──> TypeScript function/type signature
```

This does not require immediate replacement of existing Python contracts. It is
a direction to avoid making browser/client contracts a separately maintained
source of truth.

## Backend contract reuse for browser API clients

The frontend should not require an independent manually authored copy of the
application API when the backend specification already knows the same boundary.

Where the canonical application spec defines method/path/parameters/auth/result
and canonical request/response types, the same source should be able to lower to
both:

```text
application HTTP router
        ↑
        │
 canonical contracts
        │
        ↓
TypeScript API client
```

OpenAPI may be an emitted interoperability artifact, but it should not
necessarily become a second source of truth if the specification already owns
the contract.

The desired result is that parameter names, DTO fields, result types, route
identity, and error semantics cannot silently drift between Python backend and
TypeScript browser client.

## Notes as an IR-discovery signal

Prose notes remain necessary where the product has made a semantic decision but
no stable closed frontend IR can yet express it.

For example, a domain-specific statement such as:

```text
when connecting two electrical elements, choose the most appropriate compatible
connection type according to the declared domain compatibility policy
```

may initially remain classified behavior.

However, repeated note shapes across several planners are evidence that a new
structured policy or frontend backend is missing.

The intended evolution is:

```text
one-off semantic note
        ↓ repeated across cases
identify common decision class
        ↓
closed structured IR / policy
        ↓
validator + deterministic lowering
```

Notes should therefore be treated not only as LLM input but also as a discovery
surface for future deterministic compiler features.

## Expected deterministic share

These figures are planning hypotheses, not contractual targets.

For a completely arbitrary React application, frontend generation remains highly
underconstrained because visual hierarchy, responsive behavior, composition,
interaction style, and animation admit many valid implementations.

For a narrow family of browser-based engineering planners/editors, the expected
repeatability is much higher because the same editor kernel recurs across cases.

A rough working expectation is:

- an initial frontend factory may deterministically own roughly 50–70% of the conventional structure/wiring;
- after a shared editor runtime, command IR, layout IR, and typed client generation mature, typical planners may reach roughly 70–90% deterministic/runtime-driven structure;
- genuinely prose/LLM-dependent semantic decisions may fall to roughly 10–20% of decisions in ordinary cases, while specialized geometry and novel UX remain explicit irregular islands.

These percentages should be revised from evidence across real case studies rather
than treated as design requirements.

## Relative factory complexity

A universal frontend factory would not necessarily be simpler than the existing
Python factory because arbitrary UI composition is highly underdetermined.

A frontend factory specifically for planners/drawing editors is expected to be
simpler in an important way: many apparently complex interactions belong to one
shared runtime rather than to generated per-project code.

Backend applications may vary across persistence, authentication, files,
external APIs, transactions, queues, LLM calls, calculations, exports, and other
unrelated mechanisms. By contrast, planner frontends repeatedly use a narrower
architectural family:

```text
scene
+ tools
+ canvas/svg projection
+ commands
+ history
+ panels
+ typed application client
```

The major complexity should therefore be concentrated in the reusable editor
runtime and a small number of deterministic frontend backends. Individual
projects should mostly supply domain types, policies, commands, renderer/tool
declarations, and irregular extensions.

## Reusable editor packages and capability composition

The shared runtime should not necessarily become one monolithic package. The
planner family is expected to benefit from several small packages with explicit
capabilities and dependency direction.

A provisional decomposition is:

```text
@factory/editor-core
    commands
    undo/redo history
    selection
    tool lifecycle
    preview/commit lifecycle
    transient editor state primitives

@factory/editor-geometry
    point/vector/segment/rect/transform primitives
    local ↔ world transforms
    world ↔ viewport transforms
    rotation
    generic hit-test primitives
    generic snapping primitives

@factory/editor-scene
    scene/layer registry
    entity definition registry
    entity instances
    anchors/ports
    relations/connections
    renderer capability registration

@factory/editor-canvas
    Canvas-specific renderer adapter
    camera integration
    pointer normalization
    render loop
    picking integration

@factory/editor-svg
    SVG-specific renderer adapter
    path/marker helpers
    SVG projection utilities

@factory/editor-react
    viewport shell
    toolbar/palette/property panels
    layer panel
    command bindings
    standard interaction composition

@factory/editor-routing
    connection routing
    orthogonal routing where requested
    anchor-direction-aware route helpers
```

These names are provisional. Package boundaries should be validated by real
planner implementations before becoming platform API commitments.

A project should import only the capabilities it needs. A form-heavy planner may
use `editor-core` and `editor-react` without a drawing renderer. A Room Planner
may use core + geometry + scene + Canvas + React. An electrical schematic editor
may additionally use SVG or routing capabilities.

The purpose of package decomposition is not package-count optimization. It is to
prevent React, Canvas, SVG, routing, persistence, or one domain's assumptions
from leaking into the shared semantic core.

## Definition versus instance

Reusable editor entities should distinguish a reusable **definition** from a
concrete **instance**.

A definition describes reusable rendering/interaction capabilities. An instance
represents a concrete object participating in a scene or projection.

Conceptually:

```text
EntityDefinition
    stable type/capability identity
    metadata
    default/local geometry when applicable
    anchors/ports
    renderer capability key
    optional interaction capabilities

EntityInstance
    stable instance identity
    definition/type reference
    authoritative domain reference/state
    transform where the entity model requires one
```

The exact fields must remain domain-appropriate. A wall, room polygon, plumbing
fixture, and electrical symbol do not all have to fit one simplistic
`x/y/rotation` record.

The important rule is that reusable visual definitions must not be duplicated
inside every scene instance, and scene instances must not duplicate rendered SVG
or Canvas instructions as authoritative data.

Renderer bindings should preferably use renderer capabilities/registry keys
rather than making the scene model depend directly on `React.ComponentType` or
another framework-specific type.

## Coordinate-space contract

Engineering editors need explicit coordinate spaces. Ambiguous coordinates are
a source of both rendering defects and domain corruption.

The general projection chain is:

```text
definition-local coordinates
        ↓ entity/domain transform
world/domain coordinates
        ↓ camera/viewport transform
viewport coordinates
        ↓ device scaling
screen/device coordinates
```

Pointer input follows the inverse path before an accepted command changes domain
geometry.

Domain/world units MUST NOT become viewport units merely because a renderer uses
pixels internally. Real dimensions remain meaningful independently of zoom,
pan, device pixel ratio, SVG viewBox, or Canvas backing-store resolution.

Local renderer geometry should be expressed in its own local frame when the
concept has one. Camera state, pan/zoom, and viewport placement are owned outside
the renderer definition.

## Semantic anchors and derived render coordinates

Reusable connections and attachment points should refer to semantic anchors,
not permanently stored render coordinates.

`Anchor` is the general concept. Domain-specific anchor kinds may include:

- element connection ports;
- wall endpoints or midpoints;
- wall faces;
- room vertices;
- opening attachment positions;
- plumbing connection points;
- electrical terminals;
- other explicitly addressable geometric attachment points.

A connection or relation should preserve semantic topology such as:

```text
entity A + anchor outlet
        ↓
entity B + anchor inlet
```

rather than persisting stale endpoint pixels such as:

```text
fromX/fromY/toX/toY
```

Rendering resolves current anchor positions from the authoritative entities and
then derives connection geometry. Moving, rotating, resizing, or otherwise
changing an entity must therefore update the rendered connection without
rewriting its semantic endpoint identity.

The general rule is:

> Persist semantic references; derive render coordinates.

This is broader than pipe/electrical ports and should apply anywhere a planner
can express stable attachment semantics.

## Topology versus derived geometry

For connected editor concepts, topology and displayed path geometry are separate
meanings.

Conceptually:

```text
stored relation
    A.anchor-1 → B.anchor-4

render projection
    resolve anchors
        ↓
    calculate world positions
        ↓
    choose routing/projection policy
        ↓
    draw current path
```

The route may be straight, orthogonal, curved, automatically routed, or custom.
That rendering choice must not silently change which domain entities are
connected.

A domain may intentionally own route geometry when the physical path itself is
meaningful — for example, a real pipe run with bends. In that case the route is
explicit domain data, not renderer-generated connection decoration. The spec
must distinguish those cases rather than letting the renderer guess ownership.

## Stable durable identity

Durable entities that can be referenced by other entities, layers, artifacts, or
applications require stable identities appropriate to their domain semantics.

Array position, React key order, current draw order, SVG node identity, Canvas
index, and transient selection index are not durable cross-model identities.

This matters especially when one planner projects another planner's published
or accepted data. Plumbing, electrical, tile, estimating, and downstream drawing
systems must be able to refer to stable wall/room/surface identities without
scraping the visual scene.

Stable identity requirements remain domain decisions; this frontend rule does
not imply adding arbitrary IDs to value concepts that do not have independent
identity in the canonical model.

## Editable persistence versus rendered export

Saving an editable planner model and exporting a rendered document are separate
operations.

Conceptually:

```text
editable/domain working state
        ↓ persistence contract
private application working storage

editable/domain state
        ↓ renderer/export projection
SVG / Canvas pixels / PDF / image / drawing artifact
```

Rendered SVG, Canvas pixels, PDF, PNG, or other presentation output must not
become the only persisted editable source merely because it is convenient to
serialize.

When an application loads durable editable state, the eventual persistence
contract should support explicit schema/version handling, migration when
required, structural/domain validation, and only then replacement of current
working state.

The exact persistence owner remains the application/backend design. This rule
only protects the distinction between editable state and visual/export
projection.

## Cross-planner layer composition

The planner family should converge on a common editor workspace in which domain
capabilities can be composed as layers rather than each application reimplementing
foreign visualization from scratch.

A useful conceptual shape is:

```text
shared editor workspace
        │
        ├── room/wall layer
        ├── plumbing layer
        ├── electrical layer
        ├── tile layer
        └── annotations / auxiliary layers
```

A Room Planner, Plumbing Planner, Electrical Planner, or another planner may
therefore load several layer packages into the same scene. This makes common
geometry, navigation, selection, visibility, rendering, anchors, and snapping
infrastructure reusable across applications.

Applications should not import each other as whole applications. Reuse should
happen through shared editor packages and domain/editor layer packages with
explicit public boundaries.

Conceptually:

```text
@planner/walls-layer
@planner/plumbing-layer
@planner/electrical-layer
@planner/tiles-layer
```

A layer package may expose domain/editor-facing definitions such as:

- model/boundary types needed for projection;
- renderers;
- tools and command declarations;
- anchors;
- hit-test behavior;
- snapping policies;
- property descriptors;
- editor-side validation useful for interaction;
- layer metadata and visibility behavior.

A layer package must not gain persistence authority merely because another
application imported it.

## Layer ownership modes

Rendering, editing, persistence, and publication are separate capabilities. A
planner being able to display or manipulate a layer does not mean it owns the
layer's authoritative domain state.

The current working model distinguishes three layer modes.

### `owned`

The current application owns the authoritative working state for that layer.

Typical capabilities:

```text
render = yes
edit = yes
persist through current application backend = yes
publish under current application's declared contracts = when product flow allows
```

Examples may include walls in Room Planner or plumbing entities in Plumbing
Planner.

### `reference`

The current application consumes another domain's accepted/published/otherwise
resolved state for context.

Typical capabilities:

```text
render = yes
edit authoritative source = no
persist foreign authoritative state = no
publish foreign domain = no
```

For example, Plumbing Planner may render a Room Planner wall/room basis while
owning only plumbing changes.

### `draft`

The current application may host an uncommitted/local proposal using another
layer capability without thereby becoming the authoritative owner of that
foreign domain.

Typical capabilities:

```text
render = yes
edit local draft = yes
persist as host-private/local overlay = optional explicit product decision
write foreign authoritative backend = no
publish as foreign authoritative artifact = no
```

A draft may later be transferred/opened in the owning planner, validated under
that planner's domain rules, and converted into owned working state through an
explicit application flow.

The exact transfer protocol is not yet defined. The architectural point is that
"the user can draw it here" does not imply "this application now owns that
domain".

## Rendering capability is not data ownership

The following distinctions are normative architectural direction:

> Rendering capability is not data ownership.

> Editing capability is not persistence authority.

> Importing a layer package is not authorization to mutate the layer owner's
> backend.

A Room Planner may be technically capable of showing or locally sketching pipes
without exposing Room Planner backend endpoints for authoritative plumbing
state. Likewise, a plumbing or electrical application may reuse wall rendering,
selection, snapping, and geometry capabilities without becoming the owner of
room geometry.

This protects planner boundaries while allowing a rich cross-domain workspace.

## Layer packages must not own backend transport

Reusable layer packages should not directly call their domain backend as part of
rendering or ordinary editor behavior.

Avoid coupling such as:

```text
@planner/plumbing-layer
    → fetch('/plumbing/...')
```

Prefer:

```text
plumbing layer capabilities
        ↓ typed editor/domain operations
host application adapter
        ↓
application client/backend boundary
```

The host application decides which operations have persistence authority. A
foreign/reference layer can therefore be imported safely without accidentally
acquiring backend write capability.

Generated TypeScript API clients belong to explicit application integration
boundaries, not implicitly inside reusable render packages.

## Code reuse, data exchange, and data ownership are separate axes

Cross-planner architecture should preserve three independent meanings:

```text
code reuse
    shared editor packages + reusable layer packages

data exchange
    stable application/platform contracts and Platform Hub artifacts

data ownership
    the application/domain backend that owns authoritative working state
```

These mechanisms should not be collapsed into one another.

Sharing `@planner/walls-layer` does not mean Plumbing Planner reads Room Planner's
private database. Consuming `room_plan.v1` does not mean the consumer owns wall
editing. Drawing a local pipe overlay in another planner does not publish a
plumbing artifact.

The Platform Hub remains the cross-application data/artifact boundary described
in `PLATFORM_ROUTER.md`; reusable frontend packages are a code-sharing mechanism,
not an alternative integration mesh.

## Planner applications as workspace configurations

If the shared packages and ownership rules prove stable, several planner
frontends may become relatively small configurations of one engineering editor
workspace.

Conceptually:

```text
Room Planner
    shared editor shell
    + room/wall owned layers
    + demolition/construction capabilities
    + optional foreign reference/draft layers
    + Room Planner application adapter

Plumbing Planner
    shared editor shell
    + room/wall reference layers
    + plumbing owned layer
    + optional electrical/tile reference layers
    + Plumbing application adapter

Electrical Planner
    shared editor shell
    + room/wall reference layers
    + electrical owned layer
    + optional plumbing reference layer
    + Electrical application adapter
```

This is a desirable convergence direction, not permission to erase domain
boundaries. The applications may share most editor mechanics while still having
different authoritative models, validation, backend endpoints, publication
contracts, and Platform Hub artifacts.

## Open design questions

The following should be resolved through real case studies rather than fixed in
advance:

1. Which editor concerns belong in a reusable runtime versus generated project code?
2. What is the smallest useful closed command IR?
3. Which preview/commit semantics are genuinely cross-case?
4. How should structured snapping/constraint policies reference domain rules?
5. Which renderer shapes are common enough for a closed renderer DSL, and which remain custom code?
6. Should frontend-only persisted preferences have a dedicated spec area separate from domain models?
7. What becomes the canonical language-neutral contract representation for Python + TypeScript lowering?
8. How should deterministic frontend backend ownership interact with classified notes and irregular modules?
9. Which React layout decisions are stable enough to compile without over-constraining product UX?
10. Which existing Python-factory dependency/affected-set tools can be reused unchanged versus generalized to language-neutral symbols?
11. Which frontend backend should be implemented first to produce the highest evidence value across planners?
12. Which proposed editor packages are stable cross-case boundaries and which should remain one package initially?
13. What is the minimal common `LayerDefinition` contract across room, plumbing, electrical, tile, and other planners?
14. Which layer capabilities must be declared explicitly: render, select, edit, snap, persist, publish, export?
15. How should a foreign `draft` layer be transferred to its owning planner without confusing provenance or ownership?
16. Which semantic anchor kinds can be generic and which must remain domain-owned?
17. How should a host application resolve compatible versions of reusable layer packages and artifact schemas independently?

Until these questions have cross-case evidence, `FRONTEND_EDITOR.md` records the
architectural direction but does not pretend that the final frontend IR schema is
already known.