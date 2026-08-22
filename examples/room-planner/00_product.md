# Room Planner — State 0: Product Boundary

> Status: stabilized.
>
> This document records product-level decisions only. Concrete modules, Python contracts, HTTP endpoints, persistence schemas, algorithms, and detailed domain models are intentionally deferred.

## Product goal

Room Planner is a browser-based renovation planning application centered on the geometry and construction envelope of rooms.

Its responsibility is broader than drawing walls but narrower than estimating a renovation. It must let a user record the existing spatial condition, describe demolition, define new construction and finishes, calculate physical quantities, and publish versioned results for downstream platform applications.

The editor must support practical construction work with millimeter-oriented spatial accuracy rather than act as a general-purpose CAD replacement.

Room Planner does **not** calculate prices or labor costs. Those belong to PresuPro.

## Primary actor

The primary Room Planner actor in the initial product is a renovation professional who records measured conditions, prepares demolition and construction intent, reviews physical quantities, and publishes accepted planning results.

A client may influence design decisions and choose between historical revisions presented by the renovation professional, but the initial Room Planner scope does not require a client to be a direct editing actor.

Client-cabinet behavior remains outside the Room Planner product boundary.

## Primary inputs

Room Planner receives or records the following product-level inputs:

- Registry object identity and available object context;
- measured existing spatial geometry and observed conditions;
- demolition intent against the existing condition;
- construction intent for new/changed geometry and Room Planner-owned construction/finish systems;
- thickness, level, finish, and other user-supplied planning parameters required by the owned calculations;
- versioned Construction Catalog technical data required for deterministic quantity calculations.

The exact DTOs, acquisition workflows, import formats, validation structures, and editor interaction details are deferred.

## Persistent product state

Room Planner must preserve unfinished working state so work can continue across sessions.

It must also preserve identifiable historical published revisions of planning results and quantity outputs so downstream provenance remains reproducible.

The exact storage model, draft persistence representation, revision tables, and retention implementation are deferred.

## Platform object identity

Room Planner does not create renovation objects.

Registry is the platform entry point and creates the object card and canonical object identity.

Room Planner must:

- request the current objects available from Registry;
- open/work against an existing Registry object;
- associate all persisted and published Room Planner results with the Registry `object_id`;
- never create a parallel independent object identity.

## Object-level planning container and spatial levels

One Registry object maps to one Room Planner planning container.

A Registry object may represent a renovation object with one or multiple spatial levels/floors. Room Planner must be able to plan all relevant levels inside that same object-level container rather than creating parallel Registry objects merely to represent floors.

Each level participates in the same semantic separation established by Room Planner:

```text
Registry object
│
└── Room Planner container
    │
    ├── Level 0
    │   ├── Existing
    │   ├── Demolition
    │   └── Construction
    │
    ├── Level 1
    │   ├── Existing
    │   ├── Demolition
    │   └── Construction
    │
    └── ...
```

If Registry cannot currently express the level/floor facts required to describe a multi-level renovation object, that is a Registry/platform-contract gap to resolve; Room Planner must not compensate by inventing independent object identities.

Published Room Planner results should represent a coherent object-level revision across the included levels. Downstream consumers should not be required to reconstruct one renovation object by assembling independently published floor fragments.

The exact internal level model, level identity, per-level editing/revision mechanics, and Registry projection are deferred to later design states.

## Platform integration boundary

Room Planner participates in the shared platform through the living [Platform Router](../../PLATFORM_ROUTER.md) contract.

Room Planner should not integrate directly with every downstream application. It publishes versioned artifacts associated with a Registry object, and downstream applications consume those artifacts through the shared platform boundary.

The exact adapter module, API operations, DTOs, and transport are deferred to later design states.

## Room Planner is a container of semantically isolated plans

Room Planner is one application, but it contains several plans with deliberately different meanings.

The plans share the same spatial context and may be overlaid in one editor, but they MUST NOT become one undifferentiated drawing.

The product currently distinguishes three primary editable planning meanings:

