# Stage 8.1 — assembled module semantic review (record construction migration)

## Verdict

**Closed (2026-11-09, second pass).** 39 modules reviewed: 39 `PASS`, 0
`AMBIGUITY`, 0 pending, 0 stale. `81_module_review_status.json` records each
verdict and its packet hash (`slice_sha256`, the FA002 rule over
`build_slice`), recomputed on the spec after the State 7 rounds below.

The 16 `AMBIGUITY` verdicts of the first pass were closed by text, not by
decision:

- **Note forms (§2).** Dotted navigation removed from the 16 modules
  (`54ebf13f`): "the X repository of that transaction", "begin of the
  store", "rollback of that transaction", repository methods named bare. One
  `PortalStore.begin` stays in `_authorize_project_operation`: the flow
  closure reads an obliged call only from a dotted form, and without it ten
  schema capabilities of the flows are unreached (tool gap, reported).
  Values inline (status codes, quoted phrases, member lists) removed; every
  rewritten note passed `check_note_draft`.
- **Enumeration members.** A member of an enumeration whose values contain a
  dot (`AuditAction`, `Capability`) is named by its value beside its address
  (#167); a member of any other enumeration by the name the models emitter
  writes, as the Factory prompt lists and asks for (round 23: 15
  contradictions where plain members were named by value). In
  `project_tracking` rounds 24–25 read even the value form, and then the
  value-plus-name form, of two dotted actions as wrong; those two notes name
  `PAYMENT_REGISTER` and `PROGRESS_UPDATE`, which the Factory validator
  accepts since code-factory #194. Owner decision 2026-11-09: every member
  is named by its declared NAME, `AuditAction` and `Capability` included;
  the 63 notes that still named a dotted member by value are rewritten
  (SOURCE.md "Owner decisions of 2026-11-09").
- **Q10 (owner 2026-11-09).** `create_expense_from_recognition` re-validates
  the publication model from the field values the instance dumps and refuses
  a failure as `ExpenseValidationError`; no attribute probing. The owner's
  `model_validate(instance, from_attributes=True)` would return an instance
  of the model's own class unchanged under the emitted configuration
  (pydantic 2.12, checked), so it would accept the incomplete object.
- **Prompt `model_copy` line.** Factory #200 makes the line defer to the
  builders; round 23 then judged that template line itself as an
  unclassified note in `financial_policy` (three topics, open). It is the
  Factory's text, not a slice text: `financial_policy` builds no record and
  its six notes are unchanged. PASS, and the topics go to the Factory.
- **IR defect** found by round 23: no builder for a replayed expense
  outcome; `build_replayed_expense_operation_outcome` added (`0a1ee28f`).
- **`ProgressPhoto.updated_at/updated_by`** stay nullable (owner
  2026-11-09, #147). **Registry URL** read only through `runtime_settings`
  (owner 2026-11-09, `3b943d13`).

State 7 rounds (provider `codex-cli:gpt-5.6-sol:medium`): r23 33 blocking
over 12 modules; r24 2 (`project_tracking`); r25 2 (`project_tracking`);
r26 clear. Open after r26: `financial_policy` r23 T1–T3 (Factory template).

## First pass (2026-11-09 morning), kept as history

**Open.** 39 modules reviewed: 23 `PASS`, 16 `AMBIGUITY`.


The first pass: 23 `PASS`, 16 `AMBIGUITY`, 0 pending,
0 stale. `81_module_review_status.json` records each module's verdict and its
packet hash (`slice_sha256`, computed by the FA002 rule from `build_slice`).
FA002 therefore blocks admission, as it must: no `AMBIGUITY` below is decided
here; each needs a text fix by the next State 7 pass or an owner/Factory answer.

Spec reviewed: `global_spec.json` after commit `a4e6b444` (record builders,
Q01–Q12 with Q07 answered again, imports closure, State 7 round-22 fixes).
Factory checkout `code_factory_cp_witnesses` main `9a8a5c14`; accepted code
`projects/client_portal_sandbox`.

How the review was done:

- Each slice: `python tools/design_module_review.py examples/client-portal
  --module <m> --slice --json`, and `--review` for the deterministic gaps
  (0 blocks in every module; `expense_intake` 1 review: the Q10 shape check,
  below).
- The four adversarial questions, per model-generated module, against
  States 0–5:
  1. Can the same slice give two observably different behaviours?
  2. Does a trivial implementation satisfy it?
  3. Is an accepted refusal, effect or invariant missing?
  4. Does the slice add behaviour that has no source?
- Question 1 was asked of the Factory's own prompt of each module by State 7
  round-22 (three reviews per module, judged, quotes checked); its verified
  topics are the evidence of the per-module table. Questions 2–4 were checked
  directly for the values the notes rewrite inferred (below) and against the
  accepted code.

## Values the notes rewrite inferred — checked

- **Audit entity kinds.** Every operation note that passes an
  `AuditEntityKind` member to a shared audit builder was compared with the
  accepted code (`application/*.py`, `entity_kind=AuditEntityKind.X`): 28 of 28
  agree (`upsert_manual_section_plan`: `BUDGET_VERSION` only when the manual
  version is created, `SECTION_PLAN` for the plan — the code's two audits). The
  six operations that name none (`authenticate_staff`, `sign_out_staff`,
  `bootstrap_first_administrator`, `import_snapshot`,
  `issue_service_credential`, `revoke_service_credential`) use a builder whose
  IR fixes the kind; each equals the code's (`STAFF_ACCOUNT`,
  `SNAPSHOT_IMPORT`, `SERVICE_CREDENTIAL`). **PASS.**
- **Recovery-override audit.** Note: `staff.recovery_override`,
  `STAFF_ACCOUNT`, entity the `staff_id`, project `None`. Code
  (`perform_recovery_override`): the same action and kind,
  `entity_id=str(account.staff_id)`, `project_id=None`; the IR
  `revise_staff_email` sets `email_verified_at` and `updated_at` to the one
  instant, as the code does. State 5 (administrator-only, one email-changing
  operation) agrees. **PASS.**
- **`change_staff_status` and `email_verified_at`.** Note: the instant for a
  transition into `active` from `pending_verification`, unchanged for every
  other transition including `suspended → active`. Code: identical (it keeps
  `account.email_verified_at` and replaces it only on pending → active). The IR
  takes it as a parameter (`revise_staff_status`), so the choice stays with the
  caller. **PASS.** Known divergence, not new: the accepted code still refuses
  sign-in and session resolution when `email_verified_at` is `None`, while the
  spec since the 2026-11-08 sweep says sign-in decides nothing on it; the code
  follows the spec at the next Route B (HANDOFF).
- **Credential issue** (IR fix of this migration): both issue operations now
  generate the id, issue the secret for it, and pass both; a trivial
  implementation that mints a second id is refused by the signature. **PASS.**
- **Q07 name**: `_project_expense_summary` must pass the active plan's
  `display_name` or `None`; passing `None` always (the running service) now
  violates its note. **PASS.**

## Module results

Open topics are the verified blocking topics of State 7 round-22 that remain
after the fixes of `a4e6b444` (seven fixed: five missing builder arguments in
`expense_management`, the bootstrap hash sentence, readiness "no external
check").

| Module | Mode | Verdict | Open evidence |
|---|---|---|---|
| `financial_policy` | generated | PASS | none |
| `transport_guard` | generated | PASS | none |
| `staff_bootstrap_cli` | generated | PASS | none |
| `budget_repository` | generated | AMBIGUITY | 1 §15.9 literal check (table names written into SQL) |
| `registry_gateway` | generated | AMBIGUITY | 1 enum member named by NAME and by value |
| `audit_writer` | generated | AMBIGUITY | 1 §2 note class (builder wiring under `FIELD_ASSIGNMENT`) |
| `authorization_guard` | generated | AMBIGUITY | 1 §2 dotted value beside its address |
| `staff_identity` | generated | AMBIGUITY | 13 §2 value inline, 4 dotted navigation, 1 other; prompt `model_copy` line |
| `staff_bootstrap` | generated | AMBIGUITY | 1 §2 |
| `viewer_access` | generated | AMBIGUITY | 1 value inline, 1 dotted; prompt `model_copy` line |
| `service_identity` | generated | AMBIGUITY | 6 value inline, 1 dotted; prompt `model_copy` line |
| `snapshot_import` | generated | AMBIGUITY | 9 §2 value inline |
| `budget_management` | generated | AMBIGUITY | 7 §15.9 literal, 4 dotted, 6 other, 1 inline; prompt `model_copy` line |
| `expense_management` | generated | AMBIGUITY | 4 enum member NAME vs value, 1 dotted |
| `expense_intake` | generated | AMBIGUITY | Q10 check against the prompt's reflection ban; 1 inline, 1 dotted |
| `project_tracking` | generated | AMBIGUITY | 2 value inline |
| `photo_management` | generated | AMBIGUITY | 5 dotted navigation |
| `derived_views` | generated | AMBIGUITY | 5 dotted navigation |
| `runtime` | generated | AMBIGUITY | 3 dotted navigation (`PortalStore.begin`, `PortalTransaction.rollback`) |
| all 20 emitted modules (`models`, `data_provider`, `record_builders`, `system_clock`, `credential_security`, the repositories, `portal_store`, `staff_bootstrap_store`, `binary_storage`, `api_irregular`, `api`, `runtime_settings`) | deterministic | PASS | emitted from closed IR; `record_builders` RC001–RC015 0 findings |

What the open evidence means:

- **§2 dotted navigation and values inline** (most topics) are the note forms
  SPEC_STANDARD §2 forbids: `PortalTransaction.staff_access`,
  `PortalStore.begin`, and enumeration values written beside their address.
  They predate this migration (the earlier handoff kept qualified method names
  because the flow closure reads obliged calls only from dotted forms). A
  generator can implement them either way, so the module is not PASS.
- **Enumeration member NAME vs value**: notes name dotted-value members by
  value (dedc9201); the Factory prompt shows the NAME. Both are one member, but
  the judge reads two.
- **Prompt `model_copy` line**: the Factory's generic model instruction
  ("derive a changed value with `model_copy` or construct a new instance")
  contradicts `record_construction_bypassed` for builder-owned models. This is
  the Factory prompt builder's, not a spec text.

## Owner and Factory questions

1. **Q10 mechanism (owner/Factory).** Q10 requires refusing a publication
   object lacking a declared field "by checking that input shape, never by
   catching a generic attribute error"; the Factory prompt forbids `getattr`,
   `hasattr`, `vars` and probing undeclared fields. Which mechanism may the
   generated code use (for example the model's set-fields record)?
2. **Prompt line on `model_copy` (Factory).** For a model whose builder a
   module is given, the generic instruction should defer to
   `record_construction_bypassed`.
3. **Note forms of §2 (owner).** Rewrite the dotted method navigation and the
   inline enumeration values in the 16 generated modules (a State 7 pass like
   the one of this migration), or accept the qualified-method form the flow
   closure needs; the enumeration NAME-vs-value naming needs one convention the
   Factory validator and prompt agree on.
4. **`ProgressPhoto.updated_at`/`updated_by` nullability (owner).** Every
   publish and update writes both (Q04); the type and the column stay nullable.
   Tighten to non-null with a schema migration, or keep.
5. **Registry URL outside `runtime_settings`** (open since 2026-11-08,
   SPEC_STANDARD 6.11; raised again by State 2 round-101 T14).
