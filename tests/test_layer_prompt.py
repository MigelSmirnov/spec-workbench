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
    assert selection.whole and "A03 names no identifier" in selection.whole[0]
    assert "=== 00_product.md (State 0), whole ===" in text and "Model M03" in text
    assert "whole, because A03 names no identifier" in lp.note(selection, 2)


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
    assert "their texts whole, because" in instruction and "A03 names no identifier" in instruction
