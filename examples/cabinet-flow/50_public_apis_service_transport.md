# State 5 — Cabinet Flow service-transport operations

A25 timer contract: this module does not use wall clock for domain state. Local non-persisted request/response timeout measurement uses only Python `time.monotonic_ns()`; monotonic readings are never persisted as KernelInstant.

The transport performs one bounded exchange with one declared service instance.
It resolves credentials only at send time and reports transport facts without
deciding replay, authorization, outcome semantics or run state.

## `public_op:service_transport.send_request`

### Owner

`module:service_transport` owns construction and execution of one request on
the channel declared by the pinned manifest operation.

### Callers

`module:operation_invoker` calls it after the binding, target, inputs,
authority and replay decision are fixed for one exact operation attempt.

### Inputs

The pinned ServiceTarget and accepted manifest operation; exact request inputs
or a run-spool file reference already validated for the binding; bounded request
metadata; and the credential reference selected by installation policy. The
caller does not provide a raw credential, arbitrary host, redirect target,
timeout override or undeclared channel.

### Outputs

One immutable transport result containing either the bounded response payload
or streamed run-spool file reference, observed status and headers allowed by the
manifest contract, service-instance identity, timing/size evidence, and a send
classification of `definitely_not_sent` or `possibly_sent` for transport
failure. It does not decide whether an operation succeeded semantically.

### Observable effect

Exactly one bounded exchange may be attempted against the pinned service
instance using its declared `http_api`, `mcp` or `operator` channel.
Credentials are resolved immediately before send. A response file is streamed
into `module:run_spool`; an outbound file is streamed from it. No retry is
performed here.

### Enforces

The instance and operation still match the pinned manifest digest; channel and
request framing come only from manifest facts; credentials are never exposed to
the caller or persisted in evidence; redirects cannot cross to another host;
request and response size/time bounds are enforced; file transfer is streaming;
and a transport failure is classified conservatively according to whether the
request might have reached the service.

### Errors

Unknown or stale instance, unsupported channel, missing credential reference,
credential-resolution failure, DNS/connect failure, timeout, TLS/protocol
failure, forbidden redirect, oversized request/response, broken stream and
spool failure are returned as typed transport failures. Any failure after the
send boundary that cannot prove non-delivery is `possibly_sent`.

### State impact

The transport owns no durable business state. It may create or consume one
bounded run-spool file as part of streaming, but invocation evidence, replay
handling, output validation, unknown-outcome reconciliation and run transitions
belong to their owning modules.
