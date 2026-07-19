# State 7 — Classified behavioral notes

## Goal

These notes constrain implementation behavior beyond signatures and prevent trivial, forwarding-only, or placeholder implementations.

The final `global_spec.json` will copy these requirements into its `notes` array using the exact function or method prefix.

Notes use the closed class registry from `SPEC_STANDARD.md`.

---

# 1. Errors

```text
DomainError.__init__: [FIELD_ASSIGNMENT] MUST assign code, message, and entity_id to stable public attributes.
DomainError.__init__: [SCHEMA_CONSTRAINT] MUST reject a blank code or blank message.
DomainError.__init__: [FORBIDDEN_ACTION] MUST NOT derive machine-readable code from exception text.
```

---

# 2. Pydantic model validators

## Values and layout

```text
PropertyValue.validate_source_ref: [SCHEMA_CONSTRAINT] MUST require source_ref when source is object_card.
PropertyValue.validate_source_ref: [FORBIDDEN_ACTION] MUST NOT validate catalog property existence or perform external I/O.
ElementLayout.normalize_rotation: [DETERMINISM_OR_ORDERING] MUST normalize equivalent rotations to one of 0, 90, 180, or 270.
ElementLayout.normalize_rotation: [VALIDATION_ERROR] MUST reject rotations that are not supported increments after normalization.
DiagramLayout.validate_unique_references: [VALIDATION_ERROR] MUST reject duplicate element_id or connection_id layout entries.
DiagramLayout.validate_unique_references: [FORBIDDEN_ACTION] MUST NOT verify engineering entity existence; that belongs to layout policy.
```

## Catalog

```text
ConnectionVisualDefinition.validate_color: [VALIDATION_ERROR] MUST accept only the supported hexadecimal color representation for v1.
PropertyDefinition.validate_value_constraints: [SCHEMA_CONSTRAINT] MUST require default_value and every allowed value to match value_type.
PropertyDefinition.validate_value_constraints: [VALIDATION_ERROR] MUST reject minimum or maximum for non-numeric value types.
PropertyDefinition.validate_value_constraints: [VALIDATION_ERROR] MUST reject minimum greater than maximum.
PropertyDefinition.validate_value_constraints: [VALIDATION_ERROR] MUST reject duplicate allowed values by canonical typed-value identity.
PortDefinition.validate_allowed_connection_codes: [VALIDATION_ERROR] MUST reject duplicate allowed connection type codes.
ElementDefinition.validate_definition_shape: [SCHEMA_CONSTRAINT] MUST require scope_ref for diagram, object, and tenant scopes and forbid it for global scope.
ElementDefinition.validate_definition_shape: [VALIDATION_ERROR] MUST reject duplicate port codes, property codes, or estimation references.
ConnectionTypeDefinition.validate_definition_shape: [SCHEMA_CONSTRAINT] MUST enforce the same scope_ref rules as ElementDefinition.
ConnectionTypeDefinition.validate_definition_shape: [VALIDATION_ERROR] MUST reject duplicate property codes or estimation references.
CatalogSnapshot.validate_unique_definition_refs: [VALIDATION_ERROR] MUST reject duplicate id/version pairs independently for element and connection definitions.
```

## Diagram and application models

```text
Diagram.validate_timestamps: [VALIDATION_ERROR] MUST reject updated_at earlier than created_at.
DiagramElement.validate_unique_properties: [VALIDATION_ERROR] MUST reject duplicate property_code values.
DiagramConnection.validate_connection_shape: [VALIDATION_ERROR] MUST reject identical source and target PortRef values.
DiagramConnection.validate_connection_shape: [VALIDATION_ERROR] MUST reject duplicate property_code values.
DiagramRevision.validate_unique_entities: [VALIDATION_ERROR] MUST reject duplicate element IDs and duplicate connection IDs.
ValidationReport.validate_is_valid: [FIELD_ASSIGNMENT] MUST require is_valid to equal the absence of blocking issues.
WorkingDiagramResult.validate_unique_entities: [VALIDATION_ERROR] MUST reject duplicate working element or connection IDs.
CommitRevisionResult.validate_revision_alignment: [VALIDATION_ERROR] MUST require diagram.id to equal revision.diagram_id and diagram.current_revision to equal revision.revision.
```

