# Investigation packet — what an audit erasure leaves in the log

A compact packet for continuing work on one State 2 behaviour of Registry
without rereading the case. Every `[q:<key>]` is a verbatim passage pinned in
`model/sources.py` to a commit and file; `check_quotes.py` verifies all of them
mechanically. Addresses are `file:line` at the current text `cf675e5c`
(`origin/agent/registry`, 2026-10-31) unless another commit is named.

Text versions used below (full list and the rounds that read each one:
`results/rounds.md`):

| name | commit | what changed for this question | rounds that read it |
|---|---|---|---|
| V0 | `fd254d08` | State 2 draft: an empty erasure writes nothing | 1 |
| V1 | `cb9f12d3` | today in UTC; last number kept "durably" | 2–4 |
| V2 | `12e2d9ea` | A15 invariant weakened to agree with rule 6 | 5 |
| V4 | `67589757` | numbering per store history (R0-89) | 10–11 |
| V5 | `699d18f3` | rule 6 reversed; A14 rule 3 excepts the erasure | 12 |
| V6 | `b31d9eac` | A14 rule 5 excepts the erasure too — current | 13–34 |

## 1. The behaviour question

> When the owner, confirming, erases the audit entries before a date and no
> entry is older than that date, does the erasure leave an entry of its own,
> and does that entry carry a confirmation id?

And three questions that depend on it: does a no-op repeat of another
confirmed action write an entry or mint an id; is a second erasure with the
same date a "repeat"; are sequence numbers and confirmation ids fresh for it.

## 2. Accepted bases (State 0, State 1)

State 0 (`00_product.md`), owner-accepted:

- R0-66, the promise (2026-10-27, after State 0 round 18 T10), unchanged in
  every version since `fd254d08`: `00_product.md:934`
  [q:R0-66.text] — "that erasure leaves an entry of its own naming the date".
  The Primary actions row says the same with no condition on what was removed:
  `00_product.md:173` [q:R0-66.row].
- R0-37, the audit record: "a confirmation id where the owner confirmed"
  `00_product.md:588` [q:R0-37.audit].
- R0-58, what is recorded: significant changes of state, "erasures and
  anonymisations" `00_product.md:851` [q:R0-58.scope]; reads are not recorded
  `00_product.md:853` [q:R0-58.reads].
- R0-60 lists "a log entry for every erasure, without the erased values"
  `00_product.md:887` [q:R0-60.every_erasure]. **Not used as a basis**: the
  bullet sits in R0-60's list of retention tools for customer and project data
  (contact data, archived projects); it does not speak of the audit erasure,
  which R0-66 introduced later and which narrows R0-60.
- R0-89 (2026-10-31, after State 2 rounds 5–9) scopes the numbering to a
  store's history `00_product.md:1180` [q:R0-89.history]. It is a **new owner
  promise made during State 2**, see §6.

State 1 (`01_models.md`), M09 AuditEntry and Identity formats:

- M09 lists "the erasure of old entries itself (R0-66)" among the changes it
  records `01_models.md:655` [q:M09.erasure_writes]; its subject is "none …
  whose fact is the owner's date" `01_models.md:692` [q:M09.subject_none];
  it carries "the confirmation id where the owner confirmed"
  `01_models.md:698` [q:M09.conf].
- Numbering: "never reused within that history" `01_models.md:665`
  [q:M09.seq.history] (before `cce33f0b`: "never reused", unscoped
  [q:M09.seq.global]).
- Identity formats: Registry mints a confirmation id when the owner confirms
  an action that asks for confirmation — erasing old audit entries among them
  — "and writes it once into the audit entry of that action (M09)"
  `01_models.md:67` [q:ID.conf_minted]. State 1 round 01 T7 judged *whether a
  confirmed no-op mints an id* carried to State 2 (`later_state`)
  [q:SO1.r1T7]; so this sentence is not read as deciding the no-op case.

## 3. Related State 2 rules and what they constrain

