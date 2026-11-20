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

`module:runtime_settings` reads the environment. `module:deliverer_service` reads the token file, and
`module:object_connections` judges the connections file, and `module:deliverer_router` binds the routes. Nothing
crosses to a caller until the start has succeeded.

### Steps

1. The deployment launches `capability:deliverer_service.run_service`, which owns the remaining steps.
2. `capability:runtime_settings.load_runtime_settings` reads the run settings from the environment.
3. `capability:deliverer_service.load_config` turns them into the context of the operations and calls
   `capability:object_connections.load_connections` once, to judge the connections file whole.
4. `capability:deliverer_service.read_token` reads the token and checks its file permissions and length.
5. `capability:deliverer_router.create_app` builds the HTTP surface with that context and the token.
6. `capability:deliverer_service.run_service` serves that surface in the web server, on the loopback interface and the `port` of the run
   settings.

### Outcomes

The start has succeeded when the web server is listening. Otherwise the process ends without listening. A later failure
of the web server ends the process, and the deployment decides what happens next.

### Errors

A connections file that condition 1 of A5 rule 7 rejects, a run setting that A8 refuses, or a token file that A5
rule 2 rejects ends the start. `module:deliverer_service` writes no token to its output. The start writes no state, so
there is nothing to clean up.

## `flow:answer_health`

### Trigger

The deployment asks whether the service is listening.

### Boundary

`module:deliverer_router` calls `module:deliverer_api` for the answer. No token, setting, file or project crosses.

### Steps

1. The health route that `capability:deliverer_router.create_app` built calls `capability:deliverer_api.answer_health`.
2. `capability:deliverer_api.answer_health` returns the health answer with the OK member of = models.HealthStatus.

### Outcomes

The caller learns that the service is listening, and nothing else.

### Errors

None. A service that is not listening gives no answer, and the deployment decides what happens next.

## `flow:scan_project_photos`

### Trigger

The calling agent asks what a project's folder holds.

### Boundary

`module:deliverer_router` accepts the token and the project id through `module:deliverer_api` and calls
`module:photo_delivery`, which decides
every later step. `module:object_connections` decides whether the folder may be used, `module:source_folder`
reports `SourceFile` values and `module:delivery_store` supplies the records. M02 crosses back to the caller.

### Steps

1. The scan route that `capability:deliverer_router.create_app` built checks the token and then the project id with `module:deliverer_api`.
2. `capability:photo_delivery.scan_project_photos` asks `capability:object_connections.confirmed_connection` for
   the project's connection, reading the connections file once.
3. `capability:object_connections.available_photo_folder` checks the photo folder.
4. `capability:source_folder.observe_source_files` walks the folder and judges each file by A1 orders 1 to 6.
5. For each `ready` file, `capability:delivery_store.read_placement` and `capability:delivery_store.read_mark`
   complete its status by A1 orders 7 to 9.

### Outcomes

The caller receives one M02 for each reported file and the count of each status. Nothing is written.

### Errors

The route refuses a wrong token or project id through `module:deliverer_api`. `module:object_connections` refuses with
`unknown_project`, `connection_not_confirmed` or `folder_unavailable`. `module:source_folder` refuses with
`folder_unavailable` when a subfolder cannot be listed. `module:delivery_store` refuses with `state_unavailable`
when a record cannot be used. The router answers every refusal with the M08 `module:deliverer_api` builds. A file that cannot be read is an M02 with status `rejected`, not a refusal.

## `flow:deliver_one_photo`

### Trigger

The calling agent asks to deliver one photo by its name and source id.

### Boundary

`module:deliverer_router` accepts the token through `module:deliverer_api` before it reads the body, the request
form by = models.DeliverRequest, and the project id through `module:deliverer_api`. `module:photo_delivery` owns the
order of every later step and holds the project lock. `module:source_folder` hands over one `SourceRead`, a `SourceFile` with the
bytes it judged, `module:photo_preparation` returns M03 and M05, and `module:delivery_store` keeps the result. M06
crosses back to the caller.

### Steps

1. The delivery route that `capability:deliverer_router.create_app` built checks the token with `module:deliverer_api`,
   then reads the request form, then checks the project id with `module:deliverer_api`.
2. `capability:photo_delivery.deliver_project_photo` asks `capability:object_connections.confirmed_connection`
   and `capability:object_connections.available_photo_folder`, then checks the form of the source id.
3. It takes `capability:delivery_store.project_lock`.
4. `capability:delivery_store.read_placement` and `capability:delivery_store.read_mark` read both records, so a
   damaged record stops the delivery. With an existing placement the flow answers `replayed`, with the `photo_id` of
   its mark if there is one.
5. `capability:source_folder.read_named_source` applies condition 1 of A3 rule 5 and reads the file once.
6. `module:photo_delivery` compares the hash of those bytes with the requested source id.
7. `capability:photo_preparation.prepare_photo` makes the clean image and the photo moment.
8. `capability:delivery_store.store_image` writes the image and returns its reference.
9. `capability:photo_preparation.build_publication` builds the hidden publication body.
10. `capability:delivery_store.write_placement` writes the record, and the lock is released.

