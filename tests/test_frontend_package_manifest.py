from __future__ import annotations

import json
from pathlib import Path

import pytest

from frontend_package_manifest import (
    ManifestError,
    build_manifest,
    canonical_manifest_bytes,
    write_manifest,
)


def _write_package(
    root: Path,
    *,
    index_source: str | None = None,
    capability_overrides: dict | None = None,
) -> Path:
    package_dir = root / "building-layer"
    package_dir.mkdir()
    (package_dir / "package.json").write_text(
        json.dumps({"name": "@planner/building-layer", "version": "0.1.0"}),
        encoding="utf-8",
    )
    (package_dir / "index.ts").write_text(
        index_source
        or """
export { wallCreateCommand, wallRenderer, wallSnapProvider, wallHitTestProvider,
         wallAnchorProvider, projectBuildingScene, buildingLayerDefinition }
  from "./public-api";
""".strip()
        + "\n",
        encoding="utf-8",
    )

    capabilities = {
        "building.scene.project": {
            "kind": "projection",
            "implementation": {"export": "projectBuildingScene"},
            "requires": [],
        },
        "building.wall.scene2d": {
            "kind": "renderer",
            "implementation": {"export": "wallRenderer"},
            "requires": ["building.scene.project"],
            "allowed_layer_modes": ["draft", "owned", "reference"],
            "renderer_slot": {"projection": "building.wall", "family": "scene2d"},
        },
        "building.wall.snap": {
            "kind": "snap_provider",
            "implementation": {"export": "wallSnapProvider"},
            "requires": ["building.scene.project"],
            "allowed_layer_modes": ["reference", "owned", "draft"],
            "snap_kinds": ["intersection", "endpoint", "axis", "midpoint"],
        },
        "building.wall.hit_test": {
            "kind": "hit_test_provider",
            "implementation": {"export": "wallHitTestProvider"},
            "requires": ["building.scene.project"],
        },
        "building.wall.anchors": {
            "kind": "anchor_provider",
            "implementation": {"export": "wallAnchorProvider"},
            "requires": ["building.scene.project"],
        },
        "building.wall.create": {
            "kind": "command",
            "implementation": {"export": "wallCreateCommand"},
            "requires": [],
            "allowed_layer_modes": ["draft", "owned"],
            "history": "commit",
            "undo": "inverse",
            "input_type": "WallCreateInput",
            "output_type": "BuildingEditResult",
        },
    }
    if capability_overrides:
        for capability_id, value in capability_overrides.items():
            if value is None:
                capabilities.pop(capability_id, None)
            else:
                capabilities[capability_id] = value

    declarations = {
        "kind": "frontend_package_declarations",
        "schema_version": 1,
        "package": {"role": "layer"},
        "requires": {
            "packages": [
                "@factory/editor-scene",
                "@factory/editor-core",
                "@factory/editor-geometry",
            ],
            "runtime_capabilities": [],
        },
        "provides": {
            "capabilities": capabilities,
            "layers": {
                "building": {
                    "implementation": {"export": "buildingLayerDefinition"},
                    "supported_modes": ["draft", "owned", "reference"],
                    "default_capabilities": {
                        "projection": "building.scene.project",
                        "renderers": ["building.wall.scene2d"],
                        "hit_test": ["building.wall.hit_test"],
                        "anchors": ["building.wall.anchors"],
                        "snap": ["building.wall.snap"],
                    },
                }
            },
        },
        "irregular_exports": {},
    }
    (package_dir / "frontend-package-declarations.json").write_text(
        json.dumps(declarations),
        encoding="utf-8",
    )
    return package_dir


def test_manifest_generation_is_byte_deterministic(tmp_path: Path) -> None:
    package_dir = _write_package(tmp_path)

    first = build_manifest(package_dir)
    second = build_manifest(package_dir)

    assert first["manifest_hash"] == second["manifest_hash"]
    assert canonical_manifest_bytes(first) == canonical_manifest_bytes(second)

    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    write_manifest(first, first_path)
    write_manifest(second, second_path)
    assert first_path.read_bytes() == second_path.read_bytes()

    assert list(first["provides"]["capabilities"]) == sorted(
        first["provides"]["capabilities"]
    )
    assert first["requires"]["packages"] == sorted(first["requires"]["packages"])
    assert first["provides"]["capabilities"]["building.wall.create"][
        "allowed_layer_modes"
    ] == ["draft", "owned"]


def test_removed_public_export_blocks_manifest_rebuild(tmp_path: Path) -> None:
    package_dir = _write_package(tmp_path)
    build_manifest(package_dir)

    (package_dir / "index.ts").write_text(
        """
export { wallRenderer, wallSnapProvider, wallHitTestProvider,
         wallAnchorProvider, projectBuildingScene, buildingLayerDefinition }
  from "./public-api";
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="wallCreateCommand"):
        build_manifest(package_dir)


def test_missing_public_export_blocks_first_build(tmp_path: Path) -> None:
    package_dir = _write_package(
        tmp_path,
        index_source='export { buildingLayerDefinition } from "./public-api";\n',
    )

    with pytest.raises(ManifestError, match="projectBuildingScene|wallCreateCommand"):
        build_manifest(package_dir)


def test_snapshot_requires_layer_scope(tmp_path: Path) -> None:
    package_dir = _write_package(
        tmp_path,
        capability_overrides={
            "building.wall.create": {
                "kind": "command",
                "implementation": {"export": "wallCreateCommand"},
                "requires": [],
                "allowed_layer_modes": ["owned"],
                "history": "commit",
                "undo": "snapshot",
            }
        },
    )

    with pytest.raises(ManifestError, match="snapshot_scope"):
        build_manifest(package_dir)


def test_snapshot_layer_scope_is_accepted(tmp_path: Path) -> None:
    package_dir = _write_package(
        tmp_path,
        capability_overrides={
            "building.wall.create": {
                "kind": "command",
                "implementation": {"export": "wallCreateCommand"},
                "requires": [],
                "allowed_layer_modes": ["owned"],
                "history": "commit",
                "undo": "snapshot",
                "snapshot_scope": "layer",
            }
        },
    )

    manifest = build_manifest(package_dir)
    command = manifest["provides"]["capabilities"]["building.wall.create"]
    assert command["undo"] == "snapshot"
    assert command["snapshot_scope"] == "layer"


def test_reference_command_is_rejected(tmp_path: Path) -> None:
    package_dir = _write_package(
        tmp_path,
        capability_overrides={
            "building.wall.create": {
                "kind": "command",
                "implementation": {"export": "wallCreateCommand"},
                "requires": [],
                "allowed_layer_modes": ["reference"],
                "history": "commit",
                "undo": "inverse",
            }
        },
    )

    with pytest.raises(ManifestError, match="owned,draft"):
        build_manifest(package_dir)


def test_declared_for_later_kind_is_rejected(tmp_path: Path) -> None:
    package_dir = _write_package(
        tmp_path,
        capability_overrides={
            "building.measure": {
                "kind": "selector",
                "implementation": {"export": "wallCreateCommand"},
                "requires": [],
            }
        },
    )

    with pytest.raises(ManifestError, match="not v1-implemented"):
        build_manifest(package_dir)


def test_wildcard_public_export_is_rejected_fail_closed(tmp_path: Path) -> None:
    package_dir = _write_package(
        tmp_path,
        index_source='export * from "./public-api";\n',
    )
    with pytest.raises(ManifestError, match="wildcard exports"):
        build_manifest(package_dir)
