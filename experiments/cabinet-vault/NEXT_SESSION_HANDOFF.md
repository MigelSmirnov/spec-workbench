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

The protected `invoice.source.attach` runtime already proves exact authority, expected-source binding, bounded validation, PostgreSQL locking/transactions, private byte staging, atomic publication, replay, conflict rejection, crash recovery and append-only audit.

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

Invoice Card V1 now owns stable `source.source_id`. The identity survives storage-metadata changes and `invoice_source` payment evidence references it.

Backend code may reference this identity but may not mint or replace it.

## Cabinet_web synchronization contract — PASS

Machine contract:

```text
experiments/cabinet-vault/cabinet_web_sync_contract_v1.yaml
```

The v1 synchronization unit is one exact confirmed Invoice Card revision.

```text
revision identity = invoice_id + canonical card_content_hash
provenance        = source_git_commit_sha + repository path
retry identity    = delivery_id
```

A stale backend base requires reconciliation rather than last-write-wins. Arrival order is not Git ancestry. Receipt metadata is separate from immutable Card facts.

Card acceptance and source-byte attachment remain separate lifecycle operations.

## Cabinet_web media and no-expected-hash path — PASS

The previous blockers are closed by executed GitHub runtime evidence.

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

The disposable Cabinet_web adapter performs parser-backed media/hash derivation and then calls the existing authority-enforced attach runtime, which revalidates the bytes before effects.

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
media_lowering_runtime             PASS
no_expected_hash_runtime           PASS
cabinet_web_interop_gate           PASS
real Cabinet_web user-data canary  ALLOWED_NOT_EXECUTED
```

Do not confuse the executed contract/runtime canary with real user-data execution.

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

Do not use a test fixture, synthetic Card, draft, or unaccepted branch-only invoice and call it a real-data canary.

## Next action

When a real invoice becomes available in the Cabinet_web workflow:

1. refresh Cabinet_web `main` fingerprint;
2. select one confirmed Invoice Card and exact source bytes;
3. pin `invoice_id`, Card canonical content hash, source Git commit SHA and `source_id`;
4. deliver the exact Card revision through `cabinet-web-sync-v1`;
5. record the backend acceptance receipt;
6. attach source bytes through the verified Cabinet_web source adapter;
7. record parser media type and local SHA-256 evidence;
8. prove the confirmed Card document/content hash is unchanged;
9. only then mark the real user-data canary executed.

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
