# State 2 — Portal Deliverer rules and decisions

## Status

Written on 2026-11-18 from the accepted product frame, the models and the running prototype. The
owner accepted on 2026-11-18 the single principal and HTTPS rules of A5, the values of A8, the
dependency policy of A9 and the absence of removal in the first version (A3).

OQ-07 is the one earlier question still open: A5 decides the HTTPS rule, and the host and route are
carried to deployment.
The tests named below live in `prototypes/portal_deliverer/test_deliverer.py` of the Factory
repository; E2E names a check of `e2e_local_portal.py`. They are evidence of the prototype. The
checks that witness the generated service are bound after State 7.

## Accepted decision A1 — What a file of the folder becomes

### Normative rules

A scan gives each regular file of the photo folder exactly one status. The first rule that
applies decides:

| Order | Condition | Status | Reason |
|---|---|---|---|
| 1 | empty | `rejected` | `empty` |
| 2 | larger than the source limit | `rejected` | `too_large` |
| 3 | opened in non-blocking mode without following a link, what it finds is not a regular file | `rejected` | `not_a_regular_file` |
| 4 | it grew past the source limit while being read | `rejected` | `too_large` |
| 5 | opening or reading it fails, which includes a file that disappeared or became a symbolic link after its metadata was read | `rejected` | `unreadable_file` |
| 6 | does not begin with a JPEG, PNG or WEBP signature | `rejected` | `unsupported_format` |
| 7 | placed and marked | `published` | none |
| 8 | placed | `placed` | none |
| 9 | anything else | `ready` | none |

A scan covers the photo folder and all its subfolders (R0-12). When the photo folder, or a subfolder
that is not ignored and is still a folder, cannot be opened or listed, the whole operation is refused
with `folder_unavailable`, so a partial scan is never reported as complete; a listed subfolder that has
become a symbolic link or another object is the one exception, decided below. A file exactly at the source limit passes that rule. A file that
disappears before its metadata is read is not reported. Files with the same content are each reported,
with the same source id. A rejected file has no source id.

Files are visited folder by folder: the files of a folder in order of their names, then its
subfolders in order of their names, compared by Unicode code point.

A name is ignored at every level of the path when, after the letters A to Z are lowered and no other
character is changed, it begins with an item of the imported `IGNORED_NAME_PREFIXES` constant, ends with
an item of the imported `IGNORED_NAME_SUFFIXES` constant, or contains the imported `CONFLICT_COPY_MARK`
constant, the mark of a Syncthing conflict copy (R0-14). Names beginning with a dot include Syncthing's
`.syncthing.*`, `.stfolder` and `.stversions` and the phone's `.trashed-*` files. A file Syncthing is still
writing lies under such a temporary name. Ignored names are not reported, ignored folders are not entered,
and an entry the listing shows as a symbolic link is neither reported nor followed.

Syncthing may change the folder during a scan, so a scan is not a view of one instant. Each folder is
listed once, in one pass over its entries; an entry added or removed during that pass may or may not be
among them. Each rule applies
to what its step finds when it runs, and the next scan sees the folder as it then stands. A file that
changes while it is read is judged by the bytes that were read, once, without a retry. Syncthing replaces
a finished file by renaming a new one over it; a later delivery judges what it then reads under A3 rule 5.

Every folder is opened without following a link: the photo folder one folder at a time along its
resolved path (A5 rule 8), and each subfolder in the folder that holds it. A folder is listed, its entries
are read and its files are opened only through the folder that was opened, so an entry replaced by a link
after a check is never followed. A subfolder the listing showed is opened without following a link: when
the opening finds a symbolic link, dangling or not, or an object that is not a folder, it is not entered
and the scan goes on; when the subfolder is gone or the opening fails for any other reason, the scan is
refused as for a subfolder that cannot be listed. When the listing reaches an entry, one metadata reading of that
entry in its opened folder, without following a link, decides that it is a regular file and gives its
listed size and modification time; an entry that reading does not show as a regular file is not
reported, and a reading that fails other than for a file that disappeared refuses the scan with
`folder_unavailable`. Orders 1 and 2 are first decided by that size, before the file is
opened. A file is then opened in that same opened folder: an opening that fails, or a failed metadata reading of the opened file,
is order 5, and an opened object that is not a regular file is order 3; either ends the work on that file
before any byte is read. Otherwise it is read once, up to one byte past the imported `MAX_SOURCE_BYTES` constant: reaching
that byte is order 4, and the read stops there. Read once means one pass over the opened file from its
start, continued after a short read until the end of the file or that byte; the file is not opened or read
again. A read that reaches the end of the file with no bytes is order 1. A file that is read takes its modification time from one metadata reading of the file that was
opened, the one whose bytes are read, taken after the opening and before the read; A7 rule 4 gives its
form, and a delivery uses that time under A2 rule 3.

