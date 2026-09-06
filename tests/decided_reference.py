"""The reference case with its undecided facts decided, for tests that need a ready State 6.

Under the fence ``examples/cabinet-backend`` is truthfully not ready: two public
mutating operations produce timestamps and their modules retain no clock port.
A test that needs a ready State 6 decides that here, in a copy, the way an
author would — a ``Clock`` port retained by the owning services — instead of
pretending the reference case is ready.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"
CONTRACTS = "60_contracts.json"
PLAN = "60_contract_plan.json"
MODEL_CLOSURE = "60_model_closure_support.json"
PURPOSE = "Close the concrete service or bounded stream type required by canonical contracts."


def decided_reference(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    closure_path = project / MODEL_CLOSURE
    closure = json.loads(closure_path.read_text(encoding="utf-8"))
    closure["models"]["Clock"] = {"kind": "interface"}
    closure_path.write_text(json.dumps(closure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    catalog_path = project / CONTRACTS
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    plan_path = project / PLAN
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    additions = {
        "Clock.now": ("module:models", "(self) -> datetime"),
        "RegistryContextService.__init__": ("module:registry_context", "(self, clock: Clock) -> None"),
        "HoldedGatewayService.__init__": ("module:holded_gateway", "(self, clock: Clock) -> None"),
    }
    for function, (module, signature) in additions.items():
        catalog["contracts"][function] = signature
        plan["functions"].append({
            "function": function, "module": module, "visibility": "internal",
            "purpose": PURPOSE, "public_operation": None, "router_operation": None,
        })
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    notes_path = project / "80_notes.md"
    notes = notes_path.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join((
        "Clock.now: [DEPENDENCY_BOUNDARY] MUST return the current wall-clock time as a timezone-aware UTC datetime and never a naive value.",
        "RegistryContextService.__init__: [DEPENDENCY_BOUNDARY] MUST retain the exact supplied Clock port and read every observed_at from it; MUST NOT construct an alternate time source.",
        "HoldedGatewayService.__init__: [DEPENDENCY_BOUNDARY] MUST retain the exact supplied Clock port and read every attempt timestamp from it; MUST NOT construct an alternate time source.",
    )) + "\n"
    notes_path.write_text(notes, encoding="utf-8")
    return project
