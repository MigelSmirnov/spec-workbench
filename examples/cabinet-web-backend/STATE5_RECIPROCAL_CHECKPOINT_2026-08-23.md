# Cabinet Backend reciprocal checkpoint — after State 5

## Evidence identity

- Factory project: `cabinet_backend`
- accepted base-spec SHA-256:
  `e3f8e002ef67bc6b5697ac1624f352d2cc570dc80638cbc3e6c7f9b8b061568b`
- normalized SHA-256:
  `56c206cdf159cd1f7327e53fbe70d4a36f8bf560785a0b8348fb7bf753c7b181`
- terminal verification run: `20260823_091104`
- verification verdict: `PASS`
- terminal OTK covers accepted spec: `true`
- OTK audit verdict: `WARN`

Factory MCP `factory_state` and bounded `spec_scope_slice` were used read-only.
The `cabinet_backend` worktree and canonical specification were not modified.

## Verified external port surface

The accepted local Backend defines the following external transport port:

```text
VpsSynchronizationTransport.transfer_invoice
  (selection: SynchronizationWorkSelection, node: CabinetNodeIdentity)
  -> VpsInvoiceTransferPackage

VpsSynchronizationTransport.reconcile_transfer
  (synchronization_id: str)
  -> VpsTransferReconciliationEvidence

VpsSynchronizationTransport.publish_catalogue
  (delivery: RegistryCatalogueDelivery)
  -> VpsCatalogueAcknowledgement

VpsSynchronizationTransport.observe_connection
  () -> VpsConnectionObservation
```

The accepted local runtime no longer contains `get_working_set_membership`.
Cabinet Web therefore remains the owner of M27 membership and release policy;
the local Backend supplies receipt and durable-acceptance evidence only.

## Verified reciprocal models

The accepted local spec supplies typed forms for:

- `SynchronizationWorkSelection`;
- `VpsInvoiceTransferPackage`;
- `InvoiceTransferManifest`;
- `InvoiceTransferReceipt`;
- `VpsTransferReconciliationEvidence`;
- `DurableAcceptanceVerification`;
- `RegistryCatalogueDelivery`;
- `VpsCatalogueAcknowledgement`;
- `VpsConnectionObservation`;
- `CardObjectAssignmentObservation`.

The assignment observation contains exact Card revision, explicit optional
`project_id`, object label, catalogue identity, Registry snapshot identity,
decision context, and observation time. Neither sync nor the local Backend may
infer `project_id` from an opaque Card identifier or label.

## Accepted reciprocal resolution package

All eight differences were accepted together on 2026-08-23 and are normative
inputs to State 6:

1. Cabinet Web adds discovery before the existing local selection: a bounded
   M27 page returns only Invoice ID, exact Card revision/content hash,
   `manifest_id`/hash, ordered source IDs/hashes/sizes/media types/safe names,
   and an opaque cursor. Local pull selects the returned `manifest_id`.
2. The reciprocal request timeout is 120 seconds. Shorter budgets may be used
   for compatibility/discovery/status reads. Timeout after issuance is
   `outcome_unknown`, followed only by read-only reconciliation; the local
   30-second setting must be split or revised before reciprocal acceptance.
3. JSON/protocol metadata is limited to 8 MiB, one source to 30 MiB, and the
   logical Invoice package to 40 MiB. Binary parts are streamed and never
   base64-expanded inside JSON.
4. First release requires exactly one Card revision per M21 manifest:
   `len(card_revisions) = 1`. Any Card revision or source-membership change
   creates a new immutable manifest.
5. Registry delivery uses `cabinet-web-sync-v1`, catalogue ID/hash/count,
   canonical `project_id` snapshot order, endpoints, idempotency, and creation
   time. The hash is SHA-256 of canonical UTF-8 JSON with lexicographically
   sorted object keys.
6. VPS release requires accepted/already-accepted M23 for the exact manifest,
   exact Card hash and every source hash, plus accepted local
   `DurableAcceptanceVerification` with non-empty `evidence_id` and exact
   equality of required, verified, and manifest source IDs.
7. `SourceBinaryReplica.storage_reference` is created only by the local consumer
   after private temporary staging and hash verification. It is never a wire
   field; no VPS path or storage credential crosses the boundary.
8. Cabinet Web's confirmed Invoice capture/domain path produces M29
   `CardObjectAssignmentObservation` for the exact revision. Sync transports it
   and local acceptance persists it unchanged. Only explicit `project_id` plus
   exact catalogue/snapshot provenance is assigned; otherwise the state is
   `label_only`, `unassigned`, or `needs_review`, with no implicit mapping.

## Gate consequence

State 5 public-operation ownership remains closed using the verified external
port as evidence. The eight reciprocal answers no longer block exact State 6
signatures or Router IR; the normal Workbench pre-contract data-closure gate
(`60_data_closure.json`) must still close first. Final external-contract evidence
also must be content-addressed before its later gate closes; this checkpoint is
not a substitute for either required artifact.
