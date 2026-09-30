# State 1 — Cabinet Kernel models

## Status

Draft of 2026-09-29. Models are derived from the decisions K-01 to K-17 and the
primary actions of State 0. Every model and every fact names who reads it; a fact
nobody reads is not carried. This state names product meaning, identity, facts,
lifecycle and persistence; types, optionality and the complete field lists belong
to the State 6 model closure.

Groups: functions M01–M09, services M10–M11, flows M12–M18, runs M19–M23,
authority M24–M26, principals and installation M27–M28.

Not carried over from `examples/cabinet-flow`, because State 0 removed their
reason: the semantic vocabulary (axes, terms, relations, revisions, proposals),
agent delegations and authentication throttling, store continuity, automatic
outcome reconciliation, binding drift history, copying and withdrawing trial
cases, disclosure ceilings and per-reader redaction.

Closed value sets named here (statuses, kinds, classes, reasons) are product
facts; each becomes one release constant when a later state first reads it.

Every content-derived identity and digest in this kernel is the lowercase hex
SHA-256 of the canonical JSON of the model's meaning facts — never of who created
it or when. Canonical JSON is the JSON Canonicalization Scheme of RFC 8785 (JCS):
keys sorted, no insignificant whitespace, UTF-8, its number and string forms, no
non-finite numbers (State 2, A01). The
idempotency key of an effect (M26) uses the same rule.

## Model M01 — Port

### Meaning

One typed input or output position of a contract version, an operation binding
or a flow version. Read by the flow proof (K-06, K-07, K-14), by edge validation
at run time (K-07) and by the sandbox and the operation invoker to shape what
they pass.

Candidate fields:

- `name`: unique within its owner and direction;
- `direction`: `input` or `output`;
- `value_schema`: the schema a value on this port must satisfy, written in the
  subset of JSON Schema the kernel supports; an edge requires both ports to carry
  the same schema, the same carriage and, for files, the same media type (K-06);
- `carriage`: `value` or `file`;
- `media_type`: present exactly on a `file` port — the one media type it carries (K-06);
- `cardinality`: `one` or `many` — `many` is what a map runs over (K-07);
- `disclosure_class`: `open`, `business_confidential` or `personal_data`, ordered
  in that sequence from lowest to highest — on a node's input the highest class it
  accepts; on a flow input the exact class the kernel gives every value arriving
  there, since a caller declares none; on a binding output the class the service returns. A function
  output port carries no class and it is not part of the contract version's
  identity (K-14): the proof takes it as the highest class
  that can reach the function's inputs, and a run as the highest class the
  execution actually received; a function with no inputs yields `open`. A flow
  output port carries no class either: its value keeps the class it arrived
  with.

### Identity

value

### Identity evidence

Substitution: two ports with equal facts are interchangeable within the same
owner. Continuity: a port has no life apart from its immutable owner; a changed
port is a new version of the owner.

### Source of truth

The contract version, binding or flow version that declares it.

### Lifecycle candidate

None; immutable with its owner.

### Persistence candidate

Durable as part of its owner.

### Open questions

None.

## Model M02 — Slot

### Meaning

The named place a function occupies, which keeps its name while its contract
versions and implementations change. Read by the agent for repair (K-12: one slot,
its current implementation and its recent evidence) and by inspection. A slot's
current contract version is the one issued last; its current implementation is
that version's current activation.

Candidate fields:

- `slot_id`: a stable name the creating agent chooses; unique in the kernel, and a
  name already taken is refused;
- `purpose`: plain words for the owner and the agent, fixed when the slot is
  created;
- `created_by`, `created_at`.

### Identity

entity

### Identity evidence

Substitution: two slots with the same purpose are still different places; flows
and repairs address one of them. Continuity: the slot stays the same while new
contract versions and implementations are issued for it.

### Source of truth

The kernel's store; created when an agent with the author right issues the first
contract version under a new slot name — there is no separate create action.

### Lifecycle candidate

Created; no retirement in this kernel.

### Persistence candidate

Durable.

### Open questions

