# Cabinet Flow HTTP transport — global context closure

## Status and authority

Authored on 2026-09-19. Route catalogue and global context are closed as design
artifacts; final router IR is assembled with the official Workbench tool. This
is not evidence that generated application code or a deployed HTTPS entrance
exists. State 7 Notes remains the next authoring layer.

A21 retains sole ownership of owner/agent authentication, A22 owns the fixed
surface and home-server ingress decision, A26 owns resource ceilings and A27
owns durable throttling. The six external operations and their kernel contracts
are unchanged. Two host-only module APIs build and prepare the listener.

## Canonical sources

50_exposure_plan.json owns exposure. 60_contract_plan.json and 60_contracts.json
own all symbols and signatures. 70_router_closure.json owns routes;
70_router_context.json owns deterministic registration wiring.
70_http_transport_closure.json binds routes to their exact existing request and
result models for runtime schema selection and release OpenAPI construction.
60_http_errors.json owns public error data, while 60_exception_taxonomy.json
owns the two transport exception symbols. The later spec assembly must consume
these machine-readable catalogues directly as structured data; they must never
be pasted into an LLM prompt or reconstructed from this prose.

## Framework correction and ownership

The original handlers took HttpRequestContext and a typed request model. A
per-route contract check accepted that shape but does not prove framework
registration. Irregular registration imports the handler directly; it does not
supply a context factory. State 6 now correctly declares the six async handlers
as `(request: Request) -> Response`. Only the framework Request is injected.
The trusted HttpRequestContext is constructed inside the adapter.

http_router is a declared facade whose app factory and bearer extractor are
owned by the deterministic v1 emitter. http_gateway owns bounded asynchronous
framing, envelope formatting, schema construction and framework error handling.
bootstrap constructs the immutable HttpGatewayRuntime from its bound serve_http,
the generated extractor and the same injected ReleaseCeilings value. It calls
create_http_app, then prepare_http_app, and opens the listener only after all
startup checks pass. This avoids an import cycle: http_router imports the six
handlers; http_gateway receives the extractor through runtime injection.

## Request path

Each handler calls handle_http_request with its own fixed catalogue name. The
shared helper rejects any name outside the release catalogue; no URL segment,
query or body field chooses an arbitrary function. It obtains gateway_runtime
from app state, refuses duplicate Authorization headers before extraction, and
uses only the generated Authorization/Bearer extractor. Cookies, query strings
and forwarded identity headers never supply credentials. A framing failure
never becomes a principal.

The adapter reads Request.stream() under an asyncio.timeout deadline derived
from the injected transport_timeout_ms_max. It counts actual bytes and stops
before retaining more than surface_request_bytes_max. Content-Length may cause
an early refusal but cannot waive streaming checks; non-identity content
encoding is refused, so decompression cannot bypass the bound. Only UTF-8
application/json is accepted. Duplicate object keys, non-finite numbers,
invalid JSON, unknown model fields and invalid operation variants are refused.
The accepted operation's strict State 6 model validates the decoded data.
The schema layer owns command/variant consistency; the route does not invent it.

The adapter creates a fresh UUID4 correlation request_id (not a domain entity
identity or wall-clock source) and one non-serializable ChannelCredentialHandle
bound to http_api. It builds HttpRequestEnvelope from that context, the fixed
operation and the validated model. It calls the synchronous runtime dispatcher
through starlette.concurrency.run_in_threadpool once. serve_http resolves the
actor and authorizes the action under A21/A27, then calls the matching
kernel_surface operation once; authentication/authorization failure calls none.
No handler authenticates a second time, fabricates an ActorRef or supplies time.
A client disconnect after dispatch does not roll back a durable action; callers
must inspect recorded state instead of assuming cancellation or replay safety.

## Authentication policy meaning

The context's kernel_actor and kernel_owner policies have principal=null because
v1 generates no principal wrapper for an irregular handler. This is an explicit
lowering fact, not anonymous access. Both paths authenticate inside serve_http;
owner_decide additionally requires the owner. The policies must never be reused
for a new table route. Adding a table route requires a new reviewed principal
resolver and typed credential conversion before the route can be accepted.

