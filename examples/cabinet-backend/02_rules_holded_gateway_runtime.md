# State 2 repair — Holded gateway runtime lowering

## Accepted decision A71 — concrete local Holded gateway

The first implementation uses one Backend-owned HTTPS client and the shared Cabinet PostgreSQL deployment for durable technical attempt evidence.

- The dedicated Holded Invoicing v1 key is read only by bootstrap from
  `HOLDED_V1_API_KEY` and supplied directly to the concrete HTTP client.
- The verified origin, credential header, purchase paths and codecs are closed
  by `rules.holded_transport_backend`; they are not deployment guesses.
- Request timeout, response byte limit, and recovery page bound are positive finite configuration values.
- The HTTP client never retries POST. Transport-library mutation retries and redirects that can replay POST are disabled.
- Before create, the repository durably reserves the exact attempt identity, payload hash, and marker. An equivalent reservation is reused; a conflict is rejected before mutation.
- One reserved attempt permits at most one issued automatic POST. An ambiguous result can only enter read-only recovery.
- List and GET are read-only. Recovery is bounded and filters for the exact marker.
- The gateway returns a typed observed Holded document; it does not compare that document with Card truth. A51 business verification remains owned by `module:holded_publication`.
- Every response is size-bounded before parsing. Malformed, oversized, credential, timeout, TLS, rejection, and ambiguous outcomes become secret-free typed evidence.
- API keys, authorization headers, database URLs, raw request headers, and reusable credential material are never logged, persisted, or returned.
- PostgreSQL stores immutable technical attempts and lookup observations. It does not own publication eligibility or accounting-status meaning.
- Bootstrap fails closed when configuration, URL/TLS validation, database connectivity, or adapter construction fails. There is no in-memory or anonymous fallback.

### Concurrency and crash recovery

PostgreSQL uniqueness and row locking on `publication_attempt_id` authorize the single-create transition. Process memory and check-then-POST observations are not authority.

A process interruption after the issued transition but before a response is recorded is ambiguous on restart and never authorizes a second automatic POST.

### Ownership

`module:holded_gateway` owns protocol and technical evidence. `module:holded_publication` owns eligibility, complete A51 comparison, logical settlement, and manual decisions.
