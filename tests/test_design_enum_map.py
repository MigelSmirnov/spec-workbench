"""Exercise the author's CLI and real git apply on a disposable case."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import design_enum_map as tool


@pytest.fixture
def case(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = tmp_path / "examples" / "case"
    path.mkdir(parents=True)
    models = {"Input": {"kind": "enum", "values": ["x", "y"], "member_names": ["FIRST", "SECOND"]},
              "Output": {"kind": "enum", "members": {"DONE": "done", "OPEN": "open"}}}
    (path / "60_model_closure_domain.json").write_text(json.dumps({
        "schema_version": "spec_workbench_model_closure.v1", "status": "closed", "models": models}, indent=2) + "\n")
    (path / tool.DATA_PROVIDER_CLOSURE).write_text(json.dumps({
        "schema_version": "spec_workbench_data_provider_backend_closure.v1", "status": "closed",
        "backend_ir": {"kind": "data_provider_backend", "schema_version": 1,
                       "backend": {"emitter": "python_constant_data_v1"},
                       "wiring": {"module": "data", "models_module": "test.models"},
                       "constants": {"LOOKUP": {"value_type": "string_mapping", "value": {"x": "done"}}}}
    }, indent=2) + "\n")
    return path


def form_for(case, capsys, mode="--total"):
    assert tool.main(["template", str(case), "LOOKUP", "--source", "Input.input",
                      "--target", "Output.output", "--row-model", "LookupRow", mode]) == 0
    return json.loads(capsys.readouterr().out)


def test_migrate_and_retry(case, capsys):
    form = form_for(case, capsys)
    assert form["rows"] == {"FIRST": "DONE", "SECOND": None}
    path = case.parent / "form.json"
    path.write_text(json.dumps(form))
    initial = {p: p.read_bytes() for p in case.iterdir()}
    assert tool.main(["apply", str(case), str(path)]) == 2
    form["rows"]["SECOND"] = "OPEN"
    path.write_text(json.dumps(form))
    assert tool.main(["preview", str(case), str(path)]) == 0
    assert {p: p.read_bytes() for p in case.iterdir()} == initial
    assert tool.main(["apply", str(case), str(path)]) == 0
    backend = tool.read(case / tool.DATA_PROVIDER_CLOSURE)["backend_ir"]
    assert backend["schema_version"] == 2
    assert backend["constants"]["LOOKUP"] == {
        "value_type": "record_tuple", "row_model": "LookupRow", "key": ["input"], "total": True,
        "value": [{"input": "x", "output": "done"}, {"input": "y", "output": "open"}]}
    assert tool.read(case / "60_model_closure_domain.json")["models"]["LookupRow"] == {
        "fields": {"input": "Input", "output": "Output"}}
    assert tool.main(["apply", str(case), str(path)]) == 0
    assert "Already matches" in capsys.readouterr().out


def test_partial_and_stale(case, capsys):
    form = form_for(case, capsys, "--partial")
    del form["rows"]["SECOND"]
    path = case.parent / "form.json"
    path.write_text(json.dumps(form))
    closure = case / tool.DATA_PROVIDER_CLOSURE
    closure.write_text(closure.read_text() + "\n")
    assert tool.main(["apply", str(case), str(path)]) == 2
    assert "stale form" in capsys.readouterr().err
    form = form_for(case, capsys, "--partial")
    del form["rows"]["SECOND"]
    path.write_text(json.dumps(form))
    assert tool.main(["apply", str(case), str(path)]) == 0
    assert "total" not in tool.read(closure)["backend_ir"]["constants"]["LOOKUP"]
