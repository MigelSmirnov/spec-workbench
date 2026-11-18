# State 4 — Portal Deliverer key flows

## Status

Written on 2026-11-18 from the accepted States 0 to 3. Evidence:
`python3 -m pytest -q prototypes/portal_deliverer`, `python3 prototypes/portal_deliverer/e2e_local_portal.py`
and `python3 prototypes/portal_deliverer/e2e_local_syncthing.py`. In `flow:owner_delivery` a script of the
E2E run plays the calling agent against a real Client Portal process. No kernel flow exists yet, and no run
has used the owner's devices or the VPS.

Refusal codes and failure members are those of States 1 and 2. The exact answers are decided in State 6.

## `flow:service_start`

### Trigger

The deployment starts the service.

### Boundary

`module:deliverer_api` reads the settings and the token file. `module:object_connections` judges the
connections file. Nothing crosses to a caller until the start has succeeded.

### Steps

1. `capability:deliverer_api.load_config` reads the run settings and calls
   `capability:object_connections.load_connections` once, to judge the connections file whole.
2. `capability:deliverer_api.read_token` reads the token and checks its file permissions and length.
3. `capability:deliverer_api.create_app` builds the HTTP surface with the token and the clock, and the service
   listens on the loopback interface.

### Outcomes

The service answers the health route, or the process ends without listening.

### Errors

A connections file that condition 1 of A5 rule 7 rejects, a missing setting, or a token file that A5 rule 2
rejects ends the start. `module:deliverer_api` writes no token to its output. The start writes no state, so
there is nothing to clean up.

## `flow:scan_project_photos`

### Trigger

The calling agent asks what a project's folder holds.

### Boundary

`module:deliverer_api` accepts the token and the project id and calls `module:photo_delivery`, which decides
every later step. `module:object_connections` decides whether the folder may be used, `module:source_folder`
reports `SourceFile` values and `module:delivery_store` supplies the records. M02 crosses back to the caller.

### Steps

1. `capability:photo_delivery.scan_project_photos` asks `capability:object_connections.confirmed_connection` for
   the project's connection, reading the connections file once.
2. `capability:object_connections.available_photo_folder` checks the photo folder.
3. `capability:source_folder.observe_source_files` walks the folder and judges each file by A1 orders 1 to 6.
4. For each `ready` file, `capability:delivery_store.read_placement` and `capability:delivery_store.read_mark`
   complete its status by A1 orders 7 to 9.

### Outcomes

The caller receives one M02 for each reported file and the count of each status. Nothing is written.

### Errors

`module:object_connections` refuses with `unknown_project`, `connection_not_confirmed` or `folder_unavailable`.
`module:source_folder` refuses with `folder_unavailable` when a subfolder cannot be listed. `module:deliverer_api`
turns a refusal into its answer. A file that cannot be read is an M02 with status `rejected`, not a refusal.

## `flow:deliver_one_photo`

### Trigger

The calling agent asks to deliver one photo by its name and source id.

### Boundary

`module:deliverer_api` accepts the token, the request form and the project id. `module:photo_delivery` owns the
order of every later step and holds the project lock. `module:source_folder` hands over one `SourceFile` with the
bytes it judged, `module:photo_preparation` returns M03 and M05, and `module:delivery_store` keeps the result. M06
crosses back to the caller.

### Steps

1. `capability:photo_delivery.deliver_project_photo` asks `capability:object_connections.confirmed_connection`
   and `capability:object_connections.available_photo_folder`, then checks the form of the source id.
2. It takes `capability:delivery_store.project_lock`.
3. `capability:delivery_store.read_placement` finds an existing placement. If there is one,
   `capability:delivery_store.read_mark` supplies its `photo_id` and the flow answers `replayed`.
4. `capability:source_folder.read_named_source` applies condition 1 of A3 rule 5 and reads the file once.
5. `module:photo_delivery` compares the hash of those bytes with the requested source id.
6. `capability:photo_preparation.prepare_photo` makes the clean image and the photo moment.
7. `capability:delivery_store.store_image` writes the image and returns its reference.
8. `capability:photo_preparation.build_publication` builds the hidden publication body.
9. `capability:delivery_store.write_placement` writes the record, and the lock is released.

### Outcomes

The caller receives M06 with status `placed`, `replayed` or `failed`. A placed or replayed photo carries its
reference and publication body, and a replayed photo carries its `photo_id` when it is marked.

### Errors

`module:object_connections` and `module:photo_delivery` refuse the whole request as A3 rule 4 orders it.
`module:photo_delivery` turns every condition of A3 rule 5 into a `failed` M06. The lock is released on every path.
A failed atomic write removes its temporary file. An image left by a failed record write is completed by a
repeated delivery of the same file.

## `flow:record_publication`

### Trigger

The calling agent reports which Portal photo a delivered source became.

### Boundary

`module:deliverer_api` accepts the token, the request form, the project id and the `photo_id`, and hands the clock
to `module:photo_delivery` as a function. `module:system_clock` is its source. `module:object_connections` decides
the connection and `module:delivery_store` keeps the mark. M07 crosses back to the caller.

### Steps

1. `capability:photo_delivery.mark_photo_published` checks the form of the source id.
2. It reads the clock once through the function it received, which is `capability:system_clock.utc_now`.
3. `capability:object_connections.confirmed_connection` checks the connection.
4. It takes `capability:delivery_store.project_lock`.
5. `capability:delivery_store.read_placement` requires a placement of this project.
6. `capability:delivery_store.read_mark` finds an existing mark. The same `photo_id` answers `replayed`.
7. Without a mark, `capability:delivery_store.write_mark` writes it, and the lock is released.

### Outcomes

The caller receives M07 with `marked` or `replayed`. Later scans report the file as `published`, and later
deliveries of that content carry its `photo_id`.

### Errors

`module:photo_delivery` refuses with `invalid_source_id`, `not_placed` or `publication_conflict`.
`module:object_connections` refuses as in the scan. A refused mark writes nothing, and the lock is released on every
path.

## `flow:owner_delivery`

### Trigger

The owner starts a delivery for one project in the workplace (R0-07).

### Boundary

The calling agent is outside this service and organises the work (R0-15). It reads and publishes in the Portal with
its own session, and calls `module:deliverer_api`, which delegates to `module:photo_delivery`. The deliverer never
calls the Portal.

### Steps

1. The agent reads the project's staff photo list in the Portal. An old date, or a list it cannot read, stops the
   flow before anything is delivered (A11).
2. It calls `capability:photo_delivery.scan_project_photos` and shows the owner what can be delivered. The owner
   chooses.
3. For each chosen file that is not yet published, it calls `capability:photo_delivery.deliver_project_photo`.
4. A failed photo is noted and the agent goes on with the next one.
5. A delivery that carries a `photo_id` is already published, and the agent does not publish it again.
6. Otherwise the agent sends the publication body to the Portal's `photo.publish`.
7. It reports the Portal's `photo_id` through `capability:photo_delivery.mark_photo_published`.
8. It tells the owner the result of each photo.

### Outcomes

Each chosen photo ends as delivered and hidden from the client, already published, failed with its reason, or handed
to the owner. The owner shows a delivered photo with the Portal's own operation.

### Errors

The agent decides what to repeat. A run stopped between publishing and marking repeats safely while the photo is
hidden, because the Portal returns the same `photo_id`. If the owner has shown the photo first, the Portal answers
409 and the agent hands that photo to the owner (A4 rule 5). The service keeps no state of a run, so nothing is left
to clean up.
