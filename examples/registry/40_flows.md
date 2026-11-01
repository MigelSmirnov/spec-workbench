# State 4 — Registry reviewed flows

## Status

Draft of 2026-11-01. The eleven flows of the owner-accepted
`40_flow_plan.json` (owner, 2026-11-01), walked against the State 3 ownership
of `30_modules.md`. They name who triggers, what crosses each boundary, who
decides next, who produces each result and each failure. They do not freeze
State 5's public operations, their inputs or their refusal codes; a capability
named here is a State 3 candidate, and its shape is State 5's.

Every request of a caller enters through one of the two surfaces, which decide
nothing ("Explicit exclusions", R0-29): the service API reads the token and the
request and hands them to `operations`; the owner interface reads the cookie,
the CSRF value and the form and hands them to `operations`, and renders its
answer as escaped text (A19 rules 1, 2). `operations` runs A04 rule 6: stage
(1) through `service_access` for a service or `owner_sessions` for the owner,
stage (2) through `agent_sessions` for agent authority, and hands the action
to the module that owns its record for stages (3) to (6), which answers every
failure of the first failing stage. A refusal at stage (1) or (2) records
nothing and reaches no module of stages (3) to (6); the one lookup stage (2)
makes of another module is a withdrawal's pointer, resolved to its project
before the session's check (A08 rule 7, `flow:publish_and_withdraw_pointer`).

Every action that changes the store is one transaction `operations` opens
through `store` (A04 rule 4), taking the one write lock when it begins; every
agent-authority call takes it too, a read included (A10 rule 6). Inside it
`operations` reads the action's one instant and today's date from `clock` and
hands them on ("Time"), the record's module writes, and `operations` appends
the one audit entry when the action changed state and M09 lists it (A14
rule 1), naming the release and contract versions, and commits once. A
transaction that fails changes nothing (A04 rule 4) and writes no entry; the
caller is answered that the action failed, in the form State 5 declares. A
read runs in one read transaction of `store` and records nothing (A14 rule 4).
A refusal changes no record and writes no entry (A14 rule 2); what a refused
owner request still does to its session's runtime state — the arrival
restarting the 30 minutes, a confirmation value used up or cleared — is A13's
and stated in the flows that make it.

Every identity Registry mints comes from `random_values`. A record's
identity is checked by the writing module against its model and minted again
on a collision; a confirmation id names no record and is not checked against
earlier ones ("Minted identities"). Every answer's disclosure class is the highest of its facts'
(State 1, "Disclosure classes by field"); `operations` refuses a service's
answer whole when it is above the service's highest class (A09 rule 4), and no
owner answer is refused for its class. A flow references a module or a
capability only where its own steps use it beyond these rules.

## `flow:start_instance`

### Trigger

The host starts the Registry process — first start, a restart, or a start
after the owner put a store in place of a lost one (A18 rule 8). Nothing of a
previous process survives in memory: no owner session, no sign-in count or
lockout, no remembered backup date (A13 rules 2, 3; A18 rule 1).

### Boundary

`module:instance_lifecycle` owns the order of the start and serves nothing
until every check passed (A17 rule 2); it decides no check.
`module:configuration` owns reading the `REGISTRY_` variables and every check
of A17 that needs no file. `module:backups` owns the probe of the backup
location (A17 rule 2, A18 rule 5). `module:store` owns opening or making the
store and its integrity and version checks (A17 rule 5).
`module:release_declarations` gives the services a token is required for, the
store version and temporary-name suffix, and the backup prefixes; nothing of
them is read from the configuration. `module:service_api` and
`module:owner_interface` are the two surfaces; `module:owner_sessions` and
`module:backups` own the passes the running instance makes.

Crossing models: the environment's `REGISTRY_` items enter
`module:configuration` and leave as the loaded configuration — locations,
the owner credential, the backup key and the service tokens, or none of the
tokens for an owner-only start — or as one diagnostic naming the failed item;
each secret then goes only to the module that uses it ("Secrets never leave").
The store's location enters `module:store` and leaves as the open store or a
diagnostic.

### Steps

1. **Read and check the configuration.**
   `capability:instance_lifecycle.start_instance` calls
   `capability:configuration.load_configuration`, which reads the variables
   whose names begin with `REGISTRY_` and no other, and checks them in A17
   rule 2's order: no unknown item, by name in Unicode code point order; the
   service tokens all of the services `capability:release_declarations.rights_of_service`
   lists, or none, which makes an owner-only start; every other item present;
   each well formed; each secret at least 32 bytes (rule 3); no two secrets
   equal (rule 4); the store and the backup location apart, every link
   resolved (rule 5). The first failure stops the start with a diagnostic
   naming the item and never its value. No default is applied (rule 5).
2. **Probe the backup location.** `capability:backups.probe_backup_location`
   creates and removes a probe file under the temporary prefix
   `capability:release_declarations.backup_name_prefixes` names (A17 rule 2,
   A18 rule 5). A location that does not exist, or where the file cannot be
   created or removed, stops the start; a probe it could not remove stays
   and the next backup run removes it (A18 rule 4). No other file there is
   touched.
3. **Open or make the store.** `capability:store.open_store` first removes a
   file of the store's temporary name — the store's name with the suffix the
   release declares — and no other file. When the store's file does not
   exist and its directory does, it makes a new, empty store of
   `capability:release_declarations.store_version_of_release` under the
   temporary name and renames it to the store's name once complete;
   otherwise it opens the store for reading and writing, runs the full
   integrity check and compares the store version with the release's (A17
   rule 5). A leftover it cannot remove while the store is absent, a store
   that does not open, fails the check or carries another version stops the
   start; bringing a store to a new version is the release's step, not the
   start's. A making that fails removes its temporary file; one it cannot
   remove stays, and the next start removes it first (A17 rules 2, 5). The
   answer says whether the store was made new.
4. **Open the listeners.** Last, `module:instance_lifecycle` opens the
   owner interface's listener and then, unless the start is owner-only, the
   service API's, each at the address
   `capability:release_declarations.listener_addresses` gives — the
   configuration names none (A17 rules 1, 2). One that cannot be opened stops
   the start with a diagnostic naming the surface: the listeners already
   opened are closed, and a store step 3 made new is removed by
   `capability:store.discard_new_store` — one it cannot remove is an empty
   store of the release's version, which the next start opens as any store
   (A17 rule 2). An existing store is left as it was.
5. **Serve.** Only now the surfaces answer:
   `capability:service_api.serve_service_request` and
   `capability:owner_interface.serve_owner_request`. An owner-only start
   has no service API listener: a service call fails to connect and Registry
   answers nothing (A17 rule 1, owner, 2026-11-01).
