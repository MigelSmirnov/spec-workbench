# Cabinet Vault — next session handoff

## Direction

Cabinet is being tested as a self-described local data/authority box compiled into a generic host, not as a permanently product-specific backend application.

`Cabinet_web` is an autonomous application. `cabinet_backend` is a separate local durable/authority box that may connect intermittently to accept or return data. Neither application is a permanent runtime dependency of the other.

```text
Cabinet_web Card facts
        ↓ exact versioned synchronization
Cabinet local durable box
        ↓
verified generic host providers
        ↓
verified capability-specific lowerings
        ↓
local archive / source custody / effects / audit
```

Deterministic host/runtime code may implement declared rules only. Missing product meaning must remain a structured gap rather than being hidden in glue code.

## Isolated box milestone — PASS

Verified generic providers:

```text
authority_kernel
typed_schema_kernel
postgres_record_kernel
local_private_byte_vault
protected_configuration_kernel
```

The protected `invoice.source.attach` runtime proves exact authority, expected-source binding, bounded validation, PostgreSQL locking/transactions, private byte staging, atomic publication, replay, conflict rejection, crash recovery and append-only audit.

Evidence:

```text
experiments/cabinet-vault/INVOICE_SOURCE_ATTACH_RUNTIME_EVIDENCE.md
```

The original verified runtime implementation remains unchanged by the Cabinet_web interoperability work.

## Cabinet_web source identity — PASS

Reviewed upstream:

```text
MigelSmirnov/Cabinet_web
main @ d4419e3b948d49bd85a99a0941a350a73494cd27
PR #16 accepted
```

Invoice Card V1 owns stable `source.source_id`. The identity survives storage-metadata changes and `invoice_source` payment evidence references it.

Backend code may reference this identity but may not mint or replace it.

## Cabinet_web synchronization contract and acceptance runtime — PASS

Machine contract:

```text
experiments/cabinet-vault/cabinet_web_sync_contract_v1.yaml
```

Executable box extension:

```text
experiments/cabinet-vault/cabinet_web_sync_box_extension_v1.yaml
```

The v1 synchronization unit is one exact confirmed Invoice Card revision.

```text
revision identity = invoice_id + canonical card_content_hash
provenance        = source_git_commit_sha + repository path
retry identity    = delivery_id
```

The box now exposes:

```text
invoice.archive.accept_revision
```

The acceptance runtime verifies the exact canonical Card hash, consumes a reviewed Cabinet_web validation result, enforces delivery idempotency and base-revision reconciliation, stores every accepted Card revision immutably, updates current source expectations without inventing MIME/hash facts, and returns `cabinet-backend-sync-receipt-v1`.

It does **not** re-enable the deferred classical `InvoiceTransferManifest` VPS transport ingest.

Runtime evidence:

```text
experiments/cabinet-vault/CABINET_WEB_SYNC_RUNTIME_EVIDENCE.md
```

Verified GitHub execution:

```text
workflow: Cabinet Web attach canary
run_id: 32514048863
run_number: 13
head_sha: 4bd7b20d48983465757474ee6c950abebeac0b5c
conclusion: success
artifact_id: 9458097099
artifact_digest: sha256:4f09fd9fc9eef2d12df7211eb46661eb152874c01c37533a940220c797c955e7
```

Probes:

```text
SYNC-RUNTIME-001 PASS  immutable revision + source expectation
SYNC-RUNTIME-002 PASS  delivery idempotency + identity conflict
SYNC-RUNTIME-003 PASS  base-revision reconciliation + history retention
SYNC-RUNTIME-004 PASS  canonical hash/validator rejection fail closed
WEB-E2E-001      PASS  same invoice: accept revision -> receipt -> attach bytes
```

The local checkout adapter:

```text
tools/cabinet_web_checkout_sync_adapter.py
```

