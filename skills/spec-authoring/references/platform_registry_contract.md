# Platform Registry Integration Contract

## Purpose and authority

Use this reference when authoring a platform service that reads renovation
project data from `registry_sandbox` or stores data linked to a Registry
project.

This document is a conditional authoring profile for `spec-authoring`. It does
not extend the `global_spec.json` language, define Client Portal internals, or
replace inspection of the current Registry revision. Keep these categories
separate:

- **CONFIRMED** — behavior present in the inspected runtime and tests;
- **REQUIRED** — platform rule that a consuming specification must make
  explicit, even when Registry does not enforce it for the consumer;
- **CONDITIONAL** — rule that applies only when the product supports the named
  operating mode;
- **OPEN** — capability that must not be assumed.

If runtime code contradicts this reference, stop authoring and resolve the
contract drift. Do not make the generated consumer guess.

## Ownership boundary

### Current project identity and context

**CONFIRMED:** Registry owns the canonical identity and current context of a
renovation project:

- `project_id` is a UUID assigned by Registry;
- `display_name`, `address`, `status`, `customer_ref`, `created_at`, and
  `registry_updated_at` come from Registry;
- updating a project changes its mutable context without replacing its UUID;
- the currently implemented project statuses are the literal values `active`
  and `archived`.

**REQUIRED:** A consuming service must:

- accept or retain an existing `project_id`; it must not generate a Registry
  project UUID;
- treat the UUID, not a name or address, as project identity;
- obtain current project fields through Registry's public boundary;
- avoid direct access to the Registry database and direct imports of Registry
  persistence or domain classes;
- avoid duplicating Registry's project record as an independently editable
  source of current truth.

Registry's `customer_ref` is an optional reference in project context. It is
not a complete fiscal/customer record.

### Service-owned client data

**REQUIRED:** Each service remains the owner of client data required by its own
domain, such as fiscal name, NIF, email, telephone, invoice address, or billing
preferences. Registry linkage must not make that data mandatory in Registry
and must not overwrite it from `customer_ref`.

This permits, for example, an estimate to retain its own typed `Client` while
also retaining an optional Registry project snapshot. Name and address in the
project snapshot describe the renovation object; they do not replace the
estimate's client.

## Confirmed read boundary

The current public integration boundary is HTTP. The equivalent Python service
functions are implementation evidence, not a cross-service integration API.

### `GET /projects/active`

Returns `list[ProjectReference]` where:

```text
ProjectReference
  project_id: UUID
  display_name: str
  status: str
```

**CONFIRMED:** Every returned entry currently has `status == "active"`.

**OPEN:** No pagination, stable sorting, maximum result size, or incremental
cursor is currently guaranteed. A consumer must not invent those guarantees.
If its UX requires a particular order, the consumer owns and specifies that
presentation sort after decoding the typed response.

### `GET /projects/{project_id}/validate`

Returns `ProjectValidationResult`:

```text
ProjectValidationResult
  project_id: UUID
  exists: bool
  status: str | None
  is_active: bool
  failure: str | None
```

Confirmed results include:

| Condition | `exists` | `status` | `is_active` | `failure` |
| --- | ---: | --- | ---: | --- |
| active project | `true` | `"active"` | `true` | `None` |
| archived project | `true` | `"archived"` | `false` | `"archived"` |
| missing UUID | `false` | `None` | `false` | `"not_found"` |

A missing project is a successful HTTP response containing a negative typed
result; it is not a 404 from this operation.

### `GET /projects/{project_id}/context`

Returns `ProjectContext`:

```text
ProjectContext
  project: ProjectReference
  address: str
  customer_ref: str | None
  created_at: datetime
  registry_updated_at: datetime
```

The nested `ProjectReference` has the fields shown above. A missing project
produces HTTP 404. Context can currently be read for both active and archived
projects; consumers must not interpret successful context retrieval as
permission to create new linked data.

## Integration modes

### Registry-linked mode

**REQUIRED:** For a command that creates or newly links service-owned data to a
project, use this flow:

1. Accept `project_id: UUID` at the service boundary.
2. Reject any client-supplied Registry snapshot or project name/address as an
   authoritative value.
