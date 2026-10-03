from __future__ import annotations

import json

import pytest

import design_questions
from questions_workbench import documents, provider, service


class FakeProvider:
    """Answers reviews from a script, groups points by their subject, and judges
    every topic with `verdict` (by default a consequential gap)."""

    name = "fake"

    def __init__(self, reviews: list[list[dict]], verdict: dict | None = None):
        self.reviews = list(reviews)
        self.verdict = verdict or {"kind": "consequential_gap", "divergence": "a or b; the owner notices"}
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


def test_every_design_state_up_to_5_declares_a_question_scope():
    for state in range(6):
        assert documents.question_scope(state)


def test_a_topic_raised_by_two_reviews_keeps_the_state_open(tmp_path):
    case = _case(tmp_path)
    provider = FakeProvider([[_point("M01")], [_point("M01"), _point("M02")], []])
    summary = service.ask_round(case, 1, provider)
    assert summary["closed"] is False
    assert summary["repeated_topics"] == 1
    assert summary["topics"][0]["runs"] == [1, 2]
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
    assert service.status(case, 1)["closed"] is True
    # and a v1 round with no repeated topic counts as the first clear round
    assert _repeated(case, {"kind": "later_state", "later_state": 6})[0]["closed"] is True
