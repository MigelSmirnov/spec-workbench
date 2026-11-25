# State 2 — Registry installation rules: import, configuration, backups, security review

Draft of 2026-10-31. The owner accepted the proposals behind A16–A18 on
2026-10-31 (answers 13–15 of the State 2 plan), and A19 and A20, which the
security review proposed, the same day. They settle what State 0 carried here: the
import's mapping check and how Registry knows it succeeded (R0-34, R0-79),
backup and tested restore and encryption at rest (owner, 2026-10-27), and the
security review of States 0–2.

## Accepted decision A16 — the import shows its mapping, then applies it in one transaction

### Normative rules

1. The owner uploads the export file (R0-72) in the owner interface. Registry
   reads it as data (A19) and answers, without changing anything, each
   project the file holds with its id and status. As the owner picks projects,
   the mapping shows for the picks only: their rooms and pointers; the display
   name and alias each will arrive under — its v1 name and no alias unless the
   owner gives others (R0-85), a name being required (A02). That a project
   named after a person gets another name here is a rule on the owner, like
   R0-68's: Registry shows each v1 name to keep or replace and cannot tell a
   person's name (R0-82); the Customers the
   import
   will make — one for each distinct v1 `customer_ref` a picked project names,
   which is all the file says of a customer (State 1 M04) — with the projects
   each will link (R0-80); and every malformed record of the picks and every id that
   conflicts with one production holds. For each Customer it will make, the
   owner gives its name and kind and says whether the v1 value is its tax id;
   confirmation is refused while any of these is missing (A02), or while a
   name or alias the owner gives breaks A02 — an alias longer than 40
   characters included. While the
   mapping shows a malformed record, a conflict or a missing value, the
   import's confirmation step is not shown; nor while a name or alias the
   owner gives breaks A02; a confirmation applies only a clean mapping
   (rule 6). Each new
   Customer's `customer_ref` is minted when the import is accepted.
2. The uploaded file is kept in the owner session that uploaded it, in the
   process's memory only — never in the store, never on a disk — until the import is accepted, another file is uploaded in that
   session — one of the same bytes included — or the session ends (M11); then it is dropped. A refused
   confirmation keeps it, and the step may be shown again; a refused upload —
   too large or unreadable — replaces nothing. An accepted import drops the
   uploaded file of every owner session (M11); a confirmation shown in
   another session is refused because the import is closed (rule 8). Uploads
   and every other request that reads or changes an uploaded file — showing
   the mapping or the import's confirmation step, confirming, a sign-out —
   take the instance's one import lock first, then their session's lock
   (A13), check the closure while holding them, and hold both until done;
   when the closure exists, uploading, showing the mapping or the import's
   confirmation step and confirming are refused, and a sign-out goes on.
   An uploaded file is changed only by a holder of the import lock: an
   accepted import, holding it, drops every session's upload; the upload of
   a session ended by its limits goes with the session, when Registry ends it
   (A13 rule 2). Other
   session changes take their session's lock alone. So no upload lands after
   the import that closed it, and the two locks are always taken in that
   order. The mapping names
   the file by its digest. The owner confirms that mapping in the confirmation
   step (A13 rule 6); the confirmation applies the file of that digest, the
   picks, names, aliases and Customer values the mapping showed, nothing
   else; a file no longer kept is refused and must be uploaded again.
3. Registry checks what the picks bring in — each picked project with the
   rooms and pointers that name it and the v1 value it names — and nothing
   else of the file; a room or pointer naming another project belongs to that
   project: records only of projects the owner did not pick are neither checked,
   shown as conflicts nor imported, and take no part in the duplicate-id
   check. A file that cannot be read as the format States 5 and 6 declare,
   that holds two project records with one id, or a project record whose id
   or status is missing or cannot be read, is refused whole at upload, before
   anything is picked.
4. A brought-in record is malformed when: a required value is missing (A02);
   it names a project or room the file does not hold; an id occurs
   twice among the file's records of one kind; a status is outside its
   vocabulary, or a pointer is `withdrawn` (v1 never withdrew one, M05); a
   pointer's type is not declared or its owner service is not the type's
   (A22); the versions of a project's pointers of one type are not 1..n, or
   are not every one `superseded` but the highest, which is `published`; an
   instant cannot be read; an `active` project has an
   archived instant or an `archived` one has none; a `superseded` pointer has
   no superseded instant or a `published` one has one; a record's own instant
   of change, archiving or supersession is before its own instant of creation,
   adding or publishing. Imported history is not held to anything more: an
   archived project's last-changed instant may differ from its archived
   instant (v1 allowed correcting archived projects, L05), and a record's
   instants are not compared with another record's.
5. Ids are unique per kind: a project id, a room id and a pointer id are
   compared only with ids of their own kind, in the file and in production.
6. A confirmation applies the mapping of the file and the picks it is bound
   to (rule 2, A13 rule 6), which it builds once, from the kept bytes,
   inside the confirming transaction, as it must to write the records; it
   applies that mapping only when it is clean, and otherwise refuses the
   whole import, and nothing changes (R0-50, R0-79). The file and the
   picks are bound by their digest, the names, aliases and Customer values
   with them, so the mapping it builds is the one the step showed but for
   the ids production gained in between; every such id is one Registry
   mints at random (Identity formats; M01, M03, M05), the import — the one
   path for an id from outside — being closed after its one success
   (rule 8). A minted id equal to one of the picks' is improbable, not
   impossible: when it happens the mapping built in the confirming
   transaction shows that conflict, the confirmation is refused whole and
   nothing changes, and the step asked again shows the conflict. What a
   test sees of this rule is that a mapping showing a conflict or a
   malformed record gives no step and changes nothing (Required tests 2
   and 11), and that the confirming transaction applies only a clean
   mapping and refuses an unclean one (Required test 13). Restated on
   2026-11-24, under the owner's direction of that day (data-protection
   matrix, `sources/privacy_requirements_20261123.md`: every measure names
   the test that confirms it), after the witness review
   (`tests/semantic/review/SUMMARY.md`, finding 1) found the former text,
   "At confirmation Registry checks again", naming a second check: the
   check is the building of the mapping the confirmation applies, made once
   in its transaction, and the step shows its result. Restated again on
   2026-11-25, after the State 2 round-120 (T1) found that the text then
   said no confirmation could find a conflict its step did not show, while
   random minting makes such a conflict improbable, not impossible: the
   claim is dropped, and the refusal of an unclean mapping in the
   confirming transaction is what keeps the import whole.
7. An accepted import stores every picked project with its rooms and pointers,
   the Customers it makes, the migration closure (M10) and its one audit entry
   (M09) in one transaction. The import has succeeded when that transaction
   is committed; Registry knows it by the closure. Confirmations are applied
   one at a time: of two concurrent ones, the second finds the closure and is
   refused (rule 8).
