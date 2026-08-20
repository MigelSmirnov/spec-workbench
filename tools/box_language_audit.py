#!/usr/bin/env python3
"""Audit that deterministic box compiler behavior is declared by the box language."""
from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from box_composition import IMPLEMENTED_BOX_LANGUAGE_RULES as COMPOSITION_RULES
from box_derivability import IMPLEMENTED_BOX_LANGUAGE_RULES as DERIVABILITY_RULES


AUDIT_SCHEMA_VERSION = "spec_workbench_box_language_audit.v0"
EXPECTED_LANGUAGE_VERSION = "cabinet_box_language.v0"
DEFAULT_LANGUAGE = Path("experiments/cabinet-vault/box_language_v0.yaml")


@dataclass(frozen=True)
class AuditFinding:
    code: str
    subject: str
    message: str


@dataclass(frozen=True)
class AuditReport:
    schema_version: str
    language_version: str | None
    status: str
    checked_tools: tuple[str, ...]
    checked_rules: tuple[str, ...]
    findings: tuple[AuditFinding, ...]


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PyYAML is required to audit the box language") from exc
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("box language must be a mapping")
    return value


def current_implementations() -> dict[str, frozenset[str]]:
    return {
        "box_derivability": DERIVABILITY_RULES,
        "box_composition": COMPOSITION_RULES,
    }


def _test_exists(root: Path, node_id: str) -> bool:
    path_text, separator, function_name = node_id.partition("::")
    if not separator or not path_text or not function_name:
        return False
    path = root / path_text
    if not path.is_file():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
        for node in tree.body
    )


def audit_language(
    language_path: Path = DEFAULT_LANGUAGE,
    *,
    root: Path | None = None,
    implementations: dict[str, frozenset[str]] | None = None,
) -> AuditReport:
    root = Path.cwd() if root is None else root
    definition = _load_yaml(language_path)
    implementations = current_implementations() if implementations is None else implementations

    language_version = definition.get("language_version")
    rules = definition.get("rules")
    bindings = definition.get("tool_bindings")
    findings: list[AuditFinding] = []

    if language_version != EXPECTED_LANGUAGE_VERSION:
        findings.append(
            AuditFinding(
                "UNSUPPORTED_LANGUAGE_VERSION",
                str(language_version),
                f"expected {EXPECTED_LANGUAGE_VERSION}",
            )
        )
    if not isinstance(rules, dict):
        findings.append(AuditFinding("INVALID_RULE_TABLE", "rules", "rules must be a mapping"))
        rules = {}
    if not isinstance(bindings, dict):
        findings.append(
            AuditFinding("INVALID_TOOL_BINDINGS", "tool_bindings", "tool_bindings must be a mapping")
        )
        bindings = {}

    declared_rule_ids = set(rules)

    for tool_name, implemented_rules in sorted(implementations.items()):
        binding = bindings.get(tool_name)
        if not isinstance(binding, dict):
            findings.append(
                AuditFinding(
                    "IMPLEMENTATION_WITHOUT_LANGUAGE_BINDING",
                    tool_name,
                    "compiler tool has no declared language binding",
                )
            )
            continue
        declared = binding.get("declared_rules")
        if not isinstance(declared, list) or not all(isinstance(item, str) for item in declared):
            findings.append(
                AuditFinding(
                    "INVALID_DECLARED_RULES",
                    tool_name,
                    "tool binding must declare a list of rule ids",
                )
            )
            continue
        declared_set = set(declared)
        for rule_id in sorted(implemented_rules - declared_set):
            findings.append(
                AuditFinding(
                    "HIDDEN_IMPLEMENTATION_RULE",
                    f"{tool_name}:{rule_id}",
                    "compiler implements a rule that the language binding does not declare",
                )
            )
        for rule_id in sorted(declared_set - implemented_rules):
            findings.append(
                AuditFinding(
                    "DECLARED_RULE_NOT_IMPLEMENTED",
                    f"{tool_name}:{rule_id}",
                    "language requires a rule that the compiler does not declare as implemented",
                )
            )
        for rule_id in sorted(declared_set - declared_rule_ids):
            findings.append(
                AuditFinding(
                    "UNKNOWN_DECLARED_RULE",
                    f"{tool_name}:{rule_id}",
                    "tool binding references a rule absent from the language rule table",
                )
            )

    for tool_name in sorted(set(bindings) - set(implementations)):
        findings.append(
            AuditFinding(
                "LANGUAGE_BINDING_WITHOUT_IMPLEMENTATION",
                tool_name,
                "language binds rules to a compiler tool not registered by this audit",
            )
        )

    for rule_id, rule in sorted(rules.items()):
        if not isinstance(rule, dict):
            findings.append(AuditFinding("INVALID_RULE", rule_id, "rule must be a mapping"))
            continue
        tools = rule.get("tools")
        if not isinstance(tools, list) or not tools or not all(isinstance(item, str) for item in tools):
            findings.append(
                AuditFinding("RULE_WITHOUT_TOOL_OWNER", rule_id, "rule must name at least one compiler tool")
            )
        else:
            for tool_name in tools:
                binding = bindings.get(tool_name)
                declared = binding.get("declared_rules", []) if isinstance(binding, dict) else []
                if rule_id not in declared:
                    findings.append(
                        AuditFinding(
                            "RULE_TOOL_BINDING_MISMATCH",
                            f"{rule_id}:{tool_name}",
                            "rule names a tool whose binding does not include the rule",
                        )
                    )
        conformance_test = rule.get("conformance_test")
        if not isinstance(conformance_test, str) or not conformance_test:
            findings.append(
                AuditFinding(
                    "RULE_WITHOUT_CONFORMANCE_TEST",
                    rule_id,
                    "machine-addressable compiler rule must name a conformance test",
                )
            )
        elif not _test_exists(root, conformance_test):
            findings.append(
                AuditFinding(
                    "MISSING_CONFORMANCE_TEST",
                    rule_id,
                    conformance_test,
                )
            )

    return AuditReport(
        schema_version=AUDIT_SCHEMA_VERSION,
        language_version=language_version if isinstance(language_version, str) else None,
        status="pass" if not findings else "block",
        checked_tools=tuple(sorted(implementations)),
        checked_rules=tuple(sorted(declared_rule_ids)),
        findings=tuple(findings),
    )


def render_json(report: AuditReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def render_human(report: AuditReport) -> str:
    lines = [
        f"Box language audit: {report.status}",
        f"Language: {report.language_version}",
        f"Tools: {', '.join(report.checked_tools)}",
        f"Rules: {len(report.checked_rules)}",
    ]
    for finding in report.findings:
        lines.append(f"- {finding.code}: {finding.subject} — {finding.message}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", type=Path, nargs="?", default=DEFAULT_LANGUAGE)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    report = audit_language(args.language)
    print(render_json(report) if args.as_json else render_human(report), end="")
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
