# Factory compatibility profile

## Purpose and authority

`SPEC_STANDARD.md` defines the specification language. This document records
operational constraints of the current AI Code Factory toolchain that are not
expressible in that language.

Keep the boundary explicit:

- a standard violation means the specification is invalid;
- a profile violation means the current target compiler cannot reliably
  materialize the otherwise valid design;
- contradictory behavior between Factory components is a Factory defect, not a
  reason to change product semantics.

Update this profile when the target Factory changes. Do not add fields or note
markers to `global_spec.json` to encode it.

Profiles are versioned capability snapshots, not permanent design laws. A
legacy limitation may block handoff, but it must not silently become a product
architecture requirement. During a Factory capability migration:

1. preserve the accepted semantic design;
2. keep export blocked until the normative standard and implementation agree;
3. update validator, normalizer/local slices, generator, model surface, static
   gates, consumer generation, and regression evidence as one vertical change;
4. retire the legacy restriction from this profile only after the compile probe
   proves the new representation.

## Reference baselines

### Panelforge — established positive baseline

The sibling Factory project `projects/panelforge_sandbox` is the positive
reference for capabilities it has exercised end to end. In the inspected
checkout its accepted evidence includes:

- 67 declared models and a deterministic `models -> core/models` unit;
- 29 ordered modules with deep domain, policy, rendering, storage, service, and
  API responsibilities;
- strict/frozen Pydantic models and explicit enum surfaces;
- thin API orchestration with domain and artifact policy delegated to owning
  modules;
- an assembler manifest with `PASS` for 28 rebuilt modules;
- an empty linker finding list and a passing deploy manifest.

Use Panelforge as a positive example for those exact properties. It does not
exercise named discriminated-union aliases or Protocol-based repository/UoW
ports, so it is not evidence for or against those capabilities. Copy its
architectural principles and verified boundaries, not every incidental model or
module shape.

### Hydraulic Diagram Service — capability migration probe

The hydraulic-diagram case intentionally exercises two capabilities being
added to the Factory:

- named discriminated unions with explicit discriminator and closed variants;
- Protocol-based repository, UnitOfWork, authorization, and gateway ports with
  complete method contracts.

Until the Factory standard and the full vertical toolchain materialize these
forms, the case is a blocked migration probe. Do not rewrite it into a
client-held draft, module-global registry, concrete SQLAlchemy session API, or
authorization DTO merely to pass the legacy profile unless that is an
independent product architecture decision.

## Established deterministic model profile

For the current Factory checkout:

- `models` is the first entry in `module_order`;
- the runtime model generation unit maps to `core/models` and materializes as
  `core/models.py`;
- generated consumers import runtime model symbols from `core.models`;
- conceptual `model_*` sections may be used in authoring documents, but they
  are subdivisions of the one generated `models` unit, not independently
  generated packages;
- every type used by a runtime contract or internal import must have a
  materialization form supported by both the deterministic model generator and
  downstream static gates.

The established generator baseline supports ordinary models described by
`fields`, enums, and the Factory's structured spec-data forms such as
`mapping`, `vocabulary`, and `catalog`. The reconstruction currently fails
closed for unknown model kinds; named `kind: discriminated_union`
materialization is a migration target, not yet an established capability.
Structured spec data remains addressable authoring input, not a runtime DTO
merely because the models generator emits a Python name for it.

This profile constrains generation units, not semantic architecture. Domain
modules may still expose narrow package APIs at their own paths.

## Model validation ownership

A generated Pydantic validator may enforce only local, closed model
consistency. It must be decidable from the model instance and stable value
rules.

Move validation to the owning domain or boundary module when it needs any of:

- runtime `config`;
- repository state or another record;
- filesystem, network, or process I/O;
- sanitization, parsing, or security policy for SVG, PDF, HTML, XML, or another
  rich external representation;
- graph-wide or lifecycle policy.

Keeping the external representation in a typed model field is compatible with
this rule. The distinction is ownership of policy, not ownership of bytes or
text.

## Required no-deploy compile probe

After Workbench assembly and semantic lint, export the accepted specification
through `tools/export_to_factory.py`. In the Factory project, run the existing
assembler entrypoint without `--skip-linker`:

