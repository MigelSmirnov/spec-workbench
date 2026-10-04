# State 2 — Cabinet Kernel service, binding and effect rules

Draft of 2026-09-30. Rules for reading the platform manifest, operation
bindings, invoking a service, approvals, standing grants and effect outcomes
(K-03, K-08, K-16). Reuses cabinet-flow decisions 10, 12, 13, 31 and 33 where they
still hold; automatic reconciliation, replay classes, retry schedules and binding
suspension are gone (K-08, K-09, K-17).

## Accepted decision A08 — a binding pins one manifest operation, and a changed record stops it

Reuses cabinet-flow decisions 10 and 31, narrowed: no automatic reissue, no suspension
state, no history search. Closes the State 1 question of what "manifest mismatch"
is.

### Normative rules

1. A `service_id` is one or more lowercase letters, digits and `_` only; any other is
   refused before a path is built. The kernel reads a service's record only from
   `<manifest_location>/<service_id>.json` at the configured `manifest_revision`
   (M28), and only when the file's `service` field equals `service_id`. No other
   path, revision or name is searched.
2. A ManifestOperation M10 is read from the one entry of the record's
   `capabilities` whose `name` equals the operation name, together with the
   `api_base_url` and `required_headers` of the instance the installation selects
   for that service (K-16). Its `record_digest` is the SHA-256 of the canonical
   JSON of that one capability entry, so an edit to another capability of the same
   service changes nothing for this binding.
3. The operation is invocable only when its `exposed_as.http_api` is exactly one
   string of the method, one ASCII space and the path, with nothing before or
   after, whose method is `GET`, `POST`, `PUT`, `PATCH` or
   `DELETE`. An operation exposed only over `mcp` or an
   operator, or over several HTTP routes, is not invocable (K-11).
4. The idempotency key fields are read from the entry's `idempotency_key`:
   `null` means none; otherwise the text split on `+`, each part trimmed, must
   be a list of distinct plain field names, and for an operation other than `read` each
   name must equal the name of one `value` input port of the proposal — a file
   is never a key field. For a `read` operation
   the key is not used and not checked: a read writes no EffectAttempt. The rest of the syntax is
   State 6's. The key travels to the service as those input fields themselves, in
   the places A09 rule 2 gives them; the kernel adds no header or field of its own
   (K-08: "the declared idempotency key"). The EffectAttempt's `idempotency_key`
   is the SHA-256 of the canonical JSON of those fields' values, and absent when
   the manifest declares none.
5. A proposal is refused as a manifest mismatch, naming the first failing
   check in the order listed here, when: the service
   record is absent, is not valid JSON, lacks `service` or `capabilities`, or its
   `service` field differs; two entries of `capabilities` share the name; the operation is absent; its
   `effect_class` is not one of the five of M10; it is
   not invocable by rule 3, including a declared path of a shape A09 rule 1
   refuses; for an operation other than `read`, its `idempotency_key` text breaks rule 4's syntax — an empty part,
   a repeated name, or a name that is not a plain field name — which is a fault
   of the record itself, as the checks before it are; the installation selects no instance for the service or that
   instance has no `api_base_url` — one that is not an absolute `http` or
   `https` URL with a host counts as none — or names one required header
   twice, or names one the kernel sets itself (`host`, `accept-encoding`,
   `content-type`, `content-length`, A10 rule 7) other than `host`, which an
   instance may set instead of the kernel (A10 rule 7), names compared without
   regard to case — at send time both are A09 rule 6's `required_header_repeated`
   —, or has a required header whose name is not an HTTP field-name token, or whose value is empty, has leading or trailing whitespace, or holds a control character — at send time `required_header_invalid`;
   a key field of rule 4 is not a `value` input port of the proposal; or the ports do not fit
   the request shape of A09 rules 2 and 3, in that order, ports taken in name
   order; or its ports break a rule A02 sets for contract ports — unique names
   per direction, a media type exactly on `file` ports — or leave out the class
   M01 requires on each binding input and output. The proposer
   names only service, operation and ports; effect class and key fields are
   copied from the manifest (M11).
