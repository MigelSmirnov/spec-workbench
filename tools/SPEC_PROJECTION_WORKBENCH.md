# Specification Projection Workbench

`spec_projection_workbench` owns deterministic Stage 8 materialization of
already-closed authoring handoffs into `global_spec.json`.

It is deliberately **not** a new semantic design pass. It reads the normative
`skills/spec-authoring/authoring_sequence.json`, preserves specification
surfaces it does not own, and refuses to apply when an enabled deterministic
backend has no ready handoff.

## Owned projections

The initial projector owns only surfaces that already have deterministic
Workbench owners:

- accepted pre-contract structured data:
  - `config`
  - the rule namespaces declared by `60_data_closure.json`
  - `persistence`
  - `properties`
  - `determinism`
- ready State 6 handoff:
  - exact `contracts`
  - exact `function_order`
  - callable/class ownership inside `module_functions`
- ready deterministic persistence handoff:
  - `rules.persistence_backend`
- ready deterministic Router IR assembly:
  - `rules.http_router_backend`

All other `global_spec.json` sections are preserved.

An existing deterministic backend without its authoring owner is a BLOCK.
An open/invalid enabled backend is also a BLOCK. The projector never deletes
the source artifact or falls back to an LLM-owned implementation.

## Workflow

Inspect what would change:

```bash
python tools/design_spec_projection.py examples/<case> --plan --json
python tools/design_spec_projection.py examples/<case> --diff
```

Apply only when every registered source is ready:

```bash
python tools/design_spec_projection.py examples/<case> --apply
```

Then prove that the checked-in artifact matches its machine-owned sources:

```bash
python tools/design_spec_projection.py examples/<case> --verify --json
python tools/design_assembly.py examples/<case>
```

`--apply` writes atomically and immediately re-runs projection verification. If
post-write verification fails, the original `global_spec.json` is restored.

## Canonical serialization

Application emits UTF-8 JSON with two-space indentation. The first application
to a legacy hand-formatted specification may therefore include formatting
normalization. Always inspect `--diff` before applying and keep semantic review
based on the resulting assembled slice hash.
