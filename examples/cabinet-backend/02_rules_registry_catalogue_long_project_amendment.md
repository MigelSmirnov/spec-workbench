# State 2 amendment — long-running projects and old Registry catalogues

## Status

Accepted correction to `02_rules_registry_catalogue.md`.

This amendment supersedes the baseline rule that blocks every new Registry ID
assignment when the catalogue reaches 30 days of age.

## Product reason

A Cabinet user may work on one active project for three or four months while no
other projects are created. In that situation, catalogue age does not make the
already known project identity unsafe or irrelevant.

Freshness rules must distinguish:

- continuing work with a project already known and previously selected;
- selecting another project already present in the verified catalogue;
- discovering a project that did not exist in the cached catalogue;
- validating current Registry state.

## Corrected freshness policy

Catalogue age classes remain:

- `fresh`: less than 48 hours;
- `stale`: at least 48 hours but less than 7 days;
- `very_stale`: at least 7 days but less than 30 days;
- `legacy_verified`: 30 days or older.

`legacy_verified` replaces `expired_for_assignment`.

A verified catalogue never expires merely because time passed. Its age changes
the warning and confirmation requirements, not the identity of projects already
contained in it.

## Rules

### Rule L1 — Continue existing project work

A project already referenced by an accepted Invoice Card or other retained
Cabinet relationship remains selectable for additional work regardless of
catalogue age.

Cabinet MUST show:

- the catalogue age;
- the last known Registry status;
- whether a current Registry validation is unavailable.

After 30 days, explicit acknowledgement is required once per working session
before adding new invoices to that project while Registry is unavailable.

### Rule L2 — Select another cached project

A project present in the current verified catalogue may still be selected after
30 days.

The user MUST explicitly acknowledge that the project status may have changed
since the catalogue was generated.

The assignment retains the exact catalogue and project snapshot provenance and
must be revalidated after the local platform reconnects.

### Rule L3 — Unknown projects

Cabinet MUST NOT invent, manually type, or claim a Registry `project_id` that is
absent from the current verified catalogue.

A new real-world project that is not in the cached catalogue may be recorded only
as:

- an unassigned invoice; or
- a free-form label allowed by Invoice Card V1.

The Registry ID may be attached later through an explicit Card revision after a
catalogue refresh.

### Rule L4 — Age is not Registry validation

A recent catalogue does not prove that a project is still active, and an old
catalogue does not prove that it is archived or missing.

Only a current Registry validation determines `valid_active`, `valid_archived`,
`not_found`, `registry_unavailable`, or `inconclusive`.

### Rule L5 — Matching and analytics

When the catalogue is 30 days old or older and Registry is unavailable:

- invoice capture and project assignment remain allowed under Rules L1 and L2;
- new automatic PresuPro matching is deferred until current Registry validation;
- historical matches and previously calculated analysis remain readable;
- provisional analysis may be shown only with an explicit stale-context warning.

### Rule L6 — Refresh expectation

The local platform SHOULD refresh the catalogue whenever it becomes available,
but failure to connect for several months MUST NOT stop work on a known project.

The system must degrade by warning and preserving provenance, not by blocking the
core capture workflow.

## Corrected invariant

The following invariant replaces the earlier 30-day blocking invariant:

> Catalogue age never invalidates a known Registry project identity. A verified
> cached project may remain usable for capture with age-dependent warning and
> acknowledgement, while current validation-dependent operations may be
> deferred.

## Closed baseline values

| Concern | Accepted value |
| --- | --- |
| Fresh catalogue | `< 48 hours` |
| Stale warning | `48 hours to < 7 days` |
| Strong warning | `7 days to < 30 days` |
| Legacy verified catalogue | `>= 30 days` |
| Continue work on previously used project | allowed with session acknowledgement after 30 days |
| Select another project already in catalogue | allowed with explicit acknowledgement after 30 days |
| Assign Registry ID absent from catalogue | forbidden |
| Automatic new matching without current validation after 30 days | deferred |
| Capture invoice without current validation | allowed |

## Consolidation requirement

Before State 2 is declared complete, this amendment must be merged into
`02_rules_registry_catalogue.md`, replacing:

- `expired_for_assignment` with `legacy_verified`;
- the blanket 30-day assignment block;
- the related invariant and closed-value table row.
