#!/usr/bin/env python3
"""Execute typed_schema_kernel verification probes."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from typed_schema_kernel import TypedSchemaKernel, TypedSchemaValidationError


PROBE_SCHEMA_VERSION = "spec_workbench_typed_schema_kernel_probe.v0"


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    status: str
    message: str


@dataclass(frozen=True)
class ProbeReport:
    schema_version: str
    provider_id: str
    status: str
    results: tuple[ProbeResult, ...]


def _models():
    try:
        from pydantic import BaseModel, ConfigDict  # type: ignore

        class InputModel(BaseModel):
            model_config = ConfigDict(extra="forbid")
            invoice_id: str
            count: int

        class OutputModel(BaseModel):
            model_config = ConfigDict(extra="forbid")
            accepted: bool
            normalized_count: int

    except ImportError:
        from pydantic import BaseModel  # type: ignore

        class InputModel(BaseModel):
            invoice_id: str
            count: int

            class Config:
                extra = "forbid"

        class OutputModel(BaseModel):
            accepted: bool
            normalized_count: int

            class Config:
                extra = "forbid"

    return InputModel, OutputModel


def _probe_invalid_input_before_effect(kernel: TypedSchemaKernel) -> ProbeResult:
    InputModel, OutputModel = _models()
    effects: list[str] = []

    def operation(value):
        effects.append(value.invoice_id)
        return {"accepted": True, "normalized_count": value.count}

    try:
        kernel.invoke(InputModel, OutputModel, {"invoice_id": "inv-1", "count": "bad"}, operation)
    except TypedSchemaValidationError:
        pass
    except Exception as exc:  # pragma: no cover - runtime evidence
        return ProbeResult("SCHEMA-PROBE-001", "FAIL", f"unexpected failure: {type(exc).__name__}: {exc}")
    else:
        return ProbeResult("SCHEMA-PROBE-001", "FAIL", "invalid typed input reached the operation")

    if effects:
        return ProbeResult("SCHEMA-PROBE-001", "FAIL", "effect callback executed before invalid input rejection")
    return ProbeResult(
        "SCHEMA-PROBE-001",
        "PASS",
        "invalid typed input was rejected before the operation callback could execute",
    )


def _probe_undeclared_input_field(kernel: TypedSchemaKernel) -> ProbeResult:
    InputModel, _ = _models()
    try:
        kernel.validate_input(
            InputModel,
            {"invoice_id": "inv-1", "count": 1, "caller_injected_authority": "forged"},
        )
    except TypedSchemaValidationError:
        return ProbeResult(
            "SCHEMA-PROBE-002",
            "PASS",
            "undeclared caller input field was rejected at the closed typed boundary",
        )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return ProbeResult("SCHEMA-PROBE-002", "FAIL", f"unexpected failure: {type(exc).__name__}: {exc}")
    return ProbeResult("SCHEMA-PROBE-002", "FAIL", "undeclared caller field was accepted")


def _probe_invalid_output_before_disclosure(kernel: TypedSchemaKernel) -> ProbeResult:
    InputModel, OutputModel = _models()
    returned = False

    def operation(value):
        return {"accepted": True, "normalized_count": "not-an-int"}

    try:
        result = kernel.invoke(
            InputModel,
            OutputModel,
            {"invoice_id": "inv-1", "count": 1},
            operation,
        )
        returned = result is not None
    except TypedSchemaValidationError:
        pass
    except Exception as exc:  # pragma: no cover - runtime evidence
        return ProbeResult("SCHEMA-PROBE-003", "FAIL", f"unexpected failure: {type(exc).__name__}: {exc}")

    if returned:
        return ProbeResult("SCHEMA-PROBE-003", "FAIL", "invalid provider output became caller-visible")
    return ProbeResult(
        "SCHEMA-PROBE-003",
        "PASS",
        "invalid provider output was rejected before a typed result could be disclosed",
    )


def run_probe() -> ProbeReport:
    try:
        import pydantic  # noqa: F401
    except Exception as exc:  # pragma: no cover - runtime evidence
        results = tuple(
            ProbeResult(probe_id, "UNVERIFIED", f"pydantic unavailable: {type(exc).__name__}: {exc}")
            for probe_id in ("SCHEMA-PROBE-001", "SCHEMA-PROBE-002", "SCHEMA-PROBE-003")
        )
        return ProbeReport(PROBE_SCHEMA_VERSION, "typed_schema_kernel", "block", results)

    kernel = TypedSchemaKernel()
    results = (
        _probe_invalid_input_before_effect(kernel),
        _probe_undeclared_input_field(kernel),
        _probe_invalid_output_before_disclosure(kernel),
    )
    status = "pass" if all(item.status == "PASS" for item in results) else "block"
    return ProbeReport(PROBE_SCHEMA_VERSION, "typed_schema_kernel", status, results)


def main() -> int:
    report = run_probe()
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
