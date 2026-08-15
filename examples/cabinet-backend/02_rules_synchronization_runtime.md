# State 2 repair — synchronization runtime lowering

## Accepted decision A72 — concrete local VPS synchronization runtime

The first implementation uses one Backend-initiated HTTPS client and the shared
Cabinet PostgreSQL deployment for synchronization state and evidence.

- Bootstrap reads the dedicated node credential only from
  `CABINET_SYNC_NODE_CREDENTIAL` and supplies it directly to the transport.
- Bootstrap reads `CABINET_VPS_BASE_URL`; startup requires an absolute HTTPS URL
  without embedded credentials or fragments.
- Timeout and maximum response size are positive finite configured values.
- The transport is outbound-only, verifies TLS, bounds bytes before parsing,
  disables redirects or retries that can replay a mutation, and returns typed
  evidence with secret-free failures.
- PostgreSQL durably reserves synchronization/publication identity,
  idempotency-key, and content hash before network mutation.
- Equivalent retries reuse the same durable identity. Conflicting reuse is
  rejected before transport.
- An issued request without a conclusive response becomes `unknown_outcome` and
  can proceed only through read-only reconciliation; it never authorizes a
  second logical transfer.
- Catalogue publication uses an exact ordered snapshot and the same durable
  reserve/issue/reconcile discipline.
- Connection observation is read-only and cannot fabricate synchronized,
  authenticated, or durable-acceptance state.
- Credentials, authorization headers, database URLs, and raw unbounded bodies
  are never logged, persisted as business evidence, or returned.
- Bootstrap fails closed on missing configuration, invalid HTTPS settings,
  database failure, or adapter construction. There is no anonymous, in-memory,
  or service-locator fallback.

### Ownership

`synchronization` owns transport state, idempotency, reconciliation, catalogue
delivery, and connection observations. `durable_archive` alone owns local
acceptance; `registry_context` alone owns catalogue contents.
