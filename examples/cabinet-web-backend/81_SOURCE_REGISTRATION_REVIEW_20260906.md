# Source registration assembled review — 2026-09-06

Review authority: D0-008/D0-012 and A05/A17/A19/A20, with retained A10 release
and A15 protected-operator constraints. Cabinet_web is the current canonical
owner; Cabinet Flow is planned. Exact module packet hashes are in the review
ledger. Every deterministic module review reports zero structural blocks.

This review assesses the four packet questions: materially different observable
behavior, trivial/forwarding implementations, located refusals/effects, and
behavior without an accepted business source. Existing independent capabilities
retain their reviewed behavior; expanded shared model and UoW surfaces do not
transfer source admission responsibility to them.

Resolved findings:

- Post-export lineage reconciliation found the Workbench baseline had omitted
  the accepted validation_rules deterministic unit. Restored its exact accepted
  IR and ownership from Factory bb77c05d, preserving A02/A17. This is a retained
  generation mechanism, not part of source registration behavior.

- A pending admission without a custody record must have a readable status.
  It cannot pass None to the retained-source reader. Added a runtime witness.
- SourceDownload has one policy cursor with model/interface constructor inputs.
  It delegates all file I/O to SourceByteStore; the old raw-payload implementation
  is retired. No local executable boundary is mislabeled external or policy.
- Exact deterministic digest signature, data-provider symbol ownership and value
  types, imported contract model surfaces, and wire-framing notes are closed.
- The unused whole-table working-set query is removed. New canonical release
  remains an explicit refusal until typed local A10 evidence is provided.

Reviewed module outcomes:

- `models`: Reviewed M181–M197, per-file versus logical source identity, immutable typed effect results, retained pins, bounded error/reason vocabularies and complete UoW port signatures. Product InvoiceCardV1 fields remain unchanged.
- `data_provider`: Reviewed deterministic declaration ownership, positive-integer capture version, private path selectors, capability separation and note reachability. New operations occur only in the protected-operator catalogue; no ordinary transport grant is introduced.
- `runtime_settings`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `capability_policy`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `credential_vault`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `abuse_throttle`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `access_control_errors`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `security_evidence`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `authentication_admission`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `capability_grants`: Protected operator context is separately authenticated and rechecked against locked active stored owner/operator, exact identity/kind and absent machine node in caller transaction. Actor cannot be substituted.
- `principal_lifecycle`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `access_control`: Narrow require_protected_operator facade delegates to the accepted capability_grants mechanism with caller-owned UoW. No new credential, channel or auth bypass.
- `effect_journal`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `card_workspace`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `invoice_catalogue`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `validation_rules`: Reconciled against Factory accepted bb77c05d: preserve the exact deterministic backend IR, module owner, typed signature, model and catalogue imports, and ordered issue projection. No business rule or formula value is changed by source registration.
- `invoice_validation`: Public proposal and validation behavior remains unchanged. The exact accepted validation_rules evaluator is imported instead of regenerated as an internal formula interpreter; duplicate discovery remains in the capability owner.
- `invoice_lifecycle`: Reviewed removal of derive_transfer_records from contracts, flows and confirmation. Card/capture/effect atomicity and draft mutation guards remain; confirmation no longer silently becomes canonical delivery admission.
- `project_workspace`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `cabinet_persistence`: Reviewed exact composite keys, immutable effect-result insert-only surface, unique manifest binding, explicit per-Invoice/per-manifest query filters and transaction ownership. Removed unused whole-table working-set read. No canonical product seed or second writer is introduced.
- `source_byte_store`: Reviewed staging_reference_for as pure exact planned-reference derivation, stage reuse and existing exclusive byte publication. Filesystem ownership remains in the deterministic backend; no path is supplied by a request.
- `system_clock`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `canonical_digest`: Source-set digest uses the registered BaseModel contract and typed recipe. Audit provenance is excluded only from set identity; Card identity/hash and ordered per-file identities remain bound. Manifest hashing and wire recipe are preserved.
- `canonical_invoice_source`: Reviewed current versus retained pin authority, strict JSON and bounded no-symlink object reads, exact raw Card hash versus typed equality, preserved capture classification and imported Card envelope provenance. Missing input is explicit and never synthesized from product DB or current working files.
- `source_custody`: Reviewed two committed phases, exact request equality even PREPARED, pending retained pins, deterministic pre-write plans, full-set byte verification and immutable result replay. One policy cursor delegates file I/O to deterministic SourceByteStore. Exact-set authorization preserves shared-logical-ID isolation. Canonical release refuses missing typed A10 evidence without deleting bytes.
- `invoice_exchange`: Reviewed admission independently of confirmation, stable first observation and immutable READY manifests, original pending-effect replay, fresh-effect reevaluation, exact multi-file framing and no fabricated receipt. Fixed missing-custody status and explicit multiple-set ambiguity. Pull verifies exact retained Card and every member before issuance; stream failures remain interruptions.
- `registry_replica`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `chatgpt_interaction`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `web_gateway`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `sync_gateway`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `runtime_control`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `api`: Reviewed against the retained 3d12c16 behavior: owned contracts and behavioral notes are unchanged. Expanded model/dependency surfaces do not alter the module’s existing call signatures, authority, transport projection or effect semantics. Canonical admission remains owned by invoice_exchange, not this module.
- `bootstrap`: Reviewed one canonical source from existing typed root/size settings, shared effect journal and services, and no pin requirement at startup. Existing startup publication handling cannot claim completed canonical custody; explicit retry rechecks durable plans and bytes.

