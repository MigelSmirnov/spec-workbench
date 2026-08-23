# State 2 — Interpreted input, dependency, configuration, and security review

## Accepted decision A12 — external input remains data, never executable structure

### Normative rules

1. User text, ChatGPT proposals, Card fields, search terms, filenames, source
   bytes, Registry snapshots, local receipts, and external error text are
   untrusted data at their ingress boundary.
2. Operation kind, capability, state transition, sort/order field, query
   predicate, template, command, path, and parser mode come only from closed
   application vocabularies selected by trusted code.
3. Caller values cannot become SQL/query structure, shell arguments, template
   source, executable code, model/system instructions, arbitrary MCP tool names,
   filesystem paths, URL origins, or redirect targets.
4. ChatGPT-generated identifiers, hashes, totals, media declarations, and
   confirmation claims are validated or recomputed by the authoritative
   Cabinet boundary.
5. Remote/system error bodies are never rendered as trusted HTML or returned
   unbounded; only bounded stable codes and safe details cross to users.

### Formal invariants

```text
untrusted_input -/> executable_or_query_or_template_or_path_structure
model_claim -/> authorization_or_confirmation_or_integrity_evidence
external_error -/> active_browser_content
```

### Required tests

1. Injection strings in every text/identifier field remain inert data.
2. Unknown operation, transition, sort, filter, media, and redirect values fail
   closed.
3. ChatGPT-supplied hash/identity/confirmation is not trusted without server
   verification.
4. Oversized or markup-bearing external errors become bounded safe results.

### Consequence

Neither conversational input nor transport flexibility creates a generic
interpreter boundary.

## Accepted decision A13 — first-release operational configuration is finite

### Normative rules

The following are runtime config values, not domain facts:

| Key | First-release value |
| --- | ---: |
| `upload_max_file_bytes` | 31,457,280 (30 MiB) |
| `upload_files_per_handoff` | 1 |
| `upload_handoff_ttl_seconds` | 900 |
| `sync_request_timeout_seconds` | 120 |
| `sync_metadata_max_bytes` | 8,388,608 (8 MiB) |
| `sync_source_max_file_bytes` | 31,457,280 (30 MiB) |
| `invoice_package_max_bytes` | 41,943,040 (40 MiB) |
| `registry_catalogue_max_bytes` | 5,242,880 (5 MiB) |
| `auth_failure_window_seconds` | 900 |
| `auth_failures_before_throttle` | 5 |
| `auth_throttle_seconds` | 900 |
| `search_default_limit` | 20 |
| `search_max_limit` | 100 |
| `backup_interval_hours` | 24 |
| `backup_retention_days` | 30 |
| `restore_drill_interval_days` | 90 |

Additional rules:

1. Every size, count, timeout, TTL, and retention value is positive and bounded.
2. Public nginx and application limits must agree so the edge cannot accept a
   body the application cannot safely handle.
3. A timeout does not classify an already issued mutation as failed; A04/A08
   unknown-outcome rules apply.
4. Backups include canonical Cards, source bytes, idempotency/effect records,
   upload custody, synchronization evidence, Registry replicas, and release
   evidence. Reusable secrets are backed up only through the protected host
   secret-recovery mechanism, not ordinary business-data export.
5. A backup is not considered recoverable until a scheduled isolated restore
   proves integrity and exact source/Card relationships.
6. Configuration changes are deployment revisions with provenance and rollback;
   clients cannot override safety limits per request.
7. `sync_metadata_max_bytes` applies to JSON and protocol metadata, not streamed
   source bytes. One streamed source and the complete logical package must
   independently satisfy their respective limits. Binary content is never
   expanded as base64 JSON.

### Formal invariants

```text
client_request -/> safety_limit_override
timeout_after_issue -> outcome_unknown_or_reconciled
backup_recoverable -> isolated_restore_verified
```

### Required tests

