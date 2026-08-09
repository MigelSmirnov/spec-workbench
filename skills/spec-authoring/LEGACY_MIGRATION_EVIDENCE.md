# Legacy migration evidence workflow

Use this workflow when a project already has code whose decisions are not fully
represented in its design states or `global_spec.json`.

## Required sequence

```text
accepted design state
→ legacy probe evidence
→ classified findings
→ earliest owning design state
→ updated spec
→ deterministic diagnostic emitter
→ DEFECT / success
→ checkpoint evidence
```

Do not edit the spec before collecting evidence. Inspect code and focused tests,
not only notes. Inventory at least:

- predicates and state filters;
- ordering and conflict behavior;
- literals and external conventions;
- storage conversions and row/model projections;
- `CHECK`, `UNIQUE`, primary-key and index semantics;
- transaction boundaries and compound operations.

## Classify every finding

| Classification | Meaning | Action |
| --- | --- | --- |
| `derivable` | One result follows from the accepted model and backend version | Do not copy it into the project spec |
| `placement` | A product/config/policy value has no normative owner | Return it to `config`, `models`, `rules`, properties, or the owning behavior after product confirmation |
| `lowering` | A supported domain/storage representation pair needs the backend codec | Record only the supported relation; codec code and helper names remain backend-owned |
| `irregular` | The behavior is a genuine implementation responsibility outside deterministic vocabulary | Give it an explicit companion/module owner |
| `unresolved` | Evidence admits more than one semantic interpretation | BLOCK and ask the decision owner |

Code and tests are probes, never sources of norm. Do not select the majority,
the newest implementation, or the most common helper name. Preserve a stable
machine defect code and the exact evidence location so later project runs can
be compared without normalizing prose.

## Stable diagnostic boundary

Treat codes such as these as diagnostic classes, not as persistence grammar:

- `UNSUPPORTED_QUERY_GEOMETRY`
- `DYNAMIC_SQL_STRUCTURE`
- `CUSTOM_TRANSACTION_PROTOCOL`
- `CROSS_MODEL_PROJECTION`
- `IRREGULAR_WITHOUT_SATELLITE`
- `UNSUPPORTED_STORAGE_PROJECTION`
- `MISSING_QUERY_PREDICATE`

Do not add a query kind, storage form, or project-name exception for one
finding. A backend vocabulary may expand only after the same lowering
construction recurs across different projects and each occurrence has the same
semantic owner and round-trip behavior.

## Checkpoint record

For each project record:

1. probe version and accepted spec revision;
2. stable defect code, symbol/table and source location for every finding;
3. classification and normative owner, or `unresolved`;
4. diagnostic emitter result and reproducibility result;
5. which findings disappeared because they were derivable;
6. which findings remain irregular or blocked.

A migration checkpoint is complete only when every evidence item is either
derivable, addressable in an accepted design state, owned as irregular, or
explicitly blocked. Successful emission does not authorize silent decisions.
