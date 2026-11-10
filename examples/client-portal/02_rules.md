# State 2 — Client Portal rules, invariants and configuration

## Status

Migrated on 2026-11-06 from the former `spec/20_rules.md` (`SOURCE.md`). Each former
rule table R1–R17 is one indexed accepted decision A1–A17 whose `Normative rules` are
the former text verbatim; the former invariant ledger (`spec/invariant_ledger.json`,
kept as evidence) is distributed into each decision's `Formal invariants`; ledger rows
no table carries form A18–A21. A22–A29 carry the policies the accepted Factory spec
added after 2026-07-19, each with its Factory commit; A30 is the configuration; A31 is
the security review; A32 the dependency policy.

OQ-17 (dependencies) and OQ-18 (orderings), raised by this migration, were answered
by the owner decision of 2026-11-06 (current service behaviour accepted; technical
decisions delegated): A32 and A27.

On 2026-11-07 the owner removed the staff email challenges (`00_product.md` R0-23):
A10 states that the portal has none; the challenge rows of A3, A11 and A13, the
challenge settings of A30 and the invariants INV-010, INV-011, INV-012, INV-013 and
INV-016 are removed, and A3/A4 no longer require a verified email to authenticate.

On 2026-11-08 (State 2 rounds 82-91; owner decision of that day on #147: State 2
decides what a witness must show, not what an existing check asserts) A18, A21, A28
and A32 were completed on their substance: INV-027's test covers every write of an
owning record, activation included; INV-050's test recomputes every overview
component; A28 keeps supplied calendar dates as dates and CLK-001 states the one
wall reading, derived expiries and supplied times; A32 names OSV, judges every
distribution installed in the started image, and carries the check's mechanics to
the deploy route and State 8 (code-factory #189).

The former status, kept:

> **Authoring pass State 2. Builds on `00_product.md` and `10_models.md`
> (including the email-gateway revision of 2026-07-18). The invariant ledger is
> `invariant_ledger.json` in this directory; owners are named here, exact
> `owner_function`/landing are filled at States 5–7.**
>
> Decisions made at this state and surfaced explicitly (not silently):
>
> 1. **Sessions use fixed expiry without sliding renewal.** A staff session
>    ends at its TTL and requires re-login; a viewer re-enters through their
>    capability link. Simplest session model for a sole-operator business; a
>    renewal policy would be a new product decision.
> 2. **Self-service password reset requests are allowed** (a consequence of the
>    email-gateway decision): anyone may submit an email address; the response
>    never reveals whether an account exists; a token is issued and delivered
>    only for an existing verified address.
>
>    *Withdrawn by the owner on 2026-11-07 (`00_product.md` R0-23): the portal
>    has no password reset and sends no email.*
> 3. **Config default values below were confirmed by the product owner on
>    2026-07-19.** They remain runtime knobs, not architecture.
>
>    *Narrowed on 2026-11-08 (A30): the confirmed values stay, but the Registry
>    timeout, the session lifetimes and the credential entropy are release
>    constants a deployment cannot change; only the environment values of A30
>    are deployment settings.*

## Classification principles

Since 2026-11-08 (SPEC_STANDARD 15.2, 15.3.1) a value generated code reads
has one of three homes, and the decision that owns it names that home:

- a closed set of variants (statuses, kinds, codes) — an enumeration of
  `models`, named by the model;
- a constant or policy table that is the same in every environment and
  changes only by a product decision (thresholds, names, paths, timeouts,
  lifetimes, transition and capability tables) — a typed constant of the
  deterministic `data_provider`, imported by name;
- a value that depends on the deployment (URLs, origins, hosts, size bounds,
  rate limits) — a row of the start-up table `config.runtime_environment_variables`,
  validated by `runtime_settings` at each call of `load_runtime_settings` (at
  start, by the bootstrap command, by `registry_gateway` at each Registry
  call and by the emitted `binary_storage` at each binary read) and read
  into a field of `RuntimeSettings`; no other module reads the environment
  (A14, A30; owner 2026-11-09: the binary storage rows too, SPEC_STANDARD
  6.11).

The IR a deterministic backend is emitted from (`rules.*_backend` and the
policies such a backend reads) is read only by that backend. Behaviour that
applies the values — a condition that chooses what code does — is prose of
the State 7 notes (SPEC_STANDARD §2). The former split (`config` for
deployment knobs including timeouts and TTLs, `rules` for every closed
table) is withdrawn.

## Invariant ledger overview

`invariant_ledger.json` is the evidence of 2026-07-19 whose rows were
distributed into the decisions (Status above). It keeps wording the owner
withdrew with the email challenges (R0-23): the verified email of INV-001
and INV-014, the challenge tokens of INV-003 and INV-004, and INV-010…INV-013
and INV-016. Owners and expected primary landings:

| ID range | Area | Owning responsibility | Expected landing |
| --- | --- | --- | --- |
| INV-001…INV-015 | IAM: sessions, capabilities, secrets (INV-010…INV-013 and INV-016, the email challenges, removed 2026-11-07, R0-23) | authorization guard; authentication flows; credential storage | notes (+ rules for capability/transition tables; properties where pure) |
| INV-017 | Operator project scope | staff assignment management; authorization guard | notes + database uniqueness constraint |
| INV-018…INV-019 | Staff login identifiers and new passwords | staff identity | rules + notes/properties |
| PLAT-REG-001…007 | Registry platform contract | Registry gateway; project-scoped use cases | rules (status tables) + notes |
| INV-020…INV-029 | Budget, snapshot import/activation, sections | snapshot import; budget management; section linking | notes + properties (idempotency, single-active) |
| INV-030…INV-037 | Expenses, allocations, documents | expense intake; allocation management | notes + properties (sum equality) |
| INV-040…INV-044 | Progress, payments, photos | progress/payment/photo management | notes + properties (formulas, ranges) |
| INV-050…INV-053 | Derivation, money, audit | derived views; audit writer | notes + properties (determinism) |
| INV-054…INV-055 | Project-list ordering | Registry gateway; derived views | properties + determinism |

Every invariant names exactly one owning responsibility; policy data behind
an invariant lives in the rules tables below, not in prose.

## Accepted decision A1 — R1. Capability catalog (closed)

### Normative rules

```text
portal.project.read          portal.budget.read
portal.expense.read          portal.budget.manage
portal.progress.read         portal.expense.manage
portal.payment.read          portal.progress.manage
portal.photo.read            portal.payment.manage
                             portal.photo.manage
portal.access.manage
portal.estimate_snapshot.import
portal.estimate_snapshot.read_import_result
portal.estimate_snapshot.activate
```

### Formal invariants

- INV-002: roles and capabilities are never read from request data; capability sets are static rules per principal type

### Required tests

- INV-002: a check at `_require_capability` and `authorize_access_management`: for every principal kind and role, the capability set decided is exactly the one `CAPABILITY_SET_MEMBERS` gives for its `CapabilitySet` (the administrator's being the operator set together with the administrator additions), over every member of `Capability`; and a request that carries its own role, capability or principal-kind claim (a header, a body field, a query value) changes no decision: an operator presenting an administrator claim is refused access management, and a viewer presenting a manage capability is refused the mutation, each changing nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-002 [witness: verification:authorization_guard_client_portal].

### Consequence

The catalog is the closed enumeration `= models.Capability`, its one home (SPEC_STANDARD 15.2 check 5, 15.4). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): the accepted spec's `rules.capability_catalog` repeated its members and is removed.

## Accepted decision A2 — R2. Principal-type / role capability sets (static, closed)

### Normative rules

| Principal | Capabilities |
| --- | --- |
| viewer (ClientViewer) | all `*.read`, scoped by active `ProjectViewerGrant` |
| operator | all `*.read` + all `*.manage` except `access.manage` + `estimate_snapshot.activate`, scoped by active `StaffProjectAssignment` |
| administrator | operator capability set + `portal.access.manage`; project scope is the current single administrative area |
| estimate_producer (ServicePrincipal) | `estimate_snapshot.import` + `estimate_snapshot.read_import_result`, scoped by `scope_mode`/grants |

Capability sets are read-only rules data; no runtime editing. A role or
capability is never read from request data.

### Formal invariants

- INV-007: viewer capabilities are read-only; a viewer can never mutate portal data or access management

### Required tests

- INV-007: a check at `_require_capability` that the viewer set of `CAPABILITY_SET_MEMBERS` holds only `*.read` members of `Capability` and none of `*.manage`, `portal.access.manage` or the estimate-snapshot import and activation members; and, through the viewer routes, that a viewer session can reach no mutation of portal data and no access-management operation: each such attempt is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-007 [witness: verification:authorization_guard_client_portal].

### Consequence

The sets are data the generated guard reads: the data-provider constant `CAPABILITY_SET_MEMBERS` (SPEC_STANDARD 6.10 version 2), a table keyed by `= models.CapabilitySet` and `= models.Capability` and total over both, in place of `rules.principal_capability_sets`. The administrator set is the operator set together with `administrator_additions`, an operation the notes of `_require_capability` state. Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): values unchanged.

## Accepted decision A3 — R3. Status transition tables

### Normative rules

```text
StaffStatus:      pending_verification → active;  active ↔ suspended;
                  active|suspended → disabled (terminal)
ViewerStatus:     active → revoked (terminal)
PrincipalStatus:  active ↔ disabled
GrantStatus:      active → revoked (terminal)
BudgetVersionStatus: inactive → active → inactive (re-activation allowed
                  while the project is active; ≤1 active per project;
                  each activation sets activated_at/activated_by and clears
                  deactivated_at, each deactivation sets deactivated_at and
                  keeps activated_at/activated_by of the last activation)
```

Transitions outside these tables are rejected.

### Carried changes

The row `Challenges/tokens: issued → consumed | expired | revoked` is removed
with the challenges, and authentication no longer requires a verified email
besides `active` status (owner 2026-11-07, `00_product.md` R0-23). Every path
into `active` records the email as verified (activation, R0-07), so the answer
to every account stays the one the accepted spec gave.

### Formal invariants

- INV-014: a staff account authenticates only in active status; pending_verification cannot log in

### Required tests

- INV-014: a focused test at `authenticate_staff` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-014 [witness: verification:staff_identity_uow_client_portal].

### Consequence

The staff and principal tables, which generated code reads, are the data-provider constants `STAFF_STATUS_TRANSITIONS` and `PRINCIPAL_STATUS_TRANSITIONS` (SPEC_STANDARD 6.10 version 2: keyed by the pair of statuses, total, `allowed`). The viewer, grant and budget-version tables are behaviour the notes of the operations that change those statuses state (SPEC_STANDARD §2), recorded by the Normative rules above; the accepted spec's `rules.status_transitions`, which no module and no deterministic backend read, is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): values unchanged.

## Accepted decision A4 — R4. Authorization guard sequence (policy)

### Normative rules

Every project-scoped operation evaluates, in order: valid unexpired
unrevoked session → principal status `active` → project access (viewer grant / staff assignment semantics / producer
scope) → required capability from R2 → Registry lifecycle policy (R5).
First failure wins; failures are indistinguishable to the caller regarding
account/project existence beyond what their own access already proves.

The sequence is that of the operations on a project's records (State 0,
common authorization rule), with the exceptions State 0 fixes:

- the Registry lifecycle step validates the project with the Registry; an
  unanswered validation fails the operation (A6), the project overview
  included; the overview's own per-part availability (State 1) concerns
  only reads made after the guard passed;
- for a service principal the "valid session" step is its authenticated
  bearer credential (R0-09); it has no session;
- revoking a viewer grant, a staff assignment or a producer grant is access
  management: it requires a valid administrator session, an active
  principal and `portal.access.manage`, and consults neither project access
  nor the Registry, so it succeeds for an archived project and during a
  Registry outage (R0-24);
- reading a snapshot import result requires only the producer's
  authenticated bearer credential and that the record is its own; it
  rechecks neither the producer grant nor the Registry (R0-21).

### Carried changes

The exceptions are those of State 0 R0-09, R0-21 and R0-24 and of the
accepted notes `revoke_viewer_project`, `revoke_staff_project_assignment`,
`revoke_producer_project`, `get_snapshot_import_result` (owner 2026-11-06:
current service behaviour accepted; technical decisions delegated). The
"(and verified email for staff)" of the active-principal step is removed with
the challenges (owner 2026-11-07, A3 "Carried changes").

### Formal invariants

- INV-001: every project-scoped operation passes the guard sequence: valid session, active principal, project access, required capability, Registry lifecycle policy; first failure wins
- INV-004: authentication flows never reveal account or viewer existence; auth failures never expose project data
- INV-017: an operator may access a project only through one active StaffProjectAssignment; revocation blocks the next project-scoped authorization check immediately; current administrators derive project scope from the single administrative area policy
- PLAT-REG-003: a linked mutation succeeds only after server-side typed validation reports the same UUID as active
- PLAT-REG-004: client-supplied Registry context is never authoritative

