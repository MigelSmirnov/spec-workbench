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

## Current vertical slice

`invoice.summary` accepts a project and optional date range. The trusted host
lowers that capability to a parameterized SQLite aggregate and returns only:

- `project_id`;
- `invoice_count`;
- `confirmed_total`;
- `currency`;
- execution evidence.

Unconfirmed invoices do not contribute. Requests outside the grant's project
scope fail closed.

## Run the demo

The YAML loader uses PyYAML when the CLI is used. Core host execution itself is
stdlib-only.

```bash
python tools/cabinet_host.py \
  experiments/cabinet-vault/cabinet_backend_invoice_summary.yaml \
  --project project-1
```

Run the focused tests with:

```bash
pytest -q tests/test_cabinet_host.py
```

## Security boundary under test

The key question is not whether an agent can generate SQL or Python. It is
whether a cabinet can expose enough machine-readable semantics for an agent to
compose useful work while the host retains authority over data access and
lowering.

For this spike, capability names are explicitly mapped to trusted lowerings.
Agent-supplied SQL is intentionally impossible.

## Not implemented yet

- signed grants;
- expiry and replay protection;
- cryptographic key management;
- generated-code or WASM sandboxing;
- schema-derived request validation;
- multi-cabinet composition;
- persistent audit storage.
