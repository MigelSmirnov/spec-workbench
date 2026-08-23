# Room Planner case study

Working branch: `agent/room-planner`

## Working context

Before working on any numbered Room Planner design state, build the case context pack:

```bash
python tools/context_pack.py \
  --case examples/room-planner \
  --state <current-state>.md
```

The pack automatically includes this README, the current and all earlier numbered Room Planner state documents, and recursively linked local Markdown dependencies. This is the normal way to keep shared contracts and earlier decisions visible while progressing through the case without manually reopening every file.

The source documents remain authoritative. Generated context-pack output is working context, not a new design state and should not replace the linked sources.

## Shared platform contract

Room Planner uses the repository-level [Platform Router](../../PLATFORM_ROUTER.md) as its shared integration boundary.

The Platform Router is a living contract. Shared platform requirements discovered during Room Planner design must be recorded there and then carried through the Room Planner design states as an external adapter dependency.

Because this README is always seeded into the context pack, the Platform Router link is automatically imported into every later Room Planner state context. Later state documents still record their **Platform Router impact** so the effect of each design layer remains explicit and reviewable.

### Platform Router carry-forward invariant

The Platform Router link and the platform requirements discovered from Room Planner MUST NOT disappear as the case study moves to later design states.

Every Room Planner design-state document from State 1 onward must contain an explicit **Platform Router impact** section.

That section must do one of the following:

- identify the platform requirements introduced, refined, or consumed by that state and link them to `../../PLATFORM_ROUTER.md`; or
- explicitly state that the state introduces no new Platform Router requirements while preserving all previously established platform dependencies.

When a Room Planner decision reveals a requirement that is shared across applications, the change is incomplete until:

1. the requirement is recorded or refined in `PLATFORM_ROUTER.md` at the appropriate level of abstraction;
2. the current Room Planner state references the shared requirement rather than inventing a private Room Planner protocol;
3. later Room Planner states preserve the dependency and provenance/publication semantics established by earlier states.

This applies in particular to Registry object identity, Construction Catalog resolution, artifact publication and discovery, immutable publication history, provenance/basis links, stage publication milestones, and client-history availability discovered during State 0.

Concrete HTTP paths, DTOs, and transport details are still deferred until their proper design states.

## Shared frontend/editor contract

Room Planner also uses the repository-level [Frontend Editor](../../FRONTEND_EDITOR.md) as its living browser/editor architecture boundary.

That document accumulates shared frontend knowledge without copying Room Planner domain models into a second source of truth. In particular it records the browser-first delivery boundary, domain-authoritative versus transient editor state, rendering-as-projection, and the expected progression from model completeness to later interaction/API contracts.

Because this README links the Frontend Editor document, the normal case context pack imports it automatically alongside the Platform Router.

For focused frontend work, build the narrower manifest-driven context with:

```bash
python tools/frontend_context.py \
  --manifest examples/room-planner/frontend_context.json
```

The manifest lists exact canonical Markdown headings needed by the Room Planner browser editor. The tool fails if a referenced file or heading disappears, so frontend dependencies cannot silently rot when domain documents are renamed or refined.

The manifest and generated pack are dependency/indexing tools only. Canonical product and domain decisions remain in the numbered Room Planner state documents; shared frontend/editor architecture remains in `FRONTEND_EDITOR.md`.

## Design states

1. **State 0 — Product boundary**
   - [00 — Core product boundary](00_product.md)
   - [00 — Stage artifacts and demolition quantities](00_stage_artifacts.md)
2. **State 1 — Domain models**
   - [10 — Domain models](10_models.md) — working draft
   - [10 — Snapshot identity and Existing correction carry-forward](10_identity_carry_forward.md) — accepted refinement
   - [10 — Typed source and provenance references](10_source_provenance.md) — accepted refinement
   - `frontend_context.json` — machine-readable frontend dependency manifest
3. 20 — Rules and invariants
4. 30 — Module responsibilities
5. 40 — System flows
6. 50 — Public APIs
7. 60 — Contracts
8. 70 — Notes
9. Assembly

State 0 is stabilized across both `00_*.md` documents. State 1 is active and remains a working draft until its explicit model closure questions are resolved. The accepted `10_*` refinements supersede provisional terminology or model shapes in `10_models.md` where stated. `context_pack.py` will carry the stabilized State 0 sources, current State 1 documents, and linked shared architecture boundaries into later work automatically.

Later state documents must carry the Platform Router dependency forward even when they do not introduce a new shared interaction. Frontend-relevant shared requirements should likewise be evaluated against `FRONTEND_EDITOR.md` rather than being duplicated privately in later Room Planner documents.
