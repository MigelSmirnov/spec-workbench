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
  - the rule namespaces declared by `60_data_closure.json`; a namespace
    its `retired` list names (`{"address": "rules.<namespace>", "reason",
    "source_refs"}`) is removed. Retirement is authored because a namespace
    the closure dropped and one it never declared (a hand-carried backend
    binding) look the same in the assembled spec; the lint refuses a retired
    namespace that `sections.rules` still declares or that is a backend IR
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
- every closed standard backend closure (`tools/standard_backends.py`), its
  `backend_ir` verbatim:
  - `rules.<rule_key>` from `70_<id>_closure.json`, for example
    `rules.sqlite_unit_of_work_backend` from
    `70_sqlite_unit_of_work_closure.json` (SPEC_STANDARD §6.12)
- the closed data-provider closure (`70_data_provider_closure.json`), whose
  module has no State 6 contracts (SPEC_STANDARD §6.10):
  - `module_functions.<wiring.module>` and `imports.internal.<wiring.module>`:
    exactly the sorted constants
  - a module new to `module_order` is placed right after the module whose
    `module_paths` entry is `wiring.models_module`, beside it under the same
    root; a module already in the order keeps its place and path (§10)

All other `global_spec.json` sections are preserved. `implementation_obligations`
(SPEC_STANDARD §5.1) is one of them: no design artifact owns it, so a case
writes its rows into `global_spec.json` as assembly and the projection carries
them unchanged.

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
