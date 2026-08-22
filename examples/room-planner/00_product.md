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

## Plan-centric spatial model

Room Planner's authoritative editable drawing is two-dimensional and organized per spatial level/floor.

Walls, rooms, openings, dimensions, boundaries, and their plan relationships are defined in real-world plan coordinates. The drawing is supplemented by construction-relevant vertical parameters such as heights, elevations/levels, thicknesses, and opening heights where those facts are required for renovation planning.

These vertical parameters exist to let Room Planner derive construction-relevant geometry and room specifications from the 2D plan, including floor and ceiling areas, room perimeters, wall lengths, wall-face areas, net surface areas after openings, clear heights, and physical volumes where applicable.

Room Planner must support spatially varying floor and ceiling geometry rather than assuming one floor elevation and one room height for an entire room. Survey and planning may use a two-dimensional measurement grid over the plan. At relevant grid locations the product must be able to retain two independent vertical facts:

- floor elevation relative to a stable project datum/zero;
- local floor-to-ceiling clear height.

From those facts the corresponding ceiling elevation relative to the same datum can be derived. This allows a floor and ceiling to slope together while clear height remains constant, or allows floor and ceiling geometry to vary independently where the measured condition requires it.

The project datum is a measurement reference, not a claim that the physical building is level. Exact datum management, grid density, interpolation, incomplete-grid behavior, and surface reconstruction are deferred to later design states.

The initial product does not require arbitrary free-form 3D solid or mesh modeling. A future 3D representation is allowed, but it must be a derived visualization of the authoritative 2D plan and its vertical parameters rather than an independent source of spatial truth.

The exact coordinate, elevation, grid, surface, and derived-geometry models are deferred to State 1.

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

It may contain measured spatial facts such as walls, rooms, doors, windows, openings, dimensions, floor/ceiling elevations, clear heights, and other observed conditions that are accepted into Room Planner scope.

Construction intent MUST NOT leak into the Existing Plan.

For example, a future drywall partition, project plaster system, project paint system, or project floor fill must not appear in the Existing Plan merely because it is drawn on the same canvas.

The original measured condition must be capable of becoming a preserved/frozen baseline so that later renovation design does not erase what was originally recorded.

The detailed freeze/correction lifecycle is deferred.

### Demolition Plan

The Demolition Plan answers only:

> What must be removed, opened, stripped, or otherwise demolished from the existing condition?

Demolition is a distinct renovation meaning and a distinct kind of downstream work.

The Demolition Plan may refer to existing elements or existing finishes that are to be removed, but it MUST NOT create new construction.

Examples include removing an existing wall, removing a door or window, opening or enlarging an existing opening, removing an existing finish, removing floor layers, removing an existing ceiling system or covering, or other demolition actions introduced later within Room Planner scope.

Where demolition changes a measured floor or ceiling build-up, Room Planner may derive the resulting post-demolition surface/elevation map for review and subsequent Construction planning. That derived result does not turn Demolition into a second Existing source of truth.

### Construction Plan

The Construction Plan answers only:

> What must be built, added, changed, prepared, or finished as part of the renovation?

This is where new wall systems, new/changed openings, drywall systems, plaster, putty, paint, ceiling preparation/finishes, and floor leveling/fill belong.

Construction may define a target floor/ceiling surface or elevation map where the intended work changes those surfaces. The user must be able to inspect the resulting clear heights and physical quantity consequences without Room Planner deciding whether a particular furniture, kitchen, or other downstream design will fit; that design judgment remains with the user or the relevant downstream planner.

A construction element appearing here means work is intended. It must never be confused with an observed Existing condition.

## Revision semantics are separate from renovation-stage semantics

Versioning is mandatory.

`Existing`, `Demolition`, and `Construction` describe the construction meaning of data.

A published revision describes an identifiable result that was intentionally published at a point in time. Ordinary edits and draft saves do not create published revisions.

These are separate axes and must not be conflated.

Published historical plans and quantity outputs must remain identifiable and must not silently change when a later plan revision or later Construction Catalog revision exists.

The exact revision identifiers, statuses, branching representation, locking, and rollback mechanics are deferred to later states.

## Existing corrections and dependent-plan propagation

Existing represents the best-known reconstruction of the renovation object's pre-renovation physical condition rather than merely the measurements that happened to be available at one moment.

A published Existing revision is an immutable historical record, but later discovery of a measurement error, hidden condition, or more accurate observation may justify a corrected Existing working state. Such a correction is made in draft and MUST NOT rewrite an earlier published Existing revision in place. If the corrected result is later published, publication creates a new identifiable Existing revision.

