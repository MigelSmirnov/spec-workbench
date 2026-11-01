# State 5 — Registry public module operations: records

## Status

Draft of 2026-11-01. The operations of `customers`, `projects` and
`artifact_pointers`, which own the Customer, the Project with its Object and
Rooms, and the ArtifactPointer. Every one follows
`50_public_apis_0_conventions.md`.

## `public_op:customers.record_customer`

### Owner

`module:customers`. Record a Customer with a request id (A01, M04).

### Callers

`module:operations`.

### Inputs

The transaction; the request id; name, kind, contact data — phone, e-mail,
language — and fiscal data — tax id, legal name; the action's instant.

### Outputs

The Customer with its `customer_ref`, and `changed`.

### Observable effect

A new Customer: a minted `customer_ref`, revision 1, created and
last-changed at the instant, the request id kept. A repeat changes nothing.

### Enforces

Stage (4): the request id's form, the name and kind required, the rest
optional (A01 rule 1, A02); then the request id looked up among Customers —
equal current facts by `given_values.facts_equal_for_repeat` answer the
existing Customer (A01 rule 4), other facts are a conflict (A01 rule 5);
the same person recorded again is a second Customer (R0-16); a request id
an erasure removed makes a new create (A01 rule 8).

### Errors

`invalid_request` (`missing_value`, `malformed_request_id`,
`outside_closed_list` for a kind or language); `refused` (`conflict`).

### State impact

Writes one Customer.

## `public_op:customers.correct_customer`

### Owner

`module:customers`. Replace a Customer's editable facts as a whole (A03).

### Callers

`module:operations`.

### Inputs

The transaction; the `customer_ref`; the stated revision; kind, contact data
and fiscal data; the action's instant.

### Outputs

The Customer and `changed`.

### Observable effect

Every editable fact replaced, an optional one not given cleared; the
revision and last-changed instant move together. Equal facts change nothing
(A03 rule 4).

### Enforces

Stages: (3) the Customer exists; (4) the values; (5) the revision — none
stated, or one stated for an erased Customer, which has none, is stale (A04
rules 2, 3); (6) an erased Customer is not corrected.

### Errors

`not_found` (`unknown_customer`); `invalid_request` (`missing_value`,
`outside_closed_list`); `stale` (`stale_revision`); `refused`
(`customer_erased`).

### State impact

Writes one Customer.

## `public_op:customers.mark_customer`

### Owner

`module:customers`. Restrict or lift, end or resume a Customer's
relationship (R0-51, R0-57, R0-84).

### Callers

`module:operations`.

### Inputs

The transaction; the `customer_ref`; the stated revision; the transition —
restrict, lift, end with an optional date, resume; today's date; the
action's instant.

### Outputs

The Customer and `changed`.

### Observable effect

The mark set or cleared, an end dated as given or today; the revision and
last-changed instant move. A transition to the state it is in changes
nothing, and ending an ended relationship with another date does not move it
(A05 rules 1, 3).

### Enforces

Stages: (3) exists; (4) an end date later than today refused (R0-84); (5)
the revision; (6) an erased Customer refused. A restriction keeps the
contact and fiscal data, which reach no one but the owner (R0-65).

### Errors

`not_found` (`unknown_customer`); `invalid_request` (`date_after_today`);
`stale` (`stale_revision`); `refused` (`customer_erased`).

### State impact

Writes one Customer.

## `public_op:customers.erase_customer_contact`

### Owner

`module:customers`. Erase a Customer's contact data, finally (M04, R0-06).

### Callers

`module:operations`.

### Inputs

The transaction; the `customer_ref`; the stated revision, or none for an
erased Customer; the action's instant.

### Outputs

The erased Customer and `changed`.

### Observable effect

The Customer keeps its identity, the erased mark and its instant, and
nothing else: no name, contact or fiscal data, no revision, no request id;
projects still name it. An erased Customer with none stated is unchanged.

### Enforces

(5) a revision stated for an erased Customer is stale — the form that erased
it resubmitted included (A04 rule 3); a request id leaves with the values
(A01 rule 8).

### Errors

`not_found` (`unknown_customer`); `stale` (`stale_revision`).

### State impact

Writes one Customer.

## `public_op:customers.read_customer`

### Owner

`module:customers`. The customer read for the owner (M04).

### Callers

