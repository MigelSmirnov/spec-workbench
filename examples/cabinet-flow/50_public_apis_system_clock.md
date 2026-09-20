# State 5 — Cabinet Flow system-clock operations

The system clock is the kernel's single injectable source of wall-clock and
monotonic time. It owns neither domain deadlines nor retry, retention, throttling,
lifecycle or authorization policy. All canonical operational timestamps are
KernelInstant M47.

## `public_op:system_clock.now`

### Owner

`module:system_clock` owns the only production read of host wall-clock time and
the exact conversion to KernelInstant M47.

### Callers

The injected clock is called directly by timestamp-owning modules:
`module:access_control`, `module:semantic_vocabulary`,
`module:slot_registry`, `module:trial_corpus`, `module:admission`,
`module:slot_activation`, `module:operation_bindings`,
`module:flow_proof`, `module:flow_registry`,
`module:owner_authority`, `module:operation_invoker`,
`module:run_executor` and `module:value_store`.

The kernel surface, gateways and request DTOs never obtain a current-time value
merely to forward it downstream.

### Inputs

None. No actor, request payload, timezone, offset, candidate timestamp, clock
skew allowance, retry interval or retention period is accepted from a caller.

### Outputs

Exactly one KernelInstant M47:

```text
sample_ns = time.time_ns()      # exactly one production wall-clock sample
epoch_us = sample_ns // 1_000
return KernelInstant(epoch_us=epoch_us)
```

`epoch_us` is a non-negative integer. The canonical result is never a float,
naive/aware `datetime`, local date/time or free-form ISO string. UTC text
rendering is presentation only.

### Observable effect

None. Reading the clock creates no kernel record and advances no domain state.

### Enforces

A25 in full: `time.time_ns()` is the sole production wall-clock primitive and
is used only inside the production implementation of this operation; one
`now()` call samples it exactly once; consumers cannot supply or override
current wall time; no microservice/application timestamp is accepted as,
converted to, synchronized with or compared as KernelInstant M47; consumers
perform their own retry, retention, throttling and lifecycle arithmetic;
elapsed time alone never grants authority, decides an approval, completes a Run
or resolves an unknown outcome.

Local elapsed-duration measurement is not wall time. `sandbox_supervisor` and
`service_transport` obtain it only through `system_clock.monotonic_ns()`.

### Errors

Unavailable, out-of-range or otherwise invalid host clock data is a typed clock
failure. Consumers fail closed for the operation requiring current time; no
epoch zero, cached arbitrary value, local-time conversion or caller-provided
fallback is fabricated.

### State impact

None. The consuming module writes any resulting KernelInstant into the record
or persisted deadline it owns at that module's atomic state transition.

## `public_op:system_clock.monotonic_ns`

### Owner

`module:system_clock` owns the only production read of the host monotonic clock.

### Callers

`module:sandbox_supervisor` and `module:service_transport` use the injected
operation solely to enforce local, non-persisted timeouts.

### Inputs

None. Callers cannot supply a clock, sample, offset or conversion.

### Outputs

Exactly one integer returned unchanged from one `time.monotonic_ns()` sample.
The result is not a KernelInstant and has no meaning across process restart.

### Observable effect

None. The reading creates no record and advances no domain state.

### Enforces

A25: all host clocks are read in one module. Consumers may subtract two readings
to enforce a local timeout, but cannot persist a reading, derive a timestamp,
order domain events or grant authority from elapsed time.

### Errors

Unavailable or non-integer host-clock data is a typed clock failure. No wall
clock or caller value is used as a fallback.

### State impact

None.