## Estimation and change requests

```text
ElementEstimationItem.validate_item_shape: [VALIDATION_ERROR] MUST require a non-empty unique source_element_ids list.
ElementEstimationItem.validate_item_shape: [VALIDATION_ERROR] MUST reject duplicate property codes or estimation references.
ConnectionEstimationItem.validate_item_shape: [VALIDATION_ERROR] MUST require a non-empty unique source_connection_ids list.
ConnectionEstimationItem.validate_item_shape: [VALIDATION_ERROR] MUST reject duplicate property codes or estimation references.
DiagramMeasurement.validate_sources: [VALIDATION_ERROR] MUST require at least one unique source entity ID.
EstimationDataPackage.validate_package_status: [SCHEMA_CONSTRAINT] MUST forbid missing_requirements when status is complete.
EstimationDataPackage.validate_package_status: [FORBIDDEN_ACTION] MUST NOT silently reorder package items during model validation.
DiagramChangeRequest.validate_status_alignment: [SCHEMA_CONSTRAINT] MUST require resulting_revision only when status is applied and forbid it for all other statuses.
```

---

# 3. Catalog lookup and lifecycle

```text
resolve_catalog_snapshot: [VALIDATION_ERROR] MUST raise IntegrityError with the missing definition reference when any requested exact version cannot be resolved.
resolve_catalog_snapshot: [RETURN_SHAPE] MUST return each requested definition exactly once and MUST NOT substitute a newer version.
resolve_catalog_snapshot: [DETERMINISM_OR_ORDERING] MUST return definitions in stable id/version order.
list_available_definitions: [RULE_REFERENCE] MUST apply definition status and scope visibility using = rules.definition_scope_policy.
list_available_definitions: [SECURITY_BOUNDARY] MUST exclude draft definitions unless include_drafts is true and the supplied context permits their scope.
list_available_definitions: [DETERMINISM_OR_ORDERING] MUST return stable code/id/version ordering.
_index_element_definitions: [VALIDATION_ERROR] MUST raise IntegrityError when duplicate element definition id/version pairs are supplied.
_index_connection_definitions: [VALIDATION_ERROR] MUST raise IntegrityError when duplicate connection definition id/version pairs are supplied.
_is_definition_visible: [BEHAVIOR] MUST allow global definitions and context-matching object/diagram definitions according to scope policy.
_is_definition_visible: [FORBIDDEN_ACTION] MUST NOT infer tenant visibility before tenant semantics are defined.
create_element_definition_draft: [FIELD_ASSIGNMENT] MUST set status to draft, preserve the requested scope, assign actor provenance, created_at, definition_id, and version.
create_element_definition_draft: [VALIDATION_ERROR] MUST reject invalid scope_ref combinations and duplicate port/property codes.
create_element_definition_draft: [ORCHESTRATION] MUST validate draft.visual.svg_markup through _validate_element_visual_asset before constructing ElementDefinition.
create_element_definition_draft: [FORBIDDEN_ACTION] MUST NOT activate the definition or overwrite an existing active version.
_validate_element_visual_asset: [BEHAVIOR] MUST return the original SVG markup unchanged only after the complete visual-asset policy passes.
_validate_element_visual_asset: [VALIDATION_ERROR] MUST reject markup containing scripts, event handlers, external references, or foreignObject.
_validate_element_visual_asset: [CONFIG_REFERENCE] MUST enforce the size limit from = config.catalog.max_svg_markup_bytes.
_validate_element_visual_asset: [FORBIDDEN_ACTION] MUST NOT derive ports, properties, or any engineering semantics from the markup.
create_connection_definition_draft: [FIELD_ASSIGNMENT] MUST set status to draft and assign all provenance and version fields.
create_connection_definition_draft: [VALIDATION_ERROR] MUST reject invalid scope_ref combinations and duplicate property codes.
_validate_draft_scope: [RULE_REFERENCE] MUST enforce = rules.definition_scope_policy.
_validate_element_draft_uniqueness: [VALIDATION_ERROR] MUST reject duplicate port codes, property codes, and estimation refs.
_validate_connection_draft_uniqueness: [VALIDATION_ERROR] MUST reject duplicate property codes and estimation refs.
transition_definition_status: [RULE_REFERENCE] MUST enforce = rules.definition_status_transitions.
transition_definition_status: [SECURITY_BOUNDARY] MUST require allow_global_activation for activation of a global definition.
transition_definition_status: [PROVENANCE] MUST preserve definition identity, version, creator, and creation time.
transition_definition_status: [FORBIDDEN_ACTION] MUST NOT mutate the input definition in place.
_validate_definition_transition: [VALIDATION_ERROR] MUST raise DomainError for transitions outside the declared lifecycle.
_validate_activation_authority: [SECURITY_BOUNDARY] MUST reject global activation when allow_global_activation is false.
```

