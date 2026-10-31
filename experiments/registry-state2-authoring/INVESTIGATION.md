# Investigation — a revision stated for a record that has none

Question and starting point: `START.md` (fixed at `b230aa30`, before this
file). Every `[q:<key>]` is a verbatim passage pinned in `model/sources.py` and
verified by `check_quotes.py`. Addresses are `file:line` at `cf675e5c` unless
another commit is named.

Each statement is marked **[F]** fact (a passage or a git record), **[D]**
derivation (follows from facts; the steps are given), **[A]** assumption, or
**[P]** proposal.

## 1. Which State 0 promises and State 1 facts ask for an answer

- [F] State 0, Primary actions, 'erase a customer's contact data'
  (`00_product.md:152`): "unknown customer refused; erasing an erased
  customer returns it unchanged" [q:S0.erase_row].
- [F] The row dates from `7fb4e3af` (2026-10-26, "close State 0 round 2"),
  [q:S0.erase_row.origin]. The commit message says "a repeated erasure is a
  no-op". Revisions came a day later: R0-35 is dated 2026-10-27
  [q:R0-35.date]. **The row was written before revisions existed.**
- [F] R0-35 (`00_product.md:557`): "a change against an older revision is
  refused and nothing changes" [q:R0-35].
- [D] R0-35 does not decide the question, for two reasons:
  1. R0-35 speaks of a *change*, and a repeat of an erasure changes nothing.
  2. A retry carries the revision the erasure was made against. That revision
     is not *older*: the erasure gives no next revision [q:A04.r1].
- [F] R0-06 / M04: an erased Customer keeps its `customer_ref`, the erased
  mark and its instant, "nothing else" [q:R0-06.nothing_else]. Its revision is
  gone with the rest [q:M04.erased]. The owner reads it as exactly that
  [q:M04.read_erased].
- [D] So Registry cannot tell a retry (revision = the one erased from) from an
  older tab (revision < it): the fact that would tell them apart is not kept.
  Any rule must answer both alike (W01, W02). An "R0-35 exact" rule (refuse
  only older) is impossible without a new State 0/1 fact.
- [F] The other customer rows: an erased customer "cannot be corrected"
  (`:149`) [q:S0.correct_row]; restricting, lifting, ending, resuming an erased
  one are refused (`:153`, `:169`) [q:S0.restrict_row] [q:S0.end_row]
  [q:M04.erased_refused].
- [F] Projects: anonymising an anonymised project "returns it unchanged",
  deleting it whole is refused (`:170`, R0-71) [q:S0.erase_project_row]
  [q:R0-71]. An anonymised project keeps no revision [q:M01.anon_revision].
- [F] State 1 leaves "which actions must state the revision" to State 2
  [q:RT.state2].

## 2. Which State 2 rules constrain the answer

- [F] A04 r1 (`02_rules_records.md:184`): erasing states the revision it was
  made against "and leaves no revision behind" [q:A04.r1] [q:A04.r1.list].
- [F] A04 r2 (`:191`): "A stated revision that is not the record's current one
  is refused as stale" [q:A04.r2].
- [F] A04 r3 (`:193`): a would-be no-op still states the revision and is
  refused when stale. "An anonymised project and an erased Customer have no
  revision (M01, M04): an action on them states none." [q:A04.r3]
- [F] A04 r6: each check belongs to the stage of its kind; (4) values, (5) the
  stated revision, (6) lifecycle [q:A04.r6.kind] [q:A04.r6.stages]. A
  transition passing all six may be a repeat (A05) [q:A04.r6.repeat].
- [F] A04 invariant: "for action a on record r … that may move r.revision:
  a.stated_revision != r.revision => refused" [q:A04.inv].
- [F] A04 test 3 (archiving again with the new revision answers unchanged)
  and test 4 (stale before archived) [q:A04.t3] [q:A04.t4]. The Consequence
  says the owner interface "always shows and sends the revision of the card
  it rendered" [q:A04.consequence].
- [F] A05 r1: a transition to the state already held, "that passes every
  check of A04 rule 6", is accepted and changes nothing; the list includes
  "erasing an erased Customer" [q:A05.r1] [q:A05.r1.erased]. Its Consequence
  says "a retried transition is safe" [q:A05.consequence].
- [F] A14: neither a refusal nor a no-op writes an audit entry [q:A14.r2]
  [q:A14.r3]. [D] The log is the same under every answer considered here.

What these leave open [D]. Nothing says what happens when a request states a
revision and the record has none. The text can be read four ways:

1. **A04 r2** reaches it: "not the record's current one" is true when there is
   no current one, so the request is stale.
2. **A04 r3's** "states none" is an input rule: a stated revision is an invalid
   value, at stage 4.
3. A04 r3's "states none" is a caller's duty that Registry does not check:
   with r2 limited to records that have a revision, the request passes and is
   an A05 repeat.
