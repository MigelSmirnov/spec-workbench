# Room Planner — State 0: Stage Artifacts and Demolition Quantities

> Status: stabilized.
>
> This document is part of State 0 and supplements [00_product.md](00_product.md). It records the final product-boundary decisions discovered during the State 0 closure audit. Domain models, formulas, schemas, rendering implementation, and API contracts remain deferred.

## Purpose of this supplement

The main product-boundary document already establishes semantic separation between Existing, Demolition, and Construction, draft/publish behavior, independent stage publication, platform history, and the Room Planner / PresuPro boundary.

The closure audit identified two product-level decisions that must be explicit before State 1:

1. how Room Planner treats demolition quantities when removable geometry is known versus only approximately known;
2. what the user means by an Existing or Demolition **specification**.

## Demolition quantity responsibility

Room Planner owns physical demolition quantities for the spatial/construction scope that Room Planner itself owns.

Where the removable geometry is known from the Room Planner model, the application should derive the physical quantity from that geometry rather than require the user to re-enter the same measurements manually.

For example, when the user marks an existing wall for demolition, the known wall geometry may be used to derive the applicable demolition length, area, and/or volume required by later quantity rules.

Some demolition geometry cannot be known reliably from the plan alone. Existing screed, plaster build-up, fills, hidden layers, and similar construction may have a removal depth or thickness that is uncertain until work is opened.

In those cases Room Planner must allow the renovation professional to provide an explicit assumed demolition depth/thickness or equivalent physical input. The application then calculates the resulting physical quantity from the known spatial extent plus that user-supplied assumption.

A user may deliberately choose a conservative assumed value to include practical reserve. At State 0 this does not require a separate automatic reserve/contingency engine; the important product capability is that the assumption is explicit rather than silently invented by Room Planner.

Room Planner MUST NOT fabricate an unknown demolition depth or present an inferred value as measured fact merely to complete a takeoff.

Published/reproducible demolition quantities must retain enough meaning to remain attributable to the geometry and explicit assumptions on which they were calculated. The exact fields and provenance representation are deferred to later states.

Room Planner still does not own demolition pricing, labor costing, work-item composition, waste logistics, container planning, haulage, or other commercial/operational estimating concerns. Those belong to PresuPro or another later-defined owner where appropriate.

## Stage specification artifacts

In Room Planner, **specification** is an artifact produced from an accepted stage result; it is not merely an editor summary panel and it is not a fourth editable planning meaning.

Two such specification responsibilities are now explicit in the initial product boundary.

### Existing specification

An Existing specification is a lightweight artifact representing an accepted measurement / Existing result.

Its purpose is to make the measured state easy to review and consume without replacing the underlying structured Room Planner data.

At product level it is expected to contain or reference at least:

- a simple visual representation of the measured plan;
- a structured list of the relevant measured facts and quantities for that publication;
- provenance to the exact Existing publication/source from which it was produced.

### Demolition specification

A Demolition specification is a separate lightweight artifact representing an accepted Demolition result.

At product level it is expected to contain or reference at least:

- a simple visual representation of the demolition plan;
- a structured list of demolition scope and physical quantities, including quantities based on explicit user assumptions where applicable;
- provenance to the exact Demolition publication and its Existing basis.

The Existing specification and Demolition specification are separate historical artifacts because measurement and demolition can become ready and be published at different times.

## Specification generation must remain simple

These stage specifications do not require a heavy document-generation subsystem, heuristic report writer, or AI-generated narrative.

The authoritative source remains Room Planner's structured domain result. The specification is a simple, reproducible presentation artifact built from that source: conceptually **an image plus a structured list**.

The product must not require semantic guessing, free-form prose generation, or complex layout inference in order to produce a valid stage specification.

Exact image format, list schema, visual styling, pagination, PDF generation, and rendering ownership are deferred. A future renderer may create richer documents, but rich rendering is not required for the basic Existing/Demolition specification responsibility.

This decision does not make production CAD/DXF/PDF/SVG drawing generation part of Room Planner's initial authoritative editing boundary.

## Construction publication remains separate

Construction remains independently publishable as established in [00_product.md](00_product.md).

This supplement does not yet require Construction to have the same lightweight specification presentation artifact as Existing and Demolition. If later product work discovers that requirement, it must be added explicitly rather than inferred from naming symmetry.

## Relationship to `room_plan` and `room_takeoff`

The Existing and Demolition specification responsibilities do not replace the provisional `room_plan` and `room_takeoff` platform families described in [00_product.md](00_product.md).

`room_plan` remains the provisional structured Room Planner domain-result family and `room_takeoff` remains the provisional physical-quantity result family.

The specification artifacts are lightweight stage-facing representations derived from exact accepted/published Room Planner data. Their final artifact type names and whether their image/list payload is packaged together or by reference are contract decisions for later states.

## Relationship to PresuPro

PresuPro may consume Room Planner physical quantities through the platform boundary, but it does not need to reverse-engineer the visual specification artifact to recover quantities.

The structured Room Planner data/takeoff remains the machine-oriented source for estimating integration. The lightweight specification exists for review/history/communication and may expose the same relevant quantities in a human-readable list.

Pricing, labor, package conversion, commercial rounding, and estimate composition remain PresuPro responsibilities.

## Relationship to client history

The Existing and Demolition specifications are suitable candidates for the renovation-object history shown by the client cabinet because they are lightweight stage artifacts tied to exact immutable publications.

Room Planner does not own client-cabinet presentation, authorization, or redaction. The cabinet must obtain any allowed artifact through the shared platform boundary rather than Room Planner private working storage.

A later specification artifact must not rewrite or visually replace an earlier historical publication in a way that destroys provenance.

## Platform Router impact

No new Platform Hub mechanism is required by this supplement beyond the capabilities already recorded in [PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md): versioned artifact publication, immutable publication history, artifact payload/reference storage, provenance/basis links, and downstream/client-history discovery.

The new Room Planner requirement to publish lightweight Existing and Demolition specification artifacts is application-specific output discovery. Their final artifact contract names, schemas, and capability-manifest entries must be added to the Platform Router contract registry work when the corresponding later design state defines them.

The Platform Router must not become the owner of specification rendering or demolition calculations.

## State 0 closure result

After this audit, the remaining open questions in [00_product.md](00_product.md) are intentionally deferred design questions rather than hidden product-boundary gaps.

The State 0 boundary is sufficiently stabilized to proceed to State 1 — Domain Models, with the expectation that later states may return here if they expose a genuinely missing product decision.
