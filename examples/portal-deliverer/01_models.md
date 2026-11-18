# State 1 — Portal Deliverer domain models

## Status

Written on 2026-11-18 from the accepted product frame and the running prototype. Each model
states what the prototype proved.

Every identity is decided; the identity of a delivered photo is decision R0-10.

Evidence for every model: `python3 -m pytest -q prototypes/portal_deliverer`,
`python3 prototypes/portal_deliverer/e2e_local_portal.py` (a real Client Portal process and a stub
Registry) and `python3 prototypes/portal_deliverer/e2e_local_syncthing.py` (two private Syncthing
instances). No run has used the owner's own devices, the kernel or the VPS.

## Model M01 — ObjectConnection

### Meaning

One renovation object and its folders on the VPS (R0-09). `assignment_confirmed` records that the owner confirmed
these exact folders for this object. Both subfolders are written as paths inside the root. Nothing is delivered for
an unconfirmed connection. The agent writes the connection for a project the Registry already
issued, and sets the confirmation only for the folders the owner confirmed. When the agent later
changes the root or a subfolder it clears the confirmation in the same write, and sets it again
after the owner confirms the new folders (R0-11). `label` is a name for people, written by the
agent; changing it affects neither the identity nor the confirmation. The deliverer only reads the
connection.

**Fields:** `project_id: UUID`, `label: str`, `root: path`, `photo_subfolder: str`,
`invoice_subfolder: str`, `assignment_confirmed: bool`.

### Identity

entity

### Identity evidence

- Substitution: Two connections with equal folders still speak for different objects, so one
  cannot replace the other.
- Continuity: The same object stays connected while its folders or its confirmation change.
- Identified by: the `project_id` the Registry issued. The connection is written under that
  identifier, and the deliverer mints nothing here.

### Source of truth

The owner's confirmed record. The Registry remains the authority for the project itself.

### Lifecycle candidate

unconfirmed → confirmed; confirmed → unconfirmed when the root or a subfolder changes (R0-11).

### Persistence candidate

Durable persistence candidate.

### Open questions

None. The Cabinet Inbox keys its bindings by Project Card id today, so its later move to this
record (R0-09) needs a mapping to the Registry project id. That step does not change this model.

## Model M02 — SourcePhotoObservation

### Meaning

What one scan saw for one file of the photo folder. A placed file adds its `file_ref`, a published
file adds its Portal `photo_id`, and files with the same content carry the same `source_id`. The
deliverer computes it on each scan; the calling flow reads it. A server path is never part of it. `size`
is the size the file's metadata gave when it was listed. `source_id` is present for `ready`, `placed` and
`published` and absent for `rejected`, `reason` is present only for `rejected`, `file_ref` for `placed`
and `published`, and `photo_id` only for `published`.

**Fields:** `name: str` (the path relative to the photo folder, with `/` separators), `size: int`,
`source_id: str | None`, `status: ScanStatus`, `reason: ObservationReason | None`,
`file_ref: str | None`, `photo_id: UUID | None`.

**Enumerations:** `ScanStatus` is `ready`, `placed`, `published`, `rejected`. `ObservationReason` is
`empty`, `too_large`, `not_a_regular_file`, `unreadable_file`, `unsupported_format`.

### Identity

value

### Identity evidence

- Substitution: Two observations with equal facts tell the caller the same thing.
- Continuity: Nothing continues between scans; the next scan observes the folder again.

### Source of truth

Calculated from the folder, the placements and the publication marks.

### Lifecycle candidate

None.

### Persistence candidate

Calculated on demand.

### Open questions

None.

## Model M03 — PreparedPhoto

### Meaning

The image made from a source file for the Portal: upright pixels only, at most 2000 px on the
longest side, with the moment the photo was taken as UTC without an offset, and how that moment
was obtained (P-03, P-05). It exists only while a placement is made.

**Fields:** `content: bytes`, `taken_at: datetime`, `date_source: DateSource`.

**Enumeration:** `DateSource` is `exif`, `file_modified`.

### Identity

value

### Identity evidence

- Substitution: Two prepared images with equal bytes, equal moments and an equal date source serve
  the same placement.
- Continuity: It does not change after it is made; a new preparation is a new value.

### Source of truth

Derived from the source file.

### Lifecycle candidate

None.

### Persistence candidate

Temporary runtime use. Its bytes persist as the stored image named by M04.

### Open questions

None.

## Model M04 — PhotoPlacement

### Meaning

The record that one source photo of one project was placed in the Portal binary store. The
deliverer creates it once when placing a photo. A repeated placement returns it and writes nothing
(P-06). `name` is the source's relative path when it was placed and is not updated later. `sha256`,
`size` and `media_type` describe the stored image, while `source_id` is the hash of the source.

