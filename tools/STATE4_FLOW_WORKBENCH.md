# State 4 Flow Workbench

State 4 is authored semantically by an operator/agent and constrained by deterministic tooling.
The tool does not invent flows from prose.

## Project inputs

- `30_modules.md` — accepted State 3 module responsibilities and candidate capabilities.
- `30_trace.json` — authoritative State 2 -> State 3 ownership trace.
- `40_flow_plan.json` — explicit operator-accepted list of State 4 flow needs.
- `40_flows.md` — reviewed State 4 flow descriptions.

`40_flow_plan.json` is planning input, not generated architecture. Adding, removing, merging, or splitting a planned flow is a semantic design decision.

## Work loop

Ask for the next incomplete planned flow:

```bash
python tools/design_stage4.py examples/<case> --next --json
```

The result may expose:

- the accepted flow key and purpose;
- required State 3 module references;
- candidate State 3 capability references;
- whether an existing flow is missing one of those explicit references.

It must not generate Trigger, Boundary, Steps, Outcomes, or Errors.

After authoring or revising a flow, run:

```bash
python tools/design_stage4.py examples/<case> --lint --json
python tools/design_stage4.py examples/<case> --coverage --json
```

`--lint` checks the authored structure and State 3 references. `--coverage` compares authored flows with the explicit plan.

Inspect an existing flow with:

```bash
python tools/design_stage4.py examples/<case> --get flow:<name> --json
```

Emit the machine-readable handoff with:

```bash
python tools/design_stage4.py examples/<case> --handoff
```

## Router workflows

Use the read-only deterministic router for multi-step work:

```bash
python tools/design_router.py examples/<case> work-state4 --json
python tools/design_router.py examples/<case> state4-coverage --json
python tools/design_router.py examples/<case> verify-state4 --json
python tools/design_router.py examples/<case> ready-state4 --json
```

`verify-state4` validates work in progress and does not require all planned flows to be complete.

`ready-state4` is the transition gate to State 5. It requires complete explicit flow-plan coverage in addition to State 3 prerequisites, State 4 lint, handoff, and repository tests.

## MCP direction

Future MCP wrappers should expose these deterministic operations rather than reimplement State 4 semantics:

- list/get flow;
- next planned flow;
- coverage;
- lint;
- handoff.

MCP must not decide which new flows should exist, author flow semantics, assign ownership, or freeze State 5 contracts.