None.

## Model M03 — ContractVersion

### Meaning

The immutable declaration of what one version of a slot's function takes and
returns. Pinned by flow nodes and activations (K-04); read by trial, admission,
the sandbox and the proof.

Candidate fields:

- `contract_version_id`: derived by the kernel from `slot_id`, `inputs`, `outputs`
  and `resource_bounds` (K-04);
- `slot_id`;
- `inputs`, `outputs`: Ports (M01);
- `resource_bounds`: ResourceBounds (M04);
- `issued_by`, `issued_at`.

### Identity

value

### Identity evidence

Substitution: equal content yields the same version. Continuity: none; a change is
another version, so a flow pinned to a version never changes meaning.

### Source of truth

Issued by the kernel on an agent's request.

### Lifecycle candidate

None; immutable after issue.

### Persistence candidate

Durable.

### Open questions

None.

## Model M04 — ResourceBounds

### Meaning

The limits one function execution runs under (K-05). Read by the sandbox.

Candidate fields:

- `wall_time_ms`, `memory_bytes`, `output_bytes`, `process_count`: each at most
  the release ceiling of the same name.

### Identity

value

### Identity evidence

Substitution: equal limits are interchangeable. Continuity: none.

### Source of truth

The contract version; a bound above the release ceiling is refused, never
clamped (State 2, A02).

### Lifecycle candidate

None.

### Persistence candidate

Durable as part of its contract version.

### Open questions

None.

## Model M05 — Implementation

### Meaning

Immutable Python code for one contract version (K-04, State 0 question 4). Read
by trial, admission and the sandbox; shown to the agent repairing its slot.

Candidate fields:

- `implementation_id`: derived from `contract_version_id` and `code`, so equal
  code for another contract version is another implementation;
- `contract_version_id`;
- `code`: the Python source;
- `submitted_by`, `submitted_at`.

### Identity

value

### Identity evidence

Substitution: equal code for the same contract version is the same
implementation. Continuity: none; changed code is another implementation.

### Source of truth

The kernel's store, from an agent's submission.

### Lifecycle candidate

None; implementations are never deleted, so rollback can select an earlier one.

### Persistence candidate

Durable, including the code.

### Open questions

None.

## Model M06 — TrialCase

### Meaning

One input set, with its expected output when one is known, that every
implementation of a contract version must pass (K-05). Read by trial and
admission.

Candidate fields:

- `trial_case_id`: derived from `contract_version_id`, `inputs` and
  `expected_outputs` — not from its origin or who added it; a case equal in those
  facts to an existing one is that case, and the existing origin stays;
- `contract_version_id`;
- `inputs`: StoredValues (M21) by input port;
- `expected_outputs`: StoredValues by output port, absent when only the absence
  of failure is required — always absent for a captured case;
- `origin`: `authored` or `captured`;
- `captured_from`: the NodeExecution (M23) it was captured from, present exactly
  when `origin` is `captured` — only an execution of a function node pinned to the
  same contract version that was executed and did not succeed can be captured
  (K-05) — not a `skipped_by_guard` or `upstream_failed` record, and not one
  whose run was already released, since its spooled files are gone; its inputs,
  including files, become the case's inputs;
- `added_by`, `added_at`.

### Identity

value

### Identity evidence

Substitution: equal content is the same case. Continuity: none; the corpus only
grows.

### Source of truth

The kernel's store.

### Lifecycle candidate

None; never withdrawn in this kernel.

### Persistence candidate

Durable, with the values it names.

### Open questions

None.

## Model M07 — TrialExecution

### Meaning

The evidence of running one implementation on one trial case (K-05). Read by
admission and by the agent repairing the slot.

Candidate fields:

