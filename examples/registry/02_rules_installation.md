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
   reads it as data (A19) and answers the mapping without changing anything:
   each project the file holds, with its id, status, rooms and pointers; for
   each project the owner picks, the display name and alias it will arrive
   under (R0-85); each Customer the import will make and the projects it will
   link (R0-80); every id that conflicts with one production holds.
2. The mapping names the file by its digest. The owner confirms that mapping
   in the confirmation step (A13 rule 6); the confirmation applies the file of
   that digest and the picks the mapping showed, nothing else.
3. At confirmation Registry checks every conflict again. Any conflict — a
   project, room or pointer id production holds, a Registry-minted
   `customer_ref` production holds, a malformed record — refuses the whole
   import, and nothing changes (R0-50, R0-79).
4. An accepted import stores every picked project with its rooms and pointers,
   the Customers it makes, the migration closure (M10) and its one audit entry
   (M09) in one transaction. The import has succeeded when that transaction
   is committed; Registry knows it by the closure.
5. While the closure exists, uploading and confirming an import are refused
   (R0-79).
6. A refused import may be retried with a corrected file; nothing of a refused
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
3. Confirming a mapping after another file was uploaded applies only the file
   whose digest the confirmation named.
4. A second import after a successful one is refused.
5. A failure during the transaction leaves no project, no Customer and no
   closure.

### Consequence

The owner sees exactly what will arrive before anything does (R0-34), and the
closure is the one proof of success.

## Accepted decision A17 — configuration and secrets are checked before Registry serves

### Normative rules

1. The configuration names the store, the owner credential and one service
   token for each service of A09 (R0-20, R0-23).
2. Registry checks the configuration when it starts and serves nothing until
   every check passes; a failed check stops the start with a diagnostic that
   names the failed item and never its value (R0-37).
3. A secret — each token and the owner credential — is at least 32 bytes
   generated at random by the owner's vault (R0-23); a shorter one fails the
   start.
4. No two secrets are equal: two services with one token, or a token equal to
   the owner credential, fail the start.
5. A missing, malformed or unknown item fails the start; Registry applies no
   default to a secret or to the store.
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

## Accepted decision A18 — daily encrypted backups, kept 30 days, restore tested at each release

### Normative rules

1. Once a day the store is backed up as a consistent copy taken while
   Registry runs; a backup never holds part of a transaction.
2. Each backup is encrypted with a key the owner holds in the vault (R0-23),
   and is kept 30 days; older backups are deleted. An erasure in Registry
   reaches the backups when the last backup holding the erased values is
   deleted, at most 30 days after it.
3. The store and the backups live on encrypted disks of VM Platform and of
   the place the backups are kept; neither is readable from VM Agent (R0-48).
4. Before each release the owner restores the latest backup into a temporary
   instance on VM Platform, checks that it starts (A17) and answers, and
   removes it; a test instance never receives a production backup (R0-34).
5. After restoring production from a backup, the owner repeats every erasure
   made after the backup's instant, as the owner's retention review recorded
   it (R0-60), before the instance serves again.

### Formal invariants

```text
age(oldest backup) <= 30 days
every backup is encrypted and consistent
erasure at t => no backup holding the erased values exists after t + 30 days
```

### Required tests

1. A backup taken during a write restores either before or after it, never in
   between.
2. A backup older than 30 days does not exist.
3. A backup cannot be read without the owner's key.

### Consequence

Data survives the loss of the store; an erasure has a bounded reach into the
backups, as the governance can state.

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
   its digest; a running instance uses exactly those.
2. A dependency changes only by a new release, verified as any release.
3. Registry has no dependency that loads code at run time from outside its
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

1. Every security category has exactly one outcome below, resting on the
   decisions it names.
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