8. While the closure exists, uploading and confirming an import are refused
   (R0-79).
9. A refused import may be retried with a corrected file; nothing of a refused
   attempt remains.
10. The import answers once its transaction commits, listing for each
   Customer it made its v1 value and the `customer_ref` minted for it. It
   reaches the backups with the first kept backup whose snapshot begins after
   it committed (A18 rule 1). A store lost before a
   kept backup holds the import loses it, and the import may then be made
   again (R0-89).

### Formal invariants

```text
import(file f, picks P) accepted => stored(P with rooms, pointers) and
stored(new customers of P) and closure.file_digest = digest(f) and one
AuditEntry, in one transaction   -- A16-1
exists closure => import refused   -- A16-2
mapping(f, P) shows a conflict or a malformed record => no confirmation step
for P, import(f, P) not accepted, store unchanged   -- A16-3
```

### Required tests

1. Uploading answers the mapping and changes nothing; reading the store after
   it shows no imported record.
2. A file whose one pointer id production holds refuses the whole import:
   the mapping names the conflict, no confirmation step is shown, and
   nothing of the picks — a clean one included — is imported.
   Shows A16-3. [witness: verification:registry_a16_held_pointer_id_refuses_whole_import]
3. Confirming a mapping after another file was uploaded in the session is
   refused: the file it named is no longer kept — also when the new file has
   the same bytes.
4. A second import after a successful one is refused.
   Shows A16-2. [witness: verification:registry_a16_second_import_after_success_refused]
5. A failure during the transaction leaves no project, no Customer and no
   closure.
   Shows A16-1. [witness: verification:registry_a16_failed_transaction_leaves_no_import]
6. A conflicting id belonging only to a project the owner did not pick does
   not refuse the import.
7. A room naming a project absent from the file belongs to no pick: it is
   not imported and does not refuse the import.
8. Confirming without a kind for a Customer the import makes is refused.
9. A picked project holding a `withdrawn` pointer refuses the import as
   malformed.
10. Confirming after the owner session that uploaded the file has ended is
    refused.
11. Asking for the import's confirmation step while the mapping shows a
    conflicting id is answered with that mapping, not with a step: no step
    is shown and no confirmation value is made, so the value of an earlier
    clean step stays pending. (Restated on 2026-11-24 after the witness
    review, finding 2: it read "is refused", and the request is answered,
    not refused — rule 1, "the import's confirmation step is not shown".)
12. An accepted import stores every picked project with its rooms and
    pointers, the Customers it made, one closure holding the file's digest and
    exactly one audit entry; a failure inside its transaction leaves none of
    them — no project, room, pointer, Customer, closure or entry.
   Shows A16-1. [witness: verification:registry_a16_accepted_import_stores_all_in_one_transaction]
13. A confirmation whose mapping, built in the confirming transaction, is
    not clean is refused whole and nothing changes: a test that makes
    production hold one of the picks' ids after the step was shown — the
    id Registry mints at random being the only way, which a test can
    arrange only by replacing the random source — sees the refusal, the
    store unchanged and the conflict on the step asked again (rule 6).
    Through Registry's surfaces alone a minted id cannot be chosen, so the
    refusal is checked on the code by the Factory — `confirm_import`
    builds the mapping inside the confirming transaction and applies it
    only when clean — and carried to Factory verification (2026-11-25,
    round-120 T1).

### Consequence

The owner sees exactly what will arrive before anything does (R0-34), and the
closure is the one proof of success.

## Accepted decision A17 — configuration and secrets are checked before Registry serves

### Normative rules

1. The configuration is a set of environment variables whose names begin
   with `REGISTRY_`, set as R0-23 says. Registry reads exactly the items
   below and no other variable: a variable whose name names none of them —
   one beginning with `REGISTRY_` included — is neither read nor checked and
   does not stop the start (owner, 2026-11-11: only the one module that reads
   the environment sees it, and it reads the items it declares). A misspelt
   name is such a variable: the item it was meant to set is then not set. For
   a required item that stops the start, naming the item as missing; for a
   service token it is rule 2's all-or-none — some of the four set and the
   misspelt one not makes the start fail on the missing token, and none of
   the four set makes an owner-only start, whose service API answers nothing;
   the service API's address goes with the tokens in the same way.
   Registry's code receives each item as a field of the settings the one
   module that reads the environment loads; no other part of Registry reads
   a variable. The items are exactly these: the store's
   location; the backup location and the backup key (A18); the owner
   credential; the address the owner interface listens on; one service token
   for each service of A09 — PresuPro, Client Portal, Cabinet, Cabinet Kernel
   (R0-20, R0-23) — and the address the service API listens on, or, for an
   owner-only start, none of these five: Registry then serves the owner
   interface alone,
   opening no listener of the service API, so a service call reaches no
   Registry and is refused by its connection failing, with no answer (owner,
   2026-11-01; A18 rule 9). An address is a host and a port, `host:port`:
   the host an IP address — an IPv6 one in brackets — and the port a whole
   number from 1 to 65535, the data provider's constants `LISTEN_PORT_MIN`
   and `LISTEN_PORT_MAX`, which the checking code imports (SPEC_STANDARD
   §15.3.1). Written as text, with no sign and no white space anywhere: an
   IPv4 host is four numbers from 0 to 255 in ASCII decimal digits, none
   with a leading zero but 0 itself, joined by dots; an IPv6 host is in
   brackets and is an address in the text form of RFC 4291 section 2.2,
   with no zone identifier and not an IPv4-mapped address (`::ffff:0:0/96`);
   the port is ASCII decimal digits without a leading zero. The
   configuration hands each address on as its host and port. The two
   addresses have different ports, so that the two surfaces' endpoints
   never overlap, whatever their hosts. Registry binds each listener
   exclusively — it sets no option that lets a second active socket bind
   an overlapping endpoint — and an IPv6 listener accepts IPv6 connections
   alone, never IPv4 ones mapped onto it; whether a port a closed listener
   left can be bound again at once is the platform's, which Registry
   neither requires nor prevents. The addresses are the deployment's: the
   service API is reachable only in VM Platform and over the WireGuard
   channel from the VPS, the owner interface from beyond the home server
   only through the owner's VPN, with no public port (R0-28, R0-29, R0-48), and the interface each is bound to on that host,
   or on a test instance's (R0-34), is the host's administration — so the
   configuration names them
   (owner, 2026-11-11, replacing the release-fixed addresses of 2026-11-01:
   one release cannot hold both).
