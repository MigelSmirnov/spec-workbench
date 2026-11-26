# State 3 — Registry module responsibilities

Draft of 2026-11-01, reopened on 2026-11-11 by the pre-contract data
closure: every value the generated code reads has one home, the constants of
`data_provider` (SPEC_STANDARD §6.10, §15.3.1), which replaces the former
release_declarations module; the environment is read by `runtime_settings` alone
(§6.11), and `configuration` checks what it loaded; M12 AuditSequence is
`audit_log`'s. Derived from the accepted State 2 decisions A01–A22
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
| A01 | `projects` | `given_values`, `data_provider`, `customers`, `artifact_pointers`, `store`, `owner_interface` |
| A02 | `given_values` | `data_provider`, `projects`, `customers`, `artifact_pointers`, `agent_sessions`, `migration_import` |
| A03 | `projects` | `customers` |
| A04 | `operations` | `projects`, `customers`, `agent_sessions`, `owner_interface` |
| A05 | `projects` | `customers`, `artifact_pointers`, `agent_sessions`, `operations` |
| A06 | `store` | `projects`, `customers`, `artifact_pointers`, `agent_sessions`, `audit_log`, `migration_import` |
| A07 | `artifact_pointers` | `store` |
| A08 | `artifact_pointers` | `operations`, `service_access` |
| A09 | `service_access` | `data_provider`, `operations`, `model_fields` |
| A10 | `agent_sessions` | `operations` |
| A11 | `agent_sessions` | `operations`, `owner_interface` |
| A12 | `agent_sessions` | `owner_interface` |
| A13 | `owner_sessions` | `data_provider`, `clock`, `random_values`, `upload_framing`, `owner_interface`, `operations`, `model_fields` |
| A14 | `audit_log` | `operations` |
| A15 | `audit_log` | `store`, `backups` |
| A16 | `migration_import` | `owner_sessions`, `owner_interface`, `projects`, `customers`, `artifact_pointers` |
| A17 | `configuration` | `runtime_settings`, `data_provider`, `store`, `backups`, `service_access`, `owner_sessions`, `instance_lifecycle` |
| A18 | `backups` | `data_provider`, `store`, `clock`, `instance_lifecycle`, `owner_interface` |
| A19 | `owner_interface` | `data_provider`, `store`, `migration_import`, `model_fields` |
| A22 | `artifact_pointers` | `data_provider`, `migration_import` |

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
each surface it opens — the service API not at all in an owner-only start
(A17 rule 1) — on a listener of its own, at its configured address, and
decides nothing about reachability beyond that listener's own form — bound
exclusively, an IPv6 one for IPv6 alone (A17 rule 1).
The modules are the parts of that one program, not services. Only `store`
opens a SQLite database — the store's, and the decrypted copy of a backup that
`backups` hands it by path to check — and only `backups` names, renames or
deletes a file in the backup location; `store` writes and opens one there only
at the temporary path `backups` names for it. `store` holds the connection and
the transaction and decides which record goes into which row; the row
statements themselves are executed by `store_persistence`, its companion,
which only `store` calls, over that connection (below). The dependency direction is fixed, from the bottom up:

