# VVC Marketing Workspace

New separate project for Vital Vibe Construction.

- Canonical ref: `agent/vvc-marketing-workspace`.
- Current artifact: [State 0 product frame](00_product_frame.md) (simplified on 2026-10-17 by owner decision).
- Status: draft for owner review; State 0 is not accepted or closed.
- Scope of the first version: company Facebook Page publishing and Meta advertising, executed from ChatGPT through a small core-plus-adapters service on the owner's VPS. WhatsApp stays in the phone app and is out of scope.
- No production code, deployment, customer message send or Meta onboarding is performed by these documents.

## History

- `reviews/2026-10-17_state0_review_round1.md` — review of the first State 0 draft (commit `d109f01`). Its blockers A1–A4 were resolved by narrowing scope rather than by adding mechanism; the review is kept as the record of why.

## Continue

After the project is registered in `PROJECT_INDEX.json` (proposed separately through a `tools/*` pull request; until merged, main does not list this project):

```bash
python tools/workbench.py show vvc-marketing-workspace --json
python tools/authoring.py next vvc-marketing-workspace --json
```

Do not infer acceptance from the existence of this branch or file. State 0 closes when the owner confirms §2 of the product frame and answers questions 1–4 of §6. Product artifacts belong here; generic Workbench tools are not forked into this project.
