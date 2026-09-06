# State 2 — Existing originals and canonical revision admission

## Accepted decision A19 — source-set registration preserves the canonical Card

D0-012 and M181–M187 separate a logical source, its immutable file membership,
and the working-copy custody obligation. The owner clarified that Cabinet Flow
is planned; the current canonical capability is Cabinet_web under D0-008.
A05 owns general file safety, A03 authority, A04 replay, and A17 durability.

### Normative rules

1. The current input is one bounded, operator-pinned canonical snapshot of
   Cabinet_web. Its repository and accepted commit/hash are protected operator
   configuration, never request-selected paths, URLs, Git refs, or credentials.
   The adapter reads immutable input only and cannot invoke a product mutation.
2. A source-only recovery audit may supply the already reviewed associations
   only after its Card and original hashes have been verified against the
   pinned canonical revision. The audit is not a custody receipt and cannot
   authorize its own acceptance merely through self-reported origin fields.
3. Registration is a protected operator integration operation with one exact
   Card revision, source set, actor and effect identity. It is outside the
   plugin, browser and local-node grantable catalogues, like the existing
   protected operator administration. Ordinary caller credentials cannot turn
   a supplied snapshot into trusted input. The operation exposes no new public
   upload or arbitrary file-management surface.
4. Registration resolves all Card and file facts from the trusted snapshot.
   It refuses a mismatched Card/source/revision/set before creating custody.
   A confirmed Card is a valid target: no draft transition, metadata attachment,
   Card commit, confirmation call, line rewrite or evidence rewrite occurs.
5. Every distinct original has its own content identity. Preserve accepted
   source membership and file order, including alternate shots. Equal bytes
   may share physical storage but never object-level retrieval authority.
   An empty observed set remains missing source evidence, not stored custody.
6. Working bytes are independently checked under A05/A13, staged, published,
   reopened and verified through the byte-store boundary. Set custody is stored
   only when every declared member is durable and verifiable. Partial progress
   stays recoverable pending/failed evidence and is never complete success.
7. Equal retry has one retained logical result; the same effect identity with
   another request is a conflict. A different set produces another custody
   obligation. Concurrent attempts cannot overwrite content or lose members.
   Already issued manifests and release receipts are never changed by retry.
8. Exact file retrieval requires the authorized Card/source/set/hash. A guessed
   hash or a source-only request cannot select or authorize one of several files.
   No read returns a filesystem path, credential or active executable preview.
9. Legacy capture evidence remains byte-for-byte unchanged. Missing, malformed,
   stale, mismatched or incomplete proof remains distinguishable. Mechanical
   verification of old proof never asserts source-page completeness, produces
   a new proof, or establishes local Backend durable acceptance.

### Formal invariants

```text
register_source_set -> card_bytes_before = card_bytes_after
register_source_set -> capture_bytes_before = capture_bytes_after
stored_set -> every_declared_original_reopened_and_verified
same_effect AND different_request -> conflict
new_membership -> new_source_set_observation
content_hash_known -/> exact_file_read_authorized
canonical_snapshot_self_claim -/> canonical_authority
```

### Required tests

1. Confirmed multi-photo and PDF targets preserve Card bytes and existing proof,
   including alternative photographs and two Cards with the same logical source
   ID. [witness: verification:canonical_source_registration]
2. A dirty working tree cannot replace the pinned source revision; unlisted
   canonical Cards, stale audit hashes, substituted originals and traversal
   paths fail explicitly. The offline contract has executable witnesses in
   tests/test_legacy_invoice_snapshot.py; these do not replace runtime tests.
3. Partial publication, crash recovery, concurrent equal/conflicting attempts,
   and replay after a lost response cannot report false stored custody.
4. A plugin/browser/local-node caller cannot use the protected operator input
   boundary; another Card's content identity cannot grant file access.

### Consequence

The canonical-source adapter owns read verification; source_custody owns
working-byte registration and exact retrieval. The existing draft metadata
mutation remains separate. The old M14 single-file browser record remains
legacy evidence and cannot stand in for M185 multi-file set custody.

