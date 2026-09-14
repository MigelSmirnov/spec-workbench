# Live Cabinet_web product evidence — 2026-09-05, HEAD `c897897`

Observed: 2026-09-05. Source of truth: live repository `MigelSmirnov/Cabinet_web`,
`main` at `c897897` ("feat: add project stage registry and chat navigation"),
local clone `~/jestor_VBC/Cabinet_web` fast-forwarded from `8a19f8c` (322
commits, 231 files, +30 679 / −619). This document records what the product
is at that commit. It is the starting point of the migration into Cabinet
Flow and carries no architectural authority over Cabinet Flow; the accepted
decision that fixes the boundary is recorded in `00_product.md` (State 0).

## 1. Invoice Card contract: `schemas/invoice-card-v1.schema.json`

`card_version: 1`. Every top-level field is required:
`card_type, card_version, id, status, invoice_number, issue_date, service_date,
due_date, currency, supplier, buyer, object, lines, totals, payment, source,
provenance`.

Sub-shapes (`$defs`, every listed field required):

```text
party        name, tax_id, address
object       card_id, label                              (objectAssignment)
line         line_id, kind, description_original, description_normalized,
             supplier_sku, matched_material_id, quantity, unit, unit_price_net,
             discount_percent, discount_amount, net_amount, tax_rate,
             tax_amount, gross_amount
totals       net, discount, tax, gross, withholding, payable
payment      status, transactions[]
transaction  payment_id, method, paid_at, currency, tendered_amount,
             applied_amount, change_amount, reference, evidence
source       source_id, kind, file_ref, file_status, note
provenance   created_at, confirmed_at, created_by
```

Monetary values are printed decimals (cents), `tax_rate` is percent-shaped
(see `LIVE_INVOICE_DATA_EVIDENCE_20260828.md`). Schema history: `5bc08b7`
(Version 1), `4a7b953` (object assignment), `b55162f` (source id required);
unchanged since 2026-08-21.

This shape is byte-for-byte the `InvoiceCardV1` the accepted `cabinet_backend`
specification already carries. The reduced Invoice model of this case
(`InvoiceParty` with email/phone, three-field `InvoiceTotals`,
`transactions_json`, `object_context`, `created_by`/`confirmed_by` actors) is
not the product contract and has no counterpart in the live repository.

`source.file_ref` is an opaque reference (`null` on every live card);
`source.file_status` is one of the live values `not_stored` (11 cards) and
`pending` (1 card). No live card carries stored bytes through the product.

## 2. Full line capture is a product invariant

`docs/02-tools/INVOICE_WORKFLOW.md` and `INVOICE_TOOLS_MODEL.md` (design rule
11): every commercial source row — item, labor, equipment, transport,
service, fee — is one Invoice Line. Summary rows (subtotal, tax, total,
payment, tendered, change) are not lines. A synthetic aggregate line
(`materials`, `purchase`, `invoice total`) that stands in for source rows is
forbidden; totals and arithmetic checks never replace lines.

`invoice_confirm` inputs: `invoice_id, expected_content_hash, confirmed_at,
source_line_count, line_capture_complete, confirmation_note?,
idempotency_key`. Before writing it reruns validation, requires
`line_capture_complete = true`, a positive `source_line_count` equal to
`len(card.lines)`, reruns duplicate detection, and rejects every validation
and line-capture error; line-capture errors are hard errors that warning
acknowledgement cannot bypass. Error codes: `invoice_line_capture_required`,
`invoice_line_capture_mismatch`.

## 3. `line-capture.json`: separate evidence bound to the exact card hash

Sidecar per card directory (`data/cards/<invoice-id>/line-capture.json`),
present on 8 of 12 confirmed cards, `line_capture_complete = true` on all 8.
Observed shape:

```text
version, invoice_id, source_id, source_line_count, captured_line_count,
line_capture_complete, card_content_hash ("sha256:…"), state ("confirmed"),
recorded_at, operation ("confirm" | "revise_lines"),
previous_card_content_hash, revision_reason, revised_at
```

It binds the exact source (`source_id`), the source row count, the captured
row count, the exact card revision (`card_content_hash`) and the completeness
state. It is verification evidence, not part of the Invoice Card
(`INVOICE_REVISION_WORKFLOW.md`, "History").

## 4. `invoice_revise_lines`

Accepted extension for repairing confirmed lines from the original source
(`docs/02-tools/INVOICE_REVISION_WORKFLOW.md`). Inputs: `invoice_id, lines,
source_line_count, line_capture_complete, expected_content_hash, reason,
idempotency_key, revised_at?, confirm_warnings?`. Rules: only a confirmed
card; `line_capture_complete = true`; `source_line_count = len(lines)`;
non-empty reason; current content hash; replaces only `lines[]`; keeps
identity and `provenance.confirmed_at`; reruns validation; rejects errors;
explicit warning acknowledgement; writes through the recoverable mutation
service; reports previous and resulting hashes; never derives lines from
totals. Four live cards were revised this way (`operation = revise_lines`).

