# State 5 — Registry public module operations: foundation

## Status

Draft of 2026-11-01, reopened on 2026-11-11: `release_declarations` is
gone — its values are constants of `data_provider`, which a reader imports
and which have no operation (SPEC_STANDARD §6.10, §15.3.1) — and
`runtime_settings` reads the environment. Reopened on 2026-11-16 (State 6
found no operation by which `configuration` hands a secret to the module
that uses it, State 3 "Secrets never leave"; owner, 2026-11-16: the
recipient asks): `configuration.give_service_tokens` and
`configuration.give_owner_credential`, then `configuration.give_backup_key`
(State 5 round-31 T1: the backup key had stayed in the loaded configuration);
and `clock.today_in_utc` removed —
the clock is emitted from `system_clock_backend` v6, which owns exactly the
two readings, and `operations` takes an action's today as the UTC date of
its instant (owner, 2026-11-16). Reopened on 2026-11-26: `model_fields`
reads a model's declared fields for every generic walk (State 3, "Reading a
model's fields"). Reopened again on 2026-11-26: every text form Registry
reads — an instant, a date, a version's digits, a listener's address, and
the decimal and whole numbers `check_value_forms` checks — has one reading,
in `given_values` (State 3). The operations of `clock`,
`random_values`, `model_fields`, `given_values`, `runtime_settings`, `configuration`,
`store`, `audit_log` and `service_access`. Every one follows `50_public_apis_0_conventions.md`.

## `public_op:clock.recorded_now`

### Owner

`module:clock`. The current UTC wall-clock instant, the one every recorded
time is (L16, A13 rule 2).

### Callers

`module:operations`, `module:backups`, `module:store`.

### Inputs

None.

### Outputs

One instant in UTC with its time zone.

### Observable effect

None.

### Enforces

Every instant Registry records is this reading: `operations` takes it once
per action when its transaction begins, `backups` for its minute look,
`store` at the read that fixes a backup copy's snapshot (State 3, "Time";
A18 rule 1). Tests replace the clock as a whole.

### Errors

None.

### State impact

Reads the host's wall clock; touches no record.

## `public_op:clock.monotonic_reading`

### Owner

`module:clock`. The process's monotonic reading, which a change of the wall
clock does not move and which counts a suspension of the host (A13 rule 2).

### Callers

`module:owner_sessions`, `module:instance_lifecycle`.

### Inputs

None.

### Outputs

One reading in nanoseconds, comparable only with other readings of the same
process.

### Observable effect

None.

### Enforces

Every limit of A13 — 8 hours, 30, 15 and 10 minutes, 60 seconds — is
measured between two of these readings and never by the wall clock.

### Errors

None.

### State impact

Reads the host's monotonic clock; touches no record.

## `public_op:random_values.mint_identity`

### Owner

