# State 2 — Cabinet Card and ChatGPT rules

## Accepted decision A01 — canonical Cards remain type-specific and revision-safe

### Normative rules

1. ProviderCard M07, ClientCard M08, ProjectCard M09, and InvoiceCardV1 M10
   retain their existing Cabinet_web meanings and validators.
2. A stable Card ID identifies the continuing Card entity. A canonical content
   hash identifies one exact revision; titles, invoice numbers, contacts,
   filenames, and Registry labels never substitute for identity.
3. Unknown facts remain absent or explicitly unknown according to the owning
   Card contract. ChatGPT, browser input, transport, and storage cannot invent
   required facts to make validation pass.
4. Draft changes require the exact expected M03 revision. Confirmed Invoice
   content cannot be changed through a draft update; correction creates an
   explicit later revision under the same Invoice ID.
5. Duplicate candidates never merge, replace, archive, or confirm a Card
   automatically.
6. Derived catalogues, summaries, analytics, M12 shopping lists, Registry
   replicas, and local Backend receipts never replace canonical Card facts.
7. M05 logical source identity, M06 byte identity, and storage location remain
   distinct. Storage movement or later byte availability does not mint a new
   logical source.

### Formal invariants

```text
same_card_revision
<-> same_card_id AND same_canonical_content_hash

draft_update_committed
-> expected_revision = current_revision AND validation_errors = empty

derived_projection -/> canonical_fact_authority
duplicate_candidate -/> automatic_merge_or_confirmation
```

### Required tests

1. Stale revision updates fail without changing the current Card.
2. Equal titles, contacts, invoice numbers, or totals do not collapse distinct
   Card IDs.
3. Confirmed Invoice facts cannot be edited through the draft operation.
4. Missing or uncertain extracted values remain visible and are not fabricated.
5. Rebuilding summaries and catalogues does not mutate source Cards.

### Consequence

The new backend may change persistence and transport, but not existing Cabinet
identity, validation, revision, duplicate, or source semantics.

## Accepted decision A02 — ChatGPT produces reviewable proposals and explicit effects

### Normative rules

1. Online ChatGPT is the primary UI/UX. It may interpret user text, PDFs, and
   images into a structured proposal, but model confidence is never validation
   or confirmation evidence.
2. Cabinet Web performs no server-side OCR. Failure or uncertainty in ChatGPT
   extraction leaves explicit missing/uncertain facts for human correction.
3. Read operations do not mutate data and do not require effect confirmation.
4. A draft write may proceed only after the user's request clearly asks Cabinet
   to save or update that draft.
5. Confirmation, archive, release of VPS copies, replacement of confirmed
   facts, and every other irreversible or externally consequential effect
   require explicit confirmation of the exact target revision and effect.
6. Warnings and duplicate candidates that require acknowledgement are shown
   before confirmation and are bound to the exact reviewed revision.
7. Declining, omitting, or timing out confirmation leaves the current state
   unchanged.
8. The plugin reports separately: structured Card outcome, original-byte
   custody outcome, and local synchronization outcome.
9. The plugin exposes only named typed capabilities backed by existing Cabinet
   application behavior; it cannot accept arbitrary operation names or generic
   executable payloads.

### Formal invariants

```text
chatgpt_extraction -> proposal
proposal -/> validated_or_confirmed_fact

confirmed_or_irreversible_effect
-> exact_target_revision AND explicit_confirmation

confirmation_absent_or_declined -> no_effect
```

### Required tests

1. Extraction uncertainty is returned for review and does not get filled by a
   backend default.
2. Read-only searches leave all durable state unchanged.
3. Confirmation of revision A cannot authorize revision B after a concurrent
   update.
4. Declined or expired confirmation produces no write.
5. A stored Card with missing original bytes is reported as Card success plus
   source pending, never as complete source custody.

### Consequence

Conversational convenience does not weaken Cabinet validation, confirmation,
identity, or truthful partial-outcome rules.

## Accepted decision A03 — Cabinet capabilities are authorized and provisioned server-side

### Normative rules

1. Every operation resolves one active M02 CabinetPrincipal before protected
   data is returned or state is changed.
2. The single human owner may arrive through the authenticated ChatGPT plugin
   or protected browser channel; UI state, a hidden control, an object ID, or a
   model assertion is not authorization evidence.
3. Plugin and browser capabilities are scoped to the human owner and accepted
   Cabinet operations. Neither channel can manage node credentials, operator
   configuration, arbitrary files, database state, or local Backend effects.
4. One active M17 local Backend node may use only the evening synchronization
   capability set: discover/pull Invoice work, reconcile its exact issuance,
   publish one Registry catalogue, and observe compatibility.
5. The local node credential cannot authorize ChatGPT/browser Card mutation,
   source upload, VPS release, operator actions, or another installation.
6. Capability grants are created only by the public
   `access_control.provision_capability_grant` operation invoked from the
   protected composition/operator boundary. No caller may edit, infer, or
   adapt a private grant store.
7. Grant provisioning requires an authenticated active owner or operator and
   an active target principal. It accepts only an exact A16 capability allowed
   for the requested channel and binds the grant to the exact optional entity
   scope.
8. Exact replay of the same target, channel, capability, and scope is
   idempotent. Any affix-confused capability, cross-channel grant, inactive
   subject, or unauthorized grantor is rejected without partial state.
9. Operator actions are reachable only through the protected host/operator
   boundary and are not ordinary public plugin tools.
