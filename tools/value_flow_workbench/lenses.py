"""Three questions every contract answers before anything is generated.

    outputs        a required instant of a result has a source
    inputs         a scalar argument of a constructing function has a sink
    collaborators  a module State 3 says this module knows is reachable from its notes
    carriers       a fact State 1 claims, and a field a rule, flow or operation names, exists in the model closure

What the design states already imply is resolved without an author; only the
residue is asked for, in ``70_value_flow_closure.json``. Every lens returns its
denominator with its findings.
"""
from __future__ import annotations

import re
from typing import Any

from model_surface_workbench.index import scalar_type
from value_flow_workbench.case import Case, Function, declared_type
from value_flow_workbench.model import INPUT_SINKS, OUTPUT_SOURCES, SINKS_WITH_FIELD


def _finding(code: str, message: str, **fields: Any) -> dict[str, Any]:
    return {"severity": "error", "code": code, "message": message, **fields}


def _names(text: str, *words: str) -> bool:
    return any(re.search(rf"(?<![A-Za-z0-9_]){re.escape(word)}(?![A-Za-z0-9_])", text) for word in words if word)


def _judged(case: Case) -> list[Function]:
    return [item for name, item in sorted(case.functions.items())
            if item.module is not None and item.module not in case.deterministic_modules]


def _carries_instant(case: Case, annotation: str, field: str | None = None) -> bool:
    """With ``field``: one record handed in carries the same-named instant (a draft, the record
    being replaced). A collection of records does not: prior evidence is not the new instant."""
    instant = case.instant_type
    if declared_type(annotation) == instant:
        return True
    if field is not None:
        single = scalar_type(annotation)
        models = [single] if single in case.index.classes and case.index.classes[single].fields else []
    else:
        models = case.record_models(annotation)
    for model in models:
        fields = case.index.classes[model].fields
        candidates = [fields[field]] if field is not None and field in fields else ([] if field is not None else list(fields.values()))
        if any(instant in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", item) for item in candidates):
            return True
    return False


def _reaches(case: Case, function: Function, callee: str) -> bool:
    """The notes of the function's module name the callee or its module."""
    owner = case.functions[callee].module if callee in case.functions else None
    return _names(case.module_notes(function.module or ""), callee) or _names(function.note_text, owner or "")


def outputs(case: Case, declared: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[str]]]:
    """Returns (summary, findings, constructed) — constructed maps a function to the models it stamps."""
    summary: dict[str, Any] = {"enabled": case.instant_type is not None, "pairs": 0, "by_source": {}, "unresolved": 0}
    findings: list[dict[str, Any]] = []
    constructed: dict[str, list[str]] = {}
    if case.instant_type is None:
        summary["reason"] = "the case declares no rules.time_source_policy representation: the instant type is unknown"
        return summary, findings, constructed
    accessor = ".".join(case.wall_clock) if case.wall_clock else None
    seen: set[tuple[str, str]] = set()
    for function in _judged(case):
        rows = declared.get(function.name) or {}
        for model in case.record_models(function.returns):
            for field, annotation in case.index.classes[model].fields.items():
                if declared_type(annotation) != case.instant_type:
                    continue
                address = f"{model}.{field}"
                seen.add((function.name, address))
                summary["pairs"] += 1
                row = rows.get(address)
                source, problem = _output_source(case, function, field, row, accessor)
                if problem:
                    summary["unresolved"] += 1
                    findings.append(_finding(
                        problem[0], f"{function.module}.{function.name} -> {address}: {problem[1]}",
                        function=function.name, module=function.module, address=address,
                    ))
                    # A public mutating operation whose instant is still open stamps it in every
                    # likely resolution: judge its arguments now, not in a second wave.
                    if problem[0] == "instant_without_source" and function.name in case.mutating:
                        constructed.setdefault(function.name, []).append(model)
                    continue
                summary["by_source"][source] = summary["by_source"].get(source, 0) + 1
                if source.endswith("clock"):
                    constructed.setdefault(function.name, []).append(model)
    for name, rows in declared.items():
        for address in rows:
            if (name, address) not in seen:
                findings.append(_finding(
                    "value_flow_declaration_stale",
                    f"outputs.{name}.{address}: no contract returns this required instant any more; delete the declaration",
                    function=name, address=address,
                ))
    return summary, findings, constructed


