# Deterministic API assembly standard

This document is a normative extension of `SPEC_STANDARD.md` for projects whose
HTTP `api` module is emitted by the deterministic backend rather than authored by
the LLM module generator.

The purpose is to keep transport assembly deterministic while preserving the
module-ownership rules of the main specification standard.

## 1. Ownership

`api` is a **compiler-owned boundary artifact**, not a project-owned application
module.

The project specification defines application behavior in owning modules. The
deterministic API emitter may assemble HTTP wiring, authentication/dependency
wiring, request decoding, provider invocation, and response/error translation.
It must not become a second owner of product policy.

Therefore a finalized specification MUST NOT declare `api` as an ordinary
project module:

- `module_functions.api` MUST be absent;
- `module_paths.api` MUST be absent;
- `api` MUST NOT appear in `module_order`;
- `default_module` MUST NOT be `api`;
- `imports.internal.api` MUST be absent;
- no project module may import symbols from provider `api` through
  `imports.module_internal`.

The deterministic emitter owns generated endpoint/helper symbol names. Those
symbols are compiler details and MUST NOT be materialized as project
`contracts`, `module_functions`, or notes merely to make HTTP assembly possible.

## 2. API exposure manifest

The only project-level dependency declaration reserved for deterministic HTTP
assembly is:

```json
"imports": {
  "module_internal": {
    "api": {
      "invoice_archive": ["get_invoice", "attach_source"],
      "publication": ["request_publication"]
    }
  }
}
```

`imports.module_internal["api"]` is an **exposure manifest**, not normal
project-module wiring. Each entry means that the deterministic HTTP boundary is
allowed to expose one existing public provider operation.

For every `provider -> symbol` entry:

1. `provider` MUST exist in `module_functions`;
2. `symbol` MUST belong to `module_functions[provider]`;
3. `symbol` MUST be present in `imports.internal[provider]`;
4. `symbol` MUST have a top-level function contract in `contracts`;
5. the symbol MUST NOT be a class, model, constant, private helper, or
   compiler-generated symbol;
6. duplicate symbols inside one provider exposure list are invalid.

`imports.internal[provider]` remains the provider's complete public module
surface. The API exposure manifest is a consumer-specific subset and MUST NOT be
filled by copying the whole provider surface "just in case".

Absence of `imports.module_internal.api` means that deterministic HTTP assembly
has no project operations to expose. It is not permission for the emitter to
publish every public function automatically.

## 3. Derivation boundary

The API emitter may derive transport code only from already accepted structural
facts:

- exposed provider symbol;
- its exact `contracts` signature;
- referenced declared models/types;
- deterministic backend conventions for HTTP/auth/request-response lowering.

The emitter MUST NOT derive or invent:

- business eligibility;
- authorization policy beyond invoking the accepted security owner;
- storage or persistence policy;
- domain validation not present in the provider contract/owner behavior;
- retries or idempotency semantics owned by application modules;
- new default values, thresholds, allow-lists, routing policy, or product
  decisions;
- extra provider calls that are not required by deterministic lowering.

If HTTP assembly requires a fact that cannot be derived uniquely from the
specification plus the deterministic backend version, assembly returns `DEFECT`.
It does not ask the LLM to complete the router by convention.

## 4. Dependency direction

The boundary direction is one-way:

```text
external HTTP caller
  -> deterministic api
  -> exposed provider operation
```

Application/domain modules MUST NOT depend on `api`.

The deterministic boundary may call only symbols listed in the exposure
manifest. It may not use the existence of an entity ID, a model, or a public
provider export as implicit permission to expose an operation.

## 5. Notes and project symbols

Because the generated `api` artifact has no project-owned functions, finalized
specifications MUST NOT contain module-level notes addressed to `api:`.
Transport behavior that is invariant for all projects belongs to the backend
standard/emitter. Product behavior belongs to the owning provider function or
module.

A requirement that appears to need an `api:` note must be classified before it
is accepted:

- business/security policy -> owning application/security module;
- request/response type shape -> provider contract or declared model;
- deterministic HTTP lowering -> backend standard, not project prose;
- project-specific transport policy that cannot be represented by the current
  DSL -> semantic gap / standard change, not an ad-hoc router note.

## 6. Validation gate

A spec is not ready for deterministic API assembly until all of the following
hold:

- `api` has no project module ownership declarations;
- every exposed API symbol resolves to exactly one public provider function;
- no project module depends on provider `api`;
- exposure lists contain no duplicate/private/non-callable symbols;
- the exposure set is explicit; no implicit "export all" behavior exists.

`tools/spec_api_lint.py` implements these structural checks. These checks are
normative admissibility checks, not semantic heuristics.

## 7. Relationship to State 5 design

State 5 public module APIs and deterministic HTTP exposure are separate layers.

State 5 decides the stable public operations of each owning module. Only after
those provider APIs are accepted may a subset be placed in
`imports.module_internal["api"]` for external HTTP exposure.

A State 5 operation does not become an HTTP endpoint merely because it is public
to other application modules. Internal cross-module operations may remain absent
from the API exposure manifest.

This same separation allows future deterministic MCP assembly to consume stable
provider APIs without moving business semantics into MCP transport wrappers.
