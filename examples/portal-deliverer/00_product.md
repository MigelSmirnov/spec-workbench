# State 0 — Portal Deliverer product boundary

## Status

Accepted by the owner on 2026-11-18, with decisions R0-06 to R0-15. Question OQ-07 stays
open.

This case is the first one authored through an experiment: each layer asks what is
unknown, a minimal running prototype answers it, and the layer records the answer with
its evidence (R0-04). The prototype is evidence, not product code. It lives in the
Factory repository under `prototypes/portal_deliverer/`; see `SOURCE.md`.

## Product statement

Portal Deliverer brings progress photos of a renovation object from the object's
Syncthing-fork folder on the VPS to the Client Portal's binary store, and hands back
what is needed to publish each photo. The owner takes a photo on the phone and it can
reach the client's cabinet without anyone copying files to the server by hand.

Portal Deliverer does not show anything to a client. A photo exists for the client only
after it is published through the Portal's own operation.

It is not an upload feature of the Portal, a photo editor, an archive of originals, a
backup of the Syncthing folders or a general file transfer service.

## Actors and trust boundaries

- **Owner** — the one human principal. Takes the photos, decides what a client sees and
  connects an object to its folder.
- **Calling flow** — a cabinet_kernel flow started by the owner. It asks what can be
  delivered, asks for placement, publishes in the Portal with the kernel's own Portal
  session and tells the deliverer which Portal photo resulted. It reaches the deliverer
  over an authenticated boundary.
- **Syncthing-fork** — fills the object folders from the owner's devices. Its files are
  untrusted input: any name, any content, possibly incomplete, possibly replaced.
- **Client Portal** — owns photo records, visibility and what a client can read. It reads
  the binary store the deliverer writes to. The deliverer never calls it.
- **Client** — sees photos only through the Portal and has no access to the deliverer.

| Boundary | What crosses it | Trust |
|---|---|---|
| Object folder → deliverer | file names, file metadata and bytes | untrusted, read only |
| Calling flow → deliverer | project id, file name, source id, Portal photo id | authenticated by the deliverer's own bearer token |
| Deliverer → Portal binary store | prepared image files | written by the deliverer, read by the Portal |
| Deliverer → calling flow | statuses, file reference, publication body | no server path, no credential |

The deliverer holds no Portal credential (P-01).

## Primary actions

| Action | Observable result | Failure | Evidence |
|---|---|---|---|
| Connect an object to its folders (owner, through the agent) | a connection record the owner has confirmed; delivery becomes possible for that project | a connection whose subfolder is written to leave its root is refused, a photo folder linked outside the root is refused when it is used, and an unconfirmed connection delivers nothing | unit tests |
| See what can be delivered for a project | each file with a status: ready, placed or published with its source id, or rejected with a reason | unknown project, unconfirmed connection or unavailable folder is refused; nothing is changed | unit tests, E2E |
| Deliver one chosen photo | a prepared image in the Portal store, its reference and the publication body | a photo that cannot be delivered is reported with its reason and no placement is made; a file whose content differs from the chosen one is not placed | unit tests, E2E |
| Deliver the same photo again | the first result, nothing written | none | unit tests, E2E |
| Publish a placed photo (Portal operation, by the calling flow) | a photo record in the Portal, hidden from the client | the Portal's own refusal | E2E, real Portal |
| Record the publication | the file is reported as published, with its Portal photo id | a photo that was not placed, or a different photo id for the same source, is refused and nothing is changed | unit tests, E2E |
| Show the photo (Portal operation, by the owner) | the client sees and downloads exactly the placed image | the Portal's own refusal | E2E, real Portal |

Evidence is from local runs against a real Client Portal process with a stub Registry, and against two
private Syncthing instances. No run has used the owner's devices, the kernel or the VPS.

## Inputs

Image files in an object's folder; a project id; the file name and source id of a photo to deliver; the
Portal photo id of a published photo.

## Persistent data

- A record of each placement: source hash, file reference, the publication body and how
  the photo date was obtained.
- The prepared images, which live in the Portal binary store.
- A publication mark: which Portal photo a placed source became.
- One connection per object: its Registry project id, root folder, photo and invoice
  subfolders and the owner's confirmation.

Originals stay in the Syncthing folder and are never copied, moved or deleted.

## External systems

Syncthing-fork folders on the VPS, the Client Portal binary store, cabinet_kernel as the
caller. The Client Portal API and Registry are not called by the deliverer.

## Constraints

- Photos may hold the location of a client's home. Nothing but pixels may reach the store.
- The Portal stores `photo_date` as UTC without an offset (client-portal decision A28).
- The Portal has no photo deletion: a published photo can only be hidden.
- The Portal reads at most 26 214 400 bytes per binary.
- The owner's kernel runs on the owner's PC and reaches the VPS only over HTTPS.

## Decisions

### R0-01 — A separate service places binaries (owner, 2026-11-06)

