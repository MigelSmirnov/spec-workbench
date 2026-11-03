# Client Portal Open Product Questions

## Status

**Open; no decision is made by this requirements baseline**

1. What is the complete lifecycle of an approved presupuesto, including the
   point of immutability, replacement, withdrawal, and retention?
2. What is the detailed relationship between an approved presupuesto and a
   factura, given that approval and invoice creation are distinct facts?
3. Which actor or external system is authorized to publish an approved
   presupuesto to Client Portal?
4. How are approved snapshots versioned, selected, superseded, retained, and
   addressed?
5. How does a project move from a manual portal budget to an imported approved
   snapshot without losing history or misrepresenting existing data?
6. Who has authority to approve a presupuesto for client publication, and what
   future approval workflow supplies that decision?
7. Does Client Portal need a separate client-access close or revoke action in
   addition to Registry archival?
8. How are changes in a later approved presupuesto reflected when the portal
   already contains Expenses, allocations, progress, and payments?
9. How are internal PresuPro zones mapped to stable client-facing Budget
   Sections?

## Operational questions discovered after the baseline

### Q10 — Recovery after one-time service credential delivery is lost

Observed on 2026-11-04 while onboarding the PresuPro estimate producer for
`Proyecto Demo Facebook`:

- creating a service principal succeeds independently of credential issuance;
- credential issuance persists an active credential and returns its plaintext
  exactly once;
- the administrative HTTP surface exposes create, issue, revoke, grant and
  status-change operations, but no operation to list or read service
  principals and their non-secret credential metadata;
- if the response is lost, or the operator fails after issuance but before
  durably recording `principal_id` and `credential_id`, the plaintext is
  correctly unrecoverable, yet the administrator also cannot address the
  unknown active credential through the supported HTTP API to revoke it.

Questions requiring an explicit product/security decision:

1. Must the administrative API expose a list/read projection for service
   principals, credential metadata, and producer grants so an administrator
   can locate and revoke an orphaned credential?
2. Should credential issuance require an operator-supplied idempotency key or
   a prepare/confirm protocol, or is recovery by listing metadata and rotating
   credentials sufficient?
3. Must the one-time-secret response contract be shared by operator tooling so
   a response-shape mismatch cannot silently strand an active credential?
4. What recovery procedure and audit evidence are required when principal
   creation and credential issuance succeed but local secret custody fails?

Until this is decided, an operator must not blindly repeat principal or
credential creation after an ambiguous or lost response. The incident must be
reconciled and the orphaned credential revoked through an authorized
administrative recovery procedure first.
