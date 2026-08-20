# Cabinet Vault Experiment — Direction

## Read this first

This is the architectural handoff for branch `agent/cabinet-vault-experiment`.

The working hypothesis is:

> Cabinet Backend should be tested as a locally running, self-describing data and authority box compiled from specification, not as a product-specific backend application.

`SPEC_STANDARD` remains the Factory language. This experiment identifies which parts are durable semantic truth and which parts are disposable lowering or composition artifacts.

## Core architecture

A box owns its own:

- schemas and identity;
- data and storage locality;
- invariants and lifecycle;
- capabilities;
- authorization/effect policy;
- disclosure policy;
- provenance and audit requirements.

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

Do not introduce durable product-specific integration code merely because one task spans products.

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

`calculate_plan_actual` is deterministic under accepted rules. Do not introduce an LLM there.

## Implemented spikes

The branch contains:

- `CABINET_V0.md` — conceptual box model;
- coarse trusted host and typed execution-graph spikes;
- `CABINET_BACKEND_CLASSIFICATION.md`;
- `cabinet_backend_box_v0.yaml` — real archive/source-custody manifest;
- `tools/box_derivability.py` — deterministic mapping proof/gap detector;
- `tools/box_composition.py` — compiler/executor for disposable cross-box composition plans;
- Registry-like source and Cabinet provider-agnostic project-catalogue manifests;
- PresuPro-like source and Cabinet provider-agnostic estimate manifests;
- focused tests for box boundaries, derivability, composition, and estimate proof obligations.

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

`tools/box_composition.py` compiles a three-node plan:

```text
source capability
  -> exact_project
  -> target capability
```

The compiler does not accept a hand-written mapping argument.

Derivability is completed before either box is invoked. If the plan is unresolved, execution stops before source or target callbacks run. A derived projection forwards only proven target fields; unrelated source fields do not cross by default.

## First real cross-box probe — project catalogue

Registry-like project catalogue -> Cabinet project observation is fully derivable from declared semantic IDs, exact types, and `project.catalogue.authority`.

Cabinet does not require a Registry client, Registry DTO, or Registry-named semantic surface.

This validates the disposable-adapter hypothesis for a straightforward real domain case.

## Second real cross-box probe — estimate

PresuPro-like estimate -> Cabinet estimate observation is intentionally **not fully derivable yet**.

The current accepted source observation is sufficient for:

```text
source estimate identity
project identity
source update timestamp
status
locked flag
canonical content
```

The compiler reports exactly two remaining proof obligations:

```text
money.currency
money.monetary_tax_basis
```

These correspond to Cabinet-required fields:

```text
EstimateObservationInput.currency
EstimateObservationInput.monetary_basis
```

This is a meaningful semantic gap, not a compiler defect. Accepted plan/actual rules require currency and monetary/tax-basis compatibility and explicitly forbid implicit currency or net/gross reinterpretation.

The test also proves that adding authoritative declarations for those two meanings to the source manifest closes the mapping **without compiler-code change**.

See `ESTIMATE_DERIVABILITY_RESULT.md` for the recorded experiment result.

## Test evidence

On 2026-08-20 the following focused suite was executed in a real Termux checkout:

```text
tests/test_box_derivability.py
tests/test_box_composition.py
tests/test_estimate_derivability.py
tests/test_cabinet_backend_box_manifest.py
```

Result:

```text
25 passed in 0.65s
```

This is real local-run evidence. The experiment branch is still not covered by the existing automatic Stage 8.1 GitHub Actions trigger, so do not describe it as CI-green.

## Next work when resuming

Do **not** make the estimate probe green by inventing currency or monetary basis in the adapter.

Next steps:

1. trace `money.currency` and `money.monetary_tax_basis` to the earliest owning accepted design state;
2. determine whether the source authority can actually expose them, whether Cabinet requires separately authoritative assumption/evidence, or whether the current observation boundary is incomplete;
3. close the estimate mapping only by repairing the owning semantic contract;
4. connect the generic composition-plan IR to the broader agent execution-graph/discovery path so derived mappings are inserted automatically;
5. only after those probes, define the smallest reusable semantic vocabulary and deterministic transformation algebra — no universal business ontology by default;
6. compile `cabinet_backend_box_v0.yaml` into a small generic host IR/runtime and prove one archive/source capability without reintroducing service/repository/router ownership;
7. define the minimum prepare/execute/observe/settle protocol for external effects using Holded as the adversarial case;
8. classify local/VPS topology and compare the resulting implementation surface against the classical branch.

## Success condition

The experiment succeeds if useful products can be deployed as:

```text
generic host + compiled self-described box + local data/storage
```

while independent boxes can be composed without permanent pairwise adapters, and every non-trivial mapping is either provably compiled from declared meaning or rejected with a structured semantic gap that tells the specification author what remains undefined.
