"""Navigation over a snapshot of design texts (issue #159, navigation acceptance)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import design_navigate as nav  # noqa: E402

PRODUCT = """# State 0 — Ledger

A ledger for one owner.

## Rules

### R0-01 — One owner (owner, 2026-07-18)

The ledger has exactly one owner; nobody else writes to it.

### R0-02 — Monthly totals (owner, 2026-07-18)

The owner sees totals by calendar month, in euros.

## Currency policy

Amounts are kept in euros, gross.
"""

MODELS = """# State 1 — Models

## Model M01 — Entry

- `amount` Money
- `created_at` datetime

## Model M02 — Money

- euros, rounded half-even
"""

RULES = """# State 2 — Rules

## Accepted decision A01 — totals by month

### Normative rules

Totals follow R0-02; an Entry counts in the month of its created_at.

## Accepted decision A02 — retention

### Normative rules

Entries are kept for ten years.
"""

NO_IDS = """Some words before any heading.

# Notes

## Background

### Detail

Deep text.

## Background

Second background, same title.
"""


def snapshot(tmp_path: Path, extra: list[tuple[str, int | None, str]] = ()) -> nav.Snapshot:
    docs = [("docs/00_product.md", 0, PRODUCT), ("docs/01_models.md", 1, MODELS), ("docs/02_rules.md", 2, RULES),
            *extra]
    nav.write_snapshot(tmp_path, docs)
    return nav.Snapshot(tmp_path)


def test_a_requirement_is_read_alone_and_leads_to_the_decision_that_names_it(tmp_path):
    snap = snapshot(tmp_path)
    assert snap.ids("R0-")["identifiers"] == {"R0-01": ["docs/00_product.md#rules/r0-01-one-owner-owner-2026-07-18"],
                                              "R0-02": ["docs/00_product.md#rules/r0-02-monthly-totals-owner-2026-07-18"]}
    read = snap.read("R0-02")
    assert read["text"].startswith("### R0-02") and "Currency policy" not in read["text"]   # not the whole State 0
    assert read["document"] == "docs/00_product.md" and read["lines"] == [11, 14] and read["snapshot"] == snap.id
    incoming = snap.refs("R0-02")["incoming"]
    assert [(i["key"], i["state"]) for i in incoming] == [
        ("docs/02_rules.md#accepted-decision-a01-totals-by-month/normative-rules", 2)]
    decision = snap.read("A01")
    assert "Totals follow R0-02" in decision["text"] and decision["state"] == 2


def test_a_document_without_ids_is_fully_reachable_through_its_sections(tmp_path):
    snap = snapshot(tmp_path, [("docs/notes.md", None, NO_IDS)])
    sections = snap.toc("docs/notes.md")["documents"][0]["sections"]
    keys = [s["key"] for s in sections]
    assert keys == ["docs/notes.md#preamble", "docs/notes.md#title", "docs/notes.md#background",
                    "docs/notes.md#background/detail", "docs/notes.md#background~2"]
    covered = set()
    for key in keys:
        read = snap.read(key)
        covered |= set(range(read["lines"][0], read["lines"][1] + 1))
    assert covered >= set(range(1, len(NO_IDS.splitlines()) + 1)) - {2}       # every line but blank ones
    assert "Deep text." in snap.read("docs/notes.md#background")["text"]        # nested sections included
    assert "Second background" in snap.read("docs/notes.md#background~2")["text"]
    assert "Second background" not in snap.read("docs/notes.md#background")["text"]


def test_same_local_keys_in_two_documents_stay_apart(tmp_path):
    other = PRODUCT.replace("The ledger has exactly one owner", "ANOTHER DOCUMENT'S OWNER RULE")
    snap = snapshot(tmp_path, [("methodology/00_product.md", None, other)])
    first = snap.read("docs/00_product.md#rules/r0-01-one-owner-owner-2026-07-18")
    second = snap.read("methodology/00_product.md#rules/r0-01-one-owner-owner-2026-07-18")
    assert "exactly one owner" in first["text"] and "ANOTHER DOCUMENT" in second["text"]
    error = None
    try:
        snap.read("R0-01")                                       # defined twice now: ambiguous, never substituted
    except nav.NavigationError as found:
        error = str(found)
    assert error and "defined by several sections" in error


def test_reads_and_quotes_are_bound_to_one_snapshot(tmp_path):
    snap = snapshot(tmp_path)
    key = "R0-02"
    assert snap.verify_quote(key, "The owner sees totals by calendar month", snap.id)
    assert not snap.verify_quote(key, "The owner sees totals by calendar month", "0" * 64)   # another snapshot
    assert not snap.verify_quote(key, "totals by week")
    for target, expected in (("R0-99", "no section key or identifier"), ("docs/00_product.md#nope", "close")):
        try:
            snap.read(target)
            raise AssertionError("read a key that does not resolve")
        except nav.NavigationError as error:
            assert expected in str(error)
    (tmp_path / "docs" / "00_product.md").write_text(PRODUCT.replace("calendar month", "week"), encoding="utf-8")
    changed = nav.Snapshot(tmp_path)
    assert changed.id != snap.id
    try:
        changed.read(key, snap.id)
        raise AssertionError("a read on a stale snapshot id was answered")
    except nav.NavigationError as error:
        assert "is not this snapshot" in str(error)


def test_a_shared_word_is_no_reference_and_a_search_says_so(tmp_path):
    snap = snapshot(tmp_path)
    refs = snap.refs("A02")
    assert refs["outgoing"] == {} and refs["incoming"] == []           # "Entries" shares a word with M01 only
    assert "does not prove that nothing depends" in refs["note"]
    found = snap.search("euros")
    assert {r["document"] for r in found["results"]} == {"docs/00_product.md", "docs/01_models.md"}
    assert found["note"] == "lexical search results, not dependencies"
    assert snap.refs("A01")["outgoing"] == {"Entry": ["docs/01_models.md#model-m01-entry"],
                                            "R0-02": ["docs/00_product.md#rules/r0-02-monthly-totals-owner-2026-07-18"]}


def test_the_command_line_answers_json_with_the_snapshot(tmp_path):
    snap = snapshot(tmp_path)
    run = lambda *args: subprocess.run([sys.executable, str(ROOT / "tools" / "design_navigate.py"), "--root",
                                        str(tmp_path), *args], capture_output=True, text=True)
    read = run("read", "R0-01")
    assert read.returncode == 0 and json.loads(read.stdout)["snapshot"] == snap.id
    missing = run("read", "R0-42")
    assert missing.returncode == 2 and "error" in json.loads(missing.stdout)
