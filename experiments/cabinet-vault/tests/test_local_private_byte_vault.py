from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from local_private_byte_vault import (
    ByteVaultError,
    ByteVaultRecoveryError,
    ByteVaultSecurityError,
    LocalPrivateByteVault,
)
from local_private_byte_vault_probe import run_probe


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_vault_requires_absolute_private_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ByteVaultError, match="absolute"):
        LocalPrivateByteVault(Path("relative-vault"))


def test_stage_returns_opaque_references_and_rejects_raw_paths(tmp_path):
    vault = LocalPrivateByteVault(tmp_path / "vault")
    content = b"opaque"
    staged = vault.stage(content, digest(content), len(content))

    assert staged.staging_reference.startswith("staging:")
    assert staged.final_reference.startswith("blob:")
    assert str(vault.root) not in staged.staging_reference
    assert str(vault.root) not in staged.final_reference

    with pytest.raises(ByteVaultSecurityError):
        vault.verify(str(vault.staging_root / "raw-path.blob"), digest(content), len(content))


def test_stage_rejects_wrong_hash_or_size_before_publication(tmp_path):
    vault = LocalPrivateByteVault(tmp_path / "vault")
    content = b"content"

    with pytest.raises(ByteVaultError, match="size"):
        vault.stage(content, digest(content), len(content) + 1)

    with pytest.raises(ByteVaultError, match="hash"):
        vault.stage(content, digest(b"different"), len(content))


def test_publish_does_not_depend_on_os_link(tmp_path, monkeypatch):
    monkeypatch.setattr(
        os,
        "link",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("os.link must not be used")),
        raising=False,
    )
    vault = LocalPrivateByteVault(tmp_path / "vault")
    content = b"portable-publication"
    staged = vault.stage(content, digest(content), len(content))

    final_reference = vault.publish(staged.staging_reference, digest(content), len(content))

    assert vault.verify(final_reference, digest(content), len(content))


def test_remove_staging_cannot_remove_final_reference(tmp_path):
    vault = LocalPrivateByteVault(tmp_path / "vault")
    content = b"published"
    staged = vault.stage(content, digest(content), len(content))
    final_reference = vault.publish(staged.staging_reference, digest(content), len(content))

    with pytest.raises(ByteVaultSecurityError, match="final"):
        vault.remove_staging(final_reference)
    assert vault.verify(final_reference, digest(content), len(content))


def test_missing_committed_publication_blocks_recovery(tmp_path):
    vault = LocalPrivateByteVault(tmp_path / "vault")
    content = b"missing"

    with pytest.raises(ByteVaultRecoveryError):
        vault.recover_required(
            "staging:00000000000000000000000000000000",
            digest(content),
            len(content),
        )


def test_full_byte_vault_probe_passes_on_real_test_filesystem(tmp_path):
    report = run_probe(tmp_path)

    assert report.status == "pass"
    assert [item.probe_id for item in report.results] == [
        "VAULT-PROBE-001",
        "VAULT-PROBE-002",
        "VAULT-PROBE-003",
        "VAULT-PROBE-004",
        "VAULT-PROBE-005",
        "VAULT-PROBE-006",
    ]
    assert {item.status for item in report.results} == {"PASS"}
