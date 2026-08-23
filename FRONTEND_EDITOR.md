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
