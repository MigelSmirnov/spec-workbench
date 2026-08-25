# Cabinet Backend — open product questions

## Status

Open decisions after accepting the two-tier Cabinet architecture. State 0 now
accepts that fresh invoices remain fully workable on the VPS while the local
Backend owns the complete durable archive and local platform integrations.

## Synchronization and authority questions

1. After first successful synchronization, is the VPS Invoice Card strictly
   read-only, or may Cabinet explicitly check out a new revision?
2. How long does the VPS retain synchronized originals and structured invoice
   revisions?
3. Which source files, metadata, provenance, and revision history must be
   transferred atomically?
4. May a draft synchronize before confirmation, or does synchronization always
   transfer the current state regardless of lifecycle?
5. How is `unknown_outcome` reconciled after a timeout?
6. Which conflict types remain possible under the baseline single-owner-after-sync
   rule?
7. Can the local Backend reject an already confirmed VPS invoice for domain
   validation reasons, and what user state follows?
8. How are local-only historical invoices surfaced to the VPS without copying
   the complete archive?
9. Which Card types besides Invoice require a future VPS working lifecycle?

## VPS working-set questions

1. What exact invoice count, age, or storage quota defines the fresh working set?
2. Are synchronized invoice bodies searchable on the VPS until retention expiry?
3. Does the VPS retain extracted text after deleting the synchronized original?
4. What encrypted backup, if any, protects unsynchronized VPS invoices?
5. What recovery path applies if the VPS fails before synchronization?
6. Which user-visible freshness and authority labels are required?

## State 1 domain questions

1. How does Cabinet obtain the relevant PresuPro estimate for a Registry
   `project_id`?
2. What happens when several estimates exist for one project?
3. Which stable identifiers exist for PresuPro zones and estimate items?
4. Is a persisted local `EstimateSnapshot` required for every accepted match?
5. Who may confirm an estimate match?
6. Which invoice or estimate changes invalidate a confirmed match?
7. Is a rejected match a durable decision record?
8. How is a corrected Invoice Card handled after successful Holded publication?
9. Which Provider, Contact, Material List, Document, and Project Note fields are
   mandatory for the first local PostgreSQL release?
10. Is `SourceReference` shared across revisions or embedded per Card revision?

## State 2 policy questions

1. Exact transitions for `remote_only`, `syncing`, `synchronized`, `conflict`,
   `failed`, and `unknown_outcome`.
2. Revision-freeze behavior during transfer.
3. Idempotency and reconciliation rules.
4. Conflict-resolution choices and audit evidence.
5. Registry snapshot freshness and history policy.
6. Estimate-match invalidation rules.
7. Quantity analysis when units differ.
8. Forecast default and required assumptions.
9. Partial refund semantics.
10. Archived invoice inclusion in plan-versus-actual totals.
11. Holded correction and repeat-publication rules.

## Security and operations questions

1. Select Tailscale, SSH reverse tunnel, mTLS, or equivalent transport.
2. Define VPS session, recovery, expiry, and revocation.
3. Define VPS encryption, backup, and unsynchronized-invoice recovery.
4. Define local backup destination, keys, RPO, RTO, and restore tests.
5. Define synchronization credential rotation and incident response.
6. Define safe audit and log retention in both zones.
7. Define source retention and deletion guarantees after synchronization.
8. Define Holded Gateway placement and authentication.

## External-contract questions

1. PresuPro read contract for estimate identity, project link, zones, items,
   quantities, units, prices, waste, margin, discounts, IVA, and totals.
2. Evidence that identifies the estimate version used by a match.
3. Registry contract for validating project assignment during synchronization.
4. Holded Gateway command and receipt semantics for idempotency, ambiguity,
   reconciliation, and corrections.
5. Future Client Portal intake boundary.

## Resolved decisions

- Cabinet VPS and local Backend are separate trust and data zones.
- Fresh invoices remain fully workable on the VPS while the local platform is
  offline.
- A stable `invoice_id` is created at first VPS capture and preserved locally.
- The VPS is authoritative for an unsynchronized fresh invoice revision.
- The local Backend is the complete durable archive after synchronization.
- Synchronization is authenticated, encrypted, revision-aware, and idempotent.
- Unrestricted multi-master editing is not part of the baseline.
- The VPS stores a limited fresh working set, not the complete archive by
  default.
- Registry and PresuPro are reached only through the local Backend.
- Validated Work Object assignment requires local Registry evidence.
- Invoice Line fields remain comparable with PresuPro Estimate Item fields.
- The agent proposes semantic matches; only accepted matches affect analytics.
- Plan-versus-actual results are calculated on demand.
- Holded publication is independent from matching and uses Holded Gateway.
- Holded credentials never become Cabinet or agent data.