6. Before every send, the kernel reads the operation again. When the record
   cannot be read or fails one of rule 5's checks of the record itself — not
   those of the instance, which are A09 rule 6's own — the entry is absent, the operation is no longer invocable, or its digest
   differs from the binding's pin, nothing is sent and the element concludes
   `operation_failed` with detail `binding_stale` (A09 rule 6). The binding
   itself does not change; the owner accepts a new binding and the agent composes
   a new flow version that pins it (K-03). The manifest revision is read at start
   (M28), so a record changes for a running kernel only after a restart with a
   new configured revision.
7. Accepting a binding, by the owner only: an unknown `binding_id` is refused; an
   `accepted` binding is returned unchanged, without reading the manifest, even
   when its digest has changed meanwhile — a change stops its sends (rule 6),
   not its acceptance; a `proposed` one is checked again by every check of
   rule 5, those of the instance included, and, when a check fails — in the
   order rule 5 lists them, the first failing one named — refused naming that check as
   a proposal is (rule 5), with `binding_stale` when only the digest differs;
   otherwise it becomes `accepted`.
8. The kernel never writes the manifest.

### Formal invariants

```text
record_path = manifest_location / service_id + ".json" AT manifest_revision
record_digest = sha256(canonical_json(capability_entry(operation_name)))
invocable(op) <-> count(op.exposed_as.http_api) = 1
effect_class(op) != read AND key_field NOT IN input_ports -> proposal_refused
send(node) -> digest_now(binding) = binding.record_digest
digest_mismatch -> operation_failed(binding_stale) AND nothing_sent
```

### Required tests

1. A proposal for an operation exposed only over `mcp` is refused naming rule 3.
2. A proposal for a `draft-write` operation whose key field `material_id` is not
   an input port is refused.
3. Editing another capability's `note` in the same service record leaves the
   binding invocable.
4. After a restart with a revision that changes the operation's entry, the node
   concludes `binding_stale` and no request reaches the service.
5. A proposal that states its own effect class is refused; the manifest's class is
   the binding's.

### Consequence

The kernel's picture of a service cannot drift from the manifest silently and
cannot be redrawn by an agent; a change stops the effect instead of guessing.

## Accepted decision A09 — one HTTP request per attempt, and its outcome has one name

Reuses cabinet-flow decision 33, narrowed. Closes the State 1 question of how transport
outcomes map to NodeExecution statuses.

### Normative rules

1. An invocation is one HTTP request to the selected instance's `api_base_url`
   joined with the declared path, with the method declared, the instance's
   `required_headers` with their manifest values verbatim — header names compare
   without regard to case, and a record naming one header twice so is a manifest
   mismatch — and the credential
   header the installation holds for that service (A17); an installation whose
   credential header has, compared without regard to case, the name of a required
   header, or of a header the kernel sets itself (A08 rule 5), `host` included,
   refuses to start. The
   URL is the `api_base_url` without a trailing `/` followed by the declared
   path, which must start with one `/` and contain no `//`, no `.` or `..`
   segment, no `?` or `#`, and no scheme or host; a `{` or `}` appears only in a
   placeholder, which is one whole segment `{name}` whose name is not empty and
   contains no `{`, `}` or `/`, and no name is a placeholder twice; a path that
   does not is not invocable (A08 rule 3). Placeholder values are percent-encoded so that they
   stay one segment. Nothing else is normalized. Redirects are not followed; proxy environment
   variables are ignored; nothing is retried inside one attempt.
2. The request is built from the node's inputs: every `{name}` in the path takes
   the input port of that name, which must be a non-null string or integer,
   percent-encoded; for `GET` and `DELETE` the other `value` inputs are query
   parameters, each a string, integer, number or boolean (`true`/`false`) or a
   list of those sent as a repeated parameter, and a `null` value, or a `null`
   element of a list, is omitted; for
   `POST`, `PUT` and `PATCH` they form one JSON object body keyed by port name.
   Query parameters follow port name order by Unicode code point, list elements
   in list order as `name=a&name=b`; numbers and booleans are written as in
   canonical JSON; names and string values are UTF-8 percent-encoded except the
   RFC 3986 unreserved characters, a space as `%20`.
   An input placed in the path is placed nowhere else: not in the query, the JSON
   body or a multipart part. A binding with a `file` input sends, for
   `POST`, `PUT` and `PATCH`, a `multipart/form-data` body with one part per other
   input port, in port name order, named by the port — one part per file, in list order, for a `many`
   file port — a file part carrying its port's media type, a value
   part carrying its canonical JSON (State 1). Each part has exactly two
   headers: `Content-Disposition: form-data; name="<port>"`, with
   `filename="<port>"` added for a file part, and `Content-Type`, the port's
   media type for a file part and `application/json` for a value part, without
   parameters; nothing else. When proposed, a binding is refused unless, by its
   port declarations alone: every `{name}` of the path is an input port whose
   schema's `type` is `string` or `integer`; for `GET` and `DELETE`, no input is a
   `file` and every other input's schema `type` is `string`, `integer`, `number`,
   `boolean`, `null` or an `array` of those; for other methods any schema is
   accepted. A value that still does not fit at send time is a pre-send refusal
   (rule 6).