def _output_source(
    case: Case, function: Function, field: str, row: Any, accessor: str | None,
) -> tuple[str, tuple[str, str] | None]:
    parameters = function.parameters
    if row is not None:
        source = row.get("source") if isinstance(row, dict) else None
        via = row.get("via") if isinstance(row, dict) else None
        if source not in OUTPUT_SOURCES or not isinstance(row, dict) or set(row) - {"source", "via"}:
            return "", ("value_flow_declaration_invalid", f"source must be one of {sorted(OUTPUT_SOURCES)} with an optional via")
        if source == "clock":
            if accessor is None:
                return "", ("declared_clock_without_accessor", "the case closes no wall-clock backend that could hand the instant out")
            if not _names(function.note_text, accessor):
                return "", ("declared_clock_not_named", f"the note of {function.name} must name {accessor}: an unnamed clock is not handed to the module")
        if source == "argument" and not any(name == via and _carries_instant(case, kind) for name, kind in parameters):
            return "", ("value_flow_declaration_invalid", f"argument {via!r} is not a parameter that carries {case.instant_type}")
        if source == "callee":
            callee = case.functions.get(via) if isinstance(via, str) else None
            if callee is None or not _carries_instant(case, callee.returns):
                return "", ("value_flow_declaration_invalid", f"callee {via!r} is not a contract that returns a record with {case.instant_type}")
            if not _reaches(case, function, callee.name):
                return "", ("declared_callee_not_named", f"no note of {function.module} names {via}: the module cannot call what it never names")
        return f"declared:{source}", None
    if any(_carries_instant(case, kind, field) for _, kind in parameters):
        return "argument", None
    if function.name in case.read_only:
        return "stored", None
    if accessor is not None and _names(function.note_text, accessor):
        return "clock", None
    hint = f"name {accessor} in the note" if accessor else "close a wall-clock backend"
    return "", ("instant_without_source",
                f"no parameter carries it, State 5 does not make the operation read-only and the note names no clock; "
                f"{hint}, or declare the source in 70_value_flow_closure.json")


