# Client Portal — source context and legacy evidence

## Purpose of this file

Client Portal was designed in this Workbench on 2026-07-18/19 in the layout of
that time and assembled into a specification the Factory imported on
2026-07-22. The tools of the current standard do not see that layout
(`open_questions.md` Q15). This case is being migrated to the current authoring
standard; this file records where the design text comes from, which text is
authoritative, and how the running Factory project relates to it.

The method is `skills/spec-authoring/LEGACY_MIGRATION_EVIDENCE.md`: **code and
tests are probes, never sources of norm.** A migration changes form, not
meaning; a finding the evidence admits more than one reading of is
`unresolved` and becomes a question in `open_questions.md`.

## Which text is authoritative

Read from the former `README.md` and `spec/HANDOFF.md` (Workbench
`agent/client-portal` at `3d09179a`, a verbatim carry of
`product-decisions-and-reassembly` at `ce70a8f3`):

| set | role |
|---|---|
| former `01_product_boundary.md` … `09_notes.md` | the frozen requirements baseline ("requirements input … not an assembled specification"). Moved unchanged to `baseline/`. |
| former `spec/00_product.md` … `spec/80_assembly.md`, `spec/invariant_ledger.json` | the authoring pass, States 0–8, decisions of 2026-07-18/19. **The authoritative design text.** Each file moves to the current layout with its state's migration. |
| former `spec/HANDOFF.md` | key decisions 1–22 and the owner confirmation of 2026-07-19; carried into the states that own them (State 0: `00_product.md` R0-01 to R0-06). |
| `global_spec.json` (sha256 `1f6b8204…`) | the State 8 assembly of that pass; replaced when State 8 is reached again. |

## Divergence: the accepted Factory spec moved on without the case

The Factory imported the case's specification on 2026-07-22 (Factory
`4bdaa008`; it differs from the case's assembly only in four module paths
and one contract with its three notes). Between 2026-07-22 and 2026-08-17 the
Factory accepted 45 further changes to
`projects/client_portal_sandbox/specs/base/global_spec.json` through its own
spec operations, none of which reached this case. The accepted spec (sha256
`459ac96c4b8febc629c81178c9d0a84ee072d1662dc52f44d74fb0993cb3c2c7`, Factory
`6011ac93`, 2026-08-17) is what the portal runs and what the owner's open
questions Q10–Q14 were observed against.

| section | case assembly 2026-07-19 | accepted Factory spec 2026-08-17 |
|---|---|---|
| contracts | 318 | 565 |
| notes | 337 | 851 |
| models | 104 | 149 (27 entity, 80 value, 27 enum, 15 interface) |
| rules | 18 | 34 |
| modules | 20 | 39 |
| standard | v1 with `adapters`, `module_hints` | `standard_version` 2 |

The owner's goal for this migration (2026-11-06) measures the assembled result
against the accepted Factory spec, with zero meaning changes. The migration
therefore carries the meaning of the accepted Factory spec: the case text is the
design of its original part, and each accepted Factory change is carried into
the earliest design state that owns it, citing the Factory commit. Each Factory
commit body records its Why, Route, Safety and Validation; those bodies are the
rationale this case cites. Nothing below is decided by the migration.

### Accepted Factory changes and the state that owns them

All Factory references are to `code-factory` `main` at `23a17dc8`
(2026-11-06); paths under `projects/client_portal_sandbox/`.

| commit | date | change | owning state |
|---|---|---|---|
| `4bdaa008` | 07-22 | import of the case spec; module paths `application/*` for four modules | 3 |
| `50ff3ed0` | 07-22 | explicit model imports narrowed | imports closure |
| `af686d73`, `5677993e`, `48a49aa6`, `ac279dd8` | 07-22 | narrow persistence ports, SQLite audit and project-tracking repositories | 3, 6, persistence |
| `300bd11d` | 07-23 | declarative router table, `rules.http_error_policy`, `config.registry_request_paths`; two private functions removed | 5, 6, router |
| `a6d7b759`, `37b1f529`, `f8c5cb9a` | 07-24 | budget and snapshot-import SQLite units of work | 3, 6, persistence |
| `0baceacc` | 07-25 | expense repository; `rules.transaction_guard_policy` | 2, 6, persistence |
| `0f9ae3ae` | 07-26 | expense consumers on narrow ports; `rules.audit_entity_id_policy` | 2, 6, 7 |
| `7eb7ebcc`, `e12ed74d`, `fd790562`, `62c73965` | 07-26 | progress photo, email delivery, staff access, viewer access repositories; `rules.audit_result_reason_policy` | 2, 6, persistence |
| `bd561732` | 07-26 | client view repaired; `rules.model_immutability_policy` | 2, 7 |
| `ced617bd`, `efd08476`, `88c1dbbc` | 07-27 | viewer access, authorization guard, service identity on narrow ports; guard reads the persisted role and binds the session to its identity | 2, 6, 7 |
| `f12197b4` | 07-28 | `staff_identity` split into `staff_identity` and `staff_challenges` | 3, 6 |
| `39934597` | 07-29 | Argon2id password hashing (R0-06 default, made real) | 6, 7 |
| `38626cc7` | 07-31 | request-body models, runtime contract (`runtime`, `runtime_settings`) | 0 (R0-10), 5, 6 |
| `21658368`, `e8a61895` | 07-31 | JSON-only API, runtime transport, health answers | 0 (R0-11), 2, 6 |
| `35a0a09c` | 08-01 | viewer cookie sessions | 0 (R0-09), 2, 5 |
| `babd5e52` | 08-01 | binary delivery as exact bytes; `transport_guard` module | 0 (R0-12), 2, 3 |
| `3080ef0d`, `9eab4d94` | 08-02 | routes for password change, recovery override, progress, payments, photos, budget version; safe views | 5, 6 |
| `a12937fd` | 08-03 | snapshot import rejections classified by field | 2, 6 |
| `dc351917`, `51d19fdf` | 08-03, 08-06 | trusted hosts, origins, environment mapping (`config.runtime_environment_variables`) | 0 (R0-10), 2 |
| `2e77ffab` | 08-05 | `project_tracking` import surface narrowed | imports closure |
| `fe6503ea` | 08-07 | `module_hints` removed | assembly (form only) |
| `f4254847`, `61dfb1b7`, `d9b892e3` | 08-07, 08-09 | `api_irregular` viewer boundary pinned; slices reordered | 3, router |
| `fae77f99` | 08-08 | administrator project list | 0 (R0-08), 5 |
| `d2c4511e` | 08-09 | view projections, `rules.derived_view_ordering`, overview project pair | 2, 6 |
| `00ac72f1` | 08-09 | inaccessible viewer projects isolated | 2 |
| `c92b6878` | 08-09 | `rules.clock_policy` (persisted UTC) | 2 |
| `a6916180` | 08-11 | row selection and Registry URL values declared | 7 |
| `8387e0a3` | 08-15 | credential security, binary storage and viewer cookie transport backends | 2, backend binding |
| `3a72da32` | 08-15 | `identity: value|entity` on every runtime model (owner decided the Registry boundary: ProjectReference entity, ProjectContext value) | 1 |
| `d1280708` | 08-16 | `standard_version` 2, `adapters` removed, `rules.persistence_backend` v2 | persistence, assembly |
| `6011ac93` | 08-17 | first-administrator bootstrap (`staff_bootstrap`, `staff_bootstrap_store`, `staff_bootstrap_cli`, `rules.staff_bootstrap_policy`) | 0 (R0-07), 2, 3, 6 |

### Classification of what State 0 carries

