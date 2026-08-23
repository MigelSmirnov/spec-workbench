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

Until these questions have cross-case evidence, `FRONTEND_EDITOR.md` records the
architectural direction but does not pretend that the final frontend IR schema is
already known.
