# State 5 — Cabinet Kernel public module operations

## Status

Draft of 2026-10-03. One public operation per State 3 capability, each proven
by the State 4 flows `50_api_plan.json` names. An operation is what another
module, or the host, may call; everything else a module does is hidden.
Inputs and outputs name State 1 models; field types, the JSON Schema subset and
Python signatures are State 6's.

## Conventions every operation follows

- **Actor.** Every operation that writes a record receives the acting Actor M27
  — owner, agent by name, or kernel — from its caller; `module:surface`
  determines it from the token (A16 rule 3) and nothing else names it. The
  start-up operations — `effects.recover_in_flight_attempts`,
  `runs.recover_running_runs` — take no actor: they act as the kernel (A14
  rule 5, K-15).
- **Facts passed down.** A lower module never looks up a fact of a module above
  (State 3): what a call needs about a run, a flow version or an actor arrives
  as an argument.
- **Time.** Every timestamp an operation records comes from
  `clock.kernel_now`, taken at the moment the field names: a `started_at` when
  the execution or send begins — for an operation's NodeExecution, the
  `recorded_at` of its EffectAttempt when it has one (A11 rule 4) — every other
  time when its store change is made.
- **Refusal.** An operation either returns its output or refuses with one code
  of the closed set below and a bounded reason naming the first failing check
  in its rule's order. A refusal is decided before the operation's first store
  change, so it writes nothing; a refused capture copies nothing either (State
  3, "Nothing copied for a refused capture"). Codes are distinct only where
  some caller acts on the difference (K-17).
- **Values enter canonical.** `module:surface` turns every JSON text a
  request carries — a value, a port's `value_schema`, a guard value — into its
  canonical form with `canonical_values.canonical_bytes` before any module
  sees it; a text JCS cannot represent is `invalid_request` (A01 rule 1:
  refused where it enters). Modules below receive canonical bytes and compare
  schemas as equal text.
- **Checks answer, they do not refuse.** An operation that answers a question —
  `fit_port_value`, `check_request_shape`, `prepare_request`'s pre-send
  checks, `check_binding_current`, `send_prepared_request` — returns a
  failure as its result, which the caller concludes — a reference to no
  record is still `unknown_reference`; only operations that
  would change or return something refuse.
- **Several refusals.** When an operation's Errors list several refusals, they
  are checked in the order listed, and the first that holds is returned. When
  several records a request names do not exist, the `unknown_reference` names
  the first of them in the order the operation's Inputs list them (A16 rule 1:
  checks in the order listed).
- **Reason.** A refusal's reason is at most `bounded_text_bytes_max`, cut at a
  UTF-8 character boundary. It is text for a reader, naming the failed check
  and the record or field it concerns; it is not a machine identifier, and no
  caller branches on it — callers act only on the code, which is why codes are
  closed and reasons are not (K-17). A missing record is `unknown_reference`
  naming it, whatever operation looked it up.
- **Order.** Every collection in an output is in store order unless the
  operation names another order.
- **`map_index`** is absent, never a sentinel, for an element of a node that
  is not mapped — in a NodeExecution, a WaitingPoint, a SpooledFile identity
  and every input naming one; in (`node_id`, `map_index`) order an absent
  index comes before index 0 (A14 rule 2).
- **Naming an element.** A run or a node of its pinned version that does not
  exist is `unknown_reference`; a `map_index` given for a node that is not
  mapped, or absent for one that is, is `refused` — a mapped node's own
  record without `map_index` (A15 rule 1: it ran no element) records no
  execution, so no operation that names an element addresses it; it is read
  with the run's trace; a well-formed element with no
  record yet is a result — not reached, or empty — never a refusal. Every
  operation that takes an element makes these checks, except one whose Enforces
  says it trusts the facts its caller passes down (State 3) —
  `effects.reach_operation_element` and `effects.operation_element_conclusion`,
  both called only by `runs` for an element of a run it has read — which make
  none of them and have no such refusal.
- **Naming records.** A record with a minted or computed identity is named by
  it. A start-up operation passes the kernel as the Actor of the store changes
  it makes. Every other operation passes the request's actor, except where it
  acts as the kernel (admission and its trial executions, the activation that
  follows it, the activation of a read-only flow); the actor lands only in the
  by-fields of the records written — an explicit try's in the TrialExecution's
  `executed_by` — and a record with none is the kernel's own work (M27). A NodeExecution and an EffectAttempt are named by (`run_id`,
  `node_id`, `map_index`, `attempt_number`); a SpooledFile as
  `read_spooled_file` says; an Activation or FlowActivation by its store
  position.
- **Files in checks.** A check is given a file as facts — digest, size, media
  type — never bytes; a caller holding bytes computes the facts first.
  Building a request is not a check: `service_invoker.prepare_request` takes
  the bytes it must send.
- **A run holds its spool** while it has not ended, and after it ended
  `failed` until it is released (A15 rule 5). That is `runs`' rule: `runs`
  checks it before it spools or reads a run's file, `effects` acts only on
  facts `runs` passed down, and `surface` checks it from `runs.read_run`
  before `read_spooled_file`, refusing it with `refused`; `store` trusts them. It is decided from the run's
  record, never from whether bytes are still on disk: a spooled file of a run
  that no longer holds its spool is refused even while its bytes await removal.
- **Spool removal** follows every store change in which `runs` ends a run
  `succeeded`, `refused` or `cancelled`, in whichever operation that happens,
  and every release (A14 rule 4). It never fails a request: a run's records are written first,
  and a spool that cannot be removed then is removed at the next start, which
  removes the spool of every ended run that keeps none (A18 rule 4).
- **Internal error.** `internal_error` is not a refusal, so "a refusal writes
  nothing" does not hold for it. A failed store call changes no record (A18 rules 3-4); the
  module returns it as `internal_error` and `module:surface` answers without
  detail (A16 rule 7). When a request makes several store changes, those made
  before the failed one stay: each is whole, and a run is derived from its
  records (A14 rule 6; State 3, "Run state after an element").
- **Stop required.** An unconfirmed sandbox cleanup is not a refusal: it is
  the separate internal result `stop_required`, returned up the call chain
  after the caller wrote its record; `module:surface` answers
  `internal_error` — here, unlike any other internal error, that record was
  written — and ends the process (State 3, "Unconfirmed cleanup").

## Closed set of refusal codes

Returned to a caller of the MCP surface:

| code | meaning | who acts on it |
|---|---|---|
| `unauthorized` | the one token refusal: missing, unknown or revoked token, or no valid token list (A16 rules 1–2) | the caller fixes its token |
| `invalid_request` | size, unknown operation, unknown field, a field over its bound, a JSON text JCS cannot represent, a malformed continuation token (A01 rule 1, A16 rules 1, 4, 6) | the caller fixes the request |
| `not_permitted` | the actor may not call this operation (A16 rule 3) | the caller asks the owner |
| `unknown_reference` | a named record does not exist (State 0) | the caller re-reads |
| `refused` | an operation's own check failed; the reason names the check | the caller reads the reason |
| `internal_error` | the failing store change wrote nothing; changes the request made before it stay (Conventions); no detail (A16 rule 7) | the caller re-reads before repeating; the owner reads the host log |

Between modules, a refusal is the same pair (code, reason); `module:surface`
returns it unchanged except `internal_error` and `stop_required`, which it
answers as `internal_error`.

Details of an element that concluded `operation_failed` (A09 rule 6, A08 rule
6) are a closed set too, because the owner acts on each differently:
`binding_stale` — for every failure of the record itself, a changed digest
or an operation no longer invocable alike (A08 rule 6; accept a new binding),
`instance_not_selected`, `instance_address_missing`,
`required_header_repeated`, `required_header_invalid`, `plain_http_not_allowed` and
`credential_unresolved` (fix the installation), `input_not_placeable` (fix
the flow's data), `redirect_not_followed` (a `read` answered 3xx, A09 rule
5). Other details: `value_too_large` (A15 rule 4),
`cleanup_failed` (A03 rule 7), `applied_outputs_unknown` (A11 rule 3).

## Named store changes (`record_change`)

Each is one transaction (K-17); the module named is its only caller. Records
not listed are never written.