3. The kernel asks for no content encoding (`Accept-Encoding: identity`); the
   size counted is the response body's bytes after transfer decoding. A
   response is used only when its status is 2xx, its size is within
   `service_response_bytes_max` and it arrived within `transport_timeout_ms`
   (A20). A binding with a `file` output has no other output port and that port
   is `one` — a proposal otherwise is refused — and the body is that file, whose `Content-Type`, compared on type and subtype without regard to case and
   ignoring parameters, must equal the port's media type — a response with no
   `Content-Type` or with two is a `contract_violation`; otherwise the body must be UTF-8 text that
   parses as one JSON object without duplicate member names — its
   `Content-Type` is not checked — and each output port takes the member of the same name, which
   must validate against the port. Members no port names are ignored, and a
   binding without output ports reads the body only up to
   `service_response_bytes_max` — a longer one is `contract_violation` by the
   table of rule 5 — and does not parse or validate it.
4. TLS is verified for `https`. Plain `http` is allowed only for an instance of
   class `local_dev` or `disposable_rig`, as the manifest instance's `class`
   states — an absent or unknown class counts as `production` — or one whose
   `api_base_url` host is a loopback address; any other plain `http` target is refused before sending.
   The host judged here, the one connected to, and for `https` the server name
   sent and verified, are always those of `api_base_url`; a required `Host`
   header (A10 rule 7) changes only the header sent.
5. The outcome of one attempt is decided in this order:

   | what happened | `read` operation | any other operation (EffectAttempt M26) |
   |---|---|---|
   | nothing could be sent: name resolution, connection or TLS failed | `service_unreachable` | `service_unreachable`, attempt `not_sent` |
   | request may have been sent, no valid final response received (timeout, reset, EOF, a malformed status line or headers, only `1xx`) | `service_unreachable` | `outcome_unknown`, attempt `unknown` |
   | status 3xx or 5xx, whatever the body's size — reading stops at the ceiling | `service_unreachable` for 5xx, `operation_failed` for 3xx | `outcome_unknown`, attempt `unknown` |
   | status 4xx, whatever the body's size — reading stops at the ceiling | `operation_refused` | `operation_refused`, attempt `not_applied` |
   | status 2xx, outputs do not fit rule 3, or the body exceeds `service_response_bytes_max`, `stored_value_bytes_max` or the spool ceilings | `contract_violation` | `contract_violation`, attempt `applied` |
   | status 2xx, outputs fit | `succeeded` | `succeeded`, attempt `applied` |

   "Nothing could be sent" holds only when the failure happened before the
   kernel wrote the first byte of the request; any failure after that, before a
   status line arrived, is "may have been sent".
6. A check of the kernel's own that fails before anything is sent is done before
   any EffectAttempt is written. The checks run in this order and the first that
      fails is named: the binding is stale or no longer invocable (A08 rule 6);
   then, in this order, no instance selected, its address missing, plain
   `http` not allowed (rule 4), a required header repeated, a required header
   invalid (A08 rule 5), its credential not resolved (A17); an input
   value cannot be placed in the request (rule 2). The element
   concludes `operation_failed` with a detail naming the check, no EffectAttempt
   exists for it, and its approval stays unused.
7. A response status never by itself means more than this table says. The body of
   an error response is not interpreted; at most `failure_detail_bytes_max` of it
   is kept as `failure_detail`, whose class is the highest of the execution's
   class and the classes the binding declares for its outputs, under A07 rule 5.

### Formal invariants

