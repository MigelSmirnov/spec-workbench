"""Build the Kernel implementation of the Registry audit-cluster model.

    python experiments/registry-state2-kernel-pilot/adapter/build.py

Writes adapter/kernel_function.py: one Python module, standard library only,
as Cabinet Kernel's sandbox requires (spec A03 rules 2-3). It is the previous
experiment's model, byte for byte, followed by its version table and an
entry point `run(inputs)`:

1. `../registry-state2-investigation/model/sandbox.py`, unchanged
   (its `from __future__` line stays first);
2. `VERSIONS` from that experiment's `model/sources.py`, extracted with `ast`,
   so no other part of sources.py (and no git access) enters the sandbox;
3. `entry.py` from this directory: the adapter.

The adaptations are listed in ADAPTATIONS.md. The model's meaning is not
touched: every rule, reading and reduction is sandbox.py's own.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREV = HERE.parents[1] / "registry-state2-investigation" / "model"


def versions_literal() -> str:
    tree = ast.parse((PREV / "sources.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "VERSIONS":
            return "VERSIONS: dict[str, dict] = " + ast.get_source_segment(
                (PREV / "sources.py").read_text(encoding="utf-8"), node.value) + "\n"
    raise SystemExit("VERSIONS not found in sources.py")


def main() -> None:
    model = (PREV / "sandbox.py").read_text(encoding="utf-8")
    entry = (HERE / "entry.py").read_text(encoding="utf-8")
    future = "from __future__ import annotations\n"
    assert model.count(future) == 1
    # ADAPTATION 3 (ADAPTATIONS.md): the Kernel's runner executes the module
    # without entering it in sys.modules, and `dataclasses` resolves deferred
    # annotations through sys.modules[cls.__module__].__dict__. A stub module
    # under the same name gives it an empty namespace to look in; nothing of
    # the model reads it.
    shim = (future + "import sys as _k_sys, types as _k_types  # adaptation 3\n"
            "_k_sys.modules.setdefault(__name__, _k_types.ModuleType(__name__))  # adaptation 3\n")
    model = model.replace(future, shim)
    parts = [
        model.rstrip("\n"),
        "\n\n# ===== versions: VERSIONS of registry-state2-investigation/model/sources.py =====\n",
        versions_literal(),
        "\n# ===== adapter: registry-state2-kernel-pilot/adapter/entry.py =====\n",
        entry,
    ]
    code = "\n".join(parts)
    (HERE / "kernel_function.py").write_text(code, encoding="utf-8")
    print("kernel_function.py", len(code.encode()), "bytes; sha256",
          hashlib.sha256(code.encode()).hexdigest())
    print("model sandbox.py sha256", hashlib.sha256((PREV / "sandbox.py").read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
