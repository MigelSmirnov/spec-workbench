# State 5 — Registry public module operations: foundation

## Status

Draft of 2026-11-01. The operations of `clock`, `random_values`,
`release_declarations`, `given_values`, `configuration`, `store`, `audit_log`
and `service_access`. Every one follows `50_public_apis_0_conventions.md`.

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

## `public_op:clock.today_in_utc`

### Owner

`module:clock`. The UTC date of a given instant: an action's today (A15
rule 3, R0-84).

### Callers

`module:operations`.

### Inputs

One instant — the action's, read once with `recorded_now`.

### Outputs

Its calendar date in UTC.

### Observable effect

None.

### Enforces

An action's today is the date of its own instant, never a second reading of
the clock, so the two cannot fall on different dates at midnight.

### Errors

None.

### State impact

Pure; touches no record.

## `public_op:clock.monotonic_reading`

### Owner

`module:clock`. The process's monotonic reading, which a change of the wall
clock does not move and which counts a suspension of the host (A13 rule 2).

### Callers

`module:owner_sessions`.

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

## `public_op:release_declarations.import_size_limit`

### Owner

`module:release_declarations`. The import file's size limit the release
declares (A19 rule 4).

### Callers

`module:migration_import`.

### Inputs

None.

### Outputs

The limit in bytes; its value is State 6's.

### Observable effect

None.

### Enforces

A file over it is refused at upload, before it is read (A19 rule 4).

### Errors

None.

### State impact

Reads the release; touches no record.

## `public_op:release_declarations.backup_name_prefixes`

### Owner

`module:release_declarations`. The kept and the temporary backup prefixes
the release declares (A18 rule 5).

### Callers

`module:backups`.

### Inputs

None.

### Outputs

The two prefixes, neither beginning with the other; their values are State
6's.

### Observable effect

None.

### Enforces

The prefixes are the release's, never the configuration's (A18 rule 5), and
a release keeps the prefixes of the one before it, so a kept backup of an
earlier release is still counted and rotated.

### Errors

None.

### State impact

Reads the release; touches no record.

## `public_op:release_declarations.declared_artifact_types`

### Owner

`module:release_declarations`. The artifact types the running release
declares (A22 rules 1, 2).

### Callers

`module:artifact_pointers`, `module:migration_import`.

### Inputs

None.

### Outputs

The set of declared type names; the first release's is `estimate` alone.

### Observable effect

None.

### Enforces

A type is declared exactly when it is in this set; nothing reads types from
the configuration or the store (A22 rule 2).

### Errors

None.

### State impact

Reads the release; touches no record.

## `public_op:release_declarations.listener_addresses`

### Owner

`module:release_declarations`. The address each surface listens on, which
the configuration does not name (A17 rules 1, 2).

### Callers

`module:instance_lifecycle`.

### Inputs

None.

### Outputs

The owner interface's address and the service API's address.

### Observable effect

None.

### Enforces

The listeners open at these addresses and at no configured one; which
networks reach them is the host's (R0-28, R0-29).

### Errors

None.

### State impact

Reads the release; touches no record.

## `public_op:release_declarations.owner_service_of_type`

### Owner

`module:release_declarations`. The owner service a declared type fixes
(A08 rule 3, A22 rule 6).

### Callers

`module:artifact_pointers`, `module:migration_import`.

### Inputs

A declared type name.

### Outputs

Its owner service.

### Observable effect

None.

### Enforces

A pointer's owner service is this value and never the caller's choice (A08
rule 3); an imported pointer whose owner service differs is malformed (A16
rule 4).

### Errors

`invalid_request` (`unknown_artifact_type`) for a name the release does not
declare.

### State impact

Reads the release; touches no record.

## `public_op:release_declarations.release_versions`

### Owner

`module:release_declarations`. The running release's version and its
contract version (M09, A18 rule 1).

### Callers

`module:audit_log`, `module:backups`.

### Inputs

None.

### Outputs

The release version and the contract version.

