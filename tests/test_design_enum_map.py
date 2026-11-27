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
    (path / "60_model_closure_values.json").write_text(json.dumps({
        "schema_version": "spec_workbench_model_closure.v1", "status": "closed", "identity_scope": "contract_only",
        "models": {"Pair": {"identity": "value", "fields": {"left": "str"}}}}, indent=2) + "\n")
    (path / "global_spec.json").write_text(json.dumps({"models": {}}) + "\n")
    (path / tool.DATA_PROVIDER_CLOSURE).write_text(json.dumps({
        "schema_version": "spec_workbench_data_provider_backend_closure.v1", "status": "closed",
        "backend_ir": {"kind": "data_provider_backend", "schema_version": 1,
                       "backend": {"emitter": "python_constant_data_v1"},
                       "wiring": {"module": "data", "models_module": "test.models"},
                       "constants": {"LOOKUP": {"value_type": "string_mapping", "value": {"x": "done"}}}}
    }, indent=2) + "\n")
    return path


CLOSURE_CHECK = Path(tool.__file__).with_name("design_identity_closure.py")
VALUES = "60_model_closure_values.json"


def form_for(case, capsys, mode="--total", row="LookupRow", names=("input", "output")):
    assert tool.main(["template", str(case), "LOOKUP", "--source", f"Input.{names[0]}",
                      "--target", f"Output.{names[1]}", "--row-model", row, mode]) == 0
    return json.loads(capsys.readouterr().out)


def answered(form, **answers):
    return {**form, "rows": {"FIRST": "DONE", "SECOND": "OPEN"}, **answers}


def snapshot(case):
    return {p: p.read_bytes() for p in case.iterdir()}


def attempt(case, form, command="apply"):
    path = case.parent / "form.json"
    path.write_text(json.dumps(form))
    return tool.main([command, str(case), str(path)])


def closure_check(case):
    return subprocess.run([sys.executable, str(CLOSURE_CHECK), str(case)], capture_output=True, text=True)


def declare(case, name, model, file=VALUES):
    path = case / file
    doc = json.loads(path.read_text())
    doc["models"][name] = model
    path.write_text(json.dumps(doc, indent=2) + "\n")


def test_migrate_and_retry(case, capsys):
    form = form_for(case, capsys)
    assert form["rows"] == {"FIRST": "DONE", "SECOND": None}
    assert form["row_identity"] is None and "same pair of values" in form["row_identity_question"]
    assert form["row_model_file"] == VALUES
    initial = snapshot(case)
    assert attempt(case, form) == 2
    form = answered(form, row_identity="value", row_identity_reason="The row is only the pair it holds.")
    assert attempt(case, form, "preview") == 0
    assert "no new findings" in capsys.readouterr().out
    assert snapshot(case) == initial
    assert attempt(case, form) == 0
    backend = tool.read(case / tool.DATA_PROVIDER_CLOSURE)["backend_ir"]
    assert backend["schema_version"] == 2
    assert backend["constants"]["LOOKUP"] == {
        "value_type": "record_tuple", "row_model": "LookupRow", "key": ["input"], "total": True,
        "value": [{"input": "x", "output": "done"}, {"input": "y", "output": "open"}]}
    assert tool.read(case / VALUES)["models"]["LookupRow"] == {
        "identity": "value", "fields": {"input": "Input", "output": "Output"}}
    assert "LookupRow" not in tool.read(case / "60_model_closure_domain.json")["models"]
    capsys.readouterr()
    assert attempt(case, form) == 0
    assert "Already matches" in capsys.readouterr().out


def test_new_row_model_reaches_the_identity_closure_check(case, capsys):
    """Regression (PR 209): §6.10 shows a row model with fields only, §15.1.1 requires identity."""
    assert closure_check(case).returncode == 0
    form = answered(form_for(case, capsys))
    initial = snapshot(case)
    for answers in ({}, {"row_identity": "value"}, {"row_identity": "record", "row_identity_reason": "x"},
                    {"row_identity": "value", "row_identity_reason": " "}):
        assert attempt(case, {**form, **answers}) == 2
        assert "row_identity" in capsys.readouterr().err
        assert snapshot(case) == initial
    for identity in ("value", "entity"):  # the check finds the gap; the choice is the author's
        assert attempt(case, {**form, "row_identity": identity, "row_identity_reason": "Decided for this table."},
                       "preview") == 0
    capsys.readouterr()
    assert attempt(case, {**form, "row_identity": "value", "row_identity_reason": "Only the pair it holds."}) == 0
    out = capsys.readouterr().out
    assert out.index("no new findings") < out.index("Applied.") and "Only the pair it holds." in out
    assert closure_check(case).returncode == 0


