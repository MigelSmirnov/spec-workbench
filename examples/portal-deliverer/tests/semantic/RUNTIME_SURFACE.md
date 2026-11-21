# Portal Deliverer witness binding

These 19 semantic scenarios derive from the formal invariants and Required tests
of accepted decisions A1–A9 and A11 in `02_rules.md`. Their semantic oracle is
State 2. A10 is witnessed separately by the Workbench security gate.
The per-decision review and State 4 behavior graphs are in
`review/SEMANTIC_HANDOFF.md`. The test names preserve the accepted witness IDs;
a name does not broaden the invariant a test is allowed to assert.

## Status

Stage 7.1 semantic scenario review is recorded separately from runtime execution.
No fixture is shipped here: Factory owns `semantic_runtime`, as in cabinet-kernel.
Missing bindings must fail, never skip or return canned domain answers.
`semantic_closed` denotes the pre-code semantic handoff described by Stage 7.1,
not a successful generated-service execution. `factory_execution_verified` stays
false. Factory admission is checked separately and may still block export.

A9 needs the actual deployment route (not built yet according to A9).
A11 needs the actual calling flow and a Portal test instance. Those tests specify
the future integration contract; they provide no evidence that these integrations
exist today. Neither test may be bound to an implementation of the rule in the
fixture. The Portal visibility check similarly needs a real Portal instance.

## Fixture contract

Each test receives an isolated installation, confirmed connection for project
`b13c5547-fe49-439d-a7d8-0a02b2c19a7b`, fresh pre-created binary/state roots,
Europe/Madrid timezone, and a valid bearer credential. Operations run against
real files. Results are JSON-mode model dictionaries (including UUID/datetime
strings), with fields from the State 6 closures; refusals raise an exception
whose `code` is the refusal enum value. No fixture translates failed outcomes
into successes. The fixture supplies the operation context, not assertions.

Public operation bindings:

- `scan_project_photos(project_id)` → ScanResult.
- `deliver_project_photo(project_id, name, source_id)` → PlacementOutcome.
- `mark_photo_published(project_id, source_id, photo_id)` → MarkOutcome.
- `request(method, path, body=None, token=<installed credential>)` reaches the
  actual HTTP router; explicit `token=None` omits authentication. Returns a
  response with `status_code` and `text`.

Installation and observation capabilities:

- `source.put(name, bytes, mtime=<POSIX timestamp>)`, `source.remove(name)`,
  `source.symlink(name, relative_target)` prepare actual source entries.
- `source.snapshot()` records the full source tree: names, entry kinds, bytes,
  link targets, modes and nanosecond mtimes (not atimes).
- `durable_snapshot()` records binary files, placement and mark records with
  bytes, modes and nanosecond mtimes. It excludes project lock entries only;
  reads never create records. Compare snapshots directly without normalization
  that could hide changes.
- `trace_source_opens()` records every OS-level open during the delivery.
  Its `forbidden_opens(name)` selects opens of the rejected named file, a link
  target, or a folder beyond the first invalid segment. Valid traversal of a
  prefix and unrelated connections/state reads are permitted (INV-02). The
  selector uses recorded paths, not service internals or a claimed pass result.
- `read_binary(file_ref)` reads the actual stored bytes; `binary_count()` counts
  stored JPEG objects. Neither operation prepares or repairs objects.
- `record_bytes(kind, project_id, source_id)`, `write_record_bytes(...)`,
  `read_record(...)`, `record_count(...)` access actual ledger/published entries.
  Writing bytes is fault preparation only; it bypasses service validation.
- `connection.set_confirmed(bool)` rewrites the installation connection file.
  `connection.add_confirmed(project_id)` adds another isolated confirmed project.
- `fail_next_placement_write()` injects one storage write failure and restores
  normal storage on exit; it never synthesizes an operation result.
- `clock.set(naive_utc_iso)`, `clock.reset_reads()`, `clock.reads` bind and observe
  the service clock. They must count all service reads, including HTTP handlers.
- `bind_constant(name, value)` changes the generated data-provider constant
  before the next call. The encoder is real; its result is not stubbed.
- `trap_outbound_connections()` returns a list of attempted network connections
  from the service process; the HTTP test client connection is excluded.
- `private_paths` lists the absolute source root, binary root and state root.
- `concurrent_deliver(project_id, name, source_id, workers, separate_processes)`
  launches calls behind a barrier against shared real storage, returns operation
  JSON results, and fails on timeout/crash. `separate_processes=True` requires
  independent processes, not threads.
- `concurrent_mark(project_id, source_id, photo_ids, separate_processes)` does
  the same for marks; domain refusals are returned as `{"code": <value>}`.
- `portal.publish(project_id, publication)` returns the real Portal photo id;
  `portal.client_photo_ids(project_id)` observes its client-facing photo list;
  `portal.set_visible(project_id, photo_id, bool)` calls the staff operation.
  `portal.download_staff_photo(project_id, photo_id)` returns the bytes of the
  real Portal download, for the metadata invariant.
  `portal.trace_publish_calls()` records actual publication attempts.
- `portal.replace_staff_photo_dates(project_id, dates)` seeds an isolated Portal
  store, including legacy offset dates, without modifying production data.
- `deployment.check(osv_outcome)` runs the actual deployment admission route
  without deploying; only the OSV source is controlled. `vulnerable` supplies
  an advisory matching an installed distribution, `unavailable` makes the scan
  fail. Returns admission `allowed`; the witness requires refusal for both
  outcomes, without inferring approval from a clean dependency check.
- `calling_flow.deliver(project_id)` runs the real caller from its date preflight
  through its normal work. It exposes the observed `preflight_passed` decision
  and `repair_project_id` from its owner-facing report. Passing preflight does
  not imply any particular photo was selected or published.
  `trace_delivery_calls()` observes actual deliverer invocation by that caller.

## Verification

`python3 -m pytest --collect-only -q -p no:cacheprovider examples/portal-deliverer/tests/semantic`
collects exactly 19 named tests. Full execution requires the Factory binding.
Names after `test_` exactly match the 19 `verification:deliverer_*` tags.
Collection is not semantic closure, execution evidence or Factory admission.