`module:operations`.

### Inputs

The transaction; the `customer_ref`.

### Outputs

`customer_ref`, name, kind, phone, e-mail, language, tax id, legal name,
revision, created and last-changed instants, the restricted mark with its
instant, the date the relationship was ended; for an erased Customer its
erased form (Conventions).

### Observable effect

None.

### Enforces

The erased form carries no contact data (Primary actions).

### Errors

`not_found` (`unknown_customer`).

### State impact

Reads one Customer.

## `public_op:customers.list_customers`

### Owner

`module:customers`. The Customers for the owner (A06 rule 4).

### Callers

`module:operations`.

### Inputs

The transaction.

### Outputs

The Customers that are not erased by name, then `customer_ref`, each with
its `customer_ref`, name, the restricted mark with its instant and the date
its relationship was ended; then the erased ones by `customer_ref`, each in
its erased form (Conventions).

### Observable effect

None.

### Enforces

A06 rule 4's order as `store` reads it.

### Errors

None.

### State impact

Reads Customers.

## `public_op:customers.read_billing_data`

### Owner

`module:customers`. A Customer's billing data for a service allowed it (R0-80,
R0-83).

### Callers

`module:operations`.

### Inputs

The transaction; the `customer_ref`.

### Outputs

Kind, tax id and legal name, each recorded or marked absent; never contact
data, the ordinary name included.

### Observable effect

None.

### Enforces

(3) an unknown Customer refused; (6) an erased or restricted one refused
(R0-65); a value never recorded is absent, not a refusal (R0-83).

### Errors

`not_found` (`unknown_customer`); `refused` (`customer_erased`,
`customer_restricted`).

### State impact

Reads one Customer.

## `public_op:customers.check_customer_eligible`

### Owner

`module:customers`. Whether a Customer may be newly named by a project (A03
rule 5).

### Callers

`module:projects`.

### Inputs

The transaction; the `customer_ref`.

### Outputs

One answer: eligible; unknown; or erased, restricted or ended.

### Observable effect

None.

### Enforces

The one rule of eligibility; `projects` places unknown at stage (3) and the
others at stage (6), which a create's repeat never reaches (A01 rule 3).

### Errors

None; the answer is the result.

### State impact

Reads one Customer.

## `public_op:customers.make_imported_customer`

### Owner

`module:customers`. Make a Customer the import brings in for a v1
`customer_ref` (A16 rule 1, R0-80).

### Callers

`module:migration_import`.

### Inputs

The transaction; the name and kind the owner gave; the v1 value and whether
it is the tax id; the action's instant.

### Outputs

The Customer with its minted `customer_ref`.

### Observable effect

A new Customer created at the action's instant, revision 1, the v1 value as
its tax id when the owner said so.

### Enforces

Revision 1 and the import's instant (State 1, "Revisions and times"); no
request id.

### Errors

None; `migration_import` checked the values before.

### State impact

Writes one Customer.

## `public_op:projects.create_project`

### Owner

`module:projects`. Create a project with a request id (A01, R0-44, R0-45).

### Callers

`module:operations`.

### Inputs

The transaction; the request id; display name, alias, customer reference,
object — address, kind, characteristics; the action's instant.

### Outputs

The project card and `changed`.

### Observable effect

A new Project, `active`, revision 1, a minted `project_id`, created and
last-changed at the instant, the request id kept. A repeat changes nothing.

### Enforces

`customers.check_customer_eligible` asked once: (3) a named customer
exists; (4) the request id's form, display name and address required, alias,
kind and characteristics optional; then the request id among projects — a
repeat with equal facts answers the project as it stands, archived included
(A01 rules 3, 4), other facts are a conflict; (6) an erased, restricted or
ended customer refused (A03 rule 5). A request id an erasure removed makes
a new create (A01 rule 8).

### Errors

`not_found` (`unknown_customer`); `invalid_request` (`missing_value`,
`malformed_request_id`, `outside_closed_list`); `refused` (`conflict`,
`customer_erased`, `customer_restricted`, `customer_ended`).

### State impact

Writes one Project.

## `public_op:projects.correct_project`

### Owner

`module:projects`. Replace a project's editable facts as a whole (A03).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`; the stated revision; display name, alias,
customer reference, object; the action's instant.

### Outputs

The project card and `changed`.

### Observable effect

