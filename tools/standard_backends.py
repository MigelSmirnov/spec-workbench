"""Shared deterministic-backend lineage adapters.

These adapters are platform tooling: they recognize backend IR kinds that are
part of SPEC_STANDARD and expose their closed lowering evidence to Notes and
Stage 8.1 review. Product branches provide only closure/spec data; they do not
ship executable Workbench modules for standard backends.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModuleContracts:
    """A fixed set of module-level callables an emitter writes into the wired module.

    ``required`` functions are always emitted; an ``optional`` one is emitted
    exactly when the case declares its contract (``60_contracts.json``). When
    the backend IR object ``errors_key`` names the wired module as its
    ``module``, the emitter also defines the exception classes its
    ``error_members`` name there. The function names mirror the contract tables
    of the Factory emitter ``factory_tool``; admission FA021 holds them equal to
    the target Factory, read without running Factory code.
    """

    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    errors_key: str | None = None
    error_members: tuple[str, ...] = ()
    factory_tool: str | None = None
    factory_required_constant: str = "REQUIRED_CONTRACTS"
    factory_optional_constant: str = "OPTIONAL_CONTRACTS"

    def well_formed(self, backend: dict[str, Any]) -> bool:
        """The IR names its module and, when declared, distinct error classes.

        Only what ownership is computed from is checked here; the Factory
        validator remains the judge of the rest of the closed form.
        """
        wiring = backend.get("wiring")
        if not isinstance(wiring, dict) or not _name(wiring.get("module")):
            return False
        if self.errors_key is None:
            return True
        errors = backend.get(self.errors_key)
        if not isinstance(errors, dict) or not _name(errors.get("module")):
            return False
        members = [errors.get(member) for member in self.error_members]
        return all(_name(member) for member in members) and len(set(members)) == len(members)

    def owned(self, backend: dict[str, Any], declared: set[str]) -> set[str]:
        result = set(self.required) | {name for name in self.optional if name in declared}
        if self.errors_key is not None:
            errors = backend[self.errors_key]
            if errors["module"] == backend["wiring"]["module"]:
                result |= {errors[member] for member in self.error_members}
        return result


def _name(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _declared_contracts(project: Path) -> set[str]:
    path = project / "60_contracts.json"
    try:
        contracts = json.loads(path.read_text(encoding="utf-8")).get("contracts")
    except (OSError, AttributeError, ValueError):
        return set()
    return set(contracts) if isinstance(contracts, dict) else set()


@dataclass(frozen=True)
class StandardBackend:
    id: str
    closure_file: str
    closure_schema: str
    rule_key: str
    scope_mapping_path: tuple[str, ...] | None = None
    concrete_methods: tuple[str, ...] = ()
    function_wiring_key: str | None = None
    function_wiring_keys: tuple[str, ...] = ()
    module_contracts: ModuleContracts | None = None

    def _load(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def authored_backend(self, project: Path) -> dict[str, Any] | None:
        """Return the backend IR of a closed closure file, whatever is assembled."""
        closure_path = project / self.closure_file
        if not closure_path.is_file():
            return None
        try:
            closure = self._load(closure_path)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(closure, dict):
            return None
        backend = closure.get("backend_ir")
        if (
            closure.get("schema_version") != self.closure_schema
            or closure.get("status") != "closed"
            or not isinstance(backend, dict)
        ):
            return None
        if self.module_contracts is not None and (
            backend.get("kind") != self.rule_key
            or not self.module_contracts.well_formed(backend)
        ):
            return None
        return backend

    def closed_backend(self, project: Path) -> dict[str, Any] | None:
        """Return the backend IR only while nothing assembled disagrees with it.

        Before the first assembly there is no ``global_spec.json`` to disagree:
        the closed closure is the only statement of the backend, and the spec
        projection carries it into ``rules`` verbatim. Once a spec exists, any
        difference is projection drift and the backend fails closed.
        """
        backend = self.authored_backend(project)
        if backend is None:
            return None
        spec_path = project / "global_spec.json"
        if not spec_path.is_file():
            return backend
        try:
            spec = self._load(spec_path)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(spec, dict):
            return None
        rules = spec.get("rules")
        assembled = rules.get(self.rule_key) if isinstance(rules, dict) else None
        return backend if backend == assembled else None

    def _mapping(self, backend: dict[str, Any]) -> dict[str, Any] | None:
        if self.scope_mapping_path is None:
            return None
        current: Any = backend
        for part in self.scope_mapping_path:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current if isinstance(current, dict) else None

    def structured_addresses(self, project: Path) -> set[str]:
        backend = self.closed_backend(project)
        if backend is None:
            return set()
        root = f"rules.{self.rule_key}"
        result = {root}
        mapping = self._mapping(backend)
        if mapping is not None and self.scope_mapping_path is not None:
            path = ".".join(self.scope_mapping_path)
            result.add(f"{root}.{path}")
            result |= {f"{root}.{path}.{name}" for name in mapping}
        return result

    def deterministic_method_scopes(self, project: Path) -> set[str]:
        backend = self.closed_backend(project)
        if backend is None:
            return set()
        mapping = self._mapping(backend)
        if mapping is not None:
            return set(mapping)
        if self.module_contracts is not None:
            return self.module_contracts.owned(backend, _declared_contracts(project))
        wiring = backend.get("wiring")
        if self.function_wiring_keys and isinstance(wiring, dict):
            functions = {
                wiring[key]
                for key in self.function_wiring_keys
                if isinstance(wiring.get(key), str) and wiring[key]
            }
            if functions:
                return functions
        if self.function_wiring_key is not None and isinstance(wiring, dict):
            # a backend wired to one module-level operation owns exactly it
            function = wiring.get(self.function_wiring_key)
            if isinstance(function, str) and function:
                return {function}
        if self.concrete_methods:
            concrete = wiring.get("concrete_class") if isinstance(wiring, dict) else None
            if not isinstance(concrete, str) or not concrete:
                return set()
            return {f"{concrete}.{method}" for method in self.concrete_methods}
        return set()

    def module_slice(self, project: Path, module: str) -> dict[str, Any] | None:
        backend = self.closed_backend(project)
        if backend is None:
            return None
        wiring = backend.get("wiring")
        if not isinstance(wiring, dict) or wiring.get("module") != module:
            return None
        return {
            "enabled": True,
            "backend_ir": backend,
            "deterministic_method_scopes": sorted(self.deterministic_method_scopes(project)),
        }


STANDARD_BACKENDS = (
    StandardBackend(
        id="holded_transport",
        closure_file="70_holded_transport_closure.json",
        closure_schema="spec_workbench_holded_transport_backend_closure.v1",
        rule_key="holded_transport_backend",
        concrete_methods=("__init__", "create_purchase", "list_purchases", "get_purchase"),
    ),
    StandardBackend(
        id="canonical_digest",
        closure_file="70_canonical_digest_closure.json",
        closure_schema="spec_workbench_canonical_digest_backend_closure.v1",
        rule_key="canonical_digest_backend",
        scope_mapping_path=("recipes",),
    ),
    StandardBackend(
        id="system_clock",
        closure_file="70_system_clock_closure.json",
        closure_schema="spec_workbench_system_clock_backend_closure.v1",
        rule_key="system_clock_backend",
        concrete_methods=("__init__", "now"),
        function_wiring_key="function",
        function_wiring_keys=("wall_clock_function", "elapsed_clock_function"),
    ),
    # typed constants only: the module owns no callable, so no method scope is deterministic
    StandardBackend(
        id="data_provider",
        closure_file="70_data_provider_closure.json",
        closure_schema="spec_workbench_data_provider_backend_closure.v1",
        rule_key="data_provider_backend",
    ),
    StandardBackend(
        id="keyed_file_spool",
        closure_file="70_keyed_file_spool_closure.json",
        closure_schema="spec_workbench_keyed_file_spool_backend_closure.v1",
        rule_key="keyed_file_spool_backend",
        module_contracts=ModuleContracts(
            required=(
                "spool_entry_name",
                "spool_attempt_prefix",
                "publish_spool_entry",
                "read_spool_entry",
                "discard_spool_attempt",
                "remove_spool_group",
                "remove_spool_temporaries",
            ),
            optional=("spool_group_bytes", "list_spool_groups"),
            errors_key="errors",
            error_members=("refused", "internal"),
            factory_tool="tools/generate_keyed_file_spool_draft.py",
        ),
    ),
)


def standard_backends(*, exclude_ids: set[str] | None = None) -> list[StandardBackend]:
    excluded = exclude_ids or set()
    return [backend for backend in STANDARD_BACKENDS if backend.id not in excluded]