## Accepted decision A20 — canonical admission is independent of confirmation

D0-007/D0-008/D0-012 and M188–M191 define integration work for already existing
canonical revisions. A08 still owns the exact reciprocal package and A10 the
explicit safe release. The local Backend's [product-card preservation rule](../cabinet-backend/02_rules_import_admission.md)
separates logical source identity from manifest file identity, and its
[source-attachment concurrency rule](../cabinet-backend/02_rules_security_files_concurrency.md)
already accepts multi-photo source packages.

### Normative rules

1. Protected operator admission selects one exact trusted canonical observation
   and records a durable ready or pending integration outcome. It never calls
   confirm_invoice or commits a canonical product Card to manufacture work.
2. Every observed revision remains visible through admission status, including
   absent working bytes or capture proof. An empty old confirmation-produced
   queue cannot stand as evidence that no canonical Invoice exists.
3. Ready requires the exact canonical revision, nonempty accepted source set,
   verified set custody and valid current capture proof under D0-011. Missing
   prerequisites produce bounded explicit pending reasons. A confirmed status
   alone cannot bypass custody or capture checks.
4. Admission owns one operational PostgreSQL transition for its own projection,
   manifest and work record. Canonical input is an immutable external fact,
   not a second product master or a participant in a distributed Card commit.
   No direct seed into the old canonical Card tables is an admission operation.
5. The existing transfer wire structure and version remain unchanged: one
   canonical Card revision and an ordered tuple of immutable ContentReference
   entries. Each entry copies one distinct file content_id/hash/size/media from
   the accepted source observation. It does not reuse the logical Card source
   ID for multiple unequal files. No snapshot wrapper or new source-set field
   is silently added to the old Backend wire.
6. The source-set digest is operational binding evidence. The existing manifest
   digest already covers the exact ordered file references and Card revision;
   the local Backend continues to verify every required file and return its
   exact manifest receipt. Product InvoiceCardV1 content remains unchanged.
7. Equal admission replays one logical outcome. A changed Card revision or file
   set produces another manifest. Ready manifests and their issuance/receipt
   evidence are immutable; pending obligations may be re-evaluated against a
   newly trusted observation of the same canonical facts and actual proof.
8. Pull reads the exact retained canonical projection and verified working files
   named by the admitted manifest. It cannot substitute a later Card, a different
   source set, or the first photograph. Local unavailability leaves work durable;
   no operator admission claims local acceptance or triggers automatic release.
9. Exact source-set release retains A10's complete reciprocal checks. It cannot
   release a shared file still required by another live working-set obligation,
   or use a receipt for one file/set to release a different one.

### Formal invariants

```text
canonical_admission -/> canonical_card_commit OR invoice_confirmation
observed_revision -> visible_ready_or_pending_outcome
ready_admission -> exact_canonical_revision AND complete_verified_set_custody
                   AND valid_exact_capture_evidence
changed_revision_or_membership -> new_immutable_manifest
manifest_source_reference -> one_exact_original_file
operator_admission -/> local_durable_acceptance OR release_authority
```

### Required tests

1. Existing confirmed canonical Cards enter ready/pending integration state
   without Card writes or confirmation, and missing proof remains pending.
   [witness: verification:canonical_invoice_admission]
2. A multi-photo package carries every distinct file in accepted order and
   preserves the Card's logical source ID. The existing Backend accepts the
   unchanged wire shape and returns a receipt bound to all exact file hashes.
3. Retry, concurrent admission, stale revisions, lost responses, and an offline
   local Backend preserve exact identity and previously issued evidence.
4. A receipt for a former set or a subset cannot release the new set or any
   content still needed by another live working-set obligation.

### Consequence

invoice_exchange owns canonical admission and consumes source_custody evidence.
The confirmation-only producer is retired for this capability. The protected
canonical input and admission records close the legacy-to-transfer connection
without introducing Cabinet Flow storage or another product writer.
