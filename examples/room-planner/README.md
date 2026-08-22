# Room Planner case study

Working branch: `agent/room-planner`

## Shared platform contract

Room Planner uses the repository-level [Platform Router](../../PLATFORM_ROUTER.md) as its shared integration boundary.

The Platform Router is a living contract. Shared platform requirements discovered during Room Planner design must be recorded there and then carried through the Room Planner design states as an external adapter dependency.

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

## Design states

1. [00 — Product boundary](00_product.md)
2. 10 — Domain models
3. 20 — Rules and invariants
4. 30 — Module responsibilities
5. 40 — System flows
6. 50 — Public APIs
7. 60 — Contracts
8. 70 — Notes
9. Assembly

Later state documents must carry the Platform Router dependency forward even when they do not introduce a new shared interaction.
