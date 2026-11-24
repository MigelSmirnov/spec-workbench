# State 5 — Registry public module operations: actions and surfaces

## Status

Draft of 2026-11-01. The operations of `operations`, which runs every action,
of the two surfaces `service_api` and `owner_interface`, and of
`instance_lifecycle`, which starts the instance. Every one follows
`50_public_apis_0_conventions.md`.

## `public_op:operations.perform_service_operation`

### Owner

`module:operations`. Run one service operation: stages (1) and (2), the one
transaction, the record's module, the answer's class (A04 rules 4, 6; A09).

### Callers

`module:service_api`.

### Inputs

The presented token; the operation, one of A09 rule 2's; its inputs, or
that they are not of the wire format; for Kernel, the agent session the
request's envelope names beside the token, never among the operation's
inputs (R0-53).

### Outputs

The operation's answer — `validate`, `context`, the project card, the
project list, rooms, pointers, the latest pointer, the billing read, the
session's access, the agent projection, a written room or pointer, a
registered or ended session, a pending request — or a refusal of the closed
set.

### Observable effect

For an accepted change, the change, committed in one transaction; nothing
for a read or a refusal. A service operation writes no audit entry (M09).

### Enforces

Stage (1): `service_access.identify_service` and
`service_access.service_may_call`. Stage (2), for Kernel: the registration
checked for the token only (A10 rule 1); every other call through
`agent_sessions.check_agent_call`, a withdrawal's pointer resolved first by
`artifact_pointers.project_of_pointer` — an unknown pointer answered
`not_found` (`agent_call_refused`) without the session's check, the same
answer as any refusal of it (A08 rule 7, A10 rule 3). Every Kernel call runs
in a write transaction (A10 rule 6); every other read in
`store.read_in_transaction`, every change in `store.run_in_transaction`,
each given as its open store the one `store.opened_store` gives (each of the
three declared in `module_internal["operations"]["store"]`), with the
instant of
`clock.recorded_now`. The agent projection joins
`projects.read_agent_view` with `artifact_pointers.published_pointers`. An
answer's class is `personal_data` when one of the fields the imported
`PERSONAL_DATA_FIELDS` constant lists holds a value in it, nested views
included, and `business_confidential` otherwise, never `open` (owner,
2026-11-17); an answer above `service_access.highest_class_of_service` is
refused whole (A09 rule 4). No stage is re-ordered and no check added after stage (2).

### Errors

