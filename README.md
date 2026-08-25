# Spec Workbench

**Spec Workbench** is a specification authoring environment for AI Code Factory.

Unlike the factory, which generates code from an existing specification, Spec Workbench helps design the specification itself.

## Start here

Spec Workbench uses two related terms:

- a **project** is a logical working product selected through `PROJECT_INDEX.json`, such as `room-planner` or `cabinet-backend`;
- a **case** or **reference case** is specification-design content under `examples/`, used by the methodology and diagnostic/history tooling.

For normal repository navigation, do not search branches or `examples/` manually. Start with:

```bash
python tools/workbench.py
```

With no arguments the command runs `list`. It shows only the curated working projects and resolves their canonical refs, paths, and current design stages.

Equivalent explicit command:

```bash
python tools/workbench.py list
```

If a canonical project branch is missing from a single-branch or agent sandbox checkout, `list` attempts to fetch only that indexed branch from `origin`. It does not fetch or scan arbitrary branches for normal discovery.

After choosing a project, resolve its working context with:

```bash
python tools/workbench.py show <project>
```

`show` returns the canonical ref, project path, current stage, next stage, and a minimal read order. Both `list` and `show` support `--json` for agents and other tooling:

```bash
python tools/workbench.py list --json
python tools/workbench.py show room-planner --json
```

Use the exhaustive case/ref view only for repository or index diagnostics:

```bash
python tools/workbench.py status
python tools/workbench.py status --json
```

`status` may report historical case snapshots and unindexed cases. It is not the normal project-selection mechanism.

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
