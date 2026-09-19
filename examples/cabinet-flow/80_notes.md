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
serve_http: [VALIDATION_ERROR] MUST translate a KernelRefusal raised by resolve_actor, authorize_action or the selected kernel_surface operation into a refusal envelope whose error_code is the refusal code and whose error_reason is the refusal reason; the exception's string form, arguments and cause MUST never be read into the envelope.
serve_http: [RULE_REFERENCE] MUST accept a KernelRefusal only when its code is a member of = rules.refusal.codes; any other raised exception or an unlisted code MUST become the declared internal refusal with no reason.
serve_http: [TEST_EVIDENCE] A denied owner action by an authenticated agent MUST invoke no domain operation; an accepted catalogue call MUST receive the resolved actor once and preserve the owning module's result without inventing evidence.

## Response formatting

format_http_response: [RULE_REFERENCE] For a successful result MUST select the unique row in = rules.http_transport.operations whose result_model matches its validated result type and require the row's success_status; an ambiguous result binding or a mismatched supplied status MUST yield the declared internal refusal.

format_http_response: [RULE_REFERENCE] MUST match the envelope error code to exactly one row in = rules.http_transport.errors and obtain both status and fixed message from that row.
format_http_response: [RULE_REFERENCE] MUST use = rules.http_transport.unknown_error for unrecognized error codes, invalid envelope combinations and serialization failures.
format_http_response: [RULE_REFERENCE] For a refusal naming a reason MUST select the unique row in = rules.refusal.reasons whose reason matches and require that row's code to equal the envelope error code, then take error_explanation from that row's explanation; a reason with no row or a row naming another code MUST yield the declared internal refusal with no reason.
format_http_response: [RULE_REFERENCE] MUST remove error_reason and error_explanation when the error code is listed in = rules.refusal.unexplained_codes, so every authentication refusal stays indistinguishable on the wire.
format_http_response: [SECURITY_BOUNDARY] error_explanation MUST be only the catalogue text of the named reason; a module-composed sentence, a submitted value, a record identity and an exception string MUST never reach error_explanation.
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
build_http_openapi: [SCHEMA_CONSTRAINT] The shared error-envelope schema MUST declare error_reason and error_explanation as optional bounded text beside error_code and error_message, with error_reason constrained to the reasons in = rules.refusal.reasons.
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

# State 7 — Identity notes

## Content identity

identify_contract_version: [RULE_REFERENCE] MUST take record_kind from = rules.identity.record_kind.contract_version and canonicalization_version from = rules.identity.canonicalization_version.
identify_contract_version: [FIELD_ASSIGNMENT] MUST build exactly one ContractVersionDefiningContent carrying slot_id, input_ports, output_ports, resource_bounds and runtime_revision_ref unchanged from the arguments; the given order of each port sequence MUST be preserved because port order is defining.
identify_contract_version: [ORCHESTRATION] MUST call digest_defining_content exactly once with that value and MUST perform no serialization or hashing of its own.
identify_contract_version: [RETURN_SHAPE] MUST return ContractVersionIdentity whose contract_version_id is the returned digest and whose canonicalization_version equals the value placed in the defining content.
identify_contract_version: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when slot_id or runtime_revision_ref is empty, and with reason identity_duplicate_port_id when two ports of one sequence share a port_id; nothing is digested after a refusal.
identify_contract_version: [TEST_EVIDENCE] Two calls differing only in one resource bound MUST return different identities; two calls with equal arguments MUST return equal identities in separate processes.

identify_implementation: [RULE_REFERENCE] MUST take record_kind from = rules.identity.record_kind.implementation and canonicalization_version from = rules.identity.canonicalization_version.
identify_implementation: [CONFIG_REFERENCE] MUST compare the byte length of code_bytes with = config.release_ceilings.implementation_code_bytes_max before naming them and raise KernelRefusal with reason identity_content_above_ceiling whose code is that reason's code in = rules.refusal.reasons when it is larger.
identify_implementation: [ORCHESTRATION] MUST call digest_bytes exactly once with code_bytes, place the returned name in code_digest of one ImplementationDefiningContent together with contract_version_ref and entry_point unchanged, and then call digest_defining_content exactly once with that value.
identify_implementation: [SECURITY_BOUNDARY] MUST treat code_bytes only as bytes to be named: the code MUST never be decoded, imported, compiled, formatted or executed, and code_bytes MUST never become a field of the defining content.
identify_implementation: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when contract_version_ref or entry_point is empty or code_bytes is empty.
identify_implementation: [RETURN_SHAPE] MUST return the digest returned by digest_defining_content unchanged.
identify_implementation: [TEST_EVIDENCE] Equal bytes under one contract version and entry point MUST yield one identity; a different entry point or contract version MUST yield another; bytes that are not valid UTF-8 MUST be named without error.