```text
ROOM PLANNER
│
├── EXISTING PLAN
│   what physically exists on the object
│
├── DEMOLITION PLAN
│   what must be removed from the existing condition
│
└── CONSTRUCTION PLAN
    what must be created, changed, prepared, or finished
```

A fourth user-visible view may be derived:

```text
PROPOSED / TO-BE
=
EXISTING
- DEMOLITION
+ CONSTRUCTION
```

`PROPOSED` is currently considered a resulting view of the isolated source plans, not an independent place where reality is silently overwritten.

The exact persisted representation is deferred to later states.

## Semantic isolation is mandatory

The boundaries between Existing, Demolition, and Construction are product semantics, not merely visual layers or colors.

### Existing Plan

The Existing Plan answers only:

> What is physically present and measured on the renovation object?

It may contain measured spatial facts such as walls, rooms, doors, windows, openings, dimensions, and other observed conditions that are accepted into Room Planner scope.

Construction intent MUST NOT leak into the Existing Plan.

For example, a future drywall partition, project plaster system, project paint system, or project floor fill must not appear in the Existing Plan merely because it is drawn on the same canvas.

The original measured condition must be capable of becoming a preserved/frozen baseline so that later renovation design does not erase what was originally recorded.

The detailed freeze/correction lifecycle is deferred.

### Demolition Plan

The Demolition Plan answers only:

> What must be removed, opened, stripped, or otherwise demolished from the existing condition?

Demolition is a distinct renovation meaning and a distinct kind of downstream work.

The Demolition Plan may refer to existing elements or existing finishes that are to be removed, but it MUST NOT create new construction.

Examples include removing an existing wall, removing a door or window, opening or enlarging an existing opening, removing an existing finish, or other demolition actions introduced later within Room Planner scope.

### Construction Plan

The Construction Plan answers only:

> What must be built, added, changed, prepared, or finished as part of the renovation?

This is where new wall systems, new/changed openings, drywall systems, plaster, putty, paint, and floor leveling/fill belong.

A construction element appearing here means work is intended. It must never be confused with an observed Existing condition.

## Revision semantics are separate from renovation-stage semantics

Versioning is mandatory.

`Existing`, `Demolition`, and `Construction` describe the construction meaning of data.

A revision describes that the relevant plan/document result changed over time.

These are separate axes and must not be conflated.

Published historical plans and quantity outputs must remain identifiable and must not silently change when a later plan revision or later Construction Catalog revision exists.

The exact revision model, branching policy, locking, and rollback behavior are deferred to later states.

## One active Construction proposal in the initial product

The initial Room Planner product supports one active Construction proposal for a Registry object rather than parallel alternative A/B/C design variants.

Alternative design exploration is represented through the ordinary revision history of the plan. The product does not require a separate variant/branch concept in its first scope.

This decision keeps publication, quantity calculation, downstream consumption, and provenance centered on one current Construction intent plus identifiable historical revisions.

A future product requirement may introduce explicit parallel alternatives, but later architecture must not assume that capability exists today.

## Non-destructive revision behavior

Room Planner must avoid ordinary user actions that irreversibly destroy published planning history or invalidate downstream provenance.

Working drafts that have never been published may be discarded as part of normal editing workflow.

Once a result has been published, normal product behavior must preserve that historical revision. A published revision may later cease to be current, be superseded, or be archived, but it must not be silently hard-deleted or rewritten in place.

Returning to an earlier design means restoring/copying that historical state into a new current revision rather than rewinding history as though intervening revisions never existed.

This supports practical comparison workflows without introducing parallel design variants. For example, a user may publish one revision based on drywall construction, publish a later revision based on plaster, then restore the earlier drywall state as a new revision if the client chooses it.

The exact statuses, retention policy, administrative recovery mechanisms, and authorization rules are deferred to later design states.

## Primary planning scope

Current in-scope capabilities include:

