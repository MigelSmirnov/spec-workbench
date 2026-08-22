# Room Planner — State 0: Product Boundary

> Status: working draft.
>
> This document records product-level decisions only. Concrete modules, Python contracts, HTTP endpoints, persistence schemas, and implementation algorithms are intentionally deferred.

## Product goal

Room Planner is a browser-based renovation planning application centered on the geometry and construction envelope of rooms.

Its responsibility is broader than drawing walls but narrower than estimating a renovation. It must let a user record the existing spatial condition, define renovation changes, describe wall/opening construction and wall-surface finishes, describe floor leveling/fill requirements, and calculate the resulting physical quantities.

The editor must support practical construction work with millimeter-oriented spatial accuracy rather than act as a general-purpose CAD replacement.

Room Planner does **not** calculate prices or labor costs. Those belong to PresuPro.

## Platform object identity

Room Planner does not create renovation objects.

Registry is the platform entry point and creates the object card and canonical object identity.

Room Planner must:

- request the current objects available from Registry;
- open/work against an existing Registry object;
- associate all persisted and published Room Planner results with the Registry `object_id`;
- never create a parallel independent object identity.

## Platform integration boundary

Room Planner participates in the shared platform through the living [Platform Router](../../PLATFORM_ROUTER.md) contract.

The Platform Router document is intentionally developed alongside this case study. Integration requirements discovered while designing Room Planner should be added there when they are genuinely shared platform concerns.

Room Planner should not integrate directly with every downstream application.

Instead, it publishes versioned artifacts associated with a Registry object. Downstream applications consume those artifacts through the shared platform boundary.

The exact adapter module, API operations, DTOs, and transport are deferred to later design states.

## Renovation-state responsibility

Room Planner owns both the measured/current spatial state and the intended post-renovation spatial state.

The product must distinguish at least these meanings:

```text
AS-IS / BASELINE
    existing measured condition

RENOVATION INTENT
    what remains, is removed, is modified, or is added

PROPOSED / TO-BE
    resulting condition after applying the renovation intent
```

These meanings are independent from document revisions. A new revision means that the plan changed; demolition/build intent describes the construction meaning of an element.

The original measured condition should be capable of becoming a frozen baseline so that later design changes do not erase what was originally recorded.

The exact representation of baseline, change operations, and proposed geometry is deferred to the model state.

## Primary planning scope

Room Planner owns the editable geometry and construction information needed to describe the room envelope.

Current in-scope capabilities include:

- walls and connected wall geometry;
- rooms derived from spatial boundaries;
- wall height and thickness as construction-relevant facts;
- existing, retained, demolished, modified, and newly proposed wall conditions;
- doors;
- windows;
- existing, removed, modified, closed, and newly created wall openings where required by the renovation;
- construction-oriented dimensions;
- accurate placement in real-world units;
- drywall/gypsum-board partition systems and their physical quantity calculations;
- plaster with user-selected/defined thickness and resulting physical quantity calculations;
- putty quantities derived from applicable surface area;
- paint quantities derived from applicable surface area and required system parameters;
- floor leveling/fill quantities derived from room geometry and required thickness/leveling inputs;
- publication of the resulting plan and quantity outputs.

## Wall surfaces

Wall finishing is inherently side-specific.

A wall may have different treatment on each face because its two sides may belong to different rooms or construction conditions.

Room Planner therefore needs to support the product concept of separately finishable wall faces/surfaces, including correct net surface areas after applicable openings are accounted for.

The exact domain model is deferred to State 1.

## Drywall responsibility

Drywall remains inside Room Planner because it is directly tied to the wall being designed and can be calculated from the same geometry.

Room Planner may calculate physical quantities for a selected drywall construction system, such as:

- boards/sheets;
- studs and tracks/profiles;
- fasteners/screws;
- joint tape and related system consumables;
- insulation or acoustic fill where the selected system includes it;
- other measurable physical components required by the selected construction system.

Room Planner owns the calculation from wall geometry plus construction-system rules to physical quantities.

It does not own material pricing or labor pricing.

## Wall finishes responsibility

Room Planner may calculate physical quantities for wall-surface treatments including:

- plaster;
- putty;
- paint.

The calculation must use the applicable net wall-face area rather than blindly using gross wall dimensions. Doors, windows, and other relevant openings must be reflected according to later-defined product rules.

The user supplies or selects construction intent such as plaster thickness or a finish system. The application derives quantities from geometry and technical parameters.

## Floor responsibility

Room Planner owns floor leveling/fill as part of preparing the room geometry for renovation.

It may calculate required physical volume/quantity from room area and relevant thickness/leveling inputs.

Final floor covering is explicitly outside this product boundary.

A separate Tile/Floor Covering Planner is expected to own concerns such as:

- tile or other finish selection;
- layout;
- patterns;
- cuts;
- joints;
- finish-specific wastage;
- finish-material quantities.

How floor survey/level measurements enter Room Planner remains an open product question.

## Doors and windows

Doors and windows belong to Room Planner because they are spatial wall openings and directly affect:

- wall geometry;
- usable openings;
- demolition/proposed state;
- wall-face areas;
- drywall and finish quantity calculations.

They must not be treated merely as decorative SVG objects placed over a wall.

The exact opening model and catalog relationship are deferred to later states.

## Quantity responsibility

Room Planner calculates **physical quantities and volumes only** for the construction scope it owns.

Examples include:

- m² of board or finish surface;
- linear meters of profiles;
- pieces of fasteners or structural components;
- kg of mortar/compound where the technical catalog defines consumption by mass;
- m³ of plaster or floor fill where volume is the appropriate physical output.

