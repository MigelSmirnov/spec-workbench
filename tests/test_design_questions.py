from __future__ import annotations

import json
from pathlib import Path

import pytest

import design_questions
from questions_workbench import documents, judge, provider, service


QUOTED_GAP = {"kind": "consequential_gap", "quotes": ["## Model M01 — Thing"], "divergence": "a or b; the owner notices"}
UNQUOTED_GAP = {"kind": "consequential_gap", "divergence": "a or b; the owner notices"}


class FakeProvider:
    """Answers reviews from a script, groups points by their subject, and judges
    every topic with `verdict` (by default a consequential gap quoting a passage)."""

    name = "fake"

    def __init__(self, reviews: list[list[dict]], verdict: dict | None = None):
        self.reviews = list(reviews)
        self.verdict = verdict or QUOTED_GAP
        self.judged: list[str] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            ids = [line.split(":", 1)[0] for line in text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
                   if line[:1] == "T"]
            return json.dumps({"judgements": [{"id": i, **self.verdict} for i in ids]}), {}
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                subject = rest[1:rest.index("]")]
                groups.setdefault(subject, []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        return json.dumps({"open_points": self.reviews.pop(0)}), {"total_tokens": 1}


def _case(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "00_product.md").write_text("# State 0 — Demo\n\nA product.\n", encoding="utf-8")
    (case / "01_models.md").write_text("# State 1 — Demo models\n\n## Model M01 — Thing\n", encoding="utf-8")
    (case / "02_rules.md").write_text("# State 2 — Demo rules\n", encoding="utf-8")
    (case / "notes.md").write_text("no state heading\n", encoding="utf-8")
    return case


def _point(subject: str) -> dict:
    return {"subject": subject, "kind": "identity", "text": "x", "question": f"who mints {subject}?",
            "options": [], "default_guess": "uuid"}


def test_documents_are_the_states_up_to_the_asked_one(tmp_path):
    case = _case(tmp_path)
    assert [p.name for _, p in documents.design_documents(case, 1)] == ["00_product.md", "01_models.md"]


def test_every_design_state_but_the_contracts_declares_a_question_scope():
    # State 6's contracts are asked inside State 7's module prompts (QUESTIONS.md)
    for state in (0, 1, 2, 3, 4, 5, 7):
        assert documents.question_scope(state)
    assert documents.question_states() == [0, 1, 2, 3, 4, 5, 7]


def test_a_topic_raised_by_two_reviews_keeps_the_state_open(tmp_path):
    case = _case(tmp_path)
    provider = FakeProvider([[_point("M01")], [_point("M01"), _point("M02")], []])
    summary = service.ask_round(case, 1, provider)
    assert summary["closed"] is False
    assert summary["repeated_topics"] == 1
    assert len(summary["topics"][0]["runs"]) == 2  # reviews run in parallel: which two is not fixed
    assert (case / "questions" / "state1" / "round-01" / "review-3.json").is_file()
    assert service.status(case, 1)["closed"] is False


def test_single_review_topics_close_the_state_until_the_texts_change(tmp_path):
    case = _case(tmp_path)
    service.ask_round(case, 1, FakeProvider([[_point("M01")], [_point("M02")], []]))
    assert service.status(case, 1)["closed"] is False  # one clear round is not enough
    service.ask_round(case, 1, FakeProvider([[_point("M01")], [_point("M02")], []]))
    assert service.status(case, 1)["closed"] is True
    (case / "01_models.md").write_text("# State 1 — Demo models\n\nchanged\n", encoding="utf-8")
    result = service.status(case, 1)
    assert result["closed"] is False and result["stale"] is True


def test_rounds_are_numbered_and_kept(tmp_path):
    case = _case(tmp_path)
    service.ask_round(case, 1, FakeProvider([[], [], []]))
    service.ask_round(case, 1, FakeProvider([[], [], []]))
    assert service.status(case, 1)["round"] == "round-02"


def test_a_round_needs_the_state_document_and_two_reviews(tmp_path):
    case = _case(tmp_path)
    with pytest.raises(service.QuestionRoundError):
        service.ask_round(case, 3, FakeProvider([[], [], []]))
    with pytest.raises(service.QuestionRoundError):
        service.ask_round(case, 1, FakeProvider([[]]), runs=1)


def test_status_without_a_round_is_open(tmp_path, capsys):
    case = _case(tmp_path)
    assert design_questions.main(["status", str(case), "--state", "1"]) == 1
    assert "no question round yet" in capsys.readouterr().out


def _clear_provider_env(monkeypatch):
    # setenv first so monkeypatch restores even what the loader sets afterwards
    for name in ("OPENAI_API_KEY", "DESIGN_QUESTIONS_ENV_FILE", "CODE_FACTORY_ENV_FILE", "DESIGN_QUESTIONS_MODEL"):
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)


