from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from frontend_package_manifest import manifest_hash


AGGREGATE_KINDS = {"snap_provider", "anchor_provider", "hit_test_provider"}
EXCLUSIVE_KINDS = {"command", "projection", "workspace_action"}
PANEL_IDS = {"palette", "layers", "properties", "status", "history"}
LAYER_MODES = {"owned", "reference", "draft"}
DRAFT_PERSISTENCE = {"none", "host_private"}


class LinkerError(ValueError):
    """Raised when package manifests and frontend composition cannot be linked."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LinkerError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LinkerError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LinkerError(f"expected JSON object in {path}")
    return value


def canonical_frontend_ir_bytes(ir: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            ir,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _verify_manifest_hash(manifest: dict[str, Any]) -> None:
    hash_value = manifest.get("manifest_hash")
    if not isinstance(hash_value, str):
        raise LinkerError("package manifest missing manifest_hash")
    without_hash = dict(manifest)
    without_hash.pop("manifest_hash", None)
    expected = manifest_hash(without_hash)
    if hash_value != expected:
        package_id = manifest.get("package", {}).get("id", "<unknown>")
        raise LinkerError(
            f"package {package_id}: manifest_hash mismatch: expected {expected}, got {hash_value}"
        )


def _index_manifests(
    manifests: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[tuple[str, dict[str, Any]]]]]:
    packages: dict[str, dict[str, Any]] = {}
    providers: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    renderer_slots: dict[tuple[str, str], tuple[str, str]] = {}

    for manifest in manifests:
        _verify_manifest_hash(manifest)
        if manifest.get("kind") != "frontend_package_manifest":
            raise LinkerError("unsupported package manifest kind")
        if manifest.get("schema_version") != 1:
            raise LinkerError("unsupported package manifest schema_version")
        package = manifest.get("package")
        if not isinstance(package, dict):
            raise LinkerError("package manifest.package must be an object")
        package_id = package.get("id")
        if not isinstance(package_id, str) or not package_id:
            raise LinkerError("package manifest package.id must be non-empty")
        if package_id in packages:
            raise LinkerError(f"duplicate package id: {package_id}")
        packages[package_id] = manifest

        capabilities = manifest.get("provides", {}).get("capabilities", {})
        if not isinstance(capabilities, dict):
            raise LinkerError(
                f"package {package_id}: provides.capabilities must be an object"
            )
        for capability_id, record in capabilities.items():
            if not isinstance(record, dict):
                raise LinkerError(
                    f"package {package_id}: invalid capability {capability_id}"
                )
            providers.setdefault(capability_id, []).append((package_id, record))
            if record.get("kind") == "renderer":
                slot = record.get("renderer_slot")
                if not isinstance(slot, dict):
                    raise LinkerError(
                        f"package {package_id}: renderer {capability_id} missing renderer_slot"
                    )
                key = (slot.get("projection"), slot.get("family"))
                if not all(isinstance(value, str) and value for value in key):
                    raise LinkerError(
                        f"package {package_id}: renderer {capability_id} has invalid renderer_slot"
                    )
                if key in renderer_slots:
                    other_package, other_capability = renderer_slots[key]
                    raise LinkerError(
                        "duplicate renderer slot "
                        f"{key}: {other_package}:{other_capability} and "
                        f"{package_id}:{capability_id}"
                    )
                renderer_slots[key] = (package_id, capability_id)

    for capability_id, entries in providers.items():
        kinds = {record.get("kind") for _, record in entries}
        if len(kinds) != 1:
            raise LinkerError(
                f"capability {capability_id}: providers disagree on kind: {sorted(kinds)}"
            )
        kind = next(iter(kinds))
        if kind not in AGGREGATE_KINDS and len(entries) > 1:
            raise LinkerError(f"duplicate exclusive capability provider: {capability_id}")
        entries.sort(key=lambda item: item[0])

    return packages, providers


def _validate_package_dag(packages: dict[str, dict[str, Any]]) -> None:
    graph: dict[str, list[str]] = {}
    for package_id, manifest in packages.items():
        raw = manifest.get("requires", {}).get("packages", [])
        if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
            raise LinkerError(
                f"package {package_id}: requires.packages must be string list"
            )
        missing = sorted(set(raw) - packages.keys())
        if missing:
            raise LinkerError(f"package {package_id}: missing required packages {missing}")
        graph[package_id] = sorted(raw)

    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        marker = state.get(node, 0)
        if marker == 2:
            return
        if marker == 1:
            cycle_start = stack.index(node)
            cycle = stack[cycle_start:] + [node]
            raise LinkerError(f"package dependency cycle: {' -> '.join(cycle)}")
        state[node] = 1
        stack.append(node)
        for dependency in graph[node]:
            visit(dependency)
        stack.pop()
        state[node] = 2

    for package_id in sorted(graph):
        visit(package_id)


def _resolve_capability(
    capability_id: str,
    providers: dict[str, list[tuple[str, dict[str, Any]]]],
) -> list[tuple[str, dict[str, Any]]]:
    entries = providers.get(capability_id)
    if not entries:
        raise LinkerError(f"unresolved capability: {capability_id}")
    return entries


def _validate_capability_requirements(
    packages: dict[str, dict[str, Any]],
    providers: dict[str, list[tuple[str, dict[str, Any]]]],
) -> None:
    for package_id, manifest in packages.items():
        runtime_requirements = manifest.get("requires", {}).get(
            "runtime_capabilities", []
        )
        if not isinstance(runtime_requirements, list):
            raise LinkerError(
                f"package {package_id}: requires.runtime_capabilities must be a list"
            )
        for capability_id in runtime_requirements:
            _resolve_capability(capability_id, providers)

        capabilities = manifest.get("provides", {}).get("capabilities", {})
        for own_capability_id, record in capabilities.items():
            requires = record.get("requires", [])
            if not isinstance(requires, list):
                raise LinkerError(f"capability {own_capability_id}: requires must be a list")
            for capability_id in requires:
                _resolve_capability(capability_id, providers)


def _capability_ir(
    providers: dict[str, list[tuple[str, dict[str, Any]]]]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for capability_id in sorted(providers):
        entries = providers[capability_id]
        kind = entries[0][1]["kind"]
        result[capability_id] = {
            "kind": kind,
            "providers": [
                {
                    "package": package_id,
                    "export": record["implementation"]["export"],
                }
                for package_id, record in entries
            ],
        }
        if kind == "renderer":
            result[capability_id]["renderer_slot"] = entries[0][1]["renderer_slot"]
    return result


def _validate_frontend_spec_top(spec: dict[str, Any]) -> None:
    allowed = {
        "kind",
        "schema_version",
        "application",
        "runtime",
        "layers",
        "tools",
        "symbols",
        "bindings",
        "panels",
        "irregular",
    }
    unknown = set(spec) - allowed
    if unknown:
        raise LinkerError(f"frontend spec unknown top-level fields: {sorted(unknown)}")
    if spec.get("kind") != "frontend_spec":
        raise LinkerError("frontend spec kind must be 'frontend_spec'")
    if spec.get("schema_version") != 1:
        raise LinkerError("frontend spec schema_version must be 1")

    application = spec.get("application")
    if not isinstance(application, dict):
        raise LinkerError("frontend spec application must be an object")
    if application.get("workspace") != "engineering_editor":
        raise LinkerError("frontend spec v1 supports workspace=engineering_editor")
    if not isinstance(application.get("id"), str) or not application["id"]:
        raise LinkerError("frontend spec application.id must be non-empty")

    runtime = spec.get("runtime")
    if not isinstance(runtime, dict):
        raise LinkerError("frontend spec runtime must be an object")
    if runtime.get("renderer") not in {"canvas", "svg"}:
        raise LinkerError("frontend spec runtime.renderer must be canvas|svg")
    if runtime.get("world_unit") != "mm":
        raise LinkerError("frontend spec v1 world_unit must be mm")
    precision = runtime.get("edit_precision_mm")
    if (
        not isinstance(precision, (int, float))
        or isinstance(precision, bool)
        or precision <= 0
    ):
        raise LinkerError("frontend spec edit_precision_mm must be positive")


def _validate_layers(
    spec: dict[str, Any],
    packages: dict[str, dict[str, Any]],
    providers: dict[str, list[tuple[str, dict[str, Any]]]],
) -> tuple[dict[str, Any], dict[str, list[tuple[str, str]]]]:
    raw_layers = spec.get("layers", {})
    if not isinstance(raw_layers, dict):
        raise LinkerError("frontend spec layers must be an object")

    normalized: dict[str, Any] = {}
    package_layers: dict[str, list[tuple[str, str]]] = {}

    for layer_id in sorted(raw_layers):
        record = raw_layers[layer_id]
        if not isinstance(record, dict):
            raise LinkerError(f"layer {layer_id}: must be an object")
        allowed_fields = {"provider", "mode", "visible", "draft_persistence"}
        unknown = set(record) - allowed_fields
        if unknown:
            raise LinkerError(f"layer {layer_id}: unknown fields {sorted(unknown)}")

        provider = record.get("provider")
        mode = record.get("mode")
        if provider not in packages:
            raise LinkerError(f"layer {layer_id}: unknown provider package {provider!r}")
        if mode not in LAYER_MODES:
            raise LinkerError(f"layer {layer_id}: invalid mode {mode!r}")

        provided_layers = packages[provider].get("provides", {}).get("layers", {})
        layer_definition = provided_layers.get(layer_id)
        if not isinstance(layer_definition, dict):
            raise LinkerError(
                f"layer {layer_id}: provider {provider} does not provide layer {layer_id}"
            )
        supported = layer_definition.get("supported_modes", [])
        if mode not in supported:
            raise LinkerError(
                f"layer {layer_id}: mode {mode} unsupported by provider {provider}"
            )

        draft_persistence = record.get("draft_persistence")
        if mode == "draft":
            if draft_persistence not in DRAFT_PERSISTENCE:
                raise LinkerError(
                    f"layer {layer_id}: draft_persistence is required and must be "
                    f"one of {sorted(DRAFT_PERSISTENCE)}"
                )
        elif draft_persistence is not None:
            raise LinkerError(
                f"layer {layer_id}: draft_persistence is forbidden for mode={mode}"
            )

        defaults = layer_definition.get("default_capabilities", {})
        default_ids: list[str] = []
        projection = defaults.get("projection")
        if projection:
            default_ids.append(projection)
        for field in ("renderers", "hit_test", "anchors", "snap"):
            default_ids.extend(defaults.get(field, []))
        for capability_id in default_ids:
            entries = _resolve_capability(capability_id, providers)
            for package_id, capability in entries:
                if package_id != provider and capability["kind"] not in AGGREGATE_KINDS:
                    raise LinkerError(
                        f"layer {layer_id}: default capability {capability_id} "
                        f"resolved outside provider {provider}"
                    )
                allowed_modes = capability.get(
                    "allowed_layer_modes", ["owned", "reference", "draft"]
                )
                if mode not in allowed_modes:
                    raise LinkerError(
                        f"layer {layer_id}: capability {capability_id} is illegal in mode {mode}"
                    )

        normalized_record: dict[str, Any] = {
            "provider": provider,
            "mode": mode,
            "visible": bool(record.get("visible", True)),
            "default_capabilities": defaults,
        }
        if mode == "draft":
            normalized_record["draft_persistence"] = draft_persistence
        normalized[layer_id] = normalized_record
        package_layers.setdefault(provider, []).append((layer_id, mode))

    return normalized, package_layers


def _resolve_tool_capability(
    capability_id: str,
    providers: dict[str, list[tuple[str, dict[str, Any]]]],
    package_layers: dict[str, list[tuple[str, str]]],
) -> dict[str, Any]:
    entries = _resolve_capability(capability_id, providers)
    if len(entries) != 1:
        raise LinkerError(
            f"tool/action capability {capability_id} must resolve to exactly one provider"
        )
    package_id, capability = entries[0]
    kind = capability["kind"]
    result: dict[str, Any] = {
        "capability": capability_id,
        "kind": kind,
        "provider": package_id,
        "export": capability["implementation"]["export"],
    }

    if kind == "command":
        loaded = package_layers.get(package_id, [])
        if len(loaded) != 1:
            raise LinkerError(
                f"command {capability_id}: provider {package_id} must map to exactly "
                "one loaded layer in frontend_spec/v1"
            )
        layer_id, mode = loaded[0]
        allowed_modes = capability.get("allowed_layer_modes", [])
        if mode not in allowed_modes:
            raise LinkerError(
                f"command {capability_id} is illegal in layer {layer_id} mode {mode}"
            )
        result["layer"] = layer_id
        result["layer_mode"] = mode
    elif kind != "workspace_action":
        raise LinkerError(
            f"tool/action capability {capability_id} has unsupported kind {kind}"
        )
    return result


def link_frontend_spec(
    spec: dict[str, Any], manifests: list[dict[str, Any]]
) -> dict[str, Any]:
    _validate_frontend_spec_top(spec)
    packages, providers = _index_manifests(manifests)
    _validate_package_dag(packages)
    _validate_capability_requirements(packages, providers)
    layers, package_layers = _validate_layers(spec, packages, providers)

    tools_raw = spec.get("tools", [])
    if not isinstance(tools_raw, list):
        raise LinkerError("frontend spec tools must be a list")
    seen_tool_ids: set[str] = set()
    tools: list[dict[str, Any]] = []
    for record in tools_raw:
        if not isinstance(record, dict):
            raise LinkerError("tool record must be an object")
        allowed_fields = {"id", "builtin", "command", "requires", "symbol"}
        unknown = set(record) - allowed_fields
        if unknown:
            raise LinkerError(f"tool has unknown fields: {sorted(unknown)}")
        tool_id = record.get("id")
        if not isinstance(tool_id, str) or not tool_id:
            raise LinkerError("tool.id must be non-empty")
        if tool_id in seen_tool_ids:
            raise LinkerError(f"duplicate tool id: {tool_id}")
        seen_tool_ids.add(tool_id)
        refs = [field for field in ("builtin", "command") if field in record]
        if len(refs) != 1:
            raise LinkerError(
                f"tool {tool_id}: exactly one of builtin or command required"
            )
        capability_id = record[refs[0]]
        if not isinstance(capability_id, str) or not capability_id:
            raise LinkerError(f"tool {tool_id}: capability reference must be non-empty")
        linked = _resolve_tool_capability(capability_id, providers, package_layers)
        for required in record.get("requires", []):
            _resolve_capability(required, providers)
        linked["id"] = tool_id
        if "symbol" in record:
            raise LinkerError(
                f"tool {tool_id}: symbol linking is not implemented in compiler spike"
            )
        tools.append(linked)

    symbols = spec.get("symbols", {})
    if symbols not in ({}, {"catalogs": []}):
        raise LinkerError("symbol catalogs are not implemented in compiler spike")

    bindings_raw = spec.get("bindings", {})
    if not isinstance(bindings_raw, dict):
        raise LinkerError("bindings must be an object")
    unknown_bindings = set(bindings_raw) - {"keyboard"}
    if unknown_bindings:
        raise LinkerError(f"bindings has unknown fields: {sorted(unknown_bindings)}")
    keyboard_raw = bindings_raw.get("keyboard", [])
    if not isinstance(keyboard_raw, list):
        raise LinkerError("bindings.keyboard must be a list")
    keyboard: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for record in keyboard_raw:
        if not isinstance(record, dict) or set(record) != {"key", "command"}:
            raise LinkerError("keyboard binding must contain exactly key,command")
        key = record["key"]
        command = record["command"]
        if not isinstance(key, str) or not key:
            raise LinkerError("keyboard key must be non-empty")
        if key in seen_keys:
            raise LinkerError(f"conflicting keyboard binding: {key}")
        seen_keys.add(key)
        linked = _resolve_tool_capability(command, providers, package_layers)
        keyboard.append({"key": key, "action": linked})

    panels_raw = spec.get("panels", {})
    if not isinstance(panels_raw, dict):
        raise LinkerError("panels must be an object")
    unknown_panel_slots = set(panels_raw) - {"left", "right", "bottom"}
    if unknown_panel_slots:
        raise LinkerError(f"unknown panel slots: {sorted(unknown_panel_slots)}")
    panels: dict[str, list[str]] = {}
    for slot in ("left", "right", "bottom"):
        values = panels_raw.get(slot, [])
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            raise LinkerError(f"panels.{slot} must be a string list")
        unknown_ids = set(values) - PANEL_IDS
        if unknown_ids:
            raise LinkerError(f"panels.{slot}: unknown panel ids {sorted(unknown_ids)}")
        panels[slot] = list(values)

    irregular = spec.get("irregular", [])
    if not isinstance(irregular, list):
        raise LinkerError("irregular must be a list")
    normalized_irregular: list[dict[str, str]] = []
    seen_irregular: set[str] = set()
    for record in irregular:
        if not isinstance(record, dict) or set(record) != {"id", "owner", "reason"}:
            raise LinkerError("irregular record must contain exactly id,owner,reason")
        irregular_id = record["id"]
        if not isinstance(irregular_id, str) or not irregular_id:
            raise LinkerError("irregular.id must be non-empty")
        if irregular_id in seen_irregular:
            raise LinkerError(f"duplicate irregular id: {irregular_id}")
        seen_irregular.add(irregular_id)
        owner = record["owner"]
        reason = record["reason"]
        if not isinstance(owner, str) or not owner:
            raise LinkerError(f"irregular {irregular_id}: owner must be non-empty")
        if not isinstance(reason, str) or not reason.strip():
            raise LinkerError(f"irregular {irregular_id}: reason is required")
        normalized_irregular.append(
            {"id": irregular_id, "owner": owner, "reason": reason.strip()}
        )

    package_ir = {
        package_id: {
            "role": manifest["package"]["role"],
            "resolved_version": manifest["package"]["resolved_version"],
            "manifest_schema_version": manifest["schema_version"],
            "manifest_hash": manifest["manifest_hash"],
            "requires_packages": manifest.get("requires", {}).get("packages", []),
        }
        for package_id, manifest in sorted(packages.items())
    }

    return {
        "kind": "frontend_ir",
        "schema_version": 1,
        "application": dict(spec["application"]),
        "runtime": dict(spec["runtime"]),
        "packages": package_ir,
        "capabilities": _capability_ir(providers),
        "layers": layers,
        "tools": tools,
        "bindings": {"keyboard": keyboard},
        "panels": panels,
        "irregular": normalized_irregular,
    }


def write_frontend_ir(ir: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_frontend_ir_bytes(ir))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Link frontend_spec/v1 with generated package manifests."
    )
    parser.add_argument(
        "frontend_spec",
        type=Path,
        help="JSON-form frontend_spec/v1 for the compiler spike.",
    )
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        required=True,
        help="Generated frontend-package-manifest.json; repeat for each package.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        spec = _load_json(args.frontend_spec)
        manifests = [_load_json(path) for path in args.manifest]
        ir = link_frontend_spec(spec, manifests)
        write_frontend_ir(ir, args.output)
    except LinkerError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
