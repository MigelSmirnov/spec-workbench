# Source registration and canonical delivery contract — 2026-09-06

## Status and authority

This records D0-012, the contract correction requested by the owner after
recovery of the already associated originals. D0-007 through D0-011 remain
binding. It supersedes A05's requirement to turn multiple photographs into one
file and the assumption that a new Web confirmation is the only transfer
producer. It does not change InvoiceCardV1 or relax the draft-only metadata
mutation. The current assembled/runtime specification does not implement this
contract. The propagation ledger below is deliberately open until all owners,
contracts, consumers, and reciprocal evidence have been reviewed.

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
owned by Cabinet Flow, with the existing GitHub capability remaining canonical
until its migration under D0-008.

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

Cabinet Flow is the authority for source membership and completeness. Web owns
only verified working-copy custody and delivery records. The local Backend
owns its durable replicas and acceptance receipts. Each receiver independently
verifies bytes; an upstream hash declaration alone is not byte verification.

## Operation: register existing original custody

Owner: Cabinet Flow's source boundary accepts and associates originals;
Web's `source_custody` consumes the accepted association and verifies working
copies. This is separate from `attach_invoice_source_metadata`.

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

The file-ID encoding, source-set digest, exact binary framing and ordering,
issuer-authority representation, and completeness-evidence representation must
be frozen reciprocally before changing the serialized exchange. This document
does not silently select a new wire version or assert that old parsers accept
new metadata fields. The existing receipt meaning remains exact manifest and
byte acceptance. Only that exact acceptance plus the remaining A10 evidence
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

## Propagation ledger — not yet closed

The following are required changes, not claims that the current runtime already
implements them:

- State 1: distinguish document membership, per-file content, per-file custody,
  immutable canonical revision observation, and capture evidence. M06 and M14
  currently model a single content value and cannot encode the whole set.
- State 2: propagate D0-007/D0-008 into A01/A17 and D0-009/D0-012 into A05;
  review A03/A04/A08/A10/A13/A15/A16 for the new trusted ingress and replay scope.
- State 3–5: source_custody owns working-byte registration/retrieval;
  invoice_exchange owns canonical admission and pending/ready discovery;
  canonical identity and membership remain external owner facts. Retire the
  confirmation-only producer dependency and keep draft metadata effects separate.
- State 6–7: close typed models, canonical-source authority adapter, public and
  internal contracts, constructors, settings, persistence, routes, exact wire
  projection, and behavior notes; no undeclared dependency or arbitrary payload.
- Counterpart: review file identities, framing, source-set representation and
  acknowledgement/release coverage in cabinet-backend before wire-version change.
- Stage 8–9: assemble, adversarially review affected modules and the reciprocal
  scenarios, run admission, export and verify handoff, then run official Route B.

Until this ledger is closed, the old global_spec is a prior implementation
baseline, not an implementation of D0-012. Do not repair this by a handwritten
production route, database seed, forced confirmation, evidence rewrite, or by
marking a structural check as semantic acceptance.