| change | caller | writes |
|---|---|---|
| `issue_contract_version` | `functions` | ContractVersion M03, and Slot M02 when new |
| `add_trial_case` | `functions` | StoredValues M21 of the case, TrialCase M06 |
| `record_implementation` | `functions` | Implementation M05 |
| `record_trial_execution` | `functions` | one TrialExecution M07 and the StoredValues of its `value` outputs; a file output is held by its facts only, never as a StoredValue |
| `record_admission_verdict` | `functions` | AdmissionVerdict M08, and Activation M09 when admitted and not current |
| `record_activation` | `functions` | Activation M09 of a rollback, or of a reused `admitted` verdict whose implementation is not current |
| `propose_binding` | `bindings` | OperationBinding M11 `proposed` |
| `accept_binding` | `bindings` | the binding `accepted` |
| `compose_flow_version` | `flows` | FlowVersion M13 with nodes, edges, constants and their StoredValues; Flow M12 when new |
| `activate_flow_version` | `flows` | FlowActivation M18 |
| `start_run` | `runs` | Run M19 `running` with pins and input StoredValues |
| `record_run_progress` | `runs` | NodeExecutions M23 written together, in (`node_id`, `map_index`) order, with their StoredValues and SpooledFiles M22; then the run's status, outputs, WaitingPoints M20, `ended_at`, `cancelled_by` |
| `record_resumption` | `runs` | a resumption of the run |
| `release_run` | `runs` | `released_by`, `released_at` |
| `request_approval` | `effects` | EffectApproval M24 `requested` with its preview |
| `decide_approval` | `effects` | the approval `approved`, or `refused` with the element's NodeExecution `refused_by_owner` |
| `record_attempt_in_flight` | `effects` | EffectAttempt M26 `in_flight` with its authority |
| `record_attempt_outcome` | `effects` | the attempt's conclusion, the concluding NodeExecution, its StoredValues and SpooledFiles, the approval `used` unless `not_sent` |
| `record_read_outcome` | `effects` | the concluding NodeExecution of a `read` send with its StoredValues and SpooledFiles; no attempt (A10 rule 6) |
| `record_operation_failure` | `effects` | the concluding NodeExecution `operation_failed` of a pre-send failure, no attempt |
| `resolve_attempt` | `effects` | the attempt `applied` or `not_applied` with `resolved_by` |
| `grant` / `revoke` | `effects` | StandingGrant M25 `active`, or `revoked` |
| `recover_in_flight` | `effects` | one `in_flight` attempt `unknown`, its missing NodeExecution `outcome_unknown`, its approval `used` — one change per attempt |

A change is named, and its payload is the records that change lists; State 5
fixes which records each change writes, State 6 the typed payload of each. `store`
checks only its own invariants — attempt numbers, unique and existing
identities, links, no record of a kind A01 rule 6 lists edited — a lifecycle change of another entity (a status, who
decided or resolved or released and when, `concluded_at`) updates those fields
of the entity's one record in place, which keeps its store position, the
position of its creation; every other field is never changed — and trusts its caller for every rule of
the caller's decision. The caller supplies each record's facts, its content identities computed with
`canonical_values`, and the time from `clock.kernel_now`; `store` adds what
only it can: store positions, `attempt_number` and minted identities.
`store` assigns `attempt_number` inside each change that writes a
NodeExecution or an EffectAttempt (State 3, "Attempt numbers") — and, inside
`request_approval`, the EffectApproval's `attempt_number`, the element's next
number, without taking it (A11 rule 1) — and mints the
random identities of A01 rule 2 inside the change that creates the record,
minting again on a collision.

## Questions carried to State 5, closed here

1. **TrialExecutions of one admission** are written one per case,
   `record_trial_execution`, each when its case concludes; the verdict follows
   in `record_admission_verdict`. An interrupted admission keeps the evidence
   it produced and has no verdict (A04 rule 2).
2. **Which of several approvals with the same `request_digest`** (State 3,
   carried from round 19): among the element's `approved` unused approvals
   that count — after a `not_applied` resolution only those whose
   `attempt_number` is greater than that of the element's latest attempt
   resolved `not_applied` (A10 rule 1) — the oldest in store order.
3. **Which FlowActivation a `draft-write` send names** (A10 rule 6): the latest
   FlowActivation of the run's pinned version before the Run record in store
   order — the one under which it started. `runs` finds it and passes it to
   `effects` with every call about one of the run's elements (State 3, "Facts
   passed down"); store order, not time, so two records never tie. A run's
   version was active when it started (A12 rule 1), so "none" cannot occur;
   if it does, the store is inconsistent and the call is `internal_error`.
4. **Who mints random identities** and retries a collision: `store`, inside
   the change that creates the record (above).
5. **Filter forms of `store.page_records`**: no condition, or one — a field
   equal to a value, or a field in a non-empty set of values — at most
   `page_size_max` when a caller of the MCP surface gives it — taken without
   duplicates and in code-point order so that equal sets
   page alike, `surface` passing that canonical form and `store` binding the
   token to it — on one record type, the
   field one of those the MCP catalogue below allows for that type; any other
   field, or a second condition, is `invalid_request` from `module:surface`,
   which owns the catalogue; `store` checks only the continuation token, bound
   to that record type and filter.
6. **The owner reading a spooled file's bytes** (A10 rule 2): an inspection
   read of `module:surface` through `store.read_value_bytes`, refused to an
   agent and once the run's spool is gone.
7. **How a grant learns a node's effect class** (State 4 round 4):
   `effects` reads the node's binding through `bindings.read_binding`.
8. **A manifest that cannot be read at start** in
   `bindings.check_installed_instances`: the start stops and names it; every
   start step is required (State 3, "Start"). A record that fails a check of
   the record itself (A08 rule 5) counts here as one that cannot be read.

## Relations of `store.read_records`

Besides reading records by identity, `store.read_records` answers exactly these
relations, each in store order unless named otherwise. A read by identity takes one or more identities and answers in the order
given, a repeated identity once. A call names the
relation and passes the records its name mentions — a slot, a contract
version, an implementation and a corpus digest, a flow, a flow version and a
run, a run, an element, a flow version's node — or, for "by status", the
status. An element is passed as (`run_id`, `node_id`, `map_index`). A call
that passes other arguments is a defect of its caller and
answers `internal_error` — so does one that omits an argument its relation
names or passes one of another kind; that defect is decided before any record
is looked up. The record a relation
names — every one of them — must exist, or the call is
`unknown_reference`, naming the first missing record in the order the
relation's name mentions them (A16 rule 1: checks in the order listed); from an existing
record, an empty answer is a result, not a refusal. A corpus digest is a value,
not a record: a digest no verdict covers answers none. "Runs by status" and
"attempts by status" start from no record and are never `unknown_reference`. Only the modules named ask.

| relation | asked by | answers |
|---|---|---|
| contract versions of a slot | `functions` | ContractVersions M03 |
| implementations of a contract version | `functions` | Implementations M05 |
| corpus of a contract version | `functions`, `surface` (repair view) | TrialCases M06 in corpus order |
| trial executions of an implementation on its contract version's corpus | `surface` (repair view) | per case of the current corpus, in corpus order, the implementation's latest TrialExecution M07 in store order — from admission or a try alike, since an outcome depends only on implementation and case; a case never executed is omitted |
| verdict of an implementation over a corpus digest | `functions` | the AdmissionVerdict M08, or none |
| verdicts of an implementation | `functions` | AdmissionVerdicts M08 |
| latest activation of a contract version | `functions` | the Activation M09, or none |
| versions of a flow | `flows` | FlowVersions M13 |
| latest activation of a flow | `flows` | the FlowActivation M18, or none |
| latest activation of a flow version before a run's record in store order | `runs` | the FlowActivation; none cannot occur, and finding none is `internal_error` (closed question 3) |
| executions of a run | `runs` | NodeExecutions M23 with their SpooledFiles M22 |
| executions of an element | `effects`, `runs` | the element's NodeExecutions M23 with their SpooledFiles M22, from which it reads an operation element's conclusion (A11 rule 3) and the attempt number a read send's file — or, for `runs`, a function element's file — is spooled under |
| runs by status | `runs` | Runs M19 with that status, oldest first (A14 rule 5) |
| approvals of an element | `effects` | EffectApprovals M24 |
| attempts of an element | `effects` | EffectAttempts M26 |
| attempts by status | `effects` | EffectAttempts with that status (A11 rule 4) |
| active grant of a flow version's node | `effects` | the StandingGrant M25, or none |

## How answers carry values

Records reach a caller as they are (State 3), with values resolved by
`module:surface`: a `value` StoredValue as its JSON content; a file —
StoredValue fixture or SpooledFile — as digest, size and media type, a spooled
file's bytes only through `read_spooled_file` and a fixture's only through
`read_fixture_file`. For an agent, every `personal_data` value
or file is its digest and class only, with no `value_id` (A07 rule 4), an
approval preview with any `personal_data` input carries no built request,
only the approval's `request_digest` (A07 rule 4), and a
classified `failure_detail` its length and class (A07 rule 5). A
`map_index` is absent for an element of a node that is not mapped.
Wherever an answer shows a spooled file — a trace record, an approval
preview's file input — it carries the SpooledFile's full identity, so that the owner can pass it to `read_spooled_file`, and wherever it shows a trial case's file fixture it carries the fixture's `value_id`, so that the owner can pass it to `read_fixture_file` — except a
`personal_data` file shown to an agent, which is its digest and class only
(A07 rule 4).

