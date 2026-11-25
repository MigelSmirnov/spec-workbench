# State 2 — Registry access rules: service tokens, agent sessions, the owner's sign-in

Draft of 2026-10-31. The owner accepted the proposals behind these decisions on
2026-10-31 (answers 6–9 of the State 2 plan). They settle what State 0 carried
here: what each service token and Kernel's agent authority may do and receive
(R0-27, R0-31), what ends an agent session (R0-42, R0-47), the access version
(State 1 M06), and the owner session's lifetime and sign-in throttling (R0-30).

## Accepted decision A09 — each token names its service, its operations and its highest class

### Normative rules

1. Every service token names one service; Registry knows from its own release
   which operations that service may call and the highest disclosure class it
   may receive (R0-26, R0-27): the rows of rule 2, which the code reads as the
   imported `SERVICE_RIGHTS` constant and the imported
   `SERVICE_HIGHEST_CLASSES` constant (SPEC_STANDARD §15.3.1; State 1 M23,
   M24). An operation no row names for the service is refused (rule 3). The
   configuration holds the tokens, not their rights (R0-20, R0-23).
2. The services and their rights:

   | service | operations | highest class |
   |---|---|---|
   | PresuPro | validate a project reference; read a project context; read a customer's billing data; list artifacts; read the latest artifact of a type | `personal_data` |
   | Client Portal | validate a project reference; read a project context; read a project; list rooms; list artifacts; read the latest artifact of a type | `personal_data` |
   | Cabinet | list projects; read a project context; validate a project reference | `personal_data` |
   | Cabinet Kernel | with agent authority only (A10): register an agent session; end an agent session (A11); read the session's access; request access to a project; validate a project reference; read the agent projection; list rooms; add a room; list artifacts; read the latest artifact of a type; publish and withdraw an artifact pointer (R0-88) | `business_confidential` (R0-74) |

3. An operation outside a token's row is refused, whatever the request holds.
4. The classes are ordered `open` < `business_confidential` <
   `personal_data` (R0-26). An answer that would carry a class above the
   token's highest is refused whole; Registry never answers part of it.
   The first release cannot give such an answer: no answer Cabinet Kernel
   can reach carries a field the imported `PERSONAL_DATA_FIELDS` constant
   lists, and every other service's highest class is `personal_data`, the
   highest. The check is made on every answer all the same, and it is shown
   on a test release whose class tables — the imported
   `SERVICE_HIGHEST_CLASSES` constant and the imported
   `PERSONAL_DATA_FIELDS` constant (SPEC_STANDARD §15.3.1) — differ from the
   first release's in the one row a test gives (Required tests 5 and 6). Restated on 2026-11-24, under the
   owner's direction of that day (data-protection matrix P3 and D3: the
   measure that keeps `personal_data` from the agent and its AI provider is
   confirmed by a test, `sources/privacy_requirements_20261123.md`).
5. Every owner action is made in an owner session (A13), never with a service
   token; no token carries the owner's rights.
6. A new service, or a change of a row, enters by a specification change and a
   release (R0-27, R0-33).

### Formal invariants

```text
call(op) with token of service s accepted => op in rights(s)   -- A09-1
class(answer(op)) <= highest_class(s)   -- A09-2
highest_class(Cabinet Kernel) = business_confidential   -- A09-3
```

### Required tests

1. Cabinet calling 'read a customer's billing data' is refused.
   Shows A09-1. [witness: verification:registry_a09_cabinet_billing_read_refused]
2. Client Portal reading `context` receives the address; Kernel calling
   `context` is refused.
   Shows A09-1. [witness: verification:registry_a09_context_portal_answered_kernel_refused]
3. A token not in the configuration is refused like a wrong one (R0-23).
4. PresuPro calling 'publish an artifact pointer' is refused (R0-88).
   Shows A09-1. [witness: verification:registry_a09_presupro_publish_pointer_refused]

5. On a test release whose class tables give a service a highest class
   below a class one of its answers carries, that answer is refused whole:
   no field of it is disclosed (rule 4).
   Shows A09-2. [witness: verification:registry_a09_answer_above_class_refused_whole]