## 5. GitHub request bridge

`architecture/capabilities.yaml` → `request_bridge` (status accepted):
requests in `ops/capabilities/requests/<request-id>.json`, results in
`ops/capabilities/results/`, runner `tools/capability_request_runner.py`,
workflow `.github/workflows/invoice-cli-request.yml` (push to `main` on
`ops/invoice-cli/requests/*.json` or `ops/capabilities/requests/*.json`,
`contents: write`, single concurrency group). Allowlisted operations:
`route_project_invoice, update_stage_live_report, record_client_payment,
allocate_client_payment, record_organization_expenses,
record_manual_organization_expense, review_project_funds,
build_stage_action_list`. Requests carry canonical identities and structured
values only — no commands, module names, paths or capability composition.
Live: 8 capability requests with 8 results, 17 invoice-cli requests.

This bridge exists because the assistant can write GitHub files but cannot
run the repository shell. It cannot attach binary source bytes (live card
note: "current GitHub write transport cannot attach binary source bytes").

## 6. Online surfaces

`tools/mcp_server.py` (4 read tools: `search_providers, list_projects,
get_project_summary, search_invoices`) and `tools/mcp_server_extended.py`
(16 tools: the four above plus `list_project_stages, get_project_context,
get_stage_context, get_invoice, validate_stored_invoice,
find_invoice_duplicates, prepare_invoice_draft, review_project_funds,
reconcile_stage_materials_tool, get_stage_action_list,
get_stage_material_kit, get_estimator_evidence`). Writes reach the
repository only through GitHub (direct file writes and the request bridge).

## 7. Capability families and live data

Repository data (`data/`): 12 invoice cards (all confirmed, 120 lines), 3
provider, 1 client, 1 project, 2 extra-work cards; 11 project–invoice links;
1 invoice-processing workflow state. The project card
(`project-uliana-floor-20260815`) carries `stages/` (stage-1..3 with
`index.v2.json`, `changes.json`, `discovery/`, `materials/`, `notes/`,
`organization.json`), `funds/ledger.json`, `reconciliation/` (stage
reconciliation and settlement), `reports/` (stage live reports),
`estimator-packages/` (scope manifests, evidence boxes, `AGENT_TASK.md`) and
`documents/source-photos/` (nine Abdul/SUELPA photographs kept as evidence in
the project, moved there on 2026-08-27).

Schemas beyond the invoice: `estimate-v1`, `extra-work-card-v1`,
`project-fund-ledger-v1`, `project-invoice-link-v1`,
`project-invoice-workflow-v1`, `project-settlement-ledger-v1`.

Capabilities (`capabilities.yaml`, status `platform_candidate` unless noted):
`resolve_project_material_actuals, build_estimator_evidence_box,
normalize_and_reconcile_materials, resolve_stage_material_kit,
build_stage_action_list, reconcile_stage_materials,
aggregate_reconciled_materials (optional), build_estimator_document,
build_estimator_handoff_package, build_stage_live_report,
record_client_payment, get_project_fund_ledger, record_project_fund_event,
calculate_project_fund_control, calculate_partner_settlement,
get_settlement_ledger, record_settlement_event`; compositions
`prepare_estimator_document, prepare_aggregated_estimator_document,
update_stage_live_report, review_project_funds, review_partner_settlement`.
Design docs: `STAGE_ACTION_LIST`, `STAGE_LIVE_REPORT`, `STAGE_MATERIAL_KITS`,
`STAGE_RECONCILIATION`, `PROJECT_FUND_CONTROL`, `PARTNER_SETTLEMENT`,
`ESTIMATOR_HANDOFF_PACKAGE`, `PROJECT_ANALYTICS_MODEL`,
`architecture/PROJECT_STAGE_CONTRACT.yaml`.

## 8. What this evidence changes in this case

- The Invoice contract of the plugin is `InvoiceCardV1` as above, carried
  without loss; the reduced model is retired (State 1).
- Confirmation is gated by line-capture evidence bound to the exact card
  hash; revision of confirmed lines is a separate explicit operation
  (State 2 rule to be recorded).
- The request bridge is a temporary compatibility adapter for capabilities
  that have not migrated; it is not extended and its semantics are not moved
  into the plugin.
- Source bytes do not travel through GitHub and the browser upload handoff
  is not part of the first version; the first-version path for photographs
  is the Syncthing Inbox owned by Cabinet Flow (State 0).
