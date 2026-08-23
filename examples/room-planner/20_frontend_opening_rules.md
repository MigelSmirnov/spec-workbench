# Room Planner — State 2: Frontend Opening Projection Rules

> Status: accepted State 2 refinement.
>
> This document supplements [20_rules.md](20_rules.md) with rules exposed by the
> shared browser/editor architecture. It does not add new domain models; the
> canonical opening lifecycle remains defined by the stabilized State 1
> documents.

## 1. Domain semantics precede renderer choice

1. An opening aperture, an installed opening element, and its rendered symbol are
   three distinct meanings.
2. Browser scene objects, Konva nodes, SVG assets, symbol ids, and palette choices
   are never canonical Room Planner opening state.
3. `ExistingOpening` / Construction opening-result geometry remains authoritative
   for aperture dimensions and wall attachment.
4. `ExistingOpeningElement` remains authoritative for whether the modeled
   Existing door/window element exists.
5. Demolition/Construction lifecycle meaning is determined by Room Planner
   intents, never by visual appearance.

## 2. Symbol-semantic rule

1. The renderer may deterministically choose a neutral symbol from explicit
   canonical semantics such as opening/element kind.
2. A symbol variant MUST NOT introduce a physical fact absent from the domain.
3. In particular, hinge side, swing direction, handing, sash behavior, and
   similar facts MUST NOT be inferred from an SVG asset name or palette item.
4. If one of those facts later becomes planning-significant, it requires an
   earlier State 0/1 product/model decision before the renderer may treat it as
   authoritative.
5. Until such a fact exists, the visual representation must remain neutral enough
   not to imply an accepted engineering choice.

## 3. Aperture projection rule

1. Aperture world placement is derived from the canonical host wall plus its
   wall-relative profile.
2. Installed-element placement is derived from its referenced aperture.
3. Host-wall edits reproject dependent aperture/element scene geometry; stale
   viewport/Canvas coordinates are never preserved as domain facts.
4. Hit-test geometry and selection outlines are derived frontend data.
5. Semantic references, not render coordinates, are used to identify the
   aperture and installed element.

## 4. Preview/commit rule

1. Dragging/resizing an aperture may create a transient candidate profile in the
   browser.
2. Snapping and geometry helpers may modify that candidate during preview.
3. The candidate does not mutate canonical working state until a confirmed host
   planner command applies it.
4. The generic building/editor layer may propose geometry but MUST NOT decide
   whether confirmation means Existing correction, Construction create,
   Construction alter, Construction close, or a Demolition cut.
5. Room Planner stage semantics remain owned by Room Planner application/domain
   behavior.

## 5. Frontend Editor impact

These rules are shared with the architecture refinement in
[FRONTEND_EDITOR_OPENINGS.md](../../FRONTEND_EDITOR_OPENINGS.md).

They confirm rather than reverse the stabilized State 1 opening lifecycle. The
frontend architecture exposed an outdated simplification in the older generic
`FRONTEND_EDITOR.md` opening sketch; the Room Planner domain model does not need
revision for that reason.