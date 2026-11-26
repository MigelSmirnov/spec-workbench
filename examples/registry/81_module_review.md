# Stage 8.1 — module review of Registry (2026-11-25)

The record behind `81_module_review_status.json`. Each of the 23 modules was
reviewed from its packet
(`python tools/design_module_review.py examples/registry --module <name> --slice --json`)
by the Stage 7.1 adversarial method
(`skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md`):

- for every material flow and callable, the strongest materially different
  observable behaviour the packet still admits;
- placeholder resistance.

Every finding was repaired in its owning state, then reviewed again on the
rebuilt packet. No State 0–5 text changed: every repair is a State 7 note,
the State 6 import-file format, or a State 8 import edge.

## Deterministic modules

`models`, `data_provider`, `clock`, `runtime_settings` and
`store_persistence` are emitted by the Factory from closed IR. Their review
ran the Factory's own route on the Factory's own cut of each module:

1. `normalize_spec` and `build_local_spec`;
2. the module's emitter (`generate_models_draft`,
   `generate_data_provider_draft`, `generate_system_clock_draft`,
   `generate_runtime_settings_draft`, `generate_repository_draft`; Factory
   main `161f7c8d`);
3. compilation of every draft.

The first run found that the repository emitter refused `store_persistence`:
`SqliteStoreRepository` implements `StoreRepository`, but the module did not
import it. Its edges come from the State 8 skeleton, because an
emitter-written module lies outside the imports closure. The edge was
added (`2a3dc929`). On the final spec all five emit and compile.

The Workbench admission did not catch this. FA018 cuts every module, but
for an emitter-written module it runs no emitter, and the projection does
not derive the implemented-port edge. This is a tools gap, recorded for a
`tools/*` change.

## Behavioural modules

| Wave | Modules | Findings | Repairs |
|---|---|---|---|
| 1 | `operations`, `owner_interface`, `owner_sessions`, `migration_import` | 13, then 6 more opened by the repairs | `0013dcf8`, `2c2b07a9` |
| 2 | `store`, `audit_log`, `projects`, `customers`, `artifact_pointers`, `agent_sessions`, `service_access`, `service_api`, `configuration`, `instance_lifecycle`, `backups`, `random_values`, `given_values`, `upload_framing` | 26 | `43395d65`, `0a503a2e` |

The material repairs:

- **Audit.** A grant writes `session_project_granted` only when a project
  joined the set (M09).
- **Owner sessions.** The expiry pass decides by the time limits alone, so a
  request admitted before a sign-out still finds its session. The pass takes
  its reading in the same hold as an arrival.
- **Owner interface.** Each page names the links and forms it carries, so
  every owner action is reachable from a page.
- **Refusal paths.** Stated everywhere the State 5 Stages convention and
  A10 rule 3 require them, including agent-call refusals: the input that
  names the target, or the session header.
- **Numbers.** One ASCII grammar for given numbers (`check_value_forms`).
  `create_project` writes a stored number back as the text it was given, so
  an identical retry is a repeat (A01 rule 3).
- **Text forms.** Instants and dates are explicit forms, no longer a
  library reader whose accepted forms vary with its version. This covers the
  import file, owner dates and the backup record.
- **Smaller points.** Time boundaries (`at or past`), the scope of the
  import file's text-or-null check, Bearer scheme case, UTF-8 header
  decoding, exclusive IPv6-only listeners, and an empty filename naming a
  file. A failed snapshot's copy is removed, and the A18 rule 4 temporary
  name is used.

The reviewers' reports, with quotes, interpretations and re-reviews, were
working files of this session. This record keeps their results.

## Verdicts and the ledger

Final verdicts, as the reviewers gave them on the packets the ledger hashes:

- **PASS:** `operations`, `audit_log`, `projects`, `customers`,
  `service_access`, `service_api`, `configuration`, `instance_lifecycle`,
  `upload_framing`.
