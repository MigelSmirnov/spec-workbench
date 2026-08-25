# Cabinet Backend — Factory runtime execution evidence

Date recorded: 2026-08-25

Evidence class: **operator-attested external runtime execution**

Project: `cabinet-backend` (local Cabinet Backend application)

## Observed execution

The deployment operator reports that the mature `cabinet-backend` specification was taken through the Factory path and E2E checks, then an experimental invoice was processed through Cabinet Backend and successfully appeared in Holded.

This establishes one observed end-to-end external-effect canary across the generated/local runtime boundary:

```text
Cabinet Backend
  -> generated Factory implementation
  -> PostgreSQL / persistence and effect controls
  -> Holded publication gateway
  -> external Holded document creation
```

For the Holded publication path, the accepted semantic oracle remains `71_flow_5_semantic_review.md`: publication success is not defined by the POST response alone; the flow requires the accepted read/reconciliation and business-verification semantics.

## Evidence boundary

This record deliberately does **not** invent evidence that was not captured in the Workbench repository. No invoice identifier, Holded document identifier, runtime log, database row, timestamp of the external mutation, or byte-level Factory handoff hash is asserted here.

Accordingly, the evidence supports these claims only:

- the local `cabinet-backend` Factory path has been exercised successfully by the operator;
- its E2E checks were reported passing in that execution;
- at least one experimental invoice traversed the runtime and was loaded into Holded;
- the already-generated mechanical runtime patterns used by that path are therefore an E2E-tested precedent for subsequent Workbench repair.

It does **not** by itself prove reproducibility of a particular build or replace machine-captured CI/runtime provenance. A later machine-captured execution may strengthen this record without changing product semantics.

## Golden-reference use

For `cabinet-web-backend`, this evidence permits `cabinet-backend` to be used as a golden reference for **mechanical implementation/specification patterns that are shared by the two projects**, including supported `persistence_backend/v3` / `postgres_sync_v1` shapes, transaction ownership, repository query forms, codec/binding shapes, durable effect evidence, and explicit composition boundaries.

It does not transfer local-backend domain ownership to the server application and does not authorize copying local-only models, PresuPro/Holded responsibilities, archive ownership, or business semantics into `cabinet-web-backend`.
