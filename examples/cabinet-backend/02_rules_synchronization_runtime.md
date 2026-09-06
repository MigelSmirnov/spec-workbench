# State 2 repair — synchronization runtime lowering

## Accepted decision A72 — concrete local VPS synchronization runtime

The first implementation uses one Backend-initiated HTTPS client and the shared
Cabinet PostgreSQL deployment for synchronization state and evidence.

### Normative rules

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

### Formal invariants

```text
network_mutation -> durable_reservation_first
equivalent_retry -> same_durable_identity
issued_without_conclusive_response -> unknown_outcome AND read_only_reconciliation
connection_observation -/> synchronized_or_accepted_state
secret_material -/> logs_or_business_evidence
```

### Required tests

1. A network mutation without a prior durable reservation is impossible.
   [witness: verification:semantic_flow6_synchronization]
2. Equivalent retries reuse the reserved identity; conflicting reuse is
   rejected before transport.
3. An issued request without a conclusive response becomes unknown_outcome and
   proceeds only through read-only reconciliation.
4. Catalogue publication follows the same reserve, issue, and reconcile
   discipline over an exact ordered snapshot.
5. Startup fails closed on a missing credential, an invalid HTTPS URL, or
   database failure.

### Ownership

`synchronization` owns transport state, idempotency, reconciliation, catalogue
delivery, and connection observations. `durable_archive` alone owns local
acceptance; `registry_context` alone owns catalogue contents.

### Consequence

The local node can crash, retry, and reconnect without ever duplicating a
logical transfer or fabricating acceptance; every mutation is anchored to a
durable identity before it touches the wire.
