"""The one place a round reaches a model. Tests pass their own provider."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

DEFAULT_MODEL = "gpt-5.3-codex"
DEFAULT_REASONING = "medium"
MAX_OUTPUT_TOKENS = 24000


class Provider(Protocol):
    name: str

    def complete(self, instruction: str, text: str) -> tuple[str, dict[str, Any]]:
        """Return the model's text and its usage."""


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
