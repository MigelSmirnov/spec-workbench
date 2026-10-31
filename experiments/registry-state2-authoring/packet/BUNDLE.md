# Packet — a revision stated for a record that has none (Registry, State 2)

Hand-over packet for another author. It holds the question, the accepted
bases, the rules that constrain the answer, the admissible histories found so
far, and a proposed edit to check. It does **not** hold a verdict. Each
`[q:<key>]` is resolved verbatim in the appendix, with its commit and file.
Canonical text: `origin/agent/registry` @ `cf675e5c`.

## The question

When the owner submits an action that states a revision — above all **'erase
a customer's contact data'** — and the record has **no revision** (an erased
Customer, an anonymised project), what does Registry answer? In particular,
what does a resubmitted erasure get? It carries the revision the record was
erased from.

## Bases (State 0, State 1)

- Erase row: "erasing an erased customer returns it unchanged"
  [q:S0.erase_row]. The row was written on 2026-10-26, in a commit whose
  message says "a repeated erasure is a no-op" [q:S0.erase_row.origin_why];
  R0-35 is dated 2026-10-27 [q:R0-35.date].
- R0-35 [q:R0-35].
- Erased Customer: identity and the erased fact, "nothing else"
  [q:R0-06.nothing_else]; it loses its revision [q:M04.erased]; it is read as
  `customer_ref`, the mark and its instant [q:M04.read_erased].
- Refusals on an erased Customer: [q:S0.correct_row] [q:S0.restrict_row]
  [q:S0.end_row] [q:M04.erased_refused].
- Projects: [q:S0.archive_row] [q:S0.erase_project_row] [q:R0-71]
  [q:M01.anon_revision] [q:R0-62].
- Which actions state a revision is State 2's [q:RT.state2].
- Confirmed actions (customer erasure is not one) [q:ID.confirmed].

## State 2 rules that bear on it

- A04: [q:A04.r1] [q:A04.r1.list] [q:A04.r2] [q:A04.r3] [q:A04.r6.kind]
  [q:A04.r6.stages] [q:A04.r6.repeat] [q:A04.inv] [q:A04.inv.none]
  [q:A04.t3] [q:A04.t4] [q:A04.consequence]
- A05: [q:A05.r1] [q:A05.r1.erased] [q:A05.r2] [q:A05.r4] [q:A05.r4.anon]
  [q:A05.consequence]
- A01's Consequence [q:A01.consequence]; A02 r1 [q:A02.r1]
- A13: [q:A13.r6.bind] [q:A13.r6.used] [q:A13.r2.sessions]
- A14: [q:A14.r2] [q:A14.r3]

## Admissible histories found so far

Situation notation: record [state], action, stated revision. "last" is the
revision the record was erased from. Statuses: **accepted** — the texts give
the outcome; **open** — the author found several candidate outcomes.

| id | history | outcome(s) | status |
|---|---|---|---|
| W01 | C erased from revision 2; the same form resubmitted, stating 2 | unchanged / stale / invalid revision | open |
| W02 | tab A at revision 1; tab B corrects (2) and erases; tab A erases stating 1 | same as W01 | open |
| W03 | erase an erased C, stating none | unchanged | accepted |
| W04 | restrict an erased C, stating none | refused, erased | accepted |
| W05 | restrict an erased C from a card read before the erasure (stating 2) | stale / invalid / erased | open |
| W06 | correct an erased C from such a card | stale / invalid / erased | open |
| W07 | archive again from a card older than the archive, fresh confirmation in a 2nd session | stale | accepted |
| W08 | archive an archived P with its current revision | unchanged | accepted |
| W09 | erase C from an older card before any erasure | stale | accepted |
| W10 | erase C with its current revision | erased (changed), one audit entry | accepted |
| W11 | P anonymised in session 2; session 1 submits its erasure step bound to revision 3 | unchanged / stale / invalid | open |
| W12 | the same step resubmitted in the same session (value used up) | refused at confirmation | accepted |
| W13 | as W11, choosing "delete whole" | stale / invalid / refused by R0-71 | open |
| W14 | anonymise an anonymised P, stating none | unchanged | accepted |
| W15 | delete an anonymised P whole, stating none | refused (R0-71) | accepted |
| W16 | correct C (revision 2) stating no revision at all | missing value / stale | open, outside the question |

## The proposed edit (to be checked)

`patch/option_A.patch` against `examples/registry/02_rules_records.md`:

- A04 rule 3 gains: "A revision stated for one is not its current one, and
  the action is refused as stale (rule 2, stage (5) of rule 6) — a resubmitted
  erasure that states the revision the record was erased from included; read
  again, the record shows no revision, and the action stating none is
  answered as State 0 and A05 say."
- New Required tests:
  - 6. a resubmitted erasure stating the revision it was erased from is
    refused as stale and changes nothing; stating none answers it unchanged;
  - 7. restricting an erased Customer from a card read before its erasure is
    refused as stale, not as erased.


