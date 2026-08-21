# Minimal local capability bridge — design boundary

This note records the narrow implementation boundary discovered by the first real F260001 preflight.

The verified Cabinet executors are already the business/authority implementations. The missing layer is only a trusted local invocation surface.

The bridge may compose existing providers and expose local-only operations, but it may not become a new owner of:

- Invoice Card validation semantics;
- revision acceptance rules;
- source attachment rules;
- principal identity;
- grant scope;
- effect scope;
- disclosure policy;
- storage paths or database identities.

For the first canary, the two protected operations remain:

```text
invoice.archive.accept_revision  -> synchronization credential class
invoice.source.attach            -> local_agent credential class
```

Both are scoped exactly to `invoice:invoice-f260001`.

A local CLI/tool or IPC transport is sufficient. Network exposure is not required.

The bridge must call the public `execute()` methods of the existing protected executors so `AuthorityKernel.invoke()` remains on every effectful path.

The bridge must use host-owned protected configuration for provider secrets and credential verification. Requests must never be allowed to manufacture principal, grant, authorization, effect scope, database identity, vault reference or module/function selection.

No direct database read is required before the first revision attempt. A null base is safe because the acceptance runtime fails closed with `reconciliation_required` and a bounded current hash if a conflicting current revision already exists.
