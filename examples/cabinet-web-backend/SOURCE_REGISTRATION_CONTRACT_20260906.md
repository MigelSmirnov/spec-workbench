# Source registration and canonical delivery contract — 2026-09-06

## Status and authority

This records D0-012, the contract correction requested by the owner after
recovery of the already associated originals. D0-007 through D0-011 remain
binding. It supersedes A05's requirement to turn multiple photographs into one
file and the assumption that a new Web confirmation is the only transfer
producer. It does not change InvoiceCardV1 or relax the draft-only metadata
mutation. The local assembled specification now carries this contract. It has not yet
passed final module review, Factory admission, generation, or runtime verification.
The propagation ledger remains open for those acceptance steps.

Recovery evidence: Cabinet_web PR 31, commit
`3fcbd19e5721ec68e1d9f9fe798a07a9c2b09124`, merged as
`f2ade64d7c99353bc2ef1426e6cf15a5fd514a59`; the immutable audit is
`docs/04-migrations/SOURCE_RECOVERY_20260906.json` in that repository.
It establishes recovered bytes and existing associations, not custody admission,
page completeness, line completeness, or local durable acceptance.

## Current producer — owner clarification, 2026-09-06

Cabinet Flow is a planned project, not a deployed provider. Cabinet_web remains
canonical for the current capability. A transitional read-only exporter reads
one explicitly pinned Git commit of that repository, verifies the existing
source-recovery audit against the exact Card files and original blobs, and
emits a bounded immutable canonical snapshot. It does not read a caller's
working tree, accept arbitrary Card JSON, call the GitHub request bridge, or
change the product repository. Future Flow may implement the same canonical
read boundary after that capability migrates; the current contract does not
require choosing its storage now.

The operator binds the trusted repository and exact accepted commit outside
request data. An exported snapshot is canonical evidence only within that
configured trust context; its self-reported origin and digest alone are not
authentication. No new public upload endpoint is created by the exporter.

## Identity and ownership

The logical source is the pair `(card_id, source_id)` from the canonical Card.
A source_id alone is not globally unique. The Card and its logical source are
currently owned by Cabinet_web through its existing canonical artifacts.
Cabinet Flow is the future owner only after an explicit capability migration
under D0-008; it is not a provider required by this registration contract.

One logical document has an ordered, nonempty collection of immutable file
references. Every file reference carries its byte hash, byte length, verified
media type, display filename if known, and a content identity distinct from the
logical source identity. Several distinct photographs of the same page remain
several original files. An ordinal describes file order only; it is not a page
number or evidence of page completeness. An original PDF remains its original
bytes. No recompression, cropping, concatenation, or synthetic PDF can replace
original evidence as an implicit registration step.

The source-set observation binds the exact Card revision, the logical source,
the ordered file references, the authority's association evidence, and its
explicit completeness evidence. It is immutable. Reobserving the equal set is
substitutable; changing membership, order, byte identity, or the referenced
Card revision produces another observation. File custody is an integration
obligation with continuity across verification, delivery, and release. It is
not the document's identity or the product's completeness decision.

The current Cabinet_web artifacts are the authority for existing source
membership and capture evidence. They do not assert document-page completeness.
The integration backend owns only verified working-copy custody and delivery
records. Future Flow ownership begins only when that capability migrates. The local Backend
owns its durable replicas and acceptance receipts. Each receiver independently
verifies bytes; an upstream hash declaration alone is not byte verification.

## Operation: register existing original custody

Owner: the current Cabinet_web capability supplies its already accepted
originals and associations; the integration backend’s `source_custody` consumes
that accepted association and verifies working copies. No new association or
Flow service is required. This is separate from `attach_invoice_source_metadata`.

Required inputs at the integration boundary:

- an authenticated authority and authorization for this exact Card/source;
- the exact canonical Card revision reference and content hash, resolved from
  the capability's current canonical owner;
- its immutable source-set observation with ordered file references;
- bounded access to each exact file from the owner's accepted immutable store;
- a caller-scoped idempotency identity and actor provenance.

