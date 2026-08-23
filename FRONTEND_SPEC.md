# Frontend Specification

> Draft authoring/compiler contract for `frontend_spec/v1`.
>
> Status: working design. This document defines the smallest useful frontend
> specification shape to prove against Room Planner before it is promoted into a
> normative standard.

`FRONTEND_EDITOR.md` defines the shared editor architecture and ownership
boundaries. This document answers a different question:

> Which frontend decisions must be authored, which facts are derived from the
> backend specification, which behavior comes from reusable packages, and what
> should the frontend compiler emit deterministically?

The goal is not to describe React files. The goal is to describe a planner
workspace as machine-readable decisions and references to declared capabilities.

---

# 1. Core compilation model

The frontend build has four distinct sources of truth.

```text
1. backend canonical specification
        models / contracts / browser-visible HTTP surface / errors

2. frontend_spec.yaml
        workspace composition / layers / tools / symbols / bindings / panels

3. reusable package manifests
        capabilities / commands / renderers / snap providers / layer definitions

4. explicit irregular code
        project-specific behavior not represented by closed IR
```

They compile into one validated frontend IR:

```text
backend global_spec.json
        │
        ├── derive browser contract IR
        │
frontend_spec.yaml
        │
package manifests
        │
        ▼
FRONTEND NORMALIZER
        │
        ▼
validated frontend_ir.json
        │
        ├── TypeScript models/client
        ├── workspace registration
        ├── layer registration
        ├── tools/bindings
        ├── palette/symbol registry
        ├── panel/layout config
        └── irregular imports
        │
        ▼
shared editor runtime + reusable planner layers
        │
        ▼
browser application
```

A decision must have one owner. The frontend spec MUST NOT manually duplicate a
fact that can be derived canonically from the backend specification or a package
manifest.

---

# 2. What is derived from the backend specification

The Python/backend specification remains the source of truth for the application
boundary it already owns.

The frontend compiler should derive at least the following from canonical backend
spec data when available:

- browser-visible request/response models;
- enums and discriminated unions used by those models;
- browser-visible operation identities;
- HTTP method and path;
- path/query/body parameter names and types;
- return/result type;
- authentication requirement represented by the router IR;
- success response mode/status where relevant to client generation;
- canonical error mapping exposed by the HTTP boundary;
- serialization/deserialization shape;
- model schema/version information required by the browser boundary.

The browser-visible operation catalog SHOULD be derived from the deterministic
HTTP-router IR rather than from every Python `contract`. The existence of an
internal Python function does not make it a browser API.

Conceptually:

```text
contracts + models + http_router_backend/v1
                │
                ▼
        browser_contract_ir
                │
        ┌───────┴────────┐
        ▼                ▼
FastAPI router      TypeScript client
```

The frontend specification MUST NOT restate method/path/signature/body/result for
an operation already owned by the canonical backend contract.

A frontend tool or form may reference a browser operation by stable operation
identity, for example:

```yaml
submit:
  operation: project.update_draft
```

The referenced operation must exist in `browser_contract_ir` or validation fails.

---

# 3. What is authored in `frontend_spec.yaml`

The frontend spec owns decisions that the backend cannot infer safely:

- which workspace kind the application uses;
- renderer/runtime policy;
- which reusable layers are loaded;
- ownership mode of each loaded layer;
- which tools are exposed;
- which reusable commands/capabilities tools invoke;
- which symbols/catalogs appear in palettes;
- keyboard/gesture/menu bindings;
- standard panel/layout composition;
- visibility and editor-only presentation policy;
- explicit irregular owners.

The frontend spec describes capabilities and composition. It MUST NOT prescribe
TypeScript filenames, React component internals, Konva nodes, JSX, or imperative
pointer-handler algorithms.

---

# 4. What is implemented once in reusable packages

Reusable packages own algorithms and behavior that should not be regenerated for
every planner.

Examples:

```text
@factory/editor-core
    command bus / selection / undo-redo / tool lifecycle

@factory/editor-geometry
    intersections / projection / coordinate transforms / snap primitives

@factory/editor-scene
    layer registry / anchors / renderer registration

@factory/editor-canvas
    Canvas adapter / pointer normalization / picking

@factory/editor-svg-symbols
    SVG symbol loading / validation / projection

@factory/editor-react
    workspace shell / palette / panels / toolbar

@planner/building-layer
    wall nodes / walls / joins / openings / building commands
```