- **PASS_INTERNAL_VARIATION:**
  - `owner_interface`: page layout and presentation are free; which links
    and forms each page carries is fixed.
  - `owner_sessions`: a signed-out session whose step raised before
    `sign_out_owner` lingers, refused, until a time limit ends it.
  - `store`: the engine's busy wait under WAL is left to the engine.
  - `artifact_pointers`, `backups`, `random_values`: implementation detail
    only.
  - `given_values`: which code points count as unassigned follows the
    runtime's Unicode version.
- **Residual, low, settled after the reviewer's own named repair:**
  - `migration_import`: the instant text form, now explicit.
  - `agent_sessions`: the `read_session_access` path (`0a503a2e`).

  These packets changed only by those lines.

`PASS_INTERNAL_VARIATION` is recorded as `PASS`. The Stage 7.1 method
counts an internal variation as closed: no observable difference remains.
The admission code accepts only `PASS`, a divergence already recorded as
G18 in `docs/INSTRUMENT_INVENTORY_20261108.md`. Each module's summary in
the status file names its reviewer's class.

## Repair after the first Route B run (2026-11-25)

Route B run `registry-route-b-20261125T142104Z` stopped at
`migration_import`. The Factory's generation microscope (static lens)
found notes naming foreign exports that the module's import surface does
not carry:

| Module | Named, not imported | Recorded decision |
|---|---|---|
| `migration_import` | `PathElement`, `ImportCustomerValue` | rejected: never named in code |
| `artifact_pointers` | `PathElement` | rejected: never named in code |
| `projects` | `Customer` | rejected: named only to forbid reading it |
| `projects` | `ALIAS_MAX_CHARACTERS`, `OBJECT_FLOOR_AREA_MIN_EXCLUSIVE`, `OBJECT_ROOMS_MIN` | rejected: named only by a test clause |

Every decision stands, so the notes no longer name the symbols. The same
paths, fields and bounds are described in words, and the meaning is
unchanged. The `create_project` test clause now names its bounds through
`check_value_forms`, the function that applies them.

A first repair (`c0a576eb`) instead turned the constants into `uses`
(`reads`). The second Route B run (`registry-generation-20261125T145132Z`)
rejected `projects` at coverage: a `uses` entry obliges the code to import
the symbol, and only the test reads these. The original rejection was
right, and the second repair restores it.

The three packets changed by these lines only. The author re-read them
against the reviewed text and re-hashed them. No reviewer verdict
changed.

The same run hit the generation output limit (16000 tokens) on
`migration_import`, whose generated code was cut off. That is a run
parameter, not a specification defect.

## Repair after the third Route B run (2026-11-25)

Run `registry-generation-20261125T153831Z` rejected `backups` for two
reasons.

