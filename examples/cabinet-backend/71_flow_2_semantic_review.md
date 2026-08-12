# Cabinet Backend — Stage 7.1 Flow 2 semantic review

Flow: `flow:accept_local_source_attachment`

Status: **AMBIGUITY — repair required**

## Reconstructed accepted behavior

The accepted State 2/4 behavior is per-file evaluation inside one batch:

```text
authorized exact invoice target + files
        ↓
resolve accepted invoice
        ↓
for each submitted file: validate media/hash/target/provenance
        ├─ accepted/already-attached → preserve accepted source evidence
        └─ rejected → explicit per-file rejected result
        ↓
recompute source status from accepted evidence
        ↓
return per-file results + source status
```

A batch containing both valid and rejected files may therefore produce partial success. Rejected files must not replace accepted evidence, but their presence does not erase successful attachments from the same batch.

## Adversarial ambiguity

### Interpretation A — per-file partial success

Each file is evaluated independently. Valid files are attached, rejected files are represented as `SourceAttachmentItemResult.result = "rejected"`, and the returned `SourceAttachmentBatchResult` reports all outcomes.

### Interpretation B — batch-wide rejection

The implementation validates files in sequence and raises `SourceAttachmentRejectedError` as soon as one file is unsupported, unreadable, wrong-target, or hash-mismatched. No valid file from the same request is attached.

The current State 5/7 exception wording permits Interpretation B even though State 2 and State 4 require independent per-file outcomes and explicit partial success.

## Material difference

For a batch `[valid_photo, invalid_pdf]`, Interpretation A attaches the valid photo and returns one accepted plus one rejected item. Interpretation B attaches nothing and raises. This is observable business behavior, not implementation variation.

## Finding

```text
flow: flow:accept_local_source_attachment
status: AMBIGUITY
material_alternative_found: yes
placeholder_implementation_found: no
scenario_gaps:
  - mixed valid/rejected batches are not unambiguously required to preserve valid attachments
findings:
  - owner: structure
    scope: State 5 attachment outcome/error semantics propagated through State 6 exception meaning and State 7 notes
    interpretation_A: ordinary file-level rejection is returned per item while valid sibling files may attach
    interpretation_B: any rejected file raises SourceAttachmentRejectedError and aborts the entire batch
    required_resolution: reserve SourceAttachmentRejectedError for batch-level inability to produce trustworthy per-file results; represent ordinary source-policy rejection as per-file rejected items
```

## Earliest repair owner

State 2 and State 4 are already explicit. The loss occurs when the public API compresses partial-success semantics into an exception description. Repair State 5 first, then propagate to State 6 exception taxonomy and State 7 notes.

`semantic_closed`: **no**, pending repair and rerun.
