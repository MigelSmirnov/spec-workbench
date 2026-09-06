from __future__ import annotations

import json
from pathlib import Path

import pytest

from frontend_linker import LinkerError, canonical_frontend_ir_bytes, link_frontend_spec
from frontend_package_manifest import build_manifest, manifest_hash


def _write_ts_package(
    root: Path,
    *,
    directory: str,
    name: str,
    role: str,
    exports: dict[str, str],
    capabilities: dict,
    layers: dict | None = None,
    requires_packages: list[str] | None = None,
) -> Path:
    package_dir = root / directory
    package_dir.mkdir()
    (package_dir / "package.json").write_text(
        json.dumps({"name": name, "version": "0.1.0"}), encoding="utf-8"
    )
    (package_dir / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "ESNext",
                    "moduleResolution": "Bundler",
                    "strict": True,
                    "skipLibCheck": True,
                },
                "include": ["index.ts", "public-api.ts"],
            }
        ),
        encoding="utf-8",
    )
    source = "\n".join(exports.values()) + "\n"
    (package_dir / "public-api.ts").write_text(source, encoding="utf-8")
    names = ", ".join(exports)
    (package_dir / "index.ts").write_text(
        f'export {{ {names} }} from "./public-api";\n', encoding="utf-8"
    )
    declarations = {
        "kind": "frontend_package_declarations",
        "schema_version": 1,
        "package": {"role": role},
        "requires": {
            "packages": requires_packages or [],
            "runtime_capabilities": [],
        },
        "provides": {
            "capabilities": capabilities,
            "layers": layers or {},
        },
        "irregular_exports": {},
    }
    (package_dir / "frontend-package-declarations.json").write_text(
        json.dumps(declarations), encoding="utf-8"
    )
    return package_dir


def _core_package(root: Path) -> Path:
    exports = {
        "undoAction": "export const undoAction = () => undefined;",
        "redoAction": "export const redoAction = () => undefined;",
        "cancelActiveTool": "export const cancelActiveTool = () => undefined;",
    }
    capabilities = {
        "editor.history.undo": {
            "kind": "workspace_action",
            "implementation": {"export": "undoAction"},
            "requires": [],
        },
        "editor.history.redo": {
            "kind": "workspace_action",
            "implementation": {"export": "redoAction"},
            "requires": [],
        },
        "editor.tool.cancel": {
            "kind": "workspace_action",
            "implementation": {"export": "cancelActiveTool"},
            "requires": [],
        },
    }
    return _write_ts_package(
        root,
        directory="editor-core",
        name="@factory/editor-core",
        role="runtime",
        exports=exports,
        capabilities=capabilities,
    )


def _building_package(root: Path, *, require_core: bool = True) -> Path:
    exports = {
        "projectBuildingScene": 'export const projectBuildingScene = () => ({ id: "p" });',
        "wallRenderer": "export const wallRenderer = () => undefined;",
        "wallSnapProvider": "export const wallSnapProvider = () => [];",
        "wallHitTestProvider": "export const wallHitTestProvider = () => [];",
        "wallAnchorProvider": "export const wallAnchorProvider = () => [];",
        "wallCreateCommand": "export const wallCreateCommand = () => undefined;",
        "buildingLayerDefinition": "export const buildingLayerDefinition = {};",
    }
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
            "renderer_slot": {"projection": "building.wall", "family": "scene2d"},
        },
        "building.wall.snap": {
            "kind": "snap_provider",
            "implementation": {"export": "wallSnapProvider"},
            "requires": ["building.scene.project"],
            "snap_kinds": ["endpoint"],
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
            "allowed_layer_modes": ["owned", "draft"],
            "history": "commit",
            "undo": "inverse",
        },
    }
    layers = {
        "building": {
            "implementation": {"export": "buildingLayerDefinition"},
            "supported_modes": ["owned", "reference", "draft"],
            "default_capabilities": {
                "projection": "building.scene.project",
                "renderers": ["building.wall.scene2d"],
                "snap": ["building.wall.snap"],
                "hit_test": ["building.wall.hit_test"],
                "anchors": ["building.wall.anchors"],
            },
        }
    }
    return _write_ts_package(
        root,
        directory="building-layer",
        name="@planner/building-layer",
        role="layer",
        exports=exports,
        capabilities=capabilities,
        layers=layers,
        requires_packages=["@factory/editor-core"] if require_core else [],
    )


def _room_spec(*, mode: str = "owned", draft_persistence: str | None = None) -> dict:
    layer = {
        "provider": "@planner/building-layer",
        "mode": mode,
        "visible": True,
    }
    if draft_persistence is not None:
        layer["draft_persistence"] = draft_persistence
    return {
        "kind": "frontend_spec",
        "schema_version": 1,
        "application": {"id": "room_planner", "workspace": "engineering_editor"},
        "runtime": {
            "renderer": "canvas",
            "world_unit": "mm",
            "edit_precision_mm": 1,
        },
        "layers": {"building": layer},
        "tools": [
            {
                "id": "wall",
                "command": "building.wall.create",
                "requires": ["building.wall.create"],
            }
        ],
        "symbols": {},
        "bindings": {
            "keyboard": [
                {"key": "Ctrl+Z", "command": "editor.history.undo"},
                {"key": "Ctrl+Shift+Z", "command": "editor.history.redo"},
            ]
        },
        "panels": {
            "left": ["layers"],
            "right": ["properties"],
            "bottom": ["status"],
        },
        "irregular": [],
    }


