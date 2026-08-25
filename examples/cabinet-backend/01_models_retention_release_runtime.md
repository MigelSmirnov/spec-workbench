# State 1 repair — retention release runtime evidence

## Withdrawn model M76 — VpsWorkingSetMembership

Withdrawn by A76 (`02_rules_flow6_ownership_repair.md`): the VPS working set and its release belong to Cabinet Web.

Immutable read observation with `project_id: str`, `working_set_id: str`,
`invoice_revisions: tuple[InvoiceCardRevisionReference, ...]`, `node_id: str`, and
`observed_at: datetime`.

### Identity
value
### Identity evidence
Equal exact working-set identity, ordered membership, node, and observation time
are interchangeable evidence.

Later membership observations are new values. Registry status is not membership
or deletion authority.

## Runtime interface

`RetentionReleaseRepository` is the narrow PostgreSQL port for immutable
evaluations and release decisions. It owns no eligibility or deletion policy.
