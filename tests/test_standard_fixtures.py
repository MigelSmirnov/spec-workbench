from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "skills" / "spec-authoring" / "fixtures" / "standard"
STANDARD_PATH = ROOT / "skills" / "spec-authoring" / "SPEC_STANDARD.md"

ERROR_CODE_VOCABULARY = {
    "unknown_model_kind",
    "union_missing_discriminator",
    "union_empty_variants",
    "union_variant_undeclared",
    "union_variant_missing_tag",
    "union_duplicate_tag_value",
    "union_nested",
    "union_with_fields",
    "interface_missing_contracts",
    "interface_incomplete_signature",
    "interface_with_fields",
    "unknown_type_name",
    "origin_collision",
    "forbidden_type_form",
}

REQUIRED_SPEC_SECTIONS = {
    "contracts", "models", "imports", "module_functions", "module_order", "default_module",
}


def load_manifest() -> dict:
    return json.loads((FIXTURES_DIR / "MANIFEST.json").read_text(encoding="utf-8"))


def github_slug(heading: str) -> str:
    text = heading.strip().lstrip("#").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text)


def standard_anchors() -> set[str]:
    anchors = set()
    for line in STANDARD_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            anchors.add(github_slug(line))
    return anchors


def test_manifest_matches_fixture_files_exactly():
    manifest = load_manifest()
    listed = {entry["file"] for entry in manifest["fixtures"]}
    on_disk = {p.name for p in FIXTURES_DIR.glob("*.json")} - {"MANIFEST.json"}
    assert listed == on_disk


def test_fixture_names_unique_and_match_files():
    manifest = load_manifest()
    names = [entry["name"] for entry in manifest["fixtures"]]
    assert len(names) == len(set(names))
    for entry in manifest["fixtures"]:
        assert entry["file"] == f"{entry['name']}.json"


def test_every_fixture_is_minimal_structurally_valid_spec():
    manifest = load_manifest()
    for entry in manifest["fixtures"]:
        spec = json.loads((FIXTURES_DIR / entry["file"]).read_text(encoding="utf-8"))
        missing = REQUIRED_SPEC_SECTIONS - set(spec)
        assert not missing, f"{entry['name']}: missing sections {sorted(missing)}"


def test_verdicts_and_error_codes_are_consistent():
    manifest = load_manifest()
    for entry in manifest["fixtures"]:
        assert entry["expect"] in {"valid", "invalid"}
        if entry["expect"] == "valid":
            assert entry["error_codes"] == [], entry["name"]
        else:
            assert entry["error_codes"], entry["name"]
            unknown = set(entry["error_codes"]) - ERROR_CODE_VOCABULARY
            assert not unknown, f"{entry['name']}: codes outside vocabulary {sorted(unknown)}"


def test_fixture_set_covers_both_verdicts_and_all_construct_families():
    manifest = load_manifest()
    verdicts = {entry["expect"] for entry in manifest["fixtures"]}
    assert verdicts == {"valid", "invalid"}
    all_codes = {code for entry in manifest["fixtures"] for code in entry["error_codes"]}
    assert all_codes == ERROR_CODE_VOCABULARY


def test_every_rule_reference_resolves_to_a_standard_heading():
    manifest = load_manifest()
    anchors = standard_anchors()
    for entry in manifest["fixtures"]:
        rule = entry["rule"]
        assert rule.startswith("SPEC_STANDARD.md#"), entry["name"]
        anchor = rule.split("#", 1)[1]
        assert anchor in anchors, f"{entry['name']}: dangling rule anchor {anchor}"
