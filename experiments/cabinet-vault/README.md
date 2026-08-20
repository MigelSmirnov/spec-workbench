# Cabinet vault prototype

This experiment tests `CABINET_V0.md` with a minimal trusted runtime and then
applies the same architecture to the accepted real `examples/cabinet-backend`
design.

Read `DIRECTION.md` first when resuming the branch.

## What is durable

- cabinet schema;
- identity and grants;
- capability definitions;
- disclosure/effect policy;
- data inside the cabinet;
- audit evidence.

The agent does not receive a database connection, raw SQL capability, storage
paths, or the cabinet encryption key.

## Spike 1 — coarse capability

`invoice.summary` accepts a project and optional date range. The trusted host
lowers that capability to a parameterized SQLite aggregate and returns only:

- `project_id`;
- `invoice_count`;
- `confirmed_total`;
- `currency`;
- execution evidence.

Unconfirmed invoices do not contribute. Requests outside the grant's project
scope fail closed.

Run it with:

```bash
python tools/cabinet_host.py \
  experiments/cabinet-vault/cabinet_backend_invoice_summary.yaml \
  --project project-1
```

## Spike 2 — composable execution graph

`cabinet_backend_execution_graph.yaml` replaces the coarse operation with atomic
capabilities:

```text
invoice.select
  -> invoice.filter_confirmed
  -> invoice.filter_date
  -> invoice.aggregate_total
```

An agent may compose those capabilities into an execution graph, but the host
still owns every lowering. Intermediate invoice sets are represented as opaque
`InvoiceRefSet` handles that exist only inside the cabinet host. The graph cannot
return one of those handles as its public result, and the agent never receives
raw rows or generated SQL.

The host performs graph preflight before data access: capability grants,
argument shape, literal/reference types, node references, output type, resource
scope, and opaque-output escape all fail closed before execution.

Run the graph demo with:

```bash
python tools/cabinet_graph_host.py \
  experiments/cabinet-vault/cabinet_backend_execution_graph.yaml
```

Run focused tests with:

```bash
pytest -q tests/test_cabinet_host.py tests/test_cabinet_graph_host.py
```

## Spike 3 — extract a real Cabinet box from the accepted design

The toy DSL is intentionally not expanded first. `CABINET_BACKEND_CLASSIFICATION.md`
returns to the closed `examples/cabinet-backend` design and classifies the
accepted surface into:

```text
data/schema
policy/invariant
capability
deterministic operator/composition
model operation
storage/transport lowering
truly unresolved behavior
```

The classification finds that much of the Stage 8.1 implementation surface is a
classical application lowering rather than durable product identity. Service
classes, repository/UoW classes, concrete PostgreSQL/filesystem implementations,
FastAPI/app-state wiring, bootstrap constructor graphs, and permanent
Registry/PresuPro/Holded clients are therefore candidates to disappear from the
compiled Cabinet product surface.

`cabinet_backend_box_v0.yaml` is the first real manifest slice. It covers archive
inspection and local source custody because those operations are owned entirely
by Cabinet and already have accepted integrity, concurrency, authority, recovery,
and disclosure semantics.

The manifest deliberately:

- has no permanent external product dependency;
- exposes typed archive/source capabilities rather than service methods;
- makes authorization/grants a host boundary rather than an agent-supplied
  `AuthorizationDecision` argument;
- binds actor/decision identity and timestamps inside the trusted host;
- prevents callers from supplying or receiving storage/staging/final paths;
- expresses source attachment as a deterministic staged transaction/publication
  lowering;
- treats PostgreSQL, filesystem storage, MCP/IPC/HTTP, and Python classes as
  replaceable lowerings;
- defers cross-node transfer ingestion until the cross-box authority/effect
  protocol is classified rather than copying the old VPS integration boundary
  into the box.

Focused manifest-boundary tests:

```bash
pytest -q tests/test_cabinet_backend_box_manifest.py
```

The next high-value real slice is `plan_actual`: accept a typed external estimate
observation, optionally run a bounded non-authoritative semantic match proposal,
record an explicit match decision, and calculate the confirmed result
deterministically — without a PresuPro client or permanent `PlanActualService`
inside Cabinet.

## Security boundary under test

The key question is not whether an agent can generate SQL or Python. It is
whether a cabinet can expose enough machine-readable semantics for an agent to
compose useful work while the host retains authority over data access and
lowering.

The experiment separates **composition authority** from **data/effect
authority**:

- the agent chooses a graph of granted operations and transient mappings between
  independent boxes;
- the host validates grants, exact resource scope, declared types, effects, and
  disclosure;
- the host executes trusted deterministic lowerings locally;
- opaque intermediates and protected storage references stay inside the box;
- only declared public results cross the boundary;
- audit/provenance evidence records what was authorized, executed, and disclosed.

Agent-supplied SQL is intentionally impossible.

## Not implemented yet

- signed grants;
- expiry and replay protection;
- cryptographic key management;
- full schema-derived structural validation beyond the current graph prototype;
- generated-code or WASM sandboxing;
- compilation of the real box manifest into the generic host;
- multi-box discovery and agent composition;
- a cross-box effect/settlement protocol;
- persistent audit storage.
