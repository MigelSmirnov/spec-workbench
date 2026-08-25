#!/usr/bin/env python3
"""Generic protected configuration provider for host-owned secret references."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar


T = TypeVar("T")


class ProtectedConfigurationError(RuntimeError):
    pass


class ProtectedConfigurationNotReady(ProtectedConfigurationError):
    pass


class ProtectedConfigurationLeakError(ProtectedConfigurationError):
    pass


@dataclass(frozen=True)
class ConfigurationBinding:
    reference: str
    source_key: str
    required: bool = True


def _contains_secret(value: Any, secret: str) -> bool:
    if isinstance(value, str):
        return secret in value
    if isinstance(value, bytes):
        return secret.encode() in value
    if isinstance(value, Mapping):
        return any(
            _contains_secret(key, secret) or _contains_secret(item, secret)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_contains_secret(item, secret) for item in value)
    return False


class ProtectedConfigurationKernel:
    """Resolve declared host config references without exposing raw protected values."""

    def __init__(self, bindings: tuple[ConfigurationBinding, ...], source: Mapping[str, str]):
        if not bindings:
            raise ProtectedConfigurationError("at least one configuration binding is required")
        references = [binding.reference for binding in bindings]
        if any(not reference for reference in references) or len(set(references)) != len(references):
            raise ProtectedConfigurationError("configuration references must be unique and non-empty")
        if any(not binding.source_key for binding in bindings):
            raise ProtectedConfigurationError("configuration source keys must be non-empty")
        self._bindings = {binding.reference: binding for binding in bindings}
        self._source = dict(source)

    @classmethod
    def from_environment(
        cls,
        bindings: tuple[ConfigurationBinding, ...],
        environment: Mapping[str, str] | None = None,
    ) -> "ProtectedConfigurationKernel":
        source = os.environ if environment is None else environment
        return cls(bindings, source)

    def _binding(self, reference: str) -> ConfigurationBinding:
        try:
            return self._bindings[reference]
        except KeyError as exc:
            raise ProtectedConfigurationError("undeclared configuration reference") from exc

    def _protected_value(self, reference: str) -> str:
        binding = self._binding(reference)
        value = self._source.get(binding.source_key)
        if value is None or value == "":
            raise ProtectedConfigurationNotReady(
                f"required protected configuration reference is unavailable: {reference}"
            )
        return value

    def require_ready(self) -> None:
        missing = [
            binding.reference
            for binding in self._bindings.values()
            if binding.required and not self._source.get(binding.source_key)
        ]
        if missing:
            raise ProtectedConfigurationNotReady(
                "required protected configuration references are unavailable: "
                + ", ".join(sorted(missing))
            )

    def safe_descriptor(self, reference: str) -> dict[str, object]:
        binding = self._binding(reference)
        return {
            "configuration_reference": binding.reference,
            "configured": bool(self._source.get(binding.source_key)),
            "protected": True,
        }

    def safe_audit_fields(self, reference: str) -> dict[str, object]:
        return self.safe_descriptor(reference)

    def use_for_host_provider(self, reference: str, consumer: Callable[[str], T]) -> T:
        """Host-only secret use; reject a result that would return the protected value."""
        protected_value = self._protected_value(reference)
        result = consumer(protected_value)
        if _contains_secret(result, protected_value):
            raise ProtectedConfigurationLeakError(
                "host provider result attempted to expose protected configuration material"
            )
        return result
