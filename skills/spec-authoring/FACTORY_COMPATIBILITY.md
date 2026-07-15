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

## Current deterministic model profile

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

The current deterministic generator supports ordinary models described by
`fields`, enums, and the Factory's structured spec-data forms such as
`mapping`, `vocabulary`, and `catalog`. It does not define or materialize a
named `kind: discriminated_union` representation. Structured spec data is
addressable authoring input, not a runtime DTO merely because the models
generator emits a Python name for it.

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

Choose the representative consumer deliberately. Prefer a module that imports
the most demanding model surface: unions, aliases, protocols, immutable
snapshots, or nested DTOs. For every non-field form, first prove that the target
standard and generator support its exact encoding.

Handoff evidence must include:

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

### Unsupported target representation

Example: the authoring design maps the model catalog to a package
`domain/models/__init__`, while the target Factory emits and imports one
`core.models` runtime unit. Preserve the semantic model design but use the
supported generation-unit mapping.

Another example is a domain-correct closed union encoded with an invented
`kind: discriminated_union` object that the target standard never defined. The
domain decision may remain correct while the JSON representation is invalid
for the selected compiler.

### Factory contradiction

A contradiction requires semantic evidence from both sides. A validator
accepting unknown keys, a generator emitting a name, or a surface gate counting
that name is not evidence that the intended type was materialized. Inspect the
generated definition and a representative consumer before classifying the
failure. Only preserve the representation as a Factory defect when one
component demonstrably implements the required semantics and another rejects
that same supported form.

## Accuracy anti-pattern: invented type shape with name-only coverage

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

The intended domain type is precise, but the current Factory standard does not
define those keys as a runtime model encoding. The deterministic generator
falls through to ordinary Pydantic-model emission and produces:

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

For the current profile, express closed unions through supported field and
contract type expressions, or make named-union support a deliberate Factory
language change covering the standard, validator, generator, surface
extraction, static gates, and tests.

## Advisory Workbench check

`tools/semantic_lint.py` reports `S9` when a specification with generated
models does not map the `models` unit to `core/models`. `S9` is advisory because
it represents this target profile, not the normative specification language.
