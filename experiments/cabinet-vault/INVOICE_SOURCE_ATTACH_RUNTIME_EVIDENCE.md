# Invoice source attach — executed runtime evidence

## Status

`PASS` for the declared execution case:

```text
invoice.source.attach / attach_expected_missing_source
```

Executed on 2026-08-21 in the selected Termux runtime against the fingerprint-bound runtime lowering and probe runner.

This evidence is deliberately narrower than the full multi-file capability surface. It proves the single-file case where the caller supplies an explicit stable `invoice_id`, the file has an already-declared `expected_source_id`, and the expected source exists in the accepted invoice source state. It does not prove source-identity invention, invoice-number search/disambiguation, or multi-file batch orchestration.

## Structural guards before runtime execution

After the Pydantic v1 compatibility repair, the targeted guards produced:

```text
21 passed in 0.93s
```

The capability readiness compiler had already established:

```text
status: ready
host_verification_gate: pass
capability_readiness_gate: pass
blocking_gaps: []
exit: 0
```

## First runtime execution — defect found

The first real cross-provider execution did **not** pass. All seven runtime probes failed before byte or metadata effects because the nested Pydantic v1 models were created under postponed annotations and therefore retained unresolved `ForwardRef` fields.

Representative failure:

```text
TypedSchemaValidationError:
field "invoice_id" not yet prepared so type is still a ForwardRef
```

This was classified as an implementation compatibility defect, not a Cabinet semantic gap and not a generic provider failure.

Repair:

```text
remove postponed annotations from experiments/cabinet-vault/tools/invoice_source_attach_models.py
bind the new model blob fingerprint
add a regression guard that validates nested input/output models through TypedSchemaKernel
```

The repair did not change the capability contract, authority meaning, source identity rules, publication ordering, or disclosure policy.

## Successful rerun

The real runtime then produced:

```text
ATTACH-PROBE-001 PASS
  typed explicit target and exact invoice authority were required before byte or metadata effects

ATTACH-PROBE-002 PASS
  expected source/hash and bounded parser validation failed closed before staging or metadata publication

ATTACH-PROBE-003 PASS
  metadata committed, bytes published and reverified, then source became available with a safe completed result

ATTACH-PROBE-004 PASS
  equivalent replay returned the existing logical attachment without a duplicate metadata transition

ATTACH-PROBE-005 PASS
  different bytes for one exact expected source were rejected without replacing accepted publication or source evidence

ATTACH-PROBE-006 PASS
  crash after metadata commit preserved pending provenance and startup recovery converged on one published verified source

ATTACH-PROBE-007 PASS
  safe output and durable append-only audit contained no raw storage references, config keys, or reusable credential material

schema_version: spec_workbench_invoice_source_attach_runtime_probe.v0
status: pass
attach_runtime_exit=0
```

## Post-promotion guard verification

After recording the PASS runtime evidence and quoting the YAML evidence date as a stable string scalar, the final targeted machine-state guards were rerun in Termux:

```text
21 passed in 1.02s
git diff --check: pass
```

No implementation or runtime-probe fingerprint changed during this final evidence-metadata repair, so the successful end-to-end runtime probe did not need to be repeated.

## What this proves

For the fingerprint-bound single-file execution case, the selected Termux runtime proved the declared cross-provider ordering and invariants:

```text
typed input before effects
+ exact authenticated capability/resource authority
+ expected source/hash binding
+ bounded JPEG/PNG/PDF validation
+ private byte staging and reopen/hash/size verification
+ exact PostgreSQL invoice/source locking
+ atomic metadata-committed publication journal and pending source transition
+ final atomic byte publication and final verification before available status
+ idempotent equivalent replay
+ conflicting bytes rejected without replacing accepted evidence
+ recoverable crash after metadata commit
+ durable append-only audit
+ no raw storage/config/credential disclosure
```

## Boundary of the result

This evidence does **not** prove:

- multi-file batch orchestration for `AttachLocalSourceInput.files` with more than one file;
- source identity generation when `expected_source_id` is absent;
- invoice-number lookup or ambiguity resolution;
- attachment to a non-accepted invoice;
- any external transport such as HTTP, MCP, or IPC;
- PlanActual monetary semantics;
- that the old classical generated backend is verified.

The result demonstrates that one real protected Cabinet capability path can be executed through the verified generic host/provider composition without reintroducing a Cabinet service/repository/router architecture.
