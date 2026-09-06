#!/usr/bin/env python3
"""Execute and safely verify the real F260001 canary through the trusted bridge."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import subprocess
import uuid
from pathlib import Path
from typing import Any

from bounded_media_identification import identify_exact_media_type
from cabinet_web_checkout_sync_adapter import build_delivery_from_checkout
from cabinet_web_revision_accept_models import REVISION_NAMESPACE
from cabinet_web_revision_accept_runtime import revision_resource_id
from invoice_source_attach_models import INVOICE_NAMESPACE
from local_capability_bridge import (
    TARGET_INVOICE_ID,
    TARGET_SOURCE_ID,
    TrustedLocalCapabilityBridge,
)


PINNED_CARD_HASH = "sha256:e52e9d1fe3ff273b1510fd45d516daf576df4404320f75db4dfabc51c8f8a0cf"


class RealCanaryError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RealCanaryError("git_evidence_unavailable")
    return result.stdout.strip()


def _protected_environment(source: dict[str, str], cabinet_web_root: Path) -> dict[str, str]:
    env = dict(source)
    required = (
        "CABINET_BRIDGE_POSTGRES_DSN",
        "CABINET_BRIDGE_POSTGRES_SCHEMA",
        "CABINET_BRIDGE_VAULT_ROOT",
    )
    if any(not env.get(name) for name in required):
        raise RealCanaryError("protected_provider_configuration_not_ready")
    env["CABINET_BRIDGE_CABINET_WEB_ROOT"] = str(cabinet_web_root)
    env.setdefault("CABINET_BRIDGE_SYNC_CREDENTIAL_ID", f"sync-{secrets.token_hex(16)}")
    env.setdefault("CABINET_BRIDGE_SYNC_CREDENTIAL_MATERIAL", secrets.token_urlsafe(48))
    env.setdefault("CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_ID", f"local-{secrets.token_hex(16)}")
    env.setdefault("CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_MATERIAL", secrets.token_urlsafe(48))
    return env


def execute_real_canary(
    *,
    cabinet_web_root: str | Path,
    pdf_path: str | Path,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    web_root = Path(cabinet_web_root).expanduser().resolve()
    source_path = Path(pdf_path).expanduser().resolve()
    card_path = web_root / "data" / "cards" / TARGET_INVOICE_ID / "card.json"
    card_before = card_path.read_bytes()
    pdf_bytes = source_path.read_bytes()
    local_source_hash = hashlib.sha256(pdf_bytes).hexdigest()
    delivery_id = f"real-f260001-{uuid.uuid4().hex}"
    delivery = build_delivery_from_checkout(
        cabinet_web_root=web_root,
        invoice_id=TARGET_INVOICE_ID,
        delivery_id=delivery_id,
        base_backend_content_hash=None,
    )
    if delivery["card_content_hash"] != PINNED_CARD_HASH:
        raise RealCanaryError("pinned_card_hash_mismatch")
    if delivery["card_document"].get("source", {}).get("source_id") != TARGET_SOURCE_ID:
        raise RealCanaryError("pinned_source_identity_mismatch")

    protected_env = _protected_environment(
        dict(os.environ if environment is None else environment), web_root
    )
    bridge = TrustedLocalCapabilityBridge.from_environment(protected_env)
    bridge.start()
    if not bridge.readiness()["ready"]:
        raise RealCanaryError("bridge_not_ready")

    receipt = bridge.accept_revision(
        {
            "delivery": delivery,
            "interaction_id": f"real-f260001-accept-{uuid.uuid4().hex}",
        }
    )
    if receipt["outcome"] not in {"accepted", "already_accepted"}:
        return {
            "Cabinet_web main commit": _git(web_root, "rev-parse", "HEAD"),
            "spec-workbench commit": _git(Path(__file__).resolve().parents[3], "rev-parse", "HEAD"),
            "invoice_id": TARGET_INVOICE_ID,
            "Card repository path": f"data/cards/{TARGET_INVOICE_ID}/card.json",
            "Card content hash": delivery["card_content_hash"],
            "source_git_commit_sha": delivery["source_git_commit_sha"],
            "delivery_id": delivery_id,
            "revision receipt outcome": receipt["outcome"],
            "backend_current_content_hash": receipt["backend_current_content_hash"],
            "source_id": TARGET_SOURCE_ID,
            "local calculated source SHA-256": f"sha256:{local_source_hash}",
            "parser-validated media type": None,
            "source attachment result": "not_executed",
            "Card unchanged": card_path.read_bytes() == card_before,
            "acceptance audit present": False,
            "attachment audit present": False,
        }

    assert bridge._attach_adapter is not None
    media = identify_exact_media_type(
        pdf_bytes,
        validator=bridge._attach_adapter.content_validation,
    )
    attachment = bridge.attach_source(
        {
            "invoice_id": TARGET_INVOICE_ID,
            "source_id": TARGET_SOURCE_ID,
            "filename": source_path.name,
            "content_base64": base64.b64encode(pdf_bytes).decode("ascii"),
            "interaction_id": f"real-f260001-attach-{uuid.uuid4().hex}",
        }
    )

    assert bridge._records is not None
    current = bridge._records.read_record(INVOICE_NAMESPACE, TARGET_INVOICE_ID)
    revision = bridge._records.read_record(
        REVISION_NAMESPACE,
        revision_resource_id(TARGET_INVOICE_ID, PINNED_CARD_HASH),
    )
    if current is None or revision is None:
        raise RealCanaryError("accepted_state_verification_failed")
    source_state = current.payload["source_states"][TARGET_SOURCE_ID]
    expected_source = current.payload["expected_sources"][TARGET_SOURCE_ID]
    if current.payload.get("current_content_hash") != PINNED_CARD_HASH:
        raise RealCanaryError("backend_current_hash_changed")
    if current.payload.get("accepted_card_document") != delivery["card_document"]:
        raise RealCanaryError("accepted_card_document_changed")
    if revision.payload.get("card_document") != delivery["card_document"]:
        raise RealCanaryError("immutable_revision_document_changed")
    if source_state.get("status") != "available":
        raise RealCanaryError("source_not_available")
    if source_state.get("content_hash") != local_source_hash:
        raise RealCanaryError("source_hash_verification_failed")
    if source_state.get("media_type") != media.media_type:
        raise RealCanaryError("source_media_verification_failed")
    if expected_source.get("expected_hash") is not None:
        raise RealCanaryError("upstream_expected_hash_was_invented")
    if expected_source.get("media_type") is not None:
        raise RealCanaryError("upstream_expected_media_was_invented")

    audits = bridge._records.read_audit()
    acceptance_audit = any(
        event.event_type == "cabinet_web.revision.accept"
        and event.subject == TARGET_INVOICE_ID
        for event in audits
    )
    attachment_audit = any(
        event.event_type == "invoice.source.attach"
        and event.subject == TARGET_INVOICE_ID
        for event in audits
    )
    item = attachment["items"][0]
    report = {
        "Cabinet_web main commit": _git(web_root, "rev-parse", "HEAD"),
        "spec-workbench commit": _git(Path(__file__).resolve().parents[3], "rev-parse", "HEAD"),
        "invoice_id": TARGET_INVOICE_ID,
        "Card repository path": delivery["card_repository_path"],
        "Card content hash": delivery["card_content_hash"],
        "source_git_commit_sha": delivery["source_git_commit_sha"],
        "delivery_id": delivery_id,
        "revision receipt outcome": receipt["outcome"],
        "backend_current_content_hash": current.payload["current_content_hash"],
        "source_id": TARGET_SOURCE_ID,
        "local calculated source SHA-256": f"sha256:{local_source_hash}",
        "parser-validated media type": media.media_type,
        "source attachment result": item["result"],
        "Card unchanged": card_path.read_bytes() == card_before,
        "acceptance audit present": acceptance_audit,
        "attachment audit present": attachment_audit,
    }
    forbidden = tuple(
        value
        for key, value in protected_env.items()
        if key.startswith("CABINET_BRIDGE_") and value
    ) + (str(source_path), str(source_path.parent))
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True)
    if any(value in rendered for value in forbidden):
        raise RealCanaryError("safe_report_disclosure_violation")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the real F260001 bridge canary")
    parser.add_argument("--cabinet-web-root", required=True)
    parser.add_argument("--pdf", required=True)
    args = parser.parse_args()
    try:
        report = execute_real_canary(
            cabinet_web_root=args.cabinet_web_root,
            pdf_path=args.pdf,
        )
    except Exception as exc:
        print(json.dumps({"status": "blocked", "safe_error_code": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False))
    return 0 if report["source attachment result"] in {"attached", "already_attached"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
