# State 1 — Registry domain models

## Status

Draft of 2026-10-31, derived from the accepted State 0 (`00_product.md`, R0-75)
and the questions it carried to State 1 ("Carried to later states"). The v1
code (`SOURCE.md`) is evidence of what runs, never a source of norm.

On 2026-10-31 the owner answered the draft's questions: the object has no
identity of its own (M02; "object ids" in R0-50 and R0-80 is a slip, to be
corrected there by R0-86), and the
proposals under M01, M04 and M10 are accepted as written. What remains open
is marked so under a model's `Open questions`; nothing blocks State 2. The
state is not yet closed by question rounds ("State 1 readiness"). The
emulated round 1 (`experiments/registry-pochemuchka/state1/round-1/`,
2026-10-31) found fourteen blocking topics, closed in this text; two of its
closures (T05, T09) follow State 0's text over the owner's answers of the same
day and are marked so under M04 and M01.

This state names the concepts Registry needs, the facts each carries in domain
words, its identity (`value` or `entity`, `MODEL_IDENTITY_EVIDENCE.md`), who
creates, reads and changes it, its status vocabulary and what is written once.
The facts listed under a model are all its facts, and the facts a create
request supplies are named with it (State 0, "Carried to later states"); a fact
that may be absent says so in domain words ("when given"). Field names, types,
formal optionality and every answer shape belong to State 6; orders, replay
mechanisms, correction semantics and token scopes belong to State 2 (State 0,
"Carried to later states"; codex round-01 T5).

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
work's reasons, an artifact pointer for a link the agent or the owner makes
(R0-88) or the import brings in as v1 made it (M05, M10). The object
changes only with its project (R0-45) and is therefore not a model of its own
(M02). Answers a caller reads — the project card, `context`, `validate`, the
agent projection, the session's access, the billing read, the audit view — are
projections of these models, named under "Projections and answers", and are shaped in
States 5 and 6.

## Identity formats (R0-07, R0-16, R0-17, R0-34)

- Every identity Registry mints — `project_id`, `room_id`, artifact pointer id,
  `customer_ref` — is an opaque identifier with no meaning in its form. Its
  concrete format is a UUID, as the v1 ids are; the import keeps every v1
  project, room and pointer id verbatim (R0-44, R0-50, R0-79).
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
- Two further identifiers Registry mints follow the same rule (opaque, UUID):
  the owner session's (M11) and the confirmation id. Registry mints a
  confirmation id when the owner confirms an action that asks for confirmation
  — archiving a project, erasing an archived project, the import, erasing old
  audit entries (Primary actions) — and writes it once into the audit entry of
  that action (M09) and, for the import, into the migration closure (M10). It
  keeps no Confirmation record; how the owner interface carries the
  confirmation step belongs to States 2 and 5. Neither identifier appears in a
  URL (R0-29).

## Revisions and times (R0-35, L16)

- A Project and a Customer carry a revision, an ordinal starting at 1 that
  accepted change of its own facts moves by one. A change names the revision it was made
  against; a stale one is refused and nothing changes. The object has no
  revision of its own (R0-45). The revision and the last-changed instant are
  one pair: the revision moves exactly when the last-changed instant moves,
  by the actions listed below, and by nothing else. Which actions must state
  the revision they were made against is State 2's (carried, R0-35).
- Every time Registry records is an instant in UTC with time zone (L16). A
  Project and a Customer — the records that carry a revision — carry the
  instant they were created and the instant they were last changed;
  `registry_updated_at` in `context` is the project's last-changed instant
  (R0-04, L16). Every other model carries only the written-once instants its
  own facts name (codex round-01 T5).
