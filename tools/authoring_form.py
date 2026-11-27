"""The order every writing author form follows (tools/AUTHORING_FORMS.md).

A form records what it read, shows what it will write and where, applies only
what was shown, and hands back an address in the same working copy. What a
table or a decision must satisfy stays in the tool that owns it.
"""
import hashlib
import json
import shlex
from pathlib import Path


class StaleForm(ValueError):
    """The sources changed after the form or the preview was generated."""


def read_set(case: Path, paths) -> dict[str, str]:
    """Digest of every file the operation reads, keyed by its path in the case."""
    return {Path(path).relative_to(case).as_posix(): hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for path in sorted(paths)}


def revision(read: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(read, sort_keys=True).encode()).hexdigest()


def command(tool: str, *args) -> str:
    return " ".join(["python", f"tools/{tool}", *(shlex.quote(str(arg)) for arg in args)])


def changes(seen, current: dict[str, str]) -> list[str]:
    """Name each file that differs between what a form read and what is there now."""
    if not isinstance(seen, dict):
        return ["this form does not record what it read"]
    return [f"{name} {'changed' if name in seen and name in current else 'is new' if name in current else 'is gone'}"
            for name in sorted(seen.keys() | current.keys()) if seen.get(name) != current.get(name)]


def require_current(seen, current: dict[str, str], refresh: str) -> None:
    """Refuse to write from a form whose sources moved, saying which and how to continue."""
    moved = changes(seen, current)
    if moved:
        raise StaleForm(f"stale form: {'; '.join(moved)} after this form was generated, so its preview no longer "
                        f"describes what would be written. Nothing was written. Generate a fresh form, carry your "
                        f"answers over and preview again: {refresh}")


def will_write(case: Path, targets: dict[str, str]) -> str:
    """One line per file: where the change goes and what it is."""
    return "\n".join([f"Working copy: {case.resolve()}"]
                     + [f"Will write {name}: {what}" for name, what in targets.items()])


def return_address(case: Path, obj: str, reopen: str) -> dict[str, str]:
    """Where the author continues: the same working copy, the same object."""
    return {"working_copy": str(case.resolve()), "object": obj, "reopen": reopen}


def returning(address: dict[str, str]) -> str:
    return f"Return to {address['object']} in {address['working_copy']}: {address['reopen']}"
