# Real Cabinet_web data canary preflight evidence — 2026-08-21

## Result

PASS — fail-closed preflight behaved correctly.

No real-data canary execution was attempted because the required real Invoice Card input does not exist in the reviewed `Cabinet_web/main` state.

## Local agent report

Observed at approximately `2026-08-21T22:01:00+02:00`.

```text
Cabinet_web/main:
  d4419e3b948d49bd85a99a0941a350a73494cd27

spec-workbench/agent/cabinet-vault-experiment:
  89b81a2488c809dd93556e97ec6d11508ffdbd66
```

The local agent refreshed both repositories and applied the checked-in real-data canary handoff.

Observed Cabinet_web inventory:

```text
tracked Invoice Cards under data/cards: 0
confirmed Invoice Cards: 0
eligible real Invoice Card + source-byte pairs: 0
```

The agent therefore stopped before any backend effect.

## Safe result

```text
invoice_id: null
card_content_hash: null
source_git_commit_sha: null
delivery_id: null
revision_receipt_outcome: not_run_no_eligible_invoice
backend_current_content_hash: null
source_id: null
local_calculated_source_sha256: null
parser_validated_media_type: null
source_attachment_result: not_run
card_unchanged: not_applicable
audit_acceptance_present: false
audit_attachment_present: false
```

No `invoice.archive.accept_revision` invocation occurred. No `invoice.source.attach` invocation occurred. No PostgreSQL or byte-vault mutation was performed by the canary.

## Forbidden substitutes were not used

The agent explicitly did not substitute:

- test fixtures;
- synthetic Invoice Cards;
- old feature-branch invoices;
- an unconfirmed Card;
- unrelated source bytes.

This is the required fail-closed behavior for `REAL-CANARY-DATA-001`.

## Unrelated working-tree state

The local `Cabinet_web/main` checkout contained an existing uncommitted modification to:

```text
tests/test_invoice_validation.py
```

It was preserved and did not affect `data/cards`. No target Invoice Card existed, so no Card cleanliness/provenance assertion was bypassed.

The next real-data attempt must still require the selected `data/cards/<invoice-id>/card.json` to be tracked and clean before deriving its Git provenance.

## Gate consequence

```text
interop/runtime readiness: PASS
local-agent preflight behavior: PASS
real user-data canary executed: false
remaining block: no eligible real Invoice Card + source-byte pair
```

Do not interpret this preflight PASS as a real user-data canary PASS. The next transition occurs only after a real confirmed Invoice Card is accepted into `Cabinet_web/main` and its corresponding original source bytes are locally available.