10. Authorization is evaluated for the exact principal, capability, Card or
    synchronization entity, and current lifecycle state on every request.
11. Revocation prevents new actions immediately without changing Card or node
    business identity.
12. Every active M17 node is bound to exactly one active M02
    `local_backend_node` principal. Local-node authentication returns one M39
    containing both identities; authorization is evaluated against the M02
    principal, while synchronization operations receive only the bound M17.
13. M39 is the only accepted authentication proof for capability provisioning,
    enrollment after bootstrap, rotation, and revocation. An M01
    `ActorReference` carried in a command or request is provenance only and
    grants no authority.
14. The nullable entity scope has one collision-resistant canonical key: the
    lowercase SHA-256 digest of domain tag `cabinet-scope-v1` followed by the
    canonical UTF-8 JSON object. The object contains an explicit scoped/unscoped
    tag and, when scoped, every M65 field including the complete revision value;
    keys are sorted, separators are compact, and datetimes are normalized to
    timezone-aware UTC. Delimiter concatenation and omitted scope fields are
    forbidden.
15. Initial owner enrollment is the sole unauthenticated lifecycle exception:
    it is allowed only at the protected operator boundary when no owner or
    operator exists. Every later enrollment, rotation, revocation, and grant
    provisioning requires an active owner/operator M39 supplied as a separate
    operation argument.

### Formal invariants

```text
protected_operation
-> active_principal AND capability_allowed AND exact_entity_authorized

new_capability_grant
-> protected_boundary
AND active_owner_or_operator_grantor
AND active_target_principal
AND exact_A16_capability_allowed_for_channel

grant_identity = (target_principal_id, channel, capability, entity_scope)
exact_grant_replay -> same_grant AND created = false

identifier_known -/> authorization
private_grant_store_access -/> accepted_composition
local_node_credential -/> human_or_operator_capability
human_browser_credential -/> synchronization_capability
local_node_context
-> active_M02_machine_principal
AND active_bound_M17_node
AND node.principal_id = principal.principal_id

authenticated_lifecycle_actor = M39 -/> asserted_M01
scope_key = sha256("cabinet-scope-v1" || canonical_complete_M65_json)
```

The machine-readable single home for the principal-kind vocabulary is
`rules.principal_catalogue`: the owner, operator and local-node kinds, the
set of kinds that may act as owner/operator, and the synchronization contract
version an active node must carry. Notes name those values through the
catalogue, never through a model label or a prose kind.

### Required tests

1. Each channel is rejected when presenting another channel's credential.
2. A valid ID without exact capability authorization cannot read or mutate the
   entity.
3. Revoked principals and node credentials cannot start new operations.
4. A local node cannot access another installation's issuance or publication.
5. Plugin tools cannot select arbitrary operations, paths, or effect scopes.
6. Only an authenticated active owner/operator at the protected boundary can
   provision a grant for an active target.
7. Exact grant replay is idempotent; changed scope/channel/capability is a
   distinct grant and never inherits authority.
8. The runtime composition and verification harness provision grants only
   through the public operation and remain independent of private storage
   names or layouts.
9. Every local-node credential resolves an M39 whose M02 and M17 binding is
   exact; missing, inactive, cross-installation, or contract-incompatible
   bindings fail before authorization or domain dispatch.
10. Scope-key tests include delimiter-confusable values, null versus populated
    scopes, and revisions differing in every constituent field; no pair
    collides or inherits authority.
11. An asserted M01 cannot enroll, rotate, revoke, or provision. Bootstrap is
    accepted exactly once only when the protected installation has no owner or
    operator.

### Consequence

M02 and M17 identify subjects; credentials authenticate them, the protected
public provisioning operation creates exact grants, and authorization
separately evaluates those grants for every action.

## Accepted decision A04 — every Cabinet effect is idempotent and revision-atomic

### Normative rules

1. M16 CabinetEffect is the logical idempotency boundary for every protected
   write initiated by plugin or browser.
2. One principal-scoped idempotency identity binds to one operation kind,
   canonical request hash, exact target, and expected revision.
3. Repeating an identical committed request returns the prior logical result.
   Reusing the identity with different content or target is rejected.
4. The expected revision check and mutation commit are one atomic transition.
   Concurrent writers cannot both commit from the same prior revision.
5. Source handoff consumption, source custody commit, transfer issuance,
   catalogue acceptance/current selection, and manual release each have their
   own atomic transition boundary.
6. A transport timeout after issue becomes `outcome_unknown`; retry first
   reconciles the same effect or issuance and never creates a second effect.
7. Partial persistence cannot expose a committed result, consume a handoff, or
   advance source/transfer/catalogue state without its matching durable facts.

### Formal invariants

```text
count(logical_effect for principal, idempotency_identity) <= 1

same_idempotency_identity AND different_request_hash -> reject

effect_commit
-> expected_revision = current_revision_at_atomic_commit

unknown_outcome -> reconcile_same_identity_before_mutation_retry
```

### Required tests

1. Concurrent identical effects yield one logical result.
2. Concurrent updates from the same expected revision cannot both commit.
3. Conflicting idempotency reuse is rejected before mutation.
4. Failure between preparation and commit exposes no false success.
5. Timeout reconciliation returns the existing result without duplicate state.

### Consequence

ChatGPT retry behavior and intermittent local transport cannot duplicate or
silently overwrite Cabinet work.