```text
models
data_provider
clock, random_values, given_values, upload_framing, model_fields
runtime_settings
configuration
store_persistence
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
  `operations` too but opens no write transaction: `owner_sessions` applies
  it under its own locks (A13 rule 2); one that must read the store first —
  an upload, and the import's confirmation step, check the closure (A16
  rule 2) — reads it in one read transaction through
  `store.read_in_transaction`. For every other change, `operations` opens
  the transaction through `store.run_in_transaction`,
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
  project's published pointers, is joined by `operations`. Which facts of
  an answer are `personal_data` ("Disclosure classes by field") is one table
  of the release, `data_provider`'s `PERSONAL_DATA_FIELDS`, of (answer model,
  field) pairs (owner, 2026-11-17); every other fact an answer carries is
  `business_confidential` and none is `open`. The table classifies answers
  only: the uploaded import file, `personal_data` by State 1's table, is
  never an answer's field — `owner_sessions` keeps it in memory and no
  answer carries its bytes (A16 rule 2). `operations` computes an answer's class as the highest of its
  facts' — `personal_data` when one of those fields holds a value — and refuses the answer whole
  when it is above the caller's highest (A09 rule 4): a service's from
  `service_access`, and for the owner `personal_data`, the highest class, so
  no owner answer is refused for its class (Actors and trust boundaries,
  "Personal data").
- **Time.** An action has one instant: `operations` reads it from
  `clock.recorded_now` once, when the action's transaction begins, takes
  today's date as that instant's UTC date itself, so the two cannot fall on
  different dates at midnight, and hands both to every module the
  action records a new instant or compares a date in. The import's records
  keep the instants their source holds ("Revisions and times"); the Customers
  it makes, its closure and its entry carry the action's one instant. The
  limits of A13 are read by `owner_sessions` from `clock.monotonic_reading`,
  an owner request's arrival among them — for an upload, once its bounded
  head has been read (A13 rule 2);
  the minute look of A18 rule 1 by `backups` from `clock.recorded_now`; a
  backup's instant is the one `store` reads at the read that fixes the
  copy's snapshot (A18 rule 1), which `backups` records and never reads
  itself; `instance_lifecycle` times its two passes by
  `clock.monotonic_reading`. No other module reads a clock.
- **Random values and secret comparison.** Every identity Registry mints
  ("Identity formats") and every 32-byte value of A13 rule 7 comes from
  `random_values`; every comparison of a presented secret with a held one goes
  through `random_values.equal_in_constant_time` (A13 rule 7, A17 rule 6).
- **What the release declares.** Every value the generated code reads that
  is neither a setting of the environment (`runtime_settings`) nor a member
  of an enumeration or a field's type in `models` — statuses, kinds,
  languages, a whole number —
  is a constant of `data_provider`, its one home (SPEC_STANDARD §6.10, §15.3.1): the artifact vocabulary with each
  type's owner service (A22), the services' rights (A09 rule 2), the store
  version and the store's temporary-name suffix (A17 rule 5), the two backup
  prefixes, the daily time, the look and the retention (A18 rules 1, 4, 5),
  a backup record's version, the key digest's domain and the key
  derivation's info (A18 rules 1, 3),
  the import file's size limit (A19 rule 4) and the bound of an upload
  form's head (A13 rule 5), the fields that hold `personal_data` (A09 rule 4),
  the service API's session header and its HTTP statuses (owner,
  2026-11-17), the release's and contract's
  versions, the owner
  session's limits (A13), the lengths of A01 rule 1, A02 rule 4, A13 rule 7
  and A17 rule 3. A module that needs one imports it; nothing reads them from
  the configuration or the store (A22 rule 2, A09 rule 1), and no module
  restates one.
- **The environment.** Only `runtime_settings` reads the process
  environment, and only the `REGISTRY_` items A17 rule 1 lists (owner,
  2026-11-11); every other module receives the settings it needs from
  `configuration`, which checks them.
- **Secrets never leave.** No module puts a secret, a confirmation value, a
  CSRF value or an owner session's identity into a record, a log line, a diagnostic,
  an audit entry, a URL or the data of an answer Registry gives a service or
  the owner (A13 rule 7, A17 rule 6) — but for the forms `owner_interface`
  serves, which carry their session's own CSRF value and the pending
  confirmation value, and the cookie, which carries the session's identity,
  as below. An answer in A13 rule 7 and A17 rule 6 is what Registry gives a
  caller outside it (R0-23, R0-37); a value one module returns to another
  inside the process is not one, and so `configuration` gives a secret to
  the module that uses it.
  An agent session's identity, which Kernel names (R0-53), is not one of them:
  M06, M07 and M09 record it. The owner session's identity travels only in its
  cookie, the CSRF and confirmation
  values only in the forms `owner_interface` serves (A13 rule 7).
  `configuration` holds the secrets and hands each only to the module that
  uses it, which asks for it: the service tokens to `service_access`, the
  owner credential to `owner_sessions`, the backup key to `backups`.
  `random_values` compares a presented secret with a held one when asked and
  keeps neither.
- **Reading a model's fields.** Every callable that walks model values
  generically — `operations` classing an answer at any depth (A09 rule 4),
  `owner_sessions` binding a confirmation to every field of its inputs in
  their declared order (A13 rule 6), `service_api` writing an answer in its
  wire format, `owner_interface` rendering a page's values (A19 rule 1) and
  building a request's values from its form's paths — takes a model's
  fields only from `model_fields`, and tells a model from any other value
  by `model_fields`' answer alone (owner, 2026-11-26). Each caller keeps its
  own traversal: what it does with a field's value, how deep it goes, a
  tuple's elements, an enumeration member. Which field is `personal_data`
  stays `data_provider`'s personal data table, classed by `operations` (A09
  rule 4). Why the reading is one module's, and the repairs that led to it,
  are recorded in `81_module_review.md` (2026-11-25 and 2026-11-26).

## `models`

### Owns

The models M01–M29 as the domain's vocabulary — among them the forms of a
pointer's publisher and an audit entry's subject (M13–M19), the owner
session's pending confirmation and uploaded file (M20, M21) and the row
shapes of the data provider's eight tables (M22–M29), whose rows are
`data_provider`'s — and the declared vocabularies of
State 1 as enumerations — for the artifact types only the shape of a type
with its owner service (M22), whose rows are `data_provider`'s, so a stored
pointer of a type a later release removed still reads (A22 rule 4) — and the disclosure class
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
does not move and which counts a suspension of the host. Nothing else: the
module is emitted from the `system_clock_backend` IR (A13 rule 2), which
owns exactly these two readings; an action's today is `operations`'.

### Knows

Nothing.

### Must not own

Any limit or schedule: the 8 hours and the 30, 15 and 10 minutes are
`data_provider`'s constants that `owner_sessions` applies; the 03:00 is one
that `backups` applies; the 60 seconds of the session pass and of the minute
look are ones that `instance_lifecycle` applies, calling `owner_sessions` and
`backups` at those intervals.

### Hides

The host's clocks, and their replacement by fixed readings in tests.

### Candidate public capabilities

```text
recorded_now
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

