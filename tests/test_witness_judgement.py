"""One judgement per check, kept by digest (owner review of #156, 2026-11-08)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import witness_judgement as wj  # noqa: E402

CHECK = "def test_once():\n    assert ledger.record('a') is REFUSED  # INV-001\n"


def material(decision="A01", item="- INV-001: refused. [witness: verification:once]", text=CHECK,
             statements=("INV-001: an entry is counted once",), status="available", reason=None):
    return {"decision": decision, "witness": "verification:once", "item": item, "invariants": ["INV-001"],
            "statements": list(statements), "status": status, "reason": reason,
            "files": [{"path": "verification/once.py", "sha256": wj._sha(text), "text": text}]}


class Provider:
    name = "fake"

    def __init__(self, answer):
        self.answer = answer
        self.calls: list[str] = []

    def complete(self, instruction, text):
        self.calls.append(text)
        return json.dumps(self.answer), {}


def asserts(quote="assert ledger.record('a') is REFUSED  # INV-001", ids=("I1",), outcome="asserts"):
    return {"verdicts": [{"id": i, "outcome": outcome, "quotes": [quote], "why": "refuses a second record"}
                         for i in ids]}


def test_a_judgement_is_kept_by_digest_and_read_back_per_binding(tmp_path):
    materials = [material()]
    provider = Provider(asserts())
    assert wj.verdicts(tmp_path, materials)[0]["outcome"] == "not_checked"   # nothing judged yet
    wj.judge(tmp_path, provider, materials)
    rows = wj.verdicts(tmp_path, materials)
    assert rows[0]["outcome"] == "asserts" and rows[0]["quotes"]
    digest = wj.group(materials)["verification:once"]["digest"]
    assert (tmp_path / "questions" / "checks" / "verification_once" / f"{digest}.json").is_file()
    wj.judge(tmp_path, provider, materials)
    assert len(provider.calls) == 1                                             # current: not judged again


def test_quotes_not_found_in_the_check_leave_the_binding_not_checked(tmp_path):
    materials = [material()]
    wj.judge(tmp_path, Provider(asserts(quote="assert something_else()")), materials)
    row = wj.verdicts(tmp_path, materials)[0]
    assert row["outcome"] == "not_checked" and "not found in the check" in row["reason"]
    wj.judge(tmp_path, Provider({"verdicts": []}), [material(item="- INV-001: other [witness: verification:once]")])
    assert wj.verdicts(tmp_path, [material(item="- INV-001: other [witness: verification:once]")])[0][
        "outcome"] == "not_checked"


def test_does_not_needs_no_quote_and_partial_needs_one(tmp_path):
    materials = [material()]
    wj.judge(tmp_path, Provider({"verdicts": [{"id": "I1", "outcome": "does_not", "quotes": [], "why": "x"}]}),
             materials)
    assert wj.verdicts(tmp_path, materials)[0]["outcome"] == "does_not"
    other = [material(item="- INV-001: again [witness: verification:once]")]
    wj.judge(tmp_path, Provider({"verdicts": [{"id": "I1", "outcome": "partial", "quotes": []}]}), other)
    assert wj.verdicts(tmp_path, other)[0]["outcome"] == "not_checked"


def test_a_check_over_the_input_limit_is_not_judged_and_not_cut(tmp_path, monkeypatch):
    monkeypatch.setattr(wj, "INPUT_LIMIT", 100)
    provider = Provider(asserts())
    record = wj.judge(tmp_path, provider, [material(text=CHECK * 10)])[0]
    assert provider.calls == [] and record["status"] == "not_checked" and "exceed" in record["reason"]
    assert wj.verdicts(tmp_path, [material(text=CHECK * 10)])[0]["outcome"] == "not_checked"


def test_unreadable_material_is_not_judged(tmp_path):
    provider = Provider(asserts())
    unreadable = [material(status="not_checked", reason="the command names no readable file")]
    wj.judge(tmp_path, provider, unreadable)
    assert provider.calls == []
    assert wj.verdicts(tmp_path, unreadable)[0]["reason"] == "the command names no readable file"


def test_the_digest_follows_files_items_and_stated_invariants_only():
    base = wj.group([material()])["verification:once"]["digest"]
    assert wj.group([material(text=CHECK + "# changed\n")])["verification:once"]["digest"] != base
    assert wj.group([material(item="- INV-001: refused twice. [witness: verification:once]")])[
        "verification:once"]["digest"] != base
    assert wj.group([material(statements=("INV-001: an entry is counted once, even on retry",))])[
        "verification:once"]["digest"] != base
    assert wj.group([material(), material(decision="A02")])["verification:once"]["digest"] != base
    assert wj.group([dict(material(), reason="ignored")])["verification:once"]["digest"] == base


def test_every_item_bound_to_a_check_is_judged_in_one_request(tmp_path):
    materials = [material(), material(decision="A07", item="- INV-001: kept. [witness: verification:once]")]
    provider = Provider(asserts(ids=("I1", "I2")))
    wj.judge(tmp_path, provider, materials)
    assert len(provider.calls) == 1 and "I1: A01" in provider.calls[0] and "I2: A07" in provider.calls[0]
    assert "invariant: INV-001: an entry is counted once" in provider.calls[0]
    assert [r["outcome"] for r in wj.verdicts(tmp_path, materials)] == ["asserts", "asserts"]
