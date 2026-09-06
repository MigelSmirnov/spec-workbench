# Typed schema kernel runtime evidence

## Status

PASS

## Execution

Date: 2026-08-21
Runtime: user-selected Termux environment on Android
Runner: `experiments/cabinet-vault/tools/typed_schema_kernel_probe.py`
Runner fingerprint is bound in `generic_host_provider_verification_v0.yaml`.

Observed terminal result:

```text
"schema_version": "spec_workbench_typed_schema_kernel_probe.v0",
"status": "pass"
schema_probe_exit=0
```

The runner returns exit `0` only when all required schema probes return `PASS`.
Therefore the observed result proves the complete fingerprint-bound packet:

```text
SCHEMA-PROBE-001 PASS  invalid typed input rejected before operation/effect
SCHEMA-PROBE-002 PASS  undeclared caller fields rejected at the closed boundary
SCHEMA-PROBE-003 PASS  invalid provider output rejected before typed disclosure
```

## Dependency note

The selected Termux environment initially lacked `pydantic`, so the provider
remained fail-closed rather than being treated as verified. Installation of
Pydantic v2 attempted to build `pydantic-core` and failed in this runtime. The
provider and probe deliberately support the Pydantic v1 validation API as well;
a compatible Pydantic runtime was then selected and the fingerprint-bound probe
completed with `status: pass` and exit `0`.

This evidence verifies the declared typed-validation semantics. It does not make
a Pydantic major version part of the durable Cabinet semantic contract.