- A project's last-changed instant moves by: a correction of its name, alias,
  customer link or object (R0-45). It does not move by: adding a room, publishing
  or withdrawing a pointer, a session grant, archiving an archived project
  (R0-12) or anonymising an anonymised one (R0-71). Archiving moves it once and
  records the archived date. A room and a pointer are records of their own
  that name their project, not facts of it (M01), so adding one changes no
  Project fact; they have no last-changed instant: they are written once (a
  pointer's status change records its own instant) (codex round-04 T2, T3).
- A Customer's last-changed instant moves by: a correction of its contact,
  kind or fiscal data; restricting and lifting; ending and resuming the
  relationship; erasure.
- A record the import brings in keeps the instants its source holds: a
  project's created, last-changed and archived instants, a room's added
  instant, a pointer's published and superseded instants. Its revision starts
  at 1, the v1 Registry having none (R0-35). A Customer the import makes is
  created at the import's instant with revision 1.

## Disclosure classes by field (R0-26)

| class | fields |
|---|---|
| `personal_data` | Project display name (R0-82); Object address, kind and characteristics (R0-38); Customer name, phone, e-mail, language, tax id, legal name (R0-80); the import file uploaded in an owner session (M11), which holds such values |
| `business_confidential` | every other fact of every model: `project_id`, alias, status, revision, instants, the archived and anonymised marks; `customer_ref`, the Customer's kind, revision, instants and its erased, restricted and ended marks with their dates; `room_id`, room name and added instant; every artifact pointer fact; every agent session fact and the access request's text; every audit entry; the migration closure; the owner session, but for its uploaded import file |
| `open` | nothing: a project's id is not anonymous by itself (R0-26) |

Each fact has one class. An answer's class is the highest class of the facts
it carries (R0-26): the customer read, which carries the name beside the
marks, is `personal_data`; the customer list to the owner is too; the session's
access is `business_confidential`.

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
- its status: `active` or `archived` (R0-12);
- its revision (R0-35);
- the instant it was last changed ("Revisions and times");
- written once: the instant it was created; the request id of its create,
  as the caller gave it (R0-36; owner, 2026-10-31, State 2 A01), absent for a
  project the import brought in; the instant it was archived (R0-60); the
  anonymised mark (R0-62, R0-87).

The acting principal of a creation or a correction is the owner, always
(Primary actions): the project keeps no "created by".

Its rooms (M03, R0-10) and its artifact pointers (M05) are not facts of the
Project: each is a record of its own that names the project. The project's
rooms are the rooms naming it; its pointers are the pointers naming it, and
they stay after its anonymisation (R0-62, R0-87). Adding a room or publishing
a pointer therefore changes no Project fact and moves neither its revision
nor its last-changed instant ("Revisions and times"; codex round-04 T2, T3).

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
mark: it keeps its `project_id`, its status, that mark and its artifact
pointers (M05) and nothing else (R0-62, R0-87) — name, alias, object, customer link,
rooms, revision, the request id of its create and every instant are gone;
when it was archived and when it
was anonymised, the audit log says (M09). Deleting it whole is refused
(R0-71). `active` is never returned to.

### Persistence candidate

Durable, one record per project in the instance's own store (R0-05).

### Open questions

None. Settled by the owner on 2026-10-31:

- Alias (R0-82, carried): a short label, no format rule beyond a length State 6
  sets, and no uniqueness — two projects may share an alias, Registry refuses
  no duplicate, and a project without one is shown to the agent by its id.
- What an anonymised project keeps (R0-60, R0-62, carried): exactly what R0-62
  says as R0-87 narrows it (owner, 2026-10-31, codex round-02 T5) — id,
  status, the anonymised mark and its pointers. The owner's answer
  of 2026-10-31 kept the archived and anonymised instants too; State 0's
  "nothing else" (R0-62) decides against it (round 1 T09), and the audit entry
  of each step holds the instant. Keeping an instant would be a new State 0
  decision.
- Display names are not unique: two projects may carry the same display name,
  and Registry refuses no duplicate (round 1 S3).

## Model M02 — Object

### Meaning

The physical thing a project renovates: its address, its kind and the
technical characteristics the specification declares (R0-38). Exactly one per
project, given at creation with a required address (R0-45), corrected only
through the project card, moving the project's revision (R0-45). Every value
of it is `personal_data` (R0-26, R0-80).

Facts: address (required at creation, R0-45); kind, one of a closed vocabulary
the specification declares ("Declared vocabularies"), optional at creation; the
declared characteristics (their list is the specification's and belongs to
State 6).

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
import carries it inside its project (R0-86).

## Model M03 — Room

### Meaning

A named part of a project the planner and the agent work in (V1-3, R0-10):
the launch context of a downstream service is `project_id` and a `room_id`
(R0-18).

Facts: `room_id`, minted by Registry or kept by the import; its name, as its
writer wrote it (R0-68); its project; written once: the instant it was added
and the request id of its create, as the caller gave it (R0-36; owner,
2026-10-31, State 2 A01), absent for a room the import brought in.
Who added it — the owner or the agent through Kernel — is not a fact of the
room: no stated requirement reads it, State 0's output of "add a room" names
id, name and project only, and a session identity would otherwise reach every
reader of the rooms (round 1 T11).

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

Durable, a record of its own naming its project (M01); it goes when the
project is anonymised or deleted.

### Open questions

- Merging and splitting rooms (owner, 2026-10-31): a real planner scenario
  that R0-10 does not allow — a room is never renamed or removed. Until a
  consumer needs it, the planner merges by adding a new room and moving its own
  documents; the old rooms and every reference to them stay. When the planner
  needs it, the candidate is a room status after M05's pattern — `merged` (or
  superseded) with a reference to the room that replaces it, lists showing
  current rooms — as a new decision on R0-10. Does not block State 2.

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
    `customer_ref`, this mark and its instant, and nothing else (R0-06):
    name, phone, e-mail, language, tax id and legal name are gone (the one
    erasure covers the fiscal values, R0-06 narrowed by R0-80), and so are its
    kind, its revision, its recorded instant, the request id of its create
    and its restricted and ended marks;