```text
attempt -> exactly_one_http_request
redirect_followed -> never
http_without_tls -> instance.class IN {local_dev, disposable_rig} OR loopback(host)

non_read AND (possibly_sent AND no_valid_answer) -> outcome_unknown
non_read AND 4xx -> not_applied
non_read AND 2xx -> applied
read AND (not_sent OR no_answer OR 5xx) -> service_unreachable
```

### Required tests

1. A `POST` whose connection drops after the request was written concludes
   `outcome_unknown` and no second request is sent.
2. A `read` answered 503 rests the run `pending` with `service_unreachable`.
3. A `draft-write` answered 409 concludes `operation_refused` with the attempt
   `not_applied`.
4. A 2xx body missing an output port's member concludes `contract_violation`, and
   for a non-read operation the attempt is `applied`.
5. A redirect to another host is not followed and a production `http` target on a
   non-loopback host is refused before sending.
6. A proxy variable in the environment does not change where the request goes.

### Consequence

Every way a call can end has one name that says whether the effect may have
happened, so nothing downstream is built on a guess.

## Accepted decision A10 — an effect runs on the exact input the owner saw, or under the owner's standing grant

Reuses cabinet-flow decisions 12 and 13, narrowed: approval per element (M24), no
generated statements, no suspension.

### Normative rules

1. `draft-write` nodes ask nothing at run time: K-08 lists the classes that stop
   for approval, and `draft-write` is not one; its authority is the owner's
   activation of the flow version (A06). The one exception is a resend after an
   attempt resolved `not_applied`: it needs a fresh approval for every effect
   class, `draft-write` included (K-08, A11): the element then waits with reason
   `owner_approval` like any other. Before sending a `state-transition`,
   `external-effect` or `destructive` node, the kernel needs one of: an approved,
   unused EffectApproval M24 of that run, node and element whose
   `request_digest` equals the digest of the request about to be sent (rule 7) —
   any difference, in an input, the instance's `api_base_url`, a required
   header's name or value or the credential header's name, means the approval
   is no authority for this send: it stays `approved` and unused, void when the
   run ends, and the kernel proceeds as if it did not exist — under a grant
   when one applies, otherwise by asking anew as rule 2 says; or an active StandingGrant M25 for that
   node of the run's pinned flow version, when the node is not `destructive` and
   the send is not a resend after `not_applied` (A11). When both exist, the
   approval is used and recorded as the authority. A resend after
   `not_applied` is a send of an element whose `unknown` attempt the owner
   resolved `not_applied` (A11 rule 3); an attempt answered 4xx is
   `not_applied` too, but concludes its element `operation_refused` (A09 rule
   5) and is never sent again, and no other element or run is affected. A
   fresh approval after `not_applied` is one whose `attempt_number` is greater
   than that of the element's latest attempt resolved `not_applied`; approvals
   requested before it never count. When several approvals count and
   match, the oldest in store order is used (State 5, closed question 2).
   At send time the instance checks are A09 rule 6's, with their own details
   (`instance_not_selected`, `instance_address_missing` — the same "counts as
   none" as A08 rule 5 —, `required_header_repeated`, `required_header_invalid`,
   `plain_http_not_allowed`);
   only the checks of the record itself give `binding_stale` (A08 rule 6).
2. Without either, the kernel records one approval request for the element —
   none when a `requested` one for it already exists, even if the request has
   changed since: when that one is approved and the send's digest differs, rule 1
   applies — the send goes under a grant when one covers it, otherwise a new
   approval is requested — with the exact inputs
   and a preview — service, operation, effect class, the request as rule 7
   describes it with its `request_digest`, the input values and, for each file
   input, its digest, size and media type; an agent reading it gets a `personal_data` value or file only
   as digest and class (A07) — and the element waits with reason `owner_approval`. The owner
   may read the spooled file's bytes through inspection while the run holds them;
   an agent may not.
   For a mapped node each element is one approval.
3. Only the owner decides, and only an approval that is `requested` in a run
   that has not ended; deciding any other is refused. Approving sends the effect at once, in the owner's
   request, and the approval becomes `used` with the attempt's outcome (A11
   rule 1); an attempt that ends `not_sent` leaves it `approved` and unused for a
   resume (M24). The approval itself always succeeds; when a pre-send check then
   fails (A09 rule 6), nothing is sent, the element concludes `operation_failed`
   and the approval stays `approved` and unused, void once the run ends.
   Refusing writes one NodeExecution `refused_by_owner` for the refused element
   and ends the run `refused` (K-08); every other waiting element stops waiting
   without a record of its own, and nothing further is sent.
