# Stage 7.1 — Portal Deliverer semantic handoff

Reviewed 2026-11-21 against `skills/spec-authoring/STAGE_7_1_SEMANTIC_HANDOFF.md`.
This is a pre-code semantic review, not Stage 8.1 module admission or runtime
execution evidence. Authoritative sources: accepted `02_rules.md` decisions,
`01_models.md`, `30_modules.md` and `30_trace.json`, the six flows of
`40_flows.md`, `50_public_apis.md`, State 6 closures/contracts, router/clock
closures, and `80_notes.md`. Assertions are requirements on future code.

## Reconstructed behavior graphs and material branch scenarios

Each row is Given → When → Then; the named owner makes the decision. These
scenario requirements include the boundaries outside the deliverer. They do
not introduce new service operations or demand that the deliverer call Portal.

| State 4 flow | Reconstructed graph, decisions and observable branches |
|---|---|
| service_start | Deployment trigger → runtime_settings reads settings → deliverer_service validates configuration/connections and token → deliverer_router builds surface → server listens. Valid settings/credential/connections: listening on configured loopback port. Invalid setting, connection or token: process ends before listening, no credential in output, no durable state. After listening, signal stop versus server failure has the A8 exit outcome. Deployment owns dependency admission (A9): vulnerability or incomplete scan blocks deployment. |
| answer_health | Deployment request → router → deliverer_api.answer_health → health result. No token required; answer carries only health, no project, file, setting or clock access. A server not listening supplies no answer; deployment owns recovery. |
| scan_project_photos | Authenticated caller → router/API guards → photo_delivery → confirmed connection → source_folder observation → delivery_store records → ScanResult. Bad token/form/project: boundary refusal. Missing/unconfirmed/unavailable connection: refusal without changes. Ignored/link entries: absent. Ordinary file: first A1 rejection rule, otherwise ready/placed/published according to records. Unlistable nonignored directory or damaged record: whole operation refused, no partial success. No source/state mutation; caller may rescan a changing folder. |
| deliver_one_photo | Authenticated request → connection/folder/source-id guards → photo_delivery takes project lock → reads placement and mark → replay OR source validation/hash → photo_preparation → image then placement write → PlacementOutcome. Existing placement: unchanged replay even if source removed. Bad name: no forbidden open and no write except lock. Changed hash, rejected source, decode/size/write failure: the A3 failed outcome. Damaged records/unsafe storage reference: whole-request refusal. Image-write succeeds but record-write fails: no completed placement; retry completes under A3/A6. Every branch releases lock; concurrent calls serialize and produce one placement. |
| record_publication | Authenticated request/identifier guards → photo_delivery reads system clock once → confirmed connection → project lock → placement then mark → new mark OR immutable replay OR refusal. Unplaced (including source placed only in another project): not_placed. Same photo_id: first mark unchanged. Different photo_id: publication_conflict, no mutation. Damaged/unwritable mark: state_unavailable. No source-folder availability needed; replay/refusal never changes stored mark. |
| owner_delivery | Owner trigger → external calling agent reads Portal staff list → preflight → scan → owner chooses ready/placed files → deliver → skip publication if photo_id already known, otherwise Portal.publish → mark → per-photo report. Old Z/offset date or unreadable list: no placement/publication; report project requiring repair. Refused scan: stop/report. Failed/refused photo: report and continue next selection. Lost/refused publication: report failure, no automatic retry. Successful publication with failed mark: report published but unrecorded. Owner-requested rerun while hidden: same Portal photo_id then mark. Owner made visible before recovery: accepted A4 409 limit, report failure; no invented photo-id recovery. Showing photos is a separate owner action. |

## Adversarial ambiguity and placeholder resistance

For each flow above, the review asked once: “Construct the strongest materially
different alternative observable semantics that still satisfies this complete
specification slice.” It also asked whether None, an empty collection/DTO,
constant success, forwarding, or unconditional exception could satisfy it.

| Flow | Strongest alternative considered | Disposition and placeholder resistance |
|---|---|---|
| service_start | Serve before validating credentials, or keep serving after startup failure. | PASS: A5/A8, run_service order and failure exits forbid it. An unconditional exit fails valid-start scenario. |
| answer_health | Read project configuration or authenticate before reporting health. | PASS: health boundary and answer_health explicitly forbid these reads. Empty answer fails HealthAnswer. |
| scan_project_photos | Hide unreadable directories as an empty complete scan; choose status before rejection rules. | PASS: A1 and source_folder/observation notes require whole-operation refusal and ordered classification. Always-empty scan fails ordinary-file branch. Traversal strategy can vary only within accepted ordering/read constraints. |
| deliver_one_photo | Re-encode replay; overwrite prior content after replacement; treat damaged record as absent. | PASS: A3/A6 and orchestration require record-first immutable replay, new identity for changed bytes, and refusal for corruption. Constant success/no-op fails stored bytes/record and replay evidence. Lock implementation may vary within OS/process guarantees. |
| record_publication | Replace first mark; mark a source placed in another project; recover photo_id by calling Portal. | PASS: A4/A5/A6 prohibit each alternative. No-op or constant marked cannot satisfy durable first mark and conflict/replay branches. |
| owner_delivery | Ignore old dates; retry ambiguous publication automatically; recover a visible unmarked photo. | PASS: A11 and owner_delivery guards forbid the first two; A4 records the third as unavailable. Unconditional refusal fails clean-date preflight and selected-photo success scenario. |

These answers concern observable semantics, not one unique implementation.
No unresolved AMBIGUITY was found in this slice. Structural support for the
router emitter and execution of external flows are separate admission/runtime
questions; this review does not waive either.