- written once: the instant it was recorded; the request id of its create, as
  the caller gave it (R0-36; owner, 2026-10-31, State 2 A01), absent for a
  Customer the import made.

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

The restricted and ended marks are independent facts, not one status: a
Customer may be restricted and ended at once. Erasure ends both: nothing but
the identity and the erased fact survives it (R0-06), and restricting,
lifting, ending and resuming an erased Customer are refused (Primary actions).
While restricted or ended no project may newly name it (R0-51, R0-57); an
erased Customer cannot be corrected (Primary actions).

### Persistence candidate

Durable, one record per customer, forever (R0-67).

### Open questions

None. Settled by the owner on 2026-10-31:

- An erased Customer is read as its `customer_ref`, the erased mark and its
  instant, and no other value; the list shows it the same way; the billing
  read refuses it (R0-65). The owner's answer of 2026-10-31 kept the kind too;
  State 0's "nothing else" (R0-06) decides against it (round 1 T05), and
  keeping the kind would be a new State 0 decision.
- A restricted Customer is read and listed by the owner unchanged, with the
  restricted mark and its instant; to any service the billing read refuses it
  (R0-65) and `context` still names its `customer_ref` (R0-55).
- The Customer the import makes from a v1 `customer_ref` (R0-80): no v1 value
  was minted by Registry — in v1 `customer_ref` is an opaque string the caller
  supplied (L03) — so the import makes one new Customer for each distinct v1
  value and links every imported project that named it to that Customer. The
  owner gives each such Customer its kind and its name in the import, as the
  import takes display names (R0-85): a Customer without a name or a kind is
  not a state the record may be in (Primary actions, "record a customer"). The
  owner also says whether the v1 value is the Customer's tax id; one that is
  not is shown in the import's mapping and kept nowhere. This replaces the
  owner's answer of 2026-10-31 (an absent name, given after the import), which
  round 1 T08 found to contradict "record a customer".

## Model M05 — ArtifactPointer

### Meaning

Catalogue metadata and a reference to a document a service holds about a
project (V1-4, R0-02): a link the agent makes through Kernel, or the owner
makes, between the project and that document (R0-88). Registry holds the
pointer, never the payload, and never reads or checks the digest (R0-33).

Facts a pointer carries:

- its identity, minted by Registry or kept by the import (R0-17, R0-50);
- its project (M01);
- its type, one of the vocabulary the specification declared when it was
  published — or, imported, when the import accepted it — and so its owner
  service, which the vocabulary fixed (R0-33; "Declared vocabularies"); a
  later release that removes the type leaves it as it is (State 2 A22);
- its version within the project and type, minted by Registry: 1, then one
  more than the type's last (R0-17);
- its reference: `uri`, `payload_ref`, at least one (R0-17); its content
  digest when its publisher gave one (R0-33); all as their writer wrote them
  (R0-68);
