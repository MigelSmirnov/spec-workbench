# State 7 — HTTP transport notes

## Deterministic HTTP registration

create_http_app: [ORCHESTRATION] MUST construct the application through the declared deterministic router backend and register exactly the accepted canonical handlers; the returned app MUST remain unserved until prepare_http_app succeeds.
create_http_app: [FIELD_ASSIGNMENT] MUST bind the supplied immutable HttpGatewayRuntime to the backend-declared app-state slot without copying credentials or constructing alternative gateway dependencies.
create_http_app: [TEST_EVIDENCE] Construction with the accepted runtime MUST preserve its identity and register every accepted method, path and handler binding; returning an empty app or opening a socket during construction fails this obligation.
extract_http_bearer: [RULE_REFERENCE] MUST use = rules.http_transport.credential_extractor.header for the credential header source.
extract_http_bearer: [RULE_REFERENCE] MUST use = rules.http_transport.credential_extractor.scheme for the accepted credential framing.
extract_http_bearer: [SECURITY_BOUNDARY] MUST return only the credential material extracted by the deterministic backend and raise HttpCredentialError for missing or invalid framing; extraction MUST confer no identity or authority and MUST reveal no credential in diagnostics.

## Trusted listener preparation

prepare_http_app: [ORCHESTRATION] MUST prepare the existing unserved app, install http_framework_error for framework and unexpected failures, install build_http_openapi as the release schema producer, disable slash redirection and verify the complete route catalogue before returning the same app.
prepare_http_app: [FIELD_PROJECTION] MUST adapt the typed OpenAPI document returned by build_http_openapi to the framework schema callback's JSON representation while retaining field aliases, references and variant constraints.
prepare_http_app: [RULE_REFERENCE] MUST read = rules.http_transport.runtime_slot to locate the injected process-local runtime.
prepare_http_app: [RULE_REFERENCE] MUST use = rules.http_transport.operations to match every application route by its method and path and verify its handler identity.
prepare_http_app: [VALIDATION_ERROR] MUST fail startup when runtime callables or immutable release ceilings are missing, a canonical route is missing or changed, an unexpected route remains, or schema or error-boundary preparation fails; a partially prepared app MUST never be reported ready.
prepare_http_app: [SECURITY_BOUNDARY] MUST remove only the framework-owned documentation endpoints and refuse other unexpected endpoints; preparation MUST expose no anonymous schema endpoint and MUST not create a listener, principal or credential.
prepare_http_app: [TEST_EVIDENCE] A missing route, additional route, substituted handler, absent runtime or failed schema build MUST prevent readiness; a correctly prepared app MUST retain all required canonical routes and bounded error behavior.

## Bounded HTTP framing

handle_http_request: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.failure_categories whose category matches the detected credential, schema, media-type, size or timeout failure, and use that row's code; an unclassified failure MUST use the declared unexpected category.

handle_http_request: [RULE_REFERENCE] MUST use = rules.http_transport.operations to find exactly one operation binding whose operation matches the trusted handler-supplied operation; ambiguous or absent bindings MUST fail before dispatch.
handle_http_request: [CONFIG_REFERENCE] MUST enforce = config.release_ceilings.surface_request_bytes_max against actual streamed bytes before retaining or parsing an oversized body; an absent or understated length header MUST not bypass this bound.
handle_http_request: [CONFIG_REFERENCE] MUST bound body reading by = config.release_ceilings.transport_timeout_ms_max using an asynchronous deadline without introducing a persisted time source.
handle_http_request: [RULE_REFERENCE] MUST obtain the process-local runtime through = rules.http_transport.runtime_slot rather than through request data.
handle_http_request: [SECURITY_BOUNDARY] MUST refuse duplicate authorization headers before invoking the injected extract_http_bearer, use no query, cookie or forwarded identity as credentials, and create the opaque channel credential handle inside the trusted adapter.
handle_http_request: [SCHEMA_CONSTRAINT] MUST refuse compressed input, unsupported media type or charset, duplicate JSON keys, non-finite numbers, malformed JSON, unknown fields and invalid request variants; MUST validate the decoded value against the exact request model selected by the operation binding.
handle_http_request: [FIELD_ASSIGNMENT] MUST build HttpRequestContext with a fresh correlation identifier, the request-scoped opaque credential handle and the actual accepted byte count; MUST build HttpRequestEnvelope with that context, the trusted operation and its validated payload.
handle_http_request: [ORCHESTRATION] MUST await body framing, invoke the injected synchronous serve_http dispatcher once through the framework thread-pool boundary, and call format_http_response on its returned envelope; framing failures MUST cause no dispatcher invocation.
handle_http_request: [VALIDATION_ERROR] MUST map credential and framing failures to their declared bounded refusals and unexpected failures to the declared internal refusal; MUST not reflect submitted values, framework diagnostics or exception strings.
handle_http_request: [SECURITY_BOUNDARY] MUST neither retry dispatch nor authenticate a second time; a disconnect after dispatch MUST not imply rollback or permission to repeat a durable operation.
handle_http_request: [TEST_EVIDENCE] An over-limit stream without a length header, a timed-out stream and malformed credentials MUST produce no dispatch; a valid request MUST preserve its validated payload and invoke the bound dispatcher exactly once off the event loop.