6. **Start the passes.** Every 60 seconds from the start,
   `capability:owner_sessions.end_expired_sessions` (A13 rule 2). At least
   once a minute, `capability:backups.run_daily_backup_if_due`
   (`flow:daily_backup`), except in an owner-only start, which makes no
   backup run (A18 rule 9).

### Outcomes

- A running instance serving both surfaces, with no owner session, an empty
  sign-in count and no remembered backup date.
- An owner-only instance: the owner interface served alone, no service API
  listener, no backup run.
- A stopped start: one diagnostic naming the first failed item and no value,
  nothing served, no file left that the start made but one it could not
  remove — a probe, a file of the store's temporary name, or an empty store
  made new (A17 rule 2).

### Errors

- Each configuration check of step 1 — `module:configuration`'s diagnostic.
- The backup location missing or not writable — `module:backups`'
  diagnostic.
- The store's temporary file not removable while the store is absent, the
  store not opening, failing the integrity check or of another version —
  `module:store`'s diagnostic.
- A new store that cannot be made — `module:store`'s diagnostic; its
  temporary file removed, or left for the next start when it cannot be.
- A listener that cannot be opened — `module:instance_lifecycle`'s
  diagnostic; the listeners already opened closed, a store made new by this
  start removed by `module:store`.
- Every failure stops the start before anything is served; no failure is
  retried by Registry. A store that fails is never replaced or migrated by the
  start.

## `flow:owner_sign_in_and_session`

### Trigger

The owner opens the owner interface and signs in with the owner credential;
then makes requests in the session, signs out, or leaves it to expire.

### Boundary

`module:owner_interface` renders the sign-in form and every page, sets and
reads the session cookie and carries the CSRF value in every form; it decides
nothing (A13 rules 1, 5, 7). `module:operations` hands each request to
`module:owner_sessions`, which owns all of A13: the credential check, the
count and the lockout, the session, its limits, its locks, its CSRF value and
its pending confirmation. None of it is stored: a sign-in, a sign-out and the
pass open no store transaction and write no audit entry (A14 rule 2, M09).
`module:random_values` makes every secret value and compares every presented
one in constant time; `module:clock` gives the monotonic readings that alone
decide the limits.

Crossing models: the presented credential enters `module:owner_sessions` and
never leaves it; the session (M11) leaves as its identity, which travels only
in the cookie, and its CSRF value, which travels only in the forms (A13
rule 7).

### Steps

1. **Sign in.** The sign-in form posts the credential;
   `capability:operations.perform_owner_operation` hands it to
   `capability:owner_sessions.sign_in_owner`, which is the one owner request
   made without a session and checks only the lockout and the credential
   (A13 rule 4). During a lockout every sign-in is refused, the right
   credential included, and is not counted. Otherwise the credential is
   compared with the configured one through
   `capability:random_values.equal_in_constant_time`. A wrong or missing one
   is refused and counted at the reading of `capability:clock.monotonic_reading`;
   the fifth refusal less than 15 minutes old starts a lockout lasting 15
   minutes from it (A13 rule 3). Concurrent sign-ins are counted one at a
   time. A right one clears the count and makes a new session: its identity
   and CSRF value from `capability:random_values.make_secret_value`, its
   sign-in reading, no pending confirmation, no uploaded file. Other open
   sessions stay. `module:owner_interface` sets the cookie — not readable by
   scripts, sent only to Registry's origin, and only over HTTPS when the
   interface is reached from another machine (A13 rule 1).
2. **Every request of the session.** `capability:owner_sessions.admit_owner_request`
   checks at arrival that the cookie names a session that has reached no
   limit — 8 hours from sign-in, 30 minutes without an owner request, not
   signed out (A13 rule 2) — and, for a change, that the CSRF value is the
   session's (A13 rule 5). The arrival restarts the 30 minutes, the latest of
   concurrent arrivals counting. A request that passes completes even if a
   limit or a sign-out comes while it runs. A change then takes the
   session's one lock and holds it until done, so the session's changes
   apply one at a time; one that reads or changes an uploaded file takes the
   instance's import lock first (A16 rule 2). The request goes on as its
   own flow.
3. **Sign out.** `capability:owner_sessions.sign_out_owner` takes the import
   lock, then the session's lock, and in its turn among the session's changes
   ends the session and drops its pending confirmation and its uploaded file
   (M11). It is applied in turn with the session's other changes (A13 rule
   2): it takes the session's lock only after every change of the session
   that passed the session check before the sign-out arrived has had its
   turn, so each of them — admitted before it — completes, its change to the
   store included, with the pending confirmation and the uploaded file it may
   need still in place, and leaves nothing in the ended session. A request
   arriving after the sign-out is refused at the session check. A sign-out goes on when the import is closed (A16
   rule 2).
4. **Expire.** `capability:owner_sessions.end_expired_sessions`, every 60
   seconds (`flow:start_instance`), takes the import lock and then each
   session's lock and ends every session past a limit, with its confirmation
   and its file (A13 rule 2). A session past a limit already served no
   request from that moment (step 2).

### Outcomes

- A session the owner works in, its identity in the cookie only.
- A refused sign-in: the same answer whatever was wrong, never echoing the
  credential, the count moved unless a lockout held.
- An ended session: by sign-out, by a limit at the next pass, or by a
  restart; its pending confirmation and uploaded file gone with it.

### Errors

- Sign-in refused (wrong, missing, lockout) — `module:owner_sessions`, one
  answer.
