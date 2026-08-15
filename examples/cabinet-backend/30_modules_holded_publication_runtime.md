# State 3 repair — Holded publication runtime boundary

`holded_publication` exposes one `HoldedPublicationService` constructed with the
exact `HoldedPublicationRepository`, `DurableArchiveService`, and
`HoldedGatewayService`. The concrete repository is
`PostgresHoldedPublicationRepository`.

The service owns eligibility, exact revision binding, logical idempotency,
business verification, settlement/reconciliation, and status. It never accesses
HTTP, credentials, archive persistence, or environment configuration directly.

Bootstrap reuses the shared database and already constructed archive/gateway
services, constructs one publication service, and injects it into application
composition without fallback.
