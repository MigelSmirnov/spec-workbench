# Cabinet Kernel — requests from the Factory generation experiment, 2026-11-02

For the session that next opens this case. The Factory regenerated module
`run_graph` (`plan_run`) ten times, independently, from the exact generator
prompt of the accepted spec, and compared every candidate with the accepted
code. Four points came out of it for this case. None of them is a defect of
the running kernel, and none is a decision of this case yet: each is taken up
here by the case's own rounds and the owner. Before editing any name below,
run `design_provenance(cabinet-kernel, <name>)`.

## State examined

| Item | Value |
|---|---|
| Accepted spec | `962fbb6e…`, exported from `agent/cabinet-kernel` at `77d4acc` on 2026-10-25 |
| Accepted kernel tree | code-factory `034b50c9`, OTK-accepted run `20261025_204110` |
| Experiment | code-factory branch `claude/hello-87hv2c`, `experiments/microscope_emulated/run_graph/` (report `README.md`, register `../FINDINGS.md`) |
| Semantic witnesses (`71_semantic_test_export.json`) | 151/151 on the accepted tree and on each of the ten candidates put in its place |
| Recorded `plan_run` calls | 644, taken from the accepted tree during the witnesses; every candidate returns a byte-identical `RunPlan` on every one |

The ten candidates fall into two algorithm families (a topological order and
one forward pass, 8; lazy memoised recursion, 2, like the accepted code). The
spec fixes the behaviour of `plan_run`, not its algorithm, and that is as it
should be. What follows is where the generators reported having to choose,
and where their choices differ on inputs the kernel never passes to
`plan_run`.

## Relation to the strict-imports worklist

code-factory `docs/CABINET_KERNEL_STRICT_IMPORTS_WORKLIST_20261101.md` (branch
`ccr-84f22617-n37pq4`, updated 2026-11-02) lists 166 symbols to declare in
`imports.module_internal` under the rewritten SPEC_STANDARD §7. Item 1 below
is an import edit of the same kind and fits the same pass. Items 2–4 concern
the notes of `plan_run` and do not overlap with the worklist.

## 1. `EDGE_DELIVERY_RULES` is imported but not exported

`imports.module_internal["run_graph"]["data_provider"]` declares
`EDGE_DELIVERY_RULES` (decisions 47–48, A13), and
`module_functions["data_provider"]` owns it, but
`imports.internal["data_provider"]` (49 symbols) does not list it. It is the
only such gap in the spec.

Under §7, `internal` is each module's export list, so a symbol another module
imports should be in it. Generation is unaffected, because the slice takes the
consumer's imports from `module_internal`. But `normalize_spec` builds each
module's exports from `imports.internal`, so the normalized spec does not know
the table as an export. Every reader of exports, such as the microscope's
obligation lens, did not see A13's own table until the Factory read
`constants` as well. The microscope's static lens now names it
(`import_not_exported`).

To decide: add `EDGE_DELIVERY_RULES` to `imports.internal["data_provider"]` in
the strict-imports pass.

## 2. `plan_run` relies on preconditions its note does not name

`plan_run` is correct only on flow versions that `prove_version` admitted and
on values `answer_request` canonicalised:

- every input port of every node and every flow output has an edge or a
  constant, and no two edges that can both deliver end at one port
  (`80_notes.md:309`, phase 6; A05);
- guard values and stored value bytes are canonical JSON (`answer_request`,
  `read_value_bytes`).

The `[DEPENDENCY_BOUNDARY]` note (`80_notes.md:407`) says `plan_run` MUST
trust the flow version it is given, but does not say what that trust covers.
The generators saw the gap. On inputs built to break these preconditions,
the ten candidates and the accepted code fall into 8 behaviour classes:

| Input (refused before `plan_run` today) | Inputs | Classes | Choice the candidates differ on |
|---|---|---|---|
| a flow output with no edge | 428 | 2 | an empty set of edges counts as "all disabled", so `skipped_by_guard` instead of `not_produced` |
| a node input with no edge | 628 | 5 | the same, for a node |
| two unguarded edges into one port | 270 | 4 | which edge supplies the value |
| non-canonical stored bytes under a guard | 26 | 2 | compare bytes, or canonicalise first |

On the one fan-in phase 6 admits (two edges from one source, guarded on one
port with different values, in either order) all eleven agree.

To decide: name these preconditions in the `[DEPENDENCY_BOUNDARY]` note of
`plan_run`, so a regenerated module does not have to guess them, or record
that "MUST trust the flow version" is enough because phase 6 is the only
producer of flow versions.

## 3. Points of the `plan_run` notes the generators had to choose

Each generator was asked to name what it had to choose. These points recur,
with the readings that were chosen:

- the `port` of a `RecordedSource`, a `MappedListSource` and a constant's
  `StoredValuesRef`: the receiving input port (most), or the source's port;
- which `NodeExecution` is the "latest" when attempts are equal: the highest
  `attempt_number`, then `ended_at`, then position in the trace;
- whether waiting points are reported while the status is `running`, or only
  for the resting statuses;
- the conclusion of a mapped node whose elements are a mix of failed and
  waiting: waiting (most), or failed;
- what happens when a lookup finds no row in `EXECUTION_STATUS_CONCLUSIONS`,
  `EDGE_DELIVERY_RULES` or `WAIT_REASON_RESTING_STATUSES`: `undecided`,
  `pending` or `failed` as a fallback;
- a mapped node whose list has not arrived yet: one element without
  `map_index`, or no element.

On the 644 recorded calls all ten candidates agree with the accepted code,
including 11 calls with waiting points while `running`, 3 mapped nodes with
failed and waiting elements, and 30 traces with repeated attempts. So either
another rule already fixes these points, or the witnesses do not reach the
case where the readings part. The full notes, one per generator, are in
`run_graph/generator_notes.md` of the experiment.

To decide: for each point, name the rule that already fixes it, or pin it in
the `plan_run` notes and, where it matters, add a witness.

## 4. A cycle in the flow graph

`prove_version` refuses a cyclic flow version, so `plan_run` never sees one.
The accepted code still guards against it (`node_conclusion_active`). One
candidate without a guard raised `RecursionError` on a cyclic input built for
the experiment. Neither the notes nor a witness say what `plan_run` does on a
cycle.

To decide: whether "`prove_version` refuses cycles" is the whole answer, which
needs nothing here, or whether the `plan_run` note should say so.

## Reproduction

In code-factory, branch `claude/hello-87hv2c`. The semantic witnesses need
`bubblewrap` and CPython 3.12.3, as `RELEASE_SANDBOX_INTERPRETER` requires.

```bash
python tools/generation_microscope.py --project cabinet_kernel --module run_graph \
  --record tests/semantic --python <CPython 3.12.3>
python tools/generation_microscope.py --project cabinet_kernel --module run_graph \
  --candidates-dir experiments/microscope_emulated/run_graph/candidates --replay
```

Item 2's inputs come from `experiments/microscope_emulated/plan_run_stress.py`,
and the 644 recorded calls are kept in
`experiments/microscope_emulated/run_graph/results/plan_run_records.tgz`.
