# Frontend Package Manifest

> Draft compiler/linker contract for `frontend_package_manifest/v1`.
>
> Status: working design. This document defines how reusable frontend/editor
> packages declare capabilities to `frontend_spec/v1` without exposing package
> internals or duplicating application/backend contracts.

`FRONTEND_EDITOR.md` defines the architecture. `FRONTEND_SPEC.md` defines the
application authoring file. This document defines the third input to the frontend
compiler: **package manifests**.

A package manifest answers:

> What stable frontend capabilities does this package provide, what does it
> require, which public exports implement those capabilities, and under which
> layer ownership modes may they be used?

The manifest is a linker contract. It is not a second `package.json`, not a file
layout description, and not prose documentation of implementation algorithms.

---

# 1. Position in the compiler pipeline

```text
backend canonical spec
        │
frontend_spec.yaml
        │
package manifests ───────────────┐
        │                        │
symbol manifests                 │
        │                        │
        ▼                        │
frontend normalizer              │
        │                        │
        ▼                        │
capability/link validation ◄─────┘
        │
        ▼
validated frontend_ir.json
        │
        ▼
generated imports/registries/wiring
```

`frontend_spec.yaml` requests capabilities. Package manifests prove that the
requested capabilities exist and tell the emitter how to import/register them.

Example:

```yaml
# frontend_spec.yaml
layers:
  building:
    package: "@planner/building-layer"
    mode: owned

tools:
  wall:
    capability: building.wall.create
```

The compiler resolves `@planner/building-layer`, reads its manifest, verifies
that `building.wall.create` exists and is legal in `owned` mode, and emits a
public-package import/registration. If any step cannot be proven, compilation
fails.

---

# 2. Core rules

## 2.1 Capability IDs are semantic public identities

A capability ID describes what the package offers, not where the code lives.

Good:

```text
building.wall.create
building.wall.render
building.wall.snap.endpoint
editor.history.undo
viewport.zoom.fit
```

Bad:

```text
src/walls/internal/addWall.ts
WallToolbar.handleClick
useKonvaDragHandler
```

Capability IDs are stable compiler-facing names. Refactoring package files must
not require changing application frontend specs if the capability contract did
not change.

## 2.2 Public exports only

A manifest may reference only exports available through the package's declared
public boundary. It must not point the compiler at internal source paths.

Prefer:

```yaml
implementation:
  export: wallCreateCommand
```

with generated code conceptually importing:

```ts
import { wallCreateCommand } from "@planner/building-layer";
```

Do not encode:

```yaml
path: src/internal/walls/commands/createWall.ts
```

## 2.3 Package implementation stays handwritten/shared

The manifest does not contain command algorithms, renderer code, geometry
formulas, React components, or HTTP calls. It only declares public capabilities
and linkage metadata.

## 2.4 Dependency requirements are explicit

If a package needs another capability to function, it declares that requirement.
The compiler/linker must prove that the application composition supplies it.

A package must not silently reach into another package's internals.

## 2.5 Ownership permissions are explicit

A capability that mutates authoritative domain state may be legal in `owned`
mode but illegal in `reference` mode. A local proposal command may be legal in
`draft` mode without granting backend persistence authority.

The manifest records these legal modes so application composition can be checked
before runtime.

## 2.6 Package manifests do not grant backend authority

A package manifest may declare frontend/editor behavior. It does not create
backend endpoints, credentials, persistence rights, or Platform Hub publication
rights.

Backend/browser operations remain owned by canonical backend contracts and the
host application adapter/client.

---

# 3. Versioning model

Three versions must remain distinct:

```text
frontend_package_manifest schema version
    shape of this manifest language

package release version
    npm/workspace dependency resolution

capability contract version
    semantic version of an individual compiler-facing capability when needed
```

`schema_version: 1` below versions the manifest language only.

The package release version should normally come from the package manager and
lockfile rather than being manually duplicated in this manifest.

For v1, capability IDs should remain stable within compatible package releases.
If a capability changes incompatibly, prefer either a new capability ID or an
explicit capability `version` field rather than silently changing its meaning.

The exact package compatibility/resolution policy is deferred until the first
multi-package implementation.

---

# 4. Proposed top-level schema

```yaml
kind: frontend_package_manifest
schema_version: 1

package:
  id: "@planner/building-layer"
  role: layer

requires:
  packages: []
  capabilities: []

provides:
  capabilities: {}
  layers: {}
  symbols: {}

irregular_exports: {}
```

