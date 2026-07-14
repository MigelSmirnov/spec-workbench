# Hydraulic Diagram Service — source context

## Purpose of this case study

This example is the first practical run of the `spec-authoring` skill.

The target is **not** the existing frontend repository itself. The target is a new backend microservice:

> Hydraulic Diagram Service — the source of truth for structured hydraulic diagrams, their catalogs, revisions, editor layout, and deterministic estimation-data packages.

The existing frontend is used as an implementation and domain reference.

## Source repositories

- Existing editor: `MigelSmirnov/hydraulic-diagram-editor`
- Authoring methodology and target specification standard: `MigelSmirnov/spec-workbench`

## Existing product evidence

The current frontend already demonstrates:

- visual placement of hydraulic elements;
- logical ports and port-to-port connections;
- typed line definitions;
- JSON save/load;
- autosave;
- undo/redo;
- PNG export;
- MCP-based diagram editing;
- executable validation before imported JSON replaces editor state;
- separation of JSON persistence and image export;
- catalog-driven element, port, line, and template definitions.

## New backend intent

The backend will serve several clients:

- the visual hydraulic diagram editor;
- a specialized diagram-authoring agent;
- the Estimator Service backend;
- the estimator's agent through agent-facing tools such as MCP;
- future project microservices that need structured diagram data.

The service must not be designed as a persistence wrapper for React Flow JSON. React Flow is a frontend implementation detail.

## Platform context

A separate Object Card Service is intended to be the source of truth for object and customer data. All platform microservices will use a common external `object_id`.

The exact Object Card Service contract is temporarily unavailable. This is an explicit integration placeholder confined to a gateway boundary. It must not spread generic `object_data: dict` structures into the domain model.

The Estimator Service already has or is planned to have capabilities for:

- creating an object card independently during the transition period;
- agent-driven estimate composition through MCP;
- matching live Brico Depot products and prices;
- saving materials;
- pushing a completed presupuesto to Holded.

These capabilities remain outside Hydraulic Diagram Service.

## Deterministic estimation-data collector

Hydraulic Diagram Service must provide a deterministic collector that converts a concrete diagram revision into a stable package for the Estimator Service.

The collector may:

- group diagram elements;
- count quantities;
- collect connection types and parameters;
- derive measurable lengths when supported by authoritative geometry;
- expose estimation classification references;
- report missing required properties;
- preserve provenance to source diagram entities.

The collector must not:

- calculate prices;
- select Brico Depot products;
- compose the final estimate;
- create a Holded presupuesto;
- invent missing engineering decisions.

## Consumer interfaces

The same domain operation that creates estimation data must be available through multiple transport boundaries:

- service-to-service HTTP API for Estimator Service;
- agent-facing API or MCP tools for the estimator agent.

Transport handlers must not implement independent package-building logic.

## Authoring modes

This case study is an architectural migration, not a literal reconstruction of the current frontend.

Decisions already accepted:

- durable diagram data is independent of React Flow;
- editor layout is separate from engineering structure;
- element definitions are distinct from element instances;
- agent-created definitions are controlled domain records, not arbitrary JSON;
- estimation-data generation is deterministic for fixed diagram and catalog revisions;
- the service stores and exposes revisions;
- API and MCP use the same application/domain operations.

## Current unknowns

The following remain intentionally unresolved and must be localized rather than hidden behind broad placeholders:

- exact Object Card Service DTO and transport;
- authentication, authorization, tenancy, and service identity model;
- approval policy for agent-created catalog definitions;
- exact property set required by Estimator Service;
- supported hydraulic system taxonomy;
- whether route geometry is authoritative enough to calculate pipe length;
- concrete database technology;
- event bus or synchronous integration strategy;
- retention policy for diagram revisions.

## Scope rule

This case study specifies only Hydraulic Diagram Service.

Object Card Service, Estimator Service, Brico Depot integration, and Holded integration are external systems. They are described only to define stable boundaries and required outputs.