6. An answer to Cabinet Kernel carrying `business_confidential` is answered;
   on a test release whose imported `PERSONAL_DATA_FIELDS` constant names a
   field of an answer Kernel can reach, that answer is refused whole. Shows A09-3, A09-2.
   [witness: verification:registry_a09_kernel_highest_class_business_confidential]
7. Cabinet's 'read a customer's billing data', refused on the first release,
   is answered on a test release whose rights table adds it to Cabinet's row,
   the configuration — the same tokens — unchanged; the first release again
   refuses it (rules 1, 6).
8. No service token reaches an owner action: each of the four tokens asking
   for creating a project, recording a customer, archiving a project,
   granting a project to a session or erasing audit entries is refused as
   outside its rights, and nothing changes (rule 5).

### Consequence

Denial is the default (R0-27); every right is listed in one table, and the
manifest record derives from it (R0-78).

Restated on 2026-11-24, under the owner's direction of that day
(data-protection matrix P6 and D2: every security measure names the test
that confirms it), after the witness review
(`tests/semantic/review/SUMMARY.md`, findings 5 and 12) found rules 1 and 5
without a Required test and rule 4 shown only on a test release no rule
named: tests 7 and 8 show rules 1, 5 and 6, and rule 4 names the test
release tests 5 and 6 are made on. No right and no class changed.

## Accepted decision A10 — every agent-authority call is checked three times by Registry

### Normative rules

1. A call with agent authority is accepted only when the token is Cabinet
   Kernel's, the session it names is registered, and — for an operation on a
   project — the project is in that session's set (R0-46, R0-53).
   'Register an agent session' is checked for the token only: the session it
   names is the one it registers (R0-53).
2. An operation on a project that names none uses the session's active
   project; with none active it is refused (R0-69).
3. Every refusal of the third check, and of a project that does not exist, is
   the same answer as for a project that does not exist (R0-47); a call naming
   an unregistered session is answered as a call outside the set (R0-53).
   The same answer is the same whole answer: its code, its stage, its one
   failure's kind and that failure's path, which is built from the request
   alone — the name of the input by which the request names its target, the
   project or the pointer, or the session for an operation on neither, and
   never an id's value or a fact of a stored record — so two requests that
   differ only in the ids they give, or in whether their session is
   registered, are answered equal, field for field (A08 rule 7). Restated on
   2026-11-24, under the owner's direction of that day (data-protection
   matrix S10 and the agents' row on authority limited to the task), after the witness review
   (`tests/semantic/review/SUMMARY.md`, finding 4) found that the path was
   not fixed, so a test could compare the answers only without it.
4. A write with agent authority on an archived project of the set is refused
   (R0-12, R0-70); reads of it are answered.
5. The check is made at every call, a running flow's next step included; a
   revocation holds from the next call on (R0-46).
6. A call and every change of its session — a revocation, an archiving, the
   session's end — are applied one at a time: a call whose transaction
   commits before the change is accepted, one that commits after it is
   checked against the changed session and refused when the change removed
   its right. No answer and no record tells whether a call committed before
   or after a change of its session — adding a room, publishing and the
   reads write no audit entry (M09) — so no test through Registry's surfaces
   shows this rule. It is shown by the flows (State 4), in which every
   agent-authority call, a read included, takes the store's one write lock
   and checks its session inside that transaction, and checked by the
   Factory on the code that implements them; it is carried to Factory
   verification (owner's direction of 2026-11-24, data-protection matrix
   P6, D2).

### Formal invariants

```text
agent_call(session x) accepted, other than registering x => token = Kernel
and registered(x) and, for an operation on project p, p in granted(x)   -- A10-1
answer(p not in granted(x)) = answer(p does not exist)   -- A10-2
```

### Required tests

1. Kernel reading the projection of a project outside the set receives the
   not-found answer, identical to that of a random id field for field, the
   failure's path included (rule 3); so is the answer to an unregistered
   session.
   Shows A10-1, A10-2. [witness: verification:registry_a10_outside_set_answered_as_not_found]
