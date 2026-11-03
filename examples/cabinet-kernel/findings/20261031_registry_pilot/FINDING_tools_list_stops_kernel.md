# Finding: `tools/list` answers `internal_error` and stops the Kernel

Observed on a local instance of the promoted Kernel tree:
- code-factory `projects/cabinet_kernel/cabinet_kernel` at `034b50c`;
- Python 3.12, pydantic 2.13.5, bubblewrap 0.9.0.

It was not checked on the owner's running Kernel. Its deploy may differ.

## What happens

The MCP method `tools/list` is sent by an authenticated caller. Any agent
token is enough; the author right is not needed. The Kernel then:

1. answers JSON-RPC `-32603 internal_error` with an empty reason;
2. exits with status 1, writing nothing to its stderr. `serve_kernel` sets
   `stop` on any exception that leaves `answer_request`
   (`surface.py:640–647` at `034b50c`).

Every later request is refused with "connection refused" until someone starts
the Kernel again.

## Cause

`tools/list` publishes the input schema of every catalogue operation with
`_published_schema`. For two operations the schema derivation raises
`StoreInternalError("unsupported request schema annotation")`:

```text
30 catalogue operations; schema fails for 2
   add_trial_case AddTrialCaseRequest StoreInternalError unsupported request schema annotation
   list_records ListRecordsRequest StoreInternalError unsupported request schema annotation
```

That is the output of `finding/repro_tools_list_offline.py`. It imports the
generated `surface` module and calls `_published_schema`, with no network and
no store.

`AddTrialCaseRequest.inputs` is `tuple[RequestPayload, ...]`, and
`RequestPayload` is a discriminated union (`Field(discriminator=...)`). The
spec note `answer_request [FIELD_PROJECTION]` (spec-workbench
`agent/cabinet-kernel`, `80_notes.md:488`) requires it: "a discriminated union
{"anyOf": the schemas of its variants in declared order}". The implementation
does not handle the `Annotated[Union[...], Field(...)]` form. `ListRecordsRequest`
fails the same way.

## Reproduction

| how | result |
|---|---|
| `repro_tools_list_offline.py <code-factory>/projects/cabinet_kernel` | 2 of 30 schemas fail (above) |
| `curl -X POST http://127.0.0.1:8930/mcp -H 'Authorization: Bearer <agent token>' -d '{"jsonrpc":"2.0","id":3,"method":"tools/list"}'` | `{"error":{"code":-32603,"message":"internal_error",…}}`; the process is gone two seconds later |
| the second agent's run (`handover/response.txt`) | it called `tools/list` twice, at about 22:15 and 22:18 UTC; the Kernel stopped both times |

The second agent called `tools/list` because the hand-over instruction
(`handover/instruction.md`) told it that this method lists the operations.

## Against the specification

- `initialize`, `ping` and `tools/list` are the entrance's discovery methods
  (`80_notes.md:481, 487–488`; `60_contracts.md:246, 582`).
- That an `internal_error` stops the Kernel is specified (A16 rule 7;
  `60_contracts.md:1547`).
- The defect is that `tools/list` reaches an internal error at all, while the
  note gives a derivation rule for exactly the failing annotation.

## Effect

- A standard MCP client calls `tools/list` when it connects. Any agent that
  connects that way to the owner's Kernel stops it.
- An agent that cannot list the operations cannot learn the shape of
  `list_records` either. The second agent made 12 refused `list_records` calls
  and gave up on reading the execution history.
- The Factory's own client (`tools/kernel_scenarios/kernel_client.py`) calls
  only `tools/call`, so the owner's workplace does not meet the defect in
  normal use.

## Not changed

The Kernel code, its specification and the deployment were not touched.
