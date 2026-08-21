# Cabinet_web compatibility audit

## Result

The Cabinet_web ↔ local-box interoperability gate is **PASS** for the currently reviewed contracts and the verified no-MIME/no-expected-hash attachment path.

A real Cabinet_web **user-data** canary is allowed but has not been executed, because the current `Cabinet_web/main` data set contains no Invoice Card under `data/cards`.

Reviewed upstream state:

```text
repository: MigelSmirnov/Cabinet_web
ref: main
commit: d4419e3b948d49bd85a99a0941a350a73494cd27
```

Machine records:

```text
experiments/cabinet-vault/cabinet_web_interop_audit_v0.yaml
experiments/cabinet-vault/cabinet_web_real_data_canary_readiness_v1.yaml
```

Executed runtime evidence:

```text
experiments/cabinet-vault/CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md
```

## Responsibility boundary

The systems remain autonomous.

`Cabinet_web` owns:

```text
Invoice Card facts and versioned Card contracts
stable source identity inside the owning Card
working draft/confirmation operations
GitHub repository Card history
conversation/Web-facing workspace behavior
```

The local box owns:

```text
durable local archive replicas
local source bytes and publication recovery
local authority/effect enforcement
append-only operational audit
integration/processing evidence
```

The local box does not rewrite confirmed Card facts. Cabinet_web does not import backend database, vault or runtime structures as its domain model.

## CW-SOURCE-ID-001 — PASS

Cabinet_web PR #16 was accepted into `main`. Invoice Card V1 now requires `source.source_id`, its deterministic validator binds `invoice_source` payment evidence to that identity, and draft/source-metadata operations preserve rather than replace the source identity.

Backend integration may reference the Web-owned `source_id`; it may not generate or infer a replacement.

## CW-SYNC-001 — PASS

The transport-independent synchronization contract is:

```text
experiments/cabinet-vault/cabinet_web_sync_contract_v1.yaml
```

It synchronizes one exact confirmed Invoice Card revision using the existing Cabinet_web canonical content hash plus Git provenance. It separates delivery identity from revision identity, defines idempotent retry and explicit reconciliation, and returns a bounded receipt without exposing backend storage/runtime details.

Card acceptance does not claim that source bytes were attached.

## CW-MEDIA-001 — PASS

Cabinet_web `source.kind` remains a Card fact such as `photo` or `pdf`; it is not treated as exact MIME identity.

The integration uses bounded parser-backed identification over the closed accepted set:

```text
image/jpeg
image/png
application/pdf
```

The implementation does not trust filename extension, source kind or caller-declared MIME. Exactly one successful parser relation is required.

The executed GitHub runtime canary proved the no-predeclared-MIME path through PostgreSQL, the private byte vault and the existing authority-enforced source attachment runtime.

## CW-HASH-001 — PASS

Invoice Card V1 does not need to carry an expected binary SHA-256.

The executed runtime canary proved:

```text
no upstream binary hash
-> bounded byte validation
-> locally calculated SHA-256 becomes backend custody evidence
-> durable upstream hash expectation remains null
-> confirmed Card document/content hash remains unchanged
-> equal-byte replay is idempotent
-> conflicting bytes are rejected
-> interrupted publication is recoverable
```

The locally calculated hash is not written back into the confirmed Card.

## Lifecycle split remains intentional

```text
Cabinet_web.invoice_attach_source
  draft Card source-metadata mutation

local box invoice.source.attach
  durable source-byte attachment to accepted confirmed Card revision
```

Synchronization connects these operations. They are not one lifecycle operation and should not be collapsed.

## Executed interop evidence

GitHub Actions run:

```text
workflow: Cabinet Web attach canary
run_id: 32507028221
run_number: 2
head_sha: ca542b9b3dd60112f8cdd20c532f8a6f02c17d64
conclusion: success
```

Artifact:

```text
artifact_id: 9455627318
digest: sha256:1f7bcc1cabd2e8d4f58cb8310b915fc47944385d6f53d20d27e81a726b11c33e
```

All four runtime probes passed:

```text
WEB-ATTACH-001 PASS  parser MIME + local hash + immutable Card
WEB-ATTACH-002 PASS  replay + conflicting-byte rejection
WEB-ATTACH-003 PASS  interrupted publication + recovery
WEB-ATTACH-004 PASS  malformed bytes fail before publication
```

This is contract/runtime evidence using a controlled Card test vector. It is not a claim that real Cabinet_web user data has already entered the box.

## Current real-data gate

```text
isolated box runtime                 PASS
Cabinet_web source identity          PASS
Cabinet_web sync contract            PASS
parser-backed media lowering         PASS
no-expected-hash runtime             PASS
Cabinet_web interoperability         PASS
real Cabinet_web user-data canary    ALLOWED, NOT EXECUTED
```

Current `Cabinet_web/main` inventory under `data/cards` contains only:

```text
client-uliana-kolpacheva-20260815
project-uliana-floor-20260815
provider-andrey-bam-20260801
provider-santo-grua-20260815
```

There is no accepted Invoice Card candidate, so a real-data invoice canary must not be fabricated from tests or synthetic data.

## Next action

When one real confirmed Invoice Card and its corresponding source bytes are available in the Cabinet_web workflow:

1. pin the exact Cabinet_web `main` commit;
2. pin the confirmed Card canonical content hash and Git commit identity;
3. bind its exact `source_id` to the corresponding bytes;
4. deliver the Card through sync v1;
5. attach the bytes through the verified Cabinet_web source adapter;
6. record the backend receipt, parser media evidence and local SHA-256;
7. prove the confirmed Card bytes/content hash stayed unchanged.

The absence of a current real invoice candidate is a data-readiness condition, not a reason to redesign the interoperability contract.
