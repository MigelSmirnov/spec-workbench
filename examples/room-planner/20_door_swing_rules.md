# Room Planner — State 2: Door Swing Rules

> Status: accepted State 2 refinement.
>
> This document supplements `20_rules.md` after State 0/1 were repaired to make
> hinged-door opening direction explicit domain data.

## 1. Swing completeness

1. An accepted Construction `InstallHingedDoor` MUST contain an explicit
   `DoorSwing`.
2. `swing = None` is allowed only in the corresponding mutable Construction
   draft shape.
3. A renderer/palette default MUST NOT satisfy acceptance completeness.
4. An Existing hinged door may retain `swing = None` when the survey did not
   establish the opening direction; unknown Existing fact is preferable to a
   fabricated value.
5. UI/review surfaces MUST distinguish unknown Existing swing from a known
   canonical swing.

## 2. Canonical local meaning

1. `DoorSwing.hinge_jamb` is interpreted relative to the host aperture's
   start/end along the directed host wall axis.
2. `DoorSwing.swing_to_wall_side` is interpreted using the same directed wall's
   canonical `WallSide.left|right` semantics.
3. These fields, together with the host aperture profile, uniquely determine the
   plan swing of a single hinged leaf.
4. Clockwise/counter-clockwise renderer orientation is derived and MUST NOT be
   stored as an independent conflicting field.
5. A free-standing `opens_inward`/`opens_outward` boolean is not canonical.

## 3. Contextual inward/outward labels

1. User-facing labels such as `opens into Kitchen`, `opens into Corridor`,
   `opens inward`, or `opens outward` are projections of canonical swing plus
   adjacent-space context.
2. If both sides are interior rooms, the UI SHOULD prefer explicit destination
   room/space wording over ambiguous inward/outward wording.
3. If one wall side resolves to exterior and the other to interior space, the UI
   may derive inward/outward wording deterministically from that adjacency.
4. A failure to resolve adjacency MUST NOT change canonical `DoorSwing` data.

## 4. Host wall direction reversal

Reversing a directed wall from:

```text
A → B
```

to:

```text
B → A
```

while preserving the same physical wall is a semantic transform because
wall-relative opening and side data depend on orientation.

For every hosted aperture with old wall length `L`:

```text
new_offset = L - old_offset - opening_width
```

The aperture's physical world position must remain unchanged.

For a door swing on that aperture:

```text
opening_start ↔ opening_end
left ↔ right
```

must both be transformed so the hinge point and physical swing side remain
unchanged in world coordinates.

A wall-direction reversal that changes only `start_vertex_id/end_vertex_id`
without transforming dependent opening/swing data is invalid.

## 5. Aperture edits and door swing

1. Moving/resizing an aperture does not automatically change hinge jamb or swing
   side when the same door semantic identity is retained.
2. If an aperture edit makes the existing hinge/swing physically invalid, the
   editor must surface validation rather than silently flip the door.
3. Changing hinge jamb or swing side is an explicit door-element edit, not an
   incidental consequence of dragging the aperture.
4. Replacing a door may choose a different swing as part of the new Construction
   installation intent.

## 6. Proposed composition

1. A retained Existing hinged door contributes its recorded swing to Proposed.
2. If Existing swing is unknown and the door remains, Proposed preserves that
   unknown rather than inventing a direction.
3. A Construction-installed hinged door contributes its accepted explicit swing.
4. If an aperture is closed, no Proposed opening element/swing remains.
5. Demolition removal of a door removes that Existing element from Proposed but
   does not itself create a replacement swing.

## 7. Frontend projection

1. Konva/SVG scene state is derived from canonical `DoorSwing`.
2. Changing a door symbol variant without changing the Room Planner working
   domain state MUST NOT change engineering swing meaning.
3. A symbol registry may map canonical swing semantics to an appropriate visual
   asset/transform.
4. If a physical distinction represented visually is not present in canonical
   domain data, the renderer must use a neutral representation rather than
   infer the missing engineering fact.

## 8. Takeoff and pricing boundary

Door swing itself is spatial/plan semantics. It does not introduce pricing or
labor responsibility into Room Planner.

If later Construction Catalog systems distinguish physical door components by
swing/handing and Room Planner becomes responsible for those physical
quantities, that requirement must be added explicitly rather than inferred from
renderer symbol variants.

## 9. Platform Router impact

No new Platform Hub mechanism is introduced. Published Room Planner data must
preserve canonical door swing where present; the Hub does not derive, normalize,
or own door swing semantics.
