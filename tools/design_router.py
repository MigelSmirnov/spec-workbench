#!/usr/bin/env python3
"""Deterministic agent routing over the spec-workbench design tools.

The router is advisory and read-only. It does not parse Markdown, execute
commands, mutate documents, or infer design semantics. Its only responsibility
is to project one reviewed workflow from ``design_routes.json`` into concrete
tool arguments and CLI command previews.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Sequence

ROUTES_PATH = Path(__file__).with_name("design_routes.json")
PLAN_SCHEMA_VERSION = "spec_workbench_design_route_plan.v1"
SUPPORTED_EDITOR_OPERATIONS = frozenset(
    {"replace-section", "append-section", "insert-section", "replace-item"}
)
SUPPORTED_TOOLS = frozenset(
    {"design_index", "design_editor", "design_lint", "design_stage3", "design_trace", "pytest"}
)
StepKind = Literal["tool", "command", "checkpoint", "conditional", "foreach"]


class DesignRouterError(Exception):
    """A deterministic route could not be produced."""


@dataclass(frozen=True)
class RouteStep:
    id: str
    kind: StepKind
    tool: str | None
    action: str | None
    arguments: dict[str, object]
    command: str | None
    why: str
    requires: tuple[str, ...]
    stop_if: tuple[str, ...]
    next_on_success: str | None


@dataclass(frozen=True)
class RoutePlan:
    schema_version: str
    route_schema_version: str
    intent: str
    description: str
    project: str
    read_only: bool
    executes_commands: bool
    steps: tuple[RouteStep, ...]
    global_stop_conditions: tuple[str, ...]


def load_routes(path: Path = ROUTES_PATH) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DesignRouterError(f"design route table could not be loaded: {exc}") from exc
    if payload.get("schema_version") != "spec_workbench_design_routes.v1":
        raise DesignRouterError("unsupported design route schema")
    intents = payload.get("intents")
    steps = payload.get("steps")
    operations = payload.get("editor_operations")
    if not isinstance(intents, dict) or not isinstance(steps, dict):
        raise DesignRouterError("design route table must define intents and steps")
    if not isinstance(operations, dict):
        raise DesignRouterError("design route table must define editor_operations")
    if set(operations) != SUPPORTED_EDITOR_OPERATIONS:
        raise DesignRouterError("route table editor operations drifted from design_editor v1")
    for intent, definition in intents.items():
        if not isinstance(definition, dict) or not isinstance(definition.get("steps"), list):
            raise DesignRouterError(f"invalid route definition: {intent}")
        unknown = set(definition["steps"]) - set(steps)
        if unknown:
            raise DesignRouterError(
                f"route {intent!r} references unknown steps: {', '.join(sorted(unknown))}"
            )
    for step_id, definition in steps.items():
        if not isinstance(definition, dict):
            raise DesignRouterError(f"invalid step definition: {step_id}")
        tool = definition.get("tool")
        if tool is not None and tool not in SUPPORTED_TOOLS:
            raise DesignRouterError(f"step {step_id!r} names unsupported tool {tool!r}")
    return payload


def _require_text(value: str | None, label: str) -> str:
    if value is None or not value.strip():
        raise DesignRouterError(f"{label} is required")
    return value


def _command(argv: Sequence[str]) -> str:
    return shlex.join(list(argv))


def _editor_arguments(
    routes: dict[str, object],
    *,
    operation: str | None,
    item: str | None,
    section: str | None,
    after_section: str | None,
    content_file: Path | None,
) -> tuple[str, str, Path, list[str]]:
    operation = _require_text(operation, "operation")
    item = _require_text(item, "item")
    if operation not in SUPPORTED_EDITOR_OPERATIONS:
        raise DesignRouterError(f"unsupported editor operation: {operation}")
    if content_file is None:
        raise DesignRouterError("content_file is required")
    if not content_file.is_file():
        raise DesignRouterError(f"content file not found: {content_file}")
    definition = routes["editor_operations"][operation]
    section_input = definition["section_input"]
    values = {"item": item, "section": section, "after_section": after_section}
    if section_input is not None:
        _require_text(values[section_input], section_input)
    cli_arguments = [token.format(**values) for token in definition["cli_arguments"]]
    return operation, item, content_file, cli_arguments


def _step_runtime(
    step_id: str,
    *,
    project: str,
    state: int,
    kind: str,
    item: str | None,
    term: str | None,
    editor: tuple[str, str, Path, list[str]] | None,
) -> tuple[dict[str, object], str | None]:
    if step_id == "list_items":
        arguments = {"project": project, "state": state, "kind": kind}
        argv = ["python", "tools/design_index.py", project, "--list", "--state", str(state), "--kind", kind]
    elif step_id == "get_item":
        resolved_item = _require_text(item, "item")
        arguments = {"project": project, "item": resolved_item}
        argv = ["python", "tools/design_index.py", project, "--get", resolved_item]
    elif step_id == "item_references":
        resolved_item = _require_text(item, "item")
        arguments = {"project": project, "item": resolved_item}
        argv = ["python", "tools/design_index.py", project, "--references", resolved_item]
    elif step_id == "broad_mentions":
        resolved_term = _require_text(term, "term")
        arguments = {"project": project, "term": resolved_term}
        argv = ["python", "tools/design_index.py", project, "--mentions", resolved_term]
    elif step_id == "narrow_mentions":
        resolved_term = _require_text(term, "term")
        arguments = {"project": project, "term": resolved_term, "state": state, "kind": kind}
        argv = ["python", "tools/design_index.py", project, "--mentions-in-items", resolved_term, "--state", str(state), "--kind", kind]
    elif step_id == "selective_context":
        location = "$previous_result.source.path:$previous_result.source.line"
        arguments = {"project": project, "location": location, "radius": 5}
        argv = ["python", "tools/design_index.py", project, "--context", location, "--radius", "5"]
    elif step_id == "candidate_references":
        candidate = "$narrow_mentions.item_keys[]"
        arguments = {"project": project, "item": candidate}
        argv = ["python", "tools/design_index.py", project, "--references", candidate]
    elif step_id == "lint_state2":
        arguments = {"project": project, "state": 2, "context": True}
        argv = ["python", "tools/design_lint.py", project, "--state", "2"]
    elif step_id == "rebuild_index":
        arguments = {"project": project}
        argv = ["python", "tools/design_index.py", project]
    elif step_id == "state3_inventory":
        arguments = {"project": project, "state": 3}
        argv = ["python", "tools/design_stage3.py", project, "--list", "--json"]
    elif step_id == "state3_get":
        resolved_item = _require_text(item, "item")
        arguments = {"project": project, "module": resolved_item}
        argv = ["python", "tools/design_stage3.py", project, "--get", resolved_item, "--json"]
    elif step_id == "state3_lint":
        arguments = {"project": project, "state": 3}
        argv = ["python", "tools/design_stage3.py", project, "--lint", "--json"]
    elif step_id == "trace_2_3_check":
        arguments = {"project": project, "from_state": 2, "to_state": 3}
        argv = ["python", "tools/design_trace.py", project, "--check", "--json"]
    elif step_id == "trace_2_3_handoff":
        arguments = {"project": project, "from_state": 2, "to_state": 3, "consumer": "next_design_state"}
        argv = ["python", "tools/design_trace.py", project, "--handoff"]
    elif step_id in {"editor_dry_run", "editor_apply"}:
        if editor is None:
            raise DesignRouterError("editor route is missing editor arguments")
        operation, resolved_item, content_file, cli_arguments = editor
        apply = step_id == "editor_apply"
        arguments = {
            "project": project,
            "operation": operation,
            "item": resolved_item,
            "content_file": str(content_file),
            "apply": apply,
        }
        argv = ["python", "tools/design_editor.py", project, operation, *cli_arguments, "--content-file", str(content_file)]
        if apply:
            argv.append("--apply")
    elif step_id == "run_tests":
        arguments = {"path": ".", "quiet": True}
        argv = ["pytest", "-q"]
    else:
        return {}, None
    return arguments, _command(argv)


def route(
    project: Path,
    intent: str,
    *,
    item: str | None = None,
    term: str | None = None,
    operation: str | None = None,
    section: str | None = None,
    after_section: str | None = None,
    content_file: Path | None = None,
    state: int = 2,
    kind: str = "decision",
) -> RoutePlan:
    if not project.is_dir():
        raise DesignRouterError(f"project directory not found: {project}")
    if state < 0:
        raise DesignRouterError("state must be non-negative")
    if kind not in {"decision", "open_question"}:
        raise DesignRouterError(f"unsupported item kind: {kind}")
    routes = load_routes()
    intents = routes["intents"]
    if intent not in intents:
        raise DesignRouterError(
            f"unknown intent {intent!r}; choose one of: {', '.join(sorted(intents))}"
        )
    definition = intents[intent]
    if "item" in definition["required_inputs"]:
        _require_text(item, "item")
    if "term" in definition["required_inputs"]:
        _require_text(term, "term")
    editor = None
    if intent == "edit-fragment":
        editor = _editor_arguments(
            routes,
            operation=operation,
            item=item,
            section=section,
            after_section=after_section,
            content_file=content_file,
        )
    project_text = project.as_posix()
    step_ids = definition["steps"]
    result: list[RouteStep] = []
    for index, step_id in enumerate(step_ids):
        source = routes["steps"][step_id]
        arguments, command = _step_runtime(
            step_id,
            project=project_text,
            state=state,
            kind=kind,
            item=item,
            term=term,
            editor=editor,
        )
        result.append(RouteStep(
            id=step_id,
            kind=source["kind"],
            tool=source.get("tool"),
            action=source.get("action"),
            arguments=arguments,
            command=command,
            why=source["why"],
            requires=tuple(source.get("requires", [])),
            stop_if=tuple(source.get("stop_if", [])),
            next_on_success=step_ids[index + 1] if index + 1 < len(step_ids) else None,
        ))
    return RoutePlan(
        schema_version=PLAN_SCHEMA_VERSION,
        route_schema_version=routes["schema_version"],
        intent=intent,
        description=definition["description"],
        project=project_text,
        read_only=True,
        executes_commands=False,
        steps=tuple(result),
        global_stop_conditions=tuple(routes["global_stop_conditions"]),
    )


def render_json(plan: RoutePlan) -> str:
    return json.dumps(asdict(plan), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_human(plan: RoutePlan) -> str:
    lines = [f"Design route: {plan.intent}", f"Project: {plan.project}", plan.description]
    for number, step in enumerate(plan.steps, start=1):
        label = f"{number}. {step.id} [{step.kind}]"
        if step.tool and step.action:
            label += f" — {step.tool}.{step.action}"
        lines.extend(["", label, f"   why: {step.why}"])
        if step.command:
            lines.append(f"   command: {step.command}")
        if step.requires:
            lines.append("   requires: " + "; ".join(step.requires))
        if step.stop_if:
            lines.append("   stop if: " + "; ".join(step.stop_if))
        if step.next_on_success:
            lines.append(f"   next: {step.next_on_success}")
    lines.extend(["", "Global stop conditions:"])
    lines.extend(f"- {condition}" for condition in plan.global_stop_conditions)
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    intents = sorted(load_routes()["intents"])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Directory containing design Markdown")
    parser.add_argument("intent", choices=intents, help="Deterministic workflow intent")
    parser.add_argument("--item", help="Explicit item ID, supporting source key, or module key")
    parser.add_argument("--term", help="Lexical term for the broad-to-narrow loop")
    parser.add_argument("--operation", choices=sorted(SUPPORTED_EDITOR_OPERATIONS))
    parser.add_argument("--section", help="Target section for replace/append")
    parser.add_argument("--after-section", help="Existing section after which to insert")
    parser.add_argument("--content-file", type=Path, help="Complete editor content file")
    parser.add_argument("--state", type=int, default=2)
    parser.add_argument("--kind", choices=["decision", "open_question"], default="decision")
    parser.add_argument("--json", action="store_true", help="Emit stable machine-readable plan")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        plan = route(
            args.project,
            args.intent,
            item=args.item,
            term=args.term,
            operation=args.operation,
            section=args.section,
            after_section=args.after_section,
            content_file=args.content_file,
            state=args.state,
            kind=args.kind,
        )
    except DesignRouterError as exc:
        print(f"design_router: error: {exc}", file=sys.stderr)
        return 2
    print(render_json(plan) if args.json else render_human(plan), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
