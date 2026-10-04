# State 2 — Cabinet Kernel access, surface, store, release and security review

Draft of 2026-09-30. Rules for principals and the surface, secrets and service
instances, the store, time and the release, and the State 0–2 security review
(K-11, K-13, K-15, K-16, K-17). Reuses cabinet-flow decisions 21–26, 30 and 32 where they
still hold; delegations, throttling, store continuity and the kernel's own HTTP
surface are gone (K-11, K-15, State 0 exclusions).

## Accepted decision A16 — one owner token, named agent tokens, one fixed surface

Reuses cabinet-flow decisions 21 and 22, narrowed by K-11 and K-15.

### Normative rules

1. A request is handled in this order, the first failing check deciding: its
   size, counted as the bytes of the request message as received, is within
   `surface_request_bytes_max`; the configuration re-read of rule 2 passes and
   its token is known — both with the one token refusal; it names a known
   operation and fits that operation's schema (rule 4); its actor may call that
   operation at all (rule 3);
   then the operation's own checks, in the order its decision gives — a restriction
   that depends on the record named, such as A06's refusal of an agent asking for
   a version above `read`, is one of those. One convention covers every
   "first failing" of every decision: checks in the order the decision lists
   them; a check naming several conditions in one sentence takes them in the
   order written; a check that fails at several items names the first in its own
   order, or, when the items have none, the smallest identifier by code point
   (A05 rule 2); a list's elements in list order. A request naming a record
   that does not exist — a flow, a flow version, a run, a binding, any other —
   is refused as State 0's unknown reference before that record's own checks,
   never as a proof failure or a missing activation; refusal codes are State
   5's. Every request over `mcp` carries one token. The kernel compares it in constant
   time with the owner token and with each agent token of the installation (M28).
   A missing, unknown or revoked token gets one refusal that reveals nothing about
   any record. Abuse control against guessing is the reverse proxy's (State 0);
   the installation refuses to start with any token shorter than 43 characters
   (32 bytes in base64url), with two equal tokens or with two agent tokens of
   one name (M28 `agent_name`). That tokens are random is
   the installer's duty; the kernel cannot check it.
2. Before evaluating each request the kernel reads the configuration file and
   compares the SHA-256 of its bytes with that of the last read; when they differ,
   or the file cannot be read, it re-reads it (K-15) and takes from it only the
   token list. Exactly four checks apply to a re-read: the
   file can be read and parsed; every token is at least 43 characters; no two
   tokens are equal; no two agent tokens share a name (M28). When all four
   hold, the new list replaces the old one.
   When any fails, every request is refused, the owner's included, until a
   re-read passes, with the same one refusal as an unknown token (rule 1); the
   old list is not kept, since it may hold a revoked token.
   Every other field of the configuration, and every other start check, applies
   only at a restart.
3. Who may do what is exactly the State 0 table of primary actions:
   - owner only: accept a binding, approve or refuse an effect, grant or revoke,
     cancel a run, resolve an unknown outcome;
   - agent with the author right only: author a contract or an implementation,
     add a trial case;
   - owner or agent with the author right: capture a failed execution, roll a slot
     back;
   - any agent only: try an implementation, propose a binding, compose and prove a
     flow;
   - owner or any agent: inspect, activate a flow (an agent only a `read` version,
     A06), run, resume, release a failed run, read a trace.
   No request field names or changes the actor.
4. The surface is one fixed set of typed operations (K-11). Every request is
   validated against its schema at the step rule 1 gives it — after its size and
   its token, before anything else; an unknown operation, an unknown field, or a
   field over its bound is refused. The bounds are: implementation code, at most
   `implementation_code_bytes_max`; a value of a trial case or constant, at most
   `stored_value_bytes_max`, and so is a run's input value (A12 rule 1) (a file
   fixture `trial_fixture_bytes_max`); every
   other string anywhere in the request, at most `bounded_text_bytes_max`, each
   counted as its UTF-8 bytes.