A scan only reads the source folder. A signature does not prove that an image can be decoded: a `ready`
file may still fail when it is delivered.

### Formal invariants

- INV-01: no operation creates, changes, moves or deletes anything in a source folder.
- INV-02: a delivery opens no path that fails condition 1 of A3 rule 5.
- INV-18: a scan never reports a Syncthing conflict copy.

### Required tests

- INV-01: after a scan, a placement, a repeated placement and a mark, the source folder holds the same files with the same bytes, modification times and modes (`test_no_operation_changes_the_source_folder`).
- INV-02: for content with no placement, an empty or absolute name, a name with an empty, `.` or `..` segment, an ignored name at any level, a folder, and a path through a symbolic link each fail with the NOT_READY_OR_ABSENT member of = models.PlacementFailure and add no file except the project lock (`test_a_name_a_scan_would_not_report_is_not_delivered`).
- INV-18: a conflict copy in the folder and in a subfolder, each with the mark in lower, upper and mixed case, is absent from the scan (`test_a_syncthing_conflict_copy_is_neither_offered_nor_placed`). Only the letters A to Z are folded (`test_only_ascii_letters_fold_in_the_conflict_mark`). A real Syncthing conflict leaves its copy unreported while the photo itself is still reported (`e2e_local_syncthing.py`, `a real Syncthing conflict copy is not offered`).

### Consequence

A replaced file is scanned again by its new content (A3).

## Accepted decision A2 — What reaches the Portal store

### Normative rules

1. A stored image is a newly encoded JPEG made from the decoded pixels of the source, by exactly these
   operations of the image library at the version A9 pins, whose arithmetic (conversion formulas,
   resampling, rounding of sizes, alpha compositing and encoding) is that library's:
   `ImageOps.exif_transpose` applies the camera orientation to the first frame; `Image.convert` to
   `RGBA` converts the decoded samples, without colour management and without a colour profile;
   `Image.thumbnail` with the `LANCZOS` filter and a box of the imported `PHOTO_MAX_SIDE` constant on
   each side reduces the image when a side is larger than that box, keeping its proportion; the result
   is pasted onto an `RGB` image of the same size filled with the colour of the imported
   `PHOTO_BACKGROUND` constant, white, with its own alpha channel as the mask, so transparent areas
   become white; and `Image.save` writes a JPEG with the imported constants `PHOTO_QUALITY` as
   `quality`, `PHOTO_OPTIMIZE` as `optimize`, `PHOTO_PROGRESSIVE` as `progressive` and
   `PHOTO_SUBSAMPLING` as `subsampling`, with no EXIF, colour profile or other metadata. With one library version one source gives the same bytes. `sha256`
   and `size` of M04 describe the bytes that were stored, and a repeated delivery returns that placement
   without encoding again (A3 rule 2).
2. The source may be JPEG, PNG or WEBP. Checks run in this order: a first frame above the pixel
   limit (width times height) fails with `too_many_pixels`, a source that cannot be decoded with
   `unreadable_image`, and a result above the Portal's read limit with `too_large`. A value equal
   to a limit passes. Only the first frame of an animated image is delivered.
3. The photo moment is the first usable value of: EXIF `DateTimeOriginal`, EXIF `DateTime`, then
   the file's modification time. `DateTimeOriginal` uses `OffsetTimeOriginal` when that offset has
   the form `+HH:MM` or `-HH:MM` with hours up to 14 and minutes up to 59; otherwise it is read in the time zone of the `timezone` field of the run settings (A8), and so is
   `DateTime`. A camera value is unusable when it is malformed, when its UTC year
   is before 2000, or when it is more than 24 hours after the file's modification time.
4. The photo date is delivered as UTC without an offset, as the Client Portal stores it. A camera
   time with no offset is read in the time zone of that `timezone` field. A local time that occurs twice is the
   first occurrence, and a local time that does not exist is read with the offset in force before
   the clock change. A modification time is an absolute instant converted to UTC.
5. The publication body has `client_visible` false, no section and no caption (R0-06, R0-12). The
   owner sets a section or caption in the Portal. `intake_id` and `intake_source` are as M05 states. Its
   `photo_date` is the `taken_at` of M03, unchanged.

### Formal invariants

- INV-03: a stored image carries no EXIF, GPS, XMP or comment of its source.
- INV-04: every delivered photo date is UTC without an offset.
- INV-05: every publication body the deliverer builds has `client_visible` false.

### Required tests

- INV-03: a source holding GPS, EXIF, XMP and a comment is stored with none of them, by the unit test `test_a_placed_photo_keeps_no_metadata_and_the_source_is_untouched` and by the E2E check that the client's download has no EXIF.
- INV-04: camera times with an offset, without one, implausible or absent give the expected UTC value (`test_the_photo_date_is_naive_utc`).
- INV-05: every publication body returned by a placement has `client_visible` exactly false, and a published delivery is absent from the client's overview until the owner shows it (E2E, `a delivered photo stays hidden from the client`).

