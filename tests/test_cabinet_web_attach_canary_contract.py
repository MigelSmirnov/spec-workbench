from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_source_attach_canary_v1.yaml"
ADAPTER = ROOT / "tools" / "cabinet_web_source_attach_adapter.py"
OLD_RUNTIME = ROOT / "tools" / "invoice_source_attach_runtime.py"
PROBE = ROOT / "tools" / "cabinet_web_source_attach_canary_probe.py"


def load():
    value = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def test_canary_starts_blocked_until_real_runtime_execution_passes():
    contract = load()
    assert contract["status"] == "execution_required"
    assert contract["interop_gate_before_execution"] == {
        "CW-MEDIA-001": "BLOCK",
        "CW-HASH-001": "BLOCK",
        "real_Cabinet_web_canary_allowed": False,
    }
    assert "Do not mark either finding PASS" in contract["after_successful_execution_rule"]


def test_canary_preserves_old_verified_attach_runtime_blob():
    contract = load()
    binding = contract["implementation"]["existing_verified_attach_runtime"]
    assert binding["path"] == "tools/invoice_source_attach_runtime.py"
    assert binding["must_remain_unmodified_by_this_canary"] is True
    assert git_blob_sha(OLD_RUNTIME) == "4517dd23f68a81a065823941d686fec4026be433"


def test_adapter_is_disposable_lowering_not_new_card_authority():
    contract = load()
    text = ADAPTER.read_text(encoding="utf-8")
    assert "identify_exact_media_type" in text
    assert '"expected_content_hash": None' in text
    assert '"content_hash": evidence.content_hash' in text
    assert "source.kind" not in text
    assert "file_ref" not in text
    assert "write_detected_media_type_into_confirmed_Card" in contract["forbidden_shortcuts"]
    assert "write_calculated_hash_into_confirmed_Card" in contract["forbidden_shortcuts"]


def test_canary_uses_content_reference_only_after_bytes_are_observed():
    contract = load()
    rules = set(contract["lowering_rules"])
    assert "derived_ContentReference_is_created_after_observing_bytes" in rules
    assert "durable_expected_source_hash_remains_null_when_Card_has_no_hash" in rules
    assert "durable_expected_source_media_type_remains_null_when_Card_has_no_exact_media" in rules
    assert "existing_attach_runtime_revalidates_bytes_before_effect" in rules


def test_runtime_probe_covers_success_replay_conflict_recovery_and_malformed_bytes():
    contract = load()
    probes = contract["required_runtime_probes"]
    assert set(probes) == {
        "WEB-ATTACH-001",
        "WEB-ATTACH-002",
        "WEB-ATTACH-003",
        "WEB-ATTACH-004",
    }
    text = PROBE.read_text(encoding="utf-8")
    assert "already_attached" in text
    assert "source_content_conflict" in text
    assert "recover_pending_publication" in text
    assert "accepted_card_content_hash" in text
