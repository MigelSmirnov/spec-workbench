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
> 3. **Config default values below were confirmed by the product owner on
>    2026-07-19.** They remain runtime knobs, not architecture.

## Classification principles

- `config` — deployment/runtime knobs that change without redesign (URLs,
  timeouts, TTLs, rate limits, hashing parameters).
- `rules` — closed normative semantics: capability tables, transition
  tables, translation tables, policy constants (rounding, identity keys).
- `models` — typed schemas and closed enums (already in `10_models.md`).
- `notes` — behavior that applies the above (States 6–7).

## Invariant ledger overview

Full statements live in `invariant_ledger.json`. Owners and expected primary
landings:

| ID range | Area | Owning responsibility | Expected landing |
| --- | --- | --- | --- |
| INV-001…INV-016 | IAM: sessions, capabilities, secrets, challenges | authorization guard; authentication flows; credential storage; email challenge flow | notes (+ rules for capability/transition tables; properties where pure) |
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

- INV-002: a check against the rules table at `_require_capability` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.capability_catalog` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

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

- INV-007: a check against the rules table at `_require_capability` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.principal_capability_sets` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A3 — R3. Status transition tables

### Normative rules

```text
StaffStatus:      pending_verification → active;  active ↔ suspended;
                  active|suspended → disabled (terminal)
ViewerStatus:     active → revoked (terminal)
PrincipalStatus:  active ↔ disabled
GrantStatus:      active → revoked (terminal)
BudgetVersionStatus: inactive → active → inactive (re-activation allowed
                  while the project is active; ≤1 active per project)
Challenges/tokens: issued → consumed | expired | revoked (all terminal)
```

Transitions outside these tables are rejected.

### Formal invariants

- INV-014: a staff account authenticates only in active status with a verified email; pending_verification cannot log in

### Required tests

- INV-014: a focused test at `authenticate_staff` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.status_transitions` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A4 — R4. Authorization guard sequence (policy)

### Normative rules

Every project-scoped operation evaluates, in order: valid unexpired
unrevoked session → principal status `active` (and verified email for
staff) → project access (viewer grant / staff assignment semantics / producer
scope) → required capability from R2 → Registry lifecycle policy (R5).
First failure wins; failures are indistinguishable to the caller regarding
account/project existence beyond what their own access already proves.

### Formal invariants

- INV-001: every project-scoped operation passes the guard sequence: valid session, active principal (verified email for staff), project access, required capability, Registry lifecycle policy; first failure wins
- INV-004: authentication and challenge flows never reveal account or viewer existence; auth failures never expose project data
- INV-017: an operator may access a project only through one active StaffProjectAssignment; revocation blocks the next project-scoped authorization check immediately; current administrators derive project scope from the single administrative area policy
- PLAT-REG-003: a linked mutation succeeds only after server-side typed validation reports the same UUID as active
- PLAT-REG-004: client-supplied Registry context is never authoritative

### Required tests

- INV-001: a focused test at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- INV-004: a focused test at `conceal_authentication_failure` showing the invariant holds; a violating input is refused and changes nothing.
- INV-017: a focused test at `_require_staff_scope` showing the invariant holds; a violating input is refused and changes nothing.
- PLAT-REG-003: a focused test at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- PLAT-REG-004: a focused test at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.project_guard_sequence` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A5 — R5. Registry status policy

### Normative rules

| Registry state | Portal reads | Portal mutations |
| --- | --- | --- |
| `active` | allowed | allowed (with capability) |
| `archived` | allowed | rejected (`archived_project`) |
| unknown project | rejected | rejected (`unknown_project`) |

Only `active` and `archived` are accepted status literals; any other value
is a `schema_mismatch` boundary failure. Mutation guards call `validate`
server-side before every linked write; archival never revokes grants.

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

### Consequence

The table is rules data: `rules.registry_status_policy` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A6 — R6. Registry failure translation (gateway-owned)

### Normative rules

| Condition | `RegistryFailureKind` |
| --- | --- |
| malformed UUID input | `invalid_uuid` |
| `exists=false` | `not_found` |
| `is_active=false`, `exists=true` | `archived` |
| request timeout | `timeout` |
| connection/transport error | `transport_error` |
| non-success HTTP status | `http_error` |
| undecodable/invalid response body | `schema_mismatch` |
| response UUID ≠ requested UUID | `identity_mismatch` |

