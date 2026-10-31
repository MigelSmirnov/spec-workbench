# How the experimental contracts and corpora are organised

## The constraint

A trial case, once added, is part of its contract version's corpus for good:
- no operation edits or deletes it (A01 rule 6);
- every later admission runs every case of the corpus (A04 rules 1–3).

A case with expected outputs is therefore a permanent claim that the slot's
function must give exactly those outputs. Put a contested hypothesis there and
it becomes, silently, a product expectation that every future implementation
must meet.

## The organisation chosen

The rules allow a case without expected outputs. It passes when the execution
succeeds (A04 rule 3: "if the case states expected outputs …").

**Two slots, same ports, same code, different status of their cases.**

| | `exp_registry_audit_probe` | `exp_registry_audit_accepted` |
|---|---|---|
| what a case says | "the model runs on this input" | "the current accepted text gives exactly this" |
| expected outputs | none, ever | the observation and analysis the accepted witness requires |
| what may go in | any hypothesis: historical versions, constructed versions (H1), contested readings, explorations | only witnesses with status `accepted` in the Workbench (Required tests of V6), run on V6 with the default readings |
| what admission proves | the model executes on every hypothesis without error — conflicts and ambiguities are results, not failures | the model reproduces every accepted expectation, digest for digest |
| what refuting a hypothesis does | nothing to the corpus; the result is in the trial execution's outputs | n/a: refuted hypotheses never enter |

Before a case's expected output enters the accepted corpus, `run_local.py`
checks it against the witness's own expectation from the Workbench (log
actions, confirmation ids, numbers, answers, the card). The Kernel then
enforces the stored output. The Workbench decides what is accepted; the
Kernel holds it to that.

## Why not alternatives

- **One slot, expected outputs on every case.** It pins outputs such as V5's
  conflict sets as permanent expectations. They are model findings about a
  superseded text, not product expectations.
- **One slot, expected outputs only on accepted cases.** This works, but one
  corpus then mixes the two kinds. A reader of the Kernel alone cannot tell
  them apart except by the presence of expected outputs. The two slots name
  the difference in their purpose, which the Kernel keeps and shows.
- **A new contract version per hypothesis.** It would avoid growing a corpus.
  But every version change makes a new admission problem, and the slot's
  history becomes a list of unrelated corpora.

## What must stay outside the Kernel

These live in the Workbench. The Kernel holds none of them:
- why a case is accepted: the witness, its basis quotes and the decision that
  accepts it;
- which readings are contested;
- the owner's decisions.

If the accepted text changes (as V5 → V6 did), the accepted corpus cannot be
corrected. A new contract version of the accepted slot, with a new corpus, is
the only way. The old one stays as history.
