# Room Planner case study

Working branch: `agent/room-planner`

## Shared platform contract

Room Planner uses the repository-level [Platform Router](../../PLATFORM_ROUTER.md) as its shared integration boundary.

The Platform Router is a living contract. Shared API requirements discovered during Room Planner design should be recorded there and then carried through the Room Planner design states as an external adapter dependency.

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

Later state documents should link back to the Platform Router whenever they introduce or refine a shared platform interaction.
