# F260001 real Cabinet_web → local box canary evidence — 2026-08-21

## Evidence scope correction

**Functional execution: PASS. Assurance closure: PARTIAL.**

This record proves that the exact real F260001 Card was accepted, the real PDF was attached, the Card remained unchanged, and durable acceptance/attachment audit rows existed. It does **not** by itself prove every authority/transport property of the exact private run.

The property-by-property review is authoritative for assurance claims:

```text
experiments/cabinet-vault/F260001_REAL_RUN_ASSURANCE_REVIEW_2026-08-21.md
```

In particular, the real runner invoked the bridge in-process rather than through the declared CLI/stdio boundary, accessed private bridge fields for read-only verification, and the source bytes were read/parser-identified before `AuthorityKernel.invoke()`. `InvoiceRefSet` was not part of this execution path.

## Result

PASS — the first real Cabinet_web user-data **functional** canary completed through the trusted local capability bridge implementation.

This evidence distinguishes the private local real-data execution from GitHub Actions. GitHub Actions verifies the bridge/runtime composition; the real original PDF remained local and was not uploaded as CI evidence.

## Canonical Web input

```text
Cabinet_web main commit: d3fac8e5d2b85c12904cba24060717b84e2757c2
invoice_id: invoice-f260001
Card repository path: data/cards/invoice-f260001/card.json
Card content hash: sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf
source_git_commit_sha: 386134cbb28e3689fec8ffb49815db9416ebe9a8
source_id: source-f260001
```

The confirmed Web Card remained unchanged during the complete canary.

## Trusted bridge implementation

```text
spec-workbench implementation commit: bc872b605c3e4b3774749cdf1711eeeb35399eaf
entrypoint: tools/local_capability_bridge.py
real canary runner: tools/f260001_real_canary_via_bridge.py
declared bridge transport: local_cli_stdio
real runner invocation: in_process_bridge_methods
```

Protected capability configuration in the pinned implementation:

```text
invoice.archive.accept_revision
  credential class: synchronization
  resource scope: invoice:invoice-f260001

invoice.source.attach
  credential class: local_agent
  resource scope: invoice:invoice-f260001
```

Safe protected configuration reference names:

```text
database.primary_dsn
database.schema
vault.private_root
cabinet_web.reviewed_checkout
authority.synchronization.credential_id
authority.synchronization.credential_material
authority.local_agent.credential_id
authority.local_agent.credential_material
```

No configuration values, DSN, vault path, credential material or storage reference are part of this evidence.

## GitHub execution evidence for bridge/runtime

```text
workflow: Cabinet Web attach canary
run_id: 32529515458
head_sha: bc872b605c3e4b3774749cdf1711eeeb35399eaf
conclusion: success
artifact_id: 9463368772
artifact_digest: sha256:6f81d77d2e5747d19608bf438f9551f333cc309f0feebbc95d30d95f064dfdb2
```

Successful workflow steps include:

```text
static Cabinet Web interop guards
Cabinet Web revision acceptance canary
no-MIME/no-hash source attach canary
same-invoice revision-to-source E2E canary
trusted local capability bridge probe
artifact upload
```

Reported focused verification:

```text
bridge CI: 11/11 PASS
existing cabinet_web_* tests: 42/42 PASS
combined focused suite: 49/49 PASS
```

BRIDGE-001..011 include negative exact-scope and credential-class checks. Those are CI assurance evidence for the pinned implementation, not observations of negative cases in the private real-data execution.

## Real local execution

Safe report returned by the local canary:

```text
delivery_id: real-f260001-cf5972ac55c546dda6db5df0dd937931
revision receipt outcome: accepted
backend_current_content_hash: sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf
source_id: source-f260001
local calculated source SHA-256: sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66
parser-validated media type: application/pdf
source attachment result: attached
Card unchanged: true
acceptance audit present: true
attachment audit present: true
```

The real execution directly proves:

1. the exact confirmed Cabinet_web Card revision was accepted without mutation;
2. the accepted backend current hash equals the exact Web canonical hash;
3. the real original PDF was parser-identified as `application/pdf`;
4. the local box calculated and retained the binary SHA-256 as local evidence;
5. the source became attached under the exact Card-owned `source-f260001` identity;
6. durable acceptance and attachment audit rows existed for the invoice;
7. the confirmed Web Card was unchanged after all local effects.

It does **not** directly prove that the CLI/stdio isolation was exercised, that the agent process could not access bridge internals, that PDF parsing occurred only after authorization, that the host independently owned credentials relative to the runner, or that `InvoiceRefSet` remained opaque in this path.

## Full-suite note

A broader local suite reported:

```text
605 passed
6 failed
```

The six failures were reported as pre-existing stale count assertions in State 5/6/assembly and were not caused by the bridge or Cabinet_web interoperability work. They are not used as evidence for this canary and should remain separately tracked technical debt rather than being relabelled PASS.

## Gate consequence

```text
Cabinet_web canonical real input: PASS
functional revision acceptance: PASS
functional real PDF source attachment: PASS
Card immutability: PASS
durable effect-audit existence: PASS
pinned bridge CI assurance: PASS
real-run assurance closure: PARTIAL
all guarantees proven by exact real run: false
```
