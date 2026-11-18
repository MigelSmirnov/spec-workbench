# Source of this case

Portal Deliverer is authored from a running prototype. The prototype is evidence for the
design states; it is not the product code, which the Factory generates from the accepted
specification.

| What | Where |
|---|---|
| Prototype | Factory repository, `prototypes/portal_deliverer/` |
| Layer journal | `prototypes/portal_deliverer/EXPERIMENT.md` |
| Unit tests | `python3 -m pytest -q prototypes/portal_deliverer` |
| Run against a real Client Portal | `python3 prototypes/portal_deliverer/e2e_local_portal.py` |
| Declared surface | `platform/manifest/portal_deliverer.json` |
| Origin of the need | case `client-portal`, `open_questions.md`, Q12 and Q21 |

As of 2026-11-18 the prototype is not committed to the Factory repository, so these paths
exist only in the owner's working copy.
