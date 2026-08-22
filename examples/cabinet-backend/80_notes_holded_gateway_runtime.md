# State 7 repair — Holded gateway runtime notes

## HoldedGatewayService

- Constructor [DEPENDENCY_BOUNDARY]: require the exact supplied repository and HTTP client; never construct adapters, read environment variables, or use nullable/global fallbacks.
- create_holded_purchase [ORCHESTRATION]: under the attempt lock, reuse an equivalent durable reservation or reject a conflicting identity, commit the reservation before network mutation, and atomically mark the request issued before performing the sole permitted POST.
- create_holded_purchase [BEHAVIOR]: never issue POST when the attempt already records issued, ambiguous, or terminal evidence; equivalent re-entry returns the existing evidence without mutation.
- create_holded_purchase [FALLBACK]: classify timeout, connection loss, response loss, or interruption after issuance as ambiguous and append secret-free evidence; never retry POST.
- create_holded_purchase [SECURITY_BOUNDARY]: hash and compare canonical payload evidence without persisting credentials or authorization headers.
- lookup_holded_purchase [ORCHESTRATION]: use GET for a supplied document id or one bounded Holded v1 list response for an exact marker, then return typed observation evidence without mutation.
- lookup_holded_purchase [BEHAVIOR]: preserve zero, one, and multiple exact matches, malformed responses, unknown documents, and transport failures distinctly; do not perform A51 business settlement or interpret raw status.
- lookup_holded_purchase [DETERMINISM_OR_ORDERING]: process candidates in stable document-id order; one invocation performs at most one list request, while later explicit reconciliation may repeat the read without authorizing POST.

## PostgreSQL repository

- Transaction methods [DEPENDENCY_BOUNDARY]: use one PostgreSQL transaction per state transition and acquire the exact attempt row/uniqueness lock before deciding whether POST may be issued.
- reserve_attempt [BEHAVIOR]: return an existing reservation only when attempt identity, payload hash, and marker are exactly equivalent; reject conflicts.
- Evidence methods [BEHAVIOR]: append immutable technical observations and reject skipped, repeated-mutation, stale, or conflicting lifecycle transitions.
- Constructor [SECURITY_BOUNDARY]: treat the database URL as secret and never log it.

## HTTP client

- Constructor [VALIDATION_ERROR]: require the verified Holded v1 HTTPS origin, non-empty API key, and positive finite timeout/response-size bounds.
- create_purchase [FORBIDDEN_ACTION]: issue exactly one POST per invocation with transport retries and replaying redirects disabled.
- list_purchases [BEHAVIOR]: perform one read-only bounded `GET /api/invoicing/v1/documents/purchase`, decode the array, and return typed summaries in stable document-id order.
- get_purchase [BEHAVIOR]: perform one read-only exact-document request.
- All operations [SECURITY_BOUNDARY]: keep `HOLDED_V1_API_KEY` only in the outbound `key` header, redact headers, enforce TLS verification, bound bytes before JSON parsing, disable redirects/retries, and return secret-free safe evidence according to `rules.holded_transport_backend`.

## Bootstrap

- create_local_app [CONFIG_REFERENCE]: read the V1 API key only from the environment variable named by `config.holded_runtime.credential_env`; the verified origin belongs to `rules.holded_transport_backend.protocol.origin`.
- create_local_app [ORCHESTRATION]: reuse the Cabinet database URL, construct the repository, HTTP client, and service, and bind the service before exposing FastAPI.
- create_local_app [VALIDATION_ERROR]: fail closed on missing/invalid Holded configuration or adapter construction; no disabled, anonymous, or in-memory fallback is permitted.
