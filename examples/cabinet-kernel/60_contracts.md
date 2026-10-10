# State 6 — Cabinet Kernel exact contracts

## Status

Draft of 2026-10-03. The exact signatures are `60_contracts.json`, the function
inventory `60_contract_plan.json`, the typed models `60_model_closure_domain.json`
(State 1 records M01–M28 under their State 1 field names, the closed
enumerations, the platform manifest record) and `60_model_closure_operations.json`
(the arguments and answers the signatures name), `60_model_closure_values.json`
(contract-only values), `60_model_closure_store.json` (the store's rows, its
counter and the `StoreRepository` port, contract-only), the exception symbols
`60_exception_taxonomy.json`, the State 5 exposure `50_exposure_plan.json`, and
the store's tables `70_persistence_closure.json` (decision 23). The store's row
models, port contracts, table names and IR are expanded from one row table by
`experiments/cabinet-kernel/build_store_persistence.py`.
This text records the technical decisions those files rest on; the owner does
not review fields, classes or formats, so each is the agent's and says why.

## How the contracts are shaped

- **One function per State 5 operation**, named as the operation, owned by its
  module. Internal functions are declared only for a seam a module reuses
  (`inventory_rationale` of the plan); every other helper stays private to the
  generated module and is not a contract.
- **Module state is hidden in the module.** `store` holds the open database,
  the lock and the data directory after `open_store`; `installation` holds the
  loaded configuration, the last configuration digest and the current token
  list after `load_installation`. Their operations take no handle, as State 5
  gives them none ("Inputs: nothing").
- **Refusals are exceptions** (`60_exception_taxonomy.json`), one symbol per
  meaning, owned by the lowest module that raises it and that every module
  passing it on already knows (State 3 order). `UnknownReferenceError`,
  `RefusedError`, `InvalidRequestError` and `StoreInternalError` are owned by
  `store`, the lowest module every deciding module knows; a refusal of
  `functions`, `bindings`, `flows`, `effects` or `runs` raises the same
  symbol. Start-only refusals belong to their module (`InstallationRejectedError`,
  `SandboxUnavailableError`); `CredentialUnresolvedError` stays inside
  `service_invoker`, which turns it into the detail `credential_unresolved`;
  `NonCanonicalValueError` is `canonical_values`'. `StopRequiredError` is owned
  by `sandbox`, whose unconfirmed cleanup it names, and raised by the module that
  wrote the execution's record (State 3, "Unconfirmed cleanup").
  `surface.translate_failure` maps every symbol to its State 5 code; any other
  exception is `internal_error` without detail (A16 rule 7). A checking
  operation answers, it raises nothing (State 5, "Checks answer").
- **No dict, Any or untagged union.** A choice between shapes is a
  `discriminated_union`; "or none" is `X | None`; an optional argument exists
  only where State 2 or 5 makes it optional (a purpose when new, expected
  outputs, a filter, a continuation token, an absent candidate).
- **Time** is `KernelInstant` (`epoch_us`, integer microseconds since the Unix
  epoch, UTC), the one representation of every recorded `*_at` field;
  `clock.kernel_now` returns it. `clock.monotonic_ns` returns one raw host
  monotonic reading in nanoseconds (`int`); a bounded wait derives its deadline
  from it and keeps it in memory only, never stored (A19 rule 2; decision 26).
- **Values in calls are bytes.** A `value` port's value travels as its RFC 8785
  canonical bytes, a file as its bytes (`PortPayload`); records refer to values
  by `value_id` and to spooled files by their identity (`PortRef`), and hold no
  payload (A15 rule 2). JSON a record holds as a fact — a `value_schema`, a
  guard value — is canonical JSON text, so "the same schema" is equal text
  (A05 rule 2). `module:surface` turns every JSON text of a request into
  canonical form before any module sees it (State 5, "Values enter canonical").
- **Store calls are typed per change and per relation.** `record_change` takes
  one `StoreChange`, a union with one variant per named change of State 5
  (its literal is the State 5 name), carrying the facts the caller decided
  and no field `store` assigns: no minted identity, store position or
  `attempt_number`, and no actor field — `store` fills `*_by` from the `actor`
  argument as the change names it. It returns a `RecordSet`, the written
  records with everything `store` assigned. `read_records` takes one
  `RecordQuery`, a union of reads by identity and of the closed relations of
  State 5, and answers a `RecordSet`. Notes name a change or a relation by its
  variant model (`StartRunChange`, `ExecutionsOfRun`), never by the bare State 5
  name, which is also an exported function and would become an import
  (SPEC_STANDARD 7).

## Decisions closed in State 6

1. **Canonical bytes** (A01 rule 1, carried by States 1 and 2): RFC 8785 as
   written. `canonical_bytes` parses JSON text, refuses a duplicate member name,
   a non-finite number and an integer outside ±(2^53 − 1), which an IEEE double
   cannot hold exactly, and emits the JCS form. The size of a JSON value is the
   length of its canonical bytes.