---

# 4. Diagram policy

```text
validate_property_values: [RETURN_SHAPE] MUST return stable ValidationIssue records for unknown, missing, duplicate, type-invalid, disallowed, or out-of-range properties.
validate_property_values: [RULE_REFERENCE] MUST apply required_for_authoring or required_for_estimation according to the supplied ValidationStage.
validate_property_values: [DETERMINISM_OR_ORDERING] MUST return issues in stable code/entity/property order.
validate_property_value: [VALIDATION_ERROR] MUST emit a blocking issue when type, allowed-values, or numeric-bound validation fails.
_matches_property_type: [BEHAVIOR] MUST compare the TypedValue discriminator to PropertyDefinition.value_type without coercion.
_is_allowed_value: [BEHAVIOR] MUST use canonical typed-value equality and treat an empty allowed_values list as unrestricted.
_is_within_numeric_bounds: [BEHAVIOR] MUST apply bounds only to integer and decimal values.
validate_connection: [VALIDATION_ERROR] MUST report missing elements, missing ports, missing connection definition, incompatible endpoints, multiplicity violations, and invalid properties.
validate_connection: [RULE_REFERENCE] MUST evaluate checks in = rules.connection_compatibility order.
validate_connection: [FORBIDDEN_ACTION] MUST NOT infer ports from layout handles or React Flow data.
validate_connection_compatibility: [RULE_REFERENCE] MUST apply = rules.medium_compatibility and = rules.flow_compatibility.
_validate_medium_compatibility: [FALLBACK] MUST allow unspecified media only at draft stage through caller policy and MUST NOT classify it as fully estimation-ready.
_validate_flow_compatibility: [VALIDATION_ERROR] MUST reject inlet-to-inlet and outlet-to-outlet and other explicitly forbidden pairs.
_validate_port_multiplicity: [RULE_REFERENCE] MUST enforce = rules.port_multiplicity and reject a second connection on a single-use port.
validate_definition_use: [RULE_REFERENCE] MUST enforce status and scope visibility for the supplied object_id, diagram_id, and stage.
validate_definition_use: [RETURN_SHAPE] MUST return a blocking issue rather than a boolean when use is forbidden.
validate_working_diagram: [ORCHESTRATION] MUST validate all elements before connections so connection findings can rely on a complete element index.
validate_working_diagram: [RETURN_SHAPE] MUST aggregate all non-fatal findings into one ValidationReport.
validate_working_diagram: [DETERMINISM_OR_ORDERING] MUST sort findings stably.
_build_element_index: [VALIDATION_ERROR] MUST raise IntegrityError on duplicate IDs rather than overwriting an earlier element.
_build_connection_usage: [FIELD_ASSIGNMENT] MUST count both endpoints of every connection by element_id and port_code.
_sort_validation_issues: [DETERMINISM_OR_ORDERING] MUST sort by severity, code, entity type, entity id, and property code using a fixed order.
```

