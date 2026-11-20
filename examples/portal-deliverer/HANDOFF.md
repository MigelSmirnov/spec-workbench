# Portal Deliverer — where the case stands (2026-11-20)

Start with the tools, not with this page: `python tools/authoring.py next portal-deliverer`
(or the MCP `workbench_state`) gives the phase and the whole-case diagnosis. This page holds only
what those tools cannot know.

## Factory root for rounds and diagnosis

The State 7 prompts and the Factory spec check need `fastapi_sync_v2` with the credential checked
before the body (code-factory #227 and #228, both merged). The main `code_factory` checkout stays on
`docs/portal-deliverer-prototype` with someone else's uncommitted work, so run every round and
`design_diagnose` with a checkout of Factory `main`:

    SPEC_WORKBENCH_FACTORY_ROOT=<code_factory_worktrees>/main-check   # detached at origin/main

Notes propagation needs spec-workbench #196 (merged).

## Next

1. Owner 2026-11-20: the prototype is forgotten. R0-04 is withdrawn; States 0 to 5 hold no prototype
   evidence, and no state is written or answered from `prototypes/portal_deliverer/`.
2. Question rounds from State 0 in order (the sequencer names each), then States 1 to 5, then State 7.
3. Each state holds only what its phase in `authoring_sequence.json` asks for, written by SPEC_STANDARD.
   No mechanics in States 2, 3 and 5: a round topic that asks how something is done (opening, reading
   order, boundaries, framework behaviour) is disposed `--carried 7`, not answered by editing the state.
   Rounds 69-76 of State 2 show the cost of the other way.

## Open owner decisions

- `imports_factory_unavailable`: the imports gate blocks a case whose Factory project has no
  specification yet. A tools change (`not_applicable` before the first spec) or another route.

## What changed on 2026-11-20

- The Factory target `portal_deliverer`, its verification config and 19 witness tests; the checks
  are carried to code-factory#226.
- Every State 7 note rewritten to the standard (round 1: 78 topics; round 2: 9).
- Values the notes wrote inline have homes in A8 (`OBSERVATION_FAILURES`, `EXIT_STATUSES`,
  `EXIF_*_PATTERN`, `STOP_SIGNALS`, `BIND_HOST`, `TOKEN_*`, `INTAKE_ID_SEPARATOR`).
- The three API routes are table routes of the router (`fastapi_sync_v2`); `AuthenticationRequired`
  is `AuthenticationRejected`, because the Factory recognises a module's own exception by its name.
