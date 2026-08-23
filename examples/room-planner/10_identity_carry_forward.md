# Room Planner — State 1: Snapshot Identity and Existing Correction Carry-Forward

> Status: accepted State 1 model refinement.
>
> This document supplements [10_models.md](10_models.md) and records the State 1
> decisions for accepted snapshot identity, Platform Hub publication separation,
> stable Existing entity identity, correction lineage, and dependent-plan
> carry-forward conflicts. Where terminology here differs from the earlier
> working draft, this document is the later refinement.

## 1. Accepted snapshot and Platform Hub publication are different meanings

Room Planner distinguishes three lifecycle meanings:

```text
mutable working draft
        ↓ accept
immutable Room Planner snapshot
        ↓ explicit publish
Platform Hub publication / artifact history
```

Acceptance is a Room Planner domain action. It freezes a complete stage result
into an immutable snapshot with a stable Room Planner snapshot identity.

Publication is a separate explicit action that exposes an accepted result through
the shared [Platform Router / Platform Hub](../../PLATFORM_ROUTER.md). Publication
must not be implied by save, preview, or acceptance.

The Platform Hub is not an unknown external platform. It is the shared platform
integration environment in which participating services discover objects,
contracts, shared data, artifacts, publication history, and provenance. Shared
requirements discovered here belong in `../../PLATFORM_ROUTER.md`, not in a
private Room Planner publication protocol.

### Consequence for dependent stage work

A dependent Room Planner draft may use an accepted immutable snapshot as its
basis even if that snapshot has not yet been published to the Platform Hub.

For example:

```text
Existing Draft
    ↓ accept
Existing Snapshot E1
    ↓
Demolition Draft based on E1
```

Room Planner therefore does not require an unnecessary Hub publication merely
to continue its own stage-by-stage authoring workflow.

When a dependent result is explicitly published to the Platform Hub, however,
its platform-visible provenance must resolve to the exact published basis
result(s) represented in Hub artifact/publication history. A Room Planner-private
`snapshot_id` is not by itself a Platform Hub provenance reference.

The exact flow for ensuring required basis publications exist — whether already
published or published coherently as part of a later explicit publication flow —
is deferred to the flow/API states. State 1 fixes only the identity separation.

## 2. Snapshot terminology supersedes provisional revision terminology

The earlier State 1 draft used `*RevisionRef` for immutable Room Planner domain
snapshots. That wording is now refined because `revision` is also a natural
Platform Hub artifact-history term.

Use the following Room Planner domain names:

```text
ExistingSnapshotRef
    snapshot_id: str

DemolitionSnapshotRef
    snapshot_id: str

ConstructionSnapshotRef
    snapshot_id: str
```

Correspondingly, immutable stage aggregates carry `snapshot_id`, not
`revision_id`:

```text
ExistingPlanSnapshot.snapshot_id
DemolitionPlanSnapshot.snapshot_id
ConstructionPlanSnapshot.snapshot_id
```

`RoomTakeoffSnapshot` should likewise use `takeoff_snapshot_id` rather than
`takeoff_revision_id`.

The three typed snapshot refs remain intentionally separate. A generic
`SnapshotRef(stage: str, id: str)` would permit invalid dependencies such as
Demolition taking Construction as its basis.

Platform Hub artifact identifiers, publication identifiers, artifact revisions,
schema identities, and publication timestamps remain boundary concepts to be
defined in later states against `PLATFORM_ROUTER.md`.

## 3. Snapshot basis rules

The basis graph is directional:

```text
ExistingSnapshot
    ↓
DemolitionSnapshot
    ↓
ConstructionSnapshot
```

More precisely:

```text
DemolitionPlanDraft
    existing_basis: ExistingSnapshotRef

DemolitionPlanSnapshot
    existing_basis: ExistingSnapshotRef

ConstructionPlanDraft
    existing_basis: ExistingSnapshotRef
    demolition_basis: DemolitionSnapshotRef | None

ConstructionPlanSnapshot
    existing_basis: ExistingSnapshotRef
    demolition_basis: DemolitionSnapshotRef | None
```

A draft never takes another mutable draft as its durable basis.

If Construction has a Demolition basis, that Demolition snapshot must itself be
based on the same Existing snapshot expected by the Construction result. The
precise validation rule belongs to State 2, but State 1 fixes the shape so an
incoherent graph cannot be represented as an intended valid state.

## 4. Existing correction creates a new snapshot, never a mutation

A correction to Existing follows this meaning:

```text
Existing Snapshot E1
        ↓ create correction draft
Existing Draft based on E1
        ↓ accept
Existing Snapshot E2
```

`E1` remains immutable forever. `E2` is a new accepted reconstruction of the
pre-renovation condition.

Existing Demolition or Construction snapshots remain historically pinned to
`E1`; they are never silently rebound to `E2`.

