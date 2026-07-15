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
- `FACTORY_COMPATIBILITY.md` records target-specific compiler conventions and
  the pre-handoff compile probe; it is not part of the specification language.
- `BEHAVIORAL_NOTES.md` explains how to design effective notes without
  changing the factory specification language.

## Read first

Before changing the methodology, read:

1. `skills/spec-authoring/SKILL.md`
2. `skills/spec-authoring/SPEC_STANDARD.md`
3. `skills/spec-authoring/FACTORY_COMPATIBILITY.md`
4. `skills/spec-authoring/BEHAVIORAL_NOTES.md`

When working on a case study, read its design-state documents in numerical
order before modifying its assembled `global_spec.json`.

Later design-state documents may refine earlier conceptual decisions.

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
Prefer discriminated unions over generic operation/payload models at the
domain-design level, but encode them only through a representation supported by
the target `SPEC_STANDARD` and Factory profile. Never invent a new model
`kind`, metadata key, or alias encoding because its Python meaning seems
obvious.
Committed snapshots and value objects are immutable where appropriate.
Pydantic validators own local model consistency.
Domain modules own graph-wide and repository-dependent policy.
Pydantic domain models remain independent from SQLAlchemy ORM models.
Treat a model validator as local only when it is pure, deterministic, and can
decide from the model's own fields and closed value-object rules. It must not
depend on runtime config, repositories, cross-record lookup, filesystem or
network I/O, or sanitization/parsing policy for rich external formats such as
SVG, PDF, HTML, or XML. Put those checks in the domain module that owns the
asset or integration boundary.

Factory compatibility constraints
Before final handoff, select and apply the current target profile from
`skills/spec-authoring/FACTORY_COMPATIBILITY.md`.
Do not assume that a conceptually valid package layout, type alias, union, or
model method is materializable by the current Factory toolchain.
Treat name-only model-surface coverage as insufficient: a generated empty class
does not prove the fields, variants, discriminator, or alias semantics.
Run the documented compile probe, including the deterministic model unit, a
representative consumer, assembler, and linker. A compile probe is not deploy.
Classify failures before editing the specification: repair semantic ownership
at its earliest design state, repair unsupported representation at the model or
module-path state, and report contradictory Factory components as toolchain
defects instead of distorting product semantics.
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
  'TODO|FIXME|pass$|dictstr, Any|process correctly|handle errors appropriately' \
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
the selected Factory compatibility profile is satisfied;
the compile probe reaches assembler and linker without deploy, or an unresolved
toolchain contradiction is explicitly recorded as a blocker;
placeholder implementations violate explicit notes;
valid local implementation freedom remains;
