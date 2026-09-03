from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from box_composition import compile_composition, execute_composition
from box_derivability import BoxDerivabilityError, load_definition


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments" / "cabinet-vault" / "registry_project_box_v0.yaml"
TARGET = ROOT / "experiments" / "cabinet-vault" / "cabinet_registry_context_box_v0.yaml"


def definitions():
    return load_definition(SOURCE), load_definition(TARGET)


def compile_registry_to_cabinet(source=None, target=None):
    if source is None or target is None:
        source, target = definitions()
    return compile_composition(
        source,
        "project.observe",
        target,
        "project.catalogue_observation.accept",
    )


def test_compiler_emits_source_projection_target_graph_from_manifests_only():
    plan = compile_registry_to_cabinet()

    assert plan.status == "derived"
    assert plan.derivation.gaps == ()
    assert [(node.id, node.operator, node.capability) for node in plan.nodes] == [
        ("source", "invoke_capability", "project.observe"),
        ("projection", "exact_project", None),
        (
            "target",
            "invoke_capability",
            "project.catalogue_observation.accept",
        ),
    ]
    assert len(plan.plan_digest) == 64


def test_execution_uses_compiled_projection_without_hand_written_adapter():
    plan = compile_registry_to_cabinet()
    calls: list[tuple[str, str, dict[str, object]]] = []

    def source_invoke(capability, args):
        calls.append(("source", capability, args))
        return {
            "id": "project-17",
            "name": "Casa Norte",
            "address": "Calle 17",
            "status": "active",
            "updated_at": "2026-08-20T14:15:00Z",
            "provider_only_debug_value": "must not cross",
        }

    def target_invoke(capability, args):
        calls.append(("target", capability, args))
        return {"snapshot_id": "snapshot-1", **args}

    execution = execute_composition(plan, source_invoke, target_invoke)

    assert calls[0] == ("source", "project.observe", {})
    assert calls[1] == (
        "target",
        "project.catalogue_observation.accept",
        {
            "project_id": "project-17",
            "display_name": "Casa Norte",
            "address": "Calle 17",
            "status": "active",
            "catalogue_updated_at": "2026-08-20T14:15:00Z",
        },
    )
    assert "provider_only_debug_value" not in calls[1][2]
    assert execution.result["snapshot_id"] == "snapshot-1"
    assert [item["node"] for item in execution.trace] == ["source", "projection", "target"]


def test_unresolved_composition_fails_before_invoking_either_box():
    source, target = definitions()
    broken = deepcopy(source)
    broken["schemas"]["RegistryProject"]["fields"]["status"].pop("semantic")
    plan = compile_registry_to_cabinet(broken, target)
    calls: list[str] = []

    def source_invoke(_capability, _args):
        calls.append("source")
        return {}

    def target_invoke(_capability, _args):
        calls.append("target")
        return {}

    assert plan.status == "unresolved"
    with pytest.raises(BoxDerivabilityError, match="cannot execute an unresolved composition"):
        execute_composition(plan, source_invoke, target_invoke)
    assert calls == []


def test_compiled_plan_is_stable_for_identical_manifests():
    source, target = definitions()

    first = compile_registry_to_cabinet(source, target)
    second = compile_registry_to_cabinet(deepcopy(source), deepcopy(target))

    assert first == second
    assert first.plan_digest == second.plan_digest


def test_source_field_rename_changes_projection_path_not_semantic_result():
    source, target = definitions()
    renamed = deepcopy(source)
    fields = renamed["schemas"]["RegistryProject"]["fields"]
    fields["project_key"] = fields.pop("id")

    plan = compile_registry_to_cabinet(renamed, target)

    assert plan.status == "derived"
    mapping = {step.target_path: step.source_path for step in plan.derivation.mapping}
    assert mapping["ProjectCatalogueObservation.project_id"] == "RegistryProject.project_key"
