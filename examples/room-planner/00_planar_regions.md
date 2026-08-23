# Room Planner — State 0: Planar Construction Regions

> Status: accepted State 0 refinement.
>
> This document refines the stabilized product boundary after confirming a common
> renovation workflow: many construction features are authored in the 2D plan by
> drawing their footprint and entering one explicit vertical parameter manually.
> It is normative where it refines the earlier floor/ceiling wording in
> `00_product.md`.

## 1. Common authoring pattern

Room Planner remains a 2D plan-centric application. The initial product does not
require the user to build arbitrary 3D solids for common floor and ceiling work.

For relevant construction features the normal authoring pattern is:

```text
2D footprint in plan
        +
explicit vertical parameter entered by the user
        +
selected Construction Catalog system
        ↓
derived construction geometry / surfaces / physical quantities
```

The 2D footprint is authoritative plan geometry. The vertical parameter is an
explicit construction fact, not a renderer property and not an inferred value.

## 2. Floor screed / build-up

Floor screed, leveling, fill, and equivalent supported Room Planner-owned build-up
work are initially authored as planar regions.

The user:

1. draws/selects the affected 2D footprint;
2. enters the intended build-up thickness for that region;
3. selects the applicable Construction Catalog system.

Conceptually:

```text
floor region footprint
    + thickness_mm
    + construction system
```

The resulting prepared floor surface is derived from the applicable source
surface plus the explicit build-up thickness.

The initial product must support several regions with different explicit
thicknesses where the practical design requires them. A single room-wide scalar
is therefore not mandatory, but each authored region has an explicit thickness
rather than a silently interpolated construction thickness.

Measured Existing floor elevation may still vary spatially. A constant build-up
thickness over a region may therefore produce a target floor surface that follows
the source slope/variation while being offset by the entered thickness.

The product may later add an alternative absolute-target-elevation authoring mode
if a real workflow requires it. That mode is not implied by this refinement and
must not be fabricated from the current model.

## 3. Ceiling boxes / soffits are initial-scope construction

Ceiling boxes, soffits, drops, and similar locally lowered ceiling constructions
are common enough to be part of the initial Room Planner product rather than a
future speculative extension.

The user authors a ceiling box by:

1. drawing its 2D footprint in plan;
2. entering its vertical drop/height manually;
3. selecting the applicable Construction Catalog system.

Conceptually:

```text
ceiling-box footprint
    + drop_height_mm
    + construction system
```

Room Planner derives the construction envelope needed for planning and quantity
calculation, including:

- the lowered underside surface over the footprint;
- vertical side faces around the applicable footprint boundary;
- the resulting clear-height consequence below the box;
- supported physical quantities from the derived geometry plus catalog data.

The user does not model the box as an arbitrary 3D solid. The 3D-relevant facts
are derived from 2D footprint + explicit drop height.

## 4. Existing and Demolition meaning

Existing may contain measured ceiling boxes/soffits where they physically exist
and affect room geometry.

An Existing ceiling box is an observed spatial construction, not merely a hatch
or drawing annotation.

Demolition may explicitly target an Existing ceiling box for removal. Removing a
box is demolition of a physical construction and may change the resulting
post-demolition ceiling surface / clear-height geometry.

Existing floor/ceiling finish or build-up layers remain separately representable
where their material/layer meaning matters.

## 5. Construction treatment versus construction geometry

A ceiling box is not the same concept as a ceiling finish treatment.

```text
ceiling box / soffit
    = construction geometry with its own footprint and vertical extent

ceiling treatment
    = preparation / finish system applied to a ceiling surface
```

Likewise, a floor build-up region changes prepared floor geometry, while a future
surface-only treatment that does not materially change the prepared elevation
would be a different intent.

These concepts may be rendered with similar fills or hatches in 2D, but their
domain meanings and quantity consequences are different.

## 6. Browser/editor consequence

These features are not palette blocks in the same sense as doors, fixtures, or
engineering symbols.

The browser should treat them as region-editing capabilities:

```text
activate region tool
    ↓
draw/select footprint
    ↓
enter thickness/drop and system
    ↓
preview derived surface / clear height / quantities
    ↓
confirm into working draft
```

The rendered polygon, hatch, heat map, labels, handles, or contours are frontend
projections. They do not replace the canonical footprint and explicit vertical
parameter.

## 7. Quantity boundary

Room Planner owns physical geometry/quantity calculations for these constructions.

Examples include:

- floor build-up volume from footprint and explicit thickness;
- box underside area;
- box vertical side-face area;
- system component quantities derived from those surfaces/volumes and exact
  Construction Catalog technical data.

Pricing, labor costing, package conversion, and commercial rounding remain
outside Room Planner and belong to PresuPro as already established.

## 8. Platform Router impact

This refinement introduces no new Platform Hub mechanism.

Room Planner may publish the resulting structured construction geometry and
physical quantities through the already established artifact/publication
boundary. The Platform Hub must not become the owner of footprint editing,
box/screed geometry derivation, or quantity calculation.

## State 0 effect

State 0 remains stabilized with this refinement included.

The earlier broad idea that Construction may define arbitrary target floor/ceiling
surfaces is narrowed for these initial workflows:

- floor build-up is primarily authored as explicit planar regions with manual
  thickness;
- ceiling boxes/soffits are explicit initial-scope planar construction regions
  with manual drop height;
- resulting target surfaces are derived from those accepted inputs.
