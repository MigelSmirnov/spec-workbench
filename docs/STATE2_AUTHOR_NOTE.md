# Note for the author of a State 2 that keeps reopening

2026-11-20. For an author working with the tools of `main`. It changes no
tool and no rule of `main`; it says how to choose among the dispositions
`main` already has. Background and data:
`docs/STATE2_REQUIRED_RESULTS_20261120.md` on this branch.

## Stop first

If a round came back to a place you already fixed, or a topic broke because
of your own fix, do not fix it a third time. That is the stop rule of
`QUESTIONS.md`: write the topic out for the owner. A fix that breaks
something else decided more than the question asked.

## Two questions before every disposition of State 2

**1. Whose question is it?**

Can it be put in the words of States 0 and 1: their actors, models,
statuses, refusals and promises?

- Yes: it is State 2's. Go to question 2.
- No, it needs the words of an implementation (members of a JSON object, the
  service's own files and folders, opening a file, locks, temporary names,
  modes, library calls, the order of steps): it is a later layer's.
  Disposition `carried`. In `--what` write three things: the options, what
  to check of each, and the rule or invariant of States 0–2 that every option
  must keep, by its identifier.

  Not: `--what "sort out duplicate member names"`.
  But: `--what "reject a repeated member name or take the last one; check a
  hand-edited file and a partly written one; either way A2 rule 1 holds: an
  unreadable connections file confirms no connection"`.

**2. Must the two behaviours be told apart?**

Quote the promise, invariant or constraint already written in States 0–2
that one of the two behaviours breaks.

- You can quote it: `fixed`.
- You cannot: `accepted`, with the reason "both keep every stated
  requirement". The choice stays free. That someone could see a difference is
  not a reason: someone can see every difference.

## What a fix of State 2 looks like

One sentence about a result: an outcome, a refusal, a durable effect, a
guarantee. No new identifier, constant, call or procedure. On Portal
Deliverer the fixes that answered a required result added about 85
characters each.

A `standard_violation` (an enumeration not named as its members, a threshold
not named as a constant) is fixed in wording only. It adds no behaviour.

A question about how a test proves a rule goes to `factory_checks`, as
before.

## Do not build on a decision still in its round

A draft of code or of a note is not fitted to a State 2 decision while the
round on that decision is open. If the round sends the decision to a later
layer, the draft was that layer's work all along.

## When State 2 is closed

Its required results are decided, the freedom that breaks none of them is
left alone, and what a later layer must choose is addressed to it. It is not
closed by leaving the implementer nothing to guess.
