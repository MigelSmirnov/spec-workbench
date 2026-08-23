# Cabinet_web backend — VPS runtime discovery

Date: 2026-08-22

## Status

```text
ZERO_STEP: PASS
REMOTE_MUTATIONS: NONE
FACTORY_ROUTE_B_STARTED: NO
CABINET_BACKEND_WORKTREE_TOUCHED: NO
```

This is pre-State-0 evidence. It records what exists before product behavior,
ownership, contracts, or deployment decisions for the new `Cabinet_web`-owned
server backend are accepted.

## Evidence sources

- live read-only VPS inspection on `vps-c1028b5e` at 2026-08-22 21:51 UTC;
- Factory diagnostic
  `docs/CABINET_WEB_VPS_INTEGRATION_DIAGNOSTIC_20260822.md`;
- Factory state and deploy artifacts for `Cabinet_web` and
  `client_portal_sandbox`;
- current `MigelSmirnov/Cabinet_web/main` at
  `d3fac8e5d2b85c12904cba24060717b84e2757c2`;
- the deployed Cabinet release at
  `e863a9b708c8541da7eb945ce622eb1dbcdc03ea`;
- a no-match invocation of the live read-only Cabinet MCP transport.

Code, tests, deployed configuration, and runtime probes are evidence rather
than sources of product norm. Findings must still be classified and accepted
at their earliest owning Workbench state.

## Observed VPS topology

| Surface | Live observation | Classification |
| --- | --- | --- |
| VPS | Ubuntu kernel 6.8, 7.6 GiB RAM, 72 GiB disk with 58 GiB free | available resource envelope, not a sizing promise |
| edge | nginx owns public ports 80/443; configuration test passes | reusable host constraint |
| `cabinet-dev.vitalvibeconstruction.com` | valid TLS; HTTP 401 without Basic Auth | reachable protected static site |
| Cabinet release | `/var/www/cabinet-dev/current` points to release `e863a9b…` | immutable release layout exists |
| Cabinet nginx site | static `try_files`; no `/api` route | no browser backend transport exists |
| Cabinet MCP | active `cabinet-mcp-tunnel.service`; stdio MCP behind secure tunnel | agent/tool transport only |
| Client Portal | nginx proxies to `127.0.0.1:8090` | separate application deployment |
| Client Portal compose | Registry, API, frontend, and proxy exited cleanly four days earlier | operationally stopped, not evidence of a Cabinet failure |
| `cabinet_backend` | no service, container, or listening socket | not deployed on this VPS |
| unrelated listener | Panelforge Uvicorn owns loopback `127.0.0.1:8008` | must not be reused as Cabinet transport |

Public probes reproduced:

```text
https://portal.vitalvibeconstruction.com/      -> 502
https://cabinet-dev.vitalvibeconstruction.com/ -> 401 without credentials
```

The Client Portal 502 and the missing Cabinet Web backend are independent
conditions. Starting the Portal stack would not create a Cabinet API.

## Current Cabinet_web lineages

Current repository main:

```text
d3fac8e5d2b85c12904cba24060717b84e2757c2
```

VPS static release:

```text
e863a9b708c8541da7eb945ce622eb1dbcdc03ea
```

GitHub comparison reports the deployed release and `main` as diverged. The
deployed revision contains the read-only MCP work, while later main contains
Invoice Card changes. Neither branch frequency nor deployment age resolves the
target product semantics. State 0 must define the desired product slice, and
later states must reconcile source lineage explicitly.

Factory project `Cabinet_web` is only a bootstrap container:

- accepted base has no `standard_version: 2`;
- no normalized spec exists;
- no deploy or verification run exists;
- no terminal OTK covers the accepted spec.

The old Factory spec must not be sent directly through Route B.

## Existing transports

### Static browser transport

The current browser loads generated same-origin JSON files. It has no API base
URL, authenticated server session, write request, upload transport, WebSocket,
SSE, or `cabinet_backend` client.

### Cabinet MCP transport

The live service exposes bounded read operations for providers, projects,
project summaries, and invoices through an authenticated agent tunnel. A
no-match provider search completed successfully during this diagnosis, proving
the current tunnel end to end without disclosing Card data.

The MCP wire surface is not a browser contract and must not be broadly exposed
through nginx.

### Client Portal server transport

`client_portal_sandbox` provides useful implementation evidence:

- host nginx terminates TLS;
- an internal router binds loopback only;
- API, frontend, and Registry remain on an internal Docker network;
- runtime data lives in persistent volumes;
- browser and API use one public origin;
- production startup validates origin and trusted-host policy;
- health checks, body limits, non-public Registry, and one-worker SQLite
  constraints are explicit.

These are candidate platform patterns. They are not automatically Cabinet
requirements and must not be copied into the new spec without State 0-2
ownership.

## Root-cause classification

### `CW-SERVER-001` — missing Cabinet browser backend

```text
class: placement
evidence: static nginx site, static browser requests, no Cabinet HTTP process
earliest owner: State 0 product boundary and external systems
```

### `CW-BACKEND-TRANSPORT-001` — missing bounded server-to-server boundary

```text
class: unresolved
evidence: cabinet_backend is absent from VPS and its moving HTTP surface does
          not provide the current Web listing/search use cases
earliest owner: State 0 outcomes, then State 2 trust/failure policy
```

### `CW-DEPLOY-LINEAGE-001` — deployed Cabinet differs from main

```text
class: placement
evidence: VPS release e863a9b… and main d3fac8e… diverge
earliest owner: State 0 operational constraints; Stage 9 release lineage
```

### `CP-AVAILABILITY-001` — Client Portal upstream stopped

```text
class: separate operational incident
evidence: four containers exited with code 0; nginx upstream has no listener
action in this task: none
```

## Boundary supported by the evidence

The new service should be owned by `Cabinet_web`, not named or shaped as a
replacement implementation of `cabinet_backend`.

At minimum, later design must keep three boundaries distinct:

```text
browser
  -> Cabinet_web server boundary
       -> Cabinet_web domain/read/write capabilities
       -> bounded transport adapter to cabinet_backend
```

The browser must not receive a service bearer credential, import MCP wire
shapes, access backend storage, or depend on `cabinet_backend` availability for
all Cabinet behavior. Exact offline, retry, reconciliation, and audit behavior
remains a State 0-2 decision.

## State 0 entry questions

Only the first coherent decision group should be resolved next:

1. Which exact user-visible action first requires the new server backend?
2. What observable success and failure does that action have when
   `cabinet_backend` is online or offline?
3. Which system owns the durable fact created or read by that action?
4. Is the first release read-only, or must it include a write/synchronization
   operation?

Authentication mechanics, DTOs, routes, modules, storage, deployment commands,
and implementation algorithms are deliberately deferred until their owning
states.

## Zero-step verdict

```text
Factory state inspected                         PASS
current Cabinet_web main pinned                 PASS
deployed Cabinet release pinned                 PASS
live VPS access                                 PASS
nginx/listener/container topology inventoried  PASS
existing browser transport classified          PASS
existing MCP transport exercised               PASS
Client Portal deployment patterns inventoried  PASS
cabinet_backend isolation preserved            PASS
remote changes                                  NONE
ready to begin Workbench State 0               YES
```
