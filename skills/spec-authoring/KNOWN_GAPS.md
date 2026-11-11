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

## KG-003 — No form for naive UTC instants together with an elapsed-time reading (closed by `system_clock_backend/v5`)

Recorded 2026-11-07 (issue #147, comment of 15:23; client-portal at `8fe9b865`,
Factory at `29550bfd`). `system_clock_backend/v4` closed KG-002 for the wall
clock, but client-portal also measures elapsed time (`transport_guard`,
`time.monotonic`, the viewer-entry rate-limit window). With v4 both policies
failed, each in a different check:

| policy | Factory `validate_spec` | Factory time-source gate on the live module |
|---|---|---|
| no `elapsed_time` | pass | BLOCK `undeclared_elapsed_clock_access` (only at Route B) |
| `elapsed_time` held by `transport_guard` | BLOCK `local_implementation_requires_deterministic_backend` (`elapsed_clock_authority`) | pass |

Closed by SPEC_STANDARD §6.9 version 5 (`python_host_naive_utc_and_elapsed_clock_v1`):
v4's naive UTC wall-clock operation and one elapsed operation returning the raw
sample of `time.monotonic` (float seconds) or `time.monotonic_ns` (int ns) in the
same module, the only reader of both host clocks. v4 is unchanged. Both policies
above are Factory regressions (code-factory `test_generate_system_clock_draft.py`).
The case itself is not changed by this record; it reaches the form by declaring
the v5 backend and the dependencies of its consumers. The first policy is also
why the Workbench's own time check cannot stand in for the Factory gate on
code: the revision diagnosis of #147 (second direction) shows the two results apart.