| rule (current) | address | constraint on this question |
|---|---|---|
| A14 r1 | `02_rules_audit.md:12` [q:A14.r1] | an accepted change M09 lists writes its entry in the same transaction |
| A14 r2 | `:15` [q:A14.r2] | a refused action writes nothing — a refused confirmation, a later date (A15 r3) |
| A14 r3 | `:18` [q:A14.r3.new] | a no-change action writes nothing, **but for the erasure** |
| A14 r5 | `:22–26` [q:A14.r5.old] [q:A14.r5.new] | an id only for a confirmed change, **but for the erasure, which always writes its entry with its id** |
| A14 invariant | `:33` [q:A14.inv.new] | entry ⇔ accepted change or erasure (read at the transaction, §6) |
| A15 r1 | `:57` [q:A15.r1] | only the dated erasure removes entries |
| A15 r3 | `:62` [q:A15.r3] | date ≤ today (UTC); entries before 00:00 UTC of it are removed |
| A15 r4 | `:65` [q:A15.r4] | the erasure's own entry is written after the removal: never removed by itself |
| A15 r5 | `:68` [q:A15.r5.history] | the entry takes the next number of the store's history; an erasure does not lower it |
| A15 r6 | `:73` [q:A15.r6.new] | an empty erasure writes its entry naming the date, with its id |
| A15 invariants | `:81–83` [q:A15.inv.seq] [q:A15.inv.removed] [q:A15.inv.entry.v5] | ordered numbers; nothing older remains; the erasure's entry exists |
| A05 r1, r2 | `02_rules_records.md:254–262` [q:A05.r1.head] [q:A05.r1.tail] [q:A05.r2] | a *listed* transition to the state already held writes nothing, mints nothing — the erasure is **not** in the list |
| A03 r4, A01 r4 | `02_rules_records.md:152`, `:39` [q:A03.r4] [q:A01.r4] | an equal correction / a create's repeat changes nothing and writes nothing |
| A04 r6 | `02_rules_records.md:202–217` [q:A04.r6.first] [q:A04.r6.stage1] [q:A04.r6.order] | a refused confirmation answers at stage 1, a later date at stage 4, before anything is written |
| A13 r6 | `02_rules_access.md:254–261` [q:A13.r6.used] [q:A13.r6.not_id] | the one-time confirmation *value* is used up by any submission; it is not the confirmation *id* |
| A06 r6 | `02_rules_records.md` [q:A06.r6] | the log reads in sequence order, whatever the instants |

Outside the cluster, found by the search in §7: A18 keeps "the last sequence
number" of a store in each backup (`02_rules_installation.md:255, 281, 327`,
[q:A18.last_seq]); A16's import is the other confirmed action whose id also
goes into the migration closure [q:A16.import_conf].

## 4. The boundary of the choice

- **Already accepted (not reopened here):** an erasure leaves its own entry
  naming the date (R0-66); confirmed actions' entries carry the id (R0-37,
  M09); reads write nothing (R0-58); numbers are fresh within a store's
  history (M09, R0-89); refusals write nothing (A14 r2).
- **Decided in State 2, and consistent in V6:** the empty erasure is the one
  accepted action that writes an entry without changing other state (A14 r3,
  A15 r6); it mints its id (A14 r5); it is not an A05 repeat (A05 r1 is a
  closed list); a no-op repeat of a listed transition writes nothing and mints
  nothing (A05 r2).
- **Would need the owner:** anything that makes the empty erasure leave no
  trace (contradicts R0-66); a number that never repeats across a restore
  (R0-89 scoped it to a history; §6); recording refused or no-op attempts
  (R0-58).

## 5. Admissible histories and expected outcomes

Witnesses in `witnesses/witnesses.json`, run by `run.py` on every version.

