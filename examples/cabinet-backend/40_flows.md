# State 4 — Cabinet Backend key system flows

## Status

State 4 is in progress. This document records reviewed end-to-end flows using explicit State 3 module and candidate-capability references. The flow descriptions do not finalize State 5 public contracts.

---

## `flow:synchronize_invoice_to_local_archive`

### Trigger

A synchronization cycle initiated by Local Cabinet Backend observes one exact VPS Cabinet invoice work package that is eligible to be transferred toward local durable custody.

### Boundary

The transport boundary enters through `module:synchronization`. Transport delivery is not durable acceptance. Local archive acceptance belongs only to `module:durable_archive`.

The flow may use the candidate State 3 needs `capability:synchronization.synchronize_invoice_work`, `capability:synchronization.observe_vps_connection`, `capability:synchronization.reconcile_transfer_outcome`, `capability:durable_archive.accept_transfer_manifest`, and `capability:durable_archive.verify_durable_acceptance`. These names remain candidate capabilities until State 5.

### Steps

1. `module:synchronization` may first obtain a typed read-only connection observation through `capability:synchronization.observe_vps_connection`, then authenticates and performs the accepted outbound synchronization protocol using the synchronization-only node identity; local service or human authorization is not substituted for that credential boundary.
2. `module:synchronization` receives or constructs the exact transfer package and preserves its transfer identity, hashes, and delivery/reconciliation evidence without claiming business acceptance.
3. The package required set is presented to `module:durable_archive` for local acceptance under the accepted manifest, source-integrity, duplicate, quarantine, and atomic-visibility rules.
4. `module:durable_archive` validates the exact immutable Invoice Card revision and required source evidence, then either accepts the required set atomically, recognizes an already accepted idempotent transfer, or records the accepted failure/quarantine outcome.
5. Only after `module:durable_archive` proves durable acceptance may synchronization record or transmit the corresponding acceptance receipt. A successful network delivery by itself never creates an accepted archive fact.
6. If the transport outcome is unknown, `module:synchronization` reconciles by read/status evidence through `capability:synchronization.reconcile_transfer_outcome` and must not create a second logical transfer merely because the previous network result was ambiguous.
7. A caller may read the exact recorded synchronization state through `capability:synchronization.get_sync_status` at any point; the read never mutates transfer state.

### Outcomes

Successful observable outcomes are:

- the exact invoice revision and its required source set are durably accepted and visible in the local archive; or
- the transfer is recognized as already accepted with the same accepted identity/evidence.

Non-success terminal or review outcomes include:

- rejected or unsupported package content;
- quarantine requiring explicit resolution;
- duplicate-candidate review where State 2 requires review rather than silent merge;
- missing or invalid required source evidence;
- transport outcome remaining unknown until reconciliation completes.

The observable result must preserve the distinction between transport delivery state and archive acceptance state.

### Errors

`module:synchronization` owns translation of transport/authentication/retry/reconciliation failures into synchronization outcomes. It must not translate a transport success into archive acceptance.

`module:durable_archive` owns archive-validation, integrity, duplicate, idempotency, quarantine, and atomic-acceptance failures. Persistence adapters may report technical failures but must not decide those business outcomes.

If an error reveals that the package lacks data required by an already accepted State 1 or State 2 decision, the repair belongs to that earlier state rather than being hidden inside this flow.

### State 4 review notes

This flow deliberately crosses only the synchronization and durable-archive responsibility boundary. It does not include Registry catalogue publication, PresuPro analysis, Holded publication, retention release, or general local-agent operations; those require separate State 4 flows because they have different triggers, owners, errors, and observable outcomes.

---

## `flow:accept_local_source_attachment`

### Trigger

An authenticated local user or authorised local service/agent supplies one or more photographs or PDF files for attachment to one exact already accepted Invoice Card identified by stable `invoice_id`.

### Boundary

Authentication and exact-operation authorization enter through `module:access_control` using `capability:access_control.authorize_operation`. Source attachment policy and durable evidence transitions belong to `module:durable_archive` through `capability:durable_archive.attach_local_source` and may be observed through `capability:durable_archive.get_source_status`.

The local HTML uploader and local agent are adapters over the same Backend operation. Neither adapter owns matching, hash, provenance, idempotency, or archive policy.

### Steps

