# Module Review Workbench

This workbench builds the final evidence packet used to compare accepted
business meaning with the implementation contract expressed by the assembled
specification.

## Public operations

- `list_modules(project)` lists final assembled modules;
- `build_slice(project, module)` returns the complete review packet;
- `review(project, module)` reports deterministic structural gaps and marks
  the packet for semantic/adversarial review.

Each slice separates:

1. accepted evidence — owned/consumed State 2 decisions, responsibility, flows,
   public operations, and any active external-contract records that explicitly
   name the module;
2. lowered specification — symbols, exports, owned contracts, dependency
   contracts, transitive model context, persistence, direct runtime
   dependencies, routes, and resolved rule values;
3. generation constraints — every applicable note from the final assembled
   `global_spec.json`, including semantic-repair notes.

## Semantic boundary

The deterministic review detects only provable cross-layer gaps. It does not
claim that note counts establish completeness and does not invent missing
business meaning.

Dependency contract types expand the review packet's model context without
silently adding them to `imports.module_internal`. The latter remains the
minimal direct runtime import surface required by `SPEC_STANDARD`; context
closure and Python dependency edges are deliberately different concepts.

An LLM or human reviewer consumes the packet and performs the Stage 7.1
adversarial questions included in `review_protocol`. Any ambiguity must be
repaired at its earliest owning design state and propagated forward.

## CLI and MCP direction

```bash
python tools/design_module_review.py examples/<case> --list
python tools/design_module_review.py examples/<case> --module durable_archive --slice --json
python tools/design_module_review.py examples/<case> --module durable_archive --review
```

A future MCP server should expose the same three operations directly. It must
not rebuild slices, parse sources, or perform hidden semantic inference in the
transport layer.
