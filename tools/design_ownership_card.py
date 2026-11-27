"""Preview the ownership of a State 2 decision beside a State 3 module."""
import argparse
import json
from pathlib import Path

import design_index
import design_stage3
import design_trace
from design_lint import NUMBERED_RULE_RE
from imports_workbench import service as imports
from standard_backends import standard_backends


def decision_basis(case, decision, rule):
    location = decision["source"]
    basis = {"title": decision["title"], "source": location}
    if rule is None:
        return basis
    section = next((s for s in decision["sections"] if s["title"].casefold() == "normative rules"), None)
    if section:
        path = location["path"]
        lines = (case / path).read_text(encoding="utf-8").splitlines()
        entries = [(i, int(m.group(1))) for i in range(section["start_line"], section["end_line"])
                   if (m := NUMBERED_RULE_RE.match(lines[i]))]
        for index, (start, number) in enumerate(entries):
            if number == rule:
                end = entries[index + 1][0] if index + 1 < len(entries) else section["end_line"]
                return {**basis, "rule": rule, "passage": "\n".join(lines[start:end]).strip(),
                        "source": {"path": path, "start_line": start + 1, "end_line": end}}
    raise ValueError(f"No normative rule {rule} in {decision['key']}; open {location['path']}")


def constant_evidence(case, symbol):
    provider = next(b for b in standard_backends() if b.id == "data_provider")
    backend = provider.authored_backend(case)
    if not backend:
        raise ValueError(f"No closed provider at {provider.closure_file}; omit --constant to inspect ownership")
    constants = backend.get("constants")
    wiring = backend.get("wiring")
    if not isinstance(constants, dict) or not isinstance(wiring, dict) or not isinstance(wiring.get("module"), str):
        raise ValueError(f"Invalid constants or wiring in {provider.closure_file}")
    if symbol not in constants:
        raise ValueError(f"{symbol} is absent from {provider.closure_file}")
    if not isinstance(constants[symbol], dict):
        raise ValueError(f"Invalid declaration of {symbol} in {provider.closure_file}")
    name = wiring["module"]
    table = imports.load_table(case)
    if table is not None and (not isinstance(table, dict) or table.get("schema_version") != imports.TABLE_SCHEMA or not isinstance(table.get("scopes"), dict)):
        raise ValueError(f"Invalid import table: {imports.table_path(case).name}")
    readers = [m for m, edges in imports.derive(table).items() if symbol in edges.get(name, [])]
    return {"constant": symbol, "declared_in": provider.closure_file, "supplier": name,
            "row_model": constants[symbol].get("row_model"),
            "imports_source": imports.table_path(case).name if table is not None else None,
            "declared_importers": readers if table is not None else None}


def card(case, decision_key, module_name, rule=None, constant=None, owner_reason=None):
    key = decision_key.upper()
    index = design_index.build_index(case)
    if key in index["diagnostics"]["duplicate_keys"]:
        raise ValueError(f"Ambiguous decision {key}; inspect its declarations")
    decision = next((item for item in index["items"] if item["key"] == key), None)
    if not decision or decision["kind"] != "decision" or decision["state"] != 2:
        raise ValueError(f"Choose an indexed State 2 decision; {key} does not resolve to one")
    manifest = design_stage3.manifest(case)
    module_key = "module:" + module_name.removeprefix("module:")
    if module_key in manifest["diagnostics"]["duplicate_module_keys"]:
        raise ValueError(f"Ambiguous State 3 module {module_key}; inspect its declarations")
    module = next((m for m in manifest["modules"] if m["key"] == module_key), None)
    if not module:
        raise ValueError(f"Unknown State 3 module {module_name}; use design_stage3.py --list")
    trace_path = case / design_trace.DEFAULT_TRACE_FILE
    trace = design_trace.analyze(case) if trace_path.exists() else {"decisions": {}, "findings": []}
    current = trace["decisions"].get(key)
    result = {"decision": decision_basis(case, decision, rule), "module": module["key"],
              "module_location": module["source"], "trace_source": trace_path.name if trace_path.exists() else None,
              "recorded_ownership": current,
              "trace_findings": [f for f in trace["findings"] if f["subject"] == key],
              "question": "Is this module responsible for the decision, or does it supply or read its data?",
              "return_to": {"decision": key, "rule": rule, "module": module["key"], "constant": constant}}
    if constant:
        evidence = constant_evidence(case, constant)
        result["data_dependency"] = evidence
        if evidence["row_model"]:
            result["state1_question"] = (f"Does {evidence['row_model']} have independent product meaning? "
                                         "If unresolved, take this question to State 1, then return to this card.")
    if owner_reason is not None:
        if not owner_reason.strip():
            raise ValueError("State the basis for assigning the whole decision to this module")
        result["proposed_ownership"] = {"decision": key, "primary_owner": module["key"], "basis": owner_reason}
    return result


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("case", type=Path)
    cli.add_argument("decision", help="State 2 decision ID")
    cli.add_argument("module", help="module under consideration")
    cli.add_argument("--rule", type=int, help="show this numbered normative rule as evidence")
    cli.add_argument("--constant", help="show its declared supplier and importers")
    cli.add_argument("--propose-owner", metavar="BASIS", help="preview this module as owner of the whole decision")
    args = cli.parse_args(argv)
    try:
        result = card(args.case, args.decision, args.module, args.rule, args.constant, args.propose_owner)
    except (ValueError, OSError, design_trace.DesignTraceError, imports.ImportsError) as exc:
        cli.exit(2, f"Cannot open ownership card: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
