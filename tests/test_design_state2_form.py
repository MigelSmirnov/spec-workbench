import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import design_index
import design_state2_form as tool
import transition


def test_author_paths(tmp_path, capsys):
    path = tmp_path / "02_rules.md"
    path.write_text("# State 2\n\n## Accepted decision A01\n\nOne successful confirmation.\n")
    initial = path.read_bytes()
    def template():
        capsys.readouterr()
        assert tool.main(["template", str(tmp_path), "A01"]) == 0
        return json.loads(capsys.readouterr().out)

    def command(name, form):
        inp = tmp_path / "form.json"
        inp.write_text(json.dumps(form))
        return tool.main([name, str(tmp_path), str(inp)])

    form = template()
    form.update(disposition="decision", situation="Two participants confirm together.",
                source_quote="One successful confirmation.", guarantee="One success.", observation="Count successes.",
                consequence="The request owner distinguishes the results.")
    assert command("apply", form) == 2
    assert "Which result" in capsys.readouterr().err
    form["outcome"] = "Only one gets success."
    assert command("preview", form) == 0
    assert path.read_bytes() == initial
    assert command("apply", form) == 0
    saved = path.read_bytes()
    assert command("apply", form) == 0
    assert path.read_bytes() == saved
    assert design_index.get_item(tmp_path, "A02")["state"] == 2
    assert not transition.check_invariant_tests(tmp_path)["findings"]
    question = template()
    question.update(disposition="question", situation="The second participant retries.",
                    owner_question="What response does the second participant receive?")
    path.write_bytes(saved + b"\n")
    assert command("apply", question) == 2
    assert "reopen" in capsys.readouterr().err.lower()
    question = {**question, "revision": template()["revision"]}
    assert command("apply", question) == 0
    assert design_index.get_item(tmp_path, "OQ-001")["kind"] == "open_question"
    assert len(design_index.list_items(tmp_path, kind="decision")) == 2
