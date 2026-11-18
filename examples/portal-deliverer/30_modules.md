# State 3 — Portal Deliverer module responsibilities

## Status

Written on 2026-11-18 from the accepted States 0 to 2. The prototype was split into exactly these
modules to test the boundaries. Evidence: `python3 -m pytest -q prototypes/portal_deliverer`
(46 tests) and `python3 prototypes/portal_deliverer/e2e_local_portal.py` (26 checks). The tests
`test_modules_depend_only_in_the_declared_direction` and
`test_each_hidden_mechanism_stays_inside_its_module` read the imports of the prototype and fail when
a boundary below is broken.

The split found one defect of the prototype. A mark with a malformed source id was answered
`unknown_project` after reading the clock, against A4 rule 2 and A7 rule 2. One module now owns the
order of checks, and `test_a_mark_with_a_malformed_source_id_is_refused_before_the_connection_and_the_clock`
holds that order.

## Dependencies

A module may know only the modules listed for it. There are no cycles.

| Module | May know |
|---|---|
| `domain_models` | none |
| `object_connections` | `domain_models` |
| `source_folder` | `domain_models` |
| `photo_preparation` | `domain_models` |
| `delivery_store` | `domain_models` |
| `photo_delivery` | `domain_models`, `object_connections`, `source_folder`, `photo_preparation`, `delivery_store` |
| `deliverer_api` | `domain_models`, `object_connections`, `photo_delivery` |

`deliverer_api` knows `object_connections` only to load the connections when the service starts.

## Rules decided across modules

A decision has one primary owner in `30_trace.json`. Where its rules reach other modules, this table
names the owner of each rule.

| Decision | Rule | Owner |
|---|---|---|
| A1 | order 1 to 8, ignored names, walking order | `source_folder` |
| A1 | order 9 to 11, placed and published status | `photo_delivery` |
| A5 | rules 1 to 4, token and listening address | `deliverer_api` |
| A5 | rule 5, the single principal | `deliverer_api` |
| A5 | rules 6 and 7, connection and photo folder | `object_connections` |
| A5 | rule 8, project id form | `deliverer_api` |
| A5 | rule 8, source id form, and no received text in a stored path | `photo_delivery` |
| A5 | rule 9, what an answer holds | `photo_delivery` |
| A6 | rules 1 to 3, stored names, modes, atomic writes, the lock itself | `delivery_store` |
| A6 | rule 4, which checks and writes run inside the lock | `photo_delivery` |
| A7 | rules 1 and 3, the clock and the form of its reading | `deliverer_api` |
| A7 | rule 2, when an operation reads the clock | `photo_delivery` |
| A7 | rule 4, a file's modification time | `source_folder` |
| A7 | rule 5, the photo moment | `photo_preparation` |

## Invariant owners

| Invariant | Owner |
|---|---|
| INV-01, INV-02 | `source_folder` |
| INV-03, INV-04, INV-05, INV-14 | `photo_preparation` |
| INV-06, INV-07, INV-08, INV-11, INV-12, INV-13 | `photo_delivery` |
| INV-09 | `deliverer_api` |
| INV-10 | `object_connections` |
| INV-15 | deployment route (A9) |
| INV-16 | security review record (A10) |
| INV-17 | calling flow (A11), outside this service |

## `domain_models`

### Owns

- the models M01 to M07 and their enumerations;
- the policy constants and the run settings of A8;
- the form of a source id;
- the two refusal types: a refusal of the whole operation and a refusal of one file.

### Knows

- field structure and decided values;
- no folder, file, image, lock or transport behaviour.

### Must not own

- any rule that chooses between outcomes;
- reading or writing anything outside the process.

### Public surface

Exports types and constants only.

### Trace inputs

- A8

### Depth assessment

- kind: deep
- hidden mechanism: none beyond type validity; this is the shared vocabulary of the service.

## `object_connections`

### Owns

- reading the connection records and refusing to start with a subfolder that leaves its root;
- deciding whether a project has a confirmed connection;
- deciding whether the photo folder is available and strictly below the resolved root.

### Knows

- M01 and rules 6 and 7 of A5.

### Hides

- the form of the connections file;
- how relative subfolders are checked;
- how links are resolved before the folder is accepted.

### Must not own

- writing a connection or setting its confirmation, which the agent does after the owner confirms (R0-11);
- listing or reading the files of a folder;
- the Cabinet Inbox's use of the invoice folder.

### Candidate public capabilities

