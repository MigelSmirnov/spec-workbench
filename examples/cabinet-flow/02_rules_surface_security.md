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

[witness: workbench:notes]

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

[witness: workbench:router]

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

[witness: workbench:external_contracts]

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

[witness: workbench:notes]

1. The deterministic State 2 lint accepts exactly one complete review record.
2. Every reference resolves to an indexed State 2 decision.
3. No required category is silent or unresolved.

### Consequence

State 3 is blocked if any referenced decision is removed, becomes unresolved or
loses its enforceable boundary.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A21, A23, A27; affected: M16, M17, M18, M49, owner access, mcp channel, http_api channel
- secrets: APPLICABLE; references: A06, A19, A23; affected: M17, M38, M39, M41, host configuration, traces, previews, errors
- authorization: APPLICABLE; references: A01, A10, A11, A12, A13, A21; affected: M16, M17, M29, M30, M37, M42, M43, M45
- injection_interpreted_input: APPLICABLE; references: A02, A06, A17, A22; affected: M23, M32, M34, M35, agent-supplied text, submitted code, flow definitions
- external_callbacks_webhooks: APPLICABLE; references: A10, A14, A15, A23; affected: M28, M30, M41, M44, outbound service invocation and untrusted service responses
- browser_boundary: APPLICABLE; references: A03, A22; affected: http_api channel, owner-facing previews and statements
- files_artifacts: APPLICABLE; references: A02, A05, A06, A07, A20, A26; affected: M13, M22, M23, M24, M38, M46, M48, code bytes, sandbox scratch, run spool, backups
- concurrency: APPLICABLE; references: A09, A12, A14, A17, A18, A25, A28; affected: M27, M40, M41, M42, M44, M47
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

[witness: workbench:closure_gaps]

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

## Accepted decision A27 — authentication throttling is durable and exact

### Normative rules

1. `module:access_control` owns one AuthenticationThrottleState M49 per
   `(credential_binding_ref, channel)`. Credential material is never part of
   the key or record.
2. A failed authentication increments `consecutive_failures` atomically and
   records `last_failure_at` from `system_clock.now`. The exact delay after
   the resulting failure count is:

   ```text
   count 1..4 -> 0 seconds
   count 5    -> 1 second
   count 6    -> 2 seconds
   count 7    -> 4 seconds
   count 8    -> 8 seconds
   count 9    -> 16 seconds
   count >=10 -> temporary block for 900 seconds
   ```

3. On the tenth failure, `blocked_until = now + 900 seconds`. Requests during
   an active block receive the same public authentication refusal, do not
   increment the counter and do not extend the block.
4. After the active block has elapsed, the next authentication attempt is
   evaluated normally. A successful authentication resets
   `consecutive_failures = 0` and clears `blocked_until`.
5. Owner and agent credentials have independent throttle keys. Failures against
   an agent credential can never delay or block the owner's distinct
   credential/channel pair.
6. The throttle state is durable and restored with the operational store.
   Restart never resets a counter or shortens an active block.
7. Delays use KernelInstant M47 for persisted deadlines. Sleeping is not the
   source of truth: a request is allowed or refused by comparing one
   `system_clock.now` value with the durable state.

### Formal invariants

```text
throttle_key = (credential_binding_ref, channel)
credential_value IN AuthenticationThrottleState -> never

failures <= 4 -> delay_seconds = 0
failures = 5 -> delay_seconds = 1
failures = 6 -> delay_seconds = 2
failures = 7 -> delay_seconds = 4
failures = 8 -> delay_seconds = 8
failures = 9 -> delay_seconds = 16
failures >= 10 -> block_seconds = 900

blocked_attempt -/> increments_failure_count
blocked_attempt -/> extends_block
agent_failure -/> owner_throttle_state
restart -/> resets_throttle
```

### Required tests

[witness: workbench:persistence]

1. Counts one through nine produce exactly the delay table above.
2. The tenth failed authentication creates a block exactly 900 seconds after
   the recorded failure instant.
3. Repeated requests during the block return the same refusal without changing
   count or `blocked_until`.
4. Restart halfway through a block preserves the remaining block.
5. A successful authentication after expiry resets the state.
6. Ten failures on an agent credential do not delay the owner's channel.

### Consequence

Authentication abuse control is reproducible across implementations and
restart; no generated access-control module invents thresholds or sleep logic.


## Accepted decision A29 — a presented credential names its binding and proves its secret

### Normative rules

