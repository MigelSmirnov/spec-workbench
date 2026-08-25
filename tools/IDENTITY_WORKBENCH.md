# Model Identity Workbench

The identity workbench verifies that runtime model identity remains consistent
from canonical State 1 evidence through machine-readable model closure to the
assembled `global_spec.json`.

## Deep-module boundary

`tools/identity_workbench` owns:

- parsing canonical State 1 model identity records;
- loading machine-readable model closure and assembled runtime models;
- deterministic cross-layer comparison;
- stable inventory, inspection, and verification result schemas.

CLI and future MCP servers are thin adapters. They must not parse Markdown or
JSON independently, infer identity from fields, or repair semantic decisions.

## Public operations

The module exposes three transport-neutral operations:

- `inventory(project)` — list models and identity values visible at each layer;
- `inspect_model(project, name)` — return one model's values and source locations;
- `verify(project)` — fail-closed cross-layer validation of every assembled
  runtime model.

CLI equivalents:

```bash
python tools/design_identity_closure.py examples/<case> --inventory
python tools/design_identity_closure.py examples/<case> --get ModelName
python tools/design_identity_closure.py examples/<case> --json
```

## MCP direction

A future MCP server should expose the three public operations directly and use
their versioned JSON results as tool outputs. The MCP boundary may validate the
project selector and model name, but must not duplicate comparison logic.

The workbench is deliberately read-only. Choosing or changing `value` versus
`entity` remains a State 1 semantic decision performed by an operator or
authoring agent.
