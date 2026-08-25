# Estimate derivability probe — result

## Status

The first estimate derivability/composition suite was validated in a real Termux checkout on 2026-08-20:

```text
25 passed in 0.65s
```

A follow-up local PresuPro monetary reconnaissance then investigated the two proof obligations emitted by that probe.

## PresuPro monetary reconnaissance result

### `money.currency` — CLOSED at source contract level

The real PresuPro contract does not store currency on `Estimate` or on the project model. Currency is an application-level contract constant:

```text
config.app.currency = EUR
```

`calculate_estimate_totals` exposes the same deterministic `EUR` currency in its totals result.

Therefore the source box can truthfully self-describe:

```text
semantic: money.currency
authority: estimate.source.authority
source.kind: contract_constant
source.contract: config.app.currency
source.value: EUR
```

This is not an adapter default and not inference from locale/project context. It is verified source-product contract data.

The experimental `presupro_estimate_box_v0.yaml` now exposes that fact, and generic Cabinet estimate-observation acceptance requires currency but no longer invents plan/actual monetary-basis semantics at this boundary.

### Aggregate pricing semantics — deterministic

The local reconnaissance pinned the backend pricing order with a synthetic test:

```text
effective_unit_price =
    item.unit_price
    else preferred material product.last_price
    else 0

effective_qty = round(quantity * (1 + waste / 100), 4)
base_line = round(effective_qty * effective_unit_price, 2)

discount = round(base_line * discount_percent / 100, 2)
discounted_line = round(base_line - discount, 2)

line_with_margin = round(
    discounted_line * (1 + margin_percent / 100),
    2
)
margin = round(line_with_margin - discounted_line, 2)

iva_rate = item.iva_percent if set else estimate.iva_percent
line_iva = round(line_with_margin * iva_rate / 100, 2)

materials/labor subtotal = sum(discounted_line), split by item.type
taxable_subtotal = materials_subtotal + labor_subtotal + margin_total
grand_total = taxable_subtotal + iva_total
```

This proves that backend aggregate `grand_total` is tax-inclusive and that the tax-exclusive taxable base is formed after waste, discount, and margin.

### `money.monetary_tax_basis` — NOT CLOSED as one generic estimate fact

The reconnaissance found no single authoritative monetary-basis carrier that can be applied to every amount in an estimate observation.

In particular there is no canonical domain `item_total` shared by all PresuPro surfaces:

- backend aggregate calculation has a deterministic internal pricing sequence;
- export `Line Total` uses a different line representation;
- frontend line display uses another post-waste/post-margin/post-discount value;
- Holded projection transmits raw quantity, unit price, discount, and IVA without waste/margin as one canonical line-total field.

Therefore a single field such as:

```text
monetary_basis: gross_tax_inclusive
```

on the generic estimate observation would overstate what the source contract actually guarantees.

## Stronger gap discovered in accepted Cabinet design

The accepted Cabinet core model contains:

```text
EstimateItemSnapshot.total: Decimal
```

and the accepted plan/actual rule says:

```text
planned_amount = EstimateItemSnapshot.total
```

while also saying Cabinet must consume this as an accepted PresuPro result rather than reapply PresuPro arithmetic.

But the PresuPro reconnaissance found no single canonical source item-total meaning that supports that field as currently described.

This is more precise than the original generic `money.monetary_tax_basis` gap:

```text
What exactly is EstimateItemSnapshot.total?
What source value/derivation authoritatively produces it?
What monetary/tax basis does that exact planned amount carry?
```

The experimental probe now moves this obligation to a dedicated plan/actual amount boundary instead of forcing it into generic estimate-observation acceptance.

## Refined derivability architecture

The two concerns are now separated:

```text
PresuPro estimate observation
  -> identity/project/status/lock/content/currency
  -> Cabinet immutable observation
  -> fully derivable cross-box plumbing expected

PresuPro pricing semantics
  -> ??? authoritative per-item planned amount
  -> ??? exact planned amount basis
  -> Cabinet plan/actual amount requirement
  -> intentionally unresolved until specification repair
```

This is the intended behavior: a mapping gap moves to the semantic boundary that actually owns the missing decision.

## New plan/actual amount probe

The branch now contains:

- `presupro_pricing_contract_v0.yaml` — only factual pricing semantics proved by the local reconnaissance;
- `cabinet_plan_actual_amount_requirement_v0.yaml` — the Cabinet requirement extracted from `EstimateItemSnapshot.total` and plan/actual comparability;
- `tests/test_plan_actual_amount_derivability.py` — executable proof that:
  - `money.currency` derives;
  - aggregate `grand_total: Decimal` cannot substitute for item planned amount merely because the type matches;
  - canonical item planned amount remains unresolved;
  - its exact monetary basis remains unresolved;
  - adding explicit authoritative item-amount semantics would close the same compiler without compiler special-casing.

## Required design repair

Do not repair this by choosing a convenient existing PresuPro display/export value.

The earliest accepted design state must define what Cabinet means by the planned monetary amount of one `EstimateItemSnapshot`.

Possible legitimate outcomes include, but are not limited to:

- PresuPro exposes/defines a canonical per-item gross amount;
- PresuPro exposes/defines a canonical per-item tax-exclusive amount;
- Cabinet explicitly derives one amount from a declared PresuPro pricing algebra and records that derivation as part of snapshot semantics;
- the analysis grain changes so plan/actual does not pretend an unsupported canonical item amount exists.

Whichever decision is accepted must also define the exact basis used when comparing with `InvoiceLine.total`.

That actual-side amount basis should be verified separately rather than assumed.

## Evidence status

PresuPro local monetary probe reported:

```text
1 passed in 0.33s
```

for the focused synthetic pricing test, and:

```text
4 passed in 0.33s
```

for the full pricing test file. `git diff --check` passed in that local PresuPro workspace.

These are user-provided local execution results from the PresuPro workspace, not GitHub Actions evidence in this repository.

## Architectural conclusion

The detector did more than reject an adapter. It distinguished:

```text
source fact really exists but was not surfaced
  -> repair source self-description

source aggregate semantics exist but target asks a different semantic question
  -> do not coerce one into the other

accepted product model names a value whose authoritative source meaning is not closed
  -> repair the earliest owning design state
```

This is exactly the desired specification-completeness behavior.