identify_trial_case: [RULE_REFERENCE] MUST take record_kind from = rules.identity.record_kind.trial_case and canonicalization_version from = rules.identity.canonicalization_version.
identify_trial_case: [ORCHESTRATION] MUST project every element of inputs, and of expected_outputs when it is present, through defining_value_ref in the given order, build one TrialCaseDefiningContent with contract_version_ref and protected_classification unchanged, and call digest_defining_content exactly once.
identify_trial_case: [FIELD_ASSIGNMENT] MUST keep absent expected_outputs absent and an empty expected_outputs empty; the two MUST never be merged.
identify_trial_case: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when contract_version_ref or protected_classification is empty or inputs is empty.
identify_trial_case: [RETURN_SHAPE] MUST return the digest returned by digest_defining_content unchanged.
identify_trial_case: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_duplicate_port_id when two values of inputs, or two values of expected_outputs, are bound to one port_id.
identify_trial_case: [TEST_EVIDENCE] Changing one input value digest or the port a value is bound to MUST change the identity; changing only the retention class or disclosure class of a StoredValue MUST NOT change it.

identify_binding_version: [RULE_REFERENCE] MUST take record_kind from = rules.identity.record_kind.binding_version and canonicalization_version from = rules.identity.canonicalization_version.
identify_binding_version: [ORCHESTRATION] MUST pass idempotency_key_ports, preconditions and preview_ports each through canonical_string_set, build one BindingVersionDefiningContent with manifest_operation_ref, input_ports, output_ports, effect_class, replay and outcome_read_binding_ref unchanged, and call digest_defining_content exactly once.
identify_binding_version: [DETERMINISM_OR_ORDERING] The given order of input_ports and output_ports MUST be preserved; the three name collections MUST take only the order canonical_string_set returns.
identify_binding_version: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when effect_class or replay is empty, and with reason identity_duplicate_port_id when two ports of one sequence share a port_id.
identify_binding_version: [RETURN_SHAPE] MUST return the digest returned by digest_defining_content unchanged.
identify_binding_version: [TEST_EVIDENCE] Permuting preconditions MUST NOT change the identity; changing effect_class, replay or one port MUST change it.

identify_flow_version: [RULE_REFERENCE] MUST take record_kind from = rules.identity.record_kind.flow_version and canonicalization_version from = rules.identity.canonicalization_version.
identify_flow_version: [ORCHESTRATION] MUST call canonical_flow_graph once with nodes, edges and constants, build one FlowVersionDefiningContent from flow_id, flow_inputs, flow_outputs and the three returned sequences, and call digest_defining_content exactly once.
identify_flow_version: [DETERMINISM_OR_ORDERING] The given order of flow_inputs and flow_outputs MUST be preserved; nodes, edges and constants MUST take only the order canonical_flow_graph returns, never request order.
identify_flow_version: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when flow_id is empty or nodes is empty.
identify_flow_version: [RETURN_SHAPE] MUST return the digest returned by digest_defining_content unchanged.
identify_flow_version: [TEST_EVIDENCE] Permuting nodes, edges or constants in the request MUST NOT change the identity; changing one constant value, one guard or one pinned version MUST change it; changing only a constant's explanation MUST NOT.

