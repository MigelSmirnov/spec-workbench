# State 3 — Portal Deliverer module responsibilities

## Status

Written on 2026-11-18 from the accepted States 0 to 2. The prototype was split into exactly these
modules to test the boundaries. Evidence: `python3 -m pytest -q prototypes/portal_deliverer`
(80 tests), `python3 prototypes/portal_deliverer/e2e_local_portal.py` (26 checks) and
`python3 prototypes/portal_deliverer/e2e_local_syncthing.py` (19 checks on two private Syncthing
instances). The tests `test_modules_name_exactly_the_declared_symbols`,
`test_each_hidden_mechanism_stays_inside_its_module` and `test_no_module_can_call_the_portal` read
the imports of the prototype and fail when a boundary below is broken.

The split found two defects of the prototype. A mark with a malformed source id was answered
`unknown_project` after reading the clock, against A4 rule 2 and A7 rule 2; the section "Order of one
operation" now decides that order, and
`test_a_mark_with_a_malformed_source_id_is_refused_before_the_connection_and_the_clock` holds it. A
confirmation cleared while the service ran did not stop delivery, against R0-11; A5 rule 7 now has
the record read at each operation.

## Dependencies

This table is the complete and minimal list of what each module names directly. There are no
cycles, and `domain_models` names no other module.

| Consumer | Provider | Symbols |
|---|---|---|
| `object_connections` | `domain_models` | `DelivererError`, `ObjectConnection` |
| `source_folder` | `domain_models` | `MIN_AGE_SECONDS`, `MAX_SOURCE_BYTES`, `IGNORED_NAME_PREFIXES`, `IGNORED_NAME_SUFFIXES`, `CONFLICT_COPY_MARK`, `DelivererError`, `Rejected`, `SourceFile` |
| `photo_preparation` | `domain_models` | `MAX_OUTPUT_BYTES`, `MAX_PIXELS`, `PHOTO_MAX_SIDE`, `PHOTO_QUALITY`, `INTAKE_ID_PREFIX`, `INTAKE_SOURCE`, `PreparedPhoto`, `Rejected` |
| `delivery_store` | `domain_models` | `Config`, `DelivererError` |
| `photo_delivery` | `domain_models` | `SOURCE_ID_FORM`, `Config`, `DelivererError`, `Rejected`, `SourceFile` |
| `photo_delivery` | `object_connections` | `confirmed_connection`, `available_photo_folder` |
| `photo_delivery` | `source_folder` | `observe_source_files`, `read_source_bytes` |
| `photo_delivery` | `photo_preparation` | `prepare_photo`, `build_publication` |
| `photo_delivery` | `delivery_store` | `project_lock`, `store_image`, `read_placement`, `write_placement`, `read_mark`, `write_mark` |
| `deliverer_api` | `domain_models` | `MAX_PLACE_ITEMS`, `Config`, `DelivererError` |
| `deliverer_api` | `object_connections` | `load_connections` |
| `deliverer_api` | `photo_delivery` | `scan_project_photos`, `place_project_photos`, `mark_photo_published` |
| `deliverer_api` | `system_clock` | `utc_now` |

`deliverer_api` names `load_connections` only to refuse a start with a broken record. The operations
read the record themselves through `confirmed_connection`, so no module keeps connections in memory.

`system_clock` is the module that `system_clock_backend` generates, and `deliverer_api` alone names it.
`deliverer_api` passes the clock to an operation as a function, and `photo_delivery` calls the function
it receives without naming the module.

## Order of one operation

`deliverer_api` performs the steps marked API and then calls `photo_delivery`, which performs the
rest in the order shown. Only `photo_delivery` takes the project lock.

| Step | Scan | Placement | Mark |
|---|---|---|---|
| 1, API | token | token | token |
| 2, API | project id | request form, project id | request form, project id, `photo_id` |
| 3 | clock | clock | source id |
| 4 | connection | connection | clock |
| 5 | photo folder | photo folder | connection |
| 6 | observe the folder, read records | every source id | take the lock |
| 7 | | take the lock | placement exists |
| 8 | | observe the folder once | existing mark, or write the mark |
| 9 | | each photo in request order: replay, or read, verify, prepare, store the image, write the record | release the lock |
| 10 | | release the lock | |

A scan takes no lock. The source ids of a placement are items of its body and are checked at step 6, as
A3 rule 4 and A7 rule 2 decide. The connections file is read once, at the connection step.

## Rules decided across modules

A decision has one primary owner in `30_trace.json`. Where its rules reach other modules, this table
names the owner of each rule.

