# State 2 — Registry record rules: creates, corrections, revisions, lists

Draft of 2026-10-31. The owner accepted the proposals behind these decisions on
2026-10-31 (answers 1–5 of the State 2 plan). They make the State 0 and State 1
texts (`00_product.md`, `01_models.md`) exact where those carried the question
here; they add no responsibility. Field names, types and answer shapes are
States 5 and 6. Every "today" in Registry is the current date in UTC, as every
instant is (L16).

## Accepted decision A01 — a create carries a request id; its repeat changes nothing

R0-36 asks that a create repeated after a lost answer never makes a second
project, customer or room; R0-88 makes publishing a pointer a write of the
agent, which R0-78 asks to be replay-safe too. Equal content cannot tell a
repeat from a second create: a second room of the same name is a second room (R0-10), and recording
the same person twice makes two Customers (R0-16). The caller therefore names
each create once.

### Normative rules

1. 'Create a project', 'record a customer', 'add a room' and 'publish an
   artifact pointer' each carry a request id: an opaque value the caller
   makes, unique for every create it means as new. The owner interface makes
   one when it renders a create form; Cabinet Kernel gives one as an input
   field of 'add a room' and of 'publish an artifact pointer' (R0-78).
2. Registry keeps the request id with the record the create made, written once
   (M01, M03, M04, M05).
3. A repeat passes stages (1) to (4) of A04 rule 6 like any call — rights,
   the session's set, the existence of its project, its values, a publish's
   type among them (A22) — and, for 'add a room' and 'publish an artifact
   pointer', the check that its project is not archived (R0-17, R0-88). No
   other check of stage (6) is made again for a repeat: the customer a
   project named may since be restricted, and the repeat still answers the
   project.
4. A create whose request id an existing record of the same model carries is
   a repeat when the facts it supplies equal that record's current facts of
   the same kind: Registry answers the record as it stands now and changes
   nothing. A publish's repeat answers the pointer whatever its status now; it
   neither supersedes nor makes a version (R0-17, R0-88).
5. A create whose request id an existing record carries, with facts that
   differ from that record's current ones — a different value, or the record
   corrected since — is refused, and nothing changes; the caller reads the
   record.
6. Facts are compared as A02 reads them: a required value as written, an
   optional value given blank the same as one not given. For 'add a room' and
   'publish an artifact pointer' the project is one of the facts.
7. A create without a request id is refused. Creates of one model carrying
   one request id are applied one at a time: of two concurrent ones, the
   first makes the record and the second is a repeat or refused by rule 4
   or 5.
8. A request id leaves its record with the values anonymisation or erasure
   removes (M01, M04); a create arriving after that with the same request id
   is a new create.
9. A request id is never an identity: it is not answered as one, and no read
   looks a record up by it.

### Formal invariants

```text
for each model m in {Project, Customer, Room, ArtifactPointer}:
  for records r1 != r2 of m with r1.request_id and r2.request_id present:
    r1.request_id != r2.request_id
create(m, request_id = k, facts = f) where existing r of m has r.request_id = k:
  rights fail or project archived => refused, store unchanged
  f = current_facts(r)  => answer r, store unchanged
  f != current_facts(r) => refused, store unchanged
```

### Required tests

1. Two 'create a project' calls with the same request id and equal facts make
   one project; the second answers it.
2. The same request id with a different display name is refused and nothing
   changes.
3. Two 'add a room' calls with different request ids and the same name make
   two rooms (R0-10).
4. A repeat of a project's create after the project was archived answers the
   archived project and does not reactivate it.
5. A create without a request id is refused.
6. After anonymising a project, a create with that project's former request id
   makes a new project with a new id.
7. Kernel retrying a publish with the same request id gets the same pointer
   and version; the pointer it made is not superseded.
8. A repeat of a project's create after the project was corrected is refused.
9. A repeat of 'record a customer' giving an empty e-mail equals one that gave
   none.
10. Kernel repeating 'add a room' after the project left its session's set is
    answered as not found (A10).
11. Repeating a publish after its type was removed is refused as an unknown
    type (A22).

### Consequence

