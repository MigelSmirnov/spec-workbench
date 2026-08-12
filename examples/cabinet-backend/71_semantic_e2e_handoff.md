# Cabinet Backend — Stage 7.1 Semantic E2E handoff

Status: **review handoff, not yet semantic-closed**.

Read `skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md` first. This file is the Cabinet execution plan and initial behavior/test skeleton.

Do not redesign `SPEC_STANDARD.md`, Factory, or adapters while executing this handoff. The purpose here is to challenge the already-authored Cabinet specification for semantic ambiguity before final assembly.

## Sources to read before reviewing a flow

Use the smallest complete slice needed, but preserve the business chain:

- `00_product.md`
- relevant `01_models*.md`
- relevant `02_rules*.md`
- `30_modules.md`
- `40_flow_plan.json` and the relevant section of `40_flows.md`
- `50_public_apis.md`
- `60_contracts.json`
- `60_data_closure.json`
- `60_exception_taxonomy.json`
- `70_router_closure.json` / `70_router_context.json` only for exposed transport behavior
- `80_notes.md`

For each flow, reconstruct observable semantics from these sources. Do not infer product behavior from generated code.

---

# Flow 1 — `flow:synchronize_invoice_to_local_archive`

## Intended behavior graph

```text
selected exact VPS invoice work + synchronization node identity
        ↓
synchronize_invoice_work
        ↓
authenticate/transport exact work package
        ↓
transport observation
        ├─ explicit failure/unavailable/incompatible/unknown
        │      → SynchronizationOutcome preserving that state
        └─ delivered
               ↓
          accept_transfer_manifest
               ↓
          archive validates immutable card revision + source evidence
               ├─ rejected/quarantined/incomplete/etc.
               │      → classified InvoiceTransferReceipt
               └─ durably accepted/already accepted
                      ↓
                verify_durable_acceptance
                      ↓
                authoritative local durable proof
```

Critical invariant: delivery is never promoted to durable acceptance by transport evidence alone.

## Semantic pseudotests

### S1 — successful transfer does not skip durable verification

```text
given:
  an exact synchronization work selection
  authenticated compatible node identity
  transport delivery succeeds
  archive evidence is valid
when:
  the invoice is synchronized into local custody
then:
  a transport delivery observation exists
  durable acceptance is produced only by the durable archive owner
  authoritative local verification can prove acceptance
  transport delivery itself is not the acceptance proof
```

### S2 — ambiguous transport outcome remains reconcilable

```text
given:
  a valid synchronization work selection
  the remote transport outcome is unknown/ambiguous
when:
  synchronization is attempted
then:
  the result preserves an unresolved synchronization outcome
  no durable acceptance is manufactured
  the attempt remains correlatable for reconciliation
```

### S3 — rejected archive evidence is not partially accepted

```text
given:
  a delivered manifest
  archive evidence that is integrity-invalid, conflicting, incomplete, or quarantine-required
when:
  local archive acceptance is attempted
then:
  the receipt exposes the corresponding classified non-accepted outcome
  no partial accepted manifest set becomes normal archive truth
```

### S4 — repeated equivalent acceptance is idempotent

```text
given:
  a manifest/revision/source evidence set that has already been durably accepted
when:
  the equivalent acceptance is presented again
then:
  no second logical durable acceptance is created
  the result refers to the existing accepted state/evidence
```

## Adversarial review question

Can the current slice permit an implementation where `synchronize_invoice_work` itself marks a delivered package as durably accepted without `durable_archive` ownership? If yes, record `AMBIGUITY`.

---

# Flow 2 — `flow:accept_local_source_attachment`

## Intended behavior graph

```text
local authenticated actor + invoice target + source files
        ↓
authorize_operation(exact source-attachment operation)
        ↓
attach_local_source_handler (transport-only multipart transform)
        ↓
attach_local_source
        ↓
resolve exact accepted invoice target
        ↓
validate media/hash/expected target/provenance
        ├─ unknown invoice → InvoiceNotFoundError
        ├─ rejected source → SourceAttachmentRejectedError
        └─ accepted source evidence
               ↓
          update source custody/provenance only
               ↓
          get_source_status → observable availability/completeness
```