def test_linker_emits_deterministic_ir_with_package_provenance(tmp_path: Path) -> None:
    core = build_manifest(_core_package(tmp_path))
    building = build_manifest(_building_package(tmp_path))

    first = link_frontend_spec(_room_spec(), [building, core])
    second = link_frontend_spec(_room_spec(), [core, building])

    assert canonical_frontend_ir_bytes(first) == canonical_frontend_ir_bytes(second)
    assert first["packages"]["@planner/building-layer"]["manifest_hash"] == building[
        "manifest_hash"
    ]
    assert first["tools"][0]["provider"] == "@planner/building-layer"
    assert first["tools"][0]["layer"] == "building"
    assert first["tools"][0]["layer_mode"] == "owned"


def test_reference_layer_rejects_mutation_command(tmp_path: Path) -> None:
    core = build_manifest(_core_package(tmp_path))
    building = build_manifest(_building_package(tmp_path))
    with pytest.raises(LinkerError, match="illegal.*reference|reference.*illegal"):
        link_frontend_spec(_room_spec(mode="reference"), [core, building])


def test_draft_requires_explicit_persistence_policy(tmp_path: Path) -> None:
    core = build_manifest(_core_package(tmp_path))
    building = build_manifest(_building_package(tmp_path))
    with pytest.raises(LinkerError, match="draft_persistence"):
        link_frontend_spec(_room_spec(mode="draft"), [core, building])

    linked = link_frontend_spec(
        _room_spec(mode="draft", draft_persistence="none"), [core, building]
    )
    assert linked["layers"]["building"]["draft_persistence"] == "none"


def test_draft_persistence_forbidden_on_owned(tmp_path: Path) -> None:
    core = build_manifest(_core_package(tmp_path))
    building = build_manifest(_building_package(tmp_path))
    with pytest.raises(LinkerError, match="forbidden"):
        link_frontend_spec(
            _room_spec(mode="owned", draft_persistence="host_private"),
            [core, building],
        )


def test_duplicate_exclusive_provider_is_rejected(tmp_path: Path) -> None:
    core = build_manifest(_core_package(tmp_path))
    building = build_manifest(_building_package(tmp_path))

    duplicate = json.loads(json.dumps(building))
    duplicate["package"]["id"] = "@planner/building-layer-copy"
    duplicate["package"]["resolved_version"] = "0.1.0"
    duplicate["provides"]["capabilities"] = {
        "building.wall.create": duplicate["provides"]["capabilities"][
            "building.wall.create"
        ]
    }
    duplicate["provides"]["layers"] = {}
    without_hash = dict(duplicate)
    without_hash.pop("manifest_hash")
    duplicate["manifest_hash"] = manifest_hash(without_hash)

    with pytest.raises(LinkerError, match="duplicate exclusive capability provider"):
        link_frontend_spec(_room_spec(), [core, building, duplicate])


def test_multiple_aggregate_providers_are_allowed_and_sorted(tmp_path: Path) -> None:
    core = build_manifest(_core_package(tmp_path))
    building = build_manifest(_building_package(tmp_path))

    addon_dir = _write_ts_package(
        tmp_path,
        directory="snap-addon",
        name="@planner/snap-addon",
        role="runtime",
        exports={"extraSnap": "export const extraSnap = () => [];"},
        capabilities={
            "building.wall.snap": {
                "kind": "snap_provider",
                "implementation": {"export": "extraSnap"},
                "requires": [],
                "snap_kinds": ["endpoint"],
            }
        },
    )
    addon = build_manifest(addon_dir)

    linked = link_frontend_spec(_room_spec(), [addon, building, core])
    providers = linked["capabilities"]["building.wall.snap"]["providers"]
    assert [item["package"] for item in providers] == [
        "@planner/building-layer",
        "@planner/snap-addon",
    ]


def test_package_dependency_cycle_is_rejected(tmp_path: Path) -> None:
    a_dir = _write_ts_package(
        tmp_path,
        directory="a",
        name="@fixture/a",
        role="runtime",
        exports={"aAction": "export const aAction = () => undefined;"},
        capabilities={
            "fixture.a": {
                "kind": "workspace_action",
                "implementation": {"export": "aAction"},
                "requires": [],
            }
        },
        requires_packages=["@fixture/b"],
    )
    b_dir = _write_ts_package(
        tmp_path,
        directory="b",
        name="@fixture/b",
        role="runtime",
        exports={"bAction": "export const bAction = () => undefined;"},
        capabilities={
            "fixture.b": {
                "kind": "workspace_action",
                "implementation": {"export": "bAction"},
                "requires": [],
            }
        },
        requires_packages=["@fixture/a"],
    )
    a = build_manifest(a_dir)
    b = build_manifest(b_dir)

    spec = {
        "kind": "frontend_spec",
        "schema_version": 1,
        "application": {"id": "fixture", "workspace": "engineering_editor"},
        "runtime": {
            "renderer": "canvas",
            "world_unit": "mm",
            "edit_precision_mm": 1,
        },
        "layers": {},
        "tools": [],
        "symbols": {},
        "bindings": {},
        "panels": {},
        "irregular": [],
    }
    with pytest.raises(LinkerError, match="dependency cycle"):
        link_frontend_spec(spec, [a, b])
