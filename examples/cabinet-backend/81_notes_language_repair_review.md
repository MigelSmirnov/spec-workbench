# Stage 8.1 revalidation — notes-language and canonical-lineage repair

## Scope

This review revalidates the assembled module packets after the bounded State 7 notes-language repair described by `81_notes_language_repair_task.md` and the required backward lineage repair that made the already-accepted runtime façades structurally addressable in States 3–6.

No new product behavior is introduced. The repair does four things:

1. adds positive modal language to Factory-blocking callable notes without changing their meaning;
2. restores the missing `refresh_estimate_snapshot_handler` dependency note;
3. replaces incorrect API handler service bindings with the service types already required by their contracts and `create_app` composition;
4. restores canonical State 3–6 lineage for nine façades that were already present in runtime repair documents and the assembled specification but absent from one or more structural plans/catalogues.

## Validation evidence

The post-repair validation run established:

- aggregate assembly: 7/7 checks ready, 0 errors, 0 warnings;
- canonical State 7 notes gate: 0 blocks, 0 reviews;
- Factory-compatible notes-language diagnostic: 0 blocking findings;
- focused notes/propagation tests: 11 passed;
- State 6 contract coverage: 59/59 resolved, 0 errors, handoff ready;
- Router Closure: unchanged 13/13 external operations resolved;
- 183 remaining `note_without_positive_modal` findings are non-blocking normalization work explicitly deferred by the repair task.

The State 5 coverage diagnostic also reports six pre-existing flow-evidence gaps for two incomplete/source-loss operations and four bootstrap/agent-administration operations. They are outside this notes repair, do not affect the repaired nine façade operations, and do not block aggregate assembly. They remain separate cleanup work rather than being hidden in this revalidation.

## Semantic-delta method

Each Stage 8.1 module slice was rebuilt from both:

- base repair-task commit `5218ecac252f095c3f4c5adfa2b3a0d15809a986`; and
- the repaired current design state.

For every module, the review compared accepted evidence, owned symbols, exports, contracts, dependency contracts, models, persistence, direct dependencies, routes, deterministic callables, resolved rules, and semantic note text. The current deterministic structural review was then rerun.

Across all twelve modules:

- structural review blocks: 0;
- structural review findings requiring semantic review: 0;
- contracts changed: none;
- dependency contracts changed: none;
- models/persistence changed: none;
- direct dependencies changed: none;
- routes/deterministic callables changed: none;
- resolved rules changed: none.

## Module verdicts

| Module | Current slice SHA256 | Delta | Revalidated verdict |
|---|---|---|---|
| `models` | `a982d5b94f49b36d0c99db6ba69e27ff4b849689245cc45d22c5fc5072da0c70` | byte/semantic identity unchanged | PASS |
| `access_control` | `367487c64c14434b70d88855e5b5b98e2eba304b3ce93ca20432974d954f0320` | `authorize_operation` requirement strengthened from imperative to semantically identical `MUST`; accepted flow evidence gained only repaired cross-flow capability lineage | PASS |
| `durable_archive` | `286b618f8ab8ec7ebc9baa0dfb33c4fb8c7e28e808800b3346dadd189764a258` | lowered specification unchanged; accepted flow evidence reflects repaired cross-module capability lineage only | PASS |
| `registry_context` | `73de30fbc52b683ac234d6906b82513a666dbd60207833ef515073d4ec2a1878` | lowered specification unchanged; accepted Registry flow evidence now records catalogue publication handoff to synchronization | PASS |
| `holded_gateway` | `c49a9abe2b90ebddd8022f791e2fcf4d440a635a35b1b6f372e96e54dedfd4d5` | create/lookup note meaning unchanged, expressed with positive modal; publication flow evidence enriched only with status-read lineage | PASS |
| `synchronization` | `e35ead9bf4a8aa1dde2e3ac2433ea603ce157646806bf65f2832f876530eda38` | existing reconciliation/catalogue/connection/membership façade obligations made canonically addressable and modal; no lowered contract or transport-policy change | PASS_INTERNAL_VARIATION |
| `plan_actual` | `c216d05026631962f64d6168cff1ed0ff33430dcd0378a4cefd8924deec00d0f` | existing proposal/decision/unmatched façades made canonically addressable and modal; snapshot note modalized; formulas/contracts unchanged | PASS_INTERNAL_VARIATION |
| `holded_publication` | `1759a706d64bd27d91d05b60a1956a12e0ad206bb5ccfe2ae4f7fc880ab39f92` | existing status façade made canonically addressable/modal; publication lifecycle and gateway rules unchanged | PASS_INTERNAL_VARIATION |
| `retention_release` | `e1342be58ff71c50f58854e27d0d901dc81f94dade7a3d3f5ca82d4297c4858b` | existing status/membership evidence made canonically addressable; release policy/contracts unchanged | PASS_INTERNAL_VARIATION |
| `api_irregular` | `f8d080f1cb84a333d2e1397a83fe184305f47c87e118befbcb56e4d4cdd62865` | semantic packet unchanged; hash movement is provenance/source-line identity only | PASS |
| `api` | `400a867c24c45c6911c326f0891dbcb6d6d668fd3f429b833e29e32d6291d994` | incorrect archive/gateway handler dependency notes removed; handlers now name the exact `PlanActualService`, `HoldedPublicationService`, or `RetentionReleaseService` already required by delegate contracts and app-state composition; deterministic routes/contracts unchanged | PASS |
| `bootstrap` | `f3f5be217098c53d5243dbefd0eeb8bbcf7bf0c44577a8486720a7ce43958785` | enrollment/rotation/revocation constraints are semantically identical with explicit positive modal | PASS |

## Conclusion

The Stage 8.1 verdicts remain closed after the repair. The changed slices do not introduce an unresolved semantic choice or expand implementation freedom beyond the previously accepted contracts. The repaired notes instead remove ambiguity that could lead Factory generation to a trivial implementation or the wrong runtime dependency.

`81_module_review_status.json` is refreshed to the current slice hashes. Factory admission may be retried only after the repository is returned to a clean committed state; Route B remains outside Workbench Stage 9.
