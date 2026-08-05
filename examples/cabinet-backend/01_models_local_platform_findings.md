# State 1 evidence — local platform findings

## Status

Accepted evidence summary derived from the 2026-08-02 local-platform reconnaissance.

This document records facts demonstrated by executable code, storage schemas,
tests, and read-only data inspection. It does not invent missing contracts. The
full reconnaissance report remains the detailed evidence source.

---

# A. Registry contract confirmed

## Project identity and fields

Registry's canonical stored model is `ProjectRecord`.

Confirmed fields:

- `id: UUID`;
- `name: str`;
- `address: str`;
- `status: str`;
- `created_at`;
- `updated_at`;
- optional `customer_ref`.

The compact active-project projection is `ProjectReference`:

- `project_id`;
- `display_name`;
- `status`.

The detailed integration projection is `ProjectContext` and additionally exposes:

- `address`;
- optional `customer_ref`;
- `created_at`;
- `registry_updated_at`.

## Project status

The enforced Registry statuses are exactly:

- `active`;
- `archived`.

Current Registry does not define `closed`, `deleted`, soft deletion, or project
revision history.

`updated_at` is the only available project-change marker. It is not a monotonic
revision and not a content hash.

## Catalogue source

The existing narrow endpoint for the daytime Cabinet catalogue is:

```text
GET /projects/active
```

It returns all current active projects as `ProjectReference` values.

The ordinary `GET /projects` endpoint excludes archived projects unless
`include_archived=true` is supplied. Cabinet must not treat the ordinary default
list as a complete historical catalogue.

## Validation

Registry exposes two useful but distinct lookup behaviors:

- project context/detail lookup returns HTTP 404 for a missing project;
- project validation returns HTTP 200 with explicit `exists`, `status`,
  `is_active`, and failure information.

Cabinet object revalidation should use the explicit validation semantics rather
than infer existence only from a detail lookup.

---

# B. PresuPro contract confirmed

## Estimate identity and project relationship

The estimate model is `Estimate` and its `id` is an opaque string, not a UUID.

The Registry relationship is not a first-class `project_id` field. It is stored
as an optional embedded `RegistryProjectSnapshot` in `Estimate.registry_project`.

One Registry project may have multiple estimates. No uniqueness rule or current
estimate selector exists.

## Estimate lifecycle and version evidence

The runtime guarantees:

- newly created estimates begin as `draft`;
- Holded conversion requires `accepted`.

Although the UI and specification list more statuses, the Backend currently
accepts arbitrary status strings. Cabinet may rely only on behavior confirmed by
the runtime.

An estimate has `created_at` and `updated_at`, but no revision number, version, or
content hash. Updating an estimate replaces its current stored state.

## Zones and items

`EstimateZone` has no stable identifier. It contains:

- `name`;
- optional `area_m2`;
- optional `wall_m2`;
- ordered `items`.

`EstimateItem` has no stable line identifier and no separate description field.
Confirmed fields include:

- `type`;
- optional `name`;
- optional `material_id`;
- `qty`;
- `unit`;
- optional `unit_price`;
- `waste_percent`;
- `margin_percent`;
- `discount_percent`;
- optional `iva_percent`.

`material_id` identifies a material concept, not an estimate-line identity.

A PresuPro update may replace the complete zones list. Therefore a Cabinet match
to a zone/item locator is fragile and must be checked against a captured
`EstimateSnapshot` rather than treated as a durable reference into current
PresuPro state.

## Estimate retrieval

Current HTTP capabilities are:

- list all estimates with optional exact `client_name` and `status` filters;
- get one estimate by `estimate_id`;
- calculate totals separately.

There is no published project-scoped estimate lookup and no rule for selecting
one estimate when a project has several.

State 1 therefore permits only:

- an explicitly selected `estimate_id`; or
- a Cabinet-owned candidate-selection step whose result requires user or policy
  acceptance in State 2.

It must not silently define the newest estimate as the current estimate.

---

# C. Holded boundary correction

A standalone Holded Gateway service was not found.

The existing implementation is PresuPro-owned:

```text
POST /estimates/{estimate_id}/convert
```

It creates a Holded document and stores an `InvoiceRef` on the estimate.

Confirmed `InvoiceRef` fields include:

- provider;
- document type;
- external Holded ID;
- optional number, URL, status, and synchronization time.

The existing integration does not provide:

- provider idempotency keys;
- a durable command/receipt contract;
- bounded timeout wired into document calls;
- unknown-outcome classification;
- reconciliation;
- durable attempt history;
- correction or republication.

Therefore Cabinet Backend State 1 must not present `HoldedPublication` and
`HoldedPublicationAttempt` as backed by an existing Gateway contract.

They remain required Cabinet product concepts, but their external contract is
missing and Holded publication is blocked from later contract design until one
of these decisions is accepted:

1. build a dedicated shared Holded Gateway; or
2. explicitly accept a Cabinet-owned adapter and its stronger reliability
   contract.

The current PresuPro `/convert` endpoint is not a reusable Cabinet publication
boundary.

---

# D. Local integration boundary

Registry and PresuPro already operate as separate HTTP services.

PresuPro reaches Registry through an HTTP adapter configured by
`REGISTRY_API_URL`. Direct in-process Python imports are not a safe shared
boundary because the projects use colliding top-level package names.

Cabinet Backend should therefore consume local services through explicit HTTP
adapters with configured base URLs. It must not import Registry or PresuPro
application modules or access their SQLite databases directly.

Current local service ports are inconsistent across code and documentation.
Addresses must be configuration values; no hard-coded common port is accepted.

No common launcher for Registry, PresuPro, and Cabinet was found. Runtime
orchestration remains an operations concern for later design.

---

# E. Corrections required in `01_models.md`

The following State 1 interpretations are now accepted:

1. `RegistryProjectSnapshot` uses Registry UUID identity and the exact compact or
   context projection fields above.
2. Registry attention results must use `active`, `archived`, or `not_found`;
   `project_closed` is not supported by the current Registry contract.
3. Catalogue generation may use `GET /projects/active`; archived projects may be
   retained locally for history but are excluded from normal offline selection.
4. Registry snapshot change evidence uses `registry_updated_at`, while Cabinet
   may additionally compute its own snapshot content hash.
5. `EstimateReference.estimate_id` is an opaque string.
6. Estimate project linkage is read from embedded `registry_project.project_id`.
7. `EstimateZoneSnapshot` and `EstimateItemSnapshot` cannot claim stable external
   IDs when the source system provides none.
8. Estimate snapshots require a Cabinet-computed content hash for repeatability;
   this hash is Cabinet evidence, not a PresuPro revision.
9. Confirmed matches pin a Cabinet `EstimateSnapshot` and a snapshot-local item
   locator. They do not remain automatically valid against later PresuPro state.
10. Selecting the estimate for a project remains an open State 2 policy because
    the platform has no project-scoped lookup or current-estimate rule.
11. Holded Gateway is a desired platform boundary, not an implemented external
    contract.
12. Local Registry and PresuPro access uses configured HTTP adapters.

---

# F. Remaining State 1 blockers

The external model shapes are sufficiently known to close State 1.

The remaining questions are policies for State 2 rather than missing model
fields:

- whether archived Registry projects remain selectable or read-only only;
- catalogue freshness warning and blocking thresholds;
- explicit estimate selection and replacement rules;
- snapshot-local item locator and invalidation policy;
- treatment of draft versus confirmed Card imports;
- atomic acceptance of Card JSON and mandatory source bytes;
- duplicate blocking and acknowledgement policy;
- VPS retention and backup;
- the future Holded publication boundary.