`unauthenticated`, `not_permitted` (`outside_service_rights`,
`answer_above_class`), `not_found` (`agent_call_refused`, and stage (3)'s),
and the record's module's refusals unchanged; `internal_error`.

### State impact

One transaction per call.

## `public_op:operations.perform_owner_operation`

### Owner

`module:operations`. Run one owner request: sign-in and sign-out, the
confirmation step, the upload and the mapping, and every owner action in
its one transaction with its entry and confirmation id (A04, A13, A14, A16).

### Callers

`module:owner_interface`.

### Inputs

The session identity from the cookie; the CSRF value; the request — which
action or page, its target, its stated revision or access version, its
values, a confirmation value; for sign-in the credential; for an upload the
file part's declared length, which `upload_framing.read_upload_head`
derived, or none, and the file part as an unread stream that ends where the
part ends, which `owner_interface` hands on without reading and this
operation passes, unread, to `migration_import.read_import_mapping`, which
alone consumes it within the request.

### Outputs

The answer the page renders — a card, a list, a mapping, a confirmation
step, an accepted change, the newest backup from
`backups.newest_backup_instant` in the backup location
`configuration.give_backup_location` gives — its instant, that there is
none, or that the location could not be listed, each answered and rendered
as itself, never as another (A18 rule 1) — or a refusal of the closed set.

### Observable effect

For an accepted change: the change and, when the action changed state and
M09 lists it, its audit entry with, for a confirmed action, its
confirmation id, all in one transaction; for a
session's runtime change, that change; nothing for a read or a refusal
beyond what A13 says a refused request does to its session.

### Enforces

Stage (1) through `owner_sessions.admit_owner_request` — the import lock
first for a request that reads or changes an uploaded file — and, where one
is asked, `owner_sessions.take_confirmation`; sign-in alone through
`owner_sessions.sign_in_owner`. The transaction through
`store.run_in_transaction`, on the store `store.opened_store` gives, with one
instant and today from `clock`. The
compositions: an erasure with `agent_sessions.drop_project_from_sessions`
and, deleting whole, `artifact_pointers.delete_pointers_of_project`; a grant
through a request with `projects.validate_project_reference`; the import
through `migration_import`, closed by `record_migration_closure`, then
`owner_sessions.drop_uploaded_files`. The entry through
`audit_log.append_audit_entry` only when the action changed state and M09
lists it, and for an erasure of old entries after
`audit_log.erase_audit_entries_before` whatever it removed (A15 rules 4, 6);
the confirmation id from `random_values.mint_identity` only then (A14 rule
5). No owner answer is refused for its class.

### Errors

Every code of the closed set, from the module that decided it. A request
that names no owner action — its method and path are no row of the imported
`OWNER_ACTIONS` constant — is checked at stage (1) as a read and then
refused `invalid_request` (`outside_closed_list`) at stage (4), as the
service API refuses an operation it does not know (owner, 2026-11-24).

### State impact

One transaction per change; runtime state of the session.

## `public_op:service_api.serve_service_request`

### Owner

`module:service_api`. The service API's transport for the four services
(R0-27, R0-28).

### Callers

`boundary:service_client`, `module:instance_lifecycle`.

### Inputs

One HTTP request on the service API's listener: the token, the operation
and, for Kernel, the agent session in the header the imported
`SERVICE_AGENT_SESSION_HEADER` constant names, apart from the operation's
inputs; the inputs in the wire format States 5 and 6
declare. Kernel fills the session from its own run context and never from a
value the agent's flow supplies (R0-53); Registry relies on it as it relies
on Kernel naming the session.

### Outputs

One response in that wire format, v1's (owner, 2026-11-17): the answer, or
the refusal's code, stage and kinds. An answer is written as its fields with
no `answer_kind` or `view_kind` on the wire; `validate` and `context` are
their v1 bodies, field for field (R0-04). Instants are ISO 8601 text in UTC
ending in `Z`, dates ISO 8601 dates, decimals JSON strings in the stored form
(`"45.00"`). The HTTP status is the imported `SERVICE_ANSWER_STATUS` for an
answer and, for a refusal, its code's in the imported
`REFUSAL_HTTP_STATUSES` — v1's: `not_found` 404, `internal_error` 500, every
other code 422.

### Observable effect

None of its own.

### Enforces

Nothing is reachable without a token; every request goes to
`operations.perform_service_operation`; it checks nothing and holds no rule
(State 3). Not served in an owner-only start (A17 rule 1).

### Errors

None of its own: it refuses nothing. An operation name that is not one of
A09 rule 2's reaches `operations`, which refuses it at stage (1) as outside
the service's rights (`not_permitted`, `outside_service_rights`), whatever
token it carries once the token is valid; inputs that are not of the wire
format — a body that cannot be read as it, a field it does not declare, a
value of another shape than its field's — are answered stage (1) first and
then `invalid_request` (`outside_closed_list`) at stage (4). A declared
field left out is not a wire-format failure: it reaches the operation as
absent, and its module answers it (`missing_value`, A02). Every refusal is
`operations`'.

### State impact

None of its own.

## `public_op:owner_interface.serve_owner_request`

### Owner

`module:owner_interface`. The owner interface: server-rendered, script-free
forms over the owner's operations (R0-29, A19).

### Callers

`boundary:owner_browser`, `module:instance_lifecycle`.

### Inputs

One HTTP request from the owner's browser: the session cookie, the form's
fields with their CSRF value, a confirmation value where the step carries
one, the revision or access version the rendered card carried; for an
upload, a multipart body whose first part is the CSRF field and whose second
is the file (owner, 2026-11-17). `upload_framing.read_upload_head` reads
the body's head alone and answers the CSRF value and the file part's
declared length; `owner_interface` hands that length and the file part, as
an unread stream that ends where the part ends, to
`operations.perform_owner_operation`, without reading or buffering it. A
head of another form gives no CSRF value, and the upload is refused at stage
(1) before any byte of the file is read. An upload arrives, for the session
check, once its head has been read (A13 rule 2). The body reaches
`owner_interface` as a stream that ends where HTTP's framing ends it — after
its `Content-Length` bytes, or at a chunked body's last chunk
(`instance_lifecycle`'s listener). A file whose bytes run past that end lacks
its closing delimiter and is refused as `file_unreadable`; A19 rule 4's
counting applies to the bytes of the file part the stream gives.
The action is the row of the imported `OWNER_ACTIONS` constant whose method
and path are the request's, and that row says whether the request is a
change and whether it touches an uploaded file — the confirmation step
touching one only when the action it confirms is the import; the target is
the query parameter the imported `OWNER_TARGET_PARAMETER` constant names;
the CSRF value is the form field the imported `OWNER_CSRF_FIELD` constant
names; the session is the cookie the imported `OWNER_SESSION_COOKIE_NAME`
constant names (owner, 2026-11-24). A request whose body, upload head or
form cannot be read is handed on with no values, no CSRF value and no
credential, nothing partly read kept: it is admitted or refused by the
ordinary checks, a change refused at stage (1) for its missing CSRF value,
a sign-in as a missing credential (owner, 2026-11-24; option (a) of the
question State 4 round-51 and round-55 T3 carried to State 7).

### Outputs

One HTML page: the answer rendered, every stored value escaped as text for
its place, under a content security policy forbidding any script; or the
refusal rendered — the sign-in page for a request without a valid session.
Its HTTP status is the imported `SERVICE_ANSWER_STATUS` constant for an
answer and, for a refusal, its code's row of the imported
`REFUSAL_HTTP_STATUSES` constant, as the service API's (owner, 2026-11-24).
A link or a form addresses its action by that action's row of
`OWNER_ACTIONS` and its target by `OWNER_TARGET_PARAMETER`; a read is a
link or a GET form, which carries no CSRF value, and every change a POST
form carrying it, so no secret is ever in a URL (R0-29).

### Observable effect

On sign-in, the session cookie set: not readable by scripts, only to
Registry's origin, and always HTTPS-only (A13 rule 1; owner, 2026-11-17). Registry never expires or deletes the cookie: an ended session's
cookie is refused at the session check and replaced by the next sign-in, so
no answer, however late it arrives, can remove a newer session's cookie.
Two sign-ins of one browser whose answers cross make two valid sessions;
the browser keeps the cookie it received last, and the other session,
carried by no cookie, ends by its limits (A13 rule 2).
After an upload's answer, whatever it was — accepted, or refused before any
or after some bytes were read — `owner_interface` discards the unread
remainder of the body without reading it into anything and closes the
connection its listener accepted; a connection that carried an upload is
never reused. A proxy or TLS terminator in front of Registry is the host's
(Explicit exclusions).

### Enforces

A create form carries a request id from `random_values.mint_identity` made
when it is rendered (A01 rule 1); every form of a page rendered for a valid
session carries the CSRF value `owner_sessions.give_session_csrf` gives for
it, and the sign-in form none (A13 rules 4, 5, 7); every form carries the revision or access
version of what it rendered, or none (A04, A12 rule 3); no personal value
or secret in a URL (R0-29); the newest backup's instant on its page (A18
rule 1). Every check is `operations`'.

### Errors

Renders every refusal of the closed set. Refuses nothing itself: a request
it cannot read is answered by `operations` as any other, never by a closed
connection instead of an answer (owner, 2026-11-24).

### State impact

None of its own.

## `public_op:instance_lifecycle.start_instance`

### Owner

`module:instance_lifecycle`. Start Registry in A17's order and keep it
running (A17 rule 2, A13 rule 2, A18 rule 1).

### Callers

`boundary:host_process`.

### Inputs

None; the host starts the process.

### Outputs

A running instance, or a stopped start with one diagnostic naming the first
failed item and never its value.

### Observable effect

In order: `configuration.load_configuration`;
`backups.probe_backup_location`; `store.open_store`; the owner interface's
listener and then, unless the start is owner-only, the service API's, each
at its address in the loaded configuration (A17 rule 1); then the surfaces answer; then two
passes: `owner_sessions.end_expired_sessions` every imported
`SESSION_PASS_SECONDS` and, except in an owner-only start,
`backups.run_daily_backup_if_due` every imported `BACKUP_LOOK_SECONDS`, each
from the start as Conventions, "Passes", says.

### Enforces

Nothing is served until every check passed; a listener that cannot be
opened closes the one already opened and has `store.discard_new_store`
remove a store this start made new (A17 rule 2); a restart ends every owner
session (A13 rule 2). It decides no check.

### Errors

The diagnostic of the first failed step; the start stops.

### State impact

Opens the store and the listeners; starts the passes.
