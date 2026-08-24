# Frontend Compiler Spike

> Implementation acceptance plan for the first `frontend_spec/v1` +
> `frontend_package_manifest/v1` compiler slice.
>
> Status: executable spike contract. This file is intentionally narrower than
> `FRONTEND_EDITOR.md`, `FRONTEND_SPEC.md`, and `FRONTEND_PACKAGE_MANIFEST.md`.
> It defines what the first generator/linker implementation must prove.

## 1. Spike objective

Prove this chain end to end:

```text
package public TypeScript API
    + package-local capability declarations
        ↓
deterministic package-manifest generator
        ↓
verified canonical frontend-package-manifest.json
        ↓
frontend_spec.yaml
        ↓
frontend linker/normalizer
        ↓
frontend_ir.json
        ↓
deterministic TypeScript registration output
        ↓
mandatory tsc
```

The spike is successful only when valid inputs rebuild identically and invalid
composition fails before runtime.

## 2. Deterministic manifest generation

The manifest generator itself is part of the deterministic toolchain.

Canonical generation rules for the spike:

- stable sort all object keys where canonical JSON ordering matters;
- stable sort capability IDs lexicographically;
- stable sort package requirements and other semantically unordered sets;
- preserve order only where the contract declares order meaningful;
- emit UTF-8 canonical JSON with one documented serialization policy;
- do not emit timestamps, build duration, host path, machine name, random IDs, or
  other volatile build metadata into hashed semantic content;
- derive package version only from the resolved package build metadata;
- compute `manifest_hash` over the canonical representation excluding the hash
  field itself.

First generator acceptance test:

```text
same source + same package version
    build manifest A
    build manifest B
        ↓
byte-identical canonical semantic content
        ↓
identical manifest_hash
```

A repeated build producing a different hash with no semantic input change is a
`BLOCK` defect in the generator.

A separate non-semantic diagnostics file may contain timestamps or build-machine
metadata if ever useful, but that data must not participate in the canonical
manifest hash.

## 3. Public-export truth test

The canonical manifest is generated from the package public TypeScript boundary.
Every `implementation.export` and `irregular_exports.*.export` must exist in that
public surface during generation.

The spike must include this end-to-end negative fixture:

```text
1. capability declaration names wallCreateCommand
2. wallCreateCommand is exported publicly
3. package manifest generation succeeds
4. remove wallCreateCommand from the public package export surface
5. rebuild package manifest
6. generation MUST fail
```

The expected result is not a stale manifest that later fails in the frontend
linker. The package build itself must refuse to produce canonical linker truth.

This fixture validates the whole `generated-manifest-as-truth` chain rather than
only a schema rule.

## 4. Capability-kind pressure test: read-only user actions

Manifest v1 currently treats `command` as mutation-capable and therefore legal
only in `owned | draft` layer modes.

The first real reference-layer user action that is conceptually command-like but
read-only — examples may include measuring a distance, inspecting a wall, or
querying geometry — is a deliberate architecture test.

Rules for the spike:

- do not make `command` legal in `reference` by exception;
- do not route such an action through `irregular_exports` merely to bypass the
  kind rule;
- first attempt to model the behavior with an existing correct read-oriented or
  workspace-global kind;
- if no current kind expresses the semantics, record evidence and revise the
  capability-kind system explicitly.

A new read-only action class, if proven necessary, is a schema change with
validator semantics, not an escape hatch.

## 5. Undo snapshot scope

`history: commit` with `undo: snapshot` requires an explicit snapshot scope.

For the first spike, the only supported snapshot policy is:

```yaml
history: commit
undo: snapshot
snapshot_scope: layer
```

Meaning:

> `editor-core` captures and restores the complete authoritative/local-draft
> state owned by the affected layer instance for that history entry.

V1 spike rules:

- `snapshot_scope` is REQUIRED when `undo: snapshot`;
- the only accepted value is `layer`;
- `snapshot_scope` is forbidden for `undo: inverse`;
- whole-application snapshots are not supported by the first slice;
- affected-subgraph snapshots are not supported by the first slice;
- `editor-core` owns history ordering/storage mechanics;
- the layer runtime owns how its complete snapshot state is materialized and
  restored through the shared TypeScript history interface.

If layer snapshots become too expensive, optimization to an affected subgraph is
a later contract revision, not an undocumented implementation shortcut.