| finding | evidence | classification | owner |
|---|---|---|---|
| first administrator by local command | Factory `6011ac93`, `rules.staff_bootstrap_policy` | accepted spec change; product action missing from State 0 | `00_product.md` R0-07 |
| administrator project discovery | `fae77f99`, route `GET /admin/projects` | accepted spec change | R0-08 |
| viewer cookie, producer bearer | `35a0a09c`, `babd5e52`, `rules.http_transport_policy.browser_session` | accepted spec change; trust boundary | R0-09 |
| SQLite, local binary root, environment configuration | `4bdaa008`, `38626cc7`, `8387e0a3`, `d1280708`, `config.persistence` | accepted spec change; decides "physical storage undecided" | R0-10 |
| health answers | `21658368`, `rules.http_transport_policy.health` | accepted spec change | R0-11 |
| binary delivery | `babd5e52`, `rules.binary_delivery_policy` | accepted spec change | R0-12 |
| file boundary read-only | owner 2026-11-06, `open_questions.md` Q12 | owner decision | R0-13 |

Findings of later states are classified in those states' migrations.

### State 0 question round

Round-01 (2026-11-06, `questions/state0/round-01/`, Codex CLI provider) on the
migrated `00_product.md`: 45 topics, 10 blocking. Resolved on 2026-11-06 in
favour of the accepted Factory spec under the owner decision of that day
("current service behaviour accepted; technical decisions delegated"):
T1 R0-22, T7 R0-15, T8 R0-17, T10 R0-18, T12 R0-14, T17 R0-16, T32 R0-19,
T33 R0-09, T34 R0-20, T41 R0-21.

| topic | kind | where the answer may already be | note |
|---|---|---|---|
| T1 tax modes and non-gross amounts | answered_later, quote unverified | former `spec/20_rules.md` R9 ("All amounts gross … `tax_mode` is provenance only") | the judge's quote did not match verbatim; re-ask after State 2 migrates |
| T7 unauthenticated reset and health against "every operation checks … valid active session" | contradiction | R4 says "Every project-scoped operation"; R0-06, R0-11 | State 0 wording of 2026-07-18 is wider than R4 |
| T8 intake decisions "operator-supplied" against "from the operator or intake process" | contradiction | accepted spec: expense creation is a staff route (`POST /staff/projects/{project_id}/expenses/from-recognition`) | pre-existing in the text of 2026-07-18; Q12 question 3 is related and not designed |
| T10 document visibility default | consequential_gap | M30 `client_visible`; State 4/5 texts | pre-existing |
| T12 operators manage viewers and grants against access-management capability | contradiction | R2 (operator lacks `access.manage`), accepted routes `/admin/viewers…` are administrator-only | pre-existing; R0-08 repeats the accepted spec |
| T17 "every portal record belongs to exactly one project_id" against staff, viewer, audit and bootstrap records | contradiction | M01–M15, M36 have no or optional `project_id` | pre-existing; R0-07 adds one more instance |
| T32 staff-account creation and initial credential | consequential_gap | former States 4–6 (`create_staff_account`, `issue_email_verification`) | pre-existing |
| T33 bearer-only producer authentication against the open transport binding | contradiction | R0-09 (accepted spec); the open item is now annotated "Decided by R0-09" | closed in the text after the round; to be confirmed by the next round |
| T34 recovery override operation | consequential_gap | accepted route `POST /admin/staff/{staff_id}/recovery-override` (`3080ef0d`) | pre-existing |
| T41 read-import-result action | consequential_gap | accepted route `GET /integrations/snapshot-imports/{import_id}` | pre-existing |

Round-02 (`questions/state0/round-02/`): 47 topics, 4 blocking, repaired in
R0-09, R0-14, R0-17, R0-20. Round-03 (`questions/state0/round-03/`, on the
text of `65c7894013ca`): 38 topics, 2 blocking.

| topic | kind | evidence | resolution |
|---|---|---|---|
| T11 bearer-only producer against "valid active session" | contradiction | R0-09; accepted `authenticate_service_principal`, `authorize_snapshot_import` take a `ServiceActorContext`, no session | common authorization rule: a service principal's authenticated bearer credential stands in for the session |
| T23 how the initial staff password reaches its holder | consequential_gap | accepted `create_staff_account` (no delivery), `change_staff_status` (`pending_verification` → `active` sets `email_verified_at`), `staff_challenges` notes "remain inert while StaffChallengeRepository is deferred", Factory code `application/staff_challenges.py` | R0-19 rewritten (administrator hands the password over outside the portal and activates the account); R0-23 records the deferred challenges and notices; A10, A11 "Carried changes"; Q19 for the owner |

Round-04 (`questions/state0/round-04/`, on the text of `41d0f523e8c6`): 45
topics, 7 blocking: T3 R0-15 gives the deferred operations
token authority while R0-23 says they read nothing; T23 the ServicePrincipal
passage still allows several transports against R0-09; T29 the ClientViewer
passage still lets operators create viewers and links against R0-14; T31
"no portal operation carries" the initial password against its creation
request; T33 archived-project immutability against grant and assignment
changes; T40 who creates `import_id` and how the producer learns it; T44
invariant 2 "access requires a session" without the service-principal
exception. Repaired on 2026-11-06 under the owner decision of that day
(current service behaviour accepted; technical decisions delegated): the
sentences are narrowed to R0-09, R0-14, R0-15, R0-19, R0-23, and two facts
the text left unstated are carried from the accepted spec as R0-24 (archival
freezes project records, not revocation; notes `grant_viewer_project`,
`assign_staff_project`, `grant_producer_project`, `revoke_viewer_project`,
`rules.registry_status_policy`) and R0-25 (the portal assigns a fresh
`import_id` to every classified attempt and answers with the import result;
notes `_build_import_record`, `import_snapshot`, Factory code
`application/snapshot_import.py`).

| round | blocking | topics and resolution |
|---|---|---|
| round-05 | 4 | T9 identical re-publication answers the import result, not the snapshot (R0-25, import rules); T12, T13, T26 grants and assignments of an archived project against the common rule and invariant 5 (common rule and invariant 5 narrowed; R0-24: existing access continues after a new viewer link or staff reinstatement, revocation consults no Registry) |
| round-06 | 1 | T6 reading an import result does not recheck the producer grant or Registry (R0-21; Factory code `get_snapshot_import_result`) |
| round-07 | 1 | T9 the first administrator against "only administrators create staff accounts" (R0-14 names the R0-07 exception) |
| round-08 | 0 | clear; units changed by the round-07 repair still need a second clear review |
| round-09 | 0 | clear on the unchanged text; `design_questions.py status --state 0`: closed, every unit closed by two clear rounds |
| round-10–11 | 0 | reopened (`--since 3a628953`) by "Derived values" naming the zero balance balanced (State 2 A9, running service); clear twice; closed |

### Classification of what State 1 carries

The former `spec/10_models.md` moved into `01_models.md` line for line (every
non-heading line is kept; checked mechanically on 2026-11-06).

| finding | evidence | classification | owner |
|---|---|---|---|
| `identity` of 27 entities and the value models | Factory `3a72da32`; owner decision on ProjectReference / ProjectContext | accepted spec change | `01_models.md` M01–M37 `Identity` |
| `ExpenseAggregate` loses `replayed`; `ExpenseOperationOutcome` carries it | `d1280708` | accepted spec change | M31, "Projections and answers" |
| `ProjectOverview.project` optional with `project_availability` | `d2c4511e` | accepted spec change | "Projections and answers" |
| `BinaryPayload.download_name` always present | `babd5e52` | accepted spec change | "Projections and answers" |
| `ProgressPhotoView`, `ViewerSessionView`, `HealthStatus` | `9eab4d94`, `35a0a09c`, `21658368` | accepted spec change (projections) | "Projections and answers" |
| 26 request models, 15 repository interfaces, `RuntimeSettings`, `RuntimeEnvironment` | `38626cc7`, `af686d73` … `6011ac93` | accepted spec change, not State 1 concepts | "Named in later states" (States 2, 3, 5, 6) |
| Q13: older viewer codes stay valid after a new one is issued | `open_questions.md` Q13 (observation 2026-11-05) against M02, the accepted note `issue_viewer_access` ("MUST revoke every non-revoked prior credential") and Factory `application/viewer_access.py` `issue_viewer_access` (revokes every prior credential) | the probe disagrees with the observation; design and spec agree; nothing to carry | Q13 stays the owner's; "Evidence notes" of `01_models.md` |