Every editable fact replaced, an optional one not given cleared; the
revision and last-changed instant move. Equal facts change nothing.

### Enforces

(3) the project exists, a newly named customer exists; (4) the values; (5)
the revision — none, or one for an anonymised project, stale (A04 rules 2,
3); (6) an archived project, a newly named customer erased, restricted or
ended; keeping the named one is not newly naming it (A03 rule 5).

### Errors

`not_found` (`unknown_project`, `unknown_customer`); `invalid_request`
(`missing_value`, `outside_closed_list`); `stale` (`stale_revision`);
`refused` (`archived`, `customer_erased`, `customer_restricted`,
`customer_ended`).

### State impact

Writes one Project.

## `public_op:projects.archive_project`

### Owner

`module:projects`. Archive an active project, finally (R0-12).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`; the stated revision; the action's
instant.

### Outputs

The project card and `changed`.

### Observable effect

The project becomes `archived`, its archived instant the action's (M01);
its revision and last-changed instant move once. Archiving an archived project changes
nothing (A05).

### Enforces

(3) exists; (5) the revision; rooms, pointers and every session's set and
active project stay (R0-70).

### Errors

`not_found` (`unknown_project`); `stale` (`stale_revision`).

### State impact

Writes one Project.

## `public_op:projects.erase_project`

### Owner

`module:projects`. Erase an archived project: anonymise it or delete it
whole (R0-60, R0-62, R0-71).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`; the stated revision, or none for an
anonymised project; anonymise or delete whole.

### Outputs

The anonymised project's erased form, or that it was deleted; and `changed`.

### Observable effect

Anonymising keeps the id, the status `archived`, the anonymised mark and
nothing else of the record — display name, alias, object, customer link,
rooms, revision, request id and instants go (M01, R0-87); deleting whole
removes the record and its rooms. Anonymising an anonymised project changes
nothing.

### Enforces

(3) exists; (5) the revision (A04 rule 3); (6) an active project refused,
deleting an anonymised project whole refused (A05 rule 4). The sessions and
the pointers are their own modules', called by `operations` in the same
transaction.

### Errors

`not_found` (`unknown_project`); `stale` (`stale_revision`); `refused`
(`active`, `anonymised`).

### State impact

Writes or removes one Project and its Rooms.

## `public_op:projects.read_project_card`

### Owner

`module:projects`. The project card (R0-13, R0-60).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`.

### Outputs

The card, its id first (R0-13): `project_id`, display name, alias, status,
`customer_ref`, the object — address, kind, characteristics — revision,
created and last-changed instants and, when archived, the date it was
archived, the UTC date of its archived instant; and its rooms in 'list
rooms' order, each as 'list rooms' gives it. For an anonymised project its
erased form (R0-62).

### Observable effect

None.

### Enforces

A06 rule 8's order of rooms; the card is `personal_data`.

### Errors

`not_found` (`unknown_project`).

### State impact

Reads one Project and its Rooms.

## `public_op:projects.read_project_context`

### Owner

`module:projects`. `context`, field for field as v1 (R0-04).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`.

### Outputs

`project_id`, display name, status, address, `customer_ref`, created and
`registry_updated_at`; for an anonymised project its erased form (Conventions).

### Observable effect

None.

### Enforces

Never contact data (R0-04); `personal_data`.

### Errors

`not_found` (`unknown_project`).

### State impact

Reads one Project.

## `public_op:projects.validate_project_reference`

### Owner

`module:projects`. Whether a project id names a project, and whether it is
active (R0-04, R0-62).

### Callers

`module:operations`, `module:agent_sessions`.

### Inputs

The transaction; the `project_id`.

### Outputs

The `validate` answer as v1 gives it (R0-04): `exists`, `active`, and the
reason when not active — `not_found`, or `archived`, an anonymised project
included (R0-62).

### Observable effect

None.

### Enforces

It refuses nothing: the answer carries the failure (Primary actions).

### Errors

None.

### State impact

Reads one Project.

## `public_op:projects.read_agent_view`

### Owner

`module:projects`. The project's part of the agent projection (R0-43).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`.

### Outputs

`project_id`, alias, status and rooms; for an anonymised project its erased form
(R0-62).

### Observable effect

None.

### Enforces

No display name, object, customer or other `personal_data` value (R0-43,
R0-68): the part is `business_confidential`.

