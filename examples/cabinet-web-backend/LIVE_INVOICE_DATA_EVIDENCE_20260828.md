# Live Cabinet invoice data: observed arithmetic contract

Observed: 2026-08-28. Source of truth: live repository `MigelSmirnov/Cabinet_web`,
snapshot clone `~/jestor_VBC/snapshots/Cabinet_web_live_20260828`, HEAD `af39ab6`,
11 confirmed invoice cards (`data/cards/invoice-*`), 109 lines total.
Measured against the deployed `cabinet_web_backend` tree of promote `215b375`
(factory OTK `20260828_171336`) in the stage-2 sandbox
(all 11 invoices seeded through `/plugin/v1/invoice-effects/create-draft`,
then validated through `/plugin/v1/invoices/validate`).

## Observed facts

1. `lines.*.tax_rate` is a **percent-shaped decimal** (`"21"`, `"10"`), never a
   fraction. The live validator (`tools/invoice_validation.py`, PERCENT_RE)
   admits only that shape.
2. All monetary amounts are printed cents. The live validator quantizes every
   arithmetic comparison with `ROUND_HALF_UP` to `0.01`.
3. `net_amount == round_half_up(quantity * unit_price_net - discount_amount, 2)`
   holds on **109/109** lines.
4. `gross_amount == net_amount + tax_amount` holds exactly on **109/109** lines.
5. Per-line tax is **not reconstructable from the rate**: even the correct
   percent formula `round_half_up(net_amount * tax_rate / 100, 2)` holds on only
   **45/109** lines (retail suppliers round per tax group, then back-fill line
   values). The live validator does not check per-line tax reconstruction at
   all. The prior spec formula `net_amount * tax_rate` (no /100, no rounding)
   held on 0/109 lines and made every real invoice unconfirmable
   (stage-2 finding 1, `docs/PLATFORM_EXPERIMENT_STAGE2_REPORT_20260828.md`
   in the factory repository).
6. Document totals `net`/`tax` differ from the line sums by up to **±0.06 €**
   on 7/11 invoices (opposite signs, group rounding); the live validator
   reports the difference as a warning only. `totals.gross == sum of line
   gross` holds exactly on **11/11** invoices.
7. `payment`: paid invoices carry applied transactions equal to
   `totals.payable`; `paid_total + outstanding_total == gross` held on all
   seeded cards.

## Contract consequences bound into the spec

- `invoice.line_net` keeps blocking, with explicit `round_half_up(..., 2)`.
- `invoice.line_gross` keeps blocking (exact cent addition).
- `invoice.total_gross` keeps blocking (exact on all observed data).
- `invoice.line_tax`, `invoice.total_net`, `invoice.total_tax` are removed
  from the blocking check set: no formula over the observed data supports
  them as validity criteria, and the live authority does not enforce them.
- `models.InvoiceCardLine.fields.tax_rate` stays `Decimal` and carries percent
  semantics (0–100), per fact 1.

Any future change to these addresses must re-verify against a fresh snapshot
of the live repository before export.
