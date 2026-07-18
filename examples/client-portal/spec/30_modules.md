# State 3 — Module responsibilities

## Status

**Authoring pass State 3. Builds on `00_product.md`, `10_models.md`, and
`20_rules.md`. This state assigns ownership; candidate operations are not yet
contracts. Exact signatures, repository methods, HTTP shapes, and internal
helpers remain deferred to States 4–6.**

The decomposition favors a small number of deep semantic modules while
keeping integration mechanics and HTTP routing outside domain policy. The
sole-trader operating constraint argues against microservices or one package
per entity, but it does not justify a generic `manager`, `service`, or
repository that owns unrelated decisions.

## Cross-cutting decisions

### Semantic module versus generation unit

- `models` is one deterministic runtime generation unit at `core/models`, as
  required by the current Factory profile. The conceptual IAM, budget,
  expense, and integration model groups in `10_models.md` are not separate
  generated model packages.
- A semantic module may later need more than one internal generation unit,
  but callers depend only on the public module key listed here.
- Internal pipeline stages, repository helpers, serializers, token hashing,
  and HTTP decoders are not public capabilities merely because code
  generation may place them in separate files.

### Persistence and transaction boundary

`portal_store` is the concrete persistence boundary for this target. It owns
ORM mappings, queries, optimistic/uniqueness conflict translation, and
transaction commit/rollback. It exposes typed domain-oriented persistence
capabilities to owning modules and must not decide authorization, lifecycle,
idempotency, formulas, or audit policy.

This is one adapter package for operational simplicity, not one generic
`save(data)` API. State 5 must keep its public surface typed and grouped by
aggregate; State 6 must not introduce `dict`, `Any`, raw SQLAlchemy sessions,
or repository-global transaction state into domain contracts. If the target
Factory proves complete `kind: interface` materialization before assembly,
the same boundary may be expressed as narrow ports; otherwise a concrete
facade preserves the semantic dependency without inventing unsupported
Protocol surfaces.

Owning use cases determine transaction scope. Registry and email network I/O
must occur outside a portal database transaction. Atomic requirements such as
credential re-issue, expense correction plus allocation replacement, budget
activation, and snapshot acceptance are committed through `portal_store` as
one transaction.

### Binary storage boundary

`binary_storage` is an opaque read boundary behind `file_ref`.

- OCR/Telegram intake remains responsible for placing the binary and
  supplying a stable reference; the portal does not become an upload or
  recognition system.
- Domain modules decide whether an authenticated actor may access the
  referenced ExpenseDocument or ProgressPhoto.
- Only after that decision may `binary_storage` resolve the opaque reference,
  enforce reference/path/provider safety, inspect object existence and size,
  and read the object or produce the transport artifact selected in State 4.
- Raw filesystem paths, provider credentials, bucket names, and arbitrary
  client-supplied URLs never cross the public domain API. `file_ref` is never
  itself treated as proof of access.
- State 4 selects an authenticated portal stream for the small deployment.
  The storage adapter returns `BinaryPayload`; the API streams it only after
  the owning module repeats object/project/visibility authorization. Signed
  URLs are not part of the current architecture.

`binary_storage` does not delete source binaries when a business record is
hidden, excluded, revoked, or archived. Retention/deletion remains an explicit
external-storage operational policy and is not invented in this pass.

### Audit failure policy

The use case that owns a significant action also owns creation of its audit
intent. `audit_writer` validates and persists the append-only record in the
same portal transaction as a successful mutation, or persists the rejected
attempt in a separate short transaction after the rejection is known. A
successful significant mutation must not commit without its required audit
record. Integration delivery telemetry is not a substitute for domain audit.

## Responsibility map

### `models`

**Owns:** all Pydantic domain and boundary types, enums, closed catalogs, and
local pure validators from `10_models.md`.

**Hides:** generated representation and local closed-choice validation.

**Must not own:** repository lookup, runtime config, Registry/OCR/email I/O,
authorization, rich-file security, cross-record uniqueness, or lifecycle
transitions.

**Public surface:** model, enum, and catalog symbols only; no behavior API.

### `credential_security`

**Owns:** the common cryptographic boundary for passwords and issued bearer
secrets: configured password hashing, verification-form token hashing,
constant-time verification, entropy generation, plaintext lifetime rules, and
redaction-safe failure behavior.

