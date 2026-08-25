# State 1 companion — Cabinet Backend model ownership

## Status

Working ownership and lifecycle check for `01_models.md`.

This document remains inside State 1. It identifies producers, modifiers,
consumers, persistence, and reasons for change without selecting module names,
module paths, public functions, or implementation sequencing.

The matrix is preparation for deep-module design in State 3. Similar-looking
records are not required to become separate modules. State 3 must group them by
shared ownership of rules and hidden complexity.

## Ownership principles

1. Accepted Cabinet Card payloads are created and changed only through accepted
   Cabinet Card operations.
2. Backend operational records may reference a Card revision but do not silently
   mutate that revision.
3. Registry and PresuPro projections are immutable observations of external
   systems; refresh creates new snapshots.
4. Transport records describe delivery. Import records describe local business
   acceptance. Neither may impersonate the other.
5. Derived analysis is recalculated from pinned accepted inputs rather than
   edited as primary truth.
6. Every persisted mutable lifecycle has one reason for change and must later
   receive one primary enforcement owner.

---

# A. Accepted Card archive

## StoredInvoiceCard

- **Kind:** persisted archive identity.
- **Created from:** first locally accepted Invoice Card revision.
- **Changed by:** later accepted revisions or explicit archive lifecycle actions.
- **Read by:** archive search, synchronization reconciliation, matching,
  analytics, and publication eligibility.
- **Persists:** local Backend.
- **Reason to change:** the current accepted Card revision or archive lifecycle
  changed.
- **Must not own:** Invoice Card validation rules or source-byte verification.

## StoredInvoiceCardRevision

- **Kind:** immutable persisted record.
- **Created from:** one canonical accepted Invoice Card JSON payload.
- **Changed by:** never; correction creates another record.
- **Read by:** validation evidence, object validation, matching, analytics,
  publication, history, and audit.
- **Persists:** VPS working set and local archive according to retention policy.
- **Reason to change:** none after creation.
- **Must not own:** Backend synchronization or integration state.

## InvoiceCardValidationRecord

- **Kind:** immutable decision evidence.
- **Created from:** deterministic validation of one exact Card revision.
- **Changed by:** never; revalidation with another validator version creates a
  new record.
- **Read by:** import acceptance, duplicate review, confirmation presentation,
  matching and publication eligibility.
- **Persists:** both nodes when produced there; complete history locally.
- **Reason to change:** none after creation.
- **Must not own:** automatic correction of Card values.

## DuplicateCandidateReview

- **Kind:** persisted human or policy decision lifecycle.
- **Created from:** duplicate signals for an incoming Card revision.
- **Changed by:** an explicit review decision or resolution.
- **Read by:** local import acceptance and archive presentation.
- **Persists:** local Backend; VPS may receive the resulting receipt or warning.
- **Reason to change:** review status or resolution changed.
- **Must not own:** silent merging or deletion of Cards.

---

# B. Source binaries

## SourceBinary

- **Kind:** immutable-content identity with mutable availability status.
- **Created from:** Card source metadata plus received bytes when available.
- **Changed by:** verification, quarantine, retention, or deletion actions; bytes
  themselves never change under the same content identity.
- **Read by:** import acceptance, source retrieval, audit, backup, and retention.
- **Persists:** metadata on participating nodes; durable bytes locally after
  acceptance.
- **Reason to change:** availability or retention state changed.
- **Must not own:** the semantic contents of the Invoice Card.

## SourceBinaryReplica

- **Kind:** persisted storage-location record.
- **Created from:** storing one SourceBinary on one node.
- **Changed by:** verification or retention/deletion events.
- **Read by:** import acceptance, synchronization, recovery, and source access.
- **Persists:** on the node owning the storage location and in local audit
  evidence where required.
- **Reason to change:** storage or verification state changed.
- **Must not own:** source identity or Card lifecycle.

---

# C. Registry catalogue

## RegistryProjectSnapshot

- **Kind:** immutable external projection.
- **Created from:** one observed Registry project version.
- **Changed by:** never; Registry change creates a new snapshot.
- **Read by:** catalogue construction, Work Object presentation, assignment
  validation, and project-linked queries.
- **Persists:** local Backend and, when included, VPS catalogue working set.
- **Reason to change:** none after creation.
- **Must not own:** Cabinet relationships or invoices.

## RegistryCatalogueSnapshot

- **Kind:** immutable offline catalogue.
- **Created from:** a selected set of RegistryProjectSnapshots under one stated
  completeness/filter policy.
- **Changed by:** never; refresh creates a new catalogue.
- **Read by:** VPS browsing, search, and offline object selection.
- **Persists:** locally and on the VPS while published/retained.
- **Reason to change:** none after creation.
- **Must not own:** current Registry truth after its observation time.

## RegistryCataloguePublication

