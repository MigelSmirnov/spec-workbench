# Handoff — Client Portal (current)

Replaces the handoff of the morning of 2026-11-08. State of
`agent/client-portal` on 2026-11-08 after the first pass on the single-round
closure rule (Workbench #163, merged into the branch at `d407634a`), checked
against the clean Factory checkout `code_factory_cp_witnesses` at origin/main
`5a3bdec2`. The assembly, admission and diagnosis results are in
`80_assembly.md`; the semantic diff against the accepted Factory spec
459ac96c, for the owner, is `SEMANTIC_DIFF.md`.

## Where the case stands

- **Ready for export, not exported.** States 0-7 are closed on their current
  texts (`status` per state: closed, ready). `authoring next` stops at
  `state8_assembly`, which is ready. Admission reads `READY_TO_EXPORT` (22
  checks: 17 PASS, 5 NOT_APPLICABLE). The export command is prepared in
  `80_assembly.md` and waits for the owner's approval. No export, Route B or
  deploy was run.
- `90_factory_target.json` names `factory_checks_issue`
  MigelSmirnov/code-factory#189. The 54 partial witness verdicts are carried
  there by `witness_material` and no longer block.
- FA002 is closed by the Stage 8.1 ledger `81_module_review_status.json`.
  FA015 is closed by type imports in the imports closure. FA019 is closed by
  the rounds below.
- The running service still differs from the spec until the next Route B:
  the email routes, 0.00 instead of `None` (INV-044), direct clock reads
  (`design_diagnose` Factory code check: 46 findings) and
  `BootstrapAlreadyCompleted`.

## Pass of 2026-11-08 on the single-round rule (#163)

One round per change. A contradiction was fixed and then asked once on the
fix. Every other judged topic got a disposition. Provider
`codex-cli:gpt-5.6-sol:medium`. Input characters per request, measured with
the wrapper around `design_questions.py`. The judge's files are written to
its working directory and listed apart, not added in.

| state, round | units | requests | review (each) | grouping | judge inline (instr + text); files apart | blocking | outcome |
|---|---|---|---|---|---|---|---|
| 3 r37 | context | 5 | 3 × 247,764 (35,993 + 211,771) | 2,858 | 33,163 (6,105 + 27,058); 1,034,298 | 2 | T2 contradiction fixed `43efdb67`; T4 gap carried to 7 |
| 2 r96 | A28 (fix of r37 T2) | 5 | 3 × 65,944 (5,579 + 60,365) | 937 | 35,311 (6,296 + 29,015); 995,850 | 1 | T2 gap carried to factory_checks; no contradiction |
| 3 r38 | context (fix) | 3 | 3 × 126,651 (4,193 + 122,458) | — | — | 0 | clear, r37 T2 not raised again |
| 4 r40 | context | 5 | 3 × 242,913 (37,137 + 205,776) | 2,146 | 24,904 (6,101 + 18,803); 1,075,853 | 0 | clear |
| 5 r28 | build_budget_view, build_progress_view, context | 5 | 3 × 307,759 (38,511 + 269,248) | 578 | 36,462 (6,134 + 30,328); 1,173,638 | 0 | clear |
| 7 r17 | 12 modules | 40 | 36 reviews, 11,264-47,791 | 4 grouping/judge requests, 578-41,598 | — | 1 | staff_bootstrap_cli:T1 contradiction and photo_management:T1 gap, both fixed `8a9cf144` |
| 7 r18 | photo_management, staff_bootstrap_cli (fix) | 6 | 3 × 16,933; 3 × 30,778 | — | — | 0 | clear |
| 2 r97 | A28 (CLK-002 binding) | 3 | 3 × 65,096 (4,668 + 60,428) | — | — | 0 | clear |
| 3 r39 | context (binding) | 5 | 3 × 125,799 (3,278 + 122,521) | 655 | 23,319 (6,105 + 17,214); 1,035,417 | 0 | clear |
| 4 r41 | context (binding) | 3 | 3 × 114,915 (3,633 + 111,282) | — | — | 0 | clear |
| 5 r29 | context (binding) | 5 | 3 × 122,360 (3,259 + 119,101) | 633 | 22,818 (6,134 + 16,684); 1,174,554 | 0 | clear |

State 1 was already closed (round 47) when the pass started.

Changes made in this pass:

- **FA015 type imports** (`11f65b98`): `AuditRepository` `annotates`, basis
  `contract` (the signature of `append_audit`), in budget_management,
  expense_intake, expense_management, photo_management, project_tracking
  (and its two operations), service_identity, snapshot_import,
  staff_identity and viewer_access. `StaffBootstrapPort` in
  `staff_bootstrap_cli.run_bootstrap_cli`. The earlier rejections ("the
  value only passes through the call") judged the accepted code, not the
  surface the slicer needs. The Workbench imports model can express this.
- **A28 CLK-002 owners** (`43efdb67`, State 3 r37 T2): the clock source
  gives one reading per call. The viewer-entry rate limit of A25 owns its
  one reading per request and its window, as State 3 `system_clock`
  "Must not own" requires.
- **Supplied offset-aware times** (`e8499f77`, State 3 r37 T4 carried to 7).
  Principle by the operating profile: one stored meaning per timestamp, the
  instant. The notes of import_snapshot, create_expense_from_recognition,
  publish_progress_photo and issue_service_credential convert an
  offset-aware value to UTC, keeping its instant, before storing it
  offset-naive. An offset-naive value is taken as UTC.
- **State 7 r17 fixes** (`8a9cf144`): `AuditRecord` added to
  `staff_bootstrap_cli`. Its prompt showed
  `StaffBootstrapPort.create_if_empty(..., audit: AuditRecord)` once the port
  was in its surface. `_classify_photo_replay` compares the supplied
  `photo_date` in its stored form.
- **CLK-002 bound** (`5ac1900d`) to `transport_guard_client_portal`, which
  requires that a wall-clock jump does not release a limited viewer.
  `decision_witness_resolution` had blocked: CLK-002 was added in rounds
  92-95 without a binding.

Carried by disposition (`design_questions.py carried`):

- State 2 r96 T2 → `factory_checks` (code-factory #189): the CLK-002 witness
  shows that the viewer-entry rate limit is the only caller of
  `monotonic_seconds`.
- State 3 r37 T4 → State 7: done in `e8499f77`; State 7 r17/r18 asked it.

Witness verdicts after this pass: `judge-checks` re-judged the 18 bindings
of the six checks whose items changed (6 requests, 13,131-83,366
characters), then the three checks of the A28 Witnesses item (3 requests,
13,626-29,396). In all: 69 bindings, 15 asserts, 54 partial, 0 does_not.
A24 on `service_identity_consumer_uow` was `does_not` in the first run and
`partial` after its file set changed (judge variance). The A28 Witnesses
item names CLK-001 and CLK-002, so each of its three tags binds both
invariants (protocol rule). All three are partial.

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

The table below is the judgement of the morning of 2026-11-08 (68 bindings).
The current counts are in the pass above (69 bindings: 15 asserts, 54
partial); every partial binding is carried to code-factory #189.

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
invariant it is bound to. Owner of each: the Factory check (extend it,
code-factory #189), never a narrowed invariant or binding text. Since #161
they block at State 8 (`witness_material`), not in the State 2 round. The
texts of A18, A21, A28 and A32 changed on 2026-11-08 (below), so their
bindings are judged again at State 8.

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

## State 2 rounds 79-81 of 2026-11-08, before #161 (input size per request)

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

## State 2 rounds 82-95 (2026-11-08, after #161)

Run with `--since 451ea6de` (the round-81 `closed_at`), provider
`codex-cli:gpt-5.6-sol:medium`, 5 requests per round (3 reviews, grouping,
judge). Input characters per request:

| round | review (each of 3) | grouping | judge (instruction + text + files) | blocking | blocked units |
|---|---|---|---|---|---|
| 82 | 239,236 | 4,109 | 811,853 (5,411 + 252,193 + 554,249) | 10 | A18, A21, A28, A32 |
| 83 | 245,051 | 1,879 | 807,080 | 2 | A28, A32 |
| 84 | 175,189 | 1,695 | 761,903 | 1 | A32 |
| 85 | 166,010 | 3,455 | 762,766 | 5 | A28, A32 |
| 86 | 166,136 | 5,113 | 770,126 | 6 | A28, A32 |
| 87 | 166,136 | 4,389 | 767,038 | 3 | A28, A32 |
| 88 | 168,297 | 3,725 | 768,008 | 5 | A28, A32 |
| 89 | 169,061 | 2,231 | 761,508 | 4 | A28, A32 |
| 90 | 169,950 | 4,753 | 769,344 | 2 | A32 |
| 91 | 165,937 | 8,484 | 782,086 | 2 | A28 |
| 92 | 167,594 | 7,854 | 786,956 | 3 | A18, A28 |
| 93 | 151,714 | 2,956 | 62,893 inline (6,296 + 56,597); files 981,942 apart | 2 | A18, A28 |
| 94 | 167,917 | 2,204 | 70,834 inline (6,296 + 64,538); files 982,469 apart | 0 | — |
| 95 | 167,917 | 2,364 | 65,030 inline (6,296 + 58,734); files 982,469 apart | 0 | — |

Two attempts (rounds 83 and 85) failed after their three reviews on a
review answer that was not valid JSON and saved nothing; they were rerun
(3 more requests each at the sizes above). Round 87 repeats round 86 on the
same text (a retry loop treated `ask`'s exit 1 for "not closed" as a
failure). The judge's 554,249 characters of files are constant: the later
states' texts it reads for `answered_later`.

No round raised a check's coverage as a blocking topic. The reviewers still
asked "which existing check is bound to CLK-002" in rounds 83-90; the judge
set it aside each time (`answered`, `judged_before`). Workbench defect, to
the Workbench owner: the State 2 review prompt still invites questions about
bound checks.

What changed in the decisions (`02_rules.md`), each on its substance:

- A18 INV-027 (r82 T6, T12): the test covers every write of an owning
  record, budget-version activation included (the list read as exhaustive
  and left activation out), and forbids stored values of a derived view,
  not every derived column (an import's content fingerprint is stored by
  the models).
- A21 INV-050 (r82 T7): every overview component (budget, expenses,
  progress, payments, photos) equals a recomputation, not only budget and
  payments.
- A28 (r82 T5, T9, T11; r85 T9): `document_date` and `payment_date` are
  calendar dates kept as supplied, not instants (they were listed among
  UTC instants, against the State 1 models); "no arithmetic" is the clock
  source's, an operation derives an expiry as instant + TTL; CLK-001 now
  states one wall reading from the clock source, the only reader of the
  host clocks, derived expiry = instant + TTL, supplied times and dates
  kept; its test covers every timestamp-writing operation with the clock
  fixed.
- A32 (r82 T2, T8, T10; r83 T6): OSV (ecosystem PyPI) is the advisory
  source; the checked set is every distribution installed in the image
  (rule 3 said pins and their resolved libraries, DEP-002 every installed
  one); a deploy is the start of the service from an image (DEP-002 said
  "ships", its test "starts"); a passing rebuild under the same pins may
  deploy. How the snapshot is obtained and verified and how a version is
  matched to an advisory is the deploy route's and its State 8 witness's
  (code-factory #189); the age limits stay the deploy route's values.
- Rounds 83-90 drove A28 and A32 into witness mechanics (OSV export
  completeness, transport authentication, PEP 440 matching; clock
  instrumentation, read counts). On the coordinator's instruction those
  additions were removed before round 91 and the simplest form above kept.

Open after round 91 (blocking, A28), verbatim:

- T1 "Clock-source and reading-count verification for read-only
  current-time checks": "CLK-001 governs current-time comparisons, but its
  Required test omits operations that compare persisted expiry without
  writing timestamps."
- T2 "Elapsed-clock source, request scope, reading count, use, and
  non-persistence policy": "The later operation text resolves that the
  reading is per viewer-entry attempt, but State 2 still supplies no formal
  invariant or Required test for any elapsed-clock property." (Round 82 T9
  raised the same; a CLK-002 added for it in rounds 82-90 was removed with
  the mechanics before round 91.)

Round 92 (owner approved closing A28 on substance, coordinator
2026-11-08): CLK-001 extended to every read of the current time, writing a
timestamp or comparing it with a stored one (expiry checks included), one
wall reading per operation from the clock source; new CLK-002 (owner: the
clock source): elapsed durations are measured only through the clock
source's monotonic reading, used within one process, never persisted and
never compared with or mixed into wall-clock values. Required tests items
at the same level. Round 91's two A28 topics did not recur (r92 T7
`answered`, T17 `answered_later`). Status and A32 closed; open units A18,
A28.

Open after round 92 (blocking: 3), verbatim:

- T11 (A18, consequential_gap) "INV-027 permissibility and handling of
  stored derived values or caches": "The detailed test forbids every
  stored derived-view value and answers the cache question, but the
  generic Required-test sentence still requires refusal of an undefined
  violating input to a read-only recomputation."
- T15 (A28, consequential_gap) "CLK-001 architectural check prohibiting
  direct host-clock reads outside the clock source": "The Required test
  says how to observe an operation's clock-source use but does not say
  what check demonstrates the global architectural prohibition on every
  direct host-clock read."
- T16 (A18, contradiction) "INV-020 behavior when an existing snapshot
  identity is republished with conflicting content": "The unqualified
  INV-020 Required-test outcome says a violating import changes nothing,
  while the detailed required test expressly requires a changed
  re-publication to append its import result and audit."

Round 93 (owner approved fixing the three round-92 topics; on 404d1ccd,
origin/main with Workbench #162 merged: narrower judge input, review retry,
no bound-check invitation). A18: the eight generic carried-over items "a
focused test at X showing the invariant holds; a violating input is refused
and changes nothing" were removed; INV-020 and INV-022…INV-025 got detailed
items at the "what must be shown" level beside their witness tags
(INV-026…028 kept theirs). CLK-001's Required tests item adds that no module
other than the clock source reads the host wall or monotonic clock directly.

Round 93 sizes: each review 151,714 (12,622 instruction + 139,092 text);
grouping 2,956; judge 62,893 inline (6,296 instruction + 56,597 text).
Since #162 the judge's files (981,942) are written to its working
directory and read by search, not sent in the prompt; they are not part
of the request size. In rounds 82-92 the judge column above still adds
them in.

Open after round 93 (blocking: 2; open units A18, A28), verbatim:

- T4 (A18, contradiction) "Whether idempotent snapshot re-publication
  permits any persistent writes": "The Required test's unqualified no-change
  outcome conflicts with the product rule requiring two new persistent
  records for every classified idempotent replay." Quotes: "a
  re-publication of its identity with the same content changes nothing,"
  and "An attempt the import classifies — accepted, idempotent replay,
  integrity conflict, or a rejection — is recorded as a fresh immutable
  import result with a fresh `import_id` and its `snapshot.import` audit;".
  A defect of the new INV-020 item written for round 93: a same-content
  replay should also say it is recorded as its import result and audit.
  Not edited (one round only).
- T7 (A28, consequential_gap) "Whether CLK-002 requires exactly one
  monotonic-clock read per viewer-entry request": "Although the normative
  rule requires one elapsed reading per request, neither CLK-002 nor its
  Required tests item says that the test must demonstrate that read-count
  requirement."

Round 92's T11, T15, T16 did not recur as such (T16's replay question
returned as T4 on the new text). No round-93 topic is about a bound
check.

Round 94 (coordinator, fixing both round-93 topics):
- T4: the INV-020 item now says a same-content re-publication is an
  idempotent replay and that either a replay or a conflict leaves the
  snapshot unchanged, changes no business state and is recorded as its own
  import result and `snapshot.import` audit. The same "nothing stored /
  changes nothing" wording covered the classified snapshot replay in A8:
  its table row, INV-021 and INV-021's generic Required tests item now say
  the same (no snapshot stored, no business state changed, own import
  result and audit; the request is answered with the result, not the
  snapshot, `00_product.md`). The expense, photo and payment replay rows
  of A8 were left as they are: no text records anything for them.
- T7: CLK-002 and its Required tests item say one elapsed (monotonic)
  reading per viewer-entry request, as the normative rule does.

Round 94: 5 requests; reviews 167,917 each (17,646 + 150,271), grouping
2,204, judge 70,834 inline (6,296 + 64,538), files 982,469 apart.
Blocking 0, the round is clear; topics: A28 ×2 `judged_before`, A8
`answered`, A8 ×2 `answered_later`. Open units: A8, A18, A28 (each needs
a second clear review on its current text; A8 reopened by this edit).

Round 95 (confirmation, text unchanged since round 94): 6 requests — one
review answered invalid JSON and was asked once more (#162 retry), so 4
review requests of 167,917 (17,646 + 150,271); grouping 2,364; judge
65,030 inline (6,296 + 58,734), files 982,469 apart. Blocking 0, clear;
topics: A28 `later_state`, A28 `judged_before`, A8 `judged_before`, A8
`answered`. Round closed; `status --state 2`: closed true, ready true.

Reopened and not asked (coordinator: State 2 only; unchanged after round
95, `status` per state): State 1
(`Projections and answers`), States 3 and 4 (`context`), State 5
(`build_budget_view`, `build_progress_view`, `context`), State 7
(`financial_policy`, `derived_views`) — the same units as before round 82;
the State 2 edits enter the `context` of States 3-5. State 0 stays closed.

## Other open items

- **Export** waits for the owner (command in `80_assembly.md`). It targets
  the clean checkout `code_factory_cp_witnesses`. The main `code_factory`
  checkout is dirty (FA008 there) and was not used.
- **Factory checks, code-factory #189** (owner: Factory): 54 partial
  bindings (`transition.py --phase state8_assembly`), INV-044's `None`
  assertion in `budget_derivation_client_portal`, and the CLK-002
  sole-caller witness (State 2 r96 T2).
- **Route B** (owner: coordinator, after export): the live code has 46
  Factory code-check findings on the clock source and still serves the
  removed email routes and the 0.00 of INV-044.
- **Stage 8.1** evidence is the State 7 rounds and the emitter IR. No
  separate per-module adversarial review was run (ledger `semantic_evidence`).
- **Workbench gaps** (owner: Workbench):
  - A witness-tag-only edit to a State 2 Required tests item reopens the
    State 2 unit and the `context` of States 3-5. QUESTIONS.md says a
    `[witness: …]` tag is only text of its item. Binding CLK-002 cost four
    rounds (r97, r39, r41, r29), none of which raised anything.
  - The per-binding judgement still has no form for joint coverage, and a tag
    binds every invariant of its item (the A28 Witnesses item now binds
    CLK-001 and CLK-002 to each of three checks).
  - `imports_scope_stale` after a note edit has no command that re-records
    `basis_sha256` once the author has re-read the candidates. `--draft`
    leaves the stale hash; the hash was set by hand to the gate's `current`
    value, with no candidate pending.
  - The Factory slicer adds the signature types of a port's operations to a
    prompt only in part: `StaffAccount` appeared in `staff_bootstrap_cli`'s
    IMPORTS without a declaration, `AuditRecord` did not (Factory, to the
    coordinator).
- The workbench MCP `check_note_draft` answers from the pushed ref; the
  notes of this pass were checked with the local `design_notes --gate`.
