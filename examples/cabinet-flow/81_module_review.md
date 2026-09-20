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
