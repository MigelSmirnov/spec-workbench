# Cabinet Vault — next session handoff

## Where we are going

The experiment is not trying to regenerate the classical Cabinet Backend application more accurately.

The target is to separate the accepted Cabinet design into four layers:

```text
Cabinet durable semantic contract
        ↓
compiled box capabilities / policies / schemas
        ↓
generic local host and generic lowerings
        ↓
agent-side composition with independent external boxes/connectors
```

The intended deployed shape is:

```text
generic host
+ compiled self-described Cabinet box
+ local durable data/storage
```

Cross-product work is composed outside Cabinet. Cabinet should not permanently own Registry, PresuPro, Holded, VPS, HTTP, or product-specific transport clients merely because a workflow crosses those systems.

The central criterion remains:

> Keep meaning durable. Treat everything provably derivable from that meaning as a cheap disposable compilation artifact.

And the compiler rule is:

> Compiler may implement the declared language. Compiler must not silently extend it.

## Why the failed generated Cabinet Backend matters

A classical Factory run reached `route_b_complete` but did not establish a verified backend. The useful evidence is not that generation was weak; it is that the generated failure surface exposed where the classical specification mixes semantic ownership with application lowering and external integrations.

Observed failure classes included:

- missing machine relation between interface ports and concrete implementations;
- local projection dropping required lowering imports such as `psycopg`;
- required semantic/runtime verification being skipped while the overall route still appeared green;
- concrete authority-model mismatches in audit/principal/credential construction;
- a large concentration of missing/stubbed methods at Holded, Synchronization, VPS, and HTTP boundaries.

Treat this generated backend as diagnostic evidence, not as a codebase to repair by hand.

A stub is evidence that the specification or boundary must be inspected. Do not fill a stub merely to make generated code run.

## The three buckets

### 1. Problems the box architecture should remove from the Cabinet product specification

These exist primarily because Cabinet was described as a classical application with permanent integration and framework structure.

Examples:

```text
Holded HTTP adapters/gateway implementation
VPS transport adapters
product-specific synchronization clients
Registry/PresuPro/Holded client classes
FastAPI handler ownership
request.app.state dependency wiring
product-specific bootstrap constructor graph
service-class architecture
repository/UoW class graph
Postgres* Cabinet product classes
third-party import projection into Cabinet modules
```

Disposition:

```text
DO NOT improve these as durable Cabinet architecture.
```

External product/transport responsibilities move to independent boxes/connectors and agent-side composition. Framework/service/repository structure becomes disposable lowering where needed.

A concentration of stubs at an external boundary is a `BOUNDARY_LEAK` signal, not automatically an implementation backlog.

### 2. Problems that remain real but move into the generic host/runtime once

These mechanisms are necessary, but they should not be re-specified as Cabinet-specific class architecture for every product.

Examples:

```text
storage backend implementation relation
transactions and locking
PostgreSQL driver/backend
record persistence
filesystem/blob vault
schema validation
transport exposure
authentication mechanics
grant enforcement
audit persistence
startup/recovery mechanics
```

Disposition:

```text
GENERIC HOST / LOWERING CONTRACT
```

Cabinet declares what durability, authority, disclosure, transaction, and effect guarantees it requires. The host declares and proves how a selected backend satisfies those generic requirements.

The parent Cabinet interface-ownership incident is the warning: host/compiler architectural rules must be explicit language rules, never hidden assumptions in deterministic code.

### 3. Problems that must remain and be closed in the Cabinet semantic specification

These are durable product meanings and policies. Box architecture does not make them disappear.

Examples:

```text
Invoice / estimate identity and immutable evidence
source-byte custody and durable acceptance
PlanActual meanings and comparability
RetentionRelease policy
principal semantics
credential semantics
grant/resource scope
disclosure rules
audit event semantics
allowed effects
provenance
explicit match decisions
local authority boundaries
```

Disposition:

```text
SPECIFY AND PROVE
```

Current known semantic gaps include the old PlanActual aliases:

```text
EstimateItemSnapshot.total
InvoiceLine.total
```

The PresuPro probe found no single authoritative canonical item total. The real Invoice Card V1 contract has no `InvoiceLine.total`; it exposes distinct `net_amount` and `gross_amount` meanings. These require an explicit product decision later; they must not be repaired in an adapter or compiler heuristic.

Authority defects found in generated code also belong here at the semantic level: the box/host contract must close principal, credential, audit-event, grant/scope, disclosure, and effect semantics before trusting a generated implementation.

## Verification rule

The earlier Factory route demonstrated that completion of a pipeline is not proof of behavior.

For this experiment use:

```text
PASS       = required evidence executed and passed
FAIL       = required evidence executed and failed
UNVERIFIED = required evidence was not obtained
SKIP       = evidence was not executed; never equivalent to PASS
```

Do not call a box or generated backend verified when required runtime/semantic tests did not execute.

## Existing executable guards

The experiment already has:

- derivability detector: compatible box surfaces either compile or expose semantic gaps;
- composition compiler: no hand-written mapping, fail-closed before invoking boxes;
- hidden-rule audit: deterministic compiler behavior must be declared by `box_language_v0.yaml`;
- conformance tests and compiler fingerprints to prevent silent language extension.

Validated on 2026-08-20:

```text
main current experiment suite: 53 passed
built-in adversarial mutation/audit: 3 passed
box language CLI audit: pass, 15 rules, 0 findings
```

These results validate the experiment tooling only. They do not retroactively verify the previously generated classical Cabinet Backend.

## Plan for the next session

Do not start by repairing the generated classical backend and do not immediately return to the PlanActual monetary choice.

First use the failed generated backend as a bounded architecture probe.

1. Build a small **generated-backend/boundary audit** around known failures. It should classify findings rather than repair code. Initial classes:

```text
LANGUAGE_RELATION_GAP
PROJECTION_GAP
VERIFICATION_NOT_EXECUTED
BOUNDARY_LEAK
LOWERING_GAP
AUTHORITY_SEMANTIC_GAP
DOMAIN_SEMANTIC_GAP
```

2. Encode the three-bucket disposition above so the audit can distinguish:

```text
remove from Cabinet product spec
move to generic host/lowering
keep and close in Cabinet semantic spec
```

3. Make verification fail closed. Required evidence that was skipped/missing must produce `UNVERIFIED`, never `PASS`.

4. Feed representative failures from the real generated Cabinet run into the audit. In particular:

```text
missing concrete-interface implementation relation
lost psycopg projection
skipped semantic/runtime tests
Holded/Synchronization/VPS/HTTP stub concentration
audit/principal/credential construction mismatches
PlanActual and RetentionRelease unresolved domain methods
```

5. Only after this classification pass, decide the next implementation work:

- external adapter/transport findings should shrink the Cabinet box boundary;
- generic mechanism findings should define reusable host contracts;
- authority/domain findings should return to the earliest owning semantic specification state.

6. Then resume the PlanActual monetary repair with the clearer boundary, using the unchanged derivability compiler as the acceptance test.

## Stop conditions

Stop and report a semantic/architectural gap instead of adding code when:

- a generated stub requires a product-specific external client inside Cabinet;
- a deterministic compiler/host decision has no declared language rule;
- a mapping requires choosing meaning from field names or types alone;
- a disclosure/scope/authority decision is absent;
- required verification cannot run;
- fixing generated code would merely encode a decision absent from the durable specification.

The experiment succeeds when Cabinet's durable definition becomes substantially smaller than the classical application specification while preserving all real Cabinet data, authority, policy, invariants, effects, and provenance.