Dependent working intent may be carried forward by creating new drafts:

```text
D1 based on E1
    ↓ carry forward against E2
D2 Draft based on E2

C1 based on E1 + D1
    ↓ after D2 is resolved/accepted
C2 Draft based on E2 + D2
```

The carry-forward operation creates new working state. It never edits the basis
of an old snapshot in place.

When Construction has no Demolition basis, it may be carried directly from its
old Existing basis to the corrected Existing snapshot.

## 5. Stable Existing entity identity

Existing entity identity is semantic identity, not exact geometric equality.

A measured correction may change an entity's geometry while preserving the
identity of the same physical thing.

Example:

```text
E1: wall W17 length 4012 mm
E2: wall W17 length 4007 mm
```

If the correction still represents the same physical wall, `wall_id = W17`
remains stable. A dependent intent such as `remove W17` therefore remains
meaningful and can be carried forward without a conflict merely because the
measurement changed.

Entity ids must not be reassigned solely by coordinate matching after the fact.
When correction changes topology or semantic identity, the relationship between
old and new entities is recorded explicitly as lineage.

## 6. Existing entity references used by correction lineage

Lineage applies to Existing entities whose identity may be consumed by later
stage intent or provenance.

Candidate closed union `ExistingEntityRef`:

```text
ExistingWallEntityRef
    entity_kind: Literal['wall']
    wall_id: str

ExistingOpeningEntityRef
    entity_kind: Literal['opening']
    opening_id: str

ExistingRoomEntityRef
    entity_kind: Literal['room']
    room_id: str

ExistingSurfaceLayerEntityRef
    entity_kind: Literal['surface_layer']
    layer_id: str
```

Additional entity kinds must be added only when a real dependent-domain need
requires stable correction lineage. Internal geometry helpers must not be added
to this union merely because they have ids.

## 7. Existing correction lineage

`ExistingCorrectionLineage` is an immutable domain record connecting one
accepted Existing snapshot to its corrected successor.

```text
ExistingCorrectionLineage
    from_snapshot: ExistingSnapshotRef
    to_snapshot: ExistingSnapshotRef
    relations: list[ExistingEntityLineage]
```

Candidate closed union `ExistingEntityLineage` uses `lineage_kind` as its
discriminator.

### `PreservedEntityLineage`

The same semantic entity survives the correction.

```text
lineage_kind: Literal['preserved']
source: ExistingEntityRef
target: ExistingEntityRef
```

Normal measurement changes, movement, dimension correction, and other geometry
changes do not create a carry-forward conflict merely because coordinates differ
when identity is explicitly preserved.

### `SplitEntityLineage`

One prior entity is replaced by multiple semantically distinct entities.

```text
lineage_kind: Literal['split']
source: ExistingEntityRef
targets: list[ExistingEntityRef]
```

Example:

```text
W17 → W31 + W32
```

### `MergedEntityLineage`

Multiple prior entities are replaced by one semantic entity.

```text
lineage_kind: Literal['merged']
sources: list[ExistingEntityRef]
target: ExistingEntityRef
```

### `RemovedEntityLineage`

The prior entity has no successor in the corrected reconstruction.

```text
lineage_kind: Literal['removed']
source: ExistingEntityRef
```

This means the correction determined that the old modeled entity should no
longer exist in the reconstructed pre-renovation condition. It does not mean
renovation demolition physically removed the entity.

### `AddedEntityLineage`

The corrected reconstruction introduces a previously unmodeled Existing entity.

```text
lineage_kind: Literal['added']
target: ExistingEntityRef
```

### Lineage meaning

Lineage is accepted domain evidence about identity across Existing snapshots.
Geometry may help derive or propose lineage during editing, but downstream
carry-forward must consume the accepted lineage rather than independently guess
identity from coordinates.

Rules about same-kind source/target compatibility, completeness, uniqueness,
and whether a proposed lineage requires user confirmation belong to State 2.

## 8. Carry-forward result

Carrying dependent intent forward produces a new draft plus explicit unresolved
conflicts, rather than silently mutating the old draft/snapshot.

Conceptually:

```text
DemolitionCarryForwardResult
    source_snapshot: DemolitionSnapshotRef
    target_existing_basis: ExistingSnapshotRef
    draft: DemolitionPlanDraft
    conflicts: list[CarryForwardConflict]

ConstructionCarryForwardResult
    source_snapshot: ConstructionSnapshotRef
    target_existing_basis: ExistingSnapshotRef
    target_demolition_basis: DemolitionSnapshotRef | None
    draft: ConstructionPlanDraft
    conflicts: list[CarryForwardConflict]
```

These are domain result shapes, not yet function contracts.

An empty conflict list means every carried intent remained semantically
unambiguous. It does not itself mean the resulting draft has been accepted.

## 9. Typed carry-forward conflicts

