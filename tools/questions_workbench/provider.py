"""The one place a round reaches a model. Tests pass their own provider."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Protocol

DEFAULT_MODEL = "gpt-5.3-codex"
DEFAULT_REASONING = "medium"
MAX_OUTPUT_TOKENS = 24000
DEFAULT_CODEX_MODEL = "gpt-5.6-sol"
CODEX_TIMEOUT_SECONDS = 1800


class Provider(Protocol):
    name: str

    def complete(self, instruction: str, text: str) -> tuple[str, dict[str, Any]]:
        """Return the model's text and its usage."""


LATER_DIR = "later"


def _load_env(path: Path) -> None:
    if not path.is_file():
        return
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")


def load_env_file() -> None:
    """Load provider settings the way the Factory's `llm_config` does.

    An env file named in `DESIGN_QUESTIONS_ENV_FILE`, or the Factory's
    `CODE_FACTORY_ENV_FILE`, is the only one read. Without either, the nearest
    `.env` from the working directory upwards is read, so a round run from a
    case checkout uses the same provider settings as the Factory without the
    operator naming them. Values already in the environment win.
    """
    explicit = os.environ.get("DESIGN_QUESTIONS_ENV_FILE") or os.environ.get("CODE_FACTORY_ENV_FILE")
    if explicit:
        _load_env(Path(explicit))
        return
    for directory in [Path.cwd(), *Path.cwd().parents]:
        _load_env(directory / ".env")


class OpenAIProvider:
    """The model that generates code in the Factory, asked through the Responses API.

    Asking the generator's own model is the point: its open questions are the
    choices it would otherwise make silently.
    """

    def __init__(self, model: str | None = None, reasoning: str | None = None):
        self.model = model or os.environ.get("DESIGN_QUESTIONS_MODEL", DEFAULT_MODEL)
        self.reasoning = reasoning or os.environ.get("DESIGN_QUESTIONS_REASONING", DEFAULT_REASONING)
        self.name = f"openai:{self.model}:{self.reasoning}"

    def complete(self, instruction: str, text: str) -> tuple[str, dict[str, Any]]:
        load_env_file()
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set: not in the environment, in DESIGN_QUESTIONS_ENV_FILE "
                "or CODE_FACTORY_ENV_FILE, nor in a .env above the working directory"
            )
        from openai import OpenAI

        response = OpenAI().responses.create(
            model=self.model,
            instructions=instruction,
            input=text,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            reasoning={"effort": self.reasoning},
        )
        usage = response.usage.model_dump() if getattr(response, "usage", None) else {}
        return response.output_text, usage


class CodexCliProvider:
    """A model asked through the Codex CLI under the operator's ChatGPT login.

    A stand-in when the Responses API cannot be used: a ChatGPT login does not
    serve the Factory's generator model, so the round is recorded under this
    provider's own name and is not the generator's own answer. Each call runs
    `codex exec` once, ephemeral and read-only, in an empty temporary directory
    and without the user's Codex configuration, so no project file, rule or MCP
    server reaches the model.

    `complete_with_files` is the one exception: the files it is given are
    written under `later/` of that directory, the only files the model may
    read there, so it searches them instead of receiving them whole.
    """

    reads_files = True

    def __init__(self, model: str | None = None, reasoning: str | None = None):
        self.model = model or os.environ.get("DESIGN_QUESTIONS_CODEX_MODEL", DEFAULT_CODEX_MODEL)
        self.reasoning = reasoning or os.environ.get("DESIGN_QUESTIONS_REASONING", DEFAULT_REASONING)
        self.name = f"codex-cli:{self.model}:{self.reasoning}"

    def complete(self, instruction: str, text: str) -> tuple[str, dict[str, Any]]:
        return self._exec(
            instruction, text,
            "Answer from the text below alone. Do not run commands or read files; "
            "reply with the requested output and nothing else.",
            {},
        )

    def complete_with_files(self, instruction: str, text: str, files: dict[str, str]) -> tuple[str, dict[str, Any]]:
        listing = ", ".join(f"{LATER_DIR}/{name}" for name in files)
        return self._exec(
            instruction, text,
            f"Answer from the text below and from the files {listing} in the working "
            "directory. You may search and read those files; read nothing else, change "
            "nothing, and reply with the requested output and nothing else.",
            files,
        )

    def _exec(self, instruction: str, text: str, rule: str, files: dict[str, str]) -> tuple[str, dict[str, Any]]:
        prompt = f"{instruction}\n\n{rule}\n\n=== TEXT ===\n{text}"
        with tempfile.TemporaryDirectory(prefix="design-questions-codex-") as work:
            if files:
                later = Path(work) / LATER_DIR
                later.mkdir()
                for name, body in files.items():
                    (later / name).write_text(body, encoding="utf-8")
            answer_file = Path(work) / "answer.txt"
            command = [
                os.environ.get("DESIGN_QUESTIONS_CODEX_BIN", "codex"), "exec",
                "-m", self.model,
                "-c", f"model_reasoning_effort={self.reasoning}",
                "--ephemeral", "--skip-git-repo-check", "--ignore-user-config",
                "--sandbox", "read-only",
                "-o", str(answer_file),
                "-",
            ]
            completed = subprocess.run(
                command, input=prompt, cwd=work, capture_output=True, text=True,
                timeout=CODEX_TIMEOUT_SECONDS,
            )
            if completed.returncode != 0 or not answer_file.is_file():
                tail = (completed.stderr or completed.stdout or "").strip().splitlines()[-3:]
                raise RuntimeError(f"codex exec failed ({completed.returncode}): {' | '.join(tail)}")
            return answer_file.read_text(encoding="utf-8"), {}