**Hides:** hash-library/provider calls, salt/parameter encoding, random-byte
generation, and comparison details.

**Candidate public capabilities:** `hash_password`, `verify_password`,
`issue_verification_secret`, `parse_verification_secret`, `verify_secret`.

**Must not own:** account/token lifecycle, persistence, authorization,
delivery, HTTP credential extraction, or logging of plaintext. Issuing modules
receive plaintext only for the immediate response/delivery handoff and persist
only its verification form.

**Primary invariant:** INV-003. Credential-owning modules supply lifecycle
context but do not implement independent hashing schemes.

### `staff_identity`

**Owns:** the complete staff identity lifecycle: StaffAccount and
StaffProjectAssignment administration; password verification/change; login,
StaffSession creation/revocation and sign-out; suspension/reinstatement/
disabling; email verification, PendingEmailChange, PasswordResetToken;
purpose binding, TTL, single use, rate limiting, security notifications; and
exceptional administrative recovery.

**Knows:** StaffStatus transitions, verified-email login preconditions,
password hashing policy, fixed session expiry, revocation cascades, and
existence-hiding authentication outcomes.

**Hides:** account lookup normalization, session/challenge issuance and
verification through `credential_security`, outstanding-token revocation,
existence-hiding reset behavior, message construction, and atomic account/
session/challenge sequencing.

**Candidate public capabilities:** `authenticate_staff`, `sign_out_staff`,
`revoke_staff_sessions`, `change_staff_status`, `change_staff_password`,
`assign_staff_project`, `revoke_staff_project_assignment`,
`perform_recovery_override`, `issue_email_verification`,
`confirm_email_verification`, `request_email_change`,
`confirm_email_change`, `request_password_reset`, `complete_password_reset`,
`send_staff_security_notice`.

**Must not own:** email provider transport/delivery outcome, project
authorization, viewer/service credentials, HTTP cookies/headers, or
role-capability tables. Delivery acceptance never decides challenge validity.

**Primary invariants:** INV-010–INV-019, including assignment administration
and credential input policy. INV-003 is owned centrally by
`credential_security`, and
failure disclosure policy by `authorization_guard`.

### `viewer_access`

**Owns:** ClientViewer lifecycle, ViewerAccessCredential issuance/re-issue and
revocation, ViewerSession entry and revocation, ProjectViewerGrant management,
and resolution of a viewer's permitted project IDs.

**Knows:** viewer/grant status transitions, single-current-credential rule,
grant uniqueness, fixed viewer-session expiry, and revocation cascades.

**Hides:** capability secret generation/verification and atomic credential
replacement.

**Candidate public capabilities:** `create_viewer`, `revoke_viewer`,
`issue_viewer_access`, `enter_viewer_access`, `revoke_viewer_access`,
`grant_viewer_project`, `revoke_viewer_project`,
`list_viewer_project_ids`.

**Must not own:** Registry project context, role/capability evaluation,
project-data reads, mutation of portal project facts, or frontend links.

**Primary invariants:** INV-008 and PLAT-REG-007 for viewer-owned data.
INV-005–INV-007 are enforced by `authorization_guard`; INV-009 uniqueness is
owned by `portal_store`; cryptography delegates to `credential_security`.

### `service_identity`

**Owns:** ServicePrincipal lifecycle, ServiceCredential issue/rotation/
revocation, ProducerProjectGrant management, credential authentication, and
resolution of producer project scope.

**Knows:** source-type capability set, scope modes, monotonic key versions,
rotation overlap, and disabled-principal cascade.

**Hides:** secret verification and key-version allocation.

**Candidate public capabilities:** `create_service_principal`,
`change_service_principal_status`, `issue_service_credential`,
`revoke_service_credential`, `grant_producer_project`,
`revoke_producer_project`, `authenticate_service_principal`,
`authorize_producer_scope`.

**Must not own:** snapshot content validation/import, activation, Registry
HTTP, or staff/viewer authentication.

`service_identity` supplies the producer-scope fact consumed by the
`snapshot_import` owner of INV-029. `authorization_guard` owns
disabled-principal enforcement, `portal_store` owns grant uniqueness, and
cryptography delegates to `credential_security`.

### `authorization_guard`

**Owns:** the common R4 decision for one operation: session validity, active
principal, project access, required capability, and Registry lifecycle
policy in the declared order. It returns or raises one stable authorization
decision and prevents callers from duplicating partial checks.

