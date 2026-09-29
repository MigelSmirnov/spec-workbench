"""The one place a round reaches a model. Tests pass their own provider."""
from __future__ import annotations

import os
from typing import Any, Protocol

DEFAULT_MODEL = "gpt-5.3-codex"
DEFAULT_REASONING = "medium"
MAX_OUTPUT_TOKENS = 24000


class Provider(Protocol):
    name: str

    def complete(self, instruction: str, text: str) -> tuple[str, dict[str, Any]]:
        """Return the model's text and its usage."""


def load_env_file() -> None:
    """Load provider settings from the file an operator names explicitly.

    `DESIGN_QUESTIONS_ENV_FILE`, or the Factory's `CODE_FACTORY_ENV_FILE`, so a
    workbench round can use the Factory's provider settings without copying them.
    Values already in the environment win; nothing is searched for.
    """
    path = os.environ.get("DESIGN_QUESTIONS_ENV_FILE") or os.environ.get("CODE_FACTORY_ENV_FILE")
    if not path or not os.path.isfile(path):
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
            raise RuntimeError("OPENAI_API_KEY is not set; set it or name an env file in DESIGN_QUESTIONS_ENV_FILE")
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
