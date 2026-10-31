# Kernel (local-034b50c) against the local control

Probe slot: 14 cases, 14 equal to the local bundle byte for byte (sorted compact JSON of both output ports).

Accepted slot: admission verdict `admitted` over 11 cases with expected outputs (the Kernel compared every output digest).

| case | Kernel execution | = local | wall ms | model result (what the hypothesis gives) |
|---|---|---|---|---|
| p01_V0_empty_erasure | passed | yes | 89 | conflict at `erase_before(before_all, confirmed)`: {A14 invariant, A15 invariant (erasure entry)}; {A14 invariant, R0-66}; {A14 r3, A15 invariant (erasure entry)} (resolution state2_edit) |
| p02_V1_empty_erasure | passed | yes | 75 | conflict at `erase_before(before_all, confirmed)`: {A14 invariant, A15 invariant (erasure entry)}; {A14 invariant, R0-66}; {A14 r3, A15 invariant (erasure entry)} (resolution state2_edit) |
| p03_V4_empty_erasure | passed | yes | 98 | conflict at `erase_before(before_all, confirmed)`: {A14 invariant, R0-66}; {A14 r3, R0-66}; {A15 r6, R0-66} (resolution state2_edit) |
| p04_V5_empty_erasure | passed | yes | 73 | conflict at `erase_before(before_all, confirmed)`: {A14 r5, A15 r6}; {A14 invariant, A14 r5, R0-37/M09 conf}; {A14 r5, A15 invariant (erasure entry), R0-37/M09 conf} (resolution state2_edit) |
| p05_H1_empty_erasure | passed | yes | 80 | conflict at `erase_before(before_all, confirmed)`: {A14 invariant, A15 r6}; {A14 invariant, R0-66}; {A14 r3, A15 r6} (resolution state2_edit) |
| p06_V6_empty_erasure | passed | yes | 80 | consistent |
| p07_V5_own_entry_is_change | passed | yes | 73 | consistent |
| p08_V6_a14_literal | passed | yes | 77 | conflict at `erase_before(today, confirmed)`: {A14 invariant} (resolution state2_edit) |
| p09_V3a_failed_number | passed | yes | 100 | ambiguity at `correct(name=B)`: entry #2 without confirmation id / entry #3 without confirmation id |
| p10_V1_restore | passed | yes | 76 | conflict at `correct(name=B)`: {A14 invariant, A15 r5, M09 never reused (global)}; {A14 r1, A15 r5, M09 never reused (global)}; {A15 r5, M09 never reused (global), R0-58 changes} (resolution state2_mechanism) |
| p11_V6_restore | passed | yes | 81 | consistent |
| p12_V6_explore | passed | yes | 191 | explore depth 4: 1481 states; findings none |
| p13_V1_explore | passed | yes | 125 | explore depth 4: 246 states; findings {'conflict': 3} |
| p14_V6_a05_covers | passed | yes | 74 | conflict at `erase_before(before_all, confirmed)`: {A05 r2, A14 invariant}; {A05 r2, A14 r5}; {A05 r2, A15 invariant (erasure entry)} (resolution state2_edit) |
