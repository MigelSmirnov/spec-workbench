# Future capability — CAD / DXF export

> Status: parked future capability discovered during State 0.
>
> This note records architectural intent without promoting CAD generation into the current Room Planner product core or prematurely defining contracts.

## Intent

Room Planner should preserve a future path to generate professional CAD drawings from published/versioned planning data.

The preferred implementation direction is a Python CAD export module based on `ezdxf`.

The exporter is downstream from Room Planner domain data. It is not a second source of truth for walls, openings, demolition, construction, dimensions, or quantities.

Conceptually:

```text
published Room Planner revision
        +
versioned CAD block/template library
        +
drawing/export profile
        ↓
CAD / DXF exporter
        ↓
DXF drawing artifact / drawing set
```

## Boundary rule

The CAD exporter MUST consume Room Planner results; Room Planner domain state MUST NOT depend on DXF entity handles, DXF block names, CAD layers, paperspace layouts, or other exporter-specific representation details.

Changing rendering/export conventions must not mutate the semantic meaning of Existing, Demolition, Construction, or quantity results.

## Plan semantics

The exporter must preserve the semantic separation established by Room Planner:

- Existing Plan — observed/as-built geometry;
- Demolition Plan — removal scope;
- Construction Plan — new/changed work;
- Proposed/To-Be — derived presentation where required.

How these meanings map to CAD layers, linetypes, colors, layouts, sheets, and annotation conventions is an exporter concern to be designed later.

## CAD block library

The exporter should be able to resolve a curated library of reusable CAD blocks for drawing elements such as doors, windows, symbols, fixtures, annotations, or other standardized graphical elements introduced later.

The block library should be versionable so that a generated historical drawing can retain provenance to the block/template revision used to produce it.

The CAD block library is conceptually distinct from the Construction Catalog:

- Construction Catalog owns technical construction/material parameters used for calculations;
- CAD block/template library owns graphical drafting resources and drawing conventions.

Whether both are exposed through one platform catalogue service or separate implementations is intentionally unresolved.

## Output and provenance

A generated DXF should eventually be publishable as a derived platform artifact, likely under the existing broader `drawing_set` family or a more specific CAD drawing artifact if later flows justify one.

The generated artifact should retain provenance to at least:

- the exact Room Planner revision(s) used;
- the CAD block/template library revision used;
- the exporter/profile version used where reproducibility requires it.

## Initial implementation shape

Because the current AI Code Factory generates Python backend code and `ezdxf` is a Python library, the initial implementation should prefer a dedicated backend module/generation unit rather than an independent network service.

The exporter may be extracted into a separate service later only if operational scale, reuse by multiple applications, asynchronous generation, or independent deployment makes that boundary useful.

## Deferred decisions

- exact DXF version/profile;
- unit conventions in generated files;
- layer naming and style standards;
- modelspace vs paperspace responsibilities;
- dimensions and annotation generation;
- sheet/title-block templates;
- block-library storage and distribution;
- whether PDF/SVG generation shares the same rendering pipeline;
- whether export is synchronous or job-based;
- exact platform artifact type and API contract.
