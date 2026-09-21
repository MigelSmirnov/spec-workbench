# State 5 repair — complete Holded publication public operations

## Refined — `public_op:holded_publication.request_holded_publication`

Owner: `module:holded_publication`.

Through the cohesive service, locks the exact revision binding, returns an
equivalent existing publication or commits one logical publication before the
sole gateway create. Success requires complete read-back business verification.

## Refined — `public_op:holded_publication.reconcile_holded_publication`

Owner: `module:holded_publication`.

Locks/reloads an unresolved publication, resolves its exact archived revision,
uses only read-only gateway recovery, and persists the verified or still-unresolved
result without repeating create.

## `public_op:holded_publication.get_holded_publication_status`

### Owner
`module:holded_publication`

### Callers
Authorized local protected-operation adapters.

### Inputs
Exact `publication_id`.

### Outputs
The exact PostgreSQL-authoritative logical `HoldedPublication`.

### Observable effect
Read-only status observation of the logical publication.

### Enforces
PostgreSQL-authoritative truth: technical gateway evidence cannot substitute for the persisted logical publication state.

### Errors
`HoldedPublicationNotFoundError` for an unknown `publication_id`.

### State impact
None.