- `trial_execution_id`: minted at random by the kernel;
- `implementation_id`, `trial_case_id`;
- `outcome`: `passed`, `output_mismatch` (outputs valid but not equal to the
  case's expected outputs), `contract_violation`, `sandbox_violation`, `timeout`,
  `resource_exhausted` or `crashed`;
- `outputs`: StoredValues by output port, when produced;
- `resources_used`;
- `executed_at`.

### Identity

value

### Identity evidence

Substitution: an execution is an observation; two runs of the same pair are two
observations, and both are kept. The record is still a value: it is issued once
and never changed.

### Source of truth

The sandbox's observation, recorded by the kernel.

### Lifecycle candidate

None.

### Persistence candidate

Durable.

### Open questions

None.

## Model M08 — AdmissionVerdict

### Meaning

The deterministic verdict on one implementation over the whole active corpus of
its contract version (K-05). Read by activation, which requires an `admitted`
verdict over the current corpus.

Candidate fields:

- `implementation_id`;
- `corpus_digest`: the digest of the corpus the verdict covered;
- `trial_executions`: the TrialExecutions (M07) this admission ran — one per
  active case;
- `verdict`: `admitted` or `refused`;
- `reason`: for `refused`, `empty_corpus`, or the first failing case and its
  outcome;
- `decided_at`.

### Identity

value

### Identity evidence

Substitution: a verdict for the same implementation and corpus is the same
verdict. Continuity: none; a grown corpus needs a new verdict.

### Source of truth

Computed by the kernel when an implementation is submitted, from the
TrialExecutions of that admission: every active
case of the corpus is run again for the implementation at admission time, and the
verdict covers exactly those executions.

### Lifecycle candidate

None.

### Persistence candidate

Durable.

### Open questions

None.

## Model M09 — Activation

### Meaning

The selection of one admitted implementation for one contract version (K-04):
by the kernel on a new admitted verdict, or as a rollback by the owner or an
agent with the author right choosing an earlier implementation admitted over the
current corpus.
Read when a run pins its function nodes. The current activation of a contract
version is the one recorded last; the store has one writer (K-17), so records have
one order.

Candidate fields:

- `contract_version_id`, `implementation_id`;
- `activated_by`, `activated_at`.

### Identity

value

### Identity evidence

Substitution: each activation is one issued selection. Continuity: none; rollback
is another activation.

### Source of truth

The kernel on a new admitted verdict; the owner or an agent with the author right
for a rollback to an earlier admitted implementation.

### Lifecycle candidate

None.

### Persistence candidate

Durable.

### Open questions

None.

## Model M10 — ManifestOperation

### Meaning

The kernel's reading of one operation of one microservice in the platform
manifest (K-03). Read when a binding is proposed and every time the operation is
invoked, to check that the manifest record still has the pinned digest.

Candidate fields:

- `service_id`, `operation_name`;
- `record_digest`: the digest of the operation's own capability entry in the
  service's manifest record, not of the whole record (State 2, A08);
- `channel`: the manifest's channel of the operation; this kernel invokes only
  operations the service exposes over its own HTTP API (`http_api` in the
  manifest's words — not an HTTP surface of the kernel, K-11);
- `effect_class`: `read`, `draft-write`, `state-transition`, `external-effect`
  or `destructive`, ordered in that sequence from lowest to highest (K-08);
- `idempotency_key_fields`: the request fields the manifest names as the key;
- `http_method`, `path`: the declared exposure;
- `base_url`: the manifest's base URL of the one instance the installation
  selects for the service (K-16); the installation chooses the instance, the
  manifest gives its address.

### Identity

value

### Identity evidence

Substitution: equal readings of the same record digest are the same. Continuity:
none; a changed record is another reading. This is an issued snapshot of an
external authority.

### Source of truth

The platform manifest; the kernel mirrors, never writes it.

### Lifecycle candidate

None.

### Persistence candidate

Read on demand; the pinned digest is kept in the binding.

### Open questions

None.

## Model M11 — OperationBinding

### Meaning

The owner-accepted typing of one manifest operation (K-03): its input and output
ports, pinned to one manifest record digest. Read by the flow proof and by the
operation invoker.

Candidate fields:

- `binding_id`: minted at random by the kernel when proposed; two proposals with
  equal content are two bindings;
- `service_id`, `operation_name`, `record_digest`: the pinned capability entry —
  the kernel reads the digest from the manifest when the binding is proposed; the
  proposer names only the service and operation;
- `effect_class`, `idempotency_key_fields`: copied from the manifest record, never
  supplied by the proposer;
- `inputs`, `outputs`: Ports (M01);
- `status`: `proposed` or `accepted`;
- `proposed_by`, `proposed_at`, `accepted_by`, `accepted_at`.

### Identity

entity

### Identity evidence

Substitution: two proposals with the same ports are separate requests the owner
decides separately. Continuity: the same binding moves from proposed to accepted;
its ports and pin never change — a different typing is a new binding. A proposal
the owner does not accept stays proposed and is invocable by nobody.

### Source of truth

The kernel's store; accepted only by the owner.

### Lifecycle candidate

`proposed` → `accepted`, final.

### Persistence candidate

Durable.

### Open questions

None.

## Model M12 — Flow

### Meaning

The named place of a flow whose versions change (K-07). Read to find the flow's
active version when a run starts.

Candidate fields:

- `purpose` of a flow is fixed when the flow is created;
- `flow_id`: a stable name the creating agent chooses; the first flow version
  composed under a new name creates the flow — there is no separate create
  action;
- `purpose`;
- `created_by`, `created_at`.

### Identity

entity

### Identity evidence

Substitution: two flows with the same purpose are still different flows.
Continuity: the flow stays the same while versions are added.

### Source of truth

The kernel's store.

### Lifecycle candidate

Created; no retirement in this kernel.

### Persistence candidate

Durable.

### Open questions

None.

## Model M13 — FlowVersion

### Meaning

One immutable, acyclic graph of a flow (K-07). Read by the proof, by activation
and by every run of it.

Candidate fields:

- `flow_version_id`: derived from `flow_id`, `inputs`, `outputs`, `nodes`, `edges`
  and `constants`;
- `flow_id`;
- `inputs`, `outputs`: the flow's own Ports (M01), always `value` carriage (K-10);
- `nodes`: FlowNodes (M14);
- `edges`: FlowEdges (M15);
- `constants`: FlowConstants (M16);
- `authored_by`, `authored_at`.

### Identity

value

### Identity evidence

Substitution: equal content is the same version — composing it again returns the
existing version and its first author. Continuity: none; a change is another
version.

### Source of truth

The kernel's store, from an agent's composition.

### Lifecycle candidate

None.

### Persistence candidate

Durable.

### Open questions

None.

## Model M14 — FlowNode

### Meaning

One node of a flow version (K-02, K-07). Read by the proof and by the run.

Candidate fields:

- `node_id`: unique within the version;
- `kind`: `function` or `operation`;
- `contract_version_id`: present exactly for a function node;
- `binding_id`: present exactly for an operation node — the proof refuses a
  binding that is not `accepted` (K-03);
- `map_over`: the one input port a `many` edge maps the node over, when mapped. The
  node runs once per element in list order (a `many` value is a list); every other input is given the
  same value for every element; each output collects one result per element in
  that order. A node with two `many` inputs to map is refused by the proof.

### Identity

value

### Identity evidence

Substitution and continuity follow the flow version that holds it.

### Source of truth

Its flow version.

### Lifecycle candidate

None.

### Persistence candidate

Durable within its flow version.

### Open questions

None.

## Model M15 — FlowEdge

### Meaning

One connection from an output port to an input port (K-06, K-07), optionally
enabled only when a declared closed output value is present. Read by the proof
and the run.

Candidate fields:

- `from_node`, `from_port`: a node's output port or a flow input;
- `to_node`, `to_port`: a node's input port or a flow output;
- `guard`: present when the edge is guarded — an output port of the same source
  node whose value schema is a closed set of values, and the one member of that
  set that enables the edge when that port's value equals it; the proof refuses a
  guard on a port without a closed set or with a value outside it. A node whose every incoming edge is disabled by its guard is not
  executed and is recorded `skipped_by_guard`; several enabled guarded edges each
  deliver independently, and the proof refuses two edges that can both deliver to
  one input port, whatever its cardinality (State 2, A05).

### Identity

value

### Identity evidence

Follows its flow version.

### Source of truth

Its flow version.

### Lifecycle candidate

None.

### Persistence candidate

Durable within its flow version.

### Open questions

None.

## Model M16 — FlowConstant

### Meaning

A typed literal pinned in a flow version and delivered to one input port like any
other value (K-04: a function has no configuration). Read by the run.

Candidate fields:

- `to_node`, `to_port`;
- `value`: a StoredValue (M21) of `value` carriage — a constant is never a file —
  whose class the composing agent declares with the constant.

### Identity

value

### Identity evidence

Follows its flow version.

### Source of truth

Its flow version.

### Lifecycle candidate

None.

### Persistence candidate

Durable within its flow version.

### Open questions

None.

## Model M17 — ProofResult

### Meaning

The answer of proving a flow version (K-07): proven, or the first failing edge or
node with the reason. Returned to the agent composing the flow and computed again
at activation; nothing else reads it.

Candidate fields:

- `flow_version_id`;
- `proven`: yes or no;
- `failure`: the first failing edge or node and why, when not proven;
- `highest_effect_class`: of the version's operation nodes, when proven; `read`
  for a version without operation nodes.

### Identity

value

### Identity evidence

Substitution: proving the same version gives the same result. Continuity: none.

### Source of truth

Computed by the kernel.

### Lifecycle candidate

None.

### Persistence candidate

Not persisted; computed on demand.

### Open questions

None.

## Model M18 — FlowActivation

### Meaning

The selection of one proven flow version as the flow's active version (K-08:
the kernel for read-only versions, the owner otherwise). Read when a run starts
and when a standing grant is checked. A flow's active version is the one recorded
last (K-17); a new activation replaces the previous one at once, and runs already
started keep the version they pinned.

Candidate fields:

- `flow_version_id`;
- `highest_effect_class`: from the proof at activation;
- `activated_by`, `activated_at`.

### Identity

value

### Identity evidence

Substitution: each activation is one issued selection. Continuity: none;
switching back is another activation.

### Source of truth

The kernel, after proof and, for effectful versions, the owner.

### Lifecycle candidate

None.

### Persistence candidate

Durable.

### Open questions

None.

## Model M19 — Run

### Meaning

One execution of one active flow version (K-09). Read by the executor as it
advances, by the owner and agents inspecting it, and by resume and cancel.

Candidate fields:

- `run_id`: minted at random by the kernel when the run starts;
- `flow_version_id`: pinned at start;
- `pinned_implementations`: for every function node, the implementation of the
  contract version's current activation at start;
- `inputs`: StoredValues (M21) by flow input port;
- `outputs`: StoredValues by flow output port, as produced;
- `status`: `running`, `awaiting_approval`, `pending`, `succeeded`, `failed`,
  `refused` or `cancelled` — the last four final;
- `cancelled_by`: the owner, present exactly when `cancelled`;
- `waiting`: WaitingPoints (M20) while the run waits; a run may wait at several
  nodes at once — its status is `awaiting_approval` when any of them waits for the
  owner's approval, otherwise `pending`;
- `started_by`, `started_at`, `ended_at`;
- `resumptions`: each resume of the run — who resumed it and when (K-15);
- `released_by`, `released_at`: for a `failed` run, who released its spool and
  when; until then its spooled files stay (K-10).

### Identity

entity

### Identity evidence

Substitution: two runs of the same version with the same inputs are different
runs with their own traces and effects. Continuity: the run stays the same while
it advances, waits and ends.

### Source of truth

The kernel's store.

### Lifecycle candidate

While some nodes wait, independent branches keep running (K-09). The run is
`failed` when no node can run any more and some node failed, `succeeded` when every
node and output concluded successfully.
`running` ↔ `awaiting_approval` | `pending`; → `succeeded` | `failed` | `refused`
(the owner refused an effect) | `cancelled` (the owner cancelled). Resume
retries the nodes waiting on an unreachable service whatever else the run waits
for; a node waiting on an unknown outcome continues only on the owner's
resolution, and one waiting for approval only on the owner's decision (K-09).

### Persistence candidate

Durable.

### Open questions

None.

## Model M20 — WaitingPoint

### Meaning

Why a run is not advancing at one node (K-09). Read by the owner and agents
inspecting the run and by approve, resolve and resume.

Candidate fields:

- `node_id`, `map_index`;
- `reason`: `owner_approval`, `service_unreachable` or `outcome_unknown`.

### Identity

value

### Identity evidence

Substitution: equal facts are the same waiting point. Continuity: none; it exists
while the run waits there.

### Source of truth

The run.

### Lifecycle candidate

None.

### Persistence candidate

Durable within the run.

### Open questions

None.

## Model M21 — StoredValue

### Meaning

One validated value an edge carries, a run takes or returns, or a trial case
holds (K-10), stored by its content. Read by nodes as input, by trace readers and
by trial.

Candidate fields:

- `value_id`: derived from `value_digest`, `value_schema`, `carriage`,
  `media_type` and `disclosure_class`; every other model refers to a StoredValue
  by this id;
- `value_digest`: of the value's canonical bytes;
- `carriage`: `value`, or `file` only for a trial case's file fixture (K-10); a
  file moving during a run is a SpooledFile (M22), never a StoredValue;
- `media_type`: present exactly for a `file`;
- `value_schema`;
- `disclosure_class` (K-14): for a function's output, the class the execution
  actually received; for a flow input, the class its flow input port declares, assigned by the
  kernel — a caller does not declare a class;
- `size_bytes`.

The bytes of equal digest are stored once; a StoredValue is the record of those
bytes with one schema and one class, so the same bytes under another schema or
class are another StoredValue.

### Identity

value

### Identity evidence

Substitution: equal content with equal schema and class is the same value.
Continuity: none.

### Source of truth

The kernel's store. The class of a value is set by exactly one rule: a flow
input's value takes its flow input port's class (the kernel assigns it); a flow
constant's value takes the class the composing agent declares with it; a
function's output takes the highest class its execution received; a binding's
output takes the class the binding declares (K-14).

### Lifecycle candidate

None.

### Persistence candidate

Durable, bytes stored once per digest.

### Open questions

None. Values are kept as long as traces; nothing expires (K-10).

## Model M22 — SpooledFile

### Meaning

One file a node produced during one run, held until the run ends (K-10). Read by
the next node that receives it and by the owner's approval preview.

Candidate fields:

- `run_id`, `producer_node_id`, `map_index`, `attempt_number`, `producer_port`:
  the attempt that produced it, so files of two attempts are two SpooledFiles;
- `content_digest`, `size_bytes`;
- `media_type`: its port's (K-06);
- `disclosure_class`: by the rule of StoredValue (M21) — a function's output the
  highest class its execution received, a binding's output the class the binding
  declares.

### Identity

value

### Identity evidence

Substitution: equal facts are the same spooled file. Continuity: none; it is
released when its run's spool is emptied.

### Source of truth

The kernel's observation while receiving the bytes.

### Lifecycle candidate

None; removed when its run ends, or, for a `failed` run, when the run is released
(K-10).

### Persistence candidate

Temporary, for the life of its run; for a `failed` run, until it is released.

### Open questions

None.

## Model M23 — NodeExecution

### Meaning

The trace record of one concluded attempt at one node, or of a node that was not
executed because its guards disabled it or an upstream node failed (K-09). Read by the owner
and agents reading traces, by repair (K-12) and by capture into a trial corpus.

Candidate fields:

- `run_id`, `node_id`, `map_index`, `attempt_number`;
- `executed`: the implementation or the binding, absent for `skipped_by_guard`
  and `upstream_failed`, which record a node that was not executed;
- `inputs`, `outputs`: references to StoredValues by `value_id` and to
  SpooledFiles by their facts, by port — the record holds no payload;
- `status`: `succeeded`, `contract_violation`, `sandbox_violation`, `timeout`,
  `resource_exhausted`, `crashed`, `refused_by_owner`, `operation_refused` (the
  service refused), `operation_failed`,
  `service_unreachable`, `outcome_unknown`, `skipped_by_guard` or
  `upstream_failed` — `succeeded` only after output validation;
- `failure_detail`: bounded, without secrets, when not succeeded;
- `resources_used`: for a function node;
- `started_at`, `ended_at`.

### Identity

value

### Identity evidence

Substitution: an attempt's record is issued once. Continuity: none; a further
attempt is a further record.

### Source of truth

The kernel's observation.

### Lifecycle candidate

None; immutable.

### Persistence candidate

Durable.

### Open questions

None.

## Model M24 — EffectApproval

### Meaning

The owner's decision on one effect at one node of one run, on the exact input the
owner was shown (K-08). Read by the operation invoker before the effect and by
the owner deciding.

Candidate fields:

- `approval_id`: minted at random by the kernel when the approval is requested;
- `run_id`, `node_id`, `map_index`, `binding_id`;
- `input_digests`: the exact inputs shown;
- `preview`: what the owner saw — operation, target service and the input values;
  agents may read approvals, and an agent receives personal-data values only as
  digest and class (K-14);
- `status`: `requested`, `approved`, `refused` or `used`;
- `requested_at`, `decided_by`, `decided_at`.

### Identity

entity

### Identity evidence

Substitution: two requests for equal inputs at different nodes or runs are
different decisions. Continuity: the same approval moves from requested to
decided to used.

### Source of truth

The owner's decision, recorded by the kernel.

### Lifecycle candidate

`requested` → `approved` | `refused`; `approved` → `used` when the effect is sent.
An approval is used at most once. An approved effect that was never sent, because
the service was unreachable, keeps its approval for the same input when the run is
resumed. When its run ends, an approval that is still `requested` or unused can no
longer be decided or used.

### Persistence candidate

Durable.

### Open questions

None.

## Model M25 — StandingGrant

### Meaning

The owner's standing approval for one node of one flow version (K-08). Read by the
operation invoker instead of asking.

Candidate fields:

- `grant_id`: minted at random by the kernel when granted; at most one active
  grant exists for one node of one flow version;
- `flow_version_id`, `node_id`;
- `status`: `active` or `revoked`;
- `granted_by`, `granted_at`, `revoked_by`, `revoked_at`.

### Identity

entity

### Identity evidence

Substitution: a grant is one owner decision. Continuity: the same grant moves
from active to revoked.

### Source of truth

The owner's decision.

### Lifecycle candidate

`active` → `revoked`. A grant is given only for a node of the flow's active version
and belongs to that exact version: when another version becomes active, the grant
keeps covering the runs pinned to its version and covers no run of another
version. A grant never covers a `destructive` node. A grant stays active when its
version becomes active again. The owner may revoke any active grant, whether or not
its version is still the active one; runs of that version then ask again. Revoking
where no grant is active is refused.

### Persistence candidate

Durable.

### Open questions

None.

## Model M26 — EffectAttempt

### Meaning

The record written before an effect is sent, so that a crash or an unclear answer
leaves a known unknown instead of a silent one (K-08). Read by the run's recovery
after restart and by the owner resolving an unknown outcome.

Candidate fields:

- `run_id`, `node_id`, `map_index`, `attempt_number`: the attempt number counts
  every attempt at that node and element, `not_sent` ones included, so a resend is
  always a new attempt;
- `binding_id`;
- `idempotency_key`: built from the fields the manifest names;
- `authority`: the approval or the grant it used, or for a `draft-write` send
  the flow activation of the run's version (State 2, A10);
- `status`: `in_flight`, `applied`, `not_applied`, `not_sent` or `unknown` —
  `not_sent` when the service could not be reached before anything was sent;
- `recorded_at`, `concluded_at`;
- `resolved_by`: the owner, when an `unknown` was resolved.

### Identity

entity

### Identity evidence

Substitution: two attempts with equal inputs are two sends. Continuity: the same
attempt moves from in flight to its outcome.

### Source of truth

The kernel's store.

### Lifecycle candidate

`in_flight` → `applied` | `not_applied` | `not_sent` | `unknown`; `unknown` →
`applied` | `not_applied` by the owner. A `not_sent` attempt leaves its approval
unused (M24), so a resume sends a new attempt under it. Sending again after `not_applied` is a new attempt
under a fresh approval, never under a standing approval (K-08).

### Persistence candidate

Durable.

### Open questions

None.

## Model M27 — Actor

### Meaning

Who did something (K-15). Carried by every record that names a creator, decider
or starter; read to authorize owner-only actions and to tell the owner's actions
from an agent's.

Candidate fields:

- `kind`: `owner`, `agent` or `kernel` — `kernel` for what the kernel does on its
  own (admission, activation on conforming evidence, activation of a proven
  read-only flow);
- `agent_name`: for an agent, the name its token has in the installation; names
  are unique in an installation, and a configuration repeating one is refused at
  start.

### Identity

value

### Identity evidence

Substitution: equal facts name the same actor. Continuity: none within the
kernel; the installation defines the owner and the agent tokens, and `kernel` is
one fixed actor of every installation that holds no token.

### Source of truth

The installation's protected configuration for the owner and the agents; the
`kernel` actor is fixed by the kernel itself.

### Lifecycle candidate

None.

### Persistence candidate

Durable as part of the records that name it.

### Open questions

None.

## Model M28 — Installation

### Meaning

What one installation of the kernel is configured with (K-15, K-16). Read at start
and by the parts that need its facts.

Candidate fields:

- `data_directory`: where the kernel's store lives, read by the store at start;
- `manifest_location`, `manifest_revision`: where the platform manifest is read
  and the repository revision it is read at — read by every manifest reading
  (M10), so a record changes for the kernel only when the owner changes the
  configured revision;
- `service_instances`: one selected instance per service;
- `service_credentials`: references to secrets, never the secrets;
- `owner_token`, `agent_tokens`: each agent token with its name and whether it
  may author.

### Identity

value

### Identity evidence

Substitution: equal configuration is the same installation. Continuity: the
configuration is read at start; the token list is read again whenever it has
changed, so adding or revoking a token takes effect at the agent's next request
(K-15).

### Source of truth

The host's protected configuration file.

### Lifecycle candidate

None.

### Persistence candidate

Read at start; not stored by the kernel.

### Open questions

None.

## Open questions

None for State 1. Value retention was settled by the owner on 2026-09-29 (K-10).

### Carried to later states

Questions the reviews of State 1 raised that change no model fact, identity or
lifecycle; they belong to the state named and must be closed there:

- State 2: the order that makes "the first failing case" of an admission and "the
  first failure" of a proof deterministic — closed by A04 and A05.
- State 2: how several enabled edges delivering to one `many` input combine —
  closed by A05 (they are refused).
- State 2: what "manifest mismatch" is when a binding is proposed and invoked —
  closed by A08.
- State 2: what the trace records for a node whose unknown outcome the owner
  resolved, and how the run continues from it — closed by A11.
- State 2: whether bounds above the release ceilings are clamped or refused
  when a contract is authored — closed by A02 (refused).
- State 2: whether a flow version whose proof failed because a binding was not
  yet accepted can be proven again later — closed by A05 (yes).
- State 2: how NodeExecution and EffectAttempt attempt numbers relate for one
  operation node — closed by A11.
- State 2: the identity of an Activation record activated again; whether
  resubmitting an equal contract or implementation changes the current one —
  closed by A01 and A04.
- State 2: whether every flow output must be produced under every guard outcome
  — closed by A05 and A13 (no; it is reported `skipped_by_guard`).
- State 2: how transport outcomes (HTTP status, timeout, malformed response,
  validation failure) map to NodeExecution statuses — closed by A09.
- State 6: canonical bytes of a value for its digest; the supported JSON Schema
  subset; the path syntax, order and null handling of idempotency-key fields.
