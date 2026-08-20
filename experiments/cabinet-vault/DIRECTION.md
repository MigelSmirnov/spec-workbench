# Cabinet Vault Experiment — Direction

## Read this first

This is the architectural handoff for branch `agent/cabinet-vault-experiment`.

The working hypothesis is:

> Cabinet Backend should be tested as a locally running, self-describing data and authority box compiled from specification, not as a product-specific backend application.

`SPEC_STANDARD` remains the Factory language. This experiment identifies which parts are durable semantic truth and which parts are disposable lowering or composition artifacts.

## Core architecture

A box owns its own schemas/identity, data/storage locality, invariants/lifecycle, capabilities, authorization/effect policy, disclosure policy, and provenance/audit requirements.

A box MUST NOT know neighbouring products by address, API, DTO, client, adapter, or deployment dependency.

Use this rule:

> **A box describes what it means and what authority it requires, not what its neighbours mean.**

The agent chooses which independent capabilities to compose.
The deterministic compiler derives how declared-compatible surfaces connect.
Each box/host retains authority over its own data and effects.

## Derivability is a completeness rule

The placeholder detector generalizes directly to cross-box integration:

```text
generator/compiler must choose
        ↓
specification does not determine the answer
        ↓
return a structured semantic gap instead of guessing
```

This applies to field mapping, disclosure, scope, identity/revision, units, currency, monetary/tax basis, lifecycle meaning, lineage, effect settlement, and other semantic choices.

The durable rule is:

> **Keep meaning durable. Treat everything provably derivable from that meaning as a cheap disposable compilation artifact.**

Do not repair failed derivation with field-name heuristics, fuzzy model choices, hidden defaults, or pairwise bridges. Repair the specification that owns the missing meaning.

## Agent, compiler, box, and host split

```text
User intent
  -> Agent chooses composition
      -> discover source capability/schema
      -> discover target capability/schema
      -> Compiler proves or rejects mapping
           -> derived: emit disposable typed projection/graph
           -> unresolved: emit structured semantic gap
      -> execute proved graph

Box/host retains data/effect authority.
```

Agent owns transient intent, discovery, routing, orchestration, and bounded semantic/model operations where genuine interpretation remains.
Compiler owns transient derivable plumbing: semantic projection, compatible typed adaptation, declared deterministic transformations, proof, and structured gaps.
Box/host owns durable meaning, auth/grants, schema validation, capability semantics, policy, transaction/effect control, storage, protected credentials/files, disclosure, and audit/provenance.

## No permanent cross-box adapters by default

Prefer:

```text
Box A manifest + Box B manifest
        -> deterministic derivability proof
        -> disposable typed mapping/graph
        -> execution
```

Portability is lost only when required meaning lives outside the manifests.

## Determinism target

Preferred order:

1. exact deterministic projection or typed capability;
2. deterministic composition/transformation whose semantics are declared;
3. bounded typed model operation only when real interpretation remains;
4. sandboxed ephemeral generated code only as a last escape hatch.

If behavior is fully determined select/filter/project/map/derive/aggregate/validate/mutate/publish plumbing, it should not become permanent handwritten integration code.

## Cabinet Backend classification to preserve

The accepted classical design currently maps approximately as follows:

- `domain_models` -> durable data/schema;
- `access_control` -> Cabinet policy plus generic host auth/grant/audit kernel;
- `durable_archive` -> Cabinet-native semantics plus generic record/transaction/blob-vault lowering;
- `registry_context` -> Cabinet-owned project observations and assignment validation; source polling/client knowledge is external;
- `plan_actual` -> immutable observations/decisions + deterministic calculation; semantic match proposal is bounded and non-authoritative;
- `holded_publication` -> Cabinet-owned eligibility/idempotency/evidence/settlement; external mutation is separately composed;
- `holded_gateway` -> external connector/authority or transport infrastructure;
- `synchronization` -> split local evidence/policy from remote delivery/orchestration;
- `retention_release` -> data-owning box decides its destructive effect;
- service/repository/Postgres/FastAPI/bootstrap/client classes -> classical lowering unless semantics prove otherwise.

`calculate_plan_actual` remains a deterministic target. The new probes show that some of its **inputs were not semantically closed**, not that an LLM is needed for calculation.

## Implemented spikes