### Consequence

The owner decides what a client sees. Originals never leave the Syncthing folder.

## Accepted decision A3 — One placement per project and content

### Normative rules

1. A placement is identified by the project and the SHA-256 of the source content (R0-10).
2. Delivering content that already has a placement answers `replayed` with the stored placement and the
   current `photo_id` of its mark, if any, and writes nothing, whatever name the request carries and even
   when the source file has left the folder. A mark record of that placement that is damaged refuses the
   delivery under A6 rule 5.
3. One call delivers one photo, named by `name`, a relative path in the form a scan reports, and
   `source_id`. The service keeps no memory of earlier scans: it judges the name and the file when the call
   runs. A named file that passes condition 1 of rule 5 and that A1 orders 1 and 2 do not reject from its
   metadata is opened, and unless the opening decides A1 order 3 or 5, read once; the bytes that were read
   are the bytes judged, hashed and prepared.
4. Checks run in this order: token, request form and project id, connection, photo folder, source id,
   project lock, existing placement, named file. The request form is a body holding only `name` and
   `source_id`, both strings. A defect of that form or of the project id refuses the whole request with
   `invalid_request` (A5 rule 9). A
   `source_id` that does not match the imported `SOURCE_ID_PATTERN` constant in full is refused with
   `invalid_source_id`.
5. A photo that cannot be delivered is answered with the FAILED member of = models.PlacementStatus and one member of
   `= models.PlacementFailure`. Condition 1 is decided from the name, then by opening the photo folder and
   each folder of the name in turn, each in the one before it and without following a link, and by one
   metadata reading of the last segment in the last folder opened, without following a link; the file is
   then opened in that folder, so it is read from the folders that were checked. Inspecting a folder of
   the path is opening it as a folder, never reading a file of it; only the last segment is opened for
   reading (INV-02). Condition 2 applies A1 as A1 decides it: orders 1 and 2 first from that same
   metadata, before the file is opened, then the read. Conditions 3 and 4 follow the read. Conditions 1 to 4 write nothing except the
   project lock (A6 rule 4). After condition 5 a stored image may remain without a record: no caller has received
   its reference, and a repeated delivery of the same file writes it again and completes the placement,
   unless a refusal of A6 rule 5 applies.

   | Order | Condition | Member |
   |---|---|---|
   | 1 | `name` is not non-empty segments joined by single `/` characters, or a segment is `.` or `..`, or a segment is ignored under A1, or a folder on its path cannot be opened as a folder without following a link, because it is absent, is a symbolic link, is not a folder or the opening fails, or the last segment is absent or is not a regular file, or its metadata cannot be read. Names are compared exactly, without Unicode normalisation | `NOT_READY_OR_ABSENT` |
   | 2 | A1 orders 1 to 6 reject the file | `EMPTY` for order 1, `TOO_LARGE` for orders 2 and 4, `NOT_A_REGULAR_FILE` for order 3, `UNREADABLE_FILE` for order 5, `UNSUPPORTED_FORMAT` for order 6 |
   | 3 | the hash of the bytes differs from `source_id` | `SOURCE_CHANGED` |
   | 4 | A2 rule 2 fails | `TOO_MANY_PIXELS`, `UNREADABLE_IMAGE` or `TOO_LARGE`, as that rule decides |
   | 5 | writing the stored image or the record fails | `UNREADABLE_FILE` |

6. The stored image is written before the placement record, so a crash between them repeats the
   placement and leaves no record without an image.
7. A replaced source is a new photo. The earlier placement, its stored image and its mark stay.
   Removing a source changes no placement (R0-10).
8. The first version offers no removal of a placement, a mark or a stored image. Removal of a
   hidden photo is designed in the Portal (client-portal Q27).
9. A conflict copy is never the source of a new placement (R0-14). An ordinary file with the same
   content as a conflict copy is delivered as usual, and content that already has a placement replays
   under rule 2.
10. What to deliver, in which order and what to repeat is decided by the caller (R0-15).

### Formal invariants

- INV-06: at most one placement exists per project and source content, and a repeated placement writes nothing.
- INV-07: replacing or removing a source file changes no earlier placement, stored image or mark.
- INV-19: a new placement never reads a conflict copy.

### Required tests

- INV-06: a second placement returns the first publication and leaves every stored image and placement record unchanged, with one placement record in place (`test_a_repeated_placement_writes_no_durable_state`). When no refusal of A6 rule 5 applies, a delivery repeated after a failed record write completes the placement (`test_a_delivery_repeated_after_a_failed_record_write_completes`).
- INV-07: a replaced file is reported as a new `ready` photo while the earlier image and mark stay (`test_a_replaced_file_is_a_new_photo_and_the_first_delivery_stays`), and a removed file keeps its delivery (`test_removing_a_file_keeps_its_delivery`).
- INV-19: delivering content that has no placement under the name of a conflict copy fails with the NOT_READY_OR_ABSENT member of = models.PlacementFailure, adds no file except the project lock and changes no existing file (`test_a_syncthing_conflict_copy_is_neither_offered_nor_placed`). Placed content replays when only a conflict copy still holds it (`test_placed_content_replays_when_only_a_conflict_copy_still_holds_it`), and an ordinary file with the content of a conflict copy is delivered (`test_an_ordinary_file_is_placed_when_a_conflict_copy_has_the_same_content`).

