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
   may receive (R0-26, R0-27). The configuration holds the tokens, not their
   rights (R0-20, R0-23).
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
5. Every owner action is made in an owner session (A13), never with a service
   token; no token carries the owner's rights.
6. A new service, or a change of a row, enters by a specification change and a
   release (R0-27, R0-33).

### Formal invariants

```text
call(op) with token of service s accepted => op in rights(s)
class(answer(op)) <= highest_class(s)
highest_class(Cabinet Kernel) = business_confidential
```

### Required tests

1. Cabinet calling 'read a customer's billing data' is refused.
2. Client Portal reading `context` receives the address; Kernel calling
   `context` is refused.
3. A token not in the configuration is refused like a wrong one (R0-23).
4. PresuPro calling 'publish an artifact pointer' is refused (R0-88).

### Consequence

Denial is the default (R0-27); every right is listed in one table, and the
manifest record derives from it (R0-78).

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
4. A write with agent authority on an archived project of the set is refused
   (R0-12, R0-70); reads of it are answered.
5. The check is made at every call, a running flow's next step included; a
   revocation holds from the next call on (R0-46).
6. A call and every change of its session — a revocation, an archiving, the
   session's end — are applied one at a time: a call whose transaction
   commits before the change is accepted, one that commits after it is
   checked against the changed session and refused when the change removed
   its right.

### Formal invariants

```text
agent_call(session x, project p) accepted =>
  token = Kernel and registered(x) and p in granted(x)
answer(p not in granted(x)) = answer(p does not exist)
```

### Required tests

1. Kernel reading the projection of a project outside the set receives the
   not-found answer, identical to that of a random id.
2. After the owner revokes a project, the next 'add a room' on it is refused.
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
end(x) accepted => not registered(x) and no record of x remains
register(x) after end(x) => granted(x) = {} and active(x) = none
```

### Required tests

1. After Kernel ends a session, reading its access is refused.
2. Registering the ended identity again answers a session with no project.
3. The owner ends a session; its next agent-authority call is refused.

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
owner_action(x, stated v) with v != version(x) => refused, x unchanged
accepted change of x => version(x)' = version(x) + 1
```

### Required tests

1. The owner opens a session while the agent replaces its request; granting
   with the old version is refused.
2. Erasing a project in two sessions' sets moves both versions by one.
3. Granting a project already granted leaves the version.
4. Granting a project and making it active in one action moves the version
   by one.

### Consequence

The owner never answers a request the agent has since replaced, and Kernel
sees every change as a new version.

## Accepted decision A13 — the owner signs in to a session of bounded life

### Normative rules

1. The owner signs in with the owner credential (R0-30) and receives an owner
   session (M11), carried by a cookie that scripts cannot read, sent only over
   HTTPS when the interface is reached from another machine (R0-29), and only
   to Registry's own origin.
2. The session ends at the first of: 8 hours after sign-in; 30 minutes without
   an owner request; the owner's sign-out; the instance's restart (M11 is never
   durable). An owner request is any request to the owner interface that
   carries the valid session, whatever its answer; its arrival restarts the 30
   minutes — of concurrent requests the latest arrival counts; before the
   first request it runs from the sign-in. Validity is
   checked when a request arrives (A04 rule 6, stage 1); a request that
   passes it completes even if a limit or a sign-out comes while it runs, and
   a restart that interrupts it leaves nothing of it (A04 rule 4). Several
   owner sessions may be open at once; signing in ends none of the others.
   A sign-out is applied in turn with the session's other requests that
   change it: one admitted before it completes its change to the store, and
   leaves nothing in the ended session.
   The requests of one owner session that change its state — showing a
   confirmation step, uploading a file, a submission, a sign-out — are
   applied one at a time, in the order in which they take the session's one
   lock, after passing the session check: each sees the
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
   one at a time.
4. A refused sign-in answers the same whatever was wrong, and never echoes
   the credential. Sign-in is the one owner request made without a session:
   it is checked for the credential and the lockout only, carries no CSRF
   value, and the session cookie it sets is sent only to Registry's origin
   (rule 1).
5. Every change in the owner interface carries the CSRF protection bound to
   its session (R0-29); one from another session or none is refused.
6. An action that asks for confirmation (Identity formats) is submitted with a
   confirmation value Registry made when it showed the step: one-time, kept in
   the owner session, bound to the action, its target, the revision or access
   version the step showed, and its inputs — for the import, the file's digest
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
7. The session's identity, its CSRF value and a confirmation value are each at
   least 32 bytes from the operating system's random source; each is compared
   in constant time and never appears in a URL, a log line, a diagnostic or an
   audit entry (R0-29, R0-37). The identity travels only in the cookie, the
   other two only in the forms the interface serves.

### Formal invariants

```text
owner_session s valid at t <=> t < s.began + 8h and
                                t < s.last_request + 30min and
                                not signed_out(s) and no restart since s.began
refused_sign_ins(last 15min) >= 5 => sign_in refused
```

### Required tests

1. A session idle for 31 minutes is refused and asks for sign-in again.
2. The sixth sign-in within 15 minutes after five refusals is refused with the
   right credential, and accepted 15 minutes later.
3. A change without the session's CSRF value is refused.
4. A restart ends every owner session.
5. A sign-in during a lockout is refused and does not extend it.
6. A confirmation value used once — even by a refused submission — is refused
   the second time; one older than 10 minutes is refused.

### Consequence

The owner credential's exposure is bounded in time; the lockout slows a guess
without telling who is guessing.
