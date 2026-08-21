#!/usr/bin/env python3
"""Generic private filesystem byte-vault provider for the Cabinet host experiment."""
from __future__ import annotations

import fcntl
import hashlib
import os
import re
import stat
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")


class ByteVaultError(RuntimeError):
    pass


class ByteVaultSecurityError(ByteVaultError):
    pass


class ByteVaultConflictError(ByteVaultError):
    pass


class ByteVaultRecoveryError(ByteVaultError):
    pass


@dataclass(frozen=True)
class StagedBlob:
    staging_reference: str
    final_reference: str
    content_hash: str
    size_bytes: int


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class LocalPrivateByteVault:
    """Content-addressed private vault with opaque references and fail-closed recovery."""

    def __init__(self, root: str | Path, *, max_size_bytes: int | None = None):
        root_path = Path(root)
        if not root_path.is_absolute():
            raise ByteVaultError("byte-vault root must be absolute")
        if max_size_bytes is not None and max_size_bytes <= 0:
            raise ByteVaultError("max_size_bytes must be positive when configured")

        root_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root = root_path.resolve(strict=True)
        self.staging_root = self.root / "staging"
        self.final_root = self.root / "final"
        self.locks_root = self.root / "locks"
        self.staging_root.mkdir(mode=0o700, exist_ok=True)
        self.final_root.mkdir(mode=0o700, exist_ok=True)
        self.locks_root.mkdir(mode=0o700, exist_ok=True)
        self.max_size_bytes = max_size_bytes

        self._assert_private_directory(self.root)
        self._assert_private_directory(self.staging_root)
        self._assert_private_directory(self.final_root)
        self._assert_private_directory(self.locks_root)
        if os.stat(self.staging_root).st_dev != os.stat(self.final_root).st_dev:
            raise ByteVaultError("staging and final roots must be on one filesystem")

    @staticmethod
    def _assert_private_directory(path: Path) -> None:
        observed = os.lstat(path)
        if stat.S_ISLNK(observed.st_mode) or not stat.S_ISDIR(observed.st_mode):
            raise ByteVaultSecurityError("byte-vault directory must be a real directory")

    @staticmethod
    def final_reference(content_hash: str) -> str:
        if not isinstance(content_hash, str) or not _SHA256_RE.fullmatch(content_hash):
            raise ByteVaultError("content hash must be lowercase sha256 hex")
        return f"blob:{content_hash}"

    def _path_for_reference(self, reference: str) -> tuple[str, Path]:
        if not isinstance(reference, str) or ":" not in reference:
            raise ByteVaultSecurityError("invalid opaque byte-vault reference")
        kind, value = reference.split(":", 1)
        if kind == "staging" and _TOKEN_RE.fullmatch(value):
            return kind, self.staging_root / f"{value}.blob"
        if kind == "blob" and _SHA256_RE.fullmatch(value):
            return kind, self.final_root / value[:2] / f"{value}.blob"
        raise ByteVaultSecurityError("invalid opaque byte-vault reference")

    def _assert_regular_reference(self, reference: str) -> Path:
        _, path = self._path_for_reference(reference)
        try:
            observed = os.lstat(path)
        except FileNotFoundError:
            raise
        if stat.S_ISLNK(observed.st_mode) or not stat.S_ISREG(observed.st_mode):
            raise ByteVaultSecurityError("byte-vault reference must resolve to a regular file")
        return path

    def _read_digest_and_size(self, reference: str) -> tuple[str, int]:
        path = self._assert_regular_reference(reference)
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags)
        digest = hashlib.sha256()
        size = 0
        try:
            observed = os.fstat(fd)
            if not stat.S_ISREG(observed.st_mode):
                raise ByteVaultSecurityError("opened byte-vault reference is not a regular file")
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                digest.update(chunk)
        finally:
            os.close(fd)
        return digest.hexdigest(), size

    @contextmanager
    def _publication_lock(self, content_hash: str) -> Iterator[None]:
        self.final_reference(content_hash)
        lock_path = self.locks_root / f"{content_hash}.lock"
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(lock_path, flags, 0o600)
        except OSError as exc:
            raise ByteVaultSecurityError("cannot open byte-vault publication lock safely") from exc
        try:
            observed = os.fstat(fd)
            if not stat.S_ISREG(observed.st_mode):
                raise ByteVaultSecurityError("byte-vault publication lock must be a regular file")
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def reference_exists(self, reference: str) -> bool:
        try:
            path = self._assert_regular_reference(reference)
        except FileNotFoundError:
            return False
        return path.is_file()

    def verify(self, reference: str, expected_hash: str, expected_size: int) -> bool:
        self.final_reference(expected_hash)
        if not isinstance(expected_size, int) or expected_size < 0:
            raise ByteVaultError("expected_size must be a non-negative integer")
        try:
            digest, size = self._read_digest_and_size(reference)
        except FileNotFoundError:
            return False
        return digest == expected_hash and size == expected_size

    def stage(self, content: bytes, expected_hash: str, expected_size: int) -> StagedBlob:
        if not isinstance(content, bytes):
            raise ByteVaultError("content must be bytes")
        self.final_reference(expected_hash)
        if expected_size != len(content):
            raise ByteVaultError("content size does not match expected size")
        if self.max_size_bytes is not None and len(content) > self.max_size_bytes:
            raise ByteVaultError("content exceeds configured byte-vault size limit")
        if _sha256(content) != expected_hash:
            raise ByteVaultError("content hash does not match expected hash")

        token = uuid.uuid4().hex
        staging_reference = f"staging:{token}"
        staging_path = self.staging_root / f"{token}.blob"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(staging_path, flags, 0o600)
        try:
            view = memoryview(content)
            offset = 0
            while offset < len(view):
                offset += os.write(fd, view[offset:])
            os.fsync(fd)
        finally:
            os.close(fd)
        _fsync_directory(self.staging_root)

        if not self.verify(staging_reference, expected_hash, expected_size):
            try:
                os.unlink(staging_path)
            finally:
                _fsync_directory(self.staging_root)
            raise ByteVaultError("staged bytes failed reopen/hash/size verification")

        return StagedBlob(
            staging_reference=staging_reference,
            final_reference=self.final_reference(expected_hash),
            content_hash=expected_hash,
            size_bytes=expected_size,
        )

    def publish(self, staging_reference: str, expected_hash: str, expected_size: int) -> str:
        kind, staging_path = self._path_for_reference(staging_reference)
        if kind != "staging":
            raise ByteVaultSecurityError("publish requires an opaque staging reference")
        if not self.verify(staging_reference, expected_hash, expected_size):
            raise ByteVaultError("staging candidate is missing or failed verification")

        final_reference = self.final_reference(expected_hash)
        _, final_path = self._path_for_reference(final_reference)
        final_directory = final_path.parent
        final_directory.mkdir(mode=0o700, exist_ok=True)
        self._assert_private_directory(final_directory)

        with self._publication_lock(expected_hash):
            if self.reference_exists(final_reference):
                if not self.verify(final_reference, expected_hash, expected_size):
                    raise ByteVaultConflictError(
                        "content-addressed final reference already contains different bytes"
                    )
                self.remove_staging(staging_reference)
                return final_reference

            if not self.verify(staging_reference, expected_hash, expected_size):
                raise ByteVaultError("staging candidate changed before atomic publication")

            try:
                os.replace(staging_path, final_path)
            except OSError as exc:
                raise ByteVaultError("atomic byte-vault publication rename failed") from exc
            _fsync_directory(final_directory)
            _fsync_directory(self.staging_root)

            if not self.verify(final_reference, expected_hash, expected_size):
                raise ByteVaultError("published bytes failed reopen/hash/size verification")

        return final_reference

    def remove_staging(self, staging_reference: str) -> None:
        kind, path = self._path_for_reference(staging_reference)
        if kind != "staging":
            raise ByteVaultSecurityError("remove_staging cannot remove a final reference")
        try:
            self._assert_regular_reference(staging_reference)
        except FileNotFoundError:
            return
        os.unlink(path)
        _fsync_directory(self.staging_root)

    def recover_required(self, staging_reference: str, expected_hash: str, expected_size: int) -> str:
        """Finish one committed publication or fail closed when truthful recovery is impossible."""
        final_reference = self.final_reference(expected_hash)
        final_exists = self.reference_exists(final_reference)
        staging_exists = self.reference_exists(staging_reference)

        if final_exists:
            if not self.verify(final_reference, expected_hash, expected_size):
                raise ByteVaultRecoveryError("existing final bytes failed committed recovery verification")
            if staging_exists:
                if not self.verify(staging_reference, expected_hash, expected_size):
                    raise ByteVaultRecoveryError("stale staging bytes conflict with verified final content")
                self.remove_staging(staging_reference)
            return final_reference

        if not staging_exists:
            raise ByteVaultRecoveryError(
                "committed publication has neither verified final bytes nor recoverable staging bytes"
            )
        if not self.verify(staging_reference, expected_hash, expected_size):
            raise ByteVaultRecoveryError("staging bytes failed committed recovery verification")
        return self.publish(staging_reference, expected_hash, expected_size)
