# State 5 bounded repair — Flow 2 source-attachment batch semantics

## Scope

This repair closes the Stage 7.1 ambiguity recorded in `71_flow_2_semantic_review.md` without changing State 2 product policy or the State 6 function signature.

It refines `public_op:durable_archive.attach_local_source`.

## Accepted public-operation semantics

For one resolved accepted `invoice_id`, `attach_local_source` owns one batch invocation containing one or more submitted files.

Each submitted file MUST be evaluated independently against the accepted media, readability, expected-source, content-hash, target and provenance rules.

Ordinary source-policy rejection of one file MUST be represented in the returned `SourceAttachmentBatchResult.items` as that file's rejected result. It MUST NOT by itself abort valid sibling files in the same batch.

A mixed batch may therefore return both successful/idempotent and rejected item results. Successfully attached sibling files become accepted source evidence even when another sibling file is rejected.

After all file-level outcomes that can be classified are determined, the operation MUST recompute and return `source_status` from the resulting accepted archive truth.

## Error boundary

`InvoiceNotFoundError` remains a whole-operation error because no accepted mutation target exists.

`SourceAttachmentRejectedError` is reserved for a batch-level condition in which the Backend cannot safely produce trustworthy independent per-file results under accepted archive policy, for example when the request-level target/evidence relationship is itself invalid or ambiguous in a way that cannot be localized to individual submitted files.

Unsupported, unreadable, wrong-target or hash-mismatched evidence that can be classified for one specific submitted file belongs in that file's rejected item result and does not roll back accepted sibling-file outcomes.

Unexpected persistence/system failure remains outside normal attachment outcomes.

## Ownership boundary

This refinement changes no archive ownership: `module:durable_archive` still owns source acceptance, provenance, idempotency and source-status transitions. HTTP/agent adapters may only transform transport input, obtain authorization and translate the returned batch result.
