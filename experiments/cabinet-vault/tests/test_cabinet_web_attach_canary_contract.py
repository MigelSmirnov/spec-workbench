from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_source_attach_canary_v1.yaml"
ADAPTER = ROOT / "experiments" / "cabinet-vault" / "tools" / "cabinet_web_source_attach_adapter.py"
OLD_RUNTIME = ROOT / "experiments" / "cabinet-vault" / "tools" / "invoice_source_attach_runtime.py"
PROBE = ROOT / "experiments" / "cabinet-vault" / "tools" / "cabinet_web_source_attach_canary_probe.py"
EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md"


def load():
    value = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def test_canary_is_verified_by_exact_github_runtime_evidence():
    contract = load()
    verification = contract["verification"]

    assert contract["status"] == "verified_execution_case"
    assert verification["status"] == "PASS"
    assert verification["workflow"] == {
        "name": "Cabinet Web attach canary",
        "run_id": 32507028221,
        "run_number": 2,
        "head_branch": "agent/cabinet-web-attach-canary",
        "head_sha": "ca542b9b3dd60112f8cdd20c532f8a6f02c17d64",
        "conclusion": "success",
    }
    assert verification["artifact"] == {
        "artifact_id": 9455627318,
        "name": "cabinet-web-source-attach-canary",
        "digest": "sha256:1f7bcc1cabd2e8d4f58cb8310b915fc47944385d6f53d20d27e81a726b11c33e",
    }
    assert set(verification["probes"].values()) == {"PASS"}
    assert set(verification["probes"]) == {
        "WEB-ATTACH-001",
        "WEB-ATTACH-002",
        "WEB-ATTACH-003",
        "WEB-ATTACH-004",
    }
    assert EVIDENCE.is_file()


def test_verified_canary_opens_interop_but_does_not_claim_real_user_data_execution():
    gate = load()["interop_gate_after_execution"]
    assert gate == {
        "CW-MEDIA-001": "PASS",
        "CW-HASH-001": "PASS",
        "cabinet_web_interop_gate": "pass",
        "real_Cabinet_web_data_canary": "allowed_not_executed",
        "real_user_data_canary_executed": False,
    }


def test_canary_preserves_old_verified_attach_runtime_blob():
    contract = load()
    binding = contract["implementation"]["existing_verified_attach_runtime"]
    assert binding["path"] == "experiments/cabinet-vault/tools/invoice_source_attach_runtime.py"
    assert binding["must_remain_unmodified_by_this_canary"] is True
    assert binding["blob_sha"] == "4517dd23f68a81a065823941d686fec4026be433"
    assert git_blob_sha(OLD_RUNTIME) == binding["blob_sha"]


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
    rules = set(load()["lowering_rules"])
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