`data_provider`, for the length of a secret value (A13 rule 7).

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

## `data_provider`

### Owns

The typed constants of the data closure, the one home of each value the
generated code reads that is neither a setting of the environment
(`runtime_settings`) nor a member of an enumeration or a field's type
(`models`) (SPEC_STANDARD
§6.10, §15.3.1; reopened 2026-11-11, replacing the former
release_declarations module): the
artifact types with their owner services, the first release's one row
(`estimate`, PresuPro) (A22); A09 rule 2's table of the services, their
operations, and each service's highest class; the store version and the store's
temporary-name suffix (A17 rule 5); the kept and temporary backup prefixes,
neither beginning with the other, the daily time, the minute look and the
retention of 30 × 24 hours (A18 rules 1, 4, 5); a backup record's version,
the key digest's domain and the key derivation's info (A18 rules 1, 3); the import file's size limit
(A19 rule 4); the release's own version and its contract version, which
every audit entry names (M09) and a backup's record names (A18 rule 1); the
owner session's limits — 8 hours, 30 minutes, the 15
minutes and five refusals of the sign-in, the 10 minutes of a confirmation,
the 60 seconds of the pass (A13); a listen port's bounds (A17 rule 1); the request id's 128 characters (A01 rule
1), the alias's 40 and the characteristics' bounds (A02 rule 4), the 32 bytes of a secret value and of a
configured secret (A13 rule 7, A17 rule 3); the number of each of A04 rule
6's six stages, which every refusal of a check carries (A04, owner,
2026-11-17); the first revision of a Project and of a Customer (State 1,
"an ordinal starting at 1") and an agent session's first access version
(A12 rule 1); the (answer model, field) pairs that hold State 1's
`personal_data` facts (A09 rule 4, "Disclosure classes by field"); the
service API's wire constants — the header that names Kernel's agent session
(R0-53), the status of an accepted answer, 200, and each refusal code's
status, as v1 answered: `not_found` 404, `internal_error` 500, every other
code 422 (owner, 2026-11-17); and the bound of the head an upload form sends
before its file, its CSRF field among it (A13 rule 5, owner, 2026-11-17);
the listeners' read timeout, how long a listener waits for a request's next
bytes before it closes the connection (State 2 round-90 T8); the bounds of a
listener's staged close, how long and how many bytes it reads and drops
after answering a request whose body it did not read to its end; which
audit action M09 has each accepted owner action write (R0-58) (owner,
2026-11-24).
The list names groups; the data closure names each constant,
and every one is exported.

### Knows

`models`, for exactly the row models and enumerations of its eight tables:
`ArtifactTypeOwner` (a type with its owner service) and `ServiceName` for
`ARTIFACT_TYPE_OWNERS`; `ServiceRight` (a service and an operation) with
`ServiceName` and `ServiceOperation` for `SERVICE_RIGHTS`;
`ServiceHighestClass` (a service and its highest class) with `ServiceName`
and `DisclosureClass` for `SERVICE_HIGHEST_CLASSES`; `PersonalDataField` (an
answer model's name and a field's) for `PERSONAL_DATA_FIELDS`;
`RefusalHttpStatus` (a code and its status) with `RefusalCode` for
`REFUSAL_HTTP_STATUSES`; `OwnerActionRoute` (an owner action, its method and
path, whether it is a change and whether it touches an uploaded file) with
`OwnerAction` for `OWNER_ACTIONS`; `OwnerAuditAction` (an owner action,
a customer mark's transition or a project erasure's kind where the action
has one, and the audit action it writes) with `OwnerAction`,
`CustomerTransition`, `ProjectErasure` and `AuditAction` for
`OWNER_AUDIT_ACTIONS`; `OwnerFormField` (an owner form field's name, the
model it fills and how its text is read) with `OwnerFormCarrier` and
`FormValueKind` for `OWNER_FORM_FIELDS`. Its other constants are scalars and import nothing.

### Must not own

Behaviour, selection, validation or defaults: what a vocabulary change does
to existing pointers and whether a type is declared (A22 rules 3–5,
`artifact_pointers`), how a right is checked (`service_access`), anything
read from the configuration or the store.

### Hides

The values from every generator's prompt: a generated consumer is given the
name and type of a constant and imports it, so the running code reads the
value while the generator never sees it (SPEC_STANDARD §15.9).

### Candidate public capabilities

