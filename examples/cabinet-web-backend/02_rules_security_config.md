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
   [witness: verification:witness_A12]
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
   [witness: verification:witness_A13]
2. Search limits cannot exceed 100 through plugin or browser input.
3. Authentication throttle activates after five failures in the configured
   context and recovers after the configured interval without authenticating a
   failed request.
4. Timeout after issue never triggers an automatic second mutation.
5. Restore drill reconstructs exact Card/source/hash and pending-effect state.

### Consequence

Later deployment can tune documented values deliberately, while the generated
runtime cannot substitute unbounded or client-controlled defaults.

## Accepted decision A18 — runtime configuration has one typed fail-closed provider

### Normative rules

1. `module:runtime_settings` is the sole semantic and implementation owner of
   environment-variable parsing. It exposes one deterministic
   `load_runtime_settings` entrypoint and returns one immutable M135
   `RuntimeSettings` snapshot.
2. `ENVIRONMENT` is required, has no default, is normalized by trimming and
   lowercasing, and must resolve to M134 `RuntimeEnvironment`. Missing or
   invalid input aborts startup before application composition.
3. `DATABASE_URL` supplies `RuntimeSettings.database_url`. It is required in
   every environment, has no default, is not trimmed or rewritten, and an
   absent or empty value aborts startup. This is the runtime realization of
   `config.runtime_storage.database_url_required`.
4. The authentication threshold and duration inputs supply
   `RuntimeSettings.auth_failures_before_throttle` and
   `RuntimeSettings.auth_throttle_seconds`. Each is an optional positive
   base-10 integer whose absent value is taken from its accepted A13 config
   address. Invalid, zero, or negative input aborts startup.
5. The ChatGPT proposal TTL input supplies
   `RuntimeSettings.chatgpt_proposal_ttl_seconds`. It is an optional positive
   base-10 integer whose absent value is taken from
   `config.chatgpt.proposal_ttl_seconds`; invalid input aborts startup.
6. The search default and maximum inputs supply
   `RuntimeSettings.search_default_limit` and
   `RuntimeSettings.search_max_limit`. Each is an optional positive base-10
   integer whose absent value is taken from its accepted A13 config address.
   Startup also requires `search_default_limit <= search_max_limit`.
7. The upload handoff lifetime and byte-limit inputs supply
   `RuntimeSettings.upload_handoff_ttl_seconds` and
   `RuntimeSettings.upload_max_file_bytes`. Each is an optional positive
   base-10 integer whose absent value is taken from its accepted A13 config
   address. Invalid input aborts startup.
8. The exact environment-variable names, targets, defaults, parsing kinds, and
   the search relation are emitted only from the structured runtime-settings
   data closure. Notes and LLM module slices receive M135 fields, never those
   values or the runtime-settings table.
9. `bootstrap` calls `load_runtime_settings` exactly once before constructing
   any service. It injects that one M135 snapshot into every behavioral
   consumer and passes only `settings.database_url` to the PostgreSQL UoW
   factory. No consumer reads environment variables, dereferences the original
   config addresses, invents a fallback, or constructs another provider.
10. Product-specific cross-setting constraints are declared in project data.
    The generic runtime-settings backend has no unconditional dependency on
    `rules.binary_delivery_policy` or any other project's policy block.
11. The protected byte-store root input supplies
    `RuntimeSettings.source_store_root_path`. It is required in every
    environment, has no default, and is passed by the composition root to the
    filesystem byte store exactly once; an absent or empty value aborts
    startup. This closes the last legacy composition-root environment read
    that rule 9 forbids.
12. The credential pepper input supplies `RuntimeSettings.credential_pepper`.
    It is required in every environment, has no default, is passed by the
    composition root to the access-control service exactly once, and is never
    logged or exposed by any other consumer; an absent or empty value aborts
    startup.

### Formal invariants

```text
count(runtime_settings_provider) = 1
count(load_runtime_settings per application composition) = 1
runtime_consumer -> typed RuntimeSettings input
missing_or_invalid_required_setting -> startup_aborted
search_default_limit <= search_max_limit
runtime_settings_backend -/> implicit product_policy_dependency
```

### Required tests

1. Missing or invalid `ENVIRONMENT` and missing or empty `DATABASE_URL` fail
   before the application graph is constructed.
2. Each optional positive-integer input uses its accepted config default when
   absent and rejects malformed, zero, and negative values.