---

# 5. Layout

```text
validate_layout: [RETURN_SHAPE] MUST report unknown element references, unknown connection references, duplicate entries, invalid viewport, and route-point limit violations.
validate_layout: [CONFIG_REFERENCE] MUST enforce max route points from = config.layout.max_route_points_per_connection.
validate_layout: [FORBIDDEN_ACTION] MUST NOT treat layout coordinates or route points as physical measurements.
normalize_layout: [DETERMINISM_OR_ORDERING] MUST normalize rotations and preserve stable element and connection ordering.
normalize_layout: [FORBIDDEN_ACTION] MUST NOT add or delete engineering entities.
create_default_layout: [DETERMINISM_OR_ORDERING] MUST produce the same placement for the same ordered elements, connections, and catalog.
create_default_layout: [FALLBACK] MUST create presentation-only placement when authoring data has no supplied layout.
_normalize_element_layout: [FIELD_PROJECTION] MUST preserve element_id while normalizing only presentation fields.
_normalize_connection_layout: [FIELD_PROJECTION] MUST preserve connection_id and route point order.
_validate_layout_references: [VALIDATION_ERROR] MUST emit blocking issues for layout references absent from the engineering snapshot.
```

---

# 6. Diagram authoring

```text
create_diagram: [FIELD_ASSIGNMENT] MUST set status to draft, current_revision to 0, and created_at/updated_at to the supplied created_at.
create_diagram: [VALIDATION_ERROR] MUST reject an empty system_kinds set and values outside DiagramSystemKind.
create_diagram: [PROVENANCE] MUST assign created_by from the supplied ActorRef.
create_diagram: [FORBIDDEN_ACTION] MUST NOT copy customer or object-card fields beyond object_id.
change_diagram_status: [RULE_REFERENCE] MUST enforce = rules.diagram_status_transitions.
change_diagram_status: [FORBIDDEN_ACTION] MUST NOT reactivate archived diagrams in v1.
change_diagram_status: [FIELD_ASSIGNMENT] MUST preserve identity and creation fields and update only status and updated_at.
apply_authoring_command: [ORCHESTRATION] MUST dispatch exclusively by the discriminated command_type.
apply_authoring_command: [RETURN_SHAPE] MUST return a complete WorkingDiagramResult containing elements, connections, layout, revision_base, and validation.
apply_authoring_command: [FORBIDDEN_ACTION] MUST NOT mutate the base revision or command model.
apply_authoring_commands: [BEHAVIOR] MUST apply commands sequentially to an in-memory working result.
apply_authoring_commands: [VALIDATION_ERROR] MUST raise DomainError and return no partial result when a command cannot be structurally applied.
apply_authoring_commands: [DETERMINISM_OR_ORDERING] MUST preserve command order exactly.
_add_element: [VALIDATION_ERROR] MUST reject duplicate element_id and unresolved or unusable DefinitionRef.
_add_element: [FIELD_ASSIGNMENT] MUST append the new element and optional layout without changing existing instances.
_set_element_properties: [FIELD_ASSIGNMENT] MUST replace only the supplied property codes and preserve all other properties.
_set_element_properties: [VALIDATION_ERROR] MUST reject an unknown element_id.
_remove_element: [BEHAVIOR] MUST remove the element, all attached connections, and all matching layout entries in one pure operation.
_remove_element: [VALIDATION_ERROR] MUST reject an unknown element_id.
_add_connection: [VALIDATION_ERROR] MUST reject duplicate connection_id and unresolved connection definition.
_set_connection_properties: [FIELD_ASSIGNMENT] MUST replace only supplied property codes and preserve all others.
_set_connection_properties: [VALIDATION_ERROR] MUST reject an unknown connection_id.
_remove_connection: [BEHAVIOR] MUST remove the connection and its layout entry.
_remove_connection: [VALIDATION_ERROR] MUST reject an unknown connection_id.
_create_empty_working_result: [RETURN_SHAPE] MUST create revision_base 0 with empty engineering collections, a valid default viewport, and a validation report consistent with empty draft policy.
_create_working_result_from_revision: [FIELD_PROJECTION] MUST copy revision data into new lists/models without mutating the immutable revision.
_apply_layout_command: [FIELD_ASSIGNMENT] MUST replace working_layout only and preserve engineering collections.
```