**Knows:** R1–R5, principal-specific scope sources, read-versus-mutation
semantics, and first-failure/existence-hiding policy.

**Hides:** orchestration across identity modules and `registry_gateway`.

**Candidate public capabilities:** `conceal_authentication_failure`,
`authorize_project_read`,
`authorize_project_mutation`, `authorize_access_management`,
`authorize_snapshot_import`.

**Must not own:** session/credential issuance, Registry transport, domain
mutation, HTTP status formatting, or persistence of business facts.

**Primary invariants:** INV-001, INV-002, INV-004–INV-007, PLAT-REG-003 for
the common guard portion. Producer scope is obtained from `service_identity`.

### `registry_gateway`

**Owns:** Registry HTTP calls for active projects, typed validation, and live
context; configured timeout; response decoding; UUID identity matching; and
translation to RegistryFailureKind according to R6.

**Hides:** URLs, HTTP client details, status/body parsing, and transport
exceptions.

**Candidate public capabilities:** `list_active_projects`,
`validate_project_reference`, `get_project_context`.

**Must not own:** portal authorization, grants, mutation policy beyond typed
Registry facts, caching as authority, Registry database/model access, or a
portal-owned Registry snapshot.

**Primary invariants:** PLAT-REG-001, PLAT-REG-002, PLAT-REG-004–006; it
supplies the typed fact used by PLAT-REG-003 and owns INV-054 ordering.

### `email_delivery_gateway`

**Owns:** delivery-only communication with the configured email provider,
translation of provider/timeout results, and update of EmailDeliveryRecord
delivery telemetry.

**Candidate public capability:** `deliver_email_message`.

**Must not own:** challenge issuance/validity, account existence decisions,
authorization, or token storage. It never converts accepted delivery into
verified ownership.

It supplies delivery evidence to `staff_identity`, which remains the single
owner of INV-013 and never treats that evidence as confirmation.

### `binary_storage`

**Owns:** safe resolution and read of opaque `file_ref`, provider/path
boundary checks, size/content metadata verification, and storage-error
translation after domain authorization.

**Candidate public capability:** `read_binary` returning `BinaryPayload` after
the caller supplies an already-authorized opaque reference. Reference
description/validation remains internal.

**Must not own:** actor/project authorization, document/photo visibility,
business retention, OCR, image interpretation, or arbitrary URL fetching.

It supports INV-034 by keeping bytes outside ExpenseDocument; the single
business owner remains `expense_management`. Access invariants remain owned by
the document/photo use case and guard.

### `snapshot_import`

**Owns:** canonical snapshot validation/fingerprint, supported contract and
currency checks, section validation, idempotent/integrity-conflict decision,
append-only ApprovedEstimateSnapshot and SnapshotImportRecord creation, and
the producer-readable import result.

**Knows:** R7–R9, snapshot identity, producer provenance/key version, and the
required ordering: authenticate/authorize scope, validate Registry active,
then validate content, then transact acceptance and audit.

**Hides:** canonicalization and fingerprint algorithm, replay lookup, and
atomic append sequencing.

**Candidate public capabilities:** `import_snapshot`,
`get_snapshot_import_result`.

**Must not own:** activation, PortalSection linking, budget plan mutation,
producer credential management, or Registry transport.

**Primary invariants:** INV-020, INV-021, and INV-029. Budget activation owns
INV-022/INV-026, `financial_policy` owns INV-037, and `portal_store` owns the
append-only persistence constraint in INV-052.

### `budget_management`

**Owns:** manual BudgetVersion creation and SectionPlan editing;
PortalSection identity; imported-version activation; source-key linking;
creation of imported SectionPlans; atomic switch of the active version; and
identification of unresolved allocations after a switch.

**Knows:** R3, stable source-key semantics, single-active/single-manual rules,
manual versus imported mutability, and the prohibition on display-name
matching.

**Hides:** section-linking indexes, activation sequencing, and coexistence of
historical versions.

**Candidate public capabilities:** `ensure_manual_budget`,
`edit_manual_section_plans`, `review_budget_version`,
`activate_budget_version`, `get_active_budget`.

**Must not own:** snapshot authentication/import, expense mutation, derived
financial totals, Registry HTTP, or deletion of referenced section history.

