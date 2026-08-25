# Plan/actual monetary derivability — result

## Status

Experimental result combining two factual source probes with the deterministic
box derivability detector.

Validated external evidence:

- PresuPro local monetary probe: focused `1 passed in 0.33s`, full pricing file
  `4 passed in 0.33s`, `git diff --check` PASS.
- Cabinet_web Invoice Card V1 monetary probe at source-of-truth commit `63f1752`:
  focused `1 passed in 0.18s`, validator suite `16 passed, 22 subtests passed in
  0.18s`, `git diff --check` PASS.
- Workbench refined suite before the Invoice Card V1 probe: `29 passed, 1 warning
  in 0.79s`; warning was only inability to write `.pytest_cache`.

The newest actual-side workbench detector still requires a fresh checkout run.

## Planned side

Accepted Cabinet plan/actual currently says:

```text
planned_amount = EstimateItemSnapshot.total
```

The factual PresuPro probe proved:

- product currency is the deterministic source-contract constant `EUR`;
- aggregate pricing arithmetic is deterministic;
- no single canonical source item total is shared by backend aggregate logic,
  export line total, frontend line display, and Holded projection.

Therefore:

```text
money.currency
  -> derivable

estimate.item.planned_amount
  -> unresolved

estimate.item.planned_amount_basis
  -> unresolved
```

The accepted `EstimateItemSnapshot.total` field currently lacks a proven source
meaning.

## Actual side

Accepted Cabinet plan/actual currently says:

```text
actual_amount = InvoiceLine.total
```

The real Invoice Card V1 contract proves that `InvoiceLine.total` does not exist.
The closed line shape instead contains distinct canonical monetary facts:

```text
net_amount
  = ROUND_HALF_UP(quantity * unit_price_net - discount_amount, 2)
  basis = post_discount_tax_exclusive

gross_amount
  = ROUND_HALF_UP(net_amount + tax_amount, 2)
  basis = tax_inclusive
```

All line monetary values bind to the containing invoice's required root
`invoice.currency`; there is no separate line currency.

Canonical Card JSON is source truth. The deterministic validator verifies
arithmetic but does not rewrite source monetary values.

The source contract therefore truthfully self-describes both alternatives:

```text
invoice.line.net_amount
invoice.line.net_amount_basis
invoice.line.gross_amount
invoice.line.gross_amount_basis
money.currency
```

It does **not** self-describe an abstract `invoice.line.actual_amount` because the
source contract does not own the plan/actual choice between net and gross.

Expected derivability:

```text
money.currency
  -> derived

invoice.line.actual_amount
  -> unresolved

invoice.line.actual_amount_basis
  -> unresolved
```

The test also proves that if the target semantic requirement explicitly chooses
net or explicitly chooses gross, the unchanged compiler derives the mapping.

This is important: the missing decision belongs to the plan/actual semantic
contract, not to an adapter and not to Invoice Card V1.

## Combined finding

The old calculation rule is not merely missing a shared `monetary_basis` field.
Both aliases used by the rule are semantically under-specified:

```text
EstimateItemSnapshot.total
InvoiceLine.total
```

On the planned side, no authoritative canonical PresuPro item amount has yet been
identified.

On the actual side, the named source field does not exist and there are two
explicit canonical alternatives with different bases.

Therefore the correct repair is **not** to add a universal `monetary_basis`
string and preserve the old aliases.

The earliest owning plan/actual design state must define exactly:

1. which authoritative planned item amount is consumed;
2. its basis;
3. whether actual comparison consumes Invoice Card V1 `net_amount` or
   `gross_amount`;
4. why those two selected values are comparable;
5. what explicit evidence/assumption is required when they are not directly
   comparable.

## What not to do

Do not:

- map PresuPro aggregate `grand_total` to an item amount because both are Decimal;
- choose an export/frontend/Holded item representation merely because it exists;
- invent `InvoiceLine.total` as an alias for `net_amount` or `gross_amount`;
- use field-name similarity as semantic proof;
- infer `tax_amount` from `tax_rate` when the accepted Card contract does not
  define that equation;
- infer `discount_amount` from `discount_percent` when the accepted Card contract
  does not define that equation;
- ask an LLM to choose net versus gross;
- hide the choice in an adapter.

## Architectural conclusion

The derivability detector has now found three useful classes of result:

```text
fully self-described surfaces
  -> disposable compiled mapping

missing source-carried meaning
  -> repair source self-description when factual contract evidence exists

multiple valid source meanings but target has not chosen
  -> repair target business semantics
```

The Invoice Card V1 case is the third category. That is evidence that the detector
can localize not only missing fields but also misplaced decision ownership.