2. Registry checks the configuration when it starts and serves nothing until
   every check passes; a failed check stops the start with a diagnostic that
   names the failed item and never its value (R0-37). The checks run in one
   order and the first that fails stops the start: the service tokens and the
   service API's address all five or none — none makes an owner-only start,
   and some but not all fail on the first missing one in rule 1's order; every other item of rule 1 present; each well formed; the two addresses'
   ports different; each secret's length (rule 3);
   their distinctness (rule 4); the store and backup location apart (rule
   5); the backup location writable, by a probe file under the temporary
   prefix (A18 rule 5); the store opening, or made new (rule 5); last, the
   listener of each surface opened at its configured address (rule 1) — the
   owner interface's first, then the
   service API's unless the start is owner-only, one that cannot be opened
   failing the start and closing the one already opened. Within one
   check, items go in the order rule 1 lists them. A failed start leaves no
   file it made but one it could not remove: a probe, which the next backup
   run removes with the other temporary files (A18 rule 4); a file of the
   store's temporary name, which the next start removes first (rule 5); or a
   store it made new for a start a listener then failed, which it removes —
   one it cannot remove is an empty store of the release's version, which the
   next start opens as any store. A start leaves the
   backup location's other files as they are.
3. A secret — each token, the owner credential and the backup key — is at
   least the imported `SECRET_MIN_BYTES` constant (32, SPEC_STANDARD §15.3.1)
   of bytes in UTF-8 long; a shorter one fails the start. Registry checks the
   length and, by rule 4, the distinctness, and nothing else of how the owner
   made it (R0-23).
4. No two secrets are equal: two services with one token, or a token equal to
   the owner credential, fail the start.
5. A missing or malformed item fails the start; Registry applies no
   default to any item. The backup location must exist and let Registry create
   and remove a file in it; otherwise the start fails. It holds Registry's
   files only; the owner puts nothing else there. The store and the
   backup location are different places, neither inside the other, compared
   by their absolute paths with every symbolic link resolved — for a store
   file that does not exist yet, its directory resolved and its name added; a
   path that cannot be resolved, a broken link or a loop included, fails the
   start; a configuration
   where they are the same or one holds the other fails the start. Aliases a
   path comparison cannot see, such as bind mounts, are the owner's to avoid
   (Explicit exclusions). When the store's
   configured file does not exist and its directory does, Registry makes a new,
   empty store of the running release's version there at the start — no
   record but its audit sequence at 0 (M12) — under a
   temporary name — the store's name with a suffix the release declares —
   that it renames to the store's name only once the store is complete; at
   every start it first removes a file of that temporary name, left by an
   interrupted start, and no other file there — if it cannot, and the store
   is absent, the start fails; otherwise
   the store must open for reading and writing, pass the full integrity check
   — the store is a SQLite database, as v1's (L19), and the check passes when
   `PRAGMA integrity_check` answers `ok` and `PRAGMA foreign_key_check` finds
   nothing, the same as a backup's check (A18 rule 4) — and carry
   the store
   version of the running release, and a store of another version, or one
   that does not open, fails the start — bringing a store to a new version is
   a step of the release, not of the start.
6. A presented secret is compared in constant time; no secret enters a record,
   a log line, an audit entry, a diagnostic or an answer (R0-23, R0-37).
7. A change of the configuration takes effect at the next start (R0-20). A
   compromised token is revoked by replacing it and restarting. A token is a
   bearer secret: a valid one presented again is valid, on channels that
   reach Registry only from VM Platform or the WireGuard tunnel (R0-28,
   R0-39); wrong tokens are refused each time without a limit, guessing 32
   random bytes being out of reach.

### Formal invariants

```text
serving => checks_passed(config)   -- A17-1
for secrets s1 != s2 in config: value(s1) != value(s2)   -- A17-2
for every secret s in config: utf8_bytes(value(s)) >= SECRET_MIN_BYTES   -- A17-3
a start whose listener cannot be opened => it serves nothing, leaves no
listener of it open, and the store holds the records it held before that
start — for a store that start made new, no store, or, when its removal
fails, an empty one holding no record but its audit sequence at 0   -- A17-4
```

### Required tests

1. A configuration with some service tokens but without Client Portal's
   stops the start and names the missing item; one with none of the four
   and no service API address is an owner-only start.
   Shows A17-1. [witness: verification:registry_a17_missing_token_stops_start_none_owner_only]
2. Two services with one token stop the start, and so does each other pair
   of equal secrets: a token and the owner credential, a token and the
   backup key, the owner credential and the backup key.
   Shows A17-2. [witness: verification:registry_a17_equal_secrets_stop_start]
3. A 16-byte token stops the start. For each kind of secret — a service
   token, the owner credential and the backup key — a value one byte shorter
   than `SECRET_MIN_BYTES` stops the start and one of exactly
   `SECRET_MIN_BYTES` bytes is accepted. The length is counted in UTF-8
   bytes, not characters: a token of 16 two-byte characters (32 bytes) is
   accepted, and one of 15 two-byte characters and one one-byte character
   (31 bytes) stops the start.
   Shows A17-3. [witness: verification:registry_a17_secret_length_counted_in_utf8_bytes]
4. The start diagnostic never contains a secret's value.
5. A start whose store is made new and whose listener then cannot be opened
   — the owner interface's, or the service API's after the owner
   interface's was opened, which is closed again — stops, serves nothing and
   removes that store; one whose listener cannot be opened over an existing
   store leaves that store's records as they were. A removal that fails,
   leaving an empty store of the release's version, cannot be made to happen
   through the surfaces without failing the store's making too; it is
   carried to Factory verification.
   Shows A17-4. [witness: verification:registry_a17_listener_failure_serves_nothing_keeps_store]
7. A complete configuration with variables that name no item —
   `REGISTRY_EXTRA`, `REGISTRY_`, and one without the prefix — starts, and
   none of them appears in a diagnostic or a setting; one where the backup key
   is set as `REGISTRY_BACKUP_KEYY` instead of its own name stops the start,
   naming the backup key as missing; one with three tokens set and the fourth
   misspelt stops the start naming that token; one with only a misspelt
   token and no other token starts owner-only.
   Shows A17-1. [witness: verification:registry_a17_unknown_variables_ignored_misspelt_item_missing]
8. The four tokens without the service API's address stop the start naming
   the address; the address without the tokens stops it naming the first
   token. An address `127.0.0.1:8781` is accepted, `[::1]:8781` too;
   `localhost:8781`, `127.0.0.1` and `127.0.0.1:0` stop the start, naming the
   item. Two addresses with one port, `127.0.0.1:8781` and
   `0.0.0.0:8781`, stop the start naming the service API's address.
   Shows A17-1. [witness: verification:registry_a17_service_address_with_tokens_and_wellformed]
9. `[fe80::1%eth0]:8781`, `[::ffff:127.0.0.1]:8781`, `127.0.0.01:8781` and
   `127.0.0.1:08781` each stop the start, naming the item. While Registry
   runs, a second socket binding the service API's endpoint fails; an IPv4
   client cannot reach an IPv6 listener.
   Shows A17-1. [witness: verification:registry_a17_address_text_form_and_exclusive_bind]