Critical invariant: attaching source evidence never rewrites the immutable accepted Invoice Card revision.

## Semantic pseudotests

### A1 — valid attachment changes source evidence only

```text
given:
  an accepted immutable invoice revision
  an authorized actor
  a valid matching local source file
when:
  the source is attached
then:
  verified source custody/provenance is recorded
  source availability reflects the attachment
  invoice card bytes/content hash remain unchanged
```

### A2 — unknown invoice is not converted into empty source state

```text
given:
  an authorized actor
  an invoice identifier with no accepted target
when:
  source attachment or source status lookup is requested
then:
  InvoiceNotFoundError is raised
  no placeholder invoice/source state is created
```

### A3 — repeated identical bytes are idempotent, not silent replacement

```text
given:
  source bytes already attached with provenance
when:
  equivalent bytes are attached again for the same exact target
then:
  the operation is idempotent according to accepted source policy
  existing provenance is not silently replaced by unrelated evidence
```

### A4 — irregular HTTP handler owns no archive policy

```text
given:
  a multipart HTTP upload
when:
  attach_local_source_handler processes the request
then:
  it performs only transport transformation required to construct the declared source input
  archive acceptance/authorization/persistence policy remains delegated to its owning operations
```

---

# Flow 3 — `flow:refresh_registry_and_validate_assignment`

## Intended behavior graph

```text
complete Registry project observation
        ↓
refresh_registry_context
        ↓
translate accepted Registry fields
        ↓
update Registry-derived WorkObject context
        ↓
preserve Cabinet-owned fields and existing objects not proven deleted
        ↓
validate_card_assignment(exact immutable card revision)
        ↓
compare against current Registry/WorkObject evidence
        ├─ missing/unusable Registry context → RegistryContextUnavailableError
        └─ evidence available
              ↓
          valid OR unresolved/review-required validation evidence
              ↓
          get_assignment_validation returns recorded evidence only
```

Critical invariant: Registry observation can change validation/review evidence but cannot rewrite the immutable Card assignment.

## Semantic pseudotests

### R1 — refresh is one-way and preserves Cabinet-owned state

```text
given:
  an existing WorkObject with Registry-derived and Cabinet-owned fields
  a newer complete Registry observation
when:
  Registry context is refreshed
then:
  accepted Registry-derived fields are refreshed
  Cabinet-owned fields are preserved
  Cabinet performs no Registry write-back
```

### R2 — absence from later Registry response does not imply deletion

```text
given:
  a previously known WorkObject
  a later Registry response in which that project is absent
  no accepted evidence that absence means deletion
when:
  context is refreshed
then:
  the WorkObject is not silently deleted or marked completed solely from absence
```

### R3 — changed Registry evidence cannot rewrite Card assignment

```text
given:
  an immutable Card assignment
  current Registry evidence that no longer validates the earlier choice
when:
  assignment validation runs
then:
  validation/review evidence changes as required
  the immutable Card assignment itself is unchanged
```

### R4 — missing validation is not guessed from current Registry state

```text
given:
  no accepted assignment-validation evidence for an exact Card revision
when:
  get_assignment_validation is called
then:
  AssignmentValidationNotFoundError is raised
  no synthetic valid/invalid result is inferred
```

---

# Flow 4 — `flow:calculate_plan_actual`

## Intended behavior graph

```text
PresuPro estimate observation
        ↓
refresh_estimate_snapshot
        ↓
canonical immutable EstimateSnapshot (new or already known)

accepted invoice revision + WorkObject/project context + pinned EstimateSnapshot
+ confirmed match decisions + accepted assumptions
        ↓
calculate_plan_actual
        ↓
validate pinned evidence + assignment + matches + unit comparability
        ├─ failed precondition → PlanActualPreconditionError
        └─ valid
              ↓
          deterministic/reproducible analysis
              ↓
          unmatched facts + non-blocking warnings remain explicit
```

Critical invariant: source invoice, Registry, and estimate facts are immutable inputs; the analysis may derive evidence but cannot rewrite them.

## Semantic pseudotests

### P1 — equal pinned evidence produces reproducible analysis

