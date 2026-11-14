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
    assert "What you read: the units of State 2 under review" in instruction
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


# ---- the main causes of whole-text fallback on client-portal (#147 comment 6721261089)

PRODUCT_WITH_DECISIONS = """# State 0 — Demo product

## Principals

### StaffAccount

A staff member signs in.

### ServicePrincipal

A service calls in.

## Primary outcomes

### Operator management

An operator sets progress.

## Decisions

Numbered so later states can cite them.

### R0-01 — Sole trader

Few projects.

### R0-23 — No email challenge

No password reset.
"""


def test_state0_has_no_earlier_state_and_never_falls_back():
    t = [(0, "00_product.md", PRODUCT_WITH_DECISIONS)]
    selection = lp.select(t, 0, units.units(t, 0), ["00_product.md:Decisions"], {}, None)
    assert selection.whole == []


def test_a_cited_r0_decision_brings_its_own_level3_passage_not_the_whole_section():
    models = "# State 1 — Models\n\n## Model M06 — StaffSession\n\nNo password reset exists (R0-23).\n"
    t = [(0, "00_product.md", PRODUCT_WITH_DECISIONS), (1, "01_models.md", models)]
    selection = lp.select(t, 1, units.units(t, 1), ["01_models.md:Model M06 — StaffSession"], {}, None)
    received = [key for _, _, key, _ in selection.received]
    assert selection.whole == []
    assert received == ["00_product.md:Decisions / R0-23 — No email challenge"]
    assert "### R0-23 — No email challenge\n\nNo password reset.\n" in lp.render(selection, t, 1)   # verbatim


def test_model_numbers_quoted_titles_and_id_fields_resolve():
    models = ("# State 1 — Models\n\n## Model M14 — ServiceCredential\n\n- `service_principal_id: UUID`\n\n"
              "## Model M32 — SectionProgress\n\n- `percent: int`\n")
    rules = ("# State 2 — Rules\n\n## Accepted decision A20 — Progress\n\n"
             "Product text of State 0 (\"Primary outcomes\") and M32.\n")
    t = [(0, "00_product.md", PRODUCT_WITH_DECISIONS), (1, "01_models.md", models), (2, "02_rules.md", rules)]
    selection = lp.select(t, 2, units.units(t, 2), ["A20"], {}, None)
    received = [key for _, _, key, _ in selection.received]
    assert "01_models.md:Model M32 — SectionProgress" in received                     # M32
    assert "00_product.md:Primary outcomes" in received                                # quoted title
    selection = lp.select(t, 1, units.units(t, 1), ["01_models.md:Model M14 — ServiceCredential"], {}, None)
    assert [key for _, _, key, _ in selection.received] == ["00_product.md:Principals / ServicePrincipal"]


def test_a_qualified_operation_heading_defines_its_own_name_only():
    assert lp.defined("x", "## `public_op:derived_views.build_budget_view`\n") == {"build_budget_view"}
    assert "api" in lp.defined("30_modules.md:`api`", "## `api`\n\nRoutes.\n")


def test_the_closure_runs_through_models_and_decisions_not_through_modules():
    modules = ("# State 3 — Modules\n\n## `ledger`\n\nOwns A01 and A03.\n\n## `reports`\n\nOwns A02.\n")
    flows = "# State 4 — Flows\n\n## `flow:record`\n\n1. `ledger` records an entry.\n"
    t = [*texts(), (3, "30_modules.md", modules), (4, "40_flows.md", flows)]
    selection = lp.select(t, 4, units.units(t, 4), ["40_flows.md:`flow:record`"], {}, None)
    received = [key for _, _, key, _ in selection.received]
    assert "30_modules.md:`ledger`" in received                     # named by the open unit
    assert "A01" in received and "A03" in received                  # named by the module: one step
    assert "01_models.md:Model M01 — Entry" in received             # A01 -> Entry: the closure goes on
    assert "30_modules.md:`reports`" not in received                # never reached through a module


# ---------------------------------------------------------------------------
# What the reviews read is recorded; the route is a reading a probe measures
# ---------------------------------------------------------------------------

def _closure_texts():
    models = MODELS.replace("- `created_at` datetime\n\n## Model M02",
                            "- `created_at` datetime\n- `amount` Money\n\n## Model M02")
    models += "\n## Model M04 — Money\n\n- currency EUR, rounded half-even\n"
    return [(0, "00_product.md", PRODUCT), (1, "01_models.md", models), (2, "02_rules.md", RULES)]


def test_the_selection_says_how_far_each_passage_is_from_an_open_unit():
    t = _closure_texts()
    selection = lp.select(t, 2, units.units(t, 2), ["A01"], {}, None)
    assert selection.depth["01_models.md:Model M01 — Entry"] == 0          # A01 names Entry
    assert selection.depth["01_models.md:Model M04 — Money"] == 1          # Entry -> Money
    assert selection.named_by["01_models.md:Model M04 — Money"] == "01_models.md:Model M01 — Entry"
    assert [u[2] for u in selection.direct] == [k for k, d in selection.depth.items() if d == 0]
    kept = lp.record(selection, lp.render(selection, t, 2))
    assert kept["reading"] == "selection" and kept["whole"] == [] and kept["own"] == ["A01"]
    assert {"state": 1, "key": "01_models.md:Model M04 — Money", "characters": len(
        "## Model M04 — Money\n\n- currency EUR, rounded half-even\n"), "depth": 1} in kept["received"]
    assert kept["received_characters"] == sum(r["characters"] for r in kept["received"])