6. A store made new holds exactly one audit sequence (M12), at 0, and no
   other record; a start interrupted before the store's rename leaves no
   store under the store's name, and the next start makes a new one with
   one sequence at 0.

10. Each check made before the listeners are opened that fails — a
    configuration item, a backup location that cannot be written, an existing
    store failing its integrity check or of another version, a new store that
    cannot be made — stops the start before any listener is opened, and no
    request is served. When the service API's listener cannot be opened
    after the owner interface's was, the owner interface's is closed and no
    request is served on it.
   Shows A17-1. [witness: verification:registry_a17_failed_check_stops_before_any_listener]

### Consequence

A wrong configuration is found at start, not by a caller; a leaked or weak
secret cannot be shared between holders.

Restated on 2026-11-24, under the owner's direction of that day
(data-protection matrix P6 and D5: every security measure names the test
that confirms it), after the witness review
(`tests/semantic/review/SUMMARY.md`) and the independent judge of the
witnesses found that test 5, about a listener that cannot be opened, was
bound to A17-1, which speaks of the configuration's checks, and that A17-2
held two conditions no one test shows: A17-2 was `for secrets s1 != s2 in
config: value(s1) != value(s2) and len >= SECRET_MIN_BYTES`; it is now the
distinctness of rule 4 alone, the length of rule 3 is A17-3, and a failed
listener (rule 2, last check) is A17-4, test 5's. A17-4 restated on
2026-11-25, after the State 2 round-120 (T13) found that its "none, for a
store that start made new" denied the empty store rule 2 leaves when its
removal fails, which holds its audit sequence at 0 (rule 5, M12): it now
names that store. The owner-only start's
missing service listener is test 1's. No normative rule changed. Test 6's
start interrupted before the store's rename is shown only by its outcome,
a file of the temporary name removed by the next start: the interruption
itself needs a capability the surfaces do not have, and is carried to
Factory verification.

## Accepted decision A18 — daily encrypted backups, checked when made, kept 30 days

### Normative rules

1. These runs are R0-89's daily backups: one is due each day, and the days
   this rule and rule 5 leave without a kept backup are allowed. Every day at
   the daily time, the imported `BACKUP_DAILY_TIME_UTC` constant (03:00 UTC,
   SPEC_STANDARD §15.3.1), while Registry runs with its service tokens, it
   makes one backup run; "03:00" in this decision reads as that constant; a 03:00 that finds Registry stopped, or in an
   owner-only start (rule 9), makes no run, and none is made later in its
   place. The process looks at the clock at least once in each interval of
   the imported `BACKUP_LOOK_SECONDS` constant (60 seconds); a date's
   run starts at its first look at or after 03:00 of that date when an
   earlier look of the same process saw that date before 03:00, and no kept
   backup of that date exists — a kept backup's date being the UTC date of
   its recorded instant, and a file whose record cannot be read counting as
   none (rule 4), so
   a restart, a start at 03:00 or a clock set back makes no second run. A
   process runs each date at most once, remembering in its memory the dates
   it ran, a failed run included; a run's date is the date of the look that
   started it. A clock set forward past 03:00 of a date gives that date no
   run, the earlier look having seen another date, and the dates jumped over
   get none either. A
   failed date is run again only by a later process that sees 03:00 of it
   pass, which only a clock set back makes happen, and that is allowed. Runs
   never overlap: a 03:00 that finds a run still going makes no run of its
   own. A backup is a consistent copy of the store taken while Registry runs:
   one snapshot of the store, as one read transaction sees it, while other
   transactions go on; it never holds part of a transaction, and its
   recorded instant and last sequence number are those of that snapshot,
   the instant being that of the read that fixes its snapshot (below). No
   write is refused or fails because a copy is being made, nor a copy
   because of a write; how long either may wait for the other is a setting
   of the store's engine, with the files it uses, which State 6 fixes. The
   copy's read transaction fixes its
   snapshot by its first read, which is of the audit counter's last
   sequence number, and the instant is read from the clock at that read; a
   change committed after it is not in this backup, which holds the store as
   its snapshot saw it, and a later backup holds whatever the store holds
   when its own snapshot is fixed. It
   records, readable without its key, its instant, the release that made it,
   the last audit sequence number its store ever wrote — kept apart from the
   entries (A15; M12 AuditSequence), 0 for a store that never wrote one, whatever the log now
   holds — and a digest of the key it was
   made with (never the key); its age is counted from that instant. The
   owner interface shows the instant of the newest kept backup whose record
   can be read, or that there is none, from one listing of the backup
   location; read while a run renames or deletes, it shows the state before
   or after that change, never a temporary file.
2. A backup holds every record but the agent sessions (M06), which are
   removed from the copy before it is encrypted, so the copy is a store of
   its own that passes the same checks; Registry's other invariants are not
   checked again in it, its transactions having kept them: a store restored
   from it has no session, Kernel registers its sessions again and the owner
   grants them again, so a restore never brings back a grant revoked after
   the backup.
3. Each backup is encrypted with the backup key the configuration holds at its
   making (A17). When the owner changes the key, older backups stay encrypted
   with the key they were made with, which the digest each backup records
   names. Registry decrypts a backup only to check it when it is made
   (rule 4); decrypting an older one, with the key it was made with, is part
   of a restore, outside Registry (rule 8, R0-89).
4. A run goes in three steps. First, it removes every file under the
   temporary prefix; if a removal fails, the run stops there. Second, it
   writes the backup under a temporary name and checks it: it decrypts it
   into a second temporary file, opens that for reading only, checks that it
   is the store version of its release, that the full integrity check (A17
   rule 5)
   passes and that the last sequence number it keeps (A15) equals the
   recorded one, and
   removes it; a backup that passes is renamed to its kept name, one that
   fails is deleted. When the decrypted file cannot be removed, or a failed
   backup cannot be deleted, the backup stays under its temporary name and
   is not kept, the run fails, the third step still runs, and the next run
   removes what is left. This is the tested restore: no other instance is made
   from a backup. Third, whatever the second step did, it deletes every kept
   backup made more than 30 × 24 hours before the instant this step starts,
   one cutoff for the whole step — a backup made exactly 30 × 24 hours before
   it is kept. The step reads the clock once, before it looks at any file,
   and its cutoff is that UTC instant less exactly 720 hours. The clock is
   read to the microsecond, and a backup's record holds its instant in UTC
   to the microsecond (L16), so the cutoff and every record's instant have
   one precision and are compared as they are, neither rounded nor
   truncated; a backup whose instant is earlier than the cutoff is deleted. The 30 × 24 hours are one value of the release, the data
   provider's constant `BACKUP_RETENTION_HOURS` = 720, which the code that
   deletes imports (SPEC_STANDARD §15.3.1); no other place holds it. It also
   deletes every file under the kept
   prefix whose unencrypted record (rule 1) cannot be read. It takes the
   files in the order of their names; a file it cannot read or delete is
   reported, and it goes on with the next. A run succeeds only when every
   step did; one whose backup was kept but a deletion failed is failed, and
   its new backup stays kept.
