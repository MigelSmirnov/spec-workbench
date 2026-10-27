# State 0, round 3 (emulated)

Re-review of the vNext reopening R0-24..R0-40 (`--since 258999de`, commits
`59f7488d`, `46867a5f`). Run through `tools/questions_workbench.service.ask_round`
itself — the tool's own prompts, grouping, judge and quote check — with a
provider that asks independent `claude -p` processes (no tools, no MCP, no
project settings, an empty working directory) instead of Codex. Moved here from
`questions/state0/round-18` so `status` never counts it.

Reviews: 17, 17, 0 points. Review 3 raised 15 points but keyed them
`<unit>: <title>` instead of the unit key, so the tool set them aside; they are
in its `raw` and match the topics below. Repeated topics: 13; blocking: 11.

| topic | kind | closes |
|---|---|---|
| T1 Kernel's agent authority vs creating projects, rooms, listing | **consequential_gap** | owner |
| T2 import source, ids across spaces, test data | **consequential_gap** | owner |
| T3 switch requests: confirm/decline, one or many, outcome | **consequential_gap** | owner |
| T4 restriction: lifting, correcting, naming a restricted customer | **consequential_gap** | owner |
| T5 `context` for a caller not cleared for personal_data (R0-04 vs R0-26) | **consequential_gap** | owner |
| T6 where PresuPro, Cabinet, Kernel run | answered | — |
| T7 R0-40 vs R0-03/R0-06 "the only exception" | **contradiction** | owner (what survives anonymisation) |
| T8 project without an object; `context` address | **consequential_gap** | text |
| T9 `onboard_object` token | answered | — |
| T10 caller-supplied id on production create vs import only | **consequential_gap** | owner |
| T11 owner interface covers every owner action | **consequential_gap** | text |
| T12 which action and revision an object change moves | **consequential_gap** | text |
| T13 working context: one, per agent, per session | **consequential_gap** | owner |

Single topics worth closing with the text: stale "staff"/"frontend" wording in
R0-13, R0-14, R0-16; whether archive, erase and restrict state a revision;
the audit's "significant operation"; withdrawing a context and archiving its
project; erasing an object's address as a subject right.

Not clear. Next: owner decisions on T1–T5, T7, T10, T13; text closures for
T8, T11, T12; then emulated round 4 on the changed units.
