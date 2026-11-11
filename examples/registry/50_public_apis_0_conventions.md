# State 5 — Registry public module operations: conventions

## Status

Draft of 2026-11-01. One public operation per State 3 capability a reviewed
State 4 flow uses, each proven by the flows `50_api_plan.json` names. An
operation is what another module, a surface's client or the host may call;
everything else a module does is hidden. The operations are kept by module
group in `50_public_apis_1_foundation.md`, `50_public_apis_2_sessions.md`,
`50_public_apis_3_records.md`, `50_public_apis_4_import_backups.md` and
`50_public_apis_5_surfaces.md`; this file holds the conventions every one of
them follows. Inputs and outputs name State 1 models and projections; field
types and Python signatures are State 6's.

## Conventions every operation follows

- **One transaction, handed down.** Every operation of a domain module —
  `customers`, `projects`, `artifact_pointers`, `agent_sessions`,
  `migration_import`, `audit_log` — that reads or writes the store takes the
  transaction `operations` opened through `store.run_in_transaction` or
  `store.read_in_transaction` as an input, and never opens, commits or
  rolls back one (State 3, "One action, one transaction"). A write
  transaction holds the store's one write lock from its beginning; every
  agent-authority call runs in one, a read included (A10 rule 6).
- **The action's instant and today.** An operation that records an instant
  or compares a date takes the action's instant and today's date as inputs:
  `operations` reads the instant once with `clock.recorded_now` when the
  transaction begins and derives today from it with `clock.today_in_utc`
  ("Time"); the operation reads no clock. The exceptions are named: `owner_sessions` and
  `instance_lifecycle`, for its passes, read `clock.monotonic_reading`, `backups` reads `clock.recorded_now` for its
  look, and `store` reads it at a backup copy's first read.
- **The acting principal.** An operation that records who acted — a
  pointer's publisher or withdrawer, an audit entry — takes the acting
  principal (M07) from `operations`: the owner, a service, or Kernel for the
  agent naming the session (R0-53). No module below `operations` determines
  it.
- **Minted identities.** An operation that writes a record with an identity
  Registry mints asks `random_values.mint_identity` and checks, in the
  transaction it was handed, that its model holds no record of that identity,
  minting again when it does; a collision never refuses an action. A
  confirmation id is not checked ("Minted identities").
- **Stages.** An operation that checks stages (3) to (6) of A04 rule 6 checks
  them in that order and answers the first failing stage with every failure
  of that stage (A04 rule 6): one entry for each failing field of the
  request, or each failing record or identity it names, with its kind and
  the path that names it — a field by its name and the names and list
  positions of the inputs that hold it, such as the alias of the second
  pick, a record by its kind and its id or position. Entries are ordered by
  kind, in the order the operation's Errors list the kinds, and within one
  kind by path, compared element by element from the start: a name by
  Unicode code point, a list position as a number, a shorter path first.
  Two failures are answered
  alone, every other check being moot: the import's closure, `import_closed`
  (State 4, `flow:import_from_vps`), and then a confirmation's bound upload
  no longer kept, `file_not_kept`, which leaves no bytes to check again. Stages (1) and (2) are `operations`'. A refusal
  changes no record and writes no entry (A14 rule 2); what it does to an
  owner session's runtime state is A13's, stated where an operation makes it.
- **Repeats.** A transition to the state a record is in answers the record
  unchanged with `changed: false` (A05); a create's repeat answers the
  existing record with `changed: false` (A01 rule 4). Every operation that
  may be accepted without a change — a repeat, an equal correction, a
  transition to the state a record is in — answers `changed`, because
  `operations` appends the entry and mints a confirmation id only when it
  changed state (A14 rules 1, 3, 5); one that changes state whenever it is
  accepted answers no `changed`.
- **What answers never carry.** No answer carries a stored request id: it
  is kept with its record and never answered (A01 rule 9). A create form the
  owner interface renders carries a new one, for its submission (A01 rule
  1); that is not a stored record's. The projections an
  operation's Outputs name are complete: a fact not listed there is not in
  the answer.
- **Erased records answer, they do not refuse.** A read of an anonymised
  project or an erased Customer, where State 0 says it "answers that it was
  erased" (R0-62, M04), returns the erased form of the answer, not a
  refusal: for an anonymised project its `project_id`, its status
  `archived` and the anonymised mark (M01, R0-87); for an erased Customer
  its `customer_ref`, the erased mark and its instant (M04); nothing else.
