# A question for the owner — what does a resubmitted erasure get?

**Situation.** You erase a customer's contact data. The answer gets lost (the
connection drops) and the browser resubmits the same form. The form carries
the revision of the card you were looking at. The customer is already erased
and no longer has a revision.

The texts allow both answers below. Neither needs a new product promise;
both keep every accepted behaviour (see `results/witnesses.md`).

| | A — "stale, reload" (recommended) | B — "done" |
|---|---|---|
| resubmitted erasure | refused as stale; you reload and see the customer erased | answered "erased, unchanged" |
| a second tab erases, restricts or corrects the customer after the first tab erased it | refused as stale; you reload | erasing: "unchanged"; restricting or correcting: refused, "this customer was erased" |
| the same for an anonymised project, from a confirmation step shown in another session | refused as stale | anonymise or archive: unchanged; delete whole or correct: refused (R0-71, R0-12) |
| audit log | no entry in every case | no entry in every case |
| texts changed | A04 rule 3 (+1 sentence), 2 Required tests | A04 rules 2 and 3, the A04 invariant's scope, 2 Required tests |
| how it fits the rest | the same as a resubmitted archive, which is already refused as stale | the same as what State 0 meant on 2026-10-26: "a repeated erasure is a no-op" |

**Why A is recommended:**
- one rule for every action that states a revision;
- it follows A04 rule 2 as written;
- it changes no accepted invariant.

**What B buys:** the commonest retry ends with "done" rather than with a
reload.

Reply A or B, or describe another behaviour. Until you answer, the patch is
not applied and A04 stays as it is.