```text
given:
  the same exact invoice revision
  the same WorkObject/project context
  the same EstimateSnapshot
  the same confirmed matches and assumptions
when:
  plan/actual analysis is calculated repeatedly
then:
  the calculated semantic result is reproducible
  evidence identities remain pinned to the same inputs
```

### P2 — unmatched facts remain explicit

```text
given:
  valid pinned evidence with some facts not covered by confirmed matches
when:
  analysis is calculated
then:
  unmatched facts remain represented as unmatched
  they are not silently coerced into a match
```

### P3 — incomparable units block calculation

```text
given:
  otherwise valid pinned evidence
  quantities/units that fail accepted comparability preconditions
when:
  plan/actual analysis is requested
then:
  PlanActualPreconditionError is raised
  no fabricated converted comparison is emitted
```

### P4 — invalid PresuPro observation never creates partial snapshot

```text
given:
  a PresuPro observation without stable source identity or with unprocessable content
when:
  snapshot refresh is attempted
then:
  EstimateObservationRejectedError is raised
  no partial EstimateSnapshot is accepted
```

---

# Flow 5 — `flow:publish_invoice_to_holded`

## Intended behavior graph

```text
authorized local actor + exact confirmed immutable invoice revision
        ↓
authorize exact publication operation
        ↓
load accepted archive truth
        ↓
request_holded_publication
        ↓
check accepted eligibility + exact target + required source + duplicate-prevention
        ├─ ineligible → HoldedPublicationIneligibleError
        ├─ equivalent logical publication exists → return existing publication
        └─ eligible new logical publication
               ↓
          create one logical attempt with stable identity
               ↓
          create_holded_purchase
               ↓
          exactly one technical remote create
               ├─ verified success → settled logical publication
               └─ ambiguous technical outcome
                      ↓
                 reconciliation-pending publication
                      ↓
                 NO automatic second create
                      ↓
                 reconcile_holded_publication
                      ↓
                 lookup_holded_purchase (read-only)
                      ↓
                 exactly one fully verified matching remote purchase?
                      ├─ yes → settled publication
                      └─ no → HoldedReconciliationRequiredError
```

Critical invariants:

- maximum automatic create count for one logical attempt is the configured accepted value (currently one);
- ambiguous create does not permit automatic retry;
- only fully verified recovered candidate may settle publication;
- Holded credentials stay inside the gateway boundary;
- Invoice Card facts are immutable throughout publication.

## Semantic pseudotests

### H1 — happy path creates exactly one verified remote purchase

```text
given:
  an authorized actor
  an eligible exact immutable invoice revision
  required source evidence
  no existing equivalent logical publication
  remote create returns verifiable success
when:
  publication is requested
then:
  one logical publication attempt exists
  exactly one remote create mutation occurs
  the returned publication is settled only after success is verified
  the invoice revision is unchanged
```

### H2 — ineligible publication fails before successful publication can be manufactured

```text
given:
  an authorized actor
  an exact revision that fails accepted publication eligibility or required-source preconditions
when:
  publication is requested
then:
  HoldedPublicationIneligibleError is raised
  no successful logical publication is manufactured
```

### H3 — ambiguous create produces reconciliation-pending state with no automatic retry

```text
given:
  an eligible publication request
  remote create times out or otherwise has ambiguous outcome
when:
  publication is requested
then:
  exactly one remote create attempt exists
  the logical publication is reconciliation-pending
  no automatic second create is issued
  ambiguous technical evidence is preserved
```

### H4 — reconciliation settles only one fully verified match

```text
given:
  a reconciliation-pending logical publication
  read-only recovery finds exactly one remote candidate
  candidate payload/identity fully matches accepted verification requirements
when:
  reconciliation runs
then:
  the existing logical publication becomes settled
  reconciliation performs no second remote create
```

### H5 — zero, multiple, mismatched, or failed lookup cannot become success

```text
given:
  a reconciliation-pending logical publication
  recovery evidence is zero matches, multiple matches, payload mismatch, lookup failure, or inconsistent attempt evidence
when:
  reconciliation runs
then:
  HoldedReconciliationRequiredError is raised
  publication is not marked settled
  no second remote create occurs
```

### H6 — equivalent repeated publication request is idempotent

