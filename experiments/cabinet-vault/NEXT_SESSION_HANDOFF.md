# Cabinet Vault — next session handoff

## Direction

`Cabinet_web` and the Cabinet local box are autonomous state owners connected by a versioned synchronization protocol. Web owns confirmed Card facts and Git history; the local box owns durable replicas, protected source bytes, local effects, recovery and audit.

## Functional interoperability milestone — PASS

The first real F260001 execution succeeded:

```text
Cabinet_web main: d3fac8e5d2b85c12904cba24060717b84e2757c2
invoice_id: invoice-f260001
source_id: source-f260001
Card hash: sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf
revision acceptance: accepted
source attachment: attached
parser media: application/pdf
local PDF SHA-256: sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66
Card unchanged: true
durable acceptance audit: present
durable attachment audit: present
```

Functional evidence:

```text
experiments/cabinet-vault/F260001_REAL_DATA_CANARY_PASS_EVIDENCE_2026-08-21.md
```

## Assurance review — PARTIAL

Do not equate the successful operation with proof of every guarantee.

Authoritative review:

```text
experiments/cabinet-vault/F260001_REAL_RUN_ASSURANCE_REVIEW_2026-08-21.md
experiments/cabinet-vault/cabinet_web_real_data_canary_readiness_v1.yaml
experiments/cabinet-vault/cabinet_web_interop_audit_v0.yaml
```

Current classification:

```text
functional real-data execution                 PASS
pinned bridge CI / negative grant probes       PASS
all guarantees proven by exact private run     false
exact-run assurance closure                    PARTIAL
```

The important open properties are:

- the private real runner imported `TrustedLocalCapabilityBridge` and invoked it in-process; it did not exercise the declared CLI/stdio isolation boundary;
- the runner used private bridge fields for read-only verification, so process/public-surface confinement was not demonstrated;
- PDF bytes are read before bridge invocation and parser identification occurs in the source adapter before `AuthorityKernel.invoke()`; therefore authorization-before-any-source-byte-access is not satisfied by the current path;
- durable effect audit rows existed, but the safe evidence preserved only booleans rather than bounded event IDs/digests plus exact decision fields;
- exact grants and wrong-scope/wrong-credential denial are strongly proven by pinned code and BRIDGE CI negative probes, but the successful private run itself did not execute those negative cases;
- `InvoiceRefSet` was not used by the F260001 path. Its opacity remains separate `CabinetGraphHost` test evidence and must not be attributed to the real invoice canary.

## Next milestone — assurance run

Before Client/Project ownership cleanup or bridge generalization, execute one assurance-oriented run that:

1. runs the caller and trusted bridge as separate processes over the real local stdio/IPC surface;
2. keeps credentials/grants host-owned and outside the caller process/request environment;
3. if authorization-before-source-access is intended, moves source-byte acquisition/parser identification behind the authority decision or authorizes an opaque source handle before host reading;
4. executes negative wrong-credential-class and wrong-invoice-scope attempts and proves denial before protected local-box state access/effects;
5. emits bounded non-secret real-run audit attestations sufficient to verify principal/capability/scope/effects/interaction/result for the exact run.

Only after this should `exact_real_run_assurance_gate` move from `partial` to `pass`.

## Product-data cleanup remains next after assurance

The dedicated `invoice-f260001` Invoice Card is canonical. Client/Project Cards still contain legacy embedded invoice/source projections. Define explicit relationship/derived-projection semantics before deleting them, but do not use that migration to obscure the open assurance work.

## Full-suite note

A broader local run reported `605 passed, 6 failed`; the six reported stale State 5/6/assembly count assertions remain separate technical debt.