The Portal stays a read boundary for binaries; a separate intake service places them and
supplies references. Uploading into the Portal was considered and rejected
(client-portal `open_questions.md`, Q12).

### R0-02 — The object folders are the input (owner, 2026-11-18)

Files arrive through the object folders Syncthing-fork already brings to the VPS.

### R0-03 — The first version delivers progress photos only (owner, 2026-11-18)

Approved estimates, expense documents and data packages for a client's agent are not
part of this service. A second kind of delivery is a new owner decision.

### R0-04 — Each layer is filled through the experiment (owner, 2026-11-18)

A layer records what the prototype proved, what the owner decided and what is still open,
and keeps them apart. A claim with no evidence and no owner decision is an open question.

### R0-05 — Proyecto Demo Facebook is the first live project (owner, 2026-11-18)

The first run against the production Portal uses that test project only.

### R0-06 — A delivered photo arrives hidden (owner, 2026-11-18, OQ-01)

The owner reviews a delivered photo and shows it to the client with the Portal's own
operation. A wrong photo in the folder therefore never reaches a client by itself.

### R0-07 — The owner starts a delivery (owner, 2026-11-18, OQ-02)

A delivery starts from an action of the owner in the workplace. The workplace lists the photos
that are ready, the owner chooses what to deliver, and the calling flow places, publishes and
marks each chosen photo in that order. The owner sees the result of each photo: delivered, or
failed with its reason. A failed photo does not stop the others. The service delivers nothing by
itself.

### R0-08 — The deliverer keeps the publication mark (owner, 2026-11-18, OQ-03)

The calling flow records the Portal photo id at the deliverer right after publishing. The
Portal is not changed for this. The experiment found that the Portal's photo list does not
return `intake_id`, and that publishing a photo again after it was shown answers 409.

### R0-09 — One connection of an object to its folders (owner, 2026-11-18, OQ-04)

One record per object, keyed by the Registry project id and confirmed by the owner, holds the
object's photo and invoice folders. The deliverer uses it now. The Cabinet Inbox moves to it
later as a separate step.

### R0-10 — A delivered photo is identified by its content (owner, 2026-11-18, OQ-06)

A file replaced with other content is a new photo and waits for the owner's delivery. The
earlier delivery stays in the Portal until the owner hides it. Removing a file from the folder
changes nothing in the Portal.

### R0-11 — The agent connects an object after the owner confirms (owner, 2026-11-18)

The first version has no screen for connections. The agent writes the record after the owner
confirms the object and its folders. A change of the root or of a subfolder clears the confirmation,
and delivery stops until the owner confirms again.

### R0-12 — Everything under the photo folder is delivered on choice (owner, 2026-11-18, OQ-05)

A scan covers the photo folder and all its subfolders. Subfolders carry no meaning for the Portal.
The deliverer sends no section and no caption; the owner sets them in the Portal.

### R0-13 — Old photo dates are repaired before delivery (owner, 2026-11-18, OQ-08)

The agent repairs one project at a time, with a backup and the owner's permission for that project.
Before a delivery the calling flow reads the project's photos in the Portal. If a date still carries
an offset, it stops, places and publishes nothing, and tells the owner.

### R0-14 — A Syncthing conflict copy is not offered (owner, 2026-11-18)

When one file was changed on two devices, Syncthing keeps the other version as a conflict copy beside
it. The deliverer does not offer such a copy. The file stays in the folder, and the owner who wants that
version renames it, after which it is an ordinary photo.

### R0-15 — The service offers primitives and the caller organises the work (owner, 2026-11-18)

The deliverer offers three operations: scan a project's folder, deliver one photo, and record its
publication. When to scan, what to deliver next, what to repeat and which failure to treat as temporary
belong to the calling flow. The guarantees stay in the service: source folders are only read, metadata
is removed, only a confirmed folder is used, a repeated delivery creates nothing new, and every
operation needs the token. A run against real Syncthing showed that a file still arriving lies under a
temporary name, so the two-minute wait of P-04 is withdrawn.

## Accepted from the experiment (owner, 2026-11-18)

Each of these holds in the prototype and was accepted with this frame.

- **P-01** The deliverer holds no Portal credential and never calls the Portal.
- **P-02** Source folders are only read.
- **P-03** A stored image carries no EXIF, GPS, XMP or comment, is upright and is at most
  2000 px on its longest side.
- **P-04** Syncthing's temporary files and hidden names, which include the phone's `.trashed-` files,
  are ignored. The two-minute wait accepted here first was withdrawn by R0-15.
- **P-05** The photo date comes from the camera record, otherwise from the file's
  modification time, and is delivered as UTC without an offset.
- **P-06** One placement exists per project and source content; repeating it changes nothing.

## Open questions

### OQ-07 — Where does the service run and how does the kernel reach it?

It must see the Syncthing folders and the Portal store on the VPS, while the kernel needs an
HTTPS route and its own credential for the service.
