# State 5 — Cabinet Flow canonical-digest operations

The canonical digest is the one place where defining content becomes a name.
It knows no record kind, selects no field and refuses no identity: those belong
to `module:identity`. Both operations are pure, deterministic and free of
observable effect.

## `public_op:canonical_digest.digest_defining_content`

### Owner

`module:canonical_digest` owns the canonical byte form of a typed value and the
digest computed over it.

### Callers

Only `module:identity`, once per content-identified record it names.

### Inputs

One typed defining-content value built by `module:identity` for exactly one
record kind. It carries the record-kind and canonicalization-version markers
and only defining fields. It carries no byte payload, no timestamp, no author
and no rationale.

### Outputs

One lowercase hexadecimal digest.

### Observable effect

None.

### Enforces

Field order of the typed value never influences the digest; the order of a
sequence always does. Equal typed values yield equal digests across processes,
hosts and kernel restarts. Non-ASCII text is preserved rather than escaped.

### Errors

A value that cannot be serialized canonically is refused; nothing is digested
partially.

### State impact

None.

## `public_op:canonical_digest.digest_bytes`

### Owner

`module:canonical_digest` owns the digest of a raw byte sequence.

### Callers

Only `module:identity`, for implementation code bytes, fixture bytes and the
canonical bytes of a stored value.

### Inputs

One exact byte sequence. It is never decoded, framed, trimmed or normalized.

### Outputs

One lowercase hexadecimal digest of exactly those bytes.

### Observable effect

None.

### Enforces

Byte-exact repeatability: the empty sequence, embedded zero bytes and bytes
that are not valid text are all digested as they stand.

### Errors

None of its own; size ceilings are enforced by the caller before the bytes
arrive.

### State impact

None.
