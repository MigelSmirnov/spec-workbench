# PostgreSQL persistence strategy

## Decision

Hydraulic Diagram Service uses PostgreSQL as its primary database.

The initial persistence stack is:

```text
PostgreSQL
SQLAlchemy 2.x
Alembic
Pydantic domain and boundary models
```

Pydantic models remain independent from SQLAlchemy ORM models.

Repository adapters translate between domain models and persistence records.

---

# 1. Why PostgreSQL

PostgreSQL is selected because the service requires:

- atomic revision commits;
- optimistic concurrency;
- versioned catalog records;
- immutable revision history;
- several concurrent clients;
- relational indexes and constraints;
- JSONB support for validated Pydantic snapshots;
- future support for tenancy, auditing, partitioning, and service integrations.

SQLite is not selected for the backend microservice because the service is expected to support concurrent editor, agent, and estimator access.

---

# 2. Storage model

The initial design uses a hybrid relational and JSONB strategy.

Relational columns store identifiers, lifecycle state, lookup fields, version numbers, timestamps, and references used for indexing and constraints.

Validated Pydantic documents may be stored as JSONB when the record is naturally an immutable snapshot or versioned document.

## Initial table groups

```text
diagrams
diagram_revisions
element_definitions
connection_type_definitions
diagram_change_requests
```

Additional operational tables may be added later for:

```text
idempotency records
outbox events
server-held working drafts
service audit records
```

These are not assumed until their workflows are specified.

---

# 3. `diagrams`

Purpose:

- stores stable diagram identity and lifecycle metadata;
- points to the current immutable revision;
- supports discovery by `object_id`.

Candidate columns:

```text
id UUID or string primary key
object_id indexed string
name string
system_kind string enum value
status string enum value
current_revision integer
created_at timestamptz
updated_at timestamptz
created_by_actor_type string
created_by_actor_id string
created_by_label nullable string
```

Constraints:

- `current_revision >= 0`;
- status and system-kind values match domain enums;
- `object_id` is required;
- timestamps use UTC-aware values;
- the row is small and does not contain the full diagram document.

---

# 4. `diagram_revisions`

Purpose:

- stores immutable revision snapshots;
- supports exact historical reconstruction;
- provides the deterministic source for estimation-data collection.

Candidate columns:

```text
diagram_id foreign key
revision integer
schema_version integer
snapshot JSONB
created_at timestamptz
created_by JSONB or normalized actor columns
change_source string
change_summary nullable string
```

Primary key:

```text
(diagram_id, revision)
```

Snapshot content:

```text
elements
connections
layout
revision metadata required by the Pydantic DiagramRevision schema
```

Rules:

- revision rows are append-only;
- normal application APIs never update revision snapshots;
- normal application APIs never delete individual revision rows;
- every snapshot is validated as `DiagramRevision` before persistence;
- every loaded snapshot is validated before entering domain logic;
- snapshot JSONB is not accepted directly from a transport without Pydantic validation.

## Atomic commit

One transaction must:

1. lock or conditionally update the target diagram row;
2. verify `expected_current_revision`;
3. insert the new immutable revision;
4. update `diagrams.current_revision`;
5. commit both changes atomically.

A failed step rolls back the whole transaction.

---

# 5. Catalog definition storage

Element and connection definitions use versioned records.

Candidate tables:

```text
element_definitions
connection_type_definitions
```

Candidate columns:

```text
id
version
code
status
scope
scope_ref nullable
created_at
created_by
payload JSONB
```

Primary key:

```text
(id, version)
```

Rules:

- active versions are immutable;
- semantic changes create a new version;
- indexed columns support visibility and lifecycle queries;
- complete Pydantic definition content is stored in validated JSONB payload;
- historical definition versions remain available to historical diagram revisions;
- deprecation does not delete historical records.

---

# 6. Change-request storage

If included in v1, `diagram_change_requests` stores:

```text
id
 diagram_id
base_revision
status
requested_by
payload JSONB
resulting_revision nullable
created_at
updated_at
```

The JSONB payload must validate as `DiagramChangeRequest`.

Lifecycle transitions remain domain behavior, not database-trigger behavior.

---

# 7. SQLAlchemy boundary

## Domain separation

Core Pydantic models must not contain:

- SQLAlchemy `Mapped` fields;
- sessions;
- lazy-loaded relationships;
- table names;
- database-generated proxy objects;
- persistence-only state.

## ORM records

SQLAlchemy models represent tables and storage concerns.

Repository adapters perform explicit conversion:

```text
SQLAlchemy row
→ Pydantic model validation
→ domain model
```

and:

```text
Pydantic model
→ canonical serialization
→ SQLAlchemy row or JSONB payload
```

Do not rely on implicit ORM serialization of domain models.

## Sessions

- sessions are created and owned by infrastructure/application transaction boundaries;
- domain functions never receive a SQLAlchemy session;
- repository methods must not leave transactions open;
- request handlers must not enter `idle in transaction` state.

---

# 8. Alembic migrations

Alembic owns schema evolution.

Rules:

- application startup must not silently create or mutate production tables;
- migrations are explicit versioned artifacts;
- destructive migrations require explicit operational review;
- schema migrations and Pydantic `schema_version` migrations are related but separate concerns;
- historical JSONB snapshots may require application-level migration readers rather than destructive rewrite.

---

# 9. MVCC and disk-space behavior

PostgreSQL uses MVCC. `UPDATE` and `DELETE` normally create dead tuples rather than immediately shrinking relation files.

Expected behavior:

```text
data is deleted or updated
→ old tuple versions become reclaimable
→ VACUUM marks space reusable by PostgreSQL
→ operating-system file size may remain unchanged
```

This is not treated as an application bug when the space is reusable by the table.

