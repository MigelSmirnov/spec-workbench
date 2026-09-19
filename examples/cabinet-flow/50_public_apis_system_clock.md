# State 5 — Cabinet Flow system-clock operations

The system clock is the kernel's single injectable source of current wall-clock
time. It owns neither domain deadlines nor retry, retention, throttling or
authorization policy. Consumers receive one normalized UTC instant and perform
their own deterministic arithmetic and decisions.

## `public_op:system_clock.now`

### Owner

`module:system_clock` owns reading and normalizing the host's current time into
the kernel's one UTC representation.

### Callers

`module:access_control` calls it when evaluating authentication throttling and
recording authentication-time evidence.
`module:kernel_surface` calls it when a surface-owned mutation needs one
authoritative request/decision timestamp to pass to the deep module that owns
the resulting record.
`module:run_executor` calls it when evaluating persisted retry/back-off
deadlines for pending Runs.
`module:value_store` calls it when deciding which retained content has reached
its A20 expiry deadline.

### Inputs

None. No actor, request payload, timezone, offset, candidate timestamp, clock
skew allowance, retry interval or retention period is accepted from a caller.

### Outputs

One normalized, timezone-explicit UTC instant at the precision supported by the
kernel's persisted timestamp representation. The result contains no host-local
timezone, locale or monotonic-process counter.

### Observable effect

None. Reading the clock creates no kernel record and advances no domain state.

### Enforces

There is exactly one source of "current time" inside the kernel; callers cannot
supply or override wall-clock time; host-local time is normalized to UTC before
return; a consumer that needs throttling, back-off, retention or lifecycle
arithmetic applies its own accepted rule to the returned instant; elapsed time
alone never grants authority, decides an approval, completes a Run or turns an
unknown outcome into a known one.

### Errors

Unavailable, malformed, out-of-range or non-normalizable host time is a typed
clock failure. Consumers must fail closed for the operation that required
current time; no epoch, zero, cached arbitrary value or caller-provided fallback
is fabricated.

### State impact

None. Any timestamp persisted in an ActorRef-related security record,
VocabularyProposal, activation, approval, Run, retention decision or other
owned record is written by that record's owning module, not by the clock.
