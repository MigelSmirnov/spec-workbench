# State 3 — Registry module responsibilities

Draft of 2026-11-01. Derived from the accepted State 2 decisions A01–A22
(`02_rules_*.md`) over the models of State 1 (`01_models.md`). A module owns
one hidden mechanism and has one reason to change; its public surface is
smaller than what it hides. Each accepted decision has one primary owner, the
module that holds the decision's central mechanism, and consumers. Ownership is
by rule, not by decision: a consumer owns exactly the rules and parts of the
decision its own section below names, and the primary owner owns every rule of
the decision that no other section names, except a rule this text places
outside the running instance (A20, A21, A22 rule 6's "never declared again"),
which no module owns. The table is the one mapping; `30_trace.json` records the same:

| decision | primary owner | consumers |
|---|---|---|
| A01 | `projects` | `given_values`, `customers`, `artifact_pointers`, `store`, `owner_interface` |
| A02 | `given_values` | `projects`, `customers`, `artifact_pointers`, `agent_sessions`, `migration_import` |
| A03 | `projects` | `customers` |
| A04 | `operations` | `projects`, `customers`, `agent_sessions`, `owner_interface` |
| A05 | `projects` | `customers`, `artifact_pointers`, `agent_sessions`, `operations` |
| A06 | `store` | `projects`, `customers`, `artifact_pointers`, `agent_sessions`, `audit_log`, `migration_import` |
| A07 | `artifact_pointers` | `store` |
| A08 | `artifact_pointers` | `operations`, `service_access` |
| A09 | `service_access` | `release_declarations`, `operations` |
| A10 | `agent_sessions` | `operations` |
| A11 | `agent_sessions` | `operations`, `owner_interface` |
| A12 | `agent_sessions` | `owner_interface` |
| A13 | `owner_sessions` | `clock`, `random_values`, `owner_interface`, `operations` |
| A14 | `audit_log` | `operations` |
| A15 | `audit_log` | `store`, `backups` |
| A16 | `migration_import` | `owner_sessions`, `owner_interface`, `projects`, `customers`, `artifact_pointers` |
| A17 | `configuration` | `store`, `backups`, `service_access`, `owner_sessions`, `instance_lifecycle` |
| A18 | `backups` | `store`, `clock`, `instance_lifecycle`, `owner_interface` |
| A19 | `owner_interface` | `store`, `migration_import` |
| A22 | `release_declarations` | `artifact_pointers`, `migration_import` |

A20 and A21 have no runtime owner. A20 is a property of the release — which
dependencies it names and installs — made and checked by the release process,
which Registry does not manage (Explicit exclusions); A21 is an evidence record
checked by `design_lint --state 2`. `30_trace.json` records both as such. That
a removed artifact type's name is never declared again (A22 rule 6) compares a
release with the ones before it, which only the release process sees; a
running instance reads its own release alone.

Registry is one process (R0-05) serving two surfaces (Actors and trust
boundaries, "Network surface"): the service API, for the four services of A09,
and the owner interface. Which networks reach each surface, and the HTTPS that
carries the owner interface from another machine, are the host's
administration (R0-28, R0-29, R0-48; Explicit exclusions): Registry serves
each surface on a listener of its own and decides nothing about reachability.
The modules are the parts of that one program, not services. Only `store`
opens a SQLite database — the store's, and the decrypted copy of a backup that
`backups` hands it by path to check — and only `backups` names, renames or
deletes a file in the backup location; `store` writes and opens one there only
at the temporary path `backups` names for it. The dependency direction is fixed, from the bottom up:

```text
models
clock, random_values, release_declarations, given_values
configuration
store
audit_log, service_access, owner_sessions
customers
projects
artifact_pointers, agent_sessions
migration_import, backups
operations
service_api, owner_interface
instance_lifecycle
```

A module may know only modules on earlier lines of the list, never one on a
later line, and modules on one line do not know each other.

## Facts several modules touch, and their one owner

- **One action, one transaction.** Every action is one call of `operations`
  and, when it changes the store, one store transaction (A04 rule 4). A
  request that changes only an owner session's runtime state — signing in or
  out, showing a confirmation step, uploading an import file — goes through
  `operations` too but opens no store transaction: `owner_sessions` applies
  it under its own locks (A13 rule 2). For every other change, `operations`
  `operations` opens the transaction through `store.run_in_transaction`,
  calls each module the action
  changes inside it, appends the action's one audit entry through
  `audit_log.append_audit_entry` when the action changed state and M09 lists
  it (A14 rule 1)
  and commits once. No other module appends an entry. The erasure of old
  entries is appended the same way, after `audit_log.erase_audit_entries_before`
  has removed the entries in the same transaction (A15 rule 4), also when it
  removed none (A15 rule 6). A domain module never opens a transaction and
  never commits; it reads and writes through the transaction it is handed.
  Changes that write the store are applied one at a time (A01 rule 7, A07
  rule 2, A10 rule 6, A15 rule 5): `store` holds the one write lock and a
  transaction that changes anything takes it when it begins, so each change
  reads the result of the one before. Every agent-authority call takes it too,
  a read included, so a call is ordered with every change of its session
  (A10 rule 6).
- **Minted identities.** The module that writes a record checks, inside the
  transaction, that the identity `random_values` minted for it is not one its
  model already holds, and mints again when it is; a collision never refuses
  an action. A confirmation id names no record and no read looks one up; it
  is not checked against earlier ones.
- **The check order.** A04 rule 6 is `operations`': it runs stage (1) —
  through `service_access` for a service, `owner_sessions` for the owner — and
  stage (2) through `agent_sessions.check_agent_call`, and hands the action to
  the module that owns its record for stages (3) to (6). That module checks
  them in that order inside the transaction and answers every failure of the
  first failing stage, as a refusal tagged with its stage (the refusal
  vocabulary is `models`'). `operations` never re-orders them and adds no
  check of its own after stage (2).
- **Revisions.** A Project's and a Customer's revision and last-changed
  instant are moved only by `projects` and `customers`, each for its own
  records, and only together ("Revisions and times"); each checks the stated
  revision at stage (5) of its own actions, a stated revision for a record
  without one and none for a record with one included (A04 rules 2, 3). A
  session's access version is moved and checked only by `agent_sessions`
  (A12).
- **A project leaving the platform.** Anonymising or deleting a project whole
  (R0-60, R0-61, R0-62) is one action of `operations`, in one transaction:
  `projects` erases the record, `agent_sessions` removes the project from
  every session's set and active project, moving each version once (A12
  rule 1), `artifact_pointers` deletes the pointers of a project deleted
  whole, and `audit_log` appends the one entry (M09). No module calls another
  for it.
- **Answers and their class.** The projection an operation answers — the
  project card, `context`, `validate`, the agent projection, the session's
  access, the billing read, the customer read and list, the audit view — is
  built by the module that owns its records — the project card, with its
  object and its rooms in 'list rooms' order, by `projects` alone; the one
  answer that joins records of two modules, the agent projection with its
  project's published pointers, is joined by `operations`. Each fact's disclosure class
  is `models`' ("Disclosure classes by field"); `operations` computes an
  answer's class as the highest of its facts' and refuses the answer whole
  when it is above the caller's highest (A09 rule 4): a service's from
  `service_access`, and for the owner `personal_data`, the highest class, so
  no owner answer is refused for its class (Actors and trust boundaries,
  "Personal data").
- **Time.** An action has one instant: `operations` reads it from
  `clock.recorded_now` once, when the action's transaction begins, with
  today's date (`clock.today_in_utc`), and hands both to every module the
  action records a new instant or compares a date in. The import's records
  keep the instants their source holds ("Revisions and times"); the Customers
  it makes, its closure and its entry carry the action's one instant. The
  limits of A13 are read by `owner_sessions` from `clock.monotonic_reading`;
  the minute look of A18 rule 1 by `backups` from `clock.recorded_now`; a
  backup's instant is the one `store` reads when the copy's read transaction
  begins, which `backups` records and never reads itself. No other module
  reads a clock.
- **Random values and secret comparison.** Every identity Registry mints
  ("Identity formats") and every 32-byte value of A13 rule 7 comes from
  `random_values`; every comparison of a presented secret with a held one goes
  through `random_values.equal_in_constant_time` (A13 rule 7, A17 rule 6).
- **What the release declares.** The artifact vocabulary (A22), the services'
  rights (A09 rule 2), the store version, the temporary-name suffix of the
  store (A17 rule 5), the two backup prefixes (A18 rule 5) and the release's
  and contract's versions are
  `release_declarations`'; nothing reads them from the configuration or the
  store (A22 rule 2, A09 rule 1).
- **Secrets never leave.** No module puts a secret, a confirmation value, a
  CSRF value or an owner session's identity into a record, a log line, a diagnostic,
  an audit entry, a URL or the data of an answer (A13 rule 7, A17 rule 6).
  An agent session's identity, which Kernel names (R0-53), is not one of them:
  M06, M07 and M09 record it. The owner session's identity travels only in its
  cookie, the CSRF and confirmation
  values only in the forms `owner_interface` serves (A13 rule 7).
  `configuration` holds the secrets and hands each only to the module that
  uses it: the service tokens to `service_access`, the owner credential to
  `owner_sessions`, the backup key to `backups`.

## `models`

### Owns

The models M01–M11 as the domain's vocabulary, the declared vocabularies of
State 1 — for the artifact types only the shape of a type with its owner
service, whose members are `release_declarations`' — and the disclosure class
of every fact ("Disclosure classes by field"),
the order of the classes (A09 rule 4), and the refusal vocabulary: each refusal
kind with the stage of A04 rule 6 it belongs to.

### Knows

Nothing.

### Must not own

Any rule about when a record changes, any check, any persistence.

### Depth assessment

- kind: deep
- hidden mechanism: type validity of the vocabulary every other module speaks

## `clock`

### Owns

A13 rule 2's two readings: the UTC wall-clock instant every recorded time is
(L16), and the process's monotonic reading, which a change of the wall clock
does not move and which counts a suspension of the host. Today, the current
date in UTC (A15 rule 3, R0-84).

### Knows

Nothing.

### Must not own

Any limit or schedule: the 8 hours, 30, 15 and 10 minutes and the 60 seconds
are `owner_sessions`', the 03:00 and the minute look `backups'`.

### Hides

The host's clocks, and their replacement by fixed readings in tests.

### Candidate public capabilities

```text
recorded_now
today_in_utc
monotonic_reading
```

### Depth assessment

- kind: deep
- hidden mechanism: the only reader of the host clocks, replaceable as a whole in tests

## `random_values`

### Owns

Minting every opaque identity of a record or an action — `project_id`,
`room_id`, pointer id, `customer_ref`, the confirmation id — as a random UUID
("Identity formats"); making the values of A13 rule 7 — the owner session's
identity, its CSRF value, a confirmation value — of at least 32 bytes from the
operating system's random source; comparing a presented secret with a
held one in constant time (A13 rule 7, A17 rule 6).

### Knows

Nothing.

### Must not own

Which value is a secret, where it travels or when it is checked.

### Hides

The operating system's random source and the constant-time comparison.

### Candidate public capabilities

```text
mint_identity
make_secret_value
equal_in_constant_time
```

### Depth assessment

- kind: deep
- hidden mechanism: the one source of randomness and the one constant-time comparison

## `release_declarations`

### Owns

What a release declares and a running instance reads from it alone: A22 — the
artifact types with their owner services, the first release's one type
(`estimate`, PresuPro) — A09 rule 2's table of the services, their operations
and their highest classes; the store version; the store's temporary-name
suffix (A17 rule 5); the kept and temporary backup prefixes, neither beginning
with the other (A18 rule 5); the import file's size limit (A19 rule 4, its
value State 6's); the release's own version and its contract version: every
audit entry names both (M09), a backup's record the release (A18 rule 1); the
address each surface listens on, which the configuration does not name (A17
rules 1, 2).

### Knows

`models`.

### Must not own

What a vocabulary change does to existing pointers (A22 rules 4, 5 are
`artifact_pointers`'), how a right is checked (`service_access`), anything read
from the configuration or the store.

### Hides

Where in the release the declarations live and how they are loaded.

### Candidate public capabilities

```text
declared_artifact_types
owner_service_of_type
rights_of_service
store_version_of_release
backup_name_prefixes
release_versions
listener_addresses
```

### Depth assessment

- kind: deep
- hidden mechanism: the release's fixed declarations, read once and never from outside the release

## `given_values`

### Owns

A02: the one reading of a value a caller gives — a required value blank or
white space only is missing, a present value is kept exactly as written, an
optional value blank is absent. A01 rule 1's check of a request id's form —
printable text of at most 128 characters, not blank — and A01 rule 6's
comparison of the facts of a create with a record's current facts, as A02
reads them, a fact of several parts by its parts whatever their order.

### Knows

`models`.

### Must not own

Which values an action requires (each record's module says), whether a create
is a repeat (that needs the record: `projects`, `customers`,
`artifact_pointers`), whether a request id is random (the caller's duty, A01
rule 1).

### Hides

White-space classes, the printable-text check, the order-free comparison of
composite facts.

### Candidate public capabilities

```text
read_required_text
read_optional_text
check_request_id_form
facts_equal_for_repeat
```

### Depth assessment

- kind: deep
- hidden mechanism: the one rule by which every given value is read and compared

## `configuration`

### Owns

A17: reading the `REGISTRY_` environment variables and nothing else; the start
checks in rule 2's one order — no unknown item, one service token for each
service `release_declarations` lists, all or none, the other items present, each well formed, each secret at least 32 bytes,
no two secrets equal — with the diagnostic naming the failed item and never its
value; that no default is applied (rule 5); an owner-only start when no token
is given (rule 1). The path checks of rule 5 that need no file — the store and
the backup location apart, compared with every link resolved — are its too.

### Knows

`models`, `release_declarations`.

### Must not own

Opening or making the store (`store`), probing the backup location
(`backups`), what a token may do (`service_access`), the credential check of a
sign-in (`owner_sessions`).

### Hides

The environment, path resolution, and the order of the checks.

### Candidate public capabilities

```text
load_configuration
```

### Depth assessment

- kind: deep
- hidden mechanism: the ordered start checks of A17 over the process environment

## `store`

### Owns

The one SQLite database (L19) and its connections — the one the
transactions of actions run on, and the read connection a backup's copy
takes its snapshot on while they go on, in write-ahead-log mode, the
snapshot fixed by its first read, of the audit counter, with the clock read
then (A18 rule 1): opening it for reading and
writing at start and putting it in that mode when it is not (A17 rule 5), or making a new, empty store of the release's version under
the temporary name and renaming it once complete, after removing a leftover of
that name and no other file (A17 rule 5), and removing a store it made new
when the start then fails at a listener (A17 rule 2); the full integrity check —
`PRAGMA integrity_check` answering `ok`, `PRAGMA foreign_key_check` finding
nothing — and the store version check (A17 rule 5), the same check `backups`
asks of a backup's copy. Every transaction: one write lock, so changes are
applied one at a time (A01 rule 7, A07 rule 2, A15 rule 5), atomicity (A04
rule 4). A19 rule 3: every value a caller gives fills a value place of a
statement whose structure the release fixes; a value that selects among fixed
alternatives is checked against its closed list first. A06: the order of every
list read from the store — each key as A06 names it, text by Unicode code
point, every key ending in an identity or a sequence number — so no module
sorts stored records itself; the import mapping, which is not stored, is
ordered by `migration_import` by the same keys (A06 rule 8).
For a backup (A18 rules 1, 2): one consistent read snapshot of the whole store,
written as a store file of its own at the temporary path `backups` names and
makes for it, with the agent
sessions removed from that copy, so it passes the same checks; and the full
integrity and version check of such a file, the decrypted copy included,
opened for reading only. The copy answers, from its one read transaction, the
instant of the read that fixed its snapshot and the last sequence number the audit
counter it holds says (A15 rule 5), so a backup's record describes exactly its
copy (A18 rule 1).

### Knows

`models`, `clock`, `release_declarations`, `configuration`.

### Must not own

Which record a module writes or when; any domain check; the audit log's
sequence rule (A15 rule 5 is `audit_log`'s, which keeps its counter through
`store`); encrypting or keeping a backup (`backups`).

### Hides

SQL, which record goes into which row, the transaction and lock mechanics,
the temporary-name dance of a new store, the integrity pragmas.

### Candidate public capabilities

```text
open_store
discard_new_store
run_in_transaction
read_in_transaction
check_store_file
copy_store_snapshot
```

### Depth assessment

- kind: deep
- hidden mechanism: the one SQLite database, its transactions and its one write lock

## `audit_log`

### Owns

A14 and A15: appending an entry (M09) inside the transaction of the change it
records, with the next sequence number after the last the store's history ever
wrote, kept apart from the entries so an erasure never lowers it (A15 rule 5);
the actions that write an entry and the subject each names (M09); the outcome
`accepted` (A14 rule 6); that no entry is ever changed (A15 rule 1); the
erasure before a date — not later than today, every entry before 00:00 UTC of
it removed, so that the erasure's own entry `operations` appends after it,
with its confirmation id, also when nothing was removed, is never removed by
it (A15 rules 3, 4, 6); reading the log by sequence
number for the owner (A15 rule 2, A06 rule 6). The last sequence number its
store ever wrote, for a backup's record (A18 rule 1).

### Knows

`models`, `release_declarations`, `store`.

### Must not own

Whether an action changed state (the action's module says), minting the
confirmation id (`operations`), who may read the log (`operations` and
`service_access`).

### Hides

The sequence counter and how entries are stored and removed.

### Candidate public capabilities

```text
append_audit_entry
erase_audit_entries_before
read_audit_entries
last_audit_sequence
```

### Depth assessment

- kind: deep
- hidden mechanism: the append-only log and its never-lowered sequence counter

## `service_access`

### Owns

A09: telling a service by its token — the presented token compared in
constant time with each configured one, an unknown token refused like a wrong
one, without a limit (A17 rule 7) — and the service's operations and highest
class from the release (A09 rules 1, 2, 3); that Cabinet Kernel's token alone
carries agent authority and allows no class above `business_confidential`
(R0-74); that no token carries the owner's rights (A09 rule 5); A08 rule 2:
no token but Kernel's may publish or withdraw. An owner-only start holds no
token and opens no service API, so no service call reaches it (A17 rule 1).

### Knows

`models`, `release_declarations`, `random_values`, `configuration`.

### Must not own

The session and its set (A10, `agent_sessions`), the answer's class, which
`operations` computes; the owner's sign-in.

### Hides

The token table and the constant-time lookup.

### Candidate public capabilities

```text
identify_service
service_may_call
highest_class_of_service
```

### Depth assessment

- kind: deep
- hidden mechanism: the token-to-service lookup over the release's rights table

## `owner_sessions`

### Owns

A13 and M11, all runtime state: the sign-in with the owner credential, its
count of refusals over the last 15 minutes and the lockout, one answer whatever
was wrong (rules 3, 4); the session, its cookie rules and its limits — 8 hours,
30 minutes without a request, sign-out, restart — held as monotonic readings
(rule 2); the pass every 60 seconds that ends sessions by their limits, taking
the import lock and then each session's lock; each session's one lock, under
which its state-changing requests apply one at a time; the CSRF value (rule 5);
the pending confirmation — made when a step is shown, bound to the action, its
target, the revision or access version the step showed or that it showed none,
and the digest of its inputs; valid 10 minutes, used up by the first
submission that carries it, cleared by an expired one (rule 6). The uploaded
import file each session keeps in memory, replaced by the next upload — one of
the same bytes included — and dropped with the session or by an accepted
import (A16 rule 2), and the instance's one import lock, taken before any
session's lock.

### Knows

`models`, `clock`, `random_values`, `configuration`.

### Must not own

What a confirmed action does, the mapping of an uploaded file (`migration_import`),
rendering the forms that carry the values (`owner_interface`).

### Hides

The session table, the locks and their order, the monotonic arithmetic of the
limits, the lockout window.

### Candidate public capabilities

```text
sign_in_owner
sign_out_owner
admit_owner_request
show_confirmation_step
take_confirmation
keep_uploaded_file
read_uploaded_file
drop_uploaded_files
end_expired_sessions
```

### Depth assessment

- kind: deep
- hidden mechanism: the in-memory owner sessions with their limits, locks and one-time values

## `customers`

### Owns

M04 and its records: recording a Customer with a request id (A01 for this
create, through `given_values`), correcting it as a whole (A03 rules 1–4 for
customers), its revision and last-changed instant, checked at stage (5) (A04
rules 1–3 for customers); the restricted and ended marks and their
transitions, the end date not later than today (R0-84), erasure — final,
keeping the identity, the mark and its instant and nothing else (M04);
repeated transitions answered unchanged (A05 for customers); a Customer's
eligibility to be newly named — unknown, erased, restricted or ended refused
(A03 rule 5) — which `projects` asks; the customer read and list in A06
rule 4's order, and the billing read, refusing an erased or restricted
Customer (R0-65, R0-83).

### Knows

`models`, `given_values`, `random_values`, `store`.

### Must not own

Which project names a Customer (`projects`), who may read billing data
(`service_access`).

### Hides

The Customer's record shape and its erasure.

### Candidate public capabilities

```text
record_customer
correct_customer
mark_customer
erase_customer_contact
read_customer
list_customers
read_billing_data
check_customer_eligible
make_imported_customer
```

### Depth assessment

- kind: deep
- hidden mechanism: the Customer record's lifecycle of marks and its final erasure

## `projects`

### Owns

M01, M02 and M03 and their records: A01 — every create carries a request id,
a repeat answers the record unchanged when its facts equal the record's
current ones, a different one is refused, lookup among the same project's
records for a room, a repeat checked only through stage (4) — and, for 'add a
room', its project's archive check; a project's repeat answers an archived
project as it stands (A01 rule 3, test 4) — the request id leaving with the values erasure removes (rules
2–9; the pointer's publish under the same rules is `artifact_pointers'`, the
Customer's create `customers'`); A03 for projects; the revision and
last-changed instant (A04 rules 1–3 for projects); the project's lifecycle —
archive, anonymise, delete whole (M01) — and its repeated transitions (A05);
rooms, added and never changed (M03); the project card, `context`,
`validate` and the project's part of the agent projection; its lists, read
from `store` in A06 rules 1, 2 and 8's orders. A05 rule 4's refusals that are project ones.

### Knows

`models`, `given_values`, `random_values`, `store`, `customers`.

### Must not own

Sessions (`agent_sessions`), pointers (`artifact_pointers`), the audit entry
(`audit_log`), whether a caller may see a project.

### Hides

The project record with its embedded object, the room records, the repeat
recognition of creates.

### Candidate public capabilities

```text
create_project
correct_project
archive_project
erase_project
read_project_card
read_project_context
validate_project_reference
read_agent_view
add_room
list_rooms
list_projects
write_imported_project
```

### Depth assessment

- kind: deep
- hidden mechanism: the project record's lifecycle and the request-id recognition of its creates

## `artifact_pointers`

### Owns

M05 and A07: publishing assigns the next version, supersedes the type's
published pointer and stores the new one in one transaction, at most one
`published` per project and type, versions gap-free; withdrawing marks
`withdrawn` and never re-publishes an earlier one; both refused on an archived
project; the reference and digest as given. A08 rules 3–7: the owner service
fixed by the type, the publisher and the withdrawing principal recorded, a
withdrawal naming the pointer alone. A01 for the publish's request id, its
repeat answering the pointer whatever its status now. A22 rules 3–5: a removed
type's pointers kept as they are, its publish, latest read and withdrawal
refused. The pointers' list (A06 rule 3), the latest of a type, and a
project's `published` pointers in that list's order, for the agent projection
(State 1, "Projections and answers"; A06 rule 8). Deleting every pointer of a
project deleted whole (R0-60), in the transaction `operations` opens for it.

### Knows

`models`, `given_values`, `random_values`, `store`,
`release_declarations`, `projects`.

### Must not own

Whether the caller may publish (`service_access`, `agent_sessions`), the
payload or whether the document exists (V1-4).

### Hides

Version assignment and supersession inside one transaction.

### Candidate public capabilities

```text
publish_pointer
withdraw_pointer
list_pointers
latest_pointer_of_type
published_pointers
delete_pointers_of_project
project_of_pointer
write_imported_pointer
```

### Depth assessment

- kind: deep
- hidden mechanism: per-project, per-type version history with one published pointer

## `agent_sessions`

### Owns

M06 and M08, A10, A11 and A12: registering a session Kernel names and ending
it, which removes its record (A11); the granted set, the active project — an
archived project is never made active, and one archived while active stays
active (M06, R0-70) — and the pending request, replaced by the next (M08); the
access version, moved once per accepted action that changes them, checked on
the owner's actions (A12); A10's check of every agent-authority call — the
session registered, the project in its set, the active project when none is
named — and its one not-found answer for a refusal, inside the call's
transaction, so a revocation holds from the next call (A10 rules 1–6);
removing a project from every session when it is erased (R0-61); the list of
sessions in A06 rule 5's order and the session's access.

### Knows

`models`, `given_values`, `store`, `projects`.

### Must not own

The token check (`service_access`), the audit entry of a grant (`audit_log`),
what the agent does with the project.

### Hides

The session record and the version arithmetic.

### Candidate public capabilities

```text
register_session
end_session
check_agent_call
grant_project
revoke_project
set_active_project
request_project_access
answer_access_request
drop_project_from_sessions
read_session_access
list_sessions
```

### Depth assessment

- kind: deep
- hidden mechanism: the session's access record and its version under concurrent calls

## `migration_import`

### Owns

A16 and M10: reading an uploaded file as data under the release's size limit
(A19 rule 4), refusing at upload a file that cannot be read, holds two
projects with one id or a project without a readable id or status (rule 3);
the mapping for the picks — rooms, pointers, names and aliases, the Customers
it will make, malformed records and conflicting ids (rules 1, 3–5); that the
confirmation step is not shown while the mapping shows an error (rule 1);
checking again at confirmation and, in the one transaction `operations`
opens, which appends the import's audit entry, having each record written by
its own module with its source identities and instants — `projects`
the picked projects with their objects and rooms, `customers` the Customers
it makes, `artifact_pointers` the pointers, the import as their publisher
(M05) — and, once they are written, the closure (M10) with the confirmation
id `operations` minted then, or nothing (rules 6, 7);
refusing every import once the closure exists (rule 8); the answer naming each
Customer's minted `customer_ref` (rule 10). A22 rule 7: an undeclared type is
malformed.

### Knows

`models`, `given_values`, `random_values`, `store`,
`release_declarations`, `owner_sessions`, `customers`, `projects`,
`artifact_pointers`.

### Must not own

The session's locks and its kept file (`owner_sessions`), the export (R0-72),
the confirmation value (`owner_sessions`).

### Hides

The export file's reading and the mapping's checks.

### Candidate public capabilities

```text
read_import_mapping
confirm_import
record_migration_closure
```

### Depth assessment

- kind: deep
- hidden mechanism: the one-time, all-or-nothing import of picked v1 records

## `backups`

### Owns

A18: the daily run at 03:00 UTC while Registry runs with its tokens, from the
minute look and the dates the process remembers (rule 1); the copy, without
agent sessions, that `store` writes at the temporary path `backups` names
(rule 2), encrypted with the configured key, recording its
instant, release, last sequence number and key digest (rules 1, 3); the three
steps — removing temporary files, writing and checking the backup by
decrypting it and asking `store` to check the copy, deleting backups older
than 30 × 24 hours and unreadable ones (rule 4); the prefixes and the location
rules (rule 5), the probe file of A17 rule 2; the newest kept backup's instant
for the owner interface. No run in an owner-only start (rule 9).

### Knows

`models`, `clock`, `configuration`, `release_declarations`, `store`,
`audit_log`.

### Must not own

Restoring (R0-89), the host's encryption (rule 7), the store's own checks
(`store`).

### Hides

Encryption, the backup file format and record, the location's file rules.

### Candidate public capabilities

```text
run_daily_backup_if_due
probe_backup_location
newest_backup_instant
```

### Depth assessment

- kind: deep
- hidden mechanism: the checked, encrypted, 30-day backup rotation in a location Registry alone owns

## `operations`

### Owns

The operation table: every operation of either surface with its stages and
the modules it changes — not which service may call it, which is the
release's table alone (A09 rule 2), asked of `service_access.service_may_call`
at stage (1); the owner's operations are the owner interface's. A04 rules 4 and 6: one transaction per
action and the one check order, stages (1) and (2) run here, stages (3) to (6)
by the record's module, the first failing stage answered with all its
failures. A09 rule 4 at the call: an answer above the caller's class refused
whole; an operation outside a service's rights is refused at stage (1) by
`service_access`'s answer (A09 rule 3), never by a table of `operations`' own. A10 rule 3's
placement: stage (2)'s refusal hides every later one. A14 rules 1 and 5:
appending the audit entry in the action's transaction when the action changed
state. A14 rule 5: `operations` mints a confirmed action's confirmation id
inside the transaction only after the action's module has answered that it is
accepted and changed state — or, for the erasure of old audit entries, that it
is accepted, also when it removed nothing (A15 rule 6) — and hands it to the
entry and, for the import, to the closure; a refused or unchanged action
mints none. Resolving a pointer a withdrawal names to
its project, through `artifact_pointers.project_of_pointer`, before stage (2)
checks that project against the session's set (A08 rule 7). A05 rule 2's no entry and no
confirmation id for a repeat. The compositions: erasing a project (with
`agent_sessions` and `artifact_pointers`), granting through an access request,
joining the agent projection with its published pointers.

### Knows

`models`, `clock`, `random_values`, `store`, `audit_log`, `service_access`,
`owner_sessions`, `customers`, `projects`, `artifact_pointers`,
`agent_sessions`, `migration_import`, `backups`.

### Must not own

Any record's rules, any transport, rendering or wire format.

### Hides

The stage pipeline and the transaction each action runs in.

### Candidate public capabilities

```text
perform_service_operation
perform_owner_operation
```

### Depth assessment

- kind: deep
- hidden mechanism: the staged check pipeline and the one transaction of every action

## `service_api`

### Owns

The service API's transport for the four services (R0-27, R0-28): reading the
token and the request, calling `operations`, answering in the wire format
States 5 and 6 declare; nothing reachable without a token.

### Knows

`models`, `operations`.

### Must not own

Any check, right or record rule.

### Hides

The HTTP server of the service API and the reading and writing of its wire
format.

### Candidate public capabilities

```text
serve_service_request
```

### Depth assessment

- kind: facade
- delegates to: `operations`

## `owner_interface`

### Owns

R0-29's server-rendered forms over the owner's operations. A19 rules 1 and 2:
every stored value rendered as text escaped for its place, no script of its
own, a content security policy forbidding any. A01 rule 1: a request id made
when a create form is rendered. A04's consequence: every form sends the
revision of the card it rendered, or none for one that shows none; A12 rule
3's access version likewise. The session cookie and the CSRF value in its
forms (A13 rules 1, 5, 7), no personal value or secret in a URL (R0-29). The
newest backup's instant on its page (A18 rule 1). A16's upload, mapping and
confirmation pages.

### Knows

`models`, `random_values`, `owner_sessions`, `operations`.

### Must not own

Any check the server makes: the forms carry values, `operations` decides.

### Hides

HTML, escaping per context, the forms' hidden fields.

### Candidate public capabilities

```text
serve_owner_request
```

### Depth assessment

- kind: deep
- hidden mechanism: rendering every value as escaped text in script-free forms

## `instance_lifecycle`

### Owns

The start and the running instance: `configuration` first, then the backup
probe and `store`, then the listeners at the release's addresses, serving
nothing until every check passed and having `store` remove a store this start
made new when a listener cannot be opened (A17 rule 2); the
owner-only start, which opens the owner interface alone (A17 rule 1, A18
rule 9); the two surfaces, the owner interface's listener opened first; the 60-second pass
of `owner_sessions` and the minute look of `backups` (A13 rule 2, A18 rule 1);
that a restart ends every owner session (A13 rule 2).

### Knows

`models`, `release_declarations`, `configuration`, `store`,
`owner_sessions`, `backups`, `service_api`, `owner_interface`.

### Must not own

What any check or pass decides.

### Hides

The process's start sequence, its timers and the two listening surfaces.

### Candidate public capabilities

```text
start_instance
```

### Depth assessment

- kind: facade
- delegates to: `configuration`, `store`, `owner_sessions`, `backups`, `service_api`, `owner_interface`
