# State 1 clarification — Cabinet synchronization direction

## Status

Accepted clarification of the State 1 system boundary.

This document does not add State 2 business rules. It resolves ambiguities in
`01_models.md` about which node initiates communication between Cabinet and the
local Cabinet Backend, and about how Registry-derived project data reaches the
Cabinet `WorkObject` card.

## System roles

- **Cabinet** is the VPS web application and continuously available user workspace.
- **Cabinet Backend** is the local durable Backend and integration centre, normally
  available only while the local computer is running.

## Accepted boundary

Synchronization uses a **local-initiated pull model**.

Cabinet prepares completed work for retrieval but does not initiate a connection
to Cabinet Backend. When available, Cabinet Backend connects to Cabinet and pulls
ready work packages.

Cabinet does not call Registry, PresuPro, Holded, Client Portal, or other platform
applications directly. Those integrations belong to Cabinet Backend.

## State 1 model clarification

1. A completed and confirmed Cabinet work result is represented by the existing
   `InvoiceTransferManifest` and its referenced Card and source content.
2. Cabinet stores ready manifests and source bytes in a VPS-side outbound working
   area until Cabinet Backend retrieves them.
3. `InvoiceSynchronization` is initiated by the `local_backend` node, even though
   its payload direction is `vps_cabinet -> local_backend`.
4. Cabinet Backend first lists or discovers ready manifests, then retrieves the
   exact immutable package identified by its manifest hash.
5. Cabinet does not require Cabinet Backend to be reachable when the user confirms
   an Invoice Card.
6. Successful retrieval or durable acceptance does not automatically delete the
   VPS working replica; retention is governed by the separate manual VPS retention
   decision.
7. Registry catalogue publication is the reverse payload direction but remains
   initiated by Cabinet Backend: `local_backend -> vps_cabinet`.
8. Any platform-derived data made available to Cabinet is prepared and published
   by Cabinet Backend. Cabinet never fetches it from platform applications itself.

## WorkObject and Registry ownership clarification

`WorkObject` is a **Cabinet Card owned by the Cabinet web application**. It is not
a Cabinet Backend-owned domain entity.

Registry remains authoritative for project identity and current project master
data. Cabinet Backend is the integration intermediary that:

- reads Registry;
- captures immutable `RegistryProjectSnapshot` records locally;
- prepares a compact, versioned `RegistryCatalogueSnapshot`;
- publishes that catalogue to Cabinet on the VPS.

Cabinet consumes the published catalogue and creates or updates its own
`WorkObject` Cards from that published data. Cabinet does not obtain Registry data
through a direct Registry request.

The identity relationship remains:

```text
WorkObject.id = Registry ProjectRecord.id
```

This equality preserves the shared project identity but does not transfer
ownership of Registry master data to Cabinet. The `WorkObject` may own
Cabinet-specific relationships, invoices, notes, matches, working history, and
user context, while Registry continues to own the current project name, address,
customer context, and lifecycle facts.

The data flow is therefore:

```text
Registry
   ↓ read by Cabinet Backend
RegistryProjectSnapshot
   ↓ compact catalogue published by Cabinet Backend
Cabinet Registry catalogue replica
   ↓ Cabinet creates or updates WorkObject Cards
User works with WorkObject in Cabinet
   ↓ confirmed Card later pulled by Cabinet Backend
Cabinet Backend validates the referenced project against current Registry data
```

Cabinet Backend may store references to `project_id`, catalogue provenance, and
Registry snapshots needed for validation and durable history. It must not model
itself as the owner of the Cabinet `WorkObject` Card.

## Correction to LocalBackendConnectionObservation

`LocalBackendConnectionObservation` must not imply that Cabinet probes or calls the
local Backend.

For the current baseline it is interpreted as a synchronization observation owned
or produced by the local synchronization client, or as status information later
published to Cabinet. Cabinet may display the last known synchronization state,
but it does not actively test local Backend reachability.

A clearer future name may be:

```text
CabinetSynchronizationObservation
```

Candidate facts include:

- last successful pull time;
- last accepted receipt time;
- last published Registry catalogue time;
- compatible contract version;
- safe failure or authentication state.

Renaming the model in the main State 1 document remains editorial follow-up; the
normative direction defined here applies immediately.

## Boundary diagram

```text
Registry
   ↓
Cabinet Backend (local integration centre)
   ↓ publishes compact catalogue
Cabinet (VPS web application)
   ↓ owns WorkObject Cards and prepares confirmed work packages
VPS outbound working area
   ↑ Cabinet Backend initiates pull when the local computer is online
Cabinet Backend durable archive
```

## What remains for State 2

State 2 may define deterministic behavior inside this accepted boundary, including:

- ready-package eligibility;
- idempotent retries;
- manifest conflict handling;
- acknowledgement and receipt semantics;
- partial download and quarantine behavior;
- authentication and authorization policy;
- unknown outcomes.

State 2 must not reopen whether Cabinet pushes to the local Backend or directly
calls platform applications.
