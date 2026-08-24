from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


MANIFEST_KIND = "frontend_package_manifest"
MANIFEST_SCHEMA_VERSION = 1
DECLARATION_KIND = "frontend_package_declarations"
DECLARATION_SCHEMA_VERSION = 1

V1_PACKAGE_ROLES = {"runtime", "layer", "renderer_adapter", "ui_adapter"}
V1_CAPABILITY_KINDS = {
    "command",
    "renderer",
    "snap_provider",
    "hit_test_provider",
    "anchor_provider",
    "projection",
    "workspace_action",
}
LAYER_MODES = {"owned", "reference", "draft"}
READ_LAYER_KINDS = {
    "renderer",
    "snap_provider",
    "hit_test_provider",
    "anchor_provider",
    "projection",
}
HISTORY_VALUES = {"commit", "transient", "none"}
UNDO_VALUES = {"inverse", "snapshot"}
RENDERER_FAMILIES = {"scene2d", "svg_symbol"}

_EXPORT_DECL_RE = re.compile(
    r"^\s*export\s+(?:async\s+)?(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
_EXPORT_LIST_RE = re.compile(
    r"export\s*\{(?P<body>.*?)\}\s*(?:from\s*['\"][^'\"]+['\"])?\s*;",
    re.DOTALL,
)
_EXPORT_STAR_RE = re.compile(r"export\s*\*\s*from\s*['\"][^'\"]+['\"]\s*;")
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENT_LINE_RE = re.compile(r"//.*?$", re.MULTILINE)


class ManifestError(ValueError):
    """Raised when a package cannot produce a canonical frontend manifest."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"expected JSON object in {path}")
    return value


def _sorted_unique_strings(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ManifestError(f"{field} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ManifestError(f"{field} contains duplicates")
    return sorted(value)


def _strip_ts_comments(source: str) -> str:
    return _COMMENT_LINE_RE.sub("", _COMMENT_BLOCK_RE.sub("", source))


def discover_public_value_exports(index_path: Path) -> set[str]:
    """Discover explicit runtime-value exports from a package public TypeScript index.

    V1 intentionally rejects wildcard exports in the public boundary used by the
    manifest generator. The generator must be able to prove every implementation
    export without guessing through arbitrary TypeScript module graphs.
    """
    try:
        source = index_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ManifestError(f"missing public TypeScript entry point: {index_path}") from exc

    source = _strip_ts_comments(source)
    if _EXPORT_STAR_RE.search(source):
        raise ManifestError(
            f"{index_path}: wildcard exports are unsupported by manifest generator v1; "
            "use explicit named public exports"
        )

    exports = set(_EXPORT_DECL_RE.findall(source))
    for match in _EXPORT_LIST_RE.finditer(source):
        body = match.group("body")
        for raw_item in body.split(","):
            item = raw_item.strip()
            if not item or item.startswith("type "):
                continue
            parts = re.split(r"\s+as\s+", item)
            public_name = parts[-1].strip()
            if re.fullmatch(r"[A-Za-z_$][\w$]*", public_name):
                exports.add(public_name)
            else:
                raise ManifestError(
                    f"{index_path}: unsupported export item {item!r}; "
                    "manifest generator v1 requires explicit named exports"
                )
    return exports


def _require_public_export(
    record: dict[str, Any], field: str, public_exports: set[str], context: str
) -> str:
    implementation = record.get(field)
    if not isinstance(implementation, dict) or set(implementation) != {"export"}:
        raise ManifestError(f"{context}.{field} must be an object with only 'export'")
    export_name = implementation["export"]
    if not isinstance(export_name, str) or not export_name:
        raise ManifestError(f"{context}.{field}.export must be a non-empty string")
    if export_name not in public_exports:
        raise ManifestError(
            f"{context}: public export {export_name!r} does not exist in package public index"
        )
    return export_name


def _normalize_allowed_modes(
    capability_id: str, kind: str, record: dict[str, Any]
) -> list[str] | None:
    raw = record.get("allowed_layer_modes")
    if kind == "command":
        modes = _sorted_unique_strings(raw, f"{capability_id}.allowed_layer_modes")
        if not modes:
            raise ManifestError(
                f"{capability_id}.allowed_layer_modes is required for command"
            )
        invalid = set(modes) - {"owned", "draft"}
        if invalid:
            raise ManifestError(
                f"{capability_id}: command layer modes must be subset of owned,draft"
            )
        return modes

    if kind in READ_LAYER_KINDS:
        if raw is None:
            return None
        modes = _sorted_unique_strings(raw, f"{capability_id}.allowed_layer_modes")
        if not modes:
            raise ManifestError(f"{capability_id}.allowed_layer_modes cannot be empty")
        invalid = set(modes) - LAYER_MODES
        if invalid:
            raise ManifestError(
                f"{capability_id}.allowed_layer_modes has unsupported values: {sorted(invalid)}"
            )
        return modes

    if kind == "workspace_action":
        if raw is not None:
            raise ManifestError(
                f"{capability_id}: workspace_action must not declare allowed_layer_modes"
            )
        return None

    raise ManifestError(f"{capability_id}: unsupported capability kind {kind!r}")


def _normalize_command_fields(
    capability_id: str, record: dict[str, Any]
) -> dict[str, Any]:
    history = record.get("history")
    if history not in HISTORY_VALUES:
        raise ManifestError(
            f"{capability_id}.history must be one of {sorted(HISTORY_VALUES)}"
        )

    normalized: dict[str, Any] = {"history": history}
    undo = record.get("undo")
    snapshot_scope = record.get("snapshot_scope")

    if history == "commit":
        if undo not in UNDO_VALUES:
            raise ManifestError(
                f"{capability_id}.undo is required for history=commit and must be "
                f"one of {sorted(UNDO_VALUES)}"
            )
        normalized["undo"] = undo
        if undo == "snapshot":
            if snapshot_scope != "layer":
                raise ManifestError(
                    f"{capability_id}.snapshot_scope must be 'layer' for undo=snapshot"
                )
            normalized["snapshot_scope"] = "layer"
        elif snapshot_scope is not None:
            raise ManifestError(
                f"{capability_id}.snapshot_scope is forbidden for undo=inverse"
            )
    else:
        if undo is not None:
            raise ManifestError(
                f"{capability_id}.undo is forbidden when history is {history}"
            )
        if snapshot_scope is not None:
            raise ManifestError(
                f"{capability_id}.snapshot_scope is forbidden when history is {history}"
            )
    return normalized


def _normalize_renderer_fields(
    capability_id: str, record: dict[str, Any]
) -> dict[str, Any]:
    slot = record.get("renderer_slot")
    if not isinstance(slot, dict) or set(slot) != {"projection", "family"}:
        raise ManifestError(
            f"{capability_id}.renderer_slot must contain exactly projection,family"
        )
    projection = slot["projection"]
    family = slot["family"]
    if not isinstance(projection, str) or not projection:
        raise ManifestError(f"{capability_id}.renderer_slot.projection must be non-empty")
    if family not in RENDERER_FAMILIES:
        raise ManifestError(
            f"{capability_id}.renderer_slot.family must be one of {sorted(RENDERER_FAMILIES)}"
        )
    return {"renderer_slot": {"projection": projection, "family": family}}


def _normalize_capability(
    capability_id: str, record: Any, public_exports: set[str]
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ManifestError(f"capability {capability_id!r} must be an object")
    kind = record.get("kind")
    if kind not in V1_CAPABILITY_KINDS:
        raise ManifestError(
            f"{capability_id}: capability kind {kind!r} is not v1-implemented"
        )

    export_name = _require_public_export(
        record, "implementation", public_exports, f"capability {capability_id}"
    )
    requires = _sorted_unique_strings(
        record.get("requires", []), f"{capability_id}.requires"
    )
    allowed_modes = _normalize_allowed_modes(capability_id, kind, record)

    normalized: dict[str, Any] = {
        "kind": kind,
        "implementation": {"export": export_name},
        "requires": requires,
    }
    if allowed_modes is not None:
        normalized["allowed_layer_modes"] = allowed_modes

    if "input_type" in record:
        if not isinstance(record["input_type"], str) or not record["input_type"]:
            raise ManifestError(f"{capability_id}.input_type must be a non-empty string")
        normalized["input_type"] = record["input_type"]
    if "output_type" in record:
        if not isinstance(record["output_type"], str) or not record["output_type"]:
            raise ManifestError(f"{capability_id}.output_type must be a non-empty string")
        normalized["output_type"] = record["output_type"]

    if kind == "command":
        normalized.update(_normalize_command_fields(capability_id, record))
    elif kind == "renderer":
        normalized.update(_normalize_renderer_fields(capability_id, record))
    elif kind == "snap_provider":
        snap_kinds = _sorted_unique_strings(
            record.get("snap_kinds", []), f"{capability_id}.snap_kinds"
        )
        if not snap_kinds:
            raise ManifestError(f"{capability_id}.snap_kinds cannot be empty")
        normalized["snap_kinds"] = snap_kinds

    allowed_fields = {
        "kind",
        "implementation",
        "requires",
        "allowed_layer_modes",
        "input_type",
        "output_type",
    }
    if kind == "command":
        allowed_fields |= {"history", "undo", "snapshot_scope"}
    if kind == "renderer":
        allowed_fields.add("renderer_slot")
    if kind == "snap_provider":
        allowed_fields.add("snap_kinds")
    unknown = set(record) - allowed_fields
    if unknown:
        raise ManifestError(
            f"{capability_id}: fields not allowed for {kind}: {sorted(unknown)}"
        )
    return normalized


def _normalize_layers(layers: Any, public_exports: set[str]) -> dict[str, Any]:
    if layers is None:
        return {}
    if not isinstance(layers, dict):
        raise ManifestError("provides.layers must be an object")
    normalized: dict[str, Any] = {}
    for layer_id in sorted(layers):
        record = layers[layer_id]
        if not isinstance(record, dict):
            raise ManifestError(f"layer {layer_id!r} must be an object")
        export_name = _require_public_export(
            record, "implementation", public_exports, f"layer {layer_id}"
        )
        modes = _sorted_unique_strings(
            record.get("supported_modes"), f"layer {layer_id}.supported_modes"
        )
        if not modes:
            raise ManifestError(f"layer {layer_id}.supported_modes cannot be empty")
        invalid_modes = set(modes) - LAYER_MODES
        if invalid_modes:
            raise ManifestError(
                f"layer {layer_id}.supported_modes has unsupported values: "
                f"{sorted(invalid_modes)}"
            )

        defaults = record.get("default_capabilities", {})
        if not isinstance(defaults, dict):
            raise ManifestError(f"layer {layer_id}.default_capabilities must be an object")
        allowed_default_fields = {"projection", "renderers", "hit_test", "anchors", "snap"}
        unknown_defaults = set(defaults) - allowed_default_fields
        if unknown_defaults:
            raise ManifestError(
                f"layer {layer_id}.default_capabilities has unknown fields: "
                f"{sorted(unknown_defaults)}"
            )
        normalized_defaults: dict[str, Any] = {}
        if "projection" in defaults:
            projection = defaults["projection"]
            if not isinstance(projection, str) or not projection:
                raise ManifestError(
                    f"layer {layer_id}.default_capabilities.projection must be non-empty"
                )
            normalized_defaults["projection"] = projection
        for field in ("renderers", "hit_test", "anchors", "snap"):
            if field in defaults:
                normalized_defaults[field] = _sorted_unique_strings(
                    defaults[field],
                    f"layer {layer_id}.default_capabilities.{field}",
                )

        unknown = set(record) - {"implementation", "supported_modes", "default_capabilities"}
        if unknown:
            raise ManifestError(f"layer {layer_id}: unknown fields {sorted(unknown)}")

        normalized[layer_id] = {
            "implementation": {"export": export_name},
            "supported_modes": modes,
            "default_capabilities": normalized_defaults,
        }
    return normalized


def _normalize_irregular(irregular: Any, public_exports: set[str]) -> dict[str, Any]:
    if irregular is None:
        return {}
    if not isinstance(irregular, dict):
        raise ManifestError("irregular_exports must be an object")
    normalized: dict[str, Any] = {}
    for irregular_id in sorted(irregular):
        record = irregular[irregular_id]
        if not isinstance(record, dict):
            raise ManifestError(f"irregular export {irregular_id!r} must be an object")
        export_name = record.get("export")
        if not isinstance(export_name, str) or not export_name:
            raise ManifestError(f"irregular export {irregular_id}.export must be non-empty")
        if export_name not in public_exports:
            raise ManifestError(
                f"irregular export {irregular_id}: public export {export_name!r} "
                "does not exist in package public index"
            )
        kind = record.get("kind")
        reason = record.get("reason")
        if not isinstance(kind, str) or not kind:
            raise ManifestError(f"irregular export {irregular_id}.kind must be non-empty")
        if not isinstance(reason, str) or not reason.strip():
            raise ManifestError(f"irregular export {irregular_id}.reason is required")
        unknown = set(record) - {"export", "kind", "reason"}
        if unknown:
            raise ManifestError(
                f"irregular export {irregular_id}: unknown fields {sorted(unknown)}"
            )
        normalized[irregular_id] = {
            "export": export_name,
            "kind": kind,
            "reason": reason.strip(),
        }
    return normalized


def canonical_manifest_bytes(manifest_without_hash: dict[str, Any]) -> bytes:
    """Return canonical UTF-8 JSON bytes for hashing and deterministic output."""
    text = json.dumps(
        manifest_without_hash,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def manifest_hash(manifest_without_hash: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_manifest_bytes(manifest_without_hash)).hexdigest()
    return f"sha256:{digest}"


def build_manifest(
    package_dir: Path,
    *,
    declarations_name: str = "frontend-package-declarations.json",
    public_index_name: str = "index.ts",
) -> dict[str, Any]:
    package_dir = package_dir.resolve()
    package_json = _load_json(package_dir / "package.json")
    declarations = _load_json(package_dir / declarations_name)

    if declarations.get("kind") != DECLARATION_KIND:
        raise ManifestError(f"declarations.kind must be {DECLARATION_KIND!r}")
    if declarations.get("schema_version") != DECLARATION_SCHEMA_VERSION:
        raise ManifestError(
            f"declarations.schema_version must be {DECLARATION_SCHEMA_VERSION}"
        )

    package_id = package_json.get("name")
    version = package_json.get("version")
    if not isinstance(package_id, str) or not package_id:
        raise ManifestError("package.json.name must be a non-empty string")
    if not isinstance(version, str) or not version:
        raise ManifestError("package.json.version must be a non-empty string")

    declared_package = declarations.get("package")
    if not isinstance(declared_package, dict) or set(declared_package) != {"role"}:
        raise ManifestError("declarations.package must contain exactly role")
    role = declared_package["role"]
    if role not in V1_PACKAGE_ROLES:
        raise ManifestError(f"package role {role!r} is not supported in v1")

    public_exports = discover_public_value_exports(package_dir / public_index_name)

    requires = declarations.get("requires", {})
    if not isinstance(requires, dict):
        raise ManifestError("requires must be an object")
    unknown_requires = set(requires) - {"packages", "runtime_capabilities"}
    if unknown_requires:
        raise ManifestError(f"requires has unknown fields: {sorted(unknown_requires)}")
    normalized_requires = {
        "packages": _sorted_unique_strings(
            requires.get("packages", []), "requires.packages"
        ),
        "runtime_capabilities": _sorted_unique_strings(
            requires.get("runtime_capabilities", []),
            "requires.runtime_capabilities",
        ),
    }

    provides = declarations.get("provides", {})
    if not isinstance(provides, dict):
        raise ManifestError("provides must be an object")
    unknown_provides = set(provides) - {"capabilities", "layers"}
    if unknown_provides:
        raise ManifestError(f"provides has unknown fields: {sorted(unknown_provides)}")

    capabilities_raw = provides.get("capabilities", {})
    if not isinstance(capabilities_raw, dict):
        raise ManifestError("provides.capabilities must be an object")
    capabilities: dict[str, Any] = {}
    for capability_id in sorted(capabilities_raw):
        if not isinstance(capability_id, str) or not capability_id:
            raise ManifestError("capability IDs must be non-empty strings")
        capabilities[capability_id] = _normalize_capability(
            capability_id, capabilities_raw[capability_id], public_exports
        )

    layers = _normalize_layers(provides.get("layers", {}), public_exports)
    irregular = _normalize_irregular(
        declarations.get("irregular_exports", {}), public_exports
    )

    unknown_top = set(declarations) - {
        "kind",
        "schema_version",
        "package",
        "requires",
        "provides",
        "irregular_exports",
    }
    if unknown_top:
        raise ManifestError(f"declarations has unknown fields: {sorted(unknown_top)}")

    manifest_without_hash: dict[str, Any] = {
        "kind": MANIFEST_KIND,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "package": {
            "id": package_id,
            "role": role,
            "resolved_version": version,
        },
        "requires": normalized_requires,
        "provides": {
            "capabilities": capabilities,
            "layers": layers,
        },
        "irregular_exports": irregular,
    }
    result = dict(manifest_without_hash)
    result["manifest_hash"] = manifest_hash(manifest_without_hash)
    return result


def write_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    without_hash = dict(manifest)
    hash_value = without_hash.pop("manifest_hash", None)
    expected = manifest_hash(without_hash)
    if hash_value != expected:
        raise ManifestError(
            f"manifest_hash mismatch before write: expected {expected}, got {hash_value}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical_manifest_bytes(manifest))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic verified frontend package manifest."
    )
    parser.add_argument("package_dir", type=Path)
    parser.add_argument(
        "--declarations",
        default="frontend-package-declarations.json",
        help="Package-local declaration file relative to package_dir.",
    )
    parser.add_argument(
        "--public-index",
        default="index.ts",
        help="Public TypeScript entry point relative to package_dir.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path. Defaults to <package_dir>/frontend-package-manifest.json.",
    )
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    output = args.output or (package_dir / "frontend-package-manifest.json")
    try:
        manifest = build_manifest(
            package_dir,
            declarations_name=args.declarations,
            public_index_name=args.public_index,
        )
        write_manifest(manifest, output)
    except ManifestError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