## Authenticated catalogue dispatch

serve_http: [RULE_REFERENCE] MUST use = rules.http_transport.operations to match the internal envelope operation and require the payload model associated with that operation before domain dispatch.
serve_http: [ORCHESTRATION] MUST call resolve_actor with the internal HTTP channel and its trusted credential handle, then authorize_action with the returned actor and the fixed catalogue action, before invoking the selected kernel_surface operation exactly once.
serve_http: [DEPENDENCY_BOUNDARY] Domain dispatch MUST remain confined to inspect, author, request_trial, activate, run_flow and owner_decide; storage, clocks, service invocation and business transitions MUST remain with their existing owners.
serve_http: [SECURITY_BOUNDARY] MUST carry the authenticated ActorRef into the selected operation; local origin, a proxy header, a payload-supplied actor, agent text and a previous request's authorization MUST confer no authority. Owner decisions MUST require the active owner.
serve_http: [RETURN_SHAPE] MUST return HttpResponseEnvelope containing either the matching bounded operation result with absent error fields or a declared refusal with absent result; pending work and unsuccessful trial verdicts MUST remain genuine typed results rather than fabricated transport success or failure.
serve_http: [VALIDATION_ERROR] MUST make no kernel_surface invocation after framing, authentication or authorization refusal; missing, revoked, ambiguous, throttled and channel-mismatched credentials MUST share the public authentication refusal without resource existence disclosure.
serve_http: [TEST_EVIDENCE] A denied owner action by an authenticated agent MUST invoke no domain operation; an accepted catalogue call MUST receive the resolved actor once and preserve the owning module's result without inventing evidence.

## Response formatting

format_http_response: [RULE_REFERENCE] For a successful result MUST select the unique row in = rules.http_transport.operations whose result_model matches its validated result type and require the row's success_status; an ambiguous result binding or a mismatched supplied status MUST yield the declared internal refusal.

format_http_response: [RULE_REFERENCE] MUST match the envelope error code to exactly one row in = rules.http_transport.errors and obtain both status and fixed message from that row.
format_http_response: [RULE_REFERENCE] MUST use = rules.http_transport.unknown_error for unrecognized error codes, invalid envelope combinations and serialization failures.
format_http_response: [SCHEMA_CONSTRAINT] MUST reject envelopes mixing a result with refusal fields or omitting both outcomes; a successful result MUST have its declared result type and absent error fields, while a refusal MUST have no result and a declared error code.
format_http_response: [FIELD_ASSIGNMENT] MUST make the outer HTTP status agree with the validated envelope status and use the fixed catalogue message for a refusal; caller-selected messages and mismatched supplied statuses MUST not become wire authority.
format_http_response: [RETURN_SHAPE] MUST return a framework JSON response containing the validated HttpResponseEnvelope; it MUST preserve the operation result and safe null fields and MUST not serialize an exception, credential handle or host path.
format_http_response: [TEST_EVIDENCE] An unknown error code, a mismatched refusal status and a raw exception message MUST not reach the client unchanged; a pending operation result MUST remain intact inside its successful transport envelope.

## Framework failure boundary

http_framework_error: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.failure_categories whose category describes the detected failure and use its code; framework details MUST not select a category or message.

