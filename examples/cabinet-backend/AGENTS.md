# Cabinet Backend agent handoff

Current work is **Stage 7.1 — Semantic E2E review**.

Before editing Cabinet State 7 or declaring it closed, read in this order:

1. `../../skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md`
2. `71_semantic_e2e_handoff.md`
3. the relevant State 4 flow and its semantic slice (`00`/`01`/`02` → `30` → `40` → `50` → `60` → `70` → `80`).

Do not skip directly to final assembly.

The immediate task is to review each State 4 business flow as an observable behavior graph, challenge it with a materially different alternative interpretation, and validate the pre-code Given/When/Then semantic scenarios. Record findings before changing notes or upstream states.

The semantic scenarios are requirements written before implementation. Future generated code must satisfy them; do not rewrite them merely to match generated code.

Do not redesign `SPEC_STANDARD.md`, Factory, or the known deferred adapters DSL gap as part of this Stage 7.1 review.