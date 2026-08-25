# Assembly Verification Workbench

The assembly workbench provides one read-only post-assembly readiness report
without duplicating validation owned by deeper workbenches.

## Deep-module boundary

`tools/assembly_workbench` owns:

- deterministic orchestration of assembly checks;
- normalization of each owner's readiness, error, and warning semantics;
- stable aggregate and per-check result schemas;
- fail-closed check addressing.

It delegates semantic validation to the existing owners:

| Check | Owner |
| --- | --- |
| `identity` | `identity_workbench` |
| `data` | `design_stage6_data` compatibility workbench |
| `contracts` | `design_stage6_contracts` |
| `notes` | `notes_workbench.gate` |
| `router` | `router_workbench.service` |

The aggregate service must not parse design files, reinterpret findings, or
invent missing semantic decisions.

## Public operations

- `verify(project)` — return one compact readiness report for all checks;
- `inspect_check(project, name)` — return the selected owner's complete
  normalized report, including findings.

CLI equivalents:

```bash
python tools/design_assembly.py examples/<case>
python tools/design_assembly.py examples/<case> --json
python tools/design_assembly.py examples/<case> --check identity
```

## MCP direction

A future MCP server should register `verify` and `inspect_check` directly.
The aggregate response is intentionally compact; detailed findings are fetched
through the inspection operation so MCP clients do not receive every underlying
report unless requested.

The MCP adapter may constrain project and check selectors, but it must not run
shell commands or reproduce validation logic.