A run's answer, wherever an operation returns one, holds: `run_id`, the flow
version, status, starter and times, outputs produced, waiting points with
their reasons and, for `owner_approval`, the `approval_id` of the element's
`requested` approval — one always exists while it waits (A10 rule 2), once ended the
reason per missing output (A13 rule 7), and, once a `failed` run's spool is
released, `released_by` and `released_at` (M19) — every operation returning a
run, `release_run` among them, returns this one answer. An implementation's code reaches an
agent only in `get_repair_view`, for the slot's current implementation; every
other answer to an agent names an implementation without its code (K-12).
Answers have no size ceiling of their own: every field they carry is bounded
where it was accepted (A16 rule 4, A20).

## MCP surface catalogue

The one fixed set of typed operations over `mcp` (K-11), one per State 0
action. Each is handled by `module:surface` in A16 rule 1 order and then calls
the module operation named; every answer is masked for an agent under A07
rules 4–5. Field schemas and bounds are State 6's. "Agent" means any agent,
"author" an agent with the author right.

| MCP operation | actor (A16 rule 3) | calls |
|---|---|---|
| `issue_contract_version` | author | `functions.issue_contract_version` |
| `add_trial_case` | author | `functions.add_trial_case` |
| `submit_implementation` | author | `functions.submit_implementation` |
| `try_implementation` | agent | `functions.try_implementation` |
| `capture_failed_execution` | owner, author | `runs.capture_failed_execution` |
| `roll_back_slot` | owner, author | `functions.roll_back_slot` |
| `propose_binding` | agent | `bindings.propose_binding` |
| `accept_binding` | owner | `bindings.accept_binding` |
| `compose_flow_version` | agent | `flows.compose_flow_version` |
| `prove_flow_version` | agent | `flows.prove_flow_version` |
| `activate_flow_version` | owner, agent (`read` only, A06) | `flows.activate_flow_version` |
| `start_run` | owner, agent | `runs.start_run` |
| `resume_run` | owner, agent | `runs.resume_run` |
| `release_run` | owner, agent | `runs.release_run` |
| `decide_effect_approval` | owner | `runs.continue_after_approval` |
| `resolve_unknown_outcome` | owner | `runs.continue_after_resolution` |
| `cancel_run` | owner | `runs.cancel_run` |
| `grant_standing_approval` | owner | `effects.grant_standing_approval` |
| `revoke_standing_approval` | owner | `effects.revoke_standing_approval` |
| `get_slot` | owner, agent | `functions.read_slot` |
| `get_repair_view` | owner, agent | one slot's repair read (A15 rule 6, K-12), not a list operation of A16 rule 6: `functions.read_slot`; the current contract version through `functions.read_contract_version` and its whole corpus; the current implementation through `functions.read_implementation`, with code, and its trial executions on the corpus — none, without an error, when the current contract version has no current activation; and through `store.page_records` the latest NodeExecutions of the slot's implementations — `page_size_default` unless the caller asks another size, at most `page_size_max` (A16 rule 6) — with a continuation token that also carries the implementation set of its first page; passed back, it pages only the NodeExecutions below that position for that set — an implementation added since has only newer executions, so nothing below is missed — and every other part is read again as of that request; the token is bound to its slot, so passed with another slot it is `invalid_request`, as the rule below the table says for every continuation token, and only the page size may change |
| `get_contract_version` | owner, agent | `functions.read_contract_version` |
| `get_implementation` | owner with code; agent without code (K-12) | `functions.read_implementation` |
| `get_binding` | owner, agent | `bindings.read_binding` |
| `get_flow` | owner, agent | `flows.active_flow_version`, `flows.read_flow_version`: the flow's purpose, its active version and FlowActivation, or that none is active |
| `get_flow_version` | owner, agent | `flows.read_flow_version` |
| `get_run` | owner, agent | `runs.read_run` |
| `list_records` | owner, agent | `store.page_records`; for runs, each run's answer from `runs.read_run` (State 3, "Runs are listed from their records") |
| `read_spooled_file` | owner | `store.read_value_bytes` |
| `read_fixture_file` | owner | `store.read_records`, `store.read_value_bytes` |

`list_records` is the inspect and read-a-trace action over one record type,
with no filter or one condition — equal to a value, or in a set of values —
on one of the fields allowed for it; any other field is
`invalid_request`. A filter value naming no record is not a refusal: the page
is empty, and a set filter matches the records its existing members name. A
`status` value outside its model's closed set is `invalid_request`. A
continuation token used with another slot, record type or filter than it was
issued for is `invalid_request`; the page size may change between pages. When resolving a value for an answer fails,
the whole answer is `internal_error`; no partial answer is returned.

| record type | filter fields |
|---|---|
| slots, flows | none |
| contract versions | `slot_id` |
| implementations, trial cases | `contract_version_id` |
| trial executions | `implementation_id`, `trial_case_id` |
| admission verdicts | `implementation_id` |
| bindings | `status`, `service_id` |
| flow versions | `flow_id` |
| runs | `flow_version_id`, `status` |
| node executions (the trace) | `run_id`, `executed_implementation`, `executed_binding` — two names for M23's one `executed` field, by the kind of record it names; a record without `executed` matches neither |
| approvals | `run_id`, `status` |
| standing grants | `flow_version_id`, `status` |
| effect attempts | `run_id`, `status` |

No other record type is listed: activations are read through `get_slot`, flow
activations through `get_flow`, stored values within the records that name
them, spooled files through `read_spooled_file`; asking `list_records` for one
of them is `invalid_request`.

`read_spooled_file` takes only a SpooledFile — never a StoredValue — and names
it by its identity — `run_id`,
`producer_node_id`, `map_index` (omitted for a node that is not mapped),
`attempt_number`, `producer_port`, `list_index` (omitted for a `one`
port) — the lookup identity and the request's only fields; its digest, size
and media type are not asked, they come back in the answer. The identity is
looked up whole, not checked as an element: one whose `map_index` or
`list_index` is given where the record has none, or absent where it has one,
names no SpooledFile, and an
identity naming no SpooledFile is `unknown_reference`; the record outlives its
bytes — and returns its bytes whole, at most `spool_file_bytes_max` (A15 rule 3); it is
refused once the run's spool is gone, and an agent gets `not_permitted` (A10
rule 2). Checks run in that order of A16 rule 1: the actor; then the record's
existence, through `store.read_records`; then whether its run holds its
spool, from `runs.read_run`; only then are the bytes read through
`store.read_value_bytes`.

`read_fixture_file` takes only the `value_id` of a trial case's file fixture
— a StoredValue with carriage `file`, the only kind (M21, K-10) — as the
request's only field, and returns that StoredValue with its bytes whole, at
most `trial_fixture_bytes_max` (A04 rule 1). A fixture is kept for as long
as the kernel keeps its trial case, so it has no spool check. Checks run in
the order of A16 rule 1: the actor — an agent gets `not_permitted`; then the
record's existence, through `store.read_records` — a `value_id` naming no
StoredValue is `unknown_reference`; then its carriage — a StoredValue of
carriage `value` is `refused`, its content is in the answers that name it;
only then are the bytes read through `store.read_value_bytes`.

## `public_op:canonical_values.canonical_bytes`

### Owner

`module:canonical_values`. Encode one value as RFC 8785 canonical JSON bytes, or refuse a value JCS cannot
represent.

### Callers

`module:sandbox`, `module:service_invoker`, `module:surface`.

### Inputs

One JSON value.

### Outputs

Its RFC 8785 canonical bytes.

### Observable effect

None.

### Enforces

Number formatting, string escaping and key order of JCS; no Unicode
normalization (A01 rule 1).

### Errors

`refused` for a value JCS cannot represent: a non-finite number, a duplicate
key.

### State impact

Pure; touches no record.

## `public_op:canonical_values.content_identity`

### Owner

`module:canonical_values`. Compute the SHA-256 identity of a content record or value from its canonical
form, order-free lists sorted.

### Callers

`module:functions`, `module:bindings`, `module:flows`, `module:runs`, `module:effects`, `module:service_invoker`.

### Inputs

One content record's meaning facts as State 1 names them for that record, or
one value.

### Outputs

The SHA-256 hex digest of its canonical form.

### Observable effect

None.

### Enforces

Order-free lists sorted before hashing — ports by (`direction`, `name`), nodes
by `node_id`, edges in A05 edge order, constants by (`to_node`, `to_port`);
list values keep their order (A01 rule 1).

### Errors

`refused` as `canonical_bytes`.

### State impact

Pure; touches no record.

## `public_op:canonical_values.fit_port_value`

### Owner

