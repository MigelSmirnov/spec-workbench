# Room Planner — State 2: Backend-Authoritative Calculation Boundary

> Status: accepted State 2 refinement.
>
> This document defines authority rules exposed by the browser/backend boundary.
> It intentionally does **not** define concrete HTTP paths, Python module names,
> persistence tables, or final request/response DTO signatures. Those belong to
> later design states.

## 1. Browser sends canonical authoring intent, not authoritative derived results

The browser editor may maintain transient projection and preview state, but the
Room Planner backend remains authoritative for accepted domain state and
engineering derivation.

On a confirmed edit the browser sends the canonical user input needed to express
the intended domain change, for example:

- wall/vertex geometry edits in world millimetres;
- opening profile or door-swing edits;
- vertical survey measurements;
- demolition intent;
- Construction wall/opening/treatment intent;
- floor-build-up footprint + explicit thickness;
- ceiling-box footprint + explicit drop height;
- ceiling/wall niche geometry + explicit depth;
- exact selected Construction Catalog references where required.

The browser MUST NOT submit the following as authoritative facts merely because
it can calculate or render them locally:

- room area/perimeter;
- wall gross/net surface area;
- niche internal surface areas;
- ceiling-box side/underside areas;
- floor-build-up volume;
- demolition volumes/areas/lengths;
- material/component quantities;
- Proposed composition;
- acceptance validity;
- final takeoff lines.

Those values are backend-derived from canonical inputs and exact accepted/working
basis data.

## 2. Typed edits, not renderer payloads

Confirmed frontend changes lower into typed planner operations/application
requests.

The later API contract may batch several edits for efficient interaction, but a
batch must contain a closed discriminated union of real Room Planner operations,
not a generic structure such as:

```text
operation: str
payload: dict
```

Canvas/Konva nodes, SVG markup, viewport pixels, scene serialization, selection
state, drag handles, and frontend-only block overlays MUST NOT cross the Room
Planner API boundary as domain mutation payloads.

A committed request should carry an optimistic-concurrency token/version when the
later persistence/API design proves the exact form. The browser must not silently
overwrite a newer working draft.

## 3. Preview and commit remain different meanings

Interactive pointer movement may use local frontend geometry for responsive
visual feedback.

Engineering preview that depends on Room Planner business rules, exact stage
composition, or Construction Catalog data should be evaluated by the backend
through a later preview/evaluation use case rather than by duplicating the full
calculation engine in TypeScript.

Conceptually:

```text
frontend transient candidate
        ↓ optional backend evaluate
backend-derived Proposed / validation / engineering preview
        ↓
user confirms
        ↓
typed working-draft edit
```

A preview/evaluate operation does not persist the candidate unless a separate
confirmed edit is applied.

The frontend may display local approximate geometric aids while dragging, but
accepted/published engineering quantities always come from backend derivation.

## 4. Router is a thin transport boundary

The assembled Room Planner backend is expected to expose an API router, but the
router owns transport only.

The router may own:

- request parsing and schema validation;
- authentication/dependency wiring;
- conversion between transport DTOs and application inputs;
- HTTP status/error mapping;
- response serialization.

The router MUST NOT own:

- room topology derivation;
- wall/opening/niche geometry calculations;
- Proposed composition;
- physical area/volume calculations;
- Construction Catalog application logic;
- takeoff aggregation;
- acceptance rules;
- Platform Hub artifact business semantics.

Those responsibilities must be assigned to deep backend modules/application
orchestration in State 3.

## 5. Geometry measures and takeoff are different calculation layers

Room Planner must distinguish geometric measurement from construction-system
quantity derivation.

Conceptually:

```text
canonical stage geometry/intents
        ↓
resulting / Proposed geometry
        ↓
geometric measures
    length / plan area / surface area / volume
        ↓
Construction Catalog technical parameters
        ↓
physical takeoff quantities
```

Examples of geometric measures owned by Room Planner include:

- room plan area/perimeter;
- gross/net wall-face areas;
- opening/niche deductions and niche internal faces;
- floor-build-up geometric volume;
- ceiling-box underside/side geometry;
- applicable demolition length/area/volume.

