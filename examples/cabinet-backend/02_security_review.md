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

**Status:** UNRESOLVED / BLOCK.

A61 and A66 now separate the authentication boundaries explicitly:

- the public VPS owns human login/session authentication and remote agent/service
  authentication;
- the single-user local interactive baseline may delegate human trust to the
  authenticated operating-system session and therefore has no Cabinet-owned
  local password-recovery flow;
- local agents/services authenticate separately at the private Backend tool
  boundary;
- synchronization uses its own revocable `SyncNodeCredential`.

Credential separation, rotation/revocation, exact-operation authorization, and
finite-lived human sessions are accepted. Product evidence still does not select
the concrete abuse and recovery policy for the public human boundary or the
abuse/replay response policy for machine/service credentials.

Product owner must still decide:

1. for VPS human login, the failed-attempt budget and rate-limit scope (account,
   credential, source, or a defined combination) for brute-force and
   credential-stuffing resistance;
2. the VPS slowdown/temporary-lockout behavior and authorized administrative
   override;
3. who may initiate VPS human-account recovery and what evidence proves control;
4. whether successful VPS recovery revokes all active human sessions and under
   what compromise evidence related agent/service or sync credentials are also
   revoked; and
5. for VPS agent/service, local agent/service, and sync-node credentials, which
   replay/request-abuse signals trigger throttling, temporary disablement, or
   mandatory rotation/revocation.

The local single-user baseline does not require a Cabinet password store or a
Cabinet human recovery mechanism. Until the remaining VPS and machine/service
choices are accepted as enforceable State 2 policy, this category remains a
BLOCK.

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

**Status:** UNRESOLVED / BLOCK.

Cabinet has a public VPS, document-processing paths, a local Backend, and external
integration clients, so externally maintained runtime dependencies are
operationally relevant. Existing product evidence contains no accepted
vulnerability/update policy.

Product owner must decide:

1. who owns the deployed dependency inventory for each Cabinet surface;
2. which advisory source and severity/exploitability threshold blocks a release;
3. the response or remediation window for a detected vulnerability; and
4. who may approve a time-bounded exception and what rollback or containment is
   required.

Until those choices are accepted as State 2 deployment policy, this category
remains a BLOCK.

## Accepted decision A63 — State 0–2 security review record

The total review followed `skills/spec-authoring/SECURITY_REVIEW_EVIDENCE.md`.
Accepted decisions below remain authoritative; this record only makes their
coverage and unresolved gaps explicit.

### Normative rules

1. Every required security category has one explicit outcome.
2. `UNRESOLVED` categories block State 3 and are not treated as accepted risk.
3. Stable identity references navigate to State 1 semantics; they never prove
   authorization by themselves.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: UNRESOLVED; references: A61, A66, OQ-008; affected: A60, M03, M04, VPS human and service authentication, local agent/service boundary, sync-node boundary
- secrets: APPLICABLE; references: A60, A61, A66; affected: M04, synchronization, local agent/service, and Holded gateway boundaries
- authorization: APPLICABLE; references: A61, A66, source:02_rules_local_upload.md#accepted-decision; affected: M03, M06, M10, M33, exact invoice and source targets
- injection_interpreted_input: APPLICABLE; references: A62; affected: search, agent, OCR, filename, Registry, PresuPro, and Holded inputs
- external_callbacks_webhooks: APPLICABLE; references: A60, A61, source:02_rules_import.md#accepted-decision; affected: M19, M20, M21, VPS synchronization boundary (no inbound webhook is accepted)
- browser_boundary: APPLICABLE; references: A61, A66; affected: local uploader, local OS-delegated interactive context, and VPS browser sessions
- files_artifacts: APPLICABLE; references: A60, A61, A64, A66, source:02_rules_local_upload.md#accepted-decision; affected: M05, M10, M11, upload, storage, processing, and retrieval boundaries
- concurrency: APPLICABLE; references: A65, source:02_rules_import.md#accepted-decision; affected: M10, M11, M21, source attachment, import, and missing-source transitions
- dependencies: UNRESOLVED; references: OQ-011; affected: public VPS, document processing, local Backend, and integration clients

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

Cabinet cannot claim State 2 security closure or proceed to State 3 while OQ-008
and OQ-011 remain unresolved. OQ-008 no longer assumes a Cabinet-owned local
human account store; OQ-009 and OQ-010 are closed by A64 and A65, and their
review outcomes are `APPLICABLE`, not inferred `NOT_APPLICABLE`.