5. Kept and temporary names begin with two different prefixes the release
   declares, neither beginning with the other: `registry-backup-` for a kept
   backup and `registry-tmp-` for a temporary file, the data provider's
   constants `BACKUP_KEPT_PREFIX` and `BACKUP_TEMPORARY_PREFIX`, which the
   backup code imports (SPEC_STANDARD §15.3.1) — technical values the author
   chose on 2026-11-11, not configuration (A17 rule 1); a kept file's record is valid
   when its instant, release, last sequence number and key digest can all be
   read, and only a valid one counts as a kept backup; Registry removes, renames and deletes in the backup location
   only files under them, and the location is Registry's alone (A17): a file
   is under a prefix when it is a regular file directly in the location whose
   name begins with it; Registry follows no link and enters no directory
   there. A kept
   name is made from the backup's instant and is never overwritten: a backup
   whose kept name exists, or whose rename fails, is deleted and the run
   fails. A step that fails leaves no partial kept backup — only files under
   the temporary prefix, the backup and its decrypted copy among them, which
   the next run removes —
   and writes a diagnostic that names the failure and no value (A17);
   Registry keeps serving, and the next 03:00 tries again. Whether runs
   succeed is the owner's to watch on the host (Explicit exclusions: the
   host's administration).
6. While the daily runs succeed and each ends before the next 03:00, an
   erasure reaches the backups by the first
   run after the last backup holding the erased values is more than 30 × 24
   hours old (rule 4) — at
   most 31 days after the erasure — and a failed or missed run lengthens that
   by the days until a run succeeds. A restore loses the changes made after
   the backup it uses; Registry bounds neither how long a run takes nor how
   old the newest kept backup may be.
7. The store, the backup location and the disks under them are encrypted and
   kept out of VM Agent's reach by the owner's administration of VM Platform
   (R0-48; Explicit exclusions); Registry does not check the host. What
   Registry guarantees of a kept backup (A18-2) holds when it becomes kept,
   by the check of rule 4; a kept file changed or damaged afterwards by the
   host's storage is outside Registry, which does not check kept backups
   again — the storage and its encryption are the host's administration
   (data-protection matrix row D5). Decided on 2026-11-25 under the owner's
   direction of 2026-11-24 (matrix row D5), after the State 2 round-120
   (T23) asked whether A18-2 holds when a backup becomes kept or for as long
   as it is kept; the owner may reverse it.
8. Registry has no restore operation (R0-89). A store the owner puts in
   place of a lost one starts as any store (A17 rule 5) — by the release that
   made its backup, or by a later one after that release's own store
   migration — and begins its own history from the backup: numbering
   continues from its last number (A15), and a store without the migration
   closure accepts the import (A16).
9. An owner-only start (A17 rule 1) serves the owner interface alone, with no
   service API listener, and makes no backup run.

### Formal invariants

```text
after a run whose deletions succeeded: no kept backup whose instant is
earlier than its third step's cutoff (that step's start less
30 × 24 hours) exists   -- A18-1
after a run whose deletions succeeded: no backup that failed its check
exists, kept or temporary   -- A18-3
every backup, when it becomes kept, is encrypted, consistent, checked, and
records (instant, release, last sequence); no backup holds an agent
session   -- A18-2
```

### Required tests

1. A backup taken during a write restores either before or after it, never in
   between.
   Shows A18-2. [witness: verification:registry_a18_backup_during_write_is_one_snapshot]
2. After a run in which the backup failed, backups older than 30 × 24 hours
   are still deleted.
   Shows A18-1. [witness: verification:registry_a18_failed_backup_still_deletes_old_backups]
7. With the step's cutoff fixed at its start, a kept backup made exactly
   30 × 24 hours before it is kept and one made a microsecond earlier is
   deleted; a record instant with a non-zero fraction of a second is
   compared with that fraction, not at the whole second.
   Shows A18-1. [witness: verification:registry_a18_retention_cutoff_exact_to_microsecond]
8. The readable record of a kept backup holds the instant, release and last
   sequence number of the snapshot it was made from and the digest of its
   key; a backup whose decrypted sequence differs from its record is
   deleted.
   Shows A18-3, A18-2. [witness: verification:registry_a18_record_matches_snapshot_mismatch_deleted]
3. A backup cannot be read without the key it was made with.
   Shows A18-2. [witness: verification:registry_a18_backup_unreadable_without_its_key]
4. A backup whose integrity check fails is deleted and reported.
   Shows A18-3, A18-2. [witness: verification:registry_a18_integrity_failure_deleted_and_reported]
5. A store restored from a backup holds no agent session.
   Shows A18-2. [witness: verification:registry_a18_restored_store_holds_no_agent_session]
6. A 03:00 missed while Registry was stopped makes no backup at the next
   start; the next one is made at the following 03:00.

### Consequence

A tested restore exists after every run that keeps a backup, without a second instance holding
production data (R0-34); a restore cannot revive a revoked grant.

Restated on 2026-11-24, under the owner's direction of that day
(data-protection matrix S4 and D5), after the independent judge of the
witnesses found that A18-1 held two conditions no one test shows and read
its continuation as part of A18-2: A18-1 was `after a run whose deletions
succeeded: no backup older than 30 × 24 hours and no backup that failed its
check exists`; the age is A18-1, and the failed check is A18-3, shown by
tests 4 and 8; each formula is written whole, its identifier on its last
line. No normative rule changed. Restated on 2026-11-25 after the State 2
round-120: A18-1 compared a backup with a point 30 × 24 hours before the
cutoff, itself already 30 × 24 hours before the step's start (T20); it now
compares the backup's instant with the cutoff, as rule 4 does. A18-2 holds
when a backup becomes kept, later damage by the host's storage being
outside Registry (rule 7, T23). The tests' clocks do not move between two
reads of one run, so an implementation taking a backup's instant later than
the read that fixes its snapshot (rule 1) is not told apart; that remains
carried to Factory verification.

## Accepted decision A19 — every stored value is data, never code

Proposed by the security review and accepted by the owner on 2026-10-31: the
agent writes text the owner interface shows — room names (R0-68), access
request text (M08) — and the import reads a file from outside.

### Normative rules

1. The owner interface renders every stored value as text: escaped for the
   place it appears in, never as markup or script, whoever wrote it.
2. The owner interface sends no script of its own (R0-29) and forbids the
   browser to run any, by its content security policy.
3. A value a caller gives only ever fills a value place of a query or command
   whose structure the release fixes; it never becomes an identifier, an
   operator or syntax. A value that selects among fixed alternatives — a list
   order, a type — is checked against its closed list first. How the store's
   backend lowers this is the backend's.
