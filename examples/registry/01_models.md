# State 1 — Registry domain models

## Status

Draft of 2026-10-31, derived from the accepted State 0 (`00_product.md`, R0-75)
and the questions it carried to State 1 ("Carried to later states"). The v1
code (`SOURCE.md`) is evidence of what runs, never a source of norm.

On 2026-10-31 the owner answered the draft's questions: the object has no
identity of its own (M02; "object ids" in R0-50 and R0-80 is a slip, to be
corrected in `00_product.md` by a new owner decision there), and the
proposals under M01, M04 and M10 are accepted as written. What remains open
is marked so under a model's `Open questions`; nothing blocks State 2. The
state is not yet closed by question rounds ("State 1 readiness").

This state names the concepts Registry needs, the facts each carries in domain
words, its identity (`value` or `entity`, `MODEL_IDENTITY_EVIDENCE.md`), who
creates, reads and changes it, its status vocabulary and what is written once.
Types, optionality, the complete field list and every answer shape belong to
State 6; orders, replay mechanisms, correction semantics and token scopes
belong to State 2 (State 0, "Carried to later states").

Every State 1 question the owner must answer is under a model's
`Open questions`; a `BLOCK:` question stops State 2 until answered.

## Modeling boundary

Registry owns identity and trusted context only (R0-01, R0-24): projects,
their objects and rooms, customers, artifact pointers, agent session access,
the migration's closure and its own audit log. Service domain data, Kernel
functions and flows, secrets and configuration (R0-20, R0-23) are not models
of this case: a service token and the owner credential are configuration the
owner sets outside Registry, and no record, log line or answer holds one.

Concepts are kept apart by their change axis: a Customer changes for the
customer's reasons (contact, fiscal, relationship, rights), a Project for the
work's reasons, an artifact pointer for a producer's publication. The object
changes only with its project (R0-45) and is therefore not a model of its own
(M02). Answers a caller reads — the project card, `context`, `validate`, the
agent projection, the session's access, the billing read, the audit view — are
projections of these models, named under "Projections and answers", and are shaped in
States 5 and 6.

## Identity formats (R0-07, R0-16, R0-17, R0-34)

- Every identity Registry mints — `project_id`, `room_id`, artifact pointer id,
  `customer_ref` — is an opaque identifier with no meaning in its form. Its
  concrete format is a UUID, as the v1 ids the import keeps already are
  (R0-44, R0-50); the owner may choose otherwise, and the import then maps v1
  ids, which it today keeps verbatim.
- Pointer versions are small ordinal numbers per project and type, starting at
  1 (R0-17). The pointer's identity is its id, not the pair (type, version).
- A test instance's identity space is told apart from production's by the
  instance, not by the identifier: two instances share nothing (R0-05, R0-21),
  an id carries no instance mark, and the import's conflict check is the only
  guard where the spaces meet (R0-34, R0-44). Registry has no field that says
  "this id is production's".
- The agent session's identity is not minted by Registry: Cabinet Kernel names
  the session from its own run context (R0-53, R0-77); Registry records it as
  an opaque identifier it did not create.

## Revisions and times (R0-35, L16)

- A Project and a Customer carry a revision, an ordinal starting at 1 that
  every accepted change moves by one. A change names the revision it was made
  against; a stale one is refused and nothing changes. The object has no
  revision of its own (R0-45).
- Every time Registry records is an instant in UTC with time zone (L16). A
  record carries the instant it was created and the instant it was last
  changed; `registry_updated_at` in `context` is the project's last-changed
  instant (R0-04, L16).
