# State 2 — Cabinet Flow entrance, surface, secrets and security review

## Accepted decision A21 — one owner, and agents only under delegation

### Normative rules

1. An installation has exactly one OwnerPrincipal M16. No operation creates a
   second principal, a role or an invitation.
2. Every surface request is authenticated on its channel and resolved to the
   owner or to exactly one active AgentDelegation M17 before anything else is
   evaluated. A request that resolves to neither is refused without revealing
   whether any named record exists.
3. The owner authenticates by a means distinct from every agent channel
   credential. Possession of an agent credential never yields owner authority,
   and an agent cannot relay, simulate or carry an owner decision.
4. Owner-only actions are: accepting a vocabulary proposal, accepting a binding
   version, activating an effectful flow, deciding an approval, granting and
   revoking, withdrawing a protected trial case, issuing and revoking a
   delegation, cancelling a run, and suspending the owner principal. No
   delegation field can express any of them.
5. A delegation with `may_author` false may inspect, run flows and read traces.
   With `may_author` true it may also author contracts, implementations, trial
   cases, binding proposals, flows and vocabulary proposals, request trial and
   activate admitted implementations.
6. An agent's assertion is never evidence. A proof, an admission, an approval
   and a reconciliation each come from their own source and cannot be supplied
   by a caller.
7. Every record of an action carries the ActorRef M18 resolved at the entrance.
   Owner and agent are distinguishable in every record, permanently.
8. Revoking a delegation takes effect before the next request. Runs it started
   continue; it starts nothing new.
9. Repeated failed authentication on a channel is throttled per credential and
   reported to the owner. Throttling never locks the owner out through an agent
   channel's failures.

### Formal invariants

```text
request_evaluated -> resolved_to(owner) XOR resolved_to(one_active_delegation)

owner_only_action -> actor_kind = owner
agent_credential -/> owner_authority

record_of_action -> actor_ref_present AND actor_kind IN {owner, agent, kernel}
```

### Required tests

1. Each owner-only action attempted under a full authoring delegation is
   refused.
2. An unauthenticated request for an existing and for a non-existing run yields
   the same refusal.
3. A revoked delegation's next request is refused; its waiting run completes
   after the owner approves.
4. A request body claiming `actor_kind: owner` on an agent channel is recorded
   as that agent.
5. Failed authentication on the agent channel does not throttle the owner's
   means of access.

### Consequence

There is one trusted entrance. Everything an agent does is done in the owner's
name, visibly, and nothing an agent does can become the owner's decision.

## Accepted decision A22 — the surface is fixed, generic and typed

### Normative rules

1. The kernel exposes one closed set of named, typed operations, identical in
   meaning over `mcp` and `http_api`:
   inspect vocabulary, slots, contract versions, implementations, trial
   evidence, bindings, flows, proofs, runs and traces; author a slot, contract
   version, implementation, trial case, binding proposal, flow version and
   vocabulary proposal; request trial; activate an implementation; create a run;
   and, for the owner, the actions of A21 rule 4.
2. Authoring a function, a flow or a binding never adds, removes or changes a
   surface operation. A schema client can create a run of a flow authored after
   its schema was published.
3. Every request and response has a declared bounded schema. An unknown
   operation name, an unknown field or an oversized payload is refused. There is
   no operation that takes an arbitrary operation name, query, path, command or
   code to execute outside A06.
4. Submitted code is stored and executed only in the sandbox. It is never
   evaluated, imported, formatted or linted inside the kernel process.
5. Text supplied by an agent — purposes, rationales, statements, failure
   context — is data. It is never interpreted as an instruction, a template or a
   query by the kernel, and is shown to the owner marked as agent-supplied and
   separate from kernel-generated statements.
6. Listing operations are bounded and paginated and apply A03 to every value.
7. For authoring or repair the agent is given one slot's contract, serving
   implementation, corpus and recent evidence. For composition it is given
   contracts, binding versions and the vocabulary, not implementation bodies.
8. The surface never returns a credential, a host path, a manifest secret
   reference's target or a stack trace.

### Formal invariants

