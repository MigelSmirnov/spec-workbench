# State 6 — Registry exact contracts

## Status

Draft of 2026-11-16. The function inventory is `60_contract_plan.json`, the
signatures `60_contracts.json`, the typed models `60_model_closure_domain.json`
(the twelve State 1 models, the vocabularies and the data provider's row
models) and `60_model_closure_values.json` (every model the contracts
introduce, `contract_only`). This document records why the contracts have the
shape they have and how State 6 closes what earlier states carried to it. It
adds no fact: every field is one State 1 lists or one a State 5 output names.

Before this state could be written, two gaps upstream were closed by the
owner's decisions of 2026-11-16 and reopened States 3 to 5: `configuration`
gives each secret to the module that uses it, which asks for it
(`give_service_tokens`, `give_owner_credential`); and the clock is emitted
from `system_clock_backend` v6, which owns exactly the wall and the elapsed
readings, so an action's today is `operations`' (`_today_of`).

## Shape of the contracts

- **A refusal is a value.** An operation that may refuse answers a
  `discriminated_union` of its result and `Refusal` — code, stage of A04 rule
  6, and every failure of that stage with its kind and path (State 5,
  "Stages"). The specification's exceptions carry no typed field, so a
  refusal raised would lose the kinds and paths every caller renders; a
  failure of the store's own transaction is the one refusal no module
  decides, `internal_error` (`transaction_failed`), answered by `store`.
  `Refusal.stage` is an `int`, the number the wire format carries; its six
  values have one home each, the data provider's constants
  `REFUSAL_STAGE_AUTHENTICATION` to `REFUSAL_STAGE_LIFECYCLE` (owner,
  2026-11-17), which a refusing module imports as State 5's table lists.
  The stage is not a function of the code (`not_found` is stage 2 or 3),
  so it is neither derived nor a table; an enumeration would have changed
  the wire format every client reads. `internal_error` has no stage.
- **One answer type for the surfaces.** `operations` answers
  `OperationAnswer`, one union over every answer a service or the owner
  reads and `RefusedAnswer`; `service_api` writes it in its wire format and
  `owner_interface` renders it. The ports that run an action's step answer it
  too.
- **Steps are ports.** The type language has no callable and no generic
  (SPEC_STANDARD §12), so "the step to run, which receives the transaction"
  (State 5) is the `TransactionStep` interface, "the request's step, which
  receives the admitted session" the `OwnerStep` interface;
  `operations` implements them (`ServiceCallStep`, `OwnerRequestStep`,
  `OwnerActionStep`). Both ports are `models`' (SPEC_STANDARD §5): their
  `run` contracts belong to `models`, as `StoreRepository`'s do. Their
  implementations are `policy` (§5.1): `operations` holds no connection, file
  or socket, and every argument of their constructors is a model or a port.
  `implementation_obligations`: `TransactionStep` → `policy`
  [`ServiceCallStep`, `OwnerActionStep`]; `OwnerStep` → `policy`
  [`OwnerRequestStep`]; `StoreRepository` → `local`
  [`SqliteStoreRepository`]; `UploadBody` → `policy`
  [`MultipartFileBody`]; `ByteStream` → `external` (below).
- **`StoreTransaction` is a class** (owner, 2026-11-16, replacing the
  interface of the first draft). The transaction is the `StoreTransaction`
  class `store` owns, whose methods are the rows each record module reads and
  writes, in the orders A06 declares; only `store` constructs it, over the
  repository of the connection it opened, and hands it to the step. As an
  interface it had no legal implementation: `local` needs a deterministic
  backend to own the class, and `policy` forbids the connection the
  transaction holds (§5.1); a deterministic unit of work (§6.12) would be
  wanted only to generate the transaction's lifecycle itself, which is not a
  goal here. The narrow access to the store is kept by the class's explicit
  methods: record modules see those and nothing of the repository.
  The one place the exact type is lost is `run` of `TransactionStep`
  and its two implementations, typed `transaction: object`: a port of
  `models` naming a class of `store` makes `models` import `store`, which
  imports `models` — a cycle no start survives, and the Factory emits no
  `TYPE_CHECKING` import. Every other contract keeps `StoreTransaction`
  (§12, source 4). The guarantee is not left to a note:
  `run_in_transaction` and `read_in_transaction` hand the step the
  `StoreTransaction` they created, and `ServiceCallStep.run` and
  `OwnerActionStep.run` check on entry that they hold one and work with it
  from there; any other object is a wiring fault, raised before anything is
  read or written, so the transaction commits nothing and `store` answers
  `internal_error` (`transaction_failed`) as State 5 declares for a step
  that fails.
