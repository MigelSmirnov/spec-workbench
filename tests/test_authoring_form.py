"""Both writing forms follow one order: read set, shown target, reviewed apply, return address."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import authoring_form as forms
import design_enum_map
import design_state2_form


def test_changes_name_each_file_and_how_to_continue(tmp_path):
    (tmp_path / "a.md").write_text("one")
    (tmp_path / "b.md").write_text("two")
    seen = forms.read_set(tmp_path, [tmp_path / "a.md", tmp_path / "b.md"])
    forms.require_current(seen, dict(seen), "REFRESH")
    (tmp_path / "a.md").write_text("changed")
    now = forms.read_set(tmp_path, [tmp_path / "a.md", tmp_path / "c.md"] if (tmp_path / "c.md").exists()
                         else [tmp_path / "a.md"])
    with pytest.raises(forms.StaleForm) as stale:
        forms.require_current(seen, now, "REFRESH")
    text = str(stale.value)
    assert "a.md changed" in text and "b.md is gone" in text
    assert "Nothing was written" in text and text.endswith("preview again: REFRESH")
    assert forms.revision(seen) != forms.revision(now)
    with pytest.raises(forms.StaleForm, match="does not record what it read"):
        forms.require_current(None, now, "REFRESH")


@pytest.fixture
def case(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    case = tmp_path / "case"
    case.mkdir()
    (case / "global_spec.json").write_text('{"models": {}}\n')
    (case / "02_rules.md").write_text("# State 2\n\n## Accepted decision A01 — Confirmation\n\nOne value, one use.\n")
    models = {"Input": {"kind": "enum", "members": {"FIRST": "x"}}, "Output": {"kind": "enum", "members": {"DONE": "done"}}}
    closure = {"schema_version": "spec_workbench_model_closure.v1", "status": "closed"}
    (case / "60_model_closure_domain.json").write_text(json.dumps({**closure, "models": models}, indent=2) + "\n")
    (case / "60_model_closure_values.json").write_text(json.dumps(
        {**closure, "identity_scope": "contract_only", "models": {}}, indent=2) + "\n")
    (case / design_enum_map.DATA_PROVIDER_CLOSURE).write_text(json.dumps(
        {"schema_version": "spec_workbench_data_provider_backend_closure.v1", "status": "closed",
         "backend_ir": {"kind": "data_provider_backend", "schema_version": 1,
                        "backend": {"emitter": "python_constant_data_v1"},
                        "wiring": {"module": "data", "models_module": "test.models"}, "constants": {}}}, indent=2) + "\n")
    return case


FORMS = {
    "state2": (design_state2_form, ["A01"], "02_rules.md", "A01",
               dict(disposition="question", situation="Two uses arrive.", owner_question="Which one wins?")),
    "enum": (design_enum_map, ["LOOKUP", "--source", "Input.input", "--target", "Output.output",
                               "--row-model", "LookupRow", "--total"], "60_model_closure_domain.json", "LOOKUP",
             dict(rows={"FIRST": "DONE"}, row_identity="value", row_identity_reason="Only the pair.")),
}


@pytest.mark.parametrize("name", FORMS)
def test_every_writing_form_follows_the_same_order(case, capsys, name):
    tool, args, source, obj, answers = FORMS[name]
    assert tool.main(["template", str(case), *args]) == 0
    form = json.loads(capsys.readouterr().out)
    # 1. The form records what it read and where the author returns.
    assert source in form["read_set"] and form["revision"] == forms.revision(form["read_set"])
    assert form["return_to"]["working_copy"] == str(case.resolve()) and form["return_to"]["object"] == obj
    path = case.parent / "form.json"
    path.write_text(json.dumps({**form, **answers}))
    before = {p.name: p.read_bytes() for p in case.iterdir()}
    # 2. Preview says what will be written and where, and writes nothing.
    assert tool.main(["preview", str(case), str(path)]) == 0
    preview = capsys.readouterr().out
    assert f"Working copy: {case.resolve()}" in preview and "Will write " in preview and "+++ b/" in preview
    assert {p.name: p.read_bytes() for p in case.iterdir()} == before
    # 3. A source that moved after the preview stops apply, names the file and the way on.
    original = (case / source).read_bytes()
    (case / source).write_bytes(original + b"\n")
    moved = {p.name: p.read_bytes() for p in case.iterdir()}
    assert tool.main(["apply", str(case), str(path)]) == 2
    error = capsys.readouterr().err
    assert f"stale form: {source} changed after this form was generated" in error
    assert "Nothing was written" in error and form["return_to"]["reopen"] in error
    assert {p.name: p.read_bytes() for p in case.iterdir()} == moved
    # 4. Apply writes what the preview showed and hands back the same working copy and object.
    (case / source).write_bytes(original)
    assert tool.main(["apply", str(case), str(path)]) == 0
    applied = capsys.readouterr().out
    shown = [line for line in preview.splitlines() if line.startswith(("+", "-"))]
    assert shown == [line for line in applied.splitlines() if line.startswith(("+", "-"))]
    assert f"Return to {obj} in {case.resolve()}: {form['return_to']['reopen']}" in applied