`module:canonical_values`. Judge one value against one port — presence, carriage, schema, size, many — and
name the first failure.

### Callers

`module:functions`, `module:flows`, `module:runs`, `module:sandbox`, `module:service_invoker`.

### Inputs

One Port M01, the size bound that applies where the caller stands
(`stored_value_bytes_max`, `trial_fixture_bytes_max` or
`spool_file_bytes_max`), and one candidate, which may be absent — presence is
the first check: a JSON value, checked against the port's schema, its size
bound applying to the whole value, a `many` value included; or for a file its
digest, size and media type; or for a `many` file port an ordered list of
those, each checked in list order against the per-file size bound. A file's
content is not inspected (K-10): for a file, the schema check is its media type
against the port's.

### Outputs

Fits, or the first failing check: presence, carriage, schema — for `many`, a
JSON array whose every element fits — then size.

### Observable effect

None.

### Enforces

One order of checks for every caller (A04 rule 1, A12 rule 1, A13 rule 3); "the
same schema" means equal canonical JSON (A05 rule 2).

### Errors

None: a failed fit is a result; the caller decides what it concludes.

### State impact

Pure; touches no record.

## `public_op:canonical_values.highest_disclosure_class`

### Owner

`module:canonical_values`. Return the highest disclosure class of a set, open when empty.

### Callers

`module:functions`, `module:flows`, `module:runs`, `module:surface`.

### Inputs

A set of disclosure classes, possibly empty.

### Outputs

The highest by `open < business_confidential < personal_data`, `open` when
empty.

### Observable effect

None.

### Enforces

The one order of the disclosure classes, the declared order of their `models` enumeration (A07 rule 1); no construct lowers a class.

### Errors

None.

### State impact

Pure; touches no record.

## `public_op:clock.kernel_now`

### Owner

`module:clock`. Return the one kernel timestamp source.

### Callers

`module:functions`, `module:bindings`, `module:flows`, `module:effects`, `module:runs`.

### Inputs

Nothing.

### Outputs

The current kernel timestamp.

### Observable effect

None.

### Enforces

The only reader of the wall clock; replaceable as a whole in tests (A19).

### Errors

None.

### State impact

Reads the host clock only.

## `public_op:clock.monotonic_deadline`

### Owner

`module:clock`. Return a monotonic deadline for a bounded wait.

### Callers

`module:sandbox`, `module:service_invoker`.

### Inputs

A duration in milliseconds.

### Outputs

A monotonic deadline and a way to ask whether it passed.

### Observable effect

None.

### Enforces

Deadlines never read the wall clock; no time limit decides anything beyond the
wait it bounds (A14 rule 1).

### Errors

None.

### State impact

Reads the host monotonic clock only.

## `public_op:store.open_store`

### Owner

`module:store`. Take the exclusive lock, check the data directory and remove temporary files
before any record is read.

### Callers

`module:surface`.

### Inputs

The data directory from the installation.

### Outputs

An open store holding the exclusive lock.

### Observable effect

The store's own temporary files — those it writes before a rename (A18 rule 4)
— are removed; nothing else is.

### Enforces

One process per directory; private directory; no symbolic link anywhere;
nothing else is removed (A18 rules 1, 2, 4).

### Errors

`refused` naming a data directory that does not exist, the lock held, a
directory not private, or a symbolic link; the start stops. The kernel never
creates the data directory itself: the owner creates it, private to the
kernel's user; inside it `open_store` creates the database schema, the
content-addressed area and the spool area when absent.

### State impact

Takes the lock; removes temporary files only.

## `public_op:store.page_records`

### Owner

`module:store`. Page one record type in reverse store order under a caller filter, refusing a
token that names no record of that type.

### Callers

`module:surface`.

### Inputs

One record type, no filter or one — a field equal to a value or in a set of
values — a page size and an optional continuation token.

### Outputs

Up to the page size of records, newest first in reverse store order, and the
next continuation token when more remain.

### Observable effect

None.

### Enforces

A record added meanwhile never shifts, repeats or hides an item; the token is a
store position (A16 rule 6). The filter is applied as of each page's request:
a record whose filtered field changed since an earlier page is judged by its
value now, and the token stays valid when the record it names no longer
matches.

### Errors

`invalid_request` for a token that names no record of that type — a token is
bound to its record type and filter. Allowed fields and the number of
conditions are checked by `surface` before the call.

### State impact

Read-only.

## `public_op:store.put_value_bytes`

### Owner

`module:store`. Publish value bytes or a file fixture complete and digest-checked into the
content-addressed area, equal bytes once.

### Callers

`module:functions`, `module:flows`, `module:runs`, `module:effects`.

### Inputs

Bytes and their expected digest and size.

### Outputs

The digest under which the bytes are stored.

### Observable effect

The bytes exist in the content-addressed area.

### Enforces

Written to a temporary file, flushed, checked, renamed; a completed file is
never overwritten; equal bytes are stored once (A18 rule 4).

### Errors

`refused` when digest or size do not match; `internal_error` on a link or I/O
failure, nothing published.

### State impact

Adds content-addressed bytes; writes no record. Bytes whose record never
follows — a later failure of the caller's attempt — stay unnamed; nothing
removes them and equal bytes reuse them (A13 rule 3).

## `public_op:store.read_records`

### Owner

`module:store`. Read records a caller names, by identity or by owner-defined relation.

### Callers

`module:functions`, `module:bindings`, `module:flows`, `module:effects`, `module:runs`, `module:surface`.

### Inputs

One record type and identities, or one relation of the closed set in "Relations
of store.read_records".

### Outputs

The records as stored: for identities, in the order given, a repeated identity
once at its first occurrence; for a relation, in its order. Existing records
with nothing related answer empty.

### Observable effect

None.

### Enforces

Only `store` opens the database; the records A01 rule 6 lists are never
edited, and an entity's lifecycle fields change in place (Conventions).

### Errors

`unknown_reference` for the whole call when any named identity does not exist,
naming the first missing one in the order given; nothing is returned.
`internal_error` for a call whose relation arguments are a defect of its caller
("Relations of `store.read_records`"), decided before any record is looked up.

### State impact

Read-only.

## `public_op:store.read_value_bytes`

### Owner

`module:store`. Return the bytes a StoredValue or SpooledFile names; whether a run still holds
its spool is checked by its caller.

### Callers

`module:functions`, `module:runs`, `module:effects`, `module:surface`.

### Inputs

The identity of a StoredValue M21, or of a SpooledFile M22 (`run_id`,
`producer_node_id`, `map_index`, `attempt_number`, `producer_port`,
`list_index`); `store` resolves where the bytes are.

### Outputs

The bytes it names, digest-checked — for a `value` StoredValue its canonical
JSON bytes.

### Observable effect

None.

### Enforces

The caller names a record, never a place; content-addressed area or the run's
spool is `store`'s choice (owner, 2026-10-03).

### Errors

`unknown_reference` for an identity naming no record; `internal_error` when the
bytes of a record that should hold them are missing, unreadable or fail their
digest.

### State impact

Read-only.

## `public_op:store.record_change`

### Owner

`module:store`. Apply one named change of the closed set in one transaction, wholly or not at
all.

### Callers

`module:functions`, `module:bindings`, `module:flows`, `module:effects`, `module:runs`.

### Inputs

One named change of the closed set in "Named store changes" with its records —
each with the times its fields name — and the acting Actor.

### Outputs

The written records with every identity, position and `attempt_number` `store`
assigned.

### Observable effect

The records exist, all of them or none.

### Enforces

One call, one transaction; callers never name a transaction (K-17);
`attempt_number` is the element's next ordinal and an outcome names the attempt
still next (State 3); random identities minted inside, again on collision (A01
rule 2).

### Errors

`refused` when an outcome's attempt is no longer the element's next ordinal;
`internal_error` for any other broken invariant of its own, or a failed
transaction — nothing written either way.

### State impact

Writes exactly the records its change lists.

## `public_op:store.remove_run_spool`

### Owner

`module:store`. Remove the spool of a run the caller names.

### Callers

`module:runs`.

### Inputs

A run identity.

### Outputs

Done — also when the spool is already gone or the run is unknown: removal is
idempotent by intent, the one operation that does not refuse an unknown
reference.

### Observable effect

The run's spool directory is gone.

### Enforces

`store` removes what it is told; which spool goes is `runs`' decision (A18 rule
4, A14 rule 4).

### Errors

`internal_error` on an I/O failure; its caller does not fail the request on it
(Conventions, spool removal).

### State impact

Removes spooled files; writes no record.

## `public_op:store.spool_file`

### Owner

`module:store`. Publish a file into its run's spool with digest and size, within the spool
ceilings.

### Callers

`module:runs`, `module:effects`.

### Inputs

