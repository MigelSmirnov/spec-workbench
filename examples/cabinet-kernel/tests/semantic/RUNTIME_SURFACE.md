# `semantic_runtime` — the fixture surface the witness tests use

The tests in this directory are the witnesses of the accepted decisions
(`[witness: verification:kernel_aNN_*]` in the Required tests). They are
written before the kernel is generated and never rewritten to fit it. The
Factory project supplies the `semantic_runtime` pytest fixture and binds each
call below to the generated public operations; the assertions stay as written.

This file is the one list of that surface. A test calls nothing that is not
listed here; a test that needs a new call adds it here first, in the same
change.

## Conventions

- **Names.** A call is named after the State 5 public operation it reaches
  (`50_public_apis.md`, without the module prefix); its arguments are the
  operation's Inputs, named and shaped as the State 6 models
  (`60_model_closure_*.json`) — a model is passed as a dict of its fields, an
  enum as its value string.
- **Results.** A call returns the operation's output model; tests read its
  fields by name. An enum field may come back as an enum or its value string:
  tests compare `getattr(x, "value", x)`.
- **Refusals.** A refusal raises; the test reads its code (State 5, "Closed
  set of refusal codes") as `exc.code` through `pytest.raises`.
- **Store.** Each test gets a fresh, empty kernel store.
- **Actor.** The fixture acts as the actor the MCP surface would determine
  (State 5 catalogue): an author agent for `issue_contract_version`, the owner
  for owner-only operations; a test that is about the actor passes `actor=`
  explicitly.
- **What the fixture fills in.** Only what the tested decision does not depend
  on, and each such default is named below.

## Calls

| call | operation | defaults the fixture supplies |
|---|---|---|
| `issue_contract_version(slot_id, purpose, inputs, outputs)` → `contract_version_id` | `functions.issue_contract_version` | resource bounds within the installation's ceilings (A02 rule 2 refuses omitted ones) |
| `compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges, constants)` → ComposedFlowVersion | `flows.compose_flow_version` | — |
| `prove_flow_version(flow_version_id)` → ProofResult (M17) | `flows.prove_flow_version` | — |

## Places the surface cannot reach yet

A Required test that cannot be stated through the calls above, and needs a
capability rather than a call (a stub service, a kernel restart, a process
observer), is listed here with its witness and the capability it needs. It
is not written around.

| witness | capability needed |
|---|---|