### Consequence

The same content in two projects is two deliveries.

## Accepted decision A4 — The publication mark

### Normative rules

1. The calling flow publishes a placed photo, then records the Portal `photo_id` at the deliverer
   (R0-08). It does not publish an item reported as `published`, or a replayed placement that
   carries a `photo_id`.
2. Checks run in this order: token, request form and identifiers, connection, placement. A
   `photo_id` is a UUID, kept in lowercase hyphenated form. A mark needs an existing placement of
   the same project, otherwise it is refused with `not_placed`. The photo folder need not be
   available.
3. The same `photo_id` again answers `replayed` with the first mark. Another `photo_id` is refused
   with `publication_conflict` and nothing changes.
4. The deliverer holds no Portal credential, so it does not verify a `photo_id` with the Portal
   and does not check that a `photo_id` is unused by another placement. It trusts the authenticated
   calling flow for this fact.
5. While a photo is hidden, a flow that lost the Portal's answer repeats the publication and
   receives the same `photo_id`. After the owner has shown the photo the Portal answers 409, and
   the `photo_id` of an unmarked photo cannot be recovered from the Portal. This is a recorded
   limit of the first version.

### Formal invariants

- INV-08: a placement has at most one mark, and a mark never changes after it is written.

### Required tests

- INV-08: a repeated mark keeps the first `marked_at`, and another `photo_id` is refused (`test_marking_again_changes_nothing_and_another_photo_is_refused`). A mark for a source placed only in another project is refused (`test_a_photo_that_was_not_placed_cannot_be_marked`).

### Consequence

A published photo is recognised without any change to the Portal.

## Accepted decision A5 — Access and object connection

### Normative rules

1. Every operation except the health answer requires exactly one `Authorization` field. Its value is
   the scheme `Bearer`, compared without regard to case as HTTP defines an authentication scheme, one
   space and the token, compared whole, case-sensitively and in constant time. A request without that
   field, with more than one, or with any other value is refused with `unauthorized` before its
   identifiers or body are examined.
2. The token is generated with 256 bits from a cryptographic random source and is kept in a UTF-8
   file: the 32 random bytes in URL-safe Base64, 43 characters of `A`-`Z`, `a`-`z`, `0`-`9`, `-` and `_`.
   The path is the `token_file` run setting (A8). At the start it is opened once; its last component is
   opened without following a link, while the folders above it belong to the installation and are
   resolved as they stand. The permissions are those of the opened file and its content is read from it. The file is decoded as UTF-8, a byte sequence that is not
   UTF-8 ending the start, and the characters of the imported `TOKEN_TRIM_CHARACTERS` constant (the ASCII
   space, tab, line feed, carriage return, vertical tab and form feed) are removed at both ends; no other
   character is removed. The service does not start when
   the path is a symbolic link or not a regular file, when the group or others have any permission on
   the file, or when what remains has fewer characters than the imported `TOKEN_MIN_LENGTH` constant or any character that
   is not visible ASCII (`!` to `~`), since a token with such a character could not be presented in
   the `Authorization` header.
3. A token is replaced by writing a new file and restarting the service. The old token then stops
   working. The token is never written to logs, answers, repository files or the manifest.
4. The service listens on the loopback interface. A reverse proxy on the same host terminates
   HTTPS for any caller from outside. The service reads no forwarded header.
5. There is one principal: the calling flow of the owner. It may act on every confirmed connection.
6. A change of an object's root or subfolder writes `assignment_confirmed` false (R0-11). An
   operation on a project with no connection is refused with `unknown_project`, and one with an
   unconfirmed connection with `connection_not_confirmed`. This is decided by the service, not by
   the caller.
7. Each scan, placement and mark reads the connections file exactly once, at its connection check,
   and uses that reading for the whole operation. A change written later applies from the next
   operation without a restart, and an operation that has already read the file finishes on that
   reading. A request refused before its connection check does not read the file. The agent replaces
   the file by writing a complete new file in the same folder and renaming it, so a reading sees the
   complete old file or the complete new one. The file is judged whole before any project is looked
   up, so the first condition that applies decides:

   | Order | Condition | Answer |
   |---|---|---|
   | 1 | the file is absent or cannot be read, is not UTF-8 or valid JSON, does not have the record form, or the subfolders of any record break the form of rule 8 | `folder_unavailable` |
   | 2 | the file holds no record for the project | `unknown_project` |
   | 3 | the project's record is unconfirmed | `connection_not_confirmed` |

   The service does not start when condition 1 applies.
