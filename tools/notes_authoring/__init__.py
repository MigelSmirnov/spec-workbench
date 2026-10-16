"""The State 7 notes-writing environment (tools/DATA_CLOSURE_WORKBENCH.md).

This package holds its deterministic half: the declared surface a writing
agent looks values up in (M2, M4: `index`), the data-signal detector (M3:
`signals`), the scope-to-module table (M6: `binding`) and lint L2–L5
(`lint`). M1 and L1 are the Factory's resolver, called by
`notes_workbench.factory_addresses`. The agent, its prompt and the
structure request (§5) come next; until then the lint is a report.
"""