2. After the owner revokes a project, the next 'add a room' on it is refused.
   Shows A10-1. [witness: verification:registry_a10_revoked_project_next_call_refused]
3. A call naming no project, with no active project, is refused.
4. 'Add a room' on an archived project of the set is refused.
5. Kernel registers a new session id and is accepted.

### Consequence

Registry does not depend on Kernel's own check (R0-46), and no refusal tells
the agent that a project exists.

## Accepted decision A11 — Kernel registers and ends sessions; ending removes the session

### Normative rules

1. Cabinet Kernel registers a session when its agent session starts, naming
   it from its own run context (R0-53, R0-77); registering a registered
   session answers it unchanged (A05).
2. Cabinet Kernel ends a session when its agent session ends; the owner may
   end any session in the owner interface. Ending is the one end of a session:
   Registry sets no expiry of its own.
3. Ending removes the session's record — its set, active project, pending
   request and access version. The audit entries that name it stay (M09).
4. After its end a session is unregistered: a call naming it is refused as for
   an unregistered session (A10). Cabinet Kernel names every agent session
   with an identity it never uses again, so an ended identity is never
   registered again and the audit entries naming it mean one session; Registry
   relies on this as it relies on Kernel naming the session (R0-53, R0-77).
   A registration of an ended identity, Kernel's defect, makes a new session
   with an empty set.
5. Ending a session that is not registered is refused as for an unregistered
   session.
6. Registering and ending write no audit entry (M09): the grants that ended
   with the session are recorded by their own entries.

### Formal invariants

```text
end(x) accepted => not registered(x) and no record of x remains   -- A11-1
register(x) after end(x) => granted(x) = {} and active(x) = none   -- A11-2
```

### Required tests

1. After Kernel ends a session, reading its access is refused.
   Shows A11-1. [witness: verification:registry_a11_ended_session_access_read_refused]
2. Registering the ended identity again answers a session with no project.
   Shows A11-2. [witness: verification:registry_a11_reregistered_ended_identity_empty]
3. The owner ends a session; its next agent-authority call is refused.
   Shows A11-1. [witness: verification:registry_a11_owner_ended_session_call_refused]

4. After a session ends the store holds no record of it: neither its set, its
   active project, its pending request nor its access version.
   Shows A11-1. [witness: verification:registry_a11_ended_session_leaves_no_record]

### Consequence

Registry holds only living sessions; a stale session cannot keep a grant.

## Accepted decision A12 — the access version is a session's revision

### Normative rules

1. A session's access version is 1 at registration and moves by one with each
   accepted action that changes its granted set, its active project or its
   pending request (M06) — a project leaving the set by its erasure included
   (R0-61). One action moves it once, however many of these it changes:
   granting a project and making it active is one move.
2. A change that changes nothing (A05) leaves it. Ending a session states the
   current version and removes the session with it (A11); it makes no next
   version.
3. The owner's actions on a session — granting, revoking, changing or clearing
   the active project, answering a request, ending the session — state the
   access version the owner saw; a stale one is refused and nothing changes.
   Kernel's 'end an agent session' states none: its agent session has ended,
   whatever the session's access.
4. Kernel's 'request access to a project' states none: a new request always
   replaces the pending one (R0-46) and moves the version.
5. 'Read the session's access' answers the current version (R0-32).

### Formal invariants

```text
owner_action(x, stated v) with v != version(x) => refused, x unchanged   -- A12-1
accepted change of x other than its end => version(x)' = version(x) + 1   -- A12-2
```

### Required tests

1. The owner opens a session while the agent replaces its request; granting
   with the old version is refused.
   Shows A12-1, A12-2. [witness: verification:registry_a12_grant_with_replaced_request_version_refused]
2. Erasing a project in two sessions' sets moves both versions by one.
   Shows A12-2. [witness: verification:registry_a12_erasure_moves_both_session_versions]
3. Granting a project already granted leaves the version.
4. Granting a project and making it active in one action moves the version
   by one.
   Shows A12-2. [witness: verification:registry_a12_grant_and_activate_moves_once]

