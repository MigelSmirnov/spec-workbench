from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from factory_validation import assembly_check, validate_source
from factory_admission_workbench.service import _factory_validation_check
from test_factory_admission import _factory


@pytest.mark.parametrize("valid", [True, False])
def test_assembly_and_admission_share_canonical_verdict(tmp_path, valid):
    factory = _factory(tmp_path, valid=valid)
    project = tmp_path / "case"
    project.mkdir()
    source = project / "global_spec.json"
    source.write_text('{"standard_version": 2}', encoding="utf-8")
    assembly = assembly_check(project, factory)
    admission, report = _factory_validation_check(factory, source)
    assert assembly["ready"] is valid
    assert (admission.status == "PASS") is valid
    assert report == assembly["summary"]["evidence"]["report"]


@pytest.mark.parametrize("mode", ["missing", "crash", "malformed", "stale", "warnings"])
def test_unproven_validation_blocks(tmp_path, mode):
    factory = _factory(tmp_path)
    source = tmp_path / "global_spec.json"
    source.write_text("{}", encoding="utf-8")
    validator = factory / "tools/validate_spec.py"
    if mode == "missing":
        validator.unlink()
    elif mode == "crash":
        validator.write_text("raise SystemExit(1)", encoding="utf-8")
    elif mode == "malformed":
        validator.write_text(
            "import sys\nfrom pathlib import Path\nPath(sys.argv[sys.argv.index('--out')+1]).write_text('[]')",
            encoding="utf-8",
        )
    else:
        text = validator.read_text(encoding="utf-8")
        if mode == "stale":
            text = text.replace("hashlib.sha256(payload)", "hashlib.sha256(b'stale')")
        else:
            text = text.replace("'warning': 0", "'warning': 1")
        validator.write_text(text, encoding="utf-8")
    assert validate_source(source, factory)["ready"] is False


def test_explicit_factory_does_not_fall_back_to_environment(tmp_path, monkeypatch):
    factory = _factory(tmp_path)
    monkeypatch.setenv("SPEC_WORKBENCH_FACTORY_ROOT", str(factory))
    source = tmp_path / "global_spec.json"
    source.write_text("{}", encoding="utf-8")
    assert validate_source(source)["ready"] is True
    assert validate_source(source, tmp_path / "missing")["ready"] is False


@pytest.mark.skipif(not os.environ.get("SPEC_WORKBENCH_FACTORY_ROOT"), reason="real Factory checkout not configured")
@pytest.mark.parametrize("return_type,ready", [("None", True), ("MissingType", False)])
def test_real_factory_bridge(tmp_path, return_type, ready):
    source = tmp_path / "global_spec.json"
    spec = {"standard_version": 2, "contracts": {"main": f"() -> {return_type}"},
            "notes": ["main: [BEHAVIOR] application entrypoint."], "models": {},
            "imports": {"stdlib": [], "third_party": [], "internal": {}},
            "module_functions": {"app": ["main"]}, "module_order": ["app"],
            "function_order": ["main"]}
    source.write_text(json.dumps(spec), encoding="utf-8")
    assert assembly_check(tmp_path)["ready"] is ready
    admission, _ = _factory_validation_check(Path(os.environ["SPEC_WORKBENCH_FACTORY_ROOT"]), source)
    assert (admission.status == "PASS") is ready
