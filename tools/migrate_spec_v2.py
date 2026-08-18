#!/usr/bin/env python3
"""Perform the mechanical SPEC_STANDARD v1-to-v2 language-envelope migration.

This tool intentionally owns only the two semantics-free envelope changes that
can be proven mechanical for an already assembled spec:

* add top-level ``standard_version: 2`` when it is absent;
* remove the legacy top-level ``adapters`` section only when it is exactly empty.

It never invents backend IR, rewrites notes, changes routing, or converts storage
engines. Non-empty adapters and unknown language versions fail closed and require
an explicit semantic migration instead.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any

SUPPORTED_VERSION = 2
ADAPTER_LINE = '  "adapters": {},\n'
VERSION_LINE = '  "standard_version": 2,\n'


class MigrationError(ValueError):
    """The specification cannot be migrated mechanically without semantic risk."""


def _load(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MigrationError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise MigrationError("global_spec.json must contain a top-level object")
    return payload


def migrate_text(text: str) -> str:
    payload = _load(text)
    version = payload.get("standard_version")
    if version not in (None, SUPPORTED_VERSION):
        raise MigrationError(
            f"unsupported existing standard_version {version!r}; expected absent or {SUPPORTED_VERSION}"
        )

    if "adapters" in payload and payload["adapters"] != {}:
        raise MigrationError(
            "legacy adapters is non-empty; call-site semantics require explicit migration"
        )

    migrated = text
    if version is None:
        if not migrated.startswith("{\n"):
            raise MigrationError(
                "mechanical migration requires canonical pretty-printed object opening '{\\n'"
            )
        migrated = "{\n" + VERSION_LINE + migrated[2:]

    if "adapters" in payload:
        occurrences = migrated.count(ADAPTER_LINE)
        if occurrences != 1:
            raise MigrationError(
                "empty top-level adapters must appear exactly once in canonical line form"
            )
        migrated = migrated.replace(ADAPTER_LINE, "", 1)

    result = _load(migrated)
    if result.get("standard_version") != SUPPORTED_VERSION:
        raise MigrationError("migration failed to establish standard_version=2")
    if "adapters" in result:
        raise MigrationError("migration failed to remove legacy adapters")

    original_without_envelope = dict(payload)
    original_without_envelope.pop("standard_version", None)
    original_without_envelope.pop("adapters", None)
    result_without_envelope = dict(result)
    result_without_envelope.pop("standard_version", None)
    result_without_envelope.pop("adapters", None)
    if result_without_envelope != original_without_envelope:
        raise MigrationError("migration changed specification semantics outside the language envelope")
    return migrated


def migrate_file(path: Path, *, apply: bool) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    migrated = migrate_text(original)
    changed = migrated != original
    diff = "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        migrated.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    ))
    if apply and changed:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(migrated, encoding="utf-8")
        temporary.replace(path)
    return {
        "path": str(path),
        "standard_version": SUPPORTED_VERSION,
        "changed": changed,
        "applied": bool(apply and changed),
        "diff": diff,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.spec.is_file():
        print(f"migrate_spec_v2: error: file not found: {args.spec}", file=sys.stderr)
        return 2
    try:
        report = migrate_file(args.spec, apply=args.apply)
    except (OSError, MigrationError) as exc:
        print(f"migrate_spec_v2: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(report["diff"] or "already migrated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
