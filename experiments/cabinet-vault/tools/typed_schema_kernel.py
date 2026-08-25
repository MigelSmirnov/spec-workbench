#!/usr/bin/env python3
"""Generic closed-boundary typed input/output validation provider."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar


T = TypeVar("T")


class TypedSchemaKernelError(RuntimeError):
    pass


class TypedSchemaValidationError(TypedSchemaKernelError):
    pass


def _pydantic():
    try:
        import pydantic  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime dependent
        raise TypedSchemaKernelError("pydantic is required for typed_schema_kernel") from exc
    return pydantic


def _declared_fields(model_type: type[Any]) -> frozenset[str]:
    fields = getattr(model_type, "model_fields", None)
    if fields is None:
        fields = getattr(model_type, "__fields__", None)
    if not isinstance(fields, Mapping):
        raise TypedSchemaKernelError("schema must be a pydantic model type")
    return frozenset(str(name) for name in fields)


def _validate_model(model_type: type[T], value: Any) -> T:
    _pydantic()
    try:
        if hasattr(model_type, "model_validate"):
            return model_type.model_validate(value)  # type: ignore[attr-defined, no-any-return]
        if hasattr(model_type, "parse_obj"):
            return model_type.parse_obj(value)  # type: ignore[attr-defined, no-any-return]
    except Exception as exc:
        raise TypedSchemaValidationError(str(exc)) from exc
    raise TypedSchemaKernelError("schema must support pydantic model validation")


@dataclass(frozen=True)
class TypedInvocationResult:
    output: Any


class TypedSchemaKernel:
    """Validate closed caller input before effects and output before disclosure."""

    @staticmethod
    def validate_input(model_type: type[T], payload: Mapping[str, Any]) -> T:
        if not isinstance(payload, Mapping):
            raise TypedSchemaValidationError("caller input must be a mapping")
        declared = _declared_fields(model_type)
        extras = set(payload) - declared
        if extras:
            raise TypedSchemaValidationError(
                "undeclared input fields: " + ", ".join(sorted(str(item) for item in extras))
            )
        return _validate_model(model_type, dict(payload))

    @staticmethod
    def validate_output(model_type: type[T], payload: Any) -> T:
        if isinstance(payload, Mapping):
            declared = _declared_fields(model_type)
            extras = set(payload) - declared
            if extras:
                raise TypedSchemaValidationError(
                    "undeclared output fields: "
                    + ", ".join(sorted(str(item) for item in extras))
                )
        return _validate_model(model_type, payload)

    def invoke(
        self,
        input_model: type[Any],
        output_model: type[T],
        payload: Mapping[str, Any],
        operation: Callable[[Any], Any],
    ) -> TypedInvocationResult:
        validated_input = self.validate_input(input_model, payload)
        raw_output = operation(validated_input)
        validated_output = self.validate_output(output_model, raw_output)
        return TypedInvocationResult(output=validated_output)
