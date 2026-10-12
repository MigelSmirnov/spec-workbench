"""State 7 asks about the prompt a generation run gives the generator.

`run_generate.py` emits the runtime models module with the Factory's
`generate_models_draft.py` and passes it to `generate_agent.py --models`; the
prompt's model surface (enum member names, field lists, port operations) is
read from that code. Until 2026-10-12 the review built the prompt without it:
on Cabinet Kernel the 14 review prompts differed from the production ones in
2669 lines — enum values instead of member names, ``StoreRepository`` without
its operations — so contradictions were asked about another text
(tools/DATA_CLOSURE_PLAN_Q9A_ORDERED_ENUM.md §7)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from factory_slice_workbench import FactoryPromptError, module_prompts
from questions_workbench import documents, service

FIXTURE = Path(__file__).parent / "fixtures" / "factory_prompt_parity" / "global_spec.json"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


SPEC = {
    "module_functions": {"models": ["Status"], "store": ["save"], "surface": ["serve"]},
    "notes": ["- save: [BEHAVIOR] The record is stored.", "- serve: [BEHAVIOR] The surface answers."],
}

EMITTER = """import json, sys
from pathlib import Path
args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
Path(args['--output']).parent.mkdir(parents=True, exist_ok=True)
Path(args['--output']).write_text(%r + json.dumps(sorted(args)) + '\\n')
"""


def _factory(tmp_path: Path, models_code: str = "class Status(StrEnum):\n    OPEN = 'open'\n",
             *, emitter: bool = True, inspector: bool = False) -> Path:
    """A Factory whose prompt shows the models code it was given."""
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
    return ('Module: ' + local_spec['module_name'] + '\\nNOTES:\\n' + '\\n'.join(local_spec['notes'])
            + '\\nMODELS:\\n' + (models_code if models_code is not None else '<none>\\n'))
""")
    _write(root / "tools/deterministic_emission.py", """def deterministic_emission_kind(spec, module):
    return {'models': 'models'}.get(module)
""")
    if emitter:
        _write(root / "tools/generate_models_draft.py", EMITTER % models_code)
    if inspector:
        _write(root / "tools/run_spec_inspector_preflight.py", """import json, sys
from pathlib import Path
args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
Path(args['--out']).write_text(json.dumps({'status': 'PASS'}))
""")
    return root


def _spec(tmp_path: Path, spec: dict = SPEC) -> Path:
    path = tmp_path / "case" / "global_spec.json"
    _write(path, json.dumps(spec))
    return path


# 1. The mechanism: the Factory's own models emission reaches build_prompt


def test_the_prompt_is_built_with_the_models_module_the_factory_emits(tmp_path):
    prompts = module_prompts(_spec(tmp_path), _factory(tmp_path))
    assert list(prompts) == ["store", "surface"]  # models is emitted, not generated
    for prompt in prompts.values():
        assert "MODELS:\nclass Status(StrEnum):\n    OPEN = 'open'\n" in prompt
        assert "<none>" not in prompt


def test_the_emitter_gets_the_arguments_a_generation_run_gives_it(tmp_path):
    prompts = module_prompts(_spec(tmp_path), _factory(tmp_path))
    assert '["--base-spec", "--normalized-spec", "--output", "--spec"]' in prompts["store"]
    prompts = module_prompts(_spec(tmp_path), _factory(tmp_path / "inspected", inspector=True))
    assert '"--inspector-report"' in prompts["store"]


def test_a_specification_without_a_models_module_is_asked_without_models_code(tmp_path):
    spec = {"module_functions": {"store": ["save"]}, "notes": ["- save: [BEHAVIOR] The record is stored."]}
    prompts = module_prompts(_spec(tmp_path, spec), _factory(tmp_path, emitter=False))
    assert prompts["store"].endswith("MODELS:\n<none>\n")


def test_a_factory_that_cannot_emit_the_models_module_stops_the_review(tmp_path):
    with pytest.raises(FactoryPromptError, match="missing tools/generate_models_draft.py"):
        module_prompts(_spec(tmp_path), _factory(tmp_path, emitter=False))
    factory = _factory(tmp_path / "refusing")
    _write(factory / "tools/generate_models_draft.py", "import sys\nsys.exit('model_emission_error')\n")
    with pytest.raises(FactoryPromptError, match="cannot emit the `models` module"):
        module_prompts(_spec(tmp_path), factory)


def test_the_review_writes_nothing_beside_the_specification(tmp_path):
    source = _spec(tmp_path)
    before = sorted(p.name for p in source.parent.iterdir())
    module_prompts(source, _factory(tmp_path, inspector=True))
    assert sorted(p.name for p in source.parent.iterdir()) == before


# 2. Rounds closed on another prompt text reopen


class Provider:
    name = "fake"

    def __init__(self):
        self.instructions: list[str] = []

    def complete(self, instruction: str, text: str):
        self.instructions.append(instruction)
        return json.dumps({"open_points": []}), {}