4. Absence of a decision is not a decision: no time limit approves, refuses or
   ends anything. When a run ends, its undecided and unused approvals can no
   longer be decided or used; their statuses stay as they were, and the ended
   run is what makes them void.
5. Only the owner grants and revokes. A grant is given only for a node of the
   flow's active version whose effect class is not `destructive`; a request for a
   node of any other version is refused, even when an earlier grant for it is
   still active. Granting an already granted node of the active version returns
   the active grant. Revoking takes effect for every
   send after it; an element already waiting then keeps waiting for an approval.
6. A send under a grant records the grant as its authority and the same input
   digests an approval would have covered. A `draft-write` send records as its
   authority the FlowActivation M18 of the run's version, except a resend after
   `not_applied`, which records its fresh approval; a `read` send has no
   EffectAttempt.
7. The request an approval covers is described, before sending, by: the method;
   the full URL with its query (A09 rules 1 and 2); every header sent on the
   wire, names lower-cased and in code-point order, each with its value, except
   that the credential header and `content-length` appear by name only — the
   length follows from the body described — and the `multipart/form-data`
   content type without its `boundary` parameter. The headers sent are exactly:
   `host` — the authority of `api_base_url` exactly as the manifest writes it,
   not normalized (A09 rule 1), unless the instance's required headers name
   `host`, in which case that required header is sent instead, its value
   verbatim, and is the only `host` —, `accept-encoding: identity` (A09 rule 3),
   the instance's other required headers, the credential header, and, with a body, `content-type` and
   `content-length`; the HTTP client adds no other header (no user agent, no
   connection header). The body is described as the JSON body's bytes, or for
   `multipart/form-data` as the parts in order, each as its name, filename when
   present, media type and the SHA-256 of its content, so the boundary is not
   part of it: equal parts give equal descriptions. The `request_digest` is the SHA-256 of the canonical JSON of that
   description. The credential's value is never shown, so rotating it voids no
   approval; any other difference, whatever caused it, is a different request
   (owner decision 18).

### Formal invariants

```text
send(node) AND class IN {state-transition, external-effect, destructive}
-> (approval.status = approved AND approval.unused AND request_digest(send) = approval.request_digest)
   OR (grant.active AND grant.flow_version = run.flow_version AND class != destructive
       AND NOT resend_after_not_applied)
approval_used_at_most_once
no_decision -/> state_change
decider(approval | grant | revoke) = owner
```

### Required tests

1. A run reaching a `state-transition` node sends nothing until the owner
   approves, and sends once after.
2. A mapped node over three photos asks three approvals.
3. A refused approval ends the run `refused` with no request sent.
4. With a grant, the node is sent without asking and the attempt names the grant;
   a `destructive` node cannot be granted.
5. After revocation, the next run of that version asks again.
6. An agent's approval, grant or revocation is refused.
7. After a restart that changed a required header's value of the instance, an
   approval given before it on the same inputs does not cover the send: nothing
   is sent and the element asks again. A restart that only rotated the
   credential's value sends under the approval.
8. An instance at `http://127.0.0.1:8000` whose required headers name
   `Host: portal.example` sends one request to `127.0.0.1:8000` with that one
   `host` header, and the request description shows it; a binding to an
   instance whose required headers name `Accept-Encoding` is refused.

### Consequence

The owner never approves "a flow" in the abstract: the owner approves this
change, to this service, with these values, or said once that this node of this
version may run without asking.

## Accepted decision A11 — an unknown outcome is the owner's to resolve, and attempts share one count

Reuses cabinet-flow decisions 14 and 15, narrowed by K-08: no reconciliation read, no
replay classes. Closes the State 1 questions of attempt numbers and of what the
trace records after the owner resolves an unknown outcome.

### Normative rules