1. The local adapter resolves its actor/service context and asks `module:access_control` whether that principal may perform the exact source-attachment operation.
2. The caller selects one exact `invoice_id`; human-readable invoice number, supplier, date, or amount may assist search but never become the mutation identity by themselves.
3. `module:durable_archive` receives the selected invoice target plus the submitted files and calculates/validates required media, content-hash, expected-source, and provenance evidence.
4. Every submitted file is evaluated independently. Unreadable, unsupported, mismatched, or wrong-target evidence remains a failure and cannot replace already accepted evidence.
5. Reattaching identical bytes to the same invoice/source target is treated idempotently and does not create a second binary replica.
6. Successfully verified files are attached with actor, time, original filename, media type, calculated hash, origin/result evidence, and source-target linkage.
7. The resulting source-package availability/completeness state is recomputed without rewriting the immutable Invoice Card. A filled required source may remove the corresponding missing-source warning only when the accepted State 2 conditions are satisfied.
8. `capability:durable_archive.get_source_status` may expose the resulting attachment/source status to the local adapter for a clear per-file result.

### Outcomes

The flow returns an explicit result per submitted file and an updated source-evidence status for the target invoice. Accepted outcomes include newly attached verified evidence and idempotent already-attached evidence.

Review/failure outcomes include ambiguous invoice targeting before mutation, unsupported or unreadable files, expected-hash mismatch, wrong source target, authorization denial, and partial success when several submitted files do not share the same result.

A successful source attachment changes Backend-owned source availability evidence only; it never edits the accepted Invoice Card bytes or content hash.

### Errors

`module:access_control` owns authentication/authorization denial and security evidence for the protected operation.

`module:durable_archive` owns target existence, source-integrity, expected-hash, idempotency, provenance, storage-acceptance, and source-state errors. The HTML/CLI/MCP adapter only translates those outcomes for its caller.

Ambiguous human-readable search is resolved before the mutation call. No adapter may turn an ambiguous match into an automatic archive mutation.

---

## `flow:refresh_registry_and_validate_assignment`

### Trigger

Cabinet Backend refreshes Registry project context, or an existing Invoice Card assignment must be checked against newly observed Registry state after reconnection or catalogue refresh.

### Boundary

All Registry-derived project observation and Cabinet WorkObject projection belong to `module:registry_context`. The flow uses `capability:registry_context.refresh_registry_context`, `capability:registry_context.validate_card_assignment`, and `capability:registry_context.get_assignment_validation`. When the refreshed exact catalogue is delivered to VPS Cabinet, transport ownership remains in `module:synchronization` through `capability:catalogue_publication.publish_registry_catalogue`; synchronization does not choose or filter Registry truth.

Registry remains authoritative for Registry-owned project facts. Cabinet Backend never writes WorkObject or assignment changes back into Registry.

### Steps

1. `module:registry_context` performs the accepted full Registry project observation and constructs the compact project context from the verified fields only.
2. Registry-derived fields are projected into Cabinet WorkObjects keyed by stable Registry `project_id`; existing Cabinet-owned local fields remain untouched. When catalogue publication is requested, the exact already-produced catalogue delivery is passed to `capability:catalogue_publication.publish_registry_catalogue` without moving catalogue-content policy into synchronization.
3. Existing WorkObjects absent from a later catalogue response are preserved. Absence is treated as unresolved source availability rather than confirmed deletion.
4. For an Invoice Card assignment under review, `module:registry_context` validates the exact Card/project context against the refreshed observation through `capability:registry_context.validate_card_assignment`.
5. Active Registry context may validate normal availability. Archived or currently missing project context requires review and must not be interpreted as authoritative project completion.
6. The validation result is stored separately from the immutable Card object block. A changed Registry observation may change Backend-owned review state but never silently rewrite the Card assignment.
7. `capability:registry_context.get_assignment_validation` exposes the resulting validation/review evidence to callers.

### Outcomes

Observable outcomes distinguish a currently valid assignment from an assignment requiring review because the Registry project is archived, unavailable, or absent from the latest catalogue.

The refreshed WorkObject projection preserves both observed Registry facts and Cabinet-owned local fields. No outcome in the current Registry contract claims a distinct authoritative `completed` state or automatically produces `late_project_cost` from `archived`.

### Errors

`module:registry_context` owns Registry observation/translation, catalogue freshness, WorkObject projection, and assignment-validation errors.

A Registry transport/client adapter may report technical failure but may not infer deletion, completion, replacement project, or Card mutation from that failure.

If Registry lacks an authoritative fact required for a new business classification, the result remains unresolved/review-required rather than being guessed inside this flow.

---

## `flow:calculate_plan_actual`

### Trigger

A Cabinet user or agent requests reproducible plan-versus-actual analysis for a project or selected invoice evidence using accepted Invoice Card facts and PresuPro estimate observations.

### Boundary

