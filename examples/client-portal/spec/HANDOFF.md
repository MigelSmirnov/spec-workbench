# Handoff — Client Portal (current)

Replaces the handoff of 2026-11-07. State of `agent/client-portal` on
2026-11-08 at `3876e1bc` (plus this handoff), checked against the Factory
checkout `code_factory_cp_witnesses` at origin/main `5a3bdec2`; the assembly
result is `80_assembly.md`.

## Where the case stands

- Owner decision 2026-11-08 on A9/INV-044 is in the design (below).
- Assembly ready: 15/15 checks, 0 errors. Imports closure ready (195/195
  scopes, 0 stale, strict). `global_spec.json` equals its projection.
- Witness judgement (Workbench #156-#158) ran: 68 bindings, 16 asserts,
  52 partial, 0 does_not, 0 not_checked (below).
- Only State 2 rounds were run (coordinator, 2026-11-08: the other states'
  rounds still read the full texts and are to be cut down first). State 2
  is open: three blocking rounds (79-81), stopped by the ping-pong rule;
  17 units open, all on the coverage gaps below. Its transition is not
  ready (`witness_material`: 52 partial).
- Reopened and not asked: State 1 (`Projections and answers`: one clear
  review of the two it needs), States 3 and 4 (`context`, earlier-layer
  text changed), State 5 (`build_budget_view`, `build_progress_view`,
  `context`), State 7 (`financial_policy`, `derived_views`). State 0 is
  closed. `tools/authoring.py next client-portal` stops at
  `state2_rules_decisions`.
- Stage 8.1 ledger and Factory admission were not run this pass
  (coordinator). FA019 (State 2 rounds) and FA002 (no ledger) still block
  as on 2026-11-07; FA015 unchanged.

## INV-044: missing data must not look like zero (owner, 2026-11-08)

"«Нет данных» не должно выглядеть как ноль". A section without a progress
record now has `completed_work_value = None` (was `Decimal` 0, while its
percent was already `None`), and is left out of `completed_work_total`, as
it is left out of overall progress. `completed_work_total` stays `Decimal`:
the work balance subtracts payments from it. Layers: State 1
`BudgetSectionView`, `ProgressSectionView` (`Decimal | None`), M32, overall
progress over sections with a recorded progress; State 2 A9 (rule, carried
change, INV-044 text, its witness item); State 5 outputs of
`build_budget_view`, `build_progress_view`; State 6
`60_model_closure_contracts.json`; State 7 notes `build_progress_view`
[RETURN_SHAPE], `_project_budget_sections` and `_project_progress`
[FIELD_ASSIGNMENT]; `global_spec.json` by projection and note propagation.
`SOURCE.md` records the deviation from 459ac96c.

**Known code/spec difference:** the running service still returns 0.00
for such a section (Factory `application/derived_views.py`). It changes
only with a future Route B regenerating `derived_views`; no export, Route B
or deploy was done.

**Remaining item, Factory (separate Factory PR, coordinator):**
`budget_derivation_client_portal` records the section's
`completed_work_value` without asserting it; its verdict for INV-044 is
`partial` ("It does not assert that completed_work_value is None when
progress is missing"). The check must assert `None`. A9's binding is kept.

## Witness verdicts (`design_questions.py judge-checks`)

Nine Required tests items named several checks for different invariants in
one item; by the protocol each tag then binds all invariants of the item.
They were split one item per tag group (A4, A8, A9, A11, A13, A16, A18,
A19, A30). That narrows no invariant: it removes claims the items never
meant (e.g. that the photo check asserts INV-009). Before the split 53 of 68
were partial; after it 51, then 52 on the final texts.

Asserts (16): A1 `authorization_guard`; A4, A15 `registry_linkage`; A8
`snapshot_import_sqlite_uow` (INV-021), `expense_intake_uow` (INV-030);
A11 `end_to_end_walkthrough` (INV-005), `viewer_credential_reissue`
(INV-008); A19 `expense_management_uow` (INV-033); A20
`progress_manual_value`; A21 `budget_derivation` (INV-050); A22
`staff_identity_uow`; A23 `staff_bootstrap`; A29 `staff_bootstrap_store`,
`staff_bootstrap_cli`; A31 `workbench:state2_rules_decisions`; A32
`dependency_pins` (DEP-001). (Check names without the `_client_portal`
suffix.)

Partial (52) — each a real finding: the check asserts less than the
invariant it is bound to. Owner of each: the Factory check (extend it), or
the owner of the decision (narrow the invariant), never a narrowed binding
text. The State 2 round raises each as a blocking `consequential_gap`.

| decision | check | binds | what it does not assert |
|---|---|---|---|
| A2 | `authorization_guard_client_portal` | INV-007 | It does not attempt viewer access management or comprehensively assert that every viewer capability is read-only. |
| A3 | `staff_identity_uow_client_portal` | INV-014 | It does not attempt authentication after the account is changed to disabled, so the full active-only rule is not asserted. |
| A4 | `authorization_guard_client_portal` | INV-001, INV-017, PLAT-REG-003 | It does not fully prove first-failure ordering, uniqueness of active staff assignments, or reject a Registry validation result whose returned UUID differs from the requested UUID. |
| A4 | `staff_identity_uow_client_portal` | INV-004 | The check does not compare exception payloads or responses for indistinguishability and does not assert that authentication failures expose no project data. |
| A5 | `authorization_guard_client_portal` | PLAT-REG-006 | It does not assert absence of a stored Registry snapshot or that live context is fetched afresh rather than treated as cached current truth. |
| A5 | `derived_views_uow_client_portal` | PLAT-REG-006 | The check does not assert the absence of a current Registry snapshot or that archived context remains readable while granting no mutation permission. |
| A5 | `registry_linkage_client_portal` | PLAT-REG-001, PLAT-REG-002, PLAT-REG-007 | PLAT-REG-002 and PLAT-REG-007 are asserted, and unknown-project refusals plus read-only gateway behavior cover substantial parts of PLAT-REG-001. However, the no-generation assertion only scans for direct uuid1/uuid3/uuid4/uuid5 assignments, and the stored-ID assertion subtracts seeded project IDs, so it is weaker than proving that every portal-stored project_id was Registry-issued and that the Registry is the only possible creator. |
| A6 | `derived_views_uow_client_portal` | PLAT-REG-005 | It does not cover the complete closed failure-kind table or explicitly exclude cached and client-supplied fallback context. |
| A6 | `api_transport_financial_policy_registry_gateway_client_portal` | PLAT-REG-005 | It does not exercise the entire closed RegistryFailureKind table or assert that failures never fall back to cached, client-supplied, or fabricated context. |
| A7 | `expense_recognition_projection_client_portal` | INV-031 | It does not test every named invalid form at every required boundary: unsupported versions are not refused at decoding or tested over HTTP, while incomplete and provider-carrying validation-bypassing objects are not passed to create_expense_from_recognition, and incomplete bodies are not tested over HTTP. |
| A8 | `service_identity_consumer_uow_client_portal` | INV-009 | It does not test the corresponding uniqueness rule for viewer_id and project_id. |
| A8 | `viewer_access_sqlite_uow_client_portal` | INV-009 | It does not test or assert uniqueness for (service_principal_id, project_id). |
| A8 | `project_tracking_audit_writer_sqlite_uow_client_portal` | INV-042 | The check asserts idempotent replay by payment_id and rejects a conflicting replay without creating another payment. It does not assert that WorkPayment is never a factura or accounting posting, or that payments total is derived. |
| A8 | `photo_management_uow_client_portal` | INV-043 | It does not assert that visibility-only changes preserve all progress data or any financial data. |
| A9 | `project_tracking_audit_writer_sqlite_uow_client_portal` | INV-037 | It does not assert that all monetary values are EUR or that foreign-currency input is explicitly rejected and never converted. |
| A9 | `snapshot_import_sqlite_uow_client_portal` | INV-037 | It does not assert two-decimal monetary semantics, ROUND_HALF_UP behavior, or directly verify that conversion never occurs. |
| A9 | `derived_views_uow_client_portal` | INV-041 | The check verifies one completed-work calculation and only that overall progress exists when planned work cost exists. It neither asserts the exact R9 overall-progress result nor asserts that progress is unavailable when no planned work cost exists. |
| A9 | `budget_derivation_client_portal` | INV-044 | The check asserts negative overspend behavior, explicit missing completion, and not-configured project views. It explicitly does not assert that completed_work_value is None when progress is absent; that value is merely recorded and is described as 0.00. |
| A10 | `staff_identity_uow_client_portal` | INV-015 | It does not inspect administrator actor provenance, absence of email in the record, or failure atomicity between the change and audit append. |
| A11 | `authorization_guard_client_portal` | INV-005, INV-006 | It does not test revoked credentials or prove that disabled service principals and disabled staff have no usable credentials. |
| A11 | `staff_identity_uow_client_portal` | INV-006 | It verifies that a suspended staff account cannot authenticate and that its existing session is unusable. It does not test credentials or sessions after staff disablement, and it does not test disabled service principals. |
| A11 | `service_identity_consumer_uow_client_portal` | INV-006 | It does not test suspended or disabled staff accounts or whether their sessions are invalidated. |
| A12 | `authorization_guard_client_portal` | INV-029 | It supplies no import content and does not assert that authorization occurs before content validation. |
| A12 | `service_identity_consumer_uow_client_portal` | INV-029 | It does not execute a producer import or establish that authorization occurs before content validation. |
| A13 | `staff_identity_uow_client_portal` | INV-051 | For selected actions passed through _one_audit, the check requires exactly one record of that action. It neither covers every catalog action nor asserts actor provenance or service-actor key_version. |
| A13 | `snapshot_import_sqlite_uow_client_portal` | INV-053 | It does not verify that those additional audit rows also have result "rejected". |
| A14 | `expense_intake_uow_client_portal` | INV-034 | It does not directly assert the general exactly-one-document constraint regardless of allocation count or verify that binary data cannot be stored in the record. |
| A16 | `staff_identity_uow_client_portal` | INV-018 | It does not test Unicode casefolding, syntax validation generally, or refusal of whitespace. |
| A16 | `credential_security_policy_client_portal` | INV-019 | It does not test rejection of passwords violating the R16 length or control-character rules. |
| A17 | `credential_security_policy_client_portal` | INV-003 | It does not inspect persisted session tokens, viewer access tokens, or service credentials, and it does not check logs or prove that any credential type is stored only in verification/hash form. |
| A17 | `staff_identity_uow_client_portal` | INV-003 | The check verifies that tested staff passwords are not persisted as plaintext. It does not establish hashed-only storage for session tokens, viewer tokens, or service credentials, and it does not inspect logs for any credential type. |
| A18 | `budget_management_sqlite_uow_client_portal` | INV-022, INV-023, INV-024, INV-025 | It does not assert that a producer lacks activation capability or cannot activate its own import, imported-plan immutability, activation atomicity under a failure during activation, or that automatic linking exclusively uses source_key and forbids display-name matching. |
| A18 | `snapshot_import_sqlite_uow_client_portal` | INV-020 | It does not attempt or detect mutation or deletion of an already accepted snapshot. |
| A18 | `budget_derivation_client_portal` | INV-026, INV-027, INV-028 | The check behaviorally asserts import immutability/conflicts, expense-plan separation, read-time recomputation after each named mutation, read purity, activation refusal with no writes, and preservation of sections/progress. However, the claims that no table stores any derived value and no service/store path can remove a section are only heuristic name/string/surface scans, so some violating implementations could escape detection. |
| A19 | `expense_intake_uow_client_portal` | INV-032, INV-036 | The configured run does not execute the management scenarios, so it does not assert atomic amount correction with allocation adjustment or the invariant at every later commit point. |
| A19 | `expense_management_uow_client_portal` | INV-032, INV-036 | It does not inject a failure between amount correction and allocation replacement to establish rollback atomicity, so the claim that correction and adjustment are atomic at every commit point is only weakly covered. |
| A19 | `derived_views_uow_client_portal` | INV-035 | It does not seed or test an unconfirmed expense, so the confirmed-only condition is unasserted. |
| A21 | `snapshot_import_sqlite_uow_client_portal` | INV-052 | It does not test update or deletion attempts against either import records or audit records. |
| A22 | `transaction_guard_client_portal` | TXN-001, TXN-002 | It does not establish that the original domain-error object reaches the caller unchanged, because it only matches the expected exception type and does not check object identity or contents. |
| A23 | `staff_identity_uow_client_portal` | entity_id canonical | It does not examine every audit record or assert that entity_id is absent for entities without IDs. |
| A24 | `derived_views_uow_client_portal` | read value unchanged | It checks that one use case does not change the status of its supplied grant objects. It does not establish that every repository value read by any use case remains unchanged. |
| A24 | `service_identity_consumer_uow_client_portal` | read value unchanged | The check verifies preservation of selected principal values and that one rejected grant-revocation path does not invoke repository mutation. It does not assert that every repository value remains unchanged after every use case that reads it. |
| A25 | `runtime_behavior_client_portal` | TRN-001, TRN-002, TRN-003 | However, it does not prove the rejected host/body requests never reach handlers, and its logging assertions cover one query secret and query-string omission rather than every credential, cookie, or secret. |
| A25 | `transport_guard_client_portal` | TRN-001, TRN-003 | The installed guard is exercised and required to refuse untrusted-host and oversized-body requests. The logging check is weaker than TRN-003: it tests one synthetic record made only from non-secret inputs for a short list of forbidden words, without injecting credential or cookie values or inspecting actual emitted log lines. |
| A25 | `api_transport_financial_policy_registry_gateway_client_portal` | TRN-002 | It does not test a foreign Origin on viewer sign-out, so it does not assert that sign-out is refused cross-origin. |
| A26 | `snapshot_import_sqlite_uow_client_portal` | recorded reason equals exception reason | It does not compare a raised exception's own `reason` value with the recorded reason or vary message text to establish message independence. |
| A27 | `derived_views_uow_client_portal` | same order every read | It does not read the same records repeatedly and compare the results, so it only asserts a weaker form of repeatable ordering. |
| A28 | `service_identity_consumer_uow_client_portal` | CLK-001 | It does not cover TTL-derived expiries or preservation of source-supplied times such as a supplied service-credential expires_at. |
| A28 | `staff_bootstrap_client_portal` | CLK-001 | The check asserts that created_at and updated_at share one timestamp and additionally compares audit.occurred_at, but it does not assert equality for every other portal-owned event timestamp, such as email_verified_at, nor exercise TTL-derived expiries or preservation of source-supplied times. |
| A30 | `runtime_settings_client_portal` | required configuration | It does not assert the existence or configuration-driven values of every timeout, TTL, rate limit, and bound; for example, the request/body and binary-size bounds are only supplied in BASE_ENV and never independently tested. |
| A30 | `binary_storage_content_client_portal` | bound existence | The check asserts that the binary read bound exists, is configured with a valid positive numeric value, does not exceed the response ceiling, and rejects oversized content. It does not assert the existence or configurability of every timeout, TTL, rate limit, or other bound; the viewer rate-limit settings are only supplied as configuration inputs. |
| A32 | `dependency_release_gate_client_portal` | DEP-002 | It does not require the snapshot to originate from a public advisory source: the source URL/database metadata is not validated and the release permits FACTORY_OSV_EXPORT_URL to supply an arbitrary export, so the full DEP-002 claim is only partially asserted. |

Judge variance seen: A10 (INV-015) was `asserts` in the first judgement and
`partial` after re-judging the same check for other items; A24 on
`service_identity_consumer_uow` went `partial` → `does_not` → `partial`;
A32 DEP-002 went `asserts` → `partial` when its text changed (the finding
holds: `FACTORY_OSV_EXPORT_URL` may name any export).

Several invariants are covered only jointly by two checks (INV-009 viewer
and service grants; INV-037 rounding and currency; PLAT-REG-005,
PLAT-REG-006, INV-003, INV-029 split across checks). The per-binding
judgement has no form for joint coverage: each binding is judged against
the whole invariant. Workbench gap, to the Workbench owner.

## State 2 rounds of 2026-11-08 (input size per request)

| round | requests | reviews | grouping | judge (instruction + text + files) | blocking |
|---|---|---|---|---|---|
| 79 | 5 | 3 × 286,883 | 21,164 | 848,480 (4,653 + 289,578 + 554,249) | 35 |
| 80 | 5 (+6 check re-judgements) | 3 × 292,923 | 17,200 | 842,995 | 32 |
| 81 | 5 (+2 check re-judgements) | 3 × 282,853 | 19,529 | 837,231 | 30 |

A review is about 87k of instruction and 200k of texts; the round now fits
the provider (limit 1,048,576), the judge request being the largest at
~840k. Check judgements: first pass 30 requests (856,820 characters in all,
median 26,221, max 82,943), second pass 15 (377,767, max 39,491),
re-judgements in rounds 80/81: 6 (12,823-83,291) and 2 (12,790, 28,560).
State 1 rounds 46-47 (run before the coordinator's limit): 5 requests each,
reviews 66,730 / 67,519, judge 719,934 / 718,543 (644,377 of it files).

Fixes taken in rounds 79-80 (simplest code-backed form): A10 INV-015 names
its enhanced audit (A13's `staff.recovery_override` record); A18 INV-026 a
conflicting re-publication changes no business state and is recorded as
its import result and audit; A28 one wall reading per operation plus the
audit writer's own, derived expiry = instant + TTL while a supplied one is
kept, source times stored offset-naive UTC, invariant `CLK-001`; A31 the
three outcomes of the security-review procedure (NOT_APPLICABLE carries a
rationale and resolves to neither a decision nor an open question — the
invariant is narrowed to what the procedure and its gate decide); A32
DEP-002 covers every installed distribution, with the age limits named as
the deploy route's `max_snapshot_age`, `max_environment_age`.

Open after round 81 (17 units): A4, A5, A6, A7, A8, A9, A11, A13, A16,
A18, A19, A21, A22, A25, A28, A30, A32 — the coverage gaps of the table
above, plus singletons on A28 (where in an operation the one wall reading
happens; accepted forms of source-supplied datetimes) and A32 (whether the
vulnerable-image rule covers builds or only deploys).

## Other open items

- FA015: the Factory Spec Inspector requires a module importing
  `append_audit` to import `AuditRepository` too (nine modules), and
  `staff_bootstrap_cli` `StaffBootstrapPort`. Owner: imports closure, or
  the Factory/Workbench rule discrepancy. Unchanged.
- On the live code the Factory time-source gate blocks under
  `rules.time_source_policy` until the next Route B regenerates the
  consumers (`65_imports.json` marks the 45 uses `code_outdated`).
- The workbench MCP `check_note_draft` answers from the pushed canonical
  ref and refused ("authored sources do not project:
  persistence/router/state6 handoff not ready") while this branch was
  unpushed; the notes were checked with the local `design_notes --gate`.