- **The `cryptography` package was not declared.** State 6 already
  decided the package ("This needs the `cryptography` package, pinned by
  digest", A18, A20), but no State 8 import table carried it. The
  candidate's four imports failed the Factory's `unknown_top_level_import`
  gate. `imports.third_party` and `imports.third_party_by_module.backups`
  now hold the four import lines. The encryption scheme is unchanged.
- **The no-follow flag was probed with `hasattr`.** Three notes require
  "without following a link", and the generator probed the flag
  defensively. They now say the flag is named directly and never probed.
  The flag is not named in the notes, because the Factory validator reads an
  upper-case name in a note as a data symbol (§15.3).

Only the `backups` packet changed. The author re-read it and re-hashed it.
No reviewer verdict changed.

## Repair after the fourth Route B run (2026-11-25)

Run `registry-generation-20261125T155255Z` rejected `owner_interface`:
its page renderer told an enumeration member by `hasattr(value, "value")`
(`reflective_attribute_access`).

- **`owner_interface`.** `_render_owner_page` now tells each value's kind by
  its declared type, never by probing an attribute, and writes an
  enumeration member as its value. Two `[BEHAVIOR]` notes, added during this
  review, give each answer type its own links and forms, so the code must
  tell those types apart. The earlier rejection of the eleven answer types
  these notes name ("renders every answer as itself") was therefore stale.
  They are now `uses` (`inspects`). Their field types are rejected: they
  are read by attribute.
- **`instance_lifecycle`**, before its generation. `start_instance`
  binds exclusively by setting no address or port reuse option, uses the
  socket module's IPv6-only option, and names every option directly. Its
  notes no longer name `LoadedConfiguration` or `OpenedStore`, which stay
  rejected because they are read by attribute.

A static-lens sweep of every behavioural module on the new spec is clean,
except for `operations` and `service_api`. Both still name types they do
not import, but both already generated and passed coverage, so they are
left unchanged. Only the `owner_interface` and `instance_lifecycle` packets
changed. The author re-read them and re-hashed them, and no reviewer
verdict changed.

## Repair after the fifth Route B run (2026-11-25)

Run `registry-generation-20261125T160218Z` rejected `owner_interface`
again for `reflective_attribute_access`, this time in a field-path walker:
`hasattr(value, "model_dump")`. The note forbade the probe but gave no
replacement. `_read_owner_request`'s path rule now says how to walk a
value:

- tell a model by `isinstance` against the pydantic base model class;
- walk its fields by iterating it, which yields name and value in declared
  order (checked on pydantic 2.12.5);
- tell an enumeration member by `isinstance` against the enum class.

`_render_owner_page` walks by the same rule. `owner_interface` declares
`from pydantic import BaseModel` in `third_party_by_module`.

Verified on the rejected candidate with that one helper replaced: the
Factory's full static gate set reports no blocking finding.

## The host is Linux (A20 rule 6, 2026-11-25)

Three of the rejections above were the generator hedging on the host. A
writer that had to open without following a link, or bind exclusively and
to IPv6 alone, was not told where the code runs, so it probed with
`hasattr`. As in cabinet-kernel (its A20 rule 3, 2026-10-18), the owner
decided that Registry runs on Linux alone with CPython 3.12.

- **State 2.** A20 rule 6 states the decision. Its Required tests 5–7 show
  the base image and Python, a release with external code loading, and an
  installation on a non-Linux kernel. A21 records the re-review. States 2–5
  rounds 131–135, 80–82, 68 and 58 closed. Their release-process topics
  were carried to generation, factory_checks or deploy, and the topics on a
  Linux baseline were accepted, as for cabinet-kernel.
- **State 7.** The no-follow notes of `backups` and the listener note of
  `start_instance` cite A20. The `backups` and `instance_lifecycle`
  packets changed by these words only. The author re-read and re-hashed
  them.

## The imports table against the accepted code (2026-11-25)

Once Route B had built all 23 modules (spec `ceb5f485`), the imports
closure compared the table with the code:

- **Six symbols the code annotates, and the union variants it names, were
  not in `uses`.** They were first taken as `uses` with basis `code`, then
  dropped again. The code evidence comes from the untracked `app/` that the
  deploy leaves on the line, and FA008 refuses that dirty checkout. Before
  OTK, an admission can therefore never see the code. These are
  annotations of locals, not part of the minimal import surface.
- **34 `inspects` uses the code never names are rejected.** These are the
  success variants in `operations` and `StartDiagnostic` in
  `instance_lifecycle`. The code tells an outcome by `isinstance` against
  `Refusal`, or by the union's `result` field, and reads the variant by
  attribute.

The closure is closed. Packets that changed were re-hashed after the
author re-read them, and no verdict changed.

## Every generic model walk states its means (2026-11-25)

Run `registry-generation-20261125T171458Z` rejected `operations`.
`_answer_class` walked the answer tree with `hasattr(value, "__dict__")`,
the same hole as `owner_interface`'s walker, whose rule had been written
only there. The same rule now stands in every note whose callable walks
models generically:

- `_answer_class` (`operations`);
- `_confirmation_binding_digest` (`owner_sessions`);
- `_write_service_answer` (`service_api`), which also tells enumeration
  members by `isinstance`.

The rule: tell a model by `isinstance` against pydantic's base model
class, take its fields by iterating it, and never use `hasattr`, `getattr`,
`setattr`, `vars`, `__dict__` or `model_dump`. Each of these modules
declares `from pydantic import BaseModel`.

`owner_sessions` and `service_api` had passed generation, and only by the
draw. The rejected `operations` candidate, with its walker rewritten to
the rule, passes the Factory's static gates.

## The closing drain is timed by monotonic_reading (2026-11-25)

Run `registry-generation-20261125T172939Z` handed `instance_lifecycle` back
for the spec (`undeclared_elapsed_clock_access`). The staged close drains
for at most `LISTENER_CLOSE_DRAIN_SECONDS` since the shutdown, a total
State 6 decided (owner, 2026-11-24). The note said "measured as the
socket's own timeout", which cannot bound a total, so the candidate read
`time.monotonic()`.

The note now times the drain by `monotonic_reading`, the module's
elapsed-time authority. One reading is taken at the shutdown and one
before each read. Each read waits at most the time left, and the drain ends
when no time is left or a read waits it out. With a clock that does not
move, as a test fixture's, a read that waits out its time still ends the
drain.

Checked on the rejected candidate with the deadline taken from
`monotonic_reading`. The Factory's time-source gate passes it, and the
original reproduces both findings.

## Test seams named (2026-11-25)

The `semantic_runtime` fixture went to an outside implementer. The owner
decided to close the seams it needs in the specification first. State 6
`60_contracts.md` now has a "Test seams" section, and State 6/7 gained three
internal functions:

- **`instance_lifecycle._start_passes`.** The pass notes moved here from
  `start_instance`, which now calls it once.
- **`backups._run_backup`.** The run's step notes moved here from
  `run_daily_backup_if_due`. That function now starts `_run_backup` with
  the look's UTC date as `run_date`.
- **`store._integrity_ok`.** `check_store_file` asks it for the
  `INTEGRITY` check.

Each seam is called through its module's name at call time, so replacing
the module's attribute takes effect. A test release is defined as the same
code beside another `data_provider`.

Behaviour is unchanged: the same steps sit under named functions. The
author re-read the `backups`, `instance_lifecycle` and `store` packets and
re-hashed them. The other twelve re-hashed packets changed only by the
global note indices that the two inserted notes shifted (checked on
`upload_framing` against `1c7486ee`); their texts are unchanged. The imports closure was rebuilt for the moved notes, and
the only change of the import surface is `LoadedConfiguration` in
`instance_lifecycle`, for `_start_passes`'s signature. The `start_instance`
notes also no longer name `StartDiagnostic`, which stays rejected: a step's
stopped answer is told by the union's `result` field.

## 2026-11-25: two A17 witness helpers, from the fixture report

The outside implementer's fixture (Factory line, `agent/registry-semantic-runtime`,
`4551451a`, `tests/FIXTURE_REPORT.md`) ran every witness. Two A17 failures
were the witnesses' own:

