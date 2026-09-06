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
