# Cabinet vault prototype

This experiment tests `CABINET_V0.md` with a minimal trusted runtime.

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

Run the graph demo with:

```bash
python tools/cabinet_graph_host.py \
  experiments/cabinet-vault/cabinet_backend_execution_graph.yaml
```

Run focused tests with:

```bash
pytest -q tests/test_cabinet_host.py tests/test_cabinet_graph_host.py
```

## Security boundary under test

The key question is not whether an agent can generate SQL or Python. It is
whether a cabinet can expose enough machine-readable semantics for an agent to
compose useful work while the host retains authority over data access and
lowering.

The second spike deliberately separates **composition authority** from **data
authority**:

- the agent chooses a graph of granted operations;
- the host validates graph references, capability grants and resource scope;
- the host executes trusted lowerings locally;
- opaque intermediates stay inside the cabinet;
- only a declared public result crosses the boundary;
- audit evidence records the graph digest and per-node trace.

Agent-supplied SQL is intentionally impossible.

## Not implemented yet

- signed grants;
- expiry and replay protection;
- cryptographic key management;
- static graph type-checking against declared input/output schemas;
- generated-code or WASM sandboxing;
- schema-derived request validation;
- multi-cabinet composition;
- persistent audit storage.