### Required tests

- INV-001: a focused test at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- INV-004: a focused test at `conceal_authentication_failure` showing the invariant holds; a violating input is refused and changes nothing.
- INV-017: a focused test at `_require_staff_scope` showing the invariant holds; a violating input is refused and changes nothing.
- PLAT-REG-003: a focused test at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- PLAT-REG-004: a focused test at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-001, INV-017, PLAT-REG-003 [witness: verification:authorization_guard_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-004 [witness: verification:staff_identity_uow_client_portal].
- PLAT-REG-004: the Registry linkage check: the guard's request has no field
  for Registry context; an import or request carrying its own status or
  project facts is refused at decoding, before any Registry call, and writes
  nothing; the same project is admitted or refused as the Registry answers
  at that moment [witness: verification:registry_linkage_client_portal].

### Consequence

The sequence is behaviour, not data: an order of steps that chooses what the guard does is prose of the State 7 notes (SPEC_STANDARD §2), stated by the notes of `_authorize_project_operation` and of the operations each flow names. The accepted spec's `rules.project_guard_sequence` recorded the same order; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A5 — R5. Registry status policy

### Normative rules

| Registry state | Portal reads | Portal mutations |
| --- | --- | --- |
| `active` | allowed | allowed (with capability) |
| `archived` | allowed | rejected (`archived_project`) |
| unknown project | rejected | rejected (`unknown_project`) |

The one write an archived project admits: the staff progress read
`project_tracking.list_project_progress` creates the empty manual budget
version when the project has none (State 0 R0-24); no other read creates
a budget version.

Only `active` and `archived` are status literals the portal acts on (State 1
M16). The project guard of A4 reads the validation answer's `exists`
(false → not found) and, for a mutation, its `status` (anything other than
`active` → `archived_project`); the grant and assignment creation
operations of access management (revocation consults no Registry, R0-24)
read `exists` and `is_active` instead (A6, State 1 M17)
and proceed only when both are true: `exists` false is refused as an
unknown project, otherwise `is_active` false as an archived one, each with
its own operation's error (the
table's labels name the refusal, not the error: a new viewer grant answers
it as a Registry boundary failure, a staff assignment or producer grant as
the not-found or archived rejection; Factory code
`application/viewer_access.py`, `application/staff_identity.py`,
`application/service_identity.py`; owner 2026-11-06: current service
behaviour accepted); the
active-project list keeps only references whose status is `active`; a
status outside the two is never treated as active: a mutation is refused
as `archived_project` by the guard, and a read whose project context would
carry such a status is refused as an invalid Registry answer (the error it
answers is that of the accepted `_authorize_project_operation` and its
context model, carried to States 5–6). Mutation guards call `validate`
server-side before every linked write; archival never revokes grants.

### Carried changes

The former "any other value is a `schema_mismatch` boundary failure" is
narrowed to the running service (Factory code `adapters/registry_gateway.py`:
the validation and context decoders accept any status string, the active
list filters on `active`; `application/authorization_guard.py` types the
status into the context). Owner 2026-11-06: current service behaviour
accepted; technical decisions delegated.

### Formal invariants

- PLAT-REG-001: Registry is the only creator and current owner of Registry project_id; the portal never generates one
- PLAT-REG-002: portal identity linkage uses the returned UUID, never display name or address
- PLAT-REG-006: the portal stores no Registry snapshot as current truth; live context is fetched through the gateway; archived context stays readable but grants no mutation permission
- PLAT-REG-007: portal-owned client data (viewer display name) remains independent of Registry customer_ref

### Required tests

- PLAT-REG-001: a focused test at `validate_project_reference` showing the invariant holds; a violating input is refused and changes nothing.
- PLAT-REG-002: the ledger's property at `_validate_reference_identity` showing the invariant holds; a violating input is refused and changes nothing.
- PLAT-REG-006: a focused test at `get_project_context` showing the invariant holds; a violating input is refused and changes nothing.
- PLAT-REG-007: a focused test at `create_viewer` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: PLAT-REG-006 [witness: verification:authorization_guard_client_portal]; PLAT-REG-006 [witness: verification:derived_views_uow_client_portal].
- PLAT-REG-001, PLAT-REG-002, PLAT-REG-007: the Registry linkage check.
  PLAT-REG-001: the production `validate_project_reference`, answered over
  HTTP, refuses a UUID the Registry answers 404 or `exists=false` for an
  administrator, an operator, a viewer and both producer scopes, and in a
  viewer grant, an operator assignment and a producer grant, writing
  nothing; no service code generates a project id, the gateway only reads,
  and every project id the portal stores is one the Registry issued.
  PLAT-REG-002: an answer about another UUID is refused as
  `identity_mismatch` by `validate_project_reference` and
  `get_project_context`; of two projects with one display name and address,
  access to one is never access to the other. PLAT-REG-007: `create_viewer`
  stores the display name as written without asking the Registry, and a
  grant and a Registry read with another `customer_ref` leave it unchanged
  [witness: verification:registry_linkage_client_portal].

### Consequence

The policy is behaviour, not data: which Registry state admits a read or a mutation chooses what the guard does, and is stated as prose by the notes of `_authorize_project_operation`, `_context_from_validation` and the operations that read `registry_status` (SPEC_STANDARD §2); the states are the enumeration `= models.RegistryProjectStatus`. The accepted spec's `rules.registry_status_policy` recorded the same table; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A6 — R6. Registry failure translation (gateway-owned)

### Normative rules

| Condition | `RegistryFailureKind` |
| --- | --- |
| malformed UUID input (not reached: see below) | `invalid_uuid` |
| `exists=false` (read by the caller, A5; not a gateway failure) | `not_found` |
| `is_active=false`, `exists=true` (read by the caller, A5; not a gateway failure) | `archived` |
| request timeout | `timeout` |
| connection/transport error | `transport_error` |
| HTTP 404 answer | `not_found` |
| any other non-success HTTP status | `http_error` |
| undecodable/invalid response body | `schema_mismatch` |
| response UUID ≠ requested UUID | `identity_mismatch` |

No silent fallback to client-supplied context, cache, or fabricated success.

A malformed project identifier never reaches the gateway: request decoding
refuses it (HTTP 422) before any Registry call or endpoint check, and the
gateway takes only typed UUIDs, so the running service never produces
`invalid_uuid` (Factory code: no caller raises it). Every failed Registry
call is answered with exactly one kind of the table and never with a
fallback, decided in the order a call proceeds (the accepted gateway,
`adapters/registry_gateway.py`): an unusable Registry URL is
`transport_error` before any request; while the request is made, an answer
with HTTP 404 is `not_found` and any other non-success status `http_error`,
a timeout is `timeout`, and any other failure to obtain an answer is
`transport_error`; only a success answer's body is decoded, and a body that
does not decode is `schema_mismatch`; only a decoded answer is compared with
the requested project, and a mismatch is `identity_mismatch`. A later stage
is never reached after an earlier one failed, so no failure has two kinds. A decoded validation answer is returned as it is and read by
its caller as A5 says; the two readings of A5 agree, because the Registry
sets `is_active = true` exactly when `status` is `active` (Registry v1
`validate_project_reference`). The portal does not check the fields of an
answer against each other: each caller acts on the field A5 names for it,
whatever the others say (Factory code `application/authorization_guard.py`,
`application/staff_identity.py`, `application/viewer_access.py`). The Registry URL is a required start-up variable of
A30 (owner 2026-11-09): the service does not start without it, and the
gateway takes it from the settings, never from the environment. A Registry
call made while the URL is unusable (not an http or https base URL, or
carrying user information) fails as `transport_error`, as before (Factory
code `adapters/registry_gateway.py` `_registry_url`). Until 2026-11-09 the
service started without the URL and a call made while it was missing failed
as `transport_error` (owner 2026-11-06: current service behaviour accepted);
the owner changed that on 2026-11-09 (`SEMANTIC_DIFF.md`).

### Carried changes

Precedence made exact from the running service (Factory code
`adapters/registry_gateway.py` `validate_project_reference`,
`get_project_context`, `list_active_projects`, `_registry_url`; callers read
`exists`/`is_active`, e.g. `application/staff_identity.py`). Owner
2026-11-06: current service behaviour accepted; technical decisions
delegated.

### Formal invariants

- PLAT-REG-005: Registry failures translate through the closed RegistryFailureKind table; no silent fallback to cached, client-supplied, or fabricated context

### Required tests

- PLAT-REG-005: a focused test of the three gateway operations against a stubbed Registry, one case per member of `RegistryFailureKind` the gateway raises: a request timeout gives `timeout`; a connection failure and an unusable Registry URL give `transport_error`; an HTTP 404 gives `not_found`; any other non-success status gives `http_error`; an undecodable or invalid body gives `schema_mismatch`; a decoded answer for another project gives `identity_mismatch`. Each raises `RegistryBoundaryError` with exactly that kind and returns no value: no cached, client-supplied or fabricated context and no default answer. A malformed identifier is refused at request decoding before any Registry call, so `invalid_uuid` is never raised (above).
- Witnesses, the focused Factory verification checks that assert it: PLAT-REG-005 [witness: verification:derived_views_uow_client_portal]; PLAT-REG-005 [witness: verification:api_transport_financial_policy_registry_gateway_client_portal].

### Consequence

The failure kinds are the closed enumeration `= models.RegistryFailureKind`; each member names the failure it classifies, and the condition that selects a member is behaviour of the gateway's notes (SPEC_STANDARD §2: a condition that chooses what code does is prose, not a table). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): `rules.registry_failure_translation` keyed the members by internal failure labels no code reads and is removed as a second home of the enumeration.

Owner 2026-11-08 (Q11): the Registry v1 wire contract the three decoders of
`registry_gateway` read is fixed exactly — 16 field positions, the nested
`project` of the context answer with `project.project_id`, the validate
answer's `is_active`, and `registry_updated_at` (State 1 M17, table). The
decoders stay model-written: wire decoding is outside SPEC_STANDARD 6.13.
Owner 2026-11-08 (Q12): the active-project list is read from the Registry
path `projects/active` — the data-provider constants `REGISTRY_PROJECTS_PATH`
and `REGISTRY_ACTIVE_SEGMENT` joined — because the plain `projects` path
answers another shape (`ProjectSummary`) that fails strict decoding as soon
as the list is not empty; the gateway still keeps only active references
while decoding. This changes the running service (it requested `projects`).

## Accepted decision A7 — R7. Supported external contract versions

### Normative rules

```text
ocr_supported_contract_versions      = {1}
snapshot_supported_contract_versions = {1}
```

Closed sets; an unsupported version is a typed rejection, never a best-effort
parse.

"At decoding" means the public input decoding boundary of the recognition
contract, owned by `expense_intake`: `decode_recognition_publication` turns an
untrusted payload into a `ConfirmedRecognitionPublication` and refuses a
malformed payload or a `contract_version` outside the one source
`SUPPORTED_OCR_CONTRACT_VERSIONS` with `ExpenseValidationError`; the consumer
`create_expense_from_recognition` checks the version again (owner
2026-11-08, Q09). The consumer also refuses, with `ExpenseValidationError`
before it projects anything and before any write, a publication object that
lacks a field its model declares — one built bypassing validation — by
checking that concrete input shape, never by catching a generic attribute
error (owner 2026-11-08, Q10). The check is a re-validation of the model
with a typed refusal, without attribute probing (owner 2026-11-09; the
mechanism below confirmed by the owner the same day): the consumer validates the publication model again from the field values the
received instance dumps and refuses a failure as `ExpenseValidationError`;
it never reads fields by attribute lookup or the attribute dictionary.
Handing the instance itself to the model's validation would accept it
unchanged, because a model accepts an instance of its own class without
checking it.

A snapshot publication is first authorized by the import route, in A4's
order with A12's scope: a failure of the bearer credential or of the
principal's status, a project the producer may not see (no active grant of
a `granted_projects` producer, A12, or a project the Registry does not
know), a refused capability, or a Registry status other than `active` is
answered with that access error of A4 and is no import attempt: it gets no
`import_id` and records nothing (R0-25; recording it is Q20). An attempt
that passed is rejected with the reason of the first content check that
fails, in this order:
unsupported `contract_version` → `unsupported_contract_version`, currency
other than `EUR` → `currency_mismatch`, an empty `approved_by` →
`incomplete_content`, then each section in publication order — an amount
that is not a valid EUR amount → `invalid_sections`. A missing field never
reaches these checks: request decoding refuses it first (below). One record carries that one reason (R0-25).
A body that lacks a required field or carries one of the wrong type is
refused by request decoding before the bearer credential is checked: it is
not an import attempt, gets no `import_id` and writes no record. Of the
present values, only an empty `approved_by` is incomplete content; every
other present string is accepted as supplied, and the section list is not
refused for being empty or for repeating a `source_section_id` (State 1
M18; Factory code `application/snapshot_import.py`
`_validate_snapshot_publication`).

