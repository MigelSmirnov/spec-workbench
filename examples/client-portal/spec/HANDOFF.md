# Handoff — Client Portal (current)

Replaces the handoff of the authoring pass of 2026-07-19 (its key decisions
are carried into the states that own them, `SOURCE.md`). State of
`agent/client-portal` on 2026-11-07; the assembly result is `80_assembly.md`.

## Where the case stands

- States 0–7 migrated; question rounds of States 0–5 and 7 closed on their
  current texts.
- Imports closure ready (195/195 scopes, strict).
- Assembly not ready: identity 160, closure gaps 44 (time), witness 14.
- Next phase (`tools/authoring.py next client-portal`):
  `state6_exact_contracts`, whose model-closure and time-source checks are not
  checked until the model closure lands.

## Factory admission (`tools/design_factory_admission.py --update-existing`)

| check | result | owner |
|---|---|---|
| FA001, FA004, FA005, FA009, FA010, FA014, FA016, FA017, FA018, FA019, FA022 | PASS | — |
| FA007 | PASS with `--update-existing`; BLOCK without it | needs the export decision |
| FA002 | BLOCK: no Stage 8.1 ledger | reachable once the assembly is ready |
| FA003 | BLOCK: assembly not ready | see below |
| FA012 | BLOCK: 44 closure-gap findings (time) | clock source, below |
| FA015 | BLOCK: Factory Spec Inspector rejects the spec | interface findings pending review |
| FA008 | BLOCK: Factory checkout dirty | not this case |

## Model closure and clock source (prepared, not landed)

A closure of 32 State 1 models and 64 `contract_only` records validates with 0
errors. It must land with the time source, or the State 6 time-source check
goes from not checked to 35 open findings.

The time source designed for it is SPEC_STANDARD §6.9 version 5: a module
`system_clock` (`utc_now() -> datetime`, the value `datetime.utcnow()` gives;
`monotonic_seconds() -> float`, the value `time.monotonic()` gives) with
`rules.time_source_policy` naming it the only reader of both host clocks; the
44 callables that read `datetime.utcnow()` and the transport guard read time
through it. On that design the elapsed obligation closes, the wall obligation
closes except one finding, and the Factory validator passes.

The remaining finding stops it: `api_irregular.viewer_enter_endpoint` returns
`ViewerSessionView.expires_at`, which `viewer_access.enter_viewer_access`
computes; the endpoint itself reads no clock (Factory code `api_irregular.py`).
`fresh_timestamp_without_source` admits only a datetime parameter, a clock
port, a policy authority or a clock import in the endpoint's own module, so
the check cannot see an instant produced by the callee. That is a Workbench
gap (TRANSITION_PROTOCOL, `workbench_gap`), not a design defect: giving
`api_irregular` a clock import it never calls would satisfy the check
without being true. The time-source decision of 2026-11-06 in `SOURCE.md`
stays in force until the gap is closed.

Also, on the live code the Factory time-source gate blocks under that policy
until the next Route B regenerates the consumers (they still read the host
clocks themselves).

## Invariants without a witness

No Factory check asserts these; a witnessing check would have to show:

| decision | invariant | what a witnessing check must assert |
|---|---|---|
| A4 | PLAT-REG-004 | a request or import that carries Registry context (status, name) of its own is decided by the Registry answer, never by the supplied value |
| A5 | PLAT-REG-001 | the production `validate_project_reference` refuses a UUID the Registry does not know, for every principal and both producer scopes, and no operation creates a project id |
| A5 | PLAT-REG-002 | `_validate_reference_identity` refuses a Registry answer whose UUID differs from the requested one; linkage never uses a display name or address |
| A5 | PLAT-REG-007 | a viewer's display name is kept as written whatever the Registry `customer_ref` says |
| A7 | INV-031 | an expense is created only from a confirmed, complete recognition result of a supported version, and confidence, provider fields and raw responses are not persisted |
| A9 | INV-044 | a section whose actual material cost exceeds its plan shows a negative remaining, never clamped to zero, and missing data is shown as missing |
| A11 | INV-008 | re-issuing a viewer credential revokes the previous one in the same transaction, so the old secret no longer opens a session |
| A15 | INV-054, INV-055 | the active-project list is ordered by `project_id` whatever the upstream order; the viewer project list by casefolded display name, then `project_id`, display names unchanged |
| A18 | INV-026 | an import never derives or rewrites planned values from expenses or mutable producer state |
| A18 | INV-027 | after an owning record changes, the next read reflects it: totals are not stored |
| A18 | INV-028 | a section referenced by an allocation or progress record cannot be deleted |
| A20 | INV-040 | completion percent accepts only a staff value in [0, 100], and publishing a photo never changes progress |
| A21 | INV-050 | the same records give the same derived values for staff and viewer, ties included |
| A32 | both | the pinned dependencies carry no known vulnerability affecting the portal at deploy |
