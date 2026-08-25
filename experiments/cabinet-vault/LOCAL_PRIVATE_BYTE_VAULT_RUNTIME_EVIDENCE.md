# Local private byte vault — executed runtime evidence

## Result

`local_private_byte_vault` has executed runtime evidence on the real Termux
filesystem environment used for this experiment.

Final result:

```text
provider_id: local_private_byte_vault
schema_version: spec_workbench_local_private_byte_vault_probe.v0
status: pass
exit_code: 0
```

Executed on 2026-08-21 against the fingerprint-bound provider and probe runner
declared in `generic_host_provider_verification_v0.yaml`.

## First runtime finding

The first filesystem execution exposed a provider portability defect rather than
a product-semantic gap:

```text
AttributeError: module 'os' has no attribute 'link'
```

The initial publication implementation depended on `os.link`, which is not
available in the selected Termux Python runtime. The provider was not promoted
and the failure remained blocking.

Publication was repaired without weakening the accepted byte-vault invariants:

```text
per-content filesystem flock
+ verify any existing final bytes while holding the lock
+ reject conflicting existing content
+ same-filesystem atomic staging -> final rename
+ fsync directories
+ exact reopen/hash/size verification
```

This keeps the provider generic. Cabinet source identity conflict semantics remain
outside the vault and are owned by the capability/record layer under exact
resource locking.

## Successful rerun

The corrected provider produced:

```text
VAULT-PROBE-001 PASS
  caller-visible references were opaque and raw filesystem paths were rejected

VAULT-PROBE-002 PASS
  staged bytes were flushed, reopened, and verified by exact hash and size

VAULT-PROBE-003 PASS
  different bytes could not publish under one content-addressed final reference
  and existing bytes were not overwritten

VAULT-PROBE-004 PASS
  staged committed publication recovered after provider restart and repeated
  recovery converged on the same verified final blob

VAULT-PROBE-005 PASS
  committed publication with neither final nor recoverable staging bytes raised
  a startup-blocking recovery error

VAULT-PROBE-006 PASS
  symlink and non-regular filesystem references failed closed before byte access
```

The probe returned:

```text
status: pass
vault_probe_exit=0
```

## Meaning of the evidence

This evidence is sufficient to promote only `local_private_byte_vault` from
`UNVERIFIED` to `PASS` for its declared generic host requirements:

```text
opaque_source_byte_vault
staged_byte_verification_and_atomic_publication
committed_effect_recovery
```

It does not verify the complete generic host and does not by itself prove a
Cabinet `invoice.source.attach` capability execution. That capability additionally
requires the other selected providers and the Cabinet capability semantics.