No silent fallback to client-supplied context, cache, or fabricated success.

### Formal invariants

- PLAT-REG-005: Registry failures translate through the closed RegistryFailureKind table; no silent fallback to cached, client-supplied, or fabricated context

### Required tests

- PLAT-REG-005: a focused test at `_translate_registry_failure` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.registry_failure_translation` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A7 — R7. Supported external contract versions

### Normative rules

```text
ocr_supported_contract_versions      = {1}
snapshot_supported_contract_versions = {1}
```

Closed sets; an unsupported version is a typed rejection, never a best-effort
parse.

### Formal invariants

- INV-031: an Expense is created only from a confirmed, complete normalized result with a supported contract version; confidence, provider fields, and raw responses are never persisted

### Required tests

- INV-031: a focused test at `_project_expense_intake` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.supported_external_contract_versions` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A8 — R8. Idempotency identity table

### Normative rules

| Fact | Identity | Replay behavior |
| --- | --- | --- |
| Expense | `recognized_document_id` + canonical `intake_fingerprint` | same fingerprint → existing Expense/Document; different fingerprint → integrity conflict, nothing changed |
| ProgressPhoto | `intake_id` | return existing photo |
| WorkPayment | `payment_id` (command-supplied UUID) | return existing payment |
| ApprovedEstimateSnapshot | `(project_id, estimate_id, estimate_version)` + `content_fingerprint` | same fingerprint → existing snapshot (`idempotent_replay`); different → `integrity_conflict`, nothing stored |

### Formal invariants

- INV-009: at most one active grant per (viewer_id, project_id) and per (service_principal_id, project_id)
- INV-021: re-publication with identical (project, estimate_id, estimate_version) and identical fingerprint is an idempotent replay; a different fingerprint for the same identity is an integrity conflict storing nothing
- INV-030: one recognized_document_id creates at most one Expense and one ExpenseDocument; equal intake_fingerprint replay returns the existing records, while a different fingerprint is an integrity conflict changing nothing
- INV-042: a WorkPayment is idempotent by payment_id and is never a factura or accounting posting; payments total is derived
- INV-043: a ProgressPhoto is idempotent by intake_id; the gallery is chronological; visibility changes never alter financial or progress data

### Required tests

- INV-009: a focused test at `PortalTransaction.commit` showing the invariant holds; a violating input is refused and changes nothing.
- INV-021: a check against the rules table at `_classify_snapshot_replay` showing the invariant holds; a violating input is refused and changes nothing.
- INV-030: a focused test at `create_expense_from_recognition` showing the invariant holds; a violating input is refused and changes nothing.
- INV-042: a focused test at `register_work_payment` showing the invariant holds; a violating input is refused and changes nothing.
- INV-043: a focused test at `publish_progress_photo` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.idempotency_identities` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A9 — R9. Money policy

### Normative rules

- Currency literal: `EUR` only; any other currency at any boundary →
  explicit typed rejection (`currency_mismatch`).
- `Decimal`, 2 fraction digits, `ROUND_HALF_UP` at derivation boundaries;
  stored amounts are already 2-digit exact.
- All amounts gross (IVA included); snapshot `tax_mode` is provenance only.
- Completed work value: `work_planned × completion_percent / 100`, rounded
  half-up to 2 digits per section, summed after rounding.
- Overall progress: `Σ(work_planned × percent) / Σ(work_planned)` over
  sections of the active version with `work_planned > 0`; undefined (shown
  unavailable) when the denominator is 0.
- Work balance: `completed work value − payments total`; sign selects the
  presentation label (`Completed ahead of payments` / absolute value as
  `Unused advance payment`).

### Formal invariants

- INV-037: all monetary values are EUR with decimal 2-digit semantics and ROUND_HALF_UP; foreign currency input is rejected explicitly, never converted
- INV-041: completed work value and overall progress follow the R9 formulas; overall progress is unavailable, never guessed, when no planned work cost exists
- INV-044: remaining materials show overspend as negative values, never clamped or hidden; missing data is presented explicitly, never replaced by zero unless zero is confirmed

### Required tests

- INV-037: a check against the rules table at `validate_eur_amount` showing the invariant holds; a violating input is refused and changes nothing.
- INV-041: a check against the rules table at `calculate_overall_progress` showing the invariant holds; a violating input is refused and changes nothing.
- INV-044: the ledger's property at `calculate_material_balance` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.money_policy` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A10 — R10. Email challenge policy

