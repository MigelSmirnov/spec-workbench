# Bounded content validation — executed runtime evidence

## Status

`PASS`

Executed on 2026-08-21 in the selected Termux runtime against the fingerprint-bound capability execution provider:

```text
experiments/cabinet-vault/tools/bounded_content_validation_kernel.py
experiments/cabinet-vault/tools/bounded_content_validation_kernel_probe.py
```

Observed focused guards:

```text
15 passed in 0.83s
git diff --check: pass
```

Observed runner result:

```text
schema_version: spec_workbench_bounded_content_validation_kernel_probe.v0
status: pass
content_probe_exit=0
```

## Proven obligations

```text
CONTENT-PROBE-001 PASS  Pillow and pypdf import; Pillow decompression-bomb protection enabled
CONTENT-PROBE-002 PASS  valid JPEG/PNG parse; parser-observed format must match declared media type
CONTENT-PROBE-003 PASS  truncated JPEG/PNG fail closed
CONTENT-PROBE-004 PASS  strict PDF parse; malformed PDF and MIME mismatch fail closed
CONTENT-PROBE-005 PASS  size/media envelope fails closed and disabled image decompression guard blocks readiness
```

The selected lowering therefore does not treat filename, extension, caller media type, or a magic prefix as sufficient validation evidence. It uses bounded envelope checks plus parser-observed JPEG/PNG validation and strict PDF structural parsing.

## Boundary of the result

This verifies the selected generic content-validation lowering for the current closed Cabinet source media set (`image/jpeg`, `image/png`, `application/pdf`) and configured 50 MiB size bound. It does not interpret or execute embedded PDF content, does not make parser libraries part of Cabinet product identity, and does not expand the accepted media set.