Analytical policy belongs to `module:plan_actual`. It may obtain exact archived purchase evidence through `capability:durable_archive.get_archived_invoice`, exact project context through `capability:registry_context.get_work_object`, preserve a current PresuPro observation through `capability:plan_actual.refresh_estimate_snapshot`, produce non-authoritative proposals through `capability:plan_actual.propose_invoice_line_matches`, record an explicit decision through `capability:plan_actual.record_match_decision`, expose exact unmatched identities through `capability:plan_actual.get_unmatched_items`, and calculate through `capability:plan_actual.calculate_plan_actual`.

Neither PresuPro nor Registry facts are rewritten by the calculation.

### Steps

1. The flow resolves the exact accepted Invoice Card revision(s) required for the analysis from `module:durable_archive` rather than from mutable transport payloads.
2. The applicable WorkObject/project context is read from `module:registry_context`; unresolved assignment state remains explicit and may prevent project-specific analysis where State 2 requires a confirmed assignment.
3. When a fresh PresuPro observation is requested, `module:plan_actual` records it as an immutable EstimateSnapshot when its canonical content differs from the latest stored snapshot for the same PresuPro estimate identity. Identical observed content is idempotent.
4. The analysis selects exact immutable estimate snapshot identity. `capability:plan_actual.propose_invoice_line_matches` may produce stable non-authoritative proposals, but similarity alone never becomes a confirmed invoice-line/estimate-item match; only an explicit transition through `capability:plan_actual.record_match_decision` may create or change a durable decision. `capability:plan_actual.get_unmatched_items` exposes the resulting unmatched identities without fabricating placeholder items, and calculation uses only accepted/pinned confirmed decisions.
5. Unmatched invoice lines remain valid analytical facts and are included explicitly rather than causing placeholder estimate items or invoice rejection.
6. `module:plan_actual` checks quantity/unit and other accepted comparison preconditions, then computes plan, actual, variance, remaining or other accepted deterministic results from the pinned evidence.
7. The result preserves the identities of the invoice revision, estimate snapshot, project context, accepted matches, and any explicit conversion/forecast assumptions needed for reproducibility.

### Outcomes

A successful outcome is a reproducible plan-versus-actual result tied to exact immutable evidence and confirmed matching decisions.

Valid non-success/review outcomes include unresolved project assignment, missing referenced evidence, incomparable quantity/unit semantics, and explicit unmatched lines. These states do not mutate Invoice Card or PresuPro facts and are not hidden behind fabricated matches.

### Errors

`module:durable_archive` owns inability to resolve accepted invoice evidence. `module:registry_context` owns project-context availability/validation facts. `module:plan_actual` owns PresuPro snapshot acceptance, match-reference validation, comparison preconditions, deterministic calculation, and analytical warning/refusal behavior.

The PresuPro adapter may expose current external content but must not invent estimate lineage. Any semantic proposal requires an explicit Cabinet decision before it can become a confirmed match used in calculation.

---

## `flow:publish_invoice_to_holded`

### Trigger

An authenticated actor explicitly requests publication of one exact confirmed Invoice Card revision to Holded after all currently accepted Cabinet eligibility conditions are satisfied.

### Boundary

Protected-operation authorization enters through `module:access_control` and `capability:access_control.authorize_operation`. Exact archived Invoice Card evidence is read through `module:durable_archive` and `capability:durable_archive.get_archived_invoice`.

Cabinet publication eligibility and logical publication lifecycle belong to `module:holded_publication` through `capability:holded_publication.request_holded_publication`, `capability:holded_publication.reconcile_holded_publication`, and the read-only `capability:holded_publication.get_holded_publication_status`. Holded credentials, HTTP mutation/read mechanics, attempt receipts, and technical lookup belong to `module:holded_gateway` through `capability:holded_gateway.create_holded_purchase` and `capability:holded_gateway.lookup_holded_purchase`.

### Steps

1. `module:access_control` authorizes the exact Holded publication operation for the authenticated actor; reusable Holded credentials are never exposed to that actor or to `module:holded_publication`.
2. The exact confirmed Invoice Card revision is loaded from `module:durable_archive`. `module:holded_publication` evaluates Cabinet eligibility against accepted conditions, including required source evidence and any required resolved operational context, without modifying the Card.
3. Before network mutation, the publication lifecycle persists the logical publication/attempt identity and exact revision binding required by the accepted Holded rules.
4. `module:holded_gateway` performs at most one automatic create POST for that logical attempt through `capability:holded_gateway.create_holded_purchase`; it preserves the technical request/response evidence and returned Holded document identifier when available.
5. A clear create result is followed by read-back verification of the exact Holded document. Business-field verification, including accepted gross-total precision, settles the logical publication only when the returned representation proves success.
6. If the create outcome is ambiguous, no automatic second POST is allowed. `module:holded_publication` enters reconciliation and `module:holded_gateway` uses read-only marker lookup through `capability:holded_gateway.lookup_holded_purchase` followed by GET/business verification as required by the accepted recovery protocol.
7. Zero marker matches keep the outcome unknown; one verified exact match may settle the publication as recovered; multiple matches or payload disagreement require reconciliation/conflict handling rather than silent success.
8. `capability:holded_publication.reconcile_holded_publication` exposes the logical settlement/review action without leaking raw gateway credentials or turning an unverified numeric Holded status into business meaning. A caller may read the exact PostgreSQL-authoritative logical state through `capability:holded_publication.get_holded_publication_status` without substituting gateway evidence.

