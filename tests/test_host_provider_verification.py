from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "experiments" / "cabinet-vault" / "generic_host_profile_candidate_v0.yaml"
PACKETS = ROOT / "experiments" / "cabinet-vault" / "generic_host_provider_verification_v0.yaml"
AUTHORITY = ROOT / "experiments" / "cabinet-vault" / "cabinet_authority_contract_v0.yaml"


def load(path: Path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def test_every_candidate_provider_has_exactly_one_verification_packet():
    profile = load(PROFILE)
    packets = load(PACKETS)["provider_packets"]
    assert set(packets) == set(profile["providers"])


def test_each_packet_covers_exactly_the_requirements_declared_by_its_provider():
    profile = load(PROFILE)
    packets = load(PACKETS)["provider_packets"]
    for provider_id, provider in profile["providers"].items():
        assert set(packets[provider_id]["covers_requirements"]) == set(provider["satisfies"])


def test_packet_runtime_dependencies_do_not_hide_profile_dependencies():
    profile = load(PROFILE)
    packets = load(PACKETS)["provider_packets"]
    for provider_id, provider in profile["providers"].items():
        assert set(packets[provider_id].get("runtime_dependencies", [])) == set(provider["runtime_dependencies"])


def test_authority_packet_uses_the_declared_authority_probe_vocabulary():
    authority = load(AUTHORITY)
    packets = load(PACKETS)["provider_packets"]
    assert {item["id"] for item in authority["verification_obligations"]} == {
        item["id"] for item in packets["authority_kernel"]["probes"]
    }


def test_concrete_provider_and_probe_runner_match_reviewed_fingerprints():
    packets = load(PACKETS)["provider_packets"]
    for provider_id in (
        "authority_kernel",
        "typed_schema_kernel",
        "postgres_record_kernel",
        "local_private_byte_vault",
        "protected_configuration_kernel",
    ):
        packet = packets[provider_id]
        implementation = packet["implementation"]
        probe_runner = packet["probe_runner"]
        assert git_blob_sha(ROOT / implementation["path"]) == implementation["blob_sha"]
        assert git_blob_sha(ROOT / probe_runner["path"]) == probe_runner["blob_sha"]
        assert probe_runner["successful_exit"] == 0
        assert probe_runner["blocking_exit"] == 2

    postgres_probe = packets["postgres_record_kernel"]["probe_runner"]
    assert postgres_probe["dsn_environment"] == "SPEC_WORKBENCH_TEST_POSTGRES_DSN"
    assert postgres_probe["no_dsn_status"] == "UNVERIFIED"


def test_all_candidate_provider_verification_states_are_evidence_backed_pass():
    profile = load(PROFILE)
    packets = load(PACKETS)["provider_packets"]

    assert {
        provider_id
        for provider_id, provider in profile["providers"].items()
        if provider["verification"]["status"] == "PASS"
    } == set(profile["providers"])
    assert not {
        provider_id
        for provider_id, provider in profile["providers"].items()
        if provider["verification"]["status"] == "UNVERIFIED"
    }

    for provider_id, provider in profile["providers"].items():
        probes = packets[provider_id]["probes"]
        assert probes
        assert {probe["status"] for probe in probes} == {"PASS"}
        assert provider["verification"]["required"] is True
        evidence = provider["verification"].get("evidence")
        assert isinstance(evidence, list) and evidence
        assert all((ROOT / item).is_file() for item in evidence)


def test_pass_probe_requires_recorded_executed_evidence():
    packets = load(PACKETS)["provider_packets"]
    for packet in packets.values():
        for probe in packet["probes"]:
            if probe["status"] != "PASS":
                continue
            assert probe.get("executed") is True
            evidence = probe.get("evidence")
            assert isinstance(evidence, list) and evidence
            assert all(isinstance(item, str) and item for item in evidence)


def test_provider_pass_requires_all_packet_probes_pass():
    profile = load(PROFILE)
    packets = load(PACKETS)["provider_packets"]
    for provider_id, provider in profile["providers"].items():
        if provider["verification"]["status"] != "PASS":
            continue
        assert all(probe["status"] == "PASS" for probe in packets[provider_id]["probes"])
        evidence = provider["verification"].get("evidence")
        assert isinstance(evidence, list) and evidence
        assert all((ROOT / item).is_file() for item in evidence)


def test_authority_candidate_does_not_claim_open_questions_closed():
    authority_packet = load(PACKETS)["provider_packets"]["authority_kernel"]
    note = authority_packet["representation_note"]
    assert "AUTH-OQ-001" in note
    assert "AUTH-OQ-002" in note
