# Checks of the patch options

Run in a detached worktree at `cf675e5c` (scratch, not kept):

```text
git apply --check patch/option_A.patch      -> ok;  design_lint --state 2: 0 findings
git apply --check patch/option_A2.patch     -> ok;  design_lint --state 2: 0 findings
git apply --check patch/option_B.patch      -> ok;  design_lint --state 2: 0 findings
```

Model (`run.py`, `witnesses.md`): every witness with `preserve: true` passes
under the current text and under options A, A2 and B. Open situations
(`open_situations.md`):

| text | open of 135 |
|---|---|
| current | 46 |
| A | 28 — W13 stays open once A05 r4 is a reading |
| A2 | 26 |
| B | 26 |

The 26 left open by A2 and B are all the mirror family: a revision missing on
a record that has one.