For example, `frontend_spec.yaml` may request capability
`building.wall.create`; it does not cause the emitter to invent a wall-creation
algorithm. The capability must be provided by a declared package manifest.

---

# 5. What remains handwritten or LLM-generated

Handwritten/LLM code is allowed only for explicitly declared irregular areas.

Typical examples:

- novel direct-manipulation behavior with no reusable capability yet;
- highly specialized domain geometry;
- unique visualization;
- one-off workflow UI that does not fit the standard workspace composition;
- an experimental interaction being evaluated before promotion to shared IR.

The intended lifecycle is:

```text
one irregular implementation
        ↓
repeated in several planners
        ↓
identify stable semantic class
        ↓
shared package capability or closed frontend IR
        ↓
deterministic use thereafter
```

An emitter MUST NOT fall back to LLM because deterministic IR is invalid.

---

# 6. Proposed top-level `frontend_spec/v1`

The initial author-facing file is YAML for readability. The normalizer may lower
it to canonical JSON IR.

Closed top-level shape for the first experiment:

```yaml
kind: frontend_spec
schema_version: 1

application: {}
runtime: {}
layers: {}
tools: []
symbols: {}
bindings: {}
panels: {}
irregular: []
```

Unknown top-level fields are invalid in v1.

Sections should remain small. New sections are introduced only after a real case
proves that the decision cannot be derived from backend contracts or package
manifests and cannot be expressed by an existing section.

---

# 7. `application`

Minimal identity and workspace selection:

```yaml
application:
  id: room_planner
  workspace: engineering_editor
```

Rules:

- `id` is a stable application identifier.
- `workspace` selects a supported shared workspace family.
- v1 SHOULD initially support only `engineering_editor` for planner cases rather
  than becoming a universal application-layout language.
- application title/branding should not be added here unless a real deterministic
  consumer needs it.

---

# 8. `runtime`

Runtime contains frontend-only policies that cannot be inferred from domain
models.

Initial candidate:

```yaml
runtime:
  renderer: canvas
  world_unit: mm
  edit_precision_mm: 1
```

Closed candidate fields:

- `renderer`: initial registry `canvas | svg`; `canvas` is expected for Room
  Planner.
- `world_unit`: initial planner value `mm`.
- `edit_precision_mm`: explicit user-edit/commit precision policy.

The frontend spec must not name Konva, Flatten, React, or other third-party
libraries. Those are implementation choices behind shared packages.

If `world_unit` or precision is canonical domain policy in a future common spec,
this section should reference/derive it rather than duplicate it.

---

# 9. Package capability manifests

The frontend spec should reference semantic capabilities rather than package
internals. To make this possible, each reusable editor/domain package exposes a
machine-readable manifest.

Conceptual manifest:

```yaml
kind: frontend_package_manifest
schema_version: 1
package: "@planner/building-layer"
version: 0.1.0

provides:
  capabilities:
    - building.wall.render
    - building.wall.create
    - building.wall.move_node
    - building.wall.translate
    - building.wall.offset
    - building.opening.place
    - building.snap.endpoint
    - building.snap.intersection

  commands:
    - building.add_wall
    - building.move_wall_node
    - building.translate_wall
    - building.offset_wall
    - building.place_opening

  renderers:
    - building.wall
    - building.opening

  snap_providers:
    - building.endpoints
    - building.intersections
```

The exact manifest schema is provisional, but the ownership rule is not:

> The package declares what it can do; the application frontend spec declares
> which of those capabilities are enabled/composed for this workspace.

Package manifests MUST NOT grant backend authorization and SHOULD NOT contain
implicit backend URLs.

---

# 10. `layers`

Layers compose reusable planner/domain capabilities in one workspace.

Candidate shape:

```yaml
layers:
  building:
    provider: "@planner/building-layer"
    mode: owned
    visible: true

  plumbing:
    provider: "@planner/plumbing-layer"
    mode: draft
    visible: true

  electrical:
    provider: "@planner/electrical-layer"
    mode: reference
    visible: false
```

Required fields:

- `provider`: package manifest identity.
- `mode`: `owned | reference | draft`.

Optional v1 field:

- `visible`: initial editor visibility only; it is not domain state.

Mode is authority, not styling.

### `owned`

The current application owns authoritative working state for this layer. The
frontend may expose edit commands supplied by the layer, but actual persistence
still occurs only through explicit host application operations/adapters.

