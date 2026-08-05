# Cabinet Backend — Partial Source Package Acceptance

## Status

Accepted clarification for `02_rules.md`.

This rule refines A3. It defines business acceptance semantics only.
Temporary storage, upload chunking, retry intervals, timeout handling, and other
transport details remain implementation concerns.

---

## Accepted decision — partial source package handling

A confirmed Invoice Card and its source files do not have to become visible in
the durable archive as one indivisible transaction.

If one or more expected source files fail to arrive or fail verification, the
default result is an incomplete source package. The missing or invalid file must
not be represented as successfully stored.

### Normative rules

1. A confirmed Invoice Card may be preserved while its Source Package remains
   incomplete.
2. Incomplete transfer does not silently complete the import.
3. Every missing, failed, corrupt, or hash-mismatched source must retain an
   explicit status and provenance.
4. Without an explicit acceptance decision, the invoice remains outside normal
   downstream processing that requires complete source evidence.
5. An authorised actor may explicitly accept the Invoice Card with incomplete
   source evidence under A3.
6. Explicit acceptance records:
   - actor;
   - decision time;
   - reason;
   - Card revision;
   - exact missing or failed source references.
7. After explicit acceptance, the invoice may enter the durable archive with an
   explicit `source_package_status = incomplete`.
8. Incomplete source evidence does not prevent analytical use or Client Portal
   visibility when those workflows do not require originals.
9. An invoice with incomplete source evidence is not eligible for Holded
   publication.
10. Missing source files may be attached later through the authorised local
    attachment operation.
11. A later successful attachment updates source availability and package
    completeness but does not rewrite the immutable accepted Invoice Card.
12. A corrupt file, wrong invoice target, or hash mismatch cannot be converted
    into a successful attachment by the acceptance override.

---

## Formal invariants

For every expected source reference:

```text
exactly one current availability state exists:
available | missing | failed_verification
```

A source may be marked `available` only when:

```text
stored_hash = SHA256(stored_bytes)
and, when expected_hash exists:
stored_hash = expected_hash
```

For every accepted invoice with incomplete source evidence:

```text
source_package_status = incomplete
and explicit_missing_source_acceptance exists
```

Holded publication eligibility requires:

```text
source_package_status = complete
```

---

## Required tests

1. One failed file leaves the Source Package incomplete.
2. A failed file is never represented as available.
3. Without explicit acceptance, the incomplete invoice cannot enter workflows
   that require complete source evidence.
4. Explicit acceptance preserves the invoice with an auditable incomplete state.
5. Holded publication remains blocked while the Source Package is incomplete.
6. A later verified attachment may change the package from incomplete to
   complete.
7. Retrying the same verified attachment is idempotent.
8. A hash mismatch remains a verification failure and cannot be overridden as a
   successful upload.

---

## Consequence

The specification does not require a distributed all-or-nothing transaction
between Card data and every source file.

It requires truthful, deterministic state:

- complete evidence;
- incomplete but explicitly accepted evidence;
- or unaccepted incomplete transfer.

No implementation may treat a partial upload as silent success.
