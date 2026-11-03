# Cabinet Kernel — what the Factory must add for the 2026-11-03 change

Two defects found by the Registry pilot of 2026-10-31
(`findings/20261031_registry_pilot/`) reached the case. The accepted code still
has both. This case changes only its design and its tests; each item below is
the Factory's, on `main`, before or with the next export.

## 1. The fixture call `mcp_discovery`

`tests/semantic/RUNTIME_SURFACE.md` lists `mcp_discovery(method, *, token)`. Bind
it in `tests/kernel_runtime/runtime.py`. `mcp_request` cannot read a discovery
answer: `mcp_client.decode` treats every result as a `tools/call` result and
raises `SurfaceProtocolError` on `{tools: [...]}`.

## 2. Two focused checks

Add to `verification/configs/cabinet_kernel.yaml`, as its other witnesses:

- `kernel_a03_module_loaded_as_by_import` — `test_module_loaded_as_by_import`;
- `kernel_a16_tools_list_serves_every_operation` —
  `test_tools_list_serves_every_operation`.

- `kernel_a03_clock_entry_points_trapped` — `test_clock_entry_points_trapped`.

Then return here: A03 Required tests 12 and 13 and A16 Required test 13 take their
`[witness: verification:<name>]` tags. They carry none until then, because
`design_decision_witness` resolves a tag against that config and an absent check
is an error.

## 3. Regeneration

Route B regenerates `sandbox_runner` and `surface` from the specification:
`runner_source` (A03 rule 3) and `answer_request` `[FIELD_PROJECTION]`, whose rule
for a discriminated union was already there.

Checked 2026-11-03 on `projects/cabinet_kernel` at code-factory `1cdcf9e9`, in a
temporary copy of the code: both witnesses fail on the accepted code; they pass
once the runner enters the module in `sys.modules` and `_annotation_schema` unwraps
`typing.Annotated`. Those two patches were not kept: the code is generated.

The owner's decision of 2026-11-03: the clock rule guards against depending on the
time by accident, not against code written to get around it (K-02). So
`SANDBOX_TRAPPED_FUNCTIONS` only gains `time.clock_gettime`, `time.clock_gettime_ns`,
`time.thread_time`, `time.thread_time_ns` and `os.times`, and a trap on a class method
stops taking `self`: `datetime.datetime.now` concluded `crashed` instead of
`sandbox_violation`. `findings/20261103_clock/validated_runner_patch.diff` is the patch
these witnesses were checked on.

## 4. SPEC_STANDARD §7 and the slicer disagree

§7: "the projector imports the types named in the signatures of the consumer's contracts
and in the contracts of the provider functions declared in its `module_internal`". On
code-factory `1cdcf9e9`, `build_local_spec.slice_module(<normalized spec>, "run_graph")`,
with `strict_imports` either way, imports `read_value_bytes` and not `ByteSource`, the type
of its signature. The State 7 reviewers found the resulting prompt contradictory
(round 136). A document and a tool disagree, so per the Factory's rule this is reported,
not decided here. `65_imports.json` lists such types itself, which §7 allows ("listing is
no error"); they could leave it once the slicer does what §7 says.
