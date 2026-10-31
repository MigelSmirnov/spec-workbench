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
