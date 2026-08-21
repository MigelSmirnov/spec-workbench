# Local agent task — execute first real F260001 Cabinet_web → local box canary

## Goal

Execute the first real user-data canary for the canonical confirmed Invoice Card `invoice-f260001` and its original PDF through the already verified synchronization and source-attachment runtime.

Do not redesign the protocol and do not migrate legacy Client/Project projections during this task.

## Update repositories

Update both working copies first:

```text
MigelSmirnov/Cabinet_web
branch: main
expected main commit: d3fac8e5d2b85c12904cba24060717b84e2757c2 or a strict descendant with unchanged reviewed Invoice contract fingerprints

MigelSmirnov/spec-workbench
branch: agent/cabinet-vault-experiment
```

## Exact target

```text
invoice_id: invoice-f260001
Card path: data/cards/invoice-f260001/card.json
status: confirmed
source_id: source-f260001
source kind: pdf
expected Card content hash:
sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf
```

The original PDF reported by the local workflow is:

```text
/home/smirnov/Загрузки/F260001 Uliana Kolpacheva.pdf
```

Treat that path only as local input. Do not expose it in public receipt/audit output and do not write it into the confirmed Card.

## Preflight

Before any backend effect:

1. Require `Cabinet_web` to be on `main`.
2. Require `data/cards/invoice-f260001/card.json` to be tracked and clean.
3. Run `verify_reviewed_contract()` from `tools/cabinet_web_checkout_sync_adapter.py`.
4. Validate the exact Card with the current Cabinet_web Invoice validator.
5. Recompute the canonical Card hash and require exact equality with the pinned hash above. If it differs, stop and report contract/Card drift.
6. Require `source.source_id == source-f260001`.
7. Require the real PDF bytes to be readable locally.
8. Confirm the agent has authorized access to the running Cabinet local box for the exact invoice target.
9. Inspect whether the backend already has a current revision for `invoice-f260001`; do not assume first revision if state already exists.

## Build delivery

Use the existing adapter, not a hand-built payload:

```python
from uuid import uuid4
from tools.cabinet_web_checkout_sync_adapter import build_delivery_from_checkout

delivery = build_delivery_from_checkout(
    cabinet_web_root="/path/to/Cabinet_web",
    invoice_id="invoice-f260001",
    delivery_id=f"real-f260001-{uuid4().hex}",
    base_backend_content_hash=None,  # only if backend has no current revision
)
```

If backend already has a current revision, use its exact current content hash as the base only after explicit reconciliation. Never guess the base and never use last-write-wins.

## Accept exact Card revision

Invoke through the existing authorized backend connection:

```text
capability: invoice.archive.accept_revision
```

Do not write PostgreSQL records directly.

Expected receipt:

```text
contract: cabinet-backend-sync-receipt-v1
invoice_id: invoice-f260001
card_content_hash: sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf
outcome: accepted | already_accepted
```

If the outcome is `reconciliation_required`, stop normal execution, retain the receipt and reconcile explicitly. If rejected, stop and preserve the safe error evidence.

## Attach the real PDF

Only after accepted/already_accepted revision state, attach the real original PDF to the same invoice using the verified source-attachment path:

```text
invoice_id = invoice-f260001
source_id = source-f260001
content = exact bytes of F260001 Uliana Kolpacheva.pdf
filename = metadata only
caller MIME = not authority
expected upstream binary SHA-256 = absent
```

Use `CabinetWebSourceAttachAdapter` or the host capability wired to the same semantics. Do not write the vault or database directly.

The local box must parser-detect `application/pdf` and calculate the source SHA-256 itself. Those values remain local-box evidence; do not write them into the confirmed Web Card.

## Required verification

Before declaring PASS, prove all of the following:

1. receipt invoice ID is `invoice-f260001`;
2. receipt Card hash equals the pinned Card hash;
3. accepted canonical Card document equals the exact Web Card document;
4. accepted Card hash remains unchanged after source attachment;
5. `source-f260001` becomes available in local source state;
6. parser-validated media type is `application/pdf`;
7. local calculated source SHA-256 equals SHA-256 of the supplied PDF bytes;
8. durable upstream expected binary hash remains null;
9. durable upstream exact media expectation remains null unless explicitly present in the Card contract;
10. revision-acceptance audit evidence exists;
11. source-attachment audit evidence exists;
12. no credential, DSN, vault path, storage reference, raw PDF bytes or private filesystem path appears in the public receipt/report.

## Do not change during this task

Do not migrate or delete legacy invoice projections from:

```text
data/cards/client-uliana-kolpacheva-20260815/card.json
data/cards/project-uliana-floor-20260815/card.json
```

They are a separate relationship/derived-projection migration. For this canary, the dedicated `Invoice Card V1` is the canonical Web authority.

## Safe report to return

Return only:

```text
Cabinet_web main commit
spec-workbench commit
invoice_id
Card repository path
Card content hash
source_git_commit_sha
delivery_id
revision receipt outcome
backend_current_content_hash
source_id
local calculated source SHA-256
parser-validated media type
source attachment result
Card unchanged: true/false
acceptance audit present: true/false
attachment audit present: true/false
```

Do not return credential material, PostgreSQL DSN, vault/storage paths or raw invoice/PDF contents.