### `reference`

The layer may render/inspect resolved foreign state but cannot expose commands
that mutate the foreign authoritative source.

### `draft`

The host may expose local proposal/edit commands, but those commands cannot call
or imply foreign authoritative persistence.

Validator rules MUST prevent a reference layer from binding authoritative edit
commands and MUST prevent draft/reference package composition from acquiring
foreign backend write authority merely through import.

---

# 11. `tools`

Tools expose reusable behavior to the user. They bind UI tool identity to a
shared capability/command; they do not contain implementation algorithms.

Candidate shape:

```yaml
tools:
  - id: select
    builtin: editor.select

  - id: wall
    command: building.add_wall
    requires:
      - building.wall.create

  - id: move_wall_node
    command: building.move_wall_node
    requires:
      - building.wall.move_node

  - id: door
    command: building.place_opening
    symbol: door.single.left
    requires:
      - building.opening.place
```

Exactly one of `builtin` or `command` is required.

`requires` is a list of capability identities and MUST resolve against loaded
package manifests. A missing capability is a validation error.

`symbol` is optional and references the normalized symbol registry.

A tool does not directly name React components or pointer handlers.

---

# 12. `symbols`

SVG remains an authoring asset; the frontend spec composes accepted symbol
catalogs rather than embedding SVG markup.

Candidate shape:

```yaml
symbols:
  catalogs:
    - building.standard
    - plumbing.standard
```

A symbol catalog is produced from validated symbol manifests, conceptually:

```yaml
kind: symbol_manifest
schema_version: 1
id: door.single.left
title: Single door — left hinge
category: doors
asset: symbols/doors/single-left.svg
view_box: [0, 0, 100, 100]
default_size_mm:
  width: 900
  height: 100
anchors:
  - id: mount
    kind: wall_attachment
    local: [0, 50]
```

The symbol pipeline should be:

```text
agent/human authored SVG + manifest
        ↓ validate
versioned symbol catalog
        ↓ frontend compiler
registry + palette
        ↓ runtime
Canvas/SVG projection
```

No LLM is required at runtime after a symbol is accepted.

---

# 13. `bindings`

Bindings map standard user inputs to commands/tools without duplicating command
behavior.

Candidate v1 shape:

```yaml
bindings:
  keyboard:
    - key: Delete
      command: editor.delete_selection

    - key: Ctrl+Z
      command: editor.undo

    - key: Ctrl+Shift+Z
      command: editor.redo

    - key: Escape
      command: editor.cancel_tool
```

V1 should begin with keyboard bindings only. Pointer gesture grammar should not
be standardized until the wall-tool spike proves a stable representation.

Every referenced command must be supplied by the editor runtime or a loaded
package manifest.

Conflicting key bindings are invalid unless a future version defines explicit
scope/priority semantics.

---

# 14. `panels`

V1 should describe only standard workspace composition, not arbitrary React
layout.

Candidate shape:

```yaml
panels:
  left:
    - palette
    - layers

  right:
    - properties

  bottom:
    - status
```

Initial closed panel registry may include:

```text
palette
layers
properties
status
history
```

Unknown standard panel IDs are invalid. Bespoke panels belong in `irregular`
until repeated evidence justifies a new standard panel contract.

Panel entries select standard runtime capabilities. They do not point to JSX
filenames.

---

# 15. Browser operations referenced by frontend behavior

A frontend specification may bind a standard form/action to an existing backend
operation, but it must reference the canonical derived operation rather than
restate HTTP data.

Conceptual future extension:

```yaml
submit:
  operation: project.save_draft
```

The operation resolver reads canonical metadata from `browser_contract_ir`:

```text
project.save_draft
    method
    path
    request model
    response model
    auth
    errors
```

The frontend compiler then emits the typed client call and conventional
loading/error wiring.

V1 does not need a generic action/form language until Room Planner produces a
real browser flow requiring it. The important rule is already fixed: HTTP
contract data is referenced, never copied.

---

# 16. `irregular`

Irregular entries explicitly name code that lies outside deterministic frontend
ownership.

Candidate shape:

```yaml
irregular:
  - id: special_room_detection
    owner: features/special-room-detection
    reason: domain-specific interaction not represented by frontend_spec/v1
```

Required fields:

- `id`: unique stable irregular identity.
- `owner`: module/package boundary responsible for implementation.
- `reason`: short architectural reason the behavior is not represented by
  deterministic IR.