4. The invariant's "that may move r.revision" means *this* action on *this*
   record. A repeat on an erased record moves nothing, so the invariant does
   not reach it.

## 3. Histories that tell the readings apart

All in `witnesses/witnesses.json`. The `preserve` flags were fixed before any
patch was checked (`8b2562e8`).

- [F] Admissibility. The texts expect resubmitted owner forms: A01's
  Consequence [q:A01.consequence]. Several owner sessions may be open at once
  [q:A13.r2.sessions].
- [F] Admissibility. Customer erasure asks for no confirmation
  [q:ID.confirmed]. A resubmission therefore reaches the revision check.
- [D] Project erasure is confirmed. A resubmission in the same session is
  refused at stage 1, because the one-time value is used up [q:A13.r6.used]
  (W12, every reading). The project case is reachable only through a step
  shown in another session [q:A13.r6.bind] (W11, W13). **The customer case is
  the common one; the project case is the rare one.**
- [D] The open witnesses — W01, W02, W05, W06, W11, W13 — each get two or
  three outcomes the owner can see:
  - unchanged: the interface says done;
  - stale: the interface asks to reload, and the reloaded card shows the
    record erased;
  - invalid: a request error;
  - erased: "this customer was erased".

## 4. Can the answer be derived, or does the owner choose?

The model (`model/revisions.py`, `run.py`, results in `results/`) writes every
passage above as a predicate. Every reading is a parameter; nothing is chosen
in the engine. 135 situations × 32 reading sets.

- [D] **The "over revision" reading of State 0's "returns it unchanged" rows
  is rejected by accepted State 2 text.** Under it, archiving an archived
  project from an older card (W07, a fresh confirmation in a second session)
  would have to be accepted. A04 r3 and r2 refuse it as stale, and that is
  accepted text. So State 2 already reads R0-12's row "after the checks", and
  reading the erase row any other way would read two identical rows of one
  table differently. *Assumption [A]:* the rows of one table, worded alike,
  are read alike.
- [D] Of the remaining reading sets, 14 are consistent with every passage.
  They give the question's situations three different outcomes
  (`results/open_situations.md`):
  - W01 retry: stale (4 sets), invalid (8), unchanged (2);
  - W05 stale-card restrict: stale (4), invalid (8), erased (2).
- [D] **No reading needs a new State 0 promise or a new State 1 fact.** Both
  coherent answers keep every accepted witness (W03, W04, W07–W10, W12, W14,
  W15) and every State 0 row read "after the checks":
  - stale (A);
  - not checked (B).

  The "invalid value" reading is coherent too. It differs from A only in the
  stage and the kind of refusal. Nothing in the texts favours it, because A04
  r6 puts "the stated revision" in stage 5.
- [D] **The texts do not decide between A and B.**
  - For A: A04 r2's wording ("not the record's current one"); the invariant
    read by action kind; the same behaviour as a retried archive (W07); one
    rule for every revision-stating action.
  - For B: the State 0 row's origin ("a repeated erasure is a no-op", written
    before revisions); A05's Consequence ("a retried transition is safe"); the
    invariant read per action.

  Both are readings of the current text. The difference reaches the owner in
  the commonest history: a resubmitted erasure. → **a question to the owner**
  (`OWNER_QUESTION.md`). The patch stays a proposal.

## 5. Neighbours each option touches

| | option A — stale (proposed) | option B — not checked |
|---|---|---|
| A04 r2 | unchanged | scope: records with a revision |
| A04 r3 | one sentence added | one sentence added |
| A04 invariant | unchanged (both readings agree) | scope made explicit: "r having a revision" |
| A04 Required tests | +2 (retry stale; restrict from stale card stale) | +2 (retry unchanged; restrict from stale card erased) |
| A05 r1–r2 | unchanged: a repeat on an erased record happens only when it states none | unchanged, but r2's "answers the record as it stands" now also answers anonymised projects reached by archive from another session's step — read with R0-62 (only what it keeps) |
| W05, W06, W13 (stale card, erased record) | refused as stale; the owner reloads and sees it erased | refused by the lifecycle: "erased" directly |
| A13, A14, A01 | no change | no change |
| States 5–6 | the interface must handle "stale" on an erased record by reloading; the error answer (L14) is unchanged | none |

Both patches apply to `cf675e5c`. `tools/design_lint.py examples/registry
--state 2` reports 0 findings on each (`results/checks.md`).

## 6. Dependency log: what was found, when, and what it changed

