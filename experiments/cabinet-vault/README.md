# Cabinet vault prototype

This experiment tests whether accepted product semantics can compile into self-describing boxes plus a generic trusted host, while cross-product integration becomes disposable derived composition rather than permanent pairwise adapter code.

Read `DIRECTION.md` first when resuming the branch.

## Durable versus disposable

Durable:

- box schemas and meaning;
- identity and authority requirements;
- capability definitions;
- disclosure/effect policy;
- data inside the box;
- audit/provenance requirements.

Disposable when provably derivable:

- field projection;
- typed cross-box plumbing;
- deterministic composition graphs;
- transport/lowering choices that do not change semantics or authority.

The agent does not receive raw SQL, storage paths, box credentials, or authority merely by possessing an endpoint.

## Spike 1 — coarse trusted capability

`invoice.summary` demonstrated that a trusted host can expose a bounded semantic operation and lower it internally while enforcing grant scope.

```bash
python experiments/cabinet-vault/tools/cabinet_host.py \
  experiments/cabinet-vault/cabinet_backend_invoice_summary.yaml \
  --project project-1
```

## Spike 2 — typed execution graph

`cabinet_backend_execution_graph.yaml` decomposes the coarse capability into typed operators. The agent composes the graph; the host validates it before data access and keeps opaque invoice-set handles local.

```bash
python experiments/cabinet-vault/tools/cabinet_graph_host.py \
  experiments/cabinet-vault/cabinet_backend_execution_graph.yaml
```

## Spike 3 — real Cabinet box slice

`CABINET_BACKEND_CLASSIFICATION.md` classifies the accepted real Cabinet Backend design into durable semantics versus generic lowering and transient cross-box work.

`cabinet_backend_box_v0.yaml` is the first real archive/source-custody manifest. It has no permanent Registry, PresuPro, Holded, VPS, ORM, repository, or service dependency in its semantic surface. Authorization, actor identity, decision IDs/timestamps, and storage references remain host-owned.

## Spike 4 — derivability is an instrument

`experiments/cabinet-vault/tools/box_derivability.py` implements the rule:

> If mapping is determined by the two self-described box surfaces, compile it. If the compiler must choose, return a semantic gap instead of guessing.

For v0, a target field is derivable only from one unambiguous source field with:

```text
same semantic id
+ exact type
+ required authority
```

Field names are not evidence.

The Registry-like project-catalogue probe is fully derivable into the Cabinet provider-agnostic `ProjectCatalogueObservation` contract without a permanent Registry adapter.

## Spike 5 — composition compiler

`experiments/cabinet-vault/tools/box_composition.py` turns a derivability proof into a disposable execution plan:

```text
source capability
  -> exact_project
  -> target capability
```

The compiler does not accept a hand-written field mapping. If derivability is unresolved, execution stops before either source or target box is invoked. For a derived plan, only proven target fields are projected; unrelated source data does not cross by default.

## Spike 6 — estimate semantic-gap probe

The second real probe uses:

- `presupro_estimate_box_v0.yaml`;
- `cabinet_estimate_context_box_v0.yaml`;
- `tests/test_estimate_derivability.py`.

The current mapping derives source estimate identity, project identity, source update time, status, locked flag, and canonical content.

It intentionally remains unresolved for:

```text
money.currency
money.monetary_tax_basis
```

Those gaps are useful: accepted plan/actual semantics require currency and monetary/tax-basis compatibility and explicitly forbid implicit conversion or net/gross reinterpretation.

The test proves that adding authoritative declarations for these meanings to the source manifest closes the mapping without changing compiler code.

See `ESTIMATE_DERIVABILITY_RESULT.md` for the recorded result.

## Current architectural split

```text
Agent     -> chooses composition
Compiler  -> proves and derives transient plumbing
Box       -> declares meaning, authority, policy, allowed effects
Host      -> enforces authority and trusted lowering
```

The long-lived artifact is the semantic contract. Pairwise adapters should be throwaway output whenever their behavior is fully derivable.

## Test evidence

The following focused suite was executed in a real Termux checkout on 2026-08-20:

```bash
python -m pytest -q \
  tests/test_box_derivability.py \
  tests/test_box_composition.py \
  tests/test_estimate_derivability.py \
  tests/test_cabinet_backend_box_manifest.py
```

Result:

```text
25 passed in 0.65s
```

This is local-run evidence, not GitHub Actions CI evidence. The experiment branch is not covered by the existing automatic Stage 8.1 workflow trigger.

## Next work

Do not make the estimate probe green by inventing currency or monetary basis in an adapter.

Next:

1. trace the two monetary proof obligations to their earliest owning accepted design state;
2. decide whether source authority can expose them, Cabinet needs separate authoritative assumption/evidence, or the observation boundary is incomplete;
3. close the mapping by semantic repair only;
4. connect the generic composition-plan IR to agent discovery/execution-graph insertion;
5. then define the smallest reusable semantic vocabulary/transformation algebra;
6. continue toward compiling the real archive/source manifest into a generic host runtime;
7. later exercise cross-box external effects with a prepare/execute/observe/settle protocol.
