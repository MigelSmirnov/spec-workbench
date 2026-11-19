# State 5 — Portal Deliverer public module operations

## Status

Written on 2026-11-18 from the accepted States 0 to 4. These are the operations another module or the boundary of the
service may call. Inputs and outputs name their meaning, and the exact signatures are decided in State 6. The test
`test_each_module_offers_exactly_its_public_operations` of `prototypes/portal_deliverer/test_deliverer.py` fails when a
module of the prototype offers any other public function.

`boundary:deployment` is what launches the process. The calling agent
reaches the service only through the routes that `public_op:deliverer_api.create_app` builds.

## `public_op:runtime_settings.load_runtime_settings`

### Owner

`module:runtime_settings`.

### Callers

`module:deliverer_api`, through `public_op:deliverer_api.run_service`.

### Inputs

The environment of the process.

### Outputs

The run settings of A8.

### Observable effect

Reads the environment.

### Enforces

A8: a required setting is present and not empty, an optional one that is absent or empty takes its decided default, and the port is decimal digits for a number from 1 to 65535.

### Errors

A missing required setting or an invalid port ends the start.

### State impact

Read-only.

## `public_op:deliverer_api.load_config`

### Owner

`module:deliverer_api`.

### Callers

`module:deliverer_api`, through `public_op:deliverer_api.run_service`.

### Inputs

The run settings of A8.

### Outputs

The context of the operations: time zone, binary store, state folder and connections file.

### Observable effect

Reads the connections file.

### Enforces

A8 and condition 1 of A5 rule 7: the service does not start with an invalid connections file.

### Errors

An unknown time zone or an invalid connections file ends the start.

### State impact

Read-only.

## `public_op:deliverer_api.read_token`

### Owner

`module:deliverer_api`.

### Callers

`module:deliverer_api`, through `public_op:deliverer_api.run_service`.

### Inputs

The path of the token file.

### Outputs

The token with the whitespace around it removed.

### Observable effect

Reads the token file.

### Enforces

A5 rule 2: no group or other permission on the file, UTF-8 content, and after the surrounding whitespace is removed at least 32 characters, all visible ASCII.

### Errors

A file that breaks A5 rule 2 or cannot be read ends the start.

### State impact

Read-only.

## `public_op:deliverer_api.create_app`

### Owner

`module:deliverer_api`.

### Callers

`module:deliverer_api`, through `public_op:deliverer_api.run_service`.

### Inputs

The context of the operations and the token.

### Outputs

The HTTP surface with the health, scan, delivery and mark routes.

### Observable effect

None until the surface is served. The health route answers without a token. Every other route checks the token, the project id and the form of its body when it has one, calls one operation of `module:photo_delivery` and turns its refusal into an answer.

### Enforces

A5 rules 1 and 3 to 5, the project id part of rule 9 and the refusal part of rule 10, the request form of A3 rule 4 and the `photo_id` form of A4 rule 2.

### Errors

Building the surface raises no refusal. A served route answers a wrong token, a malformed request and every M08 refusal.

### State impact

Read-only.

## `public_op:deliverer_api.run_service`

### Owner

`module:deliverer_api`.

### Callers

`boundary:deployment`.

### Inputs

The environment of the process.

### Outputs

The exit status of the process: 0 when it is stopped by a signal after it has served, 1 when the start fails, without listening, and a status other than 0 when the web server fails after it has started listening. A failure is reported on the standard error stream; the text of that report is not part of the contract.

### Observable effect

Calls `public_op:runtime_settings.load_runtime_settings`, `public_op:deliverer_api.load_config`, `public_op:deliverer_api.read_token` and `public_op:deliverer_api.create_app` in that order, then serves the surface on the loopback interface and the `port` of the run settings until it is stopped.

### Enforces

A5 rule 4: the service listens on the loopback interface and reads no forwarded header.

### Errors

Any failure of the start ends the process without listening.

### State impact

Read-only.

## `public_op:object_connections.load_connections`

### Owner

`module:object_connections`.

### Callers

`module:deliverer_api`.

### Inputs

The path of the connections file.

### Outputs

The connection of each project, keyed by its Registry project id.

### Observable effect

Reads the connections file.

### Enforces

Condition 1 of A5 rule 7 and the written form of the subfolders in A5 rule 8.

### Errors

An unreadable file, a file of another form or a subfolder that breaks the form of A5 rule 8 raises an error. `confirmed_connection` turns it into `folder_unavailable`, and at the start it ends the process.

### State impact

Read-only.

## `public_op:object_connections.confirmed_connection`

### Owner

`module:object_connections`.

### Callers

`module:photo_delivery`.

### Inputs

The path of the connections file and the project id.

