# State 2 — Runtime persistence boundaries

## Accepted decision A70 — Registry context uses the shared PostgreSQL transaction mechanism

Registry catalogue observations, WorkObjects, and assignment validations are
durable Cabinet state. They must survive process restart and must not depend on
module globals or hidden database connections.

### Normative rules

1. `module:registry_context` receives a `RegistryContextRepository` explicitly.
2. The concrete repository is constructed during Backend startup from required
   PostgreSQL configuration; business modules do not read environment variables.
3. One complete catalogue refresh is committed atomically: all accepted project
   snapshots and resulting WorkObjects become visible together, or none do.
4. Concurrent refreshes serialize at the repository transaction boundary.
   A stale refresh must not overwrite a newer committed Registry observation.
5. Assignment validations are immutable append-only evidence. An identity
   collision with different evidence is a conflict, never an update.
6. Reads observe committed state only and never fabricate missing WorkObjects,
   snapshots, or validations.
7. Missing or invalid PostgreSQL configuration, migration failure, or inability
   to establish the runtime repository prevents application startup.
8. Logs and errors may contain safe record identifiers but never database
   credentials or connection strings.

### Formal invariants

```text
visible_registry_refresh = all_accepted_rows | no_new_rows
business_module_opens_database_connection = false
assignment_validation_history_is_append_only = true
startup_without_required_registry_repository = refused
```

### Required tests

1. A failure while applying a refresh leaves the previous committed catalogue
   and WorkObjects unchanged.
2. Two concurrent refreshes cannot expose a mixed observation.
3. A later committed observation is not replaced by a stale observation.
4. Restarting the application preserves WorkObjects and validation evidence.
5. A read for absent evidence returns absence to the domain function; the domain
   function emits its accepted not-found error.
6. Startup fails before serving requests when the repository cannot be created.
7. No logged failure reveals PostgreSQL credentials.

### Consequence

Registry business policy remains in `module:registry_context`; the repository
owns only PostgreSQL persistence, transaction isolation, and committed reads.

---
