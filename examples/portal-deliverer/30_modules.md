# State 3 — Portal Deliverer module responsibilities

## Status

Written on 2026-11-18 from the accepted States 0 to 2. The prototype was split into exactly these
modules to test the boundaries. Evidence: `python3 -m pytest -q prototypes/portal_deliverer`,
`python3 prototypes/portal_deliverer/e2e_local_portal.py` and
`python3 prototypes/portal_deliverer/e2e_local_syncthing.py`, which runs two private Syncthing
instances. The tests `test_modules_name_exactly_the_declared_symbols`,
`test_each_hidden_mechanism_stays_inside_its_module` and `test_no_module_can_call_the_portal` read
the imports of the prototype and fail when a boundary below is broken.

The split found two defects of the prototype. A mark with a malformed source id was answered
`unknown_project` after reading the clock, against A4 rule 2 and A7 rule 2; the section "Order of one
operation" now decides that order, and
`test_a_mark_with_a_malformed_source_id_is_refused_before_the_connection_and_the_clock` holds it. A
confirmation cleared while the service ran did not stop delivery, against R0-11; A5 rule 7 now has
the record read at each operation.

## Dependencies

This table is the complete and minimal list of what each module names directly from the other modules
of this service; the standard library and third-party libraries a module imports are declared by the
imports closure (`65_imports.json`), not here. There are no
cycles, and `domain_models` names no other module.

| Consumer | Provider | Symbols |
|---|---|---|
| `data_provider` | `domain_models` | `ExitStatusRule`, `ObservationFailure`, `ObservationReason`, `PlacementFailure`, `RefusalAnswerRule`, `RefusalCode`, `SourceSignatureRule` |
| `refusals` | `domain_models` | `PlacementFailure`, `RefusalCode` |
| `runtime_settings` | `domain_models` | `RuntimeEnvironment`, `RuntimeSettings` |
| `object_connections` | `domain_models` | `ConnectionEntry`, `ConnectionsFile`, `ObjectConnection`, `RefusalCode` |
| `object_connections` | `refusals` | `DelivererError` |
| `source_folder` | `domain_models` | `ObservationReason`, `PlacementFailure`, `RefusalCode`, `ScanStatus`, `SourceFile`, `SourceRead`, `SourceSignatureRule` |
| `source_folder` | `refusals` | `DelivererError`, `Rejected` |
| `source_folder` | `data_provider` | `CONFLICT_COPY_MARK`, `IGNORED_NAME_PREFIXES`, `IGNORED_NAME_SUFFIXES`, `MAX_SOURCE_BYTES`, `OBSERVATION_FAILURES`, `SOURCE_FORMATS`, `SOURCE_SIGNATURES` |
| `photo_preparation` | `domain_models` | `DateSource`, `PhotoPublication`, `PlacementFailure`, `PreparedPhoto` |
| `photo_preparation` | `refusals` | `Rejected` |
| `photo_preparation` | `data_provider` | `INTAKE_ID_PREFIX`, `INTAKE_ID_SEPARATOR`, `INTAKE_SOURCE`, `MAX_OUTPUT_BYTES`, `MAX_PIXELS`, `PHOTO_BACKGROUND`, `PHOTO_MAX_SIDE`, `PHOTO_OPTIMIZE`, `PHOTO_PROGRESSIVE`, `PHOTO_QUALITY`, `PHOTO_SUBSAMPLING`, `SOURCE_FORMATS`, `CAMERA_EARLIEST_YEAR`, `CAMERA_LATEST_AFTER_MODIFIED_HOURS`, `CAMERA_OFFSET_MAX_HOURS` |
| `delivery_store` | `data_provider` | `LOCK_FILE_MODE`, `RECORD_MODE`, `STATE_FOLDER_MODE`, `STORE_FOLDER_MODE`, `STORED_IMAGE_MODE`, `TEMPORARY_FILE_MODE`, `TEMPORARY_NAME_PREFIX`, `LOCKS_FOLDER`, `PLACEMENTS_FOLDER`, `MARKS_FOLDER`, `LOCK_FILE_SUFFIX`, `RECORD_FILE_SUFFIX`, `STORED_IMAGES_FOLDER`, `STORED_IMAGE_SUFFIX` |
| `delivery_store` | `domain_models` | `DeliveryContext`, `PhotoPlacement`, `PublicationMark`, `RefusalCode` |
| `delivery_store` | `refusals` | `DelivererError` |
| `photo_delivery` | `domain_models` | `DeliveryContext`, `MarkOutcome`, `MarkStatus`, `PhotoPlacement`, `PlacementFailure`, `PlacementOutcome`, `PlacementStatus`, `PublicationMark`, `RefusalCode`, `ScanResult`, `ScanStatus`, `SourceFile`, `SourcePhotoObservation` |
| `photo_delivery` | `refusals` | `DelivererError`, `Rejected` |
| `photo_delivery` | `data_provider` | `OBSERVATION_FAILURES`, `SOURCE_ID_PATTERN`, `STORED_MEDIA_TYPE` |
| `photo_delivery` | `object_connections` | `available_photo_folder`, `confirmed_connection` |
| `photo_delivery` | `source_folder` | `observe_source_files`, `read_named_source` |
| `photo_delivery` | `photo_preparation` | `build_publication`, `prepare_photo` |
| `photo_delivery` | `delivery_store` | `project_lock`, `read_mark`, `read_placement`, `store_image`, `write_mark`, `write_placement` |
| `photo_delivery` | `system_clock` | `utc_now` |
| `deliverer_api` | `data_provider` | `REFUSAL_ANSWERS` |
| `deliverer_api` | `domain_models` | `HealthAnswer`, `HealthStatus`, `Refusal`, `RefusalAnswerRule`, `RefusalCode` |
| `deliverer_api` | `refusals` | `DelivererError` |
| `deliverer_router` | `domain_models` | `DeliverRequest`, `DeliveryContext`, `HealthAnswer`, `MarkOutcome`, `PlacementOutcome`, `PublishedRequest`, `RefusalCode`, `ScanResult` |
| `deliverer_router` | `refusals` | `DelivererError` |
| `deliverer_router` | `deliverer_api` | `AuthenticationRequired`, `answer_health`, `check_token`, `parse_project_id`, `refusal_answer` |
| `deliverer_router` | `photo_delivery` | `deliver_project_photo`, `mark_photo_published`, `scan_project_photos` |
| `deliverer_service` | `data_provider` | `BIND_HOST`, `EXIT_STATUSES`, `TOKEN_ALPHABET`, `TOKEN_ENCODING`, `TOKEN_MIN_LENGTH`, `TOKEN_TRIM_CHARACTERS` |
| `deliverer_service` | `domain_models` | `DeliveryContext`, `RuntimeSettings`, `ServiceExit` |
| `deliverer_service` | `runtime_settings` | `load_runtime_settings` |
| `deliverer_service` | `object_connections` | `load_connections` |
| `deliverer_service` | `deliverer_router` | `create_app` |

