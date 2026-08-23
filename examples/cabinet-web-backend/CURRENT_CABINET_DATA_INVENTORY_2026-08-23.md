# Current Cabinet_web data inventory

Date: 2026-08-23
Source: `MigelSmirnov/Cabinet_web/main`
Commit: `d3fac8e5d2b85c12904cba24060717b84e2757c2`

## Purpose

This is State-0 evidence for the product information that `Cabinet_web`
already owns. It records types and ownership without copying personal Card
content into the Workbench case.

## Runtime Card inventory

| Stored kind | Runtime instances | Accepted meaning |
| --- | ---: | --- |
| Provider Card | 2 | A person, organisation, or not-yet-classified provider that offers working services. Drivers, carriers, workers, shops, and similar resources are represented through Provider Card facts rather than separate Card types. |
| Client Card | 1 | Client identity, contacts, contact people, and stable links to projects. |
| Project Card | 1 | One job/object with client linkage, scope, financial facts, accepted estimate, procurement, shopping-list references, sources, and derived analytics inputs. |
| Invoice Card V1 | 1 | One confirmed supplier invoice with factual lines, totals, payment evidence, source identity, object context, and provenance. |

## Existing related artifacts

- one project shopping-list JSON artifact;
- accepted estimate data embedded in the current Project Card;
- procurement estimate items and actual-purchase structures in the Project
  Card format;
- project/invoice link schema and analytics behavior, with no committed runtime
  link instance found in the reviewed tree;
- generated provider and project Web projections.

Generated `web/catalog.json` and `web/projects.json` are rebuildable views and
are not independent sources of truth.

## Named but not yet implemented Card concepts

The domain documents name Contact Card, Material List Card, Document Card,
Work Object, Artifact, and Relationship concepts, but several remain explicitly
undefined and have no accepted standalone runtime representation in the
reviewed repository.

They are not included merely because their names appear in product discovery.
Adding one requires a later explicit product decision and its own model and
ownership closure.

## State-0 consequence

The Cabinet Web Backend product boundary covers all currently implemented
Cabinet-owned information:

- Provider Cards;
- Client Cards;
- Project Cards and their existing owned project data;
- Invoice Card V1;
- existing project shopping-list artifacts;
- accepted explicit cross-record artifacts when runtime instances are created.

Drivers and workers are not separate backend aggregates unless a later product
decision changes the Provider Card model.

Synchronization must remain type-aware. This inventory does not authorize a
generic Card payload, silent projection loss, or treating one Card type's
revision/source rules as automatically valid for every other type.