- `test_listener_failure_serves_nothing_keeps_store`: over an existing
  store, the loop held each endpoint with the test's own socket and then
  asked whether the owner's endpoint accepts. With the owner's endpoint
  taken, the test's socket accepted. The check now asks the endpoint the
  test did not take.
- `_accepts`: `connect` to port 65536 raises `OverflowError`, not `OSError`,
  so `test_service_address_with_tokens_and_wellformed` failed in its
  helper. The helper now answers false for it, as it already did for
  `getaddrinfo`.

No assertion about Registry changed. `review/A17.md` names the M2 check
anew.

## 2026-11-25: the upload body reaches OwnerActionStep

The fixture report found every upload failing with `transaction_failed`:
the generated `OwnerActionStep.run` read `self.body`, which nothing set.
The defect was the spec's. `OwnerActionStep.run`'s UPLOAD_IMPORT note
named "the body its OwnerRequestStep holds", but the step was built from a
`PreparedOwnerAction` alone, and that model has no body. Now
`OwnerActionStep.__init__` takes `body: UploadBody | None` and keeps it,
`OwnerRequestStep.run` hands its own body on, and the UPLOAD_IMPORT note
reads "the body the step holds". `UploadBody` is imported to annotate the
constructor. The `operations` packet was re-read and re-hashed.

