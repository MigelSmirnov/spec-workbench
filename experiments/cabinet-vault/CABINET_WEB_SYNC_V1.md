# Cabinet Web ↔ local box synchronization v1

## Status

Experimental transport-independent boundary contract for two autonomous applications.

Machine contract:

```text
experiments/cabinet-vault/cabinet_web_sync_contract_v1.yaml
```

`Cabinet_web` is not a frontend of `cabinet_backend`, and `cabinet_backend` is not continuously required infrastructure for `Cabinet_web`.

## Ownership

```text
Cabinet_web
  owns Invoice Card facts, Card revisions, source identity and Git history

        ⇅ occasional synchronization

cabinet_backend local box
  owns durable local replicas, protected source bytes,
  local effects, processing evidence and operational audit
```

The backend never rewrites a confirmed Web Card. Web never imports backend database, vault or runtime models into its domain.

## Accepted source identity

The upstream source-identity decision is now accepted in:

```text
MigelSmirnov/Cabinet_web
main @ d4419e3b948d49bd85a99a0941a350a73494cd27
PR #16
```

Invoice Card V1 requires `source.source_id`. It is stable within the owning Card, survives source-storage metadata changes, and `invoice_source` payment evidence must reference it. The backend may reference this identity but may not invent or replace it.

This closes `CW-SOURCE-ID-001`.

## Unit of synchronization

Web delivers one exact **confirmed Invoice Card revision**.

Revision identity is:

```text
invoice_id + card_content_hash
```

Git provenance travels separately as:

```text
source_git_commit_sha
card_repository_path
```

The complete Card document travels with the delivery. `card_content_hash` reuses the existing Cabinet Web canonical hash from `tools.invoice_service.content_hash`; the backend recomputes it before accepting the revision.

Git commit identity proves origin context but is not a substitute for the exact Card document or its canonical hash.

## Delivery and reconciliation

`delivery_id` identifies a retryable delivery attempt; it is not the Card revision identity.

Rules:

1. same delivery ID + same revision → `already_accepted`;
2. same delivery ID + different revision → `delivery_identity_conflict`;
3. first delivery requires `base_backend_content_hash = null`;
4. a later delivery states the backend revision Web believes is current;
5. stale base → `reconciliation_required`, without overwrite;
6. a newly accepted revision never deletes an older immutable replica;
7. arrival order never defines Git revision ancestry.

These rules are required because synchronization may be delayed or intermittent.

## Acceptance is not source-byte attachment

```text
accept_cabinet_web_invoice_revision
```

accepts the immutable confirmed Card revision.

```text
invoice.source.attach
```

is a separate local-box effect that attaches verified bytes to an already accepted Card/source identity.

A successful Card receipt therefore never claims that source bytes were stored.

## Receipt

The backend returns bounded synchronization metadata:

```text
delivery_id
invoice_id
card_content_hash
source_git_commit_sha
outcome
accepted_at
backend_current_content_hash
bounded error_code
```

It does not disclose backend database IDs, filesystem/vault paths, credentials or raw audit storage. The receipt is not written into the immutable confirmed Card.

## Transport independence

The same semantic contract may later use local IPC, HTTP, MCP, file exchange or an agent-mediated transport. Transport wrappers remain thin and may not:

- construct or rewrite Card facts;
- choose source identity;
- guess MIME from `source.kind` or filename;
- resolve revision conflict by last-write-wins;
- expose backend storage/runtime structure as Web domain state.

This closes the design absence `CW-SYNC-001` without selecting a transport.

## Remaining canary blockers

A real Cabinet Web → local box canary is still forbidden until both remaining proofs close:

1. `CW-MEDIA-001` — exact parser-backed media identity for source bytes;
2. `CW-HASH-001` — executed no-expected-hash source attachment bound to an accepted synchronized Card revision, while proving the confirmed Card remains unchanged.

No adapter may manufacture either proof.