## The proposed patch, verbatim

```diff
diff --git a/examples/registry/02_rules_records.md b/examples/registry/02_rules_records.md
index 831a099c..160eff54 100644
--- a/examples/registry/02_rules_records.md
+++ b/examples/registry/02_rules_records.md
@@ -193,7 +193,11 @@ card it showed, and what the owner emptied is cleared.
 3. An action that would change nothing (A03 rule 4, A05) still states the
    revision and is refused when it is stale. An anonymised project and an
    erased Customer have no revision (M01, M04): an action on them states
-   none.
+   none. A revision stated for one is not its current one, and the action is
+   refused as stale (rule 2, stage (5) of rule 6) — a resubmitted erasure that
+   states the revision the record was erased from included; read again, the
+   record shows no revision, and the action stating none is answered as
+   State 0 and A05 say.
 4. Every action is atomic: it applies all its changes or none.
 5. Actions on records without a revision — adding a room, publishing or
    withdrawing a pointer, session actions — state none; the session's owner
@@ -241,6 +245,11 @@ for action a on record r in {Project, Customer} that may move r.revision:
    not as archived.
 5. Kernel naming a project outside its set with a blank room name receives the
    not-found answer, not the missing-name refusal.
+6. Erasing a Customer's contact data again from the form that erased it,
+   stating that revision, is refused as stale and changes nothing; erasing it
+   stating no revision answers it unchanged.
+7. Restricting an erased Customer from a card read before its erasure is
+   refused as stale, not as erased.
 
 ### Consequence
```

## Appendix — cited passages, verbatim

- **[q:S0.erase_row]** `cf675e5c:examples/registry/00_product.md`

  > | erase a customer's contact data | owner | the Customer keeps only its identity and the fact that it was erased; name, phone, e-mail and language are gone; projects still name it (R0-06) | unknown customer refused; erasing an erased customer returns it unchanged |

- **[q:S0.erase_row.origin_why]** `commit message of 7fb4e3af`

  > a repeated erasure is a no-op

- **[q:R0-35.date]** `cf675e5c:examples/registry/00_product.md`

  > ### R0-35 — Records carry a revision; stale changes are refused (owner, 2026-10-27; vNext §3.1, §11)

- **[q:R0-35]** `cf675e5c:examples/registry/00_product.md`

  > A project, a customer and an object carry a revision that every accepted change moves. A change states the revision it was made against; a change against an older revision is refused and nothing changes. Every change is atomic.

- **[q:R0-06.nothing_else]** `cf675e5c:examples/registry/00_product.md`

  > Erasing leaves the Customer's identity and the fact that it was erased, nothing else — the name does not survive.

- **[q:M04.erased]** `cf675e5c:examples/registry/01_models.md`

  > and so are its kind, its revision, its recorded instant, the request id of its create and its restricted and ended marks;

- **[q:M04.read_erased]** `cf675e5c:examples/registry/01_models.md`

  > An erased Customer is read as its `customer_ref`, the erased mark and its instant, and no other value;

- **[q:S0.correct_row]** `cf675e5c:examples/registry/00_product.md`

  > unknown customer refused; an erased customer cannot be corrected; a stale revision refused (R0-35)

- **[q:S0.restrict_row]** `cf675e5c:examples/registry/00_product.md`

  > | unknown or erased customer refused |

- **[q:S0.end_row]** `cf675e5c:examples/registry/00_product.md`

  > | unknown or erased customer refused; an end date later than today refused (R0-84) |

- **[q:M04.erased_refused]** `cf675e5c:examples/registry/01_models.md`

  > restricting, lifting, ending and resuming an erased Customer are refused (Primary actions).

- **[q:S0.archive_row]** `cf675e5c:examples/registry/00_product.md`

  > archiving an archived project returns it unchanged (R0-12) | unknown id refused |

- **[q:S0.erase_project_row]** `cf675e5c:examples/registry/00_product.md`

  > unknown or active project refused; anonymising an anonymised project returns it unchanged, and deleting it whole is refused (R0-71)

- **[q:R0-71]** `cf675e5c:examples/registry/00_product.md`

  > An anonymised project stays as it is: anonymising it again returns it unchanged, and deleting it whole is refused.

- **[q:M01.anon_revision]** `cf675e5c:examples/registry/01_models.md`

  > name, alias, object, customer link, rooms, revision, the request id

- **[q:R0-62]** `cf675e5c:examples/registry/00_product.md`

  > 'Read a project', `context`, 'list rooms' and the agent projection answer that it was erased, and 'list projects' never lists it.

- **[q:RT.state2]** `cf675e5c:examples/registry/01_models.md`

  > Which actions must state the revision they were made against is State 2's (carried, R0-35).