- its status: `published`, `superseded` or `withdrawn` (R0-02, R0-14);
- written once: the instant it was published and its publisher — the
  principal (M07) for a pointer published in Registry: Kernel for the agent
  naming its session, or the owner (R0-88); the import (M10) for a pointer the
  import brought in (below); the request id of its publish, as Kernel or the
  owner interface gave it (R0-88; State 2 A01), absent for an imported
  pointer; the instant it was superseded; the instant it was withdrawn and by
  which principal (R0-14).

A pointer the import brings in (R0-50) was published before Registry recorded
principals: the v1 Registry keeps no publisher (its `owner_service` is the
caller's own claim, checked by no token) and no withdrawal (L22). Its
publisher is therefore the import itself — the migration closure (M10), not a
principal — and its published and superseded instants are those the source
holds ("Revisions and times"). It is never imported `withdrawn`, so it carries
no withdrawal facts until it is withdrawn in Registry, which records them as
for any pointer (owner, 2026-10-31; codex round-02 T1).

### Identity

entity

### Identity evidence

Substitution: a new publish with equal content — another request id — is a
new pointer with a new version, and the previous one is superseded, nothing merged (R0-17), so
equal content does not make one pointer. Continuity: the pointer keeps its id
and version while its status moves from `published` to `superseded` or
`withdrawn`, stays in the history (R0-14), survives the project's archiving
(frozen, R0-17) and its anonymisation (R0-62).

### Source of truth

Registry for the pointer; the owner service named by its type for the artifact
itself (V1-4). The digest is its publisher's claim, stored as given (R0-33).

### Lifecycle candidate

```text
published -> superseded   (by the next publish of the same type on the project, R0-17)
published -> withdrawn    (by Kernel for the agent, or the owner; R0-14, R0-88)
```

Both are final. A `superseded` or `withdrawn` pointer cannot be withdrawn
again; on an archived project nothing moves (R0-17). "Latest of a type" is the
one `published` pointer of that type, or none (R0-14).

### Persistence candidate

Durable, a record of its own naming its project (M01); kept after
anonymisation (R0-62). When the owner deletes the project whole, its pointers
go with it: the project then answers `not_found` (R0-60), and so does 'list
artifacts' on it; only anonymisation keeps them, which is what tells the two
erasures apart (R0-52; codex round-05 T1).

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
  active project or the pending request moves — a new request included, equal
  text or not (R0-64; round 28 P4);
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

None for identity. What moves the access version is stated above; its start
value and how a stale version is checked are State 2's (round 28 judgement
P4).

## Model M07 — ActingPrincipal

### Meaning

Who did something, as Registry records it in an audit entry (R0-37) and on a
pointer (M05) — a room records none (M03; codex round-01 T3): the owner,
signed in with the owner credential (R0-30); a service, named by its service token (R0-27); or the agent through
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

Embedded in audit entries and pointers.

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
pending request is whichever was made last; a new request with the same text
replaces the pending one like any other and nothing distinguishes the two. Continuity: none — it is replaced whole or cleared,
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

- its sequence number, minted by Registry: greater than every number minted
  before it, starting at 1; never reused, also after old entries are erased
  (R0-66) or the store is restored (State 2 A15), so the log's order is the
  order of the numbers even where two entries share an instant (owner,
  2026-10-31; codex round-02 T2). A number minted for a change that did not
  commit is not used again, so the log may skip numbers;
- the instant of the change;
- the acting principal (M07);
- the change: which action, in a closed vocabulary State 6 declares. The
  actions that write an entry (R0-58): creating, correcting, archiving,
  anonymising and deleting a project; recording, correcting and erasing a
  customer; restricting and lifting; ending and resuming a relationship;
  granting a project to a session and revoking one; the import, as one entry
  naming the migration closure (M10) by its file digest; erasing old entries. An answer
  to an access request that grants a project writes the grant's entry; a
  decline changes no session's projects and only clears the request (R0-64),
  so it writes none (R0-58; codex round-01 T4). No entry is written for adding a
  room, publishing or withdrawing a pointer, registering a session, an access
  request or its decline, changing or clearing the active project, or any read
  (R0-58). Anonymising or deleting a project writes that one entry; the
  project leaving every session's granted set (R0-61) is its consequence and
  writes no revocation entry (owner, 2026-10-31; codex round-02 T6);
