#!/usr/bin/env python3
"""Disposable local-agent adapter from a Cabinet_web checkout to sync-v1 delivery.

The local box does not import Cabinet_web modules. This adapter verifies the
reviewed executable contract fingerprints, invokes Cabinet_web's own deterministic
validator as a subprocess, and builds the transport-independent delivery payload.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from cabinet_web_revision_accept_runtime import canonical_content_hash


EXPECTED_VALIDATOR_BLOB_SHA = "f2337466024fe64cda27f9170d42f9c1673466b5"
EXPECTED_SCHEMA_BLOB_SHA = "25042abe5d0387671d836f4e39601b1e5d63be2e"
EXPECTED_SERVICE_BLOB_SHA = "c7649351f4c5e833d7a49fd4738f47042b27e417"


class CabinetWebCheckoutContractError(RuntimeError):
    pass


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _require_fingerprint(path: Path, expected: str) -> None:
    if not path.is_file():
        raise CabinetWebCheckoutContractError(f"required Cabinet_web contract file missing: {path}")
    observed = git_blob_sha(path)
    if observed != expected:
        raise CabinetWebCheckoutContractError(
            f"Cabinet_web contract fingerprint drift for {path.name}: expected {expected}, observed {observed}"
        )


def verify_reviewed_contract(cabinet_web_root: str | Path) -> None:
    root = Path(cabinet_web_root).expanduser().resolve()
    _require_fingerprint(root / "tools" / "invoice_validation.py", EXPECTED_VALIDATOR_BLOB_SHA)
    _require_fingerprint(root / "schemas" / "invoice-card-v1.schema.json", EXPECTED_SCHEMA_BLOB_SHA)
    _require_fingerprint(root / "tools" / "invoice_service.py", EXPECTED_SERVICE_BLOB_SHA)


def validate_card_with_checkout(
    card: dict[str, Any],
    *,
    cabinet_web_root: str | Path,
) -> Sequence[Mapping[str, Any]]:
    root = Path(cabinet_web_root).expanduser().resolve()
    verify_reviewed_contract(root)
    validator = root / "tools" / "invoice_validation.py"

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        delete=False,
    ) as handle:
        json.dump(card, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary_path = Path(handle.name)

    try:
        completed = subprocess.run(
            [sys.executable, str(validator), str(temporary_path)],
            cwd=str(root),
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        temporary_path.unlink(missing_ok=True)

    if completed.returncode not in {0, 1}:
        raise CabinetWebCheckoutContractError(
            "Cabinet_web validator execution failed: " + completed.stderr.strip()
        )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise CabinetWebCheckoutContractError("Cabinet_web validator returned invalid JSON") from exc
    issues = report.get("issues")
    if not isinstance(issues, list):
        raise CabinetWebCheckoutContractError("Cabinet_web validator report has no issues list")
    return tuple(dict(item) for item in issues if isinstance(item, Mapping))


def _git_output(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise CabinetWebCheckoutContractError(
            "git command failed: " + completed.stderr.strip()
        )
    return completed.stdout.strip()


def build_delivery_from_checkout(
    *,
    cabinet_web_root: str | Path,
    invoice_id: str,
    delivery_id: str,
    base_backend_content_hash: str | None = None,
    emitted_at: str | None = None,
) -> dict[str, Any]:
    root = Path(cabinet_web_root).expanduser().resolve()
    verify_reviewed_contract(root)
    relative_path = Path("data") / "cards" / invoice_id / "card.json"
    card_path = root / relative_path
    if not card_path.is_file():
        raise CabinetWebCheckoutContractError(f"Invoice Card not found: {relative_path}")
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CabinetWebCheckoutContractError("Invoice Card cannot be read as JSON") from exc
    if not isinstance(card, dict):
        raise CabinetWebCheckoutContractError("Invoice Card must be a JSON object")
    if card.get("id") != invoice_id:
        raise CabinetWebCheckoutContractError("Invoice Card id does not match directory identity")
    if card.get("status") != "confirmed":
        raise CabinetWebCheckoutContractError("real-data canary requires a confirmed Invoice Card")

    issues = validate_card_with_checkout(card, cabinet_web_root=root)
    errors = [item for item in issues if item.get("severity", "error") == "error"]
    if errors:
        raise CabinetWebCheckoutContractError(
            "Invoice Card fails reviewed Cabinet_web validator: "
            + ", ".join(str(item.get("code", "unknown")) for item in errors)
        )

    commit_sha = _git_output(root, "log", "-1", "--format=%H", "--", relative_path.as_posix())
    if not commit_sha:
        raise CabinetWebCheckoutContractError("Invoice Card is not committed in Cabinet_web history")
    tracked = _git_output(root, "ls-files", "--error-unmatch", relative_path.as_posix())
    if tracked != relative_path.as_posix():
        raise CabinetWebCheckoutContractError("Invoice Card is not tracked at the expected repository path")

    timestamp = emitted_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "contract_version": "cabinet-web-sync-v1",
        "delivery_id": delivery_id,
        "emitted_at": timestamp,
        "producer_repository": "MigelSmirnov/Cabinet_web",
        "invoice_id": invoice_id,
        "card_contract_version": 1,
        "card_status": "confirmed",
        "card_content_hash": canonical_content_hash(card),
        "source_git_commit_sha": commit_sha,
        "card_repository_path": relative_path.as_posix(),
        "base_backend_content_hash": base_backend_content_hash,
        "card_document": card,
    }
