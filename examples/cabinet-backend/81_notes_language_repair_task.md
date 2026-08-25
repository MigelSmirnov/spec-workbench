# State 7 repair task — notes language and dependency bindings

## Why this task exists

The Cabinet Backend specification passed every Workbench gate, was admitted by
the Stage 9 Factory admission gate, and was exported and accepted as a canonical
specification. Route B then stopped at `generate_affected_selected_drafts`, on
the first LLM module, **before its first provider call**:

```
✗ underspecified local spec — rejected before provider call
  - authorize_operation: function_contract_without_semantic_note
```

The Factory's pre-generation gate (`tools/spec_underspec_gate.py`) counts a note
as generation evidence only when all three conditions hold:

1. the note is scoped to the **bare callable name** — `parse:`, never
   `Parser.parse:`;
2. it carries a note class that establishes implementation semantics — any
   canonical class except `TEST_EVIDENCE` and `FALLBACK`;
3. its prose contains a **positive modal** — `MUST`, `SHOULD`, or `MAY`, not
   counting `MUST NOT`.

This specification's notes satisfy (1) and (2) and are written in the imperative
mood, so most of them fail (3): "Return the observed state." states no
requirement the Factory can recognise. Of 384 assembled notes, 139 carry a modal,
and those carry it incidentally, inside a subordinate clause.