- **[q:ID.confirmed]** `cf675e5c:examples/registry/01_models.md`

  > confirmation id when the owner confirms an action that asks for confirmation — archiving a project, erasing an archived project, the import, erasing old audit entries (Primary actions)

- **[q:A04.r1]** `cf675e5c:examples/registry/02_rules_records.md`

  > Erasing a project or a Customer's contact data states the revision it was made against and leaves no revision behind (M01, M04): the record is anonymised, erased or deleted, not given a next revision.

- **[q:A04.r1.list]** `cf675e5c:examples/registry/02_rules_records.md`

  > correcting, archiving and erasing a project; correcting a customer, erasing its contact data, restricting and lifting, ending and resuming the relationship.

- **[q:A04.r2]** `cf675e5c:examples/registry/02_rules_records.md`

  > A stated revision that is not the record's current one is refused as stale, and nothing changes (R0-35).

- **[q:A04.r3]** `cf675e5c:examples/registry/02_rules_records.md`

  > An action that would change nothing (A03 rule 4, A05) still states the revision and is refused when it is stale. An anonymised project and an erased Customer have no revision (M01, M04): an action on them states none.

- **[q:A04.r6.kind]** `cf675e5c:examples/registry/02_rules_records.md`

  > and each check an operation states belongs to the stage of its kind

- **[q:A04.r6.stages]** `cf675e5c:examples/registry/02_rules_records.md`

  > (4) the values given (A02, A08, A22); (5) the stated revision or access version (A12); (6) the record's lifecycle — archived, erased, anonymised, not in the set, a customer's eligibility, a conflict.

- **[q:A04.r6.repeat]** `cf675e5c:examples/registry/02_rules_records.md`

  > A transition that passes all six may be a repeat that changes nothing (A05).

- **[q:A04.inv]** `cf675e5c:examples/registry/02_rules_records.md`

  > for action a on record r in {Project, Customer} that may move r.revision: a.stated_revision != r.revision => refused, r unchanged

- **[q:A04.inv.none]** `cf675e5c:examples/registry/02_rules_records.md`

  > accepted erasure, anonymisation or deletion => r has no revision after

- **[q:A04.t3]** `cf675e5c:examples/registry/02_rules_records.md`

  > Archiving moves the revision once; archiving again with the new revision answers the project unchanged.

- **[q:A04.t4]** `cf675e5c:examples/registry/02_rules_records.md`

  > Correcting an archived project with a stale revision is refused as stale, not as archived.

- **[q:A04.consequence]** `cf675e5c:examples/registry/02_rules_records.md`

  > the owner interface always shows and sends the revision of the card it rendered.

- **[q:A05.r1]** `cf675e5c:examples/registry/02_rules_records.md`

  > A transition to the state a record is already in, that passes every check of A04 rule 6, is accepted and changes nothing:

- **[q:A05.r1.erased]** `cf675e5c:examples/registry/02_rules_records.md`

  > anonymising an anonymised one (R0-71), erasing an erased Customer (Primary actions)

- **[q:A05.r2]** `cf675e5c:examples/registry/02_rules_records.md`

  > Such a transition answers the record as it stands; its revision, its last-changed instant and a session's access version stay; no audit entry is written and no confirmation id is minted.

- **[q:A05.r4]** `cf675e5c:examples/registry/02_rules_records.md`

  > The refusals State 0 states stay refusals and come first:

- **[q:A05.r4.anon]** `cf675e5c:examples/registry/02_rules_records.md`

  > deleting an anonymised project whole (R0-71)

- **[q:A05.consequence]** `cf675e5c:examples/registry/02_rules_records.md`

  > The audit log holds changes only (R0-58), and a retried transition is safe.

- **[q:A01.consequence]** `cf675e5c:examples/registry/02_rules_records.md`

  > Kernel's retried 'add a room' or publish and a resubmitted owner form are safe

- **[q:A02.r1]** `cf675e5c:examples/registry/02_rules_records.md`

  > A required value given as an empty string or as white space only is missing, and the action is refused as for a missing value

- **[q:A13.r6.bind]** `cf675e5c:examples/registry/02_rules_access.md`

  > bound to the action, its target, the revision or access version the step showed, and its inputs

- **[q:A13.r6.used]** `cf675e5c:examples/registry/02_rules_access.md`

  > is used up by the first submission that carries it, whatever its answer; a refused submission needs the step shown again.

- **[q:A13.r2.sessions]** `cf675e5c:examples/registry/02_rules_access.md`

  > Several owner sessions may be open at once; signing in ends none of the others.

- **[q:A14.r2]** `cf675e5c:examples/registry/02_rules_audit.md`

  > A refused action writes no entry — a stale revision, a failed check of rights, an unknown id, a refused sign-in included.

- **[q:A14.r3]** `cf675e5c:examples/registry/02_rules_audit.md`

  > An accepted action that changes nothing (A03 rule 4, A05) writes no entry, but for the erasure of old audit entries (A15 rule 6).