### Outputs

The confirmed M01 of the project.

### Observable effect

Reads the connections file exactly once per call.

### Enforces

A5 rules 6 and 7 and INV-10.

### Errors

`folder_unavailable`, `unknown_project` or `connection_not_confirmed`, in the order of A5 rule 7.

### State impact

Read-only.

## `public_op:object_connections.available_photo_folder`

### Owner

`module:object_connections`.

### Callers

`module:photo_delivery`.

### Inputs

A confirmed M01.

### Outputs

The resolved path of the photo folder, the path whose containment below the root was checked, for use inside the service only.

### Observable effect

Resolves the root and the photo folder.

### Enforces

The containment rule of A5 rule 8.

### Errors

`folder_unavailable` when the root or the folder is missing, is not a folder, lies in a loop of links, cannot be resolved or inspected, or does not resolve strictly below the root.

### State impact

Read-only.

## `public_op:source_folder.observe_source_files`

### Owner

`module:source_folder`.

### Callers

`module:photo_delivery`.

### Inputs

The path of the photo folder.

### Outputs

One `SourceFile` for each reported file, in the walking order of A1, with its source id when it is ready.

### Observable effect

Reads the source folder.

### Enforces

A1 orders 1 to 6, the ignored names, INV-01 and INV-18.

### Errors

`folder_unavailable` when the photo folder or a subfolder that is not ignored cannot be listed. A file that cannot be read is a rejected `SourceFile`, not an error.

### State impact

Read-only.

## `public_op:source_folder.read_named_source`

### Owner

`module:source_folder`.

### Callers

`module:photo_delivery`.

### Inputs

The path of the photo folder and the requested name.

### Outputs

Nothing when the name fails condition 1 of A3 rule 5. Otherwise a `SourceRead`: one `SourceFile`, and the bytes that were judged when it is ready. A ready `SourceFile` carries in `modified` the modification time A1 takes from the opened file, so its caller reads no metadata of its own.

### Observable effect

Reads one file once.

### Enforces

Condition 1 of A3 rule 5, A1 orders 1 to 6, INV-01, INV-02 and INV-19.

### Errors

None. A file that cannot be read is a rejected `SourceFile`.

### State impact

Read-only.

## `public_op:photo_preparation.prepare_photo`

### Owner

`module:photo_preparation`.

### Callers

`module:photo_delivery`.

### Inputs

The bytes of the source, its modification time and the configured time zone.

### Outputs

M03: a JPEG of pixels only, its photo moment in UTC without an offset, and how that moment was obtained.

### Observable effect

None.

### Enforces

A2 rules 1 to 4, INV-03, INV-04 and INV-14.

### Errors

`Rejected` with `too_many_pixels`, `unreadable_image` or `too_large`.

### State impact

Read-only.

## `public_op:photo_preparation.build_publication`

### Owner

`module:photo_preparation`.

### Callers

`module:photo_delivery`.

### Inputs

The project id, the source id, the stored reference and M03.

### Outputs

M05 with `client_visible` false, no section and no caption.

### Observable effect

None.

### Enforces

A2 rule 5 and INV-05.

### Errors

None.

### State impact

Read-only.

## `public_op:delivery_store.project_lock`

### Owner

`module:delivery_store`.

### Callers

`module:photo_delivery`.

### Inputs

The context of the operations, the project id.

### Outputs

A held lock for the duration of the caller's block.

### Observable effect

Creates the project lock file on first use with the mode of `LOCK_FILE_MODE`, and the missing folders below the state folder with `STATE_FOLDER_MODE`; a missing state folder is refused like a lock file that cannot be opened. It opens the lock file without following a link and holds an operating system lock.

### Enforces

A6 rule 4 and INV-12.

### Errors

`state_unavailable` when the state folder is missing, when a folder leading to the lock file cannot be created or given its mode or is a symbolic link or not a folder, when the lock file cannot be opened or locked, or when its entry is a symbolic link or not a regular file.

### State impact

Writes only the project lock file `locks/<project_id>.lock` and the folders below the state folder that lead to it (A6 rule 2).

## `public_op:delivery_store.store_image`

### Owner

`module:delivery_store`.

### Callers

`module:photo_delivery`.

### Inputs

The context of the operations, the project id, the source id and the image bytes.

### Outputs

The reference `photos/<project_id>/<source_id>.jpg`.

### Observable effect

Writes the stored image atomically with the mode of `STORED_IMAGE_MODE`, creating the missing folders below the binary store with `STORE_FOLDER_MODE`; each folder it creates and the image's own folder are synchronised before it returns, and a failure there is a failed write (A6 rules 2 and 3). A missing binary store is a failed write.

### Enforces

