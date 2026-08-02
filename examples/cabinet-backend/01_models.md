# State 1 — Cabinet Backend domain models

## Status

Draft domain model based on the accepted Cabinet Invoice Card V1 and the
observed `registry_sandbox` contracts.

## Model boundary

State 1 preserves the difference between:

- Registry-owned platform project identity and current project context;
- Cabinet-owned Work Object identity and operational knowledge;
- a durable Registry context replica required for Cabinet offline work;
- Invoice Card source facts and mutable object-assignment decisions.

No endpoint, database table, ORM mapping, event mechanism, or transport is
defined here.

## WorkObject

### Meaning

`WorkObject` is Cabinet's autonomous working representation of one Registry
project. It is the Cabinet UI and agent context for invoices, material lists,
documents, contacts, providers, notes, and accepted relationships concerning
that project.

It is an entity with stable Cabinet identity. It is not a second Registry
project.

### Creation

A Work Object is created lazily after Cabinet receives a Registry `project_id`,
successfully validates it, and obtains the first project context snapshot.
Repeated creation for the same Registry project resolves to the same Work
Object.

### Candidate fields

- `id` — stable Cabinet Work Object identity;
- `registry_project_id` — required Registry UUID and unique external identity;
- `registry_snapshot` — current durable `RegistryProjectSnapshot`;
- `registry_sync` — current `RegistrySyncState`;
- `cabinet_alias` — optional Cabinet-owned working name;
- `lifecycle` — Cabinet Card lifecycle;
- `created_at`;
- `updated_at`;
- `revision`.

### Ownership

Cabinet creates and modifies Work Object identity, alias, lifecycle, sync
evidence, and Cabinet relationships. Registry creates and modifies the source
values represented by the snapshot.

### Invariants

- one Work Object refers to exactly one Registry project;
- `registry_project_id` is unique among Work Objects;
- initial creation requires a successful Registry context read;
- Registry field changes do not change Work Object identity;
- Registry unavailability does not invalidate or delete the Work Object;
- ordinary Work Object edits cannot alter Registry-owned snapshot values;
- an archived Registry project remains readable but rejects new operational
  assignment by default.

## RegistryProjectSnapshot

### Meaning

`RegistryProjectSnapshot` is Cabinet's durable replica of the last successfully
observed Registry project context. It enables the Cabinet Web UI and chat-based
agents to work when Registry or the platform is temporarily unavailable.

It is a persisted value object and evidence record, not an independently
editable project model.

### Candidate fields

- `project_id`;
- `display_name`;
- `address`;
- `project_status` — `active` or `archived` from Registry;
- `customer_ref`;
- `project_created_at`;
- `registry_updated_at`;
- `captured_at`.

### Producer

A successful Registry project-context read produces the complete snapshot.
Cabinet replaces the previous current snapshot atomically while preserving
Work Object and operational history.

### Readers

- Cabinet Web UI;
- Cabinet agents;
- assignment and search capabilities;
- later reporting and publication preparation;
- audit and stale-context presentation.

### Invariants

- `project_id` equals the parent Work Object's `registry_project_id`;
- all fields in one snapshot come from the same successful Registry response;
- `captured_at` is Cabinet observation time;
- snapshot fields are not modified individually by user or agent edits;
- a snapshot can be stale while remaining valid historical evidence.

## RegistrySyncState

### Meaning

`RegistrySyncState` records what Cabinet currently knows about its ability to
refresh the Registry snapshot.

### Status vocabulary

- `current` — the latest Registry read succeeded;
- `stale` — a snapshot exists but freshness is no longer confirmed;
- `unavailable` — the last refresh failed because Registry could not be
  reached;
- `not_found` — Registry explicitly reported that the project does not exist.

Registry project status `active` or `archived` remains a separate value inside
the snapshot.

### Candidate fields

- `status`;
- `last_attempt_at`;
- `last_success_at`;
- `last_error_code` optional;
- `last_error_message` optional safe diagnostic.

### Invariants

- `current` requires a successful snapshot captured at `last_success_at`;
- temporary unavailability never erases the last successful snapshot;
- `not_found` is recorded only from an explicit Registry response;
- errors do not fabricate a new project status or context.

## InvoiceObjectAssignment

### Meaning

`InvoiceObjectAssignment` records the first-product primary assignment of an
Invoice Card. It is a Cabinet decision about how a purchase is organised, not a
fact printed by the supplier document unless supported by explicit source
context.

### States

- `unreviewed` — no assignment decision has been made;
- `assigned` — linked to one Work Object;
- `intentionally_unassigned` — reviewed and deliberately kept without an
  object;
- `label_only` — one free-form label is preserved until a Work Object is
  identified.

Agent suggestions and rejected candidates may be stored as separate decision
records rather than overloading the confirmed assignment.

### Candidate fields

- `status`;
- `work_object_id` optional;
- `label` optional;
- `decided_at` optional;
- `decided_by` optional;
- `invoice_revision`;
- `revision`.

### Invariants

- `assigned` requires exactly one existing Work Object;
- new assignment to a snapshot whose Registry status is `archived` is rejected
  by default;
- `intentionally_unassigned` has no Work Object ID;
- one Invoice Card has at most one current primary assignment;
- reassignment preserves decision history;
- multi-object and line-level allocation are outside the first product.

## Payment and PaymentTransaction

### Accepted vocabulary

The backend preserves the complete implemented Invoice Card payment-status
vocabulary:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `refunded`.

The main purchase workflow still assumes immediate full payment, but the model
must preserve source-faithful exceptional cases.

`PaymentTransaction` preserves one settlement fact. Several transactions may
belong to one Invoice Card, including split cash/card settlement. There is no
`mixed` payment method because mixing is represented by several transactions.

No cross-invoice payment aggregate, bank reconciliation, or debt workflow is
introduced in the first product.

## Invoice Card lifecycle

The accepted lifecycle remains:

- `draft`;
- `confirmed`;
- `archived`.

These values describe Cabinet record review and preservation. They do not
represent purchase ordering, delivery, consumption, or payment lifecycle.

## Offline operation rules

Using a persisted Work Object and snapshot while Registry is unavailable,
Cabinet may:

- display and search the object;
- capture and review invoices;
- assign invoices to the already known Work Object;
- maintain Cabinet-owned material lists, documents, contacts, providers, and
  notes;
- expose to agents that Registry context is stale or unavailable.

Cabinet may not:

- create a new platform Work Object for an unvalidated project ID;
- edit Registry-owned snapshot fields;
- claim the external context is current;
- create or reactivate a Registry project.

## Deferred platform models

The following belong to future Registry/platform development and are not
invented as Cabinet models:

- `RegisteredApplication`;
- `ProjectApplicationMembership`;
- `ServiceIdentity`;
- application capabilities and permissions;
- attach/detach history;
- Registry events and subscriptions.

The current Registry sandbox provides project identity, validation, launch
context, and project-context reads, but not these application-participation
contracts.

## Readiness questions

Before State 1 is accepted, verify:

- whether Cabinet alias is needed in the first release;
- the exact Cabinet Card lifecycle used for Work Objects;
- the freshness policy that changes sync state from `current` to `stale`;
- whether historical Registry snapshots are retained or only the current
  snapshot plus audit evidence;
- the allowed corrections to Cabinet historical data after Registry archive;
- the exact representation of assignment suggestion and rejection history.
