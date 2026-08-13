# State 3 bounded repair — Flow 5 Holded publication orchestration

## Status

Accepted bounded repair discovered by Stage 7.1 for `flow:publish_invoice_to_holded`.

This introduces no new product behavior. It makes the already accepted A51/A52 sequence generation-obligatory.

## `module:holded_publication` orchestration responsibility

In addition to its existing business-eligibility and logical-publication ownership, `module:holded_publication` owns sequencing one logical publication attempt across the existing `module:holded_gateway` boundary.

For a clear technical create result containing a canonical Holded `documentId`:

1. the create result is technical evidence only and must not settle logical publication success;
2. `module:holded_publication` must request read-only evidence for that exact document through the existing Holded gateway read operation;
3. it must perform the complete accepted A51 business verification against the exact immutable Invoice Card revision and stored attempt payload;
4. only a complete verified match may settle the logical publication as successful;
5. lookup/GET failure or business mismatch remains non-success/reconciliation-required evidence and must not trigger another automatic POST.

For an ambiguous create result, the existing A52 recovery sequence remains unchanged: no second automatic POST, read-only exact-marker recovery, exact candidate count classification, GET of the unique candidate when one exists, and complete A51 verification before settlement.

## Boundary preservation

`module:holded_gateway` remains the sole owner of Holded credentials, HTTP transport, raw remote responses, and read-only list/GET mechanics.

`module:holded_publication` remains the sole owner of Cabinet eligibility, exact revision binding, logical duplicate prevention, A51 business-field verification, and logical settlement.

A returned `documentId`, HTTP success, marker match, or numeric Holded status is never by itself Cabinet publication success.
