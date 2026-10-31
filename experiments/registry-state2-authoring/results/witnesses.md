# Witnesses under the current text and the two patch options

PASS/FAIL against an expected outcome (accepted witnesses); DECIDED: the outcome an option gives to an open witness; OPEN: outcomes still admitted.

| witness | status | preserve | current | option A (stale) | option A2 (stale, A05 r4 placed) | option B (ignore) |
|---|---|---|---|---|---|---|
| W01 Retry of a customer erasure after a lost answer | open | no | OPEN: accepted: unchanged | refused: invalid revision | refused: stale | DECIDED: refused: stale | DECIDED: refused: stale | DECIDED: accepted: unchanged |
| W02 A second tab, older than the erasure, erases again | open | no | OPEN: accepted: unchanged | refused: invalid revision | refused: stale | DECIDED: refused: stale | DECIDED: refused: stale | DECIDED: accepted: unchanged |
| W03 Erasing an erased customer, stating no revision | accepted | yes | PASS | PASS | PASS | PASS |
| W04 Restricting an erased customer, stating no revision | accepted | yes | PASS | PASS | PASS | PASS |
| W05 Restricting an erased customer from a stale card | open | no | OPEN: refused: invalid revision | refused: lifecycle | refused: stale | DECIDED: refused: stale | DECIDED: refused: stale | DECIDED: refused: lifecycle |
| W06 Correcting an erased customer from a stale card | open | no | OPEN: refused: invalid revision | refused: lifecycle | refused: stale | DECIDED: refused: stale | DECIDED: refused: stale | DECIDED: refused: lifecycle |
| W07 Archiving again from a card older than the archive | accepted | yes | PASS | PASS | PASS | PASS |
| W08 Archiving an archived project with its current revision | accepted | yes | PASS | PASS | PASS | PASS |
| W09 Erasing a customer from a stale card before any erasure | accepted | yes | PASS | PASS | PASS | PASS |
| W10 Erasing a customer with its current revision | accepted | yes | PASS | PASS | PASS | PASS |
| W11 Anonymising again from another session's step | open | no | OPEN: accepted: unchanged | refused: invalid revision | refused: stale | DECIDED: refused: stale | DECIDED: refused: stale | DECIDED: accepted: unchanged |
| W12 Retrying a project erasure in the same session | accepted | yes | PASS | PASS | PASS | PASS |
| W13 Deleting an anonymised project whole from another session's step | open | no | OPEN: refused: invalid revision | refused: lifecycle | refused: stale | OPEN: refused: lifecycle | refused: stale | DECIDED: refused: stale | DECIDED: refused: lifecycle |
| W14 Anonymising an anonymised project, stating no revision | accepted | yes | PASS | PASS | PASS | PASS |
| W15 Deleting an anonymised project whole, stating no revision | accepted | yes | PASS | PASS | PASS | PASS |
| W16 Correcting a customer without stating a revision (mirror case) | open | no | OPEN: refused: missing revision | refused: stale | OPEN: refused: missing revision | refused: stale | OPEN: refused: missing revision | refused: stale | OPEN: refused: missing revision | refused: stale |

Preserved witnesses not passing: none