The producing attempt — `run_id`, node, `map_index`, `attempt_number` — the
port and `list_index`, the file's bytes and its port's media type.

### Outputs

The file's digest and size.

### Observable effect

The file exists in that run's spool.

### Enforces

Complete and digest-checked before it is visible; `spool_file_bytes_max` per
file and `spool_run_bytes_max` per run (A15 rule 3). A SpooledFile is named by
its producing position alone (SpooledFileKey); a file already at that position
that no SpooledFile record names — left by a change that failed — is replaced,
and one a record names is never overwritten: that call is `internal_error`. A
link or an I/O failure is `internal_error` with nothing kept of that file.

### Errors

`refused` over a spool ceiling, nothing kept of that file or of any file that
attempt spooled before (A15 rule 3); the caller concludes the element
(`resource_exhausted`, or `contract_violation` for an operation).

### State impact

Adds a spooled file; the SpooledFile record is written by the caller's change.
When that attempt fails for another reason the file stays unnamed in the run's
spool, counted toward the spool ceiling, until `remove_run_spool` or a later
write to its position (A13 rule 3); no operation removes one attempt's files
except this one's own refusal.

## `public_op:installation.current_token_list`

### Owner

`module:installation`. Return the current token list, re-read when the file changed, or none after a
failed re-read.

### Callers

`module:surface`.

### Inputs

Nothing.

### Outputs

The owner token and the agent tokens with name and author right, or none.

### Observable effect

None.

### Enforces

Re-read when the file's digest changed or it cannot be read; the four checks only;
a failed re-read leaves no list until one passes (A16 rule 2).

### Errors

None: "none" is a result on which `surface` refuses every request.

### State impact

Reads the configuration file.

## `public_op:installation.load_installation`

### Owner

`module:installation`. Load and check the configuration file at start.

### Callers

`module:surface`.

### Inputs

The configuration file path, the process's one command-line argument (A17 rule 1).

### Outputs

The loaded installation M28: data directory, manifest source, selected
instances, credential references, tokens, the `mcp` listen address.

### Observable effect

None.

### Enforces

Checks in this order, the first failing one named: a regular private file of
the kernel's user, not a link; one JSON object with exactly the installation's
fields; no service twice among the selected instances or among the credentials;
every credential header name an HTTP field-name token; every secret file
reference an absolute path; tokens of at least 43
characters; tokens pairwise distinct; agent names pairwise distinct (A16 rule 1,
A17 rule 1, M28).

### Errors

`refused` naming the failing check; the start stops.

### State impact

Reads the configuration file.

## `public_op:installation.manifest_source`

### Owner

`module:installation`. Return the manifest location and revision fixed at start.

### Callers

`module:bindings`.

### Inputs

Nothing.

### Outputs

The manifest location and revision fixed at start (M28).

### Observable effect

None.

### Enforces

Fixed until restart (A08 rule 6).

### Errors

None.

### State impact

Read-only.

## `public_op:installation.resolve_service_credential`

### Owner

`module:installation`. Resolve one service's credential header and value only while a request is
built.

### Callers

`module:service_invoker`.

### Inputs

A service identity.

### Outputs

Its credential header name and value, for one request being built.

### Observable effect

None.

### Enforces

Resolved only when a request to that service is built; the kernel never puts the
value into a record, trace, preview, detail, log, argument or response (A17
rule 2); a service's body echoing it verbatim, 2xx included, is withheld and not used (A09 rule 7).

### Errors

`refused` with `credential_unresolved` when the reference does not resolve.

### State impact

Reads the host secret store.

## `public_op:installation.selected_instance_name`

### Owner

`module:installation`. Return the manifest instance the installation selects for a service, or none.

### Callers

`module:bindings`.

### Inputs

A service identity.

### Outputs

The selected manifest instance name, or none.

### Observable effect

None.

### Enforces

No request, flow or binding chooses another instance (A17 rule 4, K-16).

### Errors

None: "none" is a result.

### State impact

Read-only.

## `public_op:sandbox.execute_function`

### Owner

`module:sandbox`. Execute one implementation on one input set in a fresh isolated environment and
name how it ended.

### Callers

`module:functions`, `module:runs`.

### Inputs

Implementation code, the input values and file bytes by port, the contract's
ports and ResourceBounds M04.

### Outputs

With the output count taken through `canonical_values.canonical_bytes`, exactly
one outcome of `timeout`, `resource_exhausted`, `sandbox_violation`, `crashed`,
`contract_violation`, `succeeded`; on success the outputs by port; resources
used; a bounded `failure_detail` otherwise.

### Observable effect

A fresh environment was created and, on return, confirmed removed.

### Enforces

Isolation, traps, limits from outside and the outcome order of A03; outputs validated against the output ports with
`canonical_values.fit_port_value`, the bound passed being the execution's
`output_bytes`; `stored_value_bytes_max` and the spool ceilings are not the
sandbox's — `runs` and `store` apply them after the execution has otherwise
succeeded (A15 rules 3 and 4).

### Errors

None: an unconfirmed cleanup is the result `crashed` with detail
`cleanup_failed`; the caller writes the record and returns `stop_required`
(Conventions; State 3).

### State impact

Writes no record; runs a process.

## `public_op:sandbox.probe_sandbox`

### Owner

`module:sandbox`. Check at start that bubblewrap is present and one probe execution succeeds.

### Callers

`module:surface`.

### Inputs

Nothing.

### Outputs

Done.

### Observable effect

None.

### Enforces

`bubblewrap` present and one probe execution succeeds (A03 rule 8).

### Errors

`refused` naming what is missing; the start stops.

### State impact

Runs one probe process.

## `public_op:service_invoker.check_request_shape`

### Owner

`module:service_invoker`. Judge whether a binding's ports fit the request shape of its method and path.

### Callers

`module:bindings`.

### Inputs

A method, a declared path and a binding's input and output Ports.

### Outputs

Fits, or the first failing rule.

### Observable effect

None.

### Enforces

A09 rules 1–3 by port declarations alone: path placeholders, query types for
GET and DELETE, a file output alone and `one`.

### Errors

None: a misfit is a result `bindings` names as the proposal's check.

### State impact

Pure; touches no record.

## `public_op:service_invoker.prepare_request`

### Owner

`module:service_invoker`. Build one request from a ManifestOperation and inputs, with its description and
request_digest, or name the first pre-send failure.

### Callers

`module:effects`.

### Inputs

A ManifestOperation M10 with instance facts — its `service_id` names the
service —, beside it the selected instance's name exactly as
`bindings.check_binding_current` returned it, absent when none is selected,
the binding's input and output Ports, and the element's input values and file
bytes by port.

### Outputs

A prepared request — carrying the binding's output Ports for A09 rule 3 — its
description of A10 rule 7 and its `request_digest`; or the first pre-send
failure — a credential `installation` cannot resolve becomes
`credential_unresolved` here.

### Observable effect

None.

### Enforces

State 3 order after the binding: no selected instance (no name) is
`instance_not_selected`; no `api_base_url` (a name without one — whether the
record lists no instance of that name, the instance has no `api_base_url`, or
it is not an absolute `http` or `https` URL with a host, A08 rule 5) is
`instance_address_missing`; then a plain `http` target not allowed, a
repeated required header, an invalid required header
(`required_header_invalid`, A08 rule 5), then the credential, then input placement, input ports in
name order and a list's elements in list order, the first that cannot be placed
named (A09 rules 1, 2, 4, 6); credential by name only in the description (A10
rule 7); the description covers every header sent on the wire, and no header is
sent that it does not describe; one `host` header, the instance's required
`host` when it names one, else the authority of `api_base_url` (A10 rule 7); a `GET` or `DELETE` list input that is empty
adds no query parameter (A09 rule 2).

### Errors

None: a pre-send failure is a result with its detail from the closed set.

### State impact

Resolves a credential; writes nothing.

## `public_op:service_invoker.send_prepared_request`

### Owner

`module:service_invoker`. Send one prepared request once and name its outcome by the A09 table.

### Callers

`module:effects`.

### Inputs

One prepared request and the operation's effect class.

### Outputs

One outcome name of the A09 rule 5 table for that class, and for
`operation_failed` its detail code from the closed set (`redirect_not_followed`
for a `read` answered 3xx), and `value_too_large` for a `contract_violation`
whose output value exceeds `stored_value_bytes_max` (A15 rule 4); when the response is used, the output values by
port — none for a binding without output ports, whose body is ignored — or for
a file output its bytes with the port's media type, which `effects` spools; and
a bounded `failure_detail`.

### Observable effect

At most one HTTP request leaves the kernel.

### Enforces

No redirect, proxy or retry; `Accept-Encoding: identity`; TLS by instance
class; response limits; transport deadline (A09).

### Errors

None: every ending is an outcome name.

