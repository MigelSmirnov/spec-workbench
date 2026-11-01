# State 5 — Registry public module operations: sessions

## Status

Draft of 2026-11-01. The operations of `owner_sessions`, which hold the
owner's runtime state and never touch the store, and of `agent_sessions`,
which keep the agent sessions' records. Every one follows
`50_public_apis_0_conventions.md`.

## `public_op:owner_sessions.sign_in_owner`

### Owner

`module:owner_sessions`. Sign the owner in with the owner credential under
the instance's lockout, making a new owner session (A13 rules 1, 3, 4).

### Callers

`module:operations`.

### Inputs

The presented credential, or none.

### Outputs

The new session's identity and its CSRF value, or `unauthenticated`
(`sign_in_refused`).

### Observable effect

A new owner session (M11) with its sign-in reading of
`clock.monotonic_reading`, no pending confirmation and no uploaded file; the
refusal count cleared. A refused sign-in outside a lockout counts at its
reading; the fifth less than 15 minutes old starts a 15-minute lockout.

### Enforces

During a lockout every sign-in is refused, the right credential included,
and is not counted; the lockout is not extended; the credential is compared
through `random_values.equal_in_constant_time`; one answer whatever was
wrong, never echoing it; concurrent sign-ins counted one at a time; other
open sessions stay (A13 rules 2–4). The identity and the CSRF value come
from `random_values.make_secret_value`.

### Errors

`unauthenticated` (`sign_in_refused`).

### State impact

Runtime state only; no store transaction, no audit entry (A14 rule 2).

## `public_op:owner_sessions.admit_owner_request`

### Owner

`module:owner_sessions`. Admit one owner request: the session check at
arrival, the CSRF check for a change, and the locks a change takes (A13
rules 2, 5; A16 rule 2).

### Callers

`module:operations`.

### Inputs

The session identity from the cookie, or none; whether the request is a
change; the CSRF value it carries, for a change; whether it reads or
changes an uploaded file; the request's step, which receives the admitted
session.

### Outputs

The step's answer, or the refusal. For a change the step runs holding the
session's lock — and first the instance's import lock when it reads or
changes an uploaded file — and both are released when the step returns, on
every path (Conventions, "Locks of an owner request").

### Observable effect

A request carrying a valid session restarts its 30 minutes at its arrival,
whatever its answer — a CSRF refusal included; of concurrent arrivals the
latest counts (A13 rule 2).

### Enforces

A session past 8 hours from sign-in, 30 minutes without a request, or signed
out serves no request; a change carries the CSRF value of its session,
compared in constant time (A13 rule 5); the import lock is taken before the
session's lock, and both are held until the request is done (A16 rule 2);
the session's lock is granted in the order the requests passed the session
check, so its changes apply one at a time in that order; a request that
passed completes even if a limit or a sign-out comes while it runs (A13
rule 2).

### Errors

`unauthenticated` (`no_owner_session`); `not_permitted` (`csrf_refused`).

### State impact

Runtime state only.

## `public_op:owner_sessions.sign_out_owner`

### Owner

`module:owner_sessions`. End the owner's session in its turn among the
session's changes (A13 rule 2).

### Callers

`module:operations`.

### Inputs

The admitted session: the step of a sign-out request, which
`admit_owner_request` runs holding the import lock and the session's lock.

### Outputs

That the session ended.

### Observable effect

The session ends; its pending confirmation and its uploaded file are
dropped (M11).

### Enforces

Its turn comes after every change of the session that passed the session
check before the sign-out did, the session's lock being granted in that
order: each completes, its change to the store included, and leaves nothing
in the ended session; a request arriving after it is refused at the session
check. It goes on when the import is closed (A16 rule 2).

### Errors

`unauthenticated` (`no_owner_session`) when no valid session is named.

### State impact

Runtime state only.

## `public_op:owner_sessions.show_confirmation_step`

### Owner

`module:owner_sessions`. Make the session's pending confirmation for an
action that asks for one (A13 rule 6).

### Callers

`module:operations`.

### Inputs