5. Text an agent supplies — purposes, code, names — is data. The kernel never
   evaluates, imports, formats or interprets it inside its own process; code runs
   only in the sandbox (A03).
6. Every list operation returns `page_size_default` items unless the caller asks
   for another size; a size above `page_size_max` or below 1 is refused, and so is
   a continuation token that is malformed or names no record of that type. Items come
   newest first, in reverse store order (K-17). The continuation token is the
   store position of the last item returned; the next page starts below it, so a
   record added meanwhile never shifts, repeats or hides an item. Each page
   applies the filter to the records as they are at its own request: a record
   whose filtered field (a status) changes between pages leaves or enters the
   pages still to come, and the token stays valid when the record it names no
   longer matches. Paging never changes what A07 lets the caller see.
7. No response carries a token, a service credential, a host path or a stack
   trace, including on an internal error.

### Formal invariants

```text
request_evaluated -> token matches (owner | exactly one agent) in constant_time
unknown_token -> one_refusal (reveals nothing)
owner_only_action -> actor = owner
author_action -> actor = agent AND agent.may_author
request -> schema_valid AND size <= surface_request_bytes_max
agent_text -> data (never evaluated in kernel process)
page_size <= page_size_max
```

### Required tests

1. Each owner-only action attempted with an authoring agent token is refused.
2. An unknown token asking for an existing and for a missing run gets the same
   refusal.
3. Removing an agent token from the configuration refuses that agent's next
   request without a restart.
4. A request with an unknown field is refused before any record is read.
5. A purpose containing template or SQL syntax is stored and returned verbatim.
6. No response on an internal error contains a path or a stack trace.

### Consequence

There is one entrance and one list of who may do what; nothing an agent sends can
become the owner's decision.

## Accepted decision A17 — secrets and instances are the installation's

Reuses cabinet-flow decision 23, narrowed by K-16.

### Normative rules

1. The installation's configuration file holds the owner token; the agent tokens;
   the selected manifest instance name of each service it selects one for; at
   most one credential for each service it gives one: a header name — an HTTP
   field-name token, or the kernel refuses to start — and the reference that
   resolves to its value on the host (a service with none fails only its own
   requests, rule 2); and the
   address the kernel's one `mcp` entrance listens on, which the host's reverse
   proxy reaches (owner, 2026-10-03, raised by the pre-contract data closure).
   The kernel reads the file's path from its one command-line argument and reads
   no environment variable. The file
   must be a regular file, not a symbolic link, owned by the kernel's user, with
   no permission for group or others; the kernel refuses to start otherwise.
2. A credential is resolved only when a request to its service is built — a
   service the installation gives no credential, or whose secret file is
   missing, unreadable or holds an empty value or a control character, fails
   that request's pre-send check `credential_unresolved` and stops nothing
   else — and is
   added as that header. It never enters the store, a record, a trace, a preview, a
   failure detail, a log line, a process argument or a response.
3. A function never receives a credential: its environment holds only the hash
   seed (A03) and its
   inputs are values that crossed a proven edge.
4. The instance of every service is the one the installation selects (K-16); no
   request, flow or binding chooses another. A service with no selected instance
   is not invocable (A08).

### Formal invariants

```text
credential IN {store, record, trace, preview, failure_detail, log, argv, response} -> never
credential_resolved -> at_request_build AND for_its_service_only
instance(service) = installation.selected(service)
config_file_mode -> owner_only_readable
```

### Required tests

1. A canary credential appears in no record, trace, preview, log or response after
   a run that used it.
2. A configuration file readable by others stops the start.
3. No request field can make an operation node reach another instance.

### Consequence

What the kernel can reach, and with which secret, is decided on the host by the
person who installs it, and cannot be changed from a conversation.

## Accepted decision A18 — one process, one store, one writer

Reuses cabinet-flow decisions 30 and 32, narrowed by K-17: no store continuity, no
concurrent connections.

### Normative rules

1. The kernel is one process. At start it takes an exclusive lock in the data
   directory; a second process on the same directory refuses to start.
