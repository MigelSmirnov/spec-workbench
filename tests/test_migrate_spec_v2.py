from __future__ import annotations

import json
from pathlib import Path

import pytest

from migrate_spec_v2 import MigrationError, migrate_file, migrate_text


ROOT = Path(__file__).resolve().parents[1]
CABINET_SPEC = ROOT / "examples" / "cabinet-backend" / "global_spec.json"


def test_current_cabinet_migration_is_exactly_language_envelope() -> None:
    original = CABINET_SPEC.read_text(encoding="utf-8")
    migrated = migrate_text(original)
    before = json.loads(original)
    after = json.loads(migrated)

    assert after["standard_version"] == 2
    assert "adapters" not in after
    before.pop("adapters")
    after.pop("standard_version")
    assert after == before


def test_current_cabinet_dry_run_has_only_two_mechanical_changes() -> None:
    report = migrate_file(CABINET_SPEC, apply=False)
    assert report["changed"] is True
    assert report["applied"] is False
    added = [line for line in report["diff"].splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line for line in report["diff"].splitlines() if line.startswith("-") and not line.startswith("---")]
    assert added == ['+  "standard_version": 2,']
    assert removed == ['-  "adapters": {},']


def test_apply_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "global_spec.json"
    target.write_text(CABINET_SPEC.read_text(encoding="utf-8"), encoding="utf-8")
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