### State 1 question rounds

The rounds (`questions/state1/`, Codex CLI provider) asked on the migrated
`01_models.md`. Every blocking topic was closed by repairing the State 1
text to the accepted spec 459ac96c and its code under the owner decision of
2026-11-06 ("current service behaviour accepted; technical decisions
delegated"); each repaired model records it under `Carried changes`, so
the line-for-line claim above holds for the text before these repairs.
Nothing was designed; deferred features stay deferred.

| round | blocking | topics and resolution |
|---|---|---|
| round-01 | 40 | operators named as viewer, link and grant managers (M01, M02, M04 → administrator, R0-14); challenge, reset, email-change, delivery and notice records written as current (M08–M12, Status, M05, M06 marked deferred: R0-23, Q19); plaintext of presented passwords and tokens (conventions); `payment_id` and photo `intake_id` minted by the staff caller (conventions, M33, M34); re-allocation replaces allocations with fresh ids (M29); snapshot identity, replay and conflict answers, conflict `reject_reason = None` (M19, M20, R0-25); `ProjectReference.status` the Registry's string, acted on only as `active`/`archived` (M16, M17); one grant or assignment record per pair, no re-grant (M04, M07, M15: accepted UNIQUE constraints); role, scope mode and viewer display name immutable (M05, M13, M01); viewer session has no credential reference (M03); progress record created by the first update, absence is `None` (M32); expense document view present with `client_visible` (projections); bootstrap audit and password change without audit (M36); imported versions, `source_key` namespace and manual mapping are Q11 (M21, section linking, deferred) |
| round-02 | 6 | principal re-enabling (M13); State 0 sign-out-everywhere is the administrator revocation (M06); initial document description is `document_type` (M30, Factory code `application/expense_intake.py`); administrator scope is the area, not an assignment (M07, A2); unauthenticated import attempts and password changes write no audit (M36) |
| round-03 | 1 | activation refused while an allocation would be unresolved, against "become unresolved" (section linking) |
| round-04 | 4 | `all_projects` chosen at creation is State 0's "explicitly granted capability" (M13); `disabled_at`/`disabled_by` cleared on re-enabling (M13, Factory code `application/service_identity.py`); administrator assignments inert, R0-24 concerns operator assignments (M07); when an imported version is built relative to activation is Q11 (section linking) |
| round-05 | 0 | clear |
| round-06 | 0 | clear on the unchanged text; `design_questions.py status --state 1`: closed, every unit closed by two clear rounds |
| round-07 | 2 | reopened by State 2 repairs (M17 mutation-policy field, M18 sections, M36 reason code, ProjectOverview availability); M18 empty and duplicate section lists stated as the producer's obligation, not a portal check |
| round-08 | 0 | clear; M18 still needs a second clear round (State 1 open: M18 only) |
| round-09 | 0 | clear on M18 after the trim of 2026-11-06 (M18 sentence on sections shortened, no meaning change) |
| round-10 | 0 | clear (empty sections `answered_later`, repeated ids `answered`); `design_questions.py status --state 1`: closed |
| round-11–12 | 0 | reopened (`context`) by the State 0 zero-balance sentence (below); clear twice; closed |

### State 2 question rounds

Rounds 01–09 (`questions/state2/`, Codex CLI provider) on `02_rules.md`,
blocking 21, 10, 8, 8, 4, 1, 0, 3, 2. Each blocking topic was closed by
repairing the decision to the accepted spec 459ac96c and its code, recorded
under the decision's `Carried changes` (owner 2026-11-06: current service
behaviour accepted; technical decisions delegated). Meaning corrections
against the 2026-07-19 text, all to the accepted spec: A4 exceptions of
R0-09, R0-21, R0-24; A12 an ungranted producer is recorded `unknown_project`
(note `_authorize_project_operation`), `scope_denied` only for a refused
capability; A13 only `snapshot.import` and `staff.login_failed` write
rejected records; A5/A6 the guard reads `status`, grant and assignment
operations read `is_active`; A16 surrounding whitespace is refused, not
stripped. Open after round-09: A6, A8, A31, context. Several repairs wrote
implementation precision (hash parameters, character sets, limiter,
timeouts, headers, fingerprint) into State 2 prose; the coordinator's note
of 2026-11-06 stops that: such values are the accepted Factory ones, to be
carried as State 6/7 texts so the rounds can judge them `answered_later`.

Rounds 10–14 on the trimmed text (commit `ac4bad5f`), blocking 2, 0, 1, 0, 0:
round-10 A9 zero work balance had no label (repaired: `balanced`, Factory
code `domain/financial_policy.py` `calculate_work_balance`, State 1
`WorkBalanceLabel`) and A32 "affects the portal" had no criterion
(repaired: a database-listed vulnerability for the pinned version blocks;
no reachability judgement); round-12 A9 `balanced` against State 0 "shown
as `Completed ahead of payments` or `Unused advance payment`" (State 0
"Derived values" repaired to name balanced at zero; State 0 rounds 10–11
`--since 3a628953` clear, closed). Round-14: `design_questions.py status
--state 2` closed. No mechanism prose was re-expanded: the reviewers'
fingerprint, rounding, hash-profile and Registry-timeout topics came back
`later_state`, `answered_later` or `judged_before`.

Rounds 15–18 (`--since 9c18621c`) reopened A7, A8, A31 on the State 3–4
repairs; after the coordinator's decisions of 2026-11-06 (`f25e808f` import
route pre-checks, Q20; `e8e3831c` expense section check) rounds 19–20 were
clear (blocking 0, 0) and State 2 is closed; States 0 (rounds 15–16) and 1
(rounds 16–17) re-closed on R0-25, M20 and M36 the same way.

### Implementation precision carried to States 6–7 (trim of 2026-11-06)

States 1–2 state what a rule guarantees, not its mechanism (State 1 scope:
no algorithms, orders, encodings, formats or error mappings; the closed
reference case cabinet-kernel carries none in States 1–2). The values the
rounds had written into `01_models.md` and `02_rules.md` were removed and are
the accepted spec's (sha256 `459ac96c…`, Factory
`projects/client_portal_sandbox/specs/base/global_spec.json`) and its code;
State 6 contracts and State 7 notes carry them from these addresses
unchanged (owner 2026-11-06: current service behaviour accepted; technical
decisions delegated).