### Errors

`not_found` (`unknown_project`).

### State impact

Reads one Project and its Rooms.

## `public_op:projects.add_room`

### Owner

`module:projects`. Add a room to a project with a request id (A01, R0-10).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`; the room's name; the request id; the
action's instant.

### Outputs

The room and `changed`.

### Observable effect

A new Room with a minted `room_id`, its name and added instant; the
project's revision does not move. A repeat changes nothing.

### Enforces

(3) the project exists; (4) the name required, the request id's form; the
archive check, a repeat's too (A01 rule 3); the request id looked up among
this project's rooms only (A01 rule 4); (6) an archived project, a conflict.
A room of the same name is a second room.

### Errors

`not_found` (`unknown_project`); `invalid_request` (`missing_value`,
`malformed_request_id`); `refused` (`archived`, `conflict`).

### State impact

Writes one Room.

## `public_op:projects.list_rooms`

### Owner

`module:projects`. A project's rooms (A06 rule 2).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`.

### Outputs

The rooms by name, then `room_id`, each with its `room_id`, name and added
instant — the room projection every answer that carries rooms uses; for an
anonymised project, which has none left, its erased form (R0-62).

### Observable effect

None.

### Enforces

A06 rule 2's order.

### Errors

`not_found` (`unknown_project`).

### State impact

Reads Rooms.

## `public_op:projects.list_projects`

### Owner

`module:projects`. The project list (R0-13, A06 rule 1).

### Callers

`module:operations`.

### Inputs

The transaction; whether to include the archived ones.

### Outputs

One answer object: the active projects, and with them the archived ones when
asked, by last-changed instant latest first, then `project_id`; never an
anonymised one. Each item carries `project_id`, display name, alias,
status, `customer_ref`, the last-changed instant and, when archived, the
date it was archived — no object and no rooms.

### Observable effect

None.

### Enforces

Never the archived alone (Primary actions); the choice checked against its
closed list (A19 rule 3).

### Errors

`invalid_request` (`outside_closed_list`).

### State impact

Reads Projects.

## `public_op:projects.write_imported_project`

### Owner

`module:projects`. Write one picked v1 project with its object and rooms,
under its own ids and instants (A16 rule 7).

### Callers

`module:migration_import`.

### Inputs