2. **Supported JSON Schema subset** (A02 rule 1, carried by States 1 and 2): a
   schema is a JSON object using only `type` (one of `null`, `boolean`,
   `integer`, `number`, `string`, `array`, `object`, as one string), `enum`
   (a non-empty array of distinct scalars), `const` (one scalar), `properties`
   and `required` (for `object`), `additionalProperties` (`true` or `false`
   only), `items` (one schema, for `array`), `minItems`, `maxItems`,
   `minLength`, `maxLength`, `minimum` and `maximum`. Any other keyword —
   `$ref`, `pattern`, `format`, `oneOf`, `anyOf`, `allOf`, `not` among them —
   is outside the subset: A02 refuses it in a contract version, and
   `fit_port_value` answers that no value fits it, so a binding or flow port
   written outside the subset can never deliver. `integer` means a canonical
   number without a fraction. A closed set (A05 guards) is a schema with `enum`
   or `const`. A `file` port's `value_schema` is the empty schema `{}`; its fit
   is its media type (State 5, `fit_port_value`).
3. **Idempotency key fields** (A08 rule 4, carried by States 1 and 3): the
   manifest text is split on `+` and each part trimmed; an empty part, a repeated
   name, or a name that is not `[A-Za-z_][A-Za-z0-9_]*` is a manifest mismatch.
   `idempotency_key_fields` keeps the manifest's order; the key is the SHA-256
   of the canonical JSON object of those fields, keyed by name, so the order
   does not change it. A key field whose value is `null` is not refused for
   being a key field: the key covers `null`, and the service receives the
   field as A09 rule 2 places it (omitted from a query; a null path
   placeholder is `input_not_placeable`).
4. **Continuation tokens** (A16 rule 6, carried by State 2): `store` issues the
   base64url text, without padding, of the canonical JSON of the record type, the
   SHA-256 of the canonical filter, and the store position of the last item
   returned. A token that does not decode, or names another record type or
   filter, is `invalid_request`. The repair view's token is `surface`'s: the
   same encoding of the slot, the implementation set of its first page and the
   `store` token.
5. **Constants carry a declared schema.** A flow constant is a typed literal
   (M16): the composing agent declares its `value_schema` with its class, and its
   StoredValue takes both. Composition refuses a constant whose value does not
   fit its declared schema (A05 rule 7); phase 2 of the proof checks that the
   declared schema is the target port's stored schema (M21), so the value then
   fits the port (A05 rule 1); the constant's identity does not depend on
   resolving another record.
6. **The MCP entrance.** MCP over streamable HTTP at `mcp_listen_address`, one
   tool per operation of the State 5 catalogue, its input schema the request
   model of that operation; the token is the `Authorization: Bearer` header.
   A value in a request is JSON text in a string field and a file is base64
   text, so that `surface` sees the exact text it canonicalizes, duplicate
   member names included; an answer carries values as JSON text and file bytes
   as base64.
7. **Configuration file**: one JSON object whose members are the fields of
   Installation M28. A service credential is a header name and `secret_file`,
   the absolute path of a regular private file of the kernel's user whose
   content, without one trailing newline, is the value (A17 rules 1–2); the
   kernel reads no environment variable.
8. **The manifest at a revision**: `manifest_location` is a directory inside a
   git repository and `manifest_revision` a commit of it; `bindings` reads
   `<service_id>.json` of that directory at that commit as a git object, never
   from the working tree, so a record changes only with the configured revision
   (A08 rules 1 and 6). The manifest, like the installation file, is the
   owner's trusted input at a revision the owner chose: the release's closed
   list of ceilings (A20 rule 1) has none for it, and none for the headers or
   capabilities it declares. What reaches a service or an agent stays bounded
   where it is used — a request's input values by `stored_value_bytes_max`, a
   response by `service_response_bytes_max`, a refusal's reason by
   `bounded_text_bytes_max`; a record too large to read is one that cannot be
   read (State 5, closed question 8).
9. **The manifest record model** names the record's members (`service`,
   `capabilities`, `instances`, `name`, `exposed_as`, `effect_class`,
   `idempotency_key`, `api_base_url`, `required_headers`) with four
   deliberate differences: an instance's `class` is `instance_class`, a Python
   keyword being no field name; the instance's key in `instances` is
   `instance_name`; `exposed_as.http_api`, a string, a list or absent in the
   platform's records, is read as the tuple of its routes, so "exactly one
   route" is a length; and `record_digest` is the digest of the raw capability
   entry, computed while reading. `effect_class` stays text, so a value outside
   the five is representable and refused (A08 rule 5).
10. **An approval preview shown to an agent** withholds the request description
    when any input of the element is `personal_data`: its URL, query or body
    would carry the value (A07 rule 4); the agent still sees `request_digest`
    and every input as its digest and class.
11. **A NodeExecution and a TrialExecution carry `detail_code`** beside `failure_detail`: the closed
    detail of State 5 is a code, the excerpt is text, and the owner acts on the
    code.

## Decisions closed while writing State 7 (2026-10-03)

Authoring the notes asked for facts the texts did not fix. Each is the
agent's and says why; the owner-facing rules they rest on are in State 2.