The branch contains:

- `CABINET_V0.md` — conceptual box model;
- coarse trusted host and typed execution-graph spikes;
- `CABINET_BACKEND_CLASSIFICATION.md`;
- `cabinet_backend_box_v0.yaml` — real archive/source-custody manifest;
- `tools/box_derivability.py` — deterministic mapping proof/gap detector;
- `tools/box_composition.py` — compiler/executor for disposable cross-box composition plans;
- Registry-like source and Cabinet provider-agnostic project-catalogue manifests;
- PresuPro estimate-observation and pricing semantic manifests;
- Cabinet provider-agnostic estimate observation and planned-amount requirement manifests;
- Invoice Card V1 line monetary source self-description;
- Cabinet actual-line-amount requirement manifest;
- focused tests for box boundaries, derivability, composition, estimate observation, planned amount, and actual amount proof obligations.

## Derivability v0

A target field is derivable only when there is one unambiguous source field with:

```text
same semantic id
+ exact type
+ required authority
```

Field names are not evidence.

Current structured gaps include:

- `TARGET_FIELD_NOT_SELF_DESCRIBING`;
- `SEMANTIC_NOT_DECLARED`;
- `SEMANTIC_SOURCE_NOT_FOUND`;
- `TYPE_MISMATCH`;
- `AUTHORITY_MISMATCH`;
- `AMBIGUOUS_SEMANTIC_SOURCE`;
- `UNSUPPORTED_TRANSFORMATION`.

A successful derivation is executable through an exact projection. An unresolved derivation cannot execute.

## Composition compiler result

`tools/box_composition.py` compiles:

```text
source capability
  -> exact_project
  -> target capability
```

The compiler does not accept a hand-written mapping argument.
Derivability completes before either box is invoked. An unresolved plan stops before source or target callbacks run. A derived projection forwards only proven target fields.

## First real cross-box probe — project catalogue

Registry-like project catalogue -> Cabinet project observation is fully derivable from declared semantic IDs, exact types, and `project.catalogue.authority`.

Cabinet does not require a Registry client, Registry DTO, or Registry-named semantic surface.

## Second real cross-box probe — estimate observation

The first estimate probe initially reported two missing meanings:

```text
money.currency
money.monetary_tax_basis
```

A focused local PresuPro monetary reconnaissance separated them.

### Currency is a real source-contract fact

PresuPro does not store currency on each Estimate or project. Its accepted application contract fixes:

```text
config.app.currency = EUR
```

and `calculate_estimate_totals` surfaces the same deterministic currency.

Therefore `presupro_estimate_box_v0.yaml` truthfully exposes `money.currency` as a source-contract constant. This is not locale inference or an adapter default.

Generic Cabinet estimate-observation acceptance is now fully derivable.

### Generic monetary basis does not belong on observation acceptance

The same reconnaissance proved deterministic aggregate pricing, including tax-inclusive `grand_total`, but did **not** prove one canonical item-total value or one monetary basis that applies to every estimate amount.

Therefore the generic estimate observation does not carry a made-up universal `monetary_basis`. The gap belongs to the semantic operation that actually needs a comparable item amount.

## Third probe — planned item amount

The accepted Cabinet core model contains:

```text
EstimateItemSnapshot.total: Decimal
```

and accepted plan/actual semantics state:

```text
planned_amount = EstimateItemSnapshot.total
```

while saying Cabinet should consume that as an accepted PresuPro result rather than independently reapply PresuPro arithmetic.

The factual PresuPro probe found no single canonical source item total shared by backend aggregate logic, export line total, frontend line display, and Holded projection.

Represented by:

- `presupro_pricing_contract_v0.yaml`;
- `cabinet_plan_actual_amount_requirement_v0.yaml`;
- `tests/test_plan_actual_amount_derivability.py`.

Current proven derivation:

```text
money.currency
  -> derived

estimate.item.planned_amount
  -> unresolved

estimate.item.planned_amount_basis
  -> unresolved
```

A Decimal aggregate `grand_total` cannot satisfy an item amount merely because its type matches.

## Fourth probe — actual Invoice Card line amount

A factual probe against the real `Cabinet_web` source-of-truth checkout at commit `63f1752` proved that Invoice Card V1 has **no `InvoiceLine.total` field**.

