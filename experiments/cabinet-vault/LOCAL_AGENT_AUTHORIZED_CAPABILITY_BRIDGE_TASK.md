# Local agent task — expose verified Cabinet capabilities through a trusted local bridge

## Goal

Make the already verified Cabinet local-box executors callable by the local agent through a minimal trusted local transport, without changing their business semantics or weakening authority.

After the bridge passes its own tests, immediately rerun the existing F260001 real-data canary task.

This is host wiring, not a new synchronization design.

## Current blocker

The real F260001 input is ready:

```text
invoice_id: invoice-f260001
source_id: source-f260001
Card hash: sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf
real PDF local SHA-256: sha256:b1ad4b4f15ddcba8c91f0f2d17f8a45ab58fd4febcd1064360aed758f14dec66
```

The last preflight stopped because there was no authorized local host connection exposing:

```text
invoice.archive.accept_revision
invoice.source.attach
```

## Existing code to compose, not replace

Use the existing verified components:

```text
tools/authority_kernel.py
tools/protected_configuration_kernel.py
tools/typed_schema_kernel.py
tools/postgres_record_kernel.py
tools/local_private_byte_vault.py
tools/bounded_content_validation_kernel.py
tools/bounded_media_identification.py
tools/cabinet_web_revision_accept_runtime.py
tools/cabinet_web_source_attach_adapter.py
tools/invoice_source_attach_runtime.py
```

Do not route the real canary through `cabinet_host.py` or `cabinet_graph_host.py`; those are older demo SQLite hosts for different capability surfaces.

## Required trust boundaries

Preserve the executor-owned boundaries exactly:

```text
invoice.archive.accept_revision
  credential class: synchronization
  resource scope: invoice:invoice-f260001

invoice.source.attach
  credential class: local_agent
  resource scope: invoice:invoice-f260001
```

The bridge must not call protected executor internals that bypass `AuthorityKernel.invoke()`.

## Minimal bridge surface

Implement the smallest local-only transport that the local agent can invoke reliably. `local_tool` or local IPC is preferred; do not add network exposure merely for the canary.

The public operation set for this task must contain only:

```text
health/readiness
invoice.archive.accept_revision
invoice.source.attach
```

`health/readiness` must disclose only safe booleans/descriptors. It must not return credentials, DSN, vault paths, database identities or raw configuration values.

Do not add arbitrary SQL, arbitrary filesystem access, arbitrary Python execution, generic capability names supplied by the caller, or an endpoint that lets the agent select modules/functions.

## Host-owned configuration

Use protected configuration for secrets and storage/provider configuration. Secrets must not be committed to Git.

At minimum resolve host-owned references for:

```text
PostgreSQL DSN
private byte-vault root
synchronization credential verifier/configuration
local-agent credential verifier/configuration
```

Principal identity, credential class, grants, effects, disclosures and resource scope are host-owned configuration. They must not be accepted from the request payload.

For the first real canary it is acceptable to provision grants scoped exactly to:

```text
invoice:invoice-f260001
```

Do not grant wildcard invoice scope for convenience.

## Authority policies

Bind the exact executor constants/policies, including effects and disclosures. Do not duplicate them with looser handwritten values when the runtime constants can be imported.

The synchronization principal must receive only the grant required for:

```text
invoice.archive.accept_revision
```

The local-agent principal must receive only the grant required for:

```text
invoice.source.attach
```

A synchronization credential must fail on the local-agent boundary and vice versa.

## Provider startup

On bridge startup:

1. require protected configuration readiness;
2. initialize the PostgreSQL record kernel/schema;
3. initialize the private byte vault;
4. construct typed-schema and bounded-content/media providers;
5. construct both protected executors using one durable record kernel;
6. perform required pending-publication recovery before reporting ready;
7. only then expose `health/readiness = ready`.

Source publication recovery is a host-startup responsibility, not an agent-visible bypass operation.

## Cabinet_web validation boundary

Do not create a permanent backend import of Cabinet_web Python modules.

For the canary delivery, preserve the existing reviewed/pinned Cabinet_web contract-validation approach. Contract fingerprint drift must block execution rather than being repaired silently in the bridge.

## Request handling

For revision acceptance, the bridge may receive the already constructed `cabinet-web-sync-v1` delivery payload plus caller credential presentation required by the chosen local transport. It must pass the delivery to `CabinetWebRevisionAcceptExecutor.execute()`.

For source attachment, use `CabinetWebSourceAttachAdapter` / the verified attachment semantics so that missing upstream MIME/hash remain missing upstream facts while parser media and calculated SHA remain local evidence.

Do not hand-build database rows or vault references in the bridge.

## Base revision behavior

Do not add a direct database preflight read solely to discover the current hash.

For the first F260001 attempt, `base_backend_content_hash=null` is safe. If a different current revision already exists, the verified acceptance runtime must return:

```text
reconciliation_required
backend_current_content_hash: <safe hash>
```

with no overwrite. Reconcile explicitly after that receipt.

## Required tests

Add executable tests proving at least:

1. bridge refuses startup when required protected configuration is missing;
2. health/readiness never discloses secret values, DSN or vault path;
3. wrong credential class cannot cross the synchronization/local-agent boundary;
4. missing exact invoice grant is denied;
5. a grant for another invoice cannot invoke F260001;
6. caller cannot supply principal, grant, authorization decision, effect scope or storage references as authority;
7. revision acceptance through the bridge produces the same bounded receipt semantics as the verified executor;
8. source attachment through the bridge uses the same protected executor/adapter and does not expose vault paths;
9. direct arbitrary capability/function/module selection is impossible;
10. startup recovery completes before readiness is true;
11. existing Cabinet Web interop/runtime tests remain green.

Use PostgreSQL/vault test providers in CI as the existing canaries do. Do not weaken tests by swapping the real bridge composition for an in-memory fake at the protected boundary.

## Deliverables

Return:

```text
implementation commit / PR
bridge entrypoint
chosen local transport
safe configuration reference names (not values)
principal/credential classes provisioned
exact grants/scopes provisioned
bridge tests result
existing cabinet_web_* tests result
how the local agent invokes readiness
how the local agent invokes accept_revision
how the local agent invokes source.attach
```

Do not return secret values, DSN, vault root, storage references or credential material.

## Then rerun the real canary

Once the bridge reports ready and both exact grants are verified, rerun:

```text
experiments/cabinet-vault/LOCAL_AGENT_F260001_REAL_CANARY_TASK.md
```

Do not change F260001 Card facts or migrate the legacy Client/Project projections during the bridge task.