- A project's last-changed instant moves by: a correction of its name, alias,
  customer link or object (R0-45). It does not move by: adding a room, publishing
  or withdrawing a pointer, a session grant, archiving an archived project
  (R0-12) or anonymising an anonymised one (R0-71). Archiving moves it once and
  records the archived date. A room and a pointer have no last-changed instant:
  they are written once (a pointer's status change records its own instant).
- A Customer's last-changed instant moves by: a correction of its contact,
  kind or fiscal data; restricting and lifting; ending and resuming the
  relationship; erasure.

## Disclosure classes by field (R0-26)

| class | fields |
|---|---|
| `personal_data` | Project display name (R0-82); Object address, kind and characteristics (R0-38); Customer name, phone, e-mail, language, tax id, legal name (R0-80); the end-of-relationship date and the restriction mark where they are read together with a customer's name |
| `business_confidential` | `project_id`, project alias, status, revision, created and last-changed instants, archived date, erased mark; `customer_ref` and the Customer's kind, erased, restricted and ended marks without its values; `room_id` and room name; every artifact pointer field; every agent session fact; every audit entry |
| `open` | nothing: a project's id is not anonymous by itself (R0-26) |

Room names, the alias, `uri`, `payload_ref` and the digest are
`business_confidential` by a rule on their writers (R0-68, R0-82): Registry
does not inspect them.

## Model M01 — Project

### Meaning

The one record of a renovation project's identity (R0-01): what Registry says
exists, for which customer and on which object. Everything else on the
platform names a project by this record's id.

Facts a Project carries, in domain words:

- its identity `project_id`, minted by production Registry at creation or kept
  by the import (R0-44);
- its display name, given by the owner, naming the object and the work and
  never a person (R0-82), held as `personal_data`;
- its alias, a short neutral label the owner may give, the name the agent sees
  (R0-82; format and uniqueness under Open questions);
- its object, embedded, exactly one (R0-38, M02);
- its customer link, optional: the `customer_ref` of a Customer (R0-16); kept
  even after that Customer's contact data is erased (R0-06, R0-67);
- its rooms (M03), owned by the project (R0-10);
- its status: `active` or `archived` (R0-12);
- its revision (R0-35);
- written once: the instant it was created; the instant it was archived
  (R0-60); the instant it was anonymised and the fact that it was (R0-62).

Written once, derived and not a fact of its own: the last-changed instant
("Revisions and times").

The acting principal of a creation or a correction is the owner, always
(Primary actions): the project keeps no "created by".

### Identity

entity

### Identity evidence

Substitution: two projects with equal name, object and customer are two
projects; Registry never merges records that look alike (R0-34), and one
physical object held in two instances under one id is two records of a link,
not one record (R0-21). Continuity: the same project keeps its id while its
name, alias, object, customer link, rooms, pointers, status and revision
change, and after anonymisation its id, status and pointers still answer
(R0-62).

### Source of truth

Production Registry's own record (R0-01, R0-34). A consumer's snapshot holds
identity only and is never written back (V1-2, R0-80).

### Lifecycle candidate

```text
active -> archived            (owner, confirming; final, R0-12)
archived -> anonymised        (owner, confirming; final, R0-60, R0-71)
archived -> deleted whole     (owner, confirming; the record is gone, R0-60)
```

An anonymised project is a Project with status `archived` and the anonymised
mark: it keeps its `project_id`, its status, its archived instant and its
artifact pointers (M05) and nothing else — name, alias, object, customer link,
rooms and revision are gone (R0-62; see Open questions). Deleting it whole is
refused (R0-71). `active` is never returned to.

### Persistence candidate

Durable, one record per project in the instance's own store (R0-05).

### Open questions

None. Settled by the owner on 2026-10-31:

- Alias (R0-82, carried): a short label, no format rule beyond a length State 6
  sets, and no uniqueness — two projects may share an alias, Registry refuses
  no duplicate, and a project without one is shown to the agent by its id.
- What an anonymised project keeps (R0-60, R0-62, carried): exactly its id, its
  status, the archived instant, the anonymised instant and its pointers; the
  revision goes with the card, since nothing of it can be corrected again.

## Model M02 — Object

### Meaning

The physical thing a project renovates: its address, its kind and the
technical characteristics the specification declares (R0-38). Exactly one per
project, given at creation with a required address (R0-45), corrected only
through the project card, moving the project's revision (R0-45). Every value
of it is `personal_data` (R0-26, R0-80).

Facts: address (required); kind; the declared characteristics (their list is
the specification's and belongs to State 6).

### Identity

value

### Identity evidence

Substitution: an object is reached only through its project; two projects with
an equal address hold two objects and Registry does not relate them (R0-34).
Continuity: the object has no revision and no life of its own (R0-45); a
correction replaces its values under the project's next revision, and nothing
on the platform names an object apart from its project.

Owner's evidence (2026-10-31): a roof-drainage repair on a building is a
closed project, and further works on the same building for the same customer
are planned. They are a new project with its own `project_id`, its own
object holding the same address, and its own money; the two are related only
through the Customer they name (M04, `customer_ref`). Registry keeps no "same
building" link and no history of works per building: that would be the object
carrying several projects, declined in R0-38, and a new responsibility
(R0-24, R0-59). Adding an object identity later, should such a history be
wanted, is a State 0 reopening and does not break existing projects.

### Source of truth

The owner, recorded in the project card (R0-45).

### Lifecycle candidate

None of its own; it goes with the project's anonymisation or deletion (R0-62).

### Persistence candidate

Embedded in the Project record.

### Open questions

None. R0-50 and R0-80 say the import keeps "project, object, room and pointer
ids"; the v1 Registry has no object (R0-38 moved the address from the project
to it), so no v1 object id exists to keep. The owner confirmed on 2026-10-31
that "object ids" is a slip: the object has no identity of its own and the
import carries it inside its project. The wording is to be corrected in
`00_product.md` by a new owner decision there (R0-75).

## Model M03 — Room

### Meaning

A named part of a project the planner and the agent work in (V1-3, R0-10):
the launch context of a downstream service is `project_id` and a `room_id`
(R0-18).

Facts: `room_id`, minted by Registry or kept by the import; its name, as its
writer wrote it (R0-68); its project; written once: the instant it was added
and by which principal (M07) — the owner or the agent through Kernel naming
its session (Primary actions, "add a room").

### Identity

entity

### Identity evidence

Substitution: a second room with the same name in the same project is a second
room (R0-10), so equal facts do not make one room. Continuity: a room is
never renamed or removed (R0-10); its id is the only thing a downstream service
can name a room by, across the room's whole life and the project's archiving.

### Source of truth

Registry's own record, written by the owner or by Kernel for the agent.

### Lifecycle candidate

None: created, never changed, never removed (R0-10). It goes with the
project's anonymisation or deletion (R0-62).

### Persistence candidate

Durable, owned by its Project record.

### Open questions

None.

## Model M04 — Customer

### Meaning

The person or company a project is for, and Registry's one home of that
customer's personal data on the platform (R0-06, R0-80). The owner records,
reads, corrects, restricts, ends, resumes and erases it; a service cleared
for it reads the billing data; the agent never sees it (R0-25).

Facts a Customer carries:

- its identity `customer_ref`, minted by Registry (R0-16) or kept by the import
  when it is a Registry-minted one (R0-80); the Customer a project names;
- its kind: `person` or `company` (R0-37);
- its contact data: name, phone, e-mail, language (R0-06) — `personal_data`,
  owner only, erasable as a whole;
- its fiscal data, each value recorded or absent (R0-80, R0-83): tax id
  (NIF/NIE/CIF), legal name — for a person the full name as on the identity
  document; `personal_data`, read by the owner and by a service whose token
  allows the billing read;
- its revision (R0-35);
- its marks, each with the instant the owner set it:
  - restricted (R0-51), lifted by the owner;
  - relationship ended, with the date the owner gives, today by default, never
    later than today (R0-49, R0-84), cleared by resuming (R0-57);
  - erased (R0-06): written once and final (R0-67) — the Customer keeps its
    `customer_ref`, its kind and this mark; name, phone, e-mail, language, tax
    id and legal name are gone;
- written once: the instant it was recorded.

A Customer is never deleted (R0-67). Recording the same person twice makes two
Customers (R0-16): Registry has no notion of "the same person".

### Identity

entity

### Identity evidence

Substitution: two Customers with equal name and contact data are two records
(R0-16); projects name one of them, and erasing one does not touch the other.
Continuity: the same `customer_ref` names the customer while its contact,
fiscal and relationship facts change, and after erasure projects still name it
(R0-06, R0-67).

### Source of truth

The owner's record in Registry (R0-80); PresuPro and the other services keep
no customer record.

### Lifecycle candidate

```text
recorded -> (restricted <-> unrestricted)     orthogonal, owner (R0-51, R0-65)
recorded -> (ended <-> resumed)               orthogonal, owner (R0-49, R0-57)
recorded -> erased                            final, owner (R0-06, R0-67)
```

The three marks are independent facts, not one status: a Customer may be
restricted and ended at once; erasure does not clear the other marks (what it
does to them is settled in State 2 if anything). While restricted or ended no
project may newly name it (R0-51, R0-57); an erased Customer cannot be
corrected (Primary actions).

### Persistence candidate

Durable, one record per customer, forever (R0-67).

### Open questions

None. Settled by the owner on 2026-10-31:

- An erased Customer is read as its `customer_ref`, its kind, the erased mark
  and its instant, and no other value; the list shows it the same way; the
  billing read refuses it (R0-65).
- A restricted Customer is read and listed by the owner unchanged, with the
  restricted mark and its instant; to any service the billing read refuses it
  (R0-65) and `context` still names its `customer_ref` (R0-55).
- The Customer the import makes from a v1 `customer_ref` (R0-80) gets its tax
  id from the v1 value when it is one and an absent name; the owner gives the
  name after the import, as the import gives display names (R0-85). The three
  marks stay independent facts; erasure clears none of them.

## Model M05 — ArtifactPointer

### Meaning

Catalogue metadata and a service-owned reference to a document another service
published about a project (V1-4, R0-02). Registry holds the pointer, never the
payload, and never reads or checks the digest (R0-33).

Facts a pointer carries:

- its identity, minted by Registry or kept by the import (R0-17, R0-50);
- its project (M01);
- its type, one of the vocabulary the specification declares, and so its owner
  service, which the vocabulary fixes (R0-33; "Declared vocabularies");
- its version within the project and type, minted by Registry: 1, then one
  more than the type's last (R0-17);
- its reference: `uri`, `payload_ref`, at least one (R0-17); its content
  digest when the producer gave one (R0-33); all as their writer wrote them
  (R0-68);
- its status: `published`, `superseded` or `withdrawn` (R0-02, R0-14);
- written once: the instant it was published and by which principal (M07) —
  a producer service as its token names it, Kernel for the agent naming its
  session, or the owner for any owner service; the instant it was superseded;
  the instant it was withdrawn and by which principal (R0-14).

### Identity

entity

### Identity evidence

Substitution: a repeated publish with equal content is a new pointer with a
new version, and the previous one is superseded, nothing merged (R0-17), so
equal content does not make one pointer. Continuity: the pointer keeps its id
and version while its status moves from `published` to `superseded` or
`withdrawn`, stays in the history (R0-14), survives the project's archiving
(frozen, R0-17) and its anonymisation (R0-62).

### Source of truth

Registry for the pointer; the owner service named by its type for the artifact
itself (V1-4). The digest is the producer's claim, stored as given (R0-33).

### Lifecycle candidate

```text
published -> superseded   (by the next publish of the same type on the project, R0-17)
published -> withdrawn    (by its owner service, Kernel for the agent, or the owner; R0-14)
```

Both are final. A `superseded` or `withdrawn` pointer cannot be withdrawn
again; on an archived project nothing moves (R0-17). "Latest of a type" is the
one `published` pointer of that type, or none (R0-14).

### Persistence candidate

Durable, owned by its Project record; kept after anonymisation (R0-62).

### Open questions

None.

## Model M06 — AgentSession

### Meaning

Registry's record of one agent session Cabinet Kernel registered (R0-47), with
the access the owner granted it: the set of projects the agent may work on,
at most one of them active, its pending access request, and the access version
Kernel reads (R0-46, R0-64). It is how Registry confines agent authority to the
owner's choice (R0-32) and checks it on every call, independently of Kernel
(R0-53).

Facts a session carries:

- its identity, named by Kernel from its run context (R0-53, R0-77), opaque to
  Registry; registering it again returns it unchanged (R0-53);
- its granted set of `project_id`s (R0-46), each added by the owner by a grant
  or an accepted request and removed by a revocation or by the project's
  erasure (R0-61);
- its active project, optional, one of the set; cleared by the owner, by a
  revocation of it or by the project's erasure (R0-70, R0-61); never an
  archived project (R0-70) — a project archived while active stays active;
- its pending access request, optional, at most one (M08);
- its access version, an ordinal that every change of the granted set, the
  active project or the pending request moves (R0-64; round 28 P4 — the
  precise semantics are State 2's);
- written once: the instant it was registered.

### Identity

entity

### Identity evidence

Substitution: two sessions with equal granted sets are two sessions; a call
naming one session never reaches another's projects (R0-77). Continuity: the
same session keeps its identity while its set, active project, request and
version change, and a running flow is checked against the same session at each
step (R0-46).

### Source of truth

The identity is Kernel's (R0-53, R0-77); the access is Registry's own record,
set by the owner alone (R0-46).

### Lifecycle candidate

```text
registered -> (access changes, owner) -> ended
```

What ends a session, and whether its record is kept after, is State 2's
(R0-47). A session with no granted project is a session (R0-47).

### Persistence candidate

Durable while the session lives; whether it is kept after is State 2's.

### Open questions

None for identity. The access version's start and what moves it are State 2's
(round 28 judgement P4).

## Model M07 — ActingPrincipal

### Meaning

Who did something, as Registry records it in an audit entry (R0-37), on a room
and on a pointer (M03, M05): the owner, signed in with the owner credential
(R0-30); a service, named by its service token (R0-27); or the agent through
Cabinet Kernel, naming the session Kernel named (R0-53). It carries no secret
(R0-23) and no `personal_data` value.

Facts: the principal kind — `owner`, `service`, `agent_via_kernel`; the
service name when a service; the session identity (M06) when the agent.

### Identity

value

### Identity evidence

Substitution: two records of "the owner did it" or "Kernel for session S did
it" mean the same thing wherever they appear; nothing distinguishes two
instances. Continuity: a principal reference does not change; a later action
writes another one.

### Source of truth

Registry's authentication of the request (R0-27, R0-30, R0-53).

### Lifecycle candidate

None; issued once per action.

### Persistence candidate

Embedded in audit entries, rooms and pointers.

### Open questions

None.

## Model M08 — AccessRequest

### Meaning

An agent session's ask, in free text, for a further project (R0-47). The owner
sees it in the owner interface and answers it from the catalogue; either
answer clears it (R0-64). A session holds at most one; a newer one replaces it
(R0-46). Registry keeps no reason for a decline and no history of requests
(R0-64).

Facts: the text, as the agent wrote it (R0-68: a value that names a person is
not refused); written once: the instant it was made.

### Identity

value

### Identity evidence

Substitution: a request is reached only through its session, and a session's
pending request is whichever was made last; two equal texts in one session are
the same pending request. Continuity: none — it is replaced whole or cleared,
never corrected, and leaves no trace of its own (R0-64).

### Source of truth

Kernel's call for the agent (R0-47).

### Lifecycle candidate

None of its own: made, replaced or cleared by an answer (R0-64).

### Persistence candidate

Embedded in the AgentSession record while pending.

### Open questions

None.

## Model M09 — AuditEntry

### Meaning

One significant change of state as Registry recorded it (R0-37, R0-58): a
change to a project or a customer record, a grant or revocation of a session's
projects, a restriction and its lifting, an erasure or anonymisation, and the
erasure of old entries itself (R0-66). Only the owner reads it; only the owner
erases it, by date (R0-66). It holds no personal value, no whole request and no
secret (R0-37).

Facts, all written once:

- the instant of the change;
- the acting principal (M07);
- the change: which action, in a closed vocabulary State 6 declares;
- the subject: the project (`project_id`) or the customer (`customer_ref`)
  changed, by identity only (R0-37) — for a session grant, the session and the
  project;
- the outcome (accepted; whether refused attempts are recorded is settled in
  State 2, round 28 P1);
- the contract version and the release version under which it happened
  (R0-37);
- the confirmation id where the owner confirmed (R0-37);
- for an erasure of old entries: the date the owner gave (R0-66).

### Identity

entity

### Identity evidence

Substitution: two entries with equal facts are two events — two archivings of
two projects at the same instant, or an erasure and its re-run — and the log
is read in time order as distinct entries (R0-58). Continuity: an entry never
changes; it is read until the owner erases it with every entry older than a
date (R0-66).

### Source of truth

Registry's own record of its accepted changes.

### Lifecycle candidate

```text
written -> erased by the owner's dated erasure   (R0-66)
```

Immutable in between.

### Persistence candidate

Durable, append-only, for the period the governance documents (R0-60).

### Open questions

None for identity. Whether refused attempts and agent-authority reads leave an
entry is State 2's (round 28 P1; R0-58 says ordinary reads do not).

## Model M10 — MigrationClosure

### Meaning

The fact that the one import from the VPS has succeeded (R0-79), after which
the import operation is closed and refused. Registry must remember it to
refuse a second import; nothing else of the migration is a Registry record —
the export file's format is States 5 and 6 (R0-72), and the import's results
are Projects, Customers, Rooms and ArtifactPointers like any other.

Facts, written once: the instant the import succeeded; the acting principal
(the owner, M07); the confirmation id; the identity of the file accepted, as a
digest, so the audit can name what was imported without its values.

### Identity

value

### Identity evidence

Substitution: there is at most one, and two records of "the migration
succeeded at instant T" would mean the same thing. Continuity: it is written
once and never changes; it is a fact about the instance, not a thing with a
life.

### Source of truth

Registry's own record of the accepted import (R0-79).

### Lifecycle candidate

None; absent, then present forever.

### Persistence candidate

Durable, at most one per instance.

### Open questions

None. Settled by the owner on 2026-10-31: the closure is a record of its own,
not only the audit entry of the import (M09), so that refusing a second import
does not depend on the audit log, which the owner may erase by date (R0-66).

## Model M11 — OwnerSession

### Meaning

The protected session the owner gets by signing in to the owner interface with
the owner credential (R0-30). Every owner action is made in one. Its lifetime,
expiry and sign-in throttling are State 2's (R0-30, carried).

Facts: its identity, minted by Registry at sign-in; written once: the instant
it began; its expiry.

### Identity

entity

### Identity evidence

Substitution: two sign-ins are two sessions, each ending on its own; a CSRF
protection is bound to one (R0-29). Continuity: the same session carries the
owner's actions from sign-in until it ends.

### Source of truth

Registry's sign-in with the owner credential (R0-30).

### Lifecycle candidate

```text
signed in -> ended (expiry or sign-out; State 2)
```

### Persistence candidate

Temporary runtime state; never a durable record beyond its life.

### Open questions

None for identity.

## Declared vocabularies

These are closed sets the specification declares; in State 6 they become
`kind: enum` or `kind: vocabulary` models without identity (SPEC_STANDARD §5).

- Project status: `active`, `archived` (R0-12). The anonymised mark is a
  separate fact (M01), not a third status: `validate` answers `archived` for
  an anonymised project (R0-62).
- Customer kind: `person`, `company` (R0-37).
- Artifact pointer status: `published`, `superseded`, `withdrawn` (R0-14).
- Principal kind: `owner`, `service`, `agent_via_kernel` (M07).
- Artifact type vocabulary: each type with its one owner service (R0-33). The
  entries are the specification's; the v1 sets (`domain/registry/rules.py`,
  L08) are evidence of the types in use today — `estimate` by PresuPro and
  Kernel's types — not the vocabulary. Which types are declared is the owner's
  State 2 decision (carried: "the declared artifact vocabulary and what a
  change of it does to existing pointers").
- Audit change vocabulary: one entry per significant change R0-58 names,
  declared in State 6.
- Disclosure classes: `open`, `business_confidential`, `personal_data`
  (R0-26), Cabinet Kernel's.

## Projections and answers

Answers a caller reads; each is a projection of the models above, shaped in
States 5 and 6, with the disclosure class of each output declared (R0-26).
None is a model: none has facts of its own.

- The project card ('read a project'): M01 with its object, rooms and revision;
  the archived date for an archived project (R0-60); the id at the top (R0-13).
- `context`: `project_id`, display name, status, address (from the object),
  `customer_ref`, created and `registry_updated_at` — field for field as v1
  (R0-04).
- `validate`: exists, active, `not_found` or `archived` (R0-04, R0-62).
- The agent projection: `project_id`, alias, status, rooms, pointers — nothing
  held as `personal_data` (R0-43, R0-68, R0-82).
- The session's access: granted ids, active project, whether a request is
  pending, the access version (R0-46, R0-64).
- The billing read: kind, tax id, legal name, each recorded or absent (R0-83).
- The customer read and list, the erased and restricted forms under M04.
- The audit view: entries in time order (R0-58).

## State 1 readiness

- `tools/design_lint.py examples/registry --state 1` answers no error
  (2026-10-31, after the owner's answers).
- `00_product.md` owes one correction: "object ids" in R0-50 and R0-80 (M02).
- Every carried State 1 question of `00_product.md` is answered above or
  placed under a model's Open questions: fields and create requests (each
  model's facts; the create request is the facts the owner gives, State 6),
  identity formats and the test/production separation ("Identity formats"),
  what an anonymised project keeps (M01), revisions and times ("Revisions and
  times"), the erased and restricted Customer (M04), the alias (M01), the
  absent fiscal value (M04, "Projections and answers"), disclosure classes ("Disclosure
  classes by field").
- Question rounds: emulated rounds first (`experiments/registry-pochemuchka/
  state1/`), then `tools/design_questions.py ask examples/registry --state 1`
  until two clear rounds close every unit.