4. The import file is read as data with a size limit of 50 MB, 50 × 1024 ×
   1024 bytes (owner, 2026-11-11); nothing in it is executed or evaluated, and
   a file over the limit is refused before any of it is parsed. The limit is counted
   over the bytes Registry receives, never over a length the request
   declares: a declared length over the limit is refused before any byte is
   read; otherwise Registry reads the upload up to one byte more than the
   limit and refuses it as soon as it holds more than the limit, whatever
   length was declared or whether one was. The upload is the file the owner
   interface's form sends as the second part of a multipart body, after the
   field that carries the CSRF value (A13 rules 5, 7; owner, 2026-11-17): the
   limit and every byte this rule counts are the file part's, never the
   form's framing. Its declared length is the request's declared length less
   the head read before the file — at most the imported
   `UPLOAD_FORM_HEAD_MAX_BYTES` constant, which the code that reads the head
   imports from the data provider (SPEC_STANDARD §15.3.1) — and the closing
   delimiter; "before any byte is read" is before any byte of the file. A refused upload is kept nowhere
   and replaces no file the session kept (A16 rule 2). The limit is one
   value of the release, the data provider's constant
   `IMPORT_FILE_MAX_BYTES` = 52428800, which the code that receives the
   upload imports (SPEC_STANDARD §15.3.1); no other place holds it, and it
   is not configuration (A17 rule 1).

### Formal invariants

```text
render(v) = escape(v) for every stored value v   -- A19-1
no stored value is ever evaluated or executed   -- A19-2
```

### Required tests

1. A room named `<script>alert(1)</script>` is shown as that text in the owner
   interface.
   Shows A19-1. [witness: verification:registry_a19_script_room_name_shown_as_text]
2. An access request text with markup is shown as text.
   Shows A19-1. [witness: verification:registry_a19_access_request_markup_shown_as_text]
3. A display name with a quote and a semicolon is stored and read back
   unchanged.
   Shows A19-2. [witness: verification:registry_a19_quote_semicolon_name_round_trips]
4. An import file of exactly 50 × 1024 × 1024 bytes, sent by the upload form
   with its CSRF field first, is read. One of a byte more is refused as too
   large, with no mapping shown, when no length is declared, when the true
   one is, and when the declared length of the file part is one byte short
   of it — the request's body then ending inside the closing delimiter, so
   every byte of the file arrives and more than the limit is read. A
   declared length so short that the body ends inside the file's own bytes
   ends the file before its closing delimiter, and the upload is refused as
   unreadable, the limit not being passed (State 5). Either way the file the
   session kept before stays kept. (Restated on 2026-11-24 after the witness
   review, finding 3: it read "also when its declared length is smaller",
   which held only while the shortfall does not reach the file's own bytes.)

5. A19-1, A19-2: every stored value a page of the owner interface shows —
   a value that is not text in the text it is shown as — in each kind of
   place it shows one — an element's content, an attribute's
   value, a value of a link's query — shown as that text when the value
   holds `<`, `>`, `&`, `"` and `'`, the page holding no element and no
   attribute made from it, and a value in a link's query, holding also `?`,
   `#`, `/`, `=`, `+`, `%` and a space, read back from the link as that one whole value, the
   link's origin, path and other parameters unchanged; every page forbids every script by its content
   security policy. Every page is made by one renderer, so this shows it for
   every stored value, whoever wrote it and whichever way it came in, the
   import file's included.
   [witness: verification:registry_a19_every_shown_value_escaped_csp_forbids_script]
6. A19-2: a display name holding a quote, a semicolon, a comment mark and
   a statement of the store's query language is stored and read back exactly
   as given, and the store afterwards holds what it held before, unchanged,
   and the records an accepted create writes, nothing else. Every
   value of a record reaches the store through the one statement backend
   the specification fixes, which fills value places only (rule 3), so this
   shows it for every value of a record given or imported.
   [witness: verification:registry_a19_query_language_in_name_not_executed]
7. A19-2: an import file whose values hold markup, a statement of the
   store's query language and text written as program code is read into
   those same values as text, unchanged, and nothing in it is executed or
   evaluated (rule 4).
   [witness: verification:registry_a19_import_values_read_as_text_not_evaluated]

### Consequence

Text the agent writes cannot act in the owner's browser; values never change
what Registry executes.

## Accepted decision A20 — a release fixes its dependencies

Proposed by the security review and accepted by the owner on 2026-10-31.

### Normative rules

1. A release names every dependency it runs with, at an exact version, with
   its digest: every Python package, direct or transitive, by the digest of
   its distribution file; the Python version; and the base image of VM
   Platform's Registry environment by its digest, which fixes the system
   libraries and the store's engine. Tools used only to build or test are not
   dependencies of the running instance.
2. A running instance uses exactly those; installing a dependency whose digest
   differs fails.
3. A dependency changes only by a new release, verified as any release.
4. Registry has no dependency that loads code at run time from outside its
   release.
5. Rules 1–4 are kept by the release process and its installation, which
   Registry does not manage (00_product.md, Explicit exclusions): they make
   the release, name its dependencies and install them, and Registry's own
   code reads none of it (owner, 2026-11-24). This decision therefore
   declares no formal invariant of Registry: no note of a module and no
   check of Registry's code can show what the installation does, and one
   claimed here would be a false witness.

### Formal invariants

None: kept by the release process and its installation outside Registry
(rule 5) — the running dependencies are the release's (name, version,
digest), which no note or check of Registry's code can show.

### Required tests

These are tests of the release process (rule 5), shown there and not by a
check of Registry:

1. Installing the release fails when the digest differs for any one
   dependency of each kind rule 1 names — a direct Python package, a
   transitive one, the Python version and the base image — and no instance
   of that release starts.
2. A release whose list misses a package the instance would import, the
   Python version or the base image, or names any of them without an exact
   version or a digest, is not made.
3. After an installation that succeeded, the dependencies the running
   instance has are exactly the release's list, by name, version and
   digest, nothing more.
4. A release's dependencies change only with a new release (rule 3): the
   same release installed again gives the same list.

### Consequence

What runs is what was verified.

## Accepted decision A21 — security review of States 0–2

### Normative rules

