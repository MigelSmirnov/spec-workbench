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
| texts changed | A04 rule 3 (+1 sentence placing the revision check before the lifecycle refusals), 1 invariant line, 2 Required tests (`patch/option_A2.patch`) | A04 rules 2 and 3, the A04 invariant's scope, 2 Required tests (`patch/option_B.patch`) |
| how it fits the rest | the same as a resubmitted archive, which is already refused as stale | the same as what State 0 meant on 2026-10-26: "a repeated erasure is a no-op" |

**Why A is recommended:**
- one rule for every action that states a revision;
- it follows A04 rule 2 as written;
- it changes the meaning of no accepted rule: it adds one sentence and one invariant line that make explicit what A04 rule 2 already says.

**What B buys:** the commonest retry ends with "done" rather than with a
reload.

A variant of A refuses such a request as "no revision expected" (an invalid request), not as stale. The effect is the same and the message differs.

The second author who checked the hand-over (`handover/response_2.json`) also sees this as your choice. Their reason: the row "erasing an erased customer returns it unchanged" was written on 2026-10-26 as "a repeated erasure is a no-op", before revisions existed. A "stale" answer narrows it, and no record shows you were asked about that.

Reply A or B, or describe another behaviour. Until you answer, the patch is
not applied and A04 stays as it is.
