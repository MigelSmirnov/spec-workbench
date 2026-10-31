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
   confirmation is refused while any of these is missing (A02). Each new
   Customer's `customer_ref` is minted when the import is accepted.
2. The uploaded file is kept in the owner session that uploaded it, in the
   process's memory only — never in the store, never on a disk — until the import is accepted, another file is uploaded in that
   session, or the session ends (M11); then it is dropped. A refused
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
6. At confirmation Registry checks again. Any conflict — a project, room or
   pointer id production holds — or any malformed record of the picks refuses the whole
   import, and nothing changes (R0-50, R0-79).
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
   reaches the backups with the next daily run (A18). A store lost before a
   kept backup holds the import loses it, and the import may then be made
   again (R0-89).

### Formal invariants

```text
import(file f, picks P) accepted =>
  stored(P with rooms, pointers) and stored(new customers of P)
  and closure.file_digest = digest(f) and one AuditEntry, in one transaction
exists closure => import refused
conflict at confirmation => store unchanged
```

### Required tests

1. Uploading answers the mapping and changes nothing; reading the store after
   it shows no imported record.
2. A file whose one pointer id production holds refuses the whole import.
3. Confirming a mapping after another file was uploaded in the session is
   refused: the file it named is no longer kept.
4. A second import after a successful one is refused.
5. A failure during the transaction leaves no project, no Customer and no
   closure.
6. A conflicting id belonging only to a project the owner did not pick does
   not refuse the import.
7. A room naming a project absent from the file belongs to no pick: it is
   not imported and does not refuse the import.
8. Confirming without a kind for a Customer the import makes is refused.
9. A picked project holding a `withdrawn` pointer refuses the import as
   malformed.
10. Confirming after the owner session that uploaded the file has ended is
    refused.

### Consequence

The owner sees exactly what will arrive before anything does (R0-34), and the
closure is the one proof of success.

## Accepted decision A17 — configuration and secrets are checked before Registry serves

### Normative rules

1. The configuration is the set of environment variables whose names begin
   with `REGISTRY_`, set as R0-23 says; no other variable is read or
   checked. It holds exactly these items and no other: the store's
   location; the backup location and the backup key (A18); the owner
   credential; one service token for each service of A09 — PresuPro, Client
   Portal, Cabinet, Cabinet Kernel (R0-20, R0-23) — or, for an owner-only
   start, none of the four: Registry then serves the owner interface alone
   and refuses every service call (A18 rule 9).
2. Registry checks the configuration when it starts and serves nothing until
   every check passes; a failed check stops the start with a diagnostic that
   names the failed item and never its value (R0-37). The checks run in one
   order and the first that fails stops the start: no unknown item, taken in
   the order of their names by Unicode code point; every item of rule 1 present; each well formed; each secret's length (rule 3);
   their distinctness (rule 4); the store and backup location apart (rule
   5); the backup location writable, by a probe file under the temporary
   prefix (A18 rule 5); the store opening, or made new (rule 5). Within one
   check, items go in the order rule 1 lists them. A failed start leaves no
   file it made but a probe it could not remove, which the next start or run
   removes with the other temporary files.
3. A secret — each token, the owner credential and the backup key — is at
   least 32 bytes long; a shorter one fails the start. Registry checks the
   length and, by rule 4, the distinctness, and nothing else of how the owner
   made it (R0-23).
4. No two secrets are equal: two services with one token, or a token equal to
   the owner credential, fail the start.