1. A channel credential is presented as one bounded text
   `<credential_binding_ref>.<secret>`: the binding reference is everything
   before the first `.`, the secret is everything after it. A text without a
   `.`, with an empty part, or longer than the release bound for text is a
   malformed credential.
2. The gateways carry the presented text to `module:access_control` unparsed.
   Only `module:access_control` splits it, and only
   `module:installation` knows the secret of a binding.
3. The installation's protected configuration gives every credential binding
   exactly one purpose out of the closed set `owner_channel_authentication`,
   `agent_channel_authentication`, `service_invocation`, and the channel or
   service instance it is valid for. `installation.resolve_credential` refuses a
   binding asked for another purpose or channel exactly as it refuses an unknown
   one.
4. `module:access_control` resolves the named binding for the arriving channel
   at the moment of use, first for `owner_channel_authentication` and, when the
   installation refuses that, for `agent_channel_authentication`, and compares
   the resolved secret with the presented one in constant time.
5. A matching owner binding resolves to the installation's single active
   OwnerPrincipal M16. A matching agent binding resolves to the one
   AgentDelegation M17 that is `active` and carries that binding reference and
   that channel; none or more than one is a refusal.
6. A27 throttling is keyed by the named binding and the channel, and exists only
   for a binding the installation resolved for that channel. An active block
   refuses before any comparison; a wrong secret advances the state; a match
   resets it. A malformed credential and a binding the installation does not
   resolve write nothing.
7. Every failure has the one public refusal of A21 rule 2. The presented text and
   the resolved secret travel only as function arguments and results between the
   gateway, `module:access_control` and `module:installation`; they are never a
   field of a persisted or returned record and never appear in a log, trace,
   preview or error (A23 rule 1).

### Formal invariants

```text
presented = binding_ref "." secret
actor_resolved -> installation_resolved(binding_ref, channel, purpose) AND constant_time_equal(secret)

purpose = owner_channel_authentication -> actor = the_active_owner
purpose = agent_channel_authentication -> actor = the_one_active_delegation(binding_ref, channel)

throttle_state_written -> installation_resolved(binding_ref, channel)
malformed OR unresolved_binding -/> any_write
caller_named_actor_kind OR caller_named_principal -> never
```

### Required tests

[witness: workbench:notes]

1. A well-formed credential with the right secret of the owner binding resolves
   to the owner on its channel and to a refusal on the other channel.
2. A well-formed credential of an agent binding resolves to its one active
   delegation; after revocation the same text is refused.
3. A wrong secret for a known binding advances exactly that binding's throttle
   state; ten of them block it without touching the owner's state.
4. A malformed text and an unknown binding reference are refused and leave the
   store unchanged.
5. A presented text that names `owner` anywhere in its content yields nothing:
   only the binding the installation resolves decides the actor.

### Consequence

Who is asking is decided by a secret the host holds and a binding the owner
issued, never by anything the caller says about itself; the generated entrance
has nothing left to invent.

## Accepted decision A32 — value bytes and run spool are private files below the installation data root

### Normative rules

1. `module:value_store` keeps bytes below the installation `data_root` in the
   content-addressed layout this decision fixes as the
   `linux_private_files_atomic_replace_v1` profile; StoredValue metadata
   remains in the operational store. A completed object is named only by its
   lowercase SHA-256 digest and is never overwritten.
2. A write is streamed to a staging file created with exclusive permissions,
   flushed with `os.fsync`, verified for digest and size, and published with
   `os.replace` on the same filesystem. The containing directory is then
   flushed. Failure removes only the incomplete staging file.
3. `module:run_spool` keeps temporary bytes below the same `data_root`, in one
   private directory per Run. A spool object is staged and atomically published
   by digest by the same sequence, but is never part of a value-store backup or
   promoted to StoredValue implicitly.
4. All opened files use no-follow semantics where the host offers them; every
   resolved path is checked to remain below its fixed root. Raw paths never
   cross a module boundary. Startup refuses a root with group/other access or a
   value/spool path that is a symlink.
5. Terminal-run cleanup removes only the exact run directory after verifying
   its ownership marker and containment. A crash may leave staging files; the
   next open removes only incomplete staging files and terminal-run spool
   directories confirmed from durable Run state.

### Formal invariants

```text
published_bytes -> complete AND sha256_verified AND beneath_fixed_root
spool_object -> belongs_to(exactly_one_live_run)
raw_host_path_crosses_module_boundary -> never
terminal_cleanup -/> stored_value OR sibling_run
```

