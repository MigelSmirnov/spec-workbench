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

The current focus is building a repeatable methodology and deterministic toolchain for producing high-quality specifications that can later be compiled into code by AI Code Factory.

## Design toolchain

Large Markdown design states are handled through narrow deterministic tools:

```text
design_router -> chooses the deterministic early-design workflow
design_index  -> addresses and navigates State 1/2 design structure
design_editor -> plans and atomically applies one structural splice
design_lint   -> reports State 1 identity and State 2 authoring findings
design_stage3 -> addresses modules, checks State 3, traces upstream decisions, emits handoff
```

Ask the router for a plan before composing early-design commands manually:

```bash
python tools/design_router.py examples/cabinet-backend diagnose-state2

python tools/design_router.py examples/cabinet-backend trace-term \
  --term Holded

python tools/design_router.py examples/cabinet-backend diagnose-state3

python tools/design_router.py examples/cabinet-backend trace-state2-to-state3

python tools/design_router.py examples/cabinet-backend verify-state3
```

Use `--json` for agent and future MCP integration. The router is read-only: it returns ordered tool arguments, command previews, review checkpoints, and stop conditions, but never executes a command or infers design semantics.

For the authoring order, use the deterministic sequencer rather than inferring
semantic state from `60_*` / `70_*` filenames:

```bash
python tools/authoring.py next <project> --json
python tools/design_authoring_next.py examples/<case> --json
```

One sequencer routes through State 0-5, pre-contract data closure, State 6
exact contracts, optional deterministic backend closures, State 7 Notes, and
then final assembly; `skills/spec-authoring/authoring_sequence.json` is its
machine-readable source of truth.

### SPEC_STANDARD v2 language gate

Current specifications declare `standard_version: 2`. The legacy top-level
`adapters` section is not part of v2. Post-assembly verification starts with a
language gate so an implicit or unknown specification revision cannot reach
later consumers.

For a legacy assembled spec whose `adapters` section is exactly empty, the
mechanical envelope migration can be reviewed or applied without rewriting
product semantics:

```bash
python tools/migrate_spec_v2.py examples/<case>/global_spec.json
python tools/migrate_spec_v2.py examples/<case>/global_spec.json --apply
```

Non-empty legacy adapters fail closed because their call-site semantics require
an explicit migration.

### Deterministic persistence closure

`persistence_backend/v2` is currently the closed SQLite backend
(`sqlite_sync_v2`). It is post-contract because repository classes, schema
functions, and methods must bind to canonical State 6 ownership and signatures.
PostgreSQL and other unsupported persistence implementations remain on the
ordinary generation path and do not create this closure merely because the
project persists models.

When deterministic SQLite persistence is selected, author and close:

```bash
python tools/design_persistence_authoring.py examples/<case> --coverage --json
python tools/design_persistence_authoring.py examples/<case> --handoff --json
```

The optional `70_persistence_closure.json` owns the exact post-contract
`backend_ir`. Final `global_spec.json` must project that value unchanged into
`rules.persistence_backend`; the assembly persistence check validates exact
handoff lineage, closed v2 structure, table/model/config/module references, and
canonical contract ownership. Table-emitted repository methods are then known
to Notes and module-review tooling as deterministic callables rather than
LLM-owned code.

For post-assembly model identity inspection, use the transport-neutral identity
workbench:

```bash
python tools/design_identity_closure.py examples/<case> --inventory
python tools/design_identity_closure.py examples/<case> --get ModelName
python tools/design_identity_closure.py examples/<case> --json
```

The underlying `identity_workbench` module exposes the same inventory,
inspection, and verification operations for future MCP registration.

Run the complete post-assembly gate with:

```bash
python tools/design_assembly.py examples/<case>
python tools/design_assembly.py examples/<case> --check language
python tools/design_assembly.py examples/<case> --check external_contracts
python tools/design_assembly.py examples/<case> --check persistence
```

The transport-neutral `assembly_workbench` delegates to the language, identity,
data, contract, external-contract evidence, notes, router, and persistence
owners and returns a compact MCP-ready report. External facts are verified by
the Workbench against committed content-addressed evidence; Factory receives
only the already-closed specification IR.

### Notes language and dependency bindings

Passing the notes coverage gate does not mean the Factory will generate from
those notes. Its pre-generation gate counts a note as evidence only when the
note is scoped to the bare callable name, carries a semantic note class, and
states a **positive modal** — `MUST`, `SHOULD`, or `MAY`. A note written in the
imperative mood satisfies this repository and is rejected downstream, after the
specification has already been exported and accepted.

```bash
python tools/design_notes.py examples/<case> --language
python tools/design_notes.py examples/<case> --language --json
```

