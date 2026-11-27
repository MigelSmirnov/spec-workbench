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
                consequence="The request owner distinguishes the results.", title="One confirmation succeeds")
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


def test_quote_across_a_wrapped_line_title_and_trace_follow_up(tmp_path, capsys):
    path = tmp_path / "02_rules.md"
    path.write_text("# State 2\n\n## Accepted decision A01 — Confirmation\n\nThe value is used up by the first\n"
                    "   submission that carries it.\n")
    (tmp_path / "30_trace.json").write_text("{}")
    assert tool.main(["template", str(tmp_path), "A01"]) == 0
    form = json.loads(capsys.readouterr().out)
    form.update(disposition="decision", situation="Two submissions carry one value.", outcome="Only the first is accepted.",
                guarantee="One acceptance per value.", observation="Count accepted submissions.",
                consequence="The session owner refuses the second.",
                source_quote="used up by the first submission that carries it")
    inp = tmp_path / "form.json"

    def apply(answers):
        inp.write_text(json.dumps({**form, **answers}))
        return tool.main(["apply", str(tmp_path), str(inp)])

    assert apply({}) == 2
    assert "title" in capsys.readouterr().err
    assert apply({"title": "One acceptance", "source_quote": "used up by the second submission"}) == 2
    assert "exact passage" in capsys.readouterr().err
    assert apply({"title": "One acceptance"}) == 0
    out = capsys.readouterr().out
    assert "A02 has no owner in 30_trace.json yet" in out
    assert design_index.get_item(tmp_path, "A02")["title"] == "Accepted decision A02 — One acceptance"