1. Boundary values pass and values beyond each size/count limit fail.
2. Search limits cannot exceed 100 through plugin or browser input.
3. Authentication throttle activates after five failures in the configured
   context and recovers after the configured interval without authenticating a
   failed request.
4. Timeout after issue never triggers an automatic second mutation.
5. Restore drill reconstructs exact Card/source/hash and pending-effect state.

### Consequence

Later deployment can tune documented values deliberately, while the generated
runtime cannot substitute unbounded or client-controlled defaults.

## Accepted decision A14 — dependencies are inventoried and release-gated

### Normative rules

1. Every deployed Python, MCP/tunnel, Web, and host-facing runtime dependency
   has an owner, pinned or reproducibly resolved version, license, and update
   source in the release inventory.
2. Production release runs supported dependency vulnerability checks and blocks
   a known reachable critical or high-severity issue unless a time-bounded
   exception records applicability, containment, approver, expiry, upgrade or
   rollback plan, and verification evidence.
3. Critical reachable findings receive remediation or effective containment
   within 72 hours; high within 7 days; other applicable findings within 30
   days or a documented not-applicable decision.
4. Unsupported/end-of-life runtime versions and dependencies block new release.
5. Updates pass Cabinet tests, migration checks, rollback readiness, and VPS
   canary/health verification before promotion.
6. Package registry credentials and advisory service tokens obey A11 and never
   enter ordinary artifacts or logs.

### Formal invariants

```text
production_release
-> dependency_inventory_current AND vulnerability_gate_passed

unsupported_runtime_or_dependency -> release_blocked
exception -> approver AND expiry AND containment AND recovery_plan
```

### Required tests

1. Missing/unpinned direct dependency and unsupported runtime block release.
2. Reachable critical/high advisory blocks without a valid exception.
3. Expired exception blocks release.
4. Updated dependencies must pass the full Cabinet verification and rollback
   checks.
5. Dependency reports contain no registry credential.

### Consequence

The small backend has a bounded release policy without creating a separate
security subsystem or silently shipping stale vulnerable components.

## Accepted decision A15 — complete security review for States 0–2

### Normative rules

The review covers every actor and ingress boundary accepted in State 0 and ties
authorization to M02/M17 identities from State 1. All nine required categories
are applicable to this deployed server product and have enforceable decisions.

### Formal invariants

```text
State_2_security_gate_pass
<-> every_required_category = APPLICABLE
    AND every_category_references_accepted_decision
    AND no_security_open_question
```

### Required tests

1. The deterministic State 2 lint accepts exactly one complete review record.
2. Every reference resolves to an indexed State 2 decision.
3. No required category is silent or unresolved.

### Consequence

State 3 is blocked if any referenced decision is removed, becomes unresolved,
or loses its enforceable boundary.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A03, A11, A13; affected: M02, M17, browser, ChatGPT plugin, local synchronization, operator boundary
- secrets: APPLICABLE; references: A06, A11, A14; affected: M02, M15, M17, deployment configuration, logs, backups, exports
- authorization: APPLICABLE; references: A02, A03, A10, A16; affected: M02, M07, M08, M09, M10, M14, M15, M16, M17, M20, M22
- injection_interpreted_input: APPLICABLE; references: A02, A05, A07, A12, A16; affected: ChatGPT proposals, Card fields, search, files, templates, queries, operation selection
- external_callbacks_webhooks: APPLICABLE; references: A04, A08, A09; affected: local-initiated Invoice pull receipt and Registry catalogue publication boundaries
- browser_boundary: APPLICABLE; references: A05, A06, A07, A11; affected: secondary Web upload and Card surfaces
- files_artifacts: APPLICABLE; references: A01, A05, A06, A10, A13; affected: M05, M06, M14, M15, M21, source download, backups
- concurrency: APPLICABLE; references: A01, A04, A06, A08, A09, A10; affected: M10, M14, M15, M16, M20, M22, M28
- dependencies: APPLICABLE; references: A14; affected: deployed Python, MCP/tunnel, Web and host runtime dependencies
