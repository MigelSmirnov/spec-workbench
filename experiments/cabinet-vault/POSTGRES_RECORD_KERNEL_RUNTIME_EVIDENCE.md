# PostgreSQL record kernel — executed runtime evidence

## Status

**PASS — executed on 2026-08-21 against a real PostgreSQL runtime in Termux.**

This evidence applies only to the fingerprint-bound provider and probe runner recorded in `generic_host_provider_verification_v0.yaml`.

It verifies the generic `postgres_record_kernel` provider obligations for:

```text
transactional_record_store
resource_locking
audit_and_provenance
```

It does not verify the other generic host providers and does not make the complete host plan verified.

## Structural preflight

After synchronizing the experimental branch, the focused provider guards executed successfully:

```text
12 passed in 0.64s
```

The focused suite included the provider fingerprint guard and the regression guard for PostgreSQL-text-safe composite advisory-lock identity.

## First runtime execution — useful failure

The first real runtime probe reached PostgreSQL successfully and proved:

```text
RECORD-PROBE-001 PASS
RECORD-PROBE-005 PASS
```

but `RECORD-PROBE-002..004` failed with:

```text
PostgreSQL text fields cannot contain NUL (0x00) bytes
```

The defect was in the provider's composite advisory-lock key. It used an embedded NUL separator before passing the key to PostgreSQL `text` hashing.

This was treated as provider evidence, not an environment failure or a reason to weaken the probe.

The provider was repaired so the composite lock identity is deterministically encoded as PostgreSQL-text-safe JSON text. A regression test proves that control-byte values are escaped and ambiguous string concatenations cannot collide merely by boundary placement.

## Successful rerun

Command shape:

```bash
SPEC_WORKBENCH_TEST_POSTGRES_DSN="host=$PREFIX/tmp port=55432 dbname=postgres user=$(whoami)" \
python experiments/cabinet-vault/tools/postgres_record_kernel_probe.py
```

Observed result:

```text
RECORD-PROBE-001 PASS
  psycopg imported in the selected runtime

RECORD-PROBE-002 PASS
  committed transaction persisted and intentional failure rolled back

RECORD-PROBE-003 PASS
  same resource serialized while unrelated resource remained independently lockable

RECORD-PROBE-004 PASS
  failed transaction exposed neither record nor audit state

RECORD-PROBE-005 PASS
  audit insert persisted while direct UPDATE and DELETE were rejected

overall status: pass
record_probe_exit=0
```

The probe used an isolated generated schema and removed it after execution.

## Proven obligations

### RECORD-PROBE-001 — runtime dependency

`psycopg` imported in the selected runtime. This directly closes the original lost-driver projection failure for this provider execution environment.

### RECORD-PROBE-002 — transaction atomicity

A committed record transition persisted. A later intentional exception inside the transaction rolled back its attempted update, leaving the previously committed version unchanged.

### RECORD-PROBE-003 — exact-resource locking

Two concurrent transactions contending for the same logical resource serialized. A different resource remained independently lockable while the first resource was held. The contender acquired the original resource after release.

### RECORD-PROBE-004 — no partial metadata state

An intentionally failed transaction that attempted both a record mutation and an audit append exposed neither mutation after rollback.

### RECORD-PROBE-005 — append-only audit persistence

Audit insertion persisted. Direct SQL `UPDATE` and `DELETE` of the issued audit row were rejected by the provider-installed database trigger, and the original evidence remained unchanged.

## Disposition

`postgres_record_kernel` may now be marked:

```text
verification.status = PASS
```

for the reviewed implementation/probe fingerprints.

The complete generic host remains blocked because these required providers are still `UNVERIFIED`:

```text
authority_kernel
typed_schema_kernel
local_private_byte_vault
protected_configuration_kernel
```

Do not infer their behavior from the PostgreSQL provider result.
