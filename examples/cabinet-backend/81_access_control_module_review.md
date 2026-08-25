# Cabinet Backend — Stage 8.1 `access_control` module review

Status: **PASS — concrete implementation gap repaired and re-reviewed**.

## Review input

The reviewed packet was built with:

```bash
python tools/design_module_review.py examples/cabinet-backend \
  --module access_control --slice --json
```

The deterministic structural review reported three contracts, six notes, and
zero structural blocks. Manual Stage 8.1 review found a semantic completeness
gap that the structural check cannot prove.

## Accepted deployment intent

Cabinet Backend must be generated as a complete working application for a
local Linux machine and must connect to the VPS Cabinet boundary. A deployment
is not expected to supply an otherwise unspecified access-control
implementation.

## Confirmed finding

The assembled specification declares `AccessControlBackend` as
`kind: interface` and injects it into `create_app`. Its two method contracts
define only the narrow runtime port:

- `AccessControlBackend.authenticate`;
- `AccessControlBackend.authorize`.

No concrete implementation symbol is declared. The assembled specification
also supplies no concrete owner for the local service-principal store,
credential verification, capability assignments, revocation/rotation state,
authentication-failure throttling, or security-audit persistence already
assigned to `module:access_control` by State 3.

Factory may emit the interface and generate callers against it, but it cannot
invent an undeclared concrete implementation without making new architectural
and security decisions. Therefore the generated local application cannot
construct the required `AccessControlBackend` instance from the current
specification alone.

## Adversarial result

Two materially different outcomes satisfy the current assembled slice:

1. a complete local application with a persistent Linux access-control
   implementation;
2. an application that only exposes a port and cannot start until an external
   implementation is supplied.

Only the first outcome satisfies the accepted deployment intent.

## Earliest owning repair

Repair must begin before assembly:

1. State 1 must define the runtime identities and durable security evidence
   required by the accepted A61, A66, and A67 semantics;
2. State 2 must keep credential verification, capability, rotation,
   revocation, throttling, and audit invariants explicit and place every
   build-time policy value in the correct structured data block;
3. State 3 must assign a concrete Linux implementation and its persistence
   boundary to `module:access_control` while retaining the narrow
   `AccessControlBackend` port for consumers;
4. States 5–6 must add the concrete implementation's callable seams and types
   without exposing credential mechanics through the public API;
5. State 8 assembly must include the concrete implementation, required
   persistence declarations, configuration, imports, notes, and composition
   wiring before this module is re-reviewed.

Do not repair this finding by changing `AccessControlBackend` from an interface
into an underspecified concrete class or by adding an implementation only to
`global_spec.json`.

## Repair outcome

The accepted repair now provides:

- concrete `PostgresAccessControlBackend` behind the retained
  `AccessControlBackend` port;
- distinct persistent principals and credentials for Codex, Claude Code, and
  other explicitly enrolled local consumers;
- Argon2id verification, bounded throttling, rotation, revocation, and
  append-only audit evidence;
- offline Linux-owner administration with one-time credential disclosure;
- `module:bootstrap`, which constructs the backend from deployment secrets and
  supplies it to deterministic `api.create_app` without HTTP/MCP exposure of
  administration operations.

Post-repair verification:

```text
assembly: 5/5 ready, 0 errors, 0 warnings
access_control: 9 contracts, 18 notes, 0 blocks
bootstrap: 4 contracts, 7 notes, 0 blocks
```

The generated application no longer depends on an unspecified deployment-owned
Python implementation. Remaining choices such as private helper decomposition
and SQL statement organization are internal implementation variation constrained
by the accepted models, persistence classes, rules, contracts, and notes.
