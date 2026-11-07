"""The prompt of a layer: what a document round of States 0-5 reads.

Owner decision 2026-11-08 (#147, comment 6714407801): a round reads what its
layer needs, not the texts of States 0..N. Never a pass by omission.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from questions_workbench import layer_prompt as lp  # noqa: E402
from questions_workbench import service, units  # noqa: E402

PRODUCT = """# State 0 — Demo product

## Rules

- R0-01: a ledger records every entry once.
- R0-02: the owner sees totals by month.

## Currency policy

Amounts are kept in euros.
"""

MODELS = """# State 1 — Demo models

## Model M01 — Entry

- `entry_id` UUID
- `created_at` datetime

## Model M02 — MonthTotal

- `month` str
- `created_at` datetime

## Model M03 — Unrelated

- `created_at` datetime
"""

RULES = """# State 2 — Demo rules

## Accepted decision A01 — entries are counted once

### Normative rules

An `Entry` is recorded once (R0-01).

### Formal invariants

- INV-001: an entry is counted once

## Accepted decision A02 — monthly totals

### Normative rules

A `MonthTotal` sums the entries of a month; see A01.

## Accepted decision A03 — retention

### Normative rules

Entries are kept for ten years.
"""


def texts(rules: str = RULES) -> list[tuple[int, str, str]]:
    return [(0, "00_product.md", PRODUCT), (1, "01_models.md", MODELS), (2, "02_rules.md", rules)]


def chosen(scope, changed=None, referencing=None, rules: str = RULES):
    t = texts(rules)
    current = units.units(t, 2)
    selection = lp.select(t, 2, current, scope, changed or {}, referencing)
    return selection, lp.render(selection, t, 2)


def test_an_open_decision_receives_what_it_names_and_nothing_merely_sharing_a_field():
    selection, text = chosen(["A01"])
    received = [key for _, _, key, _ in selection.received]
    assert received == ["00_product.md:Rules", "01_models.md:Model M01 — Entry"]
    assert "MonthTotal" not in text.split("the passages this layer receives")[1]   # shares only created_at
    assert "Model M03" not in text and "Currency policy" not in text
    assert "A03" not in text and "## Accepted decision A02" not in text           # closed units of the layer


def test_a_single_word_model_is_found_without_code_spans():
    rules = RULES.replace("An `Entry` is recorded once", "An Entry is recorded once")
    selection, _ = chosen(["A01"], rules=rules)
    assert "01_models.md:Model M01 — Entry" in [key for _, _, key, _ in selection.received]


def test_a_closed_unit_of_the_layer_appears_only_through_referencing():
    selection, text = chosen(["A01"], referencing={"A02": ["A01"]})
    assert selection.neighbours == ["A02"] and "## Accepted decision A02" in text
    assert "## Accepted decision A03" not in text


def test_an_earlier_unit_naming_what_the_open_unit_defines_is_received():
    product = PRODUCT + "\n## Audit\n\nThe audit trail shows INV-001 breaches.\n"
    t = [(0, "00_product.md", product), (1, "01_models.md", MODELS), (2, "02_rules.md", RULES)]
    selection = lp.select(t, 2, units.units(t, 2), ["A01"], {}, None)
    assert "00_product.md:Audit" in [key for _, _, key, _ in selection.received]


def test_an_open_unit_naming_no_identifier_reads_the_earlier_states_whole():
    selection, text = chosen(["A03"])
    assert selection.whole and "A03 names nothing an earlier state defines" in selection.whole[0]
    assert "=== 00_product.md (State 0), whole ===" in text and "Model M03" in text
    assert "whole, because A03 names nothing an earlier state defines" in lp.note(selection, 2)


def test_an_open_unit_whose_only_identifiers_are_its_own_still_reads_the_earlier_states_whole():
    # review r4504187837: A03 declares INV-003 itself; that resolves nothing below
    rules = RULES.replace("Entries are kept for ten years.\n",
                          "Entries are kept for ten years.\n\n### Formal invariants\n\n"
                          "- INV-003: entries are kept for ten years\n- also `RetentionWindow` applies\n")
    selection, text = chosen(["A03"], rules=rules)
    assert selection.whole and "A03 names nothing an earlier state defines" in selection.whole[0]
    assert "Currency policy" in text and "Model M01 — Entry" in text


def test_the_selection_is_closed_over_what_the_chosen_passages_name():
    # review r4504187842: A01 names Entry; Entry's amount is a Money, defined apart
    models = MODELS.replace("- `created_at` datetime\n\n## Model M02",
                            "- `created_at` datetime\n- `amount` Money\n\n## Model M02")
    models += "\n## Model M04 — Money\n\n- currency EUR, rounded half-even (see A09 below)\n"
    product = PRODUCT + "\n## Decision A09\n\nRounding follows R0-02.\n"
    for order in ("models first", "product last"):
        t = [(0, "00_product.md", product), (1, "01_models.md", models), (2, "02_rules.md", RULES)]
        if order == "product last":
            t = [t[1], t[2], t[0]]
        selection = lp.select(t, 2, units.units(t, 2), ["A01"], {}, None)
        received = [key for _, _, key, _ in selection.received]
        assert "01_models.md:Model M04 — Money" in received, order       # Entry -> Money
        assert "00_product.md:Decision A09" in received, order          # Money -> A09
        assert "01_models.md:Model M03 — Unrelated" not in received     # shares only created_at


def test_an_earlier_decision_brings_the_decision_it_names():
    later = [(0, "00_product.md", PRODUCT), (1, "01_models.md", MODELS), (2, "02_rules.md", RULES),
             (3, "30_modules.md", "# State 3\n\n## Module ledger\n\nOwns the rule of A02.\n")]
    selection = lp.select(later, 3, units.units(later, 3), ["30_modules.md:Module ledger"], {}, None)
    received = [key for _, _, key, _ in selection.received]
    assert "A02" in received and "A01" in received                       # A02 -> A01
    assert "01_models.md:Model M02 — MonthTotal" in received             # A02 -> MonthTotal


def test_an_open_agreement_without_its_change_reads_the_earlier_states_whole():
    selection, _ = chosen([units.CONTEXT, "A01"])
    assert any("change cannot be read" in reason for reason in selection.whole)


def test_an_open_agreement_reads_the_earlier_passages_its_change_touched():
    diff = ("--- closed\n+++ now\n@@\n-- `month` int\n+- `month` str\n", [])
    selection, text = chosen([units.CONTEXT], {units.CONTEXT: diff})
    assert not selection.whole
    assert [key for _, _, key, _ in selection.received] == ["01_models.md:Model M02 — MonthTotal"]
    assert selection.neighbours == ["A02"] and "## Accepted decision A02" in text   # it speaks of MonthTotal


def test_the_round_of_state_2_reads_its_layer_prompt(tmp_path, monkeypatch):
    case = tmp_path / "demo"
    case.mkdir()
    for _, name, body in texts():
        (case / name).write_text(body, encoding="utf-8")

    class Provider:
        name = "fake"

        def __init__(self):
            self.asked: list[tuple[str, str]] = []
            self.judged: list[str] = []

        def complete(self, instruction, text):
            if instruction.startswith("You judge the topics"):
                self.judged.append(text)
                return json.dumps({"judgements": []}), {}
            if instruction.startswith("You receive the open points"):
                return json.dumps({"groups": []}), {}
            self.asked.append((instruction, text))
            return json.dumps({"open_points": []}), {}

    monkeypatch.setattr(service, "layer_context", lambda case, state: {
        "state": state, "owns": [], "carries": [], "gate_findings": [], "materials": [], "ready": True,
        "receives": [], "results": []})
    provider = Provider()
    service.ask_round(case, 2, provider)
    instruction, text = provider.asked[0]
    assert "What you read. Not the whole specification" in instruction
    assert "Currency policy" in text            # A03 names nothing: honest fallback, said so
    assert "their texts whole, because" in instruction
    assert "A03 names nothing an earlier state defines" in instruction


def test_reviewers_and_judge_both_read_the_closed_selection(tmp_path, monkeypatch):
    models = MODELS.replace("- `created_at` datetime\n\n## Model M02",
                            "- `created_at` datetime\n- `amount` Money\n\n## Model M02")
    models += "\n## Model M04 — Money\n\n- MONEY RULE: currency EUR, rounded half-even\n"
    case = tmp_path / "demo"
    case.mkdir()
    for name, body in (("00_product.md", PRODUCT), ("01_models.md", models), ("02_rules.md", RULES)):
        (case / name).write_text(body, encoding="utf-8")
    point = {"subject": "A01", "unit": "A01", "kind": "gap", "text": "counted once", "question": "how?"}

    class Provider:
        name = "fake"

        def __init__(self):
            self.asked: list[str] = []
            self.judged: list[str] = []
            self.reviews = 0

        def complete(self, instruction, text):
            if instruction.startswith("You judge the topics"):
                self.judged.append(text)
                ids = [line.split(":", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                       if line[:1] == "T"]
                return json.dumps({"judgements": [{"id": i, "kind": "indifferent", "why": "x"} for i in ids]}), {}
            if instruction.startswith("You receive the open points"):
                return json.dumps({"groups": [{"topic": "t", "members": [l.split(": ", 1)[0]
                                                                         for l in text.splitlines()]}]}), {}
            self.asked.append(text)
            self.reviews += 1
            return json.dumps({"open_points": [point] if self.reviews <= 2 else []}), {}

    monkeypatch.setattr(service, "layer_context", lambda case, state: {
        "state": state, "owns": [], "carries": [], "gate_findings": [], "materials": [], "ready": True,
        "receives": [], "results": []})
    # the selection for A01 alone is closed over Entry -> Money; the round below (all units
    # open, so read whole by the preamble's fallback) shows reviewers and judge read one input
    t = [(0, "00_product.md", PRODUCT), (1, "01_models.md", models), (2, "02_rules.md", RULES)]
    selection = lp.select(t, 2, units.units(t, 2), ["A01"], {}, None)
    assert "MONEY RULE" in lp.render(selection, t, 2)
    provider = Provider()
    service.ask_round(case, 2, provider)
    assert all("MONEY RULE" in text for text in provider.asked)
    assert provider.judged and "MONEY RULE" in provider.judged[0]