A caller-supplied Card, status, association, filename, or self-computed digest
cannot serve as its own canonical-authority evidence. A supplied path is never
an authority or a remotely dereferenceable storage location. Syncthing is
intake transport; a synchronized working file is not accepted immutable storage.
Deletion or replacement in the Inbox must not change accepted bytes.

The operation accepts an already confirmed Card. It verifies the current
canonical revision and existing logical source association, checks each file
under A05/A13, stores immutable working copies outside the synchronized/public
roots, reopens them to verify exact size and hash, and records custody only
when the complete declared set is verifiable. Staged individual files do not
make a partially registered set available. Recovery may complete the same
publication or leave an explicit failed/pending outcome, never false success.

The observable result binds the exact revision and source-set observation,
per-file verification results, the committed custody outcome, and whether the
logical operation was replayed. It returns no path, secret, fabricated Card
revision, confirmation, or local acceptance. A success must be recoverable by
that exact operation identity after a lost response.

Equal retries have one logical result. An idempotency key reused with different
input is a conflict. Different bytes under the same accepted content identity
are a conflict. An explicitly expanded source set is a new immutable
observation, never an overwrite of an old issued set. Concurrent operations
cannot lose membership, mix sets, duplicate effects, or clear missing evidence.
Physical deduplication of equal bytes never grants cross-Card access.

Observable refusal categories must distinguish authorization failure,
canonical revision mismatch, unproven association, byte absence, byte mismatch,
invalid media/limits, and idempotency conflict. No refusal mutates the Card or
its existing capture proof. An operational failure leaves a retryable exact
operation or a terminal recorded failure; it never silently invents a new ID.

## Operation: admit a canonical revision for delivery

Owner: `invoice_exchange` owns operational admission and discoverability.
`invoice_lifecycle.confirm_invoice` is not the producer for imported canonical
revisions. Source custody does not perform this admission implicitly.

Inputs are the authenticated canonical revision observation, its source-set
observation, its existing line-capture evidence, and committed working custody.
Canonical reads must come from the selected single writer or an authenticated
read-only projection with exact origin/revision evidence. Copying a Card into
PostgreSQL does not make it authoritative. Admission cannot invoke a canonical
Card commit or atomically claim a transaction over GitHub and PostgreSQL.

Admission records one operational outcome for every observed revision:
ready with an immutable manifest, or pending with exact unmet prerequisites.
Absence of old Web confirmation output cannot hide a canonical revision.
A later retry reevaluates that exact revision; it must not silently substitute
a newer Card or retain stale capture evidence under the new revision's hash.

Ready requires a valid canonical InvoiceCardV1 revision, an accepted nonempty
source set, verified bytes for every declared member, and complete capture
proof bound to that exact source and Card hash under D0-011. Missing or stale
proof leaves the revision visible as pending. Existing confirmed status is
preserved as a product fact but does not bypass these delivery prerequisites.
A custody success never synthesizes or upgrades the capture proof.

The manifest pins exactly one Card revision and every required immutable file.
Changing the Card revision or accepted source set requires a new manifest and
new receipt coverage. Previously issued manifest bytes, IDs, hashes, source
membership, and local receipts remain immutable. An offline local Backend
leaves ready work durable and discoverable without claiming acceptance.

## Reciprocal local Backend boundary

Backend A78 already distinguishes `InvoiceCardV1.source.source_id` from the
required binary identities in `InvoiceTransferManifest.source_references`.
A65 already supports separate source identities for a multi-photo package.
Preserve both decisions: each required file receives its own manifest content
identity, while the product Card retains its original logical source ID.
Never reuse that logical ID as the content ID for multiple unequal files.

The transitional input schema freezes file identity and source-set identity.
The existing Backend wire version, metadata shape and binary framing remain
unchanged under A20: one manifest ContentReference per exact original, in the
accepted order, with its content_id copied from the input file reference. The
new canonical snapshot wrapper and source-set digest are internal input and
operational binding evidence; they are not extra fields for the old Backend
parser. Reciprocal verification must exercise the unchanged wire with several
file identities for one logical Card source. The existing receipt meaning
remains exact manifest and byte acceptance. Only that exact acceptance plus the remaining A10 evidence
can authorize explicit working-copy release; registering or sending is not
release authority.

## Read and retrieval behavior

