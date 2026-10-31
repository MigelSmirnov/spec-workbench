# START — fixed before the answer is sought

Written 2026-10-31 21:42 UTC. This file is not edited afterwards. Findings go
to `INVESTIGATION.md`.

## Source

- Canonical context (`PROJECT_INDEX.json` → `python tools/workbench.py show
  registry`): `agent/registry`, `examples/registry`, resolved
  `origin/agent/registry` = `cf675e5c9d284b7578740d5b074843da066d0d4b`.
  Phase: `state3_module_responsibilities`; State 2 closed by round 34.
- Generic tooling: `main` = `22d05dbf0394d8c0974ba65c42db8168a75b9fb6`
  (identical under `tools/` and `skills/`).
- Previous experiment: `experiments/registry-state2-investigation/` at
  `868ce840` on this branch.
- Work branch: `ccr-355d0166-9mky84`, the branch assigned to this session. It
  is based on `agent/registry` and changes only `experiments/`.

## The question

> When the owner submits **'erase a customer's contact data'** stating a
> revision, and the Customer is **already erased** (so it has no revision),
> what does Registry answer: the Customer unchanged, a refusal as stale, or
> another refusal? In particular, what does a **retry after a lost answer**
> get, given that it carries the revision the first submission stated?

The same shape, to be checked as neighbours: other customer actions on an
erased Customer, and project actions on an anonymised project, when the
request states the revision the record had before.

## Where it came from

- State 0 round 18, a single review (never judged): "For an exact retry of a
  successful archive or customer erasure carrying the old revision, does
  idempotent success or stale-revision refusal take precedence?"
- State 0 round 26 T3 asked, among other things, what happens "when that
  version is stale, including nominally idempotent actions such as archiving
  an archived project or erasing an erased customer". It was judged
  `judged_before`, i.e. carried to State 2.
- State 2 round 01, a single review, "Revision semantics of terminal erasure".
  State 2 round 02 T26 (contradiction) led to the current wording that an
  erased record "leaves no revision behind".
- State 2 round 08, a single review, "Archive semantics for an anonymised
  project … must that submission state a revision?"
- Candidate list and rejections: `CANDIDATES.md`.

## What is known at the start

From reading while choosing, not yet investigated:

- State 0's Primary actions row for erasing a customer's contact data says
  "erasing an erased customer returns it unchanged".
- R0-35: a change against an older revision is refused and nothing changes.
- A04 rule 2: "A stated revision that is not the record's current one is
  refused as stale".
- A04 rule 3: a would-be no-op still states the revision and is refused when
  stale; "An anonymised project and an erased Customer have no revision
  (M01, M04): an action on them states none."
- A05 rule 1 lists "erasing an erased Customer" as an accepted repeat that
  changes nothing.
- 'Erase a customer's contact data' does not ask for confirmation (Identity
  formats lists archive, project erasure, import, audit erasure), so A13's
  one-time value does not stop a retry at stage 1.

## What is unknown

- Whether A04 rule 2 applies when the record has no current revision at all.
- Whether stating a revision where "an action … states none" is a malformed
  value (stage 4) or a stale revision (stage 5), or is ignored.
- Whether the State 0 row's "returns it unchanged" is unconditional or holds
  only for a request that states the right (no) revision.
- What the owner interface sends: the card it rendered before the erasure, or
  a fresh one. A04's Consequence says it "always shows and sends the revision
  of the card it rendered".
- Whether anything else depends on the answer: the audit log, the restore
  replay of erasures (R0-89), the order of checks.

## Decisions initially assumed to be related

A04 (rules 1, 2, 3, 6), A05 (rules 1, 2, 4), A03 (corrections of a Customer),
A14 (no entry for a refusal or a no-op), M04 (Customer revision and erased
mark), M01 (anonymised project), R0-35, R0-36, R0-06, R0-67, R0-71, and the
Primary actions rows for customers and for erasing an archived project.

## Why the question belongs to State 2

The scope of `state2_rules_decisions` names "the order or precedence of
checks, the exact refusal conditions". State 1 carried "which actions must
state the revision" to State 2 ("Revisions and times", M04). The question is
which check answers a revision stated against a record without one: an exact
refusal condition and a precedence between A04's stages and A05's repeat
rule. It changes no model fact.
