# VVC Marketing Workspace

New separate project for Vital Vibe Construction.

- Canonical ref: `agent/vvc-marketing-workspace`.
- Current artifact: [State 0 product frame](00_product_frame.md).
- Status: draft for owner review; State 0 is not accepted or closed.
- Immediate scope: Facebook presence, Meta advertising and Spanish/Russian WhatsApp enquiry handling through a ChatGPT plugin and a VPS service.
- No production code, deployment, customer message send or Meta onboarding is performed by these documents.

## Continue

Use the current main Workbench tooling and the curated project index:

```bash
python tools/workbench.py show vvc-marketing-workspace --json
python tools/authoring.py next vvc-marketing-workspace --json
```

Project registration is proposed separately through a `tools/*` pull request. Until that index change is merged, main does not list this project. Do not infer acceptance from the existence of this branch or file.

The State 0 owner review and question rounds remain pending. Resolve the recorded product-boundary questions before moving to State 1. Product artifacts belong here; generic Workbench tools are not forked into this project.
