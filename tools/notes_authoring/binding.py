"""M6: which module each note belongs to (decision Q1).

A note's scope is a callable (`function`, `Class.method`) or a module name.
The owner of a callable is the module whose `module_functions` lists it —
in a live case the projection carries the State 6 handoff's ownership, so
the table is built from authored sources; in a fixture it is the fixed
specification's. On Cabinet Kernel both bind all 507 notes alike.
"""

from __future__ import annotations

from typing import Any


def owners(spec: dict[str, Any]) -> dict[str, str]:
    table: dict[str, str] = {}
    module_functions = spec.get("module_functions") if isinstance(spec.get("module_functions"), dict) else {}
    for module, functions in module_functions.items():
        table.setdefault(str(module), str(module))
        for function in functions if isinstance(functions, list) else []:
            table.setdefault(str(function), str(module))
    return table


def bind(notes: list[dict[str, Any]], spec: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """``(notes by module, unbound notes)``. Every module of
    ``module_functions`` appears, with an empty list when it has no note."""
    table = owners(spec)
    module_functions = spec.get("module_functions") if isinstance(spec.get("module_functions"), dict) else {}
    by_module: dict[str, list[dict[str, Any]]] = {str(module): [] for module in module_functions}
    unbound: list[dict[str, Any]] = []
    for note in notes:
        scope = note["scope"]
        # `Class.method`: the method's owner is the class's (Q1, fact 10)
        module = table.get(scope) or table.get(scope.split(".", 1)[0])
        if module is None:
            unbound.append(note)
        else:
            by_module.setdefault(module, []).append(note)
    return by_module, unbound
