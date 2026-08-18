from __future__ import annotations

import json
from pathlib import Path

import pytest

from migrate_spec_v2 import MigrationError, migrate_file, migrate_text


ROOT = Path(__file__).resolve().parents[1]
CABINET_SPEC = ROOT / "examples" / "cabinet-backend" / "global_spec.json"
LEGACY_SPEC = """{
  \"contracts\": {
    \"main\": \"() -> None\"
  },
  \"adapters\": {},
  \"config\": {
    \"role\": \"data\",
    \"schema_version\": 1
  }
}
"""


def test_current_cabinet_is_already_migrated_and_idempotent() -> None:
    original = CABINET_SPEC.read_text(encoding="utf-8")
    payload = json.loads(original)
    assert payload["standard_version"] == 2
    assert "adapters" not in payload
    assert migrate_text(original) == original

    report = migrate_file(CABINET_SPEC, apply=False)
    assert report["changed"] is False
    assert report["applied"] is False
    assert report["diff"] == ""


def test_legacy_fixture_migration_is_exactly_language_envelope() -> None:
    migrated = migrate_text(LEGACY_SPEC)
    before = json.loads(LEGACY_SPEC)
    after = json.loads(migrated)

    assert after["standard_version"] == 2
    assert "adapters" not in after
    before.pop("adapters")
    after.pop("standard_version")
    assert after == before


def test_legacy_dry_run_has_only_two_mechanical_changes(tmp_path: Path) -> None:
    target = tmp_path / "global_spec.json"
    target.write_text(LEGACY_SPEC, encoding="utf-8")
    report = migrate_file(target, apply=False)
    assert report["changed"] is True
    assert report["applied"] is False
    added = [
        line for line in report["diff"].splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    removed = [
        line for line in report["diff"].splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    assert added == ['+  "standard_version": 2,']
    assert removed == ['-  "adapters": {},']


def test_apply_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "global_spec.json"
    target.write_text(LEGACY_SPEC, encoding="utf-8")
    first = migrate_file(target, apply=True)
    second = migrate_file(target, apply=True)
    assert first["applied"] is True
    assert second["changed"] is False
    assert second["applied"] is False
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["standard_version"] == 2
    assert "adapters" not in payload


def test_nonempty_adapters_require_semantic_migration() -> None:
    with pytest.raises(MigrationError, match="non-empty"):
        migrate_text('{\n  "adapters": {"parse": {"mapping": []}}\n}\n')


def test_unknown_existing_version_fails_closed() -> None:
    with pytest.raises(MigrationError, match="unsupported existing standard_version"):
        migrate_text('{\n  "standard_version": 3\n}\n')