`deliverer_service` names `load_connections` only to refuse a start with a broken record. Each operation
reads the record itself at its connection check, so no module keeps connections in memory.

`deliverer_router` is the module that `http_router_backend` generates with its `fastapi_sync_v2` backend, and it
holds only what that backend emits. It serves every route as a table route: the body of a delivery and of a mark
is read as = models.DeliverRequest and = models.PublishedRequest, the token is compared by `check_token` of
`deliverer_api` before the body is read, the project id is judged by its `parse_project_id`, and the route
then calls one operation of `photo_delivery`. `AuthenticationRequired`, every `DelivererError` and a request whose
body or form the framework refuses are each answered by `refusal_answer` of `deliverer_api`, so every refusal
leaves as M08 (A5 rules 1, 9 and 10). `deliverer_api` therefore cannot import the router back.

`system_clock` is the module that `system_clock_backend` generates, and `photo_delivery` alone names it.

## Order of one operation

`deliverer_router` performs the steps marked API, the token and the project id through `deliverer_api`, and
then calls `photo_delivery`, which performs the rest in the order shown. Only `photo_delivery` takes the project lock.

| Step | Scan | Delivery | Mark |
|---|---|---|---|
| 1, API | token | token | token |
| 2, API | project id | request form, project id | request form, project id, `photo_id` |
| 3 | connection | connection | source id |
| 4 | photo folder | photo folder | clock |
| 5 | observe the folder, read records | source id | connection |
| 6 | | take the lock | take the lock |
| 7 | | existing placement: replay | placement exists |
| 8 | | read the named file once, check it, prepare, store the image, write the record | existing mark, or write the mark |
| 9 | | release the lock | release the lock |