### Normative rules

| Purpose | Model | TTL config key | Issued by |
| --- | --- | --- | --- |
| email verification | `EmailVerificationChallenge` | `email_verification_ttl_hours` | administrator |
| email change | `PendingEmailChange` | `email_change_ttl_hours` | account or administrator |
| password reset | `PasswordResetToken` | `password_reset_ttl_minutes` | self-service or administrator |

Common policy: purpose-bound (a token is consumable only by its own flow);
single-use; revocable; plaintext exists only in the delivered message;
issuing a new challenge of the same purpose revokes outstanding ones for
that account; per-account issuing is rate-limited
(`email_challenge_rate_limit_per_hour`); delivery outcome never affects
challenge validity; flow responses never reveal account existence.

Notification kinds sent without tokens: `password_changed_notice` (to the
account email), `email_changed_notice` (to the previous email),
`account_security_notice` (suspension/disabling).

### Formal invariants

- INV-010: challenge tokens are purpose-bound, single-use, time-limited, revocable; replay and cross-flow use are rejected
- INV-012: a new email becomes the login identifier only when its PendingEmailChange is consumed; the previous address is notified after completion
- INV-013: email delivery success or failure never confirms address ownership or affects challenge validity
- INV-015: administrative recovery override is an exceptional flow with enhanced audit, never the primary email-change mechanism
- INV-016: issuing a new challenge of one purpose revokes outstanding challenges of that purpose for the account; issuing is rate-limited per account

### Required tests

- INV-010: a check against the rules table at `_issue_challenge` showing the invariant holds; a violating input is refused and changes nothing.
- INV-012: a focused test at `confirm_email_change` showing the invariant holds; a violating input is refused and changes nothing.
- INV-013: a focused test at `deliver_email_message` showing the invariant holds; a violating input is refused and changes nothing.
- INV-015: a focused test at `perform_recovery_override` showing the invariant holds; a violating input is refused and changes nothing.
- INV-016: a check against the rules table at `_issue_challenge` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.email_challenge_policy` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A11 — R11. Revocation cascade table

### Normative rules

| Revoked object | Immediate effect |
| --- | --- |
| ClientViewer | all viewer sessions invalid; credential unusable; grants untouched (records kept) |
| ViewerAccessCredential | new entries impossible; existing sessions invalid |
| ProjectViewerGrant | that project disappears from the viewer's scope; other grants unaffected |
| StaffProjectAssignment | that project disappears from the staff account's scope; other assignments unaffected |
| StaffAccount suspended/disabled | all staff sessions invalid; outstanding challenges revoked; security notice sent |
| ServicePrincipal disabled | all its credentials unusable |
| ServiceCredential | that credential unusable; other credentials of the principal unaffected (rotation overlap) |

"Immediate" means the next authorization check observes the revocation; no
grace period.

### Formal invariants

- INV-005: a revoked grant, credential, viewer, or session blocks the next authorization check immediately, per the revocation cascade table
- INV-006: a suspended or disabled staff account and a disabled service principal have no valid sessions or usable credentials
- INV-008: at most one non-revoked ViewerAccessCredential per viewer; re-issue revokes the previous credential atomically
- INV-011: successful password reset revokes all active staff sessions and all outstanding reset tokens of the account and sends a password-changed notice

### Required tests

- INV-005: a check against the rules table at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- INV-006: a check against the rules table at `_authorize_project_operation` showing the invariant holds; a violating input is refused and changes nothing.
- INV-008: a focused test at `issue_viewer_access` showing the invariant holds; a violating input is refused and changes nothing.
- INV-011: a focused test at `complete_password_reset` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.revocation_cascades` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A12 — R12. Producer scope rule

### Normative rules

`scope_mode = all_projects` → import allowed for any existing active
project. `scope_mode = granted_projects` → import allowed only with an
active `ProducerProjectGrant` for the target project; otherwise
`scope_denied`. Scope is checked before snapshot content validation.