8. The form of a subfolder: the photo and invoice subfolders are non-empty relative paths without
   `..` and are not the root itself. Separately, on each scan and placement the photo folder of the
   requested project must be a folder whose resolved path is strictly below the resolved root,
   otherwise the operation is refused with `folder_unavailable`; so is a root or photo folder that is
   missing, lies in a loop of links or cannot be resolved or inspected for any other reason. The photo folder is then reached by that
   resolved path, opened one folder at a time from the root of the file system without following a link
   at any of them (A1), so the folder that is read is the folder whose containment was checked; a folder
   on that path replaced after the check by a link or by anything that is not a folder cannot be opened,
   and the scan is refused with `folder_unavailable` or the delivery fails under condition 1 of A3 rule 5.
   This second check does not run at the start of the service or for other projects. The deliverer never opens the invoice folder, so
   the resolved path of that folder is checked by the Cabinet Inbox when it moves to this record
   (R0-09).
9. A project id is accepted only in the canonical spelling of a UUID: 36 characters, lowercase
   hexadecimal digits in groups of 8, 4, 4, 4 and 12 joined by hyphens. Any other project id, and a body
   that is not the request form of its operation, is refused with `invalid_request`. A source id must
   match the imported `SOURCE_ID_PATTERN` constant in full. Neither a file name nor any other received
   text becomes part of a stored path.
10. An answer never holds a server path, a credential or text the caller sent. File names are returned
    as plain data. A refusal is answered with M08: its status is the entry of its code in the imported
    `REFUSAL_STATUS` constant and its `detail` the entry of its code in the imported `REFUSAL_DETAIL`
    constant.

### Formal invariants

- INV-09: no operation except the health answer succeeds without the deliverer's token.
- INV-10: nothing is scanned, placed or marked for a project unless the connections file read by that operation is valid and holds a confirmed connection for the project.
- INV-11: the deliverer holds no Portal credential, never calls the Portal, and returns no server path.

### Required tests

- INV-09: every declared route except the health answer refuses a request without the token (`test_every_route_except_health_requires_the_token`); a wrong token, another scheme, a value without its single space and two `Authorization` fields are each refused with 401 and `unauthorized`, while the scheme written `bearer` is accepted (`test_the_api_requires_the_token`); a refused request with a malformed project id or body still answers `unauthorized` (`test_the_token_is_checked_before_the_request_form`).
- INV-10: scan, placement and mark each answer `connection_not_confirmed` for an unconfirmed connection (`test_an_unconfirmed_connection_delivers_nothing`). After a scan has succeeded on the running service, clearing the confirmation makes scan, placement and mark each answer `connection_not_confirmed` and write nothing (`test_a_cleared_confirmation_stops_the_running_service`). For a valid file with no record for the project, scan, placement and mark each answer `unknown_project` and write nothing (`test_a_project_without_a_connection_delivers_nothing`). For an absent file, a file that cannot be opened, a file that is not UTF-8 or JSON, a file of another form and a record that breaks the form of rule 8, also when that record is unconfirmed or belongs to another project, scan, placement and mark each answer `folder_unavailable` and write nothing (`test_unreadable_connections_deliver_nothing`), and the service does not start (`test_the_service_does_not_start_with_an_unreadable_connection_record`). A scan, placement or mark that reaches its connection check reads the file exactly once (`test_each_operation_reads_the_connection_record_once`), a request refused earlier reads it zero times (`test_a_request_refused_before_the_connection_check_does_not_read_the_file`), and a file replaced after the reading does not change the running operation (`test_an_operation_finishes_on_the_reading_it_made`). A connection leaving its root is not loaded (`test_a_connection_cannot_leave_the_object_root`), and a linked folder outside the root is refused (`test_a_photo_folder_linked_out_of_the_root_is_refused`).
- INV-11: answers of scan, place, mark and a refusal contain neither the folder path, the store path nor the state path (`test_the_api_scans_and_places_without_showing_server_paths`), and the generated service has no Portal client, no outbound HTTP dependency and no Portal credential setting. An uppercase or unhyphenated project id and a body that is not the request form each answer 422 with `invalid_request`, no answer repeats what the caller sent (`test_a_malformed_request_is_refused_as_invalid_request`), and every refusal code answers its entries of `REFUSAL_STATUS` and `REFUSAL_DETAIL` (`test_each_refusal_answers_its_status_and_detail`).

### Consequence

A wrong folder cannot deliver photos of another client until the owner confirms it.

## Accepted decision A6 — Stored files and concurrent calls

### Normative rules

