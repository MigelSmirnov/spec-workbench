# Record port requirements — Cabinet Flow, 2026-09-20

Evidence document for boundary 1 of `RUNTIME_BOUNDARY_INVENTORY_20260920.md`. It condenses
`RECORD_ACCESS_MAP_20260920.json` (82 functions of 17 modules read against notes, contracts, State 1
and State 5; every field name checked against `models[].fields`; 266 undecided points recorded per
function in the map). It is what the State 3/5/6 revision of the store boundary is written from.

## Decisions already taken for the boundary (technical form)

1. The unit of work is the typed record port: an interface model implemented locally by the emitted
   `SqliteOperationalStoreRepository`. Domain modules depend on the interface, never on the class.
2. The only process state of `operational_store` is the database location set by one opening
   operation. `begin_unit_of_work` opens its own connection and an immediate transaction; commit and
   rollback close it. Reads go the same way as writes.
3. Compare-and-set is the owning function comparing the expected value on the record it loaded
   inside that exclusive unit. `CompareAndSetExpectation(record_family, record_id, expected_version)`
   has no carrier — no model has a version — and no decision behind it; it leaves the contract.

## What the port must offer

The existing closure has 14 tables and 28 methods: `load_X` by primary key and `upsert_X`. The
functions need five operation kinds the emitter already knows (`get_by_key`, `get_unique`,
`list_by`, `insert`, `update_fields`) and three it does not decide yet (below).

| Record | Loads | Lists | Writes |
|---|---|---|---|
| SemanticAxis / Term / Relation | by id | all (empty-registry probe) | insert; update current revision; update status on expected status |
| SemanticAxisRevision / TermRevision / RelationRevision | by id | by entity; by content for the duplicate search; relations by (source, target[, kind]) | insert only |
| VocabularyProposal | by id | — | insert; decide on expected status |
| Slot | by id | — | insert; retire on expected status |
| SlotContractVersion | by id | by slot, ordered by version number | insert only |
| Implementation | by id | by contract version | insert only |
| TrialCase | by id | by contract version [and status] | insert; withdraw on expected status |
| TrialExecution | — | — | insert only |
| AdmissionVerdict | — | by (contract version, implementation), latest | insert only |
| SlotActivation | — | by contract version, latest; by (contract version, implementation) | insert, guarded by the previous activation |
| OperationBinding | by id | by status; by (service, capability, channel) | insert; update status / current version on expected value |
| OperationBindingVersion | by id | by binding | insert; write-once acceptance facts |
| Flow | by id; by name | — | insert; retire on expected status |
| FlowVersion | by id | by flow | insert only |
| FlowProof | by id | — | insert only |
| FlowActivation | by id | by flow version | insert, guarded by the previous activation |
| FlowRun | by id | by status set | insert; update status, waiting, in-flight attempts, outputs, end |
| NodeExecution | by id; by (run, node, map index, attempt) | by run (paged); by (run, node); by executed ref; by grant ref | insert only |
| OutcomeReconciliation | — | by node execution | insert only |
| EffectApproval | by id | by run; by (status, run, service instance), paged | insert; decide on expected status; consume attempts |
| StandingGrant | by id | by (flow version, node, binding version, status); by (status, flow version) | insert if no active grant for the triple; revoke on expected status |
| AgentDelegation | by id | by (credential binding, channel, status) | insert; revoke on expected status |
| AuthenticationThrottleState | by (credential binding, channel) | — | upsert |
| OwnerPrincipal | by id; the single record | — | **nothing writes it** |
| StoredValue (metadata) | by digest | by retention class | insert once; delete on expiry |
| SpooledBytes | by (run, content digest) | by run | insert; delete by run — outside the store under A20.1 |

Not yet decidable from the emitter's closed form: a filter on a set of values (`status IN …`), a
paged list with a cursor, a guarded insert ("no active record for this key exists") and a delete.

## Undecided design the access map exposed

Each line is a place where a note obliges a function to keep or find something and no model, field
or operation carries it. They are State 1/State 6 decisions, not storage detail, and they are what
made the generator invent module-level dicts with side tables (`_APPROVAL_META`,
`_GRANT_EXECUTION_COUNTS`, `_VERSION_STATUS`, `_ACCEPTANCE_RECORDS`).

**Records that do not exist**
- the in-flight effect attempt `invoke_operation` must record before a send — today an untyped
  string inside `FlowRun.in_flight_effect_attempts`, rewritten on a row the executor also rewrites;
- the retention reference `put_value` appends and `expire_values` evaluates — `retention_class` and
  `held_until` sit on the immutable `StoredValue`;
- the acceptance record of a binding version, and the suspension / reissue records of the drift sweep;
- the code object of an `Implementation` (only `code_ref` exists) and the content bytes of a value;
- the descriptor of a spooled file that must survive release; `SpooledBytes.released_at` has no writer;
- the installation record; nothing inserts `OwnerPrincipal` or writes its `status`, though suspending
  the owner is an A21 owner-only action.

**Facts with no field**
- retirement actor, time and reason on `SemanticAxis`, `SemanticTerm`, `SemanticRelation` and
  `OperationBinding` (their notes require replay of the first retirement);
- `EffectApproval`: flow version, map index, file preview, owner statement, creation instant;
- `NodeExecution`: slot or contract version (the only bridge for `slot_evidence` is
  `Implementation.contract_version_ref` → `executed_ref`), spooled-file descriptors;
- `FlowActivation`: the flow it belongs to; `TrialCase`: origin of a copied case;
- a version or revision counter on any compare-and-set record.

**Identity recipes not stated**
- vocabulary revisions (no `identify_*_revision`, no list of identity fields);
- `proof_id` (equivalent proof vs. "same identity, different content" conflict);
- `identify_binding_version` excludes `binding_id`, so two bindings of one operation share a version id;
- who mints `node_execution_id` and `reconciliation_id`.

**Uniqueness and serialization not declared**
- one active grant per (flow version, node, binding version); one active delegation per
  (credential binding, channel); (slot, version number); `Flow.name`;
- the heads of the two append-only activation chains: "latest" is an instant with no tie-break and
  there is nothing for a guard to target;
- `retire_flow` against a concurrent activation insert.

**Reads with no accessor**
- `composition_view` needs lists of bindings, slots, contract versions and vocabulary revisions and
  names no call; `contract_health` needs a verdict by id; a pinned `SlotActivation` cannot be read by
  id; `withdraw_trial_case` needs "ever contributed to an admitted verdict" from admission's records;
  `resolve_actor` has no way from presented material to a `credential_binding_ref`, and the throttle
  key of an unmatched credential is undefined.

## Order of work inside the boundary

1. State 1/6: the missing records and fields above, one owning module at a time, each with its State 1
   fact first (PR #60 methodology) and the `carriers` lens after.
2. Persistence closure: tables for every durable kind, methods from the table above, declared
   uniqueness; settle the four operation kinds against the SQLite emitter (Factory side, separate
   tools branch if the emitter must grow).
3. State 3/5/6: the store boundary revision, the interface, `implementation_obligations`, the
   opening operation and its call from `start_kernel`.
4. State 7: every record-owning note names the port operations it uses; the value-flow lenses and
   the import-cycle probe run before export.