3. Call `/projects/{project_id}/validate` with a finite configured timeout.
4. Continue only when `exists` and `is_active` are both true and the returned
   `project_id` equals the requested UUID.
5. Fetch `/projects/{project_id}/context` server-side.
6. Verify the context UUID equals the requested UUID.
7. Perform the service-owned command using typed context or a typed snapshot.

The service boundary owns translation of Registry failures into its public
error model. Distinguish at least:

- invalid UUID input;
- missing project;
- existing but inactive/archived project;
- Registry timeout or transport failure;
- non-success HTTP response;
- response schema or identity mismatch.

Do not silently fall back to client-supplied context, cached arbitrary data, or
a fabricated success result.

### Standalone mode

**CONDITIONAL:** A service may operate without Registry when its domain permits
standalone records. This is a product decision, not an integration failure
fallback.

Specify the two modes explicitly:

- `project_id is None`: do not call Registry; keep all required service-owned
  client and document data;
- `project_id is not None`: execute the complete Registry-linked flow.

Do not make Registry availability mandatory for a standalone command, and do
not silently convert a failed linked command into standalone data.

## Live context and historical snapshots

Use live Registry context when the product needs the current project display
name, address, status, or customer reference.

Use an immutable typed snapshot when a service-owned document must preserve
what was used at creation, approval, publication, or another domain event. A
minimal snapshot contains:

```text
RegistryProjectSnapshot
  project_id: UUID
  display_name: str
  status: str
  address: str
  customer_ref: str | None
  registry_created_at: datetime
  registry_updated_at: datetime
  captured_at: datetime
```

Field names may follow the consuming domain's established vocabulary, but the
types and provenance must remain explicit. `captured_at` is service-owned;
`registry_updated_at` is Registry-owned. Do not collapse them into one generic
timestamp.

A snapshot is historical evidence, not a second current project record:

- Registry remains the owner of live name, address, status, and identity;
- renaming a Registry project does not rewrite an already published document;
- current screens may fetch live context separately from the historical
  snapshot;
- a later Registry failure must not mutate an existing historical snapshot.

If the domain needs no historical evidence, store only `project_id` and fetch
live context when required. Do not add snapshots by habit.

## Archived projects

**CONFIRMED:** Registry excludes archived projects from `/projects/active`,
reports them as inactive through `/validate`, and prevents adding Registry
rooms or publishing Registry artifacts to them. Registry still permits reading
their context.

**REQUIRED:** A consumer must reject commands that newly link or create active
work under a project when `is_active` is false. The consumer must decide and
specify separately whether historical records remain readable, exportable, or
otherwise usable after archival. Do not infer those lifecycle rules from a
successful context read.

Only `active` and `archived` are currently confirmed. `paused`, `completed`,
`cancelled`, or other normalized values are **OPEN** and must not appear as
Registry facts without a runtime contract change.

## Security and operational limits

**OPEN:** The current Registry HTTP boundary does not establish an
authentication or service-authorization contract. Absence of an auth check in
the sandbox is not permission to declare production access public.

For a local trusted pilot, a consuming specification may record the deployment
constraint explicitly. Before production use it must resolve, at minimum:

- service authentication and authorization;
- network exposure and TLS ownership;
- retry and backoff policy;
- request timeout values;
- observability and correlation identifiers;
- pagination or bounded-list behavior if project volume requires it;
- compatibility/versioning for the public response models.

Keep configurable URLs, timeouts, and retry limits in `config`; keep access
policy in the owning security boundary. Never write credentials or concrete
secrets into the specification or this reference.

## Invariants for consuming specifications

When applicable, land each invariant in the State 2 ledger with one owner and
one primary representation:

| ID | Invariant | Owner |
| --- | --- | --- |
| `PLAT-REG-001` | Registry is the only creator and current owner of Registry `project_id`. | Registry boundary |
| `PLAT-REG-002` | Consumer identity linkage uses the returned UUID, never display name or address. | consuming domain |
| `PLAT-REG-003` | A linked create command succeeds only after typed validation reports the same UUID as active. | consuming use case |
| `PLAT-REG-004` | Client-supplied Registry context is never authoritative. | consuming API boundary |
| `PLAT-REG-005` | Standalone commands do not call Registry; failed linked commands do not become standalone. | consuming use case |
| `PLAT-REG-006` | A stored snapshot preserves Registry provenance and is not treated as live context. | snapshot owner |
| `PLAT-REG-007` | Service-owned client data remains independent of Registry project context. | consuming domain |