### Outcomes

Successful outcomes include a verified new Holded purchase or a verified recovered purchase, each bound to one exact Invoice Card revision and canonical Holded document identifier.

Non-success outcomes include eligibility denial, authorization denial, outcome unknown after bounded recovery, duplicate-marker conflict, business-field verification failure, and reconciliation required. Holded-specific recalculation evidence is preserved separately and never rewrites Invoice Card totals.

Unverified Holded update, refund, attachment, approval, payment, status interpretation, and later-revision reconciliation remain outside this flow.

### Errors

`module:access_control` owns protected-operation authorization failure. `module:durable_archive` owns inability to resolve accepted immutable source evidence. `module:holded_publication` owns Cabinet eligibility, logical duplicate prevention, publication state, and reconciliation classification. `module:holded_gateway` owns credential, transport, raw remote-response, single-create technical attempt, and lookup/GET errors.

No HTTP/MCP/CLI adapter may repeat POST, reinterpret unknown Holded status, or mark publication successful merely from a transport response.

---

## Withdrawn — `flow:release_vps_working_copy`

> **Withdrawn by A76** (`02_rules_flow6_ownership_repair.md`, 2026-08-23): the VPS working set, its release policy and this surface belong to Cabinet Web. Kept as design history; not assembled.

### Trigger

A user explicitly requests manual release/removal of one identified VPS Cabinet project working set or exact working-copy set after synchronization has occurred.

### Boundary

Release eligibility and decision history belong to `module:retention_release` through `capability:retention_release.evaluate_vps_release`, `capability:retention_release.request_manual_vps_release`, and the read-only `capability:retention_release.get_retention_status`.

Required durable-local proof is read from `module:durable_archive` through `capability:durable_archive.verify_durable_acceptance`, and exact working-set membership plus relevant transfer/replica status are read from `module:synchronization` through `capability:synchronization.get_working_set_membership` and `capability:synchronization.get_sync_status`.

The VPS storage/deletion adapter executes an authorized release decision but does not decide whether release is safe.

### Steps

1. The caller identifies the Registry `project_id` or exact Cabinet working set targeted by the manual release request. Registry inactivity, archive state, or synchronization success alone never creates this trigger.
2. `module:retention_release` first resolves the exact target membership through `capability:synchronization.get_working_set_membership`, then evaluates the request through `capability:retention_release.evaluate_vps_release`, gathering the exact durable-acceptance evidence required from `module:durable_archive` and relevant replica/synchronization observations from `module:synchronization`.
3. `module:durable_archive` proves whether every required local source replica for the target working set is present and verified in durable local storage. Network delivery alone is insufficient evidence.
4. If any required local replica is missing or unverified, the release decision is blocked and the VPS working copy remains intact.
5. If the preconditions are satisfied, `capability:retention_release.request_manual_vps_release` records the explicit release decision and its evidence/history. Repeating the same accepted release request is idempotent at the decision level, and `capability:retention_release.get_retention_status` may read the exact persisted decision without claiming physical deletion.
6. The VPS adapter may then perform the physical working-copy release authorized by that recorded decision and report the technical execution result. It may not broaden the selected working set or reinterpret Registry status as deletion authority.
7. Technical deletion/release failure leaves the policy decision/evidence auditable and must not be represented as completed physical release until the adapter confirms the effect.

### Outcomes

Observable outcomes include release blocked because durable-local evidence is insufficient, release authorized with an exact affected working set, and release completed or technically failed after authorization.

Successful synchronization by itself always leaves the VPS working copy intact. Current Registry status changes do not automatically trigger this flow and `archived` is not treated as a deletion command.

### Errors

`module:durable_archive` owns durable-evidence verification failure. `module:synchronization` owns transport/replica observation errors. `module:retention_release` owns the allow/block release decision and its audit history.

The physical VPS storage adapter owns only technical execution/reporting after an explicit authorized decision. It must not weaken the durable-local precondition or create automatic release policy.
