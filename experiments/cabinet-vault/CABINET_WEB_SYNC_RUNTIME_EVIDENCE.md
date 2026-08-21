# Cabinet Web sync runtime evidence

## Result

PASS.

This evidence covers executable `cabinet-web-sync-v1` revision acceptance and the same-invoice transition from accepted revision state to protected source-byte attachment.

## GitHub execution

```text
workflow: Cabinet Web attach canary
run_id: 32514048863
run_number: 13
head_branch: agent/cabinet-web-sync-runtime
head_sha: 4bd7b20d48983465757474ee6c950abebeac0b5c
executed_at: 2026-08-21
conclusion: success
```

Artifact:

```text
artifact_id: 9458097099
name: cabinet-web-interop-canary
digest: sha256:4f09fd9fc9eef2d12df7211eb46661eb152874c01c37533a940220c797c955e7
```

## Revision acceptance probes

The artifact `cabinet-web-revision-accept-canary.json` reported:

```text
schema_version: spec_workbench_cabinet_web_sync_runtime.v1
status: pass
SYNC-RUNTIME-001: PASS
SYNC-RUNTIME-002: PASS
SYNC-RUNTIME-003: PASS
SYNC-RUNTIME-004: PASS
```

The probes prove:

- one exact confirmed Card revision is stored immutably;
- source identity is projected without inventing binary MIME or SHA-256 expectations;
- same delivery/revision retry is idempotent;
- a delivery identity cannot be rebound to different content;
- stale base revisions return reconciliation instead of overwrite;
- a correctly based later revision is accepted without deleting the previous immutable revision;
- canonical Card hash mismatch fails closed;
- Cabinet_web validator errors fail before durable acceptance.

## Same-invoice E2E probe

The artifact `cabinet-web-e2e-canary.json` reported:

```text
schema_version: spec_workbench_cabinet_web_e2e_runtime.v1
status: pass
WEB-E2E-001: PASS
```

`WEB-E2E-001` used one PostgreSQL invoice state for both capabilities:

```text
cabinet-web-sync-v1 delivery
  -> invoice.archive.accept_revision
  -> cabinet-backend-sync-receipt-v1
  -> invoice.source.attach
  -> local source custody evidence
```

The source bytes were parser-identified and attached after revision acceptance. The accepted Card document and canonical Card revision hash remained unchanged. The locally calculated binary hash and detected MIME remained local box evidence and did not become fabricated upstream expectations.

## Boundary preserved

The sync ingress is declared as `invoice.archive.accept_revision` in `cabinet_web_sync_box_extension_v1.yaml`. It does not re-enable the deferred classical `InvoiceTransferManifest`/VPS transport ingest.

The local checkout adapter does not import Cabinet_web application modules into the box. It pins the reviewed executable contract fingerprints and invokes Cabinet_web's deterministic validator as a disposable local boundary before delivery construction.

## Gate consequence

The previous state had only a synchronization design contract. This evidence promotes the executable revision-acceptance path to PASS.

The technical sequence required by a real-data canary is now executable. The remaining blocker is only the availability of one real confirmed Invoice Card in `Cabinet_web/main` together with its corresponding real source bytes.