Construction-system quantities then apply exact technical catalog facts, for
example consumption, density, component definitions, spacing, or other supported
parameters.

The frontend renderer is not the owner of either layer.

## 6. Canonical downstream quantity result is `room_takeoff`

The Room Planner-owned downstream quantity result remains the
`RoomTakeoffSnapshot` / platform `room_takeoff.v1` artifact family.

Its purpose is to expose reproducible **physical** quantities without requiring
PresuPro or another consumer to duplicate Room Planner geometry or construction
calculation rules.

At the domain level the accepted shape remains based on:

```text
object identity
exact Existing basis
optional exact Demolition basis
optional exact Construction basis
exact Construction Catalog revision when used
typed demolition/construction quantity lines
typed Room Planner source provenance
```

A platform publication additionally carries Hub-resolvable artifact identity,
schema identity/version, producer/version, publication history, and upstream
artifact/shared-data provenance according to `../../PLATFORM_ROUTER.md`.

Prices, labor costs, estimate composition, package conversion, and commercial
rounding remain forbidden in `room_takeoff`.

## 7. Do not distort `room_takeoff` around the current PresuPro API

PresuPro currently may not accept a complete planner quantity list in one direct
bulk operation. That transport limitation does not change the canonical Room
Planner artifact.

The required architecture is:

```text
Room Planner
    ↓ publish
room_takeoff.v1
    ↓
Platform Hub
    ↓
PresuPro consumer / ingestion agent or adapter
    ↓ existing PresuPro agent APIs
PresuPro-owned estimate data
```

The ingestion bridge may iterate the artifact lines and call the currently
available PresuPro APIs one by one. It is a downstream compatibility mechanism,
not Room Planner business logic.

Room Planner MUST NOT:

- call PresuPro directly while calculating a takeoff;
- replace the structured takeoff artifact with imperative PresuPro API calls;
- add prices/labor merely because the current PresuPro API expects estimate
  records;
- make its quantity schema depend on the order or granularity of current
  PresuPro write operations.

If durable mapping/idempotency between one `room_takeoff` line and one PresuPro
record is required, that belongs to the downstream integration/PresuPro boundary
and must be defined from the actual PresuPro API capabilities rather than guessed
inside Room Planner.

## 8. `room_plan` and `room_takeoff` remain separate outputs

`room_plan` exposes the Room Planner-owned spatial/renovation result for consumers
that need geometry and stage semantics.

`room_takeoff` exposes the derived physical quantities for consumers such as
PresuPro that should not recalculate Room Planner geometry.

A consumer may use both contracts when its workflow needs both spatial context
and quantities, but `room_takeoff` must not require access to Room Planner's
private database or browser scene.

The two artifacts are outputs of one Room Planner backend boundary; they do not
imply separate services.

## 9. Later-state API pressure

The later flow/API states should provide application capabilities equivalent in
meaning to:

```text
load working editor/domain state
apply typed Existing/Demolition/Construction edits
evaluate working/candidate state without persistence
validate acceptance readiness
accept immutable stage snapshot
build/read takeoff preview or snapshot
publish accepted room_plan / room_takeoff results
```

Exact operation grouping, route paths, request DTOs, response DTOs, and
optimistic-concurrency fields remain intentionally deferred.

The API should expose use cases rather than internal geometry-pipeline steps.

## 10. Platform Router impact

No new artifact family is introduced.

This refinement confirms the existing shared-platform contract:

- Room Planner produces `room_plan.v1` and `room_takeoff.v1`;
- PresuPro consumes published physical quantity artifacts rather than requiring a
  producer-specific direct integration;
- current agent-mediated PresuPro ingestion is a compatibility bridge after the
  Platform Hub artifact boundary;
- Platform Hub does not own Room Planner calculation logic;
- Room Planner does not own PresuPro estimating logic.

## State 2 effect

This refinement closes the authority question for derived geometry/quantities:
**backend calculation is canonical; frontend calculation is preview/projection
only.**

State 3 must assign the resulting responsibilities to deep modules without
placing domain calculation logic in the API router.