Closed v1 package roles are initially proposed as:

```text
runtime
layer
renderer_adapter
ui_adapter
integration_adapter
```

Unknown roles are invalid. Add a role only when a real package class cannot be
represented by the existing set.

A package may provide several kinds of capability regardless of role; role is a
coarse ownership signal, not a substitute for exact capability declarations.

---

# 5. `requires`

`requires` declares composition dependencies without importing implementation
internals.

```yaml
requires:
  packages:
    - "@factory/editor-core"
    - "@factory/editor-geometry"

  capabilities:
    - editor.command.dispatch
    - geometry.segment.intersection
    - scene.anchor.register
```

## 5.1 `packages`

`packages` is used only when the package itself has a real package-level runtime
or type dependency that must be present.

Do not list packages merely because their capabilities are convenient or often
used together.

## 5.2 `capabilities`

`capabilities` expresses the semantic dependency graph.

Every required capability must be provided by exactly one resolved provider in
the application composition unless the capability kind explicitly permits
multiple providers (for example, snap providers). Multi-provider semantics must
be declared by the capability kind/backend rather than guessed by the linker.

Unresolved requirements are `BLOCK`.

---

# 6. Capability declaration

The proposed general shape is:

```yaml
provides:
  capabilities:
    building.wall.create:
      kind: command
      implementation:
        export: wallCreateCommand
      allowed_layer_modes: [owned, draft]
      requires:
        - geometry.snap.resolve
      input_type: BuildingWallCreateInput
      output_type: BuildingEditResult
```

Only fields valid for the declared `kind` are allowed. Unknown fields fail
closed.

Initial closed capability kinds:

```text
command
renderer
snap_provider
hit_test_provider
anchor_provider
tool_behavior
selector
validator
projection
workspace_action
```

This registry is intentionally small. New kinds require evidence from real
planners.

---

# 7. Common capability fields

Every capability has:

```yaml
kind: <closed capability kind>
implementation:
  export: <public package export>
```

Optional common fields:

```yaml
version: 1
allowed_layer_modes: [owned, reference, draft]
requires: []
input_type: SomePublicType
output_type: SomePublicType
```

Rules:

- `implementation.export` MUST be a public export of `package.id`.
- `allowed_layer_modes`, when present, is a non-empty subset of `owned`,
  `reference`, `draft`.
- omitted `allowed_layer_modes` means the capability is not layer-mode-sensitive;
  it does **not** mean all mutations are allowed everywhere.
- `input_type` and `output_type` refer to public package type exports or canonical
  language-neutral types known to the compiler; they never contain TypeScript
  source expressions.
- `requires` contains semantic capability IDs, not package filenames.

---

# 8. `command` capabilities

Commands represent intentional editor/application actions with explicit
preview/commit and history semantics supplied by their implementation contract.

Example:

```yaml
building.wall.create:
  kind: command
  implementation:
    export: wallCreateCommand
  allowed_layer_modes: [owned, draft]
  input_type: WallCreateInput
  output_type: BuildingEditResult
  history: commit
```

Proposed v1 `history` registry:

```text
commit
transient
none
```

Meaning:

- `commit` — successful execution creates an undoable committed editor/domain
  transition according to `editor-core` history rules;
- `transient` — preview/transient operation, not a committed history entry;
- `none` — action intentionally does not participate in editor undo history.

A command manifest does not describe how the mutation is calculated.

Examples expected from `@planner/building-layer`:

```text
building.wall.create
building.wall.node.move
building.wall.translate
building.wall.offset
building.wall.delete
building.opening.place
building.opening.delete
```

---

# 9. `renderer` capabilities

Renderer capabilities project known entities/definitions into a renderer adapter.

Example:

```yaml
building.wall.render:
  kind: renderer
  implementation:
    export: wallRenderer
  allowed_layer_modes: [owned, reference, draft]
  input_type: WallProjection
  renderer_family: scene2d
```

The initial proposed renderer-family registry is deliberately abstract:

```text
scene2d
svg_symbol
react_ui
```

Do not put `konva`, `fabric`, or internal Canvas class names into layer manifests.
The renderer adapter resolves the implementation technology behind shared
interfaces.

A renderer capability must not mutate canonical domain state.

---

# 10. `snap_provider` capabilities