- **The upload body is a port** (owner, 2026-11-16; its multipart framing,
  owner, 2026-11-17). An upload's file reaches the step unread:
  `OwnerRequestStep`, `perform_owner_operation`, `read_import_mapping` and
  `_read_bounded` take it as `UploadBody`, a port of `models` with one
  method, `read(size)` — positional, the next bytes of the stream, at most
  `size`, empty at its end. The request's raw body is another port of
  `models` with the same one method, `ByteStream`, which is `external`: the
  HTTP server makes it, and `owner_interface` takes it as such. It ends where
  HTTP's framing ends the body — after its `Content-Length` bytes, or at a
  chunked body's last chunk: `MultipartFileBody` looks
  ahead the delimiter's length, and over the socket's own reader that
  look-ahead waits for bytes the client sends only after an answer (found by
  `experiments/registry/upload_framing_proto`, where curl hung until the
  reader was cut at `Content-Length`). An upload
  form sends its CSRF field first and the file second, as multipart, since a
  script-free form has no other way to carry the CSRF value with a file
  (A13 rules 5, 7). `upload_framing.read_upload_head` reads the head alone,
  at most `UPLOAD_FORM_HEAD_MAX_BYTES` (8192 bytes) — the boundary from the
  content type, the CSRF part, the file part's headers — and answers
  `UploadHead`: the CSRF value, the delimiter `\r\n--<boundary>` that ends
  the file part, and the file part's declared length — the request's
  declared length less the head read and the closing delimiter with its
  final `--\r\n` — or none of them. `UploadBody`'s one implementation is
  `MultipartFileBody(stream, delimiter)`, `policy`, owned by
  `upload_framing`: it gives the file part's bytes and ends before the
  delimiter, holding in memory no more than the delimiter's length of
  look-ahead, so `_parse_export` still receives the bare JSON object. A
  stream that ends before the delimiter makes its `read` raise, a failure of
  the stream that `read_import_mapping` answers `file_unreadable`, as any
  stream that fails; a request that declares less than the head and the
  delimiter answers an `UploadHead` with none of its values. Its
  module imports nothing that opens a file or a connection (§5.1), which is
  why it is not `owner_interface`'s: that module reads urlencoded forms. The
  file is read in portions, and only by the step. This keeps
  `OwnerRequestStep` a legal `policy` class and keeps the moment and the
  limit of the reading where State 5 put them: after admission, under the locks
  the request needs, inside the read transaction, by `_read_bounded` at most
  one byte past the imported `IMPORT_FILE_MAX_BYTES` constant, a declared
  length over it refused before the first read. A request refused at
  admission never reads its file. The declared length `_read_bounded`
  compares is the file part's, so a file of exactly 50 MB is read (A19 rule
  4's required test); a body with an epilogue after the closing delimiter
  declares more than its file, and only a file that near the limit is then
  refused early. The bytes are counted over the file part as it is read.
- **The store is a class.** A model field may not hold a connection, so the
  store this start opens is the `RegistryStore` class `store` owns; every
  store operation takes it. `store` keeps the one `open_store` opened and
  gives it through `opened_store` (owner, 2026-11-17; State 7 structure
  request of `operations`), so that `operations` hands it to every
  transaction without the surfaces carrying it.
- **What `operations` asks** (owner, 2026-11-17; State 7 structure requests
  of `operations`). The backup location, for the newest backup's instant on
  the owner's page, through `configuration.give_backup_location`. An
  answer's class through the data provider's `PERSONAL_DATA_FIELDS`: an
  answer is `personal_data` when one of the listed (answer model, field)
  pairs holds a value in it, nested views included, and
  `business_confidential` otherwise; `open` is never answered.
- **An owner request's arrival** (owner, 2026-11-17; A13 rule 2).
  `admit_owner_request` reads `clock.monotonic_reading` when it is called and
  checks the session there; an upload arrives once its bounded head has
  been read. Nothing is held between a request's headers and its admission.
- **The owner's pages** (owner, 2026-11-17; State 7 structure requests of
  `owner_interface`). `_render_owner_page` receives the session's CSRF value,
  which `owner_sessions.give_session_csrf` gives for the cookie's session, or
  none — the sign-in page's form carries none (A13 rule 4). The session
  cookie is always `Secure` (owner, 2026-11-17): a browser accepts it from a
  loopback address over plain HTTP, and from another machine the interface
  is reached only through HTTPS (R0-29, A13 rule 1).
