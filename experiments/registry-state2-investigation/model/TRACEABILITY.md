# Traceability: normative passages ↔ model elements

`sandbox.py` splits a step in two. The **engine** (`check`, `apply`) holds what
is the same in every version: the order of checks, the domain effect, and
how a log is changed once an outcome is chosen. The **predicates**
(`rules_for`) hold every passage that decides the audit outcome. They are where the
versions differ. A predicate accepts or rejects one candidate outcome (no
entry; an entry; an entry with a confirmation id; for each, a sequence
number). The model never picks the outcome itself.

A citation is not a proof of translation. For each element the column "why
this translation" says what was kept and what was dropped. "Form" uses the
task's four kinds: transition, prohibition, condition, invariant.

## Engine (fixed across versions)

| element | passages | form | why this translation, and its limits |
|---|---|---|---|
| `check`: confirmation refused → refused at stage 1 | [q:A04.r6.stage1] [q:A13.r6.used] | condition | Only "valid or not" is modelled; binding, expiry and the one-time value of A13 r6 are collapsed into `conf_ok`. Enough here because every refusal writes nothing (A14 r2), whatever its cause. |
| `check`: unknown project → stage 3 | [q:A04.r6.order] | condition | One project slot, so "unknown" means "not created yet". |
| `check`: erasure date later than today → stage 4 | [q:A15.r3] [q:A15.t3] | condition | Dates are days relative to today. The stage is A04's "(4) the values given"; the text does not name the stage of the date check. The model's choice cannot be observed here: an erasure has no stage-5 or stage-6 check that could compete. |
| `check`: stale revision → stage 5, before lifecycle | [q:A04.r2] [q:A04.r3] [q:A04.t4] | condition | A boolean `stale`. A04 r3 (a would-be no-op is still refused when stale) is kept. |
| `check`: correction of an archived project → stage 6 | [q:R0-12.row] [q:A04.r6.order] | condition | |
| `check`: archive of an archived project → accepted repeat | [q:A05.r1.head] [q:A04.t3] | transition | Marked `repeat_of = "A05 r1"`; whether it writes anything is left to the predicates. |
| `check`: equal correction, create repeat → accepted repeat | [q:A03.r4] [q:A01.r4] [q:A01.r5] | transition | Same. A01's request-id lookup is reduced to one id `r1`. |
| `check`: erasure removes entries with day < date | [q:A15.r3] [q:A15.r1] | transition | Day granularity; A15 r3 cuts at 00:00 UTC, so within-day order does not matter. |
| `apply`: the erasure entry is appended after removal | [q:A15.r4] | transition | Built into `apply`, so the A15 r4 predicate cannot fail. It is kept only for traceability. This is a limit: the model cannot find a defect in A15 r4 itself. |
| `apply`: failed store → nothing stored | [q:A14.t3] [q:A04.r4] | prohibition | For V3a/V3b the marks are advanced before the failure, as those texts say ("before the entry commits"). |
| `apply`: `restore` replaces the store with the backup and starts a new history | [q:R0-89.title] [q:A18.restore.v0] | transition | Only used with `+restore`. The marks survive, as V3a says ("which a restore does not replace"). |
| `knowable_numbers` | [q:A15.r5.durable] [q:A15.r5.history] [q:A15.r5.marks] | condition | The numbers Registry can derive from what it holds: the entries, the kept last number (V1+), the marks (V3a/b). A number that satisfies the texts but is not knowable makes the step `out_of_store`. V0 does not say where the last number is kept: interpretation `v0_counter`. |

## Predicates

