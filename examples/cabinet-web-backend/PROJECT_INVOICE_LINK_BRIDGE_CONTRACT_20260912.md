# Temporary Project Invoice Link bridge contract — 2026-09-12

## Authority and scope

D0-013 in `00_product.md` records the owner's explicit authorization for one
additional legacy bridge operation, `link_project_invoice`. D0-008 continues
to require one canonical writer per capability. The operation belongs to the
existing Cabinet_web GitHub writer, not the generated integration backend.
This document is the implementation acceptance contract for that exception;
it is not evidence of a deployed handler or a successful live link receipt.

## Evidence and classification

Inspected legacy checkout: `feat/custom-gpt-incoming-invoices`, commit
`4e1b8cd`. Accepted Factory spec at inspection:
`0651f9ce4b8e7b335238a4dc6b581fdec7000a39d28b46997653b043561a40cf`.

| Finding | Evidence | Classification and owning decision |
| --- | --- | --- |
| `PROJECT_LINK_HANDLER_MISSING` | `tools/capability_request_runner.py`: supported operations omit linking; `tools/invoice_workflow_route.py`: confirmed Invoice without a link routes to `link_project_invoice` | Irregular application behavior, explicitly authorized by D0-013 |
| `PROJECT_LINK_TRANSPORT_UNAVAILABLE` | `tools/actions_intake.py`: confirmed status advertises unavailable project step; `tools/actions_git_writer.py`: operation and read-path allowlists exclude project linking | Compatibility transport implementation under D0-013 |
| `PROJECT_LINK_COMMIT_PATH_MISSING` | `.github/workflows/invoice-cli-request.yml`: commit step stages Cards and workflows but omits `data/links` | Required writer durability change under D0-013 |
| `PROJECT_LINK_STAGE_ALREADY_MODELED` | `schemas/project-invoice-link-v1.schema.json`: stage_id, project_id, invoice_id; `architecture/PROJECT_STAGE_CONTRACT.yaml`: canonical stage registry and alias resolution | Existing product form reused under D0-008; no new integration-owned stage model |
| `PROJECT_LINK_TARGET_OWNERSHIP` | Workbench D0-007/D0-008 and M13 versus legacy schema | Placement: canonical legacy artifacts remain authoritative until capability migration |

Owner-reported live result: Invoice `036-0009-477939` confirmed, paid,
EUR 63.08, three source rows, original stored, supplier rounding warning.
The report motivates this change; it is not a fresh read of canonical state
and must not be used as the expected revision for a later mutation.

## Request and validation boundary

The request must name the canonical Invoice, Project and explicit stage,
include an idempotency key, and bind the exact reviewed Invoice content hash
and Project/stage context. The adapter obtains current context from canonical
reads and preserves it in the immutable request; the runner verifies it again
at execution time. It never substitutes the then-current stage if the reviewed
stage context has changed.

Only confirmed Invoices qualify. Project existence, stage membership and
canonical stage identity are verified against the existing registry. Legacy
stage aliases resolve through that registry; user labels and Invoice Object
Card fields are not stage identifiers. Invalid identities, stale context,
missing evidence and conflicts produce structured refusal without link changes.
Caller-supplied filesystem paths, executable commands and operation dispatch
outside the allowlist are not accepted.

## Canonical effect

Persist one artifact satisfying `project-invoice-link-v1.schema.json` under
`data/links/project-invoices/`. Preserve existing link identities. An identical
confirmed assignment is a no-op replay, including when requested under a new
transport request ID. A different active assignment or incompatible existing
artifact produces a conflict for review, never an overwrite. Archived history
is retained and is not silently reactivated.

Each recorded line reference belongs to the pinned Invoice. Attribution to a
stage and matching a line to an estimate are separate decisions: absent matches
remain unresolved, and no source row is merged or fabricated. Existing line
matches are not replaced by this operation.

The durable receipt records the operation, request identity, link identity,
Project, canonical stage, Invoice and observed revision/context, plus whether
it created the link or replayed the accepted assignment. Final success requires
that link and receipt are published by the same canonical writer commit.
Retries after a lost submission response reconcile that same request. Retries
after a lost receipt reconcile the accepted artifact; they do not create another
logical link. Failed publication must not be reported as committed success.

The GitHub workflow stages link artifacts as well as receipts. The transport
extends only the paths and operation necessary for this capability. Invoice and
Project Cards, capture proof, original files and historical receipts stay intact.

## Actions workflow

After Invoice confirmation, report a callable project-link step with the exact
Invoice and Project context and an explicit stage argument. If the stage has
not been selected, identify the missing argument and expose canonical stage
choices. Do not advertise `available: true` before the canonical runner supports
the operation. A submitted request returns polling guidance, not saved status.
A successful final receipt advances routing beyond `link_project_invoice`;
unresolved estimate matches remain a separate review step.

## Required verification before enabling the Action

- A confirmed Invoice links to an existing explicit stage; all artifacts satisfy
  the existing schema and the original Cards and source evidence remain equal.
- Drafts, invalid identities, nonexistent stages, stale Invoice/context and
  conflicting assignments are rejected without link mutations.
- Repeating the same request, losing a transport response, and submitting the
  same assignment under another key create only one logical link.
- A conflicting payload under the same idempotency key is rejected.
- Existing confirmed links and their line matches are replayed without rewriting;
  archived or differently assigned links are not silently overwritten.
- Link publication and final receipt survive the real writer commit path; pending
  or failed publication cannot be reported as a saved assignment.
- The generated public Action schema, endpoint DTO, transport allowlist and
  runner accept the same arguments. Confirmation-to-link-to-receipt routing is
  exercised end to end on disposable data, including unresolved material matches.

Implementation validation must attach actual test results to the implementation
change. This document does not substitute for executed tests. Only a subsequent
canonical receipt can establish that the live Uliana Invoice has been linked.