2. The data directory holds one SQLite database with every kernel record, a
   content-addressed area of value bytes and file fixtures named by digest, and
   the run spool, one subdirectory per run. The directory and everything in it
   are private to the kernel's user; the kernel refuses to start otherwise. Every
   file of the directory is opened without following symbolic links; a link
   found at start stops the start, and one found later makes that store call
   fail with nothing written.
3. Only the store module opens the database. Every change is one call to the
   store module and one transaction inside it; callers never open, name or pass a
   transaction (K-17). A call that fails writes and changes no record; the only
   trace it can leave is a published file no record names, which nothing reads
   and which is replaced at its position (rule 4). Surface requests are
   handled one at a time in the order they arrive: one request, including the run
   advancement it causes (A13), ends before the next begins, so an approval, a
   cancellation and a resume of one run never race.
4. Value bytes and spooled files are written to a temporary file, flushed, checked
   against their digest and size, and then renamed into place; a completed file a record names is
   never overwritten — a spooled file no record names, left by a change that
   failed, is replaced at its position. Equal bytes are stored once. On start, temporary files and
   the spool directories of runs that ended and do not keep their spool (A14) are
   removed; nothing else is.
5. Backup and restore are an operational procedure outside the kernel (K-10); the
   kernel detects no restore and keeps no continuity counter.

### Formal invariants

```text
processes_on(data_directory) <= 1
store_change -> one_call AND one_transaction IN store_module
file_published -> complete AND digest_verified AND never_overwritten
symlink_inside(data_directory) -> refused
```

### Required tests

1. A second kernel on the same data directory refuses to start.
2. A crash during a value write leaves either no file or the complete file.
3. A failed store call leaves no partial record.
4. A symbolic link in the value area stops the start.

### Consequence

There is one place where the kernel's truth lives and one writer of it, so no
record ever has two orders.

## Accepted decision A19 — kernel time has one source

Reuses cabinet-flow decision 25, narrowed.

### Normative rules

1. Every timestamp the kernel records comes from one clock module; no other part
   of the kernel reads the wall clock. A request never supplies the current time.
2. Deadlines of one sandbox execution and one HTTP request are measured with the
   monotonic clock of the same module; a monotonic reading is never stored.
3. A timestamp received from a service is a value like any other: it never becomes
   a kernel timestamp and orders nothing in the kernel. The kernel orders its
   records only by the store's order (K-17).
4. Functions have no clock (A03).

### Formal invariants

```text
kernel_timestamp -> clock_module.now
request_field(current_time) -> refused
service_timestamp -/> kernel_timestamp
stored(monotonic_reading) -> never
```

### Required tests

1. With an injected fixed clock, the same test sequence writes the same
   timestamps.
2. A service answer with a timestamp far in the future changes no kernel record's
   time or order.

### Consequence

Generated modules have no freedom to invent a clock, and time never decides
anything alone.

## Accepted decision A20 — one release fixes every ceiling and every dependency

Reuses cabinet-flow decision 26 and its release-ceiling values, narrowed to the ceilings this kernel
reads.

### Normative rules

1. Every global ceiling is one release constant `RELEASE_CEILING_<NAME>`, the
   name below in upper case, delivered to code as a data-provider constant
   (SPEC_STANDARD 15.3.1, 6.10: one exact entry is one scalar constant; owner,
   2026-10-03, raised by the pre-contract data closure). No
   request, flow, contract, manifest, configuration or environment variable raises
   one, and no module defines a second default. Release v1:

   | name | value |
   |---|---|
   | `wall_time_ms` | 30000 |
   | `memory_bytes` | 536870912 |
   | `output_bytes` | 67108864 |
   | `process_count` | 8 |
   | `sandbox_scratch_bytes_max` | 268435456 |
   | `implementation_code_bytes_max` | 1048576 |
   | `stored_value_bytes_max` | 1048576 |
   | `trial_fixture_bytes_max` | 67108864 |
   | `spool_file_bytes_max` | 134217728 |
   | `spool_run_bytes_max` | 536870912 |
   | `service_response_bytes_max` | 134217728 |
   | `transport_timeout_ms` | 60000 |
   | `surface_request_bytes_max` | 134217728 |
   | `bounded_text_bytes_max` | 16384 |
   | `failure_detail_bytes_max` | 4096 |
   | `page_size_default` | 50 |
   | `page_size_max` | 200 |

   The first four are the ceilings of the ResourceBounds M04 fields of the same
   name. Bytes are exact integers; times are integer milliseconds.
