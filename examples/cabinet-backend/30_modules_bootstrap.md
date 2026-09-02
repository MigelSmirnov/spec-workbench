# State 3 repair — Cabinet Backend bootstrap boundary

## Status

Accepted lineage repair for the already assembled `bootstrap` module. This
record does not introduce a new runtime responsibility: it makes explicit the
composition and offline-administration boundary already used by State 4, State
5, State 6, Notes, and the closed Stage 8.1 module review.

## `bootstrap`

### Owns

- local process composition for the Cabinet Backend runtime;
- resolving required deployment configuration through the accepted configured
  environment-variable names;
- construction and wiring of concrete runtime dependencies into the application
  composition root;
- the offline Linux deployment-owner boundary for local agent enrollment,
  credential rotation, and principal revocation.

### Knows

- which accepted concrete implementations must be constructed at startup;
- deployment configuration names required to construct those implementations;
- the configured Linux deployment-owner identity required by offline local
  administration;
- dependency wiring only, not the business or persistence policy hidden behind
  the supplied ports.

### Hides

- startup/configuration lookup sequencing;
- concrete composition order;
- offline command invocation mechanics and Linux-owner verification details.

### Must not own

- authentication, authorization, credential hashing, throttling, or security
  audit policy owned by `module:access_control`;
- HTTP route semantics owned by the API boundary;
- archive, synchronization, Registry, PresuPro, Holded, or retention business
  policy;
- permissive fallback construction when required configuration or a dependency
  cannot be created.

### Candidate public capabilities

```text
create_local_app
enroll_local_agent
rotate_local_agent_credential
revoke_local_agent
```

### Depth assessment

kind: facade
delegates to: `access_control`, `durable_archive`, `synchronization`, `catalogue_publication`, `registry_context`, `plan_actual`, `holded_publication`, `holded_gateway`, `system_clock`

Composition/boundary module. It is intentionally shallow in business semantics:
its value is one fail-closed runtime construction point and one explicit offline
administration boundary, while deeper security behavior remains behind
`module:access_control`.
