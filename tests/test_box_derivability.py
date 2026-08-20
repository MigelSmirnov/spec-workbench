from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from box_derivability import derive_capability_mapping, load_definition


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments" / "cabinet-vault" / "registry_project_box_v0.yaml"
TARGET = ROOT / "experiments" / "cabinet-vault" / "cabinet_registry_context_box_v0.yaml"
TARGET_CAPABILITY = "project.catalogue_observation.accept"


def definitions():
    return load_definition(SOURCE), load_definition(TARGET)


def test_registry_to_cabinet_mapping_is_derived_only_from_declared_semantics():
    source, target = definitions()

    report = derive_capability_mapping(
        source,
        "project.observe",
        target,
        TARGET_CAPABILITY,
    )

    assert report.status == "derived"
    assert report.gaps == ()
    assert [
        (step.source_path, step.target_path, step.semantic)
        for step in report.mapping
    ] == [
        ("RegistryProject.id", "ProjectCatalogueObservation.project_id", "project.identity"),
        (
            "RegistryProject.name",
            "ProjectCatalogueObservation.display_name",
            "project.display_name",
        ),
        ("RegistryProject.address", "ProjectCatalogueObservation.address", "project.address"),
        (
            "RegistryProject.status",
            "ProjectCatalogueObservation.status",
            "project.catalogue.status",
        ),
        (
            "RegistryProject.updated_at",
            "ProjectCatalogueObservation.catalogue_updated_at",
            "project.catalogue.updated_at",
        ),
    ]


def test_cabinet_contract_does_not_name_the_source_product_in_its_semantic_surface():
    _, target = definitions()

    semantic_surface = str(target["schemas"]) + str(target["capabilities"])
    assert "Registry" not in semantic_surface
    assert target["external_dependencies"] == []


def test_field_names_are_not_used_as_mapping_evidence():
    source, target = definitions()
    renamed = deepcopy(source)
    fields = renamed["schemas"]["RegistryProject"]["fields"]
    fields["registry_project_key"] = fields.pop("id")
    fields["label"] = fields.pop("name")

    report = derive_capability_mapping(
        renamed,
        "project.observe",
        target,
        TARGET_CAPABILITY,
    )

    assert report.status == "derived"
    mapping = {step.target_path: step.source_path for step in report.mapping}
    assert mapping["ProjectCatalogueObservation.project_id"] == "RegistryProject.registry_project_key"
    assert mapping["ProjectCatalogueObservation.display_name"] == "RegistryProject.label"


def test_same_name_and_type_without_semantic_id_is_an_unresolved_gap():
    source, target = definitions()
    broken = deepcopy(source)
    source_status = broken["schemas"]["RegistryProject"]["fields"]["status"]
    source_status.pop("semantic")

    report = derive_capability_mapping(
        broken,
        "project.observe",
        target,
        TARGET_CAPABILITY,
    )

    assert report.status == "unresolved"
    assert [gap.code for gap in report.gaps] == ["SEMANTIC_NOT_DECLARED"]
    assert report.gaps[0].target_path == "ProjectCatalogueObservation.status"
    assert report.gaps[0].candidates == ("RegistryProject.status",)


def test_matching_semantic_and_type_cannot_cross_an_authority_mismatch():
    source, target = definitions()
    broken = deepcopy(source)
    broken["schemas"]["RegistryProject"]["fields"]["status"]["authority"] = "agent.inferred"

    report = derive_capability_mapping(
        broken,
        "project.observe",
        target,
        TARGET_CAPABILITY,
    )

    assert report.status == "unresolved"
    assert [gap.code for gap in report.gaps] == ["AUTHORITY_MISMATCH"]


def test_target_must_describe_its_own_semantic_need():
    source, target = definitions()
    broken = deepcopy(target)
    target_field = broken["schemas"]["ProjectCatalogueObservation"]["fields"]["address"]
    target_field.pop("semantic")

    report = derive_capability_mapping(
        source,
        "project.observe",
        broken,
        TARGET_CAPABILITY,
    )

    assert report.status == "unresolved"
    assert [gap.code for gap in report.gaps] == ["TARGET_FIELD_NOT_SELF_DESCRIBING"]


def test_v0_rejects_a_mapping_that_requires_an_undeclared_transformation():
    source, target = definitions()
    broken = deepcopy(target)
    broken["schemas"]["ProjectCatalogueObservation"]["fields"]["display_name"][
        "mapping"
    ] = "normalize"

    report = derive_capability_mapping(
        source,
        "project.observe",
        broken,
        TARGET_CAPABILITY,
    )

    assert report.status == "unresolved"
    assert [gap.code for gap in report.gaps] == ["UNSUPPORTED_TRANSFORMATION"]