A scan takes no lock. Only a mark reads the clock. The connections file is read once, at the connection
step.

## Rules decided across modules

A decision has one primary owner in `30_trace.json`. Where its rules reach other modules, this table
names the owner of each rule.

| Decision | Rule | Owner |
|---|---|---|
| A1 | orders 1 to 6, ignored names, walking order | `source_folder` |
| A1 | orders 7 to 9, placed and published status | `photo_delivery` |
| A5 | rule 1, reading the single `Authorization` field in the Bearer scheme, before the identifiers and the body | `deliverer_router` |
| A5 | rule 1, the comparison of the token | `deliverer_api` |
| A5 | rules 2 to 4, the token file, its replacement and the listening address | `deliverer_service` |
| A3 | rule 4, the request form of a placement | `deliverer_router` |
| A3 | rule 5, condition 1, whether a name is a path that may be opened | `source_folder` |
| A3 | rule 4, every other check and its order; rules 2, 3, 6 to 10 and the rest of rule 5 | `photo_delivery` |
| A4 | rule 2, the form of `photo_id` and its lowercase hyphenated spelling | `deliverer_router` |
| A4 | every other rule | `photo_delivery` |
| A5 | rule 5, the single principal | `deliverer_api` |
| A5 | rule 6, the write that clears a confirmation | the agent, outside this service (R0-11) |
| A5 | rules 7 and 8, reading the file once per operation, judging it and refusing | `object_connections` |
| A5 | rule 9, project id form | `deliverer_api` |
| A5 | rule 9, checking a source id against `SOURCE_ID_PATTERN` | `photo_delivery` |
| A5 | rule 9, stored names built only from checked identifiers | `delivery_store` |
| A5 | rule 10, what a delivery result holds | `photo_delivery` |
| A5 | rule 10, what a refusal answer holds | `deliverer_api` |
| A6 | rules 1 to 3, stored names, modes, atomic writes, the lock itself | `delivery_store` |
| A6 | rule 4, which checks and writes run inside the lock | `photo_delivery` |
| A6 | rule 5, damaged records, a failed lock and a mark that cannot be written | `delivery_store` |
| A7 | rules 1 and 3, the clock and the form of its reading | `system_clock` |
| A7 | rule 2, when an operation reads the clock | `photo_delivery` |
| A7 | rule 4, a file's modification time | `source_folder` |
| A7 | rule 5, the photo moment | `photo_preparation` |
| A8 | reading each run setting, its default, and the refusal of a missing required setting or of a value of the wrong form | `runtime_settings` |
| A8 | the refusal of a well-formed port above 65535 and of a time zone the database does not know | `deliverer_service` |

## Invariant owners

| Invariant | Owner |
|---|---|
| INV-01, INV-02, INV-18 | `source_folder` |
| INV-20 | `delivery_store` |
| INV-03, INV-04, INV-05, INV-14 | `photo_preparation` |
| INV-06, INV-07, INV-08, INV-12, INV-13, INV-19 | `photo_delivery` |
| INV-09, INV-11 | `deliverer_api` |
| INV-10 | `object_connections` |
| INV-15 | deployment route (A9) |
| INV-16 | security review record (A10) |
| INV-17 | calling flow (A11), outside this service |

`deliverer_api` owns INV-11 because every refusal answer is built by its `refusal_answer`: a refusal carries
only its code and a fixed message. `photo_delivery` supplies path-free results, and no module holds a client for any
outbound call.

## `domain_models`

### Owns

- the models M01 to M08 and their enumerations;
- `SourceFile`, what `source_folder` reports about one file to `photo_delivery`. It holds the server path
  of the file and never leaves the service; M02 is the form a caller sees;
- the type of the run settings, and `DeliveryContext`, the context of the operations that `deliverer_service` builds from them:
  binary store, state folder, time zone and connections file;
- the types that cross module boundaries without a meaning of their own in State 1: `SourceRead`, a `SourceFile`
  with the bytes that were judged; `ScanResult`, the observations of one scan and the count of each status;
  `MarkOutcome`, M07 with its `MarkStatus`; `DeliverRequest` and `PublishedRequest`, the bodies of two routes; and
  `HealthAnswer`, the body of the health route;
