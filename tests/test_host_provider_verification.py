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
        declared = set(provider["runtime_dependencies"])
        packet_dependencies = set(packets[provider_id].get("runtime_dependencies", []))
        assert packet_dependencies == declared


def test_authority_packet_uses_the_declared_authority_probe_vocabulary():
    authority = load(AUTHORITY)
    packets = load(PACKETS)["provider_packets"]

    contract_probes = {item["id"] for item in authority["verification_obligations"]}
    packet_probes = {item["id"] for item in packets["authority_kernel"]["probes"]}

    assert packet_probes == contract_probes


def test_postgres_provider_and_probe_runner_match_reviewed_fingerprints():
    packet = load(PACKETS)["provider_packets"]["postgres_record_kernel"]

    implementation = packet["implementation"]
    probe_runner = packet["probe_runner"]

    implementation_path = ROOT / implementation["path"]
    probe_path = ROOT / probe_runner["path"]

    assert git_blob_sha(implementation_path) == implementation["blob_sha"]
    assert git_blob_sha(probe_path) == probe_runner["blob_sha"]
    assert probe_runner["dsn_environment"] == "SPEC_WORKBENCH_TEST_POSTGRES_DSN"
    assert probe_runner["no_dsn_status"] == "UNVERIFIED"
    assert probe_runner["successful_exit"] == 0
    assert probe_runner["blocking_exit"] == 2


def test_candidate_packets_and_profile_remain_unverified_without_executed_evidence():
    profile = load(PROFILE)
    packets = load(PACKETS)["provider_packets"]

    for provider_id, packet in packets.items():
        probes = packet["probes"]
        assert probes
        assert {probe["status"] for probe in probes} == {"UNVERIFIED"}
        assert profile["providers"][provider_id]["verification"] == {
            "required": True,
            "status": "UNVERIFIED",
        }


def test_pass_probe_requires_recorded_executed_evidence_if_promoted_later():
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
