"""Question rounds cover late decisions: units for every state, the carried
closure of a state closed as one text, State 7 on the Factory's prompts, and
the gates that stop a late edit from going around the rounds."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import design_authoring_next
from factory_admission_workbench.model import CHECK_BLOCK, CHECK_NOT_APPLICABLE, CHECK_PASS
from factory_admission_workbench.service import _question_rounds_check
from questions_workbench import documents, service

MODULES = """# State 3 — Demo modules

Why the modules are cut this way.

## Module store

1. The store keeps every record.
2. Filler one.
3. Filler two.
4. Filler three.
5. Filler four.
6. Filler five.
7. The store refuses a record over the size limit.

## Module surface

The surface serves the owner.
"""


class Provider:
    """Clear reviews unless `points` are given; groups by subject; judges every
    topic as a quoted gap (blocking) when its subject is in `blocking`."""

    name = "fake"

    def __init__(self, points: list[dict] | None = None, blocking: set[str] = frozenset(),
                 contradictions: dict[str, list[str]] | None = None):
        self.points = points or []
        self.blocking = set(blocking)
        self.contradictions = contradictions or {}
        self.instructions: list[str] = []
        self.inputs: list[str] = []
        self.judged: list[str] = []

    def complete(self, instruction: str, text: str):
        if instruction.startswith("You judge the topics"):
            self.judged.append(text)
            listing = text.split("=== TOPICS TO JUDGE ===")[1].splitlines()
            judgements = []
            for line in listing:
                if line[:1] == "T":
                    tid, subject = line.split(": ", 1)
                    if subject in self.contradictions:
                        judgements.append({"id": tid, "kind": "contradiction", "quotes": self.contradictions[subject]})
                    elif subject in self.blocking:
                        judgements.append({"id": tid, "kind": "consequential_gap", "divergence": "a or b; the owner notices"})
                    else:
                        judgements.append({"id": tid, "kind": "indifferent", "why": "no one acts on it"})
            return json.dumps({"judgements": judgements}), {}
        if instruction.startswith("You receive the open points"):
            groups: dict[str, list[str]] = {}
            for line in text.splitlines():
                key, rest = line.split(": ", 1)
                groups.setdefault(rest[1:rest.index("]")], []).append(key)
            return json.dumps({"groups": [{"topic": s, "members": m} for s, m in groups.items()]}), {}
        self.instructions.append(instruction)
        self.inputs.append(text)
        return json.dumps({"open_points": list(self.points)}), {}


def _point(subject: str, unit: str | None = None, text: str = "x") -> dict:
    point = {"subject": subject, "kind": "gap", "text": text, "question": f"what about {subject}?",
             "options": [], "default_guess": "y"}
    if unit:
        point["unit"] = unit
    return point


def _git(case: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(case), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          check=True, capture_output=True, text=True)
    return done.stdout


def _commit(case: Path, message: str) -> None:
    _git(case, "add", "-A")
    _git(case, "commit", "-qm", message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _legacy_round(case: Path, state: int, number: int) -> None:
    """A round kept before units existed: clear, on the documents as they are."""
    directory = service.rounds_dir(case, state) / f"round-{number:02d}"
    directory.mkdir(parents=True)
    digests = {p.name: _sha(p) for _, p in documents.design_documents(case, state)}
    (directory / "summary.json").write_text(json.dumps({
        "schema_version": service.SCHEMA, "state": state, "round": directory.name, "documents": digests,
        "reviews": 3, "points": [0, 0, 0], "judge": {"provider": "fake"}, "repeated_topics": 0,
        "blocking_topics": 0, "clear": True, "closed": number > 1, "topics": [],
    }), encoding="utf-8")


def _closed_as_one_text(tmp_path: Path) -> Path:
    """A State 3 closed as one text by two clear rounds, all committed."""
    case = tmp_path / "demo"
    case.mkdir()
    (case / "30_modules.md").write_text(MODULES, encoding="utf-8")
    _git(case, "init", "-q")
    _commit(case, "State 3 texts")
    _legacy_round(case, 3, 1)
    _legacy_round(case, 3, 2)
    _commit(case, "State 3 closed")
    return case


# 1. Units for every state


def test_a_state_without_decisions_reviews_its_sections_as_units(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "30_modules.md").write_text(MODULES, encoding="utf-8")
    summary = service.ask_round(case, 3, Provider())
    assert summary["scope"] == ["30_modules.md:preamble", "30_modules.md:Module store", "30_modules.md:Module surface"]
    summary = service.ask_round(case, 3, Provider())
    assert summary["closed"] is True and service.status(case, 3)["closed"] is True


# 1. A state closed as one text carries its closure to every unit


def test_a_state_closed_as_one_text_is_closed_unit_by_unit_on_that_text(tmp_path):
    case = _closed_as_one_text(tmp_path)
    result = service.status(case, 3)
    assert result["closed"] is True and result["carried"] is True and result["units"] == 3


def test_after_a_late_edit_only_the_edited_section_is_reviewed_and_by_its_diff(tmp_path):
    case = _closed_as_one_text(tmp_path)
    (case / "30_modules.md").write_text(MODULES.replace("over the size limit.", "over the size limit, now 1 MiB."),
                                        encoding="utf-8")
    result = service.status(case, 3)
    assert result["closed"] is False and result["open_units"] == ["30_modules.md:Module store"]
    assert result["changed_units"] == ["30_modules.md:Module store"] and result["closed_at"]
    unchanged = {"subject": "old", "kind": "gap", "text": "The store keeps every record.", "question": "?",
                 "options": [], "default_guess": "y", "unit": "30_modules.md:Module store"}
    provider = Provider([unchanged, _point("new", "30_modules.md:Module store", "the size limit, now 1 MiB.")],
                        blocking={"old", "new"})
    summary = service.ask_round(case, 3, provider)
    assert summary["scope"] == ["30_modules.md:Module store"]
    assert summary["changed_units"] == ["30_modules.md:Module store"]
    assert "+7. The store refuses a record over the size limit, now 1 MiB." in provider.instructions[0]
    assert "- 30_modules.md:Module surface" not in provider.instructions[0]
    # the point quoting the unchanged first rule is set aside; the one on the change is kept
    assert [t["topic"] for t in summary["topics"]] == ["new"] and summary["set_aside"] == [1, 1, 1]
    assert summary["carried"]["from"] == ["round-01", "round-02"]
    assert service.status(case, 3)["open_units"] == ["30_modules.md:Module store"]


def test_the_carried_closure_survives_the_first_unit_rounds(tmp_path):
    case = _closed_as_one_text(tmp_path)
    (case / "30_modules.md").write_text(MODULES.replace("serves the owner.", "serves the owner only."),
                                        encoding="utf-8")
    service.ask_round(case, 3, Provider())
    summary = service.ask_round(case, 3, Provider())
    assert summary["scope"] == ["30_modules.md:Module surface"] and summary["closed"] is True
    assert service.status(case, 3)["closed"] is True


def test_a_state_never_closed_as_one_text_carries_nothing(tmp_path):
    case = tmp_path / "demo"
    case.mkdir()
    (case / "30_modules.md").write_text(MODULES, encoding="utf-8")
    _legacy_round(case, 3, 1)  # one clear round, not closed
    result = service.status(case, 3)
    assert result["closed"] is False and len(result["open_units"]) == 3


# 2. State 7 on the Factory's prompts


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _factory(tmp_path: Path) -> Path:
    """A Factory whose slicer gives a module the notes naming its functions, whose
    prompt is the cut, and which emits `models` and `clock` without a model."""
    root = tmp_path / "code_factory"
    _write(root / "tools/normalize_spec.py", """import json, sys