## Autovacuum

Policy:

- autovacuum must remain enabled;
- the application must not disable autovacuum;
- default tuning is used initially;
- table-specific tuning is introduced only from observed metrics.

## `VACUUM FULL`

Policy:

- application code must never run `VACUUM FULL`;
- `VACUUM FULL` is not routine cleanup;
- it is an administrative operation because it rewrites and locks the table;
- it may require substantial temporary free disk space.

## Regular `VACUUM`

- normal vacuuming is expected to be handled by autovacuum;
- manual vacuum may be an operational action after unusual bulk maintenance;
- business workflows do not call vacuum commands.

---

# 10. Long-transaction policy

Long-running transactions may prevent PostgreSQL from reclaiming dead tuples.

The service must avoid:

- forgotten open transactions;
- database connections left `idle in transaction`;
- network or agent calls while a database transaction is open;
- large estimation computations inside a persistence transaction;
- HTTP streaming while holding database locks;
- retries that reuse a failed transaction without rollback.

Recommended transaction shape:

```text
load required data
close read transaction where possible
perform pure domain computation
open short write transaction
verify concurrency and persist atomically
commit
```

Revision commit is the main intentional write transaction.

---

# 11. Delete and retention policy

## Revisions

Initial rule:

- committed revisions are retained;
- application APIs do not delete individual historical revisions.

This avoids high-churn deletes in the largest table.

A future retention policy may:

- archive old revisions;
- retain all published revisions and compact intermediate drafts;
- move old snapshots to cheaper storage;
- partition revisions by time or another operational key.

No retention behavior is invented in v1.

## Diagrams

Archiving is preferred over hard deletion.

Hard deletion, if introduced later, must define:

- authorization;
- cascade behavior;
- revision retention;
- catalog-reference impact;
- audit retention;
- object-card relationship;
- estimator reproducibility impact.

## Temporary tables

For operational tables whose entire contents are intentionally cleared, infrastructure may use `TRUNCATE` when semantics and locking are appropriate.

Domain repositories must not choose `TRUNCATE` as a generic delete implementation.

---

# 12. Future partitioning

Partitioning is not required for v1.

It becomes a candidate when `diagram_revisions` grows enough that:

- retention operations become expensive;
- indexes become operationally heavy;
- backup/restore windows become problematic;
- old revisions need different storage policies.

Partitioning key must be selected from real access and retention patterns.

Do not introduce monthly partitions merely by habit if revisions are primarily queried by `diagram_id`.

---

# 13. Index candidates

Initial candidates:

```text
diagrams(object_id)
diagrams(status)
diagrams(updated_at)

diagram_revisions(diagram_id, revision)
diagram_revisions(created_at)

element_definitions(code)
element_definitions(status, scope, scope_ref)
connection_type_definitions(code)
connection_type_definitions(status, scope, scope_ref)

diagram_change_requests(diagram_id, status)
```

JSONB GIN indexes are not added by default.

They should be added only for proven queries into snapshot or definition payload fields.

---

# 14. Monitoring requirements

Operational monitoring should include:

```text
database size
table and index size
dead tuple estimates
last autovacuum and autoanalyze times
long-running transactions
idle-in-transaction connections
lock waits
connection-pool usage
query latency
revision growth rate
```

The application may expose health and metrics endpoints, but it must not implement database maintenance logic.

---

# 15. Config candidates

Future `config` fields:

```text
database.url_env_name
database.pool_size
database.max_overflow
database.pool_timeout_seconds
database.statement_timeout_seconds
database.connect_timeout_seconds
database.object_verification_enabled
```

Secrets and full connection URLs are environment/runtime inputs, not values committed into `global_spec.json`.

Autovacuum is a database operational requirement, not an application config toggle.

---

# 16. Repository generation units

Candidate structure:

```text
src/hydraulic_diagram/infrastructure/persistence/
    __init__.py
    database.py
    orm_models.py
    serializers.py
    diagram_repository.py
    revision_repository.py
    catalog_repository.py
    change_request_repository.py
    unit_of_work.py
```

Responsibilities:

- `database.py`: engine and session factory;
- `orm_models.py`: SQLAlchemy table mappings;
- `serializers.py`: Pydantic/JSONB conversion helpers;
- individual repository files: domain-specific queries;
- `unit_of_work.py`: short transaction ownership.

Do not generate one mega persistence file.

---

# 17. Global-spec implications

The future `global_spec.json` should include:

- PostgreSQL and SQLAlchemy imports in persistence generation units only;
- Pydantic models independent from persistence imports;
- repository protocols separated from SQLAlchemy implementations;
- explicit revision atomicity notes;
- explicit JSONB snapshot validation notes;
- explicit no-direct-database-access notes for HTTP and MCP;
- explicit prohibition on `VACUUM FULL` and maintenance SQL in application behavior;
- explicit short-transaction and rollback requirements;
- module paths for each repository generation unit;
- Alembic as migration tooling, not runtime domain behavior.

---

# 18. Placeholder resistance

Reject:

```text
save_json(data: dict)
```

Reject:

```text
DatabaseManager
```

Reject domain models that inherit from SQLAlchemy bases.

Reject direct JSONB writes from transport payloads without Pydantic validation.

Reject generic delete behavior that assumes disk files shrink immediately.

Reject application code that runs vacuum commands after deletes.

Reject transactions that remain open during LLM, MCP, Object Card, or estimator network calls.

---

## Decision summary

The persistence decision is now stable enough for contract design:

```text
PostgreSQL
SQLAlchemy 2.x adapters
Alembic migrations
Pydantic domain models
append-only immutable diagram revisions
validated JSONB snapshots
versioned catalog JSONB documents
short atomic transactions
autovacuum enabled
no routine VACUUM FULL
```
