# Cabinet Backend — open product questions

## Status

Open State 0 decisions. No model, endpoint, table, or implementation is implied.

## Decisions that may remain open during early model work

1. Which original source binaries are stored by Cabinet, and which binary
   storage service owns them?
2. What exact relationship exists between a standalone Cabinet Work Object and
   a later Registry project link?
3. When a standalone Work Object is linked to Registry later, which Cabinet
   fields remain authoritative and which Registry fields are shown as a
   read-only projection?
4. Should the first backend preserve all Invoice Card payment statuses already
   supported by Cabinet (`unknown`, `unpaid`, `partially_paid`, `paid`,
   `refunded`) for source fidelity, while the primary purchase workflow assumes
   immediate full payment?
5. What PresuPro event produces an approved immutable presupuesto for
   downstream publication?
6. How are PresuPro zones and items mapped to Cabinet material requirements and
   later Client Portal Budget Sections?
7. What exact Cabinet facts and corrections does Client Portal accept?
8. Is Client Portal delivery push, pull, or artifact-based?
9. What production authentication and service-authorization model applies to
   users, agents, Cabinet, Registry, PresuPro, Holded Gateway, and Client
   Portal?
10. Does Holded Gateway need a separate deployable and database from its first
    release, or may it be one independently owned platform module deployed
    beside other services without direct table access?

## Resolved product questions

- One Invoice Card has one primary object assignment in the first complete
  product.
- The primary object assignment may be empty and is represented as an explicit
  unassigned state.
- Multi-object and line-level allocation do not belong to the Invoice Card V1
  fact model and are deferred.
- Multiple payment transactions may describe one purchase, including split
  cash/card settlement, but there is no cross-invoice payment aggregate in the
  first complete product.
- Standalone Cabinet Work Objects are allowed and may later be linked to
  Registry.
