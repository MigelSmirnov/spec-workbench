# State 1 repair — plan/actual runtime evidence

## Model M124 — ProposalReasonCode

`kind: enum`: `unit_match`, `currency_match`, `quantity_equal`, `unit_price_close`.

### Identity

value

### Identity evidence

The value is a closed classification without runtime identity; equal members are interchangeable.

---

## Model M74 — InvoiceLineMatchProposal

Immutable non-authoritative candidate with fields `proposal_id: str`,
`invoice_revision: InvoiceCardRevisionReference`, `invoice_line_id: str`,
`estimate_snapshot_id: str`, `estimate_item_id: str`, `score: Decimal`,
`reason_codes: tuple[ProposalReasonCode, ...]`, and `proposed_at: datetime`.

### Identity
value
### Identity evidence
Equal pinned source, candidate, score, reasons, and time facts are interchangeable.

A proposal never becomes a confirmed match without an explicit persisted
`InvoiceLineEstimateMatch` decision.

## Model M75 — UnmatchedPlanActualItems

Immutable read result with `project_id: str`, `estimate_snapshot_id: str`,
`unmatched_invoice_line_ids: tuple[str, ...]`,
`unmatched_estimate_item_ids: tuple[str, ...]`, and `observed_at: datetime`.

### Identity
value
### Identity evidence
Equal exact snapshot, unmatched identities, and observation time are interchangeable.

## Runtime interface

`PlanActualRepository` is the narrow PostgreSQL port for immutable snapshots,
proposals, match decisions, and deterministic reads. It owns no matching or
calculation policy.
