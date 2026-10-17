"""SPEC_STANDARD read one section at a time (Data Closure §3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from notes_authoring import standard

DOC = """# Standard

## Why

Intro.

## 2. notes

Notes rules.

### What to include

Include this.

```text
## 9. not a heading inside a fence
```

## 15. Data

Data intro.

### 15.2 Placement

Place it.

#### 15.2.1 Detail

Detail.

### 15.11 NOT-list

Never this.

### NOT-list

The other one.
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    skill = tmp_path / standard.SKILL
    skill.mkdir(parents=True)
    (skill / standard.STANDARD).write_text(DOC, encoding="utf-8")
    (skill / standard.INDEX).write_text("# Index\n\nStart at §2.\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("ref", ["§15.2", "15.2", "15.2.", " § 15.2 "])
def test_a_numbered_section_comes_with_its_subsections_only(repo, ref):
    found = standard.section(ref, repo)
    assert (found["section"], found["title"]) == ("15.2", "15.2 Placement")
    assert "Detail." in found["text"] and "Never this." not in found["text"]


def test_a_top_section_holds_its_unnumbered_subsections_and_a_fence_is_no_heading(repo):
    found = standard.section("§2", repo)
    assert "Include this." in found["text"] and "## 9. not a heading" in found["text"]
    assert "Data intro." not in found["text"]
    with pytest.raises(ValueError):
        standard.section("9", repo)


def test_a_title_reaches_an_unnumbered_section_and_an_exact_title_wins(repo):
    assert standard.section("what to include", repo)["text"].endswith("```")
    assert standard.section("NOT-list", repo)["text"] == "### NOT-list\n\nThe other one."


def test_an_ambiguous_or_unknown_reference_names_the_candidates(repo):
    with pytest.raises(ValueError, match="2 sections"):
        standard.section("list", repo)
    with pytest.raises(ValueError, match="no sections"):
        standard.section("§42", repo)


def test_the_contents_are_the_index_and_every_heading_below_the_title(repo):
    payload = standard.contents(repo)
    assert payload["index"].startswith("# Index")
    assert [s["section"] for s in payload["sections"]] == [None, "2", None, "15", "15.2", "15.2.1", "15.11", None]


def test_without_a_copy_in_the_repo_the_tools_own_standard_is_read(tmp_path):
    assert standard.section("15.11", tmp_path)["title"].startswith("15.11 ")


def test_the_real_standard_has_the_sections_the_task_points_to():
    for ref in ("§2", "§15", "15.2", "15.3.1", "15.11"):
        assert standard.section(ref)["text"]


def test_a_tilde_fence_or_an_indented_fence_holds_no_heading(tmp_path):
    skill = tmp_path / standard.SKILL
    skill.mkdir(parents=True)
    (skill / standard.STANDARD).write_text(
        "# S\n\n## 2. notes\n\n~~~text\n## 9. inside a tilde fence\n```\n## 8. still inside\n~~~\n\n"
        "   ```\n## 7. inside an indented fence\n   ```\n\n## 3. next\n", encoding="utf-8")
    (skill / standard.INDEX).write_text("# I\n", encoding="utf-8")
    assert [s["section"] for s in standard.contents(tmp_path)["sections"]] == ["2", "3"]
    assert "## 7. inside an indented fence" in standard.section("2", tmp_path)["text"]


def test_a_number_with_its_title_names_the_section_and_a_wrong_title_does_not(repo):
    assert standard.section("§15.2 Placement", repo)["section"] == "15.2"
    with pytest.raises(ValueError):
        standard.section("§15.2 NOT-list", repo)


def test_words_that_start_with_digits_are_still_a_title(tmp_path):
    skill = tmp_path / standard.SKILL
    skill.mkdir(parents=True)
    (skill / standard.STANDARD).write_text("# S\n\n## 2. notes\n\n### Лимит 200 строк\n\nText.\n", encoding="utf-8")
    (skill / standard.INDEX).write_text("# I\n", encoding="utf-8")
    assert standard.section("200 строк", tmp_path)["title"] == "Лимит 200 строк"
    assert standard.section("2", tmp_path)["section"] == "2"


def test_a_number_naming_a_section_with_another_section_s_title_refuses(repo):
    with pytest.raises(ValueError):
        standard.section("2 Placement", repo)


def test_a_closing_fence_carries_only_blanks_and_a_backtick_info_holds_no_backtick(tmp_path):
    skill = tmp_path / standard.SKILL
    skill.mkdir(parents=True)
    (skill / standard.STANDARD).write_text(
        "# S\n\n## 2. notes\n\n```text\n```python\n## 9. still inside\n```\n\n"
        "```code``` inline\n\n## 3. next\n", encoding="utf-8")
    (skill / standard.INDEX).write_text("# I\n", encoding="utf-8")
    assert [s["section"] for s in standard.contents(tmp_path)["sections"]] == ["2", "3"]


def test_a_dotted_number_is_always_a_section_reference(repo):
    with pytest.raises(ValueError):
        standard.section("5.2 Placement", repo)