- **Kind:** mutable delivery lifecycle.
- **Created from:** intent to publish one exact catalogue to one VPS node.
- **Changed by:** delivery attempts, acknowledgement, failure, or reconciliation.
- **Read by:** catalogue availability and operational diagnostics.
- **Persists:** local Backend and sufficient receipt state on the VPS.
- **Reason to change:** delivery knowledge changed.
- **Must not own:** catalogue contents or Registry filtering policy.

## RegistryCatalogueReplica

- **Kind:** persisted availability record.
- **Created from:** successful storage of one catalogue on one node.
- **Changed by:** verification, expiry, replacement, or deletion.
- **Read by:** offline availability checks and catalogue freshness presentation.
- **Persists:** owning node; local publication evidence may reference it.
- **Reason to change:** availability or retention state changed.
- **Must not own:** object selection decisions.

## WorkObject

- **Kind:** Cabinet working projection keyed by Registry `project_id`.
- **Created from:** first accepted Registry project snapshot.
- **Changed by:** newer accepted Registry snapshots or Cabinet attention-state
  decisions.
- **Read by:** project-linked Cabinet history, invoice queries, matching, and
  analytics.
- **Persists:** local Backend; compact project information is replicated through
  catalogue snapshots.
- **Reason to change:** observed Registry context or Cabinet attention state
  changed.
- **Must not own:** Registry name, address, or lifecycle truth.

## CardObjectAssignmentObservation

- **Kind:** immutable provenance observation.
- **Created from:** one exact Card revision and, when known, the catalogue used
  during capture.
- **Changed by:** never; a new Card revision produces another observation.
- **Read by:** Registry validation, audit, matching eligibility, and user
  explanation.
- **Persists:** VPS working state and local archive after import.
- **Reason to change:** none after creation.
- **Must not own:** replacement of the Card `object` block.

## ObjectAssignmentValidation

- **Kind:** immutable decision evidence.
- **Created from:** comparison of one Card assignment observation with current
  Registry data.
- **Changed by:** never; later Registry checks create new records.
- **Read by:** attention presentation, matching and analytics eligibility, and
  correction workflows.
- **Persists:** local Backend.
- **Reason to change:** none after creation.
- **Must not own:** silent reassignment of the Invoice Card.

---

# D. VPS-to-local transfer and import

## InvoiceTransferManifest

- **Kind:** immutable transfer description.
- **Created from:** one exact package of Card revisions, source bytes, and
  provenance selected for transfer.
- **Changed by:** never; a changed package requires a new manifest and hash.
- **Read by:** transport, import validation, idempotency, reconciliation, and
  receipts.
- **Persists:** VPS until reconciliation and locally with import evidence.
- **Reason to change:** none after creation.
- **Must not own:** acceptance policy.

## InvoiceSynchronization

- **Kind:** mutable transport lifecycle.
- **Created from:** an attempt to deliver one manifest between two nodes.
- **Changed by:** transport progress, failure, cancellation, or outcome
  reconciliation.
- **Read by:** retry scheduling, connection diagnostics, import correlation, and
  user-visible delivery state.
- **Persists:** VPS and correlated local evidence.
- **Reason to change:** knowledge about delivery changed.
- **Must not own:** validation, duplicate policy, or durable archive acceptance.

## InvoiceImport

- **Kind:** mutable local acceptance lifecycle.
- **Created from:** one delivered or otherwise received manifest.
- **Changed by:** validation, quarantine resolution, rejection, or durable
  acceptance.
- **Read by:** receipts, archive visibility, quarantine work, and audit.
- **Persists:** local Backend.
- **Reason to change:** local acceptance knowledge changed.
- **Must not own:** network delivery status or Card editing.

## ImportQuarantine

- **Kind:** mutable exception-resolution lifecycle.
- **Created from:** an import that cannot yet be safely accepted or finally
  rejected.
- **Changed by:** repair, additional bytes, review, discard, or resolution.
- **Read by:** operators, import acceptance, receipts, and diagnostics.
- **Persists:** local Backend outside normal archive visibility.
- **Reason to change:** missing evidence or review state changed.
- **Must not own:** normal accepted archive records.

## InvoiceTransferReceipt

- **Kind:** immutable target outcome evidence.
- **Created from:** the latest settled import knowledge for one idempotent
  manifest request.
- **Changed by:** never; reconciliation produces a new superseding receipt when
  policy requires history.
- **Read by:** VPS retention decisions, retry suppression, reconciliation, and
  user-visible synchronization result.
- **Persists:** local Backend and VPS.
- **Reason to change:** none after creation.
- **Must not own:** deletion of VPS data without retention policy.

## InvoiceWorkingReplica

- **Kind:** persisted node-availability summary.
- **Created from:** accepted knowledge of which Card revisions and source bytes
  exist on one node.