### Observable effect

None.

### Enforces

Every audit entry names both (M09); every backup's record names the release
(A18 rule 1).

### Errors

None.

### State impact

Reads the release; touches no record.

## `public_op:release_declarations.rights_of_service`

### Owner

`module:release_declarations`. A09 rule 2's table: the services, their
operations and their highest classes.

### Callers

`module:configuration`, `module:service_access`.

### Inputs

None.

### Outputs

For each of the four services — PresuPro, Client Portal, Cabinet, Cabinet
Kernel — its operations and its highest class, and whether it carries agent
authority (Kernel alone, R0-74).

### Observable effect

None.

### Enforces

The configuration requires one token for each service listed here (A17
rule 1); rights are read from here alone, never from the configuration (A09
rule 1).

### Errors

None.

### State impact

Reads the release; touches no record.

## `public_op:release_declarations.store_version_of_release`

### Owner

`module:release_declarations`. The store version the running release
carries, with the suffix of the store's temporary name (A17 rule 5).

### Callers

`module:store`.

### Inputs

None.

### Outputs

One store version, and the temporary-name suffix.

### Observable effect

None.

### Enforces

A store opened at the start and a backup's checked copy carry this version;
a new store is made under the store's name with this suffix, and only a file
of that name is removed as a leftover (A17 rule 5, A18 rule 4). Its value is
State 6's.

### Errors

None.

### State impact

Reads the release; touches no record.

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
only is absent, anything else kept exactly as written (A02 rules 2, 3).

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

## `public_op:given_values.read_required_text`

### Owner

`module:given_values`. Read a required value: blank or white space only is
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

None; `missing_value` is the answer, which the caller refuses at stage (4).

### State impact

Pure; touches no record.

## `public_op:configuration.load_configuration`

### Owner

`module:configuration`. Read the `REGISTRY_` variables and check them in A17
rule 2's order up to the store and backup location apart.

### Callers

`module:instance_lifecycle`.

### Inputs

None; it reads the process environment.

### Outputs

The loaded configuration — the store's location, the backup location, the
backup key, the owner credential, and either the four service tokens or
none, which marks an owner-only start — or one diagnostic naming the first
failed item and never its value.

### Observable effect

None.

### Enforces

A17 rules 1–5: no variable outside `REGISTRY_` read; no unknown item, by
name in code point order; the tokens all four of
`release_declarations.rights_of_service` or none; every other item present;
each well formed; each secret at least 32 bytes; no two secrets equal; the
store and the backup location apart, every link resolved; no default
applied. Each secret is handed later only to the module that uses it.

### Errors

The diagnostic is the answer for a failed check; the start stops on it.

### State impact

Reads the environment and resolves paths; touches no file and no record.

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
new is empty and of `release_declarations.store_version_of_release`;
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

Opens or creates the store file; writes no record.

## `public_op:store.discard_new_store`

### Owner

`module:store`. Remove a store this start made new, when the start then
fails at a listener (A17 rule 2).

### Callers

`module:instance_lifecycle`.

### Inputs

The store `open_store` answered as made new.

### Outputs

Whether it was removed.

### Observable effect

The new, empty store is removed, or left as an empty store of the release's
version when the removal fails.

### Enforces

Only a store this start made new is ever removed; an existing store is never
removed or changed by a failed start (A17 rule 2, test 5).

### Errors

None; a failed removal is reported in the start's diagnostic.

### State impact

Deletes one file it made; touches no other.

## `public_op:store.run_in_transaction`

### Owner

`module:store`. Run one action's changes in one write transaction under the
store's one write lock (A04 rule 4, A01 rule 7).

### Callers

`module:operations`.

### Inputs

The step to run inside the transaction, which receives the transaction.

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

The read to run, which receives the transaction.

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

One entry, outcome `accepted`, naming the release and contract versions of
`release_declarations.release_versions`, written with the change or not at
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
the rights are `release_declarations.rights_of_service`'s alone.

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