For complex building operations such as moving a shared wall node, `undo:
inverse` remains preferred when the building layer can provide a trustworthy
reversible domain edit. `snapshot` exists as an explicit fallback strategy, not
as proof that generic history understands topology.

## 6. Minimal implemented capability subset

The spike must implement only the kinds already marked v1-implemented and needed
by the first fixtures:

```text
command
renderer
snap_provider
hit_test_provider
anchor_provider
projection
workspace_action
```

Do not implement declared-for-later kinds during the spike.

The linker must preserve existing provider cardinality rules:

```text
aggregate:
    snap_provider
    hit_test_provider
    anchor_provider

exclusive:
    command
    projection
    workspace_action

renderer:
    exclusive by renderer slot
```

## 7. First package fixtures

Build two real fixture packages or minimal package-shaped fixtures.

### `@factory/editor-core`

Must prove at least:

- public export verification;
- workspace actions for undo/redo/cancel;
- deterministic generated manifest;
- no layer-mode declarations on workspace actions.

### `@planner/building-layer`

Must prove at least:

- one projection;
- one scene2d renderer;
- one snap provider;
- one hit-test provider;
- one anchor provider;
- one mutation command legal in `owned | draft`;
- one `history: commit` command with `undo: inverse`;
- optionally one synthetic `undo: snapshot` command solely to verify
  `snapshot_scope: layer` validation.

The spike is testing compiler/linker boundaries, not complete wall behavior.

## 8. Frontend linker fixture

Use one minimal Room Planner `frontend_spec.yaml` containing:

```text
building layer = owned
one wall tool
undo/redo keyboard bindings
standard panels
no irregular behavior required for happy path
```

Normalize it with the generated package manifests into `frontend_ir.json`.

The IR must record for every package at least:

```text
package id
resolved package version
manifest schema version
manifest hash
```

Capabilities and aggregate providers must be emitted in canonical deterministic
order.

## 9. Required negative fixtures

The first test suite must include at least:

1. same manifest build twice -> identical bytes/hash;
2. capability declaration references a public export that does not exist ->
   package manifest generation fails;
3. export existed, then is removed from public index -> rebuild fails;
4. duplicate exclusive capability provider -> linker fails;
5. multiple aggregate snap providers -> linker succeeds and order is stable;
6. `command` bound to `reference` layer -> linker fails;
7. `draft` layer missing `draft_persistence` -> frontend validation fails;
8. `draft_persistence` present on `owned` or `reference` -> validation fails;
9. `history: commit` missing `undo` -> manifest validation fails;
10. `undo: snapshot` missing `snapshot_scope` -> manifest validation fails;
11. `undo: snapshot` with scope other than `layer` -> manifest validation fails;
12. `undo: inverse` with `snapshot_scope` -> manifest validation fails;
13. package dependency cycle -> linker fails;
14. declared-for-later capability kind -> validator fails;
15. generated TypeScript linkage does not typecheck -> mandatory `tsc` fails.

## 10. Spike implementation order

1. Canonical JSON serializer + manifest hash function.
2. Package public-export discovery/verification.
3. Package-local capability declaration input for the fixture packages.
4. Generated canonical package manifest.
5. Determinism tests and removed-export negative fixture.
6. Manifest v1 validator for the implemented subset.
7. Two package fixtures: `editor-core`, `building-layer`.
8. Frontend spec v1 parser/validator for the minimal Room Planner slice.
9. Package DAG + capability linker.
10. `frontend_ir.json` canonical emitter with package version/hash provenance.
11. Generated TypeScript registration emitter.
12. Mandatory `tsc` gate.
13. Full negative-fixture matrix.

Do not add richer UI/schema features until this sequence passes.

## 11. Exit criteria

The spike is complete when all of the following are true:

- two identical package builds produce identical canonical manifests and hashes;
- deleting a declared public export prevents canonical manifest generation;
- the two fixture package manifests link into the Room Planner frontend spec;
- `frontend_ir.json` is deterministic and includes package provenance;
- illegal ownership-mode composition is rejected before emission;
- snapshot undo is unambiguous because v1 scope is `layer`;
- aggregate/exclusive provider behavior is tested;
- generated registration TypeScript passes `tsc`;
- every required negative fixture fails at the intended stage with a precise
  diagnostic;
- no invalid deterministic input falls back to LLM/irregular behavior.

Only after these criteria pass should the implementation proceed to real
wall/junction editor runtime behavior or expand the frontend schema.