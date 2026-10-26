# Registry — source context and legacy evidence

## Purpose of this case

Registry is a running service of the platform whose specification predates
SPEC_STANDARD v2: `projects/registry_sandbox/specs/base/global_spec.json` in the
Factory declares no `standard_version`, still carries the retired `adapters`
section, and the Factory refuses it (`factory_state`:
`BLOCK unsupported_standard_version`, 2026-10-26). This case re-authors the
Registry through the design states from its product meaning, with the running
code as evidence.

The method is `skills/spec-authoring/LEGACY_MIGRATION_EVIDENCE.md`: **code and
tests are probes, never sources of norm.** Every finding below is classified;
`unresolved` findings are questions for the owner, not defaults.

## Evidence sources

All Factory paths are at `code_factory` commit `f5d700b3` (`main`, 2026-10-26).

| source | what it shows |
|---|---|
| `projects/registry_sandbox/` (≈1300 lines of Python) | the running service: FastAPI app `api/runtime.py`, service `services/registry/project_service.py`, stores `infra/registry/*`, SQLite `infra/registry/sqlite_repository.py`, rules `domain/registry/rules.py` |
| `projects/registry_sandbox/specs/base/global_spec.json` | the v1 spec: 43 contracts, 16 models, 162 notes, `rules.status_policy`, `rules.artifact_policy`, `config.api` |
| `projects/registry_sandbox/frontend/` | a staff UI: list (with archived), read, create, update, archive projects; no rooms, no artifacts |
| `platform/manifest/registry.json` | 14 declared capabilities, known defects `identity-per-instance`, `closed-artifact-vocabulary`; surface gate `GATE PASS` on 2026-10-26 |
| Factory branch `agent/cabinet-kernel-store-determinism`, `projects/cabinet_kernel/operator_tests/live/` (commit `bd787fbb`) | Cabinet Kernel run against a live Registry rig, scenarios R1–R6, M1–M4 |
| consumers (below) | which operations and fields leave the service |

### Consumers observed in code

| consumer | operations | fields read |
|---|---|---|
| PresuPro `backend/adapters/registry.py` | `GET /projects/{id}/validate`, `GET /projects/{id}/context` | `exists`, `is_active`, `failure`; `project.project_id`, `display_name`, `status`, `address`, `customer_ref`, `created_at`, `registry_updated_at` |
| Client Portal `adapters/registry_gateway.py` | the same two | the same |
| Cabinet Kernel (live scenarios) | `project.create`, `room.create`, `project.context`, `artifact.publish`, `project.list` | `project.id` inside `{"project": …}` |
| `tools/onboard_object.py` (Factory operator) | `GET /projects`, `GET /projects/{id}` for each, `POST /projects` | `customer_ref`, used as the lookup key of an object |
| Cabinet Web catalogue mirror | Registry catalogue through the Cabinet Web plugin | `project_id`, `display_name`, `address`, `status`, `registry_updated_at` |
| Registry frontend | `GET /projects?include_archived`, `GET/PUT /projects/{id}`, `POST /projects`, `POST /projects/{id}/archive` | project card |

Cabinet Web is off active development since 2026-09-27; its read stays a
consumer to keep compatible, not a driver of change.

## Decisions recorded in the v1 spec

The v1 notes hold design decisions, not only implementation hints. They are
evidence of what the owner decided then; each must be kept, narrowed or
replaced by an explicit State 0–2 decision, never dropped silently.

- V1-1 `project_service [DEPENDENCY_BOUNDARY]`: the registry owns identity only
  (projects, rooms, address, customer_ref) and MUST NOT store drawings,
  measurement facts or planner documents.
- V1-2 `[PROVENANCE]`: the registry is the single living owner of identity;
  consumers snapshot identity at read time and MUST NOT write it back.
- V1-3 `[BEHAVIOR]`: the registry is the Project Hub entrypoint — it owns the
  project card context used to open downstream services, but does not
  orchestrate or store their domain data. Launch context is `project_id`,
  optional `room_id`, `source=registry`.
- V1-4 `[DEPENDENCY_BOUNDARY]`: the registry MAY persist immutable artifact
  catalogue metadata and service-owned storage references, never payloads.
- V1-5 `generate_uuid [DETERMINISM_OR_ORDERING]`: MUST return a UUID4 and MUST
  NOT reuse caller-supplied identifiers for primary keys. **This is the origin
  of the manifest defect `identity-per-instance`**: the defect is a recorded
  decision, and replacing it is an owner decision (L01).
- V1-6 `[BEHAVIOR]`: one active wall document per room is the planner's
  guarantee, not the registry's.
- V1-7 `get_project_record [BEHAVIOR]`: archived projects stay readable.

## Legacy probe findings

Locations are relative to `projects/registry_sandbox/`. Classes as in
`LEGACY_MIGRATION_EVIDENCE.md`.