1. For one run, node and element, `attempt_number` is the ordinal of the
   element's NodeExecution M23 records: each NodeExecution written for the
   element takes the next number, from 1, whatever its status — an execution, a
   send, a pre-send failure, an owner's refusal, a skip, an upstream failure, the
   record of a mapped node over an empty list. An EffectAttempt M26 carries the
   number of the NodeExecution that will conclude its send, which is the next
   number when it is written, and an EffectApproval M24 the next number when it
   is requested — the attempt it was requested for — without taking it. Nothing
   else takes or holds a number: waiting for approval writes no NodeExecution,
   and the owner's resolution of an unknown outcome writes no NodeExecution
   (rule 3).
   Reaching an operation element runs in this order: the pre-send checks of
   A09 rule 6 — a failure writes the element's next NodeExecution,
   `operation_failed`; then the authority of A10 rule 1, checked as it stands
   now — none for a `read`, the flow activation for a `draft-write` that is not
   a resend after `not_applied`, otherwise an approval or a grant; without it
   the element waits for approval, and after the approval this
   order starts again; then, for an operation other than `read`, one store call
   writes the EffectAttempt `in_flight`, naming the authority it uses — the
   approval, the grant, or for a `draft-write` send the flow activation
   (A10 rule 6);
   then the request is made; then one store call writes the outcome: the
   EffectAttempt's conclusion, the next NodeExecution, the values it produced,
   and the approval it used marked `used` — unless the attempt ended `not_sent`,
   which leaves it `approved` (M24). A crash between those two calls is the
   `in_flight` case of rule 4, whose recovery also marks that approval `used`.
2. When the outcome is `unknown`, the element's NodeExecution records
   `outcome_unknown`, the element waits with reason `outcome_unknown`, and nothing
   depending on it runs. The kernel never sends again on its own and never infers
   the outcome from an error text or a later read.
3. The owner resolves it: the EffectAttempt becomes `applied` or `not_applied`
   with `resolved_by`, and that is the only record of the resolution; the
   attempt's one NodeExecution keeps `outcome_unknown`. The element's conclusion
   is read from the two records together:
   - EffectAttempt `unknown`: the element waits (rule 2);
   - `applied`, binding without output ports: the element counts as succeeded
     and the run continues;
   - `applied`, binding with output ports: the element counts as failed with
     reason `applied_outputs_unknown` — the effect happened, but no value was
     received for what depends on it;
   - `not_applied`: the element waits again with reason `owner_approval`, and the
     next send, under a fresh approval even where a grant exists (K-08), is the
     next attempt. In the owner's same request the kernel reaches the element
     again: the pre-send checks of A09 rule 6, then, finding no authority, it
     requests the fresh approval for the request as built now (A10 rule 2).
   Resolving is refused unless the named attempt's EffectAttempt is `unknown`
   and its run has not ended.
4. On start, every EffectAttempt still `in_flight`, oldest first in store
   order and one store call per attempt, becomes `unknown`; when its
   attempt has no NodeExecution yet, the kernel writes it with status
   `outcome_unknown`, the binding as what it executed, the inputs the
   EffectAttempt names, no outputs, its start time taken from the EffectAttempt and its end
   time the time of recovery, and, when the attempt's authority is an approval,
   marks that approval `used`, in the same store call, one call per attempt. The element
   waits as in rule 2; the kernel does not ask the service.
5. Cancelling a run whose element waits on an unknown outcome leaves that
   EffectAttempt `unknown`; the kernel claims neither outcome.

### Formal invariants

```text
attempt_number(run, node, element) = ordinal of the element's NodeExecutions
effect_attempt.attempt_number = node_execution.attempt_number (same send)
resolution -> no NodeExecution; resend -> next NodeExecution number
in_flight_recorded_before_send
unknown -> element_waits AND dependants_do_not_run
node_executions_per_attempt = 1   (resolution writes none)
resolution(applied, outputs = none) -> element counts succeeded
resolution(applied, outputs != none) -> element counts failed(applied_outputs_unknown)
resolution(not_applied) -> fresh_approval_required
restart AND in_flight -> unknown
```

### Required tests

1. Killing the kernel between the in-flight record and the answer leaves an
   `unknown` attempt after restart and sends nothing.
2. Resolving `applied` for a binding without outputs continues the run; the trace
   holds one NodeExecution of attempt 1, `outcome_unknown`, and its EffectAttempt
   `applied` with the owner as `resolved_by`.
3. Resolving `not_applied` under a standing grant asks the owner for approval; the
   resend is attempt 2 with its own EffectAttempt.
4. A service error text containing "created" changes nothing.

### Consequence

The kernel says "I do not know" when it does not know, the owner who can check
the service decides, and the trace keeps both the doubt and the answer.