def test_env_is_taken_from_the_nearest_dotenv_above_the_working_directory(tmp_path, monkeypatch):
    _clear_provider_env(monkeypatch)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=outer\n", encoding="utf-8")
    inner = tmp_path / "repo" / "case"
    inner.mkdir(parents=True)
    (tmp_path / "repo" / ".env").write_text("# provider\nOPENAI_API_KEY='inner'\n", encoding="utf-8")
    monkeypatch.chdir(inner)
    provider.load_env_file()
    assert provider.os.environ["OPENAI_API_KEY"] == "inner"


def test_named_env_file_is_the_only_one_read(tmp_path, monkeypatch):
    _clear_provider_env(monkeypatch)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=nearest\n", encoding="utf-8")
    named = tmp_path / "named.env"
    named.write_text("DESIGN_QUESTIONS_MODEL=m\n", encoding="utf-8")
    monkeypatch.setenv("DESIGN_QUESTIONS_ENV_FILE", str(named))
    monkeypatch.chdir(tmp_path)
    provider.load_env_file()
    assert provider.os.environ["DESIGN_QUESTIONS_MODEL"] == "m"
    assert "OPENAI_API_KEY" not in provider.os.environ


def test_environment_wins_over_dotenv(tmp_path, monkeypatch):
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    (tmp_path / ".env").write_text("OPENAI_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    provider.load_env_file()
    assert provider.os.environ["OPENAI_API_KEY"] == "from-env"


def _repeated(case, verdict, since=None):
    provider = FakeProvider([[_point("M01")], [_point("M01")], []], verdict)
    return service.ask_round(case, 1, provider, since=since), provider


def test_a_judged_non_blocking_topic_with_evidence_leaves_the_round_clear(tmp_path):
    case = _case(tmp_path)
    summary, provider = _repeated(case, {"kind": "answered", "quotes": ["## Model M01 — Thing"]})
    assert summary["repeated_topics"] == 1 and summary["blocking_topics"] == 0 and summary["clear"] is True
    assert summary["topics"][0]["judgement"]["verified"] is True
    assert "who mints M01?" in provider.judged[0]


def test_two_clear_rounds_on_the_same_texts_close_the_state(tmp_path):
    case = _case(tmp_path)
    verdict = {"kind": "later_state", "later_state": 6}
    assert _repeated(case, verdict)[0]["closed"] is False
    assert _repeated(case, verdict)[0]["closed"] is True
    assert service.status(case, 1)["closed"] is True


def test_a_clear_round_after_a_text_change_starts_the_count_again(tmp_path):
    case = _case(tmp_path)
    verdict = {"kind": "indifferent", "why": "no caller acts on it"}
    _repeated(case, verdict)
    (case / "01_models.md").write_text("# State 1 — Demo models\n\n## Model M01 — Thing\n\nmore\n", encoding="utf-8")
    assert _repeated(case, verdict)[0]["closed"] is False


@pytest.mark.parametrize("verdict, failure", [
    ({"kind": "answered", "quotes": ["a passage nobody wrote anywhere"]}, "not found verbatim"),
    ({"kind": "answered", "quotes": []}, "not found verbatim"),
    ({"kind": "contradiction", "quotes": ["## Model M01 — Thing"]}, "two quotes"),
    ({"kind": "later_state", "later_state": 1}, "after 1"),
    ({"kind": "indifferent", "why": ""}, "no one acts"),
    ({"kind": "preexisting", "quotes": ["## Model M01 — Thing"]}, "only for a reopened state"),
    ({"kind": "obvious"}, "unknown kind"),
])
def test_a_judgement_whose_evidence_fails_blocks(tmp_path, verdict, failure):
    case = _case(tmp_path)
    summary, _ = _repeated(case, verdict)
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and judgement["verified"] is False
    assert failure in judgement["failure"]
    assert summary["clear"] is False


def test_contradiction_and_consequential_gap_block_even_when_verified(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated(case, {"kind": "contradiction", "quotes": ["# State 0 — Demo", "## Model M01 — Thing"]})
    assert summary["topics"][0]["judgement"]["verified"] is True
    assert summary["blocking_topics"] == 1
    summary, _ = _repeated(case, QUOTED_GAP)
    assert summary["topics"][0]["judgement"]["verified"] is True
    assert summary["blocking_topics"] == 1 and summary["deferred_topics"] == 0


def test_a_consequential_gap_that_quotes_no_passage_is_deferred_not_blocking(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated(case, UNQUOTED_GAP)
    judgement = summary["topics"][0]["judgement"]
    assert judgement["verified"] is True and judgement["blocking"] is False
    assert judgement["deferred_to"] == "State 6 contracts or State 7 notes"
    assert summary["clear"] is True and summary["deferred_topics"] == 1 and summary["blocking_topics"] == 0


def test_a_consequential_gap_whose_quote_is_not_in_the_texts_blocks_unverified(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated(case, {**QUOTED_GAP, "quotes": ["a passage nobody wrote anywhere"]})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "not found verbatim" in judgement["failure"]
    assert "deferred_to" not in judgement


def test_an_unquoted_gap_after_state_5_still_blocks(tmp_path):
    from questions_workbench import judge
    kept = judge.check(UNQUOTED_GAP, 6, "texts", None)
    assert kept["blocking"] is True and "deferred_to" not in kept


def test_a_deferred_gap_followed_as_precedent_stays_deferred(tmp_path):
    case = _case(tmp_path)
    _repeated(case, UNQUOTED_GAP)
    summary, _ = _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is False and judgement["deferred_to"] == "State 6 contracts or State 7 notes"
    assert summary["deferred_topics"] == 1


def test_no_repeated_topic_asks_no_judge(tmp_path):
    case = _case(tmp_path)
    provider = FakeProvider([[_point("M01")], [_point("M02")], []])
    assert service.ask_round(case, 1, provider)["clear"] is True
    assert provider.judged == []


def _git_case(tmp_path):
    import subprocess
    case = _case(tmp_path)
    run = lambda *a: subprocess.run(["git", "-C", str(case), *a], check=True, capture_output=True)
    run("init", "-q")
    run("-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "closed")
    (case / "01_models.md").write_text("# State 1 — Demo models\n\n## Model M01 — Thing\n\nNew fact.\n", encoding="utf-8")
    return case


def test_a_reopened_state_sees_the_change_and_may_set_aside_untouched_passages(tmp_path):
    case = _git_case(tmp_path)
    summary, provider = _repeated(case, {"kind": "preexisting", "quotes": ["## Model M01 — Thing"]}, since="HEAD")
    assert summary["since"] == "HEAD" and summary["clear"] is True
    assert "+New fact." in provider.judged[0]


def test_preexisting_needs_the_quote_in_both_versions(tmp_path):
    case = _git_case(tmp_path)
    summary, _ = _repeated(case, {"kind": "preexisting", "quotes": ["## Model M01 — Thing New fact."]}, since="HEAD")
    assert summary["topics"][0]["judgement"]["blocking"] is True


def test_an_unknown_since_ref_is_refused(tmp_path):
    case = _git_case(tmp_path)
    with pytest.raises(service.QuestionRoundError):
        _repeated(case, {"kind": "answered", "quotes": []}, since="no-such-ref")


def test_rounds_kept_before_the_judge_keep_their_rule(tmp_path):
    case = _case(tmp_path)
    directory = service.rounds_dir(case, 1) / "round-01"
    directory.mkdir(parents=True)
    digests = {p.name: __import__("hashlib").sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
               for _, p in documents.design_documents(case, 1)}
    (directory / "summary.json").write_text(json.dumps({
        "schema_version": "spec_workbench_question_round.v1", "state": 1, "round": "round-01",
        "documents": digests, "reviews": 3, "points": [0, 0, 0], "closed": True, "repeated_topics": 0,
        "topics": []}), encoding="utf-8")
    result = service.status(case, 1)
    assert result["closed"] is True and result["carried"] is True
    # the closure is carried to every unit, so there is nothing left to ask
    with pytest.raises(service.QuestionRoundError, match="nothing to ask"):
        _repeated(case, {"kind": "later_state", "later_state": 6})


class FilesProvider(FakeProvider):
    """A provider that, like the Codex CLI, can search files it is given."""

    reads_files = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files: list[dict[str, str]] = []
        self.instructions: list[str] = []

    def complete_with_files(self, instruction: str, text: str, files: dict[str, str]):
        self.files.append(dict(files))
        self.instructions.append(instruction)
        return self.complete(instruction, text)


def _repeated_with_files(case, verdict):
    provider = FilesProvider([[_point("M01")], [_point("M01")], []], verdict)
    return service.ask_round(case, 1, provider), provider


def test_later_documents_are_the_states_after_the_asked_one(tmp_path):
    case = _case(tmp_path)
    assert [p.name for _, p in documents.later_documents(case, 1)] == ["02_rules.md"]
    assert documents.later_documents(case, 2) == []


def test_a_judge_that_reads_files_gets_the_later_states_and_may_find_a_topic_decided_there(tmp_path):
    case = _case(tmp_path)
    summary, provider = _repeated_with_files(case, {"kind": "answered_later", "quotes": ["# State 2 — Demo rules"]})
    assert provider.files == [{"02_rules.md": "# State 2 — Demo rules\n"}]
    assert "later/02_rules.md" in provider.instructions[0]
    assert "# State 2 — Demo rules" not in provider.judged[0]  # searched, not pasted
    judgement = summary["topics"][0]["judgement"]
    assert judgement["verified"] is True and summary["clear"] is True
    assert set(summary["judge"]["later_documents"]) == {"02_rules.md"}


def test_answered_later_needs_its_quote_in_the_later_states(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated_with_files(case, {"kind": "answered_later", "quotes": ["## Model M01 — Thing"]})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "later states' texts" in judgement["failure"]


def test_a_gap_quoting_only_a_later_state_is_deferred_there(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated_with_files(case, {**UNQUOTED_GAP, "quotes": ["# State 2 — Demo rules"]})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["verified"] is True and judgement["blocking"] is False
    assert judgement["quoted_elsewhere"] is True and judgement["deferred_to"]


def test_a_gap_quoting_only_an_earlier_state_does_not_block_this_one(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated(case, {**UNQUOTED_GAP, "quotes": ["# State 0 — Demo"]})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is False and judgement["quoted_elsewhere"] is True


def test_a_contradiction_between_earlier_states_still_blocks(tmp_path):
    case = _case(tmp_path)
    (case / "02_rules.md").write_text("# State 2 — Demo rules\n\nA rule of its own here.\n", encoding="utf-8")
    provider = FakeProvider([[_point("M01")], [_point("M01")], []],
                            {"kind": "contradiction", "quotes": ["# State 0 — Demo", "## Model M01 — Thing"]})
    summary = service.ask_round(case, 2, provider)
    assert summary["topics"][0]["judgement"]["blocking"] is True


def test_a_gap_quoting_this_state_and_a_later_one_still_blocks(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated_with_files(case, {**UNQUOTED_GAP, "quotes": ["# State 2 — Demo rules", "## Model M01 — Thing"]})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["verified"] is True and judgement["blocking"] is True and "deferred_to" not in judgement


def test_a_gap_quoting_a_later_state_without_its_texts_is_unverified(tmp_path):
    case = _case(tmp_path)
    summary, _ = _repeated(case, {**UNQUOTED_GAP, "quotes": ["# State 2 — Demo rules"]})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "not found verbatim" in judgement["failure"]


def test_a_judge_without_files_cannot_answer_from_later_states(tmp_path):
    case = _case(tmp_path)
    summary, provider = _repeated(case, {"kind": "answered_later", "quotes": ["# State 2 — Demo rules"]})
    assert "answered_later" not in provider.judged[0]
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "only when" in judgement["failure"]
    assert "later_documents" not in summary["judge"]


def test_codex_provider_with_files_offers_only_those_under_later(monkeypatch):
    seen = {}

    def fake_run(command, input, cwd, capture_output, text, timeout):
        seen["files"] = sorted(str(p.relative_to(cwd)) for p in Path(cwd).rglob("*") if p.is_file())
        seen["body"] = (Path(cwd) / "later" / "80_notes.md").read_text(encoding="utf-8")
        seen["prompt"] = input
        seen["sandbox"] = command[command.index("--sandbox") + 1]
        Path(command[command.index("-o") + 1]).write_text('{"judgements": []}', encoding="utf-8")
        return provider.subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(provider.subprocess, "run", fake_run)
    asked = provider.CodexCliProvider("m", "low")
    assert asked.reads_files is True
    answer, _ = asked.complete_with_files("JUDGE", "TOPICS", {"80_notes.md": "NOTE TEXT"})
    assert answer == '{"judgements": []}'
    assert seen["files"] == ["later/80_notes.md"] and seen["body"] == "NOTE TEXT"
    assert seen["sandbox"] == "read-only"
    assert "later/80_notes.md" in seen["prompt"] and "NOTE TEXT" not in seen["prompt"]


def test_a_topic_judged_non_blocking_before_may_follow_that_judgement(tmp_path):
    case = _case(tmp_path)
    _repeated(case, {"kind": "answered", "quotes": ["## Model M01 — Thing"]})
    summary, provider = _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    assert "=== PRIOR JUDGEMENTS" in provider.judged[0] and "P1 (round-01, answered): M01" in provider.judged[0]
    judgement = summary["topics"][0]["judgement"]
    assert judgement["verified"] is True and summary["clear"] is True
    assert judgement["precedent"]["kind"] == "answered" and judgement["precedent"]["round"] == "round-01"


def test_a_followed_precedent_passes_on_its_original_judgement(tmp_path):
    case = _case(tmp_path)
    _repeated(case, {"kind": "answered", "quotes": ["## Model M01 — Thing"]})
    _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    # Two clear rounds closed every unit; an edit away from the quoted passage reopens one.
    (case / "00_product.md").write_text("# State 0 — Demo\n\nA changed product.\n", encoding="utf-8")
    _, provider = _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    assert "P1 (round-01, answered): M01" in provider.judged[0]


def test_judged_before_needs_an_offered_precedent(tmp_path):
    case = _case(tmp_path)
    summary, provider = _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    assert "=== PRIOR JUDGEMENTS" not in provider.judged[0]
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "prior judgements offered" in judgement["failure"]


def test_a_blocking_judgement_is_no_precedent(tmp_path):
    case = _case(tmp_path)
    _repeated(case, QUOTED_GAP)
    _, provider = _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    assert "=== PRIOR JUDGEMENTS" not in provider.judged[0]


def test_a_precedent_whose_quoted_passage_changed_no_longer_holds(tmp_path):
    case = _case(tmp_path)
    _repeated(case, {"kind": "answered", "quotes": ["## Model M01 — Thing"]})
    (case / "01_models.md").write_text("# State 1 — Demo models\n\n## Model M01 — Item\n", encoding="utf-8")
    summary, provider = _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    # A stale precedent is not offered, so the topic is judged afresh; a judge
    # that names it anyway is still refused.
    assert "=== PRIOR JUDGEMENTS" not in provider.judged[0]
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "prior judgements offered" in judgement["failure"]


def test_precedent_holds_only_where_its_check_looks():
    answered = {"kind": "answered", "quotes": ["## Model M01 — Thing"]}
    assert judge.precedent_holds(answered, "## Model M01 — Thing\n")
    assert not judge.precedent_holds(answered, "## Model M01 — Item\n")
    later = {"kind": "answered_later", "quotes": ["parse: [BEHAVIOR] MUST return it."]}
    assert judge.precedent_holds(later, "state text", "parse: [BEHAVIOR] MUST return it.")
    assert not judge.precedent_holds(later, "parse: [BEHAVIOR] MUST return it.", None)
    assert not judge.precedent_holds(later, "state text", "parse: [BEHAVIOR] Returns it.")


def test_precedents_come_from_the_latest_judged_rounds_only(tmp_path):
    case = _case(tmp_path)
    _repeated(case, {"kind": "answered", "quotes": ["## Model M01 — Thing"]})
    for _ in range(service.PRECEDENT_ROUNDS):
        _repeated(case, QUOTED_GAP)
    assert service._precedents(case, 1) == []


def test_codex_provider_asks_once_in_an_empty_directory_and_names_itself(monkeypatch):
    calls = []

    def fake_run(command, input, cwd, capture_output, text, timeout):
        calls.append((command, input, cwd))
        assert list(Path(cwd).iterdir()) == []
        Path(command[command.index("-o") + 1]).write_text('{"open_points": []}', encoding="utf-8")
        return provider.subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(provider.subprocess, "run", fake_run)
    asked = provider.CodexCliProvider("some-model", "high")
    answer, usage = asked.complete("INSTRUCTION", "DESIGN TEXT")

    assert answer == '{"open_points": []}' and usage == {}
    assert asked.name == "codex-cli:some-model:high"
    command, prompt, _ = calls[0]
    for flag in ("--ephemeral", "--ignore-user-config", "--skip-git-repo-check"):
        assert flag in command
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert command[command.index("-m") + 1] == "some-model"
    assert "INSTRUCTION" in prompt and "DESIGN TEXT" in prompt


def test_codex_provider_failure_is_a_runtime_error(monkeypatch):
    monkeypatch.setattr(
        provider.subprocess, "run",
        lambda command, **kwargs: provider.subprocess.CompletedProcess(command, 1, "", "model not supported"),
    )
    with pytest.raises(RuntimeError, match="model not supported"):
        provider.CodexCliProvider("m", "low").complete("I", "T")


def test_the_cli_chooses_the_codex_provider():
    args = design_questions.argparse.Namespace(provider="codex", model="m", reasoning="low")
    assert isinstance(design_questions._provider(args), provider.CodexCliProvider)
    args.provider = "openai"
    assert isinstance(design_questions._provider(args), provider.OpenAIProvider)


def test_an_unverified_follow_of_a_deferred_precedent_is_not_deferred(tmp_path):
    case = _case(tmp_path)
    _repeated(case, {**UNQUOTED_GAP, "quotes": ["# State 0 — Demo"]})
    (case / "00_product.md").write_text("# State 0 — Other\n\nA product.\n", encoding="utf-8")
    summary, _ = _repeated(case, {"kind": "judged_before", "precedent": "P1"})
    judgement = summary["topics"][0]["judgement"]
    assert judgement["blocking"] is True and "deferred_to" not in judgement and summary["deferred_topics"] == 0


def test_round_100_comes_after_round_99(tmp_path):
    case = _case(tmp_path)
    for number in (99, 100):
        directory = case / "questions" / "state1" / f"round-{number}"
        directory.mkdir(parents=True)
        (directory / "summary.json").write_text(json.dumps({
            "round": f"round-{number}", "documents": {}, "closed": False, "clear": True,
            "repeated_topics": 0, "topics": []}), encoding="utf-8")
    assert service.status(case, 1)["round"] == "round-100"


def test_the_judge_is_given_the_scope_of_the_state_it_judges():
    """Cabinet Kernel State 0 round-01 (2026-10-10): the reviewers had the State 0
    scope, the judge did not, and blocked State 0 on acceptance mechanics that
    belong to the rules of State 2. The judge reads the same stop rule, and a
    topic outside it is later_state, never blocking here."""
    from questions_workbench import documents, prompts

    scope = documents.question_scope(0)
    instruction = prompts.judge_instruction(0, False, None, False, scope)
    assert scope in instruction
    assert "does not keep State 0 open" in instruction
    assert '"later_state": the question belongs to a later state — it is outside the\n  scope of State 0' in instruction
    # the last design state is judged against its own scope, with no later state to defer to
    last = prompts.judge_instruction(7, False, None, False, documents.question_scope(7))
    assert documents.question_scope(7) in last
    assert '- "later_state"' not in last
