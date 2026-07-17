# Spec Workbench

**Spec Workbench** is a specification authoring environment for AI Code Factory.

Unlike the factory, which generates code from an existing specification, Spec Workbench helps design the specification itself.

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
10. Factory compatibility probe (assembler and linker, no deploy)

Each layer is stabilized before moving to the next.

## Repository structure

```text
skills/
    Specification authoring methodology.

examples/
    Real specification design case studies.

skills/spec-authoring/SPEC_STANDARD.md
    Definition of the global_spec.json format.

skills/spec-authoring/FACTORY_COMPATIBILITY.md
    Current target-compiler profile and mandatory no-deploy compile probe.
```

## Current status

The project is under active development.

The current focus is building a repeatable methodology for producing high-quality specifications that can later be compiled into code by AI Code Factory.

## Reference cases

- **Panelforge** in the sibling Factory checkout is the positive end-to-end
  baseline for capabilities it has actually exercised: deep generation units,
  a deterministic `core/models` surface, strict/frozen Pydantic DTOs, thin API
  orchestration, assembler completion, linker completion, and deploy evidence.
- **Hydraulic Diagram Service** is the capability-migration case for named
  discriminated unions and Protocol-based repository, UnitOfWork,
  authorization, and gateway ports.

Reference cases are evidence, not templates to copy mechanically. Panelforge
does not prove named-union or Protocol materialization, and its incidental
shapes must not be used to downgrade a more precise architecture.

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
canonical validator reports any error or warning. Only exit code 0 with status
`PASS` is handoff-ready; `WARNINGS_ONLY` is rejected. Provenance and validation
evidence are written to `projects/<project>/specs/working/`;
`global_spec.json` remains in the factory-defined format.
