# Platform manifest external-contract evidence — 2026-09-20

## Evidence boundary

This is a sanitized structural observation of the Factory repository's
`platform/manifest/` directory at immutable Git revision
`b25b523358b3371f81ced7c1ad78dc6f5feb8af3`. It records no credential value,
customer fact or service payload. The latest commit touching the observed
directory was `a2ede63edea6551e46f90759699069587f633c87`.

The directory README and all six JSON service records present at that revision
were inspected. Their exact-byte SHA-256 fingerprints were retained during the
review; the normative Cabinet Flow contract binds to the structural facts in
`rules.platform_manifest_contract`, not to the sample service identities.

## Observed record envelope

Each service is one UTF-8 JSON file named `<service>.json`. Every observed
record contains these top-level fields:

- `service`, `display_name`, `origin`, `declared_at`, `declared_because`;
- `surface_sources`;
- `instances`, an object keyed by instance identity;
- `capabilities`, an array;
- `known_defects`.

Some records also contain descriptive fields such as `not_declared`,
`transport_rules` or `identity_rule`. No record declares an explicit manifest
schema-version field.

## Observed capability contract

Every observed capability contains `name`, `exposed_as`, `effect_class`,
`idempotency_key`, `replay` and `preconditions`.

- `exposed_as` is an object keyed by channel. Its channel value is either one
  operation string or a non-empty list of operation strings.
- The README names the channels `mcp`, `http_api` and `operator`.
- The README defines effect classes `read`, `draft-write`, `state-transition`,
  `external-effect` and `destructive`.
- The README defines replay values `safe`, `refuses`, `returns_existing`,
  `overwrites` and `duplicates`.
- `idempotency_key` is either a string or `null`. Observed strings include both
  simple field-like text and prose/composite expressions. Neither the README
  nor the records define a grammar that maps these strings to typed ports.
- `preconditions` is an array of strings.
- Optional fields include `models`, `note` and `gap`. `note` is not required
  and no source identifies it as an owner-facing binding purpose.

## Observed instance contract

An instance object has a required `class` in every observed instance. Depending
on the service, it may also contain `api_base_url`, `required_headers`, health,
state, settings, start, working, dependency or expectation facts.

`required_headers` contains header names, not values. No observed instance has
a credential-binding reference. The only concrete network base-address field
is `api_base_url`; no instance-level MCP or operator endpoint mapping is
declared.

## Facts not supplied by the external source

The inspected README, records and manifest-related Factory tooling do not
define:

- a manifest-record digest recipe;
- lookup of a prior record from a digest;
- a grammar for interpreting `idempotency_key` as typed input ports;
- credential-binding references;
- a mandatory capability purpose;
- an instance-level endpoint for `mcp` or `operator`.

Cabinet Flow therefore closes these seams conservatively in A31: exact-file
SHA-256, same-path ancestor history, opaque idempotency text with fail-closed
port mapping, installation-owned credentials, optional non-normative notes and
no inferred endpoints.

## Review result

Result: the legacy manifest format is usable as a revision-pinned, read-only
external contract only with the fail-closed interpretation above. Any source
shape change requires new content-addressed evidence and an explicit contract
revision; it is not accepted by permissive parsing.
