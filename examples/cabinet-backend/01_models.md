# State 1 — Cabinet Backend domain models

## Status

Draft domain model based on the accepted Cabinet Invoice Card V1 and the
observed `registry_sandbox` contracts.

## Model boundary

State 1 preserves the difference between:

- Registry-owned project identity and current project context;
- Cabinet-owned project-scoped working knowledge;
- a durable Registry context replica required for autonomous Cabinet work;
- Invoice Card facts and mutable object-assignment decisions.

No endpoint, database table, ORM mapping, event mechanism, or transport is
defined here.

## WorkObject

### Meaning

`WorkObject` is Cabinet's local working interface for one Registry project. It
organises invoices, material lists, documents, contacts, providers, notes, and
accepted Cabinet decisions for that project.

It is not a second project entity. Its identity is the platform project
identity:

```text
WorkObject.id = Registry ProjectRecord.id
```

### Creation

Cabinet creates the persisted Work Object representation lazily after receiving
a Registry `project_id` and successfully obtaining the first project context.
Repeated opening of the same `project_id` resolves to the same Work Object.

### Candidate fields

- `id` — Registry project UUID;
- `registry_snapshot` — current durable `RegistryProjectSnapshot`;
- `registry_sync` — current `RegistrySyncState`;
- `created_at` — time Cabinet first persisted the local representation;
- `updated_at` — time Cabinet-owned state or snapshot evidence last changed;
- `revision` — Cabinet revision for local state and relationships.

A separate Cabinet alias is not required in the baseline. It may be added later
only if a concrete user need appears.

### Ownership

Registry owns project identity and the source values copied into the snapshot.
Cabinet owns persistence of the snapshot, sync evidence, and all Cabinet
relationships and history associated with the Work Object.

### Invariants

- Work Object ID is a valid Registry project UUID;
- one Registry project resolves to at most one Work Object representation;
- initial creation requires a successful Registry context read;
- Registry field changes do not change Work Object identity;
- Registry unavailability does not invalidate or delete the Work Object;
- ordinary Cabinet edits cannot alter Registry-owned snapshot values;
- archived Registry projects remain readable but reject new assignment by
  default.

## RegistryProjectSnapshot

### Meaning

`RegistryProjectSnapshot` is Cabinet's durable copy of the last successfully
observed Registry project context. It enables the Web UI and conversational
agents to work when Registry is temporarily unavailable.

It is a persisted value object and evidence record, not an independently
editable project model.

### Candidate fields

- `project_id`;
- `display_name`;
- `address`;
- `project_status` — `active` or `archived`;
- `customer_ref`;
- `project_created_at`;
- `registry_updated_at`;
- `captured_at`.

### Invariants

- `project_id` equals the parent Work Object ID;
- all fields come from one successful Registry response;
- `captured_at` is Cabinet observation time;
- snapshot fields are replaced as one unit, not edited individually;
- a snapshot may be stale while remaining valid historical evidence.

## RegistrySyncState

### Meaning

`RegistrySyncState` records what Cabinet currently knows about refreshing the
Registry snapshot.

### Status vocabulary

- `current` — the latest Registry read succeeded;
- `stale` — a snapshot exists but freshness is no longer confirmed;
- `unavailable` — the last refresh failed because Registry could not be
  reached;
- `not_found` — Registry explicitly reported that the project does not exist.

Registry lifecycle status remains separate inside the snapshot.

### Candidate fields

- `status`;
- `last_attempt_at`;
- `last_success_at`;
- `last_error_code` optional;
- `last_error_message` optional safe diagnostic.

### Invariants

- `current` requires a successful snapshot captured at `last_success_at`;
- temporary unavailability never erases the last snapshot;
- `not_found` is recorded only from an explicit Registry response;
- refresh errors never fabricate new project context.

## InvoiceObjectAssignment

### Meaning

`InvoiceObjectAssignment` records the first-product primary assignment of an
Invoice Card. Invoice Card identity is independent from Work Object identity,
so an invoice may exist without any project assignment.

### States

- `unreviewed` — no assignment decision has been made;
- `assigned` — linked to one Work Object by Registry project UUID;
- `intentionally_unassigned` — reviewed and deliberately kept without an
  object;
- `label_only` — free-form wording is retained as a matching hint without a
  confirmed Work Object.

### Candidate fields

- `status`;
- `work_object_id` optional Registry project UUID;
- `label` optional;
- `decided_at` optional;
- `decided_by` optional;
- `invoice_revision`;
- `revision`.

### Invariants

- `assigned` requires exactly one existing Work Object;
- `work_object_id` equals the target Registry project UUID;
- `unreviewed`, `intentionally_unassigned`, and `label_only` have no confirmed
  Work Object ID;
- label-only evidence never creates a Work Object;
- one Invoice Card has at most one current primary assignment;
- reassignment preserves history;
- multi-object and line-level allocation are outside the first product.

## Payment and PaymentTransaction

The backend preserves the complete implemented payment-status vocabulary:

- `unknown`;
- `unpaid`;
- `partially_paid`;
- `paid`;
- `refunded`.

The normal purchase workflow assumes immediate full payment.
`PaymentTransaction` preserves one settlement fact. Several transactions may
belong to one Invoice Card, including cash plus card. There is no `mixed`
method: mixing is represented by several transactions.

No cross-invoice payment aggregate, bank reconciliation, or debt workflow is
introduced in the first product.

## Invoice Card lifecycle

The accepted lifecycle remains:

- `draft`;
- `confirmed`;
- `archived`.

These values describe Cabinet record review and preservation. They do not
represent ordering, delivery, consumption, or payment lifecycle.

## Offline operation rules

Using a persisted Work Object and snapshot while Registry is unavailable,
Cabinet may:

- display and search the object;
- capture and review invoices;
- assign invoices to the already known Work Object;
- maintain Cabinet-owned material lists, documents, contacts, providers, and
  notes;
- expose stale or unavailable Registry context to agents.

Cabinet may not:

- create a new Work Object for an unvalidated project ID;
- edit Registry-owned snapshot fields;
- claim the external context is current;
- create or reactivate a Registry project.

## Current integration principle

Cabinet follows the same current platform pattern as other applications:

1. receive `project_id` from Registry launch context;
2. read current context from Registry;
3. create or refresh local project-scoped state;
4. fall back to the stored snapshot when Registry is unavailable.

Application registration, membership, service identity, and notifications are
future platform concerns and do not block this first integration.

## Readiness questions

Before State 1 is accepted, verify:

- the freshness policy that changes sync state from `current` to `stale`;
- whether historical snapshots are retained or only the current snapshot plus
  audit evidence;
- allowed corrections to historical Cabinet data after Registry archive;
- representation of assignment suggestion and rejection history;
- first-product semantics of partial refunds.