## 2026-11-25: unknown service operation and the session cookie

Two more State 7 notes from the fixture report disagreed with what they
lower:

- `perform_service_operation` refused an operation name that is not a
  `ServiceOperation` member as `invalid_request` (`outside_closed_list`,
  stage 4). A09 rule 1 says "An operation no row names for the service is
  refused (rule 3)", and State 5 `serve_service_request` says it is refused
  at stage (1) as `not_permitted` (`outside_service_rights`). The note now
  says that. A request that cannot be read stays `invalid_request`. One
  phrase in State 5 still disagrees: the owner-action Errors aside (owner,
  2026-11-24) says the service API refuses an operation it does not know as
  `invalid_request`. It is left for the owner, and the owner's own rule
  there is unchanged.
- `_render_owner_page` wrote the cookie attributes "as they stand" right
  after the session id. The generated `Set-Cookie` had no separator before
  `Secure`. The note now spells out the value: name, `=`, session id,
  `; `, then the attributes constant as it stands. A13 and the constant are
  unchanged.

`operations` and `owner_interface` were re-read and re-hashed. The backup
location diagnostic that does not name `backup_dir` is a generation defect
and the spec is not changed for it: `probe_backup_location`'s RETURN_SHAPE
note already requires the diagnostic to name the item.

## 2026-11-25: owner form field names and the equal-ports diagnostic

Route B on `ebf2d6fe` (run `20261125_210728`) showed two more notes that
lower their state ambiguously:

