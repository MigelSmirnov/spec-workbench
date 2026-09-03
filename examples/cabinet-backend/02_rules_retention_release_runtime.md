# State 2 repair — retention release runtime lowering

## Accepted decision A75 — durable release authorization boundary

### Normative rules

- Synchronization supplies one typed, read-only exact working-set membership.
- Retention resolves every member through synchronization observation and archive
  durable verification; missing or changed membership blocks authorization.
- PostgreSQL stores immutable evaluation and decision evidence and serializes one
  exact working-set authorization lifecycle.
- `request_manual_vps_release` reloads current membership and every authoritative
  proof under the target lock before recording a decision.
- Equivalent still-valid requests return the same logical decision; conflicting,
  stale, or broadened targets are rejected.
- `get_retention_status` returns exact committed decision/evaluation state and
  cannot infer completion of physical deletion.
- The service never deletes VPS data. A physical adapter acts only on an exact
  recorded authorization and reports execution separately.
- Bootstrap constructs the PostgreSQL repository/service and fails closed.

Repository and synchronization adapters provide evidence mechanisms only;
retention_release owns allow/block policy.

### Formal invariants

Withdrawn by A76: the release-authorization invariants of this design moved to
Cabinet Web together with Flow 6 ownership; no local fenced invariant remains
to enforce.

### Required tests

Withdrawn by A76: the flow and its semantic tests moved to Cabinet Web; no
   [witness: workbench:modules]
local test remains for this decision.

### Consequence

Superseded by A76. Flow 6 ownership moved to Cabinet Web, and this local
release-authorization design is withdrawn; the sections above remain the
record of the withdrawn shape.