Kernel's retried 'add a room' or publish and a resubmitted owner form are
safe, and Registry keeps nothing but the request id to tell a repeat. A
request id is not a deduplication of look-alike records: Registry still never
merges records because they look alike (R0-34).

## Accepted decision A02 — a required value is present and not blank

### Normative rules

1. A required value given as an empty string or as white space only is missing,
   and the action is refused as for a missing value: a project's display name
   and its object's address (R0-45), a Customer's name and kind (Primary
   actions), a room's name (R0-10), a session's access request text.
2. A value that is present is kept exactly as written; Registry trims and
   rewrites nothing (R0-68).
3. An optional value given as an empty string or white space only is absent.

### Formal invariants

```text
missing(v) <=> v is absent or strip(v) = ""
for every stored required value v: not missing(v)
stored(v) = given(v) whenever not missing(v)
```

### Required tests

1. A project with a display name of three spaces is refused.
2. A room name `"  Cocina "` is stored with its spaces.
3. A Customer correction giving an e-mail of `""` clears the e-mail.

### Consequence

L17's empty strings are closed: a blank required value never reaches the
store.

## Accepted decision A03 — a correction replaces the editable facts as a whole

### Normative rules

1. 'Correct a project' gives every editable fact of the project: display name,
   alias, customer link and the object — address, kind, characteristics
   (R0-45). 'Correct a customer' gives every editable fact of the Customer:
   kind, contact data, fiscal data (R0-80).
2. An optional fact the correction does not give is cleared; there is no
   partial correction.
3. The facts a correction does not edit — identity, status, marks, instants,
   request id — are not part of it and do not change by it.
4. A correction that gives exactly the stored facts is accepted and changes
   nothing: revision and last-changed instant stay, and no audit entry is
   written (A05).
5. A correction newly naming a customer is checked as State 0 says: unknown,
   erased, restricted or ended refused (R0-16, R0-51, R0-57). Keeping the
   customer already named is not newly naming it.

### Formal invariants

```text
after correct(p, facts f) accepted:
  editable(p) = f
  non_editable(p) = non_editable(p before)
  f = editable(p before) => p = p before
```

### Required tests

1. A project correction without an alias clears the alias.
2. A correction equal to the stored card leaves the revision where it was.
3. A correction keeping a customer that has since been restricted is accepted;
   one newly naming a restricted customer is refused.

### Consequence

L04 is kept as the rule and made explicit: the owner interface sends the whole
card it showed, and what the owner emptied is cleared.

## Accepted decision A04 — every change that moves a revision states it

### Normative rules