### Formal invariants

- INV-029: a producer import is authorized for the target project per scope_mode and grants before content validation

### Required tests

- INV-029: a focused test at `authorize_snapshot_import` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.producer_scope_policy` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A13 — R13. Audit action catalog (closed)

### Normative rules

```text
viewer.create viewer.revoke viewer.credential_issue viewer.credential_revoke
grant.create grant.revoke
staff_assignment.create staff_assignment.revoke
staff.create staff.login staff.login_failed staff.logout
staff.sessions_revoke staff.suspend staff.reinstate staff.disable
staff.email_verification_issue staff.email_verified
staff.email_change_request staff.email_changed
staff.password_reset_request staff.password_reset_complete
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
enhanced detail via its entity reference. Rejected attempts of significant
mutations are audited with `result = rejected` and a `reason_code`.

### Carried changes

The accepted Factory spec adds two policies beside the catalog (Factory `5677993e`, 2026-07-22): `rules.audit_significant_mutation_actions`, the closed subset of the catalog whose rejected attempts are audited (the "significant mutations" above, now listed), and `rules.audit_result_reason_policy`: a success carries no `reason_code`, a rejected significant mutation carries a non-blank one, a rejected non-significant action may carry one.

### Formal invariants

- INV-051: every action in the audit catalog writes exactly one AuditRecord with actor provenance; service actors record key_version
- INV-053: rejected significant mutations are audited with result=rejected and a closed reason_code

### Required tests

- INV-051: a focused test at `append_audit` showing the invariant holds; a violating input is refused and changes nothing.
- INV-053: a focused test at `append_audit` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.audit_action_catalog` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

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

- INV-034: a focused test at `_build_expense_aggregate` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.binary_delivery_policy` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

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

### Consequence

The table is rules data: `rules.project_list_ordering` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A16 — R16. Staff email and password policy

### Normative rules

- Staff login email is stripped of surrounding whitespace, syntax-validated,
  Unicode-casefolded, and stored/compared in that normalized form. No
  provider-specific dot removal, plus-tag removal, or domain rewriting occurs.
- A new password is 12–128 Unicode code points, contains no NUL/control
  characters, and is hashed exactly as supplied. The portal never trims,
  casefolds, or Unicode-normalizes password plaintext.
- No character-class composition ritual is required. A future breached-
  password service is a separate explicit boundary, not an implicit network
  call during hashing.
- Password plaintext is accepted only by create/change/reset operations and
  handed immediately to `credential_security`; it never enters audit or
  delivery records.

### Formal invariants

- INV-018: staff login email uniqueness and lookup use the R16 trimmed syntax-valid Unicode-casefolded form without provider-specific rewriting
- INV-019: new staff passwords satisfy R16 length/control-character policy and are hashed exactly as supplied without trimming or normalization

### Required tests

