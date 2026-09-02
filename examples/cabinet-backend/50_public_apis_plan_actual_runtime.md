# State 5 repair — complete plan/actual public operations

## Refined — `public_op:plan_actual.refresh_estimate_snapshot`

Owner: `module:plan_actual`.

Accepts an observation through the service, validates stable identity and
canonical content, and returns the exact newly issued or idempotently existing
immutable snapshot.

## `public_op:plan_actual.propose_invoice_line_matches`

### Owner
`module:plan_actual`

### Callers
Plan/actual request adapters.

### Inputs
Exact archived `invoice_id` with its pinned `content_hash` and exact immutable `estimate_snapshot_id`.

### Outputs
Stable ordered tuple of non-authoritative `InvoiceLineMatchProposal` values.

### Observable effect
Computes proposals from exact pinned invoice and estimate evidence; performs no decision transition.

### Enforces
Pinned-evidence identity, stable deterministic ordering, and the non-authoritative nature of proposals — only an explicit recorded decision can confirm a match.

### Errors
`PlanActualPreconditionError` when the pinned invoice revision or estimate snapshot is missing, mismatched, or insufficient for proposal computation.

### State impact
None; proposals are derived read-only output.

## `public_op:plan_actual.record_match_decision`

### Owner
`module:plan_actual`

### Callers
Plan/actual request adapters.

### Inputs
One explicit `InvoiceLineEstimateMatch` decision — confirmed, rejected, or invalidated — bound to exact invoice-line and estimate-item identities.

### Outputs
The persisted `InvoiceLineEstimateMatch` decision.

### Observable effect
Records the explicit decision under the exact source locks.

### Enforces
Explicit human/agent decision only, exact source binding, atomic rejection of a conflicting active confirmation, and idempotent replay of an equivalent decision.

### Errors
`PlanActualPreconditionError` when the referenced invoice revision, estimate snapshot, or line/item identities are missing or mismatched, or when a conflicting active confirmation exists.

### State impact
Mutates match-decision state only; invoice and estimate source facts remain immutable.

## `public_op:plan_actual.get_unmatched_items`

### Owner
`module:plan_actual`

### Callers
Plan/actual request adapters.

### Inputs
Exact `project_id` and exact immutable `estimate_snapshot_id`.

### Outputs
`UnmatchedPlanActualItems` naming explicit unmatched invoice-line and estimate-item identities.

### Observable effect
Computes unmatched identities from exact pinned evidence and active confirmed decisions.

### Enforces
Explicit unmatched truth: no placeholder item is created and no unmatched fact is hidden by a default.

### Errors
`PlanActualPreconditionError` when the exact project or estimate snapshot evidence is missing or unresolved.

### State impact
None; read-only derived output.

## Refined — `public_op:plan_actual.calculate_plan_actual`

Owner: `module:plan_actual`.

Resolves every pinned input through the service repository, archive, and Registry
boundaries before applying the already accepted deterministic formulas.
