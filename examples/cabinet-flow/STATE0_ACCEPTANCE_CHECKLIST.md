# Cabinet Flow — State 0 acceptance checklist

## Status and purpose

This checklist is derived from the accepted Cabinet Flow State 0 product
boundary. It is a verification backlog, not a replacement for normative rules,
models, contracts or executable semantic oracles.

A checked item means that the named behavior has repeatable evidence against an
identified artifact and environment. It does not mean that an implementation
mechanism has been selected merely because State 0 names the expected outcome.

Later authoring must promote each applicable item into:

- a precise State 2 rule;
- an executable semantic oracle in State 7.1;
- a deterministic PR-CI test;
- or an operator-triggered integration/release-qualification test.

The owner and exact test mechanism are deliberately deferred. Negative tests
must use bounded synthetic inputs and canary credentials; they must never risk a
production fork bomb, decompression bomb, real secret disclosure or destructive
effect.

## Evidence conventions

Every result records the tested release or artifact identity, relevant contract
and capability versions, test identity, bounded input identity or digest,
observed outcome and cleanup/health evidence.

Expected refusal, rejection, timeout, resource exhaustion and pending states are
successful test outcomes only when they are explicit and observable. A crash,
silent fallback, invented success, leaked resource or ambiguous outcome is a
test failure.

## Syncthing source ingress

- [ ] **ING-001 — incomplete delivery:** a partial, still-growing or otherwise
  incomplete file is not registered as an accepted source. State 2 must choose
  the completion/stability protocol; a single filename observation is not proof
  of completion.
- [ ] **ING-002 — content deduplication:** repeated delivery of identical bytes
  produces one source identity by accepted content digest and does not duplicate
  business processing.
- [ ] **ING-003 — hostile or unsupported media:** unsupported content, extension
  and parser identity mismatch, polyglot input and bounded decompression-bomb
  fixtures are rejected with an observable safe refusal. No unbounded decode,
  execution or partially accepted source results.
- [ ] **ING-004 — custody outside synchronization:** after acceptance, rename or
  deletion inside the synchronized Inbox does not change source identity or
  remove the held immutable bytes.
- [ ] **ING-005 — restart recovery:** pending and accepted sources are
  rediscovered from durable registry state after restart without depending on a
  new Syncthing event.

Promotion target: State 2 ingress/custody rules, State 7.1 oracles and bounded
filesystem integration tests.

## Sandbox and admission

- [ ] **SBX-001 — denied ambient authority:** separate probes for unrestricted
  network access, filesystem access outside the assigned workspace, secret
  environment access, descendant-process spawning and neighboring
  implementation access each produce an observable refusal.
- [ ] **SBX-002 — resource termination:** bounded timeout, memory exhaustion and
  process-amplification fixtures produce failure evidence; the execution
  environment and every descendant are terminated, resources are reclaimed and
  the long-lived service remains healthy.
- [ ] **SBX-003 — preview is not a transaction:** sandbox effect intents cannot
  be replayed or committed later as a production transaction. Real execution
  starts with current authority and current inputs.
- [ ] **SBX-004 — automatic-activation boundary:** automatic activation succeeds
  only for bounded computation with schema-conforming input/output and no
  protected or uncertain effect. Every declared protected effect or unresolved
  uncertainty prevents automatic activation.
- [ ] **SBX-005 — declaration versus observation:** an implementation declaring
  no effects but attempting a write, network call, secret access or other
  effect is refused. The author's declaration cannot override observed
  behavior.

Promotion target: State 2 isolation/admission rules, State 7.1 oracles,
deterministic sandbox tests and isolated host-level cleanup tests.

## Versioning and authority

- [ ] **VER-001 — immutable implementation identity:** changing implementation
  bytes creates a new digest and draft; activation of the previous digest is
  not inherited.
- [ ] **VER-002 — expanded contract:** adding data access, effects, dependencies,
  resources or scope requires a new admission and activation decision even when
  the implementation bytes are unchanged.
- [ ] **VER-003 — invocation authority:** an activated implementation without
  current authority for the exact actor, target and effect cannot apply that
  effect.
- [ ] **VER-004 — exact rollback:** rollback restores the exact earlier accepted
  binding and versions. Deactivation or replacement does not erase earlier
  accepted versions or their evidence.
- [ ] **VER-005 — scope and principal confinement:** an agent cannot invoke a
  capability outside its grant, enlarge allowed target scope such as
  `project_ids`, substitute another principal or grant itself authority.

Promotion target: State 1 identities, State 2 lifecycle/authority rules and
State 7.1 version/authorization oracles.

## Flow graph and execution