| witness | history (owner unless said) | expected (V6) | status |
|---|---|---|---|
| W01 | create A; erase before a date older than every entry | entries: create #1, erasure #2 with id | accepted (A15 test 2) |
| W02 | create A; next day; erase before today | only the erasure's entry | accepted (A15 test 1) |
| W03 | create A; erase before tomorrow | refused at stage 4, log unchanged | accepted (A15 test 3) |
| W04 | create A; next day; erase before today; correct | numbers 2, 3 | accepted (A15 test 4) |
| W05 | create A; archive (confirmed); archive again | one archive entry with id; card revision 2 | accepted (A14 test 2) |
| W12 | create A; archive with a refused confirmation; archive | refused at stage 1; one archive entry with id | inferred |
| W13 | create A; next day; erase before today; the same erasure again | two erasure entries, #2 and #3, two distinct ids | inferred |
| W14 | archive; two empty erasures | three distinct ids | assumption (§6) |

Observer in every case: the owner reading the log in the periodic review —
whether the review left its trace, and which confirmation it answers to.

## 6. Unknowns, assumptions, rejected readings

Readings the texts leave open, each run both ways by `run.py`:

- **Does an erasure's own entry count as "changing state" (A14 r1, r5)?**
  Before V6 the result depends on it: on V5, A14 r5 contradicts A15 r6 only if
  it does not (round 12 T7 judged a contradiction, T8 judged the entry side
  answered — both right, on different readings). V6 is consistent either way.
  Default: it does not (otherwise A14 r1 is circular).
- **A14's invariant over time.** Read over the log as it stands, "entry e
  exists <=> accepted action" fails after every erasure that removes an entry;
  read at the action's transaction (A14 r1: "in the same transaction") it
  holds. Default: at the transaction. Raised twice by single reviews (State 2
  rounds 2 and 13), never judged. No behaviour differs; a test generated from
  the formula literally would fail on a correct implementation.
- **"the erasure entry e" in V0's invariant** presupposes an entry. Default:
  it does (as round 4's judge read it).
- **Is an empty erasure an A05 repeat?** Rejected: A05 r1 is a closed list
  without it, A14 r3 names the erasure as the exception, and the reading
  contradicts R0-66 in every version.
- **Identity formats read as complete** (every confirmed action mints an id,
  a no-op included). Rejected: contradicts A05 r2 / A14 test 2 in every
  version, and State 1 round 01 T7 carried that case to State 2.

Assumptions (not stated by any passage):

- Confirmation ids never repeat. Identity formats says opaque, a UUID,
  minted per confirmation; nothing says unique. Taken as the intent (W14).
- The model's day granularity: instants inside one UTC day are not ordered
  against the cut-off; A15 r3 cuts at 00:00 UTC, so nothing in this question
  depends on finer instants.

Out of scope here, and why: what an erasure does to backups (A18: the owner
repeats the latest erasure after a restore, R0-89 makes it the owner's); clock
regressions (A06 r6 orders the log by number, not instant).

## 7. How the dependencies were searched

1. References out of the cluster: every `A\d\d`, `R0-\d+`, `M\d\d` in A04,
   A05, A14, A15 at `cf675e5c` (A01–A03, A08–A10, A12, A13, A22; M01, M04,
   M09; R0-12, R0-29, R0-35, R0-46, R0-53, R0-58, R0-60, R0-66, R0-70, R0-71,
   R0-84, R0-89). Each was opened; only those in §3 bear on the question.
2. References into the cluster: every mention of A14, A15, R0-66 in the other
   files — found A13 r6 (confirmation id), A18 (last number in backups, the
   repeated erasure after a restore), A21 (security review lists).
3. Vocabulary: "confirmation id", "sequence", "erase", "audit" across
   `00_product.md`, `01_models.md`, `02_rules_*.md` — found R0-60's "every
   erasure" (rejected as a basis, §2) and Identity formats (§2).
4. History: `git log -S` and per-commit diffs of `02_rules_audit.md`, and the
   round digests (`provenance.py`) — found the weakened invariant of V2 and the
   two-step fix V5→V6.
5. Rounds: every State 1 and State 2 topic about audit, confirmation ids and
   numbering (`results/rounds.md`) — found State 1 round 01 T7 (§2) and the
   restore numbering topics (State 1 rounds 18–29, State 2 rounds 2–9), which
   led to R0-89.

Missed by the first cluster cut and found this way: A13 r6 (value vs id),
Identity formats (State 1 sentence on minting), A18's use of the last number,
R0-89 as a new promise.