Room Planner does not calculate:

- material prices;
- labor prices;
- project cost;
- commercial discounts;
- supplier pricing.

Those concerns belong to PresuPro.

Whether packaging conversion and commercial rounding (for example kg to whole bags) belongs to Room Planner, Construction Catalog, or PresuPro remains unresolved and must not be assumed yet.

## Construction Catalog dependency

Technical consumption constants and construction-system parameters must not be hard-coded as arbitrary application constants.

Room Planner depends on a shared, versioned platform concept provisionally named **Construction Catalog**.

The Construction Catalog supplies technical facts such as:

- material consumption rates;
- system layer/component definitions;
- profile/stud spacing rules;
- fastener spacing or consumption rules;
- technical thickness/density parameters where needed;
- other measurable technical parameters required for deterministic quantity calculations.

The catalog owns the technical parameter values. Room Planner owns the domain calculation that applies those values to room/wall geometry.

For example, the catalog may define a mortar consumption rate in normalized physical units, while Room Planner applies that rate to net surface area and selected thickness.

The exact catalog schema, API, ownership service, and persistence model are deferred. Shared access requirements are tracked in [PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md).

## Version reproducibility

Quantity results must be reproducible.

A published quantity result must eventually retain enough provenance to identify both:

- the Room Planner plan revision from which it was calculated;
- the Construction Catalog revision/version whose technical parameters were used.

Changing a catalog value in the future must not silently change the meaning of an already published historical result.

The exact provenance model is deferred to later states.

## Primary outputs

Two distinct output responsibilities have emerged.

### `room_plan`

`room_plan` is the versioned domain artifact containing the Room Planner spatial/construction intent required by downstream planners and other platform applications.

Its exact schema is deferred to State 1.

### `room_takeoff`

`room_takeoff` is the provisional name for the versioned physical-quantity output derived from a `room_plan` using an identified Construction Catalog revision.

It is intended to give PresuPro and other consumers quantities without requiring them to duplicate Room Planner geometry or construction calculations.

A takeoff item should eventually retain enough provenance to identify the source plan and source elements that produced the quantity, but the exact schema is deferred.

`room_plan` and `room_takeoff` are outputs of the same application boundary; introducing a second artifact does not imply a second backend service.

## Relationship to PresuPro

PresuPro is the estimating application.

Room Planner provides physical quantities for its owned construction scope. PresuPro owns pricing, labor/work calculation, and estimate composition.

PresuPro should consume published Room Planner artifacts through the shared platform boundary rather than through a private Room Planner-to-PresuPro API.

PresuPro should not be required to reverse-engineer Room Planner geometry in order to reproduce drywall, plaster, putty, paint, or floor-fill quantity logic.

## Relationship to downstream planners

Room Planner is an upstream spatial source for specialized planners that own other renovation domains.

Current expected examples include:

- Tile/Floor Covering Planner;
- electrical planning;
- plumbing planning;
- other renovation domains discovered later.

A specialized planner may consume Room Planner geometry/surfaces without transferring ownership of its business rules into Room Planner.

Room Planner may later visualize data from those systems as overlays without becoming the owner of their business rules.

## Out of scope

Current explicit exclusions include:

- creation of Registry objects;
- pricing and estimating;
- labor/work pricing or work-item composition;
- tile/floor-covering layout and finish-specific calculations;
- electrical engineering rules;
- plumbing engineering rules;
- client-cabinet behavior;
- general-purpose CAD features that are not required for renovation planning.

## Precision constraint

The product is intended for real renovation work and must support millimeter-oriented spatial accuracy.

Screen pixels are not the domain coordinate system. Exact representation and interaction rules will be designed in later states.

## Frontend/backend constraint

The interactive Room Planner editor is expected to run in the browser.

The current AI Code Factory generates Python backend code only. This is a platform implementation constraint to keep in mind during later architecture work, but it does not change the product boundary.

The browser editor and generated Python backend must therefore meet through explicit contracts rather than assuming that the Factory generates the frontend editor.

## Observable user outcomes discovered so far

A user can select an existing renovation object and work on its room/wall plan.

The user can record or edit an accurate baseline, define which spatial elements remain/remove/change/add, and see the resulting proposed room geometry.

The user can define wall construction and selected wall/floor preparation systems within Room Planner scope and obtain reproducible physical quantities from them.

The plan and quantity results can be saved, revised, published, and consumed by other platform applications.

Changes to a published plan should result in a new identifiable revision rather than silently replacing the provenance of downstream work.

## Unresolved product questions

- Which wall/opening editing operations are mandatory for the first usable release?
- What is the exact lifecycle for creating, correcting, and freezing the as-is baseline?
- Can a frozen baseline be corrected, and if so how is the correction distinguished from renovation intent?
- Does the first release support only one active proposed variant, or multiple alternative design variants?
- How are floor level/survey measurements acquired or imported?
- Which construction systems/material families are required in the initial Construction Catalog?
- Does Room Planner expose editable construction-system templates, catalog-selected fixed systems, or both?
- Who owns packaging conversion and whole-package rounding?
- Does Room Planner itself own drawing/PDF/SVG export, or does a separate renderer/exporter create those artifacts?
- What parts of a room plan may be exposed directly to the client cabinet?
- What collaboration, locking, revision, and approval behavior is required?

## Cross-document rule

Any shared integration requirement discovered while progressing through later Room Planner design states must be evaluated against [PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md).

If it is a platform-wide exchange concern, update the Platform Router document rather than inventing a Room Planner-specific platform protocol.
