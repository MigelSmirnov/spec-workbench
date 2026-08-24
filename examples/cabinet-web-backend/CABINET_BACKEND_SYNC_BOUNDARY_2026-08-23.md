# cabinet_backend synchronization boundary evidence

Date: 2026-08-23
Factory project: `cabinet_backend`
Accepted base SHA-256:
`48ff46297b4b0bd134063c898a11a38df74f33c51e193fd303b1b523b3414a6e`

## Scope

Read-only evidence for Cabinet Web State 0. No `cabinet_backend` source, spec,
artifact, branch, service, or worktree was changed.

The backend is under active development and the reviewed accepted spec has no
terminal OTK evidence. Its current normalized/deployed build is stale relative
to the accepted base. These facts are a pinned design snapshot, not proof of a
deployable backend release. The boundary must be refreshed before external
contract closure and Stage 9.

## Accepted direction

The current synchronization rule declares:

```text
direction = backend_to_vps_only
```

The local `cabinet_backend` initiates network contact with the continuously
available Cabinet VPS. The VPS does not initiate a connection to the local
machine.

This one connection direction carries two product data directions:

```text
Cabinet Web -> local backend: Invoice work packages only
local backend -> Cabinet Web: Registry catalogue deliveries only
```

## Invoice intake owned by cabinet_backend

The local synchronization application receives a
`SynchronizationWorkSelection` for one invoice and calls the VPS transport to
obtain an exact `VpsInvoiceTransferPackage`.

The package contains:

- synchronization transport evidence;
- an `InvoiceTransferManifest`;
- one stored immutable Invoice Card revision;
- the required source binary replicas.

After an exact package is returned, `cabinet_backend` passes the manifest, Card
revision, and source replicas to its own durable archive acceptance boundary.
Transport delivery alone is never durable acceptance.

Only an accepted/already-accepted archive receipt may be followed by an
authoritative durable-acceptance verification for the exact Card content hash
and required source identities.

Timeout, connection loss, or response loss after issuance becomes an explicit
unknown outcome. The local backend must not repeat the logical transfer
automatically; it performs bounded read-only reconciliation for the persisted
synchronization identity.

## Registry package published to Cabinet Web

The local backend builds a `RegistryCatalogueDelivery` containing:

- catalogue identity;
- an ordered tuple of `RegistryProjectSnapshot` values;
- source and target node identities;
- idempotency key;
- creation time.

Each project snapshot carries Registry-owned project identity, display name,
address, status, Registry update time, capture time, and source contract
version.

The local backend publishes the exact delivery to Cabinet Web and receives a
bounded `VpsCatalogueAcknowledgement`. Publication is idempotent for the exact
catalogue, target node, and idempotency key. A conflicting reuse writes
nothing.

Cabinet Web treats the package as a cached Registry projection. It does not
become the source of truth for Registry projects.

## State-0 consequence

The simplest operating cycle is one operator- or locally scheduled evening
session:

1. local backend observes and authenticates the Cabinet VPS;
2. local backend discovers/selects pending Invoice work;
3. local backend pulls and durably accepts each exact Invoice package;
4. unknown outcomes are reconciled read-only;
5. local backend publishes the newest Registry catalogue package;
6. Cabinet Web acknowledges the exact catalogue;
7. the local connection closes.

Provider, Client, Project, shopping-list, and other Cabinet Web-owned data do
not flow into `cabinet_backend` in this boundary. They remain available and
owned by the autonomous Cabinet Web application.

The exact pending-work discovery contract is not visible in the reviewed
transport interface and remains an explicit later flow/API question. It must
not be hidden behind a generic list or arbitrary payload.