The generated bearer extractor only parses a header. Duplicate header checking,
handle construction, authentication and durable throttling retain their stated
owners. HttpCredentialError is mapped to the same public authentication refusal
as invalid/revoked/channel-mismatched credentials and active throttling. No
failure indicates whether an owner, delegation or requested resource exists.

## Response and error path

format_http_response validates HttpResponseEnvelope before serializing it with
JSONResponse. The outer HTTP status equals envelope.status_code. A success is
200, carries the matching typed result and has null error fields. Pending work,
a failed trial or waiting-for-owner remains a result state, not a fabricated
transport failure. A refusal has null result and a code from 60_http_errors.json;
its status and fixed message come only from that catalogue. Unknown error codes,
invalid envelope combinations or serialization failure yield internal_error.
Credentials, raw exception strings and payload fragments are never reflected.

The adapter maps HttpCredentialError and HttpFramingError through the same
formatter. http_framework_error covers framework HTTP errors (404/405), request
validation errors and unexpected exceptions. It discards framework details and
uses only the closed mapping. Invisible/absent domain resources are considered
only after authorization; pre-auth failures stay the uniform authentication
refusal. If typed error formatting itself fails, the callback returns an empty
500. The v1 error_policy is the compatible empty-body fallback, not the normal
wire refusal contract. Neither proxy nor gateway automatically retries calls.

## Startup and schema preparation

prepare_http_app installs the typed framework handlers before the middleware
stack is first built. It disables slash redirection, removes only the framework's
known docs/redoc/openapi routes and refuses any other extra route. It checks the
six exact method/path/handler bindings, the runtime and the immutable ceilings.
It builds the release OpenAPI document using the authoritative operation-model
bindings and the actual strict Pydantic schemas. Raw Request introspection is
not sufficient. The schema describes the required Authorization Bearer header,
the exact request model per operation and the envelope for every declared status.
prepare_http_app adapts the typed OpenAPI return value to the JSON representation
required by app.openapi, retaining field aliases and schema references. The
callback is installed for host-side release export, with no extra
network endpoint. Failure to build or verify any part prevents listening.

## Deployment and evidence limits

One platform reverse proxy terminates HTTPS. Same-host HTTP uses loopback;
containers must provide equivalent isolation without publishing the kernel port.
LAN, VPN, TLS and proxy headers never establish application authority. Relocation
changes installation bindings, not operations or flows. Domain and certificate
selection remain deployment configuration, outside the kernel API.

The framework contract is supported by the official documentation:
https://fastapi.tiangolo.com/advanced/using-request-directly/
https://fastapi.tiangolo.com/advanced/response-directly/
https://fastapi.tiangolo.com/tutorial/handling-errors/
https://www.starlette.io/requests/

The local probe in evidence/ checks actual Request injection, direct Response
status/body preservation and safe framework exception translation with installed
library versions. It does not test the ungenerated kernel, real credentials,
durable throttling, release schema production, TLS or network isolation. The
A22 runtime acceptance cases remain obligations for Notes and generated-code
verification. No Factory emitter was invoked outside Route B.

## State 7 data projection

Before checking or assembling HTTP Notes, run
`python tools/project_http_note_data.py --check` from this case directory.
Without --check the utility regenerates only the derived HTTP data placements
in 60_data_closure.json from the accepted route, wire and error catalogues.
It never duplicates canonical Python signatures or the router backend IR and
never changes a source catalogue. The failure-category/code association in
60_http_errors.json makes the already accepted A22 refusal cases addressable.
Rules under rules.http_transport are data-provider input, not inline prompt
content. The six endpoint bindings and fixed messages remain machine data.

80_notes.md currently covers the fourteen http_gateway/http_router callables.
Other module notes remain outstanding; this is not a complete State 7 handoff.
The whole-spec notes-language command requires global_spec.json, so its final
check remains at assembly. The current authoring gate checks classes, addresses,
consistency and callable coverage against the design artifacts.