An observation made after renovation work has begun may correct Existing only when it reveals a fact that was already true before the project work, such as a previously hidden substrate, level, dimension, or construction condition. A physical state change caused by demolition or construction work is not retroactively written into Existing merely because it was observed later.

Demolition and Construction intent created against an earlier Existing basis must not silently change meaning when a corrected Existing working state appears. Published dependent revisions remain historically associated with the Existing basis against which they were created.

When an Existing correction affects dependent renovation intent, Room Planner must support carrying the relevant Demolition and Construction intent forward onto the corrected Existing basis as dependent working drafts rather than resetting those plans to empty state.

The product may automatically propagate relationships, geometry, and intent that remain unambiguous after the correction, but automatic propagation is not silent acceptance. Room Planner must expose that dependent plans are affected and must surface unresolved or conflicting consequences for review rather than fabricate a plausible migration.

The user must explicitly confirm the Existing correction with awareness that dependent plans are affected, and must separately accept the propagated Demolition and Construction working result before treating that propagated state as the current working basis. None of these draft actions by itself creates a published revision.

Publication remains a separate product action. If the corrected and propagated working state is published, the newly published result receives new identifiable revision(s), while earlier Existing, Demolition, Construction, and published quantity revisions remain preserved so historical provenance can still be reproduced.

The exact dependency representation, propagation algorithm, conflict model, statuses, and confirmation user interface are deferred to later design states.

## One active Construction proposal in the initial product

The initial Room Planner product supports one active Construction proposal for a Registry object rather than parallel alternative A/B/C design variants.

Alternative design exploration may occur freely in the working draft. Historical published alternatives are represented through ordinary revision history; the product does not require a separate variant/branch concept in its first scope.

This decision keeps publication, quantity calculation, downstream consumption, and provenance centered on one current Construction intent plus identifiable historical published revisions.

A future product requirement may introduce explicit parallel alternatives, but later architecture must not assume that capability exists today.

## Non-destructive revision behavior

Room Planner must avoid ordinary user actions that irreversibly destroy published planning history or invalidate downstream provenance.

Working drafts that have never been published may be discarded as part of normal editing workflow.

Once a result has been published, normal product behavior must preserve that historical revision. A published revision may later cease to be current, be superseded, or be archived, but it must not be silently hard-deleted or rewritten in place.

Creating a later version must not reset or discard previous accepted work. The working state used for continued planning inherits the current accepted content by default, including unchanged geometry, demolition intent, construction intent, finishes, measurements, and other applicable planning data. The user changes only what actually needs to change.

Publishing a later version creates a complete immutable snapshot of the current publishable working result. Content that was not edited remains part of that new snapshot through inheritance; publication is not equivalent to starting a new empty project.

After publication, the application must continue from the published state rather than clearing the user's work. Further edits create later working state that may eventually be published as another revision.

Returning to an earlier design means restoring/copying that historical state into a new working draft rather than rewinding history as though intervening revisions never existed. If that restored draft is later published, it becomes a new later revision while the intervening history remains intact.

This supports practical comparison workflows without introducing parallel design variants. For example, a user may publish one revision based on drywall construction, publish a later revision based on plaster, then restore the earlier drywall state into the current draft and publish it as a new later revision if the client chooses it.

The exact statuses, retention policy, administrative recovery mechanisms, and authorization rules are deferred to later design states.

## Primary planning scope

Current in-scope capabilities include:

- walls and connected wall geometry;
- rooms derived from spatial boundaries;
- room perimeters and derived floor/ceiling surfaces required for room specification;
- wall height and thickness as construction-relevant facts;
- room, wall, opening, floor, and ceiling height/elevation parameters required by owned calculations;
- spatially varying floor/ceiling survey and planning maps based on a 2D measurement grid;
- doors and windows as real wall openings rather than decorative SVG overlays;
- construction-oriented dimensions;
- accurate placement in real-world units;
- demolition intent for relevant existing walls/openings/finishes/floor layers/ceiling systems;
- new/changed wall and opening construction;
- drywall/gypsum-board partition systems and their physical quantity calculations;
- plaster with selected/defined thickness and resulting physical quantity calculations;
- putty quantities derived from applicable surface area;
- paint and other supported surface-finish quantities derived from applicable surface area and required system parameters;
- ceiling preparation and finish intent and its physical quantity calculations;
- floor leveling/fill quantities derived from measured/derived and target floor surfaces;
- interactive preview of geometric and physical-quantity consequences before publication;
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