- A request with no session, an ended or expired one, or a change with a
  CSRF value of another session or none — refused at stage (1) by
  `module:owner_sessions`; `module:owner_interface` shows the sign-in form
  for a request without a valid session. Nothing changes but this: a
  request carrying a valid session restarts its 30 minutes whatever its
  answer, a CSRF refusal included (A13 rule 2, "an owner request is any
  request ... that carries the valid session, whatever its answer").
- No secret, credential or session identity appears in a URL, a log line, a
  diagnostic or an answer's data (A13 rule 7).

## `flow:create_and_correct_project`

### Trigger

The owner creates a project in the owner interface, corrects it, or adds a
room to it; Cabinet Kernel adds a room for the agent on a project its session
is granted (A09 rule 2).

### Boundary

`module:owner_interface` makes a create form's request id when it renders the
form (A01 rule 1) and sends the revision of the card it rendered with every
correction (A04's consequence). `module:operations` runs stages (1) and (2),
opens the transaction and appends the entry. `module:projects` owns every rule
of the project and its rooms: the request id and its repeat (A01), the values,
the correction as a whole (A03), the revision (A04), the lifecycle checks.
`module:given_values` reads and compares every given value (A02, A01 rules 1,
6). `module:customers` answers whether a Customer may be newly named (A03 rule
5). `module:audit_log` appends the entry `module:operations` hands it.

Crossing models: the form's values enter `module:projects` as the given
display name, alias, customer reference and object, with the request id or
the stated revision; they leave as the Project (M01) with its Object (M02),
its revision and instants; a room leaves as Room (M03). A Customer is
reached by its `customer_ref` only; no contact value crosses into a project.

### Steps

1. **Render a create form.** `capability:owner_interface.serve_owner_request`
   renders the form with a request id from
   `capability:random_values.mint_identity` and the session's CSRF value.
2. **Create.** `capability:operations.perform_owner_operation` admits the
   request through `capability:owner_sessions.admit_owner_request`, opens the
   transaction with `capability:store.run_in_transaction`, reads the instant
   from `capability:clock.recorded_now` and calls
   `capability:projects.create_project`. `module:projects` asks
   `capability:customers.check_customer_eligible` once for a named customer
   and places its answer by stage: unknown is a failure of stage (3), and
   erased, restricted or ended one of stage (6), which a repeat never
   reaches (A01 rule 3). It checks, in A04 rule 6's stages: (3) a named
   customer exists; (4) the request id's form
   with `capability:given_values.check_request_id_form`, the display name and
   the object's address with `capability:given_values.read_required_text`,
   the alias, the object's kind and characteristics with
   `capability:given_values.read_optional_text` (A02, R0-45, R0-82). Then the
   request id is looked up among the projects: one carrying it whose current
   facts equal the given ones by `capability:given_values.facts_equal_for_repeat`
   is a repeat — answered as it stands, an archived one included, nothing
   changed, no entry (A01 rules 3, 4); one with other facts refuses the
   create (A01 rule 5). Otherwise (6) a named customer that the same answer
   called erased, restricted or ended refuses it (A03 rule 5), and the
   project is written:
   a minted `project_id`, status `active`, revision 1, created and
   last-changed at the action's instant, the request id kept (A01 rule 2).
   `module:operations` appends the entry "creating a project" with
   `capability:audit_log.append_audit_entry` and commits. A request id that
   an erasure removed since makes this a new create (A01 rule 8).
3. **Read the card.** `capability:projects.read_project_card` answers the
   project with its object, its rooms in 'list rooms' order and its revision
   (State 1, "Projections and answers"), read in
   `capability:store.read_in_transaction`; for an anonymised project it
   answers only that the project was erased, and for an unknown one refuses
   it as not found (R0-62); the owner finds projects with
   `capability:projects.list_projects` (A06 rule 1). The card the interface
   renders carries the revision into the correction form.
4. **Correct.** `capability:projects.correct_project` takes every editable
   fact and the stated revision (A03 rule 1, A04 rule 1). Stages: (3) the
   project exists, a newly named customer exists; (4) the values, as in
   step 2; (5) the stated revision is the current one — none stated, or one
   stated for an anonymised project, which has none, is stale (A04 rules 2,
   3); (6) an archived project refused (R0-12), a newly named customer that
   is erased, restricted or ended refused, keeping the named one is not newly
   naming it (A03 rule 5). Given facts equal to the stored ones are accepted
   and change nothing, no entry (A03 rule 4). Otherwise every editable fact
   is replaced, an optional one not given is cleared (A03 rule 2), the
   revision and the last-changed instant move together, and
   `module:operations` appends "correcting a project".
5. **Add a room.** `capability:projects.add_room` takes the project, a name
   and a request id — the owner's from the rendered form, Kernel's as an
   input field (A01 rule 1). For Kernel, stage (2) runs first: the session,
   and the project in its set, or the active project when none is named,
   through `capability:agent_sessions.check_agent_call` (A10). Then (3) the
   project exists; (4) the name is required, the request id well formed; the
   request id is looked up among that project's rooms only, and the archive
   check applies to a repeat too (A01 rules 3, 4); (6) an archived project
   refused. A new room gets a minted `room_id` and its added instant; the
   project's revision and last-changed instant do not move, and no entry is
   written (State 1, "Revisions and times"; M09). A room of the same name is
   a second room (R0-10). `capability:projects.list_rooms` answers the rooms
   by name, then `room_id` (A06 rule 2).

### Outcomes

- A new project, `active`, revision 1, its creation entry written; or the
  existing project answered unchanged for a repeat.
- A corrected project at its next revision with its entry, or unchanged for
  an equal correction.
- A new room, or the existing room for a repeat; no entry, no revision move.

### Errors

- Session or CSRF refused — stage (1), `module:owner_sessions`.
- For Kernel, the session unregistered, the project outside its set or none
  active — stage (2), `module:agent_sessions`, answered as a project that does
  not exist (A10 rule 3).
- Unknown project, unknown customer — stage (3), `module:projects`.
- Missing name or address, a malformed request id, a request id carried by a
  record with other facts — stage (4), `module:projects`.
- A stale or missing revision — stage (5), `module:projects`; nothing changes.
- An archived project; a customer erased, restricted or ended — stage (6),
  `module:projects`.
- Every refusal names every failure of its stage (A04 rule 6) and writes
  nothing.

## `flow:archive_and_erase_project`

### Trigger

The owner archives an active project, or erases an archived one —
anonymising it or deleting it whole, the owner's choice (R0-60). Each is an
action that asks for confirmation (State 1, "Identity formats").

### Boundary

`module:owner_interface` shows the confirmation step and posts the
submission with the confirmation value and the revision the step showed.
`module:owner_sessions` makes, binds, uses up and clears the confirmation
value (A13 rule 6). `module:operations` runs the stages, opens the one
transaction, composes the erasure and mints the confirmation id once the
action is accepted and changed state (A14 rule 5). `module:projects` owns the
lifecycle: archive, anonymise, delete whole, their repeats and refusals (A05).
`module:agent_sessions` removes an erased project from every session (R0-61).
`module:artifact_pointers` deletes the pointers of a project deleted whole.
`module:audit_log` appends the one entry.

Crossing models: the target `project_id`, the stated revision — or none for
an anonymised project — and, for an erasure, the choice anonymise or delete;
the confirmation value, which never leaves `module:owner_sessions` but as a
form field; the Project (M01) as it stands after the action; the
confirmation id, written into the entry only.

### Steps

1. **Show the step.** `capability:owner_sessions.show_confirmation_step`
   makes a confirmation value with `capability:random_values.make_secret_value`,
   bound to the action, the project, the revision the step shows or that it
   shows none, and the digest of its inputs — the erasure's choice — and
   replaces the session's pending one; it is valid 10 minutes by
   `capability:clock.monotonic_reading` (A13 rule 6). No store transaction is
   opened.
2. **Submit.** `capability:operations.perform_owner_operation` admits the
   submission (`capability:owner_sessions.admit_owner_request`), then
   `capability:owner_sessions.take_confirmation`: a value equal to the pending
   one is used up from here on, whatever the answer; a binding to another
   action, target, revision or inputs refuses it; an expired one refuses the
   submission and clears it; another value while the pending one is valid
   refuses it and leaves it (A13 rule 6). Then `capability:store.run_in_transaction`
   opens the transaction with the action's instant and today's date from
   `capability:clock.recorded_now` and `capability:clock.today_in_utc`.
3. **Archive.** `capability:projects.archive_project`: (3) the project exists;
   (5) the stated revision is current; an archived project is answered
   unchanged — no revision move, no entry, no confirmation id (A05 rules 1,
   2). An active one becomes `archived` with its archived date, its revision
   and last-changed instant moving once (State 1). Its pointers and rooms
   stay; it stays in every session's set, and an active project stays active
   (R0-70).
4. **Erase.** `capability:projects.erase_project`: (3) the project exists; (5)
   the stated revision — none for an anonymised project (A04 rule 3); (6) an
   active project refused, deleting an anonymised project whole refused (A05
   rule 4), anonymising an anonymised one answered unchanged (A05 rule 1).
   Anonymising keeps the id, the status `archived`, the anonymised mark and
   the pointers and nothing else: the display name, the alias, the object,
   the customer link, the rooms, the revision, the request id and every
   instant go (M01, R0-62, R0-87, A01 rule 8); deleting whole removes the
   record and its rooms. In the same
   transaction `module:operations` calls
   `capability:agent_sessions.drop_project_from_sessions`, which removes the
   project from every set and active project, moving each changed session's
   access version once (A12 rule 1), and, for a deletion whole,
   `capability:artifact_pointers.delete_pointers_of_project`. No module calls
   another for it ("A project leaving the platform").
5. **Record.** Once the action's module answered accepted and changed,
   `module:operations` mints the confirmation id with
   `capability:random_values.mint_identity` and appends the one entry —
   archiving, anonymising or deleting a project — with it through
   `capability:audit_log.append_audit_entry`; the sessions' loss of the
   project writes no entry of its own (M09). It commits.
6. **Answer.** The archived project as it stands, the anonymised project
   answered as erased (R0-62), or that the project was deleted; the
   interface shows it from a fresh read.

### Outcomes

- An archived project, its entry with the confirmation id.
- An anonymised project — `validate` answers `archived`; the card,
  `context`, 'list rooms' and the agent projection answer that it was erased;
  'list projects' never lists it; its pointers are listed and read as before
  (R0-62) — out of every session, its entry with the confirmation id.
- A project deleted whole with its rooms and pointers — `validate` answers
  `not_found` — out of every session, its entry.
- A repeat answered unchanged, with no entry and no confirmation id.

### Errors

- Session, CSRF or confirmation refused — stage (1), `module:owner_sessions`;
  a used-up value needs the step shown again.
- Unknown project — stage (3), `module:projects`.
- A stale revision, or one stated for an anonymised project — stage (5),
  `module:projects`.
- Erasing an active project, deleting an anonymised one whole — stage (6),
  `module:projects`.
- A failed transaction leaves the project, every session and every pointer as
  they were, and no entry (A04 rule 4).

## `flow:customer_lifecycle`

### Trigger

The owner records a Customer, corrects it, restricts it or lifts the
restriction, ends or resumes the relationship, erases its contact data, or
reads and lists Customers; PresuPro reads a Customer's billing data when it
renders or issues a document (R0-80, R0-83).

### Boundary

`module:customers` owns every rule of the Customer (M04): its create with a
request id, its correction as a whole, its revision, its marks and their
repeats, its final erasure, its reads and the billing read's refusals.
`module:given_values` reads the values. `module:operations` runs the stages,
opens the transaction and appends the entry. For the billing read,
`module:service_access` identifies PresuPro and answers whether it may call
the operation and its highest class (A09); `module:service_api` carries it.

Crossing models: the given name, kind, contact and fiscal data enter
`module:customers` and leave as the Customer (M04) with its minted
`customer_ref`; the billing read leaves as kind, tax id and legal name, each
recorded or absent, never contact data (R0-83).

### Steps

1. **Record.** `capability:operations.perform_owner_operation` admits the
   request (`capability:owner_sessions.admit_owner_request`), opens the
   transaction (`capability:store.run_in_transaction`) and calls
   `capability:customers.record_customer`: (4) the request id's form, the
   name and kind required, the contact and fiscal data optional (A02); a
   request id a Customer carries with equal facts is a repeat answered as it
   stands, with other facts refused (A01). A new Customer gets a minted
   `customer_ref` from `capability:random_values.mint_identity`, revision 1,
   its instants. The same person recorded again is a second Customer (R0-16).
   `module:operations` appends "recording a customer" with
   `capability:audit_log.append_audit_entry`.
2. **Correct.** `capability:customers.correct_customer` takes every editable
   fact and the stated revision (A03 rule 1): (3) the Customer exists; (4)
   the values; (5) the revision — one stated for an erased Customer, which
   has none, is stale (A04 rule 3); (6) an erased Customer cannot be
   corrected. Equal facts change nothing (A03 rule 4); otherwise the next
   revision and the entry "correcting a customer".
3. **Mark.** `capability:customers.mark_customer` restricts or lifts, ends or
   resumes, with the stated revision: (3) exists; (4) an end date later than
   today, `capability:clock.today_in_utc`, refused, none given meaning today
   (R0-84); (5) the revision; (6) an erased Customer refused. A transition to
   the state it is in is answered unchanged, and ending an ended relationship
   with another date does not move it (A05 rules 1, 3). An accepted mark
   moves the revision and writes its entry. Restricting keeps the contact and
   fiscal data and stops their reaching anyone but the owner; existing
   projects keep their link (R0-51, R0-55).
4. **Erase the contact data.** `capability:customers.erase_customer_contact`
   with the stated revision: (5) a revision stated for an erased Customer,
   which has none — the form that erased it resubmitted included — is stale
   (A04 rule 3); an erased Customer with none stated is answered unchanged
   (A05 rule 1); otherwise
   the Customer keeps its identity, the erased mark and its instant and
   nothing else — no revision, no request id (M04, A01 rule 8); projects
   still name it. Entry "erasing a customer".
5. **Read and list.** `capability:customers.read_customer` answers the
   Customer, an erased one only as erased; `capability:customers.list_customers`
   answers them in A06 rule 4's order, erased ones after the others without
   contact data. Both run in `capability:store.read_in_transaction`.
6. **Billing read.** `capability:service_api.serve_service_request` hands
   PresuPro's token and request to `capability:operations.perform_service_operation`;
   stage (1) is `capability:service_access.identify_service`, comparing the
   token in constant time, and `capability:service_access.service_may_call`
   for the operation (A09 rules 1–3). `capability:customers.read_billing_data`
   then answers kind, tax id and legal name, a value never recorded marked
   absent; an unknown Customer refused (3), an erased or restricted one
   refused (6) (R0-65, R0-83). The answer is `personal_data`, within
   `capability:service_access.highest_class_of_service` for PresuPro.

### Outcomes

- A recorded, corrected, marked or erased Customer with its entry; a repeat
  or an equal change answered unchanged without one.
- The owner's reads and list, with erased Customers only as erased.
- PresuPro's billing data, or its refusal.

### Errors

- Owner session, CSRF — stage (1), `module:owner_sessions`; a token that is
  unknown or wrong, or a service outside the operation's row — stage (1),
  `module:service_access`; in an owner-only start a service call reaches no
  listener (A17 rule 1).
- Unknown Customer — stage (3), `module:customers`.
- Missing name or kind, a malformed request id, a request id with other
  facts, an end date after today — stage (4), `module:customers`.
- A stale revision — stage (5), `module:customers`.
- Correcting or marking an erased Customer; billing data of an erased or
  restricted one — stage (6), `module:customers`.

## `flow:service_reads_project`

### Trigger

PresuPro, Client Portal or Cabinet calls a read its row allows (A09 rule 2):
validate a project reference, read a project context, read a project, list
projects, list rooms, list artifacts, read the latest artifact of a type.

### Boundary

`module:service_api` carries the token and the request.
`module:service_access` tells the service by its token and answers its rights
and highest class from the release (A09). `module:operations` decides the
answer's class. `module:projects` builds the project answers;
`module:artifact_pointers` the pointer answers. Nothing is written.

Crossing models: the token, the operation and its inputs — a `project_id`, a
type, a list choice — enter; the answers leave as the projections of State 1:
`validate`, `context`, the project card, the project list, the rooms, the
pointers.

### Steps

1. **Identify.** `capability:service_api.serve_service_request` hands the
   token and request to `capability:operations.perform_service_operation`.
   `capability:service_access.identify_service` compares the token in
   constant time with each configured one; an unknown token is refused like
   a wrong one, without a limit (A17 rule 7); an owner-only start has no
   service API listener, so no call gets here (A17 rule 1). `capability:service_access.service_may_call`
   refuses an operation outside the service's row, whatever the request
   holds (A09 rule 3).
2. **Read.** In one `capability:store.read_in_transaction`:
   - `capability:projects.validate_project_reference` answers exists, active,
     `not_found` or `archived` — an anonymised project `archived`, a deleted
     one `not_found` (R0-62); it refuses nothing.
   - `capability:projects.read_project_context` answers `context` field for
     field as v1 (R0-04); an anonymised project answers that it was erased;
     an unknown one is refused as not found.
   - `capability:projects.read_project_card` answers the card, active or
     archived, with the archived date for an archived project (R0-60); an
     anonymised project answers that it was erased (R0-62).
   - `capability:projects.list_projects` answers the active projects, and
     with them the archived ones when asked, never an anonymised one (A06
     rule 1, R0-62); a list choice outside its closed set is refused (A19
     rule 3).
   - `capability:projects.list_rooms` answers the rooms (A06 rule 2); an
     anonymised project, which has none left, answers that it was erased
     (R0-62).
   - `capability:artifact_pointers.list_pointers` answers every pointer of the
     project with its type, version and status (A06 rule 3);
     an anonymised project's pointers are listed and read as before (R0-62);
     `capability:artifact_pointers.latest_pointer_of_type` the one published
     pointer of a declared type, or that none is published — a withdrawal
     never falls back (R0-14) — and refuses a type
     `capability:release_declarations.declared_artifact_types` does not
     declare as unknown (A22 rule 5).
3. **Class.** `module:operations` computes the answer's class as the highest
   of its facts' and refuses it whole when it is above
   `capability:service_access.highest_class_of_service` (A09 rule 4).

### Outcomes

- The read's answer, with no entry (A14 rule 4).
- A refusal: token, right, class, unknown project or type.

### Errors

- Unknown or wrong token, operation outside the row — stage (1),
  `module:service_access`; an owner-only start — no listener, no answer.
- Unknown project — stage (3), `module:projects` (and, for the pointer reads,
  `module:artifact_pointers`).
- A type not declared, a list choice outside its set — stage (4), the
  record's module.
- An answer above the service's class — `module:operations`, refused whole.

## `flow:agent_session_access`

### Trigger

Cabinet Kernel registers an agent session when the agent's session starts,
reads its access, asks for a project and ends it; the owner lists the
sessions, answers a request, grants, revokes, changes or clears the active
project, or ends a session; every agent-authority call is checked against the
session (A10, A11, A12).

### Boundary

`module:agent_sessions` owns the session (M06), its set, its active project,
its pending request (M08), its access version and the check of every
agent-authority call (A10–A12). `module:service_access` tells Kernel's token
and that it alone carries agent authority (R0-74). `module:operations` runs
the stages, composes a grant through an access request and joins the agent
projection. `module:projects` answers whether a project exists and is
archived, and builds the project's part of the agent projection;
`module:artifact_pointers` its published pointers. `module:audit_log` appends
the grant's and revocation's entries.

Crossing models: the session identity Kernel names (R0-53), recorded as an
opaque value it did not mint; the request text, as written; the project ids of
the set; the access version the owner saw; the session's access — granted
ids, active project, whether a request is pending, the version — and the
agent projection, neither carrying `personal_data`.

### Steps

1. **Register.** `capability:service_api.serve_service_request` hands Kernel's
   call to `capability:operations.perform_service_operation`; stage (1)
   through `capability:service_access.identify_service` and
   `capability:service_access.service_may_call`; the call takes the write
   lock. `capability:agent_sessions.register_session` is checked for the
   token only (A10 rule 1): it records the session with an empty set, no
   active project, no request, access version 1; a registered session is
   answered unchanged (A05). No entry (A11 rule 6).
2. **Check every agent call.** For every later Kernel call, in the call's
   transaction, `capability:agent_sessions.check_agent_call` checks that the
   session is registered and, for an operation on a project, that the project
   named — or the active one when none is named — is in its set (A10 rules 1,
   2, 5). The session's own operations — reading its access, requesting
   access, ending it — are not on a project and need only the registered
   session: a session with an empty set reads its access and asks for a
   project. Every refusal of it is
   answered as a project that does not exist, and an unregistered session as a
   call outside the set (A10 rule 3); it hides every later failure. A write on
   an archived project of the set is refused by the record's module at stage
   (6), a read answered (A10 rule 4).
3. **Ask for a project.** `capability:agent_sessions.request_project_access`
   with the request's text, required (A02): it replaces the pending request,
   moves the version, changes no access, writes no entry, and answers nothing
   about which projects exist (R0-46, R0-47, A12 rule 4).
4. **Read the access.** `capability:agent_sessions.read_session_access`
   answers the granted ids by `project_id`, the active project, whether a
   request is pending and the version (A06 rule 8, A12 rule 5) — for Kernel
   after stage (2), for the owner after stage (1).
5. **The owner sees the sessions.** `capability:agent_sessions.list_sessions`
   answers them by registration instant, then identity (A06 rule 5), each
   with its access and pending request; the owner picks a project from
   `capability:projects.list_projects`.
6. **Answer or grant.** `capability:operations.perform_owner_operation`
   admits the change (`capability:owner_sessions.admit_owner_request`) and
   opens the transaction. `capability:agent_sessions.answer_access_request`
   takes the stated version and the answer: a request no longer pending is
   refused; declining clears it and keeps no reason, no entry; granting
   clears it and adds the project the owner picked — and, if asked, makes it
   active — through `capability:agent_sessions.grant_project`, after
   `capability:projects.validate_project_reference` answered that it exists
   and is not archived (R0-70). `capability:agent_sessions.grant_project`
   alone does the same without a request. One action moves the version once
   (A12 rule 1). A grant that adds the project to the set is the one that
   writes an entry: `module:operations` appends the grant's entry naming the
   session and the project (M09) through
   `capability:audit_log.append_audit_entry`. A project already in the set is
   answered unchanged — no version move, no entry (A05 rules 1, 2) — and
   making it active along with it is a change of the active project, which
   moves the version and writes no entry (M09). Answering a request by
   granting a project already in the set clears the request, which moves the
   version once, and writes no entry: no project joined the set.
7. **Change the active project, revoke.**
   `capability:agent_sessions.set_active_project` makes a project of the set
   active, or clears it, which revokes nothing; an archived project cannot be
   made active (R0-70); no entry (M09).
   `capability:agent_sessions.revoke_project` removes a project from the set,
   and from active when it was; a project not in the set answers that it is
   not granted (A05 rule 4); the entry "revoking" is appended. From the next
   call on the session's check refuses it (A10 rules 5, 6).
8. **The agent projection.** After stage (2), `module:operations` joins
   `capability:projects.read_agent_view` — id, alias, status, rooms — with
   `capability:artifact_pointers.published_pointers` in 'list artifacts'
   order; no display name, object, customer or other `personal_data` value
   (R0-43, R0-68); an anonymised project answers that it was erased (R0-62).
   Its class is `business_confidential`, within Kernel's (R0-74).
9. **End.** `capability:agent_sessions.end_session` removes the session's
   record — set, active project, request, version; its entries stay (A11
   rule 3). Kernel states no version; the owner states the one seen (A12
   rule 3). Ending an unregistered session is refused as for an unregistered
   session (A11 rule 5); no entry (A11 rule 6).

### Outcomes

- A registered session with an empty set, which the owner sees.
- A pending request, replaced by the next; an answered one cleared, a grant
  with its entry.
- A set, an active project and a version that the session's access shows to
  Kernel; a revocation holding from the next call.
- The agent projection of a granted project; an ended session.

### Errors

- Kernel's token wrong or another service's — stage (1),
  `module:service_access`; owner session, CSRF — stage (1),
  `module:owner_sessions`.
- An unregistered session, a project outside the set, none active —
  stage (2), `module:agent_sessions`, one not-found answer.
- An unknown session or project for the owner — stage (3),
  `module:agent_sessions` and `module:projects`.
- A missing request text — stage (4), `module:agent_sessions`.
- A stale access version — stage (5), `module:agent_sessions`; nothing
  changes.
- A request no longer pending, an archived project granted or made active, a
  project not granted — stage (6), `module:agent_sessions`.

## `flow:publish_and_withdraw_pointer`

### Trigger

Cabinet Kernel, for the agent, publishes an artifact pointer on a project its
session is granted or withdraws one; the owner does the same in the owner
interface (A08 rule 1, R0-88).

### Boundary

`module:artifact_pointers` owns the version, the supersession, the one
`published` pointer per type, the withdrawal, the publisher and the request
id (A07, A08 rules 3–7, A01). `module:release_declarations` declares the
types and their owner services (A22). `module:agent_sessions` checks Kernel's
call (A10); `module:service_access` refuses every other service (A08 rule 2).
`module:operations` resolves a withdrawn pointer's project before stage (2)
(A08 rule 7). `module:projects` answers whether the project exists and is
archived. No entry is written (M09).

Crossing models: the project, the type, `uri` or `payload_ref` or both, the
digest as given, the request id; the pointer (M05) with its id, version,
status, owner service and publisher — Kernel naming the session, or the
owner.

### Steps

1. **Publish.** `capability:operations.perform_service_operation` (Kernel,
   through `capability:service_api.serve_service_request`) or
   `capability:operations.perform_owner_operation` (the owner, the request id
   made when the form was rendered) opens the transaction with the write
   lock. For Kernel, stage (1) is `capability:service_access.service_may_call`
   — no other service may publish — and stage (2)
   `capability:agent_sessions.check_agent_call`. Then
   `capability:artifact_pointers.publish_pointer`: (3) the project exists;
   (4) the type among `capability:release_declarations.declared_artifact_types`,
   `uri` or `payload_ref` given and not blank, the request id well formed
   (A07 rule 6, A22 rule 5); the request id looked up among that project's
   pointers, its project and publisher among the facts — a repeat answers
   the pointer whatever its status now, and the archive check applies to it
   (A01 rules 3, 4, 6); (6) an archived project refused. A new pointer gets a
   minted id, the next version of its type, the owner service of
   `capability:release_declarations.owner_service_of_type` and its
   publisher; the type's published pointer becomes `superseded` with its
   instant, all in the one transaction (A07 rules 1–3).
2. **Withdraw.** The call names the pointer only. `module:operations` finds
   the pointer's project with `capability:artifact_pointers.project_of_pointer`
   first, and for Kernel stage (2) is then
   `capability:agent_sessions.check_agent_call` on that project — so it never
   falls back to the active project. An unknown pointer, an unregistered
   session and a project outside the set are one answer, as not found, at
   stage (2) (A08 rule 7, A10 rule 3), so the order of the lookup and the
   session's check shows nothing; for the owner an unknown pointer is refused
   at stage (3); a pointer that
   does not exist or whose project is outside the set is answered as not
   found (A08 rule 7). `capability:artifact_pointers.withdraw_pointer`: a
   withdrawn or superseded pointer refused (A05 rule 4), a pointer of a
   removed type refused (A22 rule 5), one of an archived project refused
   (A07 rule 5); otherwise `withdrawn` with its instant and principal. No
   earlier version becomes `published` (A07 rule 4).
3. **Order.** Publishes and withdrawals of one project run one at a time under
   the write lock: two publishes of a type get consecutive versions; a
   withdrawal after a publish superseded its pointer is refused (A07 rule 2).

### Outcomes

- A `published` pointer, the previous one of its type `superseded`; or the
  existing pointer for a repeat.
- A `withdrawn` pointer, still in the history; 'read the latest' then answers
  that none is published.

### Errors

- Another service's token — stage (1), `module:service_access`.
- Kernel's session or set — stage (2), `module:agent_sessions`, as not found.
- Unknown project — stage (3), `module:artifact_pointers`; an unknown pointer
  the same for the owner, and for Kernel stage (2)'s not-found answer.
- An undeclared or removed type, neither `uri` nor `payload_ref`, a request id
  with other facts — stage (4), `module:artifact_pointers`.
- An archived project; a pointer already withdrawn or superseded — stage (6),
  `module:artifact_pointers`.

## `flow:import_from_vps`

### Trigger

The owner imports, once, the projects they pick from the VPS instance's export
file (R0-79), confirming the mapping Registry shows (A16).

### Boundary

`module:owner_interface` serves the upload, the mapping and the confirmation
pages. `module:owner_sessions` keeps the uploaded file in the session's
memory, holds the import lock and the session's lock, and owns the
confirmation value (A16 rule 2, A13 rule 6). `module:migration_import` owns
reading the file, the mapping and its checks, the re-check at confirmation
and the closure (A16, M10). `module:projects`, `module:customers` and
`module:artifact_pointers` write their own imported records.
`module:operations` opens the one transaction, mints the confirmation id and
appends the entry. `module:release_declarations` gives the file's size limit
and the declared types.

Crossing models: the file's bytes, kept only in memory and named by their
digest; the mapping — the picked projects by `project_id`, their rooms and
pointers, names and aliases, the Customers to make, the malformed records and
the conflicts (A06 rule 8); the owner's picks, names, aliases and Customer
values; the imported records with their source ids and instants; the
closure (M10) and the answer listing each made Customer's v1 value and
minted `customer_ref`.

### Steps

1. **Upload.** `capability:operations.perform_owner_operation` admits the
   upload with the import lock taken before the session's
   (`capability:owner_sessions.admit_owner_request`). Holding them,
   `capability:migration_import.read_import_mapping` refuses when the closure
   exists (rule 8), refuses a file over the release's size limit (A19 rule
   4) and a file that cannot be read, holds two projects with one id, or a
   project without a readable id or status (rule 3), and otherwise answers
   each project with its id and status. An accepted file is kept by
   `capability:owner_sessions.keep_uploaded_file`, replacing the session's
   earlier one; a refused upload replaces nothing.
2. **Map the picks.** For each request with picks, names, aliases and
   Customer values, `capability:owner_sessions.read_uploaded_file` gives the
   kept file, and `capability:migration_import.read_import_mapping` reads, in
   `capability:store.read_in_transaction`, what the picks bring in and
   nothing else (rule 3): their rooms and pointers, each name and alias they
   arrive under, the Customers it will make, the malformed records (rule 4,
   an undeclared type among them, A22 rule 7) and every id production holds
   (rule 5).
3. **Show the step.** Only when the mapping shows no malformed record, no
   conflict and no missing value (rule 1),
   `capability:owner_sessions.show_confirmation_step` binds a confirmation
   value to the import and the digest of the file's digest and the picks,
   names, aliases and Customer values (A13 rule 6).
4. **Confirm.** Under the import lock and the session's lock,
   `capability:owner_sessions.take_confirmation` uses the value up;
   `capability:store.run_in_transaction` opens the transaction with the
   action's instant from `capability:clock.recorded_now`; and
   `capability:migration_import.confirm_import` refuses when the closure
   exists or the file of the bound digest is no longer kept, checks the
   picks again (rule 6) and has each record written by its own module with
   its source identities and instants: `capability:projects.write_imported_project`
   the projects with their objects and rooms,
   `capability:customers.make_imported_customer` each Customer with a minted
   `customer_ref` at the action's instant, the v1 value moved to its tax id
   when the owner said so (R0-80), `capability:artifact_pointers.write_imported_pointer`
   the pointers, with the import as their publisher (M05).
5. **Close.** `module:operations` mints the confirmation id with
   `capability:random_values.mint_identity`;
   `capability:migration_import.record_migration_closure` writes the closure
   with it; `capability:audit_log.append_audit_entry` the one entry naming
   the closure by the file's digest. The transaction commits; then
   `capability:owner_sessions.drop_uploaded_files` drops every session's
   upload, the import lock still held (A16 rule 2).
6. **Answer.** Each Customer made, its v1 value and its `customer_ref` (rule
   10).

### Outcomes

- An accepted import: the picked projects under their own ids with rooms,
  pointers and links, the Customers made, the closure and one entry; every
  session's upload dropped; every later import refused.
- A confirmation refused because the closure exists — made by any import
  accepted before it, of another session or of this one: nothing applied,
  every upload already dropped, and the import refused for good; no step is
  shown again (rule 8). Stage (1) comes first — the session, the CSRF value
  and the confirmation value, used up when it was carried (A13 rule 6) — and
  this refusal comes before every other of the import's own checks.
- A confirmation refused while no closure exists: nothing applied; the file
  stays kept unless a new upload or the session's end dropped it. When the
  pending value was used up or cleared, the step must be shown again; a
  submission refused for giving another value while the pending one is still
  valid leaves that value and its step, which may be submitted again (A13
  rule 6).

### Errors

- Session, CSRF, confirmation — stage (1), `module:owner_sessions`.
- The closure exists — `module:migration_import`, at upload, mapping,
  step and confirmation.
- A file over the limit or unreadable, two projects with one id, a project
  without a readable id or status — `module:migration_import`, at upload.
- A malformed record, a conflicting id, a missing name, kind or tax-id
  answer — `module:migration_import`: no step is shown, and at confirmation
  the whole import is refused, nothing changed (rule 6).
- The bound file no longer kept — `module:migration_import`; it must be
  uploaded again.
- A failed transaction — nothing applied, no closure, the import may be
  retried (rule 9).

## `flow:daily_backup`

### Trigger

The minute look of a running instance with its service tokens reaches 03:00
UTC of a date it saw before 03:00 (A18 rule 1).

### Boundary

`module:backups` owns whether a run is due, its three steps, the encryption,
the backup's record, the names and the rotation (A18). `module:store` writes
the consistent copy without agent sessions at the path `module:backups` names
and checks a decrypted copy (A18 rules 2, 4). `module:clock` gives the look's
instant. `module:release_declarations` gives the prefixes and the release.
`module:instance_lifecycle` runs the look every minute. Nothing is written to
the store and no entry is made.

Crossing models: a temporary path; the copy's instant and last audit sequence
number, from its one read transaction; the encrypted backup with its record —
instant, release, last sequence number, key digest — readable without the
key; the kept name made from the instant.

### Steps

1. **Due?** `capability:backups.run_daily_backup_if_due`, called by
   `module:instance_lifecycle` at least once a minute, reads
   `capability:clock.recorded_now`. A run starts when an earlier look of this
   process saw this date before 03:00, the look is at or after 03:00, this
   process did not run this date, no run is going, and no kept backup of the
   date exists — a file whose record cannot be read counting as none (A18
   rule 1). The date is remembered, a failed run included.
2. **Clear temporary files.** Every regular file directly in the location
   whose name begins with the temporary prefix of
   `capability:release_declarations.backup_name_prefixes` is removed; a
   failed removal stops the run (A18 rule 4).
3. **Copy, encrypt, check.** `capability:store.copy_store_snapshot` writes one
   read snapshot of the store, the agent sessions removed, at the temporary
   path `module:backups` named, and answers that transaction's start instant
   and the last sequence number the audit counter holds (A18 rules 1, 2,
   A15 rule 5). `module:backups` encrypts it into the backup, a second file
   under the temporary prefix, with the configured key, and removes the
   unencrypted copy before going on — a copy it cannot remove fails the run
   and is left, under the temporary prefix, for the next run's step 2; the
   backup records the instant, the release from
   `capability:release_declarations.release_versions`, the sequence number
   and the key's digest; decrypts it into a second temporary file;
   `capability:store.check_store_file` opens that for reading only and checks
   the release's store version, the full integrity check and that its kept
   sequence number equals the recorded one; `module:backups` removes it. No
   unencrypted file of the store is left by a run that succeeds. A
   backup that passes is renamed to its kept name, made from its instant; one
   that fails, or whose kept name exists, or whose rename fails, is deleted
   and the run fails (A18 rules 4, 5).
4. **Rotate.** Whatever step 3 did, every kept backup made more than 30 × 24
   hours before this step's start, one cutoff, and every kept-prefix file
   whose record cannot be read is deleted, in name order; a file it cannot
   read or delete is reported and the next one taken (A18 rule 4).
5. **Show.** `capability:backups.newest_backup_instant` gives the owner
   interface the instant of the newest kept backup with a readable record, or
   that there is none, from one listing (A18 rule 1).

### Outcomes

- A kept, checked backup of the date and backups older than 30 × 24 hours
  deleted; the owner interface shows the newest instant.
- A failed run whose backup failed: no partial kept backup, only temporary
  files the next run removes, a diagnostic naming the failure and no value;
  Registry keeps serving.
- A failed run whose backup was kept but a deletion of step 4 failed: the
  new backup kept and shown as the newest, the files it could not delete
  still there, each reported; the run counts as failed (A18 rule 4).

### Errors

- A temporary file not removable — the run stops at step 2.
- The copy, encryption, check or rename failing — the run fails, step 4 still
  runs (A18 rule 4).
- A kept backup or unreadable file not deletable — reported, the run fails,
  its new backup stays kept.
- Every failure is `module:backups`' diagnostic; whether runs succeed is the
  owner's to watch on the host (A18 rule 5).

## `flow:read_and_erase_audit`

### Trigger

The owner reads the audit log, or erases every entry older than a date they
give, confirming (R0-58, R0-66).

### Boundary

`module:audit_log` owns the log, its order, the never-lowered sequence counter
and the erasure by date (A14, A15). `module:operations` admits the owner,
opens the transaction, mints the confirmation id and appends the erasure's own
entry after the removal (A15 rules 4, 6). `module:owner_sessions` owns the
confirmation value. No service token reaches the log (A15 rule 2).

Crossing models: the entries (M09) in sequence order; the date the owner
gives; the erasure's entry naming the date with its confirmation id and no
subject.

### Steps

1. **Read.** `capability:operations.perform_owner_operation` admits the
   request (`capability:owner_sessions.admit_owner_request`);
   `capability:audit_log.read_audit_entries` answers the entries by sequence
   number, ascending (A06 rule 6), in `capability:store.read_in_transaction`.
2. **Show the step.** `capability:owner_sessions.show_confirmation_step`
   binds a value to the erasure and the digest of the date; the step shows
   no revision (A13 rule 6).
3. **Erase.** The submission is admitted and
   `capability:owner_sessions.take_confirmation` uses the value up;
   `capability:store.run_in_transaction` opens the transaction with the
   instant and today's date from `capability:clock.recorded_now` and
   `capability:clock.today_in_utc`. `capability:audit_log.erase_audit_entries_before`
   refuses a date later than today and otherwise removes every entry whose
   instant is before 00:00 UTC of it (A15 rule 3).
4. **Record.** The erasure is accepted whatever it removed: `module:operations`
   mints the confirmation id with `capability:random_values.mint_identity`
   and appends, after the removal, the erasure's entry naming the date with
   it through `capability:audit_log.append_audit_entry`, with the next
   sequence number of the counter, which the erasure did not lower (A15
   rules 4–6). It commits.

### Outcomes

- The log read in sequence order.
- Entries before the date removed and the erasure's own entry written, also
  when nothing was removed.

### Errors

- Session, CSRF, confirmation — stage (1), `module:owner_sessions`.
- A date later than today — `module:audit_log`; nothing removed, no entry.
- A failed transaction — no entry removed, no entry written.
