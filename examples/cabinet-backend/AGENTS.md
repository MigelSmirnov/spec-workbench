# Cabinet Backend agent handoff

Current work is **Stage 8.1 — assembled module review**.

Stage 7.1 semantic E2E review is closed. Its accepted findings, repairs, and
runtime oracles remain authoritative inputs, but the current task is not to
repeat the flow review or execute the Factory runtime handoff.

Before editing the assembled Cabinet specification or declaring Stage 8.1
closed, read in this order:

1. `../../tools/MODULE_REVIEW_WORKBENCH.md`;
2. `71_semantic_e2e_handoff.md`;
3. list the assembled modules;
4. build the complete review slice for the target module;
5. read the accepted upstream State 1–7 sources whenever the slice exposes a
   semantic question.

List the assembled modules with:

```bash
python tools/design_module_review.py examples/cabinet-backend --list
```

Build the complete review slice with:

```bash
python tools/design_module_review.py examples/cabinet-backend \
  --module <name> --slice --json
```

Run the deterministic structural review with:

```bash
python tools/design_module_review.py examples/cabinet-backend \
  --module <name> --review
```

The slice is a review packet, not a semantic verdict. It separates accepted
evidence, lowered assembled specification, and generation constraints so that
the reviewer can inspect one final module boundary without reconstructing its
context ad hoc.

## Generation paths

Do not apply LLM-module completeness criteria to deterministic output.

The following Cabinet surfaces are assembled by deterministic Factory
backends:

- `models`;
- the `api` router;
- `api_irregular`;
- structured data blocks, including `config`, `rules`, and `persistence`.

Review those surfaces by inspecting their canonical specification input,
closed registries and references, validation result, and deterministic
lowering/emission. Their absence of generation notes is not a semantic gap.
Do not request notes merely to restate a model field, route row, data value,
storage projection, or another result derived by the applicable backend.

For a deterministic surface ask explicitly:

- is every input accepted by the backend closed, canonical, and validated?
- does every type, reference, route argument, projection, error mapping, data
  leaf, persistence class, and codec resolve according to `SPEC_STANDARD.md`?
- does lowering preserve the declared input without introducing a project
  decision or relying on LLM inference?
- does the emitter fail closed for unsupported or ambiguous input?

For an LLM-generated behavioral module ask explicitly:

- does the module preserve the accepted business meaning assigned to it?
- do its public exports remain narrow and semantic?
- does every owned contract have enough models, rules, dependencies, and notes
  to constrain implementation?
- can a trivial implementation (`None`, an empty collection, a constant
  success result, or simple forwarding) satisfy the packet without violating
  an accepted obligation?
- can two materially different observable behaviors satisfy the same packet?
- are dependency contracts present as review context without being mistaken
  for direct runtime imports or public ownership?

Record findings module by module. A zero-block result from `--review` means
only that no deterministic cross-layer gap was proven; it does not establish
semantic completeness.

Repair every confirmed finding at the earliest design state that owns the
decision, propagate it through all affected later states, rebuild
`global_spec.json` last, and then regenerate and re-review every affected
module slice.

Do not redesign `SPEC_STANDARD.md`, Factory, or the known deferred adapters DSL
gap as part of Stage 8.1. Do not rewrite the Stage 7.1 semantic runtime oracles
merely to make an assembled module pass review.
