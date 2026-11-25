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
