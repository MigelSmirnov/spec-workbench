# `semantic_runtime` — the fixture surface the witness tests use

The tests in this directory are the witnesses of Registry's accepted
decisions (`[witness: verification:registry_aNN_*]` in the Required tests of
`02_rules_*.md`). They are written before Registry is generated and never
rewritten to fit it. The Factory project `registry` supplies the
`semantic_runtime` pytest fixture and binds each call below to the generated
code; the assertions stay as written.

This file is the one list of that surface. A test calls nothing that is not
listed here; a test that needs a new call or capability adds it here first,
in the same change, with the State 5 operation or State 6 model it reaches.
Which capabilities work from outside the process and which need a seam
inside it is `review/CAPABILITIES.md`.

Why a protection is witnessed even where the first release cannot reach it:
the owner's data-protection matrix (`sources/privacy_requirements_20261123.md`)
asks of every measure "which test confirms it". A measure a Registry without
it would also pass is not confirmed, so such a measure is shown on a test
release (`configure_release`), not left unwitnessed (owner's direction of
2026-11-24: the data-protection requirements decide).
The v1 Registry is no reference for any expected value here.

## Conventions

- **Two surfaces, as Registry has.** A service reaches Registry only through
  the service API (`service_api.serve_service_request`, State 5); the owner
  only through the owner interface (`owner_interface.serve_owner_request`).
  The fixture drives both over their real listeners, started by
  `instance_lifecycle.start_instance`. Nothing is called below the surfaces
  except the named seams of "Capabilities": a test that needs a module's own
  answer is a test of the wrong level.
- **Answers are the wire answers.** A call returns the answer as the service
  API writes it (`service_api._write_service_answer`, State 6/7): a dict of
  the answer's own fields, each nested model a dict of its fields, an
  instant as its ISO text with `Z`, a Decimal as its text, an enum as its
  value string. The fixture adds `"answer_kind"` at the top level only, the
  State 6 variant name without `Answer` in snake case (`project_card`,
  `refused`, …), so a test can tell the variant. Nested views carry no
  `view_kind` (State 5 `serve_service_request`: the wire carries none); a
  test tells an anonymised project or an erased customer by its fields.
  `validate` and `context` return the bare view as the wire carries it
  (R0-04), not nested under a key. The owner call returns the same
  projection of the answer `operations.perform_owner_operation` gave for the
  request the fixture sent (see `owner`), never parsed out of HTML.
- **Refusals are answers.** A refusal does not raise: it is the answer
  `{"answer_kind": "refused", "code": ..., "stage": ..., "failures": [{"kind":
  ..., "path": [...]}]}` — State 6 `RefusedAnswer.refusal` flattened, as the
  wire writes it — with the codes, stages and kinds of State 5, "Closed set
  of refusal codes". Tests compare codes and kinds as the strings State 5
  names (`not_found`, `unknown_project`) and the stage as its number.
- **Fresh instance.** Each test gets a new instance: an empty store in a
  temporary directory, an empty backup location, the configuration below,
  started with both listeners and stopped after the test.
- **Configuration the fixture supplies.** Distinct secrets of exactly the
  imported `SECRET_MIN_BYTES` bytes and more for each of the four service
  tokens, the owner credential and the backup key; both listeners on
  loopback ports; store and backup location apart. `configure(**settings)`
  before `start()` replaces any of them (State 6 `RuntimeSettings` field
  names), and `configure(item=None)` leaves that item unset; a test that is
  about the configuration starts the instance itself.
- **The owner's session.** `owner(...)` signs in by itself only when no
  owner session was opened since the instance last started. Otherwise it
  sends the session it holds as it is — an expired, signed-out or ended one
  included — and returns that request's answer, a refusal among them; a new
  session comes only from `sign_in()`. So a test that lets a session reach
  a limit (A13: 30 minutes idle, 8 hours) and goes on as the owner calls
  `sign_in()` first. `sign_in()` while a session is open opens a second one
  and makes it the held one.