### State impact

Sends one request; writes nothing.

## `public_op:functions.add_captured_trial_case`

### Owner

`module:functions`. Add a case captured from a checked failed execution to its contract version's
corpus.

### Callers

`module:runs`.

### Inputs

The implementation the record executed, the contract version named, the
record's inputs as references — StoredValues, and spooled files as their
SpooledFiles —, the source NodeExecution, the actor.

### Outputs

The TrialCase M06 — new, or the equal existing one.

### Observable effect

The case is in the corpus; the corpus digest changed when new.

### Enforces

The executed implementation exists and its contract version, read from its own
record, is the one named; fit of every value; every file within
`trial_fixture_bytes_max` by its facts, read from its SpooledFile through
`store.read_records`; all before any byte is copied — only
then each spooled file is copied into the content-addressed area, so a refusal
copies nothing; inputs take the port's class (A04 rule 1, A15 rule 5, M21).

### Errors

`refused` naming the first failing check.

### State impact

`add_trial_case`.

## `public_op:functions.add_trial_case`

### Owner

`module:functions`. Add an authored trial case that fits its contract version.

### Callers

`module:surface`.

### Inputs

A contract version, input values by port, optional expected outputs, the actor.

### Outputs

The TrialCase with its identity and corpus place, counted from 0 in corpus
order — new, or the equal existing one.

### Observable effect

The case is in the corpus.

### Enforces

Fit in port name order — presence, carriage, schema, size; inputs take the
port's class, expected outputs the highest class of the inputs (A04 rule 1,
M21).

### Errors

`unknown_reference` for the contract version; `refused` naming the first
failing check.

### State impact

`add_trial_case`.

## `public_op:functions.current_activation`

### Owner

`module:functions`. Return a contract version's current activation, or none.

### Callers

`module:runs`, `module:surface`.

### Inputs

A contract version.

### Outputs

Its current Activation M09 with the implementation, or none.

### Observable effect

None.

### Enforces

Current is the latest activation in store order (A01 rule 3).

### Errors

`unknown_reference` for the contract version.

### State impact

Read-only.

## `public_op:functions.issue_contract_version`

### Owner

`module:functions`. Issue a contract version within the release ceilings, creating its slot when
new.

### Callers

`module:surface`.

### Inputs

A slot name, a purpose when the slot is new, input and output Ports,
ResourceBounds, the actor.

### Outputs

The ContractVersion with its identity — new, or the equal existing one; the
Slot when created.

### Observable effect

A new version becomes its slot's current contract version.

### Enforces

Purpose rule first (A01 rule 5); A02 rule 1 order; a bound above its ceiling or
omitted is refused, never clamped (A02 rule 2).

### Errors

`refused` naming the first failing check, with field and ceiling for a bound.

### State impact

`issue_contract_version`.

## `public_op:functions.read_contract_version`

### Owner

`module:functions`. Return one contract version's ports and bounds.

### Callers

`module:flows`, `module:surface`.

### Inputs

A contract version identity.

### Outputs

Its ports and bounds.

### Observable effect

None.

### Enforces

Contract versions are immutable (A01 rule 6).

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:functions.read_implementation`

### Owner

`module:functions`. Return one implementation's code and its contract version's bounds.

### Callers

`module:runs`, `module:surface`.

### Inputs

An implementation identity.

### Outputs

Its code, contract version and that version's ports and bounds.

### Observable effect

None.

### Enforces

Implementations are immutable; a run reads the one it pinned (A12 rule 2).

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:functions.read_slot`

### Owner

`module:functions`. Return a slot's contract versions, implementations, verdicts and current
activation.

### Callers

`module:surface`.

### Inputs

A slot name.

### Outputs

Its purpose and its current contract version; the whole history, unpaged — it
is a read of one slot, not a list operation of A16 rule 6 — and never
implementation code; per contract version in store order, its current corpus
digest, its implementations in store order each with its verdicts by corpus
digest — at most one per digest, since an existing verdict is reused (A04 rule
2), in store order — and its current activation; each implementation carries a
flag saying whether it holds an `admitted` verdict over its contract version's
current corpus.

### Observable effect

None.

### Enforces

A serving implementation without a verdict over its contract version's current
corpus is marked so explicitly, not left to be inferred (A04 rule 7).

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:functions.roll_back_slot`

### Owner

`module:functions`. Activate an earlier implementation admitted over the current corpus.

### Callers

`module:surface`.

### Inputs

A slot and an implementation of its current contract version, the actor.

### Outputs

The Activation now current.

### Observable effect

The named implementation serves the slot.

### Enforces

Requires an `admitted` verdict over the current corpus; runs no admission;
naming the current one records nothing (A04 rule 5).

### Errors

`unknown_reference`; `refused` for an implementation of another contract
version or slot, or without such a verdict.

### State impact

`record_activation`, or nothing.

## `public_op:functions.submit_implementation`

### Owner

`module:functions`. Accept an implementation, admit it over the whole corpus and activate it when
admitted.

### Callers

`module:surface`.

### Inputs

A contract version, Python code, the actor.

### Outputs

Not a refusal when admission fails: the Implementation, its AdmissionVerdict —
`admitted`, or `refused` with its reason — and when admitted the current
Activation — the new one, or the existing one when the implementation already
was current (A04 rule 4).

### Observable effect

When admitted and not current, the implementation serves its slot at once.

### Enforces

Identity from code and contract version; verdict reuse for an unchanged corpus
— a reused `admitted` verdict activates like a new one when the implementation
is not current; whole corpus in corpus order, never stopping early; activation
by the kernel (A04 rules 2–4, K-15).

### Errors

`unknown_reference`; code over `implementation_code_bytes_max` never arrives —
`surface` refuses it as `invalid_request` (A16 rule 4); `stop_required` from
the sandbox.

### State impact

`record_implementation` for new code only — an equal implementation records
nothing (A01 rule 4) — then, unless a verdict is reused, one
`record_trial_execution` per case and `record_admission_verdict`; for a reused
`admitted` verdict whose implementation is not current, `record_activation`.

## `public_op:functions.try_implementation`

### Owner

`module:functions`. Execute an existing implementation on named cases and return trial evidence, no
verdict.

### Callers

`module:surface`.

### Inputs

An existing implementation, optionally a list of its contract version's cases —
an empty list names none, so every case runs (A04 rule 6) — the actor.

### Outputs

One TrialExecution per case in corpus order: outcome, output digests, pass or
`output_mismatch`.

### Observable effect

None.

### Enforces

Unknown, foreign or repeated cases and an empty corpus refused before anything
executes; no verdict, no activation (A04 rule 6).

### Errors

`unknown_reference`; `refused` (`empty_corpus` or the case named);
`stop_required` from the sandbox.

### State impact

One `record_trial_execution` per case.

## `public_op:bindings.accept_binding`

### Owner

`module:bindings`. Accept a proposed binding after re-reading its manifest entry.

### Callers

`module:surface`.

### Inputs

A binding identity, the actor (the owner).

### Outputs

The binding `accepted`.

### Observable effect

Flow versions naming it can be proven (A05 rule 6).

### Enforces

Re-read as before a send; checks in A08 rule 5 order; an accepted binding
returned unchanged (A08 rule 7).

### Errors

`unknown_reference`; `refused` naming the check, `binding_stale` when only the
digest differs.

### State impact

`accept_binding`, or nothing.

## `public_op:bindings.check_binding_current`

### Owner

`module:bindings`. Before a send, return the current ManifestOperation with instance facts, or
binding_stale.

### Callers

`module:effects`.

### Inputs

A binding identity.

### Outputs

The current ManifestOperation M10 — and beside it, not in it, the selected
instance's name — with that instance's `base_url`, `required_headers` and
`instance_class` as read — the name absent when none is selected, the others
absent when missing — or `binding_stale` for any failure of the record itself
(A08 rule 6).

### Observable effect

None.

### Enforces

Judges only the record itself; instance facts passed on even when missing (A08
rule 6, State 3).

### Errors

`unknown_reference` for a binding that does not exist; staleness is a result
the caller concludes as `operation_failed`.

### State impact

Reads the manifest.

## `public_op:bindings.check_installed_instances`

### Owner

`module:bindings`. At start, refuse a credential header that names a required header or a kernel-set header.

### Callers

`module:surface`.

### Inputs

The loaded installation.

### Outputs

Done.

### Observable effect

None.

### Enforces

No credential header has, case-insensitively, the name of a required header of
its instance or one of `KERNEL_SET_HEADER_NAMES`, `host` included; reads
installation and manifest only (A09 rule 1). The services checked are those the
installation holds a credential for, in `service_id` code-point order; for
each, the kernel-set names are compared first, without reading the manifest;
then, only when the installation selects an instance for it, its manifest
record is read and that instance's required headers compared. A service with
no selected instance, or whose record lists no instance of the selected name,
fails nothing here: it is not invocable at send (A09 rule 6).

### Errors

`refused` naming the first failing service, services taken in `service_id`
code-point order and each one's manifest record read in its turn — an
unreadable record, or one failing a check of the record itself (A08 rule 5),
fails at its service; the start stops.

### State impact

Reads the manifest.

## `public_op:bindings.propose_binding`

### Owner

`module:bindings`. Check a proposal against the manifest and record it proposed with its pinned
digest.

### Callers

`module:surface`.

### Inputs

A service identity, an operation name, input and output Ports with classes, the
actor.

### Outputs

The binding `proposed` with its identity, effect class, key fields and pinned
`record_digest`.

### Observable effect

The owner can accept it.

### Enforces

A08 rule 5 order; effect class and key fields copied from the manifest, never
stated (M11).

### Errors

`refused` naming the first failing check (manifest mismatch).

### State impact

`propose_binding`.

## `public_op:bindings.read_binding`

### Owner

`module:bindings`. Return one binding: status, effect class, key fields, declared classes, ports.

### Callers

`module:flows`, `module:effects`, `module:surface`.

### Inputs

A binding identity.

### Outputs

Its status, service, operation, effect class, key fields, ports with classes,
pinned digest.

### Observable effect

None.

### Enforces

Bindings change only from `proposed` to `accepted`.

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:flows.activate_flow_version`

