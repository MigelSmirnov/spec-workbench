# State 2 — import admission reconciliation

## Accepted decision A77 — A20 governs import admission; A2 border rejection superseded (2026-09-03)

The product owner confirmed (2026-09-03) the runtime product shape: Cabinet Web
remains the main daily working surface; the local Backend is the durable archive
that downloads and preserves its data. No cross-boundary draft-editing workflow
is planned. Synchronization is therefore backup and archive transfer, exactly as
A20 B.1 records — not a business confirmation boundary.

### Normative rules

1. A20 sections B.1, D, and E govern import admission at
   `durable_archive.accept_transfer_manifest`. A2 rules 3–5 (border rejection of
   a `draft` revision with `card_not_confirmed`) are superseded.
2. A delivered `draft` revision is archived truthfully: the stored head and
   revision carry `observed_status = draft`; import never changes lifecycle
   status (A20 B.2.3).
3. The surviving A2 exclusions move to the eligibility gates: Holded publication
   refuses a revision whose `observed_status` is not `confirmed` with the
   deterministic reason `card_not_confirmed` (the A2 result name survives at the
   gate, not at the border), and confirmed actual totals continue to use only
   explicitly confirmed matching decisions (A41/A73).
4. A delivered card revision whose `card_version` is not the accepted Invoice
   Card V1 version is quarantined per A20 D.4/E.1: the receipt result is
   `quarantined` with `safe_error_code = quarantine_required`, and no archive
   head or revision is created or advanced. It is never silently parsed as V1.
5. An unsupported Cabinet Card type is structurally unrepresentable at the
   import boundary: the typed transfer package carries `InvoiceCardV1` only
   (A6's closed scope is enforced by the model contract, not by a runtime
   check).
6. Persisting `ImportQuarantine` evidence rows requires an `ArchiveUnitOfWork`
   surface addition that this decision does not make; until that separate
   surface decision, the classified quarantined receipt is the enforced
   obligation, and the VPS retains its authoritative working copy (A20 E.2.4).

### Formal invariants

```text
draft_revision -> archived_with_observed_status_draft
draft_revision -/> holded_eligible
unsupported_card_version -> quarantined_receipt AND no_archive_head_transition
non_v1_card_type -/> representable_at_import_boundary
```

### Required tests

1. A delivered `draft` revision is archived with truthful `draft` status.
   [witness: verification:witness_A77]
2. A `draft` revision with complete sources is refused Holded publication with
   reason `card_not_confirmed`.
3. A delivered revision with an unsupported `card_version` yields a
   `quarantined` receipt and creates no archive head.
4. A non-V1 canonical card cannot be represented in the typed transfer package.

### Consequence

The June-era border-rejection reading of A1/A2/A6 is reconciled with the
accepted runtime import design without any model change: `draft` archives
truthfully, exclusion is enforced where the business risk lives (publication
and analytics eligibility), and unsupported contracts quarantine instead of
silently degrading.