1. A stored image is named only from the project id and the source hash:
   `photos/<project_id>/<source_id>.jpg`. The reference must stay inside the binary store: its path,
   resolved with the links of the binary store, must lie below the resolved store. When it does not, or when a link in the store cannot be resolved,
   the delivery is refused as a whole with the UNSAFE_REFERENCE member of = models.RefusalCode, an M08
   and not a failed photo, and no stored image and no record is written. A name built that way cannot
   leave the store, so the refusal is reachable only when a folder of the store is a link that leads out
   of it or that cannot be resolved, such as a loop of links. The binary store is
   written only by the Portal and the deliverer, both installed by the owner; Syncthing and the calling
   agent have no access to it. No other actor changes its folders, so the containment checked before a
   write holds for that write.
2. A stored image has the mode of the imported `STORED_IMAGE_MODE` constant and a state record that of
   the imported `RECORD_MODE` constant, so neither is executable. The installation creates the binary
   store and the state folder; the service creates only folders below them, with the imported
   `STORE_FOLDER_MODE` and `STATE_FOLDER_MODE` constants, and removes none. Below the state folder the
   service follows no symbolic link. The Portal reads a stored image and alone decides who may retrieve
   it. The deliverer has no operation that returns image bytes.
3. Each stored image and record is written atomically: a reader sees the complete file or none, and a
   write that fails leaves the earlier state of its address as it was. A stored image is made durable
   before the record that refers to it is written, so a crash never leaves a record without its image; a
   failure to make it durable fails that write and A3 rule 5 condition 5 applies. A record is the last
   write of its operation: once it is in place the operation has taken effect. A write cut short by a
   crash leaves, besides the folders created for it, which stay under rule 2, at most a temporary file
   whose name begins with the imported `TEMPORARY_NAME_PREFIX` constant, which is never read. A3 decides what a crash between the image and the record means.
4. Deliveries and marks of one project run one at a time, across processes, under an operating
   system lock on one lock file of that project in the state folder. The project lock is that lock file
   together with the folders below the state folder that lead to it. It is created on first use, the lock
   file with the imported `LOCK_FILE_MODE` constant and those folders with the imported
   `STATE_FOLDER_MODE` constant, and is never changed or removed afterwards; its first creation is the
   only write of an operation that writes nothing else. A caller
   waits for the lock without a time limit, and the lock is released when its holder ends. The check
   that a placement or mark exists and its writing happen inside that lock.
5. A record is absent only when nothing exists at its address. A placement or mark record that exists is
   validated against its closed model, and its `project_id` and `source_id` must equal those of its
   address. A record that is a symbolic link, that cannot be read, or that fails that validation is never
   taken for an absent record: the operation is refused with the STATE_UNAVAILABLE member of
   = models.RefusalCode, whose value is `state_unavailable`, and changes no record and no stored image.
   The same refusal answers a lock that cannot be taken, which waiting for another holder is not, and a
   mark that cannot be written.

### Formal invariants

- INV-12: concurrent calls for one project never produce two placements or two marks for one source.
- INV-20: a damaged record never leads to a new placement or a new mark.

### Required tests

- INV-12: concurrent placements of one source, in one process and in separate processes, answer the PLACED member of = models.PlacementStatus once and otherwise its REPLAYED member, and leave one placement record and one stored image (`test_separate_processes_leave_one_placement`), and marks of two `photo_id` values, in one process and in separate processes, answer the MARKED member of = models.MarkStatus once, its REPLAYED member for the same value and the PUBLICATION_CONFLICT member of = models.RefusalCode for the other, and leave one mark record holding the `photo_id` whose call answered MARKED (`test_concurrent_calls_leave_one_placement_and_one_mark`, `test_separate_processes_leave_one_mark`).
- INV-20: with a damaged placement or mark record, scan, delivery and mark each answer M08 with the STATE_UNAVAILABLE member of = models.RefusalCode, the record stays as it was and no placement record, mark record or stored image is added or changed (`test_a_damaged_record_refuses_and_is_never_taken_for_an_absent_one`), a damaged mark without a placement stops a new placement (`test_a_damaged_mark_without_a_placement_stops_a_new_placement`), a mark that cannot be written is refused (`test_a_mark_that_cannot_be_written_is_refused`), and a record that is a link, dangling or not, or that names another source is refused the same way (`test_a_record_not_written_at_its_address_is_refused`).

### Consequence

A repeated action from the workplace cannot duplicate a delivery.

## Accepted decision A7 — Time

### Normative rules

1. The system clock is the one source of the current time, declared as `rules.time_source_policy`
   and reaching code through `system_clock_backend` as the operation `utc_now`.
2. Only a mark reads it, once, after the token, the request form and the identifiers are accepted and
   before the connection is examined or the project lock is taken. A mark refused before that point does
   not read it. A mark refused after it, and a replayed mark, have read it and write nothing. Scan, delivery
   and the health answer never read it.
3. The current time is a `datetime` in UTC without an offset, with microsecond precision and no
   rounding, written in ISO 8601 form as `YYYY-MM-DDTHH:MM:SS`, followed by `.` and six digits when
   the microseconds are not zero, with no offset. Every instant of a record and an answer is written
   so. It sets `marked_at`.
