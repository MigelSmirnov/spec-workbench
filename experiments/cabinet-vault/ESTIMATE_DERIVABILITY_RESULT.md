# Estimate derivability probe — result

## Status

Validated in a real checkout on Termux on 2026-08-20.

The focused experiment suite passed:

```text
25 passed in 0.65s
```

The executed set was:

```text
tests/test_box_derivability.py
tests/test_box_composition.py
tests/test_estimate_derivability.py
tests/test_cabinet_backend_box_manifest.py
```

This result is local-run evidence, not GitHub Actions CI evidence.

## What the second probe tested

The source side is `presupro_estimate_box_v0.yaml`.
The target side is `cabinet_estimate_context_box_v0.yaml`.

The target is intentionally provider-agnostic. Cabinet describes the estimate facts and authority it needs; it does not require a PresuPro client, PresuPro DTO identity, or a permanent PresuPro-to-Cabinet adapter.

The mapping compiler is the same generic `tools/box_derivability.py` used by the Registry probe. Cross-box execution is compiled by `tools/box_composition.py` into:

```text
source capability invocation
  -> exact semantic projection
  -> target capability invocation
```

No hand-written field mapping is accepted by the composition compiler.

## Observed result

The accepted source observation is sufficient to derive these Cabinet inputs:

```text
source estimate identity
project identity
source update timestamp
status
locked flag
canonical content
```

The probe remains unresolved for exactly two Cabinet-required meanings:

```text
money.currency
money.monetary_tax_basis
```

The reported gaps are `SEMANTIC_SOURCE_NOT_FOUND` for:

```text
EstimateObservationInput.currency
EstimateObservationInput.monetary_basis
```

This is intentional. The compiler must not infer either value from field names, project context, locale, existing Cabinet data, PresuPro conventions, or model judgment.

## Why these gaps matter

The accepted plan/actual rules require planned and actual monetary values to share both currency and monetary/tax basis. They explicitly forbid implicit currency conversion and net/gross/tax-basis reinterpretation.

Therefore an adapter that silently supplies either value would be making a business decision that belongs in durable specification.

The probe demonstrates the desired completeness rule:

```text
compiler must choose
  -> mapping is not derivable
  -> emit a proof obligation
  -> repair the owning semantic contract
```

## Closure test

The test suite also proves that if the source manifest is augmented with fields declaring:

```text
semantic: money.currency
authority: estimate.source.authority
```

and:

```text
semantic: money.monetary_tax_basis
authority: estimate.source.authority
```

then the same compiler derives the complete mapping without any compiler-code change.

That is the important property: semantic repair changes the specification, not the adapter implementation.

## Composition result

`tools/box_composition.py` compiles a deterministic three-node plan and refuses to execute when derivability is unresolved.

The unresolved estimate test proves that neither source nor target box callback is invoked when the mapping cannot be proven. This prevents a failed preflight from causing a source-side or target-side effect accidentally.

For a derived mapping, execution applies only the proven exact projection and then invokes the target capability. Extra source fields are not forwarded by default.

## Architectural conclusion

The experiment now has evidence for two distinct cases:

1. Registry-like project catalogue -> Cabinet project observation: completely derivable from declared semantics.
2. PresuPro-like estimate observation -> Cabinet estimate observation: mostly derivable, but blocked by two genuine monetary semantic gaps.

This supports the working rule:

> Keep meaning durable. Everything provably derivable from that meaning should be a cheap disposable compilation artifact.

The integration boundary is therefore not "prebuilt adapter versus no adapter". It is:

```text
derivable mapping
  -> compile disposable plumbing

non-derivable mapping
  -> expose missing semantic decision
```

## Next experiment

Do not add currency or monetary basis to the source manifest merely to make the test green unless the source product specification actually owns and can authoritatively expose those meanings.

The next step is to trace those two proof obligations back to their earliest owning accepted design state and decide whether:

- PresuPro/source authority really provides them explicitly;
- Cabinet must accept a separately authoritative assumption/evidence input; or
- the current plan/actual observation boundary is missing a required semantic source.

Only after that decision should the estimate mapping be closed.

In parallel, the generic composition plan is now strong enough to be connected to the broader agent execution-graph path without introducing a permanent product-specific adapter.