Layers may contribute semantic snapping candidates without owning the shared
ranking/selection algorithm.

Example:

```yaml
building.wall.snap:
  kind: snap_provider
  implementation:
    export: wallSnapProvider
  allowed_layer_modes: [owned, reference, draft]
  output_type: SnapCandidateSet
  snap_kinds:
    - endpoint
    - midpoint
    - intersection
    - axis
```

`snap_kinds` uses a closed registry owned by the editor geometry/runtime version.
Unknown snap kinds are invalid rather than interpreted heuristically.

Multiple `snap_provider` capabilities may be active simultaneously. The
`editor-geometry`/`editor-core` runtime owns collection, ranking, preview, and
commit behavior.

---

# 11. `hit_test_provider` and `anchor_provider`

## Hit testing

```yaml
building.wall.hit_test:
  kind: hit_test_provider
  implementation:
    export: wallHitTestProvider
  input_type: BuildingProjection
  output_type: HitCandidateSet
```

The provider supplies semantic candidates. Shared selection logic owns final
selection policy.

## Anchors

```yaml
building.wall.anchors:
  kind: anchor_provider
  implementation:
    export: wallAnchorProvider
  input_type: BuildingProjection
  output_type: AnchorSet
```

Anchors may include endpoints, midpoint, faces, opening attachments, or other
layer-owned semantic attachment features.

The provider returns semantic anchor identities plus current geometry. Consumers
must persist semantic references where domain semantics allow it rather than
copying stale screen coordinates.

---

# 12. `selector`, `validator`, and `projection`

These capability kinds cover pure/read-oriented reusable behavior.

```yaml
building.rooms.select:
  kind: selector
  implementation:
    export: selectRooms
  input_type: BuildingState
  output_type: RoomSet

building.edit.validate:
  kind: validator
  implementation:
    export: validateBuildingEdit
  input_type: BuildingEditCandidate
  output_type: ValidationResult

building.scene.project:
  kind: projection
  implementation:
    export: projectBuildingScene
  input_type: BuildingState
  output_type: BuildingProjection
```

A `projection` derives view/scene data and must not silently become a second
persistence model.

---

# 13. Layer declarations supplied by packages

A reusable planner layer should declare one or more named layer definitions.

```yaml
provides:
  layers:
    building:
      implementation:
        export: buildingLayerDefinition
      default_capabilities:
        render: building.wall.render
        hit_test: building.wall.hit_test
        anchors: building.wall.anchors
        snap:
          - building.wall.snap
      supported_modes: [owned, reference, draft]
```

A `LayerDefinition` provides reusable defaults. `frontend_spec.yaml` chooses
whether to load the layer, selects its mode, and may enable/disable optional
capabilities within the closed configuration supported by the package.

The package manifest does not decide that Room Planner owns building while
Plumbing Planner references it. That is an application composition decision in
`frontend_spec.yaml`.

## 13.1 Layer mode compatibility

The linker must prove:

```text
requested application layer mode
        ∈ package layer supported_modes
```

and every capability bound into that layer must also permit that mode where
`allowed_layer_modes` is declared.

A `reference` layer may use renderer/snap/anchor/hit-test capabilities while a
mutation command that allows only `[owned, draft]` remains unavailable.

---

# 14. Symbols supplied by packages

A package may expose reusable symbol catalogs or symbol definitions.

```yaml
provides:
  symbols:
    building.openings:
      kind: catalog
      implementation:
        export: openingSymbolCatalog
      symbols:
        - door.single.left
        - door.single.right
        - door.double
        - window.single
```

The actual SVG asset + semantic symbol manifest remains governed by the symbol
contract described in `FRONTEND_EDITOR.md` / future symbol schema.

The package manifest links a catalog into the capability system; it must not
embed SVG markup inline.

---

# 15. Irregular public exports

Irregular code remains explicit and typed. A package may expose an irregular
extension point without pretending it is a standard capability.

```yaml
irregular_exports:
  special_room_overlay:
    export: specialRoomOverlay
    kind: scene_extension
    reason: "Experimental visualization not represented by package-manifest v1"
```

Rules:

- `reason` is mandatory;
- `export` must be public;
- irregular exports are never selected by capability inference;
- `frontend_spec.yaml` must reference the irregular owner explicitly;
- an irregular export becoming common across planners is evidence for a new
  capability kind or shared package abstraction.

---

