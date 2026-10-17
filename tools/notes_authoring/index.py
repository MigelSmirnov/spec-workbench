"""The declared surface a writing agent and lint L2–L4 look things up in.

Built from one specification — the in-memory projection of the authored
sources in a live case (decision Q1), or a fixed `global_spec.json` in a
regression fixture. Nothing here decides legality of an address: that is the
Factory's resolver (M1, `notes_workbench.factory_addresses`).

- M2 `homes(value)`: the addresses whose declared value equals a literal.
- M4 `absence(terms)`: where a term occurs as a key or value, and the sha256
  of each namespace looked through, so "no home" is a checked statement.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterator

# Cells of a backend IR that name the IR, not a value of the product.
_STRUCTURAL_KEYS = frozenset({"role", "schema_version", "kind", "backend", "wiring"})
_CONTRACT_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def normalize(value: Any) -> str | None:
    """The comparable text of a declared scalar or of a literal in a note."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def _leaves(value: Any, path: str) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and key not in _STRUCTURAL_KEYS:
                yield from _leaves(item, f"{path}.{key}")
    elif isinstance(value, list):
        for item in value:
            yield from _leaves(item, path)
    else:
        yield path, value


@dataclass
class SpecIndex:
    enums: dict[str, tuple[str, ...]] = field(default_factory=dict)
    fields: dict[str, set[str]] = field(default_factory=dict)  # model -> field names
    contracts: set[str] = field(default_factory=set)            # callable names, methods split too
    constants: set[str] = field(default_factory=set)            # data provider constant names
    values: dict[str, set[str]] = field(default_factory=dict)   # normalized literal -> homes
    namespaces: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(cls, spec: dict[str, Any]) -> "SpecIndex":
        index = cls()
        models = spec.get("models") if isinstance(spec.get("models"), dict) else {}
        rules = spec.get("rules") if isinstance(spec.get("rules"), dict) else {}
        config = spec.get("config") if isinstance(spec.get("config"), dict) else {}
        contracts = spec.get("contracts") if isinstance(spec.get("contracts"), dict) else {}
        index.namespaces = {"models": models, "rules": rules, "config": config, "contracts": contracts}
        for name, model in models.items():
            if not isinstance(model, dict):
                continue
            if model.get("kind") == "enum" and isinstance(model.get("values"), list):
                members = tuple(str(v) for v in model["values"] if isinstance(v, str))
                index.enums[name] = members
                for member in members:
                    index.values.setdefault(member, set()).add(f"= models.{name}")
            if isinstance(model.get("fields"), dict):
                index.fields[name] = set(model["fields"])
        for name in contracts:
            index.contracts.update(_CONTRACT_NAME_RE.findall(str(name)))
        provider = rules.get("data_provider_backend")
        provider_constants = provider.get("constants") if isinstance(provider, dict) else None
        if isinstance(provider_constants, dict):
            for name, row in provider_constants.items():
                index.constants.add(name)
                value = row.get("value") if isinstance(row, dict) else row
                # a v2 table's enum column holds members, whose home is the
                # enumeration (= models.X), not the table that cites them
                row_model = models.get(row.get("row_model")) if isinstance(row, dict) else None
                row_fields = row_model.get("fields") if isinstance(row_model, dict) else None
                if isinstance(row_fields, dict) and isinstance(value, list):
                    value = [
                        {field: cell for field, cell in record.items()
                         if not (isinstance(models.get(row_fields.get(field)), dict)
                                 and models[row_fields[field]].get("kind") == "enum")}
                        for record in value if isinstance(record, dict)
                    ]
                for _, leaf in _leaves(value, ""):
                    text = normalize(leaf)
                    if text is not None:
                        index.values.setdefault(text, set()).add(f"the imported {name} constant")
        for root, block in (("rules", rules), ("config", config)):
            for key, value in block.items():
                if key in _STRUCTURAL_KEYS or (root == "rules" and key == "data_provider_backend"):
                    continue
                for path, leaf in _leaves(value, f"{root}.{key}"):
                    text = normalize(leaf)
                    if text is not None:
                        index.values.setdefault(text, set()).add(path)
        return index

    # ── names a note may write as words (contract §3) ─────────────────────

    def is_name(self, word: str) -> bool:
        return (
            word in self.contracts
            or word in self.constants
            or word in self.fields
            or word in self.enums
            or any(word in names for names in self.fields.values())
        )

    def names(self) -> frozenset[str]:
        found = set(self.contracts) | self.constants | set(self.fields) | set(self.enums)
        for names in self.fields.values():
            found |= names
        for members in self.enums.values():
            found |= set(members)
        return frozenset(found)

    def field_names(self) -> frozenset[str]:
        return frozenset(name for names in self.fields.values() for name in names)

    def fields_of_one_model(self, items: tuple[str, ...]) -> str | None:
        wanted = set(items)
        for model, names in self.fields.items():
            if wanted <= names:
                return model
        return None

    # ── M2 ─────────────────────────────────────────────────────────────────

    def homes(self, literal: str, *, reaching_code: bool = False) -> list[str]:
        """Addresses whose declared value equals ``literal``. With
        ``reaching_code``, only homes whose value reaches a generated module
        (§15.3.1: an enumeration, a provider constant, a `config` setting);
        a leaf of a deterministic backend's IR reaches the backend, not the
        model, so a literal equal to it is no leak (§15.9)."""
        text = normalize(literal)
        if text is None:
            return []
        found = set(self.values.get(text, set()))
        if re.fullmatch(r"-?\d+\.0+", text):
            found |= self.values.get(text.split(".")[0], set())
        if reaching_code:
            found = {home for home in found if not home.startswith("rules.")}
        return sorted(found)

    # ── M4 ─────────────────────────────────────────────────────────────────

    def absence(self, terms: list[str]) -> dict[str, Any]:
        """Where each term occurs as a key or a value (case-insensitive
        substring), and the sha256 of every namespace looked through."""
        hits: dict[str, list[str]] = {}
        for term in terms:
            needle = term.lower()
            found: list[str] = []
            for root, block in self.namespaces.items():
                for path, value in _walk(block, root):
                    key = path.rsplit(".", 1)[-1]
                    if needle in key.lower() or (isinstance(value, str) and needle in value.lower()):
                        found.append(path)
            hits[term] = sorted(set(found))
        return {
            "terms": hits,
            "namespaces": {
                root: hashlib.sha256(_canonical(block).encode("utf-8")).hexdigest()
                for root, block in self.namespaces.items()
            },
        }


def _walk(value: Any, path: str) -> Iterator[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield from _walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item, path)