- **The project list's choice** (owner, 2026-11-17; State 7 structure
  request of `projects`). `list_projects` takes `list_choice` as text, so a
  value outside its closed list is refused (`outside_closed_list`, A19 rule
  3) rather than unreadable; the list is `ProjectListChoice`: `active`, the
  active projects alone, and `with_archived`, the active ones with the
  archived ones. None is `active`: State 5 includes the archived ones only
  "when asked". There is no member for the archived alone ("never the
  archived alone"). A v1 client's `include_archived` flag is not read; such
  a client sends `list_choice` instead (R0-04 fixes only `context` and
  `validate`).
- **First ordinals** (State 7 structure requests of `customers` and
  `agent_sessions`). The revision a Project or a Customer is made or
  imported with is the data provider's `REVISION_FIRST`, an agent session's
  access version at registration its `ACCESS_VERSION_FIRST`; each change
  makes the next one more.
- **Given values arrive as text.** A create or a correction carries its
  values as given (`GivenCustomerFacts`, `GivenProjectFacts`,
  `GivenPointer`); the record's module reads and checks them through
  `given_values` (A02) and turns them into the model's types itself
  (`_object_from_given`). A choice from a closed list arrives as text too, so
  that a value outside it is refused (A19 rule 3) rather than unreadable.
- **Types.** Identities are `str`, a UUID's text or, for an agent session,
  the identity Kernel names; instants are timezone-aware UTC `datetime`
  (L16; the clock's v6 reading); dates `date`; the floor area `Decimal`
  (fixed precision, SPEC_STANDARD §15.8); the monotonic reading `int`
  nanoseconds.
- **Erased forms are views.** A read of an anonymised project or an erased
  Customer answers a view of the same union, `AnonymisedProject` or
  `ErasedCustomer`, never a refusal (State 5, "Erased records answer").

## Formats State 6 declares

- **The service API's wire format** (`service_api`; v1's, owner,
  2026-11-17): a request is one JSON object, `{"operation": <name>,
  "inputs": {...}}`, the session Kernel names in the header the data
  provider's `SERVICE_AGENT_SESSION_HEADER` names (`Registry-Agent-Session`)
  beside the bearer token, never among the inputs (R0-53). An answer is one
  JSON object:
  - for a refusal, `{"code", "stage", "failures": [{"kind", "path"}]}`, its
    `stage` JSON `null` for `internal_error`, the one refusal without a
    stage (State 5, "Closed set of refusal codes"; round-36 T2);
  - otherwise the answer's fields, with no `answer_kind` and no `view_kind`
    on the wire; `validate` and `context` are the nested view alone, v1's
    body field for field (R0-04);
  - instants are ISO 8601 text in UTC ending in `Z`, dates ISO 8601 dates,
    decimals JSON strings in the stored form (`"45.00"`).

  The HTTP status is `SERVICE_ANSWER_STATUS` (200) for an answer and, for a
  refusal, its code's row of `REFUSAL_HTTP_STATUSES`: `not_found` 404,
  `internal_error` 500, every other code 422, as v1 answered (`SOURCE.md`
  L14).
- **The owner interface's requests and pages** (`owner_interface`; owner,
  2026-11-24, the State 7 structure requests of `owner_interface`). An owner
  action is addressed by its row of the data provider's `OWNER_ACTIONS`
  (row model `OwnerActionRoute`, one row per `OwnerAction` member): a read
  by `GET`, every other action by `POST`, at the path `/` and the action's
  value, the project list at `/`; the row also says whether the action is a
  change, whose form carries the CSRF value (A13 rule 2), and whether it
  touches an uploaded file (A16 rule 2) — `show_confirmation` touching one
  only when its `confirm_action` is `confirm_import`. A method and path of
  no row name no action: `OwnerRequest.action` is then none, and
  `operations` refuses the request after stage (1) as `invalid_request`
  (`outside_closed_list`) at stage (4). The target is the query parameter
  `OWNER_TARGET_PARAMETER` (`target`) names, an identity and never a
  personal value (R0-29). A `GET` request's other fields are its query's, a
  `POST` request's the fields of its `application/x-www-form-urlencoded`
  body, or of the upload's multipart head. Each field is named by its path:
  an `OwnerRequest` or `OwnerValues` field by its name, a nested model's
  field by its parent's path, a full stop and its name, a tuple's element by
  its parent's path, a full stop and its position from 0, and a union's
  variant by its discriminator among its fields; a field's text is the
  field's value for text, an enumeration member's value, `true` or `false`,
  or an integer's decimal digits, and an absent field is none. A form that
  repeats a name, gives a text not of its field's type or leaves a gap in a
  tuple's positions cannot be read. The CSRF value is the field
  `OWNER_CSRF_FIELD` (`csrf`) names, the upload's first part included, and
  `OwnerRequest.csrf_value` carries it from the form's reading to the
  request's admission, since a body is read once. The import's
  confirmation step carries, besides the picks, the bound upload's number
  and digest as the fields `upload_number` and `file_digest` of
  `OwnerValues`, rendered from the step's `ImportInputs`, so its submission
  binds what was shown (owner, 2026-11-24). An action's target is one
  identity — the project, the customer, the agent session or the pointer it
  acts on; granting a project to a session, making it the active one and
  revoking it act on the session, and name the project as the field
  `project_id` of `OwnerValues` (owner, 2026-11-24). The session cookie is
  named `OWNER_SESSION_COOKIE_NAME` (`__Host-registry_session`): set
  `Secure`, `HttpOnly`, `Path=/` and no `Domain`, which the `__Host-` prefix
  makes a browser require (A13 rule 1), and `SameSite=Strict`, so a browser
  never sends it with a request another site started (owner, 2026-11-24;
  OWASP). A page's HTTP status is the service
  API's: `SERVICE_ANSWER_STATUS` for an answer, the code's row of
  `REFUSAL_HTTP_STATUSES` for a refusal. A
  request whose body, upload head or form cannot be read is handed on with
  no values, no CSRF value and no credential (option (a) of the question
  State 4 carried to State 7, round-51 and round-55 T3).