A6 rules 1 to 3.

### Errors

`unsafe_reference` when the reference leaves the binary store. A failed write raises the operating system error, which `module:photo_delivery` turns into the failure of that photo.

### State impact

Writes one stored image.

## `public_op:delivery_store.read_placement`

### Owner

`module:delivery_store`.

### Callers

`module:photo_delivery`.

### Inputs

The context of the operations, the project id and the source id.

### Outputs

M04, or nothing when its record does not exist.

### Observable effect

Reads one record.

### Enforces

A6 rule 5 and INV-20.

### Errors

`state_unavailable` for a damaged record.

### State impact

Read-only.

## `public_op:delivery_store.write_placement`

### Owner

`module:delivery_store`.

### Callers

`module:photo_delivery`.

### Inputs

The context of the operations and M04. The address of the record is taken from the `project_id` and `source_id` inside M04, so the two cannot disagree.

### Outputs

Nothing.

### Observable effect

Writes the record atomically with the mode of `RECORD_MODE`; a failed synchronisation of its folder after the rename does not undo it (A6 rule 3).

### Enforces

A6 rule 3.

### Errors

A failed write raises the operating system error, which `module:photo_delivery` turns into the failure of that photo.

### State impact

Writes one placement record.

## `public_op:delivery_store.read_mark`

### Owner

`module:delivery_store`.

### Callers

`module:photo_delivery`.

### Inputs

The context of the operations, the project id and the source id.

### Outputs

M07, or nothing when its record does not exist.

### Observable effect

Reads one record.

### Enforces

A6 rule 5 and INV-20.

### Errors

`state_unavailable` for a damaged record.

### State impact

Read-only.

## `public_op:delivery_store.write_mark`

### Owner

`module:delivery_store`.

### Callers

`module:photo_delivery`.

### Inputs

The context of the operations and M07. The address of the record is taken from the `project_id` and `source_id` inside M07, so the two cannot disagree.

### Outputs

Nothing.

### Observable effect

Writes the record atomically with the mode of `RECORD_MODE`; a failed synchronisation of its folder after the rename does not undo it (A6 rule 3).

### Enforces

A6 rules 3 and 5.

### Errors

`state_unavailable` when the mark cannot be written.

### State impact

Writes one mark record.

## `public_op:photo_delivery.scan_project_photos`

### Owner

`module:photo_delivery`.

### Callers

`module:deliverer_api`.

### Inputs

The context of the operations and the project id.

### Outputs

One M02 for each reported file, in the walking order of A1, and the count of each status that occurs.

### Observable effect

Reads the connections file, the source folder and the records.

### Enforces

A1 orders 7 to 9, INV-01 and INV-10.

### Errors

The refusals of `confirmed_connection`, `available_photo_folder`, `observe_source_files`, `read_placement` and `read_mark`, as M08.

### State impact

Read-only.

## `public_op:photo_delivery.deliver_project_photo`

### Owner

`module:photo_delivery`.

### Callers

`module:deliverer_api`.

### Inputs

The context of the operations, the project id, the name and the source id.

### Outputs

M06 with status `placed`, `replayed` or `failed`.

### Observable effect

Writes a stored image and a placement record when the photo is placed.

### Enforces

A3, INV-06, INV-07, INV-10, INV-11, INV-12 and INV-19.

### Errors

`invalid_source_id` and the refusals of the connection, the folder, the project lock and the records, as M08. Every condition of A3 rule 5 is a `failed` M06.

### State impact

Creates at most one placement of a project and content, and the project lock file on first use. After a failed record write a stored image may remain without a record (A3 rule 5).

## `public_op:photo_delivery.mark_photo_published`

### Owner

`module:photo_delivery`.

### Callers

`module:deliverer_api`.

### Inputs

The context of the operations, the project id, the source id and the `photo_id`.

### Outputs

M07 together with its `MarkStatus`, `marked` or `replayed`.

### Observable effect

Reads the clock once and writes the mark when there is none.

### Enforces

A4, A7 rule 2, INV-08, INV-10, INV-12 and INV-13.

### Errors

`invalid_source_id`, `not_placed`, `publication_conflict` and the refusals of the connection, the project lock and the records, as M08.

### State impact

Creates at most one mark of a placement, and the project lock file on first use.

## `public_op:system_clock.utc_now`

### Owner

`module:system_clock`.

### Callers

`module:photo_delivery`.

### Inputs

None.

### Outputs

The current time in UTC without an offset, in microseconds.

### Observable effect

Reads the host clock at each call. `module:photo_delivery` calls it once per mark, after the source id is accepted (A7 rule 2).

### Enforces

A7 rules 1 and 3.

### Errors

None.

### State impact

Read-only.
