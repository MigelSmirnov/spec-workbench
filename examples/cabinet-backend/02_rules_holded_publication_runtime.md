# State 2 repair — Holded publication runtime lowering

## Accepted decision A74 — PostgreSQL logical publication boundary

The first implementation stores `HoldedPublication` lifecycle state in the shared
Cabinet PostgreSQL deployment behind a typed repository.

### Normative rules

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

### Formal invariants

```text
count(active_logical_publication per card_revision) <= 1
gateway_create -> committed_publication_binding_first
ambiguous_read_back -/> second_create
status_read -> exact_persisted_state_or_failure
```

### Required tests

1. Concurrent publish requests for one revision yield one logical publication.
   [witness: verification:semantic_flow5_holded_publication]
2. The gateway create is impossible without a committed binding.
3. Persisted ambiguous read-back blocks any further automatic create.
4. Reconciliation appends transitions and never rewrites history.
5. Bootstrap fails closed without PostgreSQL.

### Consequence

One accepted revision maps to at most one logical Holded publication whose
lifecycle is fully persisted; no crash or retry can double-publish or invent
success.
