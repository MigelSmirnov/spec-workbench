# Cabinet Backend — Stage 7.1 Flow 5 semantic review

Flow: `flow:publish_invoice_to_holded`

Status: **semantic_closed**

## Reconstructed accepted behavior

State 2 A51/A52 and State 4 require:

```text
exact eligible immutable invoice revision
  -> persist logical publication + attempt before mutation
  -> at most one automatic Holded POST
     -> clear documentId: GET exact document + complete A51 verification
        -> verified match only -> publication success
        -> mismatch/read failure -> reconciliation-required/non-success
     -> ambiguous create: no second POST
        -> bounded read-only marker lookup
        -> exactly one candidate -> GET + complete A51 verification
        -> zero/multiple/mismatch -> unresolved/conflict, never success
```

The attempt marker is correlation evidence only. Holded numeric status is stored raw and has no accepted business meaning. Holded recalculation never rewrites Invoice Card facts.

## Original ambiguity

Before repair, compressed State 5/7 semantics allowed two materially different implementations:

- A: a clear create response containing `documentId` was followed by exact-document GET and complete A51 verification before logical success;
- B: the POST response itself settled logical publication success.

That difference is material because Holded may create a document whose returned representation disagrees in gross total, line order/count, tax, or another required business field.

## Repair applied

The bounded repair chain is:

- `30_modules_flow5_semantic_repair.md` — `module:holded_publication` explicitly owns sequencing clear create success through the existing read-only gateway boundary and business verification;
- `50_public_apis_flow5_semantic_repair.md` — `request_holded_publication` must obtain exact-document read evidence and pass complete A51 verification before success;
- `80_notes_flow5_semantic_repair.md` — generated code is forbidden from treating HTTP/create success, `documentId`, marker match, or raw numeric Holded status as Cabinet publication success.

No new gateway API, result type, or business rule was introduced.

## Scenario rerun

### H1 — eligible exact revision + clear create result

**PASS.** The one permitted create result is technical evidence only. A returned canonical `documentId` must be read back through the existing Holded gateway read operation. Logical success requires complete A51 verification of supplier identity/name, supplier invoice number, date, currency, line count/order/names/quantities/tax rates, and gross total within accepted currency precision.

A read failure or business mismatch remains non-success/reconciliation-required and does not authorize another automatic POST.

### H2 — ambiguous create outcome

**PASS.** One logical attempt permits at most one automatic POST. Ambiguity enters read-only marker recovery. No zero-match, timeout, process interruption, or response-loss branch authorizes an automatic retry.

### H3 — recovered candidate classification

**PASS.** Zero exact marker matches remain outcome-unknown; multiple matches remain duplicate conflict; one mismatched candidate remains reconciliation-required; exactly one candidate may settle only after GET and complete A51 verification.

### H4 — external evidence does not rewrite Cabinet truth

**PASS.** Holded intermediate rounding and raw numeric status remain external evidence. Invoice Card totals/content are immutable. Intermediate monetary differences are tolerated only under A51 when source line semantics are preserved and final gross matches within accepted currency precision.

## Adversarial ambiguity rerun

The former Interpretation B — “POST returned `documentId`, therefore publication succeeded” — now directly violates State 3/5/7 obligations.

Other implementation choices such as HTTP client library, persistence layout, internal helper decomposition, or polling timing within the bounded recovery policy do not change observable business semantics.

Result: **PASS_INTERNAL_VARIATION**.

## Placeholder resistance rerun

A semantic skeleton that only calls `create_holded_purchase` cannot satisfy the successful clear-response branch. Likewise, marker lookup without GET/business verification cannot satisfy recovered success.

Result: **PASS**.

## Flow 5 gate

`semantic_closed`: **yes**

Flow 5 may now be materialized as a runtime semantic acceptance oracle without inventing new product behavior.