- walls and connected wall geometry;
- rooms derived from spatial boundaries;
- wall height and thickness as construction-relevant facts;
- doors and windows as real wall openings rather than decorative SVG overlays;
- construction-oriented dimensions;
- accurate placement in real-world units;
- demolition intent for relevant existing walls/openings/finishes;
- new/changed wall and opening construction;
- drywall/gypsum-board partition systems and their physical quantity calculations;
- plaster with selected/defined thickness and resulting physical quantity calculations;
- putty quantities derived from applicable surface area;
- paint quantities derived from applicable surface area and required system parameters;
- floor leveling/fill quantities derived from room geometry and required thickness/leveling inputs;
- publication of versioned plan and quantity outputs.

## Wall surfaces

Wall finishing is inherently side-specific.

A wall may have different treatment on each face because its two sides may belong to different rooms or construction conditions.

Room Planner therefore needs the product concept of separately finishable wall faces/surfaces, including net surface areas after applicable openings are accounted for.

The exact domain model is deferred to State 1.

## Drywall responsibility

Drywall remains inside Room Planner because it is directly tied to the wall being designed and can be calculated from the same construction geometry.

Room Planner may calculate physical quantities for a selected drywall construction system, such as:

- boards/sheets;
- studs and tracks/profiles;
- fasteners/screws;
- joint tape and related system consumables;
- insulation or acoustic fill where the selected system includes it;
- other measurable physical components required by the selected construction system.

Room Planner owns the calculation from construction geometry plus construction-system rules to physical quantities.

Drywall construction intent belongs in the Construction Plan and MUST NOT leak into the Existing Plan.

Room Planner does not own material pricing or labor pricing.

## Wall finishes responsibility

Room Planner may calculate physical quantities for wall-surface treatments including:

- plaster;
- putty;
- paint.

The calculation must use the applicable net wall-face area rather than blindly using gross wall dimensions. Doors, windows, and other relevant openings must be reflected according to later-defined product rules.

The user supplies or selects construction intent such as plaster thickness or a finish system. The application derives quantities from geometry and technical parameters.

Project finishes belong to the Construction Plan; existing observed finishes and demolition of existing finishes are separate meanings.

## Floor responsibility

Room Planner owns floor leveling/fill as part of preparing room geometry for renovation.

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

- existing geometry;
- demolition intent;
- construction intent;
- usable openings;
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
- supplier pricing;
- purchasable package counts or commercial whole-package rounding.

Those commercial concerns belong to PresuPro.

Room Planner publishes physical quantities in their appropriate engineering units. When downstream estimating or procurement needs conversion from a physical quantity to purchasable packages, PresuPro owns that conversion and whole-package rounding. Construction Catalog may supply technical/package facts required by that calculation, but it does not own the commercial rounding decision.

Demolition and Construction must remain distinguishable in quantity outputs because they represent different kinds of downstream work.

## Construction Catalog dependency

Technical consumption constants and construction-system parameters must not be hard-coded as arbitrary application constants.

Room Planner depends on a shared, versioned platform concept provisionally named **Construction Catalog**.

The Construction Catalog supplies technical facts such as:

- material consumption rates;
- construction-system component definitions;
- layer definitions;
- profile/stud spacing rules;
- fastener spacing or consumption rules;
- technical thickness/density parameters where needed;
- other measurable technical parameters required for deterministic quantity calculations.

The catalog owns the technical parameter values. Room Planner owns the domain calculation that applies those values to Room Planner geometry and construction intent.

The exact catalog schema, API, ownership service, and persistence model are deferred. Shared access requirements are tracked in [PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md).

## Version reproducibility

Quantity results must be reproducible.

A published quantity result must eventually retain enough provenance to identify at least:

- the relevant Room Planner plan revision(s) from which it was calculated;
- the Construction Catalog revision/version whose technical parameters were used.

Changing a plan or catalog value in the future must not silently change the meaning of an already published historical result.

The exact provenance model is deferred to later states.

## Primary outputs

Two application-level output responsibilities are currently retained as provisional platform artifact families.

