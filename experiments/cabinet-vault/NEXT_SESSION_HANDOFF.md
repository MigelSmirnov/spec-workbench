# Cabinet Vault — next session handoff

## Direction

Cabinet is being tested as a self-described local data/authority box compiled into a generic host, not as a permanently product-specific backend application.

```text
Cabinet_web working Card facts
        ↓ accepted synchronization contract
Cabinet durable local box meaning
        ↓
verified generic host providers
        ↓
verified capability-specific lowerings
        ↓
local durable archive / effects / audit
```

Deterministic host/runtime code may implement declared rules only. It must not choose missing product meaning or hide a missing lowering behind glue code.

## Isolated box milestone reached

Real Termux execution on 2026-08-21 proves:

```text
generic host structural lowering       PASS
all five required generic providers    PASS
bounded content-validation lowering    PASS
invoice.source.attach readiness        PASS
attach_expected_missing_source runtime PASS
post-promotion focused guards          21 passed in 1.02s
git diff --check                       PASS
```

Verified generic providers:

```text
authority_kernel
 typed_schema_kernel
postgres_record_kernel
local_private_byte_vault
protected_configuration_kernel
```

The real protected attach case proved exact authority, expected-source binding,
bounded content validation, PostgreSQL locking/transactions, private byte staging,
atomic publication, replay, conflict rejection, crash recovery and append-only
audit without raw storage/config/credential disclosure.

Evidence:

```text
experiments/cabinet-vault/INVOICE_SOURCE_ATTACH_RUNTIME_EVIDENCE.md
```

Its verified scope remains deliberately narrow:

```text
exactly one file
explicit invoice_id
explicit existing expected_source_id
already-accepted invoice
already-declared expected source
```

It does not prove multi-file orchestration, source-ID generation, invoice-number
search, non-accepted invoice attachment or transport exposure.

## Cabinet_web is now the integration target

Reviewed repository:

```text
MigelSmirnov/Cabinet_web
main @ 63f1752dc09be93156c6e7bf45f3c80e6c7f8387
```

Machine audit:

```text
experiments/cabinet-vault/cabinet_web_interop_audit_v0.yaml
```

Human-readable audit:

```text
experiments/cabinet-vault/CABINET_WEB_COMPATIBILITY_AUDIT.md
```

Guard:

```text
tests/test_cabinet_web_interop_contract.py
```

Current result:

```text
isolated_box_runtime_evidence: PASS
cabinet_web_interop_gate: block
real_cabinet_web_canary: forbidden_until_blockers_closed
```

## Responsibility boundary already aligns

`Cabinet_web` explicitly owns Invoice Card facts, deterministic Invoice operations
and GitHub Card history. It explicitly does not own the future local archive,
database or integration orchestration assigned to Cabinet_backend.

The local box therefore owns local durable replicas, source bytes, effect
authority, publication recovery and operational audit. It must not rewrite
confirmed Card facts or force Cabinet_web domain modules to depend on backend
runtime/database structures.

The existing `Cabinet_web.invoice_attach_source` and the verified local
`invoice.source.attach` are not the same lifecycle operation:

```text
Cabinet_web.invoice_attach_source
  draft Card source-metadata mutation

local box invoice.source.attach
  durable source-byte attachment to accepted confirmed Card revision
```

Synchronization should connect them rather than collapsing them into one method.

## Blocking interop findings

### CW-SOURCE-ID-001 — upstream Card-contract drift

`docs/01-storage/INVOICE_CARD_FORMAT.md` shows `source.source_id = source-001` and
payment evidence references that identity. But the executable V1 schema,
deterministic validator, source mutation service, fixture and tests define the
source object without `source_id`; additional source fields are rejected.

The backend must not generate or infer this identity. The earliest owner is
`Cabinet_web/card-contracts`.

### CW-SYNC-001 — accepted synchronization relation missing

Cabinet_web architecture lists remote synchronization as an extension point after
an accepted integration decision. The workflow describes local synchronization,
but no machine contract yet defines:

```text
exact confirmed Card revision
canonical content hash
source Git commit identity
expected source set
idempotency identity
local acceptance receipt
revision/retry reconciliation
```

### CW-MEDIA-001 — exact media lowering missing

Cabinet_web source facts use `photo | pdf | message | scan | other`. The verified
local content validator consumes exact `image/jpeg | image/png | application/pdf`.
`photo` cannot be silently lowered to JPEG, and filename extension is not proof.

### CW-HASH-001 — no-expected-hash interop evidence missing

Invoice Card V1 currently carries no expected binary SHA-256. Backend semantics
allow a locally calculated hash to become storage evidence without rewriting the
confirmed Card, but this exact Cabinet_web no-expected-hash path still requires
explicit synchronization binding and executed evidence.

## Immediate next decision

The next decision belongs to the Cabinet_web Card-contract owner, not to backend
adapter code:

```text
Is source_id a stable identity of the Invoice Card source in Cabinet_web V1?
```

There is already strong evidence for `yes` in the accepted storage document and
payment `source_ref`, but the executable contract currently contradicts that
document. Do not silently choose or implement the answer in the backend.

After that decision is explicit:

1. repair the earliest Cabinet_web Card contract consistently (schema → validator
   → fixtures → evidence tool/tests) if required;
2. define the versioned Cabinet_web → local-box synchronization package and receipt;
3. close exact media-type lowering without filename/kind guessing;
4. execute the no-expected-hash source attachment path;
5. only then run a real Cabinet_web invoice canary through the box.

## Other open semantic work remains separate

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit conversion evidence
```

Do not close these through integration glue.
