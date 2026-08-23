# Room Planner — State 1: Remaining Model Closure

> Status: accepted State 1 closure refinement.
>
> This document closes the remaining explicit State 1 questions listed in
> [10_models.md](10_models.md) after the accepted snapshot, carry-forward,
> provenance, and opening-lifecycle refinements. State 1 is considered
> stabilized as a document set when this file is read together with the earlier
> accepted `10_*` refinements.

## 1. Initial room boundary semantics are physical, not zoning semantics

The initial Room Planner `ExistingRoom` / Proposed room concept represents a
spatial room enclosed by the physical plan topology owned by Room Planner.

A room boundary is derived from wall geometry and the wall/opening topology. A
door/window aperture does not by itself erase the semantic wall boundary between
rooms; the room derivation may use the host-wall boundary through an opening
while net wall-surface calculations still subtract the aperture appropriately.

The initial product does **not** introduce arbitrary invisible/virtual room
boundary edges merely so a user can split one open-plan space into named zones.

Therefore the provisional field remains conceptually sufficient:

```text
ExistingRoom
    room_id: str
    name: str
    boundary_faces: list[ExistingWallFaceRef]
```

with exact ordering/closure rules deferred to State 2.

### Open-plan consequence

Two areas connected without a physical Room Planner boundary are one spatial
room for this initial domain model. If later product work needs kitchen/living
zones, finish zones, occupancy zones, or other non-physical subdivisions, they
must be introduced as a separate explicit concept such as a zone/region rather
than hidden inside a generic room-boundary payload.

This does not block localized floor/ceiling work: treatment/elevation intents may
already target explicit plan footprints/surface patches without pretending those
patches are separate rooms.

## 2. Construction walls have different draft and accepted completeness

The provisional `ConstructionWall.system_ref: ConstructionSystemRef | None`
correctly models incomplete editing but is too weak for an accepted physical
wall result.

State 1 therefore distinguishes draft and accepted wall shapes.

### `ConstructionWallDraft`

```text
wall_id: str
start_vertex_id: str
end_vertex_id: str
thickness_mm: Decimal
system_ref: ConstructionSystemRef | None
```

`None` means the user has laid out geometry but has not yet selected the exact
Construction Catalog system. It never means "use latest" or "pick a default".

### `ConstructionWall`

Accepted immutable wall shape:

```text
wall_id: str
start_vertex_id: str
end_vertex_id: str
thickness_mm: Decimal
system_ref: ConstructionSystemRef
```

Every accepted new Construction wall therefore pins an exact catalog-backed
construction system.

The explicit `thickness_mm` remains domain geometry because the product needs an
actual wall thickness for spatial calculations. State 2 must ensure it is
compatible with the selected system and any catalog-supported parameterization;
Room Planner must not keep two contradictory authoritative thickness values.

### Level aggregate refinement

Mutable `ConstructionLevelDraft` uses:

```text
walls: list[ConstructionWallDraft]
```

The immutable accepted Construction level/snapshot uses:

```text
walls: list[ConstructionWall]
```

This prevents an unresolved wall system from entering an accepted snapshot
merely because the draft model allowed partial construction.

## 3. No geometry-only accepted Construction wall class in the initial product

The initial product has no second accepted wall class that means "physical wall
of unknown construction".

A Construction wall means intended renovation work. For reproducible takeoff and
future downstream use, that work must resolve to a concrete Construction Catalog
system before acceptance.

This does not prevent the browser editor from drawing geometry first. It only
separates incomplete draft geometry from an accepted construction result.

If a future product requirement genuinely needs a construction wall whose
material/system is intentionally unknown yet still publishable, that is a new
product/model decision and must not be simulated with `system_ref = None`.

## 4. Ceiling construction remains one typed treatment family for now

State 0 requires Room Planner to support ceiling preparation/finish intent and
physical quantities, but it deliberately leaves the full ceiling-system catalog
open.

The current State 1 model therefore keeps one explicit:

```text
CeilingTreatmentIntent
    construction_kind: Literal['ceiling_treatment']
    item_id: str
    target_surface: ElevationSurfaceSet
    system_ref: ConstructionSystemRef
```

This is not an arbitrary payload: it has one typed target surface and one exact
catalog-backed technical system.

No speculative union of plaster/lacquer/suspended/acoustic/etc. variants is
introduced until those variants require different domain fields or lifecycle
behavior.

