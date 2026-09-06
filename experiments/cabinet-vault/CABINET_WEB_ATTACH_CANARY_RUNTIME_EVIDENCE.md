# Cabinet Web source attach canary runtime evidence

## Result

PASS.

This evidence covers the Cabinet_web-compatible local source attachment case where the accepted confirmed Invoice Card owns `source_id` but contains neither an exact binary media type nor an expected binary SHA-256.

## GitHub execution

```text
workflow: Cabinet Web attach canary
run_id: 32507028221
run_number: 2
head_branch: agent/cabinet-web-attach-canary
head_sha: ca542b9b3dd60112f8cdd20c532f8a6f02c17d64
executed_at: 2026-08-21
conclusion: success
```

Artifact:

```text
artifact_id: 9455627318
name: cabinet-web-source-attach-canary
digest: sha256:1f7bcc1cabd2e8d4f58cb8310b915fc47944385d6f53d20d27e81a726b11c33e
```

The uploaded JSON reported:

```text
schema_version: spec_workbench_cabinet_web_attach_canary.v1
status: pass
WEB-ATTACH-001: PASS
WEB-ATTACH-002: PASS
WEB-ATTACH-003: PASS
WEB-ATTACH-004: PASS
```

## Proven behavior

`WEB-ATTACH-001` proved that bytes with no upstream exact MIME and no upstream binary hash were identified by bounded parser evidence, attached through the existing authority-enforced runtime, and persisted with local `image/png` plus calculated SHA-256 evidence while the confirmed Card document and canonical Card revision hash remained unchanged.

`WEB-ATTACH-002` proved that the no-expected-hash path is idempotent for equal bytes and rejects different bytes for the same source identity.

`WEB-ATTACH-003` proved that an induced failure after metadata commit leaves recoverable pending evidence and startup recovery converges on one verified available source without changing confirmed Card facts.

`WEB-ATTACH-004` proved that unrecognized bytes fail before staging/publication and leave the accepted Card/source expectation unchanged.

## Boundary preserved

The canary did not modify the previously verified `experiments/cabinet-vault/tools/invoice_source_attach_runtime.py`. Cabinet_web-owned `source_id` remained the source identity. Parser-observed media type and locally calculated SHA-256 remained local-box evidence and were not written into the confirmed Card or converted into fabricated upstream expectations.

## Gate consequence

This runtime evidence closes the specific interoperability blockers `CW-MEDIA-001` and `CW-HASH-001` for the Cabinet_web-compatible attachment path.

It does **not** claim that real Cabinet_web user data has already been sent through the local box. The next gate is a real-data canary using an exact accepted Cabinet_web revision and source bytes under the now-verified synchronization/attachment contract.