```text
ARTIFACT_TYPE_OWNERS
SERVICE_RIGHTS
SERVICE_HIGHEST_CLASSES
STORE_VERSION
STORE_TEMPORARY_SUFFIX
BACKUP_KEPT_PREFIX
BACKUP_TEMPORARY_PREFIX
BACKUP_DAILY_TIME_UTC
BACKUP_LOOK_SECONDS
BACKUP_RETENTION_HOURS
BACKUP_RECORD_VERSION
BACKUP_KEY_DIGEST_DOMAIN
BACKUP_KEY_DERIVATION_INFO
IMPORT_FILE_MAX_BYTES
RELEASE_VERSION
CONTRACT_VERSION
OWNER_SESSION_MAX_HOURS
OWNER_SESSION_IDLE_MINUTES
SIGN_IN_WINDOW_MINUTES
SIGN_IN_REFUSAL_LIMIT
SIGN_IN_LOCKOUT_MINUTES
CONFIRMATION_VALID_MINUTES
SESSION_PASS_SECONDS
REQUEST_ID_MAX_CHARACTERS
ALIAS_MAX_CHARACTERS
WHITE_SPACE_CODE_POINTS
OBJECT_FLOOR_AREA_MIN_EXCLUSIVE
OBJECT_ROOMS_MIN
SECRET_MIN_BYTES
LISTEN_PORT_MIN
LISTEN_PORT_MAX
REFUSAL_STAGE_AUTHENTICATION
REFUSAL_STAGE_AGENT_SESSION
REFUSAL_STAGE_EXISTENCE
REFUSAL_STAGE_VALUES
REFUSAL_STAGE_VERSION
REFUSAL_STAGE_LIFECYCLE
REVISION_FIRST
ACCESS_VERSION_FIRST
PERSONAL_DATA_FIELDS
SERVICE_AGENT_SESSION_HEADER
SERVICE_ANSWER_STATUS
REFUSAL_HTTP_STATUSES
UPLOAD_FORM_HEAD_MAX_BYTES
LISTENER_READ_TIMEOUT_SECONDS
OWNER_ACTIONS
OWNER_FORM_FIELDS
OWNER_FORM_POSITION_MARK
OWNER_FORM_PATH_SEPARATOR
OWNER_TARGET_PARAMETER
OWNER_CSRF_FIELD
OWNER_SESSION_COOKIE_NAME
OWNER_SESSION_COOKIE_ATTRIBUTES
OWNER_AUDIT_ACTIONS
LISTENER_CLOSE_DRAIN_SECONDS
LISTENER_CLOSE_DRAIN_MAX_BYTES
TEXT_ENCODING
TEXT_REPLACEMENT_CHARACTER
CONTENT_TYPE_HEADER
CONTENT_LENGTH_HEADER
SERVICE_AUTHORIZATION_HEADER
SERVICE_AUTHORIZATION_SCHEME
SERVICE_ANSWER_CONTENT_TYPE
SERVICE_INSTANT_UTC_MARK
OWNER_COOKIE_HEADER
OWNER_SET_COOKIE_HEADER
OWNER_CONTENT_SECURITY_POLICY_HEADER
OWNER_FORM_MEDIA_TYPE
UPLOAD_FORM_MEDIA_TYPE
UPLOAD_BOUNDARY_PARAMETER
UPLOAD_FILENAME_PARAMETER
UPLOAD_DELIMITER_PREFIX
UPLOAD_CLOSE_SUFFIX
BACKUP_KEY_DIGEST_PREFIX
BACKUP_KEY_DIGEST_SEPARATOR
PROJECT_VALUE_FAILURE_KINDS
CUSTOMER_ELIGIBILITY_REFUSALS
AGENT_SESSION_FAILURE_KINDS
RUNTIME_SETTING_ORDER
RUNTIME_SETTINGS_REQUIRED
RUNTIME_SETTINGS_ALL_OR_NONE
STORE_COMPANION_SUFFIXES
OWNER_CHANGE_ACTIONS
SERVICE_CHANGE_OPERATIONS
REQUEST_ID_UNPRINTABLE_CATEGORIES
DIGEST_ALGORITHM
```

### Depth assessment

- kind: deep
- hidden mechanism: the one home of every policy value; a value moves here
  once and every reader imports it

## `given_values`

### Owns

A02: the one reading of a value a caller gives — a required value blank or
white space only is missing, white space being the code points of the
imported `WHITE_SPACE_CODE_POINTS` constant (A02 rule 1), a present value is kept exactly as written, an
optional value blank is absent. A01 rule 1's check of a request id's form —
printable text of at most 128 characters, not blank — and A01 rule 6's
comparison of the facts of a create with a record's current facts, as A02
reads them, a fact of several parts by its parts whatever their order. A02
rule 4: a present value outside the form State 1 declares — the alias's
length, a value outside its enumeration, a characteristic out of its range —
answered as a failure naming every such value and its kind, which the
caller refuses at stage (4) or, for the import's mapping, shows (A16 rule
1).

Reading the text forms a value is written in, wherever Registry reads one
(owner, 2026-11-26): an instant, a calendar date, a decimal number, a whole
number, a version's digits and a listener's address (A17 rule 1). Each form
has one reading here, which answers the value the text names or that the
text is not of its form; every module that reads such a text has it read
here and nowhere else.