**Primary invariants:** INV-022–INV-026, INV-028, and shared section/project
consistency in INV-036. Derived totals in INV-027 are owned by
`derived_views`.

### `expense_intake`

**Owns:** external OCR wire validation and projection into ExpenseIntake,
confirmed/complete/supported-version enforcement, rejection of provider/raw
fields from persistence, canonical intake fingerprint/replay classification,
initial allocation/document consistency, and atomic authorized ExpenseAggregate
creation with audit.

**Hides:** boundary decoding and projection of the accepted normalized OCR
contract.

**Candidate public capability:** `create_expense_from_recognition`.

**Must not own:** OCR recognition, provider confidence policy, manual expense
creation, arbitrary project selection, or long-term expense correction.

**Primary invariants:** INV-030–INV-031. Currency/amount validation delegates
to the INV-037 owner, `financial_policy`.

### `expense_management`

**Owns:** Expense, ExpenseAllocation, and ExpenseDocument consistency after
creation; include/exclude/correction; explicit allocation replacement; atomic
amount-plus-allocation correction; document description/visibility changes;
and project ownership checks for allocation targets.

**Knows:** R8–R9, exact allocation-sum rule, one-document rule, and active
project mutation policy.

**Hides:** allocation replacement sequencing and uniqueness/conflict handling.

**Candidate public capabilities:** `correct_expense`,
`set_expense_inclusion`, `replace_expense_allocations`,
`update_expense_document`, `read_expense_document`.

**Must not own:** OCR, binary reads, automatic proportional allocation,
budget-plan mutation, or derived totals.

**Primary invariants:** INV-032–INV-034. `derived_views` owns INV-035,
`budget_management` owns shared section/project consistency in INV-036, and
`financial_policy` owns INV-037.

### `project_tracking`

**Owns:** manual SectionProgress updates and WorkPayment registration;
section/project validation; payment idempotency; and retrieval of the owning
records for views.

**Knows:** progress range/manual-source rule, payment identity, and that
payments create no factura/accounting posting.

**Candidate public capabilities:** `set_section_progress`,
`register_work_payment`, `list_project_progress`, `list_project_payments`.

**Must not own:** progress formulas, photo-derived progress, budget editing,
accounting integration, or Registry lifecycle translation.

**Primary invariants:** INV-040 and INV-042. Shared section/project
consistency in INV-036 is owned by `budget_management`.

### `financial_policy`

**Owns:** the shared pure money/progress policy: EUR and two-fraction-digit
validation, ROUND_HALF_UP quantization, section completed-work calculation,
weighted overall progress, remaining-material calculation without clamping,
payment totals, work balance, and unavailable-result semantics.

**Hides:** Decimal quantization and formula sequencing while remaining free of
I/O and mutable state.

**Candidate public capabilities:** `validate_eur_amount`,
`calculate_completed_work`, `calculate_overall_progress`,
`calculate_material_balance`, `calculate_work_balance`.

**Must not own:** record loading, persistence, presentation formatting,
currency conversion, or fallback values. Boundary modules reject invalid
currency/scale by delegating to this policy rather than reimplementing it.

**Primary invariants:** INV-037, INV-041, INV-044, INV-050. These operations
are leading candidates for State 7 properties and determinism declarations.

### `photo_management`

**Owns:** idempotent PhotoPublication acceptance, ProgressPhoto creation,
caption/section/visibility changes, same-project section validation, gallery
ordering, and access eligibility for the photo binary.

**Candidate public capabilities:** `publish_progress_photo`,
`update_progress_photo`, `list_progress_photos`,
`read_progress_photo`.

**Must not own:** Telegram intake, binary persistence/read mechanics,
financial/progress mutation, or deriving progress from images.

**Primary invariant:** INV-043. `budget_management` owns shared
section/project consistency in INV-036; `project_tracking` owns INV-040 and
photos remain a forbidden progress source.

### `derived_views`

**Owns:** deterministic read models for viewer/operator project lists,
budget summary, expense totals and unresolved allocations, progress,
completed work, payments, balance labels, and explicit unavailable values.

**Knows:** R5 read policy and composes already authorized records. It delegates
R9 arithmetic and unavailable semantics to `financial_policy` and does not
mutate or cache editable totals.

**Hides:** query composition, projection, stable ordering where defined, and
formula sequencing.