- `RefusalAnswerRule`, the row form of the refusal answers that `data_provider` holds: a refusal code with its
  status and `detail`; and `SourceSignatureRule`, the row form of the format signatures that `data_provider`
  holds: a format, a byte offset and the signature written in lowercase hexadecimal; and `ObservationFailure`,
  the row form of the correspondence of a scan's rejection reason with a delivery's failure; and
  `ExitStatusRule`, the exit status of each `ServiceExit` outcome of the service (A8);
- no exception type: those belong to `refusals` and `deliverer_api`.

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

## `refusals`

### Owns

- `DelivererError`, the refusal of a whole operation, whose code is a member of = models.RefusalCode and
  becomes M08;
- `Rejected`, the refusal of one file, whose reason is a member of = models.PlacementFailure and becomes the
  failure of that photo.

### Knows

- the two vocabularies those refusals carry, and nothing about when they are raised.

### Hides

- nothing beyond the two exception types; this is shared vocabulary, as `domain_models` is for values.

### Must not own

- any rule that decides a refusal, or the answer a refusal becomes.

### Public surface

```text
DelivererError
Rejected
```

### Trace inputs

- A3
- A5

### Depth assessment

- kind: deep
- hidden mechanism: none beyond the two exception types; the shared refusal vocabulary of the service.

## `data_provider`

### Owns

- the policy constants of A8, as typed values.

### Knows

- nothing but those values.

### Hides

- where each decided value is written down.

### Must not own

- any behaviour, check or default of a run setting.

### Public surface

```text
MAX_SOURCE_BYTES
MAX_OUTPUT_BYTES
MAX_PIXELS
PHOTO_MAX_SIDE
PHOTO_QUALITY
INTAKE_ID_PREFIX
INTAKE_SOURCE
IGNORED_NAME_PREFIXES
IGNORED_NAME_SUFFIXES
CONFLICT_COPY_MARK
SOURCE_ID_PATTERN
TOKEN_MIN_LENGTH
TOKEN_TRIM_CHARACTERS
REFUSAL_ANSWERS
STORED_IMAGE_MODE
STORE_FOLDER_MODE
RECORD_MODE
STATE_FOLDER_MODE
LOCK_FILE_MODE
TEMPORARY_NAME_PREFIX
TEMPORARY_FILE_MODE
PHOTO_OPTIMIZE
PHOTO_PROGRESSIVE
PHOTO_SUBSAMPLING
PHOTO_BACKGROUND
LOCKS_FOLDER
PLACEMENTS_FOLDER
MARKS_FOLDER
LOCK_FILE_SUFFIX
RECORD_FILE_SUFFIX
SOURCE_FORMATS
SOURCE_SIGNATURES
CAMERA_EARLIEST_YEAR
CAMERA_LATEST_AFTER_MODIFIED_HOURS
CAMERA_OFFSET_MAX_HOURS
STORED_IMAGES_FOLDER
STORED_IMAGE_SUFFIX
STORED_MEDIA_TYPE
INTAKE_ID_SEPARATOR
TOKEN_ENCODING
TOKEN_ALPHABET
BIND_HOST
EXIT_STATUSES
OBSERVATION_FAILURES
```

### Trace inputs

- A8

### Depth assessment

- kind: deep
- hidden mechanism: the one home of each decided value.

## `runtime_settings`

### Owns

- reading the run settings of A8 from the environment of the process;
- the default of each optional setting, and the refusal of a missing required setting or of a value of the
  wrong form.

### Knows

- the environment variables of A8.

### Hides

- how the environment is read and validated.

### Must not own

- checking that a path exists, which the modules that use it do;
- the policy constants of A8.

### Candidate public capabilities

```text
load_runtime_settings
```

### Trace inputs

- A8

### Depth assessment

- kind: deep
- hidden mechanism: the single boundary between the environment of the process and the service.

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
- ignored names, links, source limits and file signatures;
- computing the SHA-256 source id of each file it reads;
- deciding whether a requested name passes condition 1 of A3 rule 5, and reading that file once without
  following a link;
- the modification time of a file in the service's time form.