2. Over a ceiling is always a refusal or a failure, never a truncation — for
   code, values, files, requests, responses and outputs. The one exception is
   `failure_detail`, a diagnostic excerpt, not a value: it is cut to
   `failure_detail_bytes_max` at a UTF-8 character boundary.
3. A release pins the exact versions of the kernel's Python dependencies and of
   the sandbox runtime (A03); the sandbox interpreter of release v1 is CPython
   3.12, whose `random` module gives A03 rule 4 its list. A vulnerable dependency is answered by a new
   release; a running kernel never updates one.
4. A new release may change ceilings. They bind contract versions issued after
   it; a contract version issued earlier keeps its bounds and executes under them
   even when they exceed the new ceilings, and recorded executions are never
   reinterpreted.

### Formal invariants

```text
ceiling(name) = RELEASE_CEILING_<NAME>
override(ceiling) -> never
over_ceiling -> refusal_or_failure (never truncation)
dependencies pinned_by_release
```

### Required tests

1. Changing an environment variable does not change any ceiling.
2. A request one byte over `surface_request_bytes_max` is refused.

### Consequence

Every generated module sees one closed set of limits, chosen once, and none of
them is a local implementation choice.

## Accepted decision A21 — complete security review for States 0–2

### Normative rules

The review covers every actor and boundary accepted in State 0: the owner and the
agents on the one `mcp` channel behind the host's reverse proxy, agent-written
code, the microservices the kernel calls over their HTTP APIs, the platform
manifest, and the host that holds the installation. Each category below was
determined from those boundaries.

### Formal invariants

```text
state2_security_gate_pass
<-> every_required_category_has_one_outcome
    AND every_APPLICABLE_references_an_accepted_decision
    AND no_UNRESOLVED
```

### Required tests

1. `design_lint --state 2` accepts exactly one complete review record.
2. Every reference resolves to an indexed State 2 decision.

### Consequence

State 3 is blocked if any referenced decision is removed or loses its boundary.

### Security review

Security review: PERFORMED

- authentication_credential_abuse: APPLICABLE; references: A16, A17; affected: M27, M28, owner token, agent tokens, mcp channel, reverse proxy
- secrets: APPLICABLE; references: A03, A15, A16, A17; affected: M23, M24, M28, service credentials, tokens, traces, previews, failure details
- authorization: APPLICABLE; references: A06, A08, A10, A16; affected: M11, M18, M24, M25, M26, M27, owner-only and author actions
- injection_interpreted_input: APPLICABLE; references: A03, A05, A09, A16; affected: M05, M13, submitted code, agent-supplied text, request paths and bodies built from node inputs
- external_callbacks_webhooks: APPLICABLE; references: A08, A09, A11; affected: M10, M11, M26, outbound service calls and untrusted service responses (no inbound callback exists)
- browser_boundary: NOT_APPLICABLE; rationale: the kernel has no HTTP surface of its own and no browser client (K-11), and its only surface is typed MCP operations whose text fields are returned as data to agent clients, which own their rendering
- files_artifacts: APPLICABLE; references: A03, A09, A15, A18; affected: M06, M21, M22, file fixtures, run spool, sandbox exchange directory, value area
- concurrency: APPLICABLE; references: A10, A11, A13, A18; affected: M09, M18, M19, M24, M26, one process and one writer, approval used once, in-flight record before send
- dependencies: APPLICABLE; references: A03, A20; affected: kernel release, Python dependencies, sandbox runtime, bubblewrap on the host
