# State 7 bounded repair — Flow 2 source-attachment batch semantics

## Scope

This repair propagates the accepted State 2/4 per-file batch behavior through the generation notes for `attach_local_source`.

## Refined notes

```text
attach_local_source: [ORCHESTRATION] Evaluate every submitted file independently after resolving the exact accepted invoice target; a file-local rejection must be represented in SourceAttachmentBatchResult.items and must not by itself prevent valid sibling files from being attached.
attach_local_source: [BEHAVIOR] After classifiable per-file outcomes are applied, return one SourceAttachmentBatchResult containing every submitted file's attached, already_attached, or rejected outcome plus source_status recomputed from accepted archive truth.
attach_local_source: [VALIDATION_ERROR] Raise InvoiceNotFoundError when the exact accepted invoice target cannot be resolved. Raise SourceAttachmentRejectedError only when a request-level source-attachment condition prevents trustworthy independent per-file classification; do not use it for an ordinary file-local rejection that can be represented as SourceAttachmentItemResult(result="rejected").
attach_local_source: [PROVENANCE] Preserve previously accepted provenance when equivalent bytes are reattached; repeated attempts may add attempt evidence but must not silently replace the provenance of already accepted source evidence.

attach_local_source: [BEHAVIOR] A later verified attachment that satisfies every remaining required source changes awaiting_source or source_lost to complete while preserving all earlier incomplete-acceptance and loss-decision history.
```

## Irregular HTTP seam

`attach_local_source_handler` remains transport-only. Multipart parsing may construct the declared `LocalSourceFile` inputs, resolve authentication/authorization through the accepted access-control operations, and delegate the batch to `attach_local_source`. It must not convert a file-local rejected item into a batch-wide policy decision or implement archive acceptance itself.
