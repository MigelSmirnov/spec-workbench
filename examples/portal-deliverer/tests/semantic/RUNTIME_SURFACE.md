# Portal Deliverer witness binding

These 19 tests are authored against the accepted A1–A9 and A11 decisions of
`02_rules.md`, adapted from Factory `prototypes/portal_deliverer/test_deliverer.py`.
They do not import that prototype or implement delivery logic. State 2 decisions
are unchanged. A10 is witnessed separately by the Workbench security gate.

## Status

Authored, collected, not executed against a generated service. No fixture is
shipped here: Factory owns `semantic_runtime`, as in cabinet-kernel. Missing
bindings must fail, never skip or return canned domain answers. The export
manifest deliberately remains `authored_unbound`, not `semantic_closed`.
Do not export until review and real runtime binding are complete.

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
- `trace_source_opens()` is a context manager returning a list of attempted
  source file opens (including symlink target reads), observed at the OS boundary.
  Opening trusted traversal directories is excluded; opening a directory past
  a rejected name segment must be included.
- `read_binary(file_ref)` reads the actual stored bytes; `binary_count()` counts
  stored JPEG objects. Neither operation prepares or repairs objects.
- `record_bytes(kind, project_id, source_id)`, `write_record_bytes(...)`,
  `read_record(...)`, `record_count(...)` access actual ledger/published entries.
  Writing bytes is fault preparation only; it bypasses service validation.
- `connection.set_confirmed(bool)` rewrites the installation connection file.
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
- `portal.replace_staff_photo_dates(project_id, dates)` seeds an isolated Portal
  store, including legacy offset dates, without modifying production data.
- `deployment.check(osv_outcome)` runs the actual deployment admission route
  without deploying; only the OSV source is controlled. `vulnerable` supplies
  an advisory matching an installed distribution, `unavailable` makes the scan
  fail, and `clean` supplies a fresh empty snapshot. Returns `allowed` and
  `deployment_started`; the latter must always be false in this check mode.
- `calling_flow.deliver(project_id)` runs the real caller from its date preflight
  through scan/delivery/Portal publication/mark, returns `allowed`.
  `trace_delivery_calls()` observes actual deliverer invocation by that caller.

## Verification

`python3 -m pytest --collect-only -q -p no:cacheprovider examples/portal-deliverer/tests/semantic`
collects exactly 19 named tests. Full execution requires the Factory binding.
Names after `test_` exactly match the 19 `verification:deliverer_*` tags.
Collection is not semantic closure, execution evidence or Factory admission.