### Required tests

[witness: workbench:notes]

1. A crash before and after publish exposes either no object or the complete
   digest-verified object, never partial bytes.
2. A symlink at any storage component is refused without reading or deleting
   its target.
3. Equal value bytes reuse one object; equal bytes in different live Runs remain
   isolated in their run directories.
4. Cleanup cannot remove a non-terminal Run, a StoredValue or a sibling Run.

### Consequence

Durable value bytes survive process restart and temporary run files remain
isolated and reclaimable without turning host paths into product data.

## Accepted decision A33 — service transport is HTTP-only in this release

### Normative rules

1. `module:service_transport` implements only manifest operations exposed on
   `http_api`, using the pinned `httpx` dependency and the exact policy this
   decision fixes as the `httpx_http_only_fail_closed_v1` profile. An
   operation exposed only through `mcp` or `operator` is a typed
   unsupported-channel refusal before credential resolution or any send.
2. The manifest supplies the pinned instance base URL and operation HTTP
   exposure. The transport may join only the declared relative path to that
   base; an absolute operation URL, authority change, userinfo or fragment is
   refused. Redirect following is disabled.
3. One `httpx.Client` is created with environment trust disabled. The request
   uses explicit connect/read/write/pool timeouts no greater than M48, bounded
   streaming request and response bodies, and the installation-resolved header
   values. No automatic retry occurs.
4. TLS verification is mandatory for HTTPS. Plain HTTP is accepted only for a
   manifest instance of class `local_dev` or `disposable_rig`; a production
   target without HTTPS is refused before send.
5. A failure before request bytes can be written is `definitely_not_sent`; once
   any request bytes may have crossed the socket it is conservatively
   `possibly_sent`. Response status never by itself establishes business
   success.

### Formal invariants

```text
transport_channel = http_api
channel IN {mcp, operator} -> refusal_before_send
production_target -> scheme = https
transport_attempts_per_call <= 1
redirect_followed -> never
```

### Required tests

[witness: workbench:notes]

1. MCP-only and operator-only operations perform no DNS, credential lookup or
   socket call.
2. A cross-host redirect, absolute exposure and production HTTP target are
   refused.
3. Proxy environment variables and ambient certificates cannot redirect the
   client; no retry follows timeout or disconnect.
4. Request and response overflow fail without returning truncated valid data.

### Consequence

The release can perform bounded HTTP integration while every transport without
an accepted adapter stays visibly and safely unavailable.

## Accepted decision A34 — untrusted functions run under bubblewrap and kernel-owned rlimits

### Normative rules

1. Linux `bubblewrap` is the only isolation backend for this release. Startup
   requires the executable and exact arguments this decision fixes as the
   `linux_bubblewrap_rlimit_v1` profile; absence or a failed self-test keeps
   the supervisor unhealthy.
2. Each execution uses fresh user, PID, IPC, UTS, cgroup and network namespaces,
   a read-only runtime and input mount, an empty environment, a private proc/dev,
   and one bounded writable scratch/output exchange. No host directory is
   mounted except those exact read-only inputs and private exchange paths.
3. The kernel launches bubblewrap with `subprocess.Popen` without a shell and
   applies `resource.setrlimit` before execution for CPU, address space, file
   size, open files and process count. The parent additionally enforces the
   monotonic wall deadline and aggregate output/scratch ceilings and kills the
   whole process group on any breach.
4. Entropy devices are absent, network is unshared, environment is cleared and
   the runtime contains no clock API offered to submitted code. A denied access
   or limit signal is a non-successful closed outcome, never a warning.
5. Success requires reaping every descendant, unmounting the namespace and
   deleting the private execution directory. Failure to prove cleanup marks the
   supervisor unhealthy and discards all outputs.

### Formal invariants

```text
function_execution -> bubblewrap AND external_rlimits
function_network = absent
function_environment = empty
cleanup_unconfirmed -> output_discarded AND supervisor_unhealthy
```

### Required tests

[witness: workbench:notes]

1. Network, host filesystem, environment, clock and entropy probes fail inside
   the sandbox and yield denied evidence.
2. CPU, memory, process, file-size, scratch, output and wall limits each stop an
   adversarial implementation externally.
3. A forked descendant is gone after completion and after timeout.
4. Missing bubblewrap, a changed runtime digest and failed cleanup block startup.

### Consequence

Submitted code executes only inside one named, testable Linux isolation
mechanism whose resource and cleanup failures are closed outcomes.
