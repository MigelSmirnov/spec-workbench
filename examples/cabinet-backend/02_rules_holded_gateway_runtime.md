# State 2 repair — Holded gateway runtime lowering

## Accepted decision — concrete local Holded gateway

The first implementation uses one Backend-owned HTTPS client and the shared Cabinet PostgreSQL deployment for durable technical attempt evidence.

- The Holded API key is read only by bootstrap from `CABINET_HOLDED_API_KEY` and is supplied directly to the concrete HTTP client.
- The base URL is the configured `CABINET_HOLDED_BASE_URL`; startup requires an absolute HTTPS URL and rejects embedded credentials, fragments, or non-HTTPS schemes.
- Request timeout, response byte limit, recovery page limit, and recovery polling bounds are positive finite configuration values.
- The HTTP client never retries POST. Transport-library automatic mutation retries and redirects that can replay POST are disabled.
- Before create, the gateway repository durably reserves the exact publication-attempt identity, payload hash, and marker. An existing equivalent reservation is reused; a conflict is rejected before network mutation.
- One reserved logical attempt permits at most one issued automatic POST. An ambiguous result is persisted and can only enter read-only recovery.
- List and GET are read-only. Recovery is bounded, filters for an exact marker, and returns technical evidence; it does not decide business success.
- Every response is size-bounded before parsing. Malformed, oversized, credential, timeout, TLS, remote rejection, and ambiguous outcomes become secret-free typed evidence.
- The API key, authorization header, database URL, raw request headers, and reusable credential material are never logged, persisted, or returned.
- PostgreSQL stores immutable attempt and lookup observations. It does not own publication eligibility or interpret Holded accounting status.
- Bootstrap fails closed when configuration, TLS/URL validation, database connectivity, or client/repository construction fails. There is no in-memory or anonymous fallback.

## Concurrency and recovery

PostgreSQL uniqueness and row locking on `publication_attempt_id` authorize the single-create transition. Process memory and check-then-POST observations are not an authority boundary.

A process interruption after issuing POST but before recording a response is classified as ambiguous on restart. It never authorizes a second automatic POST.

## Ownership

`module:holded_gateway` owns protocol and technical evidence. `module:holded_publication` continues to own Cabinet eligibility, full A51 verification, logical settlement, and manual decisions.