1. The categories are the nine of the Workbench's security review
   (`skills/spec-authoring/SECURITY_REVIEW_EVIDENCE.md`), the catalogue every
   case is reviewed against; this review is complete for that catalogue and
   claims nothing beyond it. Each outcome below answers the category's
   questions, as that catalogue states them, by naming the decisions that do,
   or, for NOT_APPLICABLE, why the category's subject is absent:
   - authentication_credential_abuse: guessing, credential stuffing, session
     and token lifecycle at every human and machine boundary; scope,
     revocation, replay, who owns the abuse controls;
   - secrets: where credentials live, where they must never travel — source,
     logs, diagnostics, exports — and how exposure is revoked or rotated;
   - authorization: object-level and owner scope, privileged operations,
     enforcement on the server independent of interface state, tied to the
     stable identities of State 1;
   - injection_interpreted_input: no input becomes query, command, template or
     other interpreted structure;
   - external_callbacks_webhooks: for each inbound callback, authenticity,
     replay, idempotency, allowed transition;
   - browser_boundary: output that could run in a browser, session and cookie
     rules, allowed origins, protection of state-changing requests;
   - files_artifacts: accepted type and size, path ownership, never executed,
     storage isolation, who may retrieve it;
   - concurrency: read-check-change races, single-use values, atomic
     transitions, duplicate submissions;
   - dependencies: which dependencies run, how they are fixed and verified.
2. A change to a decision a category names reopens this review.
3. Every decision a category names is accepted.

### Formal invariants

```text
for each category c: outcome(c) in {APPLICABLE, NOT_APPLICABLE}   -- A21-1
APPLICABLE c => references(c) are decisions of States 0-2   -- A21-2
```

### Required tests

1. Each APPLICABLE category's decisions have their own required tests, and
   those tests pass.
2. The review names all nine categories of rule 1, each once, each with the
   outcome APPLICABLE or NOT_APPLICABLE; every APPLICABLE category names at
   least one reference, and every reference is an accepted decision of
   States 0–2 that exists in this text; every NOT_APPLICABLE category gives
   its rationale. `tools/design_lint.py --state 2` shows it.

- Witness, A21-1, A21-2: the security-review check of `tools/design_lint.py --state 2`, which the State 2 gate of the authoring sequence runs [witness: workbench:state2_rules_decisions].

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A09, A13, A17; affected: M11, owner credential, service tokens, sign-in, owner session cookie
- secrets: APPLICABLE; references: A14, A17, A18; affected: owner credential, service tokens, backup key, diagnostics, audit log
- authorization: APPLICABLE; references: A04, A08, A09, A10, A11, A12; affected: M05, M06, every service operation, every agent-authority operation, owner session actions
- injection_interpreted_input: APPLICABLE; references: A02, A16, A19; affected: M03, M08, import file, every stored text value
- external_callbacks_webhooks: NOT_APPLICABLE; rationale: Registry calls no other service and receives no callback (R0-18, R0-54), and every request is a caller's authenticated call (R0-27)
- browser_boundary: APPLICABLE; references: A13, A19; affected: owner interface, CSRF protection, session cookie, rendering of agent-written text
- files_artifacts: APPLICABLE; references: A07, A08, A16, A18, A19, A22; affected: M05, M10, import file, backups, pointers as references whose payload Registry never reads (R0-02)
- concurrency: APPLICABLE; references: A01, A04, A07, A12, A13, A14, A15, A16, A17, A18; affected: M01, M03, M04, M05, M06, M09, M10, M11, a start serving nothing until every check passed and binding each listener exclusively (A17), concurrent creates, corrections, publishes, session changes, single-use confirmation values, confirmations bound to no revision, resubmitted forms on records without a revision, creates racing the erasure that removes their request id, re-uploads replacing a confirmed file, concurrent import confirmations, backup snapshots taken while transactions go on, overlapping backup runs
- dependencies: APPLICABLE; references: A20; affected: Registry release, its Python dependencies

Performed again on 2026-11-01, after that day's changes to A01, A04, A13, A16,
A17 and A18 reopened it (rule 2): every category naming them was reviewed, and no
outcome changed; concurrency now names A18 too, whose one-snapshot copy and
non-overlapping runs (rule 1) it relies on.

Performed again on 2026-11-11, after that day's changes to A01, A02, A04,
A07, A13, A15, A16, A17, A18 and A19 reopened it (rule 2): every category naming them —
injection_interpreted_input (A02, A16, A19), secrets, authentication and
concurrency (A01, A04, A07, A13, A15, A17, A18), browser_boundary (A13, A19),
files_artifacts (A07, A16, A18), authorization (A04) — was reviewed; the
changes to A01, A04 and A07 name constants and an exception of the
mapping's stage (4), and A07's concurrent publishes are those of different
request ids, which change no outcome; A15's new tests of concurrent appends rest on its rule 5,
which concurrency now names. No outcome changed. files_artifacts now names A19 too, whose
import size limit is counted over the bytes received, never over a declared
length (rule 4); a new store's one audit sequence (A17 rule 5) changes no
category's subject. A17's change of the same day — a variable that names no
item is not read and does not stop the start — and its second, the
listeners' addresses named by the configuration as the deployment's (R0-28,
R0-48),
with their text form, their exclusive binding and IPv6-only listening, and
the networks R0-28, R0-29 and R0-48 give each surface, were reviewed under authentication_credential_abuse and secrets: no outcome
changed — an address is no secret, and R0-28 and R0-48 keep which network may reach
each surface the deployment's — since such
a variable is never a credential Registry uses, never enters a diagnostic,
and a misspelt secret leaves its item unset, which stops the start or makes
the start owner-only (rule 1).

Performed again on 2026-11-17, after that day's change to A19 reopened it
(rule 2): the owner interface's upload form sends its CSRF field first and
the file second, as multipart, and A19 rule 4's limit, counting and
declared length are the file part's. Reviewed under files_artifacts and
injection_interpreted_input (A19), and browser_boundary (A13, A19): the
size limit still holds over the bytes of the file Registry receives, the
head before it is bounded by a constant and never kept, the CSRF value
still travels only in a form (A13 rule 7), and the session cookie is always
HTTPS-only, which is stricter than A13 rule 1. A13 rule 2's arrival of an
upload, changed the same day to the moment its bounded head has been read,
was reviewed under authentication_credential_abuse and concurrency: the
session is checked once, at that moment, with no state held between the
request's headers and its admission; an upload whose session reaches a
limit while its head is read is refused at the session check, as any
request arriving after the limit. No outcome changed.

Performed again on 2026-11-23, after R0-97 narrowed A13 and A14 and State 2
round-91 T2, T3 and T6 named the imported constants in A13 rule 7, A17 rule 3
and A18 rule 1. R0-97 changes neither decision in the first release: it
places counters of refused attempts and their display in the second release
(R0-100), whose own State 2 decides them and reopens this review then; A13's
lockout and A14 rule 2 — a refused action writes no entry — stand as they
are. Reviewed under authentication_credential_abuse (A13, A17), secrets (A14,
A17, A18), browser_boundary (A13) and concurrency (A13, A14, A17, A18): the
session values and every secret keep their 32 bytes, now through
`SECRET_MIN_BYTES`, and the backup's daily time and look interval keep 03:00
UTC and 60 seconds through `BACKUP_DAILY_TIME_UTC` and `BACKUP_LOOK_SECONDS`.
A18 rule 1 still asks a look at the clock at least once in each interval —
the constant is the longest gap, as "at least once a minute" was — so no
rule's behaviour moved. Reviewed under files_artifacts (A18): the backups
are made, encrypted, checked and kept as before; only how the daily time and
the look interval are named changed, and no file, path, size, key or
retention moved. No outcome changed.