### Knows

`models`, `data_provider`.

### Must not own

Which values an action requires (each record's module says), whether a create
is a repeat (that needs the record: `projects`, `customers`,
`artifact_pointers`), whether a request id is random (the caller's duty, A01
rule 1), what a caller does with a value it has read: whether an instant
or a date is in order with another, whether versions run without gaps,
which address is listened on.

### Hides

White-space classes, the printable-text check, the order-free comparison of
composite facts, the grammar of each text form.

### Candidate public capabilities

```text
read_required_text
read_optional_text
check_request_id_form
check_value_forms
facts_equal_for_repeat
read_instant_text
read_date_text
read_digits_text
read_listen_address
```

### Depth assessment

- kind: deep
- hidden mechanism: the one rule by which every given value is read and compared

## `upload_framing`

### Owns

The multipart framing of an upload (owner, 2026-11-17): an upload form
sends its CSRF field as the first part of its body and the file as the
second, so that the CSRF value travels in a form (A13 rules 5, 7) and the
file still reaches `migration_import` unread. Reading the body's head alone
— the boundary the request's content type names, the first part, which
must be the CSRF field, the form field the data provider's
`OWNER_CSRF_FIELD` names (owner, 2026-11-24), and the second part's headers — at most the
data provider's `UPLOAD_FORM_HEAD_MAX_BYTES`, answering the CSRF value, or
none for a head of another form or longer than the bound; and the file
part's bytes as a stream that ends where the part ends, read only when its
reader asks and never buffered beyond the delimiter it must look ahead for;
and the file part's declared length — the request's declared length less
the head it read and the closing delimiter with its final `--` and line end,
or none when the request declares none — so that a file of exactly the
import limit is not refused for its framing (A19 rule 4). A request that
declares less than the head it read and the closing delimiter is a head of
another form. A stream that ends before the closing delimiter is a failure
of the file part's stream, which `migration_import` refuses as a file that
cannot be read (`file_unreadable`), replacing nothing kept (A16 rule 2).

### Knows

`models`, for `ByteStream`, the body it reads, `UploadHead`, which
`read_upload_head` answers, and `UploadBody`, the port `MultipartFileBody`
implements; `data_provider`, for `OWNER_CSRF_FIELD` and
`UPLOAD_FORM_HEAD_MAX_BYTES`.

### Must not own

Any check of the CSRF value (`owner_sessions`), the size limit of the file
and its reading (`migration_import`, A19 rule 4), the HTTP server and its
connection (`instance_lifecycle`), the forms and pages (`owner_interface`).

### Hides

The multipart syntax: boundaries, part headers, the look-ahead for the
closing delimiter.

### Candidate public capabilities

```text
read_upload_head
```

### Depth assessment

- kind: deep
- hidden mechanism: the multipart framing of an upload's body

## `model_fields`

### Owns

Reading the declared fields of a model value — each field's name and value,
in the order the model declares them — and telling a model from any other
value (owner, 2026-11-26; "Reading a model's fields"). A model is a value
of one of the models of `models`, whichever it is; every other value is
answered as no model. Of the decisions whose
rules need a walk it owns that reading alone, as a consumer: for A09 rule 4,
the fields of an answer and of every model nested in it, which `operations`
classes; for A13 rule 6, the fields of a confirmation's inputs in their
declared order, which `owner_sessions` binds; for A19 rule 1, the fields of
each model whose values `owner_interface` renders. It serves in the same way
the walks of two State 3 decisions that no State 2 decision states:
`service_api`'s wire format (owner, 2026-11-17) and `owner_interface`'s
reading of a request by the paths of the owner form table (owner,
2026-11-25); it owns no rule of either.

### Knows

Nothing. It reads values of the models of `models` without naming any of
them.

### Must not own

Which field is `personal_data` (`data_provider`'s personal data table,
classed by `operations`), how a value is encoded, digested, written or
rendered, or any traversal policy of its callers: how deep a walk goes, what
it does with a tuple's elements, an enumeration member or a nested model.

### Hides

How a model's declared fields and their order are found.

### Candidate public capabilities

```text
model_items
```

### Depth assessment

- kind: deep
- hidden mechanism: the one reading of a model's declared fields that every generic walk shares

## `runtime_settings`

### Owns

A17 rule 1's reading of the environment, and only it: the closed table of
the `REGISTRY_` items — the store's location, the backup location, the
backup key, the owner credential, the owner interface's address, the four
service tokens and the service API's address — loaded at each
call of `load_runtime_settings` into the settings. The table holds, for each
item, its variable's name, the settings field it fills and its type, which
is text; nothing else. Every item is optional at this level and absent when
unset, and is taken as it is set — no trimming, no case or Unicode
normalization, no default (A17 rule 5) — so that `configuration` checks
presence and form in A17 rule 2's one order. A variable that names no item
is not read (owner, 2026-11-11). The table is its own: the data closure
writes it once, as `config.runtime_environment_variables`, and no other
module holds a name. A secret's length is counted in the bytes of its UTF-8
encoding, and a presented credential is compared in those bytes (A17 rules
3, 6). Emitted deterministically (SPEC_STANDARD §6.11).

### Knows

`models`.

### Must not own

Any check of an item or across items — presence, form, the tokens all or
none, a secret's length, two secrets equal, the store and backup location
apart — which are `configuration`'s; opening the store or probing the backup location.

### Hides

Environment reading.

### Candidate public capabilities

```text
load_runtime_settings
```

### Depth assessment

- kind: deep
- hidden mechanism: the closed environment table, read as set

## `configuration`

### Owns

A17: the start checks of rule 2 that need no file, in its one order, over
the settings `runtime_settings` loads as set — the service tokens of the services
`data_provider`'s rights table lists with the service API's address, all or
none, the other items present,
each well formed, the addresses' ports different, each secret at least the 32 bytes `data_provider` holds, no
two secrets equal — with the diagnostic naming the failed item and never its
value; that no default is applied (rule 5); an owner-only start when no token
is given (rule 1); and last the path checks of rule 5 that need no file — the
store and the backup location apart, compared with every link resolved. The
checks after them — the backup probe (`backups`), opening or making the store
(`store`) and the listeners — are run in rule 2's order by
`instance_lifecycle`, which calls this module first.

### Knows

`models`, `given_values`, `data_provider`, `runtime_settings`.

### Must not own

Reading the environment (`runtime_settings`), opening or making the store
(`store`), probing the backup location (`backups`), what a token may do
(`service_access`), the credential check of a sign-in (`owner_sessions`).

### Hides

Path resolution and the order of the checks.

### Candidate public capabilities

```text
load_configuration
give_service_tokens
give_owner_credential
give_backup_key
give_backup_location
```

### Depth assessment

- kind: deep
- hidden mechanism: the ordered start checks of A17 over the loaded settings

## `store`

### Owns

The one SQLite database (L19) and its connections — the one the
transactions of actions run on, and the read connection a backup's copy
takes its snapshot on while they go on, under the engine setting State 6
fixes, the snapshot fixed by its first read, of the audit counter, with the
clock read then (A18 rule 1): opening it for reading and
writing at start, or making a new, empty store of the release's version —
holding no record but M12 AuditSequence at 0, which the release's statements
make with the store, so `store` needs nothing from `audit_log` — under
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
copy (A18 rule 1). The counter is a value `audit_log` keeps through `store`,
which holds it where the release's statements put it: `audit_log` alone
decides when it moves and what it means (A15 rule 5), and `store` reads it as
the copy's first read, and in a checked file, as it reads any stored value,
deciding nothing about it — so the reading needs no call upward to
`audit_log`. The store this start opened: `store` keeps the `RegistryStore`
`open_store` opened for the process and gives it to the module that runs
an action's transaction (owner, 2026-11-17).

### Knows

`models`, `clock`, `data_provider`, `configuration`, `store_persistence`.

### Must not own

Which record a module writes or when; any domain check; the audit log's
sequence rule (A15 rule 5 is `audit_log`'s, which keeps its counter through
`store`); encrypting or keeping a backup (`backups`).

### Hides

Which record goes into which row and which rows a list reads, the
transaction and lock mechanics,
the temporary-name dance of a new store, the integrity pragmas.

### Candidate public capabilities

```text
open_store
opened_store
discard_new_store
run_in_transaction
read_in_transaction
check_store_file
copy_store_snapshot
```

### Depth assessment

- kind: deep
- hidden mechanism: the one SQLite database, its transactions and its one write lock


## `store_persistence`

### Owns

Only the deterministic SQLite repository class and schema function lowered
from `persistence_backend/v3` for the store's closed tables: one table per
durable model — Project, Room, Customer, ArtifactPointer, AgentSession,
AuditEntry, MigrationClosure, AuditSequence (`60_data_closure.json`,
`persistence`). A row is the store's envelope of one record: the columns a
lookup, a list's order or a deletion compares, and the record itself, whole.

### Knows

`models`.

### Must not own

The connection or its transaction, minted identities, which rows a list reads
and in which order a module receives them, which records an erasure removes,
or any rule of another module — these are `store`'s or the record module's;
and any file — the store's file is `store`'s, a file in the backup location
`backups`' (above). It is part of the store of A17 and A18: only `store` calls
it, inside the transaction `store` opened, so no other module touches the
database through it.

### Hides

SQLite table creation, row codecs and the typed insert, load, list, update
and delete statements, including which column each lookup compares.

### Candidate public capabilities

```text
SqliteStoreRepository
create_store_schema
```

### Depth assessment

- kind: deep
- hidden mechanism: version-bound SQLite lowering from persistence_backend/v3
## `audit_log`

### Owns

A14 and A15: appending an entry (M09) inside the transaction of the change it
records, with the next sequence number after the last the store's history ever
wrote, kept apart from the entries — M12 AuditSequence, made at 0 with a new
store — so an erasure never lowers it (A15 rule 5);
the actions that write an entry and the subject each names (M09); the outcome
`accepted` (A14 rule 6); that no entry is ever changed (A15 rule 1); the
erasure before a date — not later than today, every entry before 00:00 UTC of
it removed, so that the erasure's own entry `operations` appends after it,
with its confirmation id, also when nothing was removed, is never removed by
it (A15 rules 3, 4, 6); reading the log by sequence
number for the owner (A15 rule 2, A06 rule 6). A backup's record takes the
last sequence number from the copy's own first read (`store`), not from
`audit_log`.

### Knows

`models`, `data_provider`, `store`.

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

`models`, `data_provider`, `random_values`, `configuration`.

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
which its state-changing requests apply one at a time; the session's
validity at a request's arrival, read when `operations` hands the request to
the session check — for an upload after its head, at most
`UPLOAD_FORM_HEAD_MAX_BYTES`, has been read (rule 2; owner, 2026-11-17);
the CSRF value (rule 5),
given for a valid session to the interface that renders its forms (owner,
2026-11-17);
the pending confirmation — made when a step is shown, bound to the action, its
target, the revision or access version the step showed or that it showed none,
and the digest of its inputs; valid 10 minutes, used up by the first
submission that carries it, cleared by an expired one (rule 6). The uploaded
import file each session keeps in memory, replaced by the next upload — one of
the same bytes included — and dropped with the session or by an accepted
import (A16 rule 2), and the instance's one import lock, taken before any
session's lock.

### Knows

`models`, `data_provider`, `clock`, `random_values`, `model_fields`,
`configuration`.

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
give_session_csrf
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
repeat answering the pointer whatever its status now. A22, as its primary
owner: a type is declared when `data_provider`'s artifact type table holds it,
and its owner service is that row's; rules 3–5: a removed type's pointers
kept as they are, its publish, latest read and withdrawal refused. The pointers' list (A06 rule 3), the latest of a type, and a
project's `published` pointers in that list's order, for the agent projection
(State 1, "Projections and answers"; A06 rule 8). Deleting every pointer of a
project deleted whole (R0-60), in the transaction `operations` opens for it.

### Knows

`models`, `given_values`, `random_values`, `store`,
`data_provider`, `projects`.

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
named; registering a session excepted, which is checked for Kernel's token
only (A10 rule 1) — and its one not-found answer for a refusal, inside the call's
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
(A19 rule 4) — from the declared length and the unread stream
`owner_interface` hands on: a declared length over the limit refused before
any byte is read, otherwise at most one byte more than the limit read and
refused as soon as it holds more — refusing at upload a file that cannot be read, holds two
projects with one id or a project without a readable id or status (rule 3);
the mapping for the picks — rooms, pointers, names and aliases, the Customers
it will make, malformed records and conflicting ids (rules 1, 3–5); that the
confirmation step is not shown while the mapping shows an error (rule 1);
building that mapping once more inside the confirming transaction, applied
only when clean (A16 rule 6), and, in the one transaction `operations`
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
`data_provider`, `owner_sessions`, `customers`, `projects`,
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

`models`, `clock`, `given_values`, `configuration`, `data_provider`, `store`.

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
state, its action the row of the data provider's `OWNER_AUDIT_ACTIONS` for
an owner action (owner, 2026-11-24). A14 rule 5: `operations` mints a confirmed action's confirmation id
inside the transaction only after the action's module has answered that it is
accepted and changed state — or, for the erasure of old audit entries, that it
is accepted, also when it removed nothing (A15 rule 6) — and hands it to the
entry and, for the import, to the closure; a refused or unchanged action
mints none. Resolving a pointer a withdrawal names to
its project, through `artifact_pointers.project_of_pointer`, before stage (2)
checks that project against the session's set (A08 rule 7). A05 rule 2's no entry and no
confirmation id for a repeat. The compositions: erasing a project (with
`agent_sessions` and `artifact_pointers`), granting through an access request,
joining the agent projection with its published pointers. The store
`store` opened, through `store.opened_store`, and the backup location,
through `configuration.give_backup_location`, are asked by `operations`
when an action needs them (owner, 2026-11-17). The import's confirmation
binding: the kept upload's number and digest with the picks when the step
is shown, the ones the submitted form carries when it is confirmed (owner,
2026-11-24).

### Knows

`models`, `data_provider`, `clock`, `random_values`, `given_values`, `model_fields`,
`configuration`, `store`, `audit_log`, `service_access`, `owner_sessions`, `customers`,
`projects`, `artifact_pointers`, `agent_sessions`, `migration_import`,
`backups`.

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
token, the session header and the request, calling `operations`,
answering in the wire format States 5 and 6 declare — v1's (owner,
2026-11-17): the answer's fields with no kind on the wire, `validate` and
`context` as v1 wrote them (R0-04), and v1's HTTP statuses, the data
provider's; nothing reachable without a token.