Limits of this PASS: new runtime witnesses are authored and syntax checked,
not executed against newly generated code. The reciprocal check validates all
12 existing raw Cards against cabinet_backend’s actual InvoiceCardV1; it is not
an external transport/archival round trip. No source registration, admission,
receipt, deletion or deployment has been performed on live data. Stage 9 must
still validate this committed review, clean source/target and exact handoff.

Re-review 2026-09-06 (f2aa792 lineage): the `SourceByteStore.staging_reference_for`
port note now states that the derived staging reference is part of the committed
publication plan and that `stage` returns that same reference. Only the `models`
slice changed (packet hash d333e9260e20… → e75c0c75e4de…); its review packet reports
149 contracts, 149 notes and zero structural blocks. The concrete
`LocalFilesystemSourceByteStore` contract order was also moved beside its class in
the contract plan; no signature, decision or other module slice changed.

Re-review 2026-09-06 (model closure repair): Route B generation of
`canonical_invoice_source` refused code that read `pin.snapshot_sha256` and
`record.canonical_snapshot_sha256`, because `60_model_closure_domain.json` had
never carried the `*_sha256` fields that State 1 declares for M181–M193 and the
accepted notes rely on (pin digest, raw Card/capture hashes, audit and schema
digests). Twelve fields were restored exactly as authored in
`01_models_source_registration.md`; `70_persistence_closure.json` gained the
matching `canonical_snapshot_sha256` columns on the custody and admission tables
and `capture_raw_sha256` on admissions. No note, decision or signature changed.
Slices re-hashed with zero structural blocks: `models`, `credential_vault`, `authentication_admission`, `capability_grants`, `principal_lifecycle`, `access_control`, `card_workspace`, `invoice_catalogue`, `project_workspace`, `cabinet_persistence`, `canonical_digest`, `canonical_invoice_source`, `source_custody`, `invoice_exchange`, `registry_replica`, `chatgpt_interaction`, `runtime_control`, `bootstrap`.

Re-review 2026-09-06 (note precision, after the model surface gate landed):
`validate_invoice` now names `totals.gross` as the source of the duplicate
lookup's gross_total (InvoiceCardTotals has no gross_total; the generated code
had answered 500). `read_pinned_canonical_snapshot` and
`read_canonical_input_object` now state the walk order
`<snapshot digest>/CANONICAL_INPUT_BUNDLE_DIRECTORY/...`, the layout the
snapshot exporter and the contract document already fix; the generator had
inverted it. Slices re-hashed with zero structural blocks: `invoice_validation`, `canonical_invoice_source`.