An expense creation from a confirmed recognition, once the route's project
guard of A4 has passed, is checked by the operation in this order:
recognition status `confirmed`, a supported contract version, the
authorized context's `portal.expense.manage` capability, its active project, a valid positive
`EUR` total, then the allocation instructions (shape, then sum equal to the
total, then each section belonging to the project), then replay by
`recognized_document_id`. Every refusal before the replay check answers
HTTP 422 with an empty body (`rules.http_router_backend.error_policy`), so
which of them failed first is not observable to the caller; a replay with
other content is the conflict of A8 (409).
A correction body with a missing or wrongly typed field (an unknown
allocation target included) is refused by request decoding before the
guard. Once the route's project guard of A4 has passed, an expense
correction checks its total first, then the expense, then the allocation instructions
(non-empty, sum, then each section target) (Factory code `domain/expense_management.py`
`correct_expense`); a refused total or allocation answers 422, an expense
of no or another project 409.

### Carried changes

Order made exact from the running service (Factory code
`application/snapshot_import.py` `import_snapshot`,
`_validate_snapshot_publication`). The former "authorization failure is
recorded as `unknown_project`, `scope_denied` or `archived_project`" is
narrowed to the running route, which refuses access before the import
(Factory code `api/router.py` `publish_snapshot_endpoint`; accepted
`rules.http_router_backend`); the accepted notes of `import_snapshot` that
record such refusals are Q20. Owner 2026-11-06: current service behaviour
accepted; technical decisions delegated.

### Formal invariants

- INV-031: an Expense is created only from a confirmed, complete normalized result with a supported contract version; confidence, provider fields, and raw responses are never persisted

### Required tests

- INV-031: a focused test at `decode_recognition_publication` and `create_expense_from_recognition` showing the invariant holds; a violating input is refused and changes nothing (the projection itself is the emitted `build_expense_intake` since 2026-11-08).
- INV-031: the expense recognition check: an unconfirmed, incomplete,
  unsupported-version or provider-carrying result is refused at decoding, by
  `create_expense_from_recognition` and over HTTP, with every table
  unchanged; the accepted result persists only its business fields, and no
  model or table carries a confidence, provider or raw field
  [witness: verification:expense_recognition_projection_client_portal].

### Consequence

The accepted versions are the data-provider constants `SUPPORTED_SNAPSHOT_CONTRACT_VERSIONS` and `SUPPORTED_OCR_CONTRACT_VERSIONS` (SPEC_STANDARD 6.10, a `record_tuple` of `SupportedContractVersion` rows, because 6.10 has no integer tuple). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): in place of `rules.supported_external_contract_versions`, values unchanged.

## Accepted decision A8 — R8. Idempotency identity table

### Normative rules

| Fact | Identity | Replay behavior |
| --- | --- | --- |
| Expense | `recognized_document_id` + canonical `intake_fingerprint` | same fingerprint → existing Expense/Document; different fingerprint → integrity conflict, nothing changed |
| ProgressPhoto | `intake_id` | a publication whose kept fields (project, section, caption, visibility, `file_ref`, `photo_date`) equal the photo as now stored → return it; otherwise conflict, nothing changed; `intake_source`, never kept, is not compared |
| WorkPayment | `payment_id` (command-supplied UUID) | a registration equal to the stored payment → return it; otherwise conflict, nothing changed |
| ApprovedEstimateSnapshot | `(project_id, estimate_id, estimate_version)` + `content_fingerprint` | same fingerprint → existing snapshot (`idempotent_replay`); different → `integrity_conflict`, no snapshot stored; either changes no business state and is recorded as its own import result and `snapshot.import` audit |

A fingerprint is a deterministic digest of the content it covers, computed
by the portal: a re-publication with an equal fingerprint is an idempotent
replay and one with a different fingerprint an integrity conflict. How the
content is canonicalised and digested is the owning function's
(`_canonical_snapshot_fingerprint`, `_canonical_intake_fingerprint`),
carried as it is in the accepted spec to States 6–7 (owner 2026-11-06:
current service behaviour accepted; technical decisions delegated).

### Formal invariants

- INV-009: at most one active grant per (viewer_id, project_id) and per (service_principal_id, project_id)
- INV-021: re-publication with identical (project, estimate_id, estimate_version) and identical fingerprint is an idempotent replay; a different fingerprint for the same identity is an integrity conflict storing no snapshot; either changes no business state and is recorded as its own import result and `snapshot.import` audit
- INV-030: one recognized_document_id creates at most one Expense and one ExpenseDocument; equal intake_fingerprint replay returns the existing records, while a different fingerprint is an integrity conflict changing nothing
- INV-042: a WorkPayment is idempotent by payment_id and is never a factura or accounting posting; payments total is derived
- INV-043: a ProgressPhoto is idempotent by intake_id; the gallery is chronological; visibility changes never alter financial or progress data

### Required tests

