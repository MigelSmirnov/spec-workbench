# Normative authoring sequence

This document defines the ordering contract for Spec Workbench authoring.
`authoring_sequence.json` is the machine-readable source of truth for orchestration;
this Markdown explains the same contract for people and agents.

`SPEC_STANDARD.md` remains normative for the serialized `global_spec.json` format.
`SKILL.md` remains normative for the semantic meaning of design states.

## One pipeline for every project

Project identity and project state are separate from orchestration:

```text
PROJECT_INDEX.json
  -> select logical project / canonical ref / path
  -> tools/authoring.py next <project>
  -> generic deterministic authoring gate
  -> project artifacts on the selected canonical ref
  -> tools/authoring.py next <project>
```

Project branches own project data and design artifacts. They must not own a forked
copy of the generic authoring sequence. MCP integrations must wrap the same
pipeline API used by the CLI rather than reimplementing routing.

## Promoted canonical sequence

The generic sequence currently promoted to `main` is:

```text
State 0  Product frame
  -> State 1  Models
  -> State 2  Rules / accepted decisions
  -> State 3  Module responsibilities and capabilities
  -> explicit State 2 -> State 3 ownership trace
  -> State 4  Reviewed end-to-end flows
  -> State 5  Public module operations
  -> promotion boundary for State 6-9 tooling
```

### State 0 — Product frame

State 0 is currently a manual semantic gate. `design_index.py` can inspect
explicit design structure from the beginning, but there is not yet a separate
State 0 deterministic linter. The sequencer must therefore report State 0 as an
explicit manual authoring step rather than silently treating it as validated.

### State 1 — Models

Use:

```bash
python tools/design_index.py examples/<case> --list --state 1
python tools/design_lint.py examples/<case> --state 1
```

Structural edits should use `design_editor.py`, whose addresses come from the
same deterministic index.

### State 2 — Rules and accepted decisions

Use:

```bash
python tools/design_index.py examples/<case> --list --state 2
python tools/design_lint.py examples/<case> --state 2
```

The State 2 lint includes the explicit security-review gate. Unresolved security
categories block State 3.

### State 3 — Module responsibilities

Use `design_stage3.py --lint`. State 3 produces stable `module:*` and
`capability:*` identities.

Before State 4, `design_trace.py --check` validates the explicit `30_trace.json`
transition: each accepted State 2 decision has exactly one primary State 3 owner
or an explicit non-runtime disposition. Ownership is never inferred from prose.

### State 4 — Reviewed flows

Use `design_stage4.py --lint`. When `40_flow_plan.json` exists, coverage and
`--next` are part of readiness so planned flows cannot disappear silently.

### State 5 — Public module operations

Use `design_stage5.py --lint`. When `50_api_plan.json` exists, coverage and
`--next` are part of readiness. State 5 freezes cross-boundary public operations
proven by reviewed State 4 flows.

## Temporary promotion boundary

The Cabinet development line contains a mature post-State-5 implementation for
contracts, persistence closure, router closure, notes, assembly, module review,
and Factory admission. That implementation is **not yet canonical generic
Workbench tooling** because parts of it still contain product-specific policy
(for example Cabinet-specific exposure and HTTP assumptions).

Until those policies are extracted, the generic sequencer in `main` must stop
explicitly at `post_state5_toolchain` instead of routing projects through a
Cabinet-specific implementation by accident.

The target continuation is:

```text
pre-contract structured data closure
  -> State 6 exact contracts / internal functions
  -> optional deterministic persistence closure
  -> optional deterministic HTTP route/context closure
  -> State 7 notes
  -> Stage 8 assembly
  -> Stage 8.1 module review
  -> Stage 9 Factory admission
```

Promotion of those phases must preserve the same rule: project-specific policy
belongs in project artifacts/configuration, not in generic orchestration code.

## Agent entry point

After resolving a logical project with `tools/workbench.py`, use:

```bash
python tools/authoring.py next <project>
```

Use `--json` for agents and future MCP wrappers.

Do not reconstruct the authoring order from filenames and do not search for a
project-local sequencer. The machine sequence is
`skills/spec-authoring/authoring_sequence.json` in `main`.