**Candidate public capabilities:** `build_project_overview`,
`build_budget_view`, `build_expense_view`, `build_progress_view`,
`build_payment_view`, `list_viewer_projects`.

**Must not own:** authorization policy, persistence writes, fallback zeros,
budget/expense corrections, or Registry current-truth storage.

**Primary invariants:** INV-027 and INV-035. Formula invariants are owned by
`financial_policy`; viewer project ordering is INV-055.

### `audit_writer`

**Owns:** construction/validation and append-only persistence of exactly one
AuditRecord for each R13 action occurrence, including rejected significant
mutations and service key-version provenance.

**Candidate public capabilities:** `append_success_audit`,
`append_rejection_audit` (State 5 may consolidate these into one typed
operation if the closed-choice result model remains precise).

**Must not own:** business transaction success, generic payload storage,
action-specific entity details, authorization, or mutable audit history.

**Primary invariants:** INV-051 and INV-053. `portal_store` owns the physical
append-only constraint shared by audit/import records in INV-052.

### `portal_store`

**Owns:** persistence mappings, typed aggregate queries, uniqueness and
concurrency enforcement, and commit/rollback for portal-owned records.

**Hides:** SQLAlchemy/database sessions, schema layout, joins, and database
exceptions.

**Candidate public surface:** concrete `PortalStore` and `PortalTransaction`
facades consumed by domain modules; transaction methods are entity-specific
and typed, never generic CRUD or raw ORM/session APIs.

**Must not own:** business validation, authorization, formulas, external
network calls, audit catalog selection, or automatic retries that could
duplicate non-idempotent effects.

**Primary invariants:** INV-009 and INV-017 for database-enforced active
grant/assignment uniqueness, and INV-052 for append-only audit/import
persistence. The viewer/service and
audit/import modules own their corresponding use cases.

### `api`

**Owns:** HTTP JSON routing, request decoding, authentication credential
extraction, dependency wiring, invocation of one owning use case, and stable
translation of declared domain/boundary failures to HTTP responses.

**Hides:** framework-specific request/response and streaming mechanics.

**Candidate public capability:** `create_app` plus route handlers that remain
transport entry points, not cross-domain APIs.

**Must not own:** role/capability decisions, Registry validation policy,
transactions, formulas, file-reference safety, ORM queries, or duplicated
business rules. Client-supplied project context, roles, and capabilities are
discarded/rejected at this boundary, never forwarded as authority.

## Candidate public ownership (`imports.internal` draft)

This is ownership, not final dependency wiring. Internal helpers and
framework route handlers are intentionally absent.

```text
models                 → model/enum/catalog symbols only
credential_security    → password and verification-secret cryptographic
                         capabilities
staff_identity       → authenticate_staff, sign_out_staff,
                         revoke_staff_sessions, change_staff_status,
                         change_staff_password, assignment management,
                         perform_recovery_override, issue/confirm verification,
                         request/confirm email
                         change, request/complete password reset,
                         send_staff_security_notice
viewer_access          → viewer, access-link, session, and grant capabilities
service_identity       → principal, credential, producer-grant, and scope
                         capabilities
authorization_guard    → conceal_authentication_failure,
                         authorize_project_read,
                         authorize_project_mutation,
                         authorize_access_management,
                         authorize_snapshot_import
registry_gateway       → list_active_projects,
                         validate_project_reference, get_project_context
email_delivery_gateway → deliver_email_message
binary_storage         → read_binary
snapshot_import        → import_snapshot, get_snapshot_import_result
budget_management      → ensure/edit/review/activate/get budget capabilities
expense_intake         → create_expense_from_recognition
expense_management     → expense/allocation/document capabilities
project_tracking       → progress and payment capabilities
financial_policy       → pure money/progress validation and formulas
photo_management       → photo publication/update/read capabilities
derived_views          → project/budget/expense/progress/payment read models
audit_writer           → typed append audit capabilities
portal_store           → PortalStore, PortalTransaction
api                    → create_app
```

## Dependency direction

```text
models
  ↓
credential_security, financial_policy, portal_store, registry_gateway,
email_delivery_gateway, binary_storage
  ↓
staff_identity, viewer_access, service_identity,
snapshot_import, budget_management, expense_management,
project_tracking, photo_management, audit_writer
  ↓
authorization_guard, expense_intake, derived_views
  ↓
api
```