spec = json.load(open(sys.argv[1], encoding='utf-8'))
spec['modules'] = {name: {} for name in spec['module_functions']}
open(sys.argv[2], 'w', encoding='utf-8').write(json.dumps(spec))
""")
    _write(root / "tools/build_local_spec.py", """import json, sys
from pathlib import Path
module, spec_path, _graph, out = sys.argv[1:5]
spec = json.load(open(spec_path, encoding='utf-8'))
owned = spec['module_functions'][module]
notes = [n for n in spec['notes'] if any(f in n for f in owned)]
(Path(out) / f'{module}.json').write_text(json.dumps({'module_name': module, 'functions': owned, 'notes': notes}))
""")
    _write(root / "tools/generate_agent.py", """def build_prompt(local_spec, models_code=None):
    return 'Module: ' + local_spec['module_name'] + '\\nNOTES:\\n' + '\\n'.join(local_spec['notes']) + '\\n'
""")
    _write(root / "tools/deterministic_emission.py", """def deterministic_emission_kind(spec, module):
    return {'models': 'models', 'clock': 'system_clock'}.get(module)
""")
    return root


SPEC = {
    "module_functions": {"models": ["Thing"], "clock": ["kernel_now"], "store": ["save"], "surface": ["serve"]},
    "notes": [
        "- save: [PRECONDITION] The record fits the size limit.",
        "- serve: [DEPENDENCY_BOUNDARY] The surface imports nothing outside the standard library.",
    ],
}


def _notes_case(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    case = tmp_path / "demo"
    _write(case / "80_notes.md", "# State 7 — Demo notes\n\n- save: the record fits.\n")
    _write(case / "global_spec.json", json.dumps(SPEC))
    monkeypatch.setattr(service, "_spec_out_of_sync", lambda case: None)
    return case, _factory(tmp_path)


def test_state7_units_are_the_generated_modules_and_their_text_the_prompt(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    read = service.state_texts(case, 7, factory)
    assert list(read.units) == ["store", "surface"]  # models and clock are emitted, not generated
    assert read.units["store"]["text"] == "Module: store\nNOTES:\n- save: [PRECONDITION] The record fits the size limit.\n"
    provider = Provider()
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    assert summary["scope"] == ["store", "surface"] and summary["reviews"] == 3
    assert len(provider.inputs) == 6 and all(text.count("Module: ") == 1 for text in provider.inputs)
    assert provider.instructions[0].startswith("You are the model that will generate the module below.")
    round_dir = service.rounds_dir(case, 7) / summary["round"]
    assert (round_dir / "prompts" / "store.txt").is_file() and (round_dir / "review-store-1.json").is_file()


def test_editing_one_modules_note_reopens_only_that_module_and_asks_its_prompt_diff(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    service.ask_round(case, 7, Provider(), factory_root=factory)
    service.ask_round(case, 7, Provider(), factory_root=factory)
    assert service.status(case, 7, factory)["closed"] is True
    spec = json.loads(json.dumps(SPEC))
    spec["notes"][1] += " Like every module it may import pydantic."
    _write(case / "global_spec.json", json.dumps(spec))
    result = service.status(case, 7, factory)
    assert result["open_units"] == ["surface"] and result["changed_units"] == ["surface"]
    quotes = ["The surface imports nothing outside the standard library.", "it may import pydantic."]
    provider = Provider([_point("pydantic", text="it may import pydantic.")], contradictions={"pydantic": quotes})
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    assert summary["scope"] == ["surface"] and summary["changed_units"] == ["surface"]
    assert all("Module: surface" in text for text in provider.inputs)
    assert "has changed since" in provider.instructions[0] and "+- serve:" in provider.instructions[0]
    assert summary["blocked_units"] == ["surface"] and summary["topics"][0]["units"] == ["surface"]
    assert summary["topics"][0]["judgement"]["kind"] == "contradiction"
    assert summary["topics"][0]["judgement"]["blocking"] is True


def test_state7_judges_a_contradiction_one_review_found_and_only_contradictions_block(tmp_path, monkeypatch):
    """Cabinet Kernel State 7 round-01 (2026-10-10): 519 repeated topics, 445 of
    them gaps, all blocking; the pydantic contradiction was raised by one review
    of three and never judged. State 7 asks for contradictions only, judges each
    topic, and a gap the judge still names is recorded without blocking."""
    case, factory = _notes_case(tmp_path, monkeypatch)
    spec = json.loads(json.dumps(SPEC))
    spec["notes"][1] += " Like every module it may import pydantic."
    _write(case / "global_spec.json", json.dumps(spec))
    quotes = ["The surface imports nothing outside the standard library.", "it may import pydantic."]

    import threading

    class OneReview(Provider):
        lock, raised = threading.Lock(), False

        def complete(self, instruction, text):
            if instruction.startswith("You are the model") and "Module: surface" in text:
                with self.lock:
                    first, OneReview.raised = not OneReview.raised, True
                if first:
                    self.instructions.append(instruction)
                    return json.dumps({"open_points": [_point("pydantic", text="it may import pydantic.")]}), {}
            return super().complete(instruction, text)

    provider = OneReview(contradictions={"pydantic": quotes})
    summary = service.ask_round(case, 7, provider, factory_root=factory)
    assert "contradicts itself" in provider.instructions[0]
    pydantic = [t for t in summary["topics"] if t["topic"] == "pydantic"]
    assert len(pydantic) == 1 and len(pydantic[0]["runs"]) == 1
    assert pydantic[0]["judgement"]["blocking"] is True and summary["blocked_units"] == ["surface"]

    gap = Provider([_point("error text", text="x")], blocking={"error text"})
    summary = service.ask_round(case, 7, gap, factory_root=factory)
    judged = [t["judgement"] for t in summary["topics"]]
    assert judged and all(j["kind"] == "consequential_gap" and j["blocking"] is False for j in judged)


def test_a_reopened_state7_judges_the_prompt_change_since_it_closed(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    _git(case, "init", "-q")
    _commit(case, "notes")
    spec = json.loads(json.dumps(SPEC))
    spec["notes"][1] += " Like every module it may import pydantic."
    _write(case / "global_spec.json", json.dumps(spec))
    provider = Provider([_point("pydantic", text="it may import pydantic.")], blocking={"pydantic"})
    service.ask_round(case, 7, provider, since="HEAD", factory_root=factory)
    judged = {text.split("`")[1]: text for text in provider.judged}  # each module is judged on its own prompt
    assert sorted(judged) == ["store", "surface"]
    assert "(no change)" in judged["store"]
    change = judged["surface"].split("=== CHANGE SINCE THE STATE WAS CLOSED (unified diff) ===")[1]
    assert "+- serve: [DEPENDENCY_BOUNDARY] The surface imports nothing outside the standard library. Like" in change


def test_state7_refuses_without_a_factory_or_with_an_unsynced_spec(tmp_path, monkeypatch):
    case, _ = _notes_case(tmp_path, monkeypatch)
    monkeypatch.setattr(documents, "factory_root", lambda: None)
    with pytest.raises(service.QuestionRoundError, match="no Factory was found"):
        service.ask_round(case, 7, Provider())
    assert "no Factory was found" in service.status(case, 7)["reason"]
    monkeypatch.setattr(service, "_spec_out_of_sync", lambda case: "global_spec.json is out of sync with the design")
    with pytest.raises(service.QuestionRoundError, match="design_spec_projection.py .* --apply"):
        service.ask_round(case, 7, Provider(), factory_root=tmp_path)


def test_a_module_whose_prompt_the_factory_refuses_stops_the_state7_round(tmp_path, monkeypatch):
    case, factory = _notes_case(tmp_path, monkeypatch)
    _write(factory / "tools/generate_agent.py", """def build_prompt(local_spec, models_code=None):
    if local_spec['module_name'] == 'surface':
        raise ValueError('data in model context: rules.limit')
    return 'Module: ' + local_spec['module_name']
