"""Offline reproduction: tools/list cannot publish the schema of add_trial_case.

    <python3.12 with pydantic> repro_tools_list_offline.py <code-factory>/projects/cabinet_kernel

Imports the generated surface module (no network, no store) and asks it for
the published schema of every catalogue operation, as `tools/list` does.
"""
import sys
import traceback

sys.path.insert(0, sys.argv[1])
from cabinet_kernel import surface  # noqa: E402

failed = []
for name, model in surface._CATALOGUE:
    try:
        surface._published_schema(model)
    except Exception as error:  # noqa: BLE001
        failed.append((name, model.__name__, type(error).__name__, str(error)))
print(f"{len(surface._CATALOGUE)} catalogue operations; schema fails for {len(failed)}")
for f in failed:
    print("  ", *f)
