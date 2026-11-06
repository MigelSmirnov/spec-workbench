# State 2 — Invariants, rules, config, and constants

## Status

**Authoring pass State 2. Builds on `00_product.md` and `10_models.md`
(including the email-gateway revision of 2026-07-18). The invariant ledger is
`invariant_ledger.json` in this directory; owners are named here, exact
`owner_function`/landing are filled at States 5–7.**

Decisions made at this state and surfaced explicitly (not silently):

1. **Sessions use fixed expiry without sliding renewal.** A staff session
   ends at its TTL and requires re-login; a viewer re-enters through their
   capability link. Simplest session model for a sole-operator business; a
   renewal policy would be a new product decision.
2. **Self-service password reset requests are allowed** (a consequence of the
   email-gateway decision): anyone may submit an email address; the response
   never reveals whether an account exists; a token is issued and delivered
   only for an existing verified address.
3. **Config default values below were confirmed by the product owner on
   2026-07-19.** They remain runtime knobs, not architecture.

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

## Rules — normative tables

### R1. Capability catalog (closed)

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

### R2. Principal-type / role capability sets (static, closed)

| Principal | Capabilities |
| --- | --- |
| viewer (ClientViewer) | all `*.read`, scoped by active `ProjectViewerGrant` |
| operator | all `*.read` + all `*.manage` except `access.manage` + `estimate_snapshot.activate`, scoped by active `StaffProjectAssignment` |
| administrator | operator capability set + `portal.access.manage`; project scope is the current single administrative area |
| estimate_producer (ServicePrincipal) | `estimate_snapshot.import` + `estimate_snapshot.read_import_result`, scoped by `scope_mode`/grants |

Capability sets are read-only rules data; no runtime editing. A role or
capability is never read from request data.

### R3. Status transition tables

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

### R4. Authorization guard sequence (policy)

Every project-scoped operation evaluates, in order: valid unexpired
unrevoked session → principal status `active` (and verified email for
staff) → project access (viewer grant / staff assignment semantics / producer
scope) → required capability from R2 → Registry lifecycle policy (R5).
First failure wins; failures are indistinguishable to the caller regarding
account/project existence beyond what their own access already proves.

### R5. Registry status policy

| Registry state | Portal reads | Portal mutations |
| --- | --- | --- |
| `active` | allowed | allowed (with capability) |
| `archived` | allowed | rejected (`archived_project`) |
| unknown project | rejected | rejected (`unknown_project`) |

Only `active` and `archived` are accepted status literals; any other value
is a `schema_mismatch` boundary failure. Mutation guards call `validate`
server-side before every linked write; archival never revokes grants.

### R6. Registry failure translation (gateway-owned)

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

### R7. Supported external contract versions

```text
ocr_supported_contract_versions      = {1}
snapshot_supported_contract_versions = {1}
```

Closed sets; an unsupported version is a typed rejection, never a best-effort
parse.

### R8. Idempotency identity table

| Fact | Identity | Replay behavior |
| --- | --- | --- |
| Expense | `recognized_document_id` + canonical `intake_fingerprint` | same fingerprint → existing Expense/Document; different fingerprint → integrity conflict, nothing changed |
| ProgressPhoto | `intake_id` | return existing photo |
| WorkPayment | `payment_id` (command-supplied UUID) | return existing payment |
| ApprovedEstimateSnapshot | `(project_id, estimate_id, estimate_version)` + `content_fingerprint` | same fingerprint → existing snapshot (`idempotent_replay`); different → `integrity_conflict`, nothing stored |

### R9. Money policy

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

### R10. Email challenge policy

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

### R11. Revocation cascade table

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

### R12. Producer scope rule

`scope_mode = all_projects` → import allowed for any existing active
project. `scope_mode = granted_projects` → import allowed only with an
active `ProducerProjectGrant` for the target project; otherwise
`scope_denied`. Scope is checked before snapshot content validation.

### R13. Audit action catalog (closed)

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

### R14. Binary delivery policy

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

### R15. Deterministic project-list ordering

- `registry_gateway.list_active_projects` normalizes its otherwise unordered
  typed result by `project_id` ascending so identical Registry facts produce
  identical gateway output.
- `derived_views.list_viewer_projects` orders ProjectListItem by
  `display_name.casefold()` ascending without changing the stored/displayed
  name, then `project_id` ascending as the stable tie.
- Registry is never credited as the source of either order. Pagination remains
  absent for the current few-project operating profile; adding it requires an
  explicit cursor/limit contract rather than truncating silently.

### R16. Staff email and password policy

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

### R17. Verification-secret envelope

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

## Config

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

## Unresolved at State 2

- Mandatory MFA for staff (open product question; architecture unaffected).
- Administrative-area boundaries (dormant until a second area exists).
- PresuPro→Portal transport binding (bearer/signed/mTLS) — resolved by the
  ServiceCredential model regardless of transport.
- External binary deletion/retention after source intake.

## State 2 readiness assessment

- Every invariant has a stable ledger id, one owning responsibility, and an
  expected landing class.
- All policy tables are rules data, not prose; every enum referenced by a
  table exists in `10_models.md`.
- Config is separated from rules by change-reason; no value is hidden in
  notes.
- No invariant is owned by "the whole system"; guard order, cascade
  semantics, and idempotency identities are explicit.
