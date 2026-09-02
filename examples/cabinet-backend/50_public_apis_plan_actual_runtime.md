# State 5 repair — complete plan/actual public operations

## Refined — `public_op:plan_actual.refresh_estimate_snapshot`

Owner: `module:plan_actual`.

Accepts an observation through the service, validates stable identity and
canonical content, and returns the exact newly issued or idempotently existing
immutable snapshot.

## Refined — `public_op:plan_actual.propose_invoice_line_matches`

Owner: `module:plan_actual`.

Returns stable ordered, non-authoritative proposals for one exact archived
invoice revision and estimate snapshot. It performs no decision transition.

## Refined — `public_op:plan_actual.record_match_decision`

Owner: `module:plan_actual`.

Records one explicit confirmed, rejected, or invalidated decision under the
exact source locks. Conflicting active confirmation is rejected atomically.

## Refined — `public_op:plan_actual.get_unmatched_items`

Owner: `module:plan_actual`.

Returns explicit unmatched invoice-line and estimate-item identities computed
from exact pinned evidence and active confirmed decisions; no placeholder item is
created.

## Refined — `public_op:plan_actual.calculate_plan_actual`

Owner: `module:plan_actual`.

Resolves every pinned input through the service repository, archive, and Registry
boundaries before applying the already accepted deterministic formulas.
