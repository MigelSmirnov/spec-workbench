"""A fix of State 2 is read for the words the earlier states do not hold.

Experiment of 2026-11-20 (docs/STATE2_REQUIRED_RESULTS_20261120.md): on Portal
Deliverer the fixes that answered a required result added about 85 characters
and no new name; the others brought in file modes, temporary names and library
calls. The report names what a change introduced; it is not a gate.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import design_change_vocabulary as vocabulary

PRODUCT = "# State 0 — Demo\n\nThe owner delivers a photo from the object folder. A repeated delivery writes nothing.\n"
MODELS = "# State 1 — Demo models\n\n## Model M01 — Placement\n\n`source_id` names the content.\n"
RULES = "# State 2 — Demo rules\n\n## Accepted decision A1 — Placement\n\n1. One placement exists per content.\n"


def git(case: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(case), *args], check=True, capture_output=True, text=True).stdout


def make(tmp_path: Path) -> tuple[Path, str]:
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text(PRODUCT, encoding="utf-8")
    (case / "01_models.md").write_text(MODELS, encoding="utf-8")
    (case / "02_rules.md").write_text(RULES, encoding="utf-8")
    git(case, "init", "-q")
    git(case, "config", "user.email", "t@t")
    git(case, "config", "user.name", "t")
    git(case, "add", "-A")
    git(case, "commit", "-q", "-m", "texts")
    return case, git(case, "rev-parse", "HEAD").strip()


def change(case: Path, line: str) -> None:
    (case / "02_rules.md").write_text(RULES + line + "\n", encoding="utf-8")


def test_a_fix_in_the_words_of_the_earlier_states_reports_nothing(tmp_path):
    case, ref = make(tmp_path)
    change(case, "2. After an interrupted delivery a repeated delivery completes the placement of `source_id`.")
    result = vocabulary.report(case, 2, ref)
    assert result["sections"] == [] and vocabulary.main([str(case), "--since", ref, "--strict"]) == 0


def test_a_fix_that_says_how_is_reported_with_its_section(tmp_path):
    case, ref = make(tmp_path)
    change(case, "2. The image is written under a temporary name from `tempfile.mkstemp` with `RECORD_MODE`, "
                 "then renamed; a `test_a_repeat_completes` shows it.")
    row, = vocabulary.report(case, 2, ref)["sections"]
    assert row["section"] == "Accepted decision A1 — Placement"
    assert row["identifiers"] == ["RECORD_MODE", "tempfile.mkstemp"]
    assert row["test_names"] == ["test_a_repeat_completes"]          # a Required tests item may name its test
    assert set(row["mechanism_words"]) == {"temporary", "rename"}
    assert vocabulary.main([str(case), "--since", ref]) == 0          # a report, not a gate
    assert vocabulary.main([str(case), "--since", ref, "--strict"]) == 1


def test_a_word_the_earlier_states_use_is_the_products_own(tmp_path):
    case, ref = make(tmp_path)
    (case / "00_product.md").write_text(PRODUCT + "\nThe owner may lock an object.\n", encoding="utf-8")
    change(case, "2. A locked object delivers nothing, and no file is renamed.")
    row, = vocabulary.report(case, 2, ref)["sections"]
    assert set(row["mechanism_words"]) == {"rename"}                  # "locked" is State 0's word


def test_only_what_the_change_added_is_read(tmp_path):
    case, _ = make(tmp_path)
    change(case, "2. The record is written under a temporary name.")
    git(case, "commit", "-qam", "how")
    ref = git(case, "rev-parse", "HEAD").strip()
    (case / "02_rules.md").write_text((case / "02_rules.md").read_text(encoding="utf-8")
                                      + "3. A replaced photo is a new photo.\n", encoding="utf-8")
    assert vocabulary.report(case, 2, ref)["sections"] == []
    assert vocabulary.report(case, 2, None)["mechanism_words"] == 1   # without --since: the whole text