The admitted session; the action; its target; the revision or access
version the step shows, or that it shows none; the action's inputs — for an
erasure its choice, for the import the file's digest with the picks, names,
aliases and Customer values, for an erasure of old entries the date.

### Outputs

The confirmation value, for the step's form only.

### Observable effect

The session's pending confirmation is replaced: a new value from
`random_values.make_secret_value`, bound to the action, its target, what the
step showed and the digest of its inputs in a fixed order, and the reading
of `clock.monotonic_reading` it was shown at.

### Enforces

A session holds at most one pending confirmation; the inputs are kept as
their digest, never as values; the value never appears in a URL, a log
line, a diagnostic or an entry (A13 rules 6, 7).

### Errors

None of its own; `migration_import` decides whether the import's step may be
shown (A16 rule 1).

### State impact

Runtime state only.

## `public_op:owner_sessions.take_confirmation`

### Owner

`module:owner_sessions`. Decide whether a submission carries the session's
pending confirmation, and use it up (A13 rule 6).

### Callers

`module:operations`.

### Inputs

The admitted session; the confirmation value the submission gives, or none;
the action, its target, the revision or access version it states or that it
states none, and the digest of its inputs.

### Outputs

That the submission is confirmed, or the refusal.

### Observable effect

A value equal to the pending one is used up from here on, whatever the
answer, a binding to another action, target, revision or inputs included; an
expired one is cleared; another value while the pending one is valid leaves
it as it was. A session without a pending value — never shown, used up or
cleared — keeps no memory of earlier values, so any value then is
`confirmation_not_pending`.

### Enforces

Valid only in its session and for 10 minutes by `clock.monotonic_reading`;
compared in constant time; it is not the confirmation id, which
`operations` mints only once the action is accepted (A14 rule 5).

### Errors

`confirmation_refused` (`confirmation_not_pending`,
`confirmation_other_value`, `confirmation_bound_elsewhere`,
`confirmation_expired`).

### State impact

Runtime state only.

## `public_op:owner_sessions.keep_uploaded_file`

### Owner

`module:owner_sessions`. Keep an accepted upload in the session's memory,
replacing the session's earlier one (A16 rule 2).

### Callers

`module:operations`.

### Inputs

The admitted session, holding the import lock and its own lock; the file's
bytes and the digest `migration_import.read_import_mapping` computed of them
when it accepted them.

### Outputs

That the file is kept.

### Observable effect

The session's earlier upload — one of the same bytes included — is replaced.

### Enforces

Kept in the process's memory only, never in the store or on a disk; changed
only by a holder of the import lock (A16 rule 2); `personal_data` (State 1).

### Errors

None.

### State impact

Runtime state only.

## `public_op:owner_sessions.read_uploaded_file`

### Owner

`module:owner_sessions`. Give back the session's kept upload (A16 rule 2).

### Callers

`module:operations`.

### Inputs

The admitted session, holding the import lock and its own lock.

### Outputs

The kept file's bytes and digest, or that none is kept.

### Observable effect

None.

### Enforces

Only the session that uploaded a file reads it.

### Errors

None; "none kept" is the answer, which `migration_import` refuses
(`file_not_kept`).

### State impact

Runtime state only.

## `public_op:owner_sessions.drop_uploaded_files`

### Owner

`module:owner_sessions`. Drop every owner session's upload once an import is
accepted (A16 rule 2).

### Callers

`module:operations`.

### Inputs

The import lock, held by the accepted import's request.

### Outputs

That every upload is dropped.

### Observable effect

No session keeps an uploaded file.

### Enforces

Done after the import's transaction committed and before the import lock is
released, so no upload lands after the import that closed it (A16 rule 2).

### Errors

None.

### State impact

Runtime state only.

## `public_op:owner_sessions.end_expired_sessions`

### Owner

`module:owner_sessions`. The pass, every 60 seconds from the start, that
ends every session past a limit (A13 rule 2).

### Callers

`module:instance_lifecycle`.

### Inputs

None.

### Outputs

How many sessions it ended.

### Observable effect

Each session past 8 hours or 30 minutes without a request ends, with its
pending confirmation and its uploaded file.

