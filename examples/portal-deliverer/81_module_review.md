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

## Re-review of `source_folder` (2026-11-21)

Route B on accepted spec `e44c34ef` rejected the generated `source_folder`: the Factory's stub gate takes a
contract whose whole body is one unconditional `raise` for a placeholder, and the note of `_unlisted_folder`
asked for exactly that body. The helper now returns the `DelivererError` with `FOLDER_UNAVAILABLE` and
`_source_files` raises it from the `OSError`, the shape of `delivery_store._state_unavailable`; A1 is
unchanged. State 7 round 7 on the new text was clear. Packet review: `None`, a raise, or another refusal code
each contradicts the `_unlisted_folder` note, and a walk failure that is not raised contradicts
`_source_files`. PASS; the ledger holds the new slice hash.

## Re-review after A9 rule 3 (2026-11-21)

Route B on accepted spec `3895f883` rejected `source_folder` again for `getattr(os, 'O_DIRECTORY', 0)` and
`getattr(os, 'O_NONBLOCK', 0)`: no decision named the host, so the generator guarded the flags. A9 rule 3 now
names Linux, no version named, as cabinet-kernel A20 rule 3. The nine notes that open a file or folder in
`source_folder`, `delivery_store` and `deliverer_service` say which flags each opening uses, in prose
(SPEC_STANDARD 2 forbids dotted names in a note), used unconditionally and never tested for. Rounds: State 2
81, State 3 52, State 4 36, State 5 49, State 7 8 and 9; all closed. Packet review of the three modules:
a probed or guarded flag, or an opening that follows a link the note forbids, contradicts its note. PASS;
the ledger holds the new slice hashes.

Route B on `7c6d11f4` then generated 11 of 12 modules and rejected `deliverer_service` for
`getattr(signal.Signals, name)`: `STOP_SIGNALS` holds signal names and no note said that each is the OS signal
of that name. The `run_service` note now says so, and that every handler is installed unconditionally, never
tested for (State 7 rounds 10 and 11). `deliverer_service` reviewed again, PASS.

## Open for the Workbench tools

The packet of `runtime_settings` does not carry `config.runtime_environment_variables`, the 6.11 table the
module is emitted from; a reviewer of the packet alone cannot see normalisation or requiredness.
