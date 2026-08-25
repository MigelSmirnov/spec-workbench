# AGENTS.md

## Mission

This repository develops a semi-manual methodology and supporting tools for
creating high-quality `global_spec.json` specifications for AI Code Factory.

The primary problem is placeholder architecture: specifications that are
structurally valid but leave important engineering decisions unresolved.

## Repository roles

- `README.md` explains the project to people.
- `AGENTS.md` tells agents how to work in the repository.
- `SPEC_STANDARD.md` defines the existing factory specification format.
- `SKILL.md` defines the specification-authoring methodology.
- `BEHAVIORAL_NOTES.md` explains how to design effective notes without
  changing the factory specification language.

## Repository entry point

Do not search `examples/`, inspect arbitrary branches, or recursively read the
repository to discover which working project the user means.

Start with:

```bash
python tools/workbench.py
```

The default command is `list`. It reads the curated `PROJECT_INDEX.json` and
shows only the logical working projects and their canonical refs. It does not
present historical, reference, methodology, or divergent side refs as separate
projects.

If the user has not already identified a project, show the listed project names
and ask which one to work on. After the project is identified, resolve its
context with:

```bash
python tools/workbench.py show <project>
```

`show` returns the canonical ref, project path, current design stage, and a
minimal project read order. Both `list` and `show` support `--json`.

Use:

```bash
python tools/workbench.py status
```

only when an exhaustive checkout/history view is explicitly needed. Normal
project discovery must not use exhaustive ref scanning.

## Authoring pipeline entry point

After resolving a logical project, do not choose design-state tools by memory,
filename prefix, repository search, or project-local orchestration. Ask the
common pipeline what comes next:

```bash
python tools/authoring.py next <project> --json
```

`tools/authoring.py` is a thin CLI over `tools/authoring_pipeline.py`. Future MCP
transports must call the same pipeline API and must not reproduce project
resolution or phase-routing logic.

`skills/spec-authoring/authoring_sequence.json` is the machine-readable source
of truth for authoring order. `AUTHORING_SEQUENCE.md` explains the same contract.
Project branches own project design data and artifacts; they do not own a forked
copy of the generic authoring sequence.

The generic pipeline promoted to `main` covers State 0 through Stage 9: the
explicit State 2 -> State 3 ownership trace, pre-contract structured data
closure, State 6 exact contracts, the enabled deterministic persistence and
HTTP router closures, State 7 notes, assembly, module review, and Factory
admission. Project-specific policy belongs in project artifacts under
`examples/<project>/`, never in `tools/`.

The repository entry points are discovery/orchestration only. They do not
replace the ordered design-state methodology or the requirement to read the
resolved project context before changing architecture.

## Read first

Before changing the methodology, read:

1. `skills/spec-authoring/SKILL.md`
2. `skills/spec-authoring/SPEC_STANDARD.md`
3. `skills/spec-authoring/BEHAVIORAL_NOTES.md`
4. `skills/spec-authoring/AUTHORING_SEQUENCE.md`

When working on a case study, read its design-state documents in numerical
order before modifying its assembled `global_spec.json`.

Later design-state documents may refine earlier conceptual decisions.

## Design-state navigation tools

When working on State 1:

1. read `skills/spec-authoring/MODEL_IDENTITY_EVIDENCE.md`;
2. list models with `python tools/design_index.py examples/<case> --list --state 1 --kind model`;
3. patch a model section through `tools/design_editor.py`;
4. run `python tools/design_lint.py examples/<case> --state 1`;
5. when an assembled specification exists, run
   `python tools/design_identity_closure.py examples/<case>`;
6. do not enter State 2 or declare assembly validated until identity closure
   passes.

For agent or future MCP inspection, use the workbench's `--inventory` and
`--get ModelName` operations. Transport wrappers must call
`identity_workbench` and must not reimplement identity parsing or comparison.

After assembly, run `python tools/design_assembly.py examples/<case>` for the
aggregate readiness gate. Use `--check <name>` for a detailed owner report;
future MCP wrappers must call `assembly_workbench` instead of reimplementing
the orchestration.

Before semantic closure, build one final packet per assembled module with
`python tools/design_module_review.py examples/<case> --module <name> --slice
--json`. Run `--review` for deterministic gaps, then perform the Stage 7.1
adversarial review from the packet; note count alone is not completeness.

Before moving from State 2 to State 3:

1. read `skills/spec-authoring/SECURITY_REVIEW_EVIDENCE.md`;
2. perform the security review across States 0–2;
3. use `tools/design_index.py` to navigate affected models and decisions;
4. use `tools/design_editor.py` for structural changes;
5. run `python tools/design_lint.py examples/<case> --state 2`;
6. do not enter State 3 while any security category is `UNRESOLVED`.

Before composing a multi-tool design workflow, ask the deterministic router for
the applicable plan:

```bash
python tools/design_router.py examples/<case> <intent> --json
```