http_framework_error: [RULE_REFERENCE] MUST use = rules.http_transport.errors to select the bounded public refusal and fixed status/message for a recognized transport or framework failure.
http_framework_error: [RULE_REFERENCE] MUST select = rules.http_transport.unknown_error for unexpected exceptions without consulting exception text or request body content.
http_framework_error: [DEPENDENCY_BOUNDARY] MUST classify framework failures using the framework HTTPException status or RequestValidationError identity, and transport failures using HttpCredentialError or the closed HttpFramingError code; request values and exception text MUST not influence classification.
http_framework_error: [ORCHESTRATION] MUST construct the refusal envelope and pass it to format_http_response; if typed formatting itself fails, MUST return a bodyless internal-error response without invoking any kernel operation.
http_framework_error: [SECURITY_BOUNDARY] MUST discard framework validation details, exception strings and submitted values; handling an error MUST not read a credential, enumerate resources or retry the failed operation.
http_framework_error: [TEST_EVIDENCE] Framework missing-route and unsupported-method failures and an unexpected exception containing a sentinel secret MUST produce bounded refusals with no sentinel; a failing formatter MUST produce a bodyless error rather than success.

## Release schema

build_http_openapi: [RULE_REFERENCE] MUST use = rules.http_transport.operations to enumerate exactly the accepted method/path bindings and select each request model and result model by their declared identities.
build_http_openapi: [RULE_REFERENCE] MUST use = rules.http_transport.errors for declared refusal statuses and the shared bounded error-envelope schema.
build_http_openapi: [SCHEMA_CONSTRAINT] MUST construct the release document from the actual strict request and envelope model schemas, including required credential security and variant constraints; raw Request introspection MUST not erase request bodies or add generic object inputs.
build_http_openapi: [SECURITY_BOUNDARY] MUST exclude runtime callables, credential handles, internal APIs and documentation endpoints from the published schema; schema export MUST not open an unauthenticated network route.
build_http_openapi: [RETURN_SHAPE] MUST return a valid framework OpenAPI document whose operation set exactly matches the accepted route catalogue; missing or unresolved request/result schemas MUST fail startup rather than yield a partial document.
build_http_openapi: [TEST_EVIDENCE] Every accepted route MUST retain its exact request-model constraints in the release schema; an added deep-module endpoint or a missing request schema MUST prevent preparation.

## Canonical HTTP entrypoints

activate_handler: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.operations whose handler identity is activate_handler; the selected operation MUST originate from this release binding, never from the incoming body, query or forwarded identity.
activate_handler: [ORCHESTRATION] MUST asynchronously delegate the received framework request and its selected operation to handle_http_request exactly once and return the produced Response unchanged; activate_handler MUST not add its own authentication, retry or domain policy.
author_handler: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.operations whose handler identity is author_handler; the selected operation MUST originate from this release binding, never from the incoming body, query or forwarded identity.
author_handler: [ORCHESTRATION] MUST asynchronously delegate the received framework request and its selected operation to handle_http_request exactly once and return the produced Response unchanged; author_handler MUST not add its own authentication, retry or domain policy.
inspect_handler: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.operations whose handler identity is inspect_handler; the selected operation MUST originate from this release binding, never from the incoming body, query or forwarded identity.
inspect_handler: [ORCHESTRATION] MUST asynchronously delegate the received framework request and its selected operation to handle_http_request exactly once and return the produced Response unchanged; inspect_handler MUST not add its own authentication, retry or domain policy.
owner_decide_handler: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.operations whose handler identity is owner_decide_handler; the selected operation MUST originate from this release binding, never from the incoming body, query or forwarded identity.
owner_decide_handler: [ORCHESTRATION] MUST asynchronously delegate the received framework request and its selected operation to handle_http_request exactly once and return the produced Response unchanged; owner_decide_handler MUST not add its own authentication, retry or domain policy.
request_trial_handler: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.operations whose handler identity is request_trial_handler; the selected operation MUST originate from this release binding, never from the incoming body, query or forwarded identity.
request_trial_handler: [ORCHESTRATION] MUST asynchronously delegate the received framework request and its selected operation to handle_http_request exactly once and return the produced Response unchanged; request_trial_handler MUST not add its own authentication, retry or domain policy.
run_flow_handler: [RULE_REFERENCE] MUST select the unique row in = rules.http_transport.operations whose handler identity is run_flow_handler; the selected operation MUST originate from this release binding, never from the incoming body, query or forwarded identity.
run_flow_handler: [ORCHESTRATION] MUST asynchronously delegate the received framework request and its selected operation to handle_http_request exactly once and return the produced Response unchanged; run_flow_handler MUST not add its own authentication, retry or domain policy.