- **Time.** The instance's two clocks are the fixture's.
  `clock.set(iso)` and `clock.advance(seconds=…, minutes=…, hours=…,
  days=…)` move the recorded clock (`clock.recorded_now`) and the monotonic
  clock (`clock.monotonic_reading`) together. `clock.suspend(seconds)` is a
  host or VM suspension: it moves both too, because the monotonic clock
  counts suspended time (A13 rule 2); it exists so a test names what it
  shows. `clock.shift_wall(seconds=…, minutes=…, hours=…, days=…)`, negative
  values allowed, is a change of the wall clock: it moves the recorded clock
  only (A13 rule 2: a change of the wall clock does not move the monotonic
  one). The default start instant is 2026-01-05T09:00:00Z. Neither clock
  moves by itself.
- **Passes run when asked.** The fixture never lets the passes of
  `instance_lifecycle` run on their own: `run_session_pass()` makes one call
  of `owner_sessions.end_expired_sessions` and returns how many sessions it
  ended (its State 5 output); `run_backup_look()` one call of
  `backups.run_daily_backup_if_due`, waiting for a run it starts to end.
- **Request ids.** A create needs a request id (A01 rule 1). Tests pass it
  explicitly; `new_request_id()` gives a fresh printable one.
- **Concurrency.** `service(...)`, `owner(...)` and `owner_confirm(...)` are
  safe to call from several threads at once, each its own HTTP request, also
  while `run_backup_look()` runs. A race shown this way is caught when the
  threads overlap; the tests use a barrier and repeat rounds, and each
  review names such a witness as probabilistic.

## Calls

| call | reaches | what the fixture does |
|---|---|---|
| `service(name, operation, inputs=None, kernel_session=None, token=…)` → answer | `service_api.serve_service_request` → `operations.perform_service_operation` | POSTs one envelope `{"operation", "inputs"}` with the service's token as `Authorization: Bearer`, and `kernel_session` in the header the imported `SERVICE_AGENT_SESSION_HEADER` constant names; `name` is a `ServiceName` value; `token=` overrides the token (`None` sends none). With no service listener open the connection fails and the call raises `OSError` |
| `service_raw(body: bytes, headers: dict)` → `(status, body_bytes, headers)` | `service_api.serve_service_request` | sends exactly what it is given |
| `owner(action, target=None, stated_version=None, confirm=True, csrf=…, **values)` → answer | `owner_interface.serve_owner_request` → `operations.perform_owner_operation` | as the owner, in the held session (see "The owner's session"): sends the action's row of the imported `OWNER_ACTIONS` constant with the session's CSRF value; `csrf=` sends that value instead and `None` sends none (no `OWNER_CSRF_FIELD`; State 6 `OwnerRequest.csrf_value`, checked by `owner_sessions.admit_owner_request`, A13 rule 5); `values` are `OwnerValues` fields (State 6), a model as a dict, an enum as its value; for an action that needs a confirmation step (A13 rule 6) it first asks for the step and submits its value when `confirm` is true, returning the confirmed answer; `confirm=False` returns the step's answer |
| `owner_confirm(step_answer, value=None)` → answer | same | submits a shown confirmation step in the session that was held when the step was shown, with its own value unless `value` is given |
| `owner_upload(content: bytes, declared_length=…)` → answer | same, `upload_import` | the multipart body State 5 names, CSRF field first; `declared_length=` sets the declared length of the file part (default: its true length) |
| `owner_http(method, path, query=None, form=None, cookie=…, raw_body=None)` → `(status, html, headers)` | `owner_interface.serve_owner_request` | one raw HTTP request; `cookie=` defaults to the held session's; for A13 and A19 tests that are about the page, the cookie or the CSRF value |
| `sign_in(credential=…)` → answer / `sign_out()` → answer | owner `sign_in` / `sign_out` | `credential=` defaults to the configured owner credential |
| `owner_session()` / `use_owner_session(s)` | — | the held owner session, an object with `.cookie` and `.csrf`, and switching to another one, for tests with two sessions |

## Capabilities

