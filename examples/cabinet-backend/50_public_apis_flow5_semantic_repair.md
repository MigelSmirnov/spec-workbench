# State 5 bounded repair — Flow 5 Holded publication semantics

## Status

Accepted repair for `public_op:holded_publication.request_holded_publication` discovered by Stage 7.1.

The existing operation and signatures remain unchanged.

## Refined observable semantics

For one eligible exact Invoice Card revision, `request_holded_publication` owns the complete logical publication sequence across the existing Holded gateway operations.

### Clear create result

A successful technical `create_holded_purchase` result containing `documentId` is not logical publication success by itself.

The operation must:

1. preserve the exact publication attempt and revision binding created before mutation;
2. obtain read-only evidence for the exact returned `documentId` through the existing Holded gateway read operation;
3. verify the complete accepted A51 business field set, including supplier identity/name, supplier invoice number, document date, currency, line count/order/names/quantities/tax rates, and gross total within accepted currency precision;
4. preserve source Invoice Card totals separately from Holded recalculated totals;
5. settle logical success only when that exact-document verification passes.

A GET/read failure, gross-total mismatch, line mismatch, or other failed A51 verification produces non-success/reconciliation-required publication state and must not trigger another automatic POST.

### Ambiguous create result

The existing A52 rule remains authoritative: the same logical attempt enters reconciliation, performs no second automatic POST, uses read-only exact-marker recovery, and may settle only after exactly one recovered candidate passes complete A51 verification.

Zero matches remain outcome-unknown; multiple exact matches remain duplicate conflict; a unique mismatched candidate remains reconciliation-required.

## Enforces

- exactly one automatic create mutation per logical attempt;
- exact immutable Invoice Card revision binding;
- technical create success is not business publication success;
- marker match is not business publication success;
- unknown numeric Holded status is never interpreted as accounting state;
- Holded recalculation evidence never rewrites the immutable Invoice Card.
