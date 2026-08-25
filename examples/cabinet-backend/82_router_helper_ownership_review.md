# Cabinet Backend — deterministic router helper ownership review

## Scope

Route B for accepted specification `8fc78cab` generated the models and nine
domain/adapter modules, then the deterministic `http_router_backend/v1` gate
reported that `api` owned `resolve_local_principal` without emitting it.

The router backend emits its app factory, credential extractors, table handlers,
and projections. A principal resolver may be referenced by the router IR but is
not one of those emitted categories. The IR validator explicitly permits such a
resolver to be directly imported by the router module.

## Ownership repair

- `resolve_local_principal` moves from `module:api` to
  `module:api_irregular`;
- `api` imports the resolver directly from `api_irregular`;
- its contract, notes, signature, and access-control dependency are unchanged;
- `api` continues to own every function deterministically emitted by
  `http_router_backend/v1`;
- `api_irregular` remains a transport adapter and does not acquire
  authentication or authorization policy.

## Adversarial review

The resolver still delegates the supplied credential to `AccessControlBackend`
and propagates `AuthenticationRequiredError`. Moving its physical declaration
does not change who validates credentials, who decides authorization, the
principal type returned to protected handlers, route behavior, or public API
surface.

The resulting ownership boundary is closed: the deterministic router imports a
non-emitted helper, while the irregular companion owns the helper's concrete
behavior and its multipart handler.

## Result

- `api_irregular`: `PASS_INTERNAL_VARIATION`;
- `api`: `PASS`;
- affected dependency closure (`bootstrap`): unchanged.
