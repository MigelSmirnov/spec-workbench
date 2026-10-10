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
  `clock.kernel_now` returns it. `clock.monotonic_deadline` returns a
  `MonotonicDeadline`, a class `clock` owns, with `has_passed` and
  `remaining_ms` — the "way to ask whether it passed" of State 5; it is never
  stored (A19 rule 2).
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
15. **`MonotonicDeadline.remaining_ms`** rounds up, so zero remaining means
    `has_passed`.
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
      decision). The entrance is `http.server.HTTPServer`, which serves one
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

## Texts of earlier states changed by State 6

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
