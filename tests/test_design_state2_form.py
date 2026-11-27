"""An author's proposal stays a draft until a reviewer accepts it."""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import design_index
import design_lint
import design_state2_form as tool
import transition


SOURCE = ("# State 2\n\n## Accepted decision A01 — Confirmation\n\nThe value is used up by the first\n"
          "   submission that carries it.\n")
ANSWERS = dict(disposition="proposal", title="One acceptance", situation="Two submissions carry one value.",
               outcome="Only the first is accepted.", guarantee="One acceptance per value.",
               observation="Count accepted submissions.", consequence="The session owner refuses the second.",
               source_quote="used up by the first submission that carries it")


@pytest.fixture
def case(tmp_path):
    (tmp_path / "02_rules.md").write_text(SOURCE)
    return tmp_path


@pytest.fixture
def run(case, capsys):
    def call(*argv, form=None):
        capsys.readouterr()
        if form is not None:
            path = case.parent / (case.name + "-form.json")
            path.write_text(json.dumps(form))
            argv = (*argv, str(path))
        code = tool.main([argv[0], str(case), *argv[1:]])
        captured = capsys.readouterr()
        return code, captured.out, captured.err
    return call


def template(run):
    code, out, _ = run("template", "A01")
    assert code == 0
    return json.loads(out)


def spec(case):
    return {p.name: p.read_bytes() for p in case.glob("*.md")}


def token(out):
    return re.search(r"--reviewed (\S+)", out).group(1)


def test_a_mechanism_answer_is_saved_as_a_draft_and_never_becomes_a_requirement(case, run):
    initial = spec(case)
    lint = design_lint.lint_project(case, state=2)
    form = {**template(run), **ANSWERS, "outcome": "We hold the lock.", "guarantee": "Держим блокировку.",
            "observation": "Mock the lock."}
    assert form["choices"] == ["proposal", "question"]
    code, out, _ = run("preview", form=form)
    assert code == 0 and "Will write proposals/state2/P-001.json" in out and "not changed" in out
    assert not (case / "proposals").exists()
    code, out, _ = run("apply", form=form)
    assert code == 0 and "Saved P-001" in out
    assert "names a mechanism (lock, блокировку)" in out
    assert "“Two submissions carry one value.” — which result must each participant see?" in out
    assert "Describe what can be checked" in out and f"Return to A01 in {case.resolve()}" in out
    assert spec(case) == initial                                   # the author changed no specification file
    assert len(design_index.list_items(case, kind="decision")) == 1
    assert "lock" not in "".join(p.read_text() for p in case.glob("*.md")).lower()
    assert design_lint.lint_project(case, state=2) == lint     # the gate sees the same specification
    code, out, _ = run("review")
    assert "P-001 [pending] at A01 — One acceptance (draft, not in the specification; names a mechanism" in out
    code, out, _ = run("review", "P-001")
    assert "It is not part of the specification." in out and "+1. Two submissions carry one value. We hold the lock." in out
    assert spec(case) == initial                                   # reading a draft writes nothing
    code, out, _ = run("reject", "P-001", "--reviewer", "owner", "--reason", "Say what the second submitter sees.")
    assert code == 0 and spec(case) == initial
    assert "P-001 [rejected]" in run("review")[1] and "Say what the second submitter sees." in run("review")[1]
    assert run("accept", "P-001", "--reviewer", "owner", "--reviewed", "x")[1].startswith("P-001 is already rejected")
    assert spec(case) == initial


def test_reviewer_accepts_exactly_what_was_reviewed(case, run):
    initial = spec(case)
    form = {**template(run), **ANSWERS}
    assert run("apply", form=form)[0] == 0
    assert run("apply", form=form)[1].startswith("P-001 already saved (pending)")
    out = run("review", "P-001")[1]
    assert "Cue:" not in out and "accepted decision A02 after A01" in out
    seen = token(out)
    assert run("accept", "P-001", "--reviewer", " ", "--reviewed", seen)[0] == 2
    (case / "02_rules.md").write_text(SOURCE + "\nA later note.\n")
    code, _, err = run("accept", "P-001", "--reviewer", "owner", "--reviewed", seen)
    assert code == 2 and "the source file changed after your review" in err and "Review again" in err
    assert len(design_index.list_items(case, kind="decision")) == 1
    seen = token(run("review", "P-001")[1])
    code, out, _ = run("accept", "P-001", "--reviewer", "owner", "--reviewed", seen)
    assert code == 0 and "Accepted P-001 as A02" in out and "now part of the specification" in out
    item = design_index.get_item(case, "A02")
    assert item["title"] == "Accepted decision A02 — One acceptance" and item["state"] == 2
    text = (case / "02_rules.md").read_text()
    assert "Accepted from proposal P-001; reviewer: owner." in text and "1. Two submissions carry one value. Only" in text
    assert not transition.check_invariant_tests(case)["findings"]
    record = json.loads((case / "proposals/state2/P-001.json").read_text())
    assert record["status"] == "accepted" and record["review"] == {"reviewer": "owner", "accepted_as": "A02"}
    assert "already accepted" in run("accept", "P-001", "--reviewer", "owner", "--reviewed", seen)[1]
    assert initial != spec(case)


def test_author_form_explains_what_blocks_it(case, run):
    form = template(run)
    assert run("apply", form={**form, **ANSWERS, "disposition": "decision"})[2].count("saves a proposal for review") == 1
    assert "title" in run("apply", form={**form, **ANSWERS, "title": None})[2]
    assert "exact passage" in run("apply", form={**form, **ANSWERS, "source_quote": "used up by the second"})[2]
    (case / "02_rules.md").write_text(SOURCE + "\nA later note.\n")
    code, _, err = run("apply", form={**form, **ANSWERS})
    assert code == 2 and "stale form: 02_rules.md changed after this form was generated" in err
    assert "Nothing was written" in err and "design_state2_form.py template" in err
    assert not (case / "proposals").exists()
    assert run("review", "P-009")[0] == 2


def test_owner_question_goes_to_the_specification_as_an_open_question(case, run):
    form = {**template(run), "disposition": "question", "situation": "The second participant retries.",
            "owner_question": "What response does the second participant receive?"}
    code, out, _ = run("preview", form=form)
    assert code == 0 and "Will write 02_rules.md: open question OQ-001 after A01" in out
    assert run("apply", form=form)[0] == 0
    assert design_index.get_item(case, "OQ-001")["kind"] == "open_question"
    assert run("apply", form=form)[1].startswith("OQ-001 already recorded")
    assert len(design_index.list_items(case, kind="decision")) == 1


def test_trace_follow_up_after_acceptance(case, run):
    (case / "30_trace.json").write_text("{}")
    assert run("apply", form={**template(run), **ANSWERS})[0] == 0
    out = run("accept", "P-001", "--reviewer", "owner", "--reviewed", token(run("review", "P-001")[1]))[1]
    assert "A02 has no owner in 30_trace.json yet" in out
