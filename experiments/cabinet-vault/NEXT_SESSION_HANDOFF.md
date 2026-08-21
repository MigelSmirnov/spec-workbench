# Cabinet Vault — next session handoff

## Direction

`Cabinet_web` and the Cabinet local box are autonomous state owners connected by a versioned synchronization protocol. `Cabinet_web` owns confirmed Card facts and Git history. The local box owns durable replicas, protected source bytes, local effects, recovery and audit.

Neither application is a permanent runtime dependency of the other.

## Interoperability milestone — REAL DATA PASS

The first real Cabinet_web user-data canary completed successfully on 2026-08-21.

Canonical Web input:

```text
Cabinet_web main: d3fac8e5d2b85c12904cba24060717b84e2757c2
invoice_id: invoice-f260001
source_id: source-f260001
Card hash: sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf
source_git_commit_sha: 386134cbb28e3689fec8ffb49815db9416ebe9a8
```

Real source evidence:

```text
local PDF SHA-256: sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66
parser media type: application/pdf
```

Execution result:

```text
invoice.archive.accept_revision: accepted
backend current Card hash: exact Web hash
invoice.source.attach: attached
Card unchanged: true
acceptance audit: present
attachment audit: present
```

Primary evidence:

```text
experiments/cabinet-vault/F260001_REAL_DATA_CANARY_PASS_EVIDENCE_2026-08-21.md
experiments/cabinet-vault/cabinet_web_real_data_canary_readiness_v1.yaml
experiments/cabinet-vault/cabinet_web_interop_audit_v0.yaml
```

## Trusted local bridge — PASS

Implementation:

```text
spec-workbench commit: bc872b605c3e4b3774749cdf1711eeeb35399eaf
tools/local_capability_bridge.py
tools/f260001_real_canary_via_bridge.py
transport: local_cli_stdio
```

The bridge exposes only:

```text
health/readiness
invoice.archive.accept_revision
invoice.source.attach
```

Authority boundaries remain exact:

```text
revision acceptance -> synchronization credential class
source attachment    -> local_agent credential class
resource scope       -> invoice:invoice-f260001
```

Protected configuration, PostgreSQL identity, vault paths, credentials and storage references remain host-owned and absent from safe outputs.

GitHub runtime evidence:

```text
workflow run: 32529515458
head: bc872b605c3e4b3774749cdf1711eeeb35399eaf
conclusion: success
artifact: 9463368772
artifact digest: sha256:6f81d77d2e5747d19608bf438f9551f333cc309f0feebbc95d30d95f064dfdb2
```

## Interoperability gate

```text
isolated box runtime              PASS
source identity contract          PASS
sync contract                     PASS
sync acceptance runtime           PASS
same-invoice technical E2E        PASS
media lowering                    PASS
no-expected-hash attachment       PASS
trusted local bridge              PASS
real Cabinet_web user-data canary PASS
real_user_data_canary_executed    true
```

There is no remaining blocker for the F260001 interoperability path.

## Full-suite note

A broader local run reported `605 passed, 6 failed`. The six failures are reported as pre-existing stale count assertions in State 5/6/assembly and are unrelated to the bridge/interop slice. Do not relabel them PASS; track them separately.

## Recommended next product-data repair

Now that `invoice-f260001` is the canonical Invoice Card and the real Web → local-box path is proven, repair the remaining duplicate ownership in Client/Project Cards.

Current legacy projections still duplicate invoice/source facts in:

```text
data/cards/client-uliana-kolpacheva-20260815/card.json
data/cards/project-uliana-floor-20260815/card.json
```

Next accepted design should define explicit relationship/derived-projection semantics before deleting data. The target direction is:

```text
Invoice Card owns canonical invoice facts.
Client/Project Cards keep stable links/projections only.
source-f260001 remains source identity owned by Invoice Card.
project/client consumers read canonical Invoice Card for invoice details.
```

Do not perform a destructive cleanup until the relationship/projection contract and affected readers are identified and tested.

## Bridge generalization remains separate

The trusted bridge is intentionally scoped to `invoice-f260001`. Generalizing it to arbitrary invoices requires a separate authority/grant provisioning design. Do not replace the exact-scope proof with wildcard invoice authority merely for convenience.

## Other open semantic work remains separate

```text
AUTH-OQ-001  smallest generic grant representation across independent boxes
AUTH-OQ-002  generic audit-event vocabulary vs Cabinet-specific event meaning
PA-MONEY-001  authoritative planned item amount + exact basis
PA-MONEY-002  actual comparison: net_amount or gross_amount
PA-MONEY-003  direct comparability or explicit conversion evidence
```