### Knows

- A1 orders 1 to 6, condition 1 of A3 rule 5, and rule 4 of A7.

### Hides

- directory traversal and the handling of files that disappear during it;
- how a partial listing becomes `folder_unavailable`;
- how the rows of `SOURCE_SIGNATURES` are matched against the first bytes of a file.

### Must not own

- any write, in any folder;
- whether a photo was placed or published;
- decoding an image.

### Candidate public capabilities

```text
observe_source_files
read_named_source
```

### Trace inputs

- A1
- A3
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
- atomic writing of one file, and creating the missing folders below the binary store and the state
  folder, which the installation creates;
- the reference of a stored image and its containment in the binary store;
- the per-project lock across processes;
- reading and writing placement and mark records, and refusing with the STATE_UNAVAILABLE member of
  = models.RefusalCode as A6 rule 5 decides. A placement record that cannot be written is the failure of that photo (A3 rule 5).

### Knows

- rules 1 to 3 and 5 of A6 and the lock of rule 4.

### Hides

- the layout of the state folder and the binary store;
- temporary names, disk synchronisation and renaming;
- the operating system lock.

### Must not own

- whether a placement or mark may be written;
- the meaning of a replay or a conflict;
- removal of a placement, a mark or a stored image, which the first version does not offer (A3);
  removing its own temporary file after a failed write (A6 rule 3) is not such a removal.

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
- comparing the hash of the bytes read with the requested source id (`source_changed`);
- turning a rejected file or a failed preparation into the failure of that photo (A3 rule 5);
- writing the stored image before the placement record;
- one mark per placement, replay and `publication_conflict`;
- which checks and writes run inside the project lock;
- keeping server paths out of every answer.

### Knows

- `system_clock` as its source of the current time, A3 and A4 without the two request forms given to `deliverer_router` above, rule 4 of A6, rule 2 of A7,
  orders 7 to 9 of A1, and the parts of rules 9 and 10 of A5 given to it above.

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
deliver_project_photo
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

- the answer of the health route;
- the comparison of the token in constant time and the one principal of A5 rule 5;
- the form of a project id (A5 rule 9);
- the status and the content of every refusal answer;
- `AuthenticationRequired`, the refusal of a request that does not carry the token.

### Knows

- rules 1 and 5, the project id part of rule 9 and the refusal part of rule 10 of A5.

### Hides

- how a token is compared and how a refusal becomes an answer.

### Must not own

- the routes, the reading of a request or its body, or the order of the checks of `photo_delivery`;
- the token file, the run settings or the start of the service;
- a Portal credential or client;
- forwarded headers, which the service does not read.

### Candidate public capabilities

```text
answer_health
```

### Trace inputs

- A5
- A8

### Depth assessment

- kind: deep
- hidden mechanism: the authenticated boundary between one trusted caller and the delivery operations.

## `deliverer_router`

### Owns

- the routes of the service, the request forms of a delivery and a mark, the reading of the single
  `Authorization` field in the Bearer scheme by the extractor the backend emits, and the context and token the
  routes read from the application.

### Knows

- the routes, their operations, the order of A5 rule 1 (the token before the identifiers and the body), the
  request form of A3 rule 4 and the `photo_id` form of A4 rule 2.

### Hides

- the web framework that serves the routes.

### Must not own

- any check other than the request forms it reads by their models, or any delivery rule;
- the content of an answer: every refusal is answered by `refusal_answer` of `deliverer_api`;
- anything `http_router_backend` does not emit.

### Candidate public capabilities

```text
create_app
```

### Trace inputs

- A3
- A4
- A5

### Depth assessment

- kind: deep
- hidden mechanism: the binding of operations to methods and paths, generated from the route closure.

## `deliverer_service`

### Owns

- the start of the service: the context of the operations and the token file;
- listening on the loopback interface only.

### Knows

- rules 2 to 4 of A5 and the run settings of A8.

### Hides

- how the token file is opened and judged, and the server that listens.

### Must not own

- any answer to a request;
- the comparison of a presented token.

### Candidate public capabilities

```text
read_token
load_config
run_service
```

### Trace inputs

- A5
- A8

### Depth assessment

- kind: deep
- hidden mechanism: the single path from the environment and the token file to a listening service.

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