## Ceiling responsibility

Ceilings are inside the Room Planner product boundary because they are construction-relevant room surfaces derived from or associated with the room's spatial geometry and are required for a useful room specification.

Room Planner must be able to record the existing ceiling condition, represent demolition intent for an existing ceiling system or finish where applicable, and represent construction/preparation/finish intent for the retained or proposed ceiling surface.

For example, an existing suspended ceiling may be marked for demolition, while a retained exposed Catalan ceiling may remain part of Existing and receive Construction intent for cleaning/preparation and lacquer or another supported finish system.

Room Planner owns the geometric physical quantities for supported ceiling work, such as applicable ceiling surface area and quantities derived from that area plus Construction Catalog technical parameters. Pricing, labor costing, and commercial work-item composition remain PresuPro responsibilities.

The exact ceiling domain model, supported ceiling systems, treatment taxonomy, and calculation rules are deferred to later design states.

## Floor and vertical-surface-map responsibility

Room Planner owns the measured and planned geometry needed to describe floor preparation and its relationship to the ceiling.

The product must support a measurement-grid view in which relevant plan locations can carry floor elevation relative to the project datum together with local floor-to-ceiling height. The corresponding ceiling elevation is derived from those two facts.

These maps must remain semantically distinct across renovation stages:

- Existing describes the measured pre-renovation floor/ceiling landscape;
- Demolition describes removal intent and may derive the resulting post-demolition substrate/surface landscape;
- Construction describes the target prepared floor/ceiling landscape after Room Planner-owned work.

A single generic `floor_level` meaning is therefore insufficient at the product level. Later domain design must preserve the distinction between measured Existing elevation, demolition-result geometry, and Construction target geometry.

Room Planner owns floor leveling/fill as part of preparing room geometry for renovation. Physical quantity calculations may depend on the spatial difference between the post-demolition/preparation surface and the Construction target surface rather than assuming one uniform thickness for the whole room.

The user must be able to experiment with proposed surface changes before committing them. For example, the user may temporarily raise a selected area or an entire target floor surface by 10 mm and inspect the resulting changes in leveling/fill thickness, physical material volume, and clear heights. Such a preview is an editing/analysis capability; it does not itself create a published revision or publish anything to the platform.

Final floor covering is explicitly outside this product boundary.

A separate Tile/Floor Covering Planner is expected to own concerns such as:

- tile or other finish selection;
- layout;
- patterns;
- cuts;
- joints;
- finish-specific wastage;
- finish-material quantities.

Room Planner publishes the prepared spatial geometry and physical quantities it owns; the final design decision about whether a resulting height or level is acceptable remains with the renovation professional or a relevant downstream planner.

The exact survey acquisition method, grid spacing, surface interpolation, editing operations, and calculation algorithms are deferred to later design states.

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
- m² of ceiling surface or supported ceiling treatment;
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

`room_plan` is the provisional versioned domain artifact family for Room Planner.

At State 0 it should be understood as the platform-facing family that carries Room Planner's coherent object-level planning results across included spatial levels while preserving the semantic separation of Existing, Demolition, and Construction.

Existing, Demolition, and Construction have independent publication readiness. An accepted Existing result may be published before Demolition is complete; an accepted Demolition result may be published before Construction is complete; and Construction may be published later as its own historical milestone.

Each later dependent publication must preserve enough provenance to identify the accepted basis against which it was prepared. A published Demolition result must remain associated with the relevant Existing publication. A published Construction result must remain associated with the relevant Existing basis and with the relevant Demolition basis where demolition participates in that proposal.

Whether later contracts expose these stage publications as one container artifact with independently versioned components, several related artifacts, or both is deliberately deferred. The product requirement is independent publication and historical identity, not a predetermined artifact packing scheme.

### `room_takeoff`

`room_takeoff` is the provisional versioned physical-quantity output derived from the relevant Room Planner plans using an identified Construction Catalog revision.

It is intended to give PresuPro and other consumers quantities without requiring them to duplicate Room Planner geometry or construction calculations.

Its quantities must preserve the distinction between demolition scope and construction scope where that distinction affects downstream work, and a published takeoff must retain provenance to the exact accepted/published planning basis used for the calculation.

`room_plan` and `room_takeoff` are outputs of the same application boundary; introducing several plan meanings or artifacts does not imply separate backend services.

## Relationship to PresuPro

PresuPro is the estimating application.

Room Planner provides physical quantities for its owned renovation scope. PresuPro owns pricing, labor/work calculation, estimate composition, and conversion of physical quantities into purchasable package counts when that commercial step is required.

