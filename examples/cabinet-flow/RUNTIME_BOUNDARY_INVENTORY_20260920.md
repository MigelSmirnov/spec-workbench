# Runtime boundary inventory — Cabinet Flow, 2026-09-20

Evidence document, not a design state. It records what reading the accepted code of Factory run 2
(spec `a5935cce…`, `projects/cabinet_flow/specs/draft/spec_*/selected`) shows about every place
where the kernel must touch its host, and what the design says about that place. It orders the work
that precedes the next paid Factory run. Each closed boundary is struck from the table below by the
commit that closes it.

## Finding

States 0–7 close the kernel's *logic*: 49 State 1 models, 28 decisions, 28 modules, 146 contracts,
107 notes, every Workbench gate green. They do not close its *runtime*. No module is told how it
reaches the host, so the generated kernel is a closed simulation: it stores nothing, sends nothing,
executes nothing and authenticates no one. Nothing reported it, because every gate checks a named
symbol against a surface, and here the mechanism is not named at all.

A State 3 `Hides` entry is a promise that a mechanism exists inside the module. For a module whose
hidden mechanism is a host effect, the promise needs one of three carriers the Factory can build:
a deterministic emitter, an `external` port with a hand-written adapter, or a note that names the
exact library calls. Cabinet Flow has the first for two boundaries (clock, digests) and the
persistence emitter for a third, which no module can reach.

## Inventory

| # | Boundary | Owner module | State 3 `Hides` | What run 2 generated | Carrier available |
|---|---|---|---|---|---|
| 1 | Durable records | `operational_store`, `operational_store_persistence` | the database, schema, transactions, record↔row mapping | committed records in a module-level dict; SQLite repository never constructed; ten domain modules keep their own records in module-level dicts; `trace_journal` probes `get_`/`read_`/`fetch_node_execution` on `payload: object` | `persistence_backend/v3` on `sqlite_sync_v2` (emitted, 14 of 29 durable kinds) — unreachable: no typed port, no `open`, no composition |
| 2 | Installation configuration and secrets | `installation` | where and how secrets are kept, how a reference becomes a usable credential | `os.environ` with invented names (`CABINET_FLOW_CREDENTIAL_BINDINGS`), invented JSON shape, invented default path in run 1 | none: no external contract for the protected configuration |
| 3 | Platform manifest at a pinned revision | `manifest_reader` | the manifest record format and revision history | `Path(revision.manifest_root_ref)` and an invented file layout | **closed 2026-09-20:** A31, `rules.platform_manifest_contract`, `PLATFORM_MANIFEST_EXTERNAL_CONTRACT_20260920.md` and active content-addressed evidence fix exact paths/bytes, legacy shapes and same-path ancestor history |
| 4 | Requests to microservices | `service_transport` | channel framing, TLS, redirects, timeouts | no network library imported; a `TransportResult` is assembled from constants | none: no HTTP/MCP client port |
| 5 | Execution of agent-authored code | `sandbox_supervisor` | the isolation backend and resource enforcement | a `tempfile.TemporaryDirectory()`; nothing is executed | none: no isolation backend is named anywhere |
| 6 | Value bytes and run files | `value_store`, `run_spool` | content-addressed area, run-scoped spool | bytes in module-level dicts, `io.BytesIO` | `source_byte_store_backend` (content-addressed, staged, verified) fits M38; spool needs a decision |
| 7 | Listeners | `http_gateway`, `mcp_gateway`, `bootstrap` | listener lifecycle, MCP framing | HTTP routes emitted; nothing starts a server; `serve_mcp` receives an envelope no component constructs | `http_router_backend` (emitted); launch and the MCP host adapter are undesigned |
| 8 | Channel authentication | `access_control` | credential verification per channel | the presented credential's payload names its own `kind`, `principal_id`, `delegation_id`; throttling is `time.sleep` over module-level dicts | depends on 1 and 2 |
| — | Wall and elapsed time | `system_clock` | host clock | emitted, correct | `system_clock_backend/v3` — closed |
| — | Identity digests | `identity` | canonical digest recipes | emitted, correct | `canonical_digest_backend` — closed |

## Order

1. **Durable records.** Everything else persists through it, and its emitter exists. The unit of
   work becomes the typed record port; the missing fifteen durable kinds get tables; one operation
   opens the store; the record-owning notes name the port's operations.
2. **Installation configuration**, because 3, 4 and 8 read it: one external contract for the
   protected configuration (location handed to `start_kernel`, closed format, secret references).
3. **Channel authentication** on top of 1 and 2.
4. **Manifest reading** against the recorded format of `platform/manifest/`.
5. **Value bytes and spool.**
6. **Service transport.**
7. **Sandbox execution.** The isolation backend is a deployment fact of the owner's machine and is
   decided last, with the owner, in terms of what it may and may not do.
8. **Listeners and launch.**

Boundary 3 was closed after this ordering was recorded. Its legacy free-text
idempotency declaration remains opaque and fail-closed until a binding proves
one exact typed-port mapping; credentials remain owned by installation rather
than the manifest.

Pending from the build of run 2 and folded into the boundaries they touch: the HTTP handler form
the router emitter requires (8), `ServiceTarget.targets` as instance records (2, 6), the emitter's
`from pydantic import TypeAdapter` in `imports.third_party` (1).

No paid Factory run is useful before boundary 1 is closed; a run after 1–3 yields a kernel that
keeps its records and knows who is asking, which is the first state worth putting on a stand.
