# State 1 clarification — Cabinet synchronization direction

## Status

Accepted clarification of the State 1 system boundary.

This document does not add State 2 business rules. It resolves ambiguities in
`01_models.md` about which node initiates communication between Cabinet and the
local Cabinet Backend, and about where Registry-derived project projections live.

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

`WorkObject` is a **Cabinet Backend-owned local projection** keyed by the Registry
`project_id`. It is not created by Cabinet through a direct Registry request.

Registry remains authoritative for project identity, name, address, customer
context, and lifecycle. Cabinet Backend reads Registry and maintains:

- `RegistryProjectSnapshot` records;
- the local `WorkObject` projection;
- `RegistryCatalogueSnapshot` publications prepared for Cabinet.

Cabinet receives only a published, compact, versioned Registry catalogue from
Cabinet Backend. Cabinet uses that catalogue to let the user select an object while
the local computer is unavailable. The selected project identifier and catalogue
provenance return later inside the completed Invoice Card work package.

Therefore the data flow is:

```text
Registry
   ↓ read by Cabinet Backend
RegistryProjectSnapshot / WorkObject
   ↓ compact catalogue published by Cabinet Backend
Cabinet offline catalogue
   ↓ user selects project; confirmed Card later pulled
Cabinet Backend validates selection against current Registry data
```

The sentence in `01_models.md` stating that “Cabinet owns relationships, invoices,
notes, matches, and history” uses **Cabinet as the wider product/domain**, not the
VPS web application as an integration owner. For node-level responsibility it
must be read as follows:

- Cabinet Backend durably owns the relationships, invoices, matches, and history;
- Cabinet may hold working copies and user decisions while offline;
- Registry owns the current project master data;
- Cabinet never becomes authoritative for Registry fields.

This interpretation removes any implication that the VPS application calls
Registry or independently maintains authoritative `WorkObject` records.

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
User -> Cabinet (VPS)
          |
          | prepares confirmed immutable work packages
          v
      VPS outbound working area
          ^
          | Cabinet Backend initiates pull when local computer is online
          |
Cabinet Backend (local)
          |
          | owns platform integrations
          v
Registry / PresuPro / Holded / Client Portal
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

State 2 must not reopen whether Cabinet pushes to the local Backend, directly
calls platform applications, or independently owns Registry project master data.
