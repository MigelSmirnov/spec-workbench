# Cabinet Backend — Stage 7.1 Flow 2 semantic review

Flow: `flow:accept_local_source_attachment`

Status: **semantic_closed**

## Reconstructed accepted behavior

The accepted behavior is per-file evaluation inside one batch:

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

A batch containing both valid and rejected files may produce partial success. Rejected files do not replace accepted evidence, and their presence does not erase successful attachments from the same batch.

## Original Stage 7.1 finding

Before repair, the State 5/7 wording allowed two materially different implementations:

- per-file partial success;
- batch-wide abort via `SourceAttachmentRejectedError` on the first rejected file.

For a batch `[valid_photo, invalid_pdf]`, those alternatives produced different accepted archive truth.

## Applied repair

The loss was repaired at the earliest affected layer and propagated forward:

- `50_public_apis_flow2_semantic_repair.md` restores the State 2/4 requirement that classifiable file-local rejection is returned as a rejected `SourceAttachmentItemResult` and does not abort valid sibling files;
- `60_exception_taxonomy.json` now reserves `SourceAttachmentRejectedError` for request/batch-level conditions that prevent trustworthy independent per-file classification;
- `80_notes_flow2_semantic_repair.md` makes per-file evaluation, complete result reporting, status recomputation, idempotent provenance preservation, and the transport-only HTTP seam generation-obligatory.

No function signature or product behavior was added.

## Scenario rerun

### A1 — valid attachment changes source evidence only

**PASS.** A valid file is attached through `durable_archive`; source status is recomputed from accepted evidence and the immutable Invoice Card is not rewritten.

### A2 — unknown invoice is not converted into empty source state

**PASS.** Target resolution failure remains `InvoiceNotFoundError`; neither attachment nor source-status operations may synthesize a placeholder invoice/source state.

### A3 — repeated identical bytes are idempotent, not silent replacement

**PASS.** Equivalent bytes do not create a duplicate binary replica. Previously accepted provenance remains preserved; a repeated attempt may add attempt evidence but cannot silently replace accepted provenance.

### A4 — irregular HTTP handler owns no archive policy

**PASS.** The irregular handler may perform multipart transformation and accepted authentication/authorization orchestration, but source acceptance, per-file rejection, persistence and source-status policy remain in `durable_archive`.

## Adversarial ambiguity rerun

Strongest alternative considered: abort the whole mixed batch when one file has a classifiable local rejection.

Result: **PASS**. That implementation now violates the repaired public-operation and generation-note obligations.

Remaining alternatives concern internal ordering of independent file checks, transaction mechanics compatible with preserving accepted sibling outcomes, storage layout, or adapter implementation. They do not change the accepted observable semantics.

Classification: **PASS_INTERNAL_VARIATION**.

## Placeholder resistance

A trivial implementation cannot satisfy the complete slice:

- an empty batch result omits one required result for each submitted file;
- blind forwarding omits media/hash/target/provenance validation;
- unconditional rejection violates accepted valid-file behavior and partial success;
- mutating the Invoice Card violates the immutable-card boundary;
- an HTTP-only policy implementation violates the ownership boundary.

Result: **PASS**.

## Final review record

```text
flow: flow:accept_local_source_attachment
status: semantic_closed
material_alternative_found: no
placeholder_implementation_found: no
scenario_gaps: []
findings:
  - resolved: mixed-batch partial-success semantics restored at State 5 and propagated through State 6/7
```

`semantic_closed`: **yes**