Performed again on 2026-11-24, after that day's changes reopened it (rule 2):
every formal invariant of A01–A18, A21 and A22 was given an identifier and its
Required tests a binding to the check that shows it; the formulas of A01-2,
A05-1, A10-1 and A12-2 were restated as their normative rules already read —
a repeat refused only at stages (1) to (4) of A04 rule 6 or, for a room or a
pointer, on an archived project (A01 rule 3); a same-state transition being
one that passed every check (A05 rules 1 and 4); registration checked for the
token only and the set asked only for an operation on a project (A10 rule 1);
a session's end making no next version (A12 rule 2) — and Required tests
were added to A02, A03, A04, A05, A06, A09, A11, A12, A14 and A17. No
normative rule changed. Reviewed under authorization (A04, A09, A10, A11,
A12), concurrency (A01, A04, A12, A14, A17), injection_interpreted_input
(A02), authentication_credential_abuse (A09, A17) and secrets (A14, A17): the
new tests show refusals and guarantees the rules already gave — an answer
above the token's class refused whole, the owner's CSRF check answering
before a stale revision, a session's end removing every fact of it, a stale
owner end refused, every check made before the listeners stopping the start before any
listener is opened
— and no outcome changed.

Performed again on 2026-11-24, after A19's invariants were given the
identifiers A19-1 and A19-2 and its Required tests 5, 6 and 7 the bindings to
the checks that show them. No normative rule changed, and A13 did not
change. Reviewed under injection_interpreted_input, browser_boundary and
files_artifacts (A19): the new tests show the escaping and the value
places the rules already required; no outcome changed.

Performed again on 2026-11-24, after the witnesses of A01–A19 and A22 were
bound to Factory checks of their Required tests in place of the
[TEST_EVIDENCE] notes, and the owner restated A03 rule 3 (a correction
leaves the created instant; its revision and last-changed instant follow
A04). No outcome changed; A03 is named by no category.

Performed again on 2026-11-24, after A20 rule 5 recorded that its rules
are kept by the release process and its installation, outside Registry
(owner), and A20 declared no formal invariant of Registry's code; its
Required tests 1–4 now say what the release process shows. No rule of
what a release contains or how it is installed moved. Reviewed under
dependencies (A20): which dependencies run and how they are fixed and
verified are unchanged, and the place that verifies them is named. No
outcome changed.

Performed again on 2026-11-24, under the owner's direction of that day
(data-protection matrix, `sources/privacy_requirements_20261123.md`), after
the witness review and the independent judge of the witnesses reopened A01,
A02, A04, A07, A08, A09, A10, A13, A14, A16, A17, A18, A19 and A22 (rule 2);
A05 and A06, which no category names, changed with them.
Formal invariants holding several conditions were given one identifier
each — A01-5, A02-6 to A02-8, A13-3 to A13-6, A17-3, A17-4 and A18-3 —
and every formula was written whole with its identifier on its last line;
Required tests that claimed more than they show were narrowed (A01, A02,
A07, A13 test 9, A22 test 1); A16 rule 6 names the check at confirmation as
the building of the mapping the confirmation applies, made once in its
transaction, not a second check, and its tests 2 and 11 say what is seen;
A19 test 4 says which short declared length is too large and which
unreadable; A10 rule 3 fixes the whole equal answer, the failure's path
built from the request alone; A09 rule 4 names the test release on which
the class check is shown; and A09 rules 1 and 5 and A13 rules 1 and 7 have
Required tests for what the surfaces show, with A10 rule 6 and the
constant-time comparison and random source of A13 rule 7 carried to Factory
verification. Reviewed under authentication_credential_abuse (A09, A13,
A17), secrets (A13 rule 7, A14, A17), authorization (A04, A08, A09, A10),
injection_interpreted_input (A02, A16, A19), browser_boundary (A13),
files_artifacts (A07, A08, A16, A18, A19, A22) and concurrency (A01, A04,
A07, A14, A16, A17, A18): no right, limit, class, check or answer moved — A10
rule 3's path now names an input, never an id, which tells the agent less,
not more — and no outcome changed.

Performed again on 2026-11-25, after the State 2 round-120 reopened A02,
A09, A13, A16, A17 and A18 (rule 2). A13 rule 1 now holds the owner
session cookie to the owner interface's own host name, which the
deployment gives it apart from every other HTTPS service of the host
(decided under the owner's direction of 2026-11-24, matrix row P6); A18-2
holds when a backup becomes kept, later damage by the host's storage
outside Registry (matrix row D5); A16 rule 6 no longer claims that no
confirmation finds a conflict its step did not show, and keeps the refusal
of an unclean mapping in the confirming transaction; A02 rule 1 names the
white space set; A17-4 names the empty store a failed removal leaves; A18-1
compares with the cutoff as rule 4 does; A09 rule 4 and A13 test 10 name
their tables and cookie values as imported constants. Reviewed under
authentication_credential_abuse and browser_boundary (A13: the cookie
reaches fewer services, not more), secrets (A13, A17, A18),
injection_interpreted_input (A02, A16), files_artifacts (A16, A18) and concurrency
(A16, A17, A18): no right, limit, class or answer moved, and no outcome
changed.

Performed again on 2026-11-25, after the State 2 rounds 123 and 124 reopened
A09, A13, A14 and A22 (rule 2). A09 rule 1, A22 rule 2 and A14 rule 1 now
name the release tables they rest on as imported constants
(`SERVICE_RIGHTS`, `SERVICE_HIGHEST_CLASSES`, `ARTIFACT_TYPE_OWNERS`,
`OWNER_AUDIT_ACTIONS`), and A14 rule 1 requires the audit table to cover
every owner action M09 lists; A13 rule 6 states what the digest of a
confirmation's inputs guarantees — one unambiguous encoding of the action,
target, version and inputs under a collision-resistant cryptographic
digest, a collision of that digest outside the guarantee — and test 12
shows that changing any of them is refused. Reviewed
under authentication_credential_abuse and authorization (A09: the same
rights and classes, read from the release), browser_boundary and
concurrency (A13: a confirmation binds what its step showed, no more),
secrets and concurrency (A14: the same entries in the same transactions)
and files_artifacts (A22: the same one declared type): no right, limit,
class or answer moved, and no outcome changed.

### Consequence

Every category has an outcome resting on accepted decisions; the GDPR review
of the platform reads its technical guarantees here (R0-37, R0-88).
