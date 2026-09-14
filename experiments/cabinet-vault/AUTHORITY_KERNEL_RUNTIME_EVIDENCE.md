# Authority kernel — executed runtime evidence

## Status

`PASS`

Executed on 2026-08-21 in the selected Termux runtime against the fingerprint-bound candidate:

```text
experiments/cabinet-vault/tools/authority_kernel.py
experiments/cabinet-vault/tools/authority_kernel_probe.py
```

Observed runner result supplied from the real runtime:

```text
schema_version: spec_workbench_authority_kernel_probe.v0
status: pass
authority_probe_exit=0
```

The reported tail also directly showed:

```text
AUTH-PROBE-008 PASS
authentication/authorization audit evidence contained no reusable credential material
```

The reviewed probe runner returns overall `status: pass` and exit `0` only when every one of `AUTH-PROBE-001..008` returns `PASS`. Therefore this execution is evidence for the full fingerprint-bound packet, not only probe 008.

## Proven obligations

```text
AUTH-PROBE-001 PASS  caller-supplied authorization decision cannot authorize an invocation
AUTH-PROBE-002 PASS  revoked principal or credential cannot authorize future invocation
AUTH-PROBE-003 PASS  exact resource scope is required
AUTH-PROBE-004 PASS  synchronization credential is rejected at the local-agent boundary
AUTH-PROBE-005 PASS  local-agent credential is rejected as synchronization authority
AUTH-PROBE-006 PASS  unauthorized effects and disclosures are denied
AUTH-PROBE-007 PASS  protected mutation actor is bound from authenticated principal
AUTH-PROBE-008 PASS  audit evidence contains no reusable credential material
```

## Boundary of the result

This verifies the current generic authority candidate representation against the accepted Cabinet authority semantics. It does **not** declare `AUTH-OQ-001` or `AUTH-OQ-002` globally resolved, does not make Cabinet role names part of the generic host, and does not prove a particular password hashing, session, database, transport, or credential-storage mechanism.

With this evidence, all five required providers in `generic_host_profile_candidate_v0.yaml` have executed PASS evidence. The structural host lowering verification gate may therefore move from `block` to `pass` for the fingerprint-bound candidate profile.