The transaction; the v1 project with its object and rooms; the display name
and alias it arrives under; the `customer_ref` it links to, or none for a v1
project that names no customer (R0-16: a project's customer is optional).

### Outputs

The written project.

### Observable effect

The Project with its source created, last-changed and archived instants,
revision 1, no request id; its rooms with their ids and added instants.

### Enforces

Ids kept verbatim (R0-44, R0-50); instants as the source holds them (State
1, "Revisions and times").

### Errors

None; `migration_import` checked conflicts and malformed records before.

### State impact

Writes one Project and its Rooms.

## `public_op:artifact_pointers.publish_pointer`

### Owner

`module:artifact_pointers`. Publish a pointer of a declared type with a
request id (A07, A08, A01).

### Callers

`module:operations`.

### Inputs

The transaction; the project; the type; `uri`, `payload_ref` or both; the
digest as given; the request id; the publisher (Kernel naming the session,
or the owner); the action's instant.

### Outputs

The pointer with every fact 'list artifacts' answers for it — id, project,
type, version, status, owner service, `uri`, `payload_ref`, digest,
publisher and published instant — and `changed`.

### Observable effect

A new pointer `published` with the next version of its type; the type's
published pointer becomes `superseded` with its instant; one transaction
(A07 rule 1). A repeat changes nothing.

### Enforces

(3) the project exists; (4) the type in
`release_declarations.declared_artifact_types`, `uri` or `payload_ref` not
blank, the request id's form; the archive check, a repeat's too; the request
id among this project's pointers, project and publisher among the facts — a
repeat answers the pointer whatever its status now (A01 rules 3, 4, 6); (6)
an archived project, a conflict. The owner service is
`release_declarations.owner_service_of_type`'s; the digest is stored, never
checked (A07 rule 6).

### Errors

`not_found` (`unknown_project`); `invalid_request` (`missing_value`,
`malformed_request_id`, `unknown_artifact_type`); `refused` (`archived`,
`conflict`).

### State impact

Writes one pointer and supersedes one.

## `public_op:artifact_pointers.withdraw_pointer`

### Owner

`module:artifact_pointers`. Withdraw a published pointer (A07 rule 4, A08
rules 4, 7).

### Callers

`module:operations`.

### Inputs

The transaction; the pointer id; the withdrawing principal; the action's
instant.

### Outputs

The pointer, `withdrawn`.

### Observable effect

The pointer becomes `withdrawn` with its instant and principal; no earlier
version becomes `published` (R0-14).

### Enforces

(3) the pointer exists — for Kernel already resolved at stage (2); (4) a
removed type refused (A22 rule 5); (6) a withdrawn or superseded pointer, a
pointer of an archived project refused (A05 rule 4, A07 rule 5).

### Errors

`not_found` (`unknown_pointer`); `invalid_request` (`unknown_artifact_type`);
`refused` (`withdrawn`, `superseded`, `archived`).

### State impact

Writes one pointer.

## `public_op:artifact_pointers.project_of_pointer`

### Owner

`module:artifact_pointers`. The project a pointer names (A08 rule 7).

### Callers

`module:operations`.

### Inputs

The transaction; the pointer id.

### Outputs

The pointer's `project_id`, or that no such pointer exists.

### Observable effect

None.

### Enforces

A withdrawal names the pointer alone; its project is the pointer's own
(A08 rule 7).

### Errors

None; "no such pointer" is the answer, which `operations` gives as
`not_found`.

### State impact

Reads one pointer.

## `public_op:artifact_pointers.list_pointers`

### Owner

`module:artifact_pointers`. Every pointer of a project: the history (A06
rule 3, R0-02).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`.

### Outputs

Every pointer — published, superseded, withdrawn, of removed types too —
each with every fact M05 holds: id, project, type, version, status, owner
service, `uri`, `payload_ref`, digest, publisher and published instant, the
superseded instant, the withdrawing principal and withdrawn instant; by type,
then version highest first, then pointer id.

### Observable effect

None.

### Enforces

An anonymised project's pointers are listed as before (R0-62); A22 rule 4.

### Errors

`not_found` (`unknown_project`).

### State impact

Reads pointers.

## `public_op:artifact_pointers.latest_pointer_of_type`

### Owner

`module:artifact_pointers`. The one published pointer of a declared type
(R0-17).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`; the type.

### Outputs

The published pointer, or that none is published — also after a withdrawal,
which never falls back (R0-14).

### Observable effect

None.

### Enforces

(4) a type `release_declarations.declared_artifact_types` does not declare
is unknown (A22 rule 5).

### Errors

`not_found` (`unknown_project`); `invalid_request` (`unknown_artifact_type`).

### State impact

Reads pointers.

## `public_op:artifact_pointers.published_pointers`

### Owner

`module:artifact_pointers`. A project's `published` pointers, for the agent
projection (State 1, "Projections and answers").

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`.

### Outputs

Its published pointers in 'list artifacts' order (A06 rule 8), a removed
type's included (A22 rule 4).

### Observable effect

None.

### Enforces

No superseded or withdrawn pointer; `business_confidential`.

### Errors

None; an unknown project answers none, `projects` having answered first.

### State impact

Reads pointers.

## `public_op:artifact_pointers.delete_pointers_of_project`

### Owner

`module:artifact_pointers`. Delete every pointer of a project deleted whole
(R0-60).

### Callers

`module:operations`.

### Inputs

The transaction; the `project_id`.

### Outputs

How many pointers it deleted.

### Observable effect

Every pointer naming the project is gone.

### Enforces

Called only in the transaction of a deletion whole; anonymising keeps the
pointers (R0-62).

### Errors

None.

### State impact

Removes pointers.

## `public_op:artifact_pointers.write_imported_pointer`

### Owner

`module:artifact_pointers`. Write one v1 pointer of a picked project, under
its id and instants, the import as its publisher (A16 rule 7, M05).

### Callers

`module:migration_import`.

### Inputs

The transaction; the v1 pointer — id, project, type, version, status,
reference, digest, published and superseded instants.

### Outputs

The written pointer.

### Observable effect

The pointer as the source holds it, publisher the import.

### Enforces

Ids and instants kept (R0-44, R0-50); `migration_import` checked its type
and versions (A16 rule 4, A22 rule 7).

### Errors

None.

### State impact

Writes one pointer.