```text
surface_operations = closed_set   (fixed by kernel release)
authored_artifact -/> changes(surface_operations)

request -> declared_schema AND bounded
agent_text -> data   (never instruction, template or query)
submitted_code_executed -> only_in_sandbox
```

### Required tests

1. A flow authored after the `http_api` schema was published is run through that
   unchanged schema.
2. Unknown operation names, unknown fields and oversized bodies are refused.
3. A purpose string containing template or query syntax is stored and shown
   verbatim and changes no behavior.
4. Submitting syntactically invalid code is accepted as bytes, fails in trial,
   and never raises inside the kernel process.
5. A composition request returns no implementation body.
6. No response contains a credential, host path or stack trace, including on
   internal error.

### Consequence

The kernel grows without its surface changing, which is what lets a client with
a frozen schema use what was written a minute ago.

## Accepted decision A23 — secrets and targets belong to the installation

### Normative rules

1. Credentials for microservice instances and for agent channels live only in
   protected host configuration of the installation. They are absent from the
   operational store, from every record of State 1, from traces, previews,
   errors, process arguments and the repository.
2. Records refer to a credential only by a binding reference that is meaningless
   outside the host. The kernel resolves it at invocation time and the resolved
   value never leaves the invoking component.
3. A function never receives a credential: its environment has no environment
   variables and its inputs are typed values that crossed a proven edge. A port
   cannot be typed to carry a credential, and the vocabulary has no term for
   one.
4. The installation selects one manifest instance per service. The
   ServiceTarget M39 is resolved at run creation and recorded. No request
   parameter, flow field or binding field selects an instance.
5. An installation whose targets include a `production` instance refuses to
   target a `disposable_rig` or `local_dev` instance of another service in the
   same run, and the reverse. Mixed targets are refused at start-up.
6. Invocation uses exactly the channel, base address and required headers the
   manifest declares for the selected instance, over an authenticated transport
   where the instance offers one. A redirect to another host is not followed.
7. A service's response is untrusted input: it is bounded in size and time and
   validated against the binding's output ports before any of it is used.
8. The kernel's releases pin the exact versions of the kernel's dependencies and
   of every SandboxRuntimeRevision's libraries. A runtime revision's content
   never changes after release; a vulnerable library is answered by a new
   revision and by withdrawing the old one from new contract versions.

### Formal invariants

```text
credential IN {store, record, trace, preview, error, argv, repository} -> never
function_environment.credentials = empty

run.service_target -> resolved_at_creation AND from_installation_only
targets_mixed(production, non_production) -> start_refused

service_response_used -> bounded AND validated_against_output_ports
```

### Required tests

1. A canary credential configured for a service appears in no record, trace,
   preview, error or log after a run that used it.
2. A request naming another instance is refused; the run reaches the configured
   instance.
3. An installation configured with a production instance of one service and a
   rig of another refuses to start.
4. A service response that redirects to another host, exceeds the size bound or
   violates the output ports concludes the node in failure with nothing used.
5. A released runtime revision's image digest is verified before each
   execution; a mismatch refuses execution.

### Consequence

What the kernel can reach and with what secret is decided once, on the host, by
the person who installs it, and cannot be changed from inside a conversation.

## Accepted decision A24 — complete security review for States 0–2

### Normative rules

The review covers every actor and boundary accepted in State 0: the owner, the
delegated agents on two channels, agent-authored code, the microservices the
kernel invokes, and the host that holds the installation. All nine required
categories are applicable and each is answered by enforceable decisions.

The kernel has no browser surface of its own. The category is nevertheless
applicable, because the `http_api` channel is reachable by web clients and
because agent-supplied text is shown to the owner; A22 governs both.

### Formal invariants

```text
State_2_security_gate_pass
<-> every_required_category = APPLICABLE
    AND every_category_references_accepted_decision
    AND no_security_open_question
```

### Required tests

1. The deterministic State 2 lint accepts exactly one complete review record.
2. Every reference resolves to an indexed State 2 decision.
3. No required category is silent or unresolved.

### Consequence