""")
    with pytest.raises(service.QuestionRoundError, match="refuses to build the prompt of `surface`"):
        service.ask_round(case, 7, Provider(), factory_root=factory)


def test_state6_has_no_round_of_its_own(tmp_path):
    """Contracts reach the generator inside each module's prompt, which State 7
    asks; a State 6 round over the documents could not see 60_contracts.json."""
    with pytest.raises(documents.QuestionScopeError):
        documents.question_scope(6)
    case = tmp_path / "demo"
    _write(case / "60_contracts.md", "# State 6 — Demo contracts\n\n## store.save\n\n`save(r) -> None`\n")
    with pytest.raises(documents.QuestionScopeError):
        service.ask_round(case, 6, Provider())


# 3. The gates


def _assembly_step(sequence, project, text):
    return design_authoring_next._result(sequence=sequence, project=project, project_text=text,
                                         phase="state8_assembly", blocked=False, reason="assemble")


def test_authoring_next_stops_at_a_state_edited_after_its_rounds_closed(tmp_path, monkeypatch):
    case = _closed_as_one_text(tmp_path)
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda sequence, project, text: None)
    monkeypatch.setattr(design_authoring_next, "_post_state5_step", _assembly_step)
    assert design_authoring_next.next_step(case, display_path="examples/demo")["phase"] == "state8_assembly"
    (case / "30_modules.md").write_text(MODULES.replace("serves the owner.", "serves the owner only."),
                                        encoding="utf-8")
    report = design_authoring_next.next_step(case, display_path="examples/demo")
    assert report["phase"] == "state3_module_responsibilities" and report["blocked"] is True
    assert report["summary"]["open_units"] == ["30_modules.md:Module surface"]
    closed_at = _git(case, "rev-parse", "HEAD").strip()  # the commit that kept the closing round
    assert report["summary"]["closed_at"] == closed_at
    assert report["question_round"] == (
        f"python tools/design_questions.py ask examples/demo --state 3 --since {closed_at}")


def test_authoring_next_asks_the_earliest_open_state_first(tmp_path, monkeypatch):
    case = _closed_as_one_text(tmp_path)
    _write(case / "00_product.md", "# State 0 — Demo\n\nA product.\n")
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda sequence, project, text: None)
    monkeypatch.setattr(design_authoring_next, "_post_state5_step", _assembly_step)
    report = design_authoring_next.next_step(case)
    assert report["phase"] == "state0_product_frame" and "no question round yet" in report["reason"]
    assert report["question_round"].endswith("--state 0")


def test_authoring_next_does_not_ask_a_state_whose_own_phase_is_ahead(tmp_path, monkeypatch):
    case = _closed_as_one_text(tmp_path)
    _write(case / "60_contracts.md", "# State 6 — Demo contracts\n")
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda sequence, project, text: None)
    monkeypatch.setattr(design_authoring_next, "_post_state5_step",
                        lambda sequence, project, text: design_authoring_next._result(
                            sequence=sequence, project=project, project_text=text,
                            phase="state6_exact_contracts", blocked=False, reason="author contracts"))
    assert design_authoring_next.next_step(case)["phase"] == "state6_exact_contracts"


def test_admission_blocks_on_an_open_unit_and_passes_when_every_state_is_closed(tmp_path):
    case = _closed_as_one_text(tmp_path)
    check = _question_rounds_check(case, tmp_path)
    assert check.status == CHECK_PASS and check.check_id == "FA019"
    (case / "30_modules.md").write_text(MODULES.replace("serves the owner.", "serves the owner only."),
                                        encoding="utf-8")
    check = _question_rounds_check(case, tmp_path)
    assert check.status == CHECK_BLOCK and check.evidence["open"] == ["state3"]
    assert check.evidence["states"]["state3"]["open_units"] == ["30_modules.md:Module surface"]
    service.ask_round(case, 3, Provider())
    service.ask_round(case, 3, Provider())
    assert _question_rounds_check(case, tmp_path).status == CHECK_PASS


def test_admission_blocks_a_case_with_no_round_and_skips_an_explicit_spec(tmp_path):
    case = tmp_path / "demo"
    _write(case / "00_product.md", "# State 0 — Demo\n\nA product.\n")
    check = _question_rounds_check(case, tmp_path)
    assert check.status == CHECK_BLOCK and "no question round yet" in check.summary
    assert _question_rounds_check(None, tmp_path).status == CHECK_NOT_APPLICABLE