- INV-009: a focused test at `PortalTransaction.commit` showing the invariant holds; a violating input is refused and changes nothing.
- INV-021: a re-publication with an equal fingerprint is classified an idempotent replay of the existing snapshot, which is not stored again, one with a different fingerprint an integrity conflict storing no snapshot; either changes no business state and is recorded as its own import result and `snapshot.import` audit.
- INV-030: a focused test at `create_expense_from_recognition` showing the invariant holds; a violating input is refused and changes nothing.
- INV-042: a focused test at `register_work_payment` showing the invariant holds; a violating input is refused and changes nothing.
- INV-043: a focused test at `publish_progress_photo` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-009 [witness: verification:service_identity_consumer_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-009 [witness: verification:viewer_access_sqlite_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-021 [witness: verification:snapshot_import_sqlite_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-030 [witness: verification:expense_intake_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-042 [witness: verification:project_tracking_audit_writer_sqlite_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-043 [witness: verification:photo_management_uow_client_portal].

### Consequence

The identities are behaviour, not data: which fields make a repeated request the same request is stated as prose by the notes of the operations this decision's tests name (SPEC_STANDARD §2). The accepted spec's `rules.idempotency_identities` recorded the same table; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A9 — R9. Money policy

### Normative rules

- Currency literal: `EUR` only; any other currency at any boundary →
  explicit typed rejection (`currency_mismatch`).
- `Decimal`, 2 fraction digits, `ROUND_HALF_UP` at derivation boundaries;
  stored amounts are already 2-digit exact.
- All amounts gross (IVA included); snapshot `tax_mode` is provenance only.
- Completed work value: `work_planned × completion_percent / 100`, rounded
  half-up to 2 digits per section, summed after rounding. A section without
  a progress record has no completed work value (`None`, never 0) and is
  left out of the sum, as it is left out of overall progress.
- Overall progress: `Σ(work_planned × percent) / Σ(work_planned)` over
  sections of the active version with `work_planned > 0` and a recorded
  progress (a section without a progress record is left out of both sums);
  undefined (shown unavailable) when the denominator is 0.
- Work balance: `completed work value − payments total`; sign selects the
  presentation label (`Completed ahead of payments` / absolute value as
  `Unused advance payment`). A zero balance is `balanced`.

### Carried changes

The zero balance's label is that of the running service (Factory code
`domain/financial_policy.py` `calculate_work_balance`; State 1
`WorkBalanceLabel`); State 0 "Derived values" names it too.

A section without a recorded progress is left out of overall progress, as
in the running service (Factory code `domain/financial_policy.py`
`calculate_overall_progress`). Owner 2026-11-06: current service
behaviour accepted; technical decisions delegated.

The completed work value of a section without a progress record is `None`,
not 0 (owner 2026-11-08: "«Нет данных» не должно выглядеть как ноль" —
missing data must not look like zero). This replaces the reading accepted
with the running service on 2026-11-06, where that value was `Decimal` 0
while its percent was `None`; the two now both say "not recorded". State 1
`BudgetSectionView` and `ProgressSectionView` type it `Decimal | None`. The
running service still returns 0 until the next Route B regenerates
`derived_views` (`spec/HANDOFF.md`).

### Formal invariants

- INV-037: all monetary values are EUR with decimal 2-digit semantics and ROUND_HALF_UP; foreign currency input is rejected explicitly, never converted
- INV-041: completed work value and overall progress follow the R9 formulas; overall progress is unavailable, never guessed, when no planned work cost exists
- INV-044: remaining materials show overspend as negative values, never clamped or hidden; missing data is presented explicitly, never replaced by zero unless zero is confirmed: a section without a progress record reads completion_percent None and completed_work_value None

### Required tests

- INV-037: a check at `validate_eur_amount`, with the values of the imported MONEY_CURRENCY, MONEY_FRACTION_DIGITS and MONEY_ROUNDING constants: an amount in another currency is refused with the typed `currency_mismatch` rejection, never converted, and changes nothing; an accepted amount is returned as a `Decimal` with exactly `MONEY_FRACTION_DIGITS` fraction digits, half-way values rounded half-up away from zero on both signs (0.005 gives 0.01, 0.015 gives 0.02, −0.005 gives −0.01). And, at each operation that accepts an amount, that the stored record carries the amount in that form, read back through the operation's own answer or the record it stored: `create_expense_from_recognition` (the expense total and each allocation amount; the line amounts of `NormalizedRecognitionItem` are validated for decimal shape only and are not stored), `correct_expense` (the total and each allocation amount), `replace_expense_allocations` (each allocation amount), `upsert_manual_section_plan` (its two planned amounts), `register_work_payment` (the amount) and `import_snapshot` (the snapshot's currency, refused when it is not the imported MONEY_CURRENCY constant, and its amounts).
- INV-041: a check at `calculate_completed_work` and `calculate_overall_progress` with fixed sections: for work_planned 100.00 at 33 % and 200.00 at 50 % the completed work values are 33.00 and 100.00 and their sum 133.00; a value that rounds at the half (work_planned 0.10 at 5 % gives 0.005) is 0.01, and two such sections give a total of 0.02, not the 0.01 of rounding the unrounded sum, because each section is rounded before the sum; overall progress is (100.00 × 33 + 200.00 × 50) / 300.00 = 44.33… as the formula gives it; a section without a progress record is left out of both sums and has completed work value `None`; a section with work_planned 0 is left out of overall progress; and when no section has work_planned above 0 with a recorded progress, overall progress is `None` (shown unavailable), never 0.
- INV-044: the ledger's property at `calculate_material_balance` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-037 [witness: verification:project_tracking_audit_writer_sqlite_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-037 [witness: verification:snapshot_import_sqlite_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-041 [witness: verification:derived_views_uow_client_portal].
- INV-044: the budget derivation check:
  `calculate_material_balance` and the budget view show an overspent section
  as a negative remaining, a section without a progress record reads
  completion `None` and completed work value `None`, and a project without a
  budget reads its views as not configured
  [witness: verification:budget_derivation_client_portal].

### Consequence

The currency, the fraction digits and the rounding mode, which generated code reads, are the imported MONEY_CURRENCY constant, the imported MONEY_FRACTION_DIGITS constant and the imported MONEY_ROUNDING constant of `data_provider`; the sign that selects each `WorkBalanceLabel` is the imported WORK_BALANCE_LABEL_SIGNS constant (SPEC_STANDARD 6.10 version 2, keyed by the label, total). The formulas stay behaviour of their notes, recorded by the Normative rules above; the accepted spec's `rules.money_policy`, whose remaining leaves no module and no deterministic backend read, is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): values unchanged.

## Accepted decision A10 — R10. No email challenges (owner 2026-11-07)

### Normative rules

The portal has no staff email challenge: no email verification, no email
change confirmed at a new address, no password-reset token and no security
notification, and it sends no email (`00_product.md` R0-03, R0-23). A staff
account's email is its login identifier only. The administrative recovery
override (R0-20) is the one operation that replaces a login email; it is an
exceptional flow with its own audit action (A13).

### Carried changes

The former R10 (email challenge policy: purpose-bound single-use
`EmailVerificationChallenge`, `PendingEmailChange` and `PasswordResetToken`
with TTLs, a per-account rate limit, delivery as telemetry, three token-free
notices) was deferred in the accepted Factory spec (sha256 `459ac96c…`: the
operations "remain inert while StaffChallengeRepository is deferred") and is
removed by the owner on 2026-11-07: "remove the staff email/password challenge
feature from the spec. There are no human staff; the owner opens portal
sessions himself and an agent works through cabinet_kernel; no e-mails are
ever needed." With it go `rules.email_challenge_policy` and the invariants
INV-010, INV-012, INV-013 and INV-016 (`open_questions.md` Q19, closed).

### Formal invariants

- INV-015: administrative recovery override is an exceptional flow with enhanced audit: one distinct `staff.recovery_override` record naming the account (`entity_id` = its `staff_id`) and the acting administrator, appended atomically with the change, keeping neither email (A13)

### Required tests

- INV-015: a focused test at `perform_recovery_override` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-015 [witness: verification:staff_identity_uow_client_portal].

### Consequence

No value: the invariant is behaviour of `perform_recovery_override` and lands as its note (State 7).

## Accepted decision A11 — R11. Revocation cascade table

### Normative rules

| Revoked object | Immediate effect |
| --- | --- |
| ClientViewer | all viewer sessions invalid; credential unusable; grants untouched (records kept) |
| ViewerAccessCredential | new entries impossible; existing sessions invalid |
| ProjectViewerGrant | that project disappears from the viewer's scope; other grants unaffected |
| StaffProjectAssignment | that project disappears from the staff account's scope; other assignments unaffected |
| StaffAccount suspended/disabled | all staff sessions invalid |
| ServicePrincipal disabled | all its credentials unusable |
| ServiceCredential | that credential unusable; other credentials of the principal unaffected (rotation overlap) |

"Immediate" means every request authenticated after the revocation commits
observes it; no grace period.

### Carried changes

The accepted Factory spec revokes the sessions of a suspended or disabled staff account and sends no security notice; the former "outstanding challenges revoked; security notice sent" and INV-011 (password reset) are removed with the challenges (owner 2026-11-07, A10, `00_product.md` R0-23).

### Formal invariants

- INV-005: a revoked grant, credential, viewer, or session blocks the next authorization check immediately, per the revocation cascade table
- INV-006: a suspended or disabled staff account and a disabled service principal have no valid sessions or usable credentials
- INV-008: at most one non-revoked ViewerAccessCredential per viewer; re-issue revokes the previous credential atomically

### Required tests

- INV-005: a check against the rules table at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- INV-006: a check against the rules table at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- INV-008: a focused test at `issue_viewer_access` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-005 [witness: verification:end_to_end_walkthrough_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-005, INV-006 [witness: verification:authorization_guard_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-006 [witness: verification:staff_identity_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-006 [witness: verification:service_identity_consumer_uow_client_portal].
- INV-008: the viewer credential re-issue check: after each re-issue exactly
  one credential is live, the previous one is revoked by the administrator,
  and neither its secret nor a session it opened is accepted; a re-issue
  failing at its audit append leaves every table unchanged
  [witness: verification:viewer_credential_reissue_client_portal].

### Consequence

The normative policy is the table above: it is the rules table of this decision (the policy data behind INV-005 and INV-006 lives in this document's rules tables, see Status), and the two checks hold the operations to it. The specification has no `rules` namespace for it: no generated code reads the table as data, and SPEC_STANDARD 15.3.1 (edition 2) refuses a `= rules.*` note address outside a backend IR. The State 7 notes of the owning operations (`revoke_viewer`, `revoke_viewer_access`, `revoke_viewer_project`, `revoke_staff_project_assignment`, `change_staff_status`, `change_service_principal_status`, `revoke_service_credential`) state each cascade as behaviour. The accepted spec's `rules.revocation_cascades` is removed (2026-11-07, SOURCE.md).

## Accepted decision A12 — R12. Producer scope rule

### Normative rules

`scope_mode = all_projects` → import allowed for any existing active
project. `scope_mode = granted_projects` → import allowed only with an
active `ProducerProjectGrant` for the target project; otherwise the
project is not visible to the producer: the import route answers the
scoped not-found rejection, exactly as for a project the Registry does not
know, so a producer cannot tell an ungranted project from a missing one.
A refused capability (the producer's source type lacks
`portal.estimate_snapshot.import`) is answered as A4's authorization
rejection. Either refusal records nothing (A7, R0-25, Q20). Scope is
checked before snapshot content validation.

### Carried changes

The former "otherwise `scope_denied`" is narrowed to the accepted spec
(note `_authorize_project_operation`: an absent or inactive grant raises
"the scoped not-found rejection"; Factory code
`application/authorization_guard.py`). The import route runs this check
before the import (`api/router.py` `publish_snapshot_endpoint`), so the
classification of `ScopedNotFoundError` as `unknown_project` and
`AuthorizationRejected` as `scope_denied` in `application/snapshot_import.py`
is reached only if access changed in between (Q20). Owner 2026-11-06: current service behaviour accepted; technical decisions delegated.

### Formal invariants

- INV-029: a producer import is authorized for the target project per scope_mode and grants before content validation

### Required tests

- INV-029: a focused test at `authorize_snapshot_import` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-029 [witness: verification:authorization_guard_client_portal]; INV-029 [witness: verification:service_identity_consumer_uow_client_portal].

### Consequence

The rule is behaviour, not data: which scope admits which project is stated as prose by the notes of `authorize_producer_scope` and `authorize_snapshot_import` (SPEC_STANDARD §2); the scopes are the enumeration `= models.ProducerScopeMode`. The accepted spec's `rules.producer_scope_policy` recorded the same rule; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A13 — R13. Audit action catalog (closed)

### Normative rules

```text
viewer.create viewer.revoke viewer.credential_issue viewer.credential_revoke
grant.create grant.revoke
staff_assignment.create staff_assignment.revoke
staff.create staff.login staff.login_failed staff.logout
staff.sessions_revoke staff.suspend staff.reinstate staff.disable
staff.recovery_override
principal.create principal.disable principal.enable
principal.credential_issue principal.credential_revoke
producer_grant.create producer_grant.revoke
budget.section_plan_edit budget.manual_version_create
snapshot.import snapshot.activate
expense.create expense.correct expense.include expense.exclude
expense.allocate document.update
progress.update payment.register
photo.publish photo.update
```

One audit record per action occurrence; `staff.recovery_override` carries
enhanced detail via its entity reference: its record is the distinct
action `staff.recovery_override` naming the account (`entity_id` = its
`staff_id`) and the acting administrator; neither the replaced nor the
replacement email is kept in any record, and the account's current email
is the only evidence of the change (Factory code
`application/staff_identity.py` `perform_recovery_override`; Owner 2026-11-06: current service behaviour accepted; technical decisions delegated.)
A rejected record of a
significant mutation carries `result = rejected` and a `reason_code`.

The significant mutations are
exactly: `viewer.create viewer.revoke viewer.credential_issue
viewer.credential_revoke grant.create grant.revoke staff_assignment.create
staff_assignment.revoke staff.create staff.suspend staff.reinstate
staff.disable staff.recovery_override principal.create principal.disable principal.enable
principal.credential_issue principal.credential_revoke
producer_grant.create producer_grant.revoke budget.section_plan_edit
budget.manual_version_create snapshot.import snapshot.activate
expense.create expense.correct expense.include expense.exclude
expense.allocate document.update progress.update payment.register
photo.publish photo.update`; every other catalog action is non-significant.

In the running service exactly two actions write a rejected record:
`snapshot.import`, for every classified attempt that is not accepted or a
replay (R0-25: an attempt the import route refuses on access is not
classified and writes nothing, Q20), with `reason_code` equal to its `ImportRejectReason` value
or, for an integrity conflict, `integrity_conflict`; and `staff.login_failed`,
non-significant, with no `reason_code`. Every other refused operation
rolls its transaction back and writes no record. The closed set of
`reason_code` values is therefore the seven `ImportRejectReason` values and
`integrity_conflict`.

### Carried changes

The former sentence "Rejected attempts of significant mutations are
audited" is narrowed to the running service: the accepted
`audit_significant_mutation_actions` and `audit_result_reason_policy` only
constrain the reason of a rejected record that is written (note of
`_validate_audit_intent`); the writers of rejected records are
`import_snapshot` and `authenticate_staff` (Factory code
`application/snapshot_import.py`, `application/staff_identity.py`). Owner
2026-11-06: current service behaviour accepted; technical decisions
delegated.

The six challenge actions `staff.email_verification_issue`,
`staff.email_verified`, `staff.email_change_request`, `staff.email_changed`,
`staff.password_reset_request` and `staff.password_reset_complete`, which no
operation of the accepted service wrote, leave the catalog and the significant
set with the challenges (owner 2026-11-07, A10, `00_product.md` R0-23).

The accepted Factory spec adds two policies beside the catalog (Factory `5677993e`, 2026-07-22): `rules.audit_significant_mutation_actions`, the closed subset of the catalog called significant mutations (listed above; removed from the case 2026-11-07, see Consequence), and `rules.audit_result_reason_policy` (retired 2026-11-09, see Consequence): a success carries no `reason_code`, a rejected significant mutation carries a non-blank one, a rejected non-significant action may carry one.

### Formal invariants

- INV-051: every action in the audit catalog writes exactly one AuditRecord with actor provenance; service actors record key_version
- INV-053: a rejected audit record of a significant mutation carries result=rejected and a closed reason_code

### Required tests

- INV-051: a focused test at `append_audit` showing the invariant holds; a violating input is refused and changes nothing.
- INV-053: a focused test at `append_audit` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-051 [witness: verification:staff_identity_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-053 [witness: verification:snapshot_import_sqlite_uow_client_portal].

### Consequence

The normative catalog and significant subset are the two lists above, the rules tables of this decision; INV-051 and INV-053 are checked against them. In the specification the catalog is the `AuditAction` enumeration (`= models.AuditAction`). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): the significant subset, which `_validate_audit_intent` reads, is the data-provider constant `AUDIT_ACTION_SIGNIFICANCE` (SPEC_STANDARD 6.10 version 2: keyed by the action, total, `significant_mutation`), so an action added without its classification stops the build; the note no longer lists the members. Neither has a `rules` namespace. The accepted spec's `rules.audit_action_catalog` and `rules.audit_significant_mutation_actions` are removed (2026-11-07, SOURCE.md). The result and reason combinations are the sentence on the reason policy above, stated as prose by the notes of `_validate_audit_intent`; the accepted spec's `rules.audit_result_reason_policy`, which no module and no deterministic backend read, is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md).

## Accepted decision A14 — R14. Binary delivery policy

### Normative rules

- A client addresses a binary by portal-owned `document_id` or `photo_id`,
  never by `file_ref`.
- The owning domain module re-checks authenticated project access and
  client-visible eligibility before storage access.
- After authorization, `binary_storage` resolves the stored opaque `file_ref`
  and returns `BinaryPayload`; the API streams its bytes with the declared
  media type. Signed/provider URLs and raw paths are forbidden.
- A missing source object is an explicit unavailable/not-found failure and
  does not mutate the business record or fabricate empty content.
- Content exceeding `binary_max_read_bytes` is rejected before response
  emission. Reading never changes retention state.

### Carried changes

The accepted Factory spec extends `rules.binary_delivery_policy` (Factory `babd5e52`, 2026-08-01; R0-12): the media type is resolved from the leading signature bytes of the stored content against a closed list per object kind (expense document: PDF, JPEG, PNG; progress photo: JPEG, PNG, WebP); an unrecognized or unlisted type is rejected with no octet-stream fallback; the download name is derived from object kind, id and the resolved extension; the response is the exact bytes with exact `Content-Length`, `attachment` for documents and `inline` for photos, `no-store` and `nosniff`. This replaces "streams its bytes with the declared media type" above. The storage read bound is checked to be no larger than the declared response ceiling at start.

### Formal invariants

- INV-034: exactly one ExpenseDocument per Expense regardless of allocation count; the binary stays outside the record

### Required tests

- INV-034: a focused test at `create_expense_from_recognition` (the aggregate is built by the emitted `build_expense_aggregate` since 2026-11-08): an expense created with one allocation and one created with several allocations each has exactly one `ExpenseDocument`, which names the expense; the document record holds the opaque `file_ref` and no binary content; and replacing the expense's allocations leaves that one document unchanged.
- Witnesses, the focused Factory verification checks that assert it: INV-034 [witness: verification:expense_intake_uow_client_portal].

### Consequence

`rules.binary_delivery_policy` (media types and signatures per object kind, download name, disposition) is IR read only by the deterministic `binary_storage` backend, which `binary_storage` is emitted from (`rules.binary_storage_backend`); no model-written module reads it. A model-written owner (`read_expense_document`, `read_progress_photo`) hands `read_binary` an authorized reference and returns the payload it answers, whose media type, download name and disposition the emitted module decided. The two storage variables are rows of the start-up table (A30). The start-up check that the read bound is no larger than the response ceiling is a constraint of that table (`BINARY_MAX_READ_BYTES` less than or equal to `MAX_BINARY_RESPONSE_BYTES`), checked by `runtime_settings` at each `load_runtime_settings`, so a violating deployment does not start; `binary_storage` applies only the read bound, at each read.

## Accepted decision A15 — R15. Deterministic project-list ordering

### Normative rules

- `registry_gateway.list_active_projects` normalizes its otherwise unordered
  typed result by `project_id` ascending so identical Registry facts produce
  identical gateway output.
- `derived_views.list_viewer_projects` orders ProjectListItem by
  `display_name.casefold()` ascending without changing the stored/displayed
  name, then `project_id` ascending as the stable tie.
- Registry is never credited as the source of either order. Pagination remains
  absent for the current few-project operating profile; adding it requires an
  explicit cursor/limit contract rather than truncating silently.

### Formal invariants

- INV-054: list_active_projects returns the same typed Registry facts ordered by project_id ascending regardless of upstream response order
- INV-055: list_viewer_projects returns accessible ProjectListItem values ordered by display_name.casefold() ascending without changing display_name and project_id ascending as the stable tie

### Required tests

- INV-054: the ledger's property at `list_active_projects` showing the invariant holds; a violating input is refused and changes nothing.
- INV-055: a focused test at `_ordered_project_items` showing the invariant holds; a violating input is refused and changes nothing.
- INV-054, INV-055: the Registry linkage check: `list_active_projects`
  returns the active Registry facts unchanged, ordered by `project_id` for a
  shuffled, a reversed and an ascending upstream answer;
  `list_viewer_projects` orders by casefolded display name, then
  `project_id`, display names unchanged
  [witness: verification:registry_linkage_client_portal].

### Consequence

The ordering is behaviour, not data: it is stated as prose by the notes of the functions this decision's tests name (SPEC_STANDARD §2). The accepted spec's `rules.project_list_ordering` recorded the same ordering; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A16 — R16. Staff email and password policy

### Normative rules

- Staff login email is syntax-validated, Unicode-casefolded, and
  stored/compared in that normalized form. No provider-specific dot
  removal, plus-tag removal, or domain rewriting occurs. A supplied address
  that contains whitespace, surrounding whitespace included, is refused,
  never stripped. The exact syntax check and casefolding are those of the
  accepted `_normalize_staff_email`, carried to States 6–7.
- A new password is 12–128 Unicode code points, contains no NUL/control
  characters, and is hashed exactly as supplied. The portal never trims,
  casefolds, or Unicode-normalizes password plaintext. The refused control
  characters are exactly the code points U+0000 to U+001F and U+007F (the
  accepted `_validate_new_password`); every other code point, other Unicode
  control and format characters included, is accepted.
- No character-class composition ritual is required. A future breached-
  password service is a separate explicit boundary, not an implicit network
  call during hashing.
- Password plaintext is accepted only by login, account creation, the
  holder's password change and the bootstrap command (there is no password
  reset, R0-23) and handed immediately to `credential_security`; it never
  enters audit records.

### Carried changes

The former "stripped of surrounding whitespace" is narrowed to the running
service, which refuses it (Factory code `application/staff_identity.py`
`_normalize_staff_email`; the accepted `rules.staff_identity_input_policy`, retired 2026-11-09, see Consequence). Owner 2026-11-06: current service
behaviour accepted; technical decisions delegated.

### Formal invariants

- INV-018: staff login email uniqueness and lookup use the R16 syntax-valid (whitespace refused) Unicode-casefolded form without provider-specific rewriting
- INV-019: new staff passwords satisfy R16 length/control-character policy and are hashed exactly as supplied without trimming or normalization

### Required tests

- INV-018: a check against the rules table at `_normalize_staff_email` showing the invariant holds; a violating input is refused and changes nothing.
- INV-019: a check at `_validate_new_password` and the operations that accept a new password, with the bounds of the data-provider constants `PASSWORD_MIN_CODEPOINTS` and `PASSWORD_MAX_CODEPOINTS`: passwords of one code point below the minimum and one above the maximum are refused and change nothing, the minimum and the maximum are accepted; a password containing any code point from U+0000 to U+001F or U+007F is refused and changes nothing, while one containing U+0080 or U+200B is accepted; a password with surrounding whitespace, a case variant and a password in a non-normalized Unicode form are each accepted and stored as the hash of exactly the supplied string, so that the supplied string verifies and its trimmed, casefolded or normalized variant does not.
- Witnesses, the focused Factory verification checks that assert it: INV-018 [witness: verification:staff_identity_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-019 [witness: verification:credential_security_policy_client_portal].

### Consequence

The password bounds, which generated code reads, are the data-provider constants `PASSWORD_MIN_CODEPOINTS` and `PASSWORD_MAX_CODEPOINTS`; the rest of the policy is behaviour its notes state, recorded by the Normative rules above; the accepted spec's `rules.staff_identity_input_policy`, whose remaining leaves no module and no deterministic backend read, is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): values unchanged.

## Accepted decision A17 — R17. Verification-secret envelope

### Normative rules

- Every portal-issued session/viewer/service plaintext token encodes
  a public record UUID selector plus a random secret generated with configured
  entropy.
- Parsing yields PresentedSecret. The store looks up only by the UUID; the
  owning identity flow must then verify the random secret against that
  record's salted verification hash and all lifecycle conditions.
- A selector alone is never authentication. Unknown selector, malformed
  envelope, wrong secret, wrong purpose, expired/used/revoked record, or
  inactive principal converges on the owning existence-hiding rejection.
- Verification hashes are never queried for equality and never used as
  deterministic lookup keys.

### Formal invariants

- INV-003: passwords, session tokens, viewer access tokens and service credentials are stored only in verification/hash form and never logged

### Required tests

- INV-003: a focused test at `issue_verification_secret` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-003 [witness: verification:credential_security_policy_client_portal]; INV-003 [witness: verification:staff_identity_uow_client_portal].

### Consequence

The envelope is behaviour of the emitted `credential_security` (its backend IR `rules.credential_security_backend`) and of the notes of the operations this decision's tests name (SPEC_STANDARD §2). The accepted spec's `rules.verification_envelope_policy` recorded the same policy; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A18 — Budget and snapshot invariants

### Normative rules

The former ledger rows INV-020…INV-029 that no table of R1–R17 carries. Their policy is the product text of State 0 ("Approved estimate snapshot", "Coexistence and transition") and the models M19–M23; no further table is needed.

### Formal invariants

- INV-020: an accepted ApprovedEstimateSnapshot is immutable; versions are append-only and never overwritten or deleted
- INV-022: import and activation are distinct actions; a producer holds no activation capability and never activates its own import
- INV-023: at most one active BudgetVersion per project; activation atomically deactivates the previous active version
- INV-024: at most one manual BudgetVersion per project; manual section plans are mutable only while the project is active; imported plans are immutable copies of their snapshot
- INV-025: PortalSection identity is stable across versions and renames; automatic linking uses source_key equality only; display-name matching is forbidden
- INV-026: planned budget values never derive from actual expenses; mutable PresuPro estimate state never changes the portal budget outside the snapshot import boundary
- INV-027: budget totals and all financial aggregates are derived at read time, never stored as editable values
- INV-028: a PortalSection referenced by any allocation or progress record is never deleted

### Required tests

- INV-022, INV-023, INV-024, INV-025: the budget management check.
  INV-022: an import activates nothing; a producer cannot activate any
  version, its own import included. INV-023: after an activation exactly
  one version of the project is active and the previous one is inactive,
  both in the same commit; a failed activation leaves the previous active
  version active. INV-024: a second manual version of a project is
  refused; a manual section plan changes only while the project is
  active; an imported plan cannot be changed. INV-025: a section keeps its
  identity across versions and renames; a snapshot section links to an
  existing section only by equal `source_key`, never by display name
  [witness: verification:budget_management_sqlite_uow_client_portal].
- INV-020: the snapshot import check: an accepted snapshot is never
  overwritten or deleted and every accepted version stays readable; a
  re-publication of its identity with the same content is an idempotent
  replay and one with different content a conflict; each leaves the
  snapshot unchanged, changes no business state and is recorded as its
  own import result and `snapshot.import` audit (A12, A13)
  [witness: verification:snapshot_import_sqlite_uow_client_portal].
- INV-026, INV-027, INV-028: the budget derivation check. INV-026: an
  accepted import stores the published planned values and rewrites no budget
  version, plan or expense; a changed re-publication is a conflict that
  changes no snapshot, budget version, plan or expense and is recorded only
  as its import result and audit (A12, A13); expense operations never move a
  plan. INV-027: no table
  stores a value of a derived view (a total or aggregate; an import's
  content fingerprint is not one), reading the views writes nothing, and
  after every write of an owning record (inclusion, allocations, progress,
  payment, plan, budget-version activation) the next read equals a
  recomputation from the stored rows.
  INV-028: no service code deletes or replaces a portal section and no store
  surface removes one; activating a budget version without an allocated
  section is refused and writes nothing, and the activation keeps the
  sections progress references
  [witness: verification:budget_derivation_client_portal].

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7). Data placement 2026-11-08 (SOURCE.md "Data placement"): the audit of an import takes its result and the source of its reason_code from the data-provider constant `IMPORT_OUTCOME_AUDIT`, keyed by `= models.ImportOutcome` and total (SPEC_STANDARD 6.10 version 2), values as `import_snapshot` stated them.

Owner 2026-11-08 (Q05): an imported `SectionPlan` has `updated_by` `None` —
State 1 M23 keeps that field for manual plans — and the author of an imported
version stays on `BudgetVersion.created_by_id`. When an imported budget is
built, and by which operation, remains open (Q11 of `open_questions.md`).

## Accepted decision A19 — Expense and allocation invariants

### Normative rules

The former ledger rows INV-030…INV-037 that no table of R1–R17 carries; product text of State 0 ("Operator management") and the models M28–M30.

### Formal invariants

- INV-032: the sum of an expense's allocations equals its total_amount at every commit point; amount correction and allocation adjustment are one atomic operation
- INV-033: automatic proportional allocation is forbidden; every allocation amount is an explicit operator value
- INV-035: only confirmed expenses with included=true participate in financial totals; excluded expenses remain visible
- INV-036: allocation targets and progress sections belong to the expense's/project's own project; cross-project references are rejected

### Required tests

- INV-032: a focused test at `PortalTransaction.commit` showing the invariant holds; a violating input is refused and changes nothing.
- INV-033: a focused test at `replace_expense_allocations` and `correct_expense` (the new allocations are built by the emitted `build_replacement_allocations` since 2026-11-08) showing the invariant holds; a violating input is refused and changes nothing.
  Witness: `replace_expense_allocations` with the explicit amounts 150.00 to a section and 50.00 to other expenses persists exactly those two allocations, and a replacement of 1.00 against the 200.00 total is refused with `ExpenseValidationError` while the stored row counts stay unchanged; nothing spreads an amount (`verification/client_portal_expense_consumer_support.py`, run by the check) [witness: verification:expense_management_uow_client_portal].
- INV-035: a focused test at `_project_expense_summary` showing the invariant holds; a violating input is refused and changes nothing.
- INV-036: a focused test at `validate_project_section` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-032, INV-036 [witness: verification:expense_intake_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-032, INV-036 [witness: verification:expense_management_uow_client_portal].
- Witnesses, the focused Factory verification checks that assert it: INV-035 [witness: verification:derived_views_uow_client_portal].

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7).

Owner 2026-11-08: every accepted include or exclude of an expense — also one
that leaves `included` as it was — replaces the Expense with `included`,
`updated_at` (the operation's one instant) and `updated_by` (the acting
staff member) (Q01); every accepted metadata update of an expense document
sets the document's `updated_by` to the acting staff member as well as its
`updated_at` (Q02); a re-allocation is a change of the Expense: it replaces
the Expense with new `updated_at` and `updated_by`, and the returned
aggregate holds that replaced Expense with the new allocations (Q03). Q01
and Q03 confirm the running service; Q02 likewise. No amount, provenance or
allocation rule changes.

## Accepted decision A20 — Progress invariant

### Normative rules

The former ledger row INV-040; product text of State 0 ("Operator management") and M32.

### Formal invariants

- INV-040: completion percent is a manual staff value in [0,100]; photographs never set progress

### Required tests

- INV-040: a focused test at `set_section_progress` showing the invariant holds; a violating input is refused and changes nothing.
- INV-040: the progress manual value check: an administrator and an assigned
  operator are admitted to `portal.progress.manage`, a viewer and a producer
  are refused; `set_section_progress` stores 0, 37 and 100 and refuses
  values outside [0, 100] and non-integers with every table unchanged;
  publishing and updating photos leave `section_progress` and the progress
  view unchanged
  [witness: verification:progress_manual_value_client_portal].

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7). Data placement 2026-11-08 (SOURCE.md "Data placement"): the upper bound of a completion percent is the data-provider constant `COMPLETION_PERCENT_MAX`; its lower bound, zero, is the meaning of a percent.

## Accepted decision A21 — Derivation and append-only records

### Normative rules

The former ledger rows INV-050 and INV-052; product text of State 0 ("Derived values", "Audit") and M19, M20, M36.

### Formal invariants

- INV-050: all derived values are deterministic and recomputable from owning records for the same accepted inputs
- INV-052: audit records and import records are append-only; no flow mutates or deletes them

### Required tests

- INV-050: a focused test at `build_project_overview` showing the invariant holds; a violating input is refused and changes nothing.
- INV-052: a focused test at `PortalTransaction.commit` showing the invariant holds; a violating input is refused and changes nothing.
- Witnesses, the focused Factory verification checks that assert it: INV-052 [witness: verification:snapshot_import_sqlite_uow_client_portal].
- INV-050: the budget derivation check: the project overview is equal for
  staff and viewer and on repeated reads, equal records inserted in either
  order (ties of sort order, dates and amounts) derive equal values, and
  every component of the overview (budget, expenses, progress, payments,
  photos) equals a recomputation from the owning records
  [witness: verification:budget_derivation_client_portal].

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7).

Owner 2026-11-08 (Q06): a budget view row exists only for a section the
viewed version plans, so its `has_unresolved_allocations` is always false;
unresolved allocations show only in the view's overall
`unresolved_allocation_count`.

Owner 2026-11-08 (Q07, answered again after the first choice named a field
`PortalSection` does not have): an expense allocation view's
`section_display_name` for a `section` target is the `display_name` of the
`SectionPlan` of that section in the project's active `BudgetVersion`; it is
`None` when the project has no active version or that version has no plan for
the section, and always `None` for an `other_expenses` target. The name is
derived at read time from the active version's plans the expense view already
reads (no stored copy); the State 1 condition "required iff target = section"
is withdrawn. Behaviour change: the running service answers `None` for every
allocation (`spec/SEMANTIC_DIFF.md`).

## Accepted decision A22 — Transaction guard policy (accepted Factory spec, 2026-07-25)

### Normative rules

A use case closes each transaction it opens exactly once. A read path rolls
back once right after its last read, then evaluates and raises; a write path
commits once on success. A guard around the transaction catches every
exception (`BaseException`), rolls back only while the transaction is still
open, and re-raises the original exception unchanged. Open state is tracked by
a local flag of the use case, never probed through the store. The normative
value is `rules.transaction_guard_policy` of the accepted Factory spec,
carried verbatim at assembly (Factory `0baceacc`).

### Formal invariants

- TXN-001: no transaction is rolled back twice, rolled back after a commit,
  or left open.
- TXN-002: a domain error raised inside a guarded transaction reaches the
  caller unchanged, never masked by a persistence error of the closed
  transaction.

### Required tests

- A focused test per use-case module that instruments the store, rejects a
  nested begin and requires exactly one close per call (Factory focused
  checks `*_uow_check`, `0f9ae3ae`, `7eb7ebcc`).
- TXN-001, TXN-002: the transaction guard check
  [witness: verification:transaction_guard_client_portal].
- TXN-001: the staff identity unit-of-work check
  [witness: verification:staff_identity_uow_client_portal].

### Consequence

The guard is behaviour, not data: the notes of every use case state it as prose (SPEC_STANDARD §2), and the transaction itself is the emitted unit of work (`rules.sqlite_unit_of_work_backend`). The accepted spec's `rules.transaction_guard_policy` records the same policy and is carried unchanged. No module reads it and no note names it; its home is the fourth of SPEC_STANDARD 15.3.1, a policy a Factory gate reads: its kind `transaction_policy` is declared in the Factory's `tools/gate_rules_reads.py` (`GATE_RULES_READS`), and the gate checks the generated code against it (owner 2026-11-09).

## Accepted decision A23 — Audit entity id policy (accepted Factory spec, 2026-07-26)

### Normative rules

`AuditIntent.entity_id` is the canonical string form of the audited entity's
identifier, produced by converting the UUID to a string; it is absent only
when the audited entity has no identifier of its own. A UUID object, a
hyphen-stripped, truncated or upper-cased form, or another entity's
identifier is forbidden. Recorded in the accepted spec as `rules.audit_entity_id_policy`
(Factory `0f9ae3ae`; retired 2026-11-09, see Consequence).

### Formal invariants

- Every audit record's `entity_id` equals the canonical string of the audited
  entity's id, or is absent when that entity has none.

### Required tests

- A writer test that rejects a UUID object and a non-canonical string for
  `entity_id`, and a consumer test per audited mutation that reads the record
  back.
- Witnesses, the focused Factory verification checks that assert it: entity_id canonical [witness: verification:staff_identity_uow_client_portal]; entity_id canonical [witness: verification:staff_bootstrap_client_portal].

### Consequence

Which entity an audit names is behaviour of the audit-appending notes, which pass the `AuditEntityKind` member and the entity id to the emitted audit builders of `record_builders` (SPEC_STANDARD §2, §6.13). The accepted spec's `rules.audit_entity_id_policy` recorded the same policy; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A24 — Records are immutable values (accepted Factory spec, 2026-07-26)

### Normative rules

Model instances are frozen. No code assigns to a field of an argument or of a
value read from a repository, and no result travels back to a caller through
a mutated input. A changed value is a new instance built from the old one.
Recorded in the accepted spec as `rules.model_immutability_policy` (Factory `bd561732`).

### Formal invariants

- A value read from a repository is unchanged after any use case that read it.

### Required tests

- A test per revocation cascade that the read record is untouched and the
  replacement carries the change.
- Witnesses, the focused Factory verification checks that assert it: read value unchanged [witness: verification:derived_views_uow_client_portal]; read value unchanged [witness: verification:service_identity_consumer_uow_client_portal].

### Consequence

State 1 models are frozen by the emitted `models`, and new and replaced records are built by the emitted builders below. The accepted spec's `rules.model_immutability_policy` records the same policy and is carried unchanged. No module reads it and no note names it; its home is the fourth of SPEC_STANDARD 15.3.1, a policy a Factory gate reads: its kind `model_policy` is declared in the Factory's `tools/gate_rules_reads.py` (`GATE_RULES_READS`), and the gate checks the generated code against it (owner 2026-11-09).

Owner 2026-11-08: every record a model-written module built from its inputs
is built by an emitted builder of `record_builders`
(`rules.record_construction_backend`, SPEC_STANDARD 6.13): a new record or a
replacement of a read one (`form: replace` keeps every unnamed field of the
base) is constructed only there, the source of each field and the disposal of
each input field are closed IR checked at the State 6 handoff, and a module
given a builder of a model never constructs that model itself. A value
computed by behaviour — a sum, a lookup, a condition, a validated amount, the
operation's one clock reading — is a builder parameter its caller computes.

## Accepted decision A25 — HTTP transport policy (accepted Factory spec, 2026-07-31 to 2026-08-06)

### Normative rules

The public API lives under `/api`, stripped by the deployment proxy. The
service answers only on its trusted hosts (at least one, no wildcard at any
position); CORS is off when its allowlist is empty, and an allowed origin is
never a wildcard. Request bodies and binary responses are bounded by runtime
settings before expensive work; viewer entry attempts are rate limited per
client network identity and route, with bounded memory and a concealed answer.
The identity is the client address of the connection, never a forwarded
header, cookie or secret, kept to its first 128 characters; a connection that
names no client is identified as `unknown`. Addresses that share their first
128 characters, and all connections that name no client, therefore share one
bucket, as in the running service (Factory code `runtime/transport_guard.py`
`_client_bucket_key`; owner 2026-11-06: current service behaviour accepted;
technical decisions delegated). An entry attempt over the limit is refused before any
code verification and creates no session; the limiter's algorithm, its
bound and its answer are those of the accepted transport guard, stated by
the notes of `transport_guard` (recorded in the accepted spec as
`rules.http_transport_policy.limits.viewer_entry`), with the values of
A30, carried to States 6–7. Logs redact authorization, cookie and secret-like names.
Fixed security headers are sent on every answer, and credential and
session answers are not cached; the header list and the answers it covers
are those of the accepted transport guard, carried to States 6–7 (owner
2026-11-06: current service behaviour accepted; technical decisions
delegated). Liveness and readiness are public and change nothing (R0-11). The
viewer browser session is the host-only cookie of R0-09; a viewer sign-out
must come from the canonical public origin (viewer entry is not
origin-checked), compared by scheme, host
and effective port, with no pattern matching. The trusted-host, CORS and public-origin
settings and their checks are those of the accepted transport guard,
stated by the notes of `transport_guard`, carried to States 6–7. Service principals use bearer
headers only. Recorded in the accepted spec as `rules.http_transport_policy` (Factory
`38626cc7`, `21658368`, `e8a61895`, `35a0a09c`, `dc351917`, `51d19fdf`).

### Formal invariants

- TRN-001: no request reaches a handler on an untrusted host or with an
  oversize body.
- TRN-002: no viewer sign-out succeeds from a foreign origin, and no viewer
  project read succeeds without the cookie.
- TRN-003: no credential, cookie or secret appears in a log line.

### Required tests

- Factory focused checks `client_portal_transport_guard`,
  `client_portal_api_transport_check` and `runtime_settings_client_portal`
  (`babd5e52`, `3080ef0d`, `dc351917`).
- TRN-001, TRN-002, TRN-003: the runtime behaviour check
  [witness: verification:runtime_behavior_client_portal].
- TRN-001, TRN-003: the transport guard check
  [witness: verification:transport_guard_client_portal].
- TRN-002: the API transport check
  [witness: verification:api_transport_financial_policy_registry_gateway_client_portal].
- The limiter key (Normative rules above) has no witness yet: the Factory
  check `verification/client_portal_transport_guard_check.py` asserts it but
  no verification command runs it; carried to Factory checks (State 2
  rounds 115–116), together with the route and request-controlled-input
  cases.

### Consequence

The values reach code by the paths of SPEC_STANDARD 15.3.1. The deployment
values are fields of the `RuntimeSettings` that `install_transport_guards`
and `create_runtime_app` are handed: `trusted_hosts`, `allowed_origins`,
`public_origin`, `max_request_body_bytes`, `max_binary_response_bytes`,
`production_logging`, `viewer_entry_rate_limit_attempts` and
`viewer_entry_rate_limit_window_seconds` (A30). The release values are the
data-provider constants below, which the model-written `transport_guard` and
`runtime` import. What remains of `rules.http_transport_policy` — the viewer
cookie name, attributes and extraction — is IR read only by the deterministic
viewer cookie backend that `api_irregular` is emitted with
(`rules.viewer_cookie_transport_backend`); no model-written module reads it.
Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): the values the generated transport guard and runtime read are data-provider constants: `API_PREFIX`, `VIEWER_ENTRY_PATH`, `VIEWER_LOGOUT_PATH`, `NO_STORE_PATHS`, `NO_STORE_CACHE_CONTROL`, `SECURITY_HEADERS`, `TRANSPORT_LOG_LABELS`, `HEALTH_LIVE_PATH`, `HEALTH_READY_PATH`, `HEALTH_OK_STATUS`, and `TRANSPORT_GUARD_STATUSES`, the status of each refusal of the guard keyed by `= models.TransportGuardRefusal`. The client network identity of the viewer-entry limiter is bounded by `VIEWER_ENTRY_CLIENT_IDENTITY_MAX_CHARACTERS` (its leading characters kept) and stands in as `VIEWER_ENTRY_CLIENT_IDENTITY_UNKNOWN` when the connection names no client; the notes of `transport_guard` state the bound and the source (owner-approved cleanup 2026-11-10: lost from the notes since `018b2e2e`; the leaves `maximum_characters` and `unknown_placeholder` of `limits.viewer_entry.client_network_identity` leave the policy). Their former leaves (`public_api_prefix`, `security_headers`, `browser_session.logout_path`, `health.liveness_path`, `health.readiness_path`) leave the policy; the cookie name and attributes stay, the viewer cookie backend reads them.

Owner 2026-11-08 (Q08): readiness answers the health status
`HEALTH_OK_STATUS` (`ok`) only after the storage probe — one transaction
opened and rolled back — succeeded, and checks no external service (no
Registry, no storage of binaries).

## Accepted decision A26 — Exceptions carry data in fields, not messages (accepted Factory spec, 2026-08-03)

### Normative rules

An exception message is never a data channel. `RegistryBoundaryError` carries
its `RegistryFailureKind` in a `kind` field and `SnapshotContentRejected` its
`ImportRejectReason` in a `reason` field; callers classify by the field.
Recorded in the accepted spec as `rules.exception_payload_policy` (Factory `a12937fd`).

### Formal invariants

- A snapshot import rejection's recorded reason equals the raised exception's
  `reason`, whatever its message text.

### Required tests

- A snapshot import test per `ImportRejectReason` value.
- Witnesses, the focused Factory verification checks that assert it: recorded reason equals exception reason [witness: verification:snapshot_import_sqlite_uow_client_portal].

### Consequence

The exception fields are State 6 contracts and the payload rules are prose of the notes that raise each exception (SPEC_STANDARD §2). The accepted spec's `rules.exception_payload_policy` records the same policy and is carried unchanged. No module reads it and no note names it; its home is the fourth of SPEC_STANDARD 15.3.1, a policy a Factory gate reads: its kind `exception_policy` is declared in the Factory's `tools/gate_rules_reads.py` (`GATE_RULES_READS`), and the gate checks the generated code against it (owner 2026-11-09).

## Accepted decision A27 — Derived view orderings (accepted Factory spec, 2026-08-09; owner 2026-11-06)

### Normative rules

Expenses are ordered by document date descending, then creation time
descending, then id descending; an expense's allocations by creation time
ascending, then id ascending; payments by payment date descending, then
recording time descending, then id descending; photos by photo date
ascending, then publication time ascending, then id ascending. Normative
value: `rules.derived_view_ordering` of the accepted spec (Factory `d2c4511e`;
retired 2026-11-09, see Consequence).

The former State 1 text of 2026-07-19 ordered the same lists by
`(document_date, expense_id)` descending, `allocation_id`,
`(payment_date, payment_id)` descending and `(photo_date, photo_id)`
ascending. The accepted value is adopted as it is and replaces that text
(owner 2026-11-06: current service behaviour accepted; technical decisions
delegated; answers OQ-18 and `open_questions.md` Q18).

### Formal invariants

- The same records yield the same order on every read.

### Required tests

- A derived-view test with two records of equal date per list.
- Witnesses, the focused Factory verification checks that assert it: same order every read [witness: verification:derived_views_uow_client_portal].

### Consequence

The orderings are behaviour, stated as prose by the notes of the functions that build each view (SPEC_STANDARD §2); `01_models.md` "Projections and answers" records the replacement. The accepted spec's `rules.derived_view_ordering` recorded the same orderings; no module and no deterministic backend read it, so it delivered nothing to generated code (SPEC_STANDARD 15.3.1), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md): the Normative rules above are its one record.

## Accepted decision A28 — Clock policy (accepted Factory spec, 2026-08-09; one clock source, coordinator 2026-11-07)

### Normative rules

Persisted timestamps are UTC, stored as offset-naive datetimes. An operation
reads the clock once for its own timestamps, and that one
instant supplies every portal-owned timestamp it writes (event times such as
`created_at`, `received_at`, `revoked_at`) and every current-time comparison
that decides the validity of those writes or of persisted records. Times a
source supplies — `approved_at`, `published_at` of a snapshot, `confirmed_at`
of a recognition, `photo_date`, a service credential's `expires_at` — are
kept as supplied: the same instant, stored offset-naive UTC like every
persisted timestamp, never replaced by the clock (State 1 Modeling
conventions). Calendar dates a source supplies — `document_date` of a
recognition, `payment_date` — are `date` values, kept as the supplied
calendar day: they carry no time or offset, are never converted to an
instant and never replaced by the clock's day; their accepted forms and checks, and where in an operation
its one clock read happens, are the accepted spec's, carried to States 6–7. An expiry is valid strictly before its instant: a
session, credential or token is usable while `now < expires_at` and expired
from `now = expires_at` on (Factory code `application/authorization_guard.py`,
`application/service_identity.py`). Reading local time, an offset-aware
persisted timestamp and a second clock read by the operation itself are
forbidden. The one exception is the `occurred_at` of an audit record appended
through the audit writer: the writer takes it when it appends (Factory
code `application/audit_writer.py` 136); the bootstrap, which builds its
own audit, keeps its one instant (Factory `c92b6878`). This
narrows the former convention "Timestamps are timezone-aware UTC" of State 1:
the instants are UTC, their stored form is offset-naive.

The host has two clocks, and one clock source is the only reader of both;
every other part of the portal obtains time from it and never reads a host
clock itself:

- the wall clock gives the instant: the current UTC time as an offset-naive
  datetime, one reading per operation for its own timestamps, the same value
  `datetime.utcnow()` gives (no cache, no local time, no second reading by
  the operation, no arithmetic in the clock source; an operation derives
  an expiry by adding its TTL to the instant it read); the audit writer's reading of an appended
  record's `occurred_at` is the one further reading (the exception above);
- the elapsed clock gives a duration scale: one reading per call of a
  clock that cannot move backwards, in seconds as a float, the same value
  `time.monotonic()` gives. Its one user is the viewer-entry rate limit of
  A25, which takes one reading per viewer-entry request and measures its
  window with it; a reading is never stored, never turned into an instant
  and never ordered against a persisted record.

How many readings an operation takes and which instant it reuses stay the
rules above. The clock source is the emitted module `system_clock`
(SPEC_STANDARD §6.9 version 5); every other module obtains time by calling its
two emitted functions, `utc_now` for the wall instant and
`monotonic_seconds` for the elapsed reading, which the notes of each
consumer name and import.

### Carried changes

The accepted spec 459ac96c has no clock source: thirteen modules read
`datetime.utcnow()` and the transport guard reads `time.monotonic()`
directly (coordinator decision of 2026-11-06, `SOURCE.md`). The coordinator
decided on 2026-11-07 to name the one source instead (SPEC_STANDARD §6.9
version 5, KG-003 closed). The values and moments are unchanged: the wall
reading equals `datetime.utcnow()` and the elapsed reading equals
`time.monotonic()`, each read at the same point of the same operation.

### Formal invariants

- CLK-001: an operation that reads the current time — to write a
  timestamp or to compare the current time with a stored one, a session or
  credential expiry check included — takes one wall reading from the clock
  source, the only reader of the host clocks; that instant is every
  current time the operation uses, and every portal-owned event timestamp
  it writes, other than an audit record's `occurred_at` taken by the audit
  writer, is that instant; an expiry it derives from a TTL is that instant
  plus its TTL; source-supplied times and dates, a service credential's
  supplied `expires_at` among them, keep their supplied values.
- CLK-002: elapsed durations are measured only through the clock source's
  monotonic reading, one elapsed reading per viewer-entry request; they
  are used within one process, never persisted,
  and never compared with or mixed into wall-clock values. Owners: the
  clock source, as the only reader of the monotonic clock; the viewer-entry
  rate limit of A25, for its one reading per request and its window.

### Required tests

- CLK-001: a test per operation that reads the current time — writing a
  timestamp or comparing it with a stored one, expiry checks included —
  with the clock source fixed at a known instant, showing that the
  operation reads it once and uses that instant for every comparison, that
  its portal-owned event timestamps equal that instant, that a derived
  expiry equals that instant plus the TTL, and that supplied times and
  dates are stored as supplied; and that no module other than the clock
  source reads the host wall or monotonic clock directly.
- CLK-002: a test showing that the elapsed durations the portal measures
  (the A25 viewer-entry window) come from the clock source's monotonic
  reading, one elapsed reading per viewer-entry request, are not persisted, and are not compared with or mixed into
  wall-clock values.
- Witnesses, the focused Factory verification checks that assert it: CLK-001 [witness: verification:service_identity_consumer_uow_client_portal]; CLK-001 [witness: verification:staff_bootstrap_client_portal]; CLK-002 [witness: verification:transport_guard_client_portal].

### Consequence

Consumers import the emitted `utc_now` and `monotonic_seconds` of `system_clock` and name them in their notes; nothing else delivers time to generated code. `rules.system_clock_backend` and `rules.time_source_policy` are the IR `system_clock` is emitted from and the Factory's time-source gate reads; no model-written module reads them. `rules.clock_policy` was the accepted spec's record of the rules above (Factory `c92b6878`); no module and no deterministic backend read it (the Factory's time-source gate reads `rules.time_source_policy`), and it is retired (owner 2026-11-09; `60_data_closure.json` `retired`, SOURCE.md). The representation it recorded is the one `utc_now` returns.

## Accepted decision A29 — First-administrator bootstrap policy (accepted Factory spec, 2026-08-17)

### Normative rules

R0-07 made exact. The local command creates the single first staff account
on an empty staff table: role administrator, status active, `email_verified_at`
set, no creator; its audit is `staff.create` by the system actor with the created
`staff_id`, result success. R0-07's "never printed, logged or audited"
concerns the email and password the command is given: the audit record
names the created account by its `staff_id` and carries neither. The emptiness check and both inserts run in one
write transaction that no concurrent attempt can interleave, so concurrent attempts create exactly one
account; when any staff account exists the command refuses with
`BootstrapAlreadyCompletedError` and nothing persists. The password is kept only
as its hash; email and password are read neither from process arguments nor
the environment nor a file and are never written to output, logs, audit,
return values or exception messages, with one exception: the use case
returns the created account view with the normalized email and the command
prints that email to the operator who supplied it (Factory code
`application/staff_bootstrap.py` 55, `cli/staff_bootstrap.py` 33). There is no HTTP route and no API
description entry. Exit codes are a closed external contract (Factory code
`cli/staff_bootstrap.py` 19, 28, 31, 34):

| Outcome | Exit code |
| --- | --- |
| account created | 0 |
| confirmation did not match | 1 |
| identity input rejected | 2 |
| bootstrap already completed | 3 |

The accepted spec held these values as `rules.staff_bootstrap_policy`
(Factory `6011ac93`); see Consequence.

### Formal invariants

- BOOT-001: at most one account is ever created by the command, and only on
  an empty staff table.
- BOOT-002: the exit code of each outcome is the one listed.

### Required tests

- A bootstrap test on an empty and a non-empty store, with two concurrent
  attempts, and one per exit code.
- BOOT-001: the bootstrap store check
  [witness: verification:staff_bootstrap_store_client_portal].
- BOOT-002: the bootstrap command check
  [witness: verification:staff_bootstrap_cli_client_portal].

### Consequence

The policy data behind the invariants is the exit-code table above, the rules table of this decision; the rest of the policy is the decision's rules text. The bootstrap modules of State 3 own it. In the specification the serialized write is lowered by `rules.sqlite_unit_of_work_backend.bootstrap_store`; the account values, the audit, the input boundary, the disclosure limits and the exit codes are stated by the State 7 notes of `bootstrap_first_administrator` and `run_bootstrap_cli`. There is no `rules` namespace for it (the accepted spec's `rules.staff_bootstrap_policy` was removed 2026-11-07, SOURCE.md). Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): `run_bootstrap_cli` reads the exit-code table, so it is the data-provider constant `BOOTSTRAP_EXIT_CODES`, keyed by `= models.BootstrapCommandOutcome` and total, values unchanged.

## Accepted decision A30 — Configuration

### Normative rules

The former configuration, kept (owner-confirmed defaults, R0-06):

Values with confirmed defaults:

```text
registry_endpoint_env_name            = REGISTRY_BASE_URL (required start-up variable since 2026-11-09)
registry_timeout_seconds               = 5
staff_session_ttl_hours                = 12
viewer_session_ttl_days                = 30
credential_entropy_bytes               = 32
credential_hash_scheme                 = argon2id (library defaults; fixed in source, not a deployment value)
binary_read_limit_env_name             = BINARY_MAX_READ_BYTES (required positive integer)
```

The *existence* of a timeout/TTL/rate limit is an invariant. The running
service reads none of the first five values from its environment (only the
URL `REGISTRY_BASE_URL` names): a deployment cannot change them, a release
does. Since 2026-11-08 they are data-provider constants (Consequence); the
owner's defaults are their values.

The Registry URL is read only through `runtime_settings` (owner decision
2026-11-09, SPEC_STANDARD 6.11: a second reader of the environment is a
defect). `REGISTRY_BASE_URL` is a required variable of the start-up table that
R0-10's check covers, read into the `registry_base_url` field of
`RuntimeSettings`: a missing or empty value stops the start, and the Registry
gateway takes the value from the settings `load_runtime_settings` returns,
never from the environment. Before this decision the gateway read the
variable itself at each call, and its absence failed only Registry calls
(`SEMANTIC_DIFF.md`). The start-up check refuses only a missing value or
one that is empty or whitespace only, tested on the value as supplied (the
row's normalization is `none`); which values the gateway accepts as a base URL and how it joins them
with the request paths stay the accepted gateway's (note `_registry_url`,
the Registry path constants), carried to States 6–7.

### Carried changes

- The email gateway endpoint and timeout, the three challenge lifetimes and the
  challenge rate limit of the former configuration are removed with the
  challenges (owner 2026-11-07, A10, `00_product.md` R0-23).
- `credential_hash_scheme`: its parameters are those of the running
  service's pinned hashing library (A32), carried to States 6–7; a change
  of them is a Factory route change (A32). Owner 2026-11-06: current
  service behaviour accepted; technical decisions delegated.
- `binary_read_limit_env_name`: the binary read limit is the environment
  variable `BINARY_MAX_READ_BYTES`, a required row of the start-up table read
  into the `binary_max_read_bytes` field of `RuntimeSettings`; the storage
  root `BINARY_STORAGE_ROOT` likewise into `binary_storage_root`. The emitted
  `binary_storage` takes both from the settings `load_runtime_settings`
  returns, which it calls at each read, as its backend IR
  (`binary_storage_backend` schema version 2, `settings`) names them, and
  reads no environment itself (owner 2026-11-09, SPEC_STANDARD 6.11;
  Factory code-factory #201). Until then it read both variables itself
  (Factory `a6916180314d`). No model-written module reads them.
  `BINARY_STORAGE_ROOT` is a required string row kept as supplied: a
  missing, empty or whitespace-only value stops the start (CFG-002); the
  start checks nothing about the path itself. How a read resolves a
  `file_ref` under the root and which filesystem conditions fail it is
  behaviour of the emitted `binary_storage`, not of this decision: the
  deterministic backend decides it from its IR, as for the media types
  (A14), and answers every such failure as `BinaryStorageError` (owner
  2026-11-06: current service behaviour accepted; technical decisions
  delegated).
- Registry paths (accepted `config.registry_request_paths`, since 2026-11-08
  the data-provider constants of the Consequence): the paths are fixed as
  `projects/active` for the active list (owner 2026-11-08, Q12, A6: the
  constants `REGISTRY_PROJECTS_PATH` and `REGISTRY_ACTIVE_SEGMENT` joined),
  `projects/{project_id}/validate` and `projects/{project_id}/context`
  (Factory `300bd11d`). The accepted spec read `projects` and kept only
  active projects while decoding; since Q12 the gateway reads
  `projects/active`, as State 0 names it, and still keeps only active
  references while decoding.
- `config.runtime_environment_variables`: the closed table of environment
  variables, their types, requiredness, normalization and per-environment
  defaults, read into `RuntimeSettings` (R0-10; Factory `a6916180314d`,
  `51d19fdf`).
- `config.persistence`: the storage schema revision and table names (Factory
  `48a49aa6` … `d1280708`), carried by the persistence closure.

### Formal invariants

- CFG-001: every timeout, TTL, rate limit and bound below exists and is
  applied; its value is the data-provider constant or the start-up setting
  this decision names: the Registry request timeout
  (`REGISTRY_TIMEOUT_SECONDS`), the staff and viewer session lifetimes
  (`STAFF_SESSION_TTL_HOURS`, `VIEWER_SESSION_TTL_DAYS`), the viewer-entry
  rate limit (`viewer_entry_rate_limit_attempts` within
  `viewer_entry_rate_limit_window_seconds`), the request body bound
  (`max_request_body_bytes`), the binary response bound
  (`max_binary_response_bytes`) and the binary read bound
  (`BINARY_MAX_READ_BYTES`).
- CFG-002: a required start-up variable that is missing or invalid stops
  the start before any request is served; for the Registry URL the start-up
  check refuses only a missing, empty or whitespace-only value, and any other unusable URL
  fails each Registry call as `transport_error` (A6).

### Required tests

- CFG-001: one check per bound, each with the bound at its value: a Registry
  request that outlasts the timeout fails as the `timeout` member of
  `RegistryFailureKind`; a staff session and a viewer session are refused
  from the instant their issue time plus their lifetime is reached; the
  viewer-entry attempt after the limit within the window is refused and
  creates no session; a request body over its bound and a binary over its
  read bound are refused before the handler or the response; and the start
  is refused when the read bound exceeds the response bound, which is how
  `max_binary_response_bytes` is applied: no module compares a response with
  it, and every binary sent is within the read bound and so within it.
- CFG-002: `runtime_settings_client_portal`: for each required variable
  other than `REGISTRY_BASE_URL` a missing value and an invalid value stop
  start-up; a missing, empty or whitespace-only `REGISTRY_BASE_URL` stops
  it, while any other value is accepted at start whatever its form (A6
  refuses an unusable one at each call); and a complete valid environment
  starts.
- Witnesses, the focused Factory verification checks that assert it: CFG-002 [witness: verification:runtime_settings_client_portal].
- Witnesses, the focused Factory verification checks that assert it: CFG-001 [witness: verification:binary_storage_content_client_portal].

### Consequence

Each value reaches code by one path of SPEC_STANDARD 15.3.1. A deployment value is a row of `config.runtime_environment_variables` read only by `load_runtime_settings`, into a field of `RuntimeSettings` (`database_url`, `environment`, `public_origin`, `trusted_hosts`, `allowed_origins`, `max_request_body_bytes`, `max_binary_response_bytes`, `production_logging`, the two viewer-entry limits and, since 2026-11-09, `registry_base_url`, `binary_storage_root` and `binary_max_read_bytes`); the emitted `binary_storage` reads the last two from the settings `load_runtime_settings` returns, like every other reader. A release value is a data-provider constant generated code imports (below). The storage table names of `config.persistence` are read only by the emitted repositories, through the persistence backend IR; `config.credential_hash_scheme` only by the emitted `credential_security`. No model-written note names a `config` address. Data placement 2026-11-08 (owner: the specification rebuilt by SPEC_STANDARD; SOURCE.md "Data placement"): the Registry request paths and timeout, the staff and viewer session lifetimes and the credential entropy have the same value in every environment and change only by a decision about the product, so by SPEC_STANDARD 15.2 (check 4 before 3) they are data-provider constants that generated code imports (`REGISTRY_PROJECTS_PATH`, `REGISTRY_ACTIVE_SEGMENT` (Q12), `REGISTRY_CONTEXT_SEGMENT`, `REGISTRY_VALIDATE_SEGMENT`, `REGISTRY_TIMEOUT_SECONDS`, `STAFF_SESSION_TTL_HOURS`, `VIEWER_SESSION_TTL_DAYS`, `CREDENTIAL_SECRET_BYTES`), values unchanged; the path templates are split into a path and three segments (the active one added by Q12), because a template is not data (15.11). The Registry URL itself is an environment value: since the owner's decision of 2026-11-09 it is the `registry_base_url` field of `RuntimeSettings`, a required row of the start-up table, and the data-provider constant `REGISTRY_BASE_URL_VARIABLE` that named the variable for the gateway is removed (SPEC_STANDARD 6.11).

## Accepted decision A31 — Security review of the migrated case

### Normative rules

The total review of `SECURITY_REVIEW_EVIDENCE.md` over States 0–2 as migrated.
It decides nothing new: each applicable category is owned by a decision above.

### Formal invariants

- Every category has an explicit outcome: APPLICABLE resolves to an accepted decision, UNRESOLVED to an open question, and NOT_APPLICABLE carries its project-specific rationale (`SECURITY_REVIEW_EVIDENCE.md`).

### Required tests

- `python tools/design_lint.py examples/client-portal --state 2`.
- Witness: the State 2 security-review gate of the authoring sequence runs this lint [witness: workbench:state2_rules_decisions].

### Consequence

State 3 may start only when no category is UNRESOLVED.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A3, A4, A10, A11, A16, A17, A25; affected: M01-M15, staff login, viewer entry, producer bearer authentication
- secrets: APPLICABLE; references: A16, A17, A25, A29; affected: M02, M03, M05, M06, M14, issued secrets, logs
- authorization: APPLICABLE; references: A1, A2, A4, A5, A11, A12; affected: every project-scoped operation, administrator routes
- injection_interpreted_input: APPLICABLE; references: A5, A16, A30; affected: Registry request paths and identifiers, staff email input, persisted queries
- external_callbacks_webhooks: APPLICABLE; references: A3, A7, A8, A12, A25; affected: M18, M25, M34, snapshot publication, recognition intake
- browser_boundary: APPLICABLE; references: A25; affected: viewer cookie session, CORS, trusted hosts, mutation origin
- files_artifacts: APPLICABLE; references: A14; affected: M30, M35, binary storage root, and the hand-over of placed binaries that stays Q12 (R0-13)
- concurrency: APPLICABLE; references: A8, A18, A19, A22, A29; affected: replay identities, single active budget version, bootstrap
- dependencies: APPLICABLE; references: A32; affected: deploy/requirements.txt (fastapi, pydantic, argon2-cffi, uvicorn pinned)

## Accepted decision A32 — Dependency pins and their vulnerability check (owner 2026-11-06: current service behaviour accepted; technical decisions delegated)

### Normative rules

1. The deployed portal runs only the externally maintained libraries pinned
   exactly in the Factory deployment
   (`projects/client_portal_sandbox/deploy/requirements.txt`: fastapi,
   pydantic, argon2-cffi, uvicorn), each a direct import of the deployed
   source; the pinned versions are those of that file.
2. A pin changes only through the Factory route, like any other deployed
   source change; nothing updates a dependency at run time or on the host.
3. A deploy is the start of the service from a built image. Before it,
   every distribution installed in that image — the pins and every library
   pip resolves for them — is checked against a snapshot of the OSV
   database (osv.dev, ecosystem PyPI) no older than the deploy route's
   maximum snapshot age; an image with a distribution that has a known
   vulnerability is not deployed until a rebuild through the Factory route
   passes the check.
   A distribution counts as affecting the portal when OSV lists a known
   vulnerability for its version; reachability inside the portal is not
   judged case by case, so such a distribution blocks the deploy whatever feature the
   advisory concerns. A check that cannot complete does not pass, and the
   deploy waits. How the
   check is run (its tool, how the snapshot is obtained and verified, how a
   version is matched to an advisory) is a deployment procedure, not a
   portal rule, carried to the deploy route and to its witness check at
   State 8 (code-factory #189).
4. The portal adds no runtime feature for this: no update service, no
   network call at start, no dependency report on any API.

This describes the existing deployment and answers OQ-17 and
`open_questions.md` Q17.

### Formal invariants

- DEP-001: every library from outside its own source that the running
  portal imports directly is pinned to one exact version in the deployment
  requirements; the libraries pip resolves for them are not pinned.
- DEP-002: no deploy starts the service from an image in which an
  installed distribution — a pin or a library pip resolves for it — has a
  known vulnerability listed for its version in the deploy route's OSV
  snapshot, within the route's age limits.

### Required tests

- DEP-001: the deployment requirements contain only `==` pins, one per direct
  import [witness: verification:dependency_pins_client_portal].
- DEP-002: the pre-deploy vulnerability check of those pins passes: the deploy
  step judges every distribution installed in the built image, bound to its
  content id, against an OSV snapshot no older than the deploy
  route's maximum snapshot age, and starts the service only on a passing
  verdict about that same image no older than its maximum environment age
  (`max_snapshot_age`, `max_environment_age`: deployment procedure values of
  the Factory deploy route, rule 3, not portal rules); a listed
  version, stale, missing or unmatchable data, or another image does not
  start it [witness: verification:dependency_release_gate_client_portal].

### Consequence

No value enters the specification (SPEC_STANDARD 15.3.1: no path to generated
code); the decision is operational and owned by the Factory deployment route.

## Answered question OQ-17 — Dependency vulnerability and update policy

Answered by A32 (owner 2026-11-06: technical decisions delegated).
`open_questions.md` Q17.

## Answered question OQ-18 — Tie-break order of the derived views

Answered by A27: the accepted Factory value is adopted (owner 2026-11-06).
`open_questions.md` Q18.


## Carried to later closures

Rules sections of the accepted Factory spec that are not State 2 decisions:
they are deterministic backend IR, authored after State 6 contracts.

- `rules.persistence_backend` (`persistence_backend/v2`, Factory `d1280708`)
  — persistence closure (`70_persistence_closure.json`).
- `rules.http_router_backend` (50 routes since the six challenge routes left on
  2026-11-07, A10; 56 in the accepted spec, Factory `300bd11d` … `a6916180314d`)
  — router closure and router context (`70_router_closure.json`,
  `70_router_context.json`).
- `rules.credential_security_backend`, `rules.binary_storage_backend`,
  `rules.viewer_cookie_transport_backend` (Factory `8387e0a3`) —
  deterministic backend binding.
- `rules.role`, `rules.schema_version` (data role, schema version 1; Factory
  `8387e0a3`) — standard version 2 section metadata, set at assembly.
- The former `rules.http_route_catalog` of 2026-07-19 is replaced by the
  router backend (Factory `300bd11d`); its routes return in State 5.

## Unresolved at State 2

The former list, kept:

- Mandatory MFA for staff (open product question; architecture unaffected).
  Not required in the running service: a staff account logs in with its
  email and password alone, and no second factor exists (owner 2026-11-06:
  current service behaviour accepted).
- Administrative-area boundaries (dormant until a second area exists).
- PresuPro→Portal transport binding (bearer/signed/mTLS) — decided by R0-09
  and A25: bearer header only; signed requests and mTLS are not accepted.
- External binary deletion/retention after source intake.

Added by the migration and answered on 2026-11-06: OQ-17 (dependencies,
A32) and OQ-18 (derived view orderings, A27).

## State 2 readiness assessment

The former assessment, kept:

- Every invariant has a stable ledger id, one owning responsibility, and an
  expected landing class.
- All policy tables are rules data, not prose; every enum referenced by a
  table exists in `10_models.md`.
- Config is separated from rules by change-reason; no value is hidden in
  notes.
- No invariant is owned by "the whole system"; guard order, cascade
  semantics, and idempotency identities are explicit.

The migration adds: every security category resolves to an accepted
decision (A31); OQ-17 and OQ-18 are answered.
