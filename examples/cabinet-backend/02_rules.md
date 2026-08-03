# State 2 — Cabinet Backend rules and invariants

## Status

Working rules baseline. Decisions are added one at a time and become normative
only when explicitly accepted here.

This state defines deterministic validation, acceptance, transition, and
reconciliation semantics for the domain models in `01_models.md`. It does not
introduce speculative compatibility, placeholder policies, APIs, SQL tables, ORM
mappings, or transport payloads.

---

# A. Invoice Card contract acceptance

## Accepted decision A1 — supported Card contract

Cabinet Backend supports exactly the currently accepted Cabinet Invoice Card V1
contract.

There are no other accepted Invoice Card contract versions at this time.
Backend therefore must not implement speculative multi-version negotiation,
implicit migration, best-effort interpretation, or forward compatibility with an
unknown Card contract.

### Normative rules

1. An incoming Invoice Card is eligible for validation only when its declared
   `card_type` and `card_version` identify the currently accepted Invoice Card V1
   contract.
2. Backend validates the complete canonical Card payload with the currently
   accepted Invoice Card V1 validator or a proven contract-equivalent
   implementation.
3. A Card declaring any other version is not accepted as an Invoice Card V1 and
   receives the deterministic result `unsupported_card_version`.
4. Backend must preserve the rejected payload and safe rejection evidence when it
   arrived through a synchronization or import boundary, but it must not publish
   that payload into the accepted Card archive.
5. Backend must not rewrite, downgrade, partially interpret, or silently discard
   fields in order to make an unsupported Card appear compatible.
6. Support for any future Card version requires a separate accepted specification
   change that defines its validator, compatibility boundary, migration behavior,
   and relationship to stored V1 revisions.

### Formal invariants

For every `StoredInvoiceCardRevision` in the accepted archive:

```text
revision.card_type = accepted_invoice_card_type
revision.card_version = accepted_invoice_card_v1_version
```

For every `InvoiceCardValidationRecord` with result `valid` or
`valid_with_warnings`:

```text
validation.validator_contract = accepted_invoice_card_v1_contract
validation.validator_version = accepted_invoice_card_v1_validator_version
```

An unsupported declared Card version may produce import rejection or quarantine
evidence, but it cannot create or replace:

- `StoredInvoiceCard`;
- `StoredInvoiceCardRevision`;
- `current_content_hash`;
- an accepted `InvoiceWorkingReplica` entry.

### Required tests

1. A valid Invoice Card V1 is evaluated by the accepted V1 validator.
2. A payload declaring an unknown Card version returns
   `unsupported_card_version`.
3. An unknown version does not create an accepted Card revision.
4. An unknown version is not silently interpreted as V1 even when its fields look
   similar to V1.
5. Repeating the same unsupported payload preserves deterministic rejection
   semantics and does not create duplicate accepted records.

### Consequence

Version negotiation is not a runtime product feature in the current baseline.
The supported contract changes only through an explicit specification and
implementation update.

---

# B. Decisions still open

The next decision is whether `draft` Invoice Cards may enter the durable local
archive and, if so, which operations must remain restricted to `confirmed`
revisions.
