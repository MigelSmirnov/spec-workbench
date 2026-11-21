# Portal Deliverer — where the case stands (2026-11-21)

Start with the tools, not with this page: `python tools/authoring.py next portal-deliverer`
(or the MCP `workbench_state`) gives the phase and the whole-case diagnosis. This page holds only
what those tools cannot know.

## State

Accepted spec `78e80ec4` (this branch at `71be860c`) is covered by terminal OTK: code-factory
Route B run `20261121_122018`, audit ok, lineage equivalence proven; the 13 modules are promoted on
Factory `main` (code-factory #239). Every question round and Stage 8.1 is closed.

Run rounds and diagnosis with `SPEC_WORKBENCH_FACTORY_ROOT` set to the main `code_factory`
checkout, which is now on `main`.

## Decisions taken while closing OTK (2026-11-21)

- R0-16 (was OQ-07): the deliverer runs beside the Client Portal on its VPS, reached through the
  Portal's front under its own route and credential. How they are installed belongs to the
  deployment (`projects/portal_deliverer/deploy` in the Factory).
- A9 rule 3: Linux host, no version named; notes name each opening's flags in prose, used
  unconditionally and never tested for (same repair as cabinet-kernel decisions 34 and 36).
- Each witness judges what this service owns. A2's INV-03 and INV-05 no longer assert how the Portal
  serves or shows a photo. A11 stays `external_owner` (30_trace.json): its witness is the calling
  flow's contract; the Factory runs it as a soft check, and it blocks in that flow's verification.
- `_stop_signal(name) -> Signals` is the declared contract that turns a STOP_SIGNALS name into a
  signal (State 7 round 10: a note may not prescribe the lookup).

## Carried to deploy

State 2 round 83 T1, T5, T6, State 3 round 52 T1 and State 4 round 37 T1: route identity, the
`not_checked` conditions and snapshot tests of the A9 check, and placing the service only on a
conforming Linux host belong to the deployment route. `design_questions.py carried
examples/portal-deliverer --to deploy` lists them.

## Next (outside this case)

1. Deploy on the VPS with `projects/portal_deliverer/deploy/release.sh` (owner's action on
   production): nginx `location /deliverer/`, the token file, a confirmed connections file.
2. The calling flow (A11): a cabinet_kernel scenario that binds `photo.scan`, `photo.deliver`,
   `photo.mark_published` (platform/manifest/portal_deliverer.json) and the Portal's `photo.publish`.
   The date check of R0-13 reads the Portal's `photo.list`, a bare array the kernel does not bind
   (cabinet-kernel A09 rule 3), so the agent makes it outside the kernel; neither the kernel nor
   the Portal is changed for it (owner, 2026-11-21).

## Lessons

- A witness helper wrote `exif or Image.Exif()`: an Exif holding only a sub-IFD is falsy, so the date
  and metadata witnesses tested photos without the metadata they meant to give.
- The exporter carries only `test_*.py`; the Factory keeps `RUNTIME_SURFACE.md` and
  `review/SEMANTIC_HANDOFF.md` beside the witnesses by hand.
- An imports `uses` row with basis `code` holds only while generated code lies in the Factory
  checkout, and admission needs that checkout clean; a symbol the emitted code needs goes on the
  module scope with an `author:` basis.