Choose the landing by observability:

- closed status/failure tables belong in `rules`;
- typed request, response, and snapshot shapes belong in `models`;
- timeout, base URL, and retry knobs belong in `config`;
- pure result/argument relations belong in `properties.<function>`;
- I/O, exception translation, orchestration, and trust boundaries remain
  classified notes.

Do not duplicate one invariant as multiple primary landings merely because it
has supporting notes and tests.

## Authoring checklist by state

### State 0 — Product boundary

- Declare Registry as an external system only when linkage exists.
- Decide whether the product supports linked mode, standalone mode, or both.
- Record Registry unavailable, missing project, and archived project as
  observable outcomes.
- Record authentication as unresolved unless a concrete boundary is confirmed.

### State 1 — Domain models

- Use UUID for Registry identity.
- Separate the service's own aggregate, service-owned client data, live
  `ProjectContext`, and any historical `RegistryProjectSnapshot`.
- Do not use `dict`, `Any`, `object`, or generic `metadata` for Registry data.

### State 2 — Invariants, rules, config, and constants

- Add the applicable `PLAT-REG-*` invariants to the ledger with exact owners.
- Declare accepted status/failure values without inventing future statuses.
- Decide the lifecycle policy for already stored records after archival.

### State 3 — Module responsibilities

- Give one adapter/gateway responsibility for HTTP, decoding, timeouts, and
  transport/schema error translation.
- Keep business permission to create linked data in the consuming domain or
  use case, not in a thin HTTP router.
- Prevent direct database and cross-repository model access.

### State 4 — Key system flows

- Trace active-list selection, linked create, missing, archived, unavailable,
  malformed response, and standalone flows where applicable.
- Show where validation ends and the service-owned transaction begins.
- Do not hold a service database transaction open during Registry network I/O.

### State 5 — Public module APIs

- Expose narrow typed operations such as `list_active_projects`,
  `validate_project_reference`, and `get_project_context` from the adapter.
- Expose a separate domain use case for the service-owned command; do not leak
  raw HTTP responses.

### State 6 — Contracts and internal functions

- Declare exact UUID, model, optional, and exception types.
- Keep transport details behind the adapter contract.
- Add helpers only when they own a behavior that cannot remain inside a deep
  module.

### State 7 — Notes and properties

- Require server-side resolution and forbid authoritative client snapshots.
- Specify timeout, failure translation, identity matching, snapshot
  provenance, and standalone behavior with existing note classes.
- Apply the placeholder test to every Registry-facing function.
- Move total, side-effect-free relations over arguments and results into
  `properties`; keep network and exception behavior in notes.

### State 8 — Assembly

- Resolve every Registry model and exception type through declared models or
  imports.
- Place URL/timeout/retry data in `config` and status policy in `rules`.
- Verify dependency direction from the consuming use case to the adapter port,
  never to Registry storage internals.

### State 9 — Factory compatibility probe

- Include the adapter and a representative linked consumer in the no-deploy
  compile probe.
- Verify generated models are concrete and typed, not empty or generic DTOs.
- Treat unresolved Factory warnings as handoff blockers under the compatibility
  profile.

## Evidence baseline

Re-check these sources before changing the public contract. Paths are relative
to the sibling AI Code Factory repository:

- `projects/registry_sandbox/core/models.py` — typed Registry boundary models;
- `projects/registry_sandbox/services/registry/project_service.py` — identity,
  status, validation, context, and archive behavior;
- `projects/registry_sandbox/api/runtime.py` — public HTTP routes and current
  error mapping;
- `projects/registry_sandbox/tests/test_project_identity_boundaries.py` — HTTP
  and service-level contract evidence;
- `projects/PresuPro_sandbox/backend/adapters/registry.py` — example consumer
  with server-side validation and context resolution;
- `projects/PresuPro_sandbox/tests/test_registry_project_integration.py` —
  linked and standalone integration evidence.

These paths prove the inspected sandbox behavior only. They do not prove auth,
production availability, compatibility versioning, or guarantees omitted from
the code and tests.