---

# 7. Revision commit

```text
commit_revision: [ORCHESTRATION] MUST perform concurrency check, revision construction, append, diagram advance, and commit inside one UnitOfWork.
commit_revision: [VALIDATION_ERROR] MUST reject working results with blocking validation issues.
commit_revision: [DETERMINISM_OR_ORDERING] MUST assign next revision as expected_current_revision + 1.
commit_revision: [FORBIDDEN_ACTION] MUST NOT call Object Card, MCP, LLM, estimator, or other network services while the transaction is open.
commit_revision: [FORBIDDEN_ACTION] MUST NOT update or delete an existing revision row.
commit_revision: [FALLBACK] MUST roll back the UnitOfWork on any exception before re-raising a domain or persistence error.
_validate_expected_revision: [VALIDATION_ERROR] MUST raise ConflictError when diagram.current_revision differs from expected_current_revision.
_build_revision: [FIELD_ASSIGNMENT] MUST use working elements, connections, and layout and assign the supplied actor, source, timestamp, schema version, and summary.
_build_revision: [PROVENANCE] MUST preserve exact actor and change_source.
_advance_diagram_revision: [FIELD_ASSIGNMENT] MUST set current_revision to the committed revision and updated_at to revision.created_at.
```

---

# 8. Estimation-data generation units

## Element and connection items

```text
collect_element_items: [BEHAVIOR] MUST group only elements with equal definition id/version and equal estimator-relevant property values.
collect_element_items: [FIELD_ASSIGNMENT] MUST sum DiagramElement.quantity and preserve unique source_element_ids.
collect_element_items: [FIELD_PROJECTION] MUST project name from the pinned definition version and assign unit_code, defaulting to the count unit defined by = rules.estimation_collection_policy.
collect_element_items: [DETERMINISM_OR_ORDERING] MUST return stable group-key order.
build_element_group_key: [DETERMINISM_OR_ORDERING] MUST use canonical typed-value serialization and exclude provenance-only fields.
_select_estimator_properties: [MODEL_REFERENCE] MUST select only properties whose definitions have required_for_estimation or another explicit estimation relevance rule in = models.PropertyDefinition.
_merge_element_group: [FIELD_ASSIGNMENT] MUST return a new item with summed quantity and sorted unique source IDs.
collect_connection_items: [BEHAVIOR] MUST group only connections with equal definition id/version, quantity unit, and estimator-relevant property values.
collect_connection_items: [FIELD_PROJECTION] MUST project name from the pinned connection type definition version.
collect_connection_items: [FORBIDDEN_ACTION] MUST NOT derive length from DiagramLayout in v1.
collect_connection_items: [DETERMINISM_OR_ORDERING] MUST return stable group-key order.
build_connection_group_key: [DETERMINISM_OR_ORDERING] MUST include definition id, version, quantity unit, and canonical estimator-property identity.
_resolve_connection_quantity: [BEHAVIOR] MUST use explicit validated connection properties or count semantics defined by the connection definition.
_resolve_connection_quantity: [FALLBACK] MUST return no invented physical length when the required explicit value is missing; completeness is handled by requirements analysis.
_merge_connection_group: [FIELD_ASSIGNMENT] MUST sum quantity and preserve sorted unique source IDs.
```

## Measurements and requirements