`CarryForwardConflict` is a closed discriminated union. The model must not fall
back to `reason: str`, `details: dict`, or an arbitrary payload.

Each conflict identifies the dependent intent whose meaning could not be safely
preserved. The exact typed `DependentIntentRef` union will be finalized together
with Proposed/takeoff source references, but it must identify the actual
Demolition or Construction item rather than only free-form text.

### `MissingTargetConflict`

The old intent referenced an Existing entity whose lineage has no usable target.

```text
conflict_kind: Literal['missing_target']
intent: DependentIntentRef
source_target: ExistingEntityRef
```

Typical cause: `RemovedEntityLineage`.

### `AmbiguousTargetConflict`

The old single-target intent maps to more than one semantically possible target,
or otherwise lacks one unique successor.

```text
conflict_kind: Literal['ambiguous_target']
intent: DependentIntentRef
source_target: ExistingEntityRef
candidate_targets: list[ExistingEntityRef]
```

Typical cause: a split such as `W17 → W31 + W32`. The system may present the
candidates but must not choose one or all of them merely because that looks
plausible.

### `InvalidRelativePlacementConflict`

The host entity remains identifiable, but a geometry-relative intent no longer
fits its corrected geometry.

```text
conflict_kind: Literal['invalid_relative_placement']
intent: DependentIntentRef
target: ExistingEntityRef
```

Example: an opening cut defined by wall-relative offset and width no longer fits
inside the corrected wall extent.

The numeric validity criteria belong to State 2.

### `InvalidHostRelationshipConflict`

The target entity survives, but a relationship on which the intent depends has
changed so that the old meaning cannot be preserved directly.

```text
conflict_kind: Literal['invalid_host_relationship']
intent: DependentIntentRef
target: ExistingEntityRef
```

Examples include an opening no longer belonging to the same wall identity or a
wall-face target losing the relationship required by the dependent intent.

### `InvalidSurfaceTargetConflict`

A room/surface-oriented intent cannot be mapped to one valid corrected surface
scope.

```text
conflict_kind: Literal['invalid_surface_target']
intent: DependentIntentRef
source_target: ExistingEntityRef
candidate_targets: list[ExistingEntityRef]
```

This covers cases where correction changes room/surface topology so a prior
floor, ceiling, or wall-surface intent no longer has one unambiguous target.

### What is not a conflict by itself

A wall or opening merely moving, changing dimensions, or receiving corrected
coordinates is not itself a conflict if its semantic identity is preserved and
the dependent intent remains valid.

State 2 will define when a preserved target's geometric change invalidates a
specific dependent intent.

## 10. Carry-forward order

When Construction depends on Demolition, correction propagation follows the
basis graph:

```text
E1 → correction → E2

D1(E1)
    ↓ carry forward
D2 Draft(E2)
    ↓ resolve conflicts / accept
D2 Snapshot(E2)

C1(E1, D1)
    ↓ carry forward
C2 Draft(E2, D2)
```

Construction must not be represented as coherently rebased to `E2` while still
claiming a Demolition basis that remains pinned to `E1`.

If Construction has `demolition_basis = None`, it may be carried directly to the
new Existing basis.

The orchestration and user interaction for this sequence belong to later states;
State 1 fixes only the dependency shape and result models.

## 11. Platform Router impact

This refinement does not introduce a private Room Planner platform mechanism.
It clarifies the boundary already accumulated in
[PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md):

- Room Planner snapshots are private/domain identities until explicitly
  published;
- Platform Hub publication creates/resolves platform-visible artifact history;
- dependent Hub publications preserve exact basis provenance;
- Hub provenance uses Hub-resolvable publication/artifact identities rather than
  opaque Room Planner-private snapshot ids;
- save, preview, acceptance, and publication remain distinct meanings.

If later flow/API design shows that the Hub needs a new concept for publishing a
dependent result together with an unpublished required basis, that requirement
must first be added to `PLATFORM_ROUTER.md` at the shared abstraction level.

## 12. State 1 closure effect

The following previously open State 1 decisions are now closed:

1. acceptance mints an immutable Room Planner snapshot before Platform Hub
   publication;
2. Room Planner basis references are typed `*SnapshotRef` values;
3. Existing corrections preserve semantic entity identity explicitly through
   `ExistingCorrectionLineage`;
4. split, merge, removal, addition, and preservation are explicit lineage facts;
5. carry-forward creates new dependent drafts rather than rebasing old snapshots
   in place;
6. carry-forward failures are represented by a closed typed conflict family,
   not generic strings/dictionaries;
7. Construction carry-forward respects the Existing → Demolition → Construction
   basis graph.

Remaining State 1 work still includes typed dependent/source refs used by
carry-forward, Proposed provenance, and takeoff provenance, plus the smaller
opening/ceiling/catalog model questions already listed in `10_models.md`.
