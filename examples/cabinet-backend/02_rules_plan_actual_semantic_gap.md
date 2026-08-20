# State 2 decision — plan/actual calculation semantics

## Status

**REOPENED — quantity semantics remain accepted; monetary semantics are unresolved.**

The earlier version of this decision treated `EstimateItemSnapshot.total` and
`InvoiceLine.total` as accepted monetary source facts. Later factual probes proved
that those aliases are not semantically closed:

- no single authoritative PresuPro item total has been established for the
  planned side;
- Invoice Card V1 has no `InvoiceLine.total` field and instead exposes distinct
  canonical `net_amount` and `gross_amount` meanings.

The monetary part of the earlier accepted decision is therefore withdrawn until
the owning Cabinet business semantics are explicitly accepted. This is a repair
of the earliest owning decision, not an adapter or compiler change.

See `01_models_plan_actual_monetary_gap.md` for the corresponding State 1
refinement.

## Preserved accepted analysis grain

The baseline analysis remains organized by exact `EstimateItemSnapshot` identity,
with explicit project-level aggregation and a separate unmatched-actual set.

One estimate item may aggregate several confirmed invoice lines. One invoice line
may contribute to at most one active confirmed estimate-item match. Splitting one
invoice line across several estimate items remains unsupported.

Only confirmed `InvoiceLineEstimateMatch` decisions may contribute as matches.
Similarity evidence alone is never analytical truth.

## Preserved quantity semantics

For each analysed Estimate Item:

```text
planned_quantity = EstimateItemSnapshot.quantity
```

For every confirmed Invoice Line matched to the Estimate Item:

```text
actual_quantity = sum(matched InvoiceLine.quantity)
```

For comparable quantities:

```text
quantity_variance = actual_quantity - planned_quantity
remaining_quantity = planned_quantity - actual_quantity
```

`remaining_quantity` is not clamped to zero. A negative result preserves the
amount by which actual quantity exceeded planned quantity.

Quantity comparison is allowed only when the Estimate Item unit and every
contributing Invoice Line unit are semantically identical under the accepted unit
vocabulary, or when the request pins explicit already accepted deterministic
conversion evidence.

Without accepted conversion evidence, a different-unit comparison raises
`PlanActualPreconditionError`. No implicit unit conversion is accepted.

## Reopened monetary semantics

### Planned amount

The previous rule:

```text
planned_amount = EstimateItemSnapshot.total
```

is no longer accepted as a closed semantic rule.

State 1 does not currently identify one authoritative PresuPro item-level source
fact with both:

```text
estimate.item.planned_amount
estimate.item.planned_amount_basis
```

A Decimal field, aggregate estimate total, export value, frontend display value,
or Holded projection must not be selected merely because it is available.

### Actual amount

The previous rule:

```text
actual_amount = InvoiceLine.total
```

is invalid because Invoice Card V1 defines no such field.

The accepted Card contract exposes two different source truths:

```text
InvoiceLine.net_amount
  basis = post_discount_tax_exclusive

InvoiceLine.gross_amount
  basis = tax_inclusive
```

Cabinet plan/actual semantics must explicitly choose which of these meanings is
the actual comparison amount. Backend, compiler, host, adapter, and model code
must not choose on Cabinet's behalf.

### Currency

Currency remains a required comparability dimension. Source-contract evidence may
provide it deterministically, but equal currency does not prove equal monetary or
tax basis.

## Open monetary decisions

The following decisions must be accepted before baseline monetary analysis can be
called semantically closed.

### PA-MONEY-001 — authoritative planned item amount

Specify exactly:

- the authoritative source field or derived source-contract fact;
- semantic identity;
- monetary/tax basis;
- why Cabinet consumes that value rather than another PresuPro representation.

### PA-MONEY-002 — authoritative actual line amount

Choose exactly one accepted Invoice Card V1 meaning for plan/actual comparison:

```text
invoice.line.net_amount
or
invoice.line.gross_amount
```

and preserve its source-owned basis.

### PA-MONEY-003 — monetary comparability

Define the rule that proves the selected planned and actual values are directly
comparable.

If they are not directly comparable, define the explicit accepted assumption or
evidence that authorizes a deterministic conversion. No implicit currency,
net/gross, discount, or tax-basis conversion is accepted.

## Monetary fail-closed rule

Until PA-MONEY-001 through PA-MONEY-003 are accepted, an operation that requires
baseline monetary plan/actual outputs must not return a successful guessed result.