```text
collect_measurements: [ORCHESTRATION] MUST combine only enabled measurement methods from = rules.estimation_collection_policy.
collect_measurements: [FORBIDDEN_ACTION] MUST NOT call any layout_route_length implementation in v1.
build_count_measurements: [PROVENANCE] MUST list all source entity IDs contributing to each count.
build_property_sum_measurements: [VALIDATION_ERROR] MUST ignore no invalid values silently; invalid property values must produce an invalid package through prior validation.
build_property_sum_measurements: [DETERMINISM_OR_ORDERING] MUST aggregate only equal measurement code and unit groups.
build_explicit_property_measurements: [FIELD_PROJECTION] MUST preserve explicit source property provenance.
analyze_estimation_requirements: [ORCHESTRATION] MUST combine element and connection requirements, deduplicate them, and sort them.
analyze_estimation_requirements: [FORBIDDEN_ACTION] MUST NOT generate suggested values unless an explicit catalog default exists.
find_missing_element_requirements: [MODEL_REFERENCE] MUST inspect PropertyDefinition.required_for_estimation from the pinned ElementDefinition version.
find_missing_connection_requirements: [MODEL_REFERENCE] MUST inspect PropertyDefinition.required_for_estimation from the pinned ConnectionTypeDefinition version.
_deduplicate_requirements: [DETERMINISM_OR_ORDERING] MUST deduplicate by stable code, entity type, entity id, and property code.
_sort_requirements: [DETERMINISM_OR_ORDERING] MUST use fixed code/entity/property ordering.
```

## Assembly and facade

```text
build_estimation_data: [ORCHESTRATION] MUST validate the revision, analyze requirements, collect grouped items and measurements, determine status, and assemble one package.
build_estimation_data: [VALIDATION_ERROR] MUST produce status invalid for broken diagram integrity and status incomplete for missing estimator data on an otherwise valid diagram.
build_estimation_data: [DETERMINISM_OR_ORDERING] MUST produce semantically identical content for the same revision, pinned definitions, and collector_rule_version, excluding package_id and generated_at.
build_estimation_data: [FORBIDDEN_ACTION] MUST NOT mutate the diagram, revision, catalog, database, prices, retailer products, or estimate records.
_determine_package_status: [BEHAVIOR] MUST return invalid when validation has blocking integrity issues, incomplete when requirements are non-empty, otherwise complete.
assemble_estimation_package: [FIELD_ASSIGNMENT] MUST populate object_id from Diagram and diagram_id/revision/schema_version from DiagramRevision.
assemble_estimation_package: [PROVENANCE] MUST retain source IDs in every grouped item and measurement.
assemble_estimation_package: [DETERMINISM_OR_ORDERING] MUST sort all item, measurement, requirement, and warning collections before model construction.
_sort_element_items: [DETERMINISM_OR_ORDERING] MUST sort by definition id, version, canonical property identity, and source IDs.
_sort_connection_items: [DETERMINISM_OR_ORDERING] MUST sort by definition id, version, unit, canonical property identity, and source IDs.
_sort_measurements: [DETERMINISM_OR_ORDERING] MUST sort by code, unit, method, and source IDs.
```

---

# 9. Change requests

```text
create_change_request: [FIELD_ASSIGNMENT] MUST create status open, preserve base_revision, requester provenance, reason, and all typed changes.
create_change_request: [VALIDATION_ERROR] MUST reject an empty changes list.
transition_change_request: [RULE_REFERENCE] MUST enforce the declared change-request status transitions.
transition_change_request: [SCHEMA_CONSTRAINT] MUST require resulting_revision when target status is applied.
transition_change_request: [FORBIDDEN_ACTION] MUST NOT apply diagram mutations itself.
_validate_change_request_transition: [VALIDATION_ERROR] MUST raise DomainError for unsupported transitions.
```

---

# 10. Repository and UnitOfWork protocols

