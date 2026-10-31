# Checks of the patch options

Run in a detached worktree at `cf675e5c` (scratch, not kept):

```text
git apply --check patch/option_A.patch      -> ok
git apply --check patch/option_B.patch      -> ok
git apply patch/option_A.patch; python tools/design_lint.py examples/registry --state 2
    Findings: 0 errors, 0 warnings, 0 info / OK: no authoring findings.
git apply patch/option_B.patch; python tools/design_lint.py examples/registry --state 2
    Findings: 0 errors, 0 warnings, 0 info / OK: no authoring findings.
```

Model (`run.py`): every witness with `preserve: true` passes under the current
text, option A and option B (`witnesses.md`, "Preserved witnesses not passing:
none"). Both options decide all 20 situations of the question's family; the 26
situations of the mirror family stay open under both (`open_situations.md`).
