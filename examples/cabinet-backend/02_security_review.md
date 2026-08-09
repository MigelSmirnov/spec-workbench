# State 2 — Cabinet security decisions and review

## Accepted decision A62 — runtime input never becomes interpreted structure

Cabinet accepts search text, filenames, uploaded documents, OCR output, agent
requests, Registry and PresuPro data, synchronization packages, and Holded
responses across the trust boundaries recorded by A60.

### Normative rules

1. Runtime or user-controlled input is data and MUST NOT become SQL/query,
   command, template, expression, tool-selection, or other executable structure.
2. A boundary may interpret input only through an explicitly selected closed
   parser, operation registry, enum, or typed field grammar owned by that
   boundary.
3. Document text, OCR content, supplier descriptions, filenames, and external
   labels cannot select a privileged Cabinet operation or enlarge its scope.
4. Stable entity IDs select a candidate target only; A61 and A66 authorization
   for the exact entity and operation remains independently required.
5. Query parameter lowering that is guaranteed by the deterministic persistence
   backend remains a backend mechanism and is not duplicated as project
   metadata or a compiler instruction.

### Formal invariants

```text
runtime_input -> data value
runtime_input -/> query_or_executable_structure

interpreted_input
-> explicitly selected closed grammar
-> validation before effect
```

### Required tests

1. Search and identifier inputs cannot alter query structure or select fields,
   operators, or commands outside the accepted closed vocabulary.
2. Filenames, OCR text, and document content cannot invoke Cabinet tools or
   privileged operations.
3. External labels and response text cannot become templates, commands, or
   dynamic operation names.
4. Rejecting interpreted input performs no protected state change.

### Consequence

State 2 owns the input/structure invariant while concrete SQL lowering, parser
implementation, and escaping remain responsibilities of the selected backend or
boundary implementation.

## Open question OQ-008 — credential abuse and account recovery policy

**Status:** RESOLVED by accepted decision A67.

A67 closes the remaining credential-abuse and recovery choices across the
accepted A60/A61/A66 identity boundaries:

- VPS human login uses account- and source-scoped abuse controls, progressive
  delay after 5 consecutive failures, and a 15-minute temporary block after 10;
- recovery uses a pre-bound email channel and a single-use short-lived token;
- successful recovery revokes every active human session;
- ordinary forgotten-password recovery does not automatically revoke separate
  agent/service or synchronization credentials;
- known or suspected compromise requires revocation or rotation of affected
  non-human credentials;
- machine/service credentials have rejection, throttling, rotation, and
  revocation behavior rather than a password-recovery flow;
- the single-user local human baseline remains OS-delegated and has no
  Cabinet-owned local password-recovery endpoint.

## Open question OQ-009 — upload payload and retrieval safety policy

**Status:** RESOLVED by accepted decision A64.

A64 closes payload acceptance, path ownership, non-executable treatment, storage
isolation, exact-entity authorization, and the current no-generic-retrieval
baseline using A60, A61, A62, A66, M05, M10, M11, and the accepted local-upload
operation. Numeric size/resource limits remain deployment configuration rather
than an unresolved product decision. Any future byte-retrieval API requires a
separate accepted disclosure decision.

## Open question OQ-010 — concurrent source attachment atomicity

**Status:** RESOLVED by accepted decision A65.

A65 defines the atomic attachment transition, identical-call idempotency,
conflicting-content rejection, and atomic visibility of replica/status/warning
changes. The accepted import decision independently owns atomic manifest
acceptance. Neither decision assigns a State 3 module.

## Open question OQ-011 — dependency vulnerability and update policy

**Status:** RESOLVED by accepted decision A68.

A68 assigns dependency inventory to each deployed surface's engineer/deployment
owner, requires reproducible dependency inventory, blocks introduction of known
critical and high vulnerabilities, defines remediation windows for deployed
critical/high/moderate findings, and permits only documented time-bounded
exceptions of at most 30 days with containment and rollback/upgrade planning.

## Accepted decision A63 — State 0–2 security review record

The total review followed `skills/spec-authoring/SECURITY_REVIEW_EVIDENCE.md`.
Accepted decisions below remain authoritative; this record only makes their
coverage and previously unresolved gaps explicit.

### Normative rules

1. Every required security category has one explicit outcome.
2. `UNRESOLVED` categories block State 3 and are not treated as accepted risk.
3. Stable identity references navigate to State 1 semantics; they never prove
   authorization by themselves.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A61, A66, A67; affected: A60, M03, M04, VPS human and service authentication, local agent/service boundary, sync-node boundary
- secrets: APPLICABLE; references: A60, A61, A66, A67; affected: M04, synchronization, local agent/service, recovery, and Holded gateway boundaries
- authorization: APPLICABLE; references: A61, A66, source:02_rules_local_upload.md#accepted-decision; affected: M03, M06, M10, M33, exact invoice and source targets
- injection_interpreted_input: APPLICABLE; references: A62; affected: search, agent, OCR, filename, Registry, PresuPro, and Holded inputs
- external_callbacks_webhooks: APPLICABLE; references: A60, A61, source:02_rules_import.md#accepted-decision; affected: M19, M20, M21, VPS synchronization boundary (no inbound webhook is accepted)
- browser_boundary: APPLICABLE; references: A61, A66, A67; affected: local uploader, local OS-delegated interactive context, VPS browser sessions, login, and recovery
- files_artifacts: APPLICABLE; references: A60, A61, A64, A66, source:02_rules_local_upload.md#accepted-decision; affected: M05, M10, M11, upload, storage, processing, and retrieval boundaries
- concurrency: APPLICABLE; references: A65, source:02_rules_import.md#accepted-decision; affected: M10, M11, M21, source attachment, import, and missing-source transitions
- dependencies: APPLICABLE; references: A68; affected: public VPS, document processing, local Backend, agent/MCP runtimes, and integration/gateway runtimes

### Formal invariants

```text
any security category = UNRESOLVED
-> State 3 transition forbidden

stable_entity_id_known
-/> operation_authorized
```

### Required tests

1. `design_lint.py --state 2` resolves every reference in this review.
2. Each `UNRESOLVED` line produces a blocking error.
3. Removing a category or its outcome fails the structural gate.
4. `NOT_APPLICABLE` cannot be introduced without a rationale.

### Consequence

All required State 0–2 security-review categories now have accepted enforceable
outcomes. OQ-008, OQ-009, OQ-010, and OQ-011 are resolved by A67, A64, A65, and
A68 respectively. Subject to structural lint and the ordinary State 2 readiness
checks, the security review no longer blocks transition to State 3.