```text
DiagramRepository.get: [RETURN_SHAPE] MUST return None only when the diagram does not exist.
DiagramRepository.save: [FORBIDDEN_ACTION] MUST NOT commit the session independently when used inside a UnitOfWork.
DiagramRepository.list_by_object_id: [SECURITY_BOUNDARY] MUST filter strictly by the supplied object_id.
DiagramRepository.list_by_object_id: [DETERMINISM_OR_ORDERING] MUST use stable updated_at/id ordering and cursor semantics.
RevisionRepository.get: [MODEL_REFERENCE] MUST validate loaded JSONB as = models.DiagramRevision before returning it.
RevisionRepository.get_current: [BEHAVIOR] MUST resolve the current revision indicated by Diagram.current_revision and return None only for revision 0.
RevisionRepository.append: [FORBIDDEN_ACTION] MUST NOT overwrite an existing diagram_id/revision pair.
CatalogRepository.get_element_definition: [MODEL_REFERENCE] MUST validate payload as = models.ElementDefinition.
CatalogRepository.get_connection_definition: [MODEL_REFERENCE] MUST validate payload as = models.ConnectionTypeDefinition.
CatalogRepository.list_visible_definitions: [RULE_REFERENCE] MUST implement the same visibility semantics as = rules.definition_scope_policy.
ChangeRequestRepository.get: [MODEL_REFERENCE] MUST validate payload as = models.DiagramChangeRequest.
UnitOfWork.__enter__: [BEHAVIOR] MUST begin or bind one short database transaction.
UnitOfWork.__exit__: [FALLBACK] MUST roll back when exc is not None and MUST NOT suppress unexpected exceptions.
UnitOfWork.commit: [BEHAVIOR] MUST commit exactly the active transaction.
UnitOfWork.rollback: [BEHAVIOR] MUST safely roll back the active transaction and leave the session reusable or closable.
```

---

# 11. External ports and application use cases

```text
CapabilityAuthorizer.require_capability: [SECURITY_BOUNDARY] MUST raise AuthorizationError when the actor lacks the exact requested capability for the resource.
CapabilityAuthorizer.require_capability: [FORBIDDEN_ACTION] MUST NOT silently downgrade an authoring request to read capability.
DisabledObjectGateway.verify_object_exists: [FALLBACK] MUST accept a non-blank object_id without inventing object fields when verification is disabled.
create_diagram_use_case: [SECURITY_BOUNDARY] MUST require diagram.author before persistence.
create_diagram_use_case: [ORCHESTRATION] MUST optionally verify object existence before creating and saving the diagram.
get_diagram_workspace: [SECURITY_BOUNDARY] MUST require diagram.read.
get_diagram_workspace: [RETURN_SHAPE] MUST return diagram, current revision, exact referenced catalog, and currently available definitions without React Flow objects.
list_object_diagrams: [CONFIG_REFERENCE] MUST enforce page size using = config.api.max_page_size.
change_diagram_status_use_case: [SECURITY_BOUNDARY] MUST require diagram.archive for archival.
apply_diagram_command_use_case: [SECURITY_BOUNDARY] MUST require diagram.author.
apply_diagram_command_use_case: [VALIDATION_ERROR] MUST reject a base_revision that is not the requested diagram revision.
apply_diagram_commands_use_case: [DETERMINISM_OR_ORDERING] MUST preserve supplied command order.
commit_diagram_revision_use_case: [SECURITY_BOUNDARY] MUST require diagram.author.
commit_diagram_revision_use_case: [ORCHESTRATION] MUST resolve exact catalog definitions and run commit-stage validation before calling commit_revision.
commit_diagram_revision_use_case: [ORCHESTRATION] MUST call ObjectGateway.publish_diagram_index after the commit transaction succeeds.
commit_diagram_revision_use_case: [FALLBACK] MUST log a failed index publication and return the successful commit result unchanged.
list_available_definitions_use_case: [SECURITY_BOUNDARY] MUST require catalog.read.
create_element_definition_draft_use_case: [SECURITY_BOUNDARY] MUST require catalog.draft.create.
create_connection_definition_draft_use_case: [SECURITY_BOUNDARY] MUST require catalog.draft.create.
transition_definition_status_use_case: [SECURITY_BOUNDARY] MUST require the capability appropriate to local or global activation.
build_diagram_estimation_data: [SECURITY_BOUNDARY] MUST require estimation.read.
build_diagram_estimation_data: [ORCHESTRATION] MUST load one explicit revision or the current revision, resolve exact definitions, and call the canonical builder.
build_diagram_estimation_data: [FORBIDDEN_ACTION] MUST NOT implement separate HTTP/MCP grouping logic.
inspect_estimation_source: [SECURITY_BOUNDARY] MUST require estimation.read.
inspect_estimation_source: [RETURN_SHAPE] MUST return only the requested source entity or its exact pinned definition.
```

