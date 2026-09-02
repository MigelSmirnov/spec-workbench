# State 1 repair — Cabinet status vocabulary and policy row forms

## Status

Accepted closed status vocabularies already named by A01, A02, A04, A05, A08,
A11, A13, and A16, plus the row forms of the declared policy tables served by
the deterministic `data_provider` module. These models define form, not
mutable policy. Runtime code receives the generated enum symbols and typed
rows through the `models` and `data_provider` modules and never receives the
values through an LLM prompt. Every enum is string-valued; record fields that
carry these vocabularies keep their accepted scalar `str` types, exactly as
`SecurityAuditRecord.subject_kind` deliberately did.

## Model M140 — EffectStatus

Values: `prepared`, `committed`, `rejected`, `outcome_unknown`.

### Identity

value

### Identity evidence

The value classifies one A04 M16 effect's lifecycle position. Equal members
are interchangeable; the effect's identity remains its idempotency identity.

## Model M141 — InvoiceLifecycleState

Values: `draft`, `confirmed`, `archived`.

### Identity

value

### Identity evidence

The value classifies one A01 M03 Invoice revision's lifecycle position. Equal
members are interchangeable; Invoice identity remains the Invoice ID and
canonical content hash.

## Model M142 — UploadHandoffStatus

Values: `issued`, `consumed`, `revoked`.

### Identity

value

### Identity evidence

The value classifies one A05 M15 upload handoff's lifecycle position. Equal
members are interchangeable and do not identify a handoff.

## Model M143 — TransferIssuanceStatus

Values: `issued`, `acknowledged`.

### Identity

value

### Identity evidence

The value classifies one A08 M22 issuance's protocol position. Equal members
are interchangeable; issuance identity remains the issuance record identity.

## Model M144 — ReconciliationStatus

Values: `accepted`, `non_complete`, `conflict`, `unknown`.

### Identity

value

### Identity evidence

The value classifies one A08 reconciliation reading of an exact
issuance/receipt pair. Equal members are interchangeable and carry no
lifecycle of their own.

## Model M145 — ComponentReadinessState

Values: `ready`, `not_ready`.

### Identity

value

### Identity evidence

The value classifies one A11/A13 readiness component observation. Equal
members are interchangeable.

## Model M146 — InvoiceRejectionCode

Members with declared safe codes:

- `access_denied` = `invoice.authorization_denied`
- `revision` = `invoice.revision_conflict`
- `validation` = `invoice.validation_rejected`
- `source_custody` = `invoice.source_not_stored`
- `confirmation` = `invoice.confirmation_invalid`
- `not_found` = `invoice.not_found`

### Identity

value

### Identity evidence

The member is the closed safe refusal vocabulary of Invoice operations
(A01/A02/A05). Equal members are interchangeable; a rejection never
identifies the refused entity.

## Model M147 — RuntimeSafeErrorCode

Members with declared safe codes:

- `protected_configuration` = `PROTECTED_CONFIGURATION_UNAVAILABLE`
- `durable_state` = `DURABLE_STATE_UNPROVEN`
- `credential_verifiers` = `CREDENTIAL_VERIFIERS_UNAVAILABLE`
- `private_listener_assumptions` = `PRIVATE_LISTENER_UNSATISFIED`
- `contract_compatibility` = `CONTRACT_INCOMPATIBLE`
- `backup_evidence` = `BACKUP_EVIDENCE_UNAVAILABLE`

### Identity

value

### Identity evidence

The member is the closed A11/A13 safe readiness-failure vocabulary. Equal
members are interchangeable and disclose no protected configuration.

## Model M148 — CapabilityGrantRule

One row of the closed A16 grantable capability catalogue.

Fields: `channel` (str), `capability` (str), `operation` (str).

### Identity

value

### Identity evidence

Rows are compared by their complete field triple; the catalogue itself is the
A16 accepted closed set served as data by the `data_provider` module.

## Model M149 — ProtectedOperatorRule

One row of the closed A16 protected operator capability set.

Fields: `capability` (str), `operation` (str).

### Identity

value

### Identity evidence

Rows are compared by their complete field pair; the set is A16 accepted data
served by the `data_provider` module.

## Model M150 — InvoiceValidationCheckRule

One row of the closed A01 Invoice validation check table.

