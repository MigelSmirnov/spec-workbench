# Known specification-language gaps

This file records intentionally deferred inconsistencies in the specification language. Entries here are not accepted design patterns; they are migration debt that remains visible while dependent tooling is being stabilized.

KG-001 is closed (below). Each open gap lists the finding codes it makes uncloseable by the author (`Finding codes:`); `tools/transition.py` marks those findings `workbench_gap` in a case that cites the gap as `[known_gap: KG-nnn]`, and they keep stopping (TRANSITION_PROTOCOL.md).

KG-001 was closed by `SPEC_STANDARD` version 2: the legacy top-level `adapters`
section was removed, call-site shape differences became caller-owned
requirements, and versioned backend IR now uses the closed structural `ref`
dictionary defined in §6.0.

## KG-002 — No conforming time-source form for a naive UTC clock read in a module-level function (closed by `system_clock_backend/v4`)

Recorded 2026-11-07 from the second client-portal assembly pass (issue #147,
branch `agent/client-portal` at `85895aad`). The owner chose option 1 of the
record (review 5812357953 of spec-workbench #148, 2026-11-07).

The rule "a fresh timestamp has a source" (`design_closure_gaps`, admission
FA012) had no conforming form for a valid, running design. Client-portal's
accepted decision A28 reads the clock once per operation as naive
`datetime.utcnow()`, in module-level functions, and stores offset-naive UTC
(`rules.clock_policy`). §6.9 v1 emitted an aware `Clock` port class, v2/v3 an
integer epoch, and naming business modules `time_source_policy` authorities was
refused (`local_implementation_requires_deterministic_backend`, §6.8).

Closed by one more form of the same family, supported on both sides:

- SPEC_STANDARD §6.9 version 4 (`python_host_naive_utc_clock_v1`): one
  module-level operation `() -> datetime`, one host reading per call as naive
  UTC (`tzinfo` None), nothing cached; the policy names its module the single
  wall-clock source with `datetime.datetime.now`, `samples_per_read: 1` and no
  `representation`. The Factory emits it, validates the closed form, checks it
  on deployment and polices its consumers with the existing conformance gate
  (code-factory `tools/generate_system_clock_draft.py`).
- Workbench: the operations of a module that really depends on that clock have
  a source (`design_closure_gaps.clock_consumers`): the module imports the
  function (`imports.module_internal`), or, before imports are decided, its
  State 3 `Knows` names the clock module. A module with neither has none.

Integration order: the code-factory change first, then the Workbench one; the
gap is closed once both are on `main`. Nothing is suppressed: a case that keeps
an undeclared clock still stops on the two codes. A case reaches the form by
declaring the v4 backend and the dependency of its consumers; the accepted
semantics of A28 (one reading per operation, its instant reused for every write,
the audit writer's own reading) are the design's and the backend does not change
them. The client-portal case itself is not changed by this record.
