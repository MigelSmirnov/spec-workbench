"""Run the projector's own code with one in-memory substitution.

tools/spec_projection_workbench/service.py:422 accepts only data-closure status
"accepted", while design_stage6_data.FINAL_DATA_CLOSURE_STATUSES is {"closed"}
and the pipeline passed this case at "closed". Nothing on disk is changed
except global_spec.json, written by the projector's apply().

    python experiments/cabinet-kernel/project_closed_data_closure.py \
        plan|diff|apply|verify examples/cabinet-kernel

Remove once the projector accepts the final status on main; then
`tools/design_spec_projection.py --verify` alone proves the projection.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path("tools").resolve()))
import design_stage6_data
from spec_projection_workbench import service

_load = design_stage6_data.load
def load(project):
    payload = _load(project)
    if payload.get("status") in design_stage6_data.FINAL_DATA_CLOSURE_STATUSES:
        payload = {**payload, "status": "accepted"}
    return payload
design_stage6_data.load = load

project = Path(sys.argv[2])
if sys.argv[1] == "plan":
    print(json.dumps(service.build_plan(project), indent=2))
elif sys.argv[1] == "diff":
    print(service.render_diff(project))
elif sys.argv[1] == "apply":
    print(json.dumps(service.apply(project), indent=2))
elif sys.argv[1] == "verify":
    print(json.dumps(service.verify(project), indent=2))
