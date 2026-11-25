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
