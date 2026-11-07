# Known specification-language gaps

This file records intentionally deferred inconsistencies in the specification language. Entries here are not accepted design patterns; they are migration debt that remains visible while dependent tooling is being stabilized.

KG-001 is closed (below). Each open gap lists the finding codes it makes uncloseable by the author (`Finding codes:`); `tools/transition.py` marks those findings `workbench_gap` in a case that cites the gap as `[known_gap: KG-nnn]`, and they keep stopping (TRANSITION_PROTOCOL.md).

KG-001 was closed by `SPEC_STANDARD` version 2: the legacy top-level `adapters`
section was removed, call-site shape differences became caller-owned
requirements, and versioned backend IR now uses the closed structural `ref`
dictionary defined in §6.0.

## KG-002 — No conforming time-source form for a naive UTC clock read in a module-level function

Finding codes: fresh_timestamp_without_source, ambient_time_note

Recorded 2026-11-07 from the second client-portal assembly pass (issue #147,
branch `agent/client-portal` at `85895aad`). Open: it needs a decision of the
standard's owner before any recogniser is written.

The rule "a fresh timestamp has a source" (`design_closure_gaps`, admission
FA012) has no conforming form for a valid, running design. Client-portal's
accepted decision A28 reads the clock once per operation as naive
`datetime.utcnow()`, in module-level functions, and stores offset-naive UTC
(`rules.clock_policy`). Against the standard:

- §6.9 v1 emits aware `datetime.now(timezone.utc)` and counts as a source only
  as a `Clock` port retained by `__init__`; module-level functions have no
  `__init__`;
- §6.9 v2/v3 return an integer epoch, not a `datetime`;
- naming the business modules `time_source_policy` authorities is refused
  (`local_implementation_requires_deterministic_backend`, §6.8);
- `design_closure_gaps` knows `datetime` parameters, clock ports in
  `__init__` and authority modules only, and router IR §6.1 has no clock ref.

Options for the owner (none is implemented):

1. a §6.9 version whose module-level operation returns naive UTC `datetime`
   (one reading per call), consumed by the business modules as an import;
2. a router-IR clock ref (§6.1) that passes one reading per request as a
   `datetime` parameter, so the operations take `now: datetime`;
3. accept a `Clock` port — this changes the accepted service's behaviour and
   signatures, and is a product migration, not a conformance fix.

Until then a case cites `[known_gap: KG-002]` in the decision that owns its
clock. Its findings of the two codes keep stopping and are marked
`workbench_gap`; the author does not change the service to satisfy them.