### Enforces

The pass alone ends sessions by their limits, taking the import lock and
then each session's lock and deciding under them, each session by a reading
of `clock.monotonic_reading` taken once its lock is held (A13 rule 2).

### Errors

None.

### State impact

Runtime state only.

## `public_op:agent_sessions.register_session`

### Owner

`module:agent_sessions`. Record the agent session Kernel names (A11 rule 1,
R0-53).

### Callers

`module:operations`.

### Inputs

The transaction; the session identity Kernel gives; the action's instant.

### Outputs

The session's access and `changed`.

### Observable effect

A new session (M06): empty set, no active project, no request, access
version 1, its registration instant. A registered session is answered
unchanged (A05).

### Enforces

The identity is recorded as given, never minted (R0-53); a registration of
an ended identity makes a new session with an empty set (A11 rule 4); no
entry (A11 rule 6).

### Errors

None of stages (3) to (6).

### State impact

Writes one session record.

## `public_op:agent_sessions.check_agent_call`

### Owner

`module:agent_sessions`. Stage (2) of every agent-authority call other than
the registration: the session registered and, for an operation on a project,
the project in its set (A10 rules 1–3, 5).

### Callers

`module:operations`.

### Inputs

The transaction; the session identity; whether the operation is on a
project; the project it names, or none to use the active one — for a
withdrawal the project of the pointer, which `operations` resolved before;
a withdrawal whose pointer does not exist never reaches this operation:
`operations` answers it `not_found` (`agent_call_refused`) itself, the same
answer as every refusal here (A08 rule 7, A10 rule 3).

### Outputs

The project the call acts on — the named one, or the active one when none
is named — or `not_found` (`agent_call_refused`).

### Observable effect

None.

### Enforces

An unregistered session, a project outside the set and no active project
when none is named are one answer, as a project that does not exist, and it
hides every later failure (A10 rule 3); checked in the call's own
transaction, so a revocation holds from the next call (A10 rules 5, 6); a
session's own operations — reading its access, requesting access, ending it
— need only the registered session.

### Errors

`not_found` (`agent_call_refused`).

### State impact

Reads the session.

## `public_op:agent_sessions.request_project_access`

### Owner

`module:agent_sessions`. Record the session's pending request in free text,
replacing the earlier one (A12 rule 4, M08).

### Callers

`module:operations`.

### Inputs

The transaction; the session; the request text; the action's instant.

### Outputs

That the request is pending — nothing about which projects exist (R0-47).
It changes state whenever accepted, so it answers no `changed`.

### Observable effect

The pending request is replaced and the access version moves by one.

### Enforces

The text is required (A02); it states no version (A12 rule 4); no entry
(M09).

### Errors

`invalid_request` (`missing_value`).

### State impact

Writes the session's request and version.

## `public_op:agent_sessions.read_session_access`

### Owner

`module:agent_sessions`. The session's access (State 1, "Projections and
answers").

### Callers

`module:operations`.

### Inputs

The transaction; the session identity.

### Outputs

The granted ids by `project_id`, the active project or none, whether a
request is pending, and the access version (A06 rule 8, A12 rule 5).

### Observable effect

None.

### Enforces

No `personal_data` value: the answer is `business_confidential` (R0-64).

### Errors

`not_found` (`unknown_session`) for the owner; for Kernel stage (2) refused
before.

### State impact

Reads the session.

## `public_op:agent_sessions.list_sessions`

### Owner

`module:agent_sessions`. The registered sessions for the owner (A06 rule 5).

### Callers

`module:operations`.

### Inputs

The transaction.

### Outputs

Every session by registration instant, then identity, each with its access
and its pending request's text.

### Observable effect

None.

### Enforces

A06 rule 5's order, as `store` reads it.

### Errors

None.

### State impact

Reads sessions.

## `public_op:agent_sessions.answer_access_request`

### Owner

`module:agent_sessions`. The owner's answer to a pending request: decline,
or grant the project the owner picked (A12 rule 3, M08).

### Callers

`module:operations`.

### Inputs

