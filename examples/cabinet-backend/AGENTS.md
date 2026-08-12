# Cabinet Backend agent handoff

Current work is **Stage 7.1 — Semantic E2E review**.

Before editing Cabinet State 7 or declaring it closed, read in this order:

1. `../../skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md`
2. `71_semantic_e2e_handoff.md`
3. build the deterministic review slice for the target State 4 flow;
4. read the relevant State 1–2 sources when the slice exposes a semantic question.

Build a review slice with:

```bash
python tools/design_semantic_review.py examples/cabinet-backend \
  --flow flow:<name> --slice --json
```

The slice is navigation/context assembly only. It must not resolve product meaning, choose among ambiguous behaviors, or replace reading the accepted upstream source when a question is discovered.

Do not skip directly to final assembly.

The immediate task is to review each State 4 business flow as an observable behavior graph, challenge it with a materially different alternative interpretation, and validate the pre-code Given/When/Then semantic scenarios. Record findings before changing notes or upstream states.

For each flow ask both questions explicitly:

- can two materially different observable behaviors satisfy the same completed specification slice?
- can a trivial implementation satisfy the slice without violating an accepted obligation?

The semantic scenarios are requirements written before implementation. Future generated code must satisfy them; do not rewrite them merely to match generated code.

Do not redesign `SPEC_STANDARD.md`, Factory, or the known deferred adapters DSL gap as part of this Stage 7.1 review.
