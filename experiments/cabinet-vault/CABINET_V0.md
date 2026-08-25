# CABINET_V0 — self-describing data cabinet experiment

## Status

Experimental. This document does not modify or supersede `SPEC_STANDARD.md`.
It tests whether the semantic core currently authored for an application can
instead describe a protected, self-describing data cabinet whose operations are
composed at runtime by agents.

## Hypothesis

A Cabinet is a long-lived trust and data boundary. Application code is not the
primary durable artifact.

Durable artifacts are:

- data schemas and identity;
- ownership and authority;
- invariants and lifecycle;
- capabilities;
- disclosure and effect policy;
- storage/locality metadata;
- audit and provenance requirements.

An agent receives a bounded grant, discovers the cabinet schema and available
capabilities, proposes an execution request, and receives only the result that
the cabinet is permitted to disclose.

Generated orchestration code, when needed, is ephemeral and is not itself an
authority source.

## Trust rule

Possession of an agent process, host account, model session, or cabinet endpoint
MUST NOT imply access to cabinet data.

A principal MUST be authenticated independently and every invocation MUST be
authorized against an explicit capability grant.

A grant is narrower than a cabinet key. It SHOULD be short-lived and MAY be
single-use. It identifies:

- principal;
- allowed capabilities;
- optional resource/data scope;
- optional disclosure scope;
- expiry;
- nonce or replay boundary.

The cabinet's encryption key remains inside the trusted cabinet runtime. Agents
do not receive the raw data-encryption key merely because they hold a grant.

## Cabinet manifest

Every cabinet exposes a machine-readable manifest to an authenticated principal.
The manifest describes only surfaces the principal is allowed to discover.

Conceptual shape:

```yaml
cabinet:
  id: finance
  schema_version: 0

schemas:
  Invoice: {...}
  InvoiceFilter: {...}
  InvoiceSummary: {...}

capabilities:
  invoice.search:
    input: InvoiceFilter
    output: [InvoiceProjection]
  invoice.aggregate:
    input: InvoiceFilter
    output: InvoiceSummary

policies:
  disclosure: {...}
  effects: {...}
  ownership: {...}
```

The manifest describes semantics, not transport. HTTP, MCP, local IPC, SQL,
WASM, or another execution mechanism are lowerings of the same capability
surface.

## Capability

A capability is the stable semantic operation visible to agents.

It defines:

- input schema;
- output schema;
- read scope;
- allowed effects;
- preconditions;
- invariants;
- disclosure constraints;
- audit requirements.

Example:

```yaml
capability: invoice.aggregate
input: InvoiceFilter
output: InvoiceSummary
reads:
  - Invoice.amount
  - Invoice.date
  - Invoice.project_id
effects: []
requires:
  - requester is authorized for selected invoice scope
disclosure:
  allow:
    - aggregate totals
    - grouping key
  deny:
    - source artifact bytes
    - credential material
```

A capability does not prescribe a Python function, class, route, repository, or
storage engine.

## Execution request

An agent does not submit arbitrary source code as authority. It submits a
bounded execution request referencing known capabilities and schemas.

Conceptual shape:

```yaml
execution:
  intent: summarize_selected_invoices
  grant: <signed-grant-ref>
  steps:
    - invoke: invoice.aggregate
      args:
        period: 2026-07
        project_id: project:123
  output:
    schema: InvoiceSummary
  effects: []
```

The cabinet runtime MUST validate the request before lowering or execution.

Unknown capability, broader resource scope, broader disclosure, undeclared
effect, expired grant, or replay violation MUST fail closed.

## Ephemeral lowering

After validation, the cabinet MAY lower an execution request into transient
implementation code or a deterministic execution backend.

Possible lowerings include:

- SQL query;
- Python sandbox function;
- WASM program;
- local tool invocation;
- remote cabinet capability invocation;
- deterministic backend IR.

The lowering MUST NOT increase authority relative to the accepted execution
request.

Generated implementation SHOULD be discarded after execution unless retained as
non-normative audit evidence. The normative evidence is the accepted request,
grant, policy version, input references, and result provenance.

## Data locality

A cabinet MAY keep raw data local and expose only computation over that data.

The preferred rule is:

> move the permitted computation to the data before moving protected data to the
> agent.

Cross-cabinet work composes capabilities. It does not require one agent to
receive unrestricted raw access to every participating cabinet.

## Relationship to SPEC_STANDARD v2

This experiment treats several existing specification concepts as candidates for
a semantic core:

| SPEC_STANDARD-oriented concept | CABINET_V0 interpretation |
| --- | --- |
| models | durable data/schema |
| identity | data/principal identity |
| rules | policy and invariants |
| contracts | candidate capability semantics |
| config | cabinet configuration |
| persistence backend | storage lowering |
| HTTP router backend | transport lowering |
| security notes | authority/disclosure constraints |
| provenance | execution/audit evidence |

Application-specific module paths, imports, Python signatures, route wiring, and
repository classes are not assumed to be part of the cabinet semantic core.

## Trusted kernel

A minimal cabinet runtime is expected to contain long-lived trusted code for:

1. identity and authentication;
2. grant verification;
3. policy evaluation;
4. schema and manifest serving;
5. transaction/effect control;
6. execution sandbox or deterministic lowering;
7. encryption/key handling;
8. audit and provenance.

Business orchestration above this kernel MAY be ephemeral.

## Experiment success criteria

The experiment is useful only if one real Cabinet Backend use case can be
expressed without inventing permanent application-layer modules for the use
case.

The spike passes when:

1. existing product/model/rule decisions can define the needed schemas and
   invariants;
2. the agent-visible operation is expressed as capabilities rather than raw
   storage access;
3. an execution request can be authorized without trusting generated code;
4. raw protected data can remain inside the cabinet where practical;
5. the result has enough provenance to audit what happened;
6. transport and storage choices remain lowerings rather than semantic owners.

## Explicit non-goals

CABINET_V0 does not yet define:

- a production cryptographic token format;
- a full capability algebra;
- distributed consensus between cabinets;
- a replacement for all existing backend code;
- autonomous write access without explicit effect policy;
- a new canonical version of `SPEC_STANDARD`.
