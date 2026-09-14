#!/usr/bin/env python3
"""Execute the local_private_byte_vault verification packet on a real filesystem."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from local_private_byte_vault import (
    ByteVaultConflictError,
    ByteVaultRecoveryError,
    ByteVaultSecurityError,
    LocalPrivateByteVault,
)


PROBE_SCHEMA_VERSION = "spec_workbench_local_private_byte_vault_probe.v0"


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    status: str
    message: str


@dataclass(frozen=True)
class ProbeReport:
    schema_version: str
    provider_id: str
    status: str
    results: tuple[ProbeResult, ...]


def _result(probe_id: str, status: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, status, message)


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _probe_opaque_references(vault: LocalPrivateByteVault) -> ProbeResult:
    content = b"opaque-reference-probe"
    digest = _digest(content)
    try:
        staged = vault.stage(content, digest, len(content))
        if str(vault.root) in staged.staging_reference or str(vault.root) in staged.final_reference:
            return _result("VAULT-PROBE-001", "FAIL", "opaque reference disclosed the configured root")
        try:
            vault.verify(str(vault.root / "staging" / "forged.blob"), digest, len(content))
        except ByteVaultSecurityError:
            pass
        else:
            return _result("VAULT-PROBE-001", "FAIL", "raw filesystem path was accepted as a vault reference")
        vault.remove_staging(staged.staging_reference)
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("VAULT-PROBE-001", "FAIL", f"opaque-reference probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "VAULT-PROBE-001",
        "PASS",
        "caller-visible references were opaque and raw filesystem paths were rejected",
    )


def _probe_stage_reopen_verify(vault: LocalPrivateByteVault) -> ProbeResult:
    content = (b"stage-reopen-hash-verify\n" * 257) + b"end"
    digest = _digest(content)
    try:
        staged = vault.stage(content, digest, len(content))
        if not vault.verify(staged.staging_reference, digest, len(content)):
            return _result("VAULT-PROBE-002", "FAIL", "staged bytes did not verify after reopen")
        if vault.verify(staged.staging_reference, digest, len(content) + 1):
            return _result("VAULT-PROBE-002", "FAIL", "wrong expected size verified")
        vault.remove_staging(staged.staging_reference)
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("VAULT-PROBE-002", "FAIL", f"stage/verify probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "VAULT-PROBE-002",
        "PASS",
        "staged bytes were flushed, reopened, and verified by exact hash and size",
    )


def _probe_conflicting_final(vault: LocalPrivateByteVault) -> ProbeResult:
    content = b"authoritative-content"
    digest = _digest(content)
    try:
        staged = vault.stage(content, digest, len(content))
        _, final_path = vault._path_for_reference(staged.final_reference)
        final_path.parent.mkdir(mode=0o700, exist_ok=True)
        final_path.write_bytes(b"conflicting-content")
        try:
            vault.publish(staged.staging_reference, digest, len(content))
        except ByteVaultConflictError:
            pass
        else:
            return _result(
                "VAULT-PROBE-003",
                "FAIL",
                "conflicting bytes were allowed to occupy one content-addressed final reference",
            )
        if final_path.read_bytes() != b"conflicting-content":
            return _result("VAULT-PROBE-003", "FAIL", "conflicting existing final bytes were overwritten")
        vault.remove_staging(staged.staging_reference)
        final_path.unlink()
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("VAULT-PROBE-003", "FAIL", f"conflict probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "VAULT-PROBE-003",
        "PASS",
        "different bytes could not publish under one content-addressed final reference and existing bytes were not overwritten",
    )


def _probe_recovery_after_restart(vault: LocalPrivateByteVault) -> ProbeResult:
    content = b"recoverable-staged-content"
    digest = _digest(content)
    try:
        staged = vault.stage(content, digest, len(content))
        restarted = LocalPrivateByteVault(vault.root)
        final_reference = restarted.recover_required(staged.staging_reference, digest, len(content))
        if final_reference != staged.final_reference:
            return _result("VAULT-PROBE-004", "FAIL", "recovery returned an unexpected final reference")
        if not restarted.verify(final_reference, digest, len(content)):
            return _result("VAULT-PROBE-004", "FAIL", "recovered final bytes failed exact verification")
        second = LocalPrivateByteVault(vault.root).recover_required(
            staged.staging_reference, digest, len(content)
        )
        if second != final_reference:
            return _result("VAULT-PROBE-004", "FAIL", "repeated recovery was not idempotent")
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("VAULT-PROBE-004", "FAIL", f"recovery probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "VAULT-PROBE-004",
        "PASS",
        "a staged committed candidate recovered after provider restart and repeated recovery converged on the same verified final blob",
    )


def _probe_unresolved_recovery_blocks(vault: LocalPrivateByteVault) -> ProbeResult:
    content = b"missing-recovery-content"
    digest = _digest(content)
    missing_reference = f"staging:{uuid.uuid4().hex}"
    try:
        try:
            vault.recover_required(missing_reference, digest, len(content))
        except ByteVaultRecoveryError:
            pass
        else:
            return _result("VAULT-PROBE-005", "FAIL", "missing committed bytes did not block recovery")
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("VAULT-PROBE-005", "FAIL", f"recovery-block probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "VAULT-PROBE-005",
        "PASS",
        "committed publication with neither final nor recoverable staging bytes raised a startup-blocking recovery error",
    )


def _probe_symlink_and_nonregular_escape(vault: LocalPrivateByteVault) -> ProbeResult:
    try:
        outside = vault.root.parent / f"outside-{uuid.uuid4().hex}.bin"
        outside.write_bytes(b"outside")
        symlink_token = uuid.uuid4().hex
        symlink_path = vault.staging_root / f"{symlink_token}.blob"
        os.symlink(outside, symlink_path)
        try:
            vault.verify(f"staging:{symlink_token}", _digest(b"outside"), len(b"outside"))
        except ByteVaultSecurityError:
            pass
        else:
            return _result("VAULT-PROBE-006", "FAIL", "symlink reference was accepted")
        symlink_path.unlink()
        outside.unlink()

        fifo_token = uuid.uuid4().hex
        fifo_path = vault.staging_root / f"{fifo_token}.blob"
        os.mkfifo(fifo_path, 0o600)
        try:
            vault.verify(f"staging:{fifo_token}", _digest(b""), 0)
        except ByteVaultSecurityError:
            pass
        else:
            return _result("VAULT-PROBE-006", "FAIL", "non-regular FIFO reference was accepted")
        fifo_path.unlink()
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("VAULT-PROBE-006", "FAIL", f"filesystem escape probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "VAULT-PROBE-006",
        "PASS",
        "symlink and non-regular filesystem references failed closed before byte access",
    )


def run_probe(parent_root: Path | None = None, *, keep_root: bool = False) -> ProbeReport:
    if parent_root is None:
        probe_root = Path(tempfile.mkdtemp(prefix="spec-workbench-vault-probe-"))
        remove_root = not keep_root
    else:
        parent_root = parent_root.expanduser().resolve()
        parent_root.mkdir(parents=True, exist_ok=True)
        probe_root = parent_root / f"spec-workbench-vault-probe-{uuid.uuid4().hex[:12]}"
        probe_root.mkdir(mode=0o700)
        remove_root = not keep_root

    results: list[ProbeResult] = []
    try:
        vault = LocalPrivateByteVault(probe_root)
        probes: tuple[Callable[[LocalPrivateByteVault], ProbeResult], ...] = (
            _probe_opaque_references,
            _probe_stage_reopen_verify,
            _probe_conflicting_final,
            _probe_recovery_after_restart,
            _probe_unresolved_recovery_blocks,
            _probe_symlink_and_nonregular_escape,
        )
        results.extend(probe(vault) for probe in probes)
    except Exception as exc:  # pragma: no cover - runtime evidence
        results.append(_result("VAULT-INITIALIZE", "FAIL", f"vault initialization failed: {type(exc).__name__}: {exc}"))
    finally:
        if remove_root:
            try:
                shutil.rmtree(probe_root)
            except Exception as exc:  # pragma: no cover - runtime evidence
                results.append(_result("PROBE-CLEANUP", "FAIL", f"probe root cleanup failed: {type(exc).__name__}: {exc}"))

    status = "pass" if len(results) == 6 and all(item.status == "PASS" for item in results) else "block"
    return ProbeReport(PROBE_SCHEMA_VERSION, "local_private_byte_vault", status, tuple(results))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-root", type=Path)
    parser.add_argument("--keep-root", action="store_true")
    args = parser.parse_args(argv)

    report = run_probe(args.parent_root, keep_root=args.keep_root)
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