- **Order.** Every list an operation reads from the store is in the order A06
  declares for it, as `store` reads it; no module sorts stored records itself
  (A06, State 3).
- **Checks answer, they do not refuse.** An operation that only answers a
  question — `customers.check_customer_eligible`,
  `projects.validate_project_reference`, `given_values.*`,
  `service_access.service_may_call` — returns its answer, and its caller
  turns it into a refusal of the right stage.
- **Locks of an owner request.** `owner_sessions.admit_owner_request` runs
  the request's step under the locks it takes and releases them when the
  step returns, on every path — an answer, a refusal or a failure — as
  `store.run_in_transaction` does its transaction. Every request is checked
  at its arrival; a change, or any request touching an uploaded file, then
  takes its place on the session's lock — the latter after waiting for the
  import lock, granted in the order requests asked for it — and the session's
  lock is granted in the order places were taken (A13 rule 2, A16 rule 2).
- **Diagnostics.** A diagnostic — a stopped start's, a failed backup run's —
  is one line on the process's standard error, which the host keeps; it
  names the failure and never a value (A17 rule 2, A18 rule 5).
- **Passes.** `instance_lifecycle` makes each of its two passes every
  interval from the start, as A13 rule 2 says of the session pass: the n-th
  call is due when `clock.monotonic_reading` shows n intervals since serving
  began, the first one interval after; a call due while the previous call of
  the same pass is still running is not made, and the pass waits for the
  next due one; deadlines that pass during a suspension of the host or a
  long call are not made up. Each time a call returns, the pass takes one
  reading and waits for the first deadline at or after it; when its wait
  ends — on time, or late after a suspension — it makes one call, whatever
  deadlines its wait passed, and takes its next reading when that call
  returns. The passes run apart, neither waiting for the
  other. A look of the backup pass answers at once: a run it starts goes on
  apart from the pass, so the looks go on every interval while a run goes
  on, and a look during a run starts none (A18 rule 1).
- **Pure operations.** An operation whose State impact says "pure" reads no
  record, no clock and no environment and touches nothing.

## Constants each module imports

`module:data_provider` has no operation: it exports constants, and a module
that names one imports it (SPEC_STANDARD §6.10, §15.3.1). The authority for
these imports is the specification's `imports.module_internal`, as for every
internal import (SPEC_STANDARD §7): State 6 writes each row below as the
entry `module_internal[<consumer>]["data_provider"]`, the listed symbols and
no other. This table is the design those entries are written from, not a
second authority beside them. The values are the data closure's.

| consumer | constants it imports from `data_provider` |
|---|---|
| `random_values` | `SECRET_MIN_BYTES` |
| `given_values` | `REQUEST_ID_MAX_CHARACTERS`, `ALIAS_MAX_CHARACTERS`, `OBJECT_FLOOR_AREA_MIN_EXCLUSIVE`, `OBJECT_ROOMS_MIN` |
| `configuration` | `SERVICE_RIGHTS`, `SECRET_MIN_BYTES` |
| `store` | `STORE_VERSION`, `STORE_TEMPORARY_SUFFIX` |
| `audit_log` | `RELEASE_VERSION`, `CONTRACT_VERSION` |
| `service_access` | `SERVICE_RIGHTS` |
| `owner_sessions` | `OWNER_SESSION_MAX_HOURS`, `OWNER_SESSION_IDLE_MINUTES`, `SIGN_IN_WINDOW_MINUTES`, `SIGN_IN_REFUSAL_LIMIT`, `SIGN_IN_LOCKOUT_MINUTES`, `CONFIRMATION_VALID_MINUTES` |
| `artifact_pointers` | `ARTIFACT_TYPE_OWNERS` |
| `migration_import` | `ARTIFACT_TYPE_OWNERS`, `IMPORT_FILE_MAX_BYTES` |
| `backups` | `BACKUP_KEPT_PREFIX`, `BACKUP_TEMPORARY_PREFIX`, `BACKUP_DAILY_TIME_UTC`, `BACKUP_RETENTION_HOURS`, `RELEASE_VERSION` |
| `instance_lifecycle` | `OWNER_INTERFACE_LISTEN_ADDRESS`, `SERVICE_API_LISTEN_ADDRESS`, `SESSION_PASS_SECONDS`, `BACKUP_LOOK_SECONDS` |

