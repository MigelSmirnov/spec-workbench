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

