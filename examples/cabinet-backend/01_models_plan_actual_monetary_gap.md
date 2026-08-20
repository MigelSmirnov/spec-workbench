# State 1 repair — plan/actual monetary semantics

## Status

**OPEN SEMANTIC GAP.**

This refinement records source-contract evidence discovered after the earlier
plan/actual decision was accepted. It does not choose a monetary meaning on
behalf of Cabinet, PresuPro, or Invoice Card V1.

The affected State 1 models keep their identity semantics. The repair concerns
the meaning of monetary facts consumed by `PlanActualAnalysis`.

## Affected models

- `M29 — EstimateItemSnapshot`;
- `M32 — PlanActualAnalysis`;
- the accepted Invoice Card V1 line projection consumed by analysis.

## Planned-side fact

The current `EstimateItemSnapshot` model describes estimate-item pricing fields
and totals, but State 1 does not prove one canonical per-item amount that is the
accepted plan/actual planned value.

Factual PresuPro reconnaissance established deterministic currency and aggregate
pricing behavior, but did not establish one authoritative item-total meaning
shared across backend aggregate logic, export, frontend display, and Holded
projection.

Therefore State 1 must not treat an undifferentiated field named `total` as
semantic proof of:

```text
estimate.item.planned_amount
estimate.item.planned_amount_basis
```

A future accepted planned amount must identify both the authoritative source fact
and its monetary/tax basis.

## Actual-side fact

Invoice Card V1 does not define `InvoiceLine.total`.

Its canonical closed line shape exposes two distinct authoritative monetary facts:

```text
net_amount
  basis = post_discount_tax_exclusive

gross_amount
  basis = tax_inclusive
```

Both are source truth. Neither is an alias for an abstract plan/actual
`actual_amount` until Cabinet explicitly chooses which meaning the analysis
consumes.

State 1 therefore must not introduce `InvoiceLine.total` as a compatibility alias
or silently map `actual_amount` to either canonical field.

## Model repair rule

`EstimateItemSnapshot` and the Invoice Card line projection may preserve source
monetary facts only with their source-owned meanings and bases.

`PlanActualAnalysis` may expose monetary planned/actual/variance values only when
an accepted plan/actual semantic decision pins:

1. one authoritative planned item amount semantic;
2. the planned amount basis;
3. one authoritative actual line amount semantic;
4. the actual amount basis;
5. a deterministic comparability rule or an explicit accepted assumption when
   direct comparison is not valid.

Currency equality alone does not establish monetary-basis compatibility.
Decimal type equality does not establish semantic compatibility.

## Open decisions

### PA-MONEY-001 — planned item amount

Which authoritative PresuPro item-level fact is the Cabinet planned amount, and
what exact monetary/tax basis does it represent?

No answer is accepted yet.

### PA-MONEY-002 — actual line amount

Does Cabinet compare plan against Invoice Card V1 `net_amount` or
`gross_amount`?

No answer is accepted yet.

### PA-MONEY-003 — comparability

What rule proves that the selected planned and actual amounts are directly
comparable? If they are not directly comparable, what explicit accepted
assumption/evidence authorizes a deterministic conversion?

No implicit net/gross, tax, or currency conversion is accepted.

## Consequence for M32 — PlanActualAnalysis

Quantity analysis may remain deterministic under the already accepted unit rules.
Monetary analysis is not semantically closed until PA-MONEY-001 through
PA-MONEY-003 are accepted.

A successful result must not fabricate monetary fields from ambiguous aliases.
If the baseline operation requires monetary outputs and the required semantic
decision is absent, calculation must fail closed rather than return a partial or
guessed monetary analysis.

## Stop conditions

Do not repair this gap by:

- renaming an arbitrary PresuPro Decimal field to `planned_amount`;
- mapping aggregate estimate `grand_total` to one item;
- recreating `InvoiceLine.total`;
- choosing Card `net_amount` or `gross_amount` by field-name preference;
- inferring monetary basis from type, currency, locale, or adapter context;
- adding a generic adapter conversion that is absent from accepted semantics.

The next accepted change must be a Cabinet plan/actual business decision, not a
compiler or lowering heuristic.