Likewise `module_internal["configuration"]["runtime_settings"]` holds
`load_runtime_settings`, which `configuration` calls itself, once per start;
`instance_lifecycle` does not call it. And
`module_internal["instance_lifecycle"]["clock"]` holds `monotonic_reading`,
by which it times its passes (Conventions, "Passes").

## Closed set of refusal codes

A refusal is a code, the stage of A04 rule 6 it belongs to (`models`, State
3), and the list of the kinds that failed in that stage. The codes are
distinct where a caller acts on the difference; the kinds are a closed set
the owner interface renders and State 6 declares as `models`' vocabulary.

| code | stage | kinds | who acts on it |
|---|---|---|---|
| `unauthenticated` | (1) | `no_valid_token` — missing, unknown or wrong, one answer (A17 rule 7); `no_owner_session` — none, ended or expired (A13 rule 2); `sign_in_refused` — wrong or missing credential or a lockout, one answer (A13 rule 4) | the service fixes its token; the owner signs in |
| `not_permitted` | (1) | `outside_service_rights` (A09 rule 3); `csrf_refused` (A13 rule 5); `answer_above_class` (A09 rule 4) | the caller is not allowed this call |
| `confirmation_refused` | (1) | `confirmation_not_pending` — the session holds no pending value: never shown, used up or cleared; `confirmation_other_value` — another value while the pending one is valid, which stays; `confirmation_bound_elsewhere` — the pending value given for another action, target, revision or inputs, now used up; `confirmation_expired` — cleared (A13 rule 6) | the owner submits the pending step again, or has it shown again |
| `not_found` | (2), (3) | `agent_call_refused` — an unregistered session, a project outside the set, none active, an unknown pointer for Kernel: one answer (A10 rule 3, A08 rule 7); `unknown_project`, `unknown_customer`, `unknown_room`, `unknown_pointer`, `unknown_session` (State 0) | the caller re-reads |
| `invalid_request` | (4) | `missing_value` (A02 rule 1); `malformed_request_id` (A01 rule 1); `outside_closed_list` (A19 rule 3) — a value outside its enumeration, an
object kind or a customer language included (A02 rule 4); `outside_form` — a
present value outside the form State 1 declares: an alias over the imported
`ALIAS_MAX_CHARACTERS` constant, a floor area not greater than the imported
`OBJECT_FLOOR_AREA_MIN_EXCLUSIVE`, a number of rooms that is not a whole
number of at least the imported `OBJECT_ROOMS_MIN`, a floor that is not a
whole number (A02 rule 4); `duplicate_pick` — a project, or a Customer's v1 value, given twice (A16 rule 1); `unknown_artifact_type` (A22 rule 5); `date_after_today` (A15 rule 3, R0-84); `file_too_large`; `file_unreadable` — bytes that do not parse as the format States 5 and 6 declare, or an upload whose body fails or ends before its declared length; `file_malformed` — a file that parses but holds two projects with one id, or a project whose id or status is missing or not of its field's shape; a status outside its vocabulary is not this, but a malformed record of a pick (A16 rule 4) (A19 rule 4, A16 rule 3) | the caller fixes the request |
| `stale` | (5) | `stale_revision` (A04 rules 2, 3); `stale_access_version` (A12 rule 3) | the owner reads again |
| `refused` | (6) | `archived`, `active` (erasing an active project), `anonymised`, `erased`, `customer_restricted`, `customer_ended`, `customer_erased`, `conflict` (A01 rule 5), `not_granted`, `not_pending`, `withdrawn`, `superseded`, `import_closed`, `file_not_kept`, `mapping_not_clean`, `no_picks` | the owner reads the record's state |
| `internal_error` | — | `transaction_failed`: a store transaction did not commit, nothing changed (A04 rule 4) | the caller reads again before repeating |

`module:operations` returns a refusal to its surface unchanged; the service
API writes it in its wire format (States 5 and 6) and the owner interface
renders it, a refusal of stage (1) for a request with no valid session as the
sign-in page. No refusal names a secret, a credential or a value given as
`personal_data` (A13 rule 7, A17 rule 6).