State 3 is blocked if any referenced decision is removed, becomes unresolved or
loses its enforceable boundary.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A21, A23; affected: M16, M17, M18, owner access, mcp channel, http_api channel
- secrets: APPLICABLE; references: A06, A19, A23; affected: M17, M38, M39, M41, host configuration, traces, previews, errors
- authorization: APPLICABLE; references: A01, A10, A11, A12, A13, A21; affected: M16, M17, M29, M30, M37, M42, M43, M45
- injection_interpreted_input: APPLICABLE; references: A02, A06, A17, A22; affected: M23, M32, M34, M35, agent-supplied text, submitted code, flow definitions
- external_callbacks_webhooks: APPLICABLE; references: A10, A14, A15, A23; affected: M28, M30, M41, M44, outbound service invocation and untrusted service responses
- browser_boundary: APPLICABLE; references: A03, A22; affected: http_api channel, owner-facing previews and statements
- files_artifacts: APPLICABLE; references: A02, A05, A06, A07, A20, A26; affected: M13, M22, M23, M24, M38, M46, M48, code bytes, sandbox scratch, run spool, backups
- concurrency: APPLICABLE; references: A09, A12, A14, A17, A18, A25; affected: M27, M40, M41, M42, M44, M47
- dependencies: APPLICABLE; references: A06, A23, A25, A26; affected: M22, M47, M48, kernel release, sandbox runtime libraries, wall-clock and monotonic time primitives

## Accepted decision A26 — one release owns every global safety ceiling

### Normative rules

1. ReleaseCeilings M48 is the only source of kernel-global maximum resource and
   payload sizes. The exact release-v1 values are the values recorded in M48;
   no module defines a second default.
2. `module:installation` reads the immutable record from the running kernel
   release during startup. `module:bootstrap` injects that same value object
   into every consumer. No request, flow, contract, manifest or environment
   variable may raise a ceiling.
3. ResourceBounds M21 includes wall time, CPU time, memory, aggregate output,
   scratch bytes and process count. An authored contract may request less than
   or equal to each corresponding sandbox ceiling and never more.
4. Implementation code, StoredValue content, trial fixture files, one run-spool
   file and the total live spool of one run are each refused before exceeding
   their M48 byte ceiling. No over-limit input or output is truncated into a
   valid value.
5. The fixed surface accepts no request above
   `surface_request_bytes_max`. All caller-authored bounded text is at most
   `bounded_text_bytes_max`; scrubbed failure detail is at most
   `failure_detail_bytes_max`.
6. List operations default to `page_size_default` and refuse a requested page
   size above `page_size_max`; pagination never changes authorization or
   disclosure filtering.
7. One transport exchange may enforce a lower manifest/binding-specific
   timeout, but never a wall timeout above `transport_timeout_ms_max`. Local
   elapsed measurement follows A25 and therefore uses only
   `time.monotonic_ns()`.
8. A new release may change the ceilings, but existing contract versions and
   execution evidence keep the exact ResourceBounds/release identity they
   already pinned. A release change never rewrites historical evidence.

### Formal invariants

```text
global_safety_ceiling -> from(ReleaseCeilings M48)

authored_resource_bound <= release_ceiling
request_size <= surface_request_bytes_max
bounded_text_size <= bounded_text_bytes_max
failure_detail_size <= failure_detail_bytes_max
page_size <= page_size_max
transport_timeout_ms <= transport_timeout_ms_max

limit_exceeded -> explicit_refusal AND no_truncation
caller_or_environment_override(release_ceiling) -> forbidden
```

### Required tests

1. Every M21 field exactly at its release ceiling is accepted and one unit over
   is refused before sandbox start.
2. Code, value, fixture, spool-file and run-total sizes at the ceiling are
   accepted; one byte over is refused without partial persistence.
3. An oversized surface body, text field, failure detail or page-size request is
   refused with its closed typed error.
4. A transport-specific timeout below the release ceiling is enforced; an
   attempt to configure a larger timeout is clamped/refused before send.
5. Restart under the same release yields byte-for-byte equal ReleaseCeilings;
   changing a host environment variable cannot alter any field.
6. A later release with different ceilings does not alter recorded ResourceBounds
   or the interpretation of an earlier NodeExecution.

### Consequence

Every generator sees one closed set of resource and payload maxima. Limits are
release facts, not local implementation choices.