| topic | removed from | accepted-spec address (459ac96c) | running code |
|---|---|---|---|
| snapshot `content_fingerprint`: covered fields, section ordering key and ties, JSON form, digest | A8, M18 | `rules.idempotency_identities.approved_snapshot`; note `_canonical_snapshot_fingerprint`, `_classify_snapshot_replay` | `application/snapshot_import.py` `_canonical_snapshot_fingerprint` |
| expense `intake_fingerprint` canonicalisation | A8 (shared sentence) | note `_canonical_intake_fingerprint`, `_classify_expense_replay` | `application/expense_intake.py` |
| Registry failure classification order, timeout classes, non-success body, endpoint usability | A6 | `rules.registry_failure_translation`; `config.registry_timeout_seconds`, `config.registry_request_paths`; notes `validate_project_reference`, `get_project_context`, `list_active_projects`, `_translate_registry_failure` | `adapters/registry_gateway.py` |
| answer for an unknown Registry status on a read | A5 | note `_authorize_project_operation`; context model `AuthorizedProjectContext`; `rules.http_router_backend.error_policy.default_status` | `application/authorization_guard.py` |
| snapshot content checks: decoding before authentication, which strings are accepted | A7 | note `_validate_snapshot_publication`, `import_snapshot` | `application/snapshot_import.py` |
| overall progress rounding point | A9 | `rules.money_policy`; note `calculate_overall_progress` | `domain/financial_policy.py` |
| staff email syntax set, whitespace set, casefolding, no IDNA | A16 | `rules.staff_identity_input_policy` (says `strip`; the code refuses, A16 kept the code); note `_normalize_staff_email` | `application/staff_identity.py` `_normalize_staff_email` |
| password control-character set | A16 | `rules.staff_identity_input_policy.credential_allows_control_characters`; note `_validate_new_password` | `application/staff_identity.py` `_validate_new_password` |
| viewer entry limiter: algorithm, window boundary, eviction, single worker, HTTP answer | A25 | `rules.http_transport_policy.limits.viewer_entry`; `config.runtime_environment_variables` (`VIEWER_ENTRY_RATE_LIMIT_*`); note `_record_viewer_entry_attempt` | `runtime/transport_guard.py`; `deploy/Dockerfile.api` |
| security header list, `no-store` routes | A25 | `rules.http_transport_policy`; notes `_apply_security_headers`, `_requires_no_store`; `rules.binary_delivery_policy` | `runtime/transport_guard.py`, `api_irregular.py` `_binary_content_response` |
| password hash profile and rehash behaviour | A30 | `rules.credential_security_backend.password` (`RFC_9106_LOW_MEMORY`); `config.credential_hash_scheme`; notes `hash_password`, `verify_password` | `security/credential_security.py` |
| Registry endpoint value accepted at each call (scheme, host, no user info, path prefix kept) | A30 | note `_registry_url`; `config.registry_endpoint_env_name`, `config.registry_request_paths` | `adapters/registry_gateway.py` `_registry_url` |
| exact dependency pins | A32 | — (deployment file) | `deploy/requirements.txt` |
| how the pre-deploy vulnerability check is run | A32 | — (no Factory tool; the trimmed text had prescribed `pip-audit`, which the service does not have) | — |
| process status after a bootstrap configuration or storage failure (uncaught exception, interpreter status and traceback) | State 5 `run_bootstrap_cli` | note `run_bootstrap_cli`; `rules.staff_bootstrap_policy.command_outcomes` | `cli/staff_bootstrap.py`; `deploy/README.md` (command line) |
| readiness answer body when the store cannot open (outer application without the inner error handlers) | State 5 `create_runtime_app` | notes `create_runtime_app`, `readiness_endpoint` | `runtime/app.py`; `adapters/portal_store.py` `PortalStore.begin` |
| source-supplied times: accepted forms (offsets, precision), their checks, and the point of an operation's one clock read | A28 (round-41) | `rules.clock_policy`; notes of the operations that read the clock (e.g. `authenticate_staff`, `issue_service_credential`) | `application/*.py` `datetime.utcnow()` call sites; `core/models.py` |
| which A30 knobs a deployment can change (the staff session lifetime is a source constant of the running code; no runtime setting carries it) | A30, State 5 `create_runtime_app` | `config.runtime_environment_variables`, `config.staff_session_ttl_hours`; note `authenticate_staff` | `application/staff_identity.py` 141; `runtime/settings.py` |
| trusted hosts, CORS allowlist and public origin: three separate settings, their names, validation and the checks each drives (the public origin only for viewer sign-out) | A25 | `rules.http_transport_policy`; `config.runtime_environment_variables`; note `install_transport_guards` | `runtime/settings.py`; `runtime/transport_guard.py` 109–146 |
| allocation amount precision: an amount with more than two fraction digits is accepted and stored as supplied; the sum is compared after two-digit rounding on correction and re-allocation, unrounded on creation (the case keeps the two-digit money rule, INV-037, of State 0–2; the code does not enforce it on allocations) | State 2 rounds 49–50, State 1 round-34 (A9, M26, R0-05; ping-pong rule) | note `_validate_allocation_sum` ("the quantized sum of instruction amounts"), `_validate_initial_allocations` | `domain/expense_management.py` 77–82; `application/expense_intake.py` 132–145; `adapters/expense_repository.py` 287 |
| non-finite amounts: request-model refusal and the decimal failure of a direct call | State 5 `validate_eur_amount` | `rules.money_policy`; note `validate_eur_amount` | `domain/financial_policy.py`; `core/models.py` `_FrozenModel` |

### Classification of what State 2 carries

The former `spec/20_rules.md` moved into `02_rules.md` line for line (checked
mechanically); `spec/invariant_ledger.json` stays as evidence, and each of its
55 rows is a formal invariant of exactly one decision A1–A21 (checked by the
build). Where each row finally lands (note, property, `30_trace.json`) is
decided in States 3–7.

| finding | evidence | classification | owner |
|---|---|---|---|
| R1–R12, R15–R17 tables | case text = accepted `rules.*` (identical values) | derivable (unchanged) | A1–A12, A15–A17 |
| audit significant actions and reason policy | `5677993e` | accepted spec change | A13 |
| binary delivery from content signature | `babd5e52` | accepted spec change | A14 |
| transaction guard, audit entity id, immutability, transport, exception payload, clock, bootstrap | `0baceacc`, `0f9ae3ae`, `bd561732`, `38626cc7`…`51d19fdf`, `a12937fd`, `c92b6878`, `6011ac93` | accepted spec change | A22–A26, A28, A29 |
| derived view tie-break orders | `d2c4511e` against State 1 text | accepted spec change; was unresolved, answered by the owner decision of 2026-11-06 | A27, Q18 |
| Registry active list: `/projects/active` (State 0) against `projects` with decode-side filter | `300bd11d`, `config.registry_request_paths`; Registry v1 `api/runtime.py` serves both | accepted spec kept (owner 2026-11-06) | A30, State 6 |
| dependency vulnerability policy | `deploy/requirements.txt` pins | was unresolved; decided under the owner decision of 2026-11-06 (technical decisions delegated) | A32, Q17 |
| persistence, router and three backend IRs; `rules.role`, `rules.schema_version` | `8387e0a3`, `d1280708`, `300bd11d`…`a6916180314d` | later deterministic closures | "Carried to later closures" |

### States 3–4 question rounds (closed 2026-11-06)

Closing pass after the coordinator's decisions (`f25e808f`, `e8e3831c`):
States 0–3 closed (State 0 round-23, State 1 round-25, State 2 round-32,
State 3 round-11), State 4 closed by rounds 03–15 (blocking 2, 0, 2, 4, 0,
0, 1, 0, 3, 0, 0, 0, 0). Repairs followed the running code (grant
admission reads `exists` and `is_active`; duplicate active grants refused
by the operation; route guard checks the activation capability; per-call
environment reads of `registry_gateway` and `binary_storage`; expense
replay conflict 409; overview per-part availability) and kept the trimming
rule: race and failure details of the import stay in the State 4 flow, not
in R0-25. State 5 rounds 01–03 (blocking 32, 8, 6): the operation texts were
repaired from the running code; State 5 stopped on six topics where the
running code contradicted a closed earlier state. **Decided by the
coordinator 2026-11-06** (owner 2026-11-06: current service behaviour
accepted; technical decisions delegated): follow the code in all six, each
by the narrowest edit of the earlier state (R0-24 and invariant 5, A28, the
`flow:staff_session_lifecycle` login step, `api` Knows, R0-09/A25, R0-07/A29).
The six topics were:

- archived project: `project_tracking.list_project_progress` (a read) creates
  the empty manual budget version and its audit through
  `ensure_manual_budget`, also for an archived project
  (`domain/project_tracking.py` 50–58, `domain/budget_management.py`
  170–217), against R0-24 "refuses every mutation of its budget";
- audit time: `audit_writer.append_audit` reads its own clock for
  `occurred_at` (`application/audit_writer.py` 136), against A28 "each
  operation reads the clock once";
- malformed login email: `IdentityInputRejected` before any audit
  (`application/staff_identity.py` 108), against `flow:staff_session_lifecycle`
  "on every rejection it appends `staff.login_failed`";
- `api` imports the seven viewer endpoints of `api_irregular`
  (`api/router.py` 22), which the accepted `imports.module_internal` and
  State 3 `api` Knows do not list;
