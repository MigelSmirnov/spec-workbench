# Local agent handoff — first real Cabinet_web → local box canary

## Goal

Execute the first **real user-data** canary using one normal confirmed Invoice Card from `Cabinet_web/main` and the corresponding original source bytes.

The protocol and runtime are already defined. Do not redesign them during this task.

```text
Cabinet_web clean confirmed Card revision
  -> build cabinet-web-sync-v1 delivery
  -> invoice.archive.accept_revision
  -> cabinet-backend-sync-receipt-v1
  -> invoice.source.attach
  -> local source custody evidence
```

## Repositories

Update both repositories before doing anything else.

```text
MigelSmirnov/Cabinet_web
branch: main

MigelSmirnov/spec-workbench
branch: agent/cabinet-vault-experiment
```

Use normal fast-forward update. Do not run the canary from an old feature branch.

## Preflight gate

The canary may start only when all of the following are true:

- `Cabinet_web` checkout is on `main`;
- the target `data/cards/<invoice-id>/card.json` is tracked and has no uncommitted changes;
- Card `status` is `confirmed`;
- Card has `source.source_id`;
- the real original source bytes corresponding to that source identity are locally accessible;
- `verify_reviewed_contract()` from `tools/cabinet_web_checkout_sync_adapter.py` succeeds;
- the local agent has an authorized connection to the running Cabinet local box for the exact invoice target.

Stop if any condition fails. Do not repair contract drift inside an adapter.

## Candidate selection

Use a real Invoice Card produced through the normal Cabinet_web workflow and accepted into `main`.

Do **not** use:

- test fixtures;
- synthetic Cards;
- draft Cards;
- old branch-only invoices;
- an uncommitted Card;
- bytes whose relation to `source.source_id` is uncertain.

If `Cabinet_web/main` still contains no eligible invoice, create/capture one through the normal Web workflow first. The canary itself must not manufacture the invoice.

## Build the exact delivery

Use the checked-in adapter rather than reconstructing the package by hand:

```python
from uuid import uuid4
from tools.cabinet_web_checkout_sync_adapter import build_delivery_from_checkout

delivery = build_delivery_from_checkout(
    cabinet_web_root="/path/to/Cabinet_web",
    invoice_id="invoice-...",
    delivery_id=f"real-canary-{uuid4().hex}",
    base_backend_content_hash=None,  # first local revision only
)
```

The adapter:

- verifies the pinned Cabinet_web validator/schema/hash fingerprints;
- invokes Cabinet_web's deterministic Invoice validator;
- requires a clean tracked Card on `main`;
- calculates the exact canonical Card content hash;
- finds the Git commit that contains the Card revision;
- builds `cabinet-web-sync-v1` without inventing source MIME or binary hash.

Do not modify the returned `card_document` before delivery.

## Accept the revision in the local box

Send the delivery through the agent's existing authorized backend connection to:

```text
capability: invoice.archive.accept_revision
```

Do not bypass the capability by writing PostgreSQL records directly.

Expected receipt contract:

```text
cabinet-backend-sync-receipt-v1
```

Acceptable first-run outcomes:

```text
accepted
already_accepted
```

If the result is:

```text
reconciliation_required
```

read the returned `backend_current_content_hash`, inspect the current backend revision, and reconcile explicitly. Do not resubmit with a guessed base and do not use last-write-wins.

If the result is `rejected_card`, `rejected_contract`, or `delivery_identity_conflict`, stop and preserve the safe receipt/error evidence.

## Attach the real source bytes

After revision acceptance, use the exact Card-owned source identity:

```text
source_id = card.source.source_id
```

Invoke the verified source attachment path for the same invoice state. Use `CabinetWebSourceAttachAdapter` or the host capability wired to the same semantics.

Input authority:

```text
invoice_id     = exact accepted Card id
source_id      = exact Card source.source_id
content bytes  = real original bytes
filename       = metadata only
```

Do not use `source.kind`, filename extension, or caller MIME as media proof. Do not manufacture an expected SHA-256 when Cabinet_web did not provide one.

The parser-derived media type and calculated SHA-256 are local-box evidence only.

## Verification after attachment

Verify all of the following before calling the canary successful:

1. the receipt identifies the exact `invoice_id` and `card_content_hash` sent by Web;
2. the immutable accepted Card revision still equals the exact Web Card document;
3. its canonical Card content hash is unchanged after source attachment;
4. the same `source_id` is now available in local source status;
5. the stored local source SHA-256 equals SHA-256 of the supplied bytes;
6. the stored media type comes from parser validation;
7. upstream expected binary hash remains null when Web had none;
8. upstream expected exact media type remains null when Web had none;
9. acceptance and source-attachment audit events both exist;
10. no credential, database identity, filesystem/vault path, or raw source bytes appear in the public receipt/evidence summary.

## Evidence to report back

Return a compact safe report containing:

```text
Cabinet_web main commit
invoice_id
card_content_hash
source_git_commit_sha
delivery_id
revision receipt outcome
backend_current_content_hash
source_id
local calculated source SHA-256
parser-validated media type
source attachment result
Card unchanged: true/false
audit acceptance present: true/false
audit attachment present: true/false
```

Do not report credential material, PostgreSQL DSN, vault root/path, storage references, or raw invoice/source contents.

## Existing proof to trust

Machine contracts and executed evidence:

```text
experiments/cabinet-vault/cabinet_web_sync_contract_v1.yaml
experiments/cabinet-vault/cabinet_web_sync_box_extension_v1.yaml
experiments/cabinet-vault/CABINET_WEB_SYNC_RUNTIME_EVIDENCE.md
experiments/cabinet-vault/CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md
experiments/cabinet-vault/cabinet_web_real_data_canary_readiness_v1.yaml
```

The current synthetic/runtime evidence already proves idempotency, revision reconciliation, immutable revision retention, parser-backed media identification, no-expected-hash attachment, conflict rejection, crash recovery, and one same-invoice acceptance-to-attachment path. The local agent's job is now to substitute one eligible **real** Web revision/source pair, not to rewrite those mechanisms.