PresuPro should consume published Room Planner artifacts through the shared platform boundary rather than through a private Room Planner-to-PresuPro API.

PresuPro should not be required to reverse-engineer Room Planner geometry in order to reproduce drywall, plaster, putty, paint, ceiling-treatment, floor-fill, or demolition quantity logic owned by Room Planner.

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

## Client-history publication responsibility

Room Planner does not own the client cabinet UI or its presentation rules, but its published planning milestones are part of the platform-visible renovation history.

Published Existing, Demolition, and Construction results must therefore remain individually discoverable through the shared platform boundary so the client cabinet or another authorized history consumer can present the chronological evolution of the renovation object.

A later Construction publication must not erase, absorb, or silently rewrite earlier Existing or Demolition publications. Later corrections and propagated versions appear as later historical publications while previous milestones remain identifiable.

Which exact payload fields are client-visible, whether a rendered derivative is required for presentation, and authorization/redaction rules are platform/client-cabinet concerns deferred beyond this product boundary.

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
- client-cabinet behavior and presentation rules;
- arbitrary free-form 3D solid/mesh modeling as an authoritative editing model;
- automated domain decisions about whether furniture, kitchens, equipment, or other downstream designs fit within the available spatial envelope;
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
preview / adjust planning consequences
        ↓
calculate physical quantities
        ↓
review
        ↓
publish an identifiable stage/result version
        ↓