- viewer entry has no origin check (`runtime/transport_guard.py` 136–146),
  against R0-09/A25 "mutating viewer requests … public origin";
- the bootstrap command prints and returns the normalized email
  (`cli/staff_bootstrap.py` 33, `application/staff_bootstrap.py` 88–96),
  against A29 "never written to output … return values".

Closing pass of 2026-11-06 (`--since 0ca1488f9c99`), after the allocation
decision: State 1 rounds 30–38 (blocking 2, 1, 0, 0, 1, 0, 0, 0, 0), State 2
rounds 49–58 (1, 4, 2, 0, 1, 2, 0, 1, 0, 0), State 3 rounds 18–19 and State 4
rounds 18–19 (0, 0), State 5 rounds 05–09 (5, 2, 1, 0, 0); State 0 stayed
closed (its text is unchanged). All of States 0–5 are closed.

#### Accepted service quirks (candidates for a later Factory change, not migration scope)

| quirk | running code | case text |
|---|---|---|
| reading the progress of a project without a budget creates its empty manual budget version and `budget.manual_version_create` audit, also for an archived project | `domain/project_tracking.py` 50–60 (`ensure_manual_budget`), `domain/budget_management.py` 170–217 | R0-24 named exception; invariant 5 |
| the audit record's `occurred_at` is read by the audit writer at append time, not taken from the operation's one instant | `application/audit_writer.py` 136 | A28 exception |
| a service credential's `expires_at` is stored as supplied; an offset-aware value is not converted, and comparing it with the offset-naive clock fails the later authentication as a server error | `application/service_identity.py` 19, 301; `adapters/service_identity_repository.py` 81, 217 | A28 source-supplied list; State 5 `issue_service_credential`; the offset-aware case is carried to States 6–7 (note `issue_service_credential`, `_credential_is_usable` of 459ac96c) |
| the A30 values without an `_env_name` (staff session 12 hours, viewer session 30 days, the other TTLs and limits, credential entropy 32 bytes) are source constants of the use cases; no deployment setting reaches them, against A30 "deployment values may differ" | `application/staff_identity.py` 140–141; `application/viewer_access.py` 117–119, 192; `application/service_identity.py` 292; `runtime/app.py` (settings to the store and transport guard only) | State 5 `create_runtime_app` named exception |
| **HIGH priority.** Zero and negative allocation amounts are accepted on expense creation, correction and re-allocation as long as the allocations sum to the total (a correction to a zero total with one zero allocation included); a later Factory change should require each allocation `amount > 0` (and two fraction digits: amounts are stored as supplied) | `core/models.py` 798–801 (`AllocationInstruction.amount` unbounded); `domain/expense_management.py` 77–82; `application/expense_intake.py` 132–145 | State 1 M26, M27, M29; State 5 `correct_expense`, `replace_expense_allocations` |
| modules import private helpers of other modules: `api` uses `api_irregular._binary_content_response`; `staff_bootstrap` uses `staff_identity._normalize_staff_email` and `_validate_new_password`; `staff_challenges` uses `staff_identity._normalize_staff_email` (and imports `_validate_new_password` without calling it); a later Factory cleanup should make them public or move them to a shared module | `api/router.py` 22; `application/staff_bootstrap.py` 6, 17–18; `application/staff_challenges.py` 9, 91 | `global_spec.json` `imports.internal` (exports carried from the assembly, see the inconsistency of 459ac96c below); `65_imports.json` |

State 5 round-04 found one more contradiction with a closed earlier
state: State 1 M26 and M27 required each allocation `amount` to be greater
than zero, while the accepted spec 459ac96c has no such rule and the running
code checks only a non-empty list and the sum (`domain/expense_management.py`
77–82, `application/expense_intake.py` 132–145; `AllocationInstruction` in
`core/models.py` 798–801 has no bound). **Decided by the coordinator
2026-11-06** (owner 2026-11-06: current service behaviour accepted;
technical decisions delegated): follow the code; M26, M27 and M29 drop
`> 0`, and the zero-total correction of State 5 `correct_expense` is
satisfiable by a zero allocation. Listed above as a HIGH-priority quirk.

#### Factory-internal inconsistency: the `api` → `api_irregular` import

The accepted `imports.module_internal` of 459ac96c does not list `api` →
`api_irregular`, while the accepted router code imports the seven viewer
endpoints and `_binary_content_response` from it (`api/router.py` 22). The
case follows the code (State 3 `api` Knows); the accepted import table is
corrected by a later Factory change, not by the migration.

History of the in-progress pass:

State 3 rounds 01–05 (blocking 6, 5, 1, 0, 0) closed State 3 at `cded5541`;
repairs (commits `1f338005`, `a5e9eeef`, `9c18621c`) reconciled ownership
wording to 459ac96c and its code and reopened States 0–2 for the touched
units, which were re-closed by their own rounds (`--since cd7d465c`). The
State 4 round-01 repairs (`48cecaa2`) reopened State 2 (A7, A8) and State 3
(`portal_store`); round-02 of State 4 and the re-asks (State 2 round-18,
State 3 round-06) left these blocking topics:

- A8 photo replay: which fields compare and against which baseline —
  repaired in the A8 row (kept fields against the photo as now stored,
  `domain/photo_management.py` `_classify_photo_replay`); to be re-asked.
- viewer grant Registry outcome and the use-case context convention —
  repaired in `40_flows.md`; to be re-asked.
- Import route pre-checks — **decided by the coordinator 2026-11-06** (owner:
  current service behaviour accepted; technical decisions delegated): the
  running route (Factory code `api/router.py` `publish_snapshot_endpoint`,
  lines 311–312; accepted `rules.http_router_backend`) calls
  `authorize_producer_scope` (answer unused) and `authorize_snapshot_import`
  before `import_snapshot`; a scope, unknown or archived refusal raises there
  and records nothing. That is the norm: R0-25, M20, M36, A7, A12, A13,
  `flow:import_estimate_snapshot` (the route, not `authorization_guard`,
  calls `service_identity.authorize_producer_scope`) and
  `public_op:snapshot_import.import_snapshot` are rewritten to it. Recording
  access-refused attempts is the missing feature Q20.
- Expense section check — **decided by the coordinator 2026-11-06**: expense
  intake validates allocation sections through the section repository it
  reads (`application/expense_intake.py` `_validate_initial_allocations`),
  not through `budget_management.validate_project_section`; State 4 flow,
  its plan and the State 5 flow evidence of that operation changed together.

#### Factory-internal inconsistency of 459ac96c

The accepted notes of `import_snapshot` ("archived, unknown/scoped … MUST each
append exactly one fresh immutable SnapshotImportRecord"; `ArchivedProjectRejected`
→ `ARCHIVED_PROJECT`, `ScopedNotFoundError` → `UNKNOWN_PROJECT`,
`AuthorizationRejected` → `SCOPE_DENIED`; code
`application/snapshot_import.py` lines 155–164) promise records that the
accepted route table prevents: `rules.http_router_backend` route
`publish_snapshot_endpoint` authorizes with `authorize_producer_scope` and
`authorize_snapshot_import` before its delegate (`api/router.py` 311–312).
Those notes are reachable only when access changes between the two checks.
The case follows the route; the inconsistency is resolved when Q20 is
designed, not in the migration.

The accepted import table of 459ac96c also disagrees with itself and with
the code on three exports. Its `imports.module_internal.staff_bootstrap`
lists `staff_identity: [_normalize_staff_email, _validate_new_password]` and
its `imports.internal.api_irregular` already exports underscore names
(`_viewer_cookie`, `_viewer_session_view`), but `imports.internal` omits
`api_irregular._binary_content_response` and
`staff_identity._normalize_staff_email`, `_validate_new_password` from their
providers' exports, while the code imports them (`api/router.py` 22,
`application/staff_bootstrap.py` 6, `application/staff_challenges.py` 9).
Exports are carried from the assembly (no design artifact authors them; the
projector reads `imports.internal` from `global_spec.json`), so the case's
`global_spec.json` adds these three names to `imports.internal` and is no
longer byte-for-byte 459ac96c there; nothing else differs.
`imports.module_internal.staff_challenges` of 459ac96c lists
`_validate_new_password`, which the code imports but never calls; the case
keeps the accepted list. Listed under the accepted service quirks.