---

# 12. PostgreSQL infrastructure

```text
create_engine_from_settings: [CONFIG_REFERENCE] MUST use pool size, overflow, timeout, statement timeout, and connect timeout from = config.database.
create_engine_from_settings: [FORBIDDEN_ACTION] MUST NOT disable PostgreSQL autovacuum or execute maintenance SQL.
create_session_factory: [BEHAVIOR] MUST create sessions with explicit transaction ownership and no silent autocommit.
serialize_diagram_revision: [MODEL_REFERENCE] MUST serialize using DiagramRevision.model_dump in canonical JSON-compatible mode.
deserialize_diagram_revision: [MODEL_REFERENCE] MUST call DiagramRevision.model_validate and raise PersistenceError on invalid stored payload.
serialize_element_definition: [MODEL_REFERENCE] MUST serialize the complete validated ElementDefinition without ORM-only fields.
deserialize_element_definition: [MODEL_REFERENCE] MUST validate the payload as ElementDefinition.
serialize_connection_definition: [MODEL_REFERENCE] MUST serialize the complete validated ConnectionTypeDefinition.
deserialize_connection_definition: [MODEL_REFERENCE] MUST validate the payload as ConnectionTypeDefinition.
SqlAlchemyDiagramRepository.__init__: [DEPENDENCY_BOUNDARY] MUST accept an existing Session and MUST NOT create its own engine or session.
SqlAlchemyRevisionRepository.append: [VALIDATION_ERROR] MUST surface duplicate primary key insertion as ConflictError or PersistenceError with a stable code.
SqlAlchemyUnitOfWork.__exit__: [FALLBACK] MUST rollback on exceptions and close owned transaction resources.
```

---

# 13. Placeholder resistance result

The following trivial implementations must violate these notes:

```text
return None
return []
return {}
return input
return EstimationDataPackage(...empty...)
blind forwarding to repository
manual dict assembly in HTTP or MCP
silent acceptance of unknown fields
silent use of latest catalog definition
```

The notes intentionally define observable assignments, validation outcomes, provenance, ordering, forbidden behavior, and side effects so that an implementation cannot satisfy the specification with a skeleton.

# 14. Positive coverage for the factory underspec gate (2026-07-15)

The factory's generation-stage `spec_underspec_gate` requires every owned
function contract to carry at least one direct positive `[BEHAVIOR]` or
`[FIELD_PROJECTION]` note; validation, ordering, and forbidden-action notes
alone do not satisfy it. The assembled specification therefore includes a
positive note per owned function stating what a correct result contains —
projections name their sources, orchestrators name the operation whose
result they return, serializers pin round-trip equality. These notes add no
new product behavior; they restate already-decided semantics in the marker
form the generation gate consumes.

## State 7 readiness assessment

The specification is ready for assembly when:

- optional v1 capabilities are explicitly included or removed;
- remaining unresolved external models are represented only through disabled adapters;
- module functions and imports are reconciled against these notes;
- every included contract has at least one classified note;
- the final JSON contains no functions that can be implemented as a no-op without contradiction.
