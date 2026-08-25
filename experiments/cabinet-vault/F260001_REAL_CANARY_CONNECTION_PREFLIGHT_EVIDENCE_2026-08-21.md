# F260001 real-data canary connection preflight evidence — 2026-08-21

## Result

PASS — fail-closed preflight behaved correctly.

The real Cabinet_web Card and original PDF were ready, but the local agent had no authorized connection to a running Cabinet local-box host exposing the required protected capabilities. No backend effect was attempted.

## Pinned input

```text
Cabinet_web main commit:
  d3fac8e5d2b85c12904cba24060717b84e2757c2

spec-workbench commit used by the local agent:
  baccdcc66b4778183b0ca308efee17117c9d7300

invoice_id:
  invoice-f260001

Card path:
  data/cards/invoice-f260001/card.json

Card content hash:
  sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf

source_git_commit_sha:
  386134cbb28e3689fec8ffb49815db9416ebe9a8

source_id:
  source-f260001

local SHA-256 of the real PDF:
  sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66
```

The confirmed Web Card remained unchanged.

## Blocking condition observed

```text
revision_receipt_outcome:
  blocked_preflight_authorized_backend_connection_unavailable

delivery_id:
  not_created

backend_current_content_hash:
  not_inspected

parser_validated_media_type:
  not_executed

source_attachment_result:
  not_executed

acceptance_audit_present:
  false

attachment_audit_present:
  false
```

No `invoice.archive.accept_revision` invocation occurred. No `invoice.source.attach` invocation occurred. No direct PostgreSQL or vault operation was used as a substitute.

## Interpretation

This is not a data or Card-contract blocker. The real candidate is ready.

The verified execution code currently exists as protected executors:

```text
experiments/cabinet-vault/tools/cabinet_web_revision_accept_runtime.py
experiments/cabinet-vault/tools/invoice_source_attach_runtime.py
experiments/cabinet-vault/tools/cabinet_web_source_attach_adapter.py
```

These executors require `AuthorityKernel` authentication/authorization and exact resource scope. They are not currently exposed to the local agent by a running trusted local transport/host surface.

The older experimental `cabinet_host.py` and `cabinet_graph_host.py` are demo SQLite hosts for other capabilities and must not be used to bypass the verified local-box runtimes.

## Gate consequence

```text
Cabinet_web real candidate readiness: PASS
Card contract/validation: PASS
real PDF availability: PASS
protected executor runtime evidence: PASS
authorized local capability connection: BLOCK
real user-data canary executed: false
backend effects: none
```

The next transition is to provide a minimal trusted local host/bridge that exposes the existing protected executors without weakening their authority, scope, effect, disclosure, recovery, or audit rules.