- [ ] **FLW-001 — fail-closed preflight matrix:** unknown capability, dangling
  `from` reference, incompatible type, duplicate node identity, undeclared
  effect and attempted escape of an opaque handle each reject the flow before
  execution.
- [ ] **FLW-002 — invalid output containment:** invalid or semantically
  unacceptable node output is an explicit failure and is never forwarded to the
  next node as successful input.
- [ ] **FLW-003 — run pinning:** rerunning the same pinned flow after activation
  of a newer capability implementation selects the original exact versions
  until an explicit repin creates a new flow version or binding.
- [ ] **FLW-004 — bounded trace:** trace evidence contains identities, versions,
  digests, statuses, validation and bounded effect-intent evidence, but no
  secrets, original source bytes or unrestricted complete business facts.

Promotion target: State 1 graph/run identities, State 2 composition rules,
State 7.1 preflight/execution oracles and deterministic PR-CI tests.

## HandoffPackage and bridge

- [ ] **HND-001 — idempotent handoff:** retransmission of the same exact
  HandoffPackage does not create a second local acceptance or duplicate local
  CapabilityInvocation.
- [ ] **HND-002 — delivery is not execution:** when the local side accepts a
  package but has not invoked its capability, Cabinet Flow reports accepted and
  not executed rather than completed.
- [ ] **HND-003 — offline recovery:** an offline local Backend produces durable
  pending state, not success or loss. Reconnection resumes or reconciles one
  exact exchange and does not duplicate it.
- [ ] **HND-004 — integrity binding:** a package whose content, manifest,
  contract reference or digest no longer matches its issued identity is
  rejected by the receiving side. The exact cryptographic/transport mechanism
  remains a later-state decision.
- [ ] **HND-005 — credential non-transitivity:** the bridge credential cannot act
  as the online owner or an MCP caller; the tunnel identity cannot authenticate
  to the bridge or local administration; browser Basic Auth and SSH credentials
  cannot substitute for either machine boundary.

Promotion target: State 1 handoff/receipt identities, State 2 bridge rules,
State 7.1 idempotency/integrity oracles and operator-triggered integration
tests. The successful lower release-qualification path additionally requires
the deployed bridge and online local Backend.

## Access planes

- [ ] **ACC-001 — browser/MCP separation:** browser Basic Auth alone creates no
  MCP principal and grants no MCP operation. An MCP request without the
  configured tunnel identity exposes no Cabinet tool or data.
- [ ] **ACC-002 — no public bypass:** a network caller cannot reach Cabinet Flow
  MCP through a direct public endpoint that bypasses the Secure MCP Tunnel.
  Loopback/operator diagnostics do not count as a public product path.
- [ ] **ACC-003 — explicit identity mapping:** an authenticated tunnel identity
  without an active mapping to the owner principal is refused before Cabinet
  data access or capability dispatch.
- [ ] **ACC-004 — identifiers are not authority:** knowledge of a Card, source,
  project, HandoffPackage or capability identifier does not authorize reading
  or mutating it.
- [ ] **ACC-005 — secret non-disclosure:** canary credentials seeded solely for
  the test do not appear in bounded logs, errors, traces, exported evidence,
  prompts, HandoffPackages or process listings/arguments. Production secrets
  are never copied into a grep fixture.

Promotion target: State 2 access/secret rules, State 7.1 authorization oracles,
deterministic canary tests and the operator-triggered GPT/OpenAI integration
test.

## Agent context

- [ ] **CTX-001 — minimum ordinary context:** an ordinary operational request
  receives only the selected public capability descriptions and authorized
  task-relevant facts/sources; it does not receive implementation bodies or the
  complete Cabinet dataset.
- [ ] **CTX-002 — mode-specific context:** authoring receives only the selected
  contract, relevant implementation and evidence; composition may receive the
  graph and public contracts without all implementation bodies; execution
  receives the minimum immutable input and declared opaque capabilities.
- [ ] **CTX-003 — explicit capability gap:** when no accepted capability can
  produce the requested result, the system returns an observable bounded gap
  and may enter managed evolution. It does not improvise hidden unregistered
  code or present an invented operational answer as accepted Cabinet state.

Promotion target: State 1 context/evidence identities, State 2 context-selection
rules, State 7.1 context-manifest oracles and deterministic prompt-envelope
tests.

## Release-checklist relationship

Ordinary PR-CI should execute every deterministic promoted oracle and safe
negative fixture. External qualification remains operator-triggered:

1. the GPT/OpenAI stage uses the deployed Secure MCP Tunnel and exact release;
2. the lower stage uses the deployed `cabinet-web-backend`, an online local
   Cabinet Backend and the exact HandoffPackage path.

Both stages bind to the same immutable release candidate and recorded
configuration identities. This checklist does not allow a mock, direct call or
manual state change to replace either external proof.