pins the reviewed Cabinet_web validator/schema/hash fingerprints, requires a clean tracked Card on `main`, invokes Cabinet_web's own deterministic validator as a disposable subprocess boundary, and builds the exact sync-v1 delivery. The local box itself does not import Cabinet_web runtime modules.

## Cabinet_web media and no-expected-hash path — PASS

Exact binary media type is derived from bytes by bounded parser evidence, not from:

```text
source.kind
filename
extension
caller-declared MIME
```

Supported parser relations remain:

```text
image/jpeg
image/png
application/pdf
```

When the Card contains no expected binary SHA-256, the local box calculates the hash and stores it as local custody evidence. It does not rewrite the confirmed Card or fabricate an upstream hash expectation.

Runtime evidence:

```text
experiments/cabinet-vault/CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md
```

Verified GitHub execution:

```text
workflow: Cabinet Web attach canary
run_id: 32507028221
run_number: 2
head_sha: ca542b9b3dd60112f8cdd20c532f8a6f02c17d64
conclusion: success
artifact_id: 9455627318
artifact_digest: sha256:1f7bcc1cabd2e8d4f58cb8310b915fc47944385d6f53d20d27e81a726b11c33e
```

Probes:

```text
WEB-ATTACH-001 PASS  no-MIME/no-hash attach + immutable Card
WEB-ATTACH-002 PASS  replay + conflicting-byte rejection
WEB-ATTACH-003 PASS  crash recovery
WEB-ATTACH-004 PASS  malformed content rejected before publication
```

## Interoperability gate — PASS

Machine audit:

```text
experiments/cabinet-vault/cabinet_web_interop_audit_v0.yaml
```

Current state:

```text
isolated_box_runtime_evidence      PASS
source_identity_contract           PASS
sync_contract_design               PASS
sync_acceptance_runtime            PASS
same_invoice_e2e_runtime           PASS
media_lowering_runtime             PASS
no_expected_hash_runtime           PASS
cabinet_web_interop_gate           PASS
real Cabinet_web user-data canary  ALLOWED_NOT_EXECUTED
```

Do not confuse the executed contract/runtime canaries with real user-data execution.

## Current real-data readiness — BLOCKED BY INPUT AVAILABILITY

Machine readiness:

```text
experiments/cabinet-vault/cabinet_web_real_data_canary_readiness_v1.yaml
```

At reviewed `Cabinet_web/main`, `data/cards` contains:

```text
client-uliana-kolpacheva-20260815
project-uliana-floor-20260815
provider-andrey-bam-20260801
provider-santo-grua-20260815
```

There is currently no Invoice Card directory, hence no exact confirmed Invoice Card revision that can be honestly bound to real source bytes for a user-data canary.

Do not use a test fixture, synthetic Card, draft, dirty working-tree Card, or unaccepted branch-only invoice and call it a real-data canary.

## Local agent task

The local agent can now execute the first real canary without implementing new synchronization mechanics.

Exact handoff:

```text
experiments/cabinet-vault/LOCAL_AGENT_REAL_DATA_CANARY_HANDOFF.md
```

The agent should update both repositories, obtain one real confirmed Invoice Card through the normal Cabinet_web workflow, ensure the exact Card is committed to `main`, retain the real source bytes, build the delivery through `cabinet_web_checkout_sync_adapter.py`, call `invoice.archive.accept_revision`, retain the receipt, then call the verified source-attachment path for the same invoice/source identity.

## Next transition

Once an eligible real invoice/source pair exists:

1. refresh Cabinet_web `main` inventory and fingerprint;
2. run the local-agent handoff exactly;
3. record the safe receipt/source evidence;
4. prove the confirmed Card document/content hash remained unchanged;
5. mark the real user-data canary executed only after all checks pass.

The interoperability architecture should not be redesigned merely because the current repository has no eligible invoice candidate.

## Other open semantic work remains separate

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit conversion evidence
```

Do not close these through Cabinet_web integration glue.