5. The owner ending a session stating a stale access version is refused; the
   session stays registered and unchanged.
   Shows A12-1. [witness: verification:registry_a12_stale_owner_end_refused_unchanged]

### Consequence

The owner never answers a request the agent has since replaced, and Kernel
sees every change as a new version.

## Accepted decision A13 — the owner signs in to a session of bounded life

### Normative rules

1. The owner signs in with the owner credential (R0-30) and receives an owner
   session (M11), carried by a cookie that scripts cannot read, sent only over
   HTTPS when the interface is reached from another machine (R0-29), and only
   to the owner interface's host name: the cookie is host-only, set without
   `Domain`. A browser sends a host-only cookie to every port of its host
   name, so the deployment gives the owner interface a host name of its
   own, under which no other HTTPS service answers — on the home server not
   the kernel workplace, the gateway or PresuPro — and no other service of
   the same host receives the owner session cookie. Decided on 2026-11-25
   under the owner's direction of 2026-11-24 (data-protection matrix row
   P6: integrity and confidentiality of the session), after the State 2
   round-120 (T28) found that a cookie cannot be held to one origin, its
   port included, as this rule then said; the owner may reverse it. The
   host name is a fact of the deployment, which Registry cannot check, as
   the addresses are (A17 rule 1): providing it and keeping every other
   HTTPS service of the host off it is a deployment step, carried to the
   deployment's owner (the Factory's platform deployment).
2. The session ends at the first of: 8 hours after sign-in; 30 minutes without
   an owner request; the owner's sign-out; the instance's restart (M11 is never
   durable). Every duration in this decision — the 8 hours, the 30, 15 and 10
   minutes, the 60 seconds — is measured by the process's monotonic clock,
   which a change of the wall clock does not move and which counts the time
   the host or its VM was suspended, so a session does not outlive a
   suspension; instants Registry records
   and A18's daily time, the imported `BACKUP_DAILY_TIME_UTC` constant, are
   UTC wall-clock time. Each duration is one value
   of the release, the data provider's constant the code imports
   (SPEC_STANDARD §15.3.1): `OWNER_SESSION_MAX_HOURS` (8),
   `OWNER_SESSION_IDLE_MINUTES` (30), `SIGN_IN_WINDOW_MINUTES` and
   `SIGN_IN_LOCKOUT_MINUTES` (15), `CONFIRMATION_VALID_MINUTES` (10),
   `SESSION_PASS_SECONDS` (60); the five refusals of rule 3 are
   `SIGN_IN_REFUSAL_LIMIT`. Both readings reach the code
   through `clock` alone, emitted from the `system_clock_backend` IR whose
   `time_source_policy` the data closure declares (SPEC_STANDARD §6.8). An owner session is never
   recorded (M11), so its instants — when it began, its last request, when
   its confirmation was shown — and its expiry at the latest are held as
   readings of that monotonic clock, and only they decide its limits; the
   UTC rule for recorded times does not reach them. A session that has reached a
   limit serves no request from that
   moment: a request carrying it is refused at the session check. Registry
   ends it — and drops its pending confirmation and its uploaded file with it
   (M11) — at a pass over the sessions it makes every 60 seconds from the
   start; the pass alone ends sessions by their limits, taking the import
   lock and then each session's lock (A16 rule 2) and deciding under them. An owner
   request is any request to the owner interface that
   carries the valid session, whatever its answer; its arrival restarts the 30
   minutes — of concurrent requests the latest arrival counts; before the
   first request it runs from the sign-in. Validity is
   checked when a request arrives (A04 rule 6, stage 1) — an upload, whose
   form sends its CSRF value before its file (A19 rule 4), arrives when that
   head, at most the imported `UPLOAD_FORM_HEAD_MAX_BYTES` constant, has been
   read (owner, 2026-11-17); a request that
   passes it completes even if a limit or a sign-out comes while it runs, and
   a restart that interrupts it leaves nothing of it (A04 rule 4). Several
   owner sessions may be open at once; signing in ends none of the others.
   A sign-out is applied in turn with the session's other requests that
   change it: one admitted before it completes its change to the store, and
   leaves nothing in the ended session.
   The requests of one owner session that change its state — showing a
   confirmation step, uploading a file, a submission, a sign-out — are
   applied one at a time, in the order in which they take the session's one
   lock, after passing the session check — those that read or change an
   uploaded file take the import lock before it (A16 rule 2): each sees the
   session as the one before left it, and other requests are not held by
   them, so a confirmation
   bound to a file a later upload replaced is refused (A16 rule 2).
