# Cabinet Backend — open product questions

## Status

Open decisions that may remain during early State 1 work. No endpoint, table,
transport, or implementation is implied.

## Domain questions

1. What freshness policy changes Registry synchronization state from `current`
   to `stale`?
2. Does Cabinet retain every historical Registry snapshot, or only the current
   snapshot plus audit evidence of replacements?
3. Which historical Cabinet corrections remain allowed after the Registry
   project becomes archived?
4. How are assignment suggestions, rejected candidates, confirmation, and
   reassignment history represented without overloading the current assignment?
5. Which original source binaries are stored by Cabinet, and which binary
   storage service owns them?
6. What is the precise first-product meaning of `refunded` when only part of a
   purchase is returned?

## External-contract questions

1. What PresuPro event produces an approved immutable presupuesto for
   downstream publication?
2. How are PresuPro zones and items mapped to Cabinet material requirements and
   later Client Portal Budget Sections?
3. What exact Cabinet facts and corrections does Client Portal accept?
4. Is Client Portal delivery push, pull, or artifact-based?
5. What production authentication and service-authorization model applies to
   users, agents, Cabinet, Registry, PresuPro, Holded Gateway, and Client
   Portal?
6. Does Holded Gateway need a separate deployable and database from its first
   release, or may it be an independently owned platform module deployed beside
   other services without direct table access?

## Resolved product questions

- Cabinet uses the same Registry project-context access pattern as the other
  current platform applications.
- Work Object is the Cabinet working interface for one Registry project.
- `WorkObject.id` equals the Registry `project_id`; no second Cabinet Work
  Object identity is introduced.
- One Registry project has at most one persisted Cabinet Work Object
  representation.
- Work Object creation requires a successful first Registry context read.
- Registry context is copied into a durable read-only snapshot for offline Web
  UI and conversational-agent work.
- Registry remains authoritative for copied project fields.
- Existing Work Objects remain usable during temporary Registry unavailability.
- Invoice Cards have their own identity and may exist without a Work Object.
- The primary assignment may be `unreviewed`, `assigned`,
  `intentionally_unassigned`, or `label_only`.
- Label-only evidence does not create a Work Object.
- One Invoice Card has at most one current primary assignment.
- Multi-object and line-level allocation are deferred.
- Multiple payment transactions may describe one purchase, including split
  cash/card settlement.
- The complete payment status vocabulary is preserved: `unknown`, `unpaid`,
  `partially_paid`, `paid`, and `refunded`.
- There is no cross-invoice payment aggregate in the first product.
- Registry application registration and project membership are future platform
  concerns, not blockers for the current context-read integration.