```text
load_connections
confirmed_connection
available_photo_folder
```

### Trace inputs

- A5

### Depth assessment

- kind: deep
- hidden mechanism: containment of an owner-confirmed folder below its object root.

## `source_folder`

### Owns

- walking the photo folder in the decided order;
- ignored names, links, the settling time, source limits and file signatures;
- detecting a file with the same content as an earlier file of the scan;
- reading the bytes of one source file without following a link;
- the modification time of a file in the service's time form.

### Knows

- A1 rules in order 1 to 8, and rule 4 of A7.

### Hides

- directory traversal and the handling of files that disappear during it;
- how a partial listing becomes `folder_unavailable`;
- the signatures of accepted formats.

### Must not own

- any write, in any folder;
- whether a photo was placed or published;
- decoding an image.

### Candidate public capabilities

```text
observe_source_files
read_source_bytes
```

### Trace inputs

- A1
- A7

### Depth assessment

- kind: deep
- hidden mechanism: safe read-only observation of a folder that another program is changing.

## `photo_preparation`

### Owns

- decoding an accepted source and the limits of A2;
- making the upright metadata-free JPEG;
- choosing the photo moment and converting it to UTC without an offset;
- building the publication body, with `client_visible` false.

### Knows

- A2, rule 5 of A7, and the form of the Portal's `photo.publish` body.

### Hides

- the image library;
- EXIF tags, camera offsets and implausible camera clocks;
- local times that occur twice or do not exist.

### Must not own

- reading a source file or writing a stored image;
- publishing, or calling the Portal;
- deciding which photos are delivered.

### Candidate public capabilities

```text
prepare_photo
build_publication
```

### Trace inputs

- A2

### Depth assessment

- kind: deep
- hidden mechanism: turning untrusted image bytes into clean pixels and one trustworthy moment.

## `delivery_store`

### Owns

- the names and modes of stored images and state records;
- atomic writing of one file;
- the reference of a stored image and its containment in the binary store;
- the per-project lock across processes;
- reading and writing placement and mark records.

### Knows

- rules 1 to 3 of A6 and the lock of rule 4.

### Hides

- the layout of the state folder and the binary store;
- temporary names, disk synchronisation and renaming;
- the operating system lock.

### Must not own

- whether a placement or mark may be written;
- the meaning of a replay or a conflict;
- removal of anything, which the first version does not offer (A3).

### Candidate public capabilities

```text
project_lock
store_image
read_placement
write_placement
read_mark
write_mark
```

### Trace inputs

- A6

### Depth assessment

- kind: deep
- hidden mechanism: durable per-file writes on a shared disk under one lock per project.

## `photo_delivery`

### Owns

- the order of checks of scan, placement and mark, after the request form is accepted;
- when an operation reads the clock;
- completing a scan with placed and published status;
- one placement per project and content, replay, and per-photo failure;
- writing the stored image before the placement record;
- one mark per placement, replay and `publication_conflict`;
- which checks and writes run inside the project lock;
- keeping server paths out of every answer.

### Knows

- A3, A4, rule 4 of A6, rule 2 of A7, and order 9 to 11 of A1.

### Hides

- how the four lower modules are combined into one operation;
- what a crash between two writes leaves behind.

### Must not own

- the token, the HTTP status of a refusal or the request form;
- image decoding, folder walking or file layout;
- any call to the Portal.

### Candidate public capabilities

```text
scan_project_photos
place_project_photos
mark_photo_published
```

### Trace inputs

- A3
- A4
- A7

### Depth assessment

- kind: deep
- hidden mechanism: the replay-safe delivery sequence of one photo across folder, store and records.

## `deliverer_api`

### Owns

- the HTTP surface declared in the manifest;
- the bearer token: reading its file, the start refusal and the constant-time comparison;
- the request form and the project id form;
- the HTTP status of every refusal;
- the system clock given to the operations;
- reading the run settings when the service starts;
- listening on the loopback interface only.

### Knows

- rules 1 to 5 and the project id part of rule 8 of A5, and rules 1 and 3 of A7.

### Hides

- the web framework;
- how a refusal becomes an answer.

### Must not own

- any delivery rule or the order of the checks of `photo_delivery`;
- a Portal credential or client;
- forwarded headers, which the service does not read.

### Candidate public capabilities

```text
create_app
read_token
load_config
```

### Trace inputs

- A5
- A7

### Depth assessment

- kind: deep
- hidden mechanism: the authenticated boundary between one trusted caller and the delivery operations.