Supported intents are `inventory`, `inspect-item`, `trace-term`,
`diagnose-state2`, `edit-fragment`, and `verify`. Follow the returned step order,
review checkpoints, and stop conditions. The router is advisory and read-only;
it does not authorize semantic content or execute its command previews.

When a case study has multiple decisions or supporting Markdown files, prefer
`tools/design_index.py` over raw `grep` for design-state navigation.

For State 2, begin with the indexed decision inventory when available:

```bash
python tools/design_index.py examples/<case> --list --state 2 --kind decision
```

Use `--get` and `--references` for explicit design structure. Shared words do
not create architectural relations.

When moving from State 2 to State 3, use the required expand -> narrow ->
references loop documented in `tools/DESIGN_INDEX_WORKFLOW.md` before assigning
a primary enforcement owner:

```bash
python tools/design_index.py examples/<case> --mentions <name>
python tools/design_index.py examples/<case> --mentions-in-items <name> --state 2 --kind decision
python tools/design_index.py examples/<case> --references <decision-id>
```

Use `--context` selectively for broad results that may change ownership,
dependencies, forbidden responsibilities, or external constraints. The broad
mention pass is intentionally wider than the normative state; the focused pass
returns to indexed State 2 evidence.

The tool may suggest where to read next; it must not invent module names,
responsibility clusters, or ownership from lexical overlap.

## Decision hierarchy

```text
Product
↓
Models
↓
Rules and invariants
↓
Module responsibilities
↓
System flows
↓
Public APIs
↓
Contracts
↓
Notes
↓
Assembly
Architecture repair rule
Always modify the earliest design state that owns an engineering decision.
Never repair only the symptom in a lower layer.
Examples:
incorrect entity or field → repair models;
incorrect invariant → repair rules;
incorrect ownership → repair module responsibilities;
incorrect sequence → repair flows;
incorrect public boundary → repair public APIs;
incorrect signature → repair contracts;
missing implementation guidance → repair notes.
Update global_spec.json only after all affected earlier states agree.
Working rules
Do not generate a complete specification directly from a short product idea.
Work through the design states in order.
Return to an earlier state when later work exposes a missing decision.
Do not hide unknowns behind dict, Any, metadata, utils, manager, processor, or vague prose.
Localize genuine unknowns behind explicit integration boundaries.
Do not introduce product behavior only during JSON assembly.
Do not silently resolve documented open questions.
Do not change the global_spec.json structure during methodology work.
Do not introduce new classified-note markers without a separate explicit change to the factory tools.
Prefer the existing SPEC_STANDARD structure and supported markers.
Factory constraints
A deep module and a generation unit are different concepts.
A deep module is a public semantic boundary with a small API that hides substantial behavior.
A generation unit is a bounded file or local specification generated in one LLM context.
One deep module may contain several generation units while exposing one public package API.
Rules:
Split generation units to improve reliable generation.
Do not split only to reduce line count.
Do not expose internal pipeline stages as public APIs.
Keep each generation unit focused enough for one LLM pass.
Avoid units requiring unrelated HTTP, persistence, UI, and domain context.
Generate package facades after internal units are stable.
Public callers must not depend on internal generation-unit paths.
Pydantic constraints
Domain and boundary models use Pydantic.
Schemas use extra="forbid" unless explicitly justified.
Prefer discriminated unions over generic operation/payload models.
Committed snapshots and value objects are immutable where appropriate.
Pydantic validators own local model consistency.
Domain modules own graph-wide and repository-dependent policy.
Pydantic domain models remain independent from SQLAlchemy ORM models.
Notes constraints
Behavioral authoring guidance may improve how existing notes are written, but it must not change the factory language.
The final specification continues to use only existing classified-note markers supported by SPEC_STANDARD.
Do not add new sections, fields, markers, or schemas to global_spec.json merely to represent authoring methodology.
Placeholder test
For every meaningful function ask:
Can this function return None, [], {}, an empty model, or merely forward its input without violating its notes?
If yes, the notes or an earlier design state are incomplete.
Also check whether an implementation can:
omit required behavior;
discard provenance;
return nondeterministic ordering;
fabricate a fallback value;
duplicate business logic in HTTP or MCP;
expose an internal generation unit as a public dependency.
Change discipline
When changing a case study:
Identify the earliest affected design state.
Update that state.
Propagate the decision through later states.
Update contracts and notes.
Update global_spec.json last.
Run available validators.
Report unresolved decisions explicitly.
Basic checks
Validate JSON syntax:
python -m json.tool path/to/global_spec.json >/dev/null
Check patch integrity:
git diff --check
Search for obvious placeholders:
grep -RInE \
  'TODO|FIXME|pass$|dict\[str, Any\]|process correctly|handle errors appropriately' \
  skills examples
Do not invent validator commands. Use only commands documented by the current repository or factory workspace.
Definition of done
A specification change is complete when:
the decision is recorded at the correct design state;
all affected later states agree;
every public operation has one owner;
every contract belongs to one generation unit;
public package exports remain narrow;
models, rules, contracts, notes, imports, and module order are consistent;
placeholder implementations violate explicit notes;
valid local implementation freedom remains;