| Decision | Rule | Owner |
|---|---|---|
| A1 | order 1 to 8, ignored names, walking order | `source_folder` |
| A1 | order 9 to 11, placed and published status | `photo_delivery` |
| A5 | rules 1 to 4, token and listening address | `deliverer_api` |
| A3 | rule 4, the request form of a placement | `deliverer_api` |
| A3 | rule 4, every other check and its order | `photo_delivery` |
| A4 | rule 2, the form of `photo_id` and its lowercase hyphenated spelling | `deliverer_api` |
| A4 | every other rule | `photo_delivery` |
| A5 | rule 5, the single principal | `deliverer_api` |
| A5 | rule 6, the write that clears a confirmation | the agent, outside this service (R0-11) |
| A5 | rules 7 and 8, reading the file once per operation, judging it and refusing | `object_connections` |
| A5 | rule 9, project id form | `deliverer_api` |
| A5 | rule 9, checking a source id against `SOURCE_ID_FORM` | `photo_delivery` |
| A5 | rule 9, stored names built only from checked identifiers | `delivery_store` |
| A5 | rule 10, what a delivery result holds | `photo_delivery` |
| A5 | rule 10, what a refusal answer holds | `deliverer_api` |
| A6 | rules 1 to 3, stored names, modes, atomic writes, the lock itself | `delivery_store` |
| A6 | rule 4, which checks and writes run inside the lock | `photo_delivery` |
| A7 | rules 1 and 3, the clock and the form of its reading | `system_clock` |
| A7 | rule 2, when an operation reads the clock | `photo_delivery` |
| A7 | rule 4, a file's modification time | `source_folder` |
| A7 | rule 5, the photo moment | `photo_preparation` |

## Invariant owners

| Invariant | Owner |
|---|---|
| INV-01, INV-02, INV-18 | `source_folder` |
| INV-03, INV-04, INV-05, INV-14 | `photo_preparation` |
| INV-06, INV-07, INV-08, INV-12, INV-13 | `photo_delivery` |
| INV-09, INV-11 | `deliverer_api` |
| INV-10 | `object_connections` |
| INV-15 | deployment route (A9) |
| INV-16 | security review record (A10) |
| INV-17 | calling flow (A11), outside this service |

`deliverer_api` owns INV-11 because every answer leaves through it: a refusal carries only its code and
a fixed message. `photo_delivery` supplies path-free results, and no module holds a client for any
outbound call.

## `domain_models`

### Owns

- the models M01 to M07 and their enumerations;
- `SourceFile`, what `source_folder` reports about one file to `photo_delivery`. It holds the server path
  of the file and never leaves the service; M02 is the form a caller sees;
- the policy constants and the run settings of A8;
- the constant `SOURCE_ID_FORM`, which no model applies by itself: a source id stays plain text until
  `photo_delivery` checks it;
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

- reading the connections file once per operation and judging it whole;
- the refusal of a start when the file is not valid;
- the written form of both subfolders, and the resolved containment of the photo folder of the requested
  project. The resolved invoice folder is not checked here (A5 rule 8);
- deciding from that reading whether a project has a confirmed connection;
- deciding whether the photo folder is available and strictly below the resolved root.

### Knows

- M01 and rules 7 and 8 of A5. The agent writes the record and clears its confirmation (rule 6).

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
- computing the SHA-256 source id of each file it reads;
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
- A7
- A8

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

- steps 3 and later of "Order of one operation";
- when an operation reads the clock;
- completing a scan with placed and published status;
- one placement per project and content, replay, and per-photo failure;
- comparing the bytes read for placing with the requested source id (`source_changed`);
- writing the stored image before the placement record;
- one mark per placement, replay and `publication_conflict`;
- which checks and writes run inside the project lock;
- keeping server paths out of every answer.

### Knows

- A3 and A4 without the two request forms given to `deliverer_api` above, rule 4 of A6, rule 2 of A7,
  order 9 to 11 of A1, and the parts of rules 9 and 10 of A5 given to it above.

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

- A1
- A3
- A4
- A5
- A6
- A7

### Depth assessment

- kind: deep
- hidden mechanism: the replay-safe delivery sequence of one photo across folder, store and records.

## `deliverer_api`

### Owns

- the HTTP surface declared in the manifest;
- the bearer token: reading its file, the start refusal and the constant-time comparison;
- steps 1 and 2 of "Order of one operation";
- the HTTP status and the content of every refusal answer;
- handing the clock to the operations;
- reading the run settings when the service starts;
- listening on the loopback interface only.

### Knows

- rules 1 to 5, the project id part of rule 9 and the refusal part of rule 10 of A5;
- the request form of A3 rule 4 and the `photo_id` form of A4 rule 2.

### Hides

- the web framework;
- how a refusal becomes an answer.

### Must not own

- any delivery rule other than these two request forms, or the order of the checks of `photo_delivery`;
- a Portal credential or client;
- forwarded headers, which the service does not read.

### Candidate public capabilities

```text
create_app
read_token
load_config
```

### Trace inputs

- A3
- A4
- A5
- A7

### Depth assessment

- kind: deep
- hidden mechanism: the authenticated boundary between one trusted caller and the delivery operations.

## `system_clock`

### Owns

- the one read of the host clock, as `rules.time_source_policy` declares it (A7 rules 1 and 3).

### Knows

- the form of the current time: UTC without an offset, in microseconds.

### Hides

- the host clock primitive.

### Must not own

- when an operation reads the clock;
- any comparison of instants.

### Candidate public capabilities

```text
utc_now
```

### Trace inputs

- A7

### Depth assessment

- kind: deep
- hidden mechanism: the single authorised read of the host clock.