digest_value: [RULE_REFERENCE] MUST take record_kind from = rules.identity.record_kind.stored_value and canonicalization_version from = rules.identity.canonicalization_version.
digest_value: [CONFIG_REFERENCE] MUST compare the byte length of canonical_value_bytes with = config.release_ceilings.stored_value_bytes_max before naming them and raise KernelRefusal with reason identity_content_above_ceiling whose code is that reason's code in = rules.refusal.reasons when it is larger.
digest_value: [ORCHESTRATION] MUST call digest_bytes exactly once with canonical_value_bytes, place the returned name in content_digest of one StoredValueDefiningContent together with value_schema_ref and semantic_term_revision_ref unchanged, and call digest_defining_content exactly once.
digest_value: [FIELD_ASSIGNMENT] An absent semantic_term_revision_ref MUST stay absent in the defining content and MUST never be replaced by empty text.
digest_value: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when value_schema_ref is empty.
digest_value: [RETURN_SHAPE] MUST return the digest returned by digest_defining_content unchanged.
digest_value: [TEST_EVIDENCE] Equal bytes under two value schemas MUST yield different digests; an absent term revision and an empty one MUST NOT be interchangeable.

## Hidden identity mechanisms

canonical_string_set: [DETERMINISM_OR_ORDERING] MUST return the given names in ascending order of their Unicode code points, comparing whole strings, with no case folding, trimming or normalization.
canonical_string_set: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_duplicate_name_in_set whose code is that reason's code in = rules.refusal.reasons when one name occurs twice, and with reason identity_defining_field_missing when a name is empty.
canonical_string_set: [RETURN_SHAPE] MUST return a tuple; an empty input MUST return an empty tuple.

canonical_flow_graph: [DETERMINISM_OR_ORDERING] MUST order nodes by ascending node_id and constants by ascending constant_id, comparing Unicode code points of whole strings.
canonical_flow_graph: [DETERMINISM_OR_ORDERING] MUST order edges by ascending value of digest_defining_content applied to each edge, because an edge has no identifier of its own.
canonical_flow_graph: [FIELD_PROJECTION] MUST project every FlowConstant to one DefiningFlowConstant carrying constant_id, semantic_term_revision_ref and value unchanged; the constant's explanation MUST be left out.
canonical_flow_graph: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_duplicate_graph_member whose code is that reason's code in = rules.refusal.reasons when two nodes share a node_id, two constants share a constant_id or two edges have equal digests.
canonical_flow_graph: [RETURN_SHAPE] MUST return the ordered nodes, the ordered edges and the ordered projected constants, in that position order, changing no node and no edge.

defining_value_ref: [FIELD_PROJECTION] MUST return one DefiningValueRef carrying port_value.port_id together with value_digest, value_schema_ref and semantic_term_revision_ref of port_value.value unchanged; carriage, size, media_type, disclosure_class, retention_class and held_until MUST be left out.
defining_value_ref: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_trial_value_not_stored whose code is that reason's code in = rules.refusal.reasons when port_value.value is a SourceReference rather than a StoredValue, and with reason identity_defining_field_missing when port_value.port_id is empty.
defining_value_ref: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when value_digest or value_schema_ref is empty.

## Text admission shared by every identity

identify_contract_version: [VALIDATION_ERROR] MUST let a text value that cannot be encoded as UTF-8 surface as KernelRefusal with reason identity_text_not_encodable whose code is that reason's code in = rules.refusal.reasons; text MUST never be repaired, trimmed, case-folded or Unicode-normalized before it is named.

## Minted identity

mint_identity: [RULE_REFERENCE] MUST accept entity_kind only when it is a member of = rules.identity.minted_entity_kinds and raise KernelRefusal with reason identity_unknown_entity_kind whose code is that reason's code in = rules.refusal.reasons otherwise.
mint_identity: [PROVENANCE] MUST draw 128 bits from the operating system's cryptographic entropy source for every call; time, a counter, a label, the installation namespace and request data MUST never contribute entropy.
mint_identity: [RETURN_SHAPE] MUST return entity_kind, installation_namespace and the lowercase hexadecimal rendering of those 128 bits joined by single colons, in that order, so identities of two entity kinds or two installations can never be equal.
mint_identity: [VALIDATION_ERROR] MUST raise KernelRefusal with reason identity_defining_field_missing whose code is that reason's code in = rules.refusal.reasons when installation_namespace is empty or contains a colon, and with reason identity_entropy_unavailable when the entropy source fails; no fallback identity is ever produced.
mint_identity: [FORBIDDEN_ACTION] MUST NOT read or write any record, reserve the identity or check it against stored identities; persistence and collision handling on insert belong to the calling module.
mint_identity: [TEST_EVIDENCE] Two consecutive calls with equal arguments MUST return different identities; an unknown entity kind MUST be refused with no entropy drawn.
