# State 2 — Registry record rules: creates, corrections, revisions, lists

Draft of 2026-10-31. The owner accepted the proposals behind these decisions on
2026-10-31 (answers 1–5 of the State 2 plan). They make the State 0 and State 1
texts (`00_product.md`, `01_models.md`) exact where those carried the question
here; they add no responsibility. Field names, types and answer shapes are
States 5 and 6.

## Accepted decision A01 — a create carries a request id; its repeat changes nothing

R0-36 asks that a create repeated after a lost answer never makes a second
project, customer or room; R0-88 makes publishing a pointer a write of the
agent, which R0-78 asks to be replay-safe too. Equal content cannot tell a repeat from a second
create: a second room of the same name is a second room (R0-10), and recording
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
3. A create whose request id an existing record of the same model already
   carries, with the same supplied facts, is a repeat: Registry answers that
   record as it stands now — archived included — and changes nothing.
4. A create whose request id an existing record carries, with different
   supplied facts, is refused, and nothing changes.
5. The supplied facts are compared as the caller gave them, value for value;
   Registry does not normalise them for the comparison. For 'add a room' the
   project is one of them.
6. A create without a request id is refused.
7. A request id leaves its record with the values anonymisation or erasure
   removes (M01, M04); a create arriving after that with the same request id
   is a new create.
8. A publish's repeat answers the pointer it made, whatever its status now;
   it neither supersedes nor makes a version (R0-17, R0-88).
9. A request id is never an identity: it is not answered as one, and no read
   looks a record up by it.

### Formal invariants

```text
for each model m in {Project, Customer, Room, ArtifactPointer}:
  for records r1 != r2 of m with r1.request_id and r2.request_id present:
    r1.request_id != r2.request_id
create(m, request_id = k, facts = f) where existing r of m has r.request_id = k:
  f = supplied_facts(r)  => answer r, store unchanged
  f != supplied_facts(r) => refused, store unchanged
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

### Consequence

Kernel's retried 'add a room' or publish and a resubmitted owner form are
safe. A request
id is not a deduplication of look-alike records: Registry still never merges
records because they look alike (R0-34).

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
   restricting and lifting, ending and resuming the relationship.
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

### Formal invariants

```text
for action a on record r in {Project, Customer} that may move r.revision:
  a.stated_revision != r.revision => refused, r unchanged
  accepted and changed(r) => r.revision' = r.revision + 1
                             and r.last_changed' = now
  accepted and not changed(r) => r.revision' = r.revision
```

### Required tests

1. Two owner tabs correct one project from revision 3; the first is accepted,
   the second is refused as stale.
2. Restricting a customer with an old revision is refused.
3. Archiving moves the revision once; archiving again with the new revision
   answers the project unchanged.

### Consequence

One rule for every record change; the owner interface always shows and sends
the revision of the card it rendered.

## Accepted decision A05 — a repeated transition returns the record unchanged

### Normative rules

1. A transition to the state a record is already in is accepted and changes
   nothing: archiving an archived project (R0-12), anonymising an anonymised
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
4. The refusals State 0 states stay refusals: withdrawing a withdrawn or
   superseded pointer (Primary actions), revoking a project not in the set
   (answered as not granted), deleting an anonymised project whole (R0-71).

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
7. Names compare by Unicode code point of the stored value; identities compare
   as their text.

### Formal invariants

```text
every list answer is totally ordered by its key; equal keys never occur
because each key ends in an identity or a sequence number
```

### Required tests

1. Two projects changed at the same instant list by id.
2. An erased Customer lists after every Customer that is not erased.
3. Artifacts of one type list version 3, 2, 1.

### Consequence

Answers are deterministic; no list pages (L09 is States 5 and 6).
