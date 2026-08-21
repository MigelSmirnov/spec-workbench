# Cabinet Web ↔ local box synchronization v1

## Status

Experimental boundary contract for `agent/cabinet-web-sync-contract`, derived from the accepted `agent/cabinet-vault-experiment` direction.

Machine-readable contract:

```text
experiments/cabinet-vault/cabinet_web_sync_contract_v1.yaml
```

This document does not make Cabinet Web a frontend of Cabinet Backend and does not make Cabinet Backend continuously available infrastructure for Cabinet Web.

## Product topology

The two applications are autonomous.

```text
Cabinet_web
  owns working Card facts and Git history

        ⇅ occasional synchronization

cabinet_backend local box
  owns durable local replicas, protected source bytes,
  local effects, processing evidence and operational audit
```

Cabinet Web must remain usable when the local box is absent. The local box must not require Cabinet Web runtime classes, database structures or a live Web process in order to preserve accepted replicas.

## Unit of synchronization

The v1 Web → box unit is one exact **confirmed Invoice Card revision**.

It is identified by:

```text
invoice_id
+ card_content_hash
```

and accompanied by Git provenance:

```text
source_git_commit_sha
card_repository_path
```

`card_content_hash` is not a new integration hash. It is the existing Cabinet Web canonical revision hash from `tools.invoice_service.content_hash`:

```text
sha256(canonical_json(card_document))
```

where canonical JSON uses UTF-8, sorted keys and compact separators exactly as Cabinet Web already does.

The backend recomputes the hash. It does not trust a caller-supplied hash without the exact Card document.

## Why the complete Card travels

The local box must be able to preserve and validate the accepted revision without acquiring authority over the Cabinet Web repository or requiring a GitHub client as part of Cabinet semantics.

Therefore the delivery contains the exact Card document plus Git provenance. Git commit identity is evidence of origin; it is not a substitute for the Card bytes or canonical content hash.

The local box validates the received Card against the accepted Cabinet Web Invoice Card V1 contract before making a replica visible.

## Source identity

`source_id` belongs to Cabinet Web Card facts.

The upstream repair is currently in:

```text
MigelSmirnov/Cabinet_web
agent/source-id-contract-repair
PR #16
```

The local box may reference this identity but may not create, replace or infer it.

Changing source storage metadata or attaching protected bytes locally does not change the Web-owned source identity.

## Card acceptance is not byte attachment

These remain separate lifecycle operations:

```text
accept_cabinet_web_invoice_revision
```

accepts an immutable confirmed Card revision.

```text
invoice.source.attach
```

is a later local-box effect that attaches verified protected bytes to an already accepted revision/source identity.

A successful Card receipt therefore does **not** claim that source bytes are stored.

This separation leaves the existing media-type and no-expected-hash blockers visible rather than hiding them inside synchronization glue.

## Idempotency and reconciliation

Two identities are deliberately separate.

```text
delivery_id
```

identifies a delivery attempt and is reused for retries.

```text
(invoice_id, card_content_hash)
```

identifies the exact Card revision.

Rules:

1. same `delivery_id` + same revision → `already_accepted`;
2. same `delivery_id` + different revision → `delivery_identity_conflict`;
3. first accepted revision requires `base_backend_content_hash = null`;
4. later revision delivery states the backend revision Web believes is current;
5. if that base does not match the backend current revision, return `reconciliation_required` and do not overwrite anything;
6. accepting a new revision never deletes the previous immutable replica;
7. arrival order is not Git history and must not be interpreted as revision ancestry.

The last rule matters for occasional/offline synchronization: delayed packages cannot silently become authoritative merely because they arrived last.

## Receipt

The backend returns a bounded receipt containing the synchronization identity and outcome, not its internal persistence model.

Allowed information includes:

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

It must not expose database primary keys, filesystem/vault paths, credentials or raw audit storage.

The receipt is synchronization metadata. It is not written into the immutable confirmed Invoice Card.

## Transport independence

The same contract may later be carried over local IPC, HTTP, MCP, a file exchange, or an agent-mediated channel.

Transport adapters must not:

- construct or rewrite Card facts;
- choose source identity;
- guess MIME from `source.kind` or a filename;
- turn revision conflict into last-write-wins;
- move backend database/runtime concepts into Cabinet Web.

## Gate impact

This contract closes the **design absence** identified by `CW-SYNC-001`.

It does not yet permit a real Cabinet Web canary. Remaining prerequisites are:

1. upstream `source_id` repair accepted into Cabinet Web `main`;
2. exact parser-backed media-type relation for source bytes (`CW-MEDIA-001`);
3. executed no-expected-hash attachment evidence bound to this synchronization relation (`CW-HASH-001`).

No adapter may manufacture those missing proofs.