### Classification of what State 3 carries

The former `spec/30_modules.md` is replaced by `30_modules.md` and
`30_trace.json`; its module texts are carried module by module, and the
module list, the public functions and the module imports are those of the
accepted spec (`module_order`, `module_functions`,
`imports.module_internal`).

| finding | evidence | classification | owner |
|---|---|---|---|
| 20 former modules | former text = accepted `module_order` members | derivable (kept, texts carried) | `30_modules.md` |
| eleven `*_repository` modules, narrow ports instead of one facade | `af686d7364d2` … `62c73965adb8`, `ced617bd55c9` … `88c1dbbcc3a6`; the former text allowed ports once `kind: interface` materialized | accepted spec change | `30_modules.md` |
| `staff_challenges` split from `staff_identity` | `f12197b46a82` | accepted spec change | `30_modules.md` |
| `api_irregular`, `transport_guard`, `runtime_settings`, `runtime` | `f42548473a1a`, `babd5e5262d9`, `38626cc7be12`, `21658368525f` | accepted spec change | `30_modules.md` |
| `staff_bootstrap`, `staff_bootstrap_store`, `staff_bootstrap_cli` | `6011ac93b143` | accepted spec change | `30_modules.md`, A29 |
| renamed and reshaped capabilities | accepted `module_functions` | accepted spec change | `30_modules.md` "Changes against the former text" |
| token-free notices (A10, A11, former `send_staff_security_notice`) have no sender | accepted spec has no sending function; Factory code uses the members only in `core/models.py` | running service kept (owner 2026-11-06); possible missing feature | `30_modules.md`, Q19 |
| A22, A26, A28 have no single owning module | the rule appears in the notes of many modules, no shared mechanism | `cross_cutting` disposition | `30_trace.json` |

### Classification of what State 4 carries

The former `spec/40_flows.md` (flows F1–F9) is replaced by `40_flows.md` and
`40_flow_plan.json` (15 flows); the former file is deleted. Each flow walks
the accepted routes of `rules.http_router_backend`, the guard order
`rules.project_guard_sequence` and the notes of the operations it names.

| finding | evidence | classification | owner |
|---|---|---|---|
| F1 login and guarded mutation, F3 viewer entry, F4 import, F6 expenses, F7 binaries, F8 overview, F9 audit | former text = accepted operations of the same modules | derivable (kept, reshaped into flows and conventions) | `40_flows.md` |
| F2 email challenges | accepted `staff_challenges` notes "remain inert while StaffChallengeRepository is deferred"; Factory code `application/staff_challenges.py` | running service kept (R0-23); missing feature Q19 | `flow:deferred_staff_challenges` |
| viewer list leaves out a project without context instead of failing | Factory `00ac72f18d9c`, note `list_viewer_projects` | accepted spec change | `flow:viewer_reads_projects` |
| import rejections recorded in the one import transaction, fresh `import_id` per classified attempt | notes `import_snapshot`, `_build_import_record` | accepted spec change | `flow:import_estimate_snapshot`, R0-25 |
| access refusals answered by the import route before the import, unrecorded | `rules.http_router_backend` route `publish_snapshot_endpoint`; Factory code `api/router.py` 311–312 | running service kept (coordinator 2026-11-06); recording them is missing feature Q20 | `flow:import_estimate_snapshot`, R0-25 |
| activation refused while allocations would lose their section | note `activate_budget_version` (conflict before any update) | accepted spec change | `flow:maintain_and_activate_budget` |
| no snapshot-to-candidate-version operation | Q11 | missing feature, deferred | `40_flows.md` "Deferred features" |
| per-part availability of the overview | Factory `d2c4511ea119` | accepted spec change | `flow:build_project_overview` |
| service start and health, bootstrap, staff and principal administration, progress/payments/photos, staff binary reads | `38626cc7be12`, `21658368525f`, `6011ac93b143`, `3080ef0dbe73`, `fae77f993e03` | accepted spec change (flows added) | `40_flow_plan.json` |

### Classification of what State 5 carries

The former `spec/50_public_apis.md` (per-module operation tables, a route
catalog and an `imports.internal` draft) is replaced by `50_public_apis.md`,
`50_api_plan.json` and `50_exposure_plan.json`; the former file is deleted.
One operation per State 3 capability (108). Each operation's callers are the
modules importing it in the accepted `imports.module_internal` (checked
mechanically on 2026-11-06), or a `boundary:` when none does; its outputs,
effects and errors are the accepted contracts and notes. An operation is
`external` exactly when a route of `rules.http_router_backend` reaches it:
the delegate of each of the 49 table routes and the handler of each of the 7
`api_irregular` routes (56); the other 52 are `internal-only`.

| finding | evidence | classification | owner |
|---|---|---|---|
| former operations of the 20 original modules | former text = accepted `module_functions` of the same names | derivable (kept, reshaped into one section each) | `50_public_apis.md` |
| eleven schema functions, bootstrap, transport, settings, runtime, viewer cookie endpoints | `af686d7364d2` … `6011ac93b143`, `35a0a09ccbb1`, `38626cc7be12` | accepted spec change (operations added) | `50_public_apis.md` |
| schema creation and the uncalled email gateway were in no State 4 flow | notes `PortalStore.begin`, `SqliteStaffBootstrapStore.create_if_empty`; `staff_challenges` imports `deliver_email_message` | form only: the flows now name the capabilities (State 4 repaired, behaviour unchanged) | `40_flows.md` |
| challenge operations inert; staff onboarding by activation | notes of `staff_challenges`, `change_staff_status` | running service kept (R0-19, R0-23); missing feature Q19 | `50_public_apis.md` |
| safe views as outputs (`StaffAccountView`, `SessionRevocationResult`, `ExpenseOperationOutcome`, `PhotoMutationResult`) | `9eab4d948181`, `d1280708714f` | accepted spec change | `50_public_apis.md` |
| a viewer grant for an unknown or inactive project answers `RegistryBoundaryError`; staff and producer grants answer `ScopedNotFoundError` or `ArchivedProjectRejected` | Factory code `application/viewer_access.py`, `application/service_identity.py`, `application/staff_identity.py`; notes of the three grant operations | running service kept (owner 2026-11-06) | `public_op:viewer_access.grant_viewer_project` |
| a missing or invisible photo answers `PhotoValidationError` (422) and an unreadable one `BinaryStorageError`; a document folds all three into `BinaryAccessRejected` | notes `_authorize_photo_reference`, `read_expense_document`; Factory code `domain/photo_management.py` | running service kept (owner 2026-11-06) | `public_op:photo_management.read_progress_photo` |
| a malformed login address answers `IdentityInputRejected` before any audit | Factory code `application/staff_identity.py` `authenticate_staff` | running service kept (owner 2026-11-06); discloses no account | `public_op:staff_identity.authenticate_staff` |
| former error families `DomainValidationRejected`, `DomainConflict` | accepted `error_policy` | accepted spec change (closed exception set) | `50_public_apis.md` conventions |

### State 7 coordinator decisions (2026-11-06)

Decided by the coordinator 2026-11-06 (owner 2026-11-06: current service
behaviour accepted; technical decisions delegated), before the State 7 notes
are written.

