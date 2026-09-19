# State 5 — Cabinet Flow HTTP application construction

## `public_op:http_router.create_http_app`

### Owner

`module:http_router` owns deterministic framework app construction under A22.

### Callers

`module:bootstrap` calls it once after the kernel's startup prerequisites pass.

### Inputs

One process-local HttpGatewayRuntime holding the bound gateway dispatcher,
credential extractor and immutable ReleaseCeilings. No request supplies it.

### Outputs

A FastAPI application with that runtime bound to app state and the six canonical
irregular handlers registered. The application is not yet a listening server.

### Observable effect

Constructs one in-memory app. Bootstrap must install the gateway error boundary
and release schema, remove default documentation routes and check readiness
before the host opens a socket.

### Enforces

Registration matches 70_router_closure.json and 70_router_context.json exactly.
No additional business API, store selector or principal is exposed. Registered
irregular handlers own the full A21/A22 authentication and framing path.

### Errors

Invalid runtime or registration fails startup. No partial app may accept traffic.

### State impact

Only process-local app state; no domain or persisted state changes.

## `public_op:http_gateway.prepare_http_app`

### Owner

`module:http_gateway` owns trusted HTTP listener preparation under A22.

### Callers

`module:bootstrap` calls it after create_http_app and before opening any socket.

### Inputs

The newly constructed FastAPI app with its complete HttpGatewayRuntime.

### Outputs

The same application with the typed framework error boundary and the exact
release OpenAPI installed, and no default docs/openapi endpoints exposed.

### Observable effect

Installs http_framework_error and build_http_openapi, removes only the known
framework documentation routes, disables slash redirection and validates that
the remaining catalogue equals the accepted six method/path/handler bindings.
It also verifies the runtime callables and immutable release ceilings. An
unexpected extra route is an error, not silently removed.

### Enforces

No default validation-detail responses; no anonymous seventh route; no direct
context injection from the body; no serving before complete preparation. The
installed schema must describe the exact operation models despite raw Request
handler signatures.

### Errors

Missing runtime, wrong route binding, extra route, invalid schema or incomplete
error-handler installation fails startup before any request is accepted.

### State impact

Only app configuration. No credential or domain state is created or changed.