def test_the_route_gives_the_direct_links_inline_and_indexes_every_other_earlier_passage():
    t = _closure_texts()
    selection = lp.select(t, 2, units.units(t, 2), ["A01"], {}, None)
    text = lp.render_route(selection, t, 2, "states")
    inline, route = text.split("=== ROUTE:")
    assert "## Model M01 — Entry" in inline and "## Model M04 — Money" not in inline
    # one step away: listed with the given passage that names it
    assert ("- states/01_models.md · Model M04 — Money" in route
            and "named by 01_models.md:Model M01 — Entry" in route)
    # a section no identifier names is never selected; the route still lists it
    assert "- states/00_product.md · Currency policy" in route
    assert "rounded half-even" not in text and "Amounts are kept in euros" not in text
    kept = lp.record(selection, text, lp.ROUTE)
    assert [r["key"] for r in kept["received"]] == [u[2] for u in selection.direct]


def test_the_route_never_falls_back_to_the_whole_texts():
    t = texts()
    selection = lp.select(t, 2, units.units(t, 2), ["A03"], {}, None)   # A03 names nothing
    assert selection.whole
    text = lp.render_route(selection, t, 2, "states")
    assert "Amounts are kept in euros" not in text and "- states/00_product.md · Currency policy" in text
    assert "no passage inline" in lp.route_note(selection, 2, ["states/00_product.md"])


class _Reviews:
    name = "fake"

    def __init__(self):
        self.asked: list[tuple[str, str, dict]] = []

    def complete(self, instruction, text):
        if instruction.startswith("You judge the topics"):
            return json.dumps({"judgements": []}), {}
        if instruction.startswith("You receive the open points"):
            return json.dumps({"groups": []}), {}
        self.asked.append((instruction, text, {}))
        return json.dumps({"open_points": []}), {}


class _FileReviews(_Reviews):
    reads_files = True

    def complete_with_files(self, instruction, text, files):
        self.asked.append((instruction, text, files))
        return json.dumps({"open_points": []}), {}


def _demo(tmp_path, monkeypatch):
    case = tmp_path / "demo"
    case.mkdir()
    for _, name, body in texts():
        (case / name).write_text(body, encoding="utf-8")
    monkeypatch.setattr(service, "layer_context", lambda case, state: {
        "state": state, "owns": [], "carries": [], "gate_findings": [], "materials": [], "ready": True,
        "receives": [], "results": []})
    return case


def test_a_round_keeps_what_its_reviews_read(tmp_path, monkeypatch):
    case = _demo(tmp_path, monkeypatch)
    provider = _Reviews()
    summary = service.ask_round(case, 2, provider)
    kept = summary["reviews_read"]
    instruction, text, _ = provider.asked[0]
    assert kept["reading"] == "selection"
    assert kept["text_characters"] == len(text) and kept["instruction_characters"] == len(instruction)
    assert any("A03 names nothing" in reason for reason in kept["whole"])   # the fallback is on record
    assert json.loads((case / "questions/state2/round-01/summary.json").read_text())["reviews_read"] == kept


def test_a_document_probe_asks_named_units_and_records_nothing_in_the_case(tmp_path, monkeypatch):
    case = _demo(tmp_path, monkeypatch)
    provider = _Reviews()
    summary = service.probe_round(case, 2, provider, tmp_path / "probe", modules=["A01"])
    assert summary["scope"] == ["A01"] and summary["reading"] == "selection"
    assert not (case / "questions").exists()
    assert summary["reviews_read"]["whole"] == [] and (tmp_path / "probe" / "summary.json").is_file()
    assert [r["kind"] for r in summary["requests"]] == ["review"] * 3
    assert "Model M01 — Entry" in provider.asked[0][1] and "Currency policy" not in provider.asked[0][1]


def test_a_route_probe_gives_the_earlier_states_as_files(tmp_path, monkeypatch):
    case = _demo(tmp_path, monkeypatch)
    provider = _FileReviews()
    summary = service.probe_round(case, 2, provider, tmp_path / "probe", modules=["A03"], reading="route")
    instruction, text, files = provider.asked[0]
    assert sorted(files) == ["states/00_product.md", "states/01_models.md"]      # the earlier states, whole
    assert files["states/00_product.md"] == PRODUCT
    assert "=== ROUTE:" in text and "Amounts are kept in euros" not in text
    assert "follow the route" in instruction and "their texts whole, because" not in instruction
    assert summary["reviews_read"]["files"] == {name: len(body) for name, body in files.items()}
    assert summary["requests"][0]["file_chars"] == len(PRODUCT) + len(texts()[1][2])


def test_a_document_probe_refuses(tmp_path, monkeypatch):
    import pytest

    case = _demo(tmp_path, monkeypatch)
    for kwargs, match in (({"reading": "route"}, "needs a provider that reads files"),
                          ({"modules": ["context"]}, "not units of State 2 a probe asks"),
                          ({"reading": "all"}, "unknown reading")):
        with pytest.raises(service.QuestionRoundError, match=match):
            service.probe_round(case, 2, _Reviews(), tmp_path / "probe", **kwargs)
    assert not (tmp_path / "probe").exists()