| topic | evidence | decision |
|---|---|---|
| time source of the operations (revised 2026-11-06, replaces the clock-policy address) | the accepted contracts (459ac96c) have no clock port; the running modules read the time with `datetime.utcnow()` (`application/*.py` call sites); SPEC_STANDARD §15.3.1 (rev 2) and the Factory resolver refuse `= rules.clock_policy.*` in a note (`rules_address_outside_backend_ir`) | the contracts stay unchanged and no clock backend (§6.9) is added; a note that needs the current time states the behaviour: the operation reads the current UTC time once and uses that single instant for every timestamp it writes and every current-time comparison it makes |
| addresses in notes | SPEC_STANDARD §15.3.1 (rev 2); Factory `resolve_data_address` refuses every non-backend `= rules.*` and every non-persistence `= config.*`, even where the Workbench gate and `check_note_draft` pass them | a note carries only addresses of registered deterministic backend IR and `config.persistence.*_table_name` / `storage_schema_revision`, each checked with the Factory resolver; the 186 carried notes with another address are rewritten: a behaviour rule in words (154), a closed value by its model symbol (5: `AuditAction`, `Capability`, `RegistryFailureKind`, `StaffRole`/`StaffStatus`/`ActorKind`/`AuditEntityKind`/`AuditResult` members), a literal without a models home first left out (27 notes); revised below: the value is written back in plain words |
| module- and class-level notes | the gate knows only `module:<name>` tokens of `30_modules.md` (closed at State 3) and no class scope | moved onto the callables they constrain, repeated per callable; the gate behaviour is reported to the coordinator as a tool/document discrepancy (SPEC_STANDARD §2 allows `module_name:`) |
| `design_closure_gaps.py` `fresh_timestamp_without_source` (36) and `ambient_time_note` (4 after the State 7 notes) | report-only fuse; the time source is the operation's own UTC read stated as behaviour, not a contract parameter | accepted, report-only; no contract or model change |
| `design_closure_gaps.py` `orphan_read_entity` (17: `BinaryPayload`, `BudgetActivationResult`, `ChallengeIssueView`, `ClientViewerView`, `DocumentMutationResult`, `ExpenseMutationResult`, `PhotoMutationResult`, `PresentedSecret`, `ProjectOverview`, `ServiceCredentialIssueResponse`, `ServicePrincipalView`, `SessionRevocationResult`, `StaffAccountView`, `StaffSessionGrant`, `ViewerCredentialIssueResponse`, `ViewerSessionGrant`, `WorkBalanceResult`) | result and view models built by the operations that return them (accepted contracts and notes of 459ac96c) | accepted, report-only; the State 7 notes of the returning operations state the construction |

If the State 7 gate itself blocks on either class, the notes stop and the
finding goes back to the coordinator.

#### Deviation from 459ac96c: parameterless exception constructors (coordinator, 2026-11-07)