12. **Model changes.** `StoredValuesRef` names one `value_id`: a value port,
    `one` or `many`, refers to one StoredValue, a `many` value being one JSON
    array (A13 rule 6). `EffectApproval` gains `attempt_number`, the attempt it
    was requested for, so "requested after a `not_applied` resolution" is
    decided from the records (A10 rule 1, A11 rule 1). `EffectAttempt` and
    `RecordAttemptInFlightChange` gain `inputs`, the element's PortRefs, so a
    recovered attempt's NodeExecution names its inputs (A11 rule 4).
    `FileFactsRef` gains `disclosure_class`: a trial execution's file output is
    recorded by facts only, and its class — the highest class of the case's
    inputs (A07 rule 3) — must travel with it to be masked. `SpooledFilesRef`
    gains `disclosure_class`, the class of the file list it names, so an empty
    list keeps the class A13 rule 6 gives it and counts in an execution's
    class (A07 rule 5).
13. **Continuation token**: base64url without padding of the canonical JSON
    object of `record_type`, `filter_digest` and `store_position`; with no
    filter the digest is that of canonical `null`.
14. **Content identities** are computed over the canonical JSON object of all
    fields of the variant, `subject_kind` included; a JSON schema is held as
    its canonical text; only unordered lists are sorted, so a corpus keeps its
    order. An idempotency key is the object of port name to JSON value, `null`
    kept (decision 3). `request_digest` is the content identity of the request
    description's canonical JSON (A10 rule 7).
15. **Time left before a deadline** rounds up to whole milliseconds, so zero
    remaining means the deadline has passed (decision 26 moved this from the
    withdrawn `MonotonicDeadline.remaining_ms` to each waiting function).
16. **Store writes.** Writing a StoredValue whose `value_id` exists returns the
    existing record; repeating any other immutable record is
    `StoreInternalError`, since its caller checks existence first.
17. **Request body and addresses.** A JSON request body is sent as its RFC 8785
    canonical bytes. "Loopback" (A09 rule 4) is an IP literal in
    `127.0.0.0/8` or `::1`; no name is resolved to decide it.
18. **Media types.** Within the kernel — ports, fixtures, proof (K-06) — media
    types are equal only as equal text; only an HTTP response's
    `Content-Type` is compared on type and subtype without regard to case,
    parameters ignored (A09 rule 3). An authored file fixture takes its port's
    media type.
19. **Corpus place** (`corpus_position`) counts from 0 in corpus order.
20. **Listing.** `list_records` lists the fourteen record types of
    `ShownRecords`; the other members of `RecordType` are read through the
    operations State 5 names for them and are `invalid_request` there.
21. **A stop during a request.** `surface` lets `StopRequiredError` pass out of
    `answer_request`; `serve_kernel` sends that request the `internal_error`
    answer and then ends the process with a non-zero status (State 3,
    "Unconfirmed cleanup").

## Decision closed at assembly (2026-10-10)

Assembly found that no state named the kernel's dependencies (A20 rule 3)
nor the MCP messages around the catalogue (decision 6). The owner chose the
standard library (2026-10-10); the protocol details below are the agent's,
each the narrowest the MCP specification allows.

22. **Dependencies and the MCP subset of release v1.**
    - *Dependencies.* The kernel imports only the standard library of CPython
      3.12; no third-party package (`imports.third_party` is empty by this
      decision). Amended by decision 25: pydantic, on which the Factory emits
      the models and the store repository, is the one third-party package. The entrance is `http.server.HTTPServer`, which serves one
      request at a time (A18 rule 3); services are called through
      `http.client`, which lets the kernel send exactly the headers of A10;
      the store is `sqlite3`. Two host programs belong to the release with
      the interpreter: `git`, through which `bindings` reads a manifest
      record as a git object (decision 8), and `bwrap` (A03). The release
      names their versions; the kernel runs no other program.
    - *Transport.* Streamable HTTP without sessions and without event
      streams: a POST to the path `MCP_ENDPOINT_PATH` carries one JSON-RPC
      2.0 message and is answered `200` with `application/json` and one
      response, or `202` without a body when the message is a notification
      or a response. Any other method on that path is `405`, any other path
      `404`, and a request with an `Origin` header `403`, all without a
      body; no `Mcp-Session-Id` is issued, one presented is ignored.
    - *Messages.* Every message is checked in A16 rule 1 order — size, then
      token — before its method is read. `initialize` answers
      `MCP_PROTOCOL_VERSION`, the tools capability without change
      notification and the server `MCP_SERVER_NAME` / `MCP_SERVER_VERSION`,
      whatever version the client asked; `ping` answers an empty result;
      `tools/list` answers one tool per catalogue operation, in catalogue
      order, without pagination, its `inputSchema` derived from the
      operation's request model by a closed rule (State 7); `tools/call`
      runs the operation. A batch, an unknown method, or a call whose name
      is no catalogue operation is a JSON-RPC error.
    - *Answers.* An operation's answer is a tool result with one text
      content, the answer as JSON text, and `isError` false. A refusal
      decided once the operation is known — fit, bounds, permission, or the
      operation's own — is a tool result with `isError` true whose text is
      the `RefusalAnswer` as JSON, so the agent reads the reason. A refusal
      decided before — size, token, a malformed message, unknown method or
      tool — is a JSON-RPC error with the code JSON-RPC defines for it, the
      refusal code as its message and the `RefusalAnswer` as its data;
      `internal_error` is `-32603`. The kernel defines no error number of
      its own.

