# Stage 8.1 — assembled module semantic review

## Verdict

All 28 assembled module slices are `PASS`. Each slice was checked against the four Workbench adversarial questions: no materially different observable behavior, trivial implementation, missing accepted refusal/effect/invariant, or source-free behavior remains admissible. Exact packet hashes are recorded in `81_module_review_status.json`.

## Module results

| Module | Contracts | Notes | Structural findings | Semantic result |
|---|---:|---:|---:|---|
| `models` | 0 | 0 | 0 | PASS |
| `system_clock` | 1 | 0 | 0 | PASS |
| `identity` | 9 | 9 | 0 | PASS |
| `installation` | 4 | 4 | 0 | PASS |
| `operational_store` | 3 | 3 | 0 | PASS |
| `access_control` | 4 | 4 | 0 | PASS |
| `semantic_vocabulary` | 8 | 8 | 0 | PASS |
| `slot_registry` | 9 | 9 | 0 | PASS |
| `trial_corpus` | 5 | 5 | 0 | PASS |
| `sandbox_supervisor` | 2 | 2 | 0 | PASS |
| `admission` | 2 | 2 | 0 | PASS |
| `slot_activation` | 4 | 4 | 0 | PASS |
| `manifest_reader` | 3 | 3 | 0 | PASS |
| `operation_bindings` | 5 | 5 | 0 | PASS |
| `flow_proof` | 1 | 1 | 0 | PASS |
| `flow_registry` | 8 | 8 | 0 | PASS |
| `owner_authority` | 9 | 9 | 0 | PASS |
| `service_transport` | 1 | 1 | 0 | PASS |
| `operation_invoker` | 2 | 2 | 0 | PASS |
| `value_store` | 4 | 4 | 0 | PASS |
| `run_spool` | 4 | 4 | 0 | PASS |
| `trace_journal` | 3 | 3 | 0 | PASS |
| `run_executor` | 5 | 5 | 0 | PASS |
| `kernel_surface` | 6 | 6 | 0 | PASS |
| `mcp_gateway` | 1 | 1 | 0 | PASS |
| `http_gateway` | 9 | 1 | 0 | PASS |
| `bootstrap` | 1 | 1 | 0 | PASS |
| `operational_store_persistence` | 30 | 0 | 0 | PASS |

## Deterministic surfaces

Domain and contract-only models, SQLite persistence, the fixed HTTP router, and the system clock are closed by versioned structured IR. The SQLite emitter owns only `operational_store_persistence`; the behavioral UnitOfWork boundary remains in `operational_store`. Tagged union wrappers preserve every closed State 6 variant without untagged unions.

## Value-flow closure delta (2026-09-20)

The slices of 27 modules moved after the value-flow closure
(`python tools/design_value_flow.py examples/cabinet-flow --coverage`: outputs 34 of 34,
inputs 59 of 59, collaborators 55 of 55). Each slice was compared with its state at
`origin/agent/cabinet-flow` (`fdd423d`) and reviewed against the intended change only.

- **Anchors only** — `identity`, `installation`, `manifest_reader`, `bootstrap`,
  `sandbox_supervisor`, `service_transport` (plus one named manifest read), `value_store`,
  `run_spool`, `trace_journal`: line-number references shifted by inserted lines; no contract,
  note or model of the module changed. `system_clock`: the two reviewed flows now name
  `capability:system_clock.monotonic_ns`, as the State 4 plan already required.
- **Named collaborators** — `admission`, `slot_activation`, `trial_corpus`, `slot_registry`,
  `operation_bindings`, `owner_authority`, `flow_registry`, `run_executor`: notes now name the
  exact operations State 5 already assigned to them, and the module imports those contracts
  with their models. No new behaviour: a module that cannot call its collaborator invents
  what it would have returned, which is the variation this closes.
- **Instants** — every required `KernelInstant` of a constructed record names
  `module:system_clock.now` in the note of the function that writes it; `request_trial`
  returns the verdict of `admission.run_trial`; `cancel_run` keeps the stored `created_at`.
- **Lifecycle facts State 5 already promised** — `Flow` and `Slot` gain `retired_by`,
  `retired_at`, `retirement_reason`; `AgentDelegation` and `StandingGrant` gain
  `revocation_reason`; `FlowRun` gains `cancellation_reason`; `VocabularyProposal` gains
  `agent_rationale`. All optional, written once; the SQLite closure carries the columns.
- **A10 engaged** — only the owner accepts a binding version, so
  `OperationBindingVersion.accepted_by` / `accepted_at` are absent on a proposed version and
  written once by `accept_binding_version`; `binding_for_invocation` refuses a version whose
  `accepted_at` is absent. This removes the sentinel instant a generator had to invent.