- the subject, by identity only (R0-37), one of a closed set fixed by the
  action (owner, 2026-10-31; codex round-02 T4): the project (`project_id`)
  for a project's actions; the customer (`customer_ref`) for a customer's
  actions, restricting and lifting, ending and resuming; the session and the
  project for a grant or a revocation; for the import, the digest of the file
  it accepted (M10) — the migration closure is unique in the instance and has
  no other identity (codex round-04 T1); none for an erasure of old entries,
  whose fact is the owner's date;
- the outcome (accepted; whether refused attempts are recorded is settled in
  State 2, round 28 P1);
- the contract version and the release version under which it happened
  (R0-37);
- the confirmation id where the owner confirmed (R0-37; "Identity formats");
- for an erasure of old entries: the date the owner gave (R0-66).

### Identity

entity

### Identity evidence

Substitution: two entries with equal facts are two events — two archivings of
two projects at the same instant, or an erasure and its re-run — and the log
is read in time order as distinct entries (R0-58); the sequence number is what
tells them apart. Continuity: an entry never changes; it is read until the owner erases it with every entry older than a
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
(the owner, M07); the confirmation id ("Identity formats"); the identity of
the file accepted, as a digest, so the audit can name what was imported
without its values.

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

None; absent, then present forever: once a backup holding it has passed its
check, no backup without it is kept (State 2 A16, A18).

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

Facts: its identity, minted by Registry at sign-in ("Identity formats");
written once: the instant it began, its expiry at the latest and its CSRF
value (R0-29); changed by the owner's requests (State 2 A13, A16; owner,
2026-10-31): the instant of its last request, which starts as the instant it
began; at most one pending confirmation — its one-time value, the action, its
target, the revision or access version and the inputs it is bound to, and
the instant it was shown — made when a confirmation step is shown, replaced
by the next one shown and cleared when used; and at most one uploaded import
file, replaced by the next upload and dropped when the import is accepted.
Everything in it ends with the session. The confirmation id of an action the owner confirms in it
is minted per confirmation, not per session ("Identity formats").

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
- Object kind: a closed set the specification declares (R0-38); its entries
  are the owner's, listed in State 6 (round 1 T10).
- Customer language: a closed set of the languages the owner writes to
  customers in; its entries are the owner's, listed in State 6 (round 1 T10).
- Artifact pointer status: `published`, `superseded`, `withdrawn` (R0-14).
- Principal kind: `owner`, `service`, `agent_via_kernel` (M07).
- Artifact type vocabulary: each type with its one owner service, where its
  documents live (R0-33). The first release declares one: `estimate` by
  PresuPro (R0-88); the v1 sets (`domain/registry/rules.py`, L08) are evidence,
  not the vocabulary. What a change of it does to existing pointers is State
  2's (A22).
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
- The agent projection: `project_id`, alias, status, rooms, and the project's
  current pointers — those `published`, without the superseded and withdrawn
  history, which the owner and the services read (R0-43's minimal projection;
  owner, 2026-10-31; codex round-02 T7) — nothing held as `personal_data`
  (R0-43, R0-68, R0-82).
- The session's access: granted ids, active project, whether a request is
  pending, the access version (R0-46, R0-64).
- The billing read: kind, tax id, legal name, each recorded or absent (R0-83).
- The customer read and list, the erased and restricted forms under M04.
- The audit view: entries in time order (R0-58).

## State 1 readiness

- `tools/design_lint.py examples/registry --state 1` answers no error
  (2026-10-31, after the owner's answers).
- Every carried State 1 question of `00_product.md` is answered above or
  placed under a model's Open questions: fields and create requests (each
  model's facts and the facts its create request supplies; their field names
  and types, State 6),
  identity formats and the test/production separation ("Identity formats"),
  what an anonymised project keeps (M01), revisions and times ("Revisions and
  times"), the erased and restricted Customer (M04), the alias (M01), the
  absent fiscal value (M04, "Projections and answers"), disclosure classes ("Disclosure
  classes by field").
- Question rounds: emulated rounds first (`experiments/registry-pochemuchka/
  state1/`), then `tools/design_questions.py ask examples/registry --state 1`
  until two clear rounds close every unit.
