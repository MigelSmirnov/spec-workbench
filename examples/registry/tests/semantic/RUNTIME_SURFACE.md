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

## Conventions

- **Two surfaces, as Registry has.** A service reaches Registry only through
  the service API (`service_api.serve_service_request`, State 5); the owner
  only through the owner interface (`owner_interface.serve_owner_request`).
  The fixture drives both over their real listeners, started by
  `instance_lifecycle.start_instance`. Nothing is called below the surfaces:
  a test that needs a module's own answer is a test of the wrong level.
- **Answers are the wire answers.** A call returns the answer as the service
  API writes it (`service_api._write_service_answer`, State 6/7): a dict of
  the answer's own fields, each nested model a dict of its fields, an
  instant as its ISO text with `Z`, a Decimal as its text, an enum as its
  value string. The fixture adds `"answer_kind"`, the State 6 variant name
  without `Answer` in snake case (`project_card`, `refused`, …), so a test
  can tell the variant. The owner call returns the same projection of the
  answer `operations.perform_owner_operation` gave for the request the
  fixture sent (see `owner`), never parsed out of HTML.
- **Refusals are answers.** A refusal does not raise: it is the answer
  `{"answer_kind": "refused", "code": ..., "stage": ..., "failures": [{"kind":
  ..., "path": [...]}]}` with the codes, stages and kinds of State 5,
  "Closed set of refusal codes". Tests compare codes and kinds as the
  strings State 5 names (`not_found`, `unknown_project`).
- **Fresh instance.** Each test gets a new instance: an empty store in a
  temporary directory, an empty backup location, the configuration below,
  started with both listeners and stopped after the test.
- **Configuration the fixture supplies.** Distinct secrets of exactly the
  imported `SECRET_MIN_BYTES` bytes and more for each of the four service
  tokens, the owner credential and the backup key; both listeners on
  loopback ports; store and backup location apart. `configure(**settings)`
  before `start()` replaces any of them (State 6 `RuntimeSettings` field
  names); a test that is about the configuration starts the instance itself.
- **Time.** The instance's two clocks are the fixture's: `clock.set(iso)`
  and `clock.advance(seconds=…, minutes=…, hours=…, days=…)` move the
  recorded clock (`clock.recorded_now`) and the monotonic clock
  (`clock.monotonic_reading`) together; `clock.suspend(seconds)` moves the
  recorded clock only (a host suspension). The default start instant is
  2026-01-05T09:00:00Z.
- **Passes run when asked.** The fixture never lets the passes of
  `instance_lifecycle` run on their own: `run_session_pass()` makes one call
  of `owner_sessions.end_expired_sessions`, `run_backup_look()` one call of
  `backups.run_daily_backup_if_due`, waiting for a run it starts to end.
- **Request ids.** A create needs a request id (A01 rule 1). Tests pass it
  explicitly; `new_request_id()` gives a fresh printable one.

## Calls

| call | reaches | what the fixture does |
|---|---|---|
| `service(name, operation, inputs=None, kernel_session=None, token=…)` → answer | `service_api.serve_service_request` → `operations.perform_service_operation` | POSTs one envelope `{"operation", "inputs"}` with the service's token as `Authorization: Bearer`, and `kernel_session` in the header the imported `SERVICE_AGENT_SESSION_HEADER` constant names; `name` is a `ServiceName` value; `token=` overrides the token (`None` sends none) |
| `service_raw(body: bytes, headers: dict)` → `(status, body_bytes, headers)` | `service_api.serve_service_request` | sends exactly what it is given |
| `owner(action, target=None, stated_version=None, confirm=True, **values)` → answer | `owner_interface.serve_owner_request` → `operations.perform_owner_operation` | as the signed-in owner (it signs in first when no session is open): sends the action's row of the imported `OWNER_ACTIONS` constant with its CSRF value; `values` are `OwnerValues` fields (State 6), a model as a dict, an enum as its value; for an action that needs a confirmation step (A13 rule 6) it first asks for the step and submits its value when `confirm` is true, returning the confirmed answer; `confirm=False` returns the step's answer |
| `owner_confirm(step_answer, value=None)` → answer | same | submits a shown confirmation step, with its own value unless `value` is given |
| `owner_upload(content: bytes, declared_length=…)` → answer | same, `upload_import` | the multipart body State 5 names, CSRF field first |
| `owner_http(method, path, query=None, form=None, cookie=…, raw_body=None)` → `(status, html, headers)` | `owner_interface.serve_owner_request` | one raw HTTP request; `cookie=` defaults to the open session's; for A13 and A19 tests that are about the page, the cookie or the CSRF value |
| `sign_in(credential=…)` → answer / `sign_out()` → answer | owner `sign_in` / `sign_out` | `credential=` defaults to the configured owner credential |
| `owner_session()` / `use_owner_session(s)` | — | the open owner session (cookie and CSRF value) and switching to another one, for tests with two sessions |

## Capabilities

| capability | for |
|---|---|
| `configure(**settings)`, `start()` → `None` or the diagnostic line, `stop()`, `restart()` | A17 start checks and order; a restart ending owner sessions (A13 rule 2) |
| `clock.set`, `clock.advance`, `clock.suspend` | every limit of A13, A15, A18 |
| `run_session_pass()`, `run_backup_look()` | A13 rule 2, A18 |
| `backup_files()` → list of names in the backup location; `read_backup(name)` → its decrypted record, read with the configured key | A18 |
| `store_rows(table)` → rows of the store, read from its file through a read-only SQLite connection, for a test that shows nothing else changed | "changes nothing" in a refusal (A04 rule 4, A14 rule 2) |
| `export_file(projects=…, rooms=…, pointers=…, customers=…)` → bytes in the import file format (State 6 `ExportFile`) | A16 |

The store, the backup location and the listeners are the instance's; a test
never writes them directly.