- **The import file** (R0-72): one UTF-8 JSON object with the arrays
  `projects` (`project_id`, `name`, `address`, `status`, `customer_ref`,
  `created_at`, `updated_at`, `archived_at`), `rooms` (`room_id`,
  `project_id`, `name`, `created_at`) and `pointers` (`pointer_id`,
  `project_id`, `artifact_type`, `owner_service`, `version`, `status`, `uri`,
  `payload_ref`, `content_digest`, `created_at`, `superseded_at`); instants
  as ISO 8601 text with their offset. The v1 store keeps no archived or
  superseded instant and no digest: the export script (outside Registry)
  writes the instant of the change that archived or superseded a record, and
  no digest. Every value is read as text and checked by A16 rule 4;
  `ExportFile` keeps each record's position, so two records of one id and a
  record with no id are told apart.
- **A backup file** (A18): its first line is the record, one JSON object
  readable without the key — `record_version` (`BACKUP_RECORD_VERSION`, 1),
  `made_at`, `release_version`, `last_sequence_number`, `key_digest`; then
  the snapshot sealed with AES-256-GCM under a 256-bit key HKDF-SHA256
  derives from the backup key's UTF-8 bytes with `BACKUP_KEY_DERIVATION_INFO`,
  a random 96-bit nonce before the ciphertext, the record line as associated
  data. The key digest is `sha256:` and the lowercase hex SHA-256 of
  `BACKUP_KEY_DIGEST_DOMAIN`'s bytes, a zero byte and the key's UTF-8 bytes. A
  later algorithm is a later record version. The record's five fields are the
  same in every version, so the record of any version is read: a backup made
  by an earlier or a later release is kept and counted by its instant like
  any other until its 30 × 24 hours have passed (A18 rules 1, 4), never
  deleted as unreadable for its version; only a run's own check, which
  decrypts the backup it just made, needs the release's version. A record
  line that is not a JSON object of these five fields, each of its type, is
  unreadable (A18 rule 4). This needs the `cryptography`
  package, pinned by digest as every dependency (A20).

## The store's rows (`70_persistence_closure.json`)

`store_persistence`, the store's companion (State 3), is lowered from
`persistence_backend/v3` (`sqlite_sync_v2`, transaction external: `store`
opens and ends every transaction). One table per durable model; a row is the
envelope of one record — the columns a lookup, a list's order or a deletion
compares, and the record itself as `json_model` — so the repository holds no
rule: which record goes into which row, which rows a list reads and how two
lists merge into A06's order, and which rows an erasure removes are
`store`'s, inside the `StoreTransaction` class.