def _case(tmp_path: Path, monkeypatch) -> Path:
    case = tmp_path / "demo"
    _write(case / "80_notes.md", "# State 7 — Demo notes\n\n- save: the record is stored.\n")
    _write(case / "global_spec.json", json.dumps(SPEC))
    monkeypatch.setattr(service, "_spec_out_of_sync", lambda case: None)
    return case


def test_rounds_closed_on_a_prompt_without_the_models_context_reopen_on_its_diff(tmp_path, monkeypatch):
    """The prompt text is the unit (units.module_units): a round closed on the
    prompt the review used to build is not a closure of the production prompt.
    Every module reopens, and its reviewers see only what the models context
    added."""
    case = _case(tmp_path, monkeypatch)
    before = _factory(tmp_path / "before", models_code="")
    service.ask_round(case, 7, Provider(), factory_root=before)
    service.ask_round(case, 7, Provider(), factory_root=before)
    assert service.status(case, 7, before)["closed"] is True

    after = _factory(tmp_path / "after")
    result = service.status(case, 7, after)
    assert result["closed"] is False
    assert result["open_units"] == ["store", "surface"] and result["changed_units"] == ["store", "surface"]
    provider = Provider()
    summary = service.ask_round(case, 7, provider, factory_root=after)
    assert summary["scope"] == ["store", "surface"] and summary["changed_units"] == ["store", "surface"]
    asked = [i for i in provider.instructions if i.startswith("You are the model")]
    assert asked and all("has changed since" in i and "+class Status(StrEnum):" in i for i in asked)
    service.ask_round(case, 7, Provider(), factory_root=after)
    assert service.status(case, 7, after)["closed"] is True


# 3. The real Factory: the review prompt is the production prompt


def _real_factory() -> Path | None:
    root = documents.factory_root()
    needed = ("tools/normalize_spec.py", "tools/build_local_spec.py", "tools/generate_agent.py",
              "tools/deterministic_emission.py", "tools/generate_models_draft.py")
    if root is None or not all((root / tool).is_file() for tool in needed):
        return None
    return root


real = pytest.mark.skipif(_real_factory() is None, reason="no Factory checkout (SPEC_WORKBENCH_FACTORY_ROOT or sibling code_factory)")


def _production_prompts(spec_path: Path, factory: Path, work: Path) -> dict[str, str]:
    """The prompts a generation run builds, step by step as run_generate.py does."""
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *args], cwd=factory, capture_output=True, text=True, check=True)

    spec = work / "global_spec.json"
    spec.write_text(spec_path.read_text(encoding="utf-8"), encoding="utf-8")
    (work / "slices").mkdir()
    run("tools/normalize_spec.py", str(spec), str(work / "normalized.json"))
    modules = list(json.loads((work / "normalized.json").read_text(encoding="utf-8"))["modules"])
    for module in modules:
        run("tools/build_local_spec.py", module, str(work / "normalized.json"), str(work / "call_graph.json"),
            str(work / "slices"))
    run("tools/generate_models_draft.py", "--spec", str(work / "slices" / "models.json"),
        "--output", str(work / "drafts" / "models.py"), "--base-spec", str(spec),
        "--normalized-spec", str(work / "normalized.json"))
    script = """
import json, sys
sys.path.insert(0, '.')
from tools.deterministic_emission import deterministic_emission_kind
from tools.generate_agent import build_prompt
spec = json.load(open(sys.argv[1]))
models_code = open(sys.argv[2]).read()
print(json.dumps({m: build_prompt(json.load(open(f'{sys.argv[3]}/{m}.json')), models_code)
                  for m in sys.argv[4:] if not deterministic_emission_kind(spec, m)}))
"""
    done = run("-c", script, str(spec), str(work / "drafts" / "models.py"), str(work / "slices"), *modules)
    return json.loads(done.stdout)


@real
def test_the_review_prompt_is_the_production_prompt(tmp_path):
    factory = _real_factory()
    review = module_prompts(FIXTURE, factory)
    production = _production_prompts(FIXTURE, factory, tmp_path)
    assert review == production


@real
def test_the_review_prompt_lists_the_store_repository_operations(tmp_path):
    prompt = module_prompts(FIXTURE, _real_factory())["store"]
    assert "- StoreRepository operations (exact, no others exist):" in prompt
    assert "    load_record(self, record_id: str) -> Record | None" in prompt
    assert "    save_record(self, record: Record) -> None" in prompt
    assert "StoreRepository: imported runtime symbol; no local surface details available." not in prompt


@real
def test_the_review_prompt_names_enum_members_as_the_generator_sees_them(tmp_path):
    prompt = module_prompts(FIXTURE, _real_factory())["store"]
    assert "- RecordStatus enum members: ARCHIVED='archived', DRAFT='draft', PUBLISHED='published'" in prompt
    assert "Python member names were not available in models context." not in prompt
    assert "- Record fields (exact, no others exist): record_id: str, status: RecordStatus, title: str" in prompt
    assert "MODELS CONTEXT:" in prompt
