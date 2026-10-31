# Candidates checked before choosing the pilot question

Written 2026-10-31, before START.md. Sources searched:

- every State 0, 1 and 2 round topic (`examples/registry/questions/*/round-*/summary.json`
  at `cf675e5c`), filtered to State 2 domain units (A01–A13, A22, `?`,
  `context`) and to the late rounds 13–34;
- the "carried to a later state" list in `00_product.md`;
- the `### Open questions` sections of `01_models.md`.

The criteria come from the task: an existing product promise; several rules;
an observable consequence; no accepted answer; not settled by the previous
experiment (`experiments/registry-state2-investigation/`, the audit cluster);
and no closed decision reopened just to get pilot material.

| # | candidate | where raised | verdict | reason |
|---|---|---|---|---|
| 1 | **A repeated customer erasure that states the revision the customer had before it was erased** (a retry after a lost answer, or a second tab) | State 0 round 18 (single review, never judged): "For an exact retry of a successful archive or customer erasure carrying the old revision, does idempotent success or stale-revision refusal take precedence?"; State 2 round 01 (single review) "Revision semantics of terminal erasure"; State 0 round 26 T3 (carried to State 2) | **chosen** | promise: the Primary actions row "erasing an erased customer returns it unchanged" against R0-35; rules: A04 rules 2, 3, 6, A05 rules 1–2, A14; observable to the owner as accepted vs refused. No passage speaks of a stated revision on a record that has none. Not touched by the previous experiment. |
| 2 | Archiving an anonymised project, and whether it states a revision | State 2 round 08 and round 15 (single reviews) | rejected as the pilot; **kept as a neighbour of 1** | Same mechanism as 1 (a record without a revision). It is weaker on its own: the owner interface never shows an anonymised project's card (R0-62), and a retried archive goes through A13's one-time confirmation. |
| 3 | Repeat of a Kernel withdrawal (no request id), R0-78 "its replay behaviour" | State 2 round 14 (single review) | rejected | State 0's Primary actions row decides it: "a pointer already withdrawn or superseded refused". R0-78 asks for the behaviour to be declared, which is State 6's manifest. |
| 4 | Do access versions move when an erased project leaves a session's set? | State 2 round 18 (single review) | rejected | A12 rule 1 and Required test 2 answer it explicitly. |
| 5 | A create's request id after its record was anonymised or erased | State 2 rounds 2, 4, 5, 9, 13 (single reviews), round 10 T11 answered | rejected | A01 rule 8 and Required test 6 answer it. |
| 6 | Several failing checks of one stage of A04 | State 2 rounds 10–19 | rejected | Answered since `430f4d4c` ("names every one of them"). The previous experiment handled it in Part 4. |
| 7 | Owner-session concurrency, expiry pass, monotonic clock (A13) | State 2 rounds 13–34 | rejected | The latest rounds judged these `judged_before`/`answered`. Mostly runtime mechanics, not a product promise. |
| 8 | Backup format, keys, file lifecycle (A17, A18) | State 2 rounds 16–33 | rejected | Representation and operations; `later_state` or `judged_before`. Outside the domain rules. |
| 9 | What a restored store replays (customer marks, cutoffs) | State 2 rounds 13–16 | rejected | R0-89 makes what the owner does around a restore the owner's; reopening it would reopen R0-89. |
| 10 | Confirmation binding for confirmed actions without a revision (import, audit erasure) | State 2 round 18 (single review) | rejected | A13 rule 6 binds the inputs ("its inputs … kept as a digest"). Close to the previous experiment's cluster. |
