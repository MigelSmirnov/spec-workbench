"""Callables an emitter lowers from closed IR need no note (notes_workbench.language)."""

from __future__ import annotations

from notes_workbench.language import factory_coverage

SPEC = {
    "module_functions": {"router": ["create_app", "scan_route"], "api": ["check_token"]},
    "contracts": {
        "create_app": "(token: str) -> FastAPI",
        "scan_route": "(request: Request, project_id: str) -> ScanResult",
        "check_token": "(token: str, credential: str) -> None",
    },
    "notes": ["check_token: [SECURITY_BOUNDARY] MUST compare the credential with the token in constant time."],
}


def test_an_emitted_callable_without_a_note_is_not_a_blocker() -> None:
    assert {f["scope"] for f in factory_coverage(SPEC)} == {"create_app", "scan_route"}
    assert factory_coverage(SPEC, {"create_app", "scan_route"}) == []


def test_an_llm_callable_without_a_note_still_blocks() -> None:
    spec = {**SPEC, "notes": []}
    assert {f["scope"] for f in factory_coverage(spec, {"create_app", "scan_route"})} == {"check_token"}