The Workbench notes gate does not check for a modal at all, and its coverage pass
reads `80_notes.md` alone, so notes authored in the modular `80_notes_*.md`
files are not gated here either. Both gaps are recorded in
[Deferred](#deferred-not-part-of-this-task).

## Detecting the work

`notes_workbench/language.py` reproduces the Factory rule against the assembled
specification and locates each note in its authored Markdown line:

```bash
python tools/design_notes.py examples/cabinet-backend --language
python tools/design_notes.py examples/cabinet-backend --language --json
```

Its `contract_without_positive_note` findings are byte-identical to the Factory
gate's `function_contract_without_semantic_note` findings across all twelve
modules. The task is complete when the command exits 0.

Baseline at the time of writing: **220 findings, 27 blocking**.

## Work item 1 — nineteen callables need a modal (blocking)

Each of these has correctly scoped, correctly classified notes that state no
requirement. Reword one note per callable into modal form. **Preserve the
meaning exactly**; this is a language repair, not a semantic revision.

```
access_control      authorize_operation
api                 extract_bearer_credential, resolve_local_principal
bootstrap           enroll_local_agent, revoke_local_agent,
                    rotate_local_agent_credential
holded_gateway      create_holded_purchase, lookup_holded_purchase
holded_publication  get_holded_publication_status
plan_actual         get_unmatched_items, propose_invoice_line_matches,
                    record_match_decision, refresh_estimate_snapshot
retention_release   get_retention_status
synchronization     get_sync_status, get_working_set_membership,
                    observe_vps_connection, publish_registry_catalogue,
                    reconcile_transfer_outcome
```

Shape of the repair:

```
before  authorize_operation: [SECURITY_BOUNDARY] Evaluate authorization only for
        the exact operation supplied by the caller and return the decision
        without performing the protected business operation.

after   authorize_operation: [SECURITY_BOUNDARY] MUST evaluate authorization only
        for the exact operation supplied by the caller and MUST return the
        decision without performing the protected business operation.
```

Note that `SynchronizationService.get_sync_status` does **not** cover
`get_sync_status`: a class-qualified scope is a different address. Where the only
modal note sits on the class method, the module-level callable still needs its
own.

## Work item 2 — one callable has no note at all (blocking)

`api.refresh_estimate_snapshot_handler` has no note in any file. Eleven of the
twelve table-emitted handlers carry exactly one note of a single shape; this one
was missed. Author it to match its siblings, using the binding its own contract
requires:

```
refresh_estimate_snapshot_handler: [DEPENDENCY_BOUNDARY] MUST obtain the exact
PlanActualService bound to request.app.state.plan_actual and pass it to
refresh_estimate_snapshot.
```

`refresh_estimate_snapshot(service: PlanActualService, observation:
PresuProEstimateObservation) -> EstimateSnapshot` and `create_app` binds
`plan_actual: PlanActualService`, so this is read off the contracts, not chosen.

The Workbench exempts table-emitted handlers from the note requirement because
their transport is lowered deterministically from the router closure. The Factory
grants no such exemption: it sees a contract and demands prose.

## Work item 3 — seven notes name the wrong dependency (blocking)

These notes are *counted as coverage* and still direct generation to read the
wrong attribute. The linker checks writes, not attribute reads, so a wrong type
here survives to `verify`.

| Note scope | States | Delegates to | Contract requires |
|---|---|---|---|
| `calculate_plan_actual_handler` | `DurableArchiveService` / `state.archive` | `calculate_plan_actual` | `PlanActualService` |
| `request_holded_publication_handler` | `DurableArchiveService` / `state.archive` | `request_holded_publication` | `HoldedPublicationService` |
| `request_holded_publication_handler` | `HoldedGatewayService` / `state.holded_gateway` | `request_holded_publication` | `HoldedPublicationService` |
| `reconcile_holded_publication_handler` | `DurableArchiveService` / `state.archive` | `reconcile_holded_publication` | `HoldedPublicationService` |
| `reconcile_holded_publication_handler` | `HoldedGatewayService` / `state.holded_gateway` | `reconcile_holded_publication` | `HoldedPublicationService` |
| `evaluate_vps_release_handler` | `DurableArchiveService` / `state.archive` | `evaluate_vps_release` | `RetentionReleaseService` |
| `request_manual_vps_release_handler` | `DurableArchiveService` / `state.archive` | `request_manual_vps_release` | `RetentionReleaseService` |

The archive-backed and registry-backed handlers are correct, which is what makes
this look like a template applied and then only partly specialised. Replace both
the type and the `request.app.state.*` attribute with the pair `create_app`
binds for the service the delegate's contract requires.

## Work item 4 — remaining imperative notes (non-blocking)

193 notes across 15 files carry a semantic class without a modal. Only the ones
above block generation, because coverage is per callable and one qualifying note
is enough. The rest still reach the generator as prose, so they are worth
normalising, but they can be done file by file after the blocking work lands:

```
80_notes.md                              87    80_notes_flow4_semantic_repair.md        5
80_notes_access_control_backend.md       20    80_notes_holded_publication_runtime.md   5
80_notes_archive_runtime.md              16    80_notes_retention_release_runtime.md    4
80_notes_holded_gateway_runtime.md       16    80_notes_flow1_semantic_repair.md        3
80_notes_synchronization_runtime.md      11    80_notes_flow2_semantic_repair.md        3
80_notes_flow6_semantic_repair.md         7    80_notes_flow4_rule_refs.md              3
80_notes_flow3_semantic_repair.md         5    80_notes_flow5_semantic_repair.md        3
80_notes_plan_actual_runtime.md           5
```

## Constraints

- Edit the authored Markdown **and** the assembled `global_spec.json` together;
  the Factory consumes the assembled notes, the repair belongs in the source.
- Do not invent semantics. Work items 1 and 4 are rewordings. Items 2 and 3 are
  read off `contracts` and `create_app`.
- Re-run `python tools/design_assembly.py examples/cabinet-backend` — all seven
  checks must stay ready.
- Editing notes changes module review slices, so refresh the Stage 8.1 lineage
  (`81_module_review_status.json`) for every module touched, or Factory
  admission fails FA002.
- Export requires a clean Workbench checkout, and the Factory project already
  exists, so re-export with `--update-existing`.

## Deferred (not part of this task)

Two gaps in the Workbench's own notes gate let this specification reach the
Factory. Closing them recomputes the status of every case in the repository, not
just this one, so it is deliberately kept out of this repair:

1. `notes_workbench/gate.py` accepts a note with no positive modal, which the
   Factory rejects.
2. its coverage pass reads only `80_notes.md`; the modular `80_notes_*.md`
   files are ungated.

Until they are closed, `design_notes.py --language` is the check that predicts
the Factory's verdict.