downstream platform consumers / object history
```

More explicitly:

1. The user opens Room Planner and selects an existing renovation object supplied by Registry.
2. The user creates or continues the Existing Plan and records the measured current condition, including relevant floor elevations and local floor-to-ceiling heights.
3. The Existing Plan remains independent from later demolition and construction work so the original observed state is not overwritten.
4. The user may publish an accepted Existing result before later renovation-stage work is complete.
5. The user records Demolition work separately against the Existing condition and may inspect resulting post-demolition geometry where removal changes floor or ceiling surfaces.
6. The user may publish an accepted Demolition result before Construction is complete; that publication remains associated with its Existing basis.
7. The user records Construction work separately, including new/changed geometry, target prepared surfaces, and the construction/finish systems owned by Room Planner.
8. The user may inspect a Proposed / To-Be result derived from Existing, Demolition, and Construction without turning that derived view into a mixed source of truth.
9. The user may preview changes to target geometry and immediately inspect resulting thicknesses, physical quantities, and clear heights before accepting those edits into the working state.
10. Room Planner calculates physical quantities for the scope it owns using the relevant geometry, construction intent, and applicable Construction Catalog data.
11. The user reviews the resulting plan and quantities.
12. When any independently publishable stage/result is ready for use outside the working session, the user explicitly publishes an identifiable version for downstream platform consumers and platform history.

The workflow does not need to complete in one session. The product must support saving incomplete work and continuing it later.

## Save, preview, and publish are different product actions

Saving working state, previewing consequences, and publishing a result have different meanings.

**Preview / what-if** means the user is exploring a geometric or planning change and its derived consequences, such as changing a target floor elevation and observing new fill thicknesses, material volumes, and clear heights. Preview does not create a published revision and does not expose a result to downstream platform consumers.

**Save / draft** means the user is preserving incomplete or ongoing working state for later continuation. Saved working state may include accepted edits and may continue from previously published content, but it is not automatically a platform promise that downstream applications should consume it. Repeated draft saves do not create published revisions.

**Publish / send** means the user intentionally creates and exposes a specific identifiable immutable result version for use by other platform applications. Publication must require an explicit two-step confirmation so that an ordinary edit, preview, or save cannot accidentally create a platform-visible version.

Publishing snapshots the complete current publishable result for the selected stage/scope, including inherited unchanged content and the user's changes required to interpret that result coherently. It does not reset the project or discard the working state. After successful publication, continued work begins from the published content.

A later edit must not silently mutate the meaning of an already published result; it produces later working state and eventually another published version only if the user explicitly publishes again.

The exact persistence model, transient-preview implementation, confirmation UI wording, publication-scope representation, and revision numbering mechanics are deferred.

## Stage publication readiness is independent

Existing, Demolition, and Construction are not required to become publishable at the same time.

Room Planner must allow an accepted Existing result to be published independently because the measured/as-built spatial condition has platform value before demolition or construction design is complete.

Room Planner must also allow an accepted Demolition result to be published independently before Construction is complete. This allows demolition scope to become an identifiable historical/platform result while later design work continues.

Construction may be published later when that proposal is accepted. Each publication is a separate historical milestone and must remain identifiable after later stages or revisions are published.

Dependent stage publications must retain their basis. Demolition must be traceable to the Existing result against which it was prepared. Construction must be traceable to the relevant Existing basis and, where applicable, the Demolition result with which it is coordinated.

These independently published milestones are expected to be discoverable by authorized platform consumers, including the client cabinet for renovation-object history. Room Planner does not define how the client cabinet renders or explains them.

The exact artifact packaging remains deferred: independent stage publication may later be represented as one `room_plan` family with stage-aware revisions/components, as several related artifacts, or as both. The product semantics above must survive whichever contract representation is chosen.

## Important failure outcomes

At State 0, the product must make the following important failures observable rather than silently fabricating or publishing a plausible-looking result:

- If the selected Registry object is unavailable or cannot be resolved, Room Planner cannot create or substitute another platform object identity and must not proceed as if the object were valid.
- If geometry or required planning inputs are incomplete or invalid for a requested calculation, Room Planner must not present the resulting quantities as valid completed takeoff data.
- If required Construction Catalog data or the required catalog revision cannot be resolved, Room Planner must not invent technical constants or silently calculate with unrelated defaults.
- If a dependent stage cannot identify or validate the Existing/Demolition basis it was prepared against, Room Planner must not publish that dependent result as though its provenance were coherent.
- If publication fails, the working result remains unpublished/draft from the platform perspective; the product must not report a successful publication.
- If a historical revision has already been published, later editing or recovery failures must not silently mutate that published historical result.

The exact validation rules, error models, retry behavior, HTTP status codes, and user-interface messages are deferred to later design states.

## Observable user outcomes discovered so far

A user can select an existing renovation object and work on its Room Planner container.

The user can create or edit an accurate Existing Plan without mixing it with future construction intent.

The user can record and inspect spatially varying floor elevations and floor-to-ceiling heights over a measurement grid rather than reducing a room to one floor level and one height.

The user can preserve unfinished work without publishing it to downstream applications.

The user can independently publish accepted Existing, Demolition, and Construction milestones as they become ready rather than waiting for the entire renovation proposal to be complete.

The user can separately describe Demolition work against the existing condition and inspect relevant resulting surface geometry.

The user can separately describe Construction work and finishes, including Room Planner-owned ceiling treatments and target prepared floor/ceiling geometry.

The user can inspect a resulting Proposed/To-Be view derived from the isolated plan meanings.

The user can derive room-relevant geometry and specifications from the authoritative 2D plan plus vertical parameters.

The user can preview a proposed geometric change and see its effects on thicknesses, quantities, and clear heights without thereby publishing a new version.

The user can obtain reproducible physical quantities for the scope owned by Room Planner.

The user can continue from previous accepted work without a new version resetting unchanged planning data.

Published stage milestones remain individually identifiable for downstream consumers and platform/client history after later stages or revisions are published.

The plan and quantity results can be saved as working drafts, revised, explicitly published, and consumed by other platform applications.

Changes to a published result must create a new identifiable revision only through a later explicit publication rather than silently replacing the provenance of downstream work.

## Unresolved product questions deferred to later states

The following questions remain intentionally unresolved because they do not block the State 0 product boundary and belong to later design work:

- Which wall/opening editing operations are mandatory for the first usable release?
- What is the exact lifecycle for creating, accepting, freezing, and correcting the Existing baseline?
- What detailed rules and user interaction distinguish a late discovery about the pre-renovation condition from a state change caused by performed demolition or construction work?
- How are floor/ceiling grid measurements acquired or imported?
- What grid density, interpolation, and surface-reconstruction rules are required for survey and planning?
- Which ceiling systems and preparation/finish treatment families are required in the first usable release?
- Which construction systems/material families are required in the initial Construction Catalog?
- Does Room Planner expose editable construction-system templates, catalog-selected fixed systems, or both?
- Which Room Planner payload fields/stage details are directly client-visible versus exposed through derived/redacted client-facing artifacts?
- At the platform contract level, how should independently publishable Existing, Demolition, and Construction milestones be represented: one stage-aware `room_plan` artifact family, several related artifacts, or both?

## Cross-document rule

Any shared integration requirement discovered while progressing through later Room Planner design states must be evaluated against [PLATFORM_ROUTER.md](../../PLATFORM_ROUTER.md).

If it is a platform-wide exchange concern, update the Platform Router document rather than inventing a Room Planner-specific platform protocol.