Adversarial question per module — can two faithful implementations now differ observably? —
answered no for every changed slice: each added sentence removes a choice (which operation,
which clock, which field), none adds one. All 28 modules remain PASS.

## Instants a module handles but does not produce (2026-09-20, after the run stopped at `run_spool`)

Factory run `cabinet_flow-route-b-20260920T140105Z` generated 20 modules and stopped at
`run_spool`: the candidate defined a host-clock helper it never called, because
`SpooledBytes.released_at` exists and no note said where an instant of this module comes from.
The value-flow lens judges required instants of returned records; an optional instant of a
handled record is outside it. Reviewed and closed in the three modules that handle
instant-bearing records without reaching the clock: `run_spool` (`receive_file`,
`release_run_files`), `trace_journal` (`record_node_execution` takes the draft's instants) and
`kernel_surface` (`run_flow`, `inspect` return stored instants). Each note now states the origin
and that no clock is read — a statement of source, not of style. No behaviour changed; slices
moved by the added sentences and by shifted line anchors only. All 28 modules remain PASS.

Open design question, not decided here: `SpooledBytes.released_at` ("when the spool entry was
emptied") has no writer in any contract — `release_run_files` deletes the objects and returns
counts. The field is only ever read as a liveness check.

## ReleaseCeilings brought back to State 1 (2026-09-20)

The closure of `ReleaseCeilings` (M48) carried seven names found nowhere else in the case
(`max_value_bytes`, …, `max_resource_bounds`), while State 1 and `config.release_ceilings` list
seventeen ceilings by name and `service_transport` names `transport_timeout_ms_max`. The Factory
build fell on `ceilings.transport_timeout_ms_max`. The closure now carries exactly the seventeen
State 1 names, each `int`, equal to the `config.release_ceilings` keys. No contract, note or rule
used the seven names. Slices moved only where the model surface is shown; all 28 modules remain PASS.

## Attributes the notes demanded and no model carried (2026-09-20, after the build of run 2)

Factory run on `a5935cce…` generated all 28 modules; the build rejected nine on fields that do not
exist. For the generated modules each was a note demanding an attribute with no carrier. Decided
from the accepted design, not invented:

- **File ports** (M05: "a closed set of accepted media types and a size ceiling"): `SemanticPort`
  carries `accepted_media_types` and `size_ceiling_bytes`, present exactly on a `byte_stream` port
  and never above `config.release_ceilings.run_spool_file_bytes_max`. `value_schema_ref` had no
  model and no resolver behind it. `trial_corpus`, `run_spool` and `validate_contract_ports` name them.
- **Transport timeout** (rule "may enforce a lower manifest/binding-specific timeout"): neither the
  manifest projection nor a binding carries one, so this release has exactly one timeout,
  `config.release_ceilings.transport_timeout_ms_max`. The note no longer asks for a binding-specific value.
- **Preconditions** (A10.5–A10.6): judging a manifest change material requires the stored facts;
  `OperationBindingVersion.preconditions` is copied like the effect class, and `sweep_manifest_drift`
  names the five compared facts.
- **Admission verdict**: `contract_version_ref`, `runtime_revision_ref`, `corpus_digest` — what the
  note of `current_admission` already promised to return.
- **Carrier named in the note**: the effect class is `FlowVersion.highest_effect_class`, read with
  `flow_registry.flow_version`; the pinned runtime is `runtime_revision_ref`; the corpus identity is
  `corpus_digest`; a trial copy reports the draft's target version; a contract version has no status.

Adversarial question per changed slice — can two faithful implementations still differ observably
on these points? No: every sentence names the field or the address. All 28 modules remain PASS.


## Everyday words that are also function names (2026-09-20, reading run 2 before the next export)

`kernel_surface` exports `inspect`, `author` and `activate`. The Factory slicer derives an import
from any whole-word match of another module's function name in positive note text, so twelve
ordinary sentences ("may inspect, run and read traces", "while author, time, rationale …", "the
actor may activate implementations") gave `access_control`, `flow_registry`, `identity`,
`sandbox_supervisor`, `slot_activation`, `slot_registry` and `trial_corpus` an import of
`kernel_surface`, which imports all of them: one cycle of fourteen modules in the accepted local
specs of run 2, and `from cabinet_flow.kernel_surface import author` at the top of the generated
files. The run never reached the link, so nothing reported it.

The twelve sentences now say the same thing without the three words (authoring actor, view records,
put into service, examine). Meaning is unchanged. Measured with the Factory's own rule
(`symbol_reference_requires_import` over `positive_note_reference_text`) on the projected spec:
97 induced edges and one cycle before, 90 edges and no cycle after. The Workbench has no gate for
this; the probe is a candidate lens.

## The path from a domain module to a durable record is undecided (2026-09-20, same reading)

State 3 gives `operational_store` the public boundary `begin_unit_of_work`, `commit_unit_of_work`,
`rollback_unit_of_work` and says domain modules never depend on the repository class. State 5 says
the handle gives "read/write access only to declared kernel record kinds" and that commit validates
"every staged typed record". No contract, note or model says how a record is staged or read:
`UnitOfWorkHandle` is `payload: object`, and the 28 typed methods of
`SqliteOperationalStoreRepository` are reachable from no module.

The accepted code of run 2 shows what two faithful implementations do with that:

- `access_control`, `admission`, `flow_registry`, `operation_bindings`, `owner_authority`,
  `run_executor`, `semantic_vocabulary`, `slot_registry`, `trial_corpus`, `value_store` keep their
  records in module-level dicts and lists (up to twelve per module);
- `operational_store` keeps committed records in a module-level dict and never constructs the
  SQLite repository; `bootstrap` never creates one either;
- `trace_journal` guesses methods on the opaque payload — `get_node_execution`, then
  `read_node_execution`, then `fetch_node_execution`;
- `access_control.resolve_actor` reads `kind`, `principal_id` and `delegation_id` out of the
  presented credential's payload: the caller names its own actor. State 5 already says
  `access_control` resolves channel credentials through `installation.resolve_credential`; the note
  names no such call and says nothing about what the payload of a `ChannelCredentialHandle` is.

Every one of these passed every gate, because nothing names the missing mechanism. Adversarial
question — can two faithful implementations differ observably? Yes: one keeps nothing across a
restart. Twelve modules are AMBIGUITY and Stage 8.1 is open until State 3/5/6 decide the record
path (a typed port over the repository methods, staged through the unit of work) and the notes of
the record-owning functions name its operations. The durable record families also need checking
against M01–M49: the persistence closure has 14 tables.

## The unit of work becomes the typed record port (2026-09-20, boundary 1 of the runtime inventory)

Admission check FA017 (spec-workbench PR #61) named four places where Cabinet Flow hid a runtime
mechanism behind nothing; two of them were the store. This revision closes those two in the form
Cabinet Web already uses — an interface model, a local implementation obligation, a closed
persistence IR — instead of a new mechanism.

- `UnitOfWorkHandle` (`payload: object`) is gone. `begin_unit_of_work` returns
  `OperationalUnitOfWork`, an interface of 107 typed record operations; `SqliteOperationalStoreRepository`
  is its `local` implementation. `CompareAndSetExpectation` and its version unions are gone with it:
  no model carries a version and no decision stood behind the type. Compare-and-set is the owning
  function comparing the expected value with the record it loaded inside the unit, which holds the
  store's one write transaction.
- The closure had 14 tables because an earlier placement reason treated every version and evidence
  kind as "embedded immutable snapshots". State 1 names them durable records of the store
  (`NodeExecution`, `FlowVersion`, `AdmissionVerdict`, …). They are now tables of class `issued`
  (§15.5: append-only, no update, no delete) — 29 tables, and an append-only kind is immutable
  because the port has no update for it. `load`/`upsert` pairs are replaced by what
  `RECORD_ACCESS_MAP_20260920.json` shows the functions need: load by key, find by unique field,
  list by equality filter in a declared order, insert, update of exactly the named fields.
- Two gates corrected the first draft. The data lint refused class `master` for the value-identity
  kinds `OperationBindingVersion` and `SandboxRuntimeRevision`: the binding version is `issued` and
  its acceptance facts need their own record (open, below); the runtime revision is release data
  and leaves the store. The Factory validator refused a list with an empty filter; the four
  whole-table lists became lists by `status` / `axis_id`, and `seed_vocabulary` loads by key.
- Measured against the Factory emitter, not assumed: `generate_repository_draft.py` assembles the
  repository deterministically from this IR (29 tables, 107 methods), and the emitted module passed
  a round trip on a real SQLite file — insert, load equal to the inserted record, duplicate key
  refused, named update, state present after reopening, ordered list.
- `imports.stdlib` gains `import sqlite3`, `imports.third_party` gains the emitter's
  `from pydantic import TypeAdapter`; the codec models of the new tables are declared for
  `operational_store_persistence`.

Still open inside this boundary, so `operational_store` and the record-owning modules stay
AMBIGUITY: the operation that establishes the database location at startup and its caller (arrives
with the installation boundary); the records and fields listed in
`RECORD_PORT_REQUIREMENTS_20260920.md` — the acceptance record of a binding version first; and the
notes of the record-owning functions, which do not yet name the port operations they use.
Slice hashes are refreshed. The six modules whose host mechanism the runtime inventory found
undecided (`installation`, `manifest_reader`, `service_transport`, `sandbox_supervisor`, `run_spool`,
`bootstrap`) are recorded AMBIGUITY as well, so the ledger says what the inventory says: 10 PASS,
18 AMBIGUITY.

## The platform manifest is now a content-addressed external contract (2026-09-20)

The real `platform/manifest/` README and all service records at immutable Factory
revision `b25b523358b3371f81ced7c1ad78dc6f5feb8af3` were inspected and captured in
`PLATFORM_MANIFEST_EXTERNAL_CONTRACT_20260920.md`. A31 and
`rules.platform_manifest_contract` now fix the record path, exact-byte digest,
legacy field shapes and vocabularies, same-path ancestor history lookup and the
fail-closed interpretation of fields the source leaves informal.

The three manifest-reader contracts and notes now agree: idempotency is opaque
`string | null` until operation binding proves an exact typed-port mapping;
`note` is optional and is not the owner's purpose; instances provide only class,
optional HTTP base URL and header names; credentials remain installation-owned.
The content-addressed evidence gate is closed and required by
`70_manifest_reader_closure.json`. This removes the runtime-inventory boundary-3
ambiguity, so `manifest_reader` advances to PASS. Transport, sandbox and
value-byte/spool host mechanisms remain outside this review.

## The credential stops being an opaque carrier; the HTTP edge takes the emitter's form (2026-09-20)

The two remaining FA017 blocks were `CredentialHandle` and `ChannelCredentialHandle`, both
`payload: object`. Behind them the generated `resolve_actor` read `kind`, `principal_id` and
`delegation_id` out of the payload — the caller named its own actor — because no text said how a
presented credential is verified or which throttle key a failed attempt has.

- **A29** decides it: the presented text is `<credential_binding_ref>.<secret>`; the installation
  gives every binding one purpose of the closed `rules.credential_purposes`; `access_control`
  resolves the named binding for the arriving channel, owner purpose first, and compares in constant
  time; the owner binding resolves to the one active owner, an agent binding to the one active
  delegation of that binding and channel; throttle state exists only for a binding the installation
  resolved; a malformed text and an unknown binding write nothing. Trace and witness recorded.
- The credential is a `str` that travels only as a function argument or result, as in Cabinet Web:
  `resolve_actor(channel, presented_credential: str)`, `resolve_credential(...) -> str`,
  `McpRequestEnvelope.credential: str`. Both handle models, `HttpRequestContext` and
  `HttpRequestEnvelope` leave the closure.
- The note of `resolve_actor` now names every call it makes: `installation.resolve_credential`, the
  unit of work, `load_authentication_throttle_state` / `upsert_authentication_throttle_state`,
  `list_owner_principal_by_status`, `list_agent_delegation_by_credential_binding_ref_and_channel`,
  `system_clock.now`, `hmac.compare_digest`, and the A27 delay and block read from `rules`.
- HTTP edge (build finding of run 2): handlers are `(request: Request, body: <DTO>)`, the extractor
  is `(request: Request) -> str`, the delegate argument is `body`, `imports.third_party` declares
  `FastAPI, Request, Response`. Probed against the Factory router emitter in a scratch folder: six
  routes assembled deterministically, `resolve_actor('http_api', extract_http_credential(request))`
  and `activate(actor, body)` — the string now meets a `str` parameter.

FA017 passes. `access_control` stays AMBIGUITY until `issue_delegation`, `revoke_delegation` and
`authorize_action` name their port operations; `installation` stays AMBIGUITY until the protected
configuration has an external contract (boundary 2).

## A30 is decided and has no carrier yet (2026-09-20)

The owner chose: a kernel started on a store restored from a copy serves reading and analysis and
applies no effect until the owner confirms the services were reconciled. A30 records that together
with where the store lives, who opens it and who establishes the owner record. Assembly and the
witness gate stay green with A30 in place although no contract carries it — a decision tagged
`workbench:notes` is witnessed by the existence of notes, not by a note that names it. So the owed
surface is written here, and the modules it touches stay AMBIGUITY until it exists:

- State 1: `StoreContinuity` (the counter, whether effects are open, who confirmed and when) as a
  durable kernel record with a table and port operations.
- `installation`: the external contract of the protected configuration (data directory, owner
  identity and name, manifest pin, selected instances, credential bindings with purpose and secret
  location), one loading operation called by `start_kernel`, and the host copy of the counter —
  read at start, written before a send.
- `operational_store`: the one opening operation (directory, schema, write-ahead journal, the
  comparison of rule 6) and its result; `begin_unit_of_work` refuses before it.
- `bootstrap.start_kernel`: load the installation, open the store, establish the owner, report
  `restored` in `KernelReadiness`.
- `operation_invoker.invoke_operation`: advance the counter in the unit that records the in-flight
  attempt, write the host copy before the send, refuse a node above `read` on a restored store.
- `kernel_surface.owner_decide` and `owner_authority`: the owner-only decision that ends the
  restored state, with the owner's statement.
- `value_store`: value bytes in the content-addressed area of the data directory
  (`source_byte_store_backend` is the available emitter), metadata in the database.

## A30, first part: the installation is read, the store is opened, the owner exists (2026-09-20)

- State 1 **M50 StoreContinuity** — the effect counter, whether effects are open, the detection
  instant of a restored store and the owner's confirmation — with a table and five port operations.
- `installation.load_installation` reads the operator-written protected configuration once. Its
  closed format lives in `rules.installation_configuration`, key names by role; the note names the
  library calls (`Path.read_text`, `json.loads`, `os.stat`) and reads no environment variable.
- `operational_store.open_store` is the only function that creates or prepares the database: data
  directory, value area, schema, write-ahead journal, and the A30 rule 6 comparison that returns
  new / continuous / restored. `begin_unit_of_work` is refused before it.
- `access_control.establish_owner` writes the one OwnerPrincipal when the store holds none; until now
  nothing in the design created it.
- New module **`store_continuity`** owns the host copy of the counter (`open_continuity`,
  `record_host_continuity_counter`). It was first placed in `installation`; the State 6 depth gate
  refused that — eight public functions of eight — and the split follows the mechanism: recognizing a
  store put back from an older copy is not configuration reading.
- `start_kernel` composes them in order and reports `store_continuity` in `KernelReadiness`; a
  restored store is a successful start.

Three refusals of the Factory validator shaped the data: a `schema_version` key under `rules` is
reserved, a key name containing `secret` is refused, and a note may not repeat a literal that lives
in `rules` — so the configuration key names are distinct from model field names and the note points
at their addresses.

Still owed by A30: the counter advance and the restored-store refusal in
`operation_invoker.invoke_operation`, the owner decision that ends a restored state
(`kernel_surface.owner_decide`, `owner_authority`, `store_continuity`), and value bytes in the
content-addressed area. Ledger: 29 modules, 10 PASS, 19 AMBIGUITY.

## A30, second part, and the records the notes were missing (2026-09-20)

PR #62 wired 62 record-owning notes to the port and recorded 17 points where a note needs a record,
a field or an operation that did not exist. This revision decides the ones that are model shape.

- **M51 EffectAttempt** — the in-flight effect attempt was an untyped string inside
  `FlowRun.in_flight_effect_attempts`. It is a record now: identity is run, node, map index and
  attempt number joined, status `in_flight -> concluded`, written before the send.
- **M52 BindingLifecycleEvent** — append-only evidence of `accepted`, `suspended`, `reissued`,
  `retired` with actor, statement, manifest digest and instant. It carries the acceptance record, the
  drift-sweep records and the retirement facts of a binding, so `OperationBinding` needs no new
  field and `OperationBindingVersion` stays immutable.
- Retirement actor, instant and reason on `SemanticAxis`, `SemanticTerm`, `SemanticRelation`, as
  `Slot` and `Flow` already had; their `update_*_status` port operations became `update_*_retirement`.
- `EffectApproval` carries what `request_approval` is given: flow version, mapped elements, file
  preview digests, the owner statement and the request instant; the note names the source of each.
- `NodeExecution.contract_version_ref` for slot evidence; revisions can be listed by `meaning` for
  the duplicate search; `authorization_for_effect` receives the map index and attempt number it
  needs to name the attempt it consumes.
- **A30 rules 5, 7, 8** — `store_continuity.advance_effect_counter` advances the counter inside the
  caller's unit or answers that effects are closed; `invoke_operation` records the EffectAttempt in
  that same unit, writes the host counter after commit and before the send, and on a restored store
  returns `operation_refused` / `refused_by_restored_store` without sending;
  `store_continuity.confirm_continuity` is the owner-only decision, routed from `owner_decide`.

Not decided here and still open: value bytes, code bytes of an implementation, the retention
reference and removal of expired content — all one boundary (6), and the available byte-store
emitter has no removal; the node-execution identity is stated as the same joined key as the attempt
and still has to reach the note of `record_node_execution`. The remaining notes are briefed in
`TASK_RECORD_NOTES_SECOND_BATCH.md`. Ledger unchanged in kind: 29 modules, 10 PASS, 19 AMBIGUITY.

## An operation that shares its name with a field or a parameter (2026-09-21, after the run stopped at `models`)

Route B run `cabinet_flow-route-b-20260920T212152Z` on spec `abaca3c4…` stopped at the first module:
`models` was rejected with `missing required import: owner_statement from cabinet_flow.owner_authority`.
The cause is the class recorded above under "Everyday words that are also function names", reached
from the other side. `owner_statement` was both the public operation of `owner_authority` and a field
of `FlowActivation`, `EffectApproval`, `StandingGrant` and `StoreContinuity`. The record-port note
`OperationalUnitOfWork.update_store_continuity_confirmation` has to list the fields it updates, the
Factory slicer matched the whole word, and the deterministic `models` module was told to import a
domain operation. The sentence cannot be rewritten without the word: the word is the field.

Slicing every module of that spec with the Factory's own `build_local_spec` found the same cause twice
more, through contract parameters rather than notes:

- `store_continuity.confirm_continuity(owner, owner_statement: str)` made `store_continuity` import
  `owner_authority.owner_statement`;
- the parameter `manifest_revision: ManifestRevisionRef` of `binding_for_invocation`,
  `sweep_manifest_drift`, `manifest_operation`, `operation_facts_changed` and `service_instance` made
  `operation_bindings` and `manifest_reader` import `installation.manifest_revision`.

In `flow_registry.activate_flow_version` and `operation_bindings.accept_binding_version` the import was
intended, and the parameter of the same name would have shadowed the imported function inside the very
body that must call it.

The fields and parameters keep their names: State 1, A11 rule 3 and the persistence closure own them.
The two operations are renamed in the words their own design already uses — A11 rule 4 "the statement
is generated by the kernel", and the installation note "the revision … pinned for the running kernel":

- `owner_authority.owner_statement` -> `owner_authority.generate_owner_statement`;
- `installation.manifest_revision` -> `installation.pinned_manifest_revision`.

Propagated from State 3 through the flow and API plans, exposure, State 6 contracts, notes and declared
imports. No model, rule, signature, note sentence or flow step changes otherwise.

Measured with the Factory's own tools on the projected spec: `build_local_spec` slices 29 of 29 modules;
`models` has no internal import; no module imports a function whose name is one of its own contract
parameters; induced edges 112 -> 109, cycles 0 -> 0. Factory validator (FA005) and Spec Inspector
(FA015) accept the spec.

Review carry-over. Sixteen module slices changed hash. Each was rebuilt at the reviewed revision
(`7ae4ee9`, where it reproduces the ledger hash) and at this one; substituting the two old names back
into the new slice gives the reviewed slice byte for byte in eleven modules, and equal up to the order
of keys and list items — moved only because the names sort differently — in `bootstrap`,
`flow_registry`, `installation`, `operation_bindings` and `owner_authority`. The PASS verdicts are
therefore carried over and only the hashes are refreshed. Ledger: 29 modules, 29 PASS.

Left open, same class, not failing today: `manifest_reader.service_instance` and
`slot_activation.serving_activation` are also field names (`NodeExecution`, `EffectApproval`,
`EffectAttempt`; `ContractHealthView`). Every module that imports them today names the operation on
purpose, so the imports are correct; the first record-port note that lists one of those fields would
repeat this stop. The Workbench still has no gate for the class: "a callable name equals a model field
or a contract parameter name" is a candidate lens next to the induced-import probe.

## Rule values reach generated code as imported constants, never as addresses (2026-09-21, after the run stopped at `installation`)

Route B run `cabinet_flow-route-b-20260921T183252Z` on spec `bba2c648…` passed `models`, `system_clock`
and `identity` and stopped at `installation` before any model call: `DataInModelContextError`, the
slice carried `rules.credential_purposes` and `rules.installation_configuration`. The Factory slicer
dereferences a note's `= rules.x` into the local spec, and the data/code seam (SPEC_STANDARD §15.9)
refuses to build a prompt that contains a value. Asking the same Factory rule about every slice gave
the whole size at once: nine modules, seven rule namespaces and `config.persistence`.

A second, quieter form of the same gap was found while reading the notes: an address written in
backticks without `=` (`rules.authentication_throttle.block_seconds`, `rules.disclosure.classes[0]`,
`rules.retry_backoff.timed_wait_reasons[1]`) is not dereferenced at all. No seam refuses it, and the
generator receives neither a value nor a symbol — it can only invent the number. Both forms are
closed together.

Shape. The design home of every value stays where A23, A27 and A29–A34 put it: its `rules` address in
`60_data_closure.json`, with its decision trace and, for the manifest contract, its content-addressed
external evidence. None of that changes. `70_data_provider_closure.json` lowers the values generated
code must read into one deterministic module, `data_provider` (State 3), emitted by the Factory's
`python_constant_data_v1`; `lowered_from` names the rules address of each of the 32 constants and the
value must equal the value there. Following the Factory's own literal-leak rule, a consumer that needs
one exact entry gets a scalar constant — the two channel purposes, the three continuity states, the
fourteen configuration key names — rather than a tuple index or a mapping key. The A27 back-off table is
a record table over the contract-only row model `AuthenticationFailureDelayRule`. The A31 contract is one
mapping, and `manifest_operation` names the five entries it reads.

Notes changed in nine consuming modules say "the imported X constant" where they gave an address;
each declares `data_provider` in `imports.module_internal`. `open_store` no longer addresses
`config.persistence`: the schema is applied by the emitted `create_operational_store_schema` and the
note needs no table name.

The three runtime profile identifiers (`rules.host_byte_storage`, `rules.sandbox_runtime`,
`rules.service_transport_runtime`) are one string each naming a profile; generated code has no use
for the string, and the six notes that addressed it already spell the mechanism in full. The address
is removed from those notes and the fact stays in `rules` and in A32–A34.

Review. Fourteen slices changed and `data_provider` is new; all fifteen were read as diffs against
`b2dea58`. Outside the changed note sentences, the declared provider imports, the row model and the
resolved rule values that left the packets, nothing differs. Two points were decided in the reading:

- `resolve_actor` looked the delay up by list position; by row it needed a rule for a count the table
  does not hold. A27 rule 2 gives counts of ten and above to the block and rule 4 says the attempt
  after an elapsed block is evaluated normally, so the note says "no delay when no row has that
  count" and nothing more.
- `load_installation` keeps the parsed content for the other functions of `installation`; the note now
  says they name its keys only through the same imported constants, so a copied key literal is a
  stated violation rather than a guess the literal-leak gate later rejects.

Measured with the Factory's own tools on the projected spec: `build_local_spec` slices 30 of 30
modules; the data/code seam refuses 0 (was 9); no slice contains a lowered value (`900` is absent from
the `access_control` slice, which carries `AUTHENTICATION_BLOCK_SECONDS: int`); the constant-data
emitter assembles `data_provider`. Ledger: 30 modules, 30 PASS.

Left open, met on the way and not decided here:

- `service_transport.send_request` resolves its credential "through `module:installation`" without
  naming `resolve_credential` or the `service_invocation` purpose; no note passes that purpose at all.
- A34 rule 1 says the exact `bwrap` arguments are fixed by `rules.sandbox_runtime`, whose value is a
  profile identifier; the arguments themselves exist only as note prose.
- `config.release_ceilings.*` reaches consumers only because the bare word inside the backticked
  address induces an import of `installation.release_ceilings`. It works and is accidental.
- Nothing in the Workbench compares a lowered constant with its `rules` source, slices a module the way
  the Factory does, or asks the seam; the pre-export probe that does all three is a `tools/*` change.

## One home per value; the release ceilings reach code through the ReleaseCeilings record (2026-09-22, before the third run)

Route B preflight on spec `48c31f7f…` blocked with `affected_data_graph_incomplete`: 25 accumulated addresses
had no module consumer (seven `rules.*` namespaces the data provider had lowered, and eighteen new
`config.persistence.*_table_name` leaves). The Workbench gates merged on 2026-09-22 name the same causes before
any export: `value_in_two_homes` (18, SPEC_STANDARD §15.4), `undereferenced_data_address` (6, §15.3.1) and the
slicer probe FA018 (8 blocks). The shape of the previous entry — the value stays at its `rules` address and
`lowered_from` points at it — is the form §15.4 forbids and the Factory resolver rejects: a leaf has one home.

Shape. The seven namespaces (`credential_purposes`, `installation_configuration`, `platform_manifest_contract`,
`store_continuity`, `host_byte_storage`, `sandbox_runtime`, `service_transport_runtime`) leave
`60_data_closure.json` with their placements; `70_data_provider_closure.json` drops `lowered_from` and its
`source_refs` name the deciding decisions (A03, A23, A26, A27, A29, A30, A31; M48–M50). A32–A34 are not
listed: no constant lowers them — each profile is one identifier, generated code has no use for the string, and
the six notes already spell the mechanism — so the fact stays in the decision text, which now names the profile
identifier instead of the removed address (rule 1 of A31–A34; no normative rule changes). The external-contract
binding moves to `rules.data_provider_backend.constants.PLATFORM_MANIFEST_CONTRACT.value`; the mapping is the
same bytes, so the verified digest is unchanged (`design_external_contracts`: 0 errors). Three leaves of
`rules.authentication_throttle` that the A27 constants already carry (`block_after_failures`, `block_seconds`,
`delay_seconds_by_failure_count_1_to_9`) are removed on the same rule; the gate does not see them because the
scalars are short and the table has another shape, but they are two homes all the same. Its four boolean
leaves stay: no constant carries them.

Two leaves in two homes, decided here. `rules.disclosure.classes` and `rules.retry_backoff.timed_wait_reasons`
are removed from the closure; the scalar constants stay. `DISCLOSURE_CLASSES` is added as an ordered tuple,
because `derive_output_class` takes "the maximum class" and A03 fixes the order
`open < business_confidential < personal_data`, yet nothing gave the generator that order; `value_store` imports
it. `timed_wait_reasons` has no consumer beyond `OUTCOME_UNKNOWN_WAIT_REASON`; the closed set stays in A28. The
remaining leaves of `rules.disclosure` and `rules.retry_backoff`, like `retention`, `kernel_time`, `authority`,
`sandbox` and `service_targets`, are unchanged and still have no consumer — a design record, not this change.

Release ceilings. The assignment proposed the config path: `config.release_ceilings` read by
`installation.release_ceilings` through `= config.release_ceilings.<leaf>`. The Factory's seam
(`tools/data_code_seam.py`) classifies every `config` leaf except persistence table names as product data, so
such a note would stop the prompt at `installation` exactly as run 18 did; the case has no `runtime_settings`
module (§6.11); and A26/M48 fix the ceilings per kernel release, not per environment. That is row two of
§15.3.1 — a threshold — so the seventeen values are `RELEASE_CEILING_*` constants (`positive_integer`, checked
equal to the M48 list) and `config.release_ceilings` is gone. `installation.release_ceilings` builds the
`ReleaseCeilings` record field by field from them and states the A26 consistency it checks. The six consumers
(`resolve_actor`, `receive_file`, `send_request`, `validate_contract_ports`, `confirm_continuity`,
`add_trial_case`) name "the `<field>` field of the ReleaseCeilings returned by
`module:installation.release_ceilings`" where they carried a backticked address, and declare
`installation.release_ceilings` and the `ReleaseCeilings` model in `imports.module_internal` (the Spec Inspector
requires the model, SI-0001–SI-0006). A26 rule 2 has bootstrap inject the same record; that wiring is bootstrap's
note and does not change.

Table names. `open_store` names the thirty-two `= config.persistence.<table>_table_name` leaves that
`create_operational_store_schema` creates — exactly the `table_name_ref` rows of the persistence closure; a
reference to the whole `config.persistence` key is refused by the seam. The probe no longer reports
`changed_data_without_consumer` for `config.persistence`, and no leaf is left unread, so none is removed.

Review. Seventeen slices changed against `683b270` (the branch was merged with `main` at `921e5e0` first; no
slice hash changed by that merge). Seven changed mechanically — `admission`, `bootstrap`, `manifest_reader`,
`operation_bindings`, `operation_invoker`, `run_executor`, `sandbox_supervisor`: only the reworded rule 1 of
A31–A34, the line shift that follows, and the binding address; substituting the old wording back gives the
reviewed decision text byte for byte. Their verdicts are carried and the hashes refreshed. Ten were read as
diffs against `683b270` with the four protocol questions:

- `data_provider`: eighteen new symbols; a deterministic emitter, no behaviour; the seventeen values equal
  M48 and the tuple equals the A03 order (checked programmatically). PASS.
- `installation`: `release_ceilings` names every field with its constant; a stub returning zeros violates
  positivity, a record built from anything else violates "and nothing else"; the two consistency checks make
  the existing "internally consistent" clause checkable (A26 rules 4 and 6). PASS.
- `access_control`, `run_spool`, `service_transport`, `slot_registry`, `store_continuity`, `trial_corpus`: one
  sentence each; the ceiling now has a source and a declared dependency, every other sentence is unchanged;
  the record's model and contract enter the slice. PASS.
- `operational_store`: `open_store` lists exactly the persistence closure's tables; nothing else changes.
  PASS.
- `value_store`: `derive_output_class` takes its order from the tuple. PASS.

Measured on the projected spec: assembly 14/14 (including the Factory validator); `design_stage6_data --lint` 0
findings (was 18); `design_notes --gate` 0 blocks (was 6); `design_lint --state 2` clean; Factory slicer probe
30 of 30 modules, 290 induced imports examined, 30 slices at the seam, 122 changed data addresses asked, 0
findings (was 8). Ledger: 30 modules, 30 PASS.

Left open, unchanged from the previous entry: `send_request` does not name `resolve_credential` or the
`service_invocation` purpose; A34 speaks of exact `bwrap` arguments that exist only as note prose;
`SpooledBytes.released_at` has no writer. New: ten `rules` namespaces remain design records without a consumer
(the owner's question 3b in the parity memo); `advance_run` spells the A28 delays in prose.