### Outcomes

The caller receives M06 with status `placed`, `replayed` or `failed`. A placed or replayed photo carries its
reference and publication body, and a replayed photo carries its `photo_id` when it is marked.

### Errors

The route refuses a wrong token, request form or project id. After it, `module:object_connections`
refuses the connection or folder, `module:photo_delivery` refuses a malformed source id, and `module:delivery_store`
refuses with `state_unavailable` when the lock or a record cannot be used. `module:photo_delivery` turns every condition of A3 rule 5 into a `failed` M06. The lock is released on every path.
A failed atomic write removes its temporary file, unless that removal fails too; the temporary file then stays, as A6 rule 3 decides. An image left by a failed record write is completed by a
repeated delivery of the same file.

## `flow:record_publication`

### Trigger

The calling agent reports which Portal photo a delivered source became.

### Boundary

`module:deliverer_router` accepts the token through `module:deliverer_api` before it reads the body, the request
form and the `photo_id` by = models.PublishedRequest, and the project id through `module:deliverer_api`, and calls
`module:photo_delivery`. `module:system_clock` supplies the time. `module:object_connections` decides
the connection and `module:delivery_store` keeps the mark. M07 crosses back to the caller.

### Steps

1. The mark route that `capability:deliverer_router.create_app` built checks the token with `module:deliverer_api`,
   then reads the request form and the `photo_id`, then checks the project id with `module:deliverer_api`.
2. `capability:photo_delivery.mark_photo_published` checks the form of the source id.
3. It reads the clock once through `capability:system_clock.utc_now`.
4. `capability:object_connections.confirmed_connection` checks the connection.
5. It takes `capability:delivery_store.project_lock`.
6. `capability:delivery_store.read_placement` requires a placement of this project.
7. `capability:delivery_store.read_mark` finds an existing mark. The same `photo_id` answers `replayed`.
8. Without a mark, `capability:delivery_store.write_mark` writes it, and the lock is released.

### Outcomes

The caller receives M07 with `marked` or `replayed`. Later scans report the file as `published`, and later
deliveries of that content carry its `photo_id`.

### Errors

The route refuses a wrong token, request form, project id or `photo_id`. `module:photo_delivery` refuses
with `invalid_source_id`, `not_placed` or `publication_conflict`. `module:object_connections` refuses as in the scan,
and `module:delivery_store` refuses with `state_unavailable` when the lock, a record or the write of the mark fails. A
refused mark writes nothing, and the lock is released on every
path.

## `flow:owner_delivery`

### Trigger

The owner starts a delivery for one project in the workplace (R0-07).

### Boundary

The calling agent is outside this service and organises the work (R0-15). It reads and publishes in the Portal with
its own session. It reaches the deliverer only through the routes of `module:deliverer_router`, which check the
token with `module:deliverer_api` and delegate to `module:photo_delivery`. The deliverer never calls the Portal. Showing a photo to the client is a later
action of the owner in the Portal and is not part of this flow.

### Steps

1. The agent reads the project's photos with the Portal's `photo.list`. An old date, or a list it cannot read, ends the
   run before anything is delivered, and the agent tells the owner which project needs the repair (A11).
2. It asks the scan route, which runs `capability:photo_delivery.scan_project_photos`. A refused scan ends the run and
   the agent tells the owner the refusal.
3. It shows the owner the files with status `ready` or `placed`, and the owner chooses. A `placed` file was delivered
   earlier and is not yet recorded as published.
4. For each chosen file it asks the delivery route, which runs `capability:photo_delivery.deliver_project_photo`.
5. A refused or `failed` delivery becomes the failure of that photo, with its reason, and the agent goes on with the
   next one.
6. A delivery that carries a `photo_id` is already published, and the agent does not publish it again.
7. Otherwise the agent sends the publication body to the Portal's `photo.publish`. A refusal or a lost answer becomes
   the failure of that photo, and the agent goes on with the next one.
8. It reports the Portal's `photo_id` to the mark route, which runs `capability:photo_delivery.mark_photo_published`. A
   refused mark becomes the failure of that photo, named as published but not recorded.
9. It tells the owner the result of each chosen photo.

### Outcomes

Each chosen photo ends as delivered or as failed with its reason (R0-07). A photo that was already published counts as
delivered. A delivered photo stays hidden from the client until the owner shows it.

### Errors

The agent makes one attempt per photo in a run and does not retry by itself. The owner starts another run, and repeating
is safe: a run stopped between publishing and marking repeats while the photo is hidden, because the Portal returns the
same `photo_id`. If the owner has shown the photo first, `photo.publish` answers 409 and the photo fails with the reason
that the owner already showed it, because its `photo_id` cannot be recovered from the Portal (A4 rule 5). The service
keeps no state of a run, so nothing is left to clean up.