### `room_plan`

`room_plan` is the provisional versioned domain artifact for Room Planner.

At State 0 it should be understood as a coherent object-level container/result boundary across all included spatial levels and over the semantically isolated Existing, Demolition, and Construction meanings rather than as one mixed drawing or a set of independently assembled floor fragments.

Whether later contracts expose these plans as one container artifact, several related artifacts, or both is deliberately deferred.

### `room_takeoff`

`room_takeoff` is the provisional versioned physical-quantity output derived from the relevant Room Planner plans using an identified Construction Catalog revision.

It is intended to give PresuPro and other consumers quantities without requiring them to duplicate Room Planner geometry or construction calculations.

Its quantities must preserve the distinction between demolition scope and construction scope where that distinction affects downstream work.

`room_plan` and `room_takeoff` are outputs of the same application boundary; introducing several plan meanings or artifacts does not imply separate backend services.

## Relationship to PresuPro

PresuPro is the estimating application.

Room Planner provides physical quantities for its owned renovation scope. PresuPro owns pricing, labor/work calculation, estimate composition, and conversion of physical quantities into purchasable package counts when that commercial step is required.

PresuPro should consume published Room Planner artifacts through the shared platform boundary rather than through a private Room Planner-to-PresuPro API.

PresuPro should not be required to reverse-engineer Room Planner geometry in order to reproduce drywall, plaster, putty, paint, floor-fill, or demolition quantity logic owned by Room Planner.

## Drawing/export ownership

Production drawing and document export are not owned by the initial Room Planner product boundary.

Room Planner publishes domain planning data. A downstream renderer/exporter may consume a published Room Planner revision and create derived artifacts such as DXF, PDF, SVG, or a versioned `drawing_set` while preserving provenance to the source Room Planner revision.

The future CAD direction is recorded separately in [FUTURE_CAD_EXPORT.md](FUTURE_CAD_EXPORT.md). Exact rendering/export contracts remain deferred.

## Collaboration scope

The initial Room Planner product does not require real-time multi-user collaborative editing of the same working plan.

The product may later introduce collaboration, presence, concurrent editing, or explicit locking if a real workflow requires them. Their absence from the initial scope must not be replaced with speculative collaboration abstractions in State 1.

Authentication, authorization, and ordinary access control are separate concerns and remain to be defined at the appropriate later state.

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
- purchasable package conversion and commercial whole-package rounding;
- tile/floor-covering layout and finish-specific calculations;
- electrical engineering rules;
- plumbing engineering rules;
- production DXF/PDF/SVG drawing generation;
- real-time multi-user collaborative editing in the initial product;
- client-cabinet behavior;
- general-purpose CAD features that are not required for renovation planning.

## Precision constraint

The product is intended for real renovation work and must support millimeter-oriented spatial accuracy.

Screen pixels are not the domain coordinate system. Exact representation and interaction rules will be designed in later states.

## Frontend/backend constraint

The interactive Room Planner editor is expected to run in the browser.

The current AI Code Factory generates Python backend code only. This is a platform implementation constraint to keep in mind during later architecture work, but it does not change the product boundary.

The browser editor and generated Python backend must therefore meet through explicit contracts rather than assuming that the Factory generates the frontend editor.

## Primary user workflow

The primary product workflow is currently:

```text
select Registry object
        ↓
create / continue Existing Plan
        ↓
record Demolition Plan
        ↓
record Construction Plan
        ↓
inspect derived Proposed / To-Be view
        ↓
calculate physical quantities
        ↓
review
        ↓
publish an identifiable version
        ↓
downstream platform consumers
```

More explicitly:

1. The user opens Room Planner and selects an existing renovation object supplied by Registry.
2. The user creates or continues the Existing Plan and records the measured current condition.
3. The Existing Plan remains independent from later demolition and construction work so the original observed state is not overwritten.
4. The user records Demolition work separately against the Existing condition.
5. The user records Construction work separately, including new/changed geometry and the construction/finish systems owned by Room Planner.
6. The user may inspect a Proposed / To-Be result derived from Existing, Demolition, and Construction without turning that derived view into a mixed source of truth.
7. Room Planner calculates physical quantities for the scope it owns using the relevant geometry, construction intent, and applicable Construction Catalog data.
8. The user reviews the resulting plan and quantities.
9. When a result is ready for use outside the user's working session, the user publishes an identifiable version for downstream platform consumers.

The workflow does not need to complete in one session. The product must support saving incomplete work and continuing it later.

## Save and publish are different product actions

Saving working state and publishing a result have different meanings.

**Save / draft** means the user is preserving incomplete or ongoing work for later continuation. Saved working state is not automatically a platform promise that downstream applications should consume it.

**Publish** means the user intentionally exposes a specific identifiable result version for use by other platform applications.

A later edit must not silently mutate the meaning of an already published result; it leads to later working state and eventually another published version.

The exact persistence model, draft state model, approval policy, and revision numbering mechanics are deferred.

## Existing Plan may be published independently

The Existing Plan has useful platform meaning before Demolition and Construction are complete.

Room Planner must therefore allow an accepted Existing result to be publishable independently from later renovation-stage work.

This allows downstream consumers that only need the measured/as-built spatial condition to begin work without waiting for the complete renovation proposal.

Whether Demolition and Construction are also independently published artifacts or published through a later `room_plan` container contract remains deferred to later design states.

## Important failure outcomes

At State 0, the product must make the following important failures observable rather than silently fabricating or publishing a plausible-looking result:

- If the selected Registry object is unavailable or cannot be resolved, Room Planner cannot create or substitute another platform object identity and must not proceed as if the object were valid.
- If geometry or required planning inputs are incomplete or invalid for a requested calculation, Room Planner must not present the resulting quantities as valid completed takeoff data.
- If required Construction Catalog data or the required catalog revision cannot be resolved, Room Planner must not invent technical constants or silently calculate with unrelated defaults.
- If publication fails, the working result remains unpublished/draft from the platform perspective; the product must not report a successful publication.
- If a historical revision has already been published, later editing or recovery failures must not silently mutate that published historical result.

The exact validation rules, error models, retry behavior, HTTP status codes, and user-interface messages are deferred to later design states.

## Observable user outcomes discovered so far

A user can select an existing renovation object and work on its Room Planner container.

The user can create or edit an accurate Existing Plan without mixing it with future construction intent.

The user can preserve unfinished work without publishing it to downstream applications.

The user can publish an accepted Existing result before the complete renovation proposal is finished.

The user can separately describe Demolition work against the existing condition.

The user can separately describe Construction work and finishes.

The user can inspect a resulting Proposed/To-Be view derived from the isolated plan meanings.

The user can obtain reproducible physical quantities for the scope owned by Room Planner.

The plan and quantity results can be saved, revised, published, and consumed by other platform applications.

Changes to a published result must create a new identifiable revision rather than silently replacing the provenance of downstream work.

## Unresolved product questions deferred to later states

The following questions remain intentionally unresolved because they do not block the State 0 product boundary and belong to later design work:

- Which wall/opening editing operations are mandatory for the first usable release?
- What is the exact lifecycle for creating, correcting, and freezing the Existing baseline?
- Can a frozen Existing baseline be corrected, and if so how is that correction distinguished from renovation intent?
- How are floor level/survey measurements acquired or imported?
- Which construction systems/material families are required in the initial Construction Catalog?
- Does Room Planner expose editable construction-system templates, catalog-selected fixed systems, or both?
- What parts of Room Planner results may be exposed directly to the client cabinet?
- At the platform contract level, should Existing, Demolition, and Construction be published as one `room_plan` container artifact, as separate related artifacts, or both?

## Cross-document rule

Any shared integration requirement discovered while progressing through later Room Planner design states must be evaluated against [PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md).

If it is a platform-wide exchange concern, update the Platform Router document rather than inventing a Room Planner-specific platform protocol.
