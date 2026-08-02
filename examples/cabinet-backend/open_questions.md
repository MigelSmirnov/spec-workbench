# Cabinet Backend — open product questions

## Status

Open decisions discovered while filling State 1. They remain explicit inputs to
State 1 closure and later State 2 rules. No endpoint, table, transport, module,
or implementation is implied.

## State 1 model questions

1. How does Cabinet obtain the relevant PresuPro estimate for a Registry
   `project_id`: direct PresuPro lookup, Registry artifact discovery, or another
   agreed boundary?
2. Does PresuPro already provide a reliable way to select one current estimate
   for a project, and what happens when several estimates exist?
3. Does Cabinet persist a full observed estimate snapshot, a compact projection,
   or only an `EstimateReference` with content hash/version?
4. Which stable identifiers currently exist for PresuPro zones and estimate
   items? If they do not exist, what fingerprint and invalidation evidence is
   sufficient for the baseline?
5. Is one Invoice Line to at most one Estimate Item the accepted first-product
   limit?
6. Is a rejected estimate match a durable decision record, or may rejection live
   only in general decision history?
7. Who may confirm an estimate match: user only, user plus trusted agent, or
   another authorized actor?
8. Which invoice or estimate changes automatically invalidate a confirmed
   match?
9. How is a corrected Invoice Card handled after a successful Holded
   publication: correction document, replacement, cancellation and republish,
   or a separate workflow owned by Holded policy?
10. Which Provider, Contact, Material List, Document, and Project Note fields
    are mandatory for the first PostgreSQL-backed Cabinet release?
11. Is `ProjectNote` an embedded Work Object entity in the baseline, or should
    notes be independent Cards from the first release?
12. Is `SourceReference` a shared independently identified entity or a value
    object embedded separately in each Card?

## State 2 policy questions

1. What freshness policy changes Registry synchronization state from `current`
   to `stale`?
2. Does Cabinet retain historical Registry snapshots or only the current
   snapshot plus audit evidence?
3. Which historical Cabinet corrections remain allowed after Registry project
   archival?
4. How are assignment suggestions, rejected candidates, confirmation, and
   reassignment history represented without overloading the current assignment?
5. What exact invoice or estimate revision changes invalidate a confirmed
   `InvoiceLineEstimateMatch`?
6. Which plan-versus-actual values are calculated when units differ and no
   explicit conversion exists?
7. Which forecast price basis is the default, if any, and must the agent always
   ask before projecting a final cost?
8. What is the precise first-product meaning of `refunded` when only part of a
   purchase is returned?
9. Can an archived Invoice Card remain in historical plan-versus-actual totals,
   and how are excluded or corrected invoices represented?
10. What rule ensures that one invoice revision has at most one successful
    Holded accounting publication unless a correction workflow explicitly
    authorizes another action?

## Source and infrastructure questions

1. Which original source binaries are stored by Cabinet?
2. Which binary storage service owns them?
3. What retention, integrity, and deletion policy applies to source binaries?
4. Does Holded Gateway require a separate deployable and database from its
   first release, or may it be an independently owned platform module deployed
   beside other services without direct table access?
5. What production authentication and service-authorization model applies to
   users, agents, Cabinet, Registry, PresuPro, Holded Gateway, and Client
   Portal?

## External-contract questions

1. What exact PresuPro read contract returns estimate identity, project link,
   zones, items, quantities, units, prices, waste, margin, discounts, IVA, and
   totals for agent-assisted analysis?
2. What contract or evidence identifies the estimate revision or content hash
   used by an accepted match?
3. What PresuPro event produces an approved immutable presupuesto for future
   downstream publication?
4. How are PresuPro zones and items mapped to later Client Portal Budget
   Sections?
5. What exact Cabinet facts and corrections does Client Portal accept?
6. Is Client Portal delivery push, pull, or artifact-based?
7. What Holded Gateway command and receipt semantics support idempotent purchase
   invoice publication, ambiguous outcomes, reconciliation, and corrections?

## Resolved product questions

- Cabinet uses the same Registry project-context access pattern as other current
  platform applications.
- Work Object is the Cabinet working interface for one Registry project.
- `WorkObject.id` equals Registry `project_id`; no second Cabinet Work Object
  identity is introduced.
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
- One Invoice Card has at most one current primary Work Object assignment.
- Multi-object Invoice allocation is deferred.
- Invoice Line fields are intentionally comparable with PresuPro Estimate Item
  fields without copying planning values into invoice facts.
- PresuPro owns the plan; Cabinet owns accepted invoice facts and match
  decisions.
- The agent owns heuristic semantic matching between differently named products
  from different shops.
- A suggestion does not participate in plan-versus-actual calculations until it
  is confirmed.
- Several Invoice Lines from several invoices may match one Estimate Item.
- Partial distribution of one Invoice Line across several Estimate Items is
  deferred from the baseline.
- Plan-versus-actual totals, variances, remaining quantities, average prices,
  and forecasts are calculated on demand rather than stored as primary facts.
- Multiple payment transactions may describe one purchase, including split
  cash/card settlement.
- The complete payment status vocabulary is preserved: `unknown`, `unpaid`,
  `partially_paid`, `paid`, and `refunded`.
- There is no cross-invoice payment aggregate in the first product.
- One confirmed Invoice Card revision may be published to Holded through Holded
  Gateway independently from PresuPro matching and analysis.
- Registry application registration and project membership are future platform
  concerns, not blockers for the current context-read integration.
