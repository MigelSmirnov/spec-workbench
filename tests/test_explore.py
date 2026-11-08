"""The exploring review of State 2 (issue #159, the agentic "почемучка").

The explorer below is a stand-in for the model: it works only through the
workspace's own `nav.py`, run as a subprocess in the workspace, as a real
agent would.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from questions_workbench import explore, layer_prompt, service, units  # noqa: E402

PRODUCT = """# State 0 — Ledger

A ledger for one owner.

## Rules

### R0-01 — One owner (owner, 2026-07-18)

The ledger has exactly one owner.

### R0-03 — Deletion on request (owner, 2026-07-18)

The owner may delete any entry at once, whatever its age.
"""

MODELS = """# State 1 — Models

## Model M01 — Entry

- `amount` decimal
- `created_at` datetime
"""

RULES = """# State 2 — Rules

## Accepted decision A02 — retention

### Normative rules

An `Entry` is kept for ten years; none is deleted earlier.
"""

TEXTS = [(0, "00_product.md", PRODUCT), (1, "01_models.md", MODELS), (2, "02_rules.md", RULES)]


class Explorer:
    """Explores like an agent: only through `python3 nav.py` in the workspace."""

    name = "fake-explorer"

    def __init__(self, complete=True):
        self.complete_flag = complete
        self.instructions: list[str] = []
        self.inputs: list[str] = []
        self.judged: list[str] = []

    def nav(self, workspace: Path, *args: str) -> dict:
        done = subprocess.run([sys.executable, "nav.py", *args], cwd=workspace, capture_output=True, text=True)
        self.trace.append({"command": f"python3 nav.py {' '.join(args)}", "exit_code": done.returncode})
        return json.loads(done.stdout)

    def explore(self, instruction, text, workspace):
        self.instructions.append(instruction)
        self.inputs.append(text)
        self.trace = []
        ids = self.nav(workspace, "ids", "R0-")["identifiers"]               # general: what does State 0 decide?
        found = None
        for identifier in sorted(ids):
            read = self.nav(workspace, "read", identifier)
            if "delete" in read["text"]:
                found = read
        decision = self.nav(workspace, "read", "A02")
        point = {"subject": "A02", "unit": "A02", "kind": "contradiction",
                 "text": "none is deleted earlier", "question": "may the owner delete an entry before ten years?",
                 "basis": [{"key": found["key"], "quote": "The owner may delete any entry at once, whatever its age."},
                           {"key": decision["key"], "quote": "none is deleted earlier"}]}
        answer = {"open_points": [point], "complete": self.complete_flag,
                  "unresolved": [] if self.complete_flag else ["did not read the methodology"],
                  "read": [found["key"], decision["key"]]}
        return json.dumps(answer), {}, list(self.trace)

    def complete(self, instruction, text):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            ids = [line.split(":", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                   if line[:1] == "T"]
            return json.dumps({"judgements": [{"id": i, "kind": "indifferent", "why": "x"} for i in ids]}), {}
        if instruction.startswith("You receive the open points"):
            return json.dumps({"groups": [{"topic": "t", "members": [l.split(": ", 1)[0]
                                                                     for l in text.splitlines()]}]}), {}
        raise AssertionError("an exploring round asks reviews through explore()")


def _case(tmp_path: Path) -> Path:
    case = tmp_path / "demo"
    case.mkdir()
    for _, name, body in TEXTS:
        (case / name).write_text(body, encoding="utf-8")
    return case


def _layer(monkeypatch):
    monkeypatch.setattr(service, "layer_context", lambda case, state: {
        "state": state, "owns": ["where time comes from"], "carries": [], "gate_findings": [], "ready": True,
        "receives": [], "results": [],
        "verdicts": [{"decision": "A02", "witness": "verification:keep", "item": "- x", "invariants": [],
                      "digest": "d" * 64, "outcome": "asserts", "why": "keeps"}]})
    monkeypatch.setattr(service, "judge_checks", lambda case, state, provider: [])


def test_the_basis_of_a_defect_lies_outside_the_initial_selection():
    # the layer prompt for A02 alone gives Entry, not the product's deletion rule
    current = units.units(TEXTS, 2)
    selection = layer_prompt.select(TEXTS, 2, current, ["A02"], {}, None)
    initial = layer_prompt.render(selection, TEXTS, 2)
    assert "Model M01 — Entry" in initial and "delete any entry at once" not in initial


def test_an_exploring_reviewer_finds_and_reads_the_basis_in_state_0(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _layer(monkeypatch)
    provider = Explorer()
    summary = service.ask_round(case, 2, provider, runs=3)
    assert len(provider.inputs) == 3
    # the earlier texts the selection could not narrow are pointed to, not pasted: the agent reads them
    assert "Not pasted here" in provider.inputs[0] and "delete any entry at once" not in provider.inputs[0]
    instruction = provider.instructions[0]
    assert "python3 nav.py" in instruction and "from the general to the particular" in instruction
    assert "methodology/SPEC_STANDARD.md" in instruction and "methodology/TRANSITION_PROTOCOL.md" in instruction
    exploration = summary["judge"]["exploration"]
    assert len(exploration["snapshot"]) == 64
    review = json.loads((case / "questions" / "state2" / summary["round"] / "review-1.json").read_text())
    assert review["snapshot"] == exploration["snapshot"]
    assert any("read R0-03" in step["command"] for step in review["trace"])          # it went to State 0 itself
    point = review["open_points"][0]
    assert point["basis_verified"] is True and all(b["verified"] for b in point["basis"])
    assert summary["not_checked_reviews"] == [] and summary["repeated_topics"] == 1
    assert provider.judged and "may the owner delete an entry before ten years?" in provider.judged[0]
    # review r4505410895: the basis the reviewer read outside the initial text reaches the judge, verbatim
    assert "The owner may delete any entry at once, whatever its age." not in provider.inputs[0]
    judged = provider.judged[0]
    assert "BASES THE REVIEWS READ" in judged and "The owner may delete any entry at once, whatever its age." in judged
    assert f"snapshot {exploration['snapshot']}" in judged


def test_a_quote_not_in_the_snapshot_is_not_a_verified_basis(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    workspace = explore.build_workspace(root, TEXTS, 2, None)

    class Liar(Explorer):
        def explore(self, instruction, text, ws):
            answer = {"open_points": [{"subject": "A02", "unit": "A02", "kind": "gap", "text": "x", "question": "y",
                                       "basis": [{"key": "R0-03", "quote": "entries are never deleted"}]}],
                      "complete": True, "unresolved": [], "read": ["R0-03"]}
            return json.dumps(answer), {}, []

    review = explore.review(Liar(), "", "", root, workspace["snapshot"])
    assert review["open_points"][0]["basis_verified"] is False and "not_checked" not in review


def test_an_unfinished_exploration_is_never_a_clean_round(tmp_path, monkeypatch):
    case = _case(tmp_path)
    _layer(monkeypatch)
    summary = service.ask_round(case, 2, Explorer(complete=False), runs=3)
    assert [r["review"] for r in summary["not_checked_reviews"]] == [1, 2, 3]
    assert "did not read the methodology" in summary["not_checked_reviews"][0]["reason"]
    assert summary["clear"] is False and summary["closed"] is False
    assert set(summary["open_units"]) == set(summary["scope"])          # a new round is needed

    class Garbled(Explorer):
        def explore(self, instruction, text, ws):
            return "I looked around.", {}, []

    summary = service.ask_round(case, 2, Garbled(), runs=3)
    assert summary["clear"] is False and "not readable JSON" in summary["not_checked_reviews"][0]["reason"]


def test_requirements_without_contracts_are_reviewed_in_full(tmp_path, monkeypatch):
    # States 0..2 only: no plan, no contract, no implementation
    case = _case(tmp_path)
    _layer(monkeypatch)

    class Quiet(Explorer):
        def explore(self, instruction, text, ws):
            self.trace = []
            self.nav(ws, "toc")
            return json.dumps({"open_points": [], "complete": True, "unresolved": [], "read": []}), {}, self.trace

    summary = service.ask_round(case, 2, Quiet(), runs=3)          # one round per change (#163)
    assert summary["clear"] is True and summary["not_checked_reviews"] == []
    assert summary["closed"] is True


def test_the_workspace_holds_the_snapshot_the_tool_and_the_phase_methodology(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    layer = {"verdicts": [{"decision": "A02", "outcome": "asserts"}], "results": [], "gate_findings": []}
    workspace = explore.build_workspace(root, TEXTS, 2, layer)
    # the State 2 round gets neither check code nor verdicts (owner decision 2026-11-08, #161)
    assert not (root / "verdicts.json").exists()
    assert workspace["documents"] == ["docs/00_product.md", "docs/01_models.md", "docs/02_rules.md"]
    names = [name for name, _ in workspace["methodology"]]
    assert names == ["methodology/TRANSITION_PROTOCOL.md", "methodology/SECURITY_REVIEW_EVIDENCE.md",
                     "methodology/SPEC_STANDARD.md"]
    assert (root / "nav.py").is_file()
    done = subprocess.run([sys.executable, "nav.py", "read", "methodology/SPEC_STANDARD.md#title"], cwd=root,
                          capture_output=True, text=True)
    assert done.returncode == 0 and json.loads(done.stdout)["snapshot"] == workspace["snapshot"]


def test_an_answer_that_is_not_a_review_never_closes_the_round(tmp_path, monkeypatch):
    # review r4505410897: a well-formed JSON without a valid open_points list is no review
    case = _case(tmp_path)
    _layer(monkeypatch)
    for answer, reason in (({"complete": True, "unresolved": []}, "open_points is not a list"),
                           ({"open_points": "none", "complete": True}, "open_points is not a list"),
                           ({"open_points": [1, "x"], "complete": True}, "point 1 is not an object"),
                           ({"open_points": [{"subject": "A02", "text": "t", "question": "q"}], "complete": True},
                            "point 1 names no basis"),
                           ({"open_points": [], "complete": "yes"}, "complete is not true or false")):

        class Odd(Explorer):
            def explore(self, instruction, text, ws, answer=answer):
                return json.dumps(answer), {}, []

        for _ in range(2):
            summary = service.ask_round(case, 2, Odd(), runs=3)
            assert summary["clear"] is False and reason in summary["not_checked_reviews"][0]["reason"]
            assert summary["closed"] is False and set(summary["open_units"]) == set(summary["scope"])
        assert service.status(case, 2)["open_units"]


def test_parallel_codex_explorations_each_read_their_own_answer(tmp_path, monkeypatch):
    # review r4505410892: every call writes and reads its own -o, never a shared file
    import random
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    from questions_workbench import provider as providers

    outputs: list[str] = []
    lock = threading.Lock()

    def fake_run(command, input, cwd, capture_output, text, timeout):
        out = Path(command[command.index("-o") + 1])
        with lock:
            outputs.append(str(out))
        marker = input.split("MARKER:", 1)[1].split()[0]
        time.sleep(random.uniform(0, 0.05))
        out.write_text(json.dumps({"marker": marker}), encoding="utf-8")
        time.sleep(random.uniform(0, 0.05))
        events = json.dumps({"item": {"type": "command_execution", "command": f"python3 nav.py read {marker}",
                                      "exit_code": 0}})
        return subprocess.CompletedProcess(command, 0, stdout=events + "\n", stderr="")

    monkeypatch.setattr(providers.subprocess, "run", fake_run)
    codex = providers.CodexCliProvider("m", "low")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    markers = [f"R{i}" for i in range(9)]
    with ThreadPoolExecutor(max_workers=9) as pool:
        results = list(pool.map(lambda m: codex.explore(f"MARKER:{m} go", "", workspace), markers))
    assert [json.loads(answer)["marker"] for answer, _, _ in results] == markers
    assert [trace[0]["command"] for _, _, trace in results] == [f"python3 nav.py read {m}" for m in markers]
    assert len(set(outputs)) == len(markers) and all(not Path(o).exists() for o in outputs)