### Knows

`models`, `data_provider`, `model_fields`, `operations`.

### Must not own

Any check, right or record rule.

### Hides

The reading and writing of its wire format. The HTTP server, its
connections and HTTP's framing are `instance_lifecycle`'s listener's, as for
the owner interface.

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
confirmation pages. An upload form sends its CSRF field as the first part
of its multipart body (owner, 2026-11-17): `owner_interface` has
`upload_framing` read that head alone and hands the file part on as its
declared length, which `upload_framing` derives, and an unread stream that
ends where the part ends, never read or buffered here, so that
`migration_import` alone applies A19 rule 4 to the file. The session cookie
is always HTTPS-only (A13 rule 1, owner, 2026-11-17): from another machine
the interface is reached only through HTTPS (R0-29); whether a browser on
Registry's own machine sends it over plain HTTP to a loopback address is
that browser's, and where it does not, HTTPS there too is the host's
(Explicit exclusions). Every
form of a page rendered for a valid session carries the CSRF value
`owner_sessions` gives for the session; the sign-in form, made without a
session, carries none (A13 rule 4). Which action a request names, by its
method and path, and whether it is a change or touches an uploaded file, are
the rows of the data provider's `OWNER_ACTIONS`; its target is the query
parameter `OWNER_TARGET_PARAMETER` names, its CSRF value the form field
`OWNER_CSRF_FIELD` names, every other field it reads or a page writes a row
of `OWNER_FORM_FIELDS` (owner, 2026-11-25), the session cookie's name
`OWNER_SESSION_COOKIE_NAME` and its attributes
`OWNER_SESSION_COOKIE_ATTRIBUTES`, and a page's HTTP status the service API's
`SERVICE_ANSWER_STATUS` and `REFUSAL_HTTP_STATUSES` (owner, 2026-11-24). A
request it cannot read — a body or a head that fails, a form that cannot be
decoded — is handed on with no values, nothing partly read kept, and
answered by `operations` as any other; it never closes the connection
instead of answering (owner, 2026-11-24, option (a) of the question State 4
carried to State 7).