A source read exposes the exact registered set and its truthful state.
Retrieving bytes selects one exact file within an authorized Card/source/set;
a source-only request cannot arbitrarily return the first image. Absence,
release, or corruption of a selected file is explicit. The returned stream is
bounded and inert, with verified media type and safe display metadata. Access
never exposes internal storage keys or permits a client to choose paths.

## Acceptance scenarios

1. Register a one-file PDF against a confirmed Invoice. Its raw Card JSON,
   revision, logical source ID, status, lines, and capture proof remain unchanged.
2. Register a multi-photo invoice using its recorded associations and order.
   Every distinct photograph is retained, including alternate shots; no new
   PDF or replacement Card source is created.
3. Equal retry and two concurrent equal registrations produce one logical
   result. Reusing an effect identity for another set fails explicitly.
4. A stale Card hash, wrong Card/source pair, untrusted association, missing
   member, unsupported media, byte mismatch, or partial publication cannot
   produce successful complete custody or ready delivery.
5. Recovery of originals without capture evidence produces custody success
   and a truthful pending delivery outcome, with no synthetic line proof.
6. An existing canonical confirmed Card becomes visible to discovery without
   `confirm_invoice`, `commit_card_revision`, or any canonical product write.
7. A new source-set observation cannot mutate an issued package or reuse its
   receipt to release files absent from that receipt.
8. Two Cards using the same logical `source_id` stay isolated; knowledge of a
   hash, filename, Card ID, or another Card's download authority is insufficient.
9. Registration of all recovered files must preserve the audit's raw hashes
   for all 12 existing Invoice Cards. Recovery-file count and invoice coverage
   are not page-completeness or capture-completeness assertions.
10. Interruption before and after metadata commit, a lost response, and a local
    Backend outage retain truthful state and permit exact idempotent recovery.

## Propagation ledger — assembly checkpoint, acceptance still open

- States 1–3: M181–M197, A19/A20 and module ownership are authored. M06
  distinguishes per-file content identity from the unchanged logical Card source;
  M45 distinguishes integration observation provenance from product provenance.
- States 4–5: registration and admission have independent flows and internal-only
  operator boundaries. Confirmation no longer produces delivery work.
- States 6–7: 452 typed functions, 63 public operations, 449 classified notes,
  29 persistence tables and deterministic query bindings are assembled. Pending
  publication plans commit before filesystem writes. Retained trusted pins support
  retries after the active pin advances. Immutable effect results preserve earlier
  pending outcomes; a fresh effect can reevaluate admission.
- Canonical input uses an operator-installed private accepted-pin.json under the
  configured source store's canonical-input directory. Its snapshot selects
  canonical-input/<snapshot_sha256>/bundle. Missing input blocks these operations,
  not generic application startup. No new RuntimeSettings fields or public upload
  channel are introduced.
- Retrieval binds exact Card, source set, admission revision and file identity.
  Card-only status refuses ambiguous multiple-set admissions. Source streams load
  one member lazily and discard bytes at EOF.
- Release of new canonical sets fails closed: the existing release command lacks
  typed local verification evidence required by A10. No original is deleted and
  no successful release is claimed. Completing that boundary remains separate work.
- Counterpart: all 12 recovered raw Cards validate against the actual generated
  cabinet_backend InvoiceCardV1 model with logical source IDs preserved. Existing
  external wire bindings remain unchanged. The external transport adapter and
  archival end-to-end behavior have not been demonstrated by that model check.
- Local structural gates for language, ownership, identity, data, contracts,
  external bindings, notes, routes and flows pass. The temporary checkout cannot
  resolve the Factory codec registry and witness configuration; the aggregate
  gate must run again in the canonical sibling checkout without waivers.
- Registration/admission runtime witnesses cover exact retry, conflicting keys,
  multi-file custody, partial publication recovery, pin advancement, concurrency,
  missing capture, lazy retrieval and package bytes. Their Python syntax is checked;
  they have not run against the new generated runtime.
- Stage 8–9: final adversarial module review, admission, export, handoff verification
  and official Factory Route B remain open. No new runtime is deployed.

Do not repair this through a handwritten production route, database seed,
forced confirmation, evidence rewrite, or by treating structural validation as
semantic or runtime acceptance.