`notes_workbench/language.py` replicates that rule against the assembled
`global_spec.json` and points at the authored Markdown line to repair, reading
every `80_notes*.md` file rather than `80_notes.md` alone. It also cross-checks
notes that name a runtime dependency: when a note says to obtain a type bound to
`request.app.state.*` and pass it to a callable, the named type must be the one
that callable's contract requires. Such a note counts as coverage either way, so
a wrong binding is otherwise invisible until runtime verification.

For the final business-to-implementation comparison, build a module review
packet from the assembled specification:

```bash
python tools/design_module_review.py examples/<case> --list
python tools/design_module_review.py examples/<case> --module <name> --slice --json
python tools/design_module_review.py examples/<case> --module <name> --review
```

`module_review_workbench` keeps accepted evidence, lowered specification, and
assembled generation constraints separate so a human or LLM can perform the
Stage 8.1 adversarial semantic review without reconstructing context ad hoc.
Modules accepted by deterministic persistence receive their repository/table/
aggregate slice as explicit lowering evidence.
Modules named by an active external-contract record also receive that exact
content-addressed evidence in the accepted-evidence portion of their slice.

### State 3 stable addresses and handoff

A State 3 responsibility heading such as:

```markdown
## `durable_archive`
```

has the stable machine address:

```text
module:durable_archive
```

Backward trace is explicit. Put only normative upstream design references in a dedicated section:

```markdown
### Trace inputs

- M06
- A64
- source:02_rules_import.md#accepted-decision
```

References mentioned elsewhere in prose do not create trace edges.

The State 3 tool can then be used directly:

```bash
python tools/design_stage3.py examples/cabinet-backend --list --json
python tools/design_stage3.py examples/cabinet-backend --get module:durable_archive --json
python tools/design_stage3.py examples/cabinet-backend --lint
python tools/design_stage3.py examples/cabinet-backend --trace --json
python tools/design_stage3.py examples/cabinet-backend --handoff --json
```

`--handoff` emits stable module keys, candidate public capability names, and upstream references. A later State 4 tool or MCP client should consume that output instead of reparsing State 3 Markdown or guessing module names.

## Factory handoff

Keep this repository next to the Code Factory checkout:

```text
workspace/
├── code_factory/
└── spec-workbench/
```

Run the official Stage 9 read-only admission gate first:

```bash
python tools/design_factory_admission.py examples/hydraulic-diagram-service \
  --project hydraulic_diagram_service
```

Cases that have a stable Factory destination should pin it in
`90_factory_target.json`:

```json
{
  "schema_version": "spec_workbench_factory_target.v1",
  "case": "hydraulic-diagram-service",
  "factory_project": "hydraulic_diagram_service"
}
```

Admission prints and records the exact `case -> Factory project` pair. A
different `--project` is blocked before export; a case without this manifest
is blocked as well — the workbench has no warnings (see "The fence" in
`skills/spec-authoring/SKILL.md`).

## GitHub Actions CI

`.github/workflows/spec-workbench-ci.yml` runs the complete Workbench test
suite and Cabinet assembly gates on every push and pull request. This makes
the checks available when changes are authored through a GitHub connector
that cannot execute local commands.

The cross-repository admission job additionally checks out the private
`MigelSmirnov/panelforge-sandbox` repository and runs the real Factory
validator. It authenticates with a dedicated read-only deploy key whose
private half is stored in `spec-workbench` as the Actions secret
`FACTORY_REPO_DEPLOY_KEY`; no personal GitHub token is exposed to the job.
Without the secret, Workbench CI still runs and the Factory job records an
explicit skip notice.

Export an admitted case into a new Factory project with:

```bash
python tools/export_to_factory.py \
  --case hydraulic-diagram-service \
  --project hydraulic_diagram_service
```

Use `--update-existing` only when intentionally replacing an existing canonical specification. The export is blocked when the two repositories have different `SPEC_STANDARD.md` content, the Workbench checkout is dirty, required external-contract evidence is stale, the source does not declare the supported `standard_version`, or the Factory's canonical validator reports errors. Provenance and validation evidence are written to `projects/<project>/specs/working/`; `global_spec.json` remains in the factory-defined format.

`export_to_factory.py --check` exposes the same read-only admission report for
automation. The standalone `design_factory_admission.py` command is the
normative human-facing gate. Stage 9 lineage and handoff receipts record both
the canonical spec identity and its `standard_version`. Stage 9 ends after the
exact canonical spec and handoff receipts are present in Factory; Route B
generation and terminal OTK belong to Factory.

## Tool ownership

`tools/`, `tests/`, `skills/` and `.github/` change only on `main` via
`tools/<topic>` branches. `agent/<project>` branches own `examples/<project>/`
and `experiments/` only; `python tools/tools_ownership_check.py --base origin/main`
is the pre-push check and the CI gate. Project-owned deterministic backends are
declared in `examples/<project>/workbench_extensions.json` and loaded through
`tools/project_extensions.py`.
