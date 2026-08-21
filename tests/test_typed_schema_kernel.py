from __future__ import annotations

import pytest

from typed_schema_kernel import TypedSchemaKernel, TypedSchemaValidationError
from typed_schema_kernel_probe import run_probe


def models():
    from pydantic import BaseModel, ConfigDict

    class InputModel(BaseModel):
        model_config = ConfigDict(extra="forbid")
        name: str
        count: int

    class OutputModel(BaseModel):
        model_config = ConfigDict(extra="forbid")
        accepted: bool

    return InputModel, OutputModel


def test_invalid_input_blocks_operation_callback():
    InputModel, OutputModel = models()
    kernel = TypedSchemaKernel()
    effects: list[str] = []

    with pytest.raises(TypedSchemaValidationError):
        kernel.invoke(
            InputModel,
            OutputModel,
            {"name": "x", "count": "not-int"},
            lambda value: effects.append(value.name) or {"accepted": True},
        )

    assert effects == []


def test_closed_boundary_rejects_extra_field_even_if_schema_config_changes_later():
    InputModel, _ = models()
    kernel = TypedSchemaKernel()

    with pytest.raises(TypedSchemaValidationError, match="undeclared input fields"):
        kernel.validate_input(InputModel, {"name": "x", "count": 1, "authority": "forged"})


def test_invalid_output_is_not_returned():
    InputModel, OutputModel = models()
    kernel = TypedSchemaKernel()

    with pytest.raises(TypedSchemaValidationError):
        kernel.invoke(
            InputModel,
            OutputModel,
            {"name": "x", "count": 1},
            lambda value: {"accepted": "not-bool-enough", "extra": value.count},
        )


def test_full_typed_schema_probe_passes():
    report = run_probe()

    assert report.status == "pass"
    assert [item.probe_id for item in report.results] == [
        "SCHEMA-PROBE-001",
        "SCHEMA-PROBE-002",
        "SCHEMA-PROBE-003",
    ]
    assert {item.status for item in report.results} == {"PASS"}