def inputs(
    case: Case, declared: dict[str, dict[str, Any]], constructed: dict[str, list[str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary = {"constructing_functions": len(constructed), "pairs": 0, "resolved": 0, "unresolved": 0}
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for name in sorted(constructed):
        function = case.functions[name]
        models = constructed[name]
        fields = {field for model in models for field in case.index.classes[model].fields}
        rows = declared.get(name) or {}
        for parameter, annotation in function.parameters:
            if case.record_models(annotation):
                continue  # a structured argument is consumed field by field; its models are judged on their own
            summary["pairs"] += 1
            seen.add((name, parameter))
            problem = None
            if parameter in rows:
                problem = _sink_problem(case, function, models, rows[parameter])
            elif parameter not in fields:
                problem = ("argument_without_sink",
                           f"{' / '.join(models)} has no field {parameter!r} and nothing says what the argument becomes; "
                           "add the field, or declare the sink in 70_value_flow_closure.json")
            if problem:
                summary["unresolved"] += 1
                findings.append(_finding(problem[0], f"{function.module}.{name}({parameter}: {annotation}): {problem[1]}",
                                         function=name, module=function.module, parameter=parameter))
            else:
                summary["resolved"] += 1
    for name, rows in declared.items():
        for parameter in rows:
            if (name, parameter) not in seen:
                findings.append(_finding(
                    "value_flow_declaration_stale",
                    f"inputs.{name}.{parameter}: not a scalar argument of a constructing function any more; delete the declaration",
                    function=name, parameter=parameter,
                ))
    return summary, findings


def _sink_problem(case: Case, function: Function, models: list[str], row: Any) -> tuple[str, str] | None:
    sink = row.get("sink") if isinstance(row, dict) else None
    target = row.get("to") if isinstance(row, dict) else None
    if sink not in INPUT_SINKS or not isinstance(row, dict) or set(row) - {"sink", "to"}:
        return "value_flow_declaration_invalid", f"sink must be one of {sorted(INPUT_SINKS)} with an optional to"
    if sink in SINKS_WITH_FIELD:
        model, _, field = str(target or "").partition(".")
        surface = case.index.classes.get(model)
        if surface is None or field not in surface.fields:
            return "declared_sink_unknown", f"sink {sink} names {target!r}, which is not a declared model field"
        if sink == "field" and model not in models:
            return "declared_sink_unknown", f"sink field must be a field of the constructed {' / '.join(models)}, not of {model}"
    if sink == "forwarded":
        if target not in case.functions:
            return "declared_sink_unknown", f"sink forwarded names {target!r}, which is not a contract"
        if not _reaches(case, function, str(target)):
            return "declared_callee_not_named", f"no note of {function.module} names {target}: the module cannot call what it never names"
    return None


def collaborators(case: Case) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary = {"edges": 0, "reachable": 0, "unreachable": 0}
    findings: list[dict[str, Any]] = []
    for module in sorted(case.knows):
        if module in case.deterministic_modules or module not in case.module_functions:
            continue
        text = case.module_notes(module)
        for other in case.knows[module]:
            summary["edges"] += 1
            if _names(text, other, *sorted(case.module_functions.get(other, ()))):
                summary["reachable"] += 1
                continue
            summary["unreachable"] += 1
            operations = ", ".join(sorted(case.module_functions.get(other, ()))[:6]) or "no contracted operation"
            findings.append(_finding(
                "known_collaborator_unreachable",
                f"{module} -> {other}: State 3 says {module} knows {other}, but no note of {module} names it or any "
                f"of its operations ({operations}); a module that cannot call its collaborator invents what it would have returned",
                module=module, collaborator=other,
            ))
    return summary, findings


def carriers(case: Case) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The typed model closure is the one field list; everything that names a field is checked against it.

    State 1 claims the facts a concept carries before any module exists, and rules, flows and
    operations name fields outright. Both are written by hand, apart from the closure: a closure
    that silently renames or regroups them leaves notes and contracts speaking two vocabularies.
    """
    summary = {"state1_models": len(case.state1_facts) + len(case.state1_nameless), "facts": 0,
               "references": len(case.field_references), "without_carrier": 0}
    findings: list[dict[str, Any]] = []
    for model in sorted(case.state1_nameless):
        summary["without_carrier"] += 1
        findings.append(_finding(
            "state1_model_without_named_facts",
            f"{case.state1_nameless[model]}: State 1 describes {model} without naming a single fact it carries, "
            f"so whoever wrote the closure chose its {len(case.index.classes[model].fields)} fields alone",
            model=model, document=case.state1_nameless[model],
        ))
    for model in sorted(case.state1_facts):
        document, names = case.state1_facts[model]
        declared = case.index.classes[model].fields
        summary["facts"] += len(names)
        lost = [name for name in names if name not in declared]
        if lost:
            summary["without_carrier"] += len(lost)
            findings.append(_finding(
                "state1_fact_without_carrier",
                f"{document}: State 1 says {model} carries {', '.join(lost)}; the model closure declares "
                f"{', '.join(sorted(declared))}",
                model=model, document=document, facts=lost,
            ))
    for document, line, model, name in case.field_references:
        if name not in case.index.classes[model].fields and name not in case.index.classes[model].methods:
            summary["without_carrier"] += 1
            findings.append(_finding(
                "named_field_without_carrier",
                f"{document}:{line} names {model}.{name}; the model closure declares "
                f"{', '.join(sorted(case.index.classes[model].fields))}",
                model=model, document=document, line=line, field=name,
            ))
    return summary, findings