- A list A06 orders by keys of one table is one `list_by` (`order_by` on its
  columns); the project list with its archived projects is two reads, one per
  status, merged by `store` on the same keys (A06 rule 1).
- A read of every row — the sessions, the audit log, the migration closure —
  is `list_selected` with no case, so both selector arguments are none.
- Erasing audit entries before a date reads the log and deletes the selected
  entries one by one, by sequence number: the backend compares by equality
  only. A session holding an erased project is found the same way (A12
  rule 1, R0-61).
- Deletion is the `delete_by` query kind (owner, 2026-11-16: added to the
  Factory's v3 for this case), so the store's erasures stay deterministic.

The companion has no State 5 operation: only `store` calls it, and its whole
surface is State 6's (State 5 round-34 T1, T8).

- **Surface.** `create_store_schema(connection: object) -> None` and the
  class `SqliteStoreRepository(connection: object)` with exactly the 37
  methods of `70_persistence_closure.json`, each typed in `60_contracts.json`
  under `StoreRepository.*`: insert, load by key, find by request id, update,
  list in A06's order, delete — per table, with the selector and order fixed
  in the method, never passed by `store`.
- **Construction and lifetime** (T4). `store` makes one repository for each
  connection it opens and only for it: the actions' connection, opened by
  `open_store` and kept for the process; the snapshot's own read connection
  and the copy's connection of `copy_store_snapshot`; the read-only connection
  of `check_store_file`. A repository lives as long as its connection; `store`
  closes the connection and drops the repository with it, and never hands one
  to another module (`StoreTransaction` is the only surface the record modules
  see).
- **Failures** (T5). A row that is not there is an answer: `None` from a load
  or a find, an empty tuple from a list, `0` from a delete. Every other
  failure — a constraint the row breaks, a record that does not decode, an
  error of the driver — is raised unchanged to `store` (the constructor takes
  no context, so the methods run without a guard, §6.3), which rolls the
  transaction back and answers `internal_error` (`transaction_failed`), nothing
  changed (A04 rule 4). No domain answer comes from a constraint: a record
  module looks a request id or an identity up before it writes (A01 rules 4,
  5; "Minted identities"), so a unique key that is broken is a failure.
- **The schema** (T7). `create_store_schema` creates the eight tables, and
  nothing else, idempotently. `open_store` calls it only for a store it
  makes new, on the temporary file's connection, in the one transaction that
  also sets the store's version (`PRAGMA user_version = STORE_VERSION`) and
  writes M12 AuditSequence at 0 through `upsert_audit_sequence_row`, before the
  rename (A17 rule 5); a failure there is the start's diagnostic. An existing
  store is opened and checked, never given its schema again.
- **The journal** (State 5, `open_store`: "the engine setting that lets a
  backup's reader and the writer go on together is set here, as State 6
  fixes it"). The store keeps SQLite's write-ahead log: `open_store` sets it
  on the actions' connection of every store it opens, made new or not. A
  reader on its own connection then sees one snapshot while the writer goes
  on, and neither waits for the other (A18 rule 1). The actions' one
  connection serves every thread under `store`'s lock: a write transaction
  takes the write lock when it begins; a read transaction takes the same
  lock, since it runs on the same connection.
- **A backup's copy** (T9). `copy_store_snapshot` opens its own read
  connection with its own repository and fixes the snapshot by its first
  read, `load_audit_sequence_row`; in that read transaction it copies the
  database to the temporary path with SQLite's online backup of that
  connection; then, on the copy's own connection and repository, it removes
  every session — `list_agent_session_rows`, then `delete_agent_session_row`
  for each — and commits (A18 rule 2). `check_store_file` reads the copy's
  `load_audit_sequence_row` on its read-only connection, after the version and
  integrity checks (A18 rule 4).

## Carried to State 6, and how it is closed

| from | topic | closed by |
|---|---|---|
| State 2 round-68 T11 | the backup key's digest | "A backup file" above; the three constants in `70_data_provider_closure.json` |
| State 3 round-31 T6 | the data provider constants' exact values | `70_data_provider_closure.json`, unchanged but for the three backup constants |
| State 5 round-19 T1, round-26 T4 | environment variables to settings fields | `config.runtime_environment_variables` targets the fields of `RuntimeSettings`, one per item |
| State 5 round-19 T16 | `STORE_VERSION`, the temporary suffix | the data provider's `STORE_VERSION` 1 and `STORE_TEMPORARY_SUFFIX` `.new` |
| State 5 round-19 T17 | listener addresses | `ListenAddress` (`host` an IP address as text, `port` an `int` from `LISTEN_PORT_MIN` to `LISTEN_PORT_MAX`); the family is the host's address's |
| State 5 round-19 T19 | release and contract versions | the data provider's `RELEASE_VERSION` and `CONTRACT_VERSION`, strings fixed by each release |
| State 5 round-30 T1–T4, T6, T7, T9, T10 | `store.discard_new_store` | below |
| State 2 round-90 T8, State 5 round-39 T3 | the listeners' read timeout | below, "The listeners" |
| State 5 round-39 T9 | an unread body's remainder and connection reuse | below, "The listeners" |

`store.discard_new_store` answers `DiscardResult`: `removed` is true when
the store's pathname no longer names a file, and `failure` names the first
step that failed — closing the connection, a companion `-wal`, `-shm` or
`-journal`, or the store file — with its kind. The steps run in that order
and stop at the first failure (State 5). A path's type is read without
following a link: a link, a directory or any other non-regular object is left
as it is and is `not_regular_file`, which stops the rest; a path that does not
exist is nothing to remove and the next step follows; a type that cannot be
read, or a path that changes between its reading and its removal so that the
removal fails, is `type_unreadable` or `remove_failed`. After a failed close
the connection's state is unknown and nothing else is tried: the start stops
and the process ends, which releases it. Only the three suffixes of the
store's own name are ever removed, and only of a store this start made new;
a pre-existing store and its companions are never touched (A17 rule 2). A
non-regular object at the store's own pathname answers `removed: false`.
`instance_lifecycle` writes the failure's step and kind in the start's one
diagnostic, beside the listener that could not be opened, never a path's
content.

## The listeners

`instance_lifecycle`'s two listeners share one HTTP implementation. Each
connection's socket waits at most the imported
`LISTENER_READ_TIMEOUT_SECONDS` (30) for the next bytes of a request — its
headers or its body, an upload's head and file among them; a wait that
reaches it ends the stream with a failure, which the reader sees as any
stream failure: an upload's head then gives no CSRF value (refused at stage
(1)), its file part `file_unreadable`, and the connection is closed. A
request answered before its body was read to its framed end — any request,
not an upload alone — has the remainder discarded unread and its
connection closed; a connection carries a next request only after one whose
body was read to its end.

That close is staged (RFC 9112 section 9.6; owner, 2026-11-24): after the
answer is written the listener shuts the socket's writing side, then reads
and drops what the client still sends until the client closes, the imported
`LISTENER_CLOSE_DRAIN_SECONDS` (2) have passed since the shutdown, or the
imported `LISTENER_CLOSE_DRAIN_MAX_BYTES` (64 MiB) have been dropped,
whichever comes first, and only then closes the socket. A plain close with
bytes still unread makes the operating system reset the connection and drop
what it had not yet sent, so a client still sending its body lost the
answer (prototype `listener_proto`, 2026-11-17: 0 of 4 answers above about
100 KB arrived over loopback with a plain close, 4 of 4 with the staged
one). The dropped bytes are read into nothing. An answer larger than the
socket's buffers, to a client that reads only after it has sent everything,
can still wait out the read timeout; the early answers are refusal pages
and stay small.

The timeout is a wait for progress, not a deadline for the request: it
applies to each read of the socket and restarts with every byte that
arrives, so a slow client that keeps sending is never cut, and one that
stops for `LISTENER_READ_TIMEOUT_SECONDS` is. It is the socket's own timeout,
measured by the operating system; `clock` does not time it, and a suspension
of the host counts as whatever the operating system counts it as (A13 rule
2's monotonic readings are the sessions', not the listeners'). A wait that
reaches it while the headers are read closes the connection with no answer
and reaches no surface. One that reaches it while a body is read is a
failure of the body's stream: what its reader has already handed on stands
— a session check already made, with its restarted 30 minutes, an admitted
change already committed — and the reader answers the failure as it answers
any stream failure (an upload's head no CSRF value, its file part
`file_unreadable`); the answer is sent if the connection still takes it,
and the connection is then closed.

## Open

- `60_contract_plan.json` stays `open` until the State 6 transition checks
  close: the clock's `70_system_clock_closure.json` waits for the Factory's
  `system_clock_backend` v6; the model-closure and time-source checks read
  variants and read impacts as the Workbench's tools PR #186 makes them.
- States 3 to 5 reopened on 2026-11-16 need their question rounds before
  State 6 hands off.