- `_read_owner_request` filled "OwnerRequest's other fields and OwnerValues"
  from "the fields named by their path". The generated code counted the path
  from `OwnerRequest`, so `values.request_id`. The fixture counted it from
  `OwnerValues`, so `request_id`. State 6 (`60_contracts.md`, "an
  `OwnerRequest` or `OwnerValues` field by its name") decides for the
  fixture, and no name is shared by the two models. The SCHEMA_CONSTRAINT
  note now names both models' fields by their own name, with `values` adding
  nothing to the path. This one ambiguity caused about 90 of the 99 failures.
- `load_configuration` named "the failed item", and the code named both
  ports for the equal-ports check. A17 Required test 8 names the service
  API's address. The note now says `service_listen` alone.

Re-read and re-hashed: `configuration` and `owner_interface` for these
notes; `operations` for the State 5 text of `7c0f17b1`; `service_api` and
`instance_lifecycle`, whose packets show the changed neighbouring notes.

## 2026-11-25: every walk of the owner request follows the path rule

On `81f355dd` (run `20261125_212255`) the generated reader read the fields
by the new rule. It then checked what it read against the submitted fields
with a walk of its own from `OwnerRequest`'s root. That walk put `values`
into the path again, so every form was refused as unreadable. No note asks
for such a check; the generator added it. The SCHEMA_CONSTRAINT note now
says that every walk of an `OwnerRequest` by these paths, such a check
included, names its fields by the same rule. The note was prepared while the
neighbour re-ran Route B on the same spec, and it is exported only if the
defect returns. `owner_interface` was re-hashed.

## 2026-11-25: the target is read from the query for every method

On `873a48b5` (run `20261125_214201`) the reader took a POST's target from
its body, while the module's own forms put it in the action's query. About
55 checks failed. The generation microscope's chain-of-custody lens, run on
five generated `owner_interface` candidates from the runs, found no single
source of the target across them: one candidate reads the query, two read a
merged field map, and one reads the body for a POST. The note said "the
query parameter", and then "from the query for a GET and from the body for
a POST" for the other fields, so the generator applied that split to the
target too. The FIELD_ASSIGNMENT note now says the target is read from the
query for every method and never from a body. `owner_interface` was
re-hashed.

## 2026-11-25: target and csrf_value keep their constants' names

On `d2b6d56b` (run `20261125_215551`) the reader named `csrf_value` by its
own name. The fixture's `csrf` field went unread, and the form was refused
as carrying an unrecognised field. The author caused this. The
SCHEMA_CONSTRAINT note said "a field of OwnerRequest … by its own name
alone", which contradicts FIELD_ASSIGNMENT for `target` and `csrf_value`,
whose names come from `OWNER_TARGET_PARAMETER` and `OWNER_CSRF_FIELD`.
The own-name rule now excludes `action` (from the route), `target` and
`csrf_value`. Three samples in a row each broke a different part of the
reader, and each break was a gap or a contradiction in these two notes.
`owner_interface` was re-hashed.

## 2026-11-25: unknown field names and tuples of any length

On `7f4071bb` (run `20261125_220855`) the reader read POST correctly. Two
new failures came from this sample's own additions:

- It refused a request that carried any field it did not expect. A GET's
  `target` was one such field, so every read by target came back empty.
  VALIDATION_ERROR now says its causes are the only causes: a field no path
  names is left unread, and the target's query parameter never makes a
  request unreadable.
- It read `tuple[ImportPick, ...]` with two elements as a fixed pair, so the
  second element's type became `Ellipsis` and every import mapping failed
  (`ValueError` inside the transaction, answered `transaction_failed`;
  reproduced on a scratch copy of the run's code). SCHEMA_CONSTRAINT now
  says that every tuple of these models is of any length and all its
  elements are of the tuple's one item type.

Five samples in a row have each broken this one hand-written form reader in
a new place. State 6's naming rule exists only as prose in `60_contracts.md`,
which the generator does not see; the notes restate it. Making it a
structure the notes can reference is put to the owner.

## 2026-11-25: the import path, from run 20261125_222330

On `7f02a412` 88 checks passed. 14 failures were fixture stubs, and 9 were
on the import path. The author traced each one on a scratch copy of the
run's code, with every swallowed exception logged:

- **Empty tuple.** A form cannot carry an empty tuple: it has no position.
  `import_choices.customers` was therefore absent. "An absent field is
  none" made it `None`, and `OwnerValues` refused it, which emptied every
  import request. SCHEMA_CONSTRAINT: a tuple with no position given is the
  empty tuple, never None.
- **The step page had no form.** `_render_owner_page` listed a form for
  every answer except `ConfirmationStepAnswer`. The step page showed the
  inputs as text only, and a19 found no hostile value in any attribute. The
  page now has one form of the confirmed action that carries its
  confirmation value and inputs. The BEHAVIOR note already said what that
  form carries.
- **A closed import was answered as a missing value.** SHOW_CONFIRMATION
  asked `_confirmation_inputs` before mapping. Once the import closed and
  the kept file was dropped, it answered NoConfirmationInputs, which the
  code refused as a missing `import_choices`. The note now maps the picks
  first, so `import_closed` and `file_not_kept` come from the mapping.
- **Witness a06.** Its v1 pointer carried `version` as a JSON number.
  State 6 "The import file" says that versions are text of decimal digits,
  so the code's FILE_UNREADABLE was right. The witness now writes the
  version as text.
- **Fixture.** `owner_confirm` resent the step's original form without the
  step's `inputs.upload_number` and `file_digest`, which a browser submits
  as the step form's hidden fields (State 6). Every confirmed import was
  therefore bound elsewhere. Correcting this belongs to the implementer.

On the scratch copy, the first and fifth fixes alone brought these files
from 15 failures to 3. The other three are the step page, the order of
the closed import, and witness a06.

## 2026-11-25: a discriminated union is declared as Annotated

On `14c82418` (run `20261125_224840`) the import path reached confirmation.
The reader in this sample then lost `access_answer` (7 checks). The models
module declares a discriminated union as `Annotated[Union[...],
Field(discriminator=…)]`, and the reader recognised a union only by its
`Union` origin. SCHEMA_CONSTRAINT now says that the models module's union
is so declared and is unwrapped before its variant is chosen.
`owner_interface` was re-hashed. The four a16 confirmations still wait on
the fixture's `owner_confirm`.

## 2026-11-25: the owner form's fields become a table (owner's decision)

Six Route B samples of `owner_interface` each broke the form reader in a new
place: `values.` in a name, a check walking with `values.`, the target read
from a POST body, the CSRF field named by its own name, unknown names and
fixed-length tuples, and Annotated unions. State 6's naming rule existed only
as prose in `60_contracts.md`, which the generator never sees, and every note
that restated it was read differently. The owner decided on 2026-11-25 to
make it a structure:

- State 1 M29 `OwnerFormField`; State 6 `OwnerFormField(name, carrier,
  reads_as)` with the enumerations `OwnerFormCarrier` (request, values) and
  `FormValueKind` (text, integer, boolean, member);
- data provider `OWNER_FORM_FIELDS`, 44 rows: the three `OwnerRequest`
  fields a form carries and every leaf path of `OwnerValues`, a tuple's
  position written as `OWNER_FORM_POSITION_MARK` (`#`). The target and the
  CSRF value keep their own constants;
- State 3 (`data_provider` and `owner_interface`), State 5 (constants
  imported; the owner surface) and State 6 (`60_contracts.md`, the form
  paragraph) name the table;
- the reader's three notes and the renderer's addressing note reference the
  table instead of restating a rule. A union's variant is now chosen by
  `OwnerValues.model_validate` on its discriminator, so the Annotated
  sentence is gone.

`owner_interface` was re-hashed. The State 1, 3 and 5 rounds follow.

## 2026-11-26: the six findings left once the fixture was complete

On the deployed app of `e83d653b`, with the fixture complete (Factory
`aff05084`), 147 tests passed and 6 failed:

- **a09, service refusal order.** An owner action's name sent as a service
  operation, with inputs the service wire format does not declare, was
  refused `invalid_request` at stage (4). `_read_service_request` answered
  None for the whole body, so the operation was lost before the rights
  check. State 5 orders stage (1) first. Now `ServiceRequest.inputs` may be
  none: a readable envelope with unreadable inputs keeps its operation,
  and `perform_service_operation` refuses the inputs only after the token
  and the rights (State 6 model and wire-format paragraph; the reader's
  SCHEMA_CONSTRAINT and VALIDATION_ERROR notes; the operation's
  SECURITY_BOUNDARY note).
- **a13, the session on the page.** The sign-in page listed the answer's
  `session_id`. A13 rule 7 carries the identity in the cookie alone. The
  renderer's SECURITY_BOUNDARY note now forbids writing it into the page.
- **a15, witness.** Its control called `validate_project_reference` as
  Cabinet Kernel for a project the agent session did not hold. A10 refuses
  that, so the kernel's control is now `read_session_access`.
- **a18 ×3, SQLite's companion files.** The decrypted copy, opened for the
  check, left `-wal` and `-shm` files in the backup location. The
  `_run_backup` notes now remove both unencrypted copies together with
  their companion files, as `discard_new_store` already does for a new
  store.

Re-hashed: models, backups, operations, service_api, owner_interface.

## 2026-11-26: the CSRF field is read, from run 20261126_091939

Route B on spec 063010fd (Factory `agent/registry@3e7d4f1d`) blocked 98 of
114 checks: every owner POST was refused at stage 1 as `csrf_refused`. The
generated `_read_owner_request` read a form only by the rows of
`OWNER_FORM_FIELDS` and left `csrf_value` None. The prompt allowed it: the
FIELD_ASSIGNMENT note named the CSRF field by `OWNER_CSRF_FIELD`, but the
SCHEMA_CONSTRAINT note said the reader names no field "in any other way" and
the VALIDATION_ERROR note said a field no row names "MUST be left unread" —
and the CSRF field is in no row by the decision of 2026-11-25 above ("The
target and the CSRF value keep their own constants"). `_render_owner_page`
already wrote it as the exception ("but the target and the CSRF value").

- State 7: the three notes of `_read_owner_request` now except the field
  `OWNER_CSRF_FIELD` names, and the reader reads it from the query or the
  body as it reads the rows' fields. State 6 prose (`60_contracts.md`) says
  the same; State 5 already did. A13 and the models are unchanged.
- Imports: the scope's candidates re-read, none new; basis renewed.

`owner_interface` re-read on its new slice: one reading of the CSRF value
remains, no note lets it stay None when the form carries it, A13 rule 5's
refusal is still where it was. PASS. Re-hashed: owner_interface.

## 2026-11-26: the file part is read in delimiter-length pieces, from run 20261126_101151

Route B on spec 1cb1c0f4 (Factory `agent/registry@1a6ba1d8`) timed out its
aggregate check at 900 s on
`test_a19_data_not_code::test_import_file_size_limit_counted_over_received_bytes`:
five uploads of about 50 MiB. The reused `upload_framing` draft (`f78d959d`)
read the file part with `stream.read(1)`, about 53 s per upload before the
socket's own costs; the earlier draft (`8e010271`) asked for the delimiter's
length less the bytes it held, and the whole suite took 302 s. The note bound
only what is held, so both were legal. Owner, 2026-11-26: name the read size.

- State 7: `MultipartFileBody.read` calls `stream.read` only while it holds
  fewer bytes than the delimiter's length, each time asking for that length
  less the bytes held. The second clause came out of this re-read: asking
  for "the length less the bytes held" alone asks for zero bytes when the
  whole length is held, and the VALIDATION_ERROR note takes empty bytes
  before the delimiter for a stream that ended. The hold bound and A13 are
  unchanged; State 6 states only the bound.
- Imports: the scope re-read, `uses` still empty; basis renewed.

`upload_framing` re-read on its new slice: one read size, no zero-byte read,
the end of the stream still told from the delimiter. PASS. Re-hashed:
upload_framing.

## Known tooling limits met in the review

- **Union variants.** The review packet does not expand union variants
  (`OperationAnswer`, `ConfirmationInputs`, `CustomerView`, …) or show
  data-provider constant values. The Factory's own local spec does carry
  them: for `owner_interface` it holds 136 models, every answer variant
  included. Reviewers read them from `global_spec.json` and
  `70_data_provider_closure.json`.
- **Emitter edges.** As above: FA018 runs no emitter on emitter-written
  modules.
- **Factory checks the Workbench does not run.** Neither the State 7 gate
  nor `check_note_draft` runs the Factory validator's §15.3 check of
  upper-case names. No Workbench check compares a contract's stated
  dependency with `imports.third_party`.
- **Code evidence before OTK.** The imports closure reads the deploy's
  untracked `projects/<p>/app/`, and FA008 refuses the checkout while that
  directory is there. Before promotion, the two cannot both pass.
- **Microscope constants.** The chain-of-custody lens reports every
  imported data-provider constant (`OWNER_ACTIONS`, `OWNER_TARGET_PARAMETER`,
  …) as absent in 0/5 candidates. Every candidate imports and uses them, so
  the lens does not see constants read inside a function.