| topic | evidence | decision |
|---|---|---|
| `X.__init__(self) -> None` of module-local exceptions in model-generated modules (State 7 rounds 01–03: financial_policy, staff_bootstrap, staff_challenges ×2, project_tracking ×2, photo_management) | owner 2026-11-07: the Factory prompt is not changed; it renders every module-local exception as `class X(Exception): pass`. The running constructors only call `super().__init__()` or `super().__init__("<fixed text>")`; no live code reads the message (`str(exc)`, `.args`, logging): `api/router.py` `_domain_error_response` answers by type with a body-less status, `cli/staff_bootstrap.py` prints its own fixed lines, and no `raise` passes an argument. A26 (`02_rules.md`): an exception message is never a data channel | the 18 contracts are left out of `60_contracts.json` / `60_contract_plan.json` with their 18 notes and imports scopes: `ArchivedProjectRejected`, `AuthorizationRejected`, `ScopedNotFoundError` (authorization_guard), `ChallengeRejected`, `ChallengeRateLimited` (staff_challenges), `IdentityInputRejected` (staff_identity), `BudgetValidationError`, `BudgetConflictError` (budget_management), `ExpenseValidationError`, `ExpenseConflictError`, `BinaryAccessRejected` (expense_management), `TrackingValidationError`, `TrackingConflictError` (project_tracking), `PhotoValidationError`, `PhotoConflictError` (photo_management), `FinancialValidationError` (financial_policy), `EmailDeliveryError` (email_delivery_gateway), `BootstrapAlreadyCompleted` (staff_bootstrap). Their ownership is `60_exception_taxonomy.json`, whose `meaning` keeps each former contract purpose verbatim; the "carries no detail" properties now hold by the `pass` body and argument-free raises, no longer by a contract or note in the generation prompt. Reverses 387a854a (`__init__` defined in the class) |
| kept constructor contracts | `conceal_authentication_failure() -> AuthenticationRejected`: the Factory validator accepts a signature type only as a module-owned class with a contract; `PersistenceError.__init__` is fixed by the sqlite unit-of-work emitter (`ERROR_CONTRACTS`); `BinaryStorageError` (binary_storage) is not model-generated; `RegistryBoundaryError(kind)` and `SnapshotContentRejected(reason)` carry the A26 fields | unchanged. `AuthenticationRejected` (authorization_guard) and `RegistryBoundaryError` (registry_gateway) keep a prompt where OWNED CLASSES requires `__init__` while MODULE-LOCAL EXCEPTION EXPORTS shows `pass`; no round has raised it |
| semantic diff against 459ac96c | the change removes 18 contracts and 18 notes and adds one sentence to the `bootstrap_first_administrator` [VALIDATION_ERROR] note (the class is this module's own, a plain `pass` subclass raised without arguments) | expected differences of the later semantic diff; behaviour of the running service unchanged |

#### `connection: object` in the model-written repository (coordinator, 2026-11-07)

| topic | evidence | decision |
|---|---|---|
| `connection: object` of `create_budget_schema` and `SqliteBudgetRepository.__init__` (round-02 budget_repository:T1) | budget_repository is the one repository with `emission: irregular` (`70_persistence_closure.json`), so the Factory leaves it to the model; the unit-of-work emitter fixes `<Repository>.__init__` as `(self, connection: object, context: …)` (`REPOSITORY_INIT`) and calls the schema function with its connection; the prompt line "annotate each parameter with the type its CONTRACTS signature declares, never object or nothing" is deliberate (owner 2026-11-07); running code `adapters/budget_repository.py:9,62` keeps `object` and uses only `cursor()` | signatures unchanged; one [DEPENDENCY_BOUNDARY] note per callable states that `object` is the declared type, fixed by the backend, and how the connection is used. Not a deviation from 459ac96c beyond the two added notes |

#### Values in notes restored (coordinator, 2026-11-06)

| topic | evidence | decision |
|---|---|---|
| literals left out of the notes | non-backend `rules.*` and non-persistence `config.*` never reach the generating model (§15.3.1); a note that states the behaviour without the value makes Route B guess, and the regenerated service would differ from the accepted one | the value is written back in plain words exactly as 459ac96c `rules`/`config` and its notes hold it, cross-checked with the code at the lines of the table below; 30 notes of the 26 consuming callables (the table rows 1–16; members of `AuditAction` and `Capability` by their model symbol); `design_notes --gate` stays 0 blocks |
| notes lint L2/L3 on the restored values | `design_notes_lint.py`: +10 L2 `literal_with_home` (the numbers 0, 1, 5, 12, 30 coincide with other declared config values) and +19 L3 `uncovered_data_signal` (2, 3, 128, the Registry and auth paths); L2–L5 run only in the notes-authoring acceptance environment, not in Factory admission v2; 459ac96c itself carries 150 such findings | accepted like those of 459ac96c, report-only; they close with the data-provider upgrade below |

### State 7 data-provider upgrade (deferred follow-up, after migration)

Decided by the coordinator 2026-11-06: not part of this migration. A data
provider (§6.10, `data_provider_backend`, `70_data_provider_closure.json`)
adds a module, row models and constants and would reopen States 1, 3 and 6:
a standard upgrade, not the reproduction of the service. The literal values
below (accepted code, Factory `23a17dc84205`) have no models home and no
address legal in a note (§15.3.1); until the upgrade the notes of the
consuming callables carry each value in plain words (above).

| # | leaf (accepted spec) | value | consumers (module.callable) | code |
|---|---|---|---|---|
| 1 | `rules.money_policy.currency` | `EUR` | financial_policy.validate_eur_amount; expense_management.correct_expense; project_tracking.register_work_payment; snapshot_import._validate_snapshot_publication | `application/snapshot_import.py:101`, `domain/budget_management.py:250` |
| 2 | `rules.money_policy.fraction_digits`, `.rounding` | `2`, `ROUND_HALF_UP` | financial_policy._quantize_money, validate_eur_amount, calculate_completed_work, calculate_work_balance; project_tracking.register_work_payment | `domain/financial_policy.py:14` |
| 3 | `rules.staff_identity_input_policy.credential_min_codepoints`, `.credential_max_codepoints` | `12`, `128` | staff_identity._validate_new_password | `application/staff_identity.py:47` |
| 4 | `rules.status_transitions.staff`, `.principal` | transition tables | staff_identity.change_staff_status; service_identity.change_service_principal_status | `application/staff_identity.py:242`, `application/service_identity.py:99` |
| 5 | `rules.principal_capability_sets` | capability sets per principal kind (members of `Capability`) | authorization_guard._require_capability, authorize_access_management | `application/authorization_guard.py:135-146` |
| 6 | `rules.audit_significant_mutation_actions` | subset of `AuditAction` | audit_writer._validate_audit_intent | `application/audit_writer.py:75` |
| 7 | `config.registry_endpoint_env_name` | `REGISTRY_BASE_URL` | registry_gateway._registry_url, validate_project_reference, get_project_context, list_active_projects | `adapters/registry_gateway.py:22` |
| 8 | `config.registry_timeout_seconds` | `5` | registry_gateway.validate_project_reference, get_project_context, list_active_projects | `adapters/registry_gateway.py:73,103,139` |
| 9 | `config.registry_request_paths` | `projects`, `projects/{project_id}/validate`, `projects/{project_id}/context` | the three registry_gateway operations | `adapters/registry_gateway.py:68,99,135` |
| 10 | `rules.supported_external_contract_versions.ocr`, `.snapshot` | `[1]`, `[1]` | expense_intake.create_expense_from_recognition; snapshot_import._validate_snapshot_publication | `application/expense_intake.py:170`, `application/snapshot_import.py:99` |
| 11 | `config.staff_session_ttl_hours` | `12` | staff_identity.authenticate_staff | `application/staff_identity.py:141` |
| 12 | `config.viewer_session_ttl_days` | `30` | viewer_access.enter_viewer_access | `application/viewer_access.py:117` |
| 13 | `rules.binary_delivery_policy.response.content_disposition` | `expense_document` → `attachment`, `progress_photo` → `inline` | api.staff_read_expense_document_endpoint, staff_read_progress_photo_endpoint; api_irregular.viewer_read_expense_document_endpoint, viewer_read_progress_photo_endpoint | `api_irregular.py:131,139` |
| 14 | `rules.http_transport_policy.security_headers` | header values | transport_guard._apply_security_headers; api_irregular.viewer_restore_session_endpoint | `runtime/transport_guard.py:17-19` |
| 15 | no-store path set and viewer entry / logout paths (`rules.http_router_backend.routes`, `rules.http_transport_policy.browser_session.logout_path`) | seven canonical paths | transport_guard._requires_no_store, install_transport_guards | `runtime/transport_guard.py:90-98` |
| 16 | `rules.staff_bootstrap_policy.command_outcomes` | exit codes `0`-`3` | staff_bootstrap_cli.run_bootstrap_cli | `cli/staff_bootstrap.py:19,28,31,34` |

Not requests: the runtime environment variable table (`config.runtime_environment_variables`)
is lowered by the settings module emitter (`runtime/settings.py`, generated from
the settings data, §6.11), so `load_runtime_settings` names the table in words.
The carried prose of 459ac96c still holds literals the notes lint (L2/L3) flags
(HTTP status codes in service_identity and staff_identity notes, health paths
and the `/api` prefix in runtime, user-facing message texts in
authorization_guard and service_identity, default ports in `_normalized_origin`,
the session secret entropy in `authenticate_staff`); they are carried unchanged
and belong to the same data-provider work.

### Factory rules added after the accepted spec

The accepted spec predates the Factory rule `missing_implementation_disposition`
(`code_factory/tools/implementation_obligations.py` `validate`, added
2026-10-10): every `kind: interface` used in a parameter type of another
contract needs a row in the top-level `implementation_obligations` section
(SPEC_STANDARD §5.1). The accepted spec has no such section, so it fails the
current normalizer on six interfaces. No design artifact owns the section; it
is written into `global_spec.json`, and the projection preserves it
(`tools/SPEC_PROJECTION_WORKBENCH.md`).

Rows written (2026-11-06), each the concrete class the running code hands to
the consumer (Factory code `projects/client_portal_sandbox`):

| interface | disposition | implementation | code |
|---|---|---|---|
| `AuditRepository` | local | `SqliteAuditRepository` | `adapters/audit_repository.py:27`; `PortalTransaction.audit` returns it (`adapters/portal_store.py:59,81`) |
| `StaffAccessRepository` | local | `SqliteStaffAccessRepository` | `adapters/staff_access_repository.py:53`; `adapters/portal_store.py:67,547` |
| `ViewerAccessRepository` | local | `SqliteViewerAccessRepository` | `adapters/viewer_access_repository.py:63`; `adapters/portal_store.py:68,674` |
| `ServiceIdentityRepository` | local | `SqliteServiceIdentityRepository` | `adapters/service_identity_repository.py:56`; `adapters/portal_store.py:69,539` |

Each of the four modules is selected by the Factory `repository` emitter, so the
generation-closure rule `local_implementation_requires_deterministic_backend`
passes for them.

Rows added once the unit-of-work emitter existed (2026-11-06):

| interface | disposition | implementation | code |
|---|---|---|---|
| `AuditRepositoryContext` | local | `PortalTransaction`, `SqliteStaffBootstrapStore` | `adapters/portal_store.py:55` (passed as `self` to every repository at 59–69); `adapters/staff_bootstrap_store.py:12` (passed as `self` at 39–40) |
| `StaffBootstrapPort` | local | `SqliteStaffBootstrapStore` | `adapters/staff_bootstrap_store.py:12`; created by the bootstrap command `cli/staff_bootstrap.py:22` |

They were held earlier because no Factory emitter selected `portal_store` or
`staff_bootstrap_store` (`local_implementation_requires_deterministic_backend`).
The Factory emitter `python_sqlite_unit_of_work_v1` (Factory PR #181, added
2026-11-06; Workbench registration and SPEC_STANDARD §6.12
`sqlite_unit_of_work_backend/v1`, Workbench PR #146) now owns both modules. The
case declares it in `70_sqlite_unit_of_work_closure.json`; the projection
carries the IR into `rules.sqlite_unit_of_work_backend`. The IR is the running
code's shape: store `PortalStore`, transaction `PortalTransaction`, error
`PersistenceError` in `portal_store`; eleven accessors in the order
`PortalStore.begin` creates schemas and builds repositories; bootstrap store
`SqliteStaffBootstrapStore.create_if_empty` in `staff_bootstrap_store`, guarded
by the staff account table, writing the account then the audit record.

The twelve challenge methods of `PortalTransaction` (`get_`, `insert_`,
`list_`, `update_` for email changes, email verifications and password resets)
are declared `unbacked_methods`: in the running code they raise
`PersistenceError` (`adapters/portal_store.py:131–594`), because no challenge
repository exists — the deferral of `00_product.md` R0-23 and
`open_questions.md` Q19.

Consequence at the next Route B: the emitted repositories inherit their port
interfaces (`class SqliteAuditRepository(AuditRepository)`, where the running
`adapters/audit_repository.py:27` declares no base). This is a code-shape change
with no behaviour change.

Checks after the change: `design_emitter_binding.py --coverage` with the
Factory root unbound 0; `design_factory_slices.py` ready; admission FA010
(obligations cover every interface-typed dependency), FA017 (every lowered
repository is reachable) and FA005 (Factory validator) pass.