- **Changed by:** local acceptance, replication, retention, or deletion.
- **Read by:** synchronization planning, source access, and reconciliation.
- **Persists:** node-local state with enough shared evidence for reconciliation.
- **Reason to change:** available content on the node changed.
- **Must not own:** the content or semantics of those records.

## SynchronizationConflict

- **Kind:** mutable explicit resolution lifecycle.
- **Created from:** incompatible Card revisions or Backend decisions that cannot
  be resolved by idempotency and predecessor checks.
- **Changed by:** explicit resolution only.
- **Read by:** synchronization, archive visibility, operators, and audit.
- **Persists:** local Backend and sufficient VPS conflict state.
- **Reason to change:** conflict resolution state changed.
- **Must not own:** source-byte mutation or automatic arbitrary winner selection.

## LocalBackendConnectionObservation

- **Kind:** ephemeral or short-retention operational observation.
- **Created from:** a reachability/authentication/compatibility check.
- **Changed by:** replaced by later observations rather than treated as durable
  business truth.
- **Read by:** VPS user messaging and synchronization scheduling.
- **Persists:** limited VPS operational history.
- **Reason to change:** observed connectivity changed.
- **Must not own:** invoice or catalogue lifecycle.

---

# E. PresuPro, analysis, and Holded

## EstimateSnapshot

- **Kind:** immutable external projection.
- **Created from:** one observed PresuPro estimate version.
- **Changed by:** never; estimate change creates a new snapshot.
- **Read by:** matching, analysis, invalidation checks, and audit.
- **Persists:** local Backend.
- **Reason to change:** none after creation.
- **Must not own:** mutable PresuPro plan truth.

## InvoiceLineEstimateMatch

- **Kind:** mutable Cabinet decision lifecycle.
- **Created from:** acceptance or rejection of a proposed match between exact
  Card-line and EstimateSnapshot item references.
- **Changed by:** explicit decision or invalidation.
- **Read by:** plan-versus-actual analysis and matching review.
- **Persists:** local Backend.
- **Reason to change:** decision or validity changed.
- **Must not own:** Invoice Card facts or PresuPro estimate contents.

## PlanActualAnalysis

- **Kind:** calculated view, optionally cached with pinned inputs.
- **Created from:** exact estimate, Card, assignment, match, and assumption
  references.
- **Changed by:** recalculation from different pinned inputs; not manual editing.
- **Read by:** Cabinet conversation, UI, reporting, and forecasting.
- **Persists:** not required as primary truth; a cache or analysis receipt may be
  retained for reproducibility.
- **Reason to change:** one input or explicit assumption changed.
- **Must not own:** source facts, matches, or plan truth.

## HoldedPublication

- **Kind:** mutable business-publication lifecycle.
- **Created from:** one eligibility decision for one exact confirmed Card
  revision.
- **Changed by:** cancellation or settled gateway outcome.
- **Read by:** publication controls, reconciliation, audit, and user status.
- **Persists:** local Backend.
- **Reason to change:** business publication state changed.
- **Must not own:** Holded credentials or HTTP retry details.

## HoldedPublicationAttempt

- **Kind:** immutable technical attempt evidence.
- **Created from:** one gateway call attempt belonging to a HoldedPublication.
- **Changed by:** never; retry creates another attempt.
- **Read by:** reconciliation, diagnostics, and audit.
- **Persists:** local Backend or Holded Gateway receipt archive according to the
  later boundary contract.
- **Reason to change:** none after creation.
- **Must not own:** Cabinet publication eligibility.

---

# F. Deep-module preparation check

State 3 must not create one module for every model above. Candidate responsibility
clusters must be derived only after State 2 assigns invariants and transitions.

The following are preliminary ownership affinities, not accepted module names:

- accepted Card archive, validation evidence, source durability, duplicate
  handling, import, and quarantine share one durable-acceptance problem;
- Registry snapshots, catalogue construction/publication, offline provenance,
  and assignment validation share one project-context problem;
- Estimate snapshots, match decisions, and analysis share one plan-versus-actual
  problem;
- Holded business publication and attempt evidence share one controlled external
  publication problem;
- transport and connection observations may belong with synchronization, but
  transport must remain ignorant of archive acceptance policy.

These affinities are intentionally broader than endpoint-sized services. State 3
must reject modules that merely forward calls, expose every internal step, or
collect unrelated behavior under names such as `manager`, `processor`,
`helpers`, or `utils`.

## State 1 readiness result

The current model set is ready to proceed toward State 2 when:

1. every required field in `01_models.md` has a known source or is marked as
   requiring local-platform evidence;
2. mutable lifecycles are not conflated with immutable evidence;
3. transport, import, archive, external projections, and calculated views remain
   distinct;
4. no Backend model redefines Invoice Card V1;
5. remaining unknowns are policy questions or external-contract questions rather
   than hidden model placeholders.
