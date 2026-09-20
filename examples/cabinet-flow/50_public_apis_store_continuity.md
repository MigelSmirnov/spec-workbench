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

The host state directory and the installation identity from the loaded
installation facts.

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

## `public_op:store_continuity.advance_effect_counter`

### Owner

`module:store_continuity` owns the StoreContinuity M50 counter.

### Callers

`module:operation_invoker`, inside the unit of work that records an in-flight
EffectAttempt M51, before any send above `read`.

### Inputs

The caller's open unit of work.

### Outputs

The advanced counter, or nothing when effects are closed because the store is
restored.

### Observable effect

The counter of this installation's StoreContinuity grows by one inside the
caller's unit; with effects closed nothing is written.

### Enforces

A30 rules 5 and 7: the counter advances in the same unit as the attempt record;
a restored store advances nothing, so the caller sends nothing.

### Errors

Continuity not opened, a missing StoreContinuity record and a store failure are
errors; closed effects are an answer, not an error.

### State impact

StoreContinuity M50 `effect_counter` plus one, or none.

## `public_op:store_continuity.confirm_continuity`

### Owner

`module:store_continuity` owns the end of a restored state (A30 rule 8).

### Callers

`module:kernel_surface`, for the owner-only decision of that kind.

### Inputs

The resolved owner ActorRef M18 and the owner's own statement that the services
were reconciled.

### Outputs

The StoreContinuity M50 after the decision.

### Observable effect

In one unit of work the counter becomes one more than the larger of the store's
and the host's, effects open, and the owner, instant and statement are
recorded; after commit the host copy is written with the same value.

### Enforces

Only the active owner; only a restored store; the statement is bounded text
and is data, never interpreted.

### Errors

A non-owner actor, a store that is not restored, an empty or oversized
statement and a failed host write are refusals that leave effects closed.

### State impact

StoreContinuity M50 confirmation fields and counter; the host copy.
