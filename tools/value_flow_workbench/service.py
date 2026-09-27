from __future__ import annotations

from pathlib import Path
from typing import Any

import fence
from value_flow_workbench import case as case_loader
from value_flow_workbench import closure, lenses
from value_flow_workbench.model import CLOSURE_FILE, REPORT_SCHEMA


def coverage(project: Path) -> dict[str, Any]:
    project = project.resolve()
    case = case_loader.load(project)
    authored = closure.load_optional(project)
    declared_outputs = authored["outputs"] if authored else {}
    declared_inputs = authored["inputs"] if authored else {}
    output_summary, findings, constructed = lenses.outputs(case, declared_outputs)
    input_summary, input_findings = lenses.inputs(case, declared_inputs, constructed)
    collaborator_summary, collaborator_findings = lenses.collaborators(case)
    carrier_summary, carrier_findings = lenses.carriers(case)
    findings = findings + input_findings + collaborator_findings + carrier_findings
    judged_modules = {item.module for item in case.functions.values()
                      if item.module is not None and item.module not in case.deterministic_modules}
    # A lens that judged nothing over a non-empty design has not passed; it has not run.
    if not output_summary["enabled"]:
        findings.append({"severity": "error", "code": "value_flow_lens_judged_nothing", "lens": "outputs",
                         "message": f"outputs: {output_summary['reason']}"})
    if collaborator_summary["edges"] == 0 and len(judged_modules) > 1:
        findings.append({"severity": "error", "code": "value_flow_lens_judged_nothing", "lens": "collaborators",
                         "message": f"collaborators: State 3 names no collaborator for any of {len(judged_modules)} modules; "
                                    "write the modules a module calls in backticks under Knows (or 'delegates to')"})
    if authored is not None and authored["status"] != "closed" and not findings:
        findings.append({"severity": "error", "code": "value_flow_closure_open",
                         "message": f"{CLOSURE_FILE} resolves everything but is still marked open; close it"})
    if carrier_summary["state1_models"] == 0 and case.index.classes:
        findings.append({"severity": "error", "code": "value_flow_lens_judged_nothing", "lens": "carriers",
                         "message": "carriers: no State 1 model section (## Model <key> — <Name>) matches a closed model; "
                                    "the closure was written with nothing to be checked against"})
    findings = fence.enforce(findings)
    errors = fence.stops(findings)
    judged = sum(1 for item in case.functions.values()
                 if item.module is not None and item.module not in case.deterministic_modules)
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": project.name,
        "closure": {"exists": authored is not None, "status": authored["status"] if authored else None},
        "summary": {
            "functions_judged": judged,
            "functions_without_module": sum(1 for item in case.functions.values() if item.module is None),
            "deterministic_modules": sorted(case.deterministic_modules),
            "instant_type": case.instant_type,
            "wall_clock": ".".join(case.wall_clock) if case.wall_clock else None,
            "outputs": output_summary,
            "inputs": input_summary,
            "collaborators": collaborator_summary,
            "carriers": carrier_summary,
            "errors": errors,
            "handoff_ready": errors == 0,
        },
        "findings": findings,
    }
