# State 2 — Registry audit rules: what is recorded, how the log is kept

Draft of 2026-10-31. The owner accepted the proposals behind these decisions on
2026-10-31 (answers 11 and 12 of the State 2 plan). They settle what the rounds
of States 0 and 1 carried here — whether refused, no-op and read actions leave
an entry (round 28 P1) — and how the audit log is protected (R0-37).

## Accepted decision A14 — only an accepted change writes an entry

### Normative rules

1. An entry is written by an accepted action that changes state and that M09
   lists, in the same transaction as the change: if the change is not stored,
   neither is the entry, and the reverse.
2. A refused action writes no entry — a stale revision, a failed check of
   rights, an unknown id, a refused sign-in included. Security events of the
   infrastructure are the infrastructure's (R0-58).
3. An accepted action that changes nothing (A03 rule 4, A05) writes no entry.
4. Reads write no entry, whoever reads — the owner, a service, Kernel for the
   agent (R0-58).
5. A confirmation id is minted only for an accepted, confirmed action that
   changes state, and is written into its entry (and, for the import, into the
   migration closure); a confirmed action that changes nothing mints none.
6. Every entry records the outcome `accepted`; State 6 declares no other
   outcome.

### Formal invariants

```text
entry e exists <=> accepted action a with changed(a) and a in M09.actions
                   and e written in the transaction of a
e.outcome = accepted
```

### Required tests

1. A correction refused as stale leaves the log unchanged.
2. Archiving an archived project leaves the log unchanged and mints no
   confirmation id.
3. A failure while storing a correction leaves neither the change nor its
   entry.
4. Kernel reading the agent projection leaves the log unchanged.

### Consequence

The log is a record of what changed, never of attempts (R0-58); it needs no
outcome but `accepted`.

## Accepted decision A15 — the log is append-only and the owner erases it by date

### Normative rules

1. No action changes an entry. Entries are added by A14 and removed only by
   'erase audit entries before a date' (R0-66); Registry has no other path that
   removes one.
2. Only the owner reads the log, in an owner session (A13); no service token
   has a right to it (A09).
3. The date of an erasure is a date not later than today, the current date in
   UTC; a later date is refused. Every entry whose instant is before 00:00 UTC
   of that date is removed.
4. The erasure's own entry is written after the removal, in the same
   transaction, with the current instant; it is therefore never removed by the
   erasure that wrote it.
5. Sequence numbers are never reused within a store's history (M09): changes
   that write an entry are applied one at a time, and each entry takes the
   number after the last that history ever wrote, kept in the store apart
   from the entries, so an erasure does not lower it. A store restored after a
   loss begins its own history from the backup's last number (R0-89).
6. An erasure that removes no entry changes nothing: it is accepted, writes no
   entry and mints no confirmation id (A14).

### Formal invariants

```text
for entries e1 written before e2: e1.sequence < e2.sequence
erase(d) accepted => no entry with instant < start_of(d) remains
erase(d) accepted and removed at least one entry
                  => its erasure entry e has e.instant >= start_of(d)
```

### Required tests

1. In a log whose entries are all older than today, erasing before today
   leaves exactly the new erasure entry.
2. Erasing before a date older than every entry removes nothing, writes no
   entry and mints no confirmation id.
3. A date later than today is refused.
4. After an erasure, the next entry's sequence number is one more than the
   erasure entry's.
5. No operation of any service token reads the log.

### Consequence

The log cannot be rewritten through Registry; its period is the owner's,
applied by date (R0-60, R0-66).