| capability | for | reaches |
|---|---|---|
| `configure(**settings)`, `start()` → `None` or the diagnostic line, `stop()`, `restart()` | A17 start checks and order; a restart ending owner sessions (A13 rule 2). After a failed `start()` the instance is stopped and can be configured and started again | `instance_lifecycle.start_instance`, `configuration.load_configuration` → `runtime_settings.load_runtime_settings` |
| `configure_environment(variables: dict[str, str])` | A17 rule 2: the next start sees exactly these variables beside the host's own non-`REGISTRY_` ones, and the fixture's configuration is not applied | State 6 `config.runtime_environment_variables` |
| `configure_release(**constants)` | after `stop()` and before `start()`: the instance runs over the same store and backup location on a test release whose named data-provider constants hold the given values. For measures the first release cannot reach: the rights rows and the class check (A09 rules 1, 4 and 6: `SERVICE_RIGHTS`, `SERVICE_HIGHEST_CLASSES`, `PERSONAL_DATA_FIELDS`), the vocabulary by release (A22, A06 rule 3, `ARTIFACT_TYPE_OWNERS`) | the data provider's constants, State 6 `ServiceHighestClass`, `PersonalDataField`, `ArtifactTypeOwner`; a test release as `60_contracts.md`, "Test seams", names it |
| `diagnostics()` → list of lines | what the instance wrote to standard error since the fixture started it (A17 rule 2, A18 rule 5) | State 5 Conventions, "Diagnostics" |
| `clock.set`, `clock.advance`, `clock.suspend`, `clock.shift_wall` | every limit of A13, A15, A18 | `clock.recorded_now`, `clock.monotonic_reading` |
| `run_session_pass()` → int, `run_backup_look()` | A13 rule 2, A18 | `owner_sessions.end_expired_sessions`, `backups.run_daily_backup_if_due`; the instance's own passes held by replacing `instance_lifecycle._start_passes`, a run's end known by wrapping `backups._run_backup` (`60_contracts.md`, "Test seams") |
| `backup_files()` → list of names in the backup location; `backup_bytes(name)` → the file's bytes; `read_backup(name, key=None)` → `{table: rows}` of the decrypted snapshot, read with the configured key or `key=`, raising when it cannot be decrypted | A18 | State 6 "A backup file", `BackupRecord` |
| `restore(name)` → `None` or the diagnostic line | A18 rule 8: stops the instance, puts the decrypted snapshot in place of the store (the owner's restore, outside Registry, R0-89) and starts again with the same configuration | `instance_lifecycle.start_instance`, `store.open_store` |
| `store_rows(table)` → list of dicts keyed by column, `record` being the model's JSON; works while the instance is stopped; read through a read-only SQLite connection | "changes nothing" in a refusal (A04 rule 4, A14 rule 2) | the tables of `70_persistence_closure.json` |
| `export_file(projects=…, rooms=…, pointers=…)` → bytes in the import file format, each record a dict of its fields (State 6 `ExportFile`; it holds no customers) | A16 | State 6 "The import file" |
| `faults.fail_store_call(method)` | the next call of that `StoreRepository` method (State 6, `70_persistence_closure.json`, e.g. `insert_audit_entry_row`, `insert_pointer_row`, `update_pointer_row`, `insert_migration_closure_row`) raises a driver error once; `store.run_in_transaction` rolls back and the operation answers `internal_error` / `transaction_failed` | A07 rule 2, A14, A15, A16 rule 5 |
| `faults.fail_next_backup_check(kind)` | `kind` `"integrity"`: the next run's snapshot copy fails `store.check_store_file` though it decrypts; `"sequence_mismatch"`: its M12 `AuditSequence` differs from the recorded number (A18 rule 4 step 2) | `store.copy_store_snapshot`, `store.check_store_file`; `"integrity"` by replacing `store._integrity_ok` (`60_contracts.md`, "Test seams") |
| `faults.hold_backup_snapshot()` → gate with `wait_fixed(timeout)` → bool and `release()` | the next backup run's copy waits after its first read, which fixes the snapshot, until released: a backup taken during a write (A18 rule 3) | `store.copy_store_snapshot` |

The store, the backup location and the listeners are the instance's; a test
never writes them directly, except the files an A17 test places in its own
`tmp_path` before a start it makes itself.