| id | finding | location | class | owning state |
|---|---|---|---|---|
| L01 | The server mints every id (UUID4); a caller cannot supply one. The same physical object gets a different `project_id` in every instance (rig vs VPS, 2026-09-10). | `domain/registry/utils.py:generate_uuid`; v1 note V1-5 | `unresolved` | State 0 / 1 |
| L02 | `project.create` accepts no idempotency key: two equal calls create two projects (kernel R2); a lost answer leaves orphan-or-duplicate (kernel R3). The operator works around it by reading every project and matching `customer_ref`. | `services/registry/project_service.py:create_project`; `tools/onboard_object.py:find_project` | `unresolved` | State 2 |
| L03 | `customer_ref` is an opaque optional string: no format, no uniqueness, no entity behind it. It is used as a de-facto object key by operators and the Portal import. No contact data (phone, e-mail) exists anywhere on the platform; PresuPro `Client` holds `email` but no phone, Portal `ClientViewer` holds no contact data by decision. | `core/models.py`; `tools/portal_import/README.md`; Factory `AGENTS.md` "Client portal" | `unresolved` | State 0 / 1 |
| L04 | `PUT /projects/{id}` replaces `name`, `address`, `customer_ref` as a whole; a request without `customer_ref` clears it. | `infra/registry/project_store.py:update_project_record` | `unresolved` | State 2 |
| L05 | An archived project can be updated; rooms and artifacts cannot be added to it. | `services/registry/project_service.py:update_project`, `add_room`, `publish_artifact` | `unresolved` | State 2 |
| L06 | Archive is one-way (no unarchive) and repeatable: a second archive succeeds and moves `updated_at`. | `infra/registry/project_store.py:archive_project_record` | `unresolved` | State 2 |
| L07 | Publishing supersedes the previous artifact and inserts the new one in separate commits; two concurrent publishes of one type violate `UNIQUE(project_id, artifact_type, version)` and answer 500. | `services/registry/project_service.py:publish_artifact`, `infra/registry/artifact_store.py` | `irregular` → transaction boundary | State 2 |
| L08 | Artifact types and owner services are two closed sets of five, unrelated to each other (`estimate` by `walls` is accepted). `client_portal_viewer` is refused 422 (kernel R4). | `domain/registry/rules.py`; `rules.artifact_policy` | `unresolved` | State 1 / 2 |
| L09 | Lists answer bare JSON arrays (`project.list`, `project.list_active`, `room.list`, `artifact.list`); the kernel cannot bind them (R5). `config.api.default_page_size`/`max_page_size` are declared but nothing pages. | `api/runtime.py`; `config.api` | `placement` (paging) / `unresolved` (shape) | State 5 / 6 |
| L10 | Orders: projects by `updated_at` desc then id; rooms by name then id; artifacts by type, version desc, id. | stores | `derivable` once stated as rules | State 2 |
| L11 | `project.list_active` repeats `project.list` without archived in another shape (`ProjectReference`); no observed consumer. | `services/registry/project_service.py:list_active_projects` | `unresolved` (who uses it) | State 0 |
| L12 | Room: a name inside a project, not unique, never renamed or removed; listable on an archived project. No observed consumer reads rooms except the kernel test; V1-3 names planner launch context with `room_id`. | `infra/registry/room_store.py` | `unresolved` (who uses it) | State 0 / 1 |
| L13 | `validate` answers `failure` `not_found` or `archived`; any other status also answers `archived` (unreachable under the `CHECK`). | `services/registry/project_service.py:validate_project_reference` | `derivable` | State 2 |
| L14 | Error mapping: `LookupError` → 404 `{"detail"}`, `ValueError` → 422 `{"detail"}`, request validation → 422 with FastAPI's own shape, integrity error → 500. | `api/runtime.py` | `lowering` / `placement` | State 5 / 6 |
| L15 | No authentication or authorization on any route. CORS allows the frontend origin `127.0.0.1:5174`/`localhost:5174`. The kernel sends a credential header nobody checks. | `api/runtime.py` | `unresolved` (trust boundary) | State 0 |
| L16 | Timestamps are timezone-aware UTC, stored as ISO text; `registry_updated_at` is the project's `updated_at`. | `domain/registry/utils.py`, `sqlite_repository.py` | `lowering` | State 6 |
| L17 | `name` and `address` are required strings with no length or uniqueness rule; empty strings pass. | `core/models.py` | `placement` | State 2 |
| L18 | Every read loads the whole table and filters in Python. | stores | `derivable` (backend) | — |
| L19 | SQLite file `data/registry.sqlite3`, `REGISTRY_DB_PATH` override, WAL, foreign keys on; an operator compaction script. | `sqlite_repository.py`, `scripts/compact_registry_db.py` | `placement` (config) / `irregular` (compaction) | State 2 / 3 |
| L20 | The project read answers `{"project": …, "rooms": [...]}`, so a caller reaches the id only through a nested object. | `core/models.py:ProjectResponse` | `unresolved` (public shape) | State 5 |
| L21 | `room.list` on an unknown project answers an empty list; every other project-scoped read answers 404. | `services/registry/project_service.py:list_rooms` | `unresolved` → State 0 drafts "not found" | State 0 |
| L22 | No operation withdraws an artifact pointer; a pointer whose payload was deleted stays `published`. | `infra/registry/artifact_store.py` | `unresolved` | State 0 (OQ-09) |

## Not evidence

Generated `DEPENDENCY_BOUNDARY` notes naming import paths, the repository
fallback helpers (`_repo_get_by_id` and friends) and their tests describe how
the v1 generator was steered, not product behaviour. They are not carried.
