# Writing Registry's witness tests — the task

Decided 2026-11-24 by the owner: Registry's decisions are witnessed the way
cabinet-kernel's are — by runtime tests written before the code is
generated, run by the Factory project `registry`, and judged by
`design_questions.py judge-checks` on their code. The `note:` bindings to
[TEST_EVIDENCE] notes are gone: the notes still feed generation, they no
longer witness a decision.

## What is ready

- **The bindings.** Every numbered Required test of `02_rules_*.md` that
  shows a formal invariant ends with `Shows <ids>. [witness:
  verification:registry_aNN_<slug>]` — 109 checks over A01–A19 and A22.
  A20 is kept by the release process outside Registry; A21 by the Workbench
  check `state2_rules_decisions`. Three Required tests were added so that no
  invariant lost its witness with the notes: A04 test 11, A09 test 6, A22
  test 4.
- **The checks.** code-factory `verification/configs/registry.yaml` runs each
  as `python -m pytest projects/registry/tests/semantic/test_aNN_<topic>.py::test_<slug>`.
- **The files.** `71_semantic_test_export.json` lists one test file per
  decision (`status: open` until every file is written and reviewed).
- **The surface.** `RUNTIME_SURFACE.md`: the only calls and capabilities a
  test may use.

## What to write, per decision

One file `test_aNN_<topic>.py` as the manifest names it, holding:

1. One test `test_<slug>` for every tagged Required test, named exactly by
   its tag's slug (`registry_a04_archive_moves_revision_once` →
   `test_archive_moves_revision_once`). It shows what the Required test says
   — every case it names, with the invariants after `Shows` — and fails for
   an implementation that violates them.
2. A test for every untagged Required test too, named by what it shows: it
   runs in the project's pytest check, not as a witness.
3. The module docstring: the decision, its source file, and the surface it
   uses, as `cabinet-kernel/tests/semantic/test_a01_identity.py` does.

Rules, from cabinet-kernel's tests (branch `agent/cabinet-kernel`):

- **From the design, never from code.** Expected values come from States 1–7
  (a refusal's code, stage and kind from State 5, "Closed set of refusal
  codes"; a constant by its value in the data closure, named in a comment).
  Each assertion can be traced to a rule.
- **Observable only.** A test calls only what `RUNTIME_SURFACE.md` lists.
  A call it needs and the file lacks is added there first, with the State 5
  operation or State 6 model it reaches.
- **A control beside each refusal.** Where a test shows a refusal, it also
  shows the accepted case next to it, so a Registry that refuses everything
  fails.
- **Nothing changed means read back.** "Changes nothing" is shown by reading
  the records back through the surface (and `store_rows` where a surface read
  cannot tell).
- **No skip, no xfail.** A test that cannot be written without guessing is a
  finding on the decision, not a skipped test.

## Review, before the manifest is closed

For each decision, `review/ANN.md`: a table of every witness test with at
least one named mutant (a plausible wrong Registry) and whether the test
catches it, and why; the corrections made. `review/SUMMARY.md` totals them,
as `cabinet-kernel/tests/semantic/review/` does. Then:

- `python -m py_compile` every test file;
- one test per tag, same name: `design_decision_witness.py --coverage` with
  `SPEC_WORKBENCH_FACTORY_ROOT` at a code-factory checkout holding the
  config;
- `71_semantic_test_export.json` to `semantic_closed`;
  `design_semantic_handoff.py` passes;
- `design_questions.py judge-checks` on the real tests; a `partial` binding
  is carried to the code-factory issue named as `factory_checks_issue` in
  `90_factory_target.json` (to be opened then).