| order | found while | dependency | effect on the understanding |
|---|---|---|---|
| 1 | choosing (START) | A04 r1–r3, r6; A05; A14; M01; M04; R0-35, R0-06, R0-67, R0-71; the customer rows | the initial cluster |
| 2 | step 1, reading M04 | an erased Customer also loses its marks; restrict/lift/end/resume on it are refused | the question is a family: every customer action on an erased record, not only erasure |
| 3 | step 1, `git log -S` | the row "erasing an erased customer returns it unchanged" predates R0-35 (`7fb4e3af`, "a repeated erasure is a no-op") | State 0's intent leans to "unchanged"; the start had assumed the row and A04 r2 agreed |
| 4 | step 1 | R0-35 speaks of "an older revision" and of a change | R0-35 does not decide; a retry's revision is not older |
| 5 | step 1 | R0-06 "nothing else" | Registry cannot tell a retry from an older tab; "R0-35 exact" would need a new State 0/1 fact |
| 6 | step 2, history of A04 | "leaves no revision behind" came from State 2 round 2 T26; "states none" was in the draft | the author settled the record's state after erasure, never a request stating a revision |
| 7 | step 3, outgoing refs | Identity formats: customer erasure is not confirmed; A13 r6: a used value stops a retry at stage 1 | the customer case is the common one; the project case needs two sessions |
| 8 | step 3, vocabulary search ("resubmit", "retried") | A01's Consequence, A05's Consequence | the texts expect resubmitted owner forms; "a retried transition is safe" supports B |
| 9 | step 4, modelling | the invariant's "that may move r.revision" has two readings | B is a reading of the current text, not a change of it |
| 10 | step 4, modelling | A04 r3 + test 3 already read R0-12's row "after the checks" | rejects reading the erase row "whatever the revision"; both options keep the rows |
| 11 | step 4, the model's exhaustive table | **the mirror case:** a request stating *no* revision for a record that has one — missing value (stage 4) or stale (stage 5)? | a neighbour outside the question; 26 situations; reachable only by a request the owner interface never makes (it always sends the card's revision) — left open, not patched |
| 12 | step 3, incoming refs | A18 / R0-89 (repeating erasures after a restore) | checked and dropped: R0-89 makes what the owner does around a restore the owner's; the owner reads the record first |

Search method:
- out of the cluster: every `A\d\d`, `R0-\d+`, `M\d\d` named in A04 and A05;
- into it: "A04 rule", "A05" and "(A05)" in all texts;
- vocabulary: "revision", "erased Customer", "anonymised", "resubmit",
  "retr", "lost answer";
- history: `git log -S` on the three key sentences;
- rounds: State 0–2 topics matching erasure × revision, retry or stale.

## 7. What is left open on purpose

- [D] The mirror case (W16): no revision stated for a record that has one. It
  is answered "refused" under every reading, so the only difference is
  "missing" against "stale". Only a client other than the owner interface can
  produce it. It does not belong to the question and is not patched.
- [A] Which reading of A04 r3's "states none" the author of the draft meant
  is not recorded anywhere. The commit message of `fd254d08` does not say.

## 8. Proposal

- [P] Option A (`patch/option_A.patch`): two sentences in A04 rule 3 and two
  Required tests. The texts do not decide it; it is put to the owner in
  `OWNER_QUESTION.md` against option B (`patch/option_B.patch`), and is **not**
  an accepted decision.

## 9. After the hand-over (added later; §1–§8 are unchanged)

The second author (`handover/`) read `packet/BUNDLE.md` and, with each read
logged, the Registry texts at `cf675e5c`. They reached the same conclusion
independently: the texts do not decide, and the owner chooses. They found
three things this investigation had missed:

| found by the second author | checked here | consequence |
|---|---|---|
| A04 r6: "a stage that does not apply to it is skipped" — a fourth ground for option B (stage 5 does not apply to a record without a revision) | [F] the clause is in A04 r6 at `cf675e5c` | the patch must say stage 5 applies, or the clause keeps inviting B |
| A05 r4 "come first": before the A05 repeat only, or before stage 5 too? Under option A, W13 (delete an anonymised project whole, stating a revision) is stale or refused by R0-71 | [D] the model had put A05 r4's refusals in stage 6 inside `failing_stages`, without a reading. **An unknown hidden in the engine.** It is now the reading `a05_r4_first`; with it, option A leaves W13 open (`results/witnesses.md`) | option A2 places A05 r4's refusals in stage 6; the second author proposes the smaller alternative of limiting the sentence to the erased Customer |
| A13 r6: what a step shown on a record without a revision binds | [F] not said; one single-review topic in State 2 round 18 | W11 and W13 may stop at stage 1; open under A, harmless under B |

The second author withdrew one claim of their own: whether the State 0 row
stays reachable from the interface. The interface is State 5's.

[P] Patch options after the hand-over:

- `option_A2.patch` = A + stage 5 made explicit + an invariant line + A05 r4
  placed;
- `option_B.patch` unchanged.

Both still need the owner's dated decision cited in A04 r3 once it exists. The
second author's wording for B is kept in `handover/response_2.json`.