**Fields:** `project_id: UUID`, `source_id: str`, `name: str`, `file_ref: str`, `sha256: str`,
`size: int`, `media_type: str`, `date_source: DateSource`, `publication: PhotoPublication`.

### Identity

entity

### Identity evidence

- Substitution: Equal photos of two projects are two deliveries with different references, so
  one placement cannot replace the other (`test_the_same_photo_in_two_projects_stays_two_deliveries`).
- Continuity: The same placement is returned after the source file has left the folder
  (`test_placing_again_returns_the_same_result_without_writing`).
- Minted by: the deliverer, from `project_id` and `source_id`, the SHA-256 of the source content.
- Issued: a placement is a fact about one observed content and is never rewritten.

### Source of truth

Backend-owned record of the deliverer. The stored image is read by the Portal.

### Lifecycle candidate

placed (terminal).

### Persistence candidate

Durable persistence candidate.

### Open questions

None. A delivered photo is identified by its content (R0-10).

## Model M05 — PhotoPublication

### Meaning

The body the calling flow sends to the Portal's `photo.publish`. `intake_id` identifies the
delivery of one source photo to one project: the deliverer derives it from the placement identity
as `deliverer-photo-<project_id>-<source_id>`, so a repeated publication is
recognised by the Portal. `intake_source` states where the photo entered the system and is always
`syncthing`. `client_visible` is always false (R0-06). The deliverer builds the body once within
M04.

**Fields:** `intake_id: str`, `project_id: UUID`, `file_ref: str`, `photo_date: datetime`,
`section_id: UUID | None`, `caption: str | None`, `client_visible: bool`, `intake_source: str`.

### Identity

value

### Identity evidence

- Substitution: Two equal bodies ask the Portal for the same publication.
- Continuity: It is not changed after it is built. The E2E run repeats the same body and the
  Portal answers with the same photo while the photo is hidden.

### Source of truth

The Portal owns the form of this body. The deliverer owns the values it supplies.

### Lifecycle candidate

None.

### Persistence candidate

Durable, as part of M04.

### Open questions

None.

## Model M06 — PlacementOutcome

### Meaning

The answer to one delivery. `source_id` is the one the caller requested. It holds the placement facts
when there is a placement, and the Portal `photo_id` when the photo is already marked as published.

**Fields:** `source_id: str`, `status: PlacementStatus`, `reason: PlacementFailure | None`,
`placement: PhotoPlacement | None`, `photo_id: UUID | None`.

**Enumerations:** `PlacementStatus` is `placed`, `replayed`, `failed`. `PlacementFailure` is
`not_ready_or_absent`, `source_changed`, `empty`, `unsupported_format`, `too_many_pixels`,
`unreadable_image`, `too_large`, `not_a_regular_file`, `unreadable_file`.

### Identity

value

### Identity evidence

- Substitution: Two equal outcomes tell the caller the same thing.
- Continuity: An outcome belongs to one delivery and does not continue after it.

### Source of truth

Calculated by the delivery.

### Lifecycle candidate

None.

### Persistence candidate

Calculated on demand.

### Open questions

None.

## Model M07 — PublicationMark

### Meaning

The record that a placed photo became one Portal photo (R0-08). The calling flow reports the
`photo_id` right after `photo.publish` answers, and the deliverer creates the mark. The scan and a
repeated placement read it, so a flow does not publish the photo again. The same `photo_id` again
returns the first mark; another `photo_id` is refused.

**Fields:** `project_id: UUID`, `source_id: str`, `photo_id: UUID`, `marked_at: datetime`.

**Enumeration:** `MarkStatus` is `marked` for the call that created the mark and `replayed` for a
later call with the same `photo_id`. It is part of the answer to that call and is not stored.
It is kept apart from M04 because the Portal's answer arrives after the placement, from another actor.

### Identity

entity

### Identity evidence

- Substitution: Marks of two placements point at different Portal photos and cannot replace
  each other.
- Continuity: The first mark stands when it is sent again, and its `marked_at` does not change
  (`test_marking_again_changes_nothing_and_another_photo_is_refused`).
- Minted by: the deliverer, keyed by the placement it belongs to. The Portal mints `photo_id`.
- Issued: a mark is written once.

### Source of truth

Backend-owned record of the deliverer. The Portal remains the authority for the photo itself.

### Lifecycle candidate

marked (terminal).

### Persistence candidate

Durable persistence candidate.

### Open questions

None. If the Portal gains removal of a
hidden photo (client-portal Q27), the mark of a removed photo must be reconsidered there.