It must raise `PlanActualPreconditionError` or an equivalent explicit semantic-gap
result when the pinned evidence cannot prove the selected planned amount, actual
amount, currency, and compatible basis.

The following are forbidden repairs:

- reconstructing `InvoiceLine.total`;
- selecting `net_amount` or `gross_amount` by heuristic;
- using PresuPro aggregate `grand_total` as an item amount;
- selecting a source Decimal by type equality;
- inferring basis from field names, locale, currency, or integration context;
- hiding a conversion or choice in an adapter or generic lowering.

## Unmatched invoice lines

An accepted invoice line without a confirmed Estimate Item match remains
explicitly unmatched and must not create a placeholder Estimate Item.

The unmatched line identity set is deterministic and may be reported now.

`unmatched_actual_amount` and project monetary totals remain unavailable until the
same actual-amount and monetary-comparability decisions used for matched lines are
accepted. The system must not aggregate unmatched monetary values under an
invented alias.

## Successful result boundary

A quantity-only intermediate calculation may expose deterministic quantity facts
when the caller and contract explicitly request only those facts.

The baseline full `PlanActualAnalysis` previously required monetary planned,
actual, and variance values. That full result is currently **not semantically
closed** and must not be represented as verified until the monetary decisions are
accepted and derivability succeeds from the declared source contracts.

A provenance-only, warning-only, empty, or placeholder full analysis is not a
successful substitute.

## Reproducibility

For identical pinned invoice revisions, project identity/context,
`EstimateSnapshot`, confirmed match identities, and accepted assumption
identities, repeated deterministic quantity calculations must produce equal
semantic quantity fields and unmatched identity sets.

Once monetary semantics are accepted, monetary reproducibility must additionally
pin the exact selected monetary semantics, bases, and any accepted conversion
assumption identities.

Runtime timestamps, persistence IDs, cache metadata, or execution ordering are
not part of semantic equality unless separately accepted as domain evidence.

## Forecast boundary

Forecast values remain outside the required baseline. They may be included only
when the request pins separately accepted forecast assumptions. Absence of
forecast assumptions must not cause Cabinet Backend to invent a forecast.

## Preserved invariants

- only confirmed `InvoiceLineEstimateMatch` decisions may contribute as matches;
- similarity evidence alone never contributes as a match;
- one invoice line has at most one active confirmed Estimate Item match;
- one Estimate Item may aggregate many confirmed invoice lines;
- unmatched lines remain explicit and never create placeholder estimate items;
- EstimateSnapshots and accepted Invoice Card revisions remain immutable;
- matches remain pinned to their exact EstimateSnapshot;
- newer EstimateSnapshots do not inherit matches automatically;
- missing, stale, incompatible, unresolved, or incomparable pinned evidence fails
  closed rather than being guessed;
- PresuPro lineage is never inferred from project identity, content similarity,
  timestamps, or naming.

## Required tests

1. Two identical pinned quantity-only requests produce semantically equal quantity
   fields and unmatched identity sets.
2. Planned quantity comes from the exact Estimate Item quantity.
3. Two matched invoice lines for one Estimate Item are summed into that item's
   actual quantity.
4. `remaining_quantity = planned_quantity - actual_quantity` and remains negative
   when actual exceeds plan.
5. Different units without accepted conversion evidence raise
   `PlanActualPreconditionError`.
6. An explicit pinned unit-conversion assumption may enable a deterministic
   different-unit quantity comparison.
7. A request for full monetary analysis fails closed while PA-MONEY-001 through
   PA-MONEY-003 are unresolved.
8. Neither aggregate PresuPro totals nor type-compatible Decimal fields can close
   the planned item amount by themselves.
9. Neither Invoice Card V1 `net_amount` nor `gross_amount` is selected unless the
   accepted target semantic decision names it explicitly.
10. Currency equality without compatible monetary basis is insufficient.
11. Unmatched lines remain explicit and do not mutate any Estimate Item actual.
12. Source Invoice Card, EstimateSnapshot, Registry context, and confirmed match
   records remain unchanged by calculation.
13. No forecast is invented when no accepted forecast assumptions are pinned.

## Closure condition

This decision may return to **ACCEPTED** only after:

1. PA-MONEY-001, PA-MONEY-002, and PA-MONEY-003 are explicitly resolved in the
   owning Cabinet semantic design;
2. the selected meanings are propagated into source/target box manifests without
   changing the generic derivability rules;
3. the unchanged derivability compiler proves both planned and actual monetary
   mappings;
4. the required fail-closed and successful-path tests execute and pass.