Fields: `code` (str), `field_path` (str), `formula` (str).

A `field_path` is a dot-separated segment path over the declared invoice
fields. The literal segment `*` iterates the owning tuple — one row targets
every element — and a reported concrete path replaces `*` with the bracketed
element index. The grammar is form; the row values remain data served by the
`data_provider` module.

### Identity

value

### Identity evidence

Rows are compared by their complete field triple; `code` values join the
declared validation issue order.

## Model M151 — EstimateCheckRule

One row of the closed A01/A04 estimate validation check table.

Fields: `code` (str), `field_path` (str), `formula` (str).

A `field_path` follows the same grammar as M150: a dot-separated segment path
whose literal `*` segment iterates the owning list — for estimates, the
parsed sections.

### Identity

value

### Identity evidence

Rows are compared by their complete field triple.

## Model M152 — ContentFormatSignatureRule

One row of the closed A05 byte-signature catalogue, flattened to one
signature per row so every row is a stable scalar record.

Fields: `format` (str), `media_type` (str), `offset` (int),
`bytes_hex` (str).

### Identity

value

### Identity evidence

Rows are compared by their complete field quadruple; a format with several
signatures owns several rows.

## Model M153 — CabinetChannel

Values: `plugin`, `browser`, `local_node`.

### Identity

value

### Identity evidence

The value classifies the closed A03/A16 access channel a credential and a
grant are bound to. Equal members are interchangeable; the protected
operator boundary is not a wire channel and has no member.

## Model M154 — ReadinessComponent

Values: `protected_configuration`, `durable_state`, `credential_verifiers`,
`private_listener_assumptions`, `contract_compatibility`, `backup_evidence`.

### Identity

value

### Identity evidence

The member names one A11/A13 readiness aspect; declaration order is the
accepted reporting order. Equal members are interchangeable, and the
matching M147 safe code carries the same member name.

## Model M155 — InvoiceLifecycleUnitOfWork

The narrow A17-rule-2 unit-of-work port of the Invoice lifecycle module: the
ten transaction, card-reference, custody-read, and manifest/working-set
operations its atomic confirmation edge uses, plus the M156 effect-journal,
M157 card-commit, and M158 revision-read sub-surfaces its retained
collaborators exercise inside the same transaction. The wide persistence port
satisfies it structurally; the lifecycle module receives only this surface,
and no collaborator it calls requires more.

### Identity

value

### Identity evidence

An interface carries no instance identity; the composition passes the one
operation-scoped unit of work opened by the factory.

## Model M156 — EffectJournalUnitOfWork

The narrow A17-rule-2 unit-of-work port the effect journal requires from its
caller's already active transaction: reservation lock, effect and idempotency
reads, reservation insert, and result binding — the exact five operations the
A04 begin/commit mechanics name. The wide persistence port and M155 satisfy
it structurally; the journal never begins, commits, or rolls back.

### Identity

value

### Identity evidence

An interface carries no instance identity; the caller passes its one active
operation-scoped unit of work.

## Model M157 — CardRevisionCommitUnitOfWork

The narrow A17-rule-2 unit-of-work port the caller-owned Card commit
requires: card lock, current-selector read, immutable revision append, and
current-selector insert/move — the exact five operations the A01 revision
mechanics name. The wide persistence port and M155 satisfy it structurally;
the commit helper never begins, commits, or rolls back.

### Identity

value

### Identity evidence

An interface carries no instance identity; the caller passes its one active
operation-scoped unit of work.

## Model M158 — InvoiceRevisionReadUnitOfWork

The narrow A17-rule-2 unit-of-work port of the catalogue's exact-revision
read: current-selector read, stored revision read, and available working-set
listing — the three operations one Invoice view assembly uses. The wide
persistence port and M155 satisfy it structurally; the read never mutates or
closes the transaction.

### Identity

value

### Identity evidence

An interface carries no instance identity; the caller passes its one active
operation-scoped unit of work.

## Model M159 — InvoiceLifecycleUnitOfWorkFactory

The narrow factory the lifecycle composition retains: one operation opens one
fresh inactive M155 unit of work. The wide persistence factory satisfies it
structurally; no second implementation exists.

### Identity

value

### Identity evidence

An interface carries no instance identity; the composition passes the one
persistence factory.
