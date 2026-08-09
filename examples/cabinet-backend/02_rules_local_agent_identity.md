# State 2 — Local Cabinet agent and interactive identity boundary

## Accepted decision A66 — local agents use service identity; local human access may delegate to the OS

A60 and A61 remain authoritative for the two Cabinet trust zones, exact-operation authorization, and the dedicated synchronization identity. This decision refines the local-identity baseline now that the product boundary explicitly includes an agent running inside the local platform.

The following earlier A61 baseline assumptions are superseded:

- a Cabinet-owned local account store is not required for the single-user baseline;
- a reusable Cabinet password is not required for interactive use on the protected local machine;
- a local agent is not required to act only through an authenticated local-user delegation;
- the `SyncNodeCredential` must never be reused as the local agent credential.

### Normative rules

1. Cabinet exposes agent/application operations on both participating runtimes:
   - VPS Cabinet exposes the continuously available remote tool boundary;
   - Local Cabinet Backend exposes a local/private tool boundary for the agent and other explicitly enrolled local consumers.
2. Both boundaries should expose the same logical Cabinet application operations where the owning data and integrations permit them. A transport wrapper may use MCP, HTTP, CLI, IPC, or another accepted local transport without moving business rules into that wrapper.
3. The local tool boundary is not a public internet surface. It binds only to localhost, local IPC, or an explicitly trusted private interface selected by deployment policy.
4. Interactive human use on the single-user local platform may rely on the authenticated operating-system session and local machine protection instead of a separate Cabinet password store.
5. OS-delegated local human access does not create a Cabinet password-recovery flow. Loss or compromise of the local machine is handled through operating-system/device recovery plus revocation of Cabinet machine/service credentials.
6. A local agent or other non-human local consumer must authenticate as an explicit local service identity or through an equivalent OS/IPC peer identity that the Backend can map to one enrolled service principal.
7. Local service identity is distinct from human interactive context and from `SyncNodeCredential`. No credential may be interchangeable across these boundaries.
8. Each local service principal receives only the operations/capabilities needed by that consumer. Running on localhost does not itself authorize an operation.
9. Cabinet Backend performs authorization for the exact requested operation and target. Client UI state, prompt text, possession of an entity ID, or successful local network connection is not authorization proof.
10. Audit/provenance for an agent-assisted mutation records the acting service/agent identifier and, when the operation was explicitly initiated on behalf of a human interaction, the human/interaction context separately.
11. Reusable human passwords, local service credentials, and sync-node credentials must not be placed in agent prompts, Cards, source files, exports, generated artifacts, or ordinary logs.
12. Local service credentials must support revocation and rotation without changing the semantic identity of Cabinet business entities or the synchronization installation identity.
13. A future multi-user or remotely exposed local deployment requires a new accepted product/security decision before introducing Cabinet-owned local human accounts, remote local-browser authentication, or a public local endpoint.

### Formal invariants

```text
local_human_interactive_baseline
-> authenticated OS session
-> Cabinet operation authorization

local_agent_operation
-> enrolled local service principal
-> exact capability and target authorization

SyncNodeCredential
-/> local agent operation

local service credential
-/> synchronization authority

localhost reachability
-/> operation authorization
```

### Required tests

1. A local agent request without an enrolled service/peer identity is rejected before protected state changes.
2. A valid local service identity cannot perform an operation outside its allowed capability set.
3. `SyncNodeCredential` is rejected at the local agent/application boundary.
4. A local agent credential is rejected as synchronization authority.
5. OS-delegated interactive local access does not require or expose a Cabinet password-recovery endpoint in the single-user baseline.
6. Audit evidence distinguishes a direct service action from an agent action explicitly performed on behalf of a human interaction.
7. Binding the local tool surface to localhost/private transport does not bypass authorization checks.

### Consequence

Cabinet can run a capable local agent next to the complete archive, Registry, PresuPro, source files, and local integrations without inventing a second human password system for a single-user machine. Additional local consumers can be enrolled as separate service principals with narrow capabilities, while synchronization continues to use its dedicated installation credential.

A66 does not resolve VPS human login throttling/recovery policy or dependency policy. Those remain owned by OQ-008 and OQ-011 respectively.
