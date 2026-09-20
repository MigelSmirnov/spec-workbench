# State 5 — Cabinet Flow store-continuity operations

The host keeps, outside the backup unit, a copy of the counter of effects the
store has begun to send. Comparing the two at start is how a store put back from
an older copy is recognized (A30).

## `public_op:store_continuity.open_continuity`

### Owner

`module:store_continuity` owns the host copy of the StoreContinuity M50 effect
counter, kept in the host state directory, outside the data directory.

### Callers

`module:bootstrap`, before the store is opened.

### Inputs

The host state directory from the loaded installation facts.

### Outputs

The counter, or nothing when the host holds no copy.

### Observable effect

The directory is remembered for this process and the host file is read once;
nothing is written.

### Enforces

The file name of `rules.store_continuity`; an unreadable or malformed copy is
reported as an error, never as an absent one.

### Errors

A relative directory, unreadable or malformed copy.

### State impact

None.

## `public_op:store_continuity.record_host_continuity_counter`

### Owner

`module:store_continuity` owns the host copy of the StoreContinuity M50 effect
counter.

### Callers

`module:operation_invoker` after the unit that recorded an in-flight attempt
committed and before the send; `module:owner_authority` when the owner ends a
restored state.

### Inputs

The counter value just committed in the store.

### Outputs

Nothing.

### Observable effect

The host file is replaced atomically and flushed to disk before the call
returns.

### Enforces

The value never decreases except through the owner's decision of A30 rule 8;
a failed write is an error the caller must treat as "not sent".

### Errors

Continuity not opened, a lower value, write or flush failure.

### State impact

None in the kernel store.