1. Every action that moves a Project's or a Customer's revision ("Revisions and
   times") states the revision it was made against: correcting, archiving and
   erasing a project; correcting a customer, erasing its contact data,
   restricting and lifting, ending and resuming the relationship. Erasing a
   project or a Customer's contact data states the revision it was made
   against and leaves no revision behind (M01, M04): the record is anonymised,
   erased or deleted, not given a next revision.
2. A stated revision that is not the record's current one is refused as stale,
   and nothing changes (R0-35).
3. An action that would change nothing (A03 rule 4, A05) still states the
   revision and is refused when it is stale. An anonymised project and an
   erased Customer have no revision (M01, M04): an action on them states
   none.
4. Every action is atomic: it applies all its changes or none.
5. Actions on records without a revision — adding a room, publishing or
   withdrawing a pointer, session actions — state none; the session's owner
   actions state its access version instead (A12).
6. Every operation — read or change, of a service, Kernel or the owner —
   checks in one order, and the first failure is its answer; a stage that
   does not apply to it is skipped, and each check an operation states belongs
   to the stage of its kind: (1) the caller's authentication and its right to
   the operation (A09) — for the owner, a valid owner session, then its CSRF
   value, then a confirmation value where one is asked (A13);
   (2) for agent authority, the session and its set (A10), whose refusal
   hides every later failure; (3) that the record named exists; (4) the
   values given (A02, A08, A22); (5) the stated revision or access version
   (A12); (6) the record's lifecycle — archived, erased, anonymised, not in the
   set, a customer's eligibility, a conflict. Only an action that passes all
   six may be a repeat that changes nothing (A05); a create's repeat is
   recognised as A01 rule 3 says.

### Formal invariants

```text
answer(a) = first failing check of a in the order (1)..(6), else its effect
for action a on record r in {Project, Customer} that may move r.revision:
  a.stated_revision != r.revision => refused, r unchanged
  accepted and changed(r) and r keeps a revision
                          => r.revision' = r.revision + 1
                             and r.last_changed' = now
  accepted erasure, anonymisation or deletion => r has no revision after
  accepted and not changed(r) => r.revision' = r.revision
```

### Required tests

1. Two owner tabs correct one project from revision 3; the first is accepted,
   the second is refused as stale.
2. Restricting a customer with an old revision is refused.
3. Archiving moves the revision once; archiving again with the new revision
   answers the project unchanged.
4. Correcting an archived project with a stale revision is refused as stale,
   not as archived.
5. Kernel naming a project outside its set with a blank room name receives the
   not-found answer, not the missing-name refusal.

### Consequence

One rule for every record change; the owner interface always shows and sends
the revision of the card it rendered.

## Accepted decision A05 — a repeated transition returns the record unchanged

### Normative rules

1. A transition to the state a record is already in, that passes every check
   of A04 rule 6, is accepted and changes nothing: archiving an archived project (R0-12), anonymising an anonymised
   one (R0-71), erasing an erased Customer (Primary actions), restricting a
   restricted Customer, lifting an unrestricted one, ending an ended
   relationship, resuming one that is not ended (R0-84), granting a project
   already in a session's set, making the active project active again,
   clearing an active project that is already clear, registering a registered
   session (R0-53).
2. Such a transition answers the record as it stands; its revision, its
   last-changed instant and a session's access version stay; no audit entry
   is written and no confirmation id is minted.
3. Ending an ended relationship with another date does not move the date: the
   owner resumes and ends again to change it.
4. The refusals State 0 states stay refusals and come first: withdrawing a
   withdrawn or superseded pointer (Primary actions), revoking a project not
   in the set (answered as not granted), deleting an anonymised project whole
   (R0-71), granting or making active an archived project — already granted
   or active included (R0-70).

### Formal invariants

```text
transition t to state s on record r with state(r) = s:
  accepted, r unchanged, no AuditEntry, no confirmation id
```

### Required tests

1. Restricting a restricted Customer answers it, with the same revision and no
   new audit entry.
2. Ending an ended relationship with a new date keeps the old date.
3. Granting a project already granted leaves the access version.
4. Withdrawing a withdrawn pointer is refused.
5. Granting again a granted project that has since been archived is refused,
   and the project stays in the set (R0-46, R0-70).

### Consequence

The audit log holds changes only (R0-58), and a retried transition is safe.

## Accepted decision A06 — every list has one declared order

### Normative rules

1. 'List projects': by last-changed instant, latest first, then by
   `project_id` (L10).
2. 'List rooms': by name, then by `room_id` (L10).
3. 'List artifacts': by type, then by version, highest first, then by pointer
   id (L10).
4. 'List customers': Customers that are not erased by name, then by
   `customer_ref`; erased ones after them by `customer_ref`.
5. 'List agent sessions': by registration instant, earliest first, then by
   session identity.
6. 'Read the audit log': by sequence number, ascending (M09).
7. Every key is ascending unless named "latest first" or "highest first".
   Names, artifact types and identities compare by Unicode code point of the
   stored text; instants and numbers by value.
8. A collection inside an answer follows the order of the list that answers it
   alone: a project card's rooms as 'list rooms'; the agent projection's
   pointers as 'list artifacts'; a session's granted ids by `project_id`; the
   import mapping's projects by `project_id`, each one's rooms and pointers as
   their lists, and the Customers it makes by their v1 value.

### Formal invariants

```text
every list answer is totally ordered by its key; equal keys never occur
because each key ends in an identity or a sequence number
```

### Required tests

1. Two projects changed at the same instant list by id.
2. An erased Customer lists after every Customer that is not erased.
3. Artifacts of one type list version 3, 2, 1.
4. A project card lists its rooms in the order of 'list rooms'.

### Consequence

Answers are deterministic; no list pages (L09 is States 5 and 6).