### Knows

`models`, for `HttpRequest`, `ByteStream` and `HttpResponse`, which its
surface takes and answers, `OwnerRequest`, `OwnerValues`, `OwnerAdmission`
and `OwnerAction`, which it reads, builds and matches; `OwnerFormCarrier`
and `FormValueKind`, by whose members it reads a form field's row; `OperationAnswer`,
which it renders by its fields, and of its variants the three it checks
by name: `RefusedAnswer`, rendered with its code's status, `SignedInAnswer`,
whose session it sets as the cookie, and `NewestBackupAnswer`, each of whose
outcomes it renders as itself; and `RefusalCode`, whose `UNAUTHENTICATED`
member it renders as the sign-in page;
`data_provider`, for `OWNER_ACTIONS`, `OWNER_FORM_FIELDS`,
`OWNER_FORM_POSITION_MARK`, `OWNER_TARGET_PARAMETER`,
`OWNER_CSRF_FIELD`, `OWNER_SESSION_COOKIE_NAME`,
`OWNER_SESSION_COOKIE_ATTRIBUTES`, `SERVICE_ANSWER_STATUS` and
`REFUSAL_HTTP_STATUSES`; `random_values`, for `mint_identity`, a create
form's request id; `model_fields`, for `model_items`, by which it reads a
model's fields when it renders a page or builds a request's values; `upload_framing`, for `read_upload_head` and
`MultipartFileBody`; `owner_sessions`, for `give_session_csrf`;
`operations`, for `perform_owner_operation`.

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
probe and `store`, then the listeners at the configured addresses, serving
nothing until every check passed and having `store` remove a store this start
made new when a listener cannot be opened (A17 rule 2); the
owner-only start, which opens the owner interface alone (A17 rule 1, A18
rule 9); the two surfaces, the owner interface's listener opened first,
each request's body handed on as a stream that ends where HTTP's own
framing ends the body — after its `Content-Length` bytes, or at the last
chunk of a chunked body — so that no reader of it waits for bytes the client
sends only after an answer, and no byte of another request is read as the
body's — HTTP's framing of every request of both surfaces, one
implementation: a request whose `Content-Length` or `Transfer-Encoding`
header is malformed is refused by the listener from its headers alone, its
connection closed, and reaches no surface; the body itself is never read
ahead by the listener, so a body that ends before its framing says, or
whose chunks are malformed, is a failure of the stream its reader sees
while reading it; a request answered before its body was read to its end
closes its connection by a staged close — its writing side shut, what the
client still sends read and dropped up to the data provider's
`LISTENER_CLOSE_DRAIN_SECONDS` and `LISTENER_CLOSE_DRAIN_MAX_BYTES`, then
closed — so the answer reaches a client still sending its body (RFC 9112
section 9.6; owner, 2026-11-24); the 60-second pass
of `owner_sessions` and the minute look of `backups` (A13 rule 2, A18 rule 1);
that a restart ends every owner session (A13 rule 2).

### Knows

`models`, `clock`, `data_provider`, `configuration`, `store`,
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