The canonical closed line shape instead exposes:

```text
net_amount
  = ROUND_HALF_UP(quantity * unit_price_net - discount_amount, 2)
  basis = post_discount_tax_exclusive

gross_amount
  = ROUND_HALF_UP(net_amount + tax_amount, 2)
  basis = tax_inclusive
```

All line monetary values bind to the containing document's required root `invoice.currency`. The validator verifies the canonical Card values but does not rewrite them.

The accepted plan/actual rule currently says:

```text
actual_amount = InvoiceLine.total
```

so the old rule names a source field that does not exist and leaves a real business choice unresolved: compare planned amounts against V1 `net_amount` or V1 `gross_amount`.

This is represented by:

- `invoice_card_v1_line_monetary_contract_v0.yaml` — both actually proved V1 monetary meanings;
- `cabinet_plan_actual_actual_amount_requirement_v0.yaml` — the unresolved target requirement;
- `tests/test_plan_actual_actual_amount_derivability.py` — fail-closed detector.

Expected derivation:

```text
money.currency
  -> derived

invoice.line.actual_amount
  -> unresolved

invoice.line.actual_amount_basis
  -> unresolved
```

The test also proves that if the target contract explicitly chooses net semantics **or** explicitly chooses gross semantics, the unchanged compiler derives the mapping. Therefore the missing decision belongs to `plan_actual`, not to Invoice Card V1 and not to an adapter.

See `PLAN_ACTUAL_MONETARY_DERIVABILITY_RESULT.md`.

## Combined monetary finding

The old deterministic formula is not yet executable from semantically closed inputs because both aliases used by it are under-specified:

```text
EstimateItemSnapshot.total
InvoiceLine.total
```

Planned side: no authoritative canonical PresuPro item amount has yet been identified.

Actual side: the named field does not exist; V1 provides two explicit authoritative alternatives with different bases.

The correct repair is not a generic `monetary_basis` string bolted onto the adapter. The earliest owning plan/actual State 1/State 2 decision must define exactly which planned amount and which actual amount are compared and why their bases are compatible.

## Evidence from local execution

### Workbench

On 2026-08-20 the refined workbench suite before the newest actual-side detector was run in a real checkout:

```text
29 passed, 1 warning in 0.79s
```

The warning was only inability to write `.pytest_cache` and did not affect results.

### PresuPro

Focused monetary test:

```text
1 passed in 0.33s
```

Full pricing test file:

```text
4 passed in 0.33s
```

`git diff --check`: PASS.

### Cabinet_web Invoice Card V1

Focused synthetic line monetary test:

```text
1 passed in 0.18s
```

Validator suite:

```text
16 passed, 22 subtests passed in 0.18s
```

`git diff --check`: PASS.

These are real local-run results, not GitHub Actions CI evidence.

The newest workbench actual-side detector still requires a fresh checkout run before being called green.

## Next work when resuming

Do **not** invent aliases for `EstimateItemSnapshot.total` or `InvoiceLine.total`.

Next steps:

1. run the newest workbench suite including `tests/test_plan_actual_actual_amount_derivability.py`;
2. repair the earliest State 1/State 2 `plan_actual` semantic decision so it explicitly names the authoritative planned amount, its basis, the chosen actual V1 amount (`net_amount` or `gross_amount`), and the comparability rule;
3. only after that decision, propagate the selected meanings into the box source/target manifests and require the unchanged derivability compiler to close both planned and actual mappings;
4. then implement the deterministic calculation over those proved semantic inputs;
5. connect generic composition-plan IR to broader agent discovery/execution so derived mappings are inserted automatically;
6. define only the smallest reusable semantic vocabulary/operator algebra demonstrated by these probes;
7. compile `cabinet_backend_box_v0.yaml` into a generic host IR/runtime and prove one archive/source capability without service/repository/router ownership;
8. define the minimum prepare/execute/observe/settle protocol for external effects using Holded as the adversarial case;
9. classify local/VPS topology and compare implementation surface against the classical branch.

## Success condition

The experiment succeeds if useful products can be deployed as:

```text
generic host + compiled self-described box + local data/storage
```

while independent boxes can be composed without permanent pairwise adapters, and every non-trivial mapping is either provably compiled from declared meaning or rejected with a structured semantic gap that points to the owning specification decision.
