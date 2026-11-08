"""Frame of the data-provider module in client-portal's assembled specification.

The State 8 projector (tools/design_spec_projection.py) carries
rules.data_provider_backend from 70_data_provider_closure.json, but it places a
module only through its State 6 contracts, and the data provider has none; and
it sets the rules namespaces 60_data_closure.json declares without removing the
ones that file no longer declares. This script does exactly those two things,
read from the case's sources and deciding nothing, as the cabinet-kernel case's
State 8 skeleton did (spec-workbench f924c17f):

- module_order gets `data_provider` right after `models` (it imports only the
  row models and enumerations of models); module_paths `core/data_provider`
  beside `core/models`; module_functions and imports.internal list exactly the
  constants of the closure (SPEC_STANDARD 6.10);
- each rules namespace named in RETIRED is removed once 60_data_closure.json no
  longer declares it: its values moved to a data-provider constant or were a
  second home of a models enumeration (SOURCE.md, "Data placement").

Idempotent: a second run changes nothing. Run before
`python tools/design_spec_projection.py examples/client-portal --apply`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[2] / "examples" / "client-portal"
MODULE = "data_provider"
PATH = "core/data_provider"
RETIRED = (
    "capability_catalog",              # second home of models.Capability (A1)
    "principal_capability_sets",       # CAPABILITY_SET_MEMBERS (A2)
    "registry_failure_translation",    # second home of models.RegistryFailureKind (A6)
    "supported_external_contract_versions",  # SUPPORTED_*_CONTRACT_VERSIONS (A7)
)


def main() -> int:
    spec_path = CASE / "global_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    closure = json.loads((CASE / "70_data_provider_closure.json").read_text(encoding="utf-8"))
    data = json.loads((CASE / "60_data_closure.json").read_text(encoding="utf-8"))
    backend = closure["backend_ir"]
    assert backend["wiring"]["module"] == MODULE
    constants = sorted(backend["constants"])

    order = [m for m in spec["module_order"] if m != MODULE]
    order.insert(order.index("models") + 1, MODULE)
    spec["module_order"] = order
    paths = dict(spec["module_paths"])
    paths[MODULE] = PATH
    spec["module_paths"] = {m: paths[m] for m in order}
    functions = dict(spec["module_functions"])
    functions[MODULE] = constants
    spec["module_functions"] = {m: functions[m] for m in order if m in functions}
    spec["imports"]["internal"][MODULE] = constants

    declared = data["sections"]["rules"]
    for namespace in RETIRED:
        if namespace in declared:
            raise SystemExit(f"rules.{namespace} is still declared by 60_data_closure.json")
        spec["rules"].pop(namespace, None)

    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