# 16. Package manifest example: `@factory/editor-core`

```yaml
kind: frontend_package_manifest
schema_version: 1

package:
  id: "@factory/editor-core"
  role: runtime

requires:
  packages: []
  capabilities: []

provides:
  capabilities:
    editor.history.undo:
      kind: workspace_action
      implementation:
        export: undoAction

    editor.history.redo:
      kind: workspace_action
      implementation:
        export: redoAction

    editor.selection.delete:
      kind: command
      implementation:
        export: deleteSelectionCommand
      history: commit

    editor.tool.cancel:
      kind: workspace_action
      implementation:
        export: cancelActiveTool

  layers: {}
  symbols: {}

irregular_exports: {}
```

This package owns generic editor behavior, not wall/plumbing semantics.

---

# 17. Package manifest example: `@planner/building-layer`

```yaml
kind: frontend_package_manifest
schema_version: 1

package:
  id: "@planner/building-layer"
  role: layer

requires:
  packages:
    - "@factory/editor-core"
    - "@factory/editor-geometry"
    - "@factory/editor-scene"

  capabilities:
    - editor.command.dispatch
    - geometry.snap.resolve
    - scene.anchor.register

provides:
  capabilities:
    building.scene.project:
      kind: projection
      implementation:
        export: projectBuildingScene
      input_type: BuildingState
      output_type: BuildingProjection

    building.wall.render:
      kind: renderer
      implementation:
        export: wallRenderer
      allowed_layer_modes: [owned, reference, draft]
      input_type: WallProjection
      renderer_family: scene2d

    building.wall.hit_test:
      kind: hit_test_provider
      implementation:
        export: wallHitTestProvider
      allowed_layer_modes: [owned, reference, draft]

    building.wall.anchors:
      kind: anchor_provider
      implementation:
        export: wallAnchorProvider
      allowed_layer_modes: [owned, reference, draft]

    building.wall.snap:
      kind: snap_provider
      implementation:
        export: wallSnapProvider
      allowed_layer_modes: [owned, reference, draft]
      snap_kinds: [endpoint, midpoint, intersection, axis]

    building.wall.create:
      kind: command
      implementation:
        export: wallCreateCommand
      allowed_layer_modes: [owned, draft]
      history: commit
      input_type: WallCreateInput
      output_type: BuildingEditResult

    building.wall.node.move:
      kind: command
      implementation:
        export: moveWallNodeCommand
      allowed_layer_modes: [owned, draft]
      history: commit

    building.wall.offset:
      kind: command
      implementation:
        export: offsetWallCommand
      allowed_layer_modes: [owned, draft]
      history: commit

    building.opening.place:
      kind: command
      implementation:
        export: placeOpeningCommand
      allowed_layer_modes: [owned, draft]
      history: commit

  layers:
    building:
      implementation:
        export: buildingLayerDefinition
      supported_modes: [owned, reference, draft]
      default_capabilities:
        projection: building.scene.project
        render: building.wall.render
        hit_test: building.wall.hit_test
        anchors: building.wall.anchors
        snap:
          - building.wall.snap

  symbols:
    building.openings:
      kind: catalog
      implementation:
        export: openingSymbolCatalog
      symbols:
        - door.single.left
        - door.single.right
        - door.double
        - window.single

irregular_exports: {}
```

The exact capability inventory will be adjusted after the first wall-editor
vertical slice. The important point is the shape: stable semantic IDs, public
exports, explicit requirements, and ownership-mode legality.

---

# 18. Linking with `frontend_spec.yaml`

Given application authoring input:

```yaml
layers:
  building:
    package: "@planner/building-layer"
    mode: owned

tools:
  wall:
    capability: building.wall.create

  select:
    capability: editor.selection.select

bindings:
  keyboard:
    Ctrl+Z: editor.history.undo
    Ctrl+Shift+Z: editor.history.redo
```

The frontend linker performs:

```text
resolve package
    ↓
validate package manifest schema
    ↓
collect provided capabilities
    ↓
resolve transitive required capabilities/packages
    ↓
check unique/supported providers
    ↓
check layer-mode legality
    ↓
check referenced public exports
    ↓
check referenced types
    ↓
produce canonical import/registration plan
```

No fuzzy matching is allowed. `building.wall.create` does not resolve to
`building.wall.add` because the names look similar.

---

# 19. Canonical linker IR