3. Registry counts the sign-ins refused for a wrong or missing credential
   whose instant is less than 15 minutes before now, for the whole instance:
   Registry tells no callers apart by address (R0-27). The fifth such refusal
   starts a lockout that lasts while now is less than 15 minutes after that
   refusal. During the lockout every sign-in is refused — the right credential
   included — and is not counted; the lockout is not extended. A successful
   sign-in clears the count. Count and lockout are runtime state, like the
   owner session, and a restart clears them. Concurrent sign-ins are counted
   one at a time, in the order they take the instance's one sign-in lock,
   under which each takes its monotonic reading, compares the credential,
   reads the count, decides and updates it, and only then releases it.
4. A refused sign-in answers the same whatever was wrong, and never echoes
   the credential. Sign-in is the one owner request made without a session:
   it is checked for the credential and the lockout only, carries no CSRF
   value, and the session cookie it sets is sent only to the owner
   interface's host name (rule 1).
5. Every change in the owner interface carries the CSRF protection bound to
   its session (R0-29); one from another session or none is refused.
6. An action that asks for confirmation (Identity formats) is submitted with a
   confirmation value Registry made when it showed the step: one-time, kept in
   the owner session, bound to the action, its target, the revision or access
   version the step showed, or that it showed none when the action has
   neither (a record without a revision, A04 rule 3, among them), and its
   inputs — for the import, the file's digest
   and the picks — kept as a digest of those values in a fixed order, never
   as the values themselves; a submission's inputs are bound when their digest
   equals it. A session holds at most one: showing a confirmation step
   replaces the one pending (M11). It is valid only in that session, while
   less than 10 minutes have passed since it was shown, and is used up by the first submission that carries it, whatever
   its answer; a refused submission needs the step shown again. A submission
   carries it when it passes the owner session and CSRF checks (A04 rule 6,
   stage 1) and gives a value equal to the pending one; from there on,
   whatever the answer — a binding to another action or input included — the
   pending value is used up. A submission refused before those checks, or
   giving another value while the pending one is still valid, is refused and
   leaves it as it was. A submission that passes those checks when the
   pending one has expired is refused and clears it, whatever value it
   gives. It is not
   the confirmation id, which Registry mints only when the action is accepted
   (A14).
7. The session's identity, its CSRF value and a confirmation value are each
   as many bytes from the operating system's random source as the imported
   `SECRET_MIN_BYTES` constant names (32, SPEC_STANDARD §15.3.1); each is compared
   in constant time and never appears in a URL, a log line, a diagnostic or an
   audit entry (R0-29, R0-37). The identity travels only in the cookie, the
   other two only in the forms the interface serves. Where they travel and
   where they never appear is shown by Required test 11. That each comparison
   takes constant time and each value is drawn from the operating system's
   random source cannot be seen through Registry's surfaces: it is checked on
   the code, where State 5 routes every such comparison through
   `random_values.equal_in_constant_time` and makes every such value in
   `random_values.make_secret_value` alone, and carried to Factory
   verification (owner's direction of 2026-11-24, data-protection matrix P6,
   D5). Likewise rule 1's HTTPS from another machine: a test reaches
   Registry on its own host only, and Required test 10 shows the cookie's
   attributes that make a browser send it only over HTTPS and only to the
   host name it was set by; that no other HTTPS service answers under the
   owner interface's host name is the deployment's (rule 1).

### Formal invariants

