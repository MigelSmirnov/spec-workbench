# Stage 8.1 review — registry_context

## Result

PASS — PostgreSQL runtime boundary repaired and re-reviewed.

## Original ambiguity

The accepted Registry projection, WorkObject lifecycle, and immutable assignment
validation were persistent, but the assembled module had no repository,
transaction, concrete implementation, or bootstrap composition boundary.

## Repair

The final assembly declares:

- RegistryContextRepository as a narrow typed persistence port;
- PostgresRegistryContextRepository as the concrete local implementation;
- RegistryContextService as the single cohesive dependency for callers;
- one transaction and catalogue lock per complete Registry observation merge;
- preservation of Cabinet-owned fields and existing WorkObjects absent from a
  later observation;
- immutable assignment-validation persistence;
- exact accepted Card evidence resolved through DurableArchiveService;
- reuse of the deployment PostgreSQL URL without sharing archive repository
  methods or domain transaction ownership;
- explicit app-state and bootstrap composition with fail-closed construction.

## Adversarial findings repaired

The first assembled repair used replacement semantics, which contradicted the
accepted flow requirement to preserve existing objects absent from a later
Registry response. It also attempted assignment validation from identifiers
without a declared source for immutable Card evidence.

The final design uses merge_work_objects keyed by stable project_id and injects
the already closed DurableArchiveService into RegistryContextService.

## Verification

GitHub Actions run 31880447002 executed the canonical module review on commit
4759e938af7d18985b0e14541c16b2533d14d72b.

- contracts: 26;
- assembled notes: 47;
- accepted decisions: 6;
- flows: 2;
- blocks: 0;
- review prompts: 0;
- slice SHA-256:
  913b957e20440aefa440b0d6b0a8c1f0d34eb6456196bf335250d7d34ca178f2.

The module cannot replace a complete catalogue, fabricate missing context, infer
deletion from absence, validate an assignment without exact Card evidence, or
open ad-hoc persistence without violating the final packet.