Rules:

- irregular ownership must not overlap a deterministic section silently;
- an irregular owner may consume generated types/runtime capabilities;
- an irregular owner must obey the same domain/editor/backend ownership rules;
- irregular code is not permission to mutate foreign backend state;
- repeated irregular shapes should trigger review for promotion into a reusable
  capability or future IR version.

---

# 17. Room Planner candidate `frontend_spec.yaml`

The first implementation should attempt to compile something approximately this
small:

```yaml
kind: frontend_spec
schema_version: 1

application:
  id: room_planner
  workspace: engineering_editor

runtime:
  renderer: canvas
  world_unit: mm
  edit_precision_mm: 1

layers:
  building:
    provider: "@planner/building-layer"
    mode: owned
    visible: true

  plumbing:
    provider: "@planner/plumbing-layer"
    mode: draft
    visible: true

  electrical:
    provider: "@planner/electrical-layer"
    mode: reference
    visible: false

tools:
  - id: select
    builtin: editor.select

  - id: wall
    command: building.add_wall
    requires: [building.wall.create]

  - id: move_wall_node
    command: building.move_wall_node
    requires: [building.wall.move_node]

  - id: door
    command: building.place_opening
    symbol: door.single.left
    requires: [building.opening.place]

symbols:
  catalogs:
    - building.standard

bindings:
  keyboard:
    - { key: Delete, command: editor.delete_selection }
    - { key: Ctrl+Z, command: editor.undo }
    - { key: Ctrl+Shift+Z, command: editor.redo }
    - { key: Escape, command: editor.cancel_tool }

panels:
  left: [palette, layers]
  right: [properties]
  bottom: [status]

irregular: []
```

This example deliberately does not contain:

- wall geometry algorithms;
- SVG markup;
- HTTP paths;
- request/response DTO definitions;
- React component names;
- Konva objects;
- persistence implementation;
- Platform Hub calls.

Those decisions have other owners.

---

# 18. Normalized frontend IR

`frontend_spec.yaml` is authoring syntax. The compiler should normalize it into a
strict machine representation before any emission.

Conceptually:

```text
frontend_spec.yaml
        + browser_contract_ir
        + package manifests
        + symbol manifests
        ↓
normalize + resolve + validate
        ↓
frontend_ir.json
```

The normalized IR should replace loose references with resolved identities while
preserving source/provenance for diagnostics.

For example a normalized tool record may contain:

```json
{
  "id": "wall",
  "command": "building.add_wall",
  "provider": "@planner/building-layer",
  "required_capabilities": ["building.wall.create"],
  "layer": "building"
}
```

The exact normalized schema should be derived from implementation needs; it is
not necessary to expose compiler-only lowering details to authors.

---

# 19. Validation / fail-closed rules

The first validator should reject at least:

1. unknown top-level fields;
2. unsupported `schema_version`;
3. unsupported workspace/renderer/unit;
4. duplicate tool IDs;
5. missing package manifests;
6. requested capabilities not supplied by loaded packages/runtime;
7. requested commands not supplied by loaded packages/runtime;
8. symbol references not present in loaded catalogs;
9. invalid symbol manifests/SVG policy violations;
10. duplicate/conflicting keyboard bindings;
11. unknown standard panel IDs;
12. `reference` layers exposing authoritative edit commands;
13. foreign `draft` layers attempting authoritative persistence;
14. frontend records that duplicate/redefine canonical HTTP method/path/signature
    fields;
15. referenced browser operation absent from backend-derived
    `browser_contract_ir`;
16. irregular IDs without explicit owners/reasons;
17. overlapping deterministic and irregular ownership without an explicit future
    extension mechanism.

A validation failure blocks deterministic emission. It does not switch to an LLM
fallback.

---

# 20. Deterministic compiler outputs

A successful compile should be capable of producing conventional generated files
such as:

```text
src/generated/
    models.generated.ts
    api.generated.ts
    errors.generated.ts
    workspace.generated.ts
    layers.generated.ts
    tools.generated.ts
    bindings.generated.ts
    panels.generated.ts
    symbols.generated.ts
    irregular.generated.ts
```

Exact filenames are emitter implementation details, not authoring spec fields.

The generated workspace should be thin enough that application bootstrap is
conceptually equivalent to:

```ts
createEngineeringWorkspace(generatedWorkspace)
```