### Owner

`module:flows`. Prove a flow version again and activate it by the kernel or the owner.

### Callers

`module:surface`.

### Inputs

A flow version identity, the actor.

### Outputs

The flow's active FlowActivation.

### Observable effect

The version is the flow's active version; runs already started keep theirs.

### Enforces

A06 rule 4 order: prove again; an agent above `read` refused, nothing kept; the
active version returns its activation; actor kernel for `read`, owner otherwise
(A06, K-15).

### Errors

`unknown_reference`; `refused` with the proof failure, or for an agent above
`read`.

### State impact

`activate_flow_version`, or nothing.

## `public_op:flows.active_flow_version`

### Owner

`module:flows`. Return a flow's active version and its activation, or none.

### Callers

`module:runs`, `module:effects`, `module:surface`.

### Inputs

A flow identity.

### Outputs

The Flow M12 with its purpose, and its active flow version and FlowActivation,
or that none is active.

### Observable effect

None.

### Enforces

Active is the latest FlowActivation in store order (A01 rule 3).

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:flows.compose_flow_version`

### Owner

`module:flows`. Keep a flow version after its pre-proof refusals.

### Callers

`module:surface`.

### Inputs

A flow name, a purpose when new, ports, nodes, edges, guards, constants with
declared classes, the actor.

### Outputs

The FlowVersion with its identity — new, or the equal existing one — and the
proof result `prove_flow_version` computes for it at this call, also for an
equal existing version (State 0 "compose and prove"); the proof is not stored.

### Observable effect

The version is kept, proven or not.

### Enforces

Purpose rule first; A05 rule 7 pre-proof refusals in order; identity per A01
rule 1. A constant's StoredValue takes the `value_schema` and class the
composing agent declared with it (State 6, decision 5), never its target's, so
a version whose constant targets a missing port, or one whose stored schema
is not the declared one, is still kept and fails its proof (A05 phase 2);
a constant whose value does not fit its own declared schema is a pre-proof
refusal (A05 rule 7).

### Errors

`refused` naming the first pre-proof failure or the purpose rule.

### State impact

`compose_flow_version`, or nothing.

## `public_op:flows.prove_flow_version`

### Owner

`module:flows`. Return a flow version's proof: proven with its highest effect class, or the
first failure.

### Callers

`module:surface`.

### Inputs

A flow version identity.

### Outputs

ProofResult M17: proven with `highest_effect_class`, or the first failure with
phase, node or edge and reason.

### Observable effect

None.

### Enforces

Nine phases in fixed order; reads contract versions and bindings through their
owners; computed on demand, never stored (A05).

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:flows.read_flow_version`

### Owner

`module:flows`. Return one flow version's graph.

### Callers

`module:runs`, `module:effects`, `module:surface`.

### Inputs

A flow version identity.

### Outputs

Its ports, nodes, edges, guards and constants.

### Observable effect

None.

### Enforces

