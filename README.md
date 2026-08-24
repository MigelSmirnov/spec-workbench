# Spec Workbench

**Spec Workbench** is a specification authoring environment for AI Code Factory.

Unlike the factory, which generates code from an existing specification, Spec Workbench helps design the specification itself.

## Start here

Use the repository entry point before looking for a case manually:

```bash
python tools/workbench.py
```

With no arguments it runs `status`: it shows the current checkout, its case
studies and cases that exist only on other known local/remote Git refs.

List all discovered case-study snapshots explicitly with:

```bash
python tools/workbench.py list
```

Both commands support `--json` for agents and other tooling:

```bash
python tools/workbench.py status --json
python tools/workbench.py list --json
```

`list` deliberately inspects known Git refs, not only the checked-out
`examples/` directory. This makes active case studies discoverable even when
their working branch has not yet been merged to `main`.

## Goal

Create specifications that:

- describe architecture, not just JSON structure;
- avoid placeholder-driven design;
- are developed layer by layer;
- can be deterministically compiled into code.

## Core ideas

- **SPEC_STANDARD** defines the specification language.
- **spec-authoring** defines the authoring methodology.
- Specification design progresses through explicit design states:

1. Product boundary
2. Domain models
3. Rules & Invariants
4. Module responsibilities
5. System flows
6. Public APIs
7. Contracts
8. Notes
9. Assembly

Each layer is stabilized before moving to the next.

## Frontend compiler contracts

Browser/editor generation has its own linked contract set. Treat these documents
as one architecture/compiler family rather than discovering them independently:

- [FRONTEND_EDITOR.md](FRONTEND_EDITOR.md) — shared browser/editor architecture,
  package boundaries, geometry, rendering, ownership, and reusable planner layers;
- [FRONTEND_SPEC.md](FRONTEND_SPEC.md) — application-facing `frontend_spec/v1`
  authoring/compiler contract: what is derived from backend specs versus authored
  as frontend composition;
- [FRONTEND_PACKAGE_MANIFEST.md](FRONTEND_PACKAGE_MANIFEST.md) —
  `frontend_package_manifest/v1` linker contract that declares reusable package
  capabilities, public exports, dependencies, layer modes, and symbol catalogs.

The intended relationship is:

```text
backend canonical spec
        +
frontend_spec/v1
        +
frontend package manifests
        +
symbol manifests
        ↓
validated frontend IR
        ↓
generated browser wiring over shared runtime/packages
```

When working on reusable frontend/editor architecture, read all three documents.
A package manifest declares frontend capabilities only; it does not create backend
authority, persistence rights, or application endpoints.

## Repository structure

```text
skills/
    Specification authoring methodology.

examples/
    Real specification design case studies.

skills/spec-authoring/SPEC_STANDARD.md
    Definition of the global_spec.json format.
```

## Current status

The project is under active development.

The current focus is building a repeatable methodology for producing high-quality specifications that can later be compiled into code by AI Code Factory.

## Factory handoff

Keep this repository next to the Code Factory checkout:

```text
workspace/
├── code_factory/
└── spec-workbench/
```

Export an accepted case into a new Factory project with:

```bash
python tools/export_to_factory.py \
  --case hydraulic-diagram-service \
  --project hydraulic_diagram_service
```

Use `--update-existing` only when intentionally replacing an existing canonical
specification. The export is blocked when the two repositories have different
`SPEC_STANDARD.md` content, the Workbench checkout is dirty, or the Factory's
canonical validator reports errors. Provenance and validation evidence are
written to `projects/<project>/specs/working/`; `global_spec.json` remains in
the factory-defined format.