```bash
python rebuild_module.py --project <project> models <representative-module> [other-modules ...]
```

For a full handoff, pass the complete `module_order`. This command performs the
Factory validation, normalization, local-spec generation, draft/static checks,
assembly, and linker path described by `rebuild_module.py`. It does not deploy.
Do not run `sandbox.sh deploy`, `sandbox.sh cycle`,
`factory_control/run_route_b_predeploy.sh`, or `deploy_project.py` as part of
this Workbench probe.

Export is allowed only when the Factory canonical validator exits with code 0,
reports `PASS`, and records zero errors and zero warnings. `WARNINGS_ONLY` is a
profile failure and must stop the handoff before bootstrap or compilation. Do
not classify warnings as accepted boundary types or defer them to the compile
probe; repair their owning design states so the exported specification is
warning-free.

Choose the representative consumer deliberately. Prefer a module that imports
the most demanding model surface: unions, aliases, protocols, immutable
snapshots, or nested DTOs. For every non-field form, first prove that the target
standard and generator support its exact encoding.

Handoff evidence must include:

- the canonical validation report with status `PASS` and zero findings;
- the exact command and module set;
- the assembler run id;
- `assembler_manifest.json`;
- static-gate reports for failures;
- `linker_report.json` when linker ran;
- an explicit statement that deploy was not run.

## Failure classification

### Semantic ownership failure

Example: an SVG security policy is encoded as a Pydantic field validator and
depends on a configured byte limit. Repair module ownership and propagate the
decision from the earliest affected design state.

### Missing target capability or invalid representation

Example: the authoring design maps the model catalog to a package
`domain/models/__init__`, while the target Factory emits and imports one
`core.models` runtime unit. Preserve the semantic model design but use the
supported generation-unit mapping.

Another example is a domain-correct closed union whose normative
`kind: discriminated_union` representation is still being added to the target
standard and compiler. The domain decision remains correct; handoff stays
blocked until the representation is normative and materialized. If a case
invented the shape independently of that standard change, the encoding is also
invalid and must not be treated as implicit permission.

### Factory contradiction

A contradiction requires semantic evidence from both sides. A validator
accepting unknown keys, a generator emitting a name, or a surface gate counting
that name is not evidence that the intended type was materialized. Inspect the
generated definition and a representative consumer before classifying the
failure. Only preserve the representation as a Factory defect when one
component demonstrably implements the required semantics and another rejects
that same supported form.

## Legacy failure evidence: name-only union coverage

Do not confuse architectural precision with unsupported serialization.
Consider this authoring shape:

```json
"AuthoringCommand": {
  "kind": "discriminated_union",
  "discriminator": "command_type",
  "variants": ["AddElementCommand", "RemoveElementCommand"],
  "fields": {}
}
```

The intended domain type is precise. Before the Factory reconstruction, the
standard did not define those keys as a runtime model encoding and the
deterministic generator fell through to ordinary Pydantic-model emission:

```python
class AuthoringCommand(_FrozenModel):
    pass
```

A name-based model-surface check can still report the symbol as present. A
consumer static gate may later reject its import because the source spec entry
looks like read-only spec data. The late failure is not proof that the gate is
wrong; the generated empty class proves that the requested union never existed.

Apply these checks before accepting any non-standard model form:

1. Locate the representation in `SPEC_STANDARD.md`; absence is unsupported,
   not implicit permission.
2. Locate an explicit generator branch and regression test for the form.
3. Inspect generated code for fields, variants, discriminator, alias, or root
   semantics; do not accept `N/N` name coverage alone.
4. Generate a consumer that imports and uses the type.
5. Classify a later gate failure only after steps 1–4 establish semantic
   materialization.

Do not reproduce this legacy failure by flattening the domain model. Complete
named-union support as a deliberate Factory language change covering the
standard, validator, normalization/local slicing, generator, surface
extraction, static gates, representative consumers, and tests. Until that
vertical change passes, keep the precise design and report the handoff blocker.

## Advisory Workbench check

`tools/semantic_lint.py` reports `S9` when a specification with generated
models does not map the `models` unit to `core/models`. `S9` is advisory because
it represents this target profile, not the normative specification language.
