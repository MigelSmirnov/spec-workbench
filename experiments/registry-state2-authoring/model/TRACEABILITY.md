# Traceability — model/revisions.py

The model decides nothing the texts leave open. The **engine** knows two
things only:

- `already_there`: which state each action leads to, so a repeat can be
  recognised;
- `TARGET`: the effect of an accepted action.

Everything else is a **predicate** over candidate outcomes (`preds`), or a
**reading** of a passage (`READINGS`), named and run both ways.

## Readings (the open points, made explicit)

| reading | passage | values | what the texts say for each |
|---|---|---|---|
| `a04_r2` | [q:A04.r2] | `all_records` / `records_with_revision` | "not the record's current one" is true when there is none / presupposes there is one |
| `a04_r3_none` | [q:A04.r3] | `caller_duty` / `invalid_value` | "an action on them states none" binds the caller only / makes a stated one an invalid value at stage 4 |
| `a04_inv` | [q:A04.inv] | `action_kind` / `this_action` | "that may move r.revision" names kinds of action / this action on this record |
| `s0_unchanged_rows` | [q:S0.erase_row] [q:S0.archive_row] [q:R0-71] | `over_revision` / `after_checks` | "returns it unchanged" whatever revision is stated (stages 1–4 still apply) / only for a request that passes every check |
| `absent_revision` | [q:A04.r1.list] [q:A02.r1] | `missing_value` / `stale` | no revision stated on a record that has one: missing (stage 4) / stale (stage 5) — the mirror case |

## Predicates

| id | layer | passages | translation and its limits |
|---|---|---|---|
| R0-35 | S0 | [q:R0-35] | Forbids an accepted change unless the request states the current revision. It does not forbid accepting a no-op, because R0-35 speaks of changes. |
| S0 action rows (effect) | S0 | [q:S0.erase_row] [q:S0.correct_row] | An accepted action that is not a repeat does what its row says. Corrections are taken with facts that differ from the stored ones; A03 rule 4 is not modelled. |
| S0 refusal rows | S0 | [q:S0.correct_row] [q:S0.restrict_row] [q:S0.end_row] [q:S0.erase_project_row] [q:M04.erased_refused] | `lifecycle_refusal`: the refusals State 0 states — correcting, restricting, lifting, ending, resuming an erased Customer; correcting an archived or anonymised project; deleting an active or anonymised project; anonymising an active one. |
| S0 "returns it unchanged" rows | S0 | [q:S0.erase_row] [q:S0.archive_row] [q:S0.erase_project_row] [q:R0-71] | Per `s0_unchanged_rows`. Assumption: the three rows are read alike (one table, one wording). |
| A04 r6 order | S2 | [q:A04.r6.kind] [q:A04.r6.stages] | `failing_stages` lists the failing checks under the readings; the earliest answers. Stage 1 is only the confirmation value (A13); authentication is out of scope. |
| A05 r1–r2 | S2 | [q:A05.r1] [q:A05.r1.erased] [q:A05.r2] | A repeat that passes every check answers unchanged. |
| accepted change only when not already there | S2 | [q:A05.r1] | |
| A04 invariant | S2-invariant | [q:A04.inv] | Per `a04_inv`. "stated differs" counts "stated a revision, record has none" and "stated none, record has one". |

## Situations and their admissibility

A situation is one step: the record's state, the action, the stated
revision, and the confirmation (fresh or used). Which history reaches it is
argued in `witnesses/witnesses.json`:

- a resubmitted form: A01's Consequence;
- two owner sessions: A13 rule 2;
- the interface sending the rendered card's revision: A04's Consequence.

A situation stating *none* for a record that has a revision is reachable only
by a client other than the owner interface. That is why the mirror family is
not counted as a consequence for the owner.

The model has no sequences. Each situation stands for the history its witness
gives. A rejected reading set is not a history: it is a set of readings
inconsistent with some admissible situation. The `readings.md` lines name the
first such situation and the passages that exclude the last candidates.

## Cost

| item | size | time |
|---|---|---|
| `revisions.py` | ~280 lines, about a third comments; 8 predicates, 5 readings | about 1 h, including two corrections (below) |
| `run.py` | ~150 lines | |
| quotes | 49 pinned passages (`sources.py`) | most of the reading time; they would be needed for the prose investigation anyway |

Two corrections found while building:

1. A missing predicate (the effect of a non-repeat) showed up as an ambiguity
   *inside* one reading set. It was a modelling gap, not a text gap.
2. A first "unconditional" reading of the State 0 rows also overrode stage 1.
   It was replaced by `over_revision`, a fair version of the alternative.

Either would have produced a false finding had it gone unnoticed.
