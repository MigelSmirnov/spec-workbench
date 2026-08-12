# State 7 repair — Flow 1 synchronization generation notes

## Status

Accepted bounded State 7 repair for `flow:synchronize_invoice_to_local_archive`.

These notes supplement the `# synchronization` entries in `80_notes.md` and exist to make the already accepted State 4 sequence generation-obligatory.

## `synchronize_invoice_work`

synchronize_invoice_work: [ORCHESTRATION] When transport produces an exact delivered package, present that exact manifest, immutable Card revision evidence, and required source evidence to durable_archive.accept_transfer_manifest before returning the delivered branch; a delivered result with receipt=None is forbidden when the archive boundary was reachable and no archive call was attempted.

synchronize_invoice_work: [ORCHESTRATION] Preserve the InvoiceTransferReceipt returned by durable_archive.accept_transfer_manifest in SynchronizationOutcome.receipt; do not reinterpret archive validation, duplicate, incomplete, integrity, or quarantine classifications inside synchronization.

synchronize_invoice_work: [ORCHESTRATION] When and only when the archive receipt is accepted or already_accepted, obtain authoritative proof for the same exact invoice revision/evidence identity through durable_archive.verify_durable_acceptance and preserve that result in SynchronizationOutcome.durable_acceptance.

synchronize_invoice_work: [FORBIDDEN] Never populate positive durable_acceptance from transport delivery, transfer receipt presence, or synchronization-local evidence; only a positive DurableAcceptanceVerification returned by durable_archive may establish it.

synchronize_invoice_work: [BEHAVIOR] Authentication failure, incompatibility, transport failure, remote unavailability, and unresolved or ambiguous delivery may return without an archive receipt because no exact delivered package is available for acceptance; preserve those states explicitly for reconciliation instead of fabricating archive work.

synchronize_invoice_work: [BEHAVIOR] A delivered exact package may return without positive durable acceptance only when durable_archive produced a classified non-accepted receipt or authoritative verification is negative/not-verifiable; omission of the archive acceptance or verification step is not a valid terminal behavior.

## Boundary preservation

These notes constrain sequencing only. They do not authorize `synchronize_invoice_work` to implement Card validation, duplicate policy, source-integrity policy, quarantine decisions, atomic archive visibility, or durable-proof sufficiency. Those remain `durable_archive` responsibilities.