`module:random_values`. Mint one opaque identity as a random UUID ("Identity
formats").

### Callers

`module:operations`, `module:customers`, `module:projects`, `module:artifact_pointers`, `module:owner_interface`.

### Inputs

None.

### Outputs

One random UUID, from the operating system's random source.

### Observable effect

None.

### Enforces

Every `project_id`, `room_id`, pointer id, `customer_ref` and confirmation
id Registry mints, and every request id the owner interface puts into a
create form (A01 rule 1), is such a value; whether it collides is the
writing module's to check (Conventions).

### Errors

None.

### State impact

Reads the operating system's random source; touches no record.

## `public_op:random_values.make_secret_value`

### Owner

`module:random_values`. Make one secret value of at least 32 bytes from the
operating system's random source (A13 rule 7).

### Callers

`module:owner_sessions`.

### Inputs

None.

### Outputs

One value of 32 random bytes, in the text form the cookie and the forms
carry.

### Observable effect

None.

### Enforces

The owner session's identity, its CSRF value and every confirmation value
are made here and nowhere else (A13 rule 7).

### Errors

None.

### State impact

Reads the operating system's random source; touches no record.

## `public_op:random_values.equal_in_constant_time`

### Owner

`module:random_values`. Compare a presented secret with a held one in time
that does not depend on where they differ (A13 rule 7, A17 rule 6).

### Callers

`module:owner_sessions`, `module:service_access`.

### Inputs

The presented value and the held value, as bytes.

### Outputs

Whether they are equal.

### Observable effect

None.

### Enforces

Every comparison of a token, the owner credential, a session identity, a
CSRF value or a confirmation value goes through it.

### Errors

None; values of different lengths answer unequal.

### State impact

Pure; touches no record.

## `public_op:model_fields.model_items`

### Owner

`module:model_fields`. Read a model value's declared fields, each name with
its value in the order the model declares them, or answer that the value is
no model (owner, 2026-11-26; State 3, "Reading a model's fields").

### Callers

`module:operations`, `module:owner_sessions`, `module:service_api`, `module:owner_interface`.

### Inputs

Any value.

### Outputs

For a model, its declared fields as name and value pairs in their declared
order, a nested model given as a value and not opened; for any other value,
that it is no model. A model's declared fields are the fields its model in
the specification lists, each by the name written there and in that order:
a model of `models` derives from no other model (SPEC_STANDARD §12) and
declares no alias, computed field, private attribute or extra field, so
there is no inherited field, second name or further member to place. Its
values are those the model holds for those fields.

### Observable effect

None.

### Enforces

Every generic walk of a model takes its fields here and nowhere else:
`operations` classing an answer at any depth (A09 rule 4), `owner_sessions`
binding a confirmation to its inputs in their declared order (A13 rule 6),
`service_api` writing an answer, `owner_interface` rendering a page (A19
rule 1) and building a request's values. Which field is `personal_data`,
and how a value is written, digested or rendered, stay its callers'.

### Errors

None; a value that is no model is answered as such.

### State impact

Pure; touches no record.

## `public_op:given_values.check_request_id_form`

### Owner

`module:given_values`. Check a request id's form: printable text of at most
128 characters, not blank (A01 rule 1).

### Callers

`module:customers`, `module:projects`, `module:artifact_pointers`.

### Inputs

The given request id, or none.

### Outputs

Either the request id as given, or the failure: `missing_value` for none or
a blank one, `malformed_request_id` otherwise.

### Observable effect

None.

### Enforces

The form only; whether it is random is the caller's duty (A01 rule 1).

### Errors

None; the failure is the answer, which the create's module refuses at stage
(4).

### State impact

Pure; touches no record.

## `public_op:given_values.facts_equal_for_repeat`

### Owner

`module:given_values`. Compare the facts a create gives with a record's
current facts of the same kind, as A02 reads them (A01 rule 6).

### Callers

`module:customers`, `module:projects`, `module:artifact_pointers`.

### Inputs

The given facts and the record's current facts, each as the create's model
names them; for a room and a publish, the project among them, for a publish
the publisher too.

### Outputs

Whether they are equal.

### Observable effect

None.

### Enforces

A required value compares as written; an optional value given blank equals
one not given; a fact of several parts — an object's characteristics —
compares by its parts in any order (A01 rule 6, A02).

### Errors

None.

### State impact

Pure; touches no record.

## `public_op:given_values.read_optional_text`

### Owner

`module:given_values`. Read an optional value as given: blank or white space
only — the code points of the imported `WHITE_SPACE_CODE_POINTS` constant —
is absent, anything else kept exactly as written (A02 rules 1-3).

### Callers

`module:customers`, `module:projects`, `module:artifact_pointers`, `module:migration_import`.

### Inputs

The given text, or none.

### Outputs

The value as written, or absent.

### Observable effect

None.

### Enforces

Registry trims and rewrites nothing (R0-68).

### Errors

None.

### State impact

Pure; touches no record.

## `public_op:given_values.check_value_forms`

### Owner

`module:given_values`. Check the present values a caller gives against the
form State 1 declares (A02 rule 4, R0-90).

### Callers

`module:projects`, `module:customers`, `module:migration_import`.

### Inputs

The values as `read_optional_text` and `read_required_text` answered them,
each with the field it fills: an alias; an object kind; a floor area, a
number of rooms, a floor; a customer language; a Customer's kind.

### Outputs

Nothing when every present value is within its form; otherwise every value
outside it, each with its field and its kind: `outside_form` for an alias
over the imported `ALIAS_MAX_CHARACTERS` constant, counted in Unicode code
points, a floor area not greater than the imported
`OBJECT_FLOOR_AREA_MIN_EXCLUSIVE` constant, a number of rooms that is not a
whole number of at least the imported `OBJECT_ROOMS_MIN` constant, a floor
that is not a whole number;
`outside_closed_list` for a kind or language outside its enumeration.

### Observable effect

None.

### Enforces

A02 rule 4: an absent value is never checked here (rule 3); the caller
refuses the failures at stage (4), except `migration_import`, which shows
them in the mapping (A16 rule 1).

### Errors

None of its own: its failures are its answer.

### State impact

Pure; touches no record.

## `public_op:given_values.read_required_text`

### Owner

`module:given_values`. Read a required value: blank or white space only —
the code points of the imported `WHITE_SPACE_CODE_POINTS` constant — is
missing, anything else kept exactly as written (A02 rules 1, 2).

### Callers

`module:customers`, `module:projects`, `module:artifact_pointers`, `module:agent_sessions`, `module:migration_import`.

### Inputs

The given text, or none.

### Outputs

The value as written, or `missing_value`.

### Observable effect

None.

### Enforces

A02 rule 1 for every required value: a project's display name and address,
a Customer's name and kind, a room's name, a request text, an imported
project's name and a Customer's name and kind the owner gives the import.

### Errors

None; `missing_value` is the answer, which the caller refuses at stage (4)
— except a value the owner gives the import's mapping, a display name or a
Customer's name or kind, which `migration_import.read_import_mapping` shows
as a missing value of a non-clean mapping, the import's own refusal coming
only at confirmation (A16 rule 1). A required value missing inside a record
the file brings in is a malformed record (A16 rule 4), not a missing value.

### State impact

Pure; touches no record.

## `public_op:given_values.read_instant_text`

### Owner

`module:given_values`. Read an instant written in the internet date and time format, narrowed as
Registry reads it, or answer that the text is not of that form (owner,
2026-11-26; State 3, `given_values`).

### Callers

`module:migration_import`, `module:backups`.

### Inputs

A text.

### Outputs

The instant the text names, timezone-aware and in UTC to the
microsecond, or that the text is not of the form: only the format's date
and time with an offset, the capital letters `T` and `Z` alone, a fraction
of a second of at most microseconds, every digit an ASCII digit, a real
calendar date and a real time of that day.

### Observable effect

None.

### Enforces

Every instant Registry reads from text is read here alone: the
instants of a record the import file brings in (A16 rule 4) and the
instant a backup's record line holds (A18 rule 1). What a caller does
with an instant, or with a text not of the form, stays its caller's.

### Errors

None; a text not of its form is answered as such, never raised.

### State impact

Pure; touches no record.

## `public_op:given_values.read_date_text`

### Owner

`module:given_values`. Read a calendar date written in the extended calendar date form of the
ISO date and time standard, or answer that the text is not of that form
(owner, 2026-11-26; State 3, `given_values`).

### Callers

`module:operations`.

### Inputs

A text.

### Outputs

The date the text names, or that the text is not of the form: the year,
the month and the day in that form alone, every digit an ASCII digit, naming
a real calendar date.

### Observable effect

None.

### Enforces

Every date the owner gives — a Customer's end date, the date before which
old audit entries are erased — is read here alone; whether it is later
than today stays its caller's.

### Errors

None; a text not of its form is answered as such, never raised.

### State impact

Pure; touches no record.

## `public_op:given_values.read_digits_text`

### Owner

`module:given_values`. Read a text of ASCII decimal digits alone as the whole number they name,
or answer that the text is not of that form (owner, 2026-11-26).

### Callers

`module:migration_import`.

### Inputs

A text.

### Outputs

The whole number the digits name in decimal, leading zeros allowed, or
that the text is not of the form: an empty text, a sign and white space are
not of it.

### Observable effect

None.

### Enforces

The version of a pointer the import file brings in is read here alone:
one not of the form marks its record malformed (A16 rule 4).

### Errors

None; a text not of its form is answered as such, never raised.

### State impact

Pure; touches no record.

## `public_op:given_values.read_listen_address`

### Owner

`module:given_values`. Read a listener's address in A17 rule 1's text form, or answer that the
text is not of that form (A17 rule 1; owner, 2026-11-26).

### Callers

`module:configuration`.

### Inputs

A text.

### Outputs

The address's host, without brackets, and its port as a whole number, or
that the text is not of the form: a host and a port as the authority of the
URI generic syntax writes them, the host an IPv4 address in dotted decimal
with no leading zero in a part but a lone zero or a bracketed IPv6 address in
any text form of RFC 4291 section 2.2 with no zone identifier and not
IPv4-mapped, the port without a leading zero from the imported
`LISTEN_PORT_MIN` to `LISTEN_PORT_MAX` constant, no white space and no sign.

### Observable effect

None.

### Enforces

A17 rule 1's address form, read here alone; `configuration` judges an
address item well formed exactly when this reading answers an address.

### Errors

None; a text not of its form is answered as such, never raised.

### State impact

Pure; touches no record.

## `public_op:upload_framing.read_upload_head`

### Owner

`module:upload_framing`. Read an upload's multipart head alone, so that its
CSRF value travels in the form and the file reaches `migration_import`
unread (A13 rules 5, 7; owner, 2026-11-17).

### Callers

`module:owner_interface`.

### Inputs

The request's unread body stream, its content type and its declared length,
or that it declared none.

### Outputs

The CSRF value the first part carries, the delimiter that ends the file
part, and the file part's declared length — the request's declared length
less the head it read and the closing delimiter with its final `--` and line
end, or none when the request declared none; or that the head is not of that form — no multipart content type or
boundary, a first part that is not the CSRF field, no second part that is
the file — or is longer than the imported `UPLOAD_FORM_HEAD_MAX_BYTES`
constant, or declares less than that head and the closing delimiter, or the
request's stream fails or ends while the head is read — with none of these
values. The file part's stream is a `MultipartFileBody`, the class
`upload_framing` owns that implements `UploadBody` (State 6); it fails
when the request's stream ends before the closing delimiter, which
`migration_import.read_import_mapping` refuses as `file_unreadable`, as any
stream that fails — unless more than the limit had already been read, which
is `file_too_large` (A19 rule 4, restated 2026-11-24).

### Observable effect

Reads the stream up to the start of the file part's content and no further,
at most the bound; a head it refuses leaves the rest of the stream unread.

### Enforces

A13 rule 7: the CSRF value is taken from the form's body, never from a URL,
and is neither checked nor kept here — `owner_sessions` checks it at the
session check. A19 rule 4 stays `migration_import`'s: no byte of the file is
read here, and the file part's stream, a `MultipartFileBody` over the same
stream and that delimiter, gives the file's bytes only as its reader asks.

### Errors

None: a head of another form answers no CSRF value, and the upload is
refused at stage (1) as a change without one (A04 rule 6, A13 rule 5).

### State impact

None: it reads the request's stream only.

## `public_op:runtime_settings.load_runtime_settings`

### Owner

`module:runtime_settings`. Read the `REGISTRY_` items A17 rule 1 lists from
the process environment into the settings, each as set or absent; no other
variable is read (owner, 2026-11-11).

### Callers

`module:configuration`.

### Inputs

None; it reads the process environment.

### Outputs

The settings: the store's location, the backup location, the backup key,
the owner credential, the owner interface's address, each of the four
service tokens and the service API's address, each as set or absent.

### Observable effect

None.

### Enforces

A17 rules 1 and 5: no other variable read, no default applied. Every check
— presence, form and the checks across items — is
`configuration.load_configuration`'s, in A17 rule 2's one order.

### Errors

None: it checks nothing (SPEC_STANDARD §6.11).

### State impact

Reads the environment; touches no file and no record.

## `public_op:configuration.load_configuration`

### Owner

`module:configuration`. Check the settings `runtime_settings` loads in A17
rule 2's order up to the store and backup location apart.

### Callers

`module:instance_lifecycle`.

### Inputs

None; it calls `runtime_settings.load_runtime_settings` itself and checks
the settings it answers.

### Outputs

The loaded configuration — the store's location, the backup location, the
owner interface's address, and either the service API's
address or none, which marks an owner-only start — or one diagnostic naming
the first failed item and never its value. The secrets — the owner
credential, the service tokens, the backup key — are not answered:
`configuration` keeps them, checked, and gives each only to the module that
uses it (State 3), through `give_owner_credential`, `give_service_tokens`
and `give_backup_key`.

### Observable effect

None.

### Enforces

A17 rules 1–5: the tokens all four of the services the imported
`SERVICE_RIGHTS` constant lists with the service API's address, or none;
every other item present; each — an address as
`given_values.read_listen_address` reads it (`host:port`, the host an IP
address, the port from the imported `LISTEN_PORT_MIN` to `LISTEN_PORT_MAX`
constant), the two ports different —
well formed; each secret at least the imported `SECRET_MIN_BYTES` constant; no two secrets equal; the
store and the backup location apart, every link resolved; no default
applied. Each secret is handed later only to the module that uses it,
which asks for it: through `give_owner_credential`, `give_service_tokens`
and `give_backup_key`.

### Errors

The diagnostic is the answer for a failed check; the start stops on it.

### State impact

Resolves paths; keeps the checked secrets in the process's memory; touches no file and no record.

## `public_op:configuration.give_service_tokens`

### Owner

`module:configuration`. Give the checked service tokens to `service_access`,
the one module that compares them (State 3, "Secrets never leave"; A09 rule
1, A17 rule 7).

### Callers

`module:service_access`.

### Inputs

None.

### Outputs

Each service the imported `SERVICE_RIGHTS` constant lists with its token, as
`load_configuration` checked it; none in an owner-only start, which opens no
service API (A17 rule 1).

### Observable effect

None.

### Enforces

The tokens are those of the one `load_configuration` of this start, never
read again from the environment; no other module keeps them.

### Errors

None: after a start whose `load_configuration` passed, it always answers.
It is asked by `service_access.identify_service` at each identification; `runtime_settings` and `configuration`,
which load and check the value, are the only other modules that keep it;
`random_values.equal_in_constant_time` receives it only as an argument of
one comparison and keeps nothing.

### State impact

Reads the process's memory; touches no record.

## `public_op:configuration.give_owner_credential`

### Owner

`module:configuration`. Give the checked owner credential to
`owner_sessions`, the one module that compares it (State 3, "Secrets never
leave"; A13 rule 4).

### Callers

`module:owner_sessions`.

### Inputs

None.

### Outputs

The owner credential, as `load_configuration` checked it.

### Observable effect

None.

### Enforces

The credential is the one of this start's `load_configuration`, never read
again from the environment; no other module keeps it.

### Errors

None: after a start whose `load_configuration` passed, it always answers.
It is asked by `owner_sessions.sign_in_owner` at each comparison of a presented credential, outside a lockout; `runtime_settings` and `configuration`,
which load and check the value, are the only other modules that keep it;
`random_values.equal_in_constant_time` receives it only as an argument of
one comparison and keeps nothing.

### State impact

Reads the process's memory; touches no record.

## `public_op:configuration.give_backup_key`

### Owner

`module:configuration`. Give the checked backup key to `backups`, the one
module that encrypts and checks a backup with it (State 3, "Secrets never
leave"; A18 rule 3).

### Callers

`module:backups`.

### Inputs

None.

### Outputs

The backup key, as `load_configuration` checked it.

### Observable effect

None.

### Enforces

The key is the one of this start's `load_configuration`, never read again
from the environment, so a changed key takes effect at the next start (A17
rule 7); no other module keeps it.

### Errors

None: after a start whose `load_configuration` passed, it always answers.
It is asked by `backups.run_daily_backup_if_due` at each run it starts;
`runtime_settings` and `configuration`, which load and check the value, are
the only other modules that keep it.

### State impact

Reads the process's memory; touches no record.

## `public_op:configuration.give_backup_location`

### Owner

`module:configuration`. Give the checked backup location to `operations`,
which asks `backups` for the newest backup's instant there for the owner's
page (A18 rule 1; owner, 2026-11-17).

### Callers

`module:operations`.

### Inputs

None.

### Outputs

The backup location, as `load_configuration` checked and resolved it.

### Observable effect

None.

### Enforces

The location is the one of this start's `load_configuration`, never read
again from the environment, so a changed location takes effect at the next
start (A17 rule 7). It is not a secret: `instance_lifecycle` also receives
it from `load_configuration`.

### Errors

None: after a start whose `load_configuration` passed, it always answers.

### State impact

Reads the process's memory; touches no file and no record.

## `public_op:store.open_store`

### Owner

`module:store`. Open the store for the running instance, or make a new,
empty one (A17 rule 5).

### Callers

`module:instance_lifecycle`.

### Inputs

The store's configured location.

### Outputs

The open store and whether this start made it new, or a diagnostic naming
the failure.

### Observable effect

A leftover file of the store's temporary name is removed; a new store is
made under that name and renamed to the store's name once complete.

### Enforces

A17 rule 5: only the temporary name is removed, no other file; a store made
new holds no record but M12 AuditSequence at 0 and is of the imported
`STORE_VERSION` constant;
otherwise the store opens for reading and writing, passes `PRAGMA
integrity_check` answering `ok` and `PRAGMA foreign_key_check` finding
nothing, and carries the release's store version. The engine setting that
lets a backup's reader and the writer go on together is set here, as State 6
fixes it (A18 rule 1).

### Errors

A diagnostic, and the start stops, for: a leftover it cannot remove while the
store is absent; a store that does not open, fails the check or carries
another version; a new store it cannot make, whose temporary file it
removes or, when it cannot, leaves for the next start (A17 rule 2).

### State impact

Opens or creates the store file; a store made new holds one record, M12
AuditSequence at 0, made with it, and no other.

## `public_op:store.opened_store`

### Owner

`module:store`. Give the store this start opened to the module that runs an
action's transaction (owner, 2026-11-17).

### Callers

`module:operations`.

### Inputs

None.

### Outputs

The open store `open_store` answered for this start.

### Observable effect

None.

### Enforces

There is one open store per process (L19): `store` keeps the one
`open_store` opened, and `operations` passes it to `run_in_transaction` and
`read_in_transaction` as the open store each takes as its first input. It is kept for the process and never replaced.

### Errors

None: it is asked only by a surface's request, and a surface serves nothing
until `open_store` succeeded (A17 rule 2). Asked before that, it is a wiring
fault that raises, so nothing is read or written.

### State impact

Reads the process's memory; touches no file and no record.

## `public_op:store.discard_new_store`

### Owner

`module:store`. Remove a store this start made new, when the start then
fails at a listener (A17 rule 2).

### Callers

`module:instance_lifecycle`.

### Inputs

The store `open_store` answered as made new.

### Outputs

Whether it was removed: true when the store's file is gone; false
otherwise.

### Observable effect

The store's one connection — `open_store` opens no other — is closed; then,
in this order, the companion files SQLite may keep beside the store under
its name with a suffix, `-wal`, `-shm`, `-journal`, each removed when it is
a regular file, and last the store's file. A path of another type is left
as it is. The first close or removal that fails stops the rest, so the
store's file is removed only after its companions are: what a failure
leaves is the store's file with some of its companions, an empty store of
the release's version, which the next start opens as any store.

### Enforces

Only a store this start made new is ever removed; an existing store is never
removed or changed by a failed start (A17 rule 2, test 5).

### Errors

None; a failed removal is named in the start's one diagnostic beside the
surface that could not be opened.

### State impact

Deletes the store's companion files and then the store file it made, when
it can; touches no other file.

## `public_op:store.run_in_transaction`

### Owner

`module:store`. Run one action's changes in one write transaction under the
store's one write lock (A04 rule 4, A01 rule 7).

### Callers

`module:operations`.

### Inputs

The open store, which `opened_store` gives; the step to run inside the
transaction, which receives the transaction.

### Outputs

The step's answer once committed, or `internal_error`
(`transaction_failed`) when it did not commit.

### Observable effect

Every change the step made is committed together, or none is.

### Enforces

Changes are applied one at a time, each on the result of the one before (A01
rule 7, A07 rule 2, A10 rule 6, A15 rule 5); a value a caller gives fills a
value place of a statement the release fixes, a value choosing among fixed
alternatives checked against its closed list first (A19 rule 3); lists are
read in A06's order. A step that answers a refusal commits nothing.

### Errors

`internal_error` (`transaction_failed`); nothing changed.

### State impact

Writes the store, atomically.

## `public_op:store.read_in_transaction`

### Owner

`module:store`. Run one read in one read transaction (A14 rule 4).

### Callers

`module:operations`.

### Inputs

The open store, which `opened_store` gives; the read to run, which receives
the transaction.

### Outputs

The read's answer, from one consistent view of the store.

### Observable effect

None.

### Enforces

A read sees the store as one transaction does and never part of a change;
lists in A06's order; values fill value places only (A19 rule 3).

### Errors

`internal_error` (`transaction_failed`) when the store cannot be read.

### State impact

Reads the store; writes nothing.

## `public_op:store.copy_store_snapshot`

### Owner

`module:store`. Write one consistent snapshot of the whole store, without the
agent sessions, as a store file of its own at the path `backups` names (A18
rules 1, 2).

### Callers

`module:backups`.

### Inputs

The temporary path `backups` named under its temporary prefix.

### Outputs

The instant read with `clock.recorded_now` at the read that fixed the
snapshot, and the last sequence number the audit counter held in it (A15
rule 5, 0 for a store that never wrote one).

### Observable effect

A file at the given path: a store of the release's version holding every
record but the agent sessions (M06).

### Enforces

One read transaction on the copy's own connection; its first read, of the
audit counter, fixes the snapshot; actions' writes go on and none is refused
or fails for the copy, nor the copy for them (A18 rule 1). The counter is
read as a stored value; `audit_log` alone decides what it means (State 3).

### Errors

`internal_error` (`transaction_failed`) when the copy cannot be read or
written; the path's file is then whatever was written, under the temporary
prefix.

### State impact

Reads the store; writes one file at the given path.

## `public_op:store.check_store_file`

### Owner

`module:store`. Check a store file opened for reading only: version,
integrity and audit counter (A18 rule 4).

### Callers

`module:backups`.

### Inputs

The file's path; the sequence number its backup's record holds.

### Outputs

Whether it passed, and which check failed first.

### Observable effect

None.

### Enforces

The file carries the release's store version, `PRAGMA integrity_check`
answers `ok`, `PRAGMA foreign_key_check` finds nothing, and the last
sequence number its counter keeps equals the recorded one (A17 rule 5, A18
rule 4). It never opens the file for writing.

### Errors

None; a failed check is the answer.

### State impact

Reads one file; writes nothing.

## `public_op:audit_log.append_audit_entry`

### Owner

`module:audit_log`. Append one entry (M09) in the transaction of the change
it records, with the next sequence number (A14 rule 1, A15 rule 5).

### Callers

`module:operations`.

### Inputs

The transaction; the action, from M09's closed vocabulary; its subject by
identity — the project, the customer, the session and the project, the
import's file digest, or none for an erasure of old entries; the acting
principal; the action's instant; the confirmation id when one was minted;
the date, for an erasure of old entries.

### Outputs

The entry with its sequence number.

### Observable effect

One entry, outcome `accepted`, naming the release and contract versions, the
imported `RELEASE_VERSION` and `CONTRACT_VERSION` constants, written with
the change or not at
all.

### Enforces

The number is one more than the last the store's history ever wrote, from a
counter kept apart from the entries, so an erasure never lowers it (A15
rule 5); no entry holds a personal value, a whole request or a secret
(R0-37); no entry is changed afterwards (A15 rule 1).

### Errors

None of its own; a failing write fails the transaction.

### State impact

Writes one entry and the counter.

## `public_op:audit_log.erase_audit_entries_before`

### Owner

`module:audit_log`. Remove every entry before a date the owner gives (A15
rules 3, 4).

### Callers

`module:operations`.

### Inputs

The transaction, the date, today's date.

### Outputs

How many entries it removed — 0 included.

### Observable effect

Every entry whose instant is before 00:00 UTC of the date is gone.

### Enforces

A date later than today is refused (A15 rule 3); the erasure's own entry,
which `operations` appends after this in the same transaction, is never
removed by it (A15 rule 4); the counter is not touched (A15 rule 5).

### Errors

`invalid_request` (`date_after_today`).

### State impact

Removes entries.

## `public_op:audit_log.read_audit_entries`

### Owner

`module:audit_log`. Read the log for the owner (A15 rule 2).

### Callers

`module:operations`.

### Inputs

The transaction.

### Outputs

The audit view: every entry by sequence number, ascending (A06 rule 6).

### Observable effect

None.

### Enforces

The log is the owner's alone (A15 rule 2): no service operation reaches it.

### Errors

None.

### State impact

Reads entries.

## `public_op:service_access.identify_service`

### Owner

`module:service_access`. Tell a service by the token it presents (A09 rules
1, 3).

### Callers

`module:operations`.

### Inputs

The presented token, or none.

### Outputs

The service, or `unauthenticated` (`no_valid_token`).

### Observable effect

None.

### Enforces

The token is compared in constant time with each configured one through
`random_values.equal_in_constant_time`; an unknown token answers as a wrong
one, without a limit (A17 rule 7); no token carries the owner's rights (A09
rule 5). The tokens are the configuration's, handed to this module alone.

### Errors

`unauthenticated` (`no_valid_token`).

### State impact

Pure over the loaded tokens; touches no record.

## `public_op:service_access.service_may_call`

### Owner

`module:service_access`. Whether a service may call an operation, from the
release's table (A09 rules 2, 3).

### Callers

`module:operations`.

### Inputs

The service and the operation.

### Outputs

Whether it may; for Kernel, that the call carries agent authority.

### Observable effect

None.

### Enforces

An operation outside the service's row is refused whatever the request holds
(A09 rule 3); no token but Kernel's may publish or withdraw (A08 rule 2);
the rights are the imported `SERVICE_RIGHTS` and `SERVICE_HIGHEST_CLASSES`
constants' alone.

### Errors

None; `operations` turns a no into `not_permitted`
(`outside_service_rights`).

### State impact

Pure; touches no record.

## `public_op:service_access.highest_class_of_service`

### Owner

`module:service_access`. The highest disclosure class a service may receive
(A09 rules 2, 4).

### Callers

`module:operations`.

### Inputs

The service.

### Outputs

Its highest class — `personal_data`, or `business_confidential` for Cabinet
Kernel (R0-74).

### Observable effect

None.

### Enforces

`operations` refuses an answer whole when its class is above this one (A09
rule 4); the order of classes is `models`'.

### Errors

None.

### State impact

Pure; touches no record.
