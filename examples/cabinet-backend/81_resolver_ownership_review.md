# Stage 8.1 re-review — principal resolver ownership

## Why this review exists

`resolve_local_principal` was owned by `module:api`. The Factory's
`http_router_backend/v1` emitter refused the module: its deterministic draft
does not cover an owned principal resolver, so generation stopped with
`missing contract function: resolve_local_principal`.

The Factory's own IR validator (`tools/http_router_ir.py`) accepts a resolver
that is either owned or directly imported by the router module, so the emitter
and the validator disagree. Rather than widen the emitter, this case moves the
resolver to the module that the specification standard already implies.

## Change

- `module_functions`: `resolve_local_principal` moves from `api` to
  `access_control`.
- `imports.module_internal.api.access_control`: gains `resolve_local_principal`,
  so the router imports it directly.
- `60_contract_plan.json`: the ownership record follows.
- `30_modules_access_control_backend.md`: the public surface is widened
  explicitly and the reasoning is recorded.

The contract signature is unchanged:
`(access_control: AccessControlBackend, credential: str) -> AuthenticatedPrincipalContext`.

## Adversarial review

**Is the new owner correct?** Yes. SPEC_STANDARD §6.1 requires a thin router.
Establishing identity from a credential is an access-control decision, not
transport. The resolver is a free function over the abstract
`AccessControlBackend`, structurally identical to `authorize_operation`, which
already lives in this module.

**Does `access_control` now own something it must not?** No. Its "Must not own"
list forbids HTTP/MCP request parsing and route policy. The resolver receives an
already-extracted credential string; `extract_bearer_credential` stays in `api`
and remains the only function that touches the HTTP request.

**Does the widened public surface contradict State 3?** It did, and the document
is corrected rather than bypassed: the surface now names three symbols instead
of two. The concrete `PostgresAccessControlBackend` is still withheld from
runtime consumers, which was the constraint that sentence protected.

**Do the resolver's notes survive the move?** Yes. Both notes travel with the
function and remain coherent with their new neighbours: the SECURITY_BOUNDARY
note requires resolution through the access-control backend, and the
VALIDATION_ERROR note propagates `AuthenticationRequiredError`, which
`access_control` owns and already exports. `api` continues to import that
exception for its error policy.

**Does the router still resolve?** Yes. `rules.http_router_backend.principals.
local_actor.resolver` is unchanged; the validator's `owned | direct_imports`
test is now satisfied through the direct import instead of ownership.

**Models.** No new model imports are needed. `access_control` already imported
`AuthenticatedPrincipalContext`.

## Deterministic review

```text
access_control  10 contracts; 20 notes; 0 blocks; 0 review prompts
api             14 contracts; 22 notes; 0 blocks; 0 review prompts
```

Both modules keep their prior verdict: PASS.
