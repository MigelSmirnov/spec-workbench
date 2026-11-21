# Stage 8.1 — Portal Deliverer module review (2026-11-21)

Each module was reviewed from its packet
(`python tools/design_module_review.py examples/portal-deliverer --module <name> --slice --json`)
by the method of `tools/MODULE_REVIEW_WORKBENCH.md` and `STAGE_7_1_SEMANTIC_HANDOFF.md`. Three reviewers,
three modules each, judged whether code generated from the packet alone gives the observable behaviour the
accepted decisions require: the strongest different implementation the packet still allows, and placeholder
resistance (None, an empty result, constant success, forwarding, an unconditional exception). The prototype
was not read. The deterministic modules (`models`, `data_provider`, `runtime_settings`, `system_clock`,
`deliverer_router`) were checked against their closures. The ledger is `81_module_review_status.json`; its
hashes are of the slices after the repairs below.

## Findings and where they were closed

Every finding was a State 7 note that did not say what a State 2 decision already decides, except the port
bound, which had no home.

| Module | Finding | Closed by |
|---|---|---|
| `photo_preparation` | AMBIGUITY: the library's own pixel limit at its default, raised or lifted gives `unreadable_image` or `too_many_pixels` for the same oversized header | note `prepare_photo`: the library's limit is switched off; only `MAX_PIXELS` decides (A2 rule 2) |
| `object_connections` | AMBIGUITY: `_subfolder` walked "written segments" where A5 rule 8 refuses a parent segment | note `_subfolder` restates A5 rule 8 |
| `object_connections` | AMBIGUITY: a byte-order mark in the connections file was left open | note `_connections_file`: no byte-order mark |
| `delivery_store` | variation: a per-process lock would not exclude threads (A6 rule 4, INV-12) | note `project_lock`: the per-open-file lock |
| `delivery_store` | variation: the encoding of a read record | notes `read_placement`, `read_mark`: the JSON form of the model, as written |
| `photo_delivery` | variation: the order of `counts` | note `scan_project_photos`: in the order of the `ScanStatus` members |
| `deliverer_service` | hardening: the port bound was prose | A8 `MAX_PORT`; note `load_config` refuses a port above it |

The repairs went through State 7 rounds 4 to 6, State 2 round 80 (A8), State 3 round 51, State 4 round 35
and State 5 round 48; all closed. Assembly 15/15.

## Open for the Workbench tools

The packet of `runtime_settings` does not carry `config.runtime_environment_variables`, the 6.11 table the
module is emitted from; a reviewer of the packet alone cannot see normalisation or requiredness.
