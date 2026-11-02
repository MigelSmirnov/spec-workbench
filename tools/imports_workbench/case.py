"""What the imports closure reads: the specification State 8 will materialise.

The symbol catalog (who owns and exports what, contracts, models) is the
projector's own view of the case (spec_projection_workbench.projected_spec), so
the closure judges exactly the specification the Factory will receive. Notes
are the authored State 7 notes; State 3 Knows comes from 30_modules.md.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from imports_workbench.model import MODELS_MODULE, TARGET_FILE, ImportsError

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class Note:
    scope: str            # the authored prefix: function, Class.method, symbol or module
    text: str
    note_class: str = ""
    path: str = ""
    line: int = 0


@dataclass
class Scope:
    id: str                       # <module>.<contract> or <module>
    module: str
    contract: str | None          # None for the module scope
    signature: str = ""
    notes: list[tuple[str, Note]] = field(default_factory=list)   # (address, note)

    @property
    def basis_sha256(self) -> str:
        payload = {"contract": self.contract, "signature": self.signature,
                   "notes": [[note.note_class, note.text] for _, note in self.notes]}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    @property
    def text(self) -> str:
        return "\n".join(note.text for _, note in self.notes)


@dataclass
class Case:
    project_root: str
    modules: list[str]                                  # State 3 order
    module_functions: dict[str, list[str]]              # owned symbols
    exports: dict[str, list[str]]                       # imports.internal: what others may import
    contracts: dict[str, str]
    models: dict[str, dict[str, Any]]
    notes: list[Note]
    knows: dict[str, list[str]] = field(default_factory=dict)
    deterministic: set[str] = field(default_factory=set)  # contracts an emitter lowers from IR
    module_internal: dict[str, Any] = field(default_factory=dict)  # current, for drift
    factory_target: str | None = None

    # -- ownership ---------------------------------------------------------
    def owner(self, symbol: str) -> str | None:
        for module, symbols in self.module_functions.items():
            if symbol in symbols or symbol.split(".", 1)[0] in symbols:
                return module
        return None

    def providers(self, symbol: str) -> list[str]:
        return [module for module, symbols in self.exports.items() if symbol in symbols]

    def catalog(self) -> dict[str, list[str]]:
        """Exported symbol -> modules that export it."""
        found: dict[str, list[str]] = {}
        for module, symbols in self.exports.items():
            for symbol in symbols:
                found.setdefault(symbol, []).append(module)
        return found

    # -- scopes ------------------------------------------------------------
    def module_contracts(self, module: str) -> list[str]:
        return [name for name in self.contracts if self.owner(name) == module]

    def out_of_scope(self) -> dict[str, str]:
        """Modules the closure does not judge, with the reason (shown, never silent)."""
        reasons: dict[str, str] = {}
        for module in self.modules:
            if module == MODELS_MODULE:
                reasons[module] = "the models module is emitted deterministically and imports nothing of the project"
                continue
            contracts = self.module_contracts(module)
            if not any(name not in self.deterministic for name in contracts):
                reasons[module] = ("every contract is lowered by an emitter from closed IR" if contracts
                                   else "the module owns no contract: an emitter writes it")
        return reasons

    def scopes(self) -> dict[str, Scope]:
        skipped = self.out_of_scope()
        result: dict[str, Scope] = {}
        for module in self.modules:
            if module in skipped:
                continue
            result[module] = Scope(id=module, module=module, contract=None)
            for name in self.module_contracts(module):
                if name not in self.deterministic:
                    result[f"{module}.{name}"] = Scope(id=f"{module}.{name}", module=module, contract=name,
                                                       signature=self.contracts[name])
        for note in self.notes:
            scope = self._note_scope(note, result)
            if scope is not None:
                scope.notes.append((f"note:{scope.id}#{len(scope.notes) + 1}", note))
        return result

    def _note_scope(self, note: Note, scopes: dict[str, Scope]) -> Scope | None:
        if note.scope in self.contracts:
            module = self.owner(note.scope)
            return scopes.get(f"{module}.{note.scope}") if module else None
        if note.scope in scopes:
            return scopes[note.scope]
        module = self.owner(note.scope)
        return scopes.get(module) if module else None


_MODULE_SECTION = re.compile(r"^## `([A-Za-z_][A-Za-z0-9_]*)`\s*$", re.MULTILINE)
_KNOWS_SECTION = re.compile(r"^### Knows\s*$(.*?)(?=^### |\Z)", re.MULTILINE | re.DOTALL)
# "**Delegates to**: ..." and "**Delegates to:** ..." alike
_DELEGATES = re.compile(r"^[-*\s]*\**delegates to\s*(?::\**|\**\s*:)\s*(.*?)\s*$", re.MULTILINE | re.IGNORECASE)
_PARENTHESIS = re.compile(r"\([^()]*\)")
_LEAD_NAME = re.compile(r"\s*`(?:module:)?([A-Za-z_][A-Za-z0-9_]*)`")
_LEAD_SEPARATOR = re.compile(r"\s*(?:,|\band\b)")
_ITEM = re.compile(r"(?:^|\n)\s*[-*]\s+")


def leading_names(text: str) -> list[str]:
    """The backticked names a Knows list leads with: `a`, `b` (why) and `c`.

    Parenthetical comments are skipped; the list ends at the first word that is
    not a name. A backticked name later in prose ("except `x`", "the `now`
    `runs` passes") is not a collaborator. Each bullet item is a list of its own.
    """
    found: list[str] = []
    for item in _ITEM.split(_PARENTHESIS.sub(" ", text)):
        position = 0
        while True:
            name = _LEAD_NAME.match(item, position)
            if name is None:
                break
            found.append(name.group(1))
            separator = _LEAD_SEPARATOR.match(item, name.end())
            if separator is None:
                break
            position = separator.end()
    return found


def knows(project: Path, modules: set[str]) -> dict[str, list[str]]:
    """State 3 collaborators of each module, read from the lists Knows and
    "delegates to" lead with (IMPORTS_WORKBENCH.md §14). Prose is not parsed:
    "every module except `x`" names no collaborator here."""
    path = project / "30_modules.md"
    if not path.is_file():
        return {}
    parts = _MODULE_SECTION.split(path.read_text(encoding="utf-8"))
    result: dict[str, list[str]] = {}
    for position in range(1, len(parts), 2):
        module, body = parts[position], parts[position + 1]
        section = _KNOWS_SECTION.search(body)
        named = leading_names(section.group(1)) if section else []
        for delegates in _DELEGATES.findall(body):
            named += leading_names(delegates)
        named = sorted({name for name in named if name in modules and name != module})
        if named:
            result[module] = named
    return result


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportsError(f"cannot read {path.name}: {exc}") from exc


def factory_target(project: Path) -> str | None:
    """The Factory project the case targets. A target file that cannot be read is
    an error, never "no target": that would turn a block into not_applicable
    (obligation_workbench.factory_parity treats it as absent, so it is not reused)."""
    path = project / TARGET_FILE
    if not path.is_file():
        return None
    payload = _read_json(path)
    value = payload.get("factory_project") if isinstance(payload, dict) else None
    if not isinstance(value, str) or not value:
        raise ImportsError(f"{TARGET_FILE} must be an object with a non-empty factory_project")
    return value


def load(project: Path) -> Case:
    """The case as State 8 will project it."""
    from notes_workbench import gate as notes_gate
    from notes_workbench.language import _iter_authored_notes
    from spec_projection_workbench import service as projection
    from spec_projection_workbench.model import SpecProjectionError

    project = project.resolve()
    try:
        spec = projection.projected_spec(project, imports=False)
    except SpecProjectionError as exc:
        raise ImportsError(f"the projector cannot build the specification: {exc}") from exc
    imports = spec.get("imports") or {}
    module_functions = {str(k): [str(s) for s in v] for k, v in (spec.get("module_functions") or {}).items()
                        if isinstance(v, list)}
    modules = [str(m) for m in spec.get("module_order") or module_functions]
    modules += [m for m in module_functions if m not in modules]
    exports = {str(k): [str(s) for s in v] for k, v in (imports.get("internal") or {}).items() if isinstance(v, list)}
    notes = [Note(scope=item["scope"], text=item["text"], note_class=item.get("class") or "",
                  path=item.get("path") or "", line=int(item.get("line") or 0))
             for item in _iter_authored_notes(project)]
    return Case(
        project_root=project.name,
        modules=modules,
        module_functions=module_functions,
        exports=exports,
        contracts={str(k): str(v) for k, v in (spec.get("contracts") or {}).items() if isinstance(v, str)},
        models={str(k): v for k, v in (spec.get("models") or {}).items() if isinstance(v, dict)},
        notes=notes,
        knows=knows(project, set(modules)),
        deterministic=set(notes_gate._load_deterministic_callable_scopes(project)),
        module_internal=imports.get("module_internal") or {},
        factory_target=factory_target(project),
    )