Re-review 2026-09-06 (snapshot validation mode): the canonical source witnesses
refused every fixture snapshot with invalid_snapshot because the generated
reader validated the decoded dict in pydantic strict mode, which rejects the
Decimal, date and datetime strings JSON carries inside InvoiceCardV1. The note
now names JSON-mode model_validate_json and states that strictness applies to
the JSON text. Slices re-hashed with zero structural blocks: `canonical_invoice_source`.

Re-review 2026-09-06 (ordinal base): the witnesses refused every fixture set
with source_set_mismatch because the generated validator required ordinals
0, 1, ... while the snapshot exporter writes 1, 2, .... The note now states
that the first member carries ordinal 1. Slices re-hashed with zero structural
blocks: `canonical_invoice_source`.

Re-review 2026-09-06 (open flags): Route B refused a canonical_invoice_source
candidate for hasattr(os, "O_NOFOLLOW") (reflective_attribute_access gate). The
three reading notes now prescribe one shared helper with the unconditional
flags os.O_RDONLY | os.O_NOFOLLOW on the POSIX runtime and no platform probe.
Slices re-hashed with zero structural blocks: `canonical_invoice_source`.

Re-review 2026-09-06 (retained pin source, status code type): generated
register_canonical_source_set and admit_canonical_invoice filled
canonical_repository_commit with observation digests because no note named the
source; both notes now copy canonical_snapshot_sha256 and
canonical_repository_commit from read_canonical_input_pin. M132
InvoiceTransferStatus.safe_error_code was typed TransferReceiptErrorCode while
get_invoice_transfer_status reports admission-pending and canonical-source
codes; the field is now a bounded code string (str | None) and the note names
the .value. Slices re-hashed with zero structural blocks: `models`, `credential_vault`, `authentication_admission`, `capability_grants`, `principal_lifecycle`, `access_control`, `card_workspace`, `invoice_catalogue`, `invoice_lifecycle`, `project_workspace`, `cabinet_persistence`, `source_custody`, `invoice_exchange`, `registry_replica`, `chatgpt_interaction`, `runtime_control`, `bootstrap`.

Re-review 2026-09-06 (drill transaction shape): Route B refused a
runtime_control candidate that re-read and updated the drill record after
commit (owned_transaction_call_outside_begin). The verify_backup_restore note
now states the A17 single-transaction shape. Slices re-hashed with zero
structural blocks: `runtime_control`.

Re-review 2026-09-06 (recovery clock): Route B refused a bootstrap candidate
for datetime.now() in startup recovery (naive_datetime_now). The composition
root note now binds every recovery timestamp to the single SystemClock now().
Slices re-hashed with zero structural blocks: `bootstrap`.

Re-review 2026-09-06 (content reference projection): the witnesses refused
registration with custody_mismatch because get_registered_source_observation
compared contents[i].source_id with the logical source_id and prefixed the
content hash, while source_custody projects source_id = member.content_id and
the bare digest (what final_reference_for accepts). The projection is now
stated identically in the three notes that name it. Slices re-hashed with zero
structural blocks: `canonical_invoice_source`, `source_custody`, `invoice_exchange`.

Re-review 2026-09-06 (custody equivalence, pull source id): the witnesses
refused the concurrent re-registration under a newer pin (custody_mismatch:
equivalence had compared the retained pin with the current one) and the
package pull (source_not_stored: the retrieval request carried the member
content_id as source_id). Both notes now state the rule exactly. Slices
re-hashed with zero structural blocks: `source_custody`, `invoice_exchange`.

Re-review 2026-09-06 (receipt hash order): the live stand refused the
acknowledgement of every multi-file manifest (422) because the generated
receipt check compared accepted_source_hashes as a tuple in manifest order
while cabinet_backend reports them sorted. The note now compares the hashes as
multisets. Slices re-hashed with zero structural blocks: `invoice_exchange`.

Re-review 2026-09-06 (proposal issue strings): witness A02 refused a
regenerated chatgpt_interaction that placed a revision model dump into
ValidationIssue.expected/actual (str | None). The proposal note now states
that revision-reporting issues carry the content_hash strings. Slices
re-hashed with zero structural blocks: `chatgpt_interaction`.