5. A missing, malformed or unknown item fails the start; Registry applies no
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
   empty store of the running release's version there at the start, under a
   temporary name — the store's name with a suffix the release declares —
   that it renames to the store's name only once the store is complete; at
   every start it first removes a file of that temporary name, left by an
   interrupted start, and no other file there; otherwise
   the store must open for reading and writing, pass the store's own
   integrity check, and carry the store
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
serving => checks_passed(config)
for secrets s1 != s2 in config: value(s1) != value(s2) and len >= 32 bytes
```

### Required tests

1. A configuration with some service tokens but without Client Portal's
   stops the start and names the missing item; one with none of the four is
   an owner-only start.
2. Two services with one token stop the start.
3. A 16-byte token stops the start.
4. The start diagnostic never contains a secret's value.

### Consequence

A wrong configuration is found at start, not by a caller; a leaked or weak
secret cannot be shared between holders.

## Accepted decision A18 — daily encrypted backups, checked when made, kept 30 days

### Normative rules

1. These runs are R0-89's daily backups: one is due each day, and the days
   this rule and rule 5 leave without a kept backup are allowed. Every day at
   03:00 UTC, while Registry runs with its service tokens, it
   makes one backup run; a 03:00 that finds Registry stopped, or in an
   owner-only start (rule 9), makes no run, and none is made later in its
   place. The process looks at the clock at least once a minute; a date's
   run starts at its first look at or after 03:00 of that date when an
   earlier look of the same process saw that date before 03:00, and no kept
   backup of that date exists — a kept backup's date being the UTC date of
   its recorded instant, and a file whose record cannot be read counting as
   none (rule 4), so
   a restart, a start at 03:00 or a clock set back makes no second run. A
   process runs each date at most once, remembering in its memory the dates
   it ran, a failed run included; after a clock set forward it runs only for
   the date it then sees pass 03:00, and the dates jumped over get no run. A
   failed date is run again only by a later process that sees 03:00 of it
   pass, which only a clock set back makes happen, and that is allowed. Runs
   never overlap: a 03:00 that finds a run still going makes no run of its
   own. A backup is a consistent copy of the store taken while Registry runs:
   one snapshot of the store, as one read transaction sees it, while other
   transactions go on; it never holds part of a transaction, and its
   recorded instant and last sequence number are those of that snapshot. It
   records, readable without its key, its instant, the release that made it,
   the last audit sequence number it holds and a digest of the key it was
   made with (never the key); its age is counted from that instant. The
   owner interface shows the instant of the newest kept backup whose record
   can be read, or that there is none.
2. A backup holds every record but the agent sessions (M06): a store restored
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
   is the store version of its release, that the store's own integrity check
   passes and that its audit log ends at the recorded sequence number, and
   removes it; a backup that passes is renamed to its kept name, one that
   fails is deleted. When the decrypted file cannot be removed, or a failed
   backup cannot be deleted, the backup stays under its temporary name and
   is not kept, the run fails, the third step still runs, and the next run
   removes what is left. This is the tested restore: no other instance is made
   from a backup. Third, whatever the second step did, it deletes every kept
   backup made more than 30 × 24 hours before the instant this step starts,
   one cutoff for the whole step, and every file under the kept
   prefix whose unencrypted record (rule 1) cannot be read. It takes the
   files in the order of their names; a file it cannot read or delete is
   reported, and it goes on with the next. A run succeeds only when every
   step did; one whose backup was kept but a deletion failed is failed, and
   its new backup stays kept.
5. Kept and temporary names begin with two different prefixes the release
   declares, neither beginning with the other; a kept file's record is valid
   when its instant, release, last sequence number and key digest can all be
   read, and only a valid one counts as a kept backup; Registry removes, renames and deletes in the backup location
   only files under them, and the location is Registry's alone (A17): a file
   is under a prefix when it is a regular file directly in the location whose
   name begins with it; Registry follows no link and enters no directory
   there. A kept
   name is made from the backup's instant and is never overwritten: a backup
   whose kept name exists, or whose rename fails, is deleted and the run
   fails. A step that fails leaves no partial kept backup —
   at most a file under the temporary prefix, which the next run removes —
   and writes a diagnostic that names the failure and no value (A17);
   Registry keeps serving, and the next 03:00 tries again. Whether runs
   succeed is the owner's to watch on the host (Explicit exclusions: the
   host's administration).
6. While the daily runs succeed, an erasure reaches the backups by the first
   run after the last backup holding the erased values is 30 days old — at
   most 31 days after the erasure — and a failed or missed run lengthens that
   by the days until a run succeeds. A restore loses the changes made after
   the backup it uses; Registry bounds neither how long a run takes nor how
   old the newest kept backup may be.
7. The store, the backup location and the disks under them are encrypted and
   kept out of VM Agent's reach by the owner's administration of VM Platform
   (R0-48; Explicit exclusions); Registry does not check the host.
8. Registry has no restore operation (R0-89). A store the owner puts in
   place of a lost one starts as any store (A17 rule 5) — by the release that
   made its backup, or by a later one after that release's own store
   migration — and begins its own history from the backup: numbering
   continues from its last number (A15), and a store without the migration
   closure accepts the import (A16).
9. An owner-only start (A17 rule 1) serves the owner interface alone and
   makes no backup run.

### Formal invariants

```text
after a run whose deletions succeeded: no backup older than 30 days and no
  backup that failed its check exists