```text
given:
  an existing equivalent logical publication bound to the exact immutable revision
when:
  the equivalent publication request is repeated
then:
  the existing logical publication is returned/preserved
  no duplicate logical obligation or extra remote create is introduced
```

## First adversarial ambiguity target

Try to construct a conforming implementation that performs a second Holded POST after an ambiguous first POST. If the full slice still permits it, Stage 7.1 fails immediately and the missing constraint must be located upstream. If it cannot be constructed without violating accepted rules/notes, mark this branch `PASS`.

---

# Flow 6 — `flow:release_vps_working_copy`

## Intended behavior graph

```text
manual actor intent + exact project/working-set target
        ↓
authorize release operation
        ↓
get_sync_status + verify_durable_acceptance
        ↓
evaluate_vps_release
        ↓
manual baseline + exact working set + durable-local proof + synchronization/retention evidence
        ├─ missing/inconsistent/ineligible → VpsReleaseBlockedError
        └─ allowed VpsReleaseEvaluation
               ↓
          request_manual_vps_release
               ↓
          re-check still-applicable exact evaluation/target
               ├─ stale/mismatch/conflict/new ineligibility → VpsReleaseBlockedError
               └─ record release decision
                      ↓
                 later storage adapter may perform physical release
```

Critical invariant: Registry status alone never authorizes deletion/release, and these domain operations do not themselves perform physical deletion.

## Semantic pseudotests

### V1 — durable-local proof is mandatory

```text
given:
  manual release intent for an exact working set
  no authoritative durable-local acceptance proof
when:
  release evaluation is requested
then:
  VpsReleaseBlockedError is raised
  no release decision is recorded
```

### V2 — Registry status alone cannot allow release

```text
given:
  Registry status that appears complete/archived
  missing required durable-local proof
when:
  release is evaluated
then:
  release remains blocked
  Registry status is not treated as deletion authority
```

### V3 — allowed evaluation performs no physical deletion

```text
given:
  exact working-set identity
  authoritative durable-local proof
  consistent synchronization and retention evidence
when:
  release evaluation succeeds
then:
  an allowed VpsReleaseEvaluation is returned/recorded
  no physical working-copy deletion occurs
```

### V4 — stale evaluation cannot authorize release

```text
given:
  a previously allowed evaluation
  evidence or target context that has become stale/mismatched/newly ineligible
when:
  manual release decision is requested
then:
  VpsReleaseBlockedError is raised
  no physical release authorization is recorded
```

### V5 — repeated equivalent manual decision is idempotent

```text
given:
  an already recorded authorized release decision for the same exact still-valid evaluation/target
when:
  the equivalent request is repeated
then:
  the existing equivalent decision is preserved/returned
  no conflicting decision history is created
```

---

# Review protocol for the next agent

Process **one flow at a time**. Do not bulk-approve all six.

For each flow:

1. Read the full semantic slice listed at the top.
2. Verify or correct the behavior graph **only from accepted sources**.
3. For every material branch, verify that the pseudotest `Then` follows from the specification without guessing.
4. Ask the adversarial ambiguity question: construct the strongest materially different behavior that still appears compliant.
5. Ask the placeholder-resistance question for each generated callable in that flow.
6. Record findings before editing anything.
7. Route each real finding to its owner: upstream business/rule/model, deterministic structure/property, or State 7 note.
8. Re-run the flow review after each correction.
9. Mark the flow `semantic_closed` only when no material ambiguity or placeholder path remains.

Suggested review record:

```text
flow: flow:...
status: PASS | AMBIGUITY | PLACEHOLDER_RISK | semantic_closed
material_alternative_found: yes/no
placeholder_implementation_found: yes/no
scenario_gaps: [...]
findings:
  - owner: upstream_business | structure | property | note
    scope: ...
    interpretation_A: ...
    interpretation_B: ...
    required_resolution: ...
```

## Important boundary

The pseudotests in this handoff are **requirements written before implementation**. They may later become runtime tests, but they must not be rewritten merely to match generated code. If generated code disagrees with a semantic-closed scenario, code generation/implementation is wrong unless the upstream specification is intentionally changed and reviewed again.
