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
   name and alias each will arrive under (R0-85); the Customers the import
   will make — one for each distinct v1 `customer_ref` a picked project names,
   which is all the file says of a customer (State 1 M04) — with the projects
   each will link (R0-80); and every malformed record and every id that
   conflicts with one production holds. For each Customer it will make, the
   owner gives its name and kind and says whether the v1 value is its tax id;
   confirmation is refused while any of these is missing (A02). Each new
   Customer's `customer_ref` is minted when the import is accepted.
2. The uploaded file is kept in the owner session that uploaded it, never in
   the store, until the import is accepted, another file is uploaded in that
   session, or the session ends (M11); then it is dropped. A refused
   confirmation keeps it, and the step may be shown again. The mapping names
   the file by its digest. The owner confirms that mapping in the confirmation
   step (A13 rule 6); the confirmation applies the file of that digest, the
   picks, names, aliases and Customer values the mapping showed, nothing
   else; a file no longer kept is refused and must be uploaded again.
3. Registry checks what the picks bring in — the picked projects with their
   rooms and pointers and the v1 values they name — and nothing else of the
   file: records only of projects the owner did not pick are neither checked,
   shown as conflicts nor imported, and take no part in the duplicate-id
   check. A file that cannot be read as the format States 5 and 6
   declare is refused whole.
4. A brought-in record is malformed when: a required value is missing (A02);
   it names a project or room the file does not hold; an id occurs
   twice among the file's records of one kind; a status is outside its
   vocabulary, or a pointer is `withdrawn` (v1 never withdrew one, M05); a
   pointer's type is not declared or its owner service is not the type's
   (A22); the versions of a project's pointers of one type are not 1..n, or
   more than one of them is `published`, or a `superseded` one is not lower
   than a later version; an instant cannot be read; an `active` project has an
   archived instant or an `archived` one has none; a `superseded` pointer has
   no superseded instant or a `published` one has one; a record was changed,
   archived or superseded before it was created, added or published.
5. Ids are unique per kind: a project id, a room id and a pointer id are
   compared only with ids of their own kind, in the file and in production.
6. At confirmation Registry checks again. Any conflict — a project, room or
   pointer id production holds — or any malformed record refuses the whole
   import, and nothing changes (R0-50, R0-79).
7. An accepted import stores every picked project with its rooms and pointers,
   the Customers it makes, the migration closure (M10) and its one audit entry
   (M09) in one transaction. The import has succeeded when that transaction
   is committed; Registry knows it by the closure.
8. While the closure exists, uploading and confirming an import are refused
   (R0-79).
9. A refused import may be retried with a corrected file; nothing of a refused
   attempt remains.

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
7. A picked project whose room names a project absent from the file refuses
   the import as malformed.
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

1. The configuration holds exactly these items and no other: the store's
   location; the backup location and the backup key (A18); the owner
   credential; one service token for each service of A09 — PresuPro, Client
   Portal, Cabinet, Cabinet Kernel (R0-20, R0-23).
2. Registry checks the configuration when it starts and serves nothing until
   every check passes; a failed check stops the start with a diagnostic that
   names the failed item and never its value (R0-37).
3. A secret — each token, the owner credential and the backup key — is at
   least 32 bytes long; a shorter one fails the start. That the owner's vault
   generates it at random is the owner's duty (R0-23), which Registry cannot
   check.
4. No two secrets are equal: two services with one token, or a token equal to
   the owner credential, fail the start.
5. A missing, malformed or unknown item fails the start; Registry applies no
   default to any item. The backup location must exist and let Registry create
   and remove a file in it; otherwise the start fails. The store must open for reading and writing and carry
   the store version of the running release; a store of another version, or
   one that does not open, fails the start — bringing a store to a new version
   is a step of the release, not of the start.
6. A presented secret is compared in constant time; no secret enters a record,
   a log line, an audit entry, a diagnostic or an answer (R0-23, R0-37).
7. A change of the configuration takes effect at the next start (R0-20).

### Formal invariants

```text
serving => checks_passed(config)
for secrets s1 != s2 in config: value(s1) != value(s2) and len >= 32 bytes
```

### Required tests

1. A configuration without Client Portal's token stops the start and names the
   missing item.
2. Two services with one token stop the start.
3. A 16-byte token stops the start.
4. The start diagnostic never contains a secret's value.

### Consequence

A wrong configuration is found at start, not by a caller; a leaked or weak
secret cannot be shared between holders.

## Accepted decision A18 — daily encrypted backups, checked when made, kept 30 days

### Normative rules

1. Registry backs up its store once a day at 03:00 UTC into the backup
   location, as a consistent copy taken while it runs: a backup never holds
   part of a transaction. A run that 03:00 found Registry stopped is made when
   it next starts, if no backup was made that UTC day; there is at most one
   run per UTC day, and runs never overlap. A backup records its instant, the release that made
   it and the last audit sequence number it holds.
2. A backup holds every record but the agent sessions (M06): a store restored
   from it has no session, Kernel registers its sessions again and the owner
   grants them again, so a restore never brings back a grant revoked after
   the backup.
3. Each backup is encrypted with the backup key the configuration holds at its
   making (A17). When the owner changes the key, older backups stay encrypted
   with the key they were made with; the owner keeps that key in the vault
   until the last of them is deleted (R0-23).
4. Right after writing a backup Registry checks it: it decrypts it into a
   temporary file in the backup location, opens it for reading only, checks
   that it is the store version of its release, that the store's own
   integrity check passes and that its audit log ends at the recorded
   sequence number, and removes the temporary file. A backup that fails the
   check is deleted and counts as failed. This is the tested restore: no
   other instance is made from a backup.
5. Every day at the same run — whether the new backup succeeded or not —
   Registry deletes every backup made more than 30 × 24 hours before.
6. A backup or a deletion that fails leaves no partial file, writes a
   diagnostic that names the failure and no value (A17), and is tried again at
   the next run; Registry keeps serving. Whether the runs succeed is the
   owner's to watch on the host (Explicit exclusions: the host's
   administration).
7. While the daily runs succeed, an erasure reaches the backups at most 30
   days after it, and a restore loses at most a day of changes; a failed run
   lengthens both by the days until a run succeeds.
8. The store, the backup location and the disks under them are encrypted and
   kept out of VM Agent's reach by the owner's administration of VM Platform
   (R0-48; Explicit exclusions); Registry does not check the host.
9. Restoring production replaces the store with a backup, by the owner on the
   host while Registry is stopped (Explicit exclusions). Every change after the
   backup's instant is lost, the audit entries with it: numbering continues
   from the backup's last number, and the lost entries exist nowhere. Before
   any service or agent uses the restored instance again the owner repeats,
   in the owner interface, every erasure, restriction and end of a
   relationship made after the backup, from the owner's own record of the
   retention review (R0-60); Registry, which no longer holds them, cannot list
   them.

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

### Consequence

A tested restore exists every day without a second instance holding
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
3. Every value reaches the store as a bound parameter, never as part of a
   statement.
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
   claims nothing beyond it. That document states the questions each category
   asks; each outcome below answers them by naming the decisions that do, or,
   for NOT_APPLICABLE, why the category's subject is absent.
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
- concurrency: APPLICABLE; references: A01, A04, A07, A12, A14; affected: M01, M04, M05, M06, M09, concurrent creates, corrections, publishes and session changes
- dependencies: APPLICABLE; references: A20; affected: Registry release, its Python dependencies

### Consequence

Every category has an outcome resting on accepted decisions; the GDPR review
of the platform reads its technical guarantees here (R0-37, R0-88).