| id | layer | form | passages | why this translation, and its limits |
|---|---|---|---|---|
| R0-66 | S0 | transition | [q:R0-66.row] [q:R0-66.text] | "leaves an entry of its own" → an accepted erasure has an entry. "naming the date" is built into the entry. No condition on removal, because the passage has none. |
| R0-37/M09 conf | S0 | condition | [q:R0-37.audit] [q:M09.conf] | "a confirmation id where the owner confirmed" → an entry of a confirmed action carries an id. It does not say a no-op mints one. |
| R0-58 changes | S0 | transition | [q:R0-58.scope] | A significant change of state is recorded. Limited to the audited actions of the model. |
| R0-58 reads | S0 | prohibition | [q:R0-58.reads] [q:A14.r4] | |
| M09 never reused (global / per history) | S1 | invariant | [q:M09.seq.global] / [q:M09.seq.history] [q:R0-89.history] | Global before `cce33f0b`, per history after. It reads ghost state: every number ever written, in every history. |
| Identity formats (strict) | S1 | transition | [q:ID.conf_minted] | Only with `id_formats_strict=True`. That reading takes the sentence as complete; State 1 round 01 T7 carried the no-op case to State 2 [q:SO1.r1T7]. |
| A14 r1 | S2 | transition | [q:A14.r1] | "changes state" is `_changes_state`. Whether an erasure's own entry counts is interpretation `own_entry_is_change`. |
| A14 r2 | S2 | prohibition | [q:A14.r2] | |
| A14 r3 | S2 | prohibition | [q:A14.r3.old] / [q:A14.r3.new] | V5+ adds "but for the erasure". |
| A14 r5 | S2 | condition | [q:A14.r5.old] / +[q:A14.r5.new] | An id iff an accepted, confirmed action that changes state; V6 adds the erasure. Read as "iff" because "only for … ; … mints none" states both directions. |
| A14 invariant | S2-invariant | invariant | [q:A14.inv.old] / [q:A14.inv.new] | Interpretation `a14_inv_reading`. `at_commit` checks the step's own entry. `literal` also requires every accepted change of the history to still have its entry. |
| A05 r2 | S2 | prohibition | [q:A05.r1.head] [q:A05.r2] [q:A14.t2] | Applies to the transitions A05 r1 lists. `a05_covers_empty_erasure` adds the empty erasure (rejected reading). |
| A03 r4 / A01 r4 | S2 | prohibition | [q:A03.r4] [q:A01.r4] | |
| A15 r4 | S2 | condition | [q:A15.r4] | See the engine: it cannot fail. |
| A15 r5 | S2 | transition | per version, see `sources.VERSIONS[*].numbering` | `ever` is "continues from the last number ever written" (a ghost read). `durable`/`history` is the store's kept last number. `marks` allows either the marks or the store, because "ever written" does not say whether a number recorded before a failed commit counts. `marks_skip` uses the marks. |
| A15 r6 | S2 | transition | [q:A15.r6.old] [q:A15.t2.old] / [q:A15.r6.new] [q:A15.t2.new] | V0–V4: an empty erasure writes nothing. V5+: it writes an entry with an id. |
| A15 invariant (order) | S2-invariant | invariant | [q:A15.inv.seq] | Over the present log: numbers increase in write order. |
| A15 invariant (removed) | S2-invariant | invariant | [q:A15.inv.removed] | |
| A15 invariant (erasure entry) | S2-invariant | invariant | [q:A15.inv.entry.v0] / [q:A15.inv.entry.v2] / [q:A15.inv.entry.v5] | V2–V4 are conditional on a removal. V0/V1 interpretation `a15_inv_presupposes`. |

## What the model leaves out

These are not in the model, so it says nothing about them:

- every other action (customers, sessions, pointers, the import), the agent
  and services;
- several failing checks of one stage. The model has at most one failing
  check per stage, so A04's "names every one of them" is not exercised;
- concurrency (A13's lock, "applied one at a time"), instants inside a day,
  the clock going back;
- the content of an entry other than action, number, id and date;
- what backups hold (A18), other than the restore of numbering.

## Cost of upkeep (measured on this pilot)

- `sandbox.py`: ~590 lines, about a third of them comments. The engine (`check`, `apply`, `knowable_numbers`) is ~150; 23 predicates (some per-version alternatives).
- One text version is one entry in `sources.VERSIONS` (five flags). The
  passages it cites are entries in `sources.Q`. Adding V5→V6 needed one flag
  and two quotes.
- A version that changes a passage's *meaning* needs a predicate. A version
  that changes only the wording needs a new quote. `check_quotes.py` fails when
  a cited passage no longer exists at the commit.
