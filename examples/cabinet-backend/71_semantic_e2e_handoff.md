# Cabinet Backend — Stage 7.1 Semantic E2E handoff

Status: **semantic_closed — six reviewed flows have executable Workbench-owned runtime oracles**.

The detailed original scenario plan remains represented by the six `71_flow_*_semantic_review.md` records and the executable tests under `tests/semantic/`. Stage 7.1 found and repaired material ambiguity in every reviewed flow before runtime handoff.

## Closure summary

| Flow | Review | Runtime oracle |
|---|---|---|
| `flow:synchronize_invoice_to_local_archive` | `71_flow_1_semantic_review.md` | `tests/semantic/test_synchronize_invoice_to_local_archive.py` |
| `flow:accept_local_source_attachment` | `71_flow_2_semantic_review.md` | `tests/semantic/test_accept_local_source_attachment.py` |
| `flow:refresh_registry_and_validate_assignment` | `71_flow_3_semantic_review.md` | `tests/semantic/test_refresh_registry_and_validate_assignment.py` |
| `flow:calculate_plan_actual` | `71_flow_4_semantic_review.md` | `tests/semantic/test_calculate_plan_actual.py` |
| `flow:publish_invoice_to_holded` | `71_flow_5_semantic_review.md` | `tests/semantic/test_publish_invoice_to_holded.py` |
| `flow:release_vps_working_copy` | `71_flow_6_semantic_review.md` | `tests/semantic/test_release_vps_working_copy.py` |

## Runtime-oracle ownership

The files under `tests/semantic/` are Workbench acceptance artifacts derived from semantic-closed scenarios. They are not implementation tests for the Workbench itself and they must not be rewritten merely to fit generated code.

Each oracle depends on a Factory/project-owned pytest fixture named `semantic_runtime`. That fixture is the binding seam from generated public operations to the implementation-independent assertions. The Factory may implement the fixture and supporting test adapters, but it must preserve the Workbench test files byte-for-byte unless the upstream specification is intentionally changed and Stage 7.1 is reviewed again.

## Factory handoff preparation

`71_semantic_test_export.json` declares the semantic test export set. `tools/export_to_factory.py` recognizes this manifest when exporting with `--case` and is prepared to:

1. require the manifest status `semantic_closed`;
2. verify every declared source test exists inside the case directory;
3. copy each test byte-for-byte into the Factory project `tests/semantic/` directory;
4. reject a differing existing target unless `--update-existing` is explicit;
5. verify source and target SHA-256 after copy;
6. record per-file provenance in `spec_workbench_handoff.json`;
7. record `factory_execution_verified = false` because Workbench export cannot prove local Factory runtime execution.

The physical Factory migration and execution are intentionally **not claimed here**. The Factory is local and unavailable in this environment. The prepared exporter must be exercised against the real local Factory checkout before runtime acceptance can be reported as passing.

## Local Factory completion gate

After export on the local machine, Stage 7.1 runtime handoff is operationally complete only when:

```text
all six declared semantic tests copied with matching SHA-256
+ Factory semantic_runtime binding exists
+ pytest executes the copied tests in the generated project
+ failures are treated as implementation/generation defects unless upstream semantics are intentionally reopened
```

No successful local Factory execution is asserted by this Workbench closure record.
