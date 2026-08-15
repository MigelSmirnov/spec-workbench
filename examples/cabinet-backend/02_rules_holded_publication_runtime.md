# State 2 repair — Holded publication runtime lowering

## Accepted decision A74 — PostgreSQL logical publication boundary

The first implementation stores `HoldedPublication` lifecycle state in the shared
Cabinet PostgreSQL deployment behind a typed repository.

- One exact Invoice Card revision has at most one active logical publication.
- The logical publication and exact revision/attempt binding are committed before
  the sole gateway create call.
- Equivalent requests return the existing publication; conflicting active state
  is rejected under PostgreSQL uniqueness and row locking.
- Gateway attempts and observations remain technical evidence; only the
  publication service applies A51/A52 business verification and settlement.
- Ambiguous/failed read-back evidence is persisted before returning and never
  authorizes another create.
- Reconciliation locks and reloads the exact publication and archive revision,
  uses read-only gateway lookup, then appends a verified or unresolved transition.
- Status reads return exact persisted state or fail; no default success exists.
- Bootstrap constructs the repository/service and fails closed without PostgreSQL.

The repository owns storage mechanics only. Eligibility, verification, duplicate
prevention, and settlement remain owned by `holded_publication`.