Generated files should not contain domain algorithms already owned by reusable
packages.

---

# 21. Deterministic versus handwritten boundary

Working ownership table:

| Area | Owner | Per-project generation |
| --- | --- | --- |
| Browser DTO/types | backend canonical spec | deterministic |
| Browser API client | backend router/contracts | deterministic |
| HTTP method/path/auth/errors | backend canonical spec | derived, never duplicated |
| Workspace/layers | `frontend_spec.yaml` | deterministic |
| Tool registration | `frontend_spec.yaml` + package manifests | deterministic |
| Keyboard bindings | `frontend_spec.yaml` | deterministic |
| Standard panels | `frontend_spec.yaml` | deterministic |
| Symbol registry/palette | symbol manifests + frontend spec | deterministic |
| Canvas interaction engine | shared editor package | written once |
| Geometry primitives | shared editor package | written once |
| Wall/junction algorithms | `building-layer` | written once |
| Undo/redo/selection | shared editor package | written once |
| SVG symbol artwork | agent/human authoring | authored once per symbol/variant |
| Novel project behavior | explicit `irregular` owner | handwritten/LLM |
| Foreign domain persistence | owning planner backend only | never gained by frontend import |

This table should be reviewed whenever a new proposed frontend field appears. If
it merely duplicates backend truth or a reusable package algorithm, it should not
enter `frontend_spec/v1`.

---

# 22. V1 intentional non-goals

Do not solve these in v1 unless the first Room Planner implementation proves they
are required:

- arbitrary React component graph generation;
- general CSS/theme DSL;
- general pointer gesture language;
- arbitrary state-machine language;
- arbitrary command implementation language;
- parametric SVG programming language;
- generic form system for every application type;
- universal frontend framework support;
- cross-planner draft transfer protocol;
- production drawing/export schema;
- WebGL-specific renderer IR;
- automatic inference of layer ownership from package names or backend endpoints.

Keeping v1 small is intentional. The first objective is to prove deterministic
composition, not to model every UI decision.

---

# 23. First implementation order

Recommended evidence-driven order:

1. Define `frontend_spec/v1` validator for the closed top-level sections.
2. Define minimal package manifest schema and manifests for `editor-core` and
   `building-layer`.
3. Derive a small `browser_contract_ir` from one real backend/router spec.
4. Define symbol manifest validation for one door SVG.
5. Normalize the Room Planner YAML example into `frontend_ir.json`.
6. Emit workspace/layer/tool/binding/symbol registries.
7. Connect emitted registrations to the Room Planner wall/junction runtime spike.
8. Verify that removing a capability, command, symbol, or backend operation fails
   closed with a precise diagnostic.
9. Add one explicit irregular module to prove the boundary.
10. Only then decide whether forms, pointer gestures, richer layout, or additional
    backend families deserve v1 extensions.

The first successful milestone is not a polished application. It is:

> A small Room Planner frontend can be rebuilt from backend spec +
> `frontend_spec.yaml` + package/symbol manifests, while reusable algorithms live
> outside the generated project and invalid composition is rejected before code
> generation.

---

# 24. Open questions for `frontend_spec/v1`

The following remain intentionally unresolved until the first compiler spike:

1. Should package identities/versions be listed explicitly in `frontend_spec`, or
   resolved from layer/tool capability providers by the build system?
2. Should `visible` remain in the spec or be treated as a frontend preference?
3. Should tools bind directly to commands, capabilities, or a separate tool
   definition registry supplied by packages?
4. How should an owned layer declare which host backend operations persist it,
   without duplicating backend contracts?
5. What stable operation identity should `browser_contract_ir` use?
6. Should symbol catalogs be package manifests, separate catalog files, or both?
7. What is the minimum metadata required to safely project an SVG symbol into
   millimetre world space?
8. When does a pointer gesture representation become stable enough for closed IR?
9. How should standard property panels obtain editable field metadata without
   duplicating domain model semantics?
10. Should package manifest compatibility reference frontend IR versions, editor
    runtime versions, or both?
11. What provenance should `frontend_ir.json` retain for diagnostics and
    affected-set rebuilds?
12. Which current `SPEC_STANDARD` dependency tools can be generalized to validate
    capability and operation references across Python and TypeScript outputs?

Until these have implementation evidence, `frontend_spec/v1` should remain a
small composition language rather than a universal UI description format.
