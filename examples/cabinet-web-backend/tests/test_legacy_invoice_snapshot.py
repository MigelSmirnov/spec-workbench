"""Migration-boundary witnesses using committed synthetic source repositories."""
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).parents[1] / "tools" / "emit_legacy_invoice_snapshot.py"
SPEC = importlib.util.spec_from_file_location("legacy_snapshot", SCRIPT)
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


def commit(repo):
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Contract test",
                    "-c", "user.email=contract@example.invalid", "commit", "-qm", "fixture"],
                   check=True, capture_output=True)
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).decode().strip()


def write(repo, name, value):
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(value if isinstance(value, bytes) else snapshot.canonical_bytes(value))


@pytest.fixture
def source(tmp_path):
    repo = tmp_path / "source"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    # An external fixture schema isolates exporter behavior; the real-data
    # acceptance separately validates all Cards against the pinned product schema.
    write(repo, "schemas/invoice-card-v1.schema.json", {"type": "object", "required": ["id", "source", "lines"]})
    cards = {}
    for name in ("invoice-a", "invoice-b"):
        card = {"id": name, "status": "confirmed", "source": {"source_id": "source-001"}, "lines": [{"description": "Test row"}]}
        cards[name] = card
        write(repo, f"data/cards/{name}/card.json", card)
    evidence = {"version": 1, "invoice_id": "invoice-a", "source_id": "source-001",
                "line_capture_complete": True, "source_line_count": 1, "captured_line_count": 1,
                "card_content_hash": "sha256:" + snapshot.sha256(snapshot.canonical_bytes(cards["invoice-a"]))}
    write(repo, "data/cards/invoice-a/line-capture.json", evidence)
    files = []
    for name, suffix, raw in (("invoice-a", "1.jpg", b"\xff\xd8\xffshot-a\xff\xd9"),
                              ("invoice-a", "2.jpg", b"\xff\xd8\xffshot-b\xff\xd9"),
                              ("invoice-b", "1.pdf", b"%PDF-1.4\nfixture\n%%EOF")):
        path = f"data/cards/{name}/{suffix}"
        write(repo, path, raw)
        files.append({"invoice_id": name, "path": path, "sha256": snapshot.sha256(raw), "size_bytes": len(raw)})
    audit = {"card_mutations": 0, "files": files,
             "invoice_card_file_sha256": {n: snapshot.sha256(snapshot.canonical_bytes(c)) for n, c in cards.items()}}
    write(repo, "audit.json", audit)
    revision = commit(repo)
    return repo, revision, audit, cards, evidence


def build(repo, revision):
    return snapshot.build_snapshot(snapshot.PinnedRepository(repo, revision, 100000), "audit.json")


def test_committed_input_preserves_confirmed_cards_order_and_capture(source):
    repo, revision, _, cards, _ = source
    before = (repo / "data/cards/invoice-a/card.json").read_bytes()
    result, objects = build(repo, revision)
    first, second = result["invoices"]
    assert first["card"] == cards["invoice-a"]
    assert second["card"] == cards["invoice-b"]
    assert first["source_set"]["source_id"] == second["source_set"]["source_id"]
    assert first["source_set"]["card_id"] != second["source_set"]["card_id"]
    assert [x["ordinal"] for x in first["source_set"]["files"]] == [1, 2]
    assert first["capture_state"] == "verified_legacy_capture"
    assert second["capture_state"] == "missing"
    assert all(x["document_completeness"] == "not_asserted" for x in result["invoices"])
    assert objects[first["card_raw_sha256"]] == before
    assert (repo / "data/cards/invoice-a/card.json").read_bytes() == before
    assert build(repo, revision) == (result, objects)


def test_dirty_working_tree_is_not_canonical_input(source):
    repo, revision, _, _, _ = source
    expected = build(repo, revision)
    write(repo, "data/cards/invoice-a/card.json", {"id": "attacker"})
    write(repo, "data/cards/invoice-a/1.jpg", b"changed working bytes")
    assert build(repo, revision) == expected


def test_unrelated_audit_provenance_does_not_change_membership_identity(source):
    repo, revision, audit, _, _ = source
    first, _ = build(repo, revision)
    audit["review_note"] = "Additional provenance; no association changed."
    write(repo, "audit.json", audit)
    second, _ = build(repo, commit(repo))
    assert first["association_audit_sha256"] != second["association_audit_sha256"]
    assert [i["source_set_hash"] for i in first["invoices"]] == [i["source_set_hash"] for i in second["invoices"]]


def test_changed_card_cannot_reuse_old_association(source):
    repo, _, _, cards, _ = source
    cards["invoice-a"]["lines"].append({"description": "Unreviewed successor"})
    write(repo, "data/cards/invoice-a/card.json", cards["invoice-a"])
    with pytest.raises(ValueError, match="Card differs"):
        build(repo, commit(repo))


def test_changed_original_cannot_reuse_audited_hash(source):
    repo, _, _, _, _ = source
    write(repo, "data/cards/invoice-a/1.jpg", b"\xff\xd8\xffother\xff\xd9")
    with pytest.raises(ValueError, match="original hash or length"):
        build(repo, commit(repo))


def test_stale_capture_is_preserved_without_upgrading(source):
    repo, _, _, _, evidence = source
    evidence["card_content_hash"] = "sha256:" + "0" * 64
    raw = snapshot.canonical_bytes(evidence)
    write(repo, "data/cards/invoice-a/line-capture.json", raw)
    result, objects = build(repo, commit(repo))
    item = result["invoices"][0]
    assert item["capture_state"] == "stale"
    assert objects[item["capture_raw_sha256"]] == raw


def test_unlisted_canonical_invoice_cannot_disappear(source):
    repo, _, _, cards, _ = source
    write(repo, "data/cards/invoice-c/card.json", {**cards["invoice-b"], "id": "invoice-c"})
    with pytest.raises(ValueError, match="complete canonical Invoice inventory"):
        build(repo, commit(repo))


@pytest.mark.parametrize("raw", [b"broken json", b"[]", b"null", b"\xff"])
def test_malformed_capture_remains_visible_and_preserved(source, raw):
    repo, _, _, _, _ = source
    write(repo, "data/cards/invoice-a/line-capture.json", raw)
    result, objects = build(repo, commit(repo))
    item = result["invoices"][0]
    assert len(result["invoices"]) == 2
    assert item["capture_state"] == "invalid"
    assert objects[item["capture_raw_sha256"]] == raw


@pytest.mark.parametrize("path", ["../outside", "/etc/passwd", "a/../b", "a\\b", "a//b"])
def test_paths_cannot_escape_or_select_git_options(path):
    with pytest.raises(ValueError, match="repository-relative"):
        snapshot.safe_path(path)


def test_object_bound_and_full_commit_are_enforced(source):
    repo, revision, _, _, _ = source
    with pytest.raises(ValueError, match="full pinned"):
        snapshot.PinnedRepository(repo, "HEAD", 100000)
    limited = snapshot.PinnedRepository(repo, revision, 1)
    with pytest.raises(ValueError, match="configured bound"):
        limited.read("audit.json")


def test_duplicate_json_keys_are_not_silently_accepted():
    with pytest.raises(ValueError, match="duplicate JSON key"):
        snapshot.load_json(b'{"id":"one","id":"two"}')


@pytest.mark.parametrize("count", [True, 0, -1, "1"])
def test_capture_counts_cannot_manufacture_completeness(source, count):
    _, _, _, cards, evidence = source
    evidence["source_line_count"] = count
    assert snapshot.capture_state(cards["invoice-a"], evidence["card_content_hash"], evidence) == "invalid"