## Witness-by-witness scope review

Each executable witness retains its accepted ID. The invariant and its Required
test are the oracle; filenames and historical names add no requirements.

| Decision / invariant | Semantic scenario and scope correction |
|---|---|
| A1 INV-01 | Given source tree, scan/place/replay/mark preserve names, bytes, modes and mtimes. Source immutability is tested here, not bundled into INV-03. |
| A1 INV-02 | Given an unplaced source and invalid/ignored/link path, delivery fails without forbidden file or post-invalid-segment opens and writes nothing except lock. Allowed prefix and unrelated state/config opens are not forbidden. |
| A1 INV-18 | Given conflict marks in root/subfolder and ASCII case variants, scan omits those copies. A non-ASCII lookalike is not folded into the mark. |
| A2 INV-03 | Given source EXIF/GPS/XMP/comment, placed and Portal-downloaded bytes contain none. Removed size, orientation, checksum and source-immutability assertions: those do not witness metadata removal. |
| A2 INV-04 | Given offset/local/unusable/absent camera time and known modified instant, date is expected naive UTC. No dependence on current clock. |
| A2 INV-05 | Given returned publication and a real Portal publication, client_visible is exactly false and client overview excludes it until owner shows it. Removed caption/section assertions. |
| A3 INV-06 | Given first placement, replay returns it without durable mutation and exactly one record exists; a failed record write can complete on retry. |
| A3 INV-07 | Given placed/marked content, replacement and removal preserve earlier placement, bytes and mark; new content is judged as new. |
| A3 INV-19 | Given unplaced content only in conflict copy, no new placement/read from that copy; ordinary copy can place, and existing content can replay from its identity. |
| A4 INV-08 | Given mark, repeat preserves it and another photo_id conflicts. Source placed only in another project cannot be marked here. |
| A5 INV-09 | Given protected operation, absent/wrong credential refuses before invalid identifiers; health remains reachable without credential. |
| A5 INV-10 | Given unconfirmed connection, scan/place/mark refuse without durable mutation. Connection/read/startup variants remain requirements of A5's full Required test. |
| A5 INV-11 | Given scan/place/mark/refusal, answers disclose no private paths; scan/place/mark attempt no outbound network. Removed unrelated choice of HTTP success/refusal status from the path-disclosure oracle. |
| A6 INV-12 | Given simultaneous same-source requests, one placement and one immutable mark win; competing mark ID conflicts. Both thread and process schedules are required. |
| A6 INV-20 | Given malformed placement/mark record, no operation treats it as absent or mutates durable content. Linked/mismatched records and failed mark write are also required by the accepted item. |
| A7 INV-13 | Given counting clock, scan/delivery/health never read it; mark reads it once and records that instant. |
| A8 INV-14 | Given encoded bytes exceeding the read limit, failure is too_large and nothing is stored. A reduced bound is an isolated boundary-test parameter, not a changed product setting. |
| A9 INV-15 | Given matching vulnerability or unavailable scan, deployment admission refuses. Removed clean-scan-implies-approval and test-runner deployment_started assertions. |
| A11 INV-17 | Given old Z/positive/negative-offset date, caller preflight stops placement/publication and identifies project. No old dates passes preflight; it does not imply selected photos or completed publication. |

## Handoff result: five conditions

1. **Graph reconstruction:** six State 4 flow graphs above name accepted guards,
   owners, transitions, terminal results and recovery. No runtime-only rule is
   used as a semantic source.
2. **Ambiguity:** adversarial review above has no unresolved AMBIGUITY; accepted
   A4 recovery limit is retained, not repaired by the reviewer.
3. **Placeholder resistance:** positive branches require listening/health,
   actual observations, stored placement and immutable mark; empty/constant
   outcomes fail. Negative preservation witnesses are assessed with these
   positive branches, not mistaken for stand-alone proof of all functionality.
4. **Material scenarios:** Given/When/Then branches in the flow table and scoped
   executable witnesses have explicit observable results. Unavailable future
   runtime bindings do not make these requirements ambiguous.
5. **Owner repair:** review findings were witness overconstraint and manifest
   representation, owned by this Stage 7.1 test/handoff layer. They were repaired
   here; no product decision, accepted limitation, upstream note or global_spec
   was changed to make tests pass.

The pre-code scenario handoff is semantic_closed. This is not a claim that
all executable variants of each Required test have already been materialized,
that Stage 8.1 module review is complete, or that generated code passed tests.
`factory_execution_verified` remains false. Export admission is a separate gate.

## Export check after review

`export_to_factory.py --case portal-deliverer --project portal_deliverer
--factory-root /home/smirnov/jestor_VBC/exp_vbc/demo/code_factory --check`
was rerun on 2026-11-21. The semantic export plan validates the 19 witness IDs
and ten unique decision files. Every file is self-contained: the exporter copies
only manifest paths, so no unlisted helper-module import is required.

Admission remains BLOCKED, not only by imports:

- FA001 / FA008: dirty Workbench and Factory checkouts.
- FA002: missing Stage 8.1 module-review ledger.
- FA003: assembly blocked.
- FA022: imports_factory_unavailable (1).
- FA005: unsupported http_router_backend emitter fastapi_sync_v2.
- FA018: Factory local specifications cannot be built.
- FA019: State 7 prompt/question closure blocked by normalization.

Spec Inspector FA015 passes. These are reported, not bypassed by changing
the accepted router policy, closing module review without performing it, or
marking runtime execution verified. No Factory specification was exported.