This diagram shows layering, not an assertion that every lower module imports
every module above it. Important directed edges are:

- `authorization_guard` → identity owner + `registry_gateway`;
- `staff_identity` → `credential_security` + `email_delivery_gateway`;
- `snapshot_import` → `service_identity` + `registry_gateway` +
  `portal_store` + `audit_writer`;
- business mutators → `authorization_guard` + `portal_store` +
  `audit_writer`;
- authorized document/photo delivery → owning domain module, then
  `binary_storage`;
- `derived_views` → authorized typed reads + `registry_gateway`, never raw
  ORM or Registry storage.

No service database transaction remains open across Registry or email
network I/O.

## Candidate generation order and paths

`models` remains first and maps to the established deterministic runtime
unit. State 8 places `authorization_guard` before the identity modules because
their exact dependency edges consume its trusted guard/error surface; the
guard itself depends only on models, Registry, and persistence.

```text
module_order:
  models
  credential_security
  financial_policy
  portal_store
  registry_gateway
  email_delivery_gateway
  binary_storage
  audit_writer
  authorization_guard
  staff_identity
  viewer_access
  service_identity
  snapshot_import
  budget_management
  expense_management
  expense_intake
  project_tracking
  photo_management
  derived_views
  api

module_paths:
  models                 → core/models
  credential_security    → security/credential_security
  financial_policy       → domain/financial_policy
  portal_store           → adapters/portal_store
  registry_gateway       → adapters/registry_gateway
  email_delivery_gateway → adapters/email_delivery_gateway
  binary_storage         → adapters/binary_storage
  audit_writer           → application/audit_writer
  staff_identity       → domain/staff_identity
  viewer_access          → domain/viewer_access
  service_identity       → domain/service_identity
  authorization_guard    → application/authorization_guard
  snapshot_import        → domain/snapshot_import
  budget_management      → domain/budget_management
  expense_management     → domain/expense_management
  expense_intake         → application/expense_intake
  project_tracking       → domain/project_tracking
  photo_management       → domain/photo_management
  derived_views          → application/derived_views
  api                    → api/runtime
```

Package facades, if generation units are later split, are generated after
their internals; public callers retain these logical module keys and do not
import internal generation paths.

## Placeholder-resistance review

- No module is named `utils`, `helpers`, `manager`, `processor`, or generic
  `service`.
- `portal_store` is accepted only as a typed persistence adapter; a generic
  CRUD or `dict` surface would fail State 5.
- `authorization_guard` produces the complete R4 decision; callers cannot
  satisfy it by checking only a token or project ID.
- `snapshot_import`, `budget_management`, and `expense_management` each own
  the transaction that creates their promised state; the API cannot become
  the hidden orchestrator.
- `derived_views` owns concrete formulas and unavailable semantics; returning
  empty/zero summaries will contradict R9 and its future notes/properties.
- `binary_storage` cannot authorize by possession of `file_ref`, and domain
  modules cannot read paths or provider URLs directly.
- Integration gateways translate only their own failures and never make
  product authorization or lifecycle decisions.

## Unresolved decisions carried forward

- Mandatory staff MFA.
- Administrative-area boundaries while only one area exists.
- PresuPro transport binding.
- List pagination beyond the current few-project profile; R15 now owns
  deterministic project-list ordering.
- Visible expense-correction history beyond append-only audit.
- SnapshotImportRecord retention.
- External-store deletion/retention policy.

The fixed-expiry session decision, self-service existence-hiding password
reset, and proposed config defaults remain explicitly unconfirmed by the
product owner. They may guide flow drafts but must be re-confirmed before
State 8 assembly.

## State 3 readiness assessment

- Every State 2 invariant has one semantic owner or an explicit split between
  a boundary fact and the consuming enforcement owner; exact
  `owner_function` remains deferred to States 5–7 as intended.
- Model creation and mutation responsibilities are assigned; storage owns no
  business policy.
- Registry, email, OCR intake, and binary storage are explicit boundaries;
  no direct external database/model access is permitted.
- Public capabilities are smaller than hidden behavior and do not expose
  internal sequencing.
- The thin API has no authority to invent policy, transactions, or derived
  values.
- Remaining questions are bounded later-state or operational decisions and do
  not require a generic placeholder in the module map.

State 3 is coherent enough to begin State 4 key-system-flow design.