Flow versions are immutable (A01 rule 6).

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:effects.decide_effect_approval`

### Owner

`module:effects`. Record the owner's approval or refusal of a requested approval.

### Callers

`module:runs`.

### Inputs

An approval identity, approve or refuse, the actor (the owner); from `runs`
that the run has not ended.

### Outputs

The approval `approved`, or `refused` with the element's NodeExecution
`refused_by_owner`.

### Observable effect

A refusal makes the run end `refused` when `runs` next derives it.

### Enforces

Only a `requested` approval is decided (A10 rule 3); the run's end is checked
by `runs` first (State 3).

### Errors

`unknown_reference`; `refused` for an approval not `requested`.

### State impact

`decide_approval`.

## `public_op:effects.grant_standing_approval`

### Owner

`module:effects`. Grant a standing approval for a non-destructive node of a flow's active
version.

### Callers

`module:surface`.

### Inputs

A flow, a node, the actor (the owner).

### Outputs

The active StandingGrant — new, or the one already active.

### Observable effect

Later sends of that node in runs of that version need no approval, except a
resend after `not_applied`, which needs a fresh approval whatever grant exists
(A10 rule 1).

### Enforces

Only a node of the active version (`flows.active_flow_version`,
`flows.read_flow_version`) whose binding, read through `bindings.read_binding`,
is not `destructive` (A10 rule 5).

### Errors

`unknown_reference` for a flow that does not exist; `refused` when the flow has
no active version, for a node not in it (A10 rule 5), a function node, or a
`destructive` node.

### State impact

`grant`, or nothing.

## `public_op:effects.operation_element_conclusion`

### Owner

`module:effects`. Return an operation element's conclusion from its records.

### Callers

`module:runs`.

### Inputs

A run, node and element.

### Outputs

Its conclusion: succeeded with outputs; failed with its status, or with
`applied_outputs_unknown` for an attempt resolved applied whose binding has
outputs; waiting with its reason and, for `owner_approval`, the `approval_id`
of the element's `requested` approval, so `runs` builds the run's answer
(Conventions) without reading approval records itself; or not reached when the
element has no NodeExecution yet (A11 rule 3).

### Observable effect

None.

### Enforces

Read from the NodeExecution and EffectAttempt together; the trace is the only
source (A15 rule 7). Trusts the run, its pinned version and the element that
`runs` passes down (State 3) and checks none of them again.

### Errors

None of its own: a run, node or element `runs` names exists; a failed read is
`internal_error`.

### State impact

Read-only.

## `public_op:effects.reach_operation_element`

### Owner

`module:effects`. Reach one operation element: pre-send checks, authority, in-flight record,
send, outcome record.

### Callers

`module:runs`.

### Inputs

The run's id, its pinned flow version, the FlowActivation under which it
started, that it has not ended, the node and element, the element's inputs by
port as references — StoredValues and SpooledFiles, never bytes — the actor.
`effects` reads their bytes through `store.read_value_bytes` to build the
request and names the same references in the approval preview and the
NodeExecution it writes.

### Outputs

The element's conclusion as `operation_element_conclusion` gives it, or that it
waits for approval with the `approval_id` it waits on.

### Observable effect

At most one request leaves the kernel, under covered authority.

### Enforces

Trusts the facts `runs` passes down (State 3) and checks none of them again.
A11 rule 1 order: pre-send checks, authority of A10 rule 1, `in_flight` before
the send, outcome after; idempotency key from key fields (A08 rule 4); approval
choice and `draft-write` authority as closed above.

### Errors

None of its own: pre-send failures and send outcomes are conclusions; any
refusal or error of a module it calls that is not one of those is
`internal_error`.

### State impact

`record_operation_failure`, or `request_approval`, or
`record_attempt_in_flight` then `record_attempt_outcome`; for `read`,
`record_read_outcome`.

## `public_op:effects.recover_in_flight_attempts`

### Owner

`module:effects`. At start, turn every in_flight attempt unknown with its record.

### Callers

`module:surface`.

### Inputs

Nothing: it acts as the kernel.

### Outputs

Done.

### Observable effect

None.

### Enforces

Attempts oldest first in store order. Every `in_flight` attempt becomes
`unknown`, its missing NodeExecution `outcome_unknown` — executed the
attempt's binding, inputs the ones the EffectAttempt names, no outputs — and
its approval `used` when its authority is an approval — a grant or a
FlowActivation changes nothing; the service is not asked (A11 rule 4).

### Errors

`internal_error`; the start stops.

### State impact

`recover_in_flight`.

## `public_op:effects.resolve_unknown_outcome`

### Owner

`module:effects`. Record the owner's resolution of an unknown attempt.

### Callers

`module:runs`.

### Inputs

An attempt, `applied` or `not_applied`, the actor (the owner); from `runs` that
the run has not ended.

### Outputs

The attempt resolved.

### Observable effect

None.

### Enforces

Only an `unknown` attempt; no NodeExecution is written (A11 rule 3).

### Errors

`unknown_reference`; `refused` for an attempt not `unknown`.

### State impact

`resolve_attempt`.

## `public_op:effects.revoke_standing_approval`

### Owner

`module:effects`. Revoke an active standing approval.

### Callers

`module:surface`.

### Inputs

A grant identity, the actor (the owner).

### Outputs

The grant `revoked`.

### Observable effect

Later sends ask again; elements already waiting keep waiting (A10 rule 5).

### Enforces

Any active grant, whether or not its version is still active (M25).

### Errors

`unknown_reference`; `refused` for a grant already revoked.

### State impact

`revoke`.

## `public_op:runs.cancel_run`

### Owner

`module:runs`. End a run cancelled at the owner's request.

### Callers

`module:surface`.

### Inputs

A run, the actor (the owner).

### Outputs

The run's answer, ended `cancelled`.

### Observable effect

Nothing further is sent; the run's spool can no longer be read, and its files
are removed in this request or, when removal fails, at the next start (A18
rule 4).

### Enforces

A14 rule 3; an `unknown` attempt stays `unknown` (A11 rule 5).

### Errors

`unknown_reference`; `refused` for a run that has ended.

### State impact

`record_run_progress`, then `store.remove_run_spool`. A spool that cannot be
removed does not fail the request: the run has ended, and the spool of an ended
run that keeps none is removed at the next start (A18 rule 4).

## `public_op:runs.capture_failed_execution`

### Owner

`module:runs`. Check a failed execution and its run, copy its inputs, and hand the case to
functions.

### Callers

`module:surface`.

### Inputs

A NodeExecution, the contract version named, the actor.

### Outputs

The TrialCase from `functions.add_captured_trial_case`.

### Observable effect

The case is in its corpus.

### Enforces

Record first — a function element that ran in the sandbox (its record names
resources used) and did not succeed — then run and spool, all before an equal
existing case is returned (A15 rule 5, M06); copies nothing itself: passes
the record's inputs down as references, spooled files as their SpooledFiles
(State 3, "Capture").

### Errors

`unknown_reference`; `refused` naming the first failing check, its own or
`functions`'.

### State impact

Copies bytes through `store`; the case through `functions`.

## `public_op:runs.continue_after_approval`

### Owner

`module:runs`. Apply the owner's approval decision and advance the run.

### Callers

`module:surface`.

### Inputs

An approval, approve or refuse, the actor (the owner).

### Outputs

The run's answer as it rests or ended.

### Observable effect

An approved effect is sent in this request (A10 rule 3).

### Enforces

An unknown approval is `unknown_reference` first, the approval read through
`store.read_records` to find its run; then run not ended; then
`effects.decide_effect_approval`; after an approval the element is reached
again and the run advanced (A13 rule 1); after a refusal nothing is reached —
the run is derived `refused` (A10 rule 3).

### Errors

`unknown_reference`; `refused` for an ended run or from `effects`.

### State impact

Through `effects`, then `record_run_progress`.

## `public_op:runs.continue_after_resolution`

### Owner

`module:runs`. Apply the owner's resolution and advance the run.

### Callers

`module:surface`.

### Inputs

An attempt, `applied` or `not_applied`, the actor (the owner).

### Outputs

The run's answer as it rests or ended.

### Observable effect

The run advances as far as it can: elements that become ready run, and their
requests are sent under the authority each has (A13).

### Enforces

An unknown attempt is `unknown_reference` first, the attempt read through
`store.read_records` to find its run; then run not ended; conclusion per A11
rule 3; `not_applied` waits for a fresh approval even under a grant (K-08):
the element is reached again through `effects.reach_operation_element`, which
runs the pre-send checks and, finding no authority, requests that approval for
the request as built now (A11 rule 3).

### Errors

`unknown_reference`; `refused` for an ended run or from `effects`.

### State impact

Through `effects` — the resolution, and after `not_applied` a pre-send failure or `request_approval` — then `record_run_progress`.

## `public_op:runs.read_run`

### Owner

`module:runs`. Return a run's answer from its Run record and its trace.

### Callers

`module:surface`.

### Inputs

A run.

### Outputs

Its answer as Conventions define a run's answer — `approval_id` included for
`owner_approval` — outputs in flow output port name order and waiting points in
(`node_id`, `map_index`) order: status, outputs produced as StoredValue
references — `surface` resolves them for the reader — waiting points, and once
ended the reason per missing output, `skipped_by_guard` or `not_produced` (A13
rule 7).

### Observable effect

None.

### Enforces

Assembled when asked from the Run record — its status, produced outputs and
waiting points as `runs` wrote them — and the trace, which gives the reason
per missing output; reading stores nothing (State 3).

### Errors

`unknown_reference`.

### State impact

Read-only.

## `public_op:runs.recover_running_runs`

### Owner

`module:runs`. At start, remove spools of ended runs that keep none and advance runs left
running.

### Callers

`module:surface`.

### Inputs

Nothing: it acts as the kernel.

### Outputs

Done.

### Observable effect

Spools of ended runs that keep none are removed — one that cannot be removed
stays, unreported, and is removed again at the next start —; runs left
`running` rest or end.

### Enforces

First names spools to remove (A14 rule 4); then derives every run not ended —
`running`, `awaiting_approval`, `pending` — from its records, oldest first,
rewriting a lagging status or waiting point; an operation element whose wait
no longer holds (its approval decided, its attempt resolved) is reached again
through `effects.reach_operation_element`; then advances, as the kernel, every
run left `running` (A14 rule 5).

### Errors

`stop_required` from the sandbox, or `internal_error` from a store change,
stops the start; a spool that cannot be removed does not (see Spool removal in
Conventions).

### State impact

`store.remove_run_spool`; `record_run_progress`.

## `public_op:runs.release_run`

### Owner

`module:runs`. Release a failed run's spool.

### Callers

`module:surface`.

### Inputs

A run, the actor.

### Outputs

The run's answer with `released_by` and `released_at`.

### Observable effect

The run's spool can no longer be read; its files are removed in this request
or, when removal fails, at the next start (A18 rule 4).

### Enforces

Only a `failed` run not yet released (A14 rule 4).

### Errors

`unknown_reference`; `refused` otherwise.

### State impact

`release_run`, then `store.remove_run_spool`. A spool that cannot be removed
does not fail the request: the release is recorded, and the spool of a released
run is removed at the next start (A18 rule 4).

## `public_op:runs.resume_run`

### Owner

`module:runs`. Resend elements waiting on an unreachable service and advance the run.

### Callers

`module:surface`.

### Inputs

A run, the actor.

### Outputs

The run's answer as it rests or ended.

### Observable effect

Elements waiting on an unreachable service are sent again.

### Enforces

Resends in (`node_id`, `map_index`) order before advancing; approval and
outcome waits untouched (A14 rule 2).

### Errors

`unknown_reference`; `refused` when no element waits on `service_unreachable`.

### State impact

`record_resumption` first, then the resends through `effects`, then
`record_run_progress`.

## `public_op:runs.start_run`

### Owner

`module:runs`. Start and pin a run of a flow's active version and advance it.

### Callers

`module:surface`.

### Inputs

A flow, input values by flow input port, the actor.

### Outputs

The run's answer as it rests or ended.

### Observable effect

A run exists and has advanced as far as it can (A13 rule 1).

### Enforces

A12 rule 1 order; pins the version and implementations (A12 rule 2); inputs
take their port's class.

### Errors

`unknown_reference` for a flow that does not exist; `refused` naming the first
failing start check — no active version first — no run created; `stop_required`
from the sandbox.

### State impact

`start_run`; `record_run_progress`.

## `public_op:surface.serve_kernel`

### Owner

`module:surface`. Start the kernel in its fixed order and serve the one MCP entrance.

### Callers

`boundary:host_process`.

### Inputs

The configuration file path, the process's one command-line argument (A17 rule 1).

### Outputs

A serving kernel; or a stopped start: the failing step and its reason on the
host's standard error, without secrets, and a non-zero process exit.

### Observable effect

The MCP entrance opens only after every start step.

### Enforces

Start order of State 3; one request at a time; token, schema, actor table and
masking under A07 for every request (A16, A07 rules 4–5).

### Errors

Any start step's refusal stops the start; `stop_required` ends the process
after the record (State 3).

### State impact

Runs the start; then serves.
