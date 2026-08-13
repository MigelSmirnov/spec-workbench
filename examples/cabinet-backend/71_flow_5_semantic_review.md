# Cabinet Backend — Stage 7.1 Flow 5 semantic review

Flow: `flow:publish_invoice_to_holded`

Status: **AMBIGUITY — repair required**

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

## Adversarial ambiguity

### Interpretation A — verified publication

A clear create response containing `documentId` is only technical attempt evidence. `request_holded_publication` obtains read-only evidence for that exact document through the Holded gateway, performs the complete A51 business verification, and marks the logical publication successful only when verification passes.

### Interpretation B — POST-success publication

A successful technical create response containing `documentId` immediately settles `HoldedPublication` as successful. The implementation stores the identifier and may omit the GET/read-back verification entirely.

Interpretation B can satisfy the current compressed State 5/7 wording about a "verified-success requirement" by treating the returned create response as sufficient verification evidence; no current generated-callable obligation explicitly sequences clear create success into `lookup_holded_purchase`/GET verification.

## Material difference

A remote document can be created with a wrong gross total, changed line order/count, wrong tax, or other business mismatch. Interpretation A returns non-success/reconciliation-required. Interpretation B reports publication success. This is materially different observable accounting behavior.

## Placeholder resistance

Status: **PLACEHOLDER_RISK** for the successful-create branch.

A gateway implementation that POSTs once and returns the technical result is not itself a placeholder. The semantic skeleton is in `request_holded_publication`: it may accept that technical result as logical success without executing the accepted A51 verification sequence.

## Scenario review before repair

- H1 exact eligible revision + clear create response: **not fully derivable** because GET verification is not generation-obligatory.
- H2 ambiguous create outcome: single-POST/no-retry rule is explicit; recovery verification is substantially constrained.
- H3 zero/multiple/mismatched recovered candidates: explicit non-success/reconciliation behavior is constrained.
- H4 raw numeric status and Holded rounding never rewrite Card truth: constrained by upstream rules, but should remain explicit in generation notes.

## Finding

```text
flow: flow:publish_invoice_to_holded
status: AMBIGUITY
material_alternative_found: yes
placeholder_implementation_found: yes
findings:
  - owner: structure
    scope: State 3/5 orchestration ownership propagated to State 7
    interpretation_A: clear POST success must be followed by exact-document GET and complete A51 verification before logical success
    interpretation_B: returned documentId from POST is enough to settle logical publication
    required_resolution: make holded_publication own mandatory clear-response read-back sequencing through the existing read-only holded_gateway operation, while gateway remains owner of credentials/transport and publication remains owner of business verification/settlement
```

## Earliest repair owner

State 2 and State 4 are already explicit. The loss occurs in State 3/5 orchestration compression. Repair module/API semantics and propagate to State 7 Notes. No new result type or gateway operation is required.

`semantic_closed`: **no**, pending repair and rerun.