4. A file's modification time is converted to the same form before it is compared or delivered, dropping
   any fraction finer than a microsecond toward the earlier instant.
5. The photo moment comes from the file, as A2 decides, and never from the service clock.

### Formal invariants

- INV-13: a mark reads the service clock at most once, and no other operation reads it.

### Required tests

- INV-13: a counting clock is read once by a mark and not at all by a scan, a delivery or the health answer (`test_only_the_mark_reads_the_clock`), and `marked_at` equals that reading (`test_a_marked_photo_is_reported_as_published`).

### Consequence

Every instant the deliverer writes has the form the Portal stores.

## Accepted decision A8 — Decided values

### Normative rules

Run settings are fields of the settings object, read from the environment of the process. A variable
that is set but empty counts as absent: a required one ends the start, an optional one takes its
default. `PORTAL_DELIVERER_PORT` is decimal ASCII digits for a number from 1 to 65535, and anything else
ends the start. A time zone the time zone database does not know ends the start:

| Field | Type | Environment variable | Decided |
|---|---|---|---|
| `timezone` | `str` | `PORTAL_DELIVERER_TIMEZONE` | optional, `Europe/Madrid` when absent |
| `binary_root` | `str` | `PORTAL_DELIVERER_BINARY_ROOT` | required, per installation |
| `state_dir` | `str` | `PORTAL_DELIVERER_STATE_DIR` | required, per installation |
| `connections_file` | `str` | `PORTAL_DELIVERER_CONNECTIONS_FILE` | required, per installation |
| `token_file` | `str` | `PORTAL_DELIVERER_TOKEN_FILE` | required, per installation |
| `port` | `int` | `PORTAL_DELIVERER_PORT` | optional, 8850 when absent |

Policy values are constants of the data provider:

| Constant | Type | Value |
|---|---|---|
| `MAX_SOURCE_BYTES` | `int` | 41 943 040 |
| `MAX_OUTPUT_BYTES` | `int` | 26 214 400 |
| `MAX_PIXELS` | `int` | 80 000 000 |
| `PHOTO_MAX_SIDE` | `int` | 2000 |
| `PHOTO_QUALITY` | `int` | 85 |
| `INTAKE_ID_PREFIX` | `str` | `deliverer-photo-` |
| `INTAKE_SOURCE` | `str` | `syncthing` |
| `IGNORED_NAME_PREFIXES` | `tuple[str, ...]` | `.`, `~syncthing~` |
| `IGNORED_NAME_SUFFIXES` | `tuple[str, ...]` | `.tmp`, `~` |
| `CONFLICT_COPY_MARK` | `str` | `.sync-conflict-` |
| `SOURCE_ID_PATTERN` | `str` | `[0-9a-f]{64}` |
| `TOKEN_MIN_LENGTH` | `int` | 32 |
| `TOKEN_TRIM_CHARACTERS` | `str` | space, tab, line feed, carriage return, vertical tab, form feed |
| `STORED_IMAGE_MODE` | `int` | 0o644 |
| `STORE_FOLDER_MODE` | `int` | 0o755 |
| `RECORD_MODE` | `int` | 0o600 |
| `STATE_FOLDER_MODE` | `int` | 0o700 |
| `LOCK_FILE_MODE` | `int` | 0o600 |
| `TEMPORARY_NAME_PREFIX` | `str` | `.tmp-` |
| `TEMPORARY_FILE_MODE` | `int` | 0o600 |
| `LOCKS_FOLDER` | `str` | `locks` |
| `PLACEMENTS_FOLDER` | `str` | `ledger` |
| `MARKS_FOLDER` | `str` | `published` |
| `LOCK_FILE_SUFFIX` | `str` | `.lock` |
| `RECORD_FILE_SUFFIX` | `str` | `.json` |
| `PHOTO_OPTIMIZE` | `bool` | true |
| `PHOTO_PROGRESSIVE` | `bool` | false |
| `PHOTO_SUBSAMPLING` | `str` | `4:2:0` |
| `PHOTO_BACKGROUND` | `tuple[int, int, int]` | (255, 255, 255) |
| `REFUSAL_STATUS` | `dict[RefusalCode, int]` | one entry per `RefusalCode` member, below |
| `REFUSAL_DETAIL` | `dict[RefusalCode, str]` | one entry per `RefusalCode` member, below |

| `RefusalCode` | `REFUSAL_STATUS` | `REFUSAL_DETAIL` |
|---|---|---|
| `unauthorized` | 401 | `the request does not carry the deliverer's token` |
| `invalid_request` | 422 | `the project id or the body of the request has the wrong form` |
| `unknown_project` | 404 | `the project has no object connection` |
| `connection_not_confirmed` | 409 | `the owner has not confirmed the object's folders` |
| `folder_unavailable` | 503 | `the object folders cannot be read` |
| `state_unavailable` | 503 | `the delivery records cannot be read or written` |
| `invalid_source_id` | 422 | `the source id has the wrong form` |
| `unsafe_reference` | 422 | `the stored image would leave the binary store` |
| `not_placed` | 409 | `the photo has not been delivered` |
| `publication_conflict` | 409 | `the photo is already marked with another photo id` |