### Current scope interpretation

For the initial product this model covers supported ceiling preparation and
finish systems selected from the Construction Catalog and applied to an explicit
ceiling target surface.

A future **new structural/suspended ceiling construction system** that requires
a different geometric or lifecycle model must be added explicitly when product
scope proves that need. It is not inferred merely because Existing may contain a
suspended ceiling that can be demolished.

## 5. `SpatialLevel.level_id` remains Room Planner-local in State 1

The canonical cross-application identity is still Registry `object_id`.
`PLATFORM_ROUTER.md` does not yet define a shared platform floor/level identity
contract required by Room Planner.

Therefore State 1 closes with:

```text
Registry object_id
    └── Room Planner container
        └── local SpatialLevel.level_id
```

`level_id` is stable inside the Room Planner object and participates in Room
Planner snapshot/provenance references, but it is not claimed to be a Registry
or Platform Hub global identity.

If a later cross-application use case proves that several planners must address
the same canonical floor independently, the shared requirement belongs first in
[PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md). Room Planner must not unilaterally
promote its local `level_id` into a platform contract.

## 6. State 1 blocker closure matrix

The explicit blockers originally listed in `10_models.md` are now resolved as
follows:

1. accepted vs published snapshot identity → closed by
   [10_identity_carry_forward.md](10_identity_carry_forward.md);
2. carry-forward conflict union → closed by
   `10_identity_carry_forward.md`;
3. Proposed source refs → closed by
   [10_source_provenance.md](10_source_provenance.md) and refined for openings by
   [10_opening_lifecycle.md](10_opening_lifecycle.md);
4. takeoff source refs → closed by `10_source_provenance.md` and refined for
   opening intent by `10_opening_lifecycle.md`;
5. room boundary edge completeness → closed by this document: no virtual zoning
   edges in the initial room model;
6. Construction opening responsibility → closed by
   `10_opening_lifecycle.md` with explicit create/alter/close lifecycle;
7. ceiling treatment taxonomy → closed by this document: retain one typed
   catalog-backed treatment until distinct fields/behavior are proven;
8. catalog-backed wall system selection → closed by this document: required for
   accepted Construction walls, optional only in drafts;
9. level/Registry projection → closed for State 1: local Room Planner level
   identity until a shared Hub/Registry requirement exists.

## 7. Placeholder-resistance closure audit

After the accepted refinements, State 1 no longer relies on the provisional
placeholders called out by the base draft:

- no generic plan payload;
- no generic revision ref across stages;
- no untyped carry-forward conflict reason/details;
- no `source_item_ids: list[str]` takeoff provenance;
- no one-size-fits-all Construction opening object;
- no fake Proposed entities for removed geometry;
- no accepted Construction wall with an unresolved system;
- no virtual room-boundary payload added "for flexibility";
- no speculative ceiling subtype catalog encoded before its domain need exists.

Some older provisional names/shapes remain visible in `10_models.md` as the
chronological base draft. The accepted later `10_*` refinement documents are
normative where they explicitly supersede those shapes. A future consolidation
may rewrite the base file for readability, but consolidation must not invent new
semantics.

## 8. Frontend/editor consequence

State 1 now provides enough authoritative domain data for the browser editor to
project its core scene without defining React/component contracts yet:

```text
Existing topology + vertical survey
Demolition intents
Construction wall/opening/treatment intents
        ↓
Derived Proposed scene
```

The browser may maintain transient zoning-like selections, guides, preview
polygons, snap state, and selection groups, but such UI conveniences do not
become `Room` entities or accepted domain geometry unless a later product
concept explicitly owns them.

Frontend dependencies continue to be indexed by
`frontend_context.json`/`tools/frontend_context.py`; canonical model semantics
remain in the numbered State documents.

## 9. Platform Router impact

This closure introduces no new Platform Hub mechanism.

The only platform-facing conclusion is reaffirmed: `SpatialLevel.level_id` is
not yet a shared Hub identity. All previously accepted publication, artifact,
Construction Catalog, and provenance requirements remain unchanged.

## State 1 result

**State 1 — Domain Models is stabilized as a document set.**

The next design state may now define **State 2 — Rules and Invariants**. If
State 2 exposes a missing model concept rather than merely a missing rule, the
methodology requires returning to State 1 and repairing the model here first.