## Decision closed for the store's persistence (2026-10-10)

Factory admission FA013 found the store's tables and its repository of mutable
records left to generation. They are now a deterministic closure
(`persistence_backend/v3`, emitter `sqlite_sync_v2`, cabinet-flow 5987af6 as
precedent); State 3 split `store_persistence` off `store` for it.

23. **The store's rows and their port.**
    - *One row per record.* Every record type of `store.read_records` has one
      table whose row model is named after it (`RunRow` for Run): its
      `store_position`, its `record_type`, the fields a lookup filters on, and
      `record`, the record itself as one JSON object. A store position is the
      store's fact, not a field of the record — records are returned as they are
      (State 5) — so it cannot be a column of the record's own table; the row is
      the store's envelope. Activation and FlowActivation, identified by their
      store position, are keyed by it; the counter of store positions is one row
      of `StorePositionCounter`, keyed by the one `StoreCounterName` member.
    - *Keys of an element.* `map_index` is absent for an element of a node that
      is not mapped, and an equality on an absent column matches nothing; so an
      element and an attempt are columns holding the record's `ElementKey` and
      `AttemptKey` (and a spooled file its `SpooledFileKey`), compared whole as
      their JSON form, which is equal exactly when the keys are equal.
    - *What the port offers.* Per row: insert; load by the complete key; for a
      type `list_records` pages, the whole type in store order (an equality on
      its own `record_type`, the one whole-table read `sqlite_sync_v2` lowers)
      and find by store position (the continuation token's check); the equality
      lists a relation or a page filter reads, in store order; and, for the five
      records whose lifecycle fields change, an update of `status` and `record`
      in place, which keeps the store position. No other record type has an
      update, so A01 rule 6 holds by the port's shape.
    - *What stays in `store`.* The transaction (`transaction: external`: `store`
      begins, commits and rolls back on its one connection), store positions
      (`next_store_position`, the one internal function that takes the port),
      attempt numbers, minted identities, which rows a relation or a page reads
      and how they combine — latest as the last of a list, a set filter as one
      list per value merged by position, a page as the reverse of the list below
      the token's position — the files, their durability and the lock (State 7).
    - *Implementation.* `StoreRepository` is a `kind: interface` of `models`;
      `implementation_obligations` names `SqliteStoreRepository` its `local`
      implementation, and `store` builds that class over its connection.
      `StoreRepository` and its rows are contract-only models: they are not State 1
      records and carry no persistence class; the records keep theirs (five
      `master`, thirteen `issued`).
    - *Accepted by the owner (2026-10-10).* A row is the store's envelope, not a
      second domain model (§15.5.1): it adds no domain fact. A page reads the
      whole equality list and is cut in `store`; v3 has no limit or range, and
      one owner on one local kernel does not need one — a v4 form is asked for
      only when a list's size makes it necessary. The JSON form of a key column
      is that of the pinned pydantic of the release (A20 rule 3): a release that
      changes the pydantic version checks that the form of `ElementKey`,
      `AttemptKey` and `SpooledFileKey` is unchanged, or migrates those columns.
      The A18 witness counts `store_persistence` as part of the store module:
      it may send row statements (`.cursor`, `.execute`) and nothing else.

## Decisions closed at Stage 8.1 (2026-10-10)

The module review (spec-workbench PR #100) left three modules undecided; the
owner decided each on 2026-10-10.

24. **Rollback order, the runs to recover, and the shown effect attempt.**
    - *Rollback to the serving implementation.* `roll_back_slot` checks, after
      the slot, the implementation and its contract version, whether the named
      implementation is the current activation; if it is, it returns that
      Activation and records nothing, without the verdict check. A serving
      implementation that lacks a verdict over a grown corpus (A04 rule 7) is
      therefore named, not refused (A04 rule 5: "Naming the implementation that
      is already current returns the current activation and records nothing").
    - *Runs to recover, in store order.* `RunsByStatus` names a set of
      statuses (`statuses: tuple[RunStatus, ...]`, non-empty, no repeats) and
      answers the runs of any of them oldest first in store order: `store`
      merges one `list_run_rows_by_status` per status by store position, as it
      merges a page's set filter (decision 23). `runs.recover_running_runs`
      asks once for `running`, `awaiting_approval` and `pending` (A14 rule 5,
      A19 rule 3); a store position stays the store's fact.
    - *The shown effect attempt.* `ShownRecords.effect_attempts` is
      `tuple[ShownEffectAttempt, ...]`: every field of the EffectAttempt, its
      inputs as `ShownPort` through `show_port_refs`, so an agent receives a
      `personal_data` input only as digest and class (A07 rule 4). `RecordSet`,
      the store's answer, keeps the record itself.
    - *A port named twice in a trial case* (Stage 8.1 note repair N07): the
      case is refused, never one of the two values kept silently.

## Decisions closed before the first Route B (2026-10-10)

The `semantic_runtime` fixture review (code-factory PR #51) found that the
Factory's emitters contradict decision 22 and that the release, the entry
point and the store's directory names were nowhere written. The owner decided
each on 2026-10-10.

25. **Release v1 pins, the entry point and the store layout.**
    - *pydantic.* The Factory emits `models` as pydantic models and the store
      repository's JSON columns through pydantic (SPEC_STANDARD §6.3); the
      kernel therefore imports the standard library and pydantic, nothing
      else. `imports.third_party` stays empty: the emitters import it, no
      generated module names it. Decision 23's key-column form is that of
      this pinned pydantic.
    - *What the release pins* (A20 rule 3), as `data_provider` constants:
      `RELEASE_SANDBOX_INTERPRETER` "CPython 3.12.3", `RELEASE_BWRAP_VERSION`
      "0.9.0", `RELEASE_PYTHON_DEPENDENCIES` {pydantic: 2.12.5} — the versions
      of the owner's host on 2026-10-10 — and `SANDBOX_RUNTIME_PATHS`
      ("/usr"), the only host paths `execute_function` binds read-only. The
      sandbox is the security boundary, so `probe_sandbox` stops the start when
      `bwrap --version` or the probe's interpreter differs from these. `git`
      2.43.0 is recorded here only: it reads manifests and bounds no sandbox,
      and the kernel does not check it.
    - *Entry point.* The host starts the kernel as
      `python -m cabinet_kernel.surface <config_path>`; run as a script, the
      surface module calls `serve_kernel` and exits with its status.
    - *Store layout.* The content-addressed area is
      `STORE_VALUE_AREA_DIRECTORY` ("values") with a value's bytes named by
      its digest, the spool area `STORE_SPOOL_AREA_DIRECTORY` ("spool") with
      one directory per `run_id`, both directly inside `data_directory`.
    - *Smaller points.* An answer writes a field that is None as `null`,
      never omitting it; `probe_sandbox` looks for `bwrap` on the process's
      `PATH`; the fixture's one wrapper process between the kernel and
      `bwrap`, and its way of obstructing a cleanup, are accepted as test
      harness; `RUNTIME_SURFACE.md` is corrected (`ShownComposedFlowVersion`,
      `token=None`, `raw`, `run_spool`, the default page size).

## Decision closed for the clock (2026-10-10)

The first Route B stopped at `clock`: the Factory's time-source gate refused
the generated module with `clock_representation_mismatch`, because the
`kernel_now` note asked for a private reader function and SPEC_STANDARD §6.8
wants the operation that samples the clock to return the instant itself — no
generation could pass. The Factory then closed the gap that let `clock` be
generated at all (code-factory PR #57): every module `rules.time_source_policy`
grants a host clock is an executable boundary produced by a deterministic
backend (§6.9), whatever `single_host_source` says. The owner decided on
2026-10-10 to bring the kernel to Route B on that form, as Cabinet Flow did
(its A25, which A19 reuses).

26. **The clock is emitted, not generated.**
    - `clock` owns exactly `kernel_now() -> KernelInstant` and
      `monotonic_ns() -> int`, lowered by the Factory's `python_host_clock_v1`
      from `70_system_clock_closure.json` (`system_clock_backend/v3`);
      `rules.time_source_policy` names `clock` the single host source of both
      clocks. The module has no notes: its code is fixed by the policy (one
      `time.time_ns()` sample floored to microseconds, one raw
      `time.monotonic_ns()` sample).
    - `monotonic_deadline` and `MonotonicDeadline` are withdrawn. A bounded
      wait reads `monotonic_ns` once at its start; its deadline is that
      reading plus the bound in nanoseconds, held in a local variable of the
      waiting function only and never stored (A19 rule 2); the wait has
      passed when a later reading reaches it, and the time left is the
      difference rounded up to whole milliseconds (convention 15).
      `sandbox.execute_function` and `service_invoker.send_prepared_request`
      each bound one wait this way.
    - Tests still replace the clock module as a whole (A19 required tests);
      fixing its monotonic source fixes `monotonic_ns`.

## Decision closed for the surface's imports (2026-10-10)

Route B on decision 26 stopped at `surface`, the last generated module: its
candidate imported `BaseModel` from pydantic, as the `serve_kernel` note
allowed ("like every kernel module it imports nothing outside the CPython 3.12
standard library except pydantic"), while decision 25 left
`imports.third_party` empty, so the Factory's `unknown_top_level_import` gate
refused it. The note and the declared imports said two things; the owner left
the call to the agent.

27. **The surface names pydantic; no other generated module does.**
    `surface` declares `from pydantic import BaseModel`
    (`imports.third_party_by_module`): it builds the published `inputSchema` of
    each operation from its request model and writes every answer model as
    JSON (decision 22), which needs to recognise a model class, and the
    Factory's static gates forbid recognising it by reflection
    (`getattr`/`hasattr`). Every other generated module reaches pydantic only
    through the models it imports. Decision 25's "no generated module names
    it" holds for every module but the surface; its pin is unchanged.

## Decisions closed by the State 7 contradiction round (2026-10-10)

The State 7 round-02 (`questions/state7/round-02/summary.json`) read the prompt
the Factory builds for each generated module and judged 36 topics blocking: two
passages of one prompt that a generator cannot both satisfy. The owner left
every technical call to the agent. Each topic was checked first; 31 are
contradictions and are removed by the smallest edit of the text that owns them,
5 are a general rule whose exception is already written beside it and are left
as they are. No text of States 2–5 changed: every contradiction was in a note,
or between a note and a State 6 signature, and each edit aligns the note with a
rule States 2–5 already state. The exact text is in `80_notes.md`; the
contradiction gate is `questions/state7/round-02`.

28. **The State 7 contradiction round.**
    - *canonical_values T3, not a contradiction.* `fit_port_value` judges list
      elements one by one "within one check", and its size note takes a value
      port's canonical JSON "as the whole value even for cardinality many": a
      `many` value is one JSON array (decision 12), so its size check judges no
      element, and the size note states that exception in its own words.
    - *store T1, T4, T9.* `page_records` asked for a whole list and a find at a
      position "for every listed type", which read as every record type, while
      the port has none for StoredValue and SpooledFile (only lookups by digest,
      attempt or run). It now names the fourteen types `list_records` lists
      (decision 20); activation, flow_activation, stored_value and spooled_file
      are never paged — the surface refuses them — and as `record_type` raise
      `InvalidRequestError` before any read. Decision 23's port is unchanged.
    - *store T2.* `open_store` kept the value files a StoredValue "and a file
      fixture record" names, but no fixture record exists: a trial case's file
      fixture is a file-carriage StoredValue (M21), so the digest lookup it
      gives covers every kept file. The note now says so.
    - *store T3.* The lock was taken on a lock file inside `data_directory`
      before the privacy and link checks, while a failed check "creates
      nothing" (State 5, `open_store`). The lock is now taken on
      `data_directory` itself, opened as a directory without following links,
      so no check can leave a created file; A18 rule 1's "an exclusive lock in
      the data directory" holds, and the lock file leaves the list of files the
      store creates.
    - *store T5.* "Only the status and decision fields" change contradicted the
      lifecycle fields the same function updates (outputs, waiting points,
      times, resumptions). The boundary now names the lifecycle fields
      `record_change` lists, a run's resumptions added there; State 5's "an
      entity's lifecycle fields change in place" is the rule.
    - *store T6, not a contradiction.* "A relation that finds nothing answers an
      empty RecordSet" is the general rule; the validation note of the same
      function writes its one exception, `ActivationBeforeRun` finding no
      activation, which is a broken invariant (a run starts only under an active
      version), not an empty relation.
    - *store T7.* An over-ceiling `spool_file` at a position a SpooledFile
      record names was both refused-and-cleaned and `StoreInternalError`. The
      position check now comes first and removes nothing; the ceiling refusal
      then removes only the attempt's files, none of which a record names, the
      attempt being the element's next (A11 rule 1).
    - *store T10.* `record_change` returned records "with every store position",
      but a store position is not a field of a record (decision 23). It is now
      returned only where it is the identity, of an Activation or a
      FlowActivation.
    - *sandbox T1.* The isolation note allowed no host path but the exchange
      directory, while the next note binds `SANDBOX_RUNTIME_PATHS` read-only
      (decision 25). The note now names both, as A03 rule 1 does ("no host
      directory is mounted except the read-only runtime and that exchange
      directory"); decision 25 is unchanged.
    - *sandbox T2.* "A many file port as the list of its bytes" now says a
      `FileListPayload` whose `contents` is the tuple of its files' bytes.
    - *sandbox T4.* `probe_sandbox` returns None only when every check of its
      validation note holds, the version and interpreter checks of decision 25
      included.
    - *service_invoker T1.* "Read at most to the ceiling, a longer body being
      over it" could not detect a longer body. The body is now read to one byte
      past `service_response_bytes_max`, that byte arriving meaning over the
      ceiling, as `resolve_service_credential` already reads its secret; the
      credential search and an output-less binding read the same way.
    - *service_invoker T2.* A credential header named `host` would have given a
      second Host header. The header note now states that the credential header
      is never a name of `KERNEL_SET_HEADER_NAMES`: an installation holding such
      a credential refuses to start (A09 rule 1) and credentials do not change
      until restart.
    - *functions T1.* `contract_version_id` was computed before the bound
      checks, from a `ResourceBoundsRequest` that may hold None while
      `ContractVersionContent` needs `ResourceBounds`. The identity is computed
      when every bound is given; a request that omits one equals no stored
      version, computes no identity and is refused by the bound check. A01
      rule 4 and A20 rule 4 (an equal existing version returned even under a
      lowered ceiling) are unchanged.
    - *bindings T1.* `check_installed_instances` checked the credential header
      name for every service, and also said a service with no selected instance
      "fails nothing here". It now fails no check that reads the manifest; the
      header-name check, which reads none, applies to it (A09 rule 1).
    - *effects T1, T2, T3.* `send_under_authority` had to write the element's
      input PortRefs and build the idempotency key from input values, with
      neither among its arguments nor in `ElementRef`. The signature gains
      `inputs: tuple[PortRef, ...]` (an internal function; no State 5 text
      names it); `reach_operation_element` passes the inputs it was given, and
      the key reads each key field's StoredValue bytes (a key field is a value
      input, A08 rule 5).
    - *effects T4.* A pre-send failure's `ended_at` was "the time of the check"
      against the module rule "the moment the outcome change is built". It now
      follows the rule: `started_at` when the checks began, `ended_at` when its
      RecordOperationFailureChange is built (A19 rule 1).
    - *effects T5, T7.* `authority` may be None and `SendResult.attempt_status`
      may be None, while a non-read send writes both into fields that need a
      value. Both are None exactly for a `read` binding: `reach_operation_element`
      sends a non-read binding only with the authority found, and
      `send_prepared_request` sets the attempt status for every other class. A
      non-read send given either as None is a broken invariant,
      `StoreInternalError`, nothing sent.
    - *effects T6, T9.* The execution copied the SendResult outcome and one
      output per port even when storing the outputs turned the outcome into
      `contract_violation`. Its status, detail and outputs now come from the
      outcome after storing: `value_too_large` for an output over the stored
      value ceiling, no detail for a spool refusal (A09 rule 7: an answer
      refused only by the spool ceilings keeps no `failure_detail`), outputs
      only when succeeded (A13 rule 3: an element that does not succeed keeps
      no output).
    - *effects T8.* A binding port's `disclosure_class` is optional in the type,
      but StoredValue and SpooledFile need one. The note now states that every
      binding port has a class, a proposal without one being refused (A08
      rule 5, M01).
    - *runs T1.* A produced flow output needs a `value_id`, while a mapped
      node's file output is a SpooledFilesRef. A flow output is never of file
      carriage (A05 rule 7), so a file list reaches only node inputs and every
      produced flow output is a StoredValuesRef; the notes now say so.
    - *runs T2, T3.* `start_run` takes `PortPayload`, file forms included, but
      fits every input as a JSON candidate and stores it as a value. Every flow
      input is of value carriage (A05 rule 7): a file payload is refused at the
      carriage check, naming the port, before a candidate is built.
      `handle_start_run` builds only `JsonPayload`, so no answer changes.
    - *runs T5, T7, not contradictions.* After each function element runs
      writes the element's execution with the records it made non-executable,
      and a failed element of a mapped node does not stop the next one; the
      `cleanup_failed` note of the same function writes its exception in full
      ("that one execution … execute and reach nothing more … raise
      StopRequiredError"), which A03 rule 7 and State 3 "Unconfirmed cleanup"
      require.
    - *runs T6.* "No record of its own holds" a mapped node's file output, yet
      over an empty list the node's one NodeExecution holds every output as an
      empty list. The note now says what A13 rule 6 says: a non-empty list is
      derived from its elements, an empty one is named by the node's one
      NodeExecution without `map_index`.
    - *surface T1.* The start sequence propagated an exception "unchanged with
      the step named in its reason". The exception now propagates unchanged and
      `run_start_sequence` writes the failing step's name to standard error
      first; `serve_kernel` adds the reason. State 5 (`serve_kernel`: "the
      failing step and its reason on the host's standard error") is unchanged.
    - *surface T3, not a contradiction.* The first `answer_request` note orders
      the checks of a catalogue operation; the method note writes the
      exception: `initialize`, `ping` and `tools/list` answer after the size and
      token checks, and only `tools/call` "then pass[es] the remaining checks of
      the first note", as decision 22 ("checked in A16 rule 1 order — size,
      then token — before its method is read") decides.
    - *surface T4.* A file-carriage StoredValue's `media_type` is optional in the
      type while `ShownFile` needs one. Every such value has its port's one
      media type (decision 18); one without is a record that cannot be read,
      `StoreInternalError`.
    - *surface T8.* The note listed "JSON texts" among texts never
      "interpreted", while the surface canonicalizes them. A16 rule 5 lists
      purposes, code and names only; the note now does the same and says a
      JSON text is data parsed only as JSON, by `canonical_bytes` and the
      schema check that judges it, never evaluated or executed.

### State 7 round-03 (2026-10-10)

Twelve contradictions remained; eleven are removed by wording, one was a
misreading (`FileFactsRef` is in the IMPORTS of `functions`):

- An exception written in another note is now stated at the general rule it
  narrows: `read_records` (ActivationBeforeRun raises), `advance_run`
  (`cleanup_failed` stops the run), `answer_request` (initialize, ping and
  tools/list name no catalogue operation).
- `record_change`: ResolveAttemptChange sets the AttemptStatus member named
  like the AttemptResolution; a change's StoredValues take their positions
  before every other record it writes.
- `remove_run_spool`: a link inside the spool raises StoreInternalError with
  nothing removed, as everywhere under the data directory (A18 rule 2).
- `issue_contract_version`: a Port's value_schema is JSON text; a file port's
  is `{}`. `add_trial_case`: value_digest is content_identity of a BytesContent.
- `reach_operation_element`: a non-read binding with no authority requests the
  approval and sends nothing. `send_under_authority`: a read binding has no
  attempt to stay applied. `execute_function_element`: spool_file's refusal
  has already removed the attempt's files.

### State 7 round-04 (2026-10-10)

Four more, by wording: `prepare_request`'s digest ignores the multipart
boundary the description leaves out; `find_send_authority` takes the oldest
approval among those that count; the empty mapped list's StoredValue of `[]`
is written and named by its one NodeExecution (A13 rule 6); a kernel
exception's message holds no secret, so `translate_failure` may show it.

### State 7 round-05 (2026-10-10)

Three more, by wording: the statuses a variant writes or sets are the
module's, like positions and by-fields; store_position is a field exactly
where it is the identity (Activation, FlowActivation); a mapped output's array
takes the port's stored schema as items, so a many port nests arrays.

### State 7 round-06 (2026-10-10)

Two more: the closed inputSchema rule maps `X | None` to
`{"anyOf": [the schema of X, {"type": "null"}]}`, so what is published admits
the null a request may carry (the 8.1 remark "Published inputSchema and null",
decided); an end of stream is a transport failure only before the response is
complete — a body delimited by the connection's close is complete at it.

### State 7 round-07 (2026-10-10)

Six more, by wording: lifecycle fields are those the model declares (a
resolution sets status and resolved_by and records no time); attempt_number
comes from the change, the element's next number the caller read and spooled
under; a failed change's unnamed spool file stays until replaced or its run's
spool is removed, and recover_running_runs removes ended runs' spools
(A18 rule 4); the general per-element progress change excepts cleanup_failed;
ended_at is the draft's; a waiting operation element is not reached again.

## Texts of earlier states changed by State 6

- States 3, 4 and 5 (2026-10-10, decision 26): `clock`'s capabilities are
  `kernel_now` and `monotonic_ns`; the flows that bound a wait name
  `capability:clock.monotonic_ns`; `public_op:clock.monotonic_deadline` is
  replaced by `public_op:clock.monotonic_ns`.
- Semantic test documents (2026-10-10, decision 25):
  `tests/semantic/RUNTIME_SURFACE.md` corrected; no test file changed.
- State 5 (2026-10-10, decision 24): the relation "runs by status" answers
  the runs of any of the given statuses, oldest first in store order.
- State 5 (2026-10-10, Stage 9 FA018): eight names of "Named store changes"
  and their "State impact" lines name the event, not the operation —
  `contract_version_issued`, `trial_case_added`, `binding_proposed`,
  `binding_accepted`, `flow_version_composed`, `flow_version_activated`,
  `run_started`, `run_released`. Each was the discriminator value of its
  StoreChange variant and the name of an exported function, so the Factory's
  slice of `models` had to import that function (SPEC_STANDARD 6, `imports`:
  a whole word in a module's text that names another module's export is an
  import; a module that does not call the function does not name it). The
  operations keep their names; only the change values moved.
- State 3 (2026-10-10, decision 23): the companion module `store_persistence`
  on the second line of the dependency list, `store` knowing it, and the record
  port paragraph of `store`; `30_trace.json` names it a consumer of A01 and A18.
- State 5: the relation "executions of an element", asked by `effects`, which
  reads an operation element's conclusion from its NodeExecution and
  EffectAttempt together (State 5, `operation_element_conclusion`) and spools a
  `read` send's file under the element's next attempt number; and `surface` as
  a caller of `canonical_bytes`, with the convention "Values enter canonical".
- State 1: one punctuation change in ProofResult M17, so that `read`, a value of
  `highest_effect_class`, is not read as a fact of the model. The State 1
  rounds 21–25 then asked for what State 2 had already decided but State 1 did
  not say; each is now said in State 1 with its State 2 source: how an
  EffectAttempt names its authority (a flow activation by store position, M26),
  how a TrialCase names the NodeExecution it was captured from (M06), that a
  grant for a `read` or `draft-write` node is given and never used, that a
  grant moves no run (M25), and that an element has at most one `requested`
  approval (M24).
- State 5, from its rounds 36–38: `effects.operation_element_conclusion`, like
  `reach_operation_element`, trusts the run and element `runs` passes down and
  has no refusal of its own; `read_spooled_file` takes only the lookup
  identity, looked up whole.
- State 4, from its round 7: resume names the `draft-write` authority (the
  flow activation, A14 rule 2), and the unknown-reference refusal of the reads
  `surface` assembles is `surface`'s (State 3).
- State 0: K-08 says, as the action table does, that a proven read-only flow
  is activated by the kernel when the owner or an agent asks for it (State 1
  round 22 read "once proven" as activation at proof time; A06 rule 2).

## Not applicable here

- **HTTP router.** The kernel has no HTTP API of its own (K-11): every State 5
  operation is `internal-only` in `50_exposure_plan.json`, and no router
  handler is planned. The MCP entrance is `surface`'s.