The transaction; the session; the stated access version; decline or grant
with the picked project and whether to make it active; what
`projects.validate_project_reference` answered for it.

### Outputs

The session's access, whether a project joined the set, and `changed`.

### Observable effect

The request is cleared; for a grant the project joins the set — and, if
asked, becomes active; the version moves once for the whole answer (A12
rule 1). A decline keeps no reason.

### Enforces

Stages (3) to (6): an unknown session or project; a stale version (A12 rule
3); a request no longer pending, an archived project (R0-70). A project
already in the set adds nothing, and the answer still clears the request.

### Errors

`not_found` (`unknown_session`, `unknown_project`); `stale`
(`stale_access_version`); `refused` (`not_pending`, `archived`).

### State impact

Writes the session.

## `public_op:agent_sessions.grant_project`

### Owner

`module:agent_sessions`. Add a project to a session's set without a request,
and, if asked, make it active (R0-46).

### Callers

`module:operations`.

### Inputs

The transaction; the session; the stated access version; the project; whether
to make it active; what `projects.validate_project_reference` answered for
it.

### Outputs

The session's access, whether the project joined the set, and `changed`.

### Observable effect

The project joins the set and, if asked, becomes active; one version move.

### Enforces

A project already in the set is unchanged (A05), and making it active then is
a change of the active project only; an archived project is never granted or
made active (R0-70).

### Errors

`not_found` (`unknown_session`, `unknown_project`); `stale`
(`stale_access_version`); `refused` (`archived`).

### State impact

Writes the session.

## `public_op:agent_sessions.set_active_project`

### Owner

`module:agent_sessions`. Make a project of the set active, or clear the
active project (M06, R0-70).

### Callers

`module:operations`.

### Inputs

The transaction; the session; the stated access version; the project, or
none to clear; whether it is archived, from `projects`.

### Outputs

The session's access and `changed`.

### Observable effect

The active project changes or is cleared; the version moves by one.

### Enforces

Clearing revokes nothing; a project not in the set is not granted; an
archived project cannot be made active, already active included (A05 rule
4); one archived while active stays active (M06); no entry (M09).

### Errors

`not_found` (`unknown_session`); `stale` (`stale_access_version`); `refused`
(`not_granted`, `archived`).

### State impact

Writes the session.

## `public_op:agent_sessions.revoke_project`

### Owner

`module:agent_sessions`. Remove a project from a session's set (R0-46).

### Callers

`module:operations`.

### Inputs

The transaction; the session; the stated access version; the project.

### Outputs

The session's access.

### Observable effect

The project leaves the set, and the active project when it was; the version
moves by one.

### Enforces

A project not in the set answers that it is not granted (A05 rule 4); from
the next call on, `check_agent_call` refuses it (A10 rules 5, 6).

### Errors

`not_found` (`unknown_session`); `stale` (`stale_access_version`); `refused`
(`not_granted`).

### State impact

Writes the session.

## `public_op:agent_sessions.end_session`

### Owner

`module:agent_sessions`. End a session, which removes its record (A11 rules
2, 3).

### Callers

`module:operations`.

### Inputs

The transaction; the session; for the owner the access version seen, for
Kernel none (A12 rule 3).

### Outputs

That the session ended.

### Observable effect

The session's record — set, active project, request, version — is removed;
the entries that name it stay.

### Enforces

Ending is the one end of a session (A11 rule 2); ending an unregistered one
is refused as an unregistered session (A11 rule 5); no entry (A11 rule 6).

### Errors

`not_found` (`unknown_session`); `stale` (`stale_access_version`) for the
owner.

### State impact

Removes one session record.

## `public_op:agent_sessions.drop_project_from_sessions`

### Owner

`module:agent_sessions`. Remove an erased project from every session's set
and active project (R0-61).

### Callers

`module:operations`.

### Inputs

The transaction; the project being anonymised or deleted whole.

### Outputs

The sessions it changed.

### Observable effect

The project leaves every set and active project; each session it changed
moves its version once (A12 rule 1).

### Enforces

Done in the erasure's own transaction; no revocation entry (M09).

### Errors

None.

### State impact

Writes the sessions that held the project.