Closed lists are enumerations: `= models.ScanStatus`, `= models.ObservationReason`,
`= models.DateSource`, `= models.PlacementStatus`, `= models.PlacementFailure`,
`= models.MarkStatus` and `= models.RefusalCode`. `RefusalCode` is `unauthorized`, `invalid_request`,
`unknown_project`, `connection_not_confirmed`, `folder_unavailable`, `state_unavailable`,
`invalid_source_id`, `unsafe_reference`, `not_placed` and `publication_conflict`.

`MAX_OUTPUT_BYTES` equals the Portal's `BINARY_MAX_READ_BYTES`. A change of that Portal value is
released together with a change of this constant. The deliverer does not ask the Portal for it.

### Formal invariants

- INV-14: a stored image never exceeds the Portal's read limit.

### Required tests

- INV-14: a prepared image above the stored image limit fails with `too_large` and nothing is stored (`test_an_image_above_the_portal_read_limit_is_not_stored`).

### Consequence

A stored image can always be read back by the Portal.

## Accepted decision A9 — Dependencies

### Normative rules

1. The direct libraries are pinned to exact versions: pillow, fastapi, pydantic and uvicorn. The
   libraries they require are resolved when the deployment image is built and are covered by rule 2.
2. The image library decodes untrusted files. Before each deployment every distribution installed
   in the image is checked against a snapshot of the OSV database, ecosystem PyPI, that the deployment route accepts
   as current. That route owns the age limit, and no code of this service reads it. Any known vulnerability listed for an installed version
   blocks the deployment, whatever its severity, and a check that cannot complete does not pass.
   This is the policy the Client Portal already follows.

### Formal invariants

- INV-15: no distribution with a known vulnerability is deployed.

### Required tests

- INV-15: the deployment route refuses an image holding a distribution with a known vulnerability, and refuses when the check cannot complete.

### Consequence

The prototype's `requirements.txt` already pins these libraries. The OSV check is not built for this service yet.

## Accepted decision A11 — Old photo dates stop a delivery

### Normative rules

1. Before placing anything for a project, the calling flow reads that project's staff photo list in
   the Portal. A `photo_date` ending in `Z` or in an offset `+HH:MM` or `-HH:MM` is an old date.
2. When the list holds an old date, or cannot be read, the flow places and publishes nothing for that
   project and tells the owner which project needs the repair.
3. The agent repairs the dates of one project at a time, after a backup and with the owner's
   permission for that project (R0-13). The repair changes the Portal's data, not the deliverer's.
4. The deliverer does not make this check, because it never calls the Portal (INV-11).

### Formal invariants

- INV-17: a calling flow publishes no delivered photo to a project whose staff photo list holds an old date.

### Required tests

- INV-17: a project holding a date with an offset is detected before delivery, and a project holding only UTC dates passes (E2E, `the flow can see an old date before it delivers`, `a project with UTC dates passes that check`). The calling flow's own stop is shown when that flow exists.

### Consequence

The first delivered photo cannot break the photo list of a project with old dates.

## Accepted decision A10 — Security review

### Normative rules

The total review of `SECURITY_REVIEW_EVIDENCE.md` over States 0 to 2. Each applicable category is
owned by a decision above.

### Formal invariants

- INV-16: every security category has an explicit outcome.

### Required tests

- INV-16: `python tools/design_lint.py examples/portal-deliverer --state 2` reports no security finding. The closed list of categories is `SECURITY_REVIEW_EVIDENCE.md`.

### Consequence

State 3 may start only when no category is unresolved.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A5; affected: bearer token boundary
- secrets: APPLICABLE; references: A5; affected: token file, logs, answers
- authorization: APPLICABLE; references: A5; affected: M01, every project-scoped operation
- injection_interpreted_input: APPLICABLE; references: A5, A6; affected: project id, source id, file names, stored paths
- external_callbacks_webhooks: NOT_APPLICABLE; rationale: no external system sends events to the deliverer, and the publication mark is an authenticated call of the owner's flow
- browser_boundary: NOT_APPLICABLE; rationale: the service has no browser client, cookie, page or cross-origin surface, and a caller that displays a file name treats it as plain text
- files_artifacts: APPLICABLE; references: A1, A2, A5, A6, A8; affected: M01, M02, M03, M04, connections file, source folders, Portal binary store
- concurrency: APPLICABLE; references: A3, A4, A5, A6; affected: M01, M04, M07
- dependencies: APPLICABLE; references: A9; affected: image library, web framework, validation library, web server
