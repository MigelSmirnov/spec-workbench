# Cabinet Backend — open product questions

## Status

Open decisions that may remain during early State 1 work. No endpoint, table,
transport, or implementation is implied.

## Domain questions

1. Is a Cabinet-owned `cabinet_alias` required in the first Work Object model,
   or is the copied Registry display name sufficient?
2. What exact Cabinet Card lifecycle applies to Work Objects independently of
   Registry project status?
3. What freshness policy changes Registry synchronization state from `current`
   to `stale`?
4. Does Cabinet retain every historical Registry snapshot, or only the current
   snapshot plus audit evidence of replacements?
5. Which historical Cabinet corrections remain allowed after the Registry
   project becomes archived?
6. How are assignment suggestions, rejected candidates, confirmation, and
   reassignment history represented without overloading the current Invoice
   Card assignment?
7. Which original source binaries are stored by Cabinet, and which binary
   storage service owns them?
8. What is the precise first-product meaning of `refunded` when only part of a
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
6. When will Registry define registered applications, project-to-application
   membership, participation checks, attach/detach history, service identity,
   and change notifications?
7. Does Holded Gateway need a separate deployable and database from its first
   release, or may it be an independently owned platform module deployed beside
   other services without direct table access?

## Resolved product questions

- A Work Object is Cabinet's autonomous representation of one Registry project.
- The relationship is one Registry project to zero or one Cabinet Work Object.
- Work Object creation requires successful initial Registry validation and a
  first project-context read.
- Work Object has its own stable Cabinet identity and a required unique
  `registry_project_id`.
- Registry context is copied into a durable read-only snapshot for offline Web
  UI and conversational-agent work.
- Registry remains authoritative for copied project identity fields.
- Existing Work Objects remain usable during temporary Registry unavailability.
- Invoice Cards may exist without a Work Object.
- One Invoice Card has one primary object assignment in the first complete
  product.
- The primary assignment may be unreviewed, assigned, intentionally unassigned,
  or label-only.
- Multi-object and line-level allocation are deferred.
- Multiple payment transactions may describe one purchase, including split
  cash/card settlement.
- The complete payment status vocabulary is preserved: `unknown`, `unpaid`,
  `partially_paid`, `paid`, and `refunded`.
- There is no cross-invoice payment aggregate in the first complete product.
- Registry application registration and project membership are not implemented
  in the current sandbox and remain future platform contracts.
