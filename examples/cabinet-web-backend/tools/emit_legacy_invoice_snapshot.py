#!/usr/bin/env python3
"""Compile a pinned, audited Cabinet_web commit into read-only contract evidence.

This is an offline migration-data emitter, not an ingress endpoint, custody
admission, capture writer, or transfer producer. It never executes repository code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile

from jsonschema import Draft202012Validator


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: object) -> bytes:
    # The existing Cabinet_web invoice_service.content_hash contract.
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def source_set_hash(source_set: dict) -> str:
    # Provenance remains pinned by the outer snapshot. Updating an unrelated
    # audit entry must not create a new custody obligation for equal membership.
    membership = {name: source_set[name] for name in (
        "card_id", "source_id", "card_content_hash", "files"
    )}
    return "sha256:" + sha256(canonical_bytes(membership))


def load_json(raw: bytes) -> object:
    def unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def reject_constant(_: str) -> None:
        raise ValueError("non-finite JSON number")
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_keys,
                      parse_constant=reject_constant)


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or "\\" in value or "\x00" in value
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError("invalid repository-relative path")
    return str(path)


class PinnedRepository:
    def __init__(self, repository: Path, commit: str, max_object_bytes: int):
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("a full pinned Git commit is required")
        if max_object_bytes <= 0:
            raise ValueError("object bound must be positive")
        self.repository = repository.resolve(strict=True)
        self.commit = commit
        self.max_object_bytes = max_object_bytes
        if self.git("cat-file", "-t", commit).strip() != b"commit":
            raise ValueError("pinned object is not a commit")

    def git(self, *args: str) -> bytes:
        return subprocess.run(
            ["git", "--no-replace-objects", "-C", str(self.repository), *args],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout

    def read(self, path: str) -> bytes:
        object_name = self.commit + ":" + safe_path(path)
        if self.git("cat-file", "-t", object_name).strip() != b"blob":
            raise ValueError("expected a committed file blob")
        size = int(self.git("cat-file", "-s", object_name))
        if size < 1 or size > self.max_object_bytes:
            raise ValueError("committed object outside configured bound")
        raw = self.git("cat-file", "blob", object_name)
        if len(raw) != size:
            raise ValueError("Git object length mismatch")
        return raw

    def paths(self) -> set[str]:
        return {p.decode("utf-8") for p in self.git(
            "ls-tree", "-rz", "--name-only", self.commit, "--", "data/cards"
        ).split(b"\x00") if p}


def recovered_media(raw: bytes) -> str:
    # This emitter handles the audited JPEG/PDF recovery corpus only. The
    # general source ingress catalogue and full content validation remain A05.
    if raw.startswith(b"\xff\xd8\xff") and raw.rstrip().endswith(b"\xff\xd9"):
        return "image/jpeg"
    if raw.startswith(b"%PDF-") and raw.rstrip().endswith(b"%%EOF"):
        return "application/pdf"
    raise ValueError("unrecognized recovered JPEG/PDF original")


def capture_state(card: dict, card_hash: str, evidence: dict | None) -> str:
    if evidence is None:
        return "missing"
    if (type(evidence.get("version")) is not int or evidence["version"] != 1
            or evidence.get("invoice_id") != card["id"]):
        return "invalid"
    if evidence.get("card_content_hash") != card_hash:
        return "stale"
    if evidence.get("source_id") != card["source"]["source_id"]:
        return "mismatch"
    if evidence.get("line_capture_complete") is not True:
        return "incomplete"
    counts = (evidence.get("source_line_count"), evidence.get("captured_line_count"))
    if any(type(n) is not int or n < 1 for n in counts):
        return "invalid"
    if any(n != len(card["lines"]) for n in counts):
        return "mismatch"
    return "verified_legacy_capture"


def build_snapshot(repository: PinnedRepository, audit_path: str) -> tuple[dict, dict[str, bytes]]:
    audit_raw = repository.read(audit_path)
    audit = load_json(audit_raw)
    if not isinstance(audit, dict) or audit.get("card_mutations") != 0:
        raise ValueError("expected the source-only recovery audit")
    hashes = audit["invoice_card_file_sha256"]
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("missing audited canonical Card inventory")
    paths = repository.paths()
    card_ids = {PurePosixPath(p).parent.name for p in paths
                if re.fullmatch(r"data/cards/invoice-[^/]+/card\.json", p)}
    if card_ids != set(hashes):
        raise ValueError("audit does not cover the complete canonical Invoice inventory")
    schema_raw = repository.read("schemas/invoice-card-v1.schema.json")
    card_schema = load_json(schema_raw)
    Draft202012Validator.check_schema(card_schema)
    validator = Draft202012Validator(card_schema)
    objects: dict[str, bytes] = {}

    def retain(raw: bytes) -> str:
        digest = sha256(raw)
        if digest in objects and objects[digest] != raw:
            raise ValueError("content identity conflict")
        objects[digest] = raw
        return digest

    audit_hash = retain(audit_raw)
    schema_hash = retain(schema_raw)
    grouped: dict[str, list[dict]] = {i: [] for i in card_ids}
    unassociated = 0
    for entry in audit["files"]:
        invoice_id = entry["invoice_id"]
        raw = repository.read(entry["path"])
        if sha256(raw) != entry["sha256"] or len(raw) != entry["size_bytes"]:
            raise ValueError("audited original hash or length mismatch")
        media_type = recovered_media(raw)
        if invoice_id is None:
            unassociated += 1
            continue
        if invoice_id not in grouped:
            raise ValueError("original association targets an unknown Invoice")
        digest = retain(raw)
        if any(f["content_sha256"] == digest for f in grouped[invoice_id]):
            raise ValueError("duplicate content identity within audited source set")
        grouped[invoice_id].append({
            "ordinal": len(grouped[invoice_id]) + 1,
            "content_id": "sha256:" + digest,
            "content_sha256": digest,
            "size_bytes": len(raw), "media_type": media_type,
            "display_filename": entry.get("original_filename") or PurePosixPath(entry["path"]).name,
        })
    observations = []
    for invoice_id in sorted(card_ids):
        raw = repository.read("data/cards/" + invoice_id + "/card.json")
        if sha256(raw) != hashes[invoice_id]:
            raise ValueError("canonical Card differs from the association audit")
        card = load_json(raw)
        validator.validate(card)
        if card["id"] != invoice_id or not card["source"].get("source_id"):
            raise ValueError("canonical Card/source identity mismatch")
        card_hash = "sha256:" + sha256(canonical_bytes(card))
        capture_path = "data/cards/" + invoice_id + "/line-capture.json"
        capture_raw = repository.read(capture_path) if capture_path in paths else None
        malformed_capture = False
        try:
            evidence = load_json(capture_raw) if capture_raw is not None else None
            malformed_capture = capture_raw is not None and not isinstance(evidence, dict)
        except (ValueError, UnicodeError):
            evidence = None
            malformed_capture = True
        source_set = {
            "card_id": invoice_id, "source_id": card["source"]["source_id"],
            "card_content_hash": card_hash,
            "association_audit_sha256": audit_hash, "files": grouped[invoice_id],
        }
        observations.append({
            "card_id": invoice_id, "card_raw_sha256": retain(raw),
            "card_content_hash": card_hash, "card": card,
            "source_set": source_set,
            "source_set_hash": source_set_hash(source_set),
            "capture_raw_sha256": retain(capture_raw) if capture_raw is not None else None,
            "capture_state": "invalid" if malformed_capture else capture_state(card, card_hash, evidence),
            "document_completeness": "not_asserted",
        })
    snapshot = {
        "schema_version": "cabinet_legacy_invoice_snapshot.v1",
        "repository_commit": repository.commit,
        "association_audit_sha256": audit_hash,
        "invoice_schema_sha256": schema_hash,
        "unassociated_original_count": unassociated,
        "invoices": observations,
    }
    return snapshot, objects


def emit(repository: PinnedRepository, audit_path: str, destination: Path) -> dict:
    destination = destination.resolve()
    if destination.exists():
        raise ValueError("output already exists; an immutable snapshot is never overwritten")
    # Never put generated evidence inside the canonical source repository.
    if destination.is_relative_to(repository.repository):
        raise ValueError("output must be outside the canonical repository")
    snapshot, objects = build_snapshot(repository, audit_path)
    wrapper_schema = json.loads((Path(__file__).parents[1] / "contracts" /
                                "legacy_invoice_snapshot_v1.schema.json").read_text())
    Draft202012Validator(wrapper_schema).validate(snapshot)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".cabinet-snapshot-", dir=destination.parent))
    try:
        (stage / "objects").mkdir(mode=0o700)
        for digest, raw in objects.items():
            target = stage / "objects" / digest
            with target.open("xb") as stream:
                os.chmod(target, 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if sha256(target.read_bytes()) != digest:
                raise ValueError("exported object failed re-read verification")
        raw_snapshot = canonical_bytes(snapshot) + b"\n"
        target = stage / "snapshot.json"
        with target.open("xb") as stream:
            os.chmod(target, 0o600)
            stream.write(raw_snapshot)
            stream.flush()
            os.fsync(stream.fileno())
        # mkdir reserves the caller's destination exclusively. Rename into a
        # fixed child cannot replace a concurrent export's output.
        destination.mkdir(mode=0o700)
        stage.rename(destination / "bundle")
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {
        "snapshot_sha256": sha256(raw_snapshot),
        "invoice_count": len(snapshot["invoices"]),
        "associated_original_count": sum(len(i["source_set"]["files"]) for i in snapshot["invoices"]),
        "capture_verified_count": sum(i["capture_state"] == "verified_legacy_capture" for i in snapshot["invoices"]),
        "unassociated_original_count": snapshot["unassociated_original_count"],
        "canonical_mutations": 0, "custody_admissions": 0, "transfer_admissions": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--audit-path", required=True)
    parser.add_argument("--max-object-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = PinnedRepository(args.repository, args.commit, args.max_object_bytes)
    print(json.dumps(emit(repository, args.audit_path, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