def test_patch_that_loses_identity_is_not_written(case, capsys, monkeypatch):
    form = answered(form_for(case, capsys), row_identity="value", row_identity_reason="Only the pair it holds.")
    monkeypatch.setattr(tool, "row_declaration", lambda form, row, info: (None, VALUES))
    initial = snapshot(case)
    assert attempt(case, form) == 2
    captured = capsys.readouterr()
    assert "invalid_contract_closure_identity [LookupRow]" in captured.err and "nothing was written" in captured.err
    assert "Applied" not in captured.out
    assert snapshot(case) == initial


def test_existing_findings_do_not_block_or_count_as_success(case, capsys):
    declare(case, "Stray", {"fields": {"left": "str"}})
    assert closure_check(case).returncode == 1
    form = answered(form_for(case, capsys), row_identity="value", row_identity_reason="Only the pair it holds.")
    assert attempt(case, form) == 0
    assert "(2 already present)" in capsys.readouterr().out
    assert "[Stray]" in closure_check(case).stdout and "LookupRow" not in closure_check(case).stdout


def test_existing_row_model_keeps_its_identity(case, capsys):
    declare(case, "LookupRow", {"identity": "value", "fields": {"input": "Input", "output": "Output"}})
    form = form_for(case, capsys)
    assert form["row_model_declared"]["file"] == VALUES and form["row_identity"] == "value"
    assert "row_identity_question" not in form and "row_model_file" not in form
    initial = snapshot(case)
    assert attempt(case, answered(form, row_identity="entity", row_identity_reason="x")) == 2
    assert f"LookupRow is value in {VALUES}" in capsys.readouterr().err
    assert snapshot(case) == initial
    assert attempt(case, answered(form)) == 0
    assert tool.read(case / VALUES)["models"]["LookupRow"]["identity"] == "value"
    assert tool.main(["template", str(case), "LOOKUP", "--source", "Input.key", "--target", "Output.output",
                      "--row-model", "LookupRow", "--total"]) == 2
    assert '"input": "Input"' in capsys.readouterr().err


def test_entity_row_model_asks_before_writing(case, capsys):
    declare(case, "LookupRow", {"identity": "entity", "fields": {"input": "Input", "output": "Output"}})
    form = form_for(case, capsys)
    assert form["row_identity"] == "entity" and "never changes state" in form["row_identity_question"]
    initial = snapshot(case)
    assert attempt(case, answered(form)) == 2
    assert "row_identity_reason" in capsys.readouterr().err
    assert snapshot(case) == initial
    assert attempt(case, answered(form, row_identity_reason="The product tracks each pairing by its own id.")) == 0
    assert tool.read(case / VALUES)["models"]["LookupRow"]["identity"] == "entity"


def test_state1_concept_takes_its_identity_and_home_from_state1(case, capsys):
    (case / "01_models.md").write_text("## Model M1 — LookupRow\n\n### Identity\n\nvalue\n")
    form = form_for(case, capsys)
    assert form["row_identity"] == "value" and form["row_model_state1"]["location"] == "01_models.md:1"
    assert form["row_model_file"] == "60_model_closure_domain.json"
    assert attempt(case, answered(form, row_identity="entity", row_identity_reason="x")) == 2
    assert "01_models.md:1" in capsys.readouterr().err
    assert attempt(case, answered(form)) == 0
    assert tool.read(case / "60_model_closure_domain.json")["models"]["LookupRow"]["identity"] == "value"
    assert closure_check(case).returncode == 0


def test_messages_name_the_field_and_the_next_step(case, capsys):
    for column, expected in (("Inputs.input", "Inputs is not declared in"), ("Input", "Enum.field")):
        assert tool.main(["template", str(case), "LOOKUP", "--source", column, "--target", "Output.output",
                          "--row-model", "LookupRow", "--total"]) == 2
        assert expected in capsys.readouterr().err
    (case / VALUES).unlink()
    assert attempt(case, answered(form_for(case, capsys), row_identity="value", row_identity_reason="pair")) == 2
    assert "this project has none" in capsys.readouterr().err


def test_partial_and_stale(case, capsys):
    form = form_for(case, capsys, "--partial")
    del form["rows"]["SECOND"]
    closure = case / tool.DATA_PROVIDER_CLOSURE
    closure.write_text(closure.read_text() + "\n")
    assert attempt(case, form) == 2
    assert "stale form" in capsys.readouterr().err
    form = form_for(case, capsys, "--partial")
    del form["rows"]["SECOND"]
    form.update(row_identity="value", row_identity_reason="Only the pair it holds.")
    assert attempt(case, form) == 0
    assert "total" not in tool.read(closure)["backend_ir"]["constants"]["LOOKUP"]