- INV-018: a check against the rules table at `_normalize_staff_email` showing the invariant holds; a violating input is refused and changes nothing.
- INV-019: a check against the rules table at `_validate_new_password` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.staff_identity_input_policy` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

## Accepted decision A17 — R17. Verification-secret envelope

### Normative rules

- Every portal-issued session/challenge/viewer/service plaintext token encodes
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

- INV-003: passwords, session tokens, viewer access tokens, service credentials, and challenge tokens are stored only in verification/hash form and never logged

### Required tests

- INV-003: a focused test at `issue_verification_secret` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

The table is rules data: `rules.verification_envelope_policy` (SPEC_STANDARD 15.3.1, a rules table). The owning functions named in the tests carry it by address.

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

- INV-020: a focused test at `import_snapshot` showing the invariant holds; a violating input is refused and changes nothing.
- INV-022: a focused test at `activate_budget_version` showing the invariant holds; a violating input is refused and changes nothing.
- INV-023: a focused test at `activate_budget_version` showing the invariant holds; a violating input is refused and changes nothing.
- INV-024: a focused test at `upsert_manual_section_plan` showing the invariant holds; a violating input is refused and changes nothing.
- INV-025: a focused test at `_link_snapshot_sections` showing the invariant holds; a violating input is refused and changes nothing.
- INV-026: a focused test at `import_snapshot` showing the invariant holds; a violating input is refused and changes nothing.
- INV-027: a focused test at `build_budget_view` showing the invariant holds; a violating input is refused and changes nothing.
- INV-028: a focused test at `PortalTransaction.commit` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7).

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
- INV-033: a focused test at `_build_replacement_allocations` showing the invariant holds; a violating input is refused and changes nothing.
- INV-035: a focused test at `_project_expense_summary` showing the invariant holds; a violating input is refused and changes nothing.
- INV-036: a focused test at `validate_project_section` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7).

## Accepted decision A20 — Progress invariant

### Normative rules

The former ledger row INV-040; product text of State 0 ("Operator management") and M32.

### Formal invariants

- INV-040: completion percent is a manual staff value in [0,100]; photographs never set progress

### Required tests

- INV-040: a focused test at `set_section_progress` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7).

## Accepted decision A21 — Derivation and append-only records

### Normative rules

The former ledger rows INV-050 and INV-052; product text of State 0 ("Derived values", "Audit") and M19, M20, M36.

### Formal invariants

- INV-050: all derived values are deterministic and recomputable from owning records for the same accepted inputs
- INV-052: audit records and import records are append-only; no flow mutates or deletes them

### Required tests

- INV-050: a focused test at `build_project_overview` showing the invariant holds; a violating input is refused and changes nothing.
- INV-052: a focused test at `PortalTransaction.commit` showing the invariant holds; a violating input is refused and changes nothing.

### Consequence

No value: each invariant is behaviour of its owning function and lands as a note or a property there (States 6–7).

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

- No transaction is rolled back twice, rolled back after a commit, or left open.
- A domain error raised inside a guarded transaction reaches the caller
  unchanged, never masked by a persistence error of the closed transaction.

### Required tests

- A focused test per use-case module that instruments the store, rejects a
  nested begin and requires exactly one close per call (Factory focused
  checks `*_uow_check`, `0f9ae3ae`, `7eb7ebcc`).

### Consequence

`rules.transaction_guard_policy`, a rules table; the guard notes of every
use case address it.

## Accepted decision A23 — Audit entity id policy (accepted Factory spec, 2026-07-26)

### Normative rules

`AuditIntent.entity_id` is the canonical string form of the audited entity's
identifier, produced by converting the UUID to a string; it is absent only
when the audited entity has no identifier of its own. A UUID object, a
hyphen-stripped, truncated or upper-cased form, or another entity's
identifier is forbidden. Normative value: `rules.audit_entity_id_policy`
(Factory `0f9ae3ae`).

### Formal invariants

- Every audit record's `entity_id` equals the canonical string of the audited
  entity's id, or is absent when that entity has none.

### Required tests

- A writer test that rejects a UUID object and a non-canonical string for
  `entity_id`, and a consumer test per audited mutation that reads the record
  back.

### Consequence

`rules.audit_entity_id_policy`; every audit-appending note addresses it.

## Accepted decision A24 — Records are immutable values (accepted Factory spec, 2026-07-26)

### Normative rules

Model instances are frozen. No code assigns to a field of an argument or of a
value read from a repository, and no result travels back to a caller through
a mutated input. A changed value is a new instance built from the old one.
Normative value: `rules.model_immutability_policy` (Factory `bd561732`).

### Formal invariants

- A value read from a repository is unchanged after any use case that read it.

### Required tests

- A test per revocation cascade that the read record is untouched and the
  replacement carries the change.

### Consequence

`rules.model_immutability_policy`; State 1 models are frozen.

## Accepted decision A25 — HTTP transport policy (accepted Factory spec, 2026-07-31 to 2026-08-06)

### Normative rules

The public API lives under `/api`, stripped by the deployment proxy. The
service answers only on its trusted hosts (at least one, no wildcard at any
position); CORS is off when its allowlist is empty, and an allowed origin is
never a wildcard. Request bodies and binary responses are bounded by runtime
settings before expensive work; viewer entry attempts are rate limited per
client network address and route, with bounded memory and a concealed answer,
the address read only from the connection, never from a forwarded header,
cookie or secret. Logs redact authorization, cookie and secret-like names.
Fixed security headers are sent; credential and session answers are
`no-store`. Liveness and readiness are public and change nothing (R0-11). The
viewer browser session is the host-only cookie of R0-09; mutating viewer
requests must come from the canonical public origin, compared by scheme, host
and effective port, with no pattern matching. Service principals use bearer
headers only. Normative value: `rules.http_transport_policy` (Factory
`38626cc7`, `21658368`, `e8a61895`, `35a0a09c`, `dc351917`, `51d19fdf`).

### Formal invariants

- No request reaches a handler on an untrusted host or with an oversize body.
- No viewer mutation succeeds from a foreign origin or without the cookie.
- No credential, cookie or secret appears in a log line.

### Required tests

- Factory focused checks `client_portal_transport_guard`,
  `client_portal_api_transport_check` and `runtime_settings_client_portal`
  (`babd5e52`, `3080ef0d`, `dc351917`).

### Consequence

`rules.http_transport_policy` with its runtime settings (A30); the
deterministic HTTP router and the viewer cookie backend read it.

## Accepted decision A26 — Exceptions carry data in fields, not messages (accepted Factory spec, 2026-08-03)

### Normative rules

An exception message is never a data channel. `RegistryBoundaryError` carries
its `RegistryFailureKind` in a `kind` field and `SnapshotContentRejected` its
`ImportRejectReason` in a `reason` field; callers classify by the field.
Normative value: `rules.exception_payload_policy` (Factory `a12937fd`).

### Formal invariants

- A snapshot import rejection's recorded reason equals the raised exception's
  `reason`, whatever its message text.

### Required tests

- A snapshot import test per `ImportRejectReason` value.

### Consequence

`rules.exception_payload_policy`.

## Accepted decision A27 — Derived view orderings (accepted Factory spec, 2026-08-09; owner 2026-11-06)

### Normative rules

Expenses are ordered by document date descending, then creation time
descending, then id descending; an expense's allocations by creation time
ascending, then id ascending; payments by payment date descending, then
recording time descending, then id descending; photos by photo date
ascending, then publication time ascending, then id ascending. Normative
value: `rules.derived_view_ordering` (Factory `d2c4511e`).

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

### Consequence

`rules.derived_view_ordering`; `01_models.md` "Projections and answers"
records the replacement.

## Accepted decision A28 — Clock policy (accepted Factory spec, 2026-08-09)

### Normative rules

Persisted timestamps are UTC, stored as offset-naive datetimes. Each operation
reads the clock once (`datetime.utcnow()`), and that one instant supplies every
timestamp it writes and every current-time comparison that decides the validity
of those writes or of persisted records. Reading local time, an offset-aware
persisted timestamp and a second clock read within one operation are
forbidden. Normative value: `rules.clock_policy` (Factory `c92b6878`). This
narrows the former convention "Timestamps are timezone-aware UTC" of State 1:
the instants are UTC, their stored form is offset-naive.

### Formal invariants

- All timestamps written by one operation are equal.

### Required tests

- A test per multi-write operation (activation, revocation cascades,
  bootstrap) that its written timestamps are one instant.

### Consequence

`rules.clock_policy`.

## Accepted decision A29 — First-administrator bootstrap policy (accepted Factory spec, 2026-08-17)

### Normative rules

R0-07 made exact. The local command creates the single first staff account
on an empty staff table: role administrator, status active, email verified,
no creator; its audit is `staff.create` by the system actor with the created
`staff_id`, result success. The emptiness check and both inserts run in one
immediate write transaction, so concurrent attempts create exactly one
account; when any staff account exists the command refuses with
`BootstrapAlreadyCompleted` and nothing persists. The password is kept only
as its hash; email and password are read neither from process arguments nor
the environment nor a file and are never written to output, logs, audit,
return values or exception messages. There is no HTTP route and no API
description entry. Exit codes are a closed external contract: 0 account
created, 1 confirmation did not match, 2 identity input rejected, 3 bootstrap
already completed. Normative value: `rules.staff_bootstrap_policy` (Factory
`6011ac93`).

### Formal invariants

- At most one account is ever created by the command, and only on an empty
  staff table.
- The exit code of each outcome is the one listed.

### Required tests

- A bootstrap test on an empty and a non-empty store, with two concurrent
  attempts, and one per exit code.

### Consequence

`rules.staff_bootstrap_policy`; the bootstrap modules of State 3 own it.

## Accepted decision A30 — Configuration

### Normative rules

The former configuration, kept (owner-confirmed defaults, R0-06):

Runtime knobs with confirmed defaults (deployment values may differ):

```text
registry_endpoint_env_name            = REGISTRY_BASE_URL
registry_timeout_seconds               = 5
email_gateway_url_env_name             = EMAIL_GATEWAY_URL
email_gateway_timeout_seconds         = 10
staff_session_ttl_hours                = 12
viewer_session_ttl_days                = 30
email_verification_ttl_hours           = 72
email_change_ttl_hours                 = 24
password_reset_ttl_minutes             = 60
email_challenge_rate_limit_per_hour    = 5
credential_entropy_bytes               = 32
credential_hash_scheme                 = argon2id (library defaults)
binary_read_limit_env_name             = BINARY_MAX_READ_BYTES (required positive integer)
```

Values are knobs; the *existence* of a timeout/TTL/rate limit is an
invariant, its value is config.

### Carried changes

- `binary_read_limit_env_name` now addresses its environment variable entry,
  `= config.runtime_environment_variables.variables.BINARY_MAX_READ_BYTES`
  (Factory `a6916180314d`).
- `config.registry_request_paths`: the Registry paths are fixed as
  `projects`, `projects/{project_id}/validate`, `projects/{project_id}/context`
  (Factory `300bd11d`). State 0 names `/projects/active` for the active list;
  the accepted spec reads `projects` and keeps only active projects while
  decoding. Registry v1 serves both paths (`projects/registry_sandbox/api/runtime.py`).
  Which Registry endpoint the gateway calls is an external contract of State 6
  (EXTERNAL_CONTRACT_EVIDENCE); recorded there, not decided here.
- `config.runtime_environment_variables`: the closed table of environment
  variables, their types, requiredness, normalization and per-environment
  defaults, read into `RuntimeSettings` (R0-10; Factory `a6916180314d`,
  `51d19fdf`).
- `config.persistence`: the storage schema revision and table names (Factory
  `48a49aa6` … `d1280708`), carried by the persistence closure.

### Formal invariants

- The existence of every timeout, TTL, rate limit and bound is invariant; its
  value is configuration.

### Required tests

- `runtime_settings_client_portal`: an invalid or missing required variable
  stops start-up.

### Consequence

`config.*` (SPEC_STANDARD 15.3.1, runtime settings and configuration).

## Accepted decision A31 — Security review of the migrated case

### Normative rules

The total review of `SECURITY_REVIEW_EVIDENCE.md` over States 0–2 as migrated.
It decides nothing new: each applicable category is owned by a decision above.

### Formal invariants

- Every category resolves to an accepted decision or an open question.

### Required tests

- `python tools/design_lint.py examples/client-portal --state 2`.

### Consequence

State 3 may start only when no category is UNRESOLVED.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A3, A4, A10, A11, A16, A17, A25; affected: M01-M15, staff login, viewer entry, producer bearer authentication
- secrets: APPLICABLE; references: A16, A17, A25, A29; affected: M02, M03, M05, M06, M08-M10, M14, issued secrets, logs
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
   source.
2. A pin changes only through the Factory route, like any other deployed
   source change; nothing updates a dependency at run time or on the host.
3. Before a deploy, the pinned versions are checked against a public
   known-vulnerability database; a pin with a known vulnerability that affects
   the portal is not deployed until it is updated through the Factory route.
4. The portal adds no runtime feature for this: no update service, no
   network call at start, no dependency report on any API.

This describes the existing deployment and answers OQ-17 and
`open_questions.md` Q17.

### Formal invariants

- Every library the running portal imports from outside its own source is
  pinned to one exact version in the deployment requirements.
- No deploy ships a pin with a known vulnerability affecting the portal.

### Required tests

- The deployment requirements contain only `==` pins, one per direct import.
- The pre-deploy vulnerability check of those pins passes.

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
- `rules.http_router_backend` (56 routes, Factory `300bd11d` … `a6916180314d`)
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
- Administrative-area boundaries (dormant until a second area exists).
- PresuPro→Portal transport binding (bearer/signed/mTLS) — resolved by the
  ServiceCredential model regardless of transport.
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
