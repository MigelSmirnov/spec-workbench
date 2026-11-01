# State 5 — Registry public module operations: import and backups

## Status

Draft of 2026-11-01. The operations of `migration_import`, the one-time
import of picked v1 projects, and of `backups`, the daily encrypted backups.
Every one follows `50_public_apis_0_conventions.md`.

## `public_op:migration_import.read_import_mapping`

### Owner

`module:migration_import`. Read an uploaded export file as data and answer
its projects, or, for the owner's picks, the mapping (A16 rules 1, 3–5).

### Callers

`module:operations`.

### Inputs

The read transaction; the mode, `upload` or `mapping`; the file's bytes;
for `mapping`, the picks — possibly none — each with the display name and
alias it arrives under, and for each Customer the import will make its
name, its kind and whether the v1 value is its tax id.

### Outputs

Always the file's digest, the SHA-256 of its bytes, which Registry computes
and never takes from a caller. At `upload`, each project the file holds with
its id and status. At `mapping`, the mapping: the picked projects by `project_id`, each one's rooms and
pointers in their lists' orders, the name and alias each arrives under, the
Customers it will make by their v1 value with the projects each links, every
malformed record of the picks, every id production holds, and every missing
value; and whether the mapping is clean — no malformed record, no conflict,
no missing value and at least one pick — which alone lets the confirmation
step be shown. A mapping of no pick is not clean (`no_picks`): an import of
nothing is not confirmed.

### Observable effect

None.

### Enforces

The closure first: when it exists, refused (A16 rule 8). The file over the
`release_declarations.import_size_limit`, not readable as the format States
5 and 6 declare, holding two projects with one id, or a project without a
readable id or status, refused whole at upload (A16 rule 3, A19 rule 4). Only what the
picks bring in is checked (rule 3); a record is malformed as rule 4 says, a
pointer of a type `release_declarations.declared_artifact_types` does not
declare or whose owner service is not `release_declarations.owner_service_of_type`'s
among them (A22 rule 7); ids compared per kind (rule 5); names read with
`given_values` (A02). Nothing is executed or evaluated (A19 rule 4).

### Errors

`refused` (`import_closed`); `invalid_request` (`file_too_large`,
`file_unreadable`, `file_malformed`).

### State impact

Reads the closure and the ids production holds; writes nothing.

## `public_op:migration_import.confirm_import`

### Owner

`module:migration_import`. Check the mapping again and have every picked
record written by its own module, in the import's one transaction (A16
rules 6, 7).

### Callers

`module:operations`.

### Inputs

The transaction; the kept file, or that none is kept; the bound digest; the
picks, names, aliases and Customer values the confirmation bound; the
action's instant.

### Outputs

The written projects and, for each Customer made, its v1 value and its
minted `customer_ref` (rule 10).

### Observable effect

Through `projects.write_imported_project`,
`customers.make_imported_customer` and
`artifact_pointers.write_imported_pointer`: the picked projects with their
objects, rooms and pointers under their own ids and instants, the import
their pointers' publisher, and the Customers made at the action's instant.

### Enforces

The closure first (rule 8); the file of the bound digest still kept, its
digest computed again from the kept bytes (rule 2); the picks checked
again — any conflict, malformed record or missing value, or no pick at all,
refuses the whole import (rule 6); the values the confirmation bound and nothing else;
the projects link to the Customers it makes (R0-80).

### Errors

`refused` (`import_closed`, `file_not_kept`, `mapping_not_clean`,
`no_picks`).

### State impact

Writes Projects, Rooms, Customers and pointers, all in the one transaction.

## `public_op:migration_import.record_migration_closure`

### Owner

`module:migration_import`. Write the migration closure once the import's
records are written (M10, A16 rule 7).

### Callers

`module:operations`.

### Inputs

The transaction; the accepted file's digest; the confirmation id
`operations` minted; the action's instant.

### Outputs

The closure.

### Observable effect

The one closure of the instance; from now on every upload, mapping, step and
confirmation is refused (rule 8).

### Enforces

Written in the import's transaction after its records and before its entry;
a failed transaction leaves none, and the import may be retried (rule 9).

### Errors

None.

### State impact

Writes the closure.

## `public_op:backups.probe_backup_location`

### Owner

`module:backups`. Probe the backup location at the start (A17 rule 2, A18
rule 5).

### Callers

`module:instance_lifecycle`.

### Inputs

The configured backup location.

### Outputs

That the location takes and gives up a file, or a diagnostic naming the
failure.

### Observable effect

A probe file under the temporary prefix of
`release_declarations.backup_name_prefixes` is created and removed; one it
cannot remove stays, for the next run's first step (A18 rule 4).

### Enforces

No other file of the location is touched; a regular file directly in it,
no link followed (A18 rule 5).

### Errors

The diagnostic; the start stops on it.

### State impact

Creates and removes one file.

## `public_op:backups.run_daily_backup_if_due`

### Owner

`module:backups`. The minute look: when a date's run is due, run it in its
three steps (A18 rules 1, 4, 5).

### Callers

`module:instance_lifecycle`.

### Inputs

The configured backup location and key.

### Outputs

Nothing to the caller; a run's failure, and each file step 3 could not read
or delete, is a diagnostic (Conventions, "Diagnostics").

### Observable effect

When due: the temporary files removed; a backup — the copy of
`store.copy_store_snapshot` encrypted with the key, its record holding the
instant, the release from `release_declarations.release_versions`, the last
sequence number and the key's digest — checked by decrypting it and asking
`store.check_store_file`, and kept under a name made from its instant; the
backups older than 30 × 24 hours and the unreadable kept files deleted.

### Enforces

Due at the first look at or after 03:00 UTC, by `clock.recorded_now`, of a
date an earlier look of this process saw before 03:00, when this process
did not run it, no run is going and no kept backup of the date exists; a
run's date remembered, failed included (A18 rule 1); runs never overlap; the
unencrypted copy removed before the check; a kept name never overwritten;
only files under the two prefixes touched (rule 5); step 3 whatever step 2
did, one cutoff, in name order (rule 4). Never in an owner-only start (rule
9).

### Errors

None to the caller; Registry keeps serving.

### State impact

Writes, renames and deletes files in the backup location; writes no record.

## `public_op:backups.newest_backup_instant`

### Owner

`module:backups`. The instant of the newest kept backup, for the owner
interface (A18 rule 1).

### Callers

`module:operations`.

### Inputs

The configured backup location.

### Outputs

The instant of the newest kept backup whose record can be read; that there
is none; or that the location could not be listed, which is never shown as
"none".

### Observable effect

None.

### Enforces

One listing of the location; read while a run renames or deletes, it shows
the state before or after, never a temporary file (A18 rule 1).

### Errors

None.

### State impact

Lists the backup location; writes nothing.
