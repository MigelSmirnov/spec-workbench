# State 2 — Holded runtime boundary

## Accepted decision A71 — Holded transport and attempt persistence are explicit startup dependencies

### Normative rules

1. `module:holded_gateway` receives a `HoldedHttpClient` and
   `HoldedGatewayRepository` explicitly.
2. The concrete client is constructed at startup from a required HTTPS base URL,
   API credential, connect timeout, read timeout, and bounded recovery polling
   configuration.
3. Missing credentials, non-HTTPS base URL, invalid timeout bounds, or client
   construction failure prevents application startup.
4. Credentials remain inside the concrete client. They never appear in domain
   models, returned evidence, exception text, URLs, or logs.
5. The repository commits attempt-start evidence before the client may issue the
   one allowed POST.
6. An existing started or terminal attempt prevents another automatic POST for
   the same `publication_attempt_id`.
7. Transport timeout, connection loss, malformed response, or response loss is
   recorded as an ambiguous technical outcome; the gateway does not retry POST.
8. Lookup performs bounded read-only list/GET calls and never mutates Holded.
9. Provider errors are translated into safe stable error codes while raw secret
   material and authorization headers are discarded.

### Formal invariants

```text
one publication_attempt_id -> at most one automatic Holded POST
attempt_start_commit < Holded POST
Holded credential outside concrete client = false
lookup_may_mutate_Holded = false
startup_with_invalid_Holded_configuration = refused
```

### Required tests

1. A committed existing attempt prevents a second POST.
2. Repository failure before POST produces no HTTP mutation.
3. A timeout after request delivery records ambiguity and produces no retry.
4. Lookup uses only read operations and terminates at configured bounds.
5. Credential and authorization headers are absent from logs and evidence.
6. Startup fails for missing credential, non-HTTPS URL, or invalid timeout.

### Consequence

Holded business policy remains in publication/gateway modules; concrete adapters
own only PostgreSQL evidence persistence and authenticated HTTPS mechanics.

---
