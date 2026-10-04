# State 6 — Cabinet Kernel exact contracts

## Status

Draft of 2026-10-03. The exact signatures are `60_contracts.json`, the function
inventory `60_contract_plan.json`, the typed models `60_model_closure_domain.json`
(State 1 records M01–M28 under their State 1 field names, the closed
enumerations, the platform manifest record) and `60_model_closure_operations.json`
(the arguments and answers the signatures name), the exception symbols
`60_exception_taxonomy.json`, and the State 5 exposure `50_exposure_plan.json`.
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
   does not change it. A key field whose value is `null` is not refused: `null`
   is the value the service receives, and the key covers it.
4. **Continuation tokens** (A16 rule 6, carried by State 2): `store` issues the
   base64url text, without padding, of the canonical JSON of the record type, the
   SHA-256 of the canonical filter, and the store position of the last item
   returned. A token that does not decode, or names another record type or
   filter, is `invalid_request`. The repair view's token is `surface`'s: the
   same encoding of the slot, the implementation set of its first page and the
   `store` token.
5. **Constants carry a declared schema.** A flow constant is a typed literal
   (M16): the composing agent declares its `value_schema` with its class, and its
   StoredValue takes both. Phase 2 of the proof checks that the declared schema
   is the target port's stored schema (M21) and that the value fits the port
   (A05 rule 1); the constant's identity does not depend on resolving another
   record.
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
   (A08 rules 1 and 6).
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
11. **A NodeExecution carries `detail_code`** beside `failure_detail`: the closed
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
    inputs (A07 rule 3) — must travel with it to be masked.
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

## Texts of earlier states changed by State 6

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
- **Persistence backend.** No `70_persistence_closure.json`: the store is on the
  ordinary generation path.
