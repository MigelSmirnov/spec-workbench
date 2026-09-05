# Canonical Factory validation in assembly

The aggregate assembly result now includes the `factory` check. It runs the
target Factory's canonical validator on `global_spec.json`, verifies the bound
spec SHA and accepts only a successful PASS report without errors or warnings.
Missing Factory, malformed/stale reports and tool failures block readiness.
Stage 9 calls the same `factory_validation.validate_source` service.

Configure the target explicitly:

```bash
python tools/design_assembly.py examples/<case> --factory-root /path/to/code_factory --json
```

The API accepts `factory_root=`; other orchestration can use
`SPEC_WORKBENCH_FACTORY_ROOT`. With neither, the normal sibling `code_factory`
is selected. An explicit unavailable target never falls back to another copy.
Individual owner checks remain inspectable without Factory. Aggregate readiness
is not available offline; CI records that state and checks the real bridge in
the cross-repository job.

This change belongs to `tools/pipeline-integrity-pr`, based on GitHub Workbench
`main` at `ae5fa49`. The active Cabinet branch has additional generic checks, including
witness and flows; applying this change there must preserve those checks and
append `factory`. It must not replace the branch's check registry with main's.

The companion Factory change documents standard coverage in
`docs/STANDARD_GATE_COVERAGE.md`, adds reviewed corpus replay and binds Route B
admission to its receipt. Historical rejected candidates require their original
context and reviewed expected verdicts; old reports are not automatically an oracle.

Validation for this bridge:

```bash
SPEC_WORKBENCH_FACTORY_ROOT=/path/to/code_factory python -m pytest -q \
  tests/test_factory_validation.py tests/test_factory_admission.py \
  tests/test_export_to_factory.py tests/test_design_assembly.py
```

Repository instructions reference `skills/spec-authoring/BEHAVIORAL_NOTES.md`,
which is absent on this base. The existing standard and authoring sequence were
used; no note language or product design decisions are changed here.
