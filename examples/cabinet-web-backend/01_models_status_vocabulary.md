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

### Identity

value

### Identity evidence

Rows are compared by their complete field triple; `code` values join the
declared validation issue order.

## Model M151 — EstimateCheckRule

One row of the closed A01/A04 estimate validation check table.

Fields: `code` (str), `field_path` (str), `formula` (str).

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