every kept backup is encrypted, consistent, checked, and records
  (instant, release, last sequence); no backup holds an agent session
```

### Required tests

1. A backup taken during a write restores either before or after it, never in
   between.
2. After a run in which the backup failed, backups older than 30 days are
   still deleted.
3. A backup cannot be read without the key it was made with.
4. A backup whose integrity check fails is deleted and reported.
5. A store restored from a backup holds no agent session.
6. A 03:00 missed while Registry was stopped makes no backup at the next
   start; the next one is made at the following 03:00.

### Consequence

A tested restore exists after every run that keeps a backup, without a second instance holding
production data (R0-34); a restore cannot revive a revoked grant.

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
4. The import file is read as data with a size limit State 6 sets; nothing in
   it is executed or evaluated, and a file over the limit is refused.

### Formal invariants

```text
render(v) = escape(v) for every stored value v
no stored value is ever evaluated or executed
```

### Required tests

1. A room named `<script>alert(1)</script>` is shown as that text in the owner
   interface.
2. An access request text with markup is shown as text.
3. A display name with a quote and a semicolon is stored and read back
   unchanged.

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

### Formal invariants

```text
running dependencies = release.dependencies (name, version, digest)
```

### Required tests

1. Installing the release with a dependency whose digest differs fails.

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
for each category c: outcome(c) in {APPLICABLE, NOT_APPLICABLE}
APPLICABLE c => references(c) are decisions of States 0-2
```

### Required tests

1. Each APPLICABLE category's decisions have their own required tests, and
   those tests pass.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A09, A13, A17; affected: M11, owner credential, service tokens, sign-in, owner session cookie
- secrets: APPLICABLE; references: A14, A17, A18; affected: owner credential, service tokens, backup key, diagnostics, audit log
- authorization: APPLICABLE; references: A08, A09, A10, A11, A12; affected: M05, M06, every service operation, every agent-authority operation, owner session actions
- injection_interpreted_input: APPLICABLE; references: A02, A16, A19; affected: M03, M08, import file, every stored text value
- external_callbacks_webhooks: NOT_APPLICABLE; rationale: Registry calls no other service and receives no callback (R0-18, R0-54), and every request is a caller's authenticated call (R0-27)
- browser_boundary: APPLICABLE; references: A13, A19; affected: owner interface, CSRF protection, session cookie, rendering of agent-written text
- files_artifacts: APPLICABLE; references: A07, A08, A16, A18, A22; affected: M05, M10, import file, backups, pointers as references whose payload Registry never reads (R0-02)
- concurrency: APPLICABLE; references: A01, A04, A07, A12, A13, A14, A16; affected: M01, M04, M05, M06, M09, M10, M11, concurrent creates, corrections, publishes, session changes, single-use confirmation values, concurrent import confirmations
- dependencies: APPLICABLE; references: A20; affected: Registry release, its Python dependencies

### Consequence

Every category has an outcome resting on accepted decisions; the GDPR review
of the platform reads its technical guarantees here (R0-37, R0-88).
