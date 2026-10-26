# Registry — emulated question rounds

These rounds imitate `tools/design_questions.py ask` with independent Claude
subagents, because neither the Responses API nor the Codex CLI was available in
the session that drafted the case (2026-10-26). They follow
`skills/spec-authoring/QUESTIONS.md` — three reviews reading only the state
texts with the state's `question_scope`, topics grouped, every topic raised by
two or more reviews judged, quotes checked verbatim — but they are **not**
rounds of the tool:

- they live here, not under `examples/registry/questions/`, so `status` and
  `authoring next` never count them toward closing a state;
- the reviewer is not the generator's model, so, as for `--provider codex`,
  they find real gaps but not necessarily the generator's; every state is closed
  again by real rounds before it is handed to the Factory.

Layout: `state<N>/round-<k>/review-<i>.json`, `summary.json` (topics, how many
reviews raised each, the judgement and its checked quotes) and `summary.md`.