```text
owner_session s, t >= s.began + 8h on the monotonic clock => s not valid at t   -- A13-1
owner_session s, t >= s.last_request + 30min on the monotonic clock => s not
valid at t   -- A13-3
owner_session s signed out before t => s not valid at t   -- A13-4
owner_session s, a restart of the instance since s.began => s not valid at t   -- A13-5
owner_session s, t < s.began + 8h and t < s.last_request + 30min on the
monotonic clock, not signed out, no restart since s.began => s valid at t,
whatever the wall clock reads   -- A13-6
refused_sign_ins(last 15min) >= 5 => sign_in refused   -- A13-2
```

### Required tests

1. A session idle for 31 minutes is refused and asks for sign-in again.
   Shows A13-3. [witness: verification:registry_a13_idle_31_minutes_refused]
2. The sixth sign-in within 15 minutes after five refusals is refused with the
   right credential, and accepted 15 minutes later.
   Shows A13-2. [witness: verification:registry_a13_lockout_refuses_right_credential]
3. A change without the session's CSRF value is refused.
4. A restart ends every owner session.
   Shows A13-5. [witness: verification:registry_a13_restart_ends_owner_sessions]
5. A sign-in during a lockout is refused and does not extend it.
   Shows A13-2. [witness: verification:registry_a13_lockout_sign_in_not_extending]
6. A confirmation value used once — even by a refused submission — is refused
   the second time; one older than 10 minutes is refused.
7. A session with a request every 10 minutes is refused 8 hours after its
   sign-in; a session signed out is refused at its next request, also within
   its 30 minutes.
   Shows A13-1, A13-4. [witness: verification:registry_a13_eight_hours_and_sign_out_refused]
8. A request a microsecond before 30 minutes after the last one is served;
   one exactly 30 minutes after it is refused.
   Shows A13-3, A13-6. [witness: verification:registry_a13_idle_limit_boundary_exclusive]
9. With the clocks replaced in the test: moving the wall clock back or
   forward by hours changes no session's validity; a suspension of 31
   minutes, counted by the monotonic reading, makes its next request
   refused, a submission of its pending confirmation included; the next pass
   ends that session and no other.
   Shows A13-3, A13-6. [witness: verification:registry_a13_monotonic_clock_decides_validity]
10. Signing in sets the session cookie the imported
    `OWNER_SESSION_COOKIE_NAME` constant names, with the attributes the
    imported `OWNER_SESSION_COOKIE_ATTRIBUTES` constant lists and no other —
    `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/` and no `Domain`
    (SPEC_STANDARD §15.3.1) — and a refused sign-in sets none (rules 1, 4).
11. The session's identity, its CSRF value and a shown confirmation value
    appear in no URL of a page the interface serves, in no diagnostic and in
    no stored row, the audit entries among them; the identity is not in a
    page, and the CSRF and confirmation values only in its forms (rule 7).
12. A pending confirmation shown for one action, target, version and inputs
    is refused, and used up, when the submission carrying its value changes
    any one of them: another action, another target, another version or
    none, another value of any input, or the same list in another order
    (rule 6).

### Consequence

The owner credential's exposure is bounded in time; the lockout slows a guess
without telling who is guessing.

Restated on 2026-11-24, under the owner's direction of that day
(data-protection matrix P6 and D2, `sources/privacy_requirements_20261123.md`:
every security measure names the test that confirms it), after the witness
review (`tests/semantic/review/SUMMARY.md`, findings 5 and class 2) and the
independent judge of the witnesses found that A13-1 held four limits no one
test shows and that test 9 claimed what no surface shows: A13-1 was
`valid(s, t) <=> t < s.began + 8h and t < s.last_request + 30min and not
signed_out(s) and no restart since s.began`; it is now the 8 hours alone,
and the 30 minutes, the sign-out, the restart and validity within all four
are A13-3, A13-4, A13-5 and A13-6, each test naming the limits it shows.
Test 9 no longer claims that the pass drops the ended session's
confirmation and upload: an ended session cannot be asked about them, and
its requests are refused at the session check before either is read. Rules
1 and 7, which had no Required test, have tests 10 and 11 for what the
surfaces show; the rest of rule 7 and rule 1's HTTPS are carried to Factory
verification, as rule 7 now says. No limit and no behaviour changed.
