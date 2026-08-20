# Estimate derivability probe — result

## Status

Validated in a real checkout on Termux on 2026-08-20.

Focused experiment result:

```text
25 passed in 0.65s
```

Executed:

```text
tests/test_box_derivability.py
tests/test_box_composition.py
tests/test_estimate_derivability.py
tests/test_cabinet_backend_box_manifest.py
```

This is local-run evidence, not GitHub Actions CI evidence.

## What the probe tested

Source: `presupro_estimate_box_v0.yaml`.
Target: `cabinet_estimate_context_box_v0.yaml`.

The target is provider-agnostic. Cabinet describes the estimate meanings and authority it needs; it does not require a PresuPro client, PresuPro DTO identity, or permanent PresuPro-to-Cabinet adapter.

`tools/box_derivability.py` proves or rejects the mapping. `tools/box_composition.py` compiles the proof into:

```text
source capability invocation
  -> exact semantic projection
  -> target capability invocation
```

No hand-written mapping is accepted by the composition compiler.

## Observed derivation

The current source self-description is sufficient for:

```text
source estimate identity
project identity
source update timestamp
status
locked flag
canonical content
```

The mapping remains unresolved for exactly two Cabinet-required meanings:

```text
money.currency
money.monetary_tax_basis
```

Reported gaps:

```text
SEMANTIC_SOURCE_NOT_FOUND -> EstimateObservationInput.currency
SEMANTIC_SOURCE_NOT_FOUND -> EstimateObservationInput.monetary_basis
```

The compiler must not infer either value from field names, project context, locale, existing Cabinet data, product conventions, or model judgment.

## Why the gaps matter

Accepted plan/actual semantics require planned and actual monetary values to share both currency and monetary/tax basis. Implicit currency conversion and implicit net/gross/tax-basis reinterpretation are forbidden.

Therefore an adapter that supplies either missing value would be making a business decision that belongs in durable specification.

The completeness rule is working as intended:

```text
compiler must choose
  -> mapping is not derivable
  -> emit a proof obligation
  -> repair the owning semantic contract
```

## Closure test

The test suite proves that if the source manifest is augmented with authoritative declarations for:

```text
money.currency
money.monetary_tax_basis
```

then the same compiler derives the complete mapping without any compiler-code change.

That test is hypothetical closure evidence only. It does **not** authorize adding those fields until the real source contract proves that it owns and exposes those meanings.

## Composition result

`tools/box_composition.py` compiles a deterministic three-node plan and refuses to execute an unresolved composition.

The unresolved estimate test proves that neither source nor target callback is invoked when mapping cannot be proven. A failed semantic preflight therefore cannot accidentally cause a box effect.

For a derived mapping, only the proven projection is passed to the target. Extra source fields are not forwarded by default.

## Trace back into the accepted Cabinet design

The derivability gaps were traced back through the accepted design states after the green test run.

### Currency — boundary closure mismatch

State 1 `Model M28 — EstimateSnapshot` already says an immutable estimate snapshot contains `currency` and that PresuPro owns the estimate composition facts.

The closed core model also contains:

```text
EstimateSnapshot.currency: str
```

But the closed inbound support model is:

```text
PresuProEstimateObservation:
  presupro_estimate_id
  project_id
  presupro_updated_at
  status
  locked
  canonical_content
  observed_at
```

with no currency field.

The public contract is still:

```text
refresh_estimate_snapshot(
  observation: PresuProEstimateObservation
) -> EstimateSnapshot
```

and the generation notes say the operation must reject a partial/unprocessable observation rather than fabricate a snapshot. No accepted rule or note identifies another authoritative source from which `EstimateSnapshot.currency` is obtained.

**Conclusion:** `money.currency` is not merely absent from the experimental source manifest. The accepted classical boundary itself does not currently close how required snapshot currency arrives.

Earliest repair owner: the State 1 external estimate projection/input model boundary, then propagation through State 2 acceptance rules and later contracts/notes.

### Monetary/tax basis — missing semantic carrier

The deeper gap is `money.monetary_tax_basis`.

The accepted plan/actual semantic decision requires planned and actual values to have the same accepted monetary/tax basis and explicitly forbids implicit basis conversion.

However the closed `EstimateSnapshot` model has no monetary-basis field, and the closed `PresuProEstimateObservation` has no such field either.

`PlanActualRequest` contains `assumption_ids`, but the current closed core/support model sets do not define a corresponding accepted assumption/evidence model that carries a monetary-basis decision.

**Conclusion:** there is currently no explicit durable semantic carrier that proves the monetary/tax basis required by the calculation rule.

Earliest repair owner: State 1 must either define the missing basis/evidence concept or prove that basis is a fixed property of an already accepted source contract. State 2 must then define exactly how that evidence authorizes comparability. A later adapter, service note, or calculation fallback is too late.

## What not to do

Do not repair either gap by:

- parsing `canonical_content` using an undocumented convention;
- assuming EUR from deployment/project context;
- assuming gross or net from IVA fields;
- adding a PresuPro-specific adapter default;
- letting an LLM choose a basis;
- treating `assumption_ids` as proof when no accepted assumption model defines what those IDs reference.

Any of those would move the missing decision into implementation instead of closing specification.

## Required source reconnaissance before semantic repair

The existing `presupro_estimate_lineage_discovery.md` verified identity, mutability, locking, status, and lineage. It did **not** establish currency or monetary-total basis semantics.

Before changing the accepted models, perform a focused PresuPro monetary-contract reconnaissance that answers:

1. Is estimate currency an explicit stored/API field, a project-level fact, or absent?
2. Who is authoritative for that currency?
3. Do estimate/item totals represent net, gross/tax-inclusive, or another declared basis?
4. Is the basis fixed by contract or variable per estimate/item?
5. How do IVA, discount, waste, margin, unit price, line total, and estimate total relate deterministically?
6. Which exact fields survive API/export and can be self-described by a source box?
7. Can the monetary basis be stated as a contract-level semantic constant, or must it travel as data/evidence?

Only evidence from the actual source contract should close these proof obligations.

## Architectural conclusion

The experiment now has evidence for two distinct integration cases:

1. Registry-like project catalogue -> Cabinet project observation: completely derivable from declared semantics.
2. PresuPro-like estimate observation -> Cabinet estimate observation: mostly derivable, but blocked by two genuine monetary semantic gaps that trace into the accepted product design itself.

This supports the working rule:

> Keep meaning durable. Everything provably derivable from that meaning should be a cheap disposable compilation artifact.

The integration boundary is:

```text
derivable mapping
  -> compile disposable plumbing

non-derivable mapping
  -> expose missing semantic decision
  -> trace it to its owning design state
```

## Next experiment

Create a focused, evidence-driven PresuPro monetary reconnaissance rather than making the estimate mapping green by assertion.

After source evidence is known:

1. repair the earliest owning semantic state;
2. propagate the decision to box self-description;
3. rerun the unchanged derivability/composition compiler;
4. require the mapping to become derived without adapter code or compiler special-casing.
