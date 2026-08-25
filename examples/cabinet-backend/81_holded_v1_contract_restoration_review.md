# Holded V1 contract restoration review

## Scope

This review covers the restoration of the already-proven Holded Invoicing V1
purchase-document transport contract. The accepted runtime evidence is recorded
in `holded_purchase_idempotency_discovery.md`; no new remote probe was used.

## Accepted boundary

- Runtime credential: `HOLDED_V1_API_KEY`; HTTP header: `key`.
- Origin: `https://api.holded.com`.
- Create/list path: `/api/invoicing/v1/documents/purchase`.
- Exact-document path: `/api/invoicing/v1/documents/purchase/{document_id}`.
- Create performs one POST. Recovery performs one GET of the V1 list and may
  then perform one exact-document GET. Transport retries and pagination loops
  are absent.
- Payload and response mappings are closed by
  `70_holded_transport_closure.json` and must be emitted without semantic edits.

## Module review result

`holded_transport` owns only `HttpxHoldedHttpClient` and is fully emitted by the
closed deterministic backend. `holded_gateway` retains orchestration and marker
recovery policy but no longer invents the HTTP wire protocol. The affected
models, publication consumer, API context, and bootstrap wiring were reviewed
against their current assembled slices. Every structural review reports zero
blocks and zero review prompts.

Result: `PASS` for deterministic modules and `PASS_INTERNAL_VARIATION` for the
behavioral modules. The change restores accepted behavior and introduces no
retry/repair fallback.

## Evidence closure review

The external facts are now bound by
`70_external_contract_evidence.json` to the SHA-256 of the sanitized successful
experiment and to canonical hashes of twelve assembled values. The bindings
cover the V1 credential slot, Unix timestamp types, origin, `key` header,
purchase endpoints, item wire fields, subtotal semantics, and response mapping.
The evidence contains no credential value and is not an instruction to rerun
the mutation experiment.

The `models`, `holded_transport`, `holded_gateway`, `holded_publication`, and
`bootstrap` slices were re-reviewed with the active external contract included.
Every structural review reports zero blocks and zero review prompts.
