# State 3 repair — Holded gateway runtime boundary

## Module: holded_gateway

The module provides `HoldedGatewayService` as its cohesive generated boundary.

Depends on:

- `HoldedHttpClient`, a narrow create/list/GET transport port;
- `HoldedAttemptRepository`, a narrow PostgreSQL technical-evidence port.

Concrete local implementations are separated by mechanism:

- `module:holded_transport` owns deterministic `HttpxHoldedHttpClient`;
- `module:holded_gateway` owns `PostgresHoldedAttemptRepository` and the
  cohesive gateway orchestration.

The transport owns exact Holded v1 request paths, wire codecs, bounded response
parsing and secret redaction. The gateway owns single-create enforcement,
transport classification, and immutable technical attempt/lookup evidence.

It must not own Cabinet publication eligibility, choose an Invoice Card revision, perform A51 business settlement, read environment variables, or silently retry a mutation.

## Module: bootstrap

Bootstrap reads the declared Holded configuration, validates it, constructs the concrete HTTP client and PostgreSQL repository, constructs one `HoldedGatewayService`, and supplies it to application composition. Startup fails closed on missing or invalid configuration.

## Dependency rule

`holded_publication` receives the cohesive `HoldedGatewayService` explicitly. No module globals, service locators, ad-hoc HTTP clients, direct environment reads, or direct repository access are permitted.
