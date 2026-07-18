# State 0 — Product Boundary

## Status

**Agreed baseline**

## Product purpose

Client Portal is the client-facing view of an existing renovation project. Its
current purpose is to present the project's current identity/context and the
budget information that is explicitly available for portal use.

## Responsibilities

- Present the selected renovation project to the client.
- Use Registry-owned project identity and current project context.
- Present budget information from an approved external source when such a
  source exists.
- Support temporary manual-budget data for the pilot while PresuPro lacks a
  publishable immutable approved snapshot.
- Keep unknown approval, publication, versioning, and invoicing decisions
  visible rather than replacing them with assumed behavior.

## Explicit non-goals

- Creating, renaming, archiving, or otherwise managing Registry projects.
- Creating or editing PresuPro estimates.
- Calculating PresuPro totals independently.
- Approving estimates or defining an approval workflow.
- Creating facturas or operating the Holded invoicing flow.
- Treating a Holded payload as the canonical portal presupuesto.
- Defining functionality beyond the current project-context and budget pilot.

## Ownership boundaries

- Registry owns `project_id` and the current project name, address, status, and
  project customer reference.
- PresuPro owns editable estimate data, estimate calculations, and any future
  approved estimate snapshot contract.
- Client Portal owns its client-facing presentation and the temporary manual
  budget information used by the pilot.
- PresuPro's fiscal client data remains PresuPro-owned and is not replaced by
  Registry project context.

## Read and write responsibilities

- Client Portal reads project identity and current context from Registry.
- Client Portal does not write project identity or project context to Registry.
- Client Portal does not use a current mutable PresuPro estimate as if it were
  an approved publication snapshot.
- The pilot may receive and maintain manual budget information within the
  portal boundary.
- The current MVP does not write estimate or invoice state to PresuPro.

## Current MVP scope

- Work with an existing active Registry project.
- Validate the selected project reference and display its current Registry
  context.
- Present manually supplied pilot budget information.
- Preserve a migration boundary for a future approved estimate snapshot
  without defining that snapshot prematurely.