Package manifests should normalize into a canonical package/capability graph
inside `frontend_ir.json`.

Conceptually:

```json
{
  "packages": {
    "@planner/building-layer": {
      "role": "layer",
      "requires_packages": ["@factory/editor-core"],
      "requires_capabilities": ["editor.command.dispatch"],
      "provided_capabilities": [
        "building.wall.render",
        "building.wall.create"
      ]
    }
  },
  "capabilities": {
    "building.wall.create": {
      "provider": "@planner/building-layer",
      "kind": "command",
      "export": "wallCreateCommand",
      "layer": "building",
      "layer_mode": "owned"
    }
  }
}
```

This graph should be usable by dependency/affected-set tooling similarly to the
existing backend specification graph.

---

# 20. Fail-closed validation

At minimum, v1 validation must reject:

1. unknown manifest `kind` or `schema_version`;
2. unknown package role;
3. duplicate package IDs in one resolved composition;
4. duplicate exclusive capability providers;
5. unresolved required packages;
6. unresolved required capabilities;
7. unknown capability kind;
8. fields not permitted for the capability kind;
9. missing/non-public implementation exports;
10. invalid public type references;
11. invalid/empty `allowed_layer_modes`;
12. application layer mode unsupported by the package layer;
13. command capability used in a forbidden layer mode;
14. mutation capability exposed through a `reference` layer when not explicitly legal;
15. unknown snap/renderer/history registry values;
16. frontend-spec capability references with no exact provider;
17. irregular export without explicit reason;
18. attempts to encode internal source paths as implementation linkage;
19. backend transport/auth/persistence authority declared implicitly by a frontend package;
20. cyclic package requirements when the runtime dependency model cannot support the cycle.

Validation errors are compilation blockers, not prompts for an emitter to guess.

---

# 21. What the deterministic emitter gets from the manifest

The manifest gives the compiler enough information to emit conventional linkage,
for example:

```ts
import {
  buildingLayerDefinition,
  wallCreateCommand,
  wallRenderer,
  wallSnapProvider,
} from "@planner/building-layer";
```

and then deterministic registration such as:

```text
register package
register layer
register renderer
register snap provider
register command
bind frontend-spec tool/shortcut/palette item
```

The emitter does **not** generate the implementation of `wallCreateCommand` or
`wallRenderer`. Those live in the reusable package.

---

# 22. What should be built first

Do not implement every proposed capability kind at once.

The first package-manifest slice should prove only what Room Planner needs for
the initial wall spike:

```text
package identity/role
requires packages/capabilities
layer declaration + supported modes
command
renderer
snap_provider
hit_test_provider
anchor_provider
projection
public export linkage
frontend-spec exact capability resolution
```

Defer richer selectors, validators, symbol catalogs, integration adapters, and
capability-version negotiation until a real use case needs them.

Suggested implementation order:

1. define JSON Schema/Pydantic validation model for manifest v1 subset;
2. write two fixture manifests: `editor-core` and `building-layer`;
3. validate exact capability IDs and public export names;
4. build package/capability graph;
5. link one Room Planner `frontend_spec.yaml`;
6. emit a deterministic TypeScript registration file;
7. prove `owned` vs `reference` mode blocking;
8. prove missing capability/export fails closed;
9. only then expand the manifest language.

---

# 23. Open questions

1. Should package manifests live inside each npm package or in a central registry?
2. How should the compiler verify a named public export before TypeScript build:
   package metadata, generated export index, TypeScript analysis, or a build-time
   manifest generated by the package itself?
3. Which capability kinds are truly exclusive providers and which aggregate
   multiple providers?
4. Should capability versions be explicit from v1 or added only when the first
   incompatible capability evolution appears?
5. Should public `input_type`/`output_type` use package-exported TS names initially
   or a language-neutral type registry immediately?
6. How should optional package capabilities be enabled/disabled by
   `frontend_spec.yaml` without creating arbitrary free-form config?
7. Does `LayerDefinition` belong entirely in package manifests, or should runtime
   layer metadata be a generated TypeScript object while the manifest declares
   only compiler-relevant facts?
8. How should symbol catalogs link to a future normative SVG symbol manifest?
9. Which dependency edges should participate in frontend affected-set rebuilds?
10. How should package release compatibility be locked so deterministic builds
    cannot silently change when a package is upgraded?

Until these questions have implementation evidence, v1 is a minimal linker
contract, not a general plugin system.