3. A search default greater than the search maximum fails startup.
4. Composition loads one snapshot and every affected consumer uses only its
   typed M135 fields.
5. Cabinet Web runtime-settings emission succeeds without a
   `rules.binary_delivery_policy` block.
6. Client Portal retains its explicitly declared startup-consistency check
   through the same backend.
   [witness: verification:witness_A18]

### Consequence

Runtime configuration is loaded once as typed data. Behavioral generation no
longer receives product values or freedom to reinterpret their runtime source,
and project-specific constraints remain outside the generic emitter.

## Accepted decision A17 — PostgreSQL metadata and protected VPS byte custody

### Normative rules

1. PostgreSQL is the authoritative store for every Cabinet Web `master` model,
   current selectors, immutable evidence, idempotency reservation, conflict,
   and recovery-journal state.
2. Every stateful application operation receives a narrow repository or unit
   of work. Domain services never receive a database URL, open connections,
   read environment variables, or construct persistence adapters.
3. One application operation uses one explicit PostgreSQL transaction. Locks
   and uniqueness constraints serialize identity, revision, idempotency, and
   current-selector decisions before state is read or changed. A failed
   operation rolls back without exposing partial logical state.
4. Original source bytes are stored only beneath one required absolute private
   VPS storage root. The root is outside the public Web tree, is not a symlink,
   is on one filesystem for staging and final paths, and is unavailable to
   callers as a path or storage identifier.
5. File names are derived from server-verified SHA-256 content identity, never
   from caller filenames, Card fields, MIME text, or source metadata.
6. Byte publication writes a private staging file, flushes it, reopens it and
   verifies exact size and SHA-256, records the candidate/final identity and
   publication state inside the owning PostgreSQL transaction, and uses an
   atomic same-filesystem rename. An existing final path is never replaced by
   different bytes.
7. A transaction failure before commit removes the candidate staging file. A
   failure after metadata commit remains a recoverable pending publication.
   Startup recovery verifies and finalizes it or records a bounded failed state;
   it never reports the source as available while metadata and bytes disagree.
8. PostgreSQL migrations run before serving traffic and are monotonic and
   rollback-aware. Startup fails closed when the database URL, connectivity,
   schema version, storage root, permissions, atomic-rename capability, or
   recovery pass is invalid.
9. Backups jointly cover PostgreSQL and the private byte store. A backup is
   releasable only after isolated restore proves exact Card revision, source
   identity, source hash, effect, transfer, Registry-replica, and pending-work
   relationships.
10. Cabinet Web remains operational with the local backend offline. No Cabinet
    Web read or mutation performs an outbound connection to the local network,
    and synchronization reads only already committed Web-side state.
11. Every wall-clock timestamp persisted, emitted in a runtime model, or
    compared with persisted state is timezone-aware UTC. Naive datetimes are
    forbidden. Elapsed intervals use a monotonic clock and are never derived
    by subtracting wall-clock timestamps.

### Formal invariants

```text
master_state -> committed_postgresql_row
source_available -> committed_metadata AND reopened_final_bytes_hash_match
domain_service -/> database_url OR environment OR adapter_construction
local_backend_offline -/> cabinet_web_state_unavailable
request_path -/> filesystem_path
persisted_or_emitted_timestamp -> timezone_aware_utc
elapsed_interval -> monotonic_clock
```

### Required tests

1. Concurrent revision, idempotency, issuance, receipt, and catalogue writes
   [witness: verification:witness_A17]
   produce one accepted transition or an explicit conflict without lost update.
2. Process termination before file commit, after metadata commit, and around
   atomic rename is recovered without exposing truncated or unverified bytes.
3. Traversal names, symlinks, hash mismatch, cross-filesystem roots, unusable
   permissions, and missing configuration fail closed.
4. Starting with the local backend unavailable still permits all Cabinet
   Web-owned reads and authorized mutations and preserves pending synchronization.
5. Isolated restore verifies the database/byte-store relationship before the
   restored instance can become ready.
6. Runtime timestamp tests reject naive values, compare only timezone-aware UTC
   values, and keep elapsed timeout/throttle measurement monotonic.

### Consequence

State 3 must separate application policy from PostgreSQL and filesystem
mechanisms, State 6 must expose narrow repository/unit-of-work and byte-store
contracts plus one composition root, and Stage 8.1 cannot close until every
stateful slice receives those dependencies.

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
   [witness: verification:deployed_tree_inventory]
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
   [witness: workbench